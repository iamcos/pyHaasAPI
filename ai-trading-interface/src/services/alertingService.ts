/**
 * Alerting Service
 * Handles system alerts, notifications, and escalation
 */

import { logger } from './loggingService';

export enum AlertSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

export enum AlertCategory {
  PERFORMANCE = 'performance',
  ERROR = 'error',
  SECURITY = 'security',
  SYSTEM = 'system',
  BUSINESS = 'business'
}

export interface Alert {
  id: string;
  timestamp: Date;
  severity: AlertSeverity;
  category: AlertCategory;
  title: string;
  message: string;
  data?: any;
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: Date;
  resolved: boolean;
  resolvedBy?: string;
  resolvedAt?: Date;
  escalated: boolean;
  escalatedAt?: Date;
  context?: Record<string, any>;
}

export interface AlertRule {
  id: string;
  name: string;
  category: AlertCategory;
  condition: (data: any) => boolean;
  severity: AlertSeverity;
  message: string;
  enabled: boolean;
  cooldownPeriod: number; // milliseconds
  escalationDelay: number; // milliseconds
  maxOccurrences?: number;
  context?: Record<string, any>;
}

export interface NotificationChannel {
  id: string;
  name: string;
  type: 'browser' | 'console' | 'webhook' | 'email';
  config: Record<string, any>;
  enabled: boolean;
  severityFilter: AlertSeverity[];
  categoryFilter: AlertCategory[];
}

class AlertingService {
  private alerts: Map<string, Alert> = new Map();
  private rules: Map<string, AlertRule> = new Map();
  private channels: Map<string, NotificationChannel> = new Map();
  private lastTriggered: Map<string, Date> = new Map();
  private occurrenceCount: Map<string, number> = new Map();
  private maxAlerts: number = 1000;

  constructor() {
    this.setupDefaultRules();
    this.setupDefaultChannels();
    logger.info('Alerting', 'Alerting service initialized');
  }

  private setupDefaultRules(): void {
    // Performance rules
    this.addRule({
      id: 'slow_response_time',
      name: 'Slow Response Time',
      category: AlertCategory.PERFORMANCE,
      condition: (data) => data.responseTime > 5000,
      severity: AlertSeverity.WARNING,
      message: 'Response time exceeded 5 seconds',
      enabled: true,
      cooldownPeriod: 60000, // 1 minute
      escalationDelay: 300000 // 5 minutes
    });

    this.addRule({
      id: 'critical_response_time',
      name: 'Critical Response Time',
      category: AlertCategory.PERFORMANCE,
      condition: (data) => data.responseTime > 10000,
      severity: AlertSeverity.CRITICAL,
      message: 'Response time exceeded 10 seconds',
      enabled: true,
      cooldownPeriod: 30000, // 30 seconds
      escalationDelay: 120000 // 2 minutes
    });

    this.addRule({
      id: 'high_memory_usage',
      name: 'High Memory Usage',
      category: AlertCategory.PERFORMANCE,
      condition: (data) => data.memoryUsage > 500 * 1024 * 1024, // 500MB
      severity: AlertSeverity.WARNING,
      message: 'Memory usage exceeded 500MB',
      enabled: true,
      cooldownPeriod: 120000, // 2 minutes
      escalationDelay: 600000 // 10 minutes
    });

    // Error rules
    this.addRule({
      id: 'javascript_error',
      name: 'JavaScript Error',
      category: AlertCategory.ERROR,
      condition: (data) => data.error instanceof Error,
      severity: AlertSeverity.ERROR,
      message: 'JavaScript error occurred',
      enabled: true,
      cooldownPeriod: 10000, // 10 seconds
      escalationDelay: 300000 // 5 minutes
    });

    this.addRule({
      id: 'api_error_rate',
      name: 'High API Error Rate',
      category: AlertCategory.ERROR,
      condition: (data) => data.errorRate > 0.1, // 10% error rate
      severity: AlertSeverity.WARNING,
      message: 'API error rate exceeded 10%',
      enabled: true,
      cooldownPeriod: 60000, // 1 minute
      escalationDelay: 300000 // 5 minutes
    });

    // System rules
    this.addRule({
      id: 'connection_lost',
      name: 'Connection Lost',
      category: AlertCategory.SYSTEM,
      condition: (data) => data.connectionStatus === 'disconnected',
      severity: AlertSeverity.CRITICAL,
      message: 'Connection to server lost',
      enabled: true,
      cooldownPeriod: 30000, // 30 seconds
      escalationDelay: 60000 // 1 minute
    });
  }

  private setupDefaultChannels(): void {
    // Browser notification channel
    this.addChannel({
      id: 'browser_notifications',
      name: 'Browser Notifications',
      type: 'browser',
      config: {
        requirePermission: true,
        icon: '/icon.png'
      },
      enabled: true,
      severityFilter: [AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL],
      categoryFilter: Object.values(AlertCategory)
    });

    // Console logging channel
    this.addChannel({
      id: 'console_logging',
      name: 'Console Logging',
      type: 'console',
      config: {},
      enabled: true,
      severityFilter: Object.values(AlertSeverity),
      categoryFilter: Object.values(AlertCategory)
    });

    // Development webhook (if configured)
    if (import.meta.env.VITE_ALERT_WEBHOOK_URL) {
      this.addChannel({
        id: 'webhook_alerts',
        name: 'Webhook Alerts',
        type: 'webhook',
        config: {
          url: import.meta.env.VITE_ALERT_WEBHOOK_URL,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        },
        enabled: true,
        severityFilter: [AlertSeverity.ERROR, AlertSeverity.CRITICAL],
        categoryFilter: Object.values(AlertCategory)
      });
    }
  }

  // Rule management
  addRule(rule: AlertRule): void {
    this.rules.set(rule.id, rule);
    logger.info('Alerting', `Alert rule added: ${rule.name}`, rule);
  }

  removeRule(ruleId: string): void {
    this.rules.delete(ruleId);
    logger.info('Alerting', `Alert rule removed: ${ruleId}`);
  }

  enableRule(ruleId: string): void {
    const rule = this.rules.get(ruleId);
    if (rule) {
      rule.enabled = true;
      logger.info('Alerting', `Alert rule enabled: ${rule.name}`);
    }
  }

  disableRule(ruleId: string): void {
    const rule = this.rules.get(ruleId);
    if (rule) {
      rule.enabled = false;
      logger.info('Alerting', `Alert rule disabled: ${rule.name}`);
    }
  }

  // Channel management
  addChannel(channel: NotificationChannel): void {
    this.channels.set(channel.id, channel);
    logger.info('Alerting', `Notification channel added: ${channel.name}`, channel);
  }

  removeChannel(channelId: string): void {
    this.channels.delete(channelId);
    logger.info('Alerting', `Notification channel removed: ${channelId}`);
  }

  enableChannel(channelId: string): void {
    const channel = this.channels.get(channelId);
    if (channel) {
      channel.enabled = true;
      logger.info('Alerting', `Notification channel enabled: ${channel.name}`);
    }
  }

  disableChannel(channelId: string): void {
    const channel = this.channels.get(channelId);
    if (channel) {
      channel.enabled = false;
      logger.info('Alerting', `Notification channel disabled: ${channel.name}`);
    }
  }

  // Alert processing
  processData(data: any, context?: Record<string, any>): void {
    for (const [ruleId, rule] of this.rules) {
      if (!rule.enabled) continue;

      try {
        if (rule.condition(data)) {
          this.triggerAlert(rule, data, context);
        }
      } catch (error) {
        logger.error('Alerting', `Error evaluating rule ${rule.name}`, { error, rule, data });
      }
    }
  }

  private triggerAlert(rule: AlertRule, data: any, context?: Record<string, any>): void {
    const now = new Date();
    const lastTriggered = this.lastTriggered.get(rule.id);

    // Check cooldown period
    if (lastTriggered && (now.getTime() - lastTriggered.getTime()) < rule.cooldownPeriod) {
      return;
    }

    // Check max occurrences
    if (rule.maxOccurrences) {
      const count = this.occurrenceCount.get(rule.id) || 0;
      if (count >= rule.maxOccurrences) {
        return;
      }
      this.occurrenceCount.set(rule.id, count + 1);
    }

    const alert: Alert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: now,
      severity: rule.severity,
      category: rule.category,
      title: rule.name,
      message: rule.message,
      data,
      acknowledged: false,
      resolved: false,
      escalated: false,
      context: { ...rule.context, ...context }
    };

    this.alerts.set(alert.id, alert);
    this.lastTriggered.set(rule.id, now);

    // Maintain alerts size limit
    if (this.alerts.size > this.maxAlerts) {
      const oldestAlertId = Array.from(this.alerts.keys())[0];
      this.alerts.delete(oldestAlertId);
    }

    logger.warn('Alerting', `Alert triggered: ${alert.title}`, alert);

    // Send notifications
    this.sendNotifications(alert);

    // Schedule escalation if configured
    if (rule.escalationDelay > 0) {
      setTimeout(() => {
        this.escalateAlert(alert.id);
      }, rule.escalationDelay);
    }
  }

  private sendNotifications(alert: Alert): void {
    for (const [channelId, channel] of this.channels) {
      if (!channel.enabled) continue;

      // Check severity filter
      if (!channel.severityFilter.includes(alert.severity)) continue;

      // Check category filter
      if (!channel.categoryFilter.includes(alert.category)) continue;

      try {
        this.sendNotification(channel, alert);
      } catch (error) {
        logger.error('Alerting', `Failed to send notification via ${channel.name}`, { error, alert });
      }
    }
  }

  private async sendNotification(channel: NotificationChannel, alert: Alert): Promise<void> {
    switch (channel.type) {
      case 'browser':
        await this.sendBrowserNotification(channel, alert);
        break;
      case 'console':
        this.sendConsoleNotification(channel, alert);
        break;
      case 'webhook':
        await this.sendWebhookNotification(channel, alert);
        break;
      case 'email':
        await this.sendEmailNotification(channel, alert);
        break;
      default:
        logger.warn('Alerting', `Unknown notification channel type: ${channel.type}`);
    }
  }

  private async sendBrowserNotification(channel: NotificationChannel, alert: Alert): Promise<void> {
    if (!('Notification' in window)) {
      logger.warn('Alerting', 'Browser notifications not supported');
      return;
    }

    if (Notification.permission === 'denied') {
      logger.warn('Alerting', 'Browser notifications denied');
      return;
    }

    if (Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        logger.warn('Alerting', 'Browser notification permission not granted');
        return;
      }
    }

    const notification = new Notification(alert.title, {
      body: alert.message,
      icon: channel.config.icon || '/icon.png',
      tag: alert.id,
      requireInteraction: alert.severity === AlertSeverity.CRITICAL
    });

    notification.onclick = () => {
      window.focus();
      notification.close();
    };

    // Auto-close after 10 seconds for non-critical alerts
    if (alert.severity !== AlertSeverity.CRITICAL) {
      setTimeout(() => {
        notification.close();
      }, 10000);
    }
  }

  private sendConsoleNotification(channel: NotificationChannel, alert: Alert): void {
    const prefix = `[ALERT] [${alert.severity.toUpperCase()}] [${alert.category.toUpperCase()}]`;
    
    switch (alert.severity) {
      case AlertSeverity.INFO:
        console.info(prefix, alert.title, alert.message, alert.data);
        break;
      case AlertSeverity.WARNING:
        console.warn(prefix, alert.title, alert.message, alert.data);
        break;
      case AlertSeverity.ERROR:
      case AlertSeverity.CRITICAL:
        console.error(prefix, alert.title, alert.message, alert.data);
        break;
    }
  }

  private async sendWebhookNotification(channel: NotificationChannel, alert: Alert): Promise<void> {
    const payload = {
      alert: {
        id: alert.id,
        timestamp: alert.timestamp.toISOString(),
        severity: alert.severity,
        category: alert.category,
        title: alert.title,
        message: alert.message,
        data: alert.data,
        context: alert.context
      },
      source: 'ai-trading-interface',
      version: import.meta.env.VITE_APP_VERSION || '1.0.0'
    };

    await fetch(channel.config.url, {
      method: channel.config.method || 'POST',
      headers: channel.config.headers || { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }

  private async sendEmailNotification(channel: NotificationChannel, alert: Alert): Promise<void> {
    // Email notification would be implemented here
    // This would typically involve calling an email service API
    logger.info('Alerting', 'Email notification not implemented', { channel, alert });
  }

  // Alert management
  acknowledgeAlert(alertId: string, acknowledgedBy: string): void {
    const alert = this.alerts.get(alertId);
    if (alert && !alert.acknowledged) {
      alert.acknowledged = true;
      alert.acknowledgedBy = acknowledgedBy;
      alert.acknowledgedAt = new Date();
      
      logger.info('Alerting', `Alert acknowledged: ${alert.title}`, { alertId, acknowledgedBy });
    }
  }

  resolveAlert(alertId: string, resolvedBy: string): void {
    const alert = this.alerts.get(alertId);
    if (alert && !alert.resolved) {
      alert.resolved = true;
      alert.resolvedBy = resolvedBy;
      alert.resolvedAt = new Date();
      
      logger.info('Alerting', `Alert resolved: ${alert.title}`, { alertId, resolvedBy });
    }
  }

  private escalateAlert(alertId: string): void {
    const alert = this.alerts.get(alertId);
    if (!alert || alert.acknowledged || alert.resolved || alert.escalated) {
      return;
    }

    alert.escalated = true;
    alert.escalatedAt = new Date();

    // Increase severity for escalation
    if (alert.severity === AlertSeverity.WARNING) {
      alert.severity = AlertSeverity.ERROR;
    } else if (alert.severity === AlertSeverity.ERROR) {
      alert.severity = AlertSeverity.CRITICAL;
    }

    logger.error('Alerting', `Alert escalated: ${alert.title}`, alert);

    // Send escalation notifications
    this.sendNotifications(alert);
  }

  // Data retrieval
  getAlerts(
    severity?: AlertSeverity,
    category?: AlertCategory,
    acknowledged?: boolean,
    resolved?: boolean,
    limit?: number
  ): Alert[] {
    let filteredAlerts = Array.from(this.alerts.values());

    if (severity) {
      filteredAlerts = filteredAlerts.filter(alert => alert.severity === severity);
    }

    if (category) {
      filteredAlerts = filteredAlerts.filter(alert => alert.category === category);
    }

    if (acknowledged !== undefined) {
      filteredAlerts = filteredAlerts.filter(alert => alert.acknowledged === acknowledged);
    }

    if (resolved !== undefined) {
      filteredAlerts = filteredAlerts.filter(alert => alert.resolved === resolved);
    }

    // Sort by timestamp (newest first)
    filteredAlerts.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    if (limit) {
      filteredAlerts = filteredAlerts.slice(0, limit);
    }

    return filteredAlerts;
  }

  getRules(): AlertRule[] {
    return Array.from(this.rules.values());
  }

  getChannels(): NotificationChannel[] {
    return Array.from(this.channels.values());
  }

  // Statistics
  getAlertStatistics(): any {
    const alerts = Array.from(this.alerts.values());
    
    return {
      total: alerts.length,
      bySeverity: {
        info: alerts.filter(a => a.severity === AlertSeverity.INFO).length,
        warning: alerts.filter(a => a.severity === AlertSeverity.WARNING).length,
        error: alerts.filter(a => a.severity === AlertSeverity.ERROR).length,
        critical: alerts.filter(a => a.severity === AlertSeverity.CRITICAL).length
      },
      byCategory: {
        performance: alerts.filter(a => a.category === AlertCategory.PERFORMANCE).length,
        error: alerts.filter(a => a.category === AlertCategory.ERROR).length,
        security: alerts.filter(a => a.category === AlertCategory.SECURITY).length,
        system: alerts.filter(a => a.category === AlertCategory.SYSTEM).length,
        business: alerts.filter(a => a.category === AlertCategory.BUSINESS).length
      },
      acknowledged: alerts.filter(a => a.acknowledged).length,
      resolved: alerts.filter(a => a.resolved).length,
      escalated: alerts.filter(a => a.escalated).length
    };
  }

  // Cleanup
  cleanup(): void {
    this.alerts.clear();
    this.lastTriggered.clear();
    this.occurrenceCount.clear();
    logger.info('Alerting', 'Alerting service cleaned up');
  }
}

// Create singleton instance
export const alertingService = new AlertingService();

export default alertingService;