"""
Alert and Notification Service

Provides price alerts, performance threshold notifications, visual and audio alerts,
and alert history management.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import os
import threading

from ..utils.logging import get_logger
from ..utils.errors import handle_error, ErrorCategory, ErrorSeverity


class AlertType(Enum):
    """Alert type enumeration"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE = "price_change"
    VOLUME_SPIKE = "volume_spike"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    DRAWDOWN_LIMIT = "drawdown_limit"
    POSITION_SIZE = "position_size"
    CUSTOM = "custom"


class AlertPriority(Enum):
    """Alert priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status enumeration"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    DISABLED = "disabled"
    EXPIRED = "expired"


class NotificationMethod(Enum):
    """Notification method enumeration"""
    VISUAL = "visual"
    AUDIO = "audio"
    POPUP = "popup"
    LOG = "log"
    EMAIL = "email"  # Future implementation
    WEBHOOK = "webhook"  # Future implementation


@dataclass
class AlertCondition:
    """Alert condition definition"""
    field: str  # e.g., 'price', 'volume', 'pnl', 'drawdown'
    operator: str  # 'gt', 'lt', 'eq', 'gte', 'lte', 'change_pct'
    value: float
    timeframe: Optional[str] = None  # For time-based conditions
    
    def evaluate(self, current_value: float, previous_value: Optional[float] = None) -> bool:
        """Evaluate condition against current value"""
        try:
            if self.operator == 'gt':
                return current_value > self.value
            elif self.operator == 'lt':
                return current_value < self.value
            elif self.operator == 'eq':
                return abs(current_value - self.value) < 0.0001  # Float comparison
            elif self.operator == 'gte':
                return current_value >= self.value
            elif self.operator == 'lte':
                return current_value <= self.value
            elif self.operator == 'change_pct' and previous_value is not None:
                if previous_value == 0:
                    return False
                change_pct = ((current_value - previous_value) / previous_value) * 100
                return abs(change_pct) >= self.value
            
            return False
            
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'operator': self.operator,
            'value': self.value,
            'timeframe': self.timeframe
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertCondition':
        return cls(
            field=data['field'],
            operator=data['operator'],
            value=data['value'],
            timeframe=data.get('timeframe')
        )


@dataclass
class Alert:
    """Alert definition"""
    id: str
    name: str
    alert_type: AlertType
    symbol: Optional[str]  # For market-based alerts
    condition: AlertCondition
    priority: AlertPriority = AlertPriority.MEDIUM
    status: AlertStatus = AlertStatus.ACTIVE
    notification_methods: List[NotificationMethod] = field(default_factory=lambda: [NotificationMethod.VISUAL])
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    triggered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    trigger_count: int = 0
    max_triggers: Optional[int] = None
    cooldown_minutes: int = 5  # Minimum time between triggers
    last_triggered_at: Optional[datetime] = None
    message_template: str = "Alert triggered: {name}"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if alert is active"""
        if self.status != AlertStatus.ACTIVE:
            return False
        
        if self.expires_at and datetime.now() > self.expires_at:
            self.status = AlertStatus.EXPIRED
            return False
        
        if self.max_triggers and self.trigger_count >= self.max_triggers:
            self.status = AlertStatus.TRIGGERED
            return False
        
        return True
    
    def can_trigger(self) -> bool:
        """Check if alert can trigger (considering cooldown)"""
        if not self.is_active():
            return False
        
        if self.last_triggered_at:
            cooldown_delta = timedelta(minutes=self.cooldown_minutes)
            if datetime.now() - self.last_triggered_at < cooldown_delta:
                return False
        
        return True
    
    def trigger(self, current_value: float, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger the alert"""
        now = datetime.now()
        self.triggered_at = now
        self.last_triggered_at = now
        self.trigger_count += 1
        
        # Format message
        message_context = {
            'name': self.name,
            'symbol': self.symbol or 'N/A',
            'value': current_value,
            'threshold': self.condition.value,
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
            **(context or {})
        }
        
        message = self.message_template.format(**message_context)
        
        return {
            'alert_id': self.id,
            'name': self.name,
            'message': message,
            'priority': self.priority.value,
            'symbol': self.symbol,
            'current_value': current_value,
            'threshold_value': self.condition.value,
            'triggered_at': now.isoformat(),
            'notification_methods': [method.value for method in self.notification_methods],
            'metadata': self.metadata
        }
    
    def acknowledge(self) -> None:
        """Acknowledge the alert"""
        self.acknowledged_at = datetime.now()
        self.status = AlertStatus.ACKNOWLEDGED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'alert_type': self.alert_type.value,
            'symbol': self.symbol,
            'condition': self.condition.to_dict(),
            'priority': self.priority.value,
            'status': self.status.value,
            'notification_methods': [method.value for method in self.notification_methods],
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'trigger_count': self.trigger_count,
            'max_triggers': self.max_triggers,
            'cooldown_minutes': self.cooldown_minutes,
            'last_triggered_at': self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            'message_template': self.message_template,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        alert = cls(
            id=data['id'],
            name=data['name'],
            alert_type=AlertType(data['alert_type']),
            symbol=data.get('symbol'),
            condition=AlertCondition.from_dict(data['condition']),
            priority=AlertPriority(data.get('priority', 'medium')),
            status=AlertStatus(data.get('status', 'active')),
            notification_methods=[NotificationMethod(method) for method in data.get('notification_methods', ['visual'])],
            trigger_count=data.get('trigger_count', 0),
            max_triggers=data.get('max_triggers'),
            cooldown_minutes=data.get('cooldown_minutes', 5),
            message_template=data.get('message_template', 'Alert triggered: {name}'),
            metadata=data.get('metadata', {})
        )
        
        # Parse datetime fields
        if data.get('created_at'):
            alert.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('expires_at'):
            alert.expires_at = datetime.fromisoformat(data['expires_at'])
        if data.get('triggered_at'):
            alert.triggered_at = datetime.fromisoformat(data['triggered_at'])
        if data.get('acknowledged_at'):
            alert.acknowledged_at = datetime.fromisoformat(data['acknowledged_at'])
        if data.get('last_triggered_at'):
            alert.last_triggered_at = datetime.fromisoformat(data['last_triggered_at'])
        
        return alert


@dataclass
class AlertEvent:
    """Alert event record"""
    id: str
    alert_id: str
    alert_name: str
    message: str
    priority: AlertPriority
    symbol: Optional[str]
    current_value: float
    threshold_value: float
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'alert_name': self.alert_name,
            'message': self.message,
            'priority': self.priority.value,
            'symbol': self.symbol,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'triggered_at': self.triggered_at.isoformat(),
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'metadata': self.metadata
        }


class AlertService:
    """Alert and notification service"""
    
    def __init__(self, storage_path: str = "alerts"):
        self.logger = get_logger(__name__)
        self.storage_path = storage_path
        
        # Alert storage
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[AlertEvent] = []
        
        # Data tracking for conditions
        self.market_data: Dict[str, Dict[str, float]] = {}  # symbol -> field -> value
        self.portfolio_data: Dict[str, float] = {}  # field -> value
        self.previous_values: Dict[str, float] = {}  # For change calculations
        
        # Notification handlers
        self.notification_handlers: Dict[NotificationMethod, Callable] = {}
        
        # Configuration
        self.max_history_size = 1000
        self.check_interval = 1.0  # seconds
        
        # Background task
        self.check_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Audio support
        self.audio_enabled = self._check_audio_support()
        
        # Initialize storage
        self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize alert storage"""
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            self._load_alerts()
            self._load_history()
            
            self.logger.info(f"Alert service initialized with {len(self.alerts)} alerts")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize alert storage: {e}")
    
    def _load_alerts(self) -> None:
        """Load alerts from storage"""
        try:
            alerts_file = os.path.join(self.storage_path, "alerts.json")
            if os.path.exists(alerts_file):
                with open(alerts_file, 'r') as f:
                    data = json.load(f)
                    for alert_data in data.get('alerts', []):
                        alert = Alert.from_dict(alert_data)
                        self.alerts[alert.id] = alert
                        
        except Exception as e:
            self.logger.error(f"Failed to load alerts: {e}")
    
    def _save_alerts(self) -> None:
        """Save alerts to storage"""
        try:
            alerts_file = os.path.join(self.storage_path, "alerts.json")
            data = {
                'alerts': [alert.to_dict() for alert in self.alerts.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(alerts_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save alerts: {e}")
    
    def _load_history(self) -> None:
        """Load alert history from storage"""
        try:
            history_file = os.path.join(self.storage_path, "history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    for event_data in data.get('events', []):
                        event = AlertEvent(
                            id=event_data['id'],
                            alert_id=event_data['alert_id'],
                            alert_name=event_data['alert_name'],
                            message=event_data['message'],
                            priority=AlertPriority(event_data['priority']),
                            symbol=event_data.get('symbol'),
                            current_value=event_data['current_value'],
                            threshold_value=event_data['threshold_value'],
                            triggered_at=datetime.fromisoformat(event_data['triggered_at']),
                            metadata=event_data.get('metadata', {})
                        )
                        
                        if event_data.get('acknowledged_at'):
                            event.acknowledged_at = datetime.fromisoformat(event_data['acknowledged_at'])
                        
                        self.alert_history.append(event)
                        
        except Exception as e:
            self.logger.error(f"Failed to load alert history: {e}")
    
    def _save_history(self) -> None:
        """Save alert history to storage"""
        try:
            history_file = os.path.join(self.storage_path, "history.json")
            data = {
                'events': [event.to_dict() for event in self.alert_history[-self.max_history_size:]],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save alert history: {e}")
    
    def _check_audio_support(self) -> bool:
        """Check if audio notifications are supported"""
        try:
            # Try to import audio libraries
            import pygame
            return True
        except ImportError:
            try:
                import playsound
                return True
            except ImportError:
                return False
    
    async def start(self) -> None:
        """Start the alert service"""
        try:
            self.running = True
            
            # Register default notification handlers
            self._register_default_handlers()
            
            # Start background checking task
            self.check_task = asyncio.create_task(self._check_alerts_loop())
            
            self.logger.info("Alert service started")
            
        except Exception as e:
            self.logger.error(f"Failed to start alert service: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the alert service"""
        try:
            self.running = False
            
            if self.check_task and not self.check_task.done():
                self.check_task.cancel()
                await self.check_task
            
            # Save current state
            self._save_alerts()
            self._save_history()
            
            self.logger.info("Alert service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping alert service: {e}")
    
    def create_alert(
        self,
        name: str,
        alert_type: AlertType,
        condition: AlertCondition,
        symbol: Optional[str] = None,
        priority: AlertPriority = AlertPriority.MEDIUM,
        notification_methods: List[NotificationMethod] = None,
        expires_at: Optional[datetime] = None,
        max_triggers: Optional[int] = None,
        cooldown_minutes: int = 5,
        message_template: str = None
    ) -> str:
        """Create a new alert"""
        try:
            import uuid
            alert_id = str(uuid.uuid4())
            
            alert = Alert(
                id=alert_id,
                name=name,
                alert_type=alert_type,
                symbol=symbol,
                condition=condition,
                priority=priority,
                notification_methods=notification_methods or [NotificationMethod.VISUAL],
                expires_at=expires_at,
                max_triggers=max_triggers,
                cooldown_minutes=cooldown_minutes,
                message_template=message_template or f"Alert triggered: {name}"
            )
            
            self.alerts[alert_id] = alert
            self._save_alerts()
            
            self.logger.info(f"Created alert: {name} ({alert_id})")
            return alert_id
            
        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}")
            raise
    
    def update_alert(self, alert_id: str, **kwargs) -> bool:
        """Update an existing alert"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            
            # Update fields
            for field, value in kwargs.items():
                if hasattr(alert, field):
                    setattr(alert, field, value)
            
            self._save_alerts()
            self.logger.info(f"Updated alert: {alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update alert {alert_id}: {e}")
            return False
    
    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert"""
        try:
            if alert_id in self.alerts:
                alert_name = self.alerts[alert_id].name
                del self.alerts[alert_id]
                self._save_alerts()
                
                self.logger.info(f"Deleted alert: {alert_name} ({alert_id})")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete alert {alert_id}: {e}")
            return False
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        return self.alerts.get(alert_id)
    
    def list_alerts(self, status: Optional[AlertStatus] = None) -> List[Alert]:
        """List alerts, optionally filtered by status"""
        alerts = list(self.alerts.values())
        
        if status:
            alerts = [alert for alert in alerts if alert.status == status]
        
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id in self.alerts:
                self.alerts[alert_id].acknowledge()
                self._save_alerts()
                
                # Update history
                for event in reversed(self.alert_history):
                    if event.alert_id == alert_id and not event.acknowledged_at:
                        event.acknowledged_at = datetime.now()
                        break
                
                self._save_history()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    def update_market_data(self, symbol: str, data: Dict[str, float]) -> None:
        """Update market data for alert checking"""
        if symbol not in self.market_data:
            self.market_data[symbol] = {}
        
        # Store previous values for change calculations
        for field, value in data.items():
            key = f"{symbol}_{field}"
            if key in self.market_data[symbol]:
                self.previous_values[key] = self.market_data[symbol][field]
            self.market_data[symbol][field] = value
    
    def update_portfolio_data(self, data: Dict[str, float]) -> None:
        """Update portfolio data for alert checking"""
        # Store previous values
        for field, value in data.items():
            if field in self.portfolio_data:
                self.previous_values[field] = self.portfolio_data[field]
            self.portfolio_data[field] = value
    
    def get_alert_history(self, limit: int = 100) -> List[AlertEvent]:
        """Get alert history"""
        return sorted(self.alert_history, key=lambda e: e.triggered_at, reverse=True)[:limit]
    
    def register_notification_handler(
        self, 
        method: NotificationMethod, 
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Register notification handler"""
        self.notification_handlers[method] = handler
    
    async def _check_alerts_loop(self) -> None:
        """Background loop to check alerts"""
        while self.running:
            try:
                await self._check_all_alerts()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in alert checking loop: {e}")
                await asyncio.sleep(5)
    
    async def _check_all_alerts(self) -> None:
        """Check all active alerts"""
        try:
            for alert in self.alerts.values():
                if not alert.can_trigger():
                    continue
                
                # Get current value based on alert type
                current_value = self._get_current_value(alert)
                if current_value is None:
                    continue
                
                # Get previous value for change calculations
                previous_value = self._get_previous_value(alert)
                
                # Check condition
                if alert.condition.evaluate(current_value, previous_value):
                    await self._trigger_alert(alert, current_value)
                    
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
    
    def _get_current_value(self, alert: Alert) -> Optional[float]:
        """Get current value for alert condition"""
        try:
            if alert.symbol and alert.symbol in self.market_data:
                # Market-based alert
                market_data = self.market_data[alert.symbol]
                return market_data.get(alert.condition.field)
            else:
                # Portfolio-based alert
                return self.portfolio_data.get(alert.condition.field)
                
        except Exception as e:
            self.logger.error(f"Error getting current value for alert {alert.id}: {e}")
            return None
    
    def _get_previous_value(self, alert: Alert) -> Optional[float]:
        """Get previous value for change calculations"""
        try:
            if alert.symbol:
                key = f"{alert.symbol}_{alert.condition.field}"
            else:
                key = alert.condition.field
            
            return self.previous_values.get(key)
            
        except Exception as e:
            self.logger.error(f"Error getting previous value for alert {alert.id}: {e}")
            return None
    
    async def _trigger_alert(self, alert: Alert, current_value: float) -> None:
        """Trigger an alert"""
        try:
            # Create alert event
            trigger_data = alert.trigger(current_value)
            
            # Create history event
            import uuid
            event = AlertEvent(
                id=str(uuid.uuid4()),
                alert_id=alert.id,
                alert_name=alert.name,
                message=trigger_data['message'],
                priority=alert.priority,
                symbol=alert.symbol,
                current_value=current_value,
                threshold_value=alert.condition.value,
                triggered_at=datetime.now(),
                metadata=trigger_data.get('metadata', {})
            )
            
            self.alert_history.append(event)
            
            # Keep history size manageable
            if len(self.alert_history) > self.max_history_size:
                self.alert_history = self.alert_history[-self.max_history_size:]
            
            # Send notifications
            for method in alert.notification_methods:
                await self._send_notification(method, trigger_data)
            
            # Save state
            self._save_alerts()
            self._save_history()
            
            self.logger.info(f"Alert triggered: {alert.name} ({alert.id})")
            
        except Exception as e:
            self.logger.error(f"Error triggering alert {alert.id}: {e}")
    
    async def _send_notification(self, method: NotificationMethod, data: Dict[str, Any]) -> None:
        """Send notification using specified method"""
        try:
            if method in self.notification_handlers:
                handler = self.notification_handlers[method]
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            else:
                self.logger.warning(f"No handler registered for notification method: {method.value}")
                
        except Exception as e:
            self.logger.error(f"Error sending {method.value} notification: {e}")
    
    def _register_default_handlers(self) -> None:
        """Register default notification handlers"""
        # Visual notification (log-based)
        self.register_notification_handler(
            NotificationMethod.VISUAL,
            self._visual_notification_handler
        )
        
        # Audio notification
        if self.audio_enabled:
            self.register_notification_handler(
                NotificationMethod.AUDIO,
                self._audio_notification_handler
            )
        
        # Log notification
        self.register_notification_handler(
            NotificationMethod.LOG,
            self._log_notification_handler
        )
    
    def _visual_notification_handler(self, data: Dict[str, Any]) -> None:
        """Default visual notification handler"""
        priority = data.get('priority', 'medium')
        message = data.get('message', 'Alert triggered')
        
        # This would integrate with the TUI to show visual alerts
        # For now, just log with appropriate level
        if priority == 'critical':
            self.logger.critical(f"🚨 CRITICAL ALERT: {message}")
        elif priority == 'high':
            self.logger.error(f"🔴 HIGH ALERT: {message}")
        elif priority == 'medium':
            self.logger.warning(f"🟡 MEDIUM ALERT: {message}")
        else:
            self.logger.info(f"🔵 LOW ALERT: {message}")
    
    def _audio_notification_handler(self, data: Dict[str, Any]) -> None:
        """Default audio notification handler"""
        try:
            priority = data.get('priority', 'medium')
            
            # Different sounds for different priorities
            sound_files = {
                'critical': 'critical_alert.wav',
                'high': 'high_alert.wav',
                'medium': 'medium_alert.wav',
                'low': 'low_alert.wav'
            }
            
            sound_file = sound_files.get(priority, 'medium_alert.wav')
            
            # Try to play sound in a separate thread to avoid blocking
            def play_sound():
                try:
                    # Try pygame first
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(sound_file)
                    pygame.mixer.music.play()
                except ImportError:
                    try:
                        # Fallback to playsound
                        import playsound
                        playsound.playsound(sound_file, block=False)
                    except ImportError:
                        # System beep as last resort
                        print('\a')  # ASCII bell character
            
            threading.Thread(target=play_sound, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error playing alert sound: {e}")
            # Fallback to system beep
            print('\a')
    
    def _log_notification_handler(self, data: Dict[str, Any]) -> None:
        """Default log notification handler"""
        message = data.get('message', 'Alert triggered')
        priority = data.get('priority', 'medium')
        symbol = data.get('symbol', 'N/A')
        
        log_message = f"ALERT [{priority.upper()}] {symbol}: {message}"
        
        if priority == 'critical':
            self.logger.critical(log_message)
        elif priority == 'high':
            self.logger.error(log_message)
        elif priority == 'medium':
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        active_alerts = len([a for a in self.alerts.values() if a.is_active()])
        triggered_alerts = len([a for a in self.alerts.values() if a.status == AlertStatus.TRIGGERED])
        
        return {
            'running': self.running,
            'total_alerts': len(self.alerts),
            'active_alerts': active_alerts,
            'triggered_alerts': triggered_alerts,
            'history_events': len(self.alert_history),
            'audio_enabled': self.audio_enabled,
            'notification_handlers': list(self.notification_handlers.keys()),
            'market_symbols': len(self.market_data),
            'portfolio_fields': len(self.portfolio_data)
        }