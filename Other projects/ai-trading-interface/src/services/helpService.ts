/**
 * Help Service
 * Manages in-app help system, guided tours, and contextual assistance
 */

export interface HelpTopic {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  lastUpdated: Date;
  relatedTopics: string[];
  videoUrl?: string;
  externalLinks?: { title: string; url: string }[];
}

export interface TourStep {
  id: string;
  target: string; // CSS selector
  title: string;
  content: string;
  position: 'top' | 'bottom' | 'left' | 'right' | 'center';
  action?: 'click' | 'hover' | 'focus';
  optional?: boolean;
  condition?: () => boolean;
}

export interface GuidedTour {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: number; // minutes
  steps: TourStep[];
  prerequisites?: string[];
  completionReward?: string;
}

export interface ContextualHelp {
  component: string;
  triggers: string[];
  content: string;
  priority: number;
  showOnce?: boolean;
}

class HelpService {
  private helpTopics: Map<string, HelpTopic> = new Map();
  private guidedTours: Map<string, GuidedTour> = new Map();
  private contextualHelp: Map<string, ContextualHelp> = new Map();
  private completedTours: Set<string> = new Set();
  private viewedHelp: Set<string> = new Set();
  private currentTour: string | null = null;
  private currentStep: number = 0;

  constructor() {
    this.initializeHelpContent();
    this.loadUserProgress();
  }

  private initializeHelpContent(): void {
    // Initialize help topics
    this.addHelpTopic({
      id: 'getting-started',
      title: 'Getting Started with AI Trading Interface',
      content: `
# Getting Started

Welcome to the AI Trading Interface! This comprehensive guide will help you get started with the platform.

## Overview

The AI Trading Interface is a powerful tool that combines artificial intelligence with trading automation to help you:

- Develop and test trading strategies
- Analyze market data in real-time
- Manage risk automatically
- Monitor portfolio performance

## First Steps

1. **Connect to HaasOnline**: Configure your HaasOnline connection in Settings
2. **Explore the Dashboard**: Familiarize yourself with the main interface
3. **Take a Guided Tour**: Use the help system to learn key features
4. **Create Your First Strategy**: Start with the Strategy Development Studio

## Key Features

### Dashboard
Your central hub for monitoring all trading activities, market data, and performance metrics.

### Strategy Development
Visual and code-based tools for creating, testing, and optimizing trading strategies.

### Market Analysis
AI-powered market analysis tools including sentiment analysis, pattern recognition, and arbitrage detection.

### Risk Management
Automated risk management systems with real-time monitoring and emergency controls.

### Analytics
Comprehensive analytics and reporting tools for performance analysis and optimization.

## Need Help?

- Use the search function to find specific topics
- Take guided tours for hands-on learning
- Check contextual help tooltips throughout the interface
- Visit our documentation for detailed guides
      `,
      category: 'Getting Started',
      tags: ['basics', 'introduction', 'overview'],
      difficulty: 'beginner',
      lastUpdated: new Date(),
      relatedTopics: ['dashboard-overview', 'strategy-basics', 'market-analysis-intro']
    });

    this.addHelpTopic({
      id: 'dashboard-overview',
      title: 'Dashboard Overview',
      content: `
# Dashboard Overview

The dashboard is your command center for monitoring all trading activities and market conditions.

## Main Components

### Portfolio Overview
- Real-time P&L tracking
- Asset allocation visualization
- Performance metrics

### Market Sentiment Panel
- AI-powered sentiment analysis
- Market trend indicators
- News impact assessment

### Opportunity Alerts
- Real-time trading opportunities
- Risk-adjusted recommendations
- Custom alert configuration

### Performance Metrics
- Key performance indicators
- Comparative analysis
- Historical performance tracking

## Customization

You can customize your dashboard by:
- Rearranging panels
- Adding/removing widgets
- Setting up custom alerts
- Configuring refresh intervals

## Navigation

Use the sidebar to navigate between different sections:
- Market Intelligence
- Strategy Development
- Risk Management
- Analytics
- Settings
      `,
      category: 'Interface',
      tags: ['dashboard', 'navigation', 'overview'],
      difficulty: 'beginner',
      lastUpdated: new Date(),
      relatedTopics: ['getting-started', 'customization', 'navigation']
    });

    this.addHelpTopic({
      id: 'strategy-development',
      title: 'Strategy Development Guide',
      content: `
# Strategy Development Guide

Learn how to create, test, and deploy trading strategies using our advanced development tools.

## Strategy Types

### Visual Strategies
- Drag-and-drop interface
- Pre-built components
- No coding required
- Perfect for beginners

### Code-Based Strategies
- Full HaasScript support
- Advanced customization
- Professional development tools
- Version control integration

## Development Process

1. **Design**: Plan your strategy logic
2. **Build**: Create using visual or code tools
3. **Test**: Backtest with historical data
4. **Optimize**: Fine-tune parameters
5. **Deploy**: Activate on live markets

## Best Practices

- Start simple and iterate
- Always backtest thoroughly
- Consider risk management
- Monitor performance regularly
- Keep detailed documentation

## Tools Available

- Visual Script Editor
- Code Editor with syntax highlighting
- Backtesting engine
- Parameter optimization
- Version control
- Strategy comparison tools
      `,
      category: 'Strategy Development',
      tags: ['strategy', 'development', 'coding', 'backtesting'],
      difficulty: 'intermediate',
      lastUpdated: new Date(),
      relatedTopics: ['haasscript-basics', 'backtesting-guide', 'optimization-tips']
    });

    // Initialize guided tours
    this.addGuidedTour({
      id: 'first-time-user',
      title: 'Welcome Tour',
      description: 'A comprehensive introduction to the AI Trading Interface for new users.',
      category: 'Getting Started',
      difficulty: 'beginner',
      estimatedTime: 10,
      steps: [
        {
          id: 'welcome',
          target: 'body',
          title: 'Welcome to AI Trading Interface!',
          content: 'Let\'s take a quick tour to get you familiar with the platform. This tour will show you the key features and how to navigate the interface.',
          position: 'center'
        },
        {
          id: 'dashboard',
          target: '[data-tour="dashboard"]',
          title: 'Dashboard Overview',
          content: 'This is your main dashboard where you can monitor your portfolio, market conditions, and trading opportunities in real-time.',
          position: 'bottom'
        },
        {
          id: 'sidebar',
          target: '[data-tour="sidebar"]',
          title: 'Navigation Sidebar',
          content: 'Use this sidebar to navigate between different sections of the platform. Each section provides specialized tools and information.',
          position: 'right'
        },
        {
          id: 'market-intelligence',
          target: '[data-tour="market-intelligence"]',
          title: 'Market Intelligence',
          content: 'Access AI-powered market analysis, sentiment tracking, and opportunity detection tools here.',
          position: 'right',
          action: 'click'
        },
        {
          id: 'strategy-development',
          target: '[data-tour="strategy-development"]',
          title: 'Strategy Development',
          content: 'Create, test, and optimize your trading strategies using our visual and code-based development tools.',
          position: 'right',
          action: 'click'
        },
        {
          id: 'risk-management',
          target: '[data-tour="risk-management"]',
          title: 'Risk Management',
          content: 'Monitor and control your trading risks with automated systems and real-time alerts.',
          position: 'right',
          action: 'click'
        },
        {
          id: 'help-system',
          target: '[data-tour="help-button"]',
          title: 'Help System',
          content: 'Access help, documentation, and guided tours anytime using this help button. You can search for specific topics or browse by category.',
          position: 'left'
        },
        {
          id: 'completion',
          target: 'body',
          title: 'Tour Complete!',
          content: 'You\'ve completed the welcome tour! You can always access help and take additional tours from the help menu. Happy trading!',
          position: 'center'
        }
      ]
    });

    this.addGuidedTour({
      id: 'strategy-creation',
      title: 'Creating Your First Strategy',
      description: 'Learn how to create a simple trading strategy using the visual editor.',
      category: 'Strategy Development',
      difficulty: 'beginner',
      estimatedTime: 15,
      prerequisites: ['first-time-user'],
      steps: [
        {
          id: 'navigate-to-strategy',
          target: '[data-tour="strategy-development"]',
          title: 'Navigate to Strategy Development',
          content: 'First, let\'s go to the Strategy Development section where you can create and manage your trading strategies.',
          position: 'right',
          action: 'click'
        },
        {
          id: 'create-new-strategy',
          target: '[data-tour="new-strategy-button"]',
          title: 'Create New Strategy',
          content: 'Click this button to start creating a new trading strategy. You can choose between visual and code-based development.',
          position: 'bottom',
          action: 'click'
        },
        {
          id: 'choose-visual-editor',
          target: '[data-tour="visual-editor-option"]',
          title: 'Choose Visual Editor',
          content: 'For this tour, we\'ll use the visual editor which allows you to create strategies using drag-and-drop components.',
          position: 'right',
          action: 'click'
        },
        {
          id: 'add-components',
          target: '[data-tour="component-palette"]',
          title: 'Component Palette',
          content: 'This palette contains all the building blocks for your strategy. Drag components from here onto the canvas to build your logic.',
          position: 'right'
        },
        {
          id: 'configure-component',
          target: '[data-tour="component-properties"]',
          title: 'Configure Components',
          content: 'When you select a component, its properties appear here. You can customize parameters, conditions, and actions.',
          position: 'left'
        },
        {
          id: 'test-strategy',
          target: '[data-tour="test-strategy-button"]',
          title: 'Test Your Strategy',
          content: 'Once you\'ve built your strategy, use this button to run backtests and see how it would have performed historically.',
          position: 'bottom',
          action: 'click'
        }
      ]
    });

    // Initialize contextual help
    this.addContextualHelp({
      component: 'StrategyEditor',
      triggers: ['first-visit', 'empty-canvas'],
      content: 'Start by dragging components from the palette on the left. Connect them to create your trading logic flow.',
      priority: 1,
      showOnce: true
    });

    this.addContextualHelp({
      component: 'MarketAnalysis',
      triggers: ['data-loading'],
      content: 'Market data is being loaded. This may take a few moments for the first time.',
      priority: 2
    });

    this.addContextualHelp({
      component: 'RiskManagement',
      triggers: ['high-risk-detected'],
      content: 'High risk detected in your portfolio. Consider reviewing your position sizes and stop-loss settings.',
      priority: 3
    });
  }

  // Help topic management
  addHelpTopic(topic: HelpTopic): void {
    this.helpTopics.set(topic.id, topic);
  }

  getHelpTopic(id: string): HelpTopic | undefined {
    return this.helpTopics.get(id);
  }

  searchHelpTopics(query: string, category?: string, difficulty?: string): HelpTopic[] {
    const results: HelpTopic[] = [];
    const searchTerms = query.toLowerCase().split(' ');

    for (const topic of this.helpTopics.values()) {
      // Filter by category and difficulty if specified
      if (category && topic.category !== category) continue;
      if (difficulty && topic.difficulty !== difficulty) continue;

      // Search in title, content, and tags
      const searchText = `${topic.title} ${topic.content} ${topic.tags.join(' ')}`.toLowerCase();
      
      const matchScore = searchTerms.reduce((score, term) => {
        if (searchText.includes(term)) {
          // Higher score for title matches
          if (topic.title.toLowerCase().includes(term)) score += 3;
          // Medium score for tag matches
          else if (topic.tags.some(tag => tag.toLowerCase().includes(term))) score += 2;
          // Lower score for content matches
          else score += 1;
        }
        return score;
      }, 0);

      if (matchScore > 0) {
        results.push({ ...topic, matchScore } as any);
      }
    }

    // Sort by match score
    return results.sort((a: any, b: any) => b.matchScore - a.matchScore);
  }

  getHelpTopicsByCategory(category: string): HelpTopic[] {
    return Array.from(this.helpTopics.values()).filter(topic => topic.category === category);
  }

  getRelatedTopics(topicId: string): HelpTopic[] {
    const topic = this.getHelpTopic(topicId);
    if (!topic) return [];

    return topic.relatedTopics
      .map(id => this.getHelpTopic(id))
      .filter(Boolean) as HelpTopic[];
  }

  // Guided tour management
  addGuidedTour(tour: GuidedTour): void {
    this.guidedTours.set(tour.id, tour);
  }

  getGuidedTour(id: string): GuidedTour | undefined {
    return this.guidedTours.get(id);
  }

  getAvailableTours(difficulty?: string): GuidedTour[] {
    const tours = Array.from(this.guidedTours.values());
    
    if (difficulty) {
      return tours.filter(tour => tour.difficulty === difficulty);
    }
    
    return tours;
  }

  getRecommendedTours(): GuidedTour[] {
    const completed = this.completedTours;
    const available = Array.from(this.guidedTours.values());
    
    return available.filter(tour => {
      // Not already completed
      if (completed.has(tour.id)) return false;
      
      // Prerequisites met
      if (tour.prerequisites) {
        return tour.prerequisites.every(prereq => completed.has(prereq));
      }
      
      return true;
    }).sort((a, b) => {
      // Prioritize beginner tours
      if (a.difficulty === 'beginner' && b.difficulty !== 'beginner') return -1;
      if (b.difficulty === 'beginner' && a.difficulty !== 'beginner') return 1;
      return 0;
    });
  }

  startTour(tourId: string): boolean {
    const tour = this.getGuidedTour(tourId);
    if (!tour) return false;

    // Check prerequisites
    if (tour.prerequisites) {
      const unmetPrereqs = tour.prerequisites.filter(prereq => !this.completedTours.has(prereq));
      if (unmetPrereqs.length > 0) {
        console.warn(`Cannot start tour ${tourId}: missing prerequisites ${unmetPrereqs.join(', ')}`);
        return false;
      }
    }

    this.currentTour = tourId;
    this.currentStep = 0;
    return true;
  }

  getCurrentTourStep(): { tour: GuidedTour; step: TourStep; stepIndex: number } | null {
    if (!this.currentTour) return null;

    const tour = this.getGuidedTour(this.currentTour);
    if (!tour) return null;

    const step = tour.steps[this.currentStep];
    if (!step) return null;

    return { tour, step, stepIndex: this.currentStep };
  }

  nextTourStep(): boolean {
    if (!this.currentTour) return false;

    const tour = this.getGuidedTour(this.currentTour);
    if (!tour) return false;

    if (this.currentStep < tour.steps.length - 1) {
      this.currentStep++;
      return true;
    } else {
      // Tour completed
      this.completeTour(this.currentTour);
      return false;
    }
  }

  previousTourStep(): boolean {
    if (!this.currentTour || this.currentStep <= 0) return false;
    
    this.currentStep--;
    return true;
  }

  skipTourStep(): boolean {
    const current = this.getCurrentTourStep();
    if (!current || !current.step.optional) return false;
    
    return this.nextTourStep();
  }

  completeTour(tourId: string): void {
    this.completedTours.add(tourId);
    this.currentTour = null;
    this.currentStep = 0;
    this.saveUserProgress();
  }

  exitTour(): void {
    this.currentTour = null;
    this.currentStep = 0;
  }

  // Contextual help management
  addContextualHelp(help: ContextualHelp): void {
    this.contextualHelp.set(help.component, help);
  }

  getContextualHelp(component: string, trigger: string): ContextualHelp | null {
    const help = this.contextualHelp.get(component);
    if (!help || !help.triggers.includes(trigger)) return null;

    // Check if should show only once
    if (help.showOnce && this.viewedHelp.has(`${component}-${trigger}`)) {
      return null;
    }

    return help;
  }

  markHelpViewed(component: string, trigger: string): void {
    this.viewedHelp.add(`${component}-${trigger}`);
    this.saveUserProgress();
  }

  // User progress management
  private loadUserProgress(): void {
    try {
      const completed = localStorage.getItem('help_completed_tours');
      if (completed) {
        this.completedTours = new Set(JSON.parse(completed));
      }

      const viewed = localStorage.getItem('help_viewed_help');
      if (viewed) {
        this.viewedHelp = new Set(JSON.parse(viewed));
      }
    } catch (error) {
      console.warn('Failed to load help progress:', error);
    }
  }

  private saveUserProgress(): void {
    try {
      localStorage.setItem('help_completed_tours', JSON.stringify(Array.from(this.completedTours)));
      localStorage.setItem('help_viewed_help', JSON.stringify(Array.from(this.viewedHelp)));
    } catch (error) {
      console.warn('Failed to save help progress:', error);
    }
  }

  // Utility methods
  getCategories(): string[] {
    const categories = new Set<string>();
    for (const topic of this.helpTopics.values()) {
      categories.add(topic.category);
    }
    return Array.from(categories).sort();
  }

  getCompletionStats(): { completedTours: number; totalTours: number; completionRate: number } {
    const totalTours = this.guidedTours.size;
    const completedTours = this.completedTours.size;
    const completionRate = totalTours > 0 ? (completedTours / totalTours) * 100 : 0;

    return { completedTours, totalTours, completionRate };
  }

  reset(): void {
    this.completedTours.clear();
    this.viewedHelp.clear();
    this.currentTour = null;
    this.currentStep = 0;
    localStorage.removeItem('help_completed_tours');
    localStorage.removeItem('help_viewed_help');
  }
}

// Create singleton instance
export const helpService = new HelpService();

export default helpService;