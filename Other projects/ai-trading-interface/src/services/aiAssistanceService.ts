/**
 * AI-Powered Assistance Service
 * Provides intelligent help and contextual assistance using AI
 */

import { helpService } from './helpService';

export interface AssistanceRequest {
  query: string;
  context?: {
    currentPage?: string;
    userAction?: string;
    errorMessage?: string;
    componentState?: any;
  };
  userId?: string;
  sessionId: string;
}

export interface AssistanceResponse {
  id: string;
  query: string;
  response: string;
  confidence: number;
  suggestions: string[];
  relatedTopics: string[];
  actions?: AssistanceAction[];
  timestamp: Date;
}

export interface AssistanceAction {
  type: 'navigate' | 'open_help' | 'start_tour' | 'execute_command';
  label: string;
  data: any;
}

export interface ConversationHistory {
  id: string;
  messages: Array<{
    type: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    metadata?: any;
  }>;
  context: any;
  startTime: Date;
  lastActivity: Date;
}

class AIAssistanceService {
  private conversations: Map<string, ConversationHistory> = new Map();
  private knowledgeBase: Map<string, any> = new Map();
  private commonQueries: Map<string, AssistanceResponse> = new Map();

  constructor() {
    this.initializeKnowledgeBase();
    this.initializeCommonQueries();
  }

  private initializeKnowledgeBase(): void {
    // Initialize with common trading and platform knowledge
    this.knowledgeBase.set('trading_basics', {
      topics: ['orders', 'positions', 'risk_management', 'technical_analysis'],
      content: {
        orders: 'Trading orders are instructions to buy or sell assets. Common types include market orders, limit orders, and stop orders.',
        positions: 'A position represents your current holdings in an asset. Long positions profit when price rises, short positions profit when price falls.',
        risk_management: 'Risk management involves controlling potential losses through position sizing, stop-losses, and diversification.',
        technical_analysis: 'Technical analysis uses price charts and indicators to predict future price movements.'
      }
    });

    this.knowledgeBase.set('platform_features', {
      topics: ['dashboard', 'strategy_development', 'market_intelligence', 'risk_management', 'analytics'],
      content: {
        dashboard: 'The dashboard provides an overview of your portfolio, market conditions, and trading opportunities.',
        strategy_development: 'Strategy development tools allow you to create, test, and deploy automated trading strategies.',
        market_intelligence: 'Market intelligence provides AI-powered analysis of market conditions and opportunities.',
        risk_management: 'Risk management tools help monitor and control trading risks in real-time.',
        analytics: 'Analytics tools provide detailed performance analysis and reporting capabilities.'
      }
    });

    this.knowledgeBase.set('troubleshooting', {
      topics: ['connection_issues', 'performance_problems', 'data_issues', 'strategy_issues'],
      content: {
        connection_issues: 'Connection problems can be resolved by checking internet connectivity, API credentials, and firewall settings.',
        performance_problems: 'Performance issues can be improved by closing unnecessary applications, reducing data refresh rates, and clearing cache.',
        data_issues: 'Data problems can be fixed by checking data provider connections, verifying subscriptions, and clearing data cache.',
        strategy_issues: 'Strategy problems can be diagnosed by checking strategy logic, market conditions, and risk limits.'
      }
    });
  }

  private initializeCommonQueries(): void {
    // Pre-populate common queries and responses
    this.commonQueries.set('how to create strategy', {
      id: 'create_strategy_help',
      query: 'how to create strategy',
      response: `To create a trading strategy, follow these steps:

1. **Navigate to Strategy Development**: Click on "Strategy Development" in the sidebar
2. **Choose Development Method**: Select either Visual Editor (drag-and-drop) or Code Editor
3. **Define Strategy Logic**: Set up your entry and exit conditions
4. **Add Risk Management**: Include stop-losses and position sizing rules
5. **Backtest**: Test your strategy on historical data
6. **Paper Trade**: Test with real market data but simulated money
7. **Deploy**: Activate your strategy for live trading

Would you like me to start the "Creating Your First Strategy" guided tour?`,
      confidence: 0.95,
      suggestions: [
        'Start guided tour for strategy creation',
        'Learn about visual vs code-based strategies',
        'Understand backtesting process'
      ],
      relatedTopics: ['strategy-development', 'backtesting-guide', 'risk-management'],
      actions: [
        {
          type: 'start_tour',
          label: 'Start Strategy Creation Tour',
          data: { tourId: 'strategy-creation' }
        },
        {
          type: 'navigate',
          label: 'Go to Strategy Development',
          data: { route: '/strategy-development' }
        }
      ],
      timestamp: new Date()
    });

    this.commonQueries.set('connection problems', {
      id: 'connection_help',
      query: 'connection problems',
      response: `If you're experiencing connection issues, try these solutions:

1. **Check Internet Connection**: Ensure you have a stable internet connection
2. **Verify API Credentials**: Go to Settings > API Configuration and verify your credentials
3. **Check Firewall**: Make sure the application isn't blocked by your firewall
4. **Exchange Status**: Check if the exchange or data provider is experiencing issues
5. **Rate Limits**: Verify you haven't exceeded API rate limits
6. **Restart Application**: Try restarting the application

If the problem persists, check the error logs in Settings > System > Logs for more details.`,
      confidence: 0.90,
      suggestions: [
        'Check API configuration',
        'View system logs',
        'Test connection status'
      ],
      relatedTopics: ['troubleshooting', 'api-configuration', 'system-settings'],
      actions: [
        {
          type: 'navigate',
          label: 'Go to API Settings',
          data: { route: '/settings/api' }
        },
        {
          type: 'execute_command',
          label: 'Test Connection',
          data: { command: 'test_connection' }
        }
      ],
      timestamp: new Date()
    });

    this.commonQueries.set('risk management', {
      id: 'risk_management_help',
      query: 'risk management',
      response: `Risk management is crucial for successful trading. Here's how to set it up:

**Automated Risk Management:**
- **Position Sizing**: Set maximum position sizes based on your risk tolerance
- **Stop-Loss Orders**: Automatically exit losing positions at predetermined levels
- **Daily Loss Limits**: Set maximum daily loss limits to protect your capital
- **Exposure Limits**: Limit exposure to specific assets or sectors

**Risk Monitoring:**
- **Real-time Metrics**: Monitor Value at Risk (VaR) and other risk metrics
- **Risk Alerts**: Get notified when risk thresholds are exceeded
- **Portfolio Analysis**: Analyze diversification and correlation risks

**Emergency Controls:**
- **Circuit Breakers**: Automatic trading halts during extreme conditions
- **Emergency Stop**: Manual button to immediately halt all trading

Navigate to Risk Management to configure these settings.`,
      confidence: 0.92,
      suggestions: [
        'Configure risk limits',
        'Set up risk alerts',
        'Learn about position sizing'
      ],
      relatedTopics: ['risk-management', 'position-sizing', 'stop-loss-optimization'],
      actions: [
        {
          type: 'navigate',
          label: 'Go to Risk Management',
          data: { route: '/risk-management' }
        },
        {
          type: 'open_help',
          label: 'Risk Management Guide',
          data: { topicId: 'risk-management-guide' }
        }
      ],
      timestamp: new Date()
    });
  }

  async getAssistance(request: AssistanceRequest): Promise<AssistanceResponse> {
    const conversationId = request.sessionId;
    
    // Get or create conversation
    let conversation = this.conversations.get(conversationId);
    if (!conversation) {
      conversation = {
        id: conversationId,
        messages: [],
        context: request.context || {},
        startTime: new Date(),
        lastActivity: new Date()
      };
      this.conversations.set(conversationId, conversation);
    }

    // Add user message to conversation
    conversation.messages.push({
      type: 'user',
      content: request.query,
      timestamp: new Date(),
      metadata: request.context
    });

    // Process the query
    const response = await this.processQuery(request, conversation);

    // Add assistant response to conversation
    conversation.messages.push({
      type: 'assistant',
      content: response.response,
      timestamp: new Date(),
      metadata: {
        confidence: response.confidence,
        suggestions: response.suggestions,
        actions: response.actions
      }
    });

    conversation.lastActivity = new Date();

    return response;
  }

  private async processQuery(request: AssistanceRequest, conversation: ConversationHistory): Promise<AssistanceResponse> {
    const query = request.query.toLowerCase().trim();
    
    // Check for exact matches in common queries
    for (const [key, response] of this.commonQueries) {
      if (query.includes(key)) {
        return {
          ...response,
          id: `response_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date()
        };
      }
    }

    // Analyze query intent
    const intent = this.analyzeIntent(query, request.context);
    
    // Generate contextual response
    const response = await this.generateResponse(query, intent, request.context, conversation);
    
    return response;
  }

  private analyzeIntent(query: string, context?: any): string {
    const keywords = query.split(' ').map(word => word.toLowerCase());
    
    // Intent classification based on keywords
    if (keywords.some(word => ['create', 'build', 'make', 'develop'].includes(word)) &&
        keywords.some(word => ['strategy', 'bot', 'algorithm'].includes(word))) {
      return 'create_strategy';
    }
    
    if (keywords.some(word => ['error', 'problem', 'issue', 'bug', 'broken'].includes(word))) {
      return 'troubleshooting';
    }
    
    if (keywords.some(word => ['risk', 'loss', 'stop', 'limit'].includes(word))) {
      return 'risk_management';
    }
    
    if (keywords.some(word => ['how', 'what', 'where', 'when', 'why'].includes(word))) {
      return 'information_seeking';
    }
    
    if (keywords.some(word => ['connect', 'connection', 'api', 'login'].includes(word))) {
      return 'connection_help';
    }
    
    if (keywords.some(word => ['dashboard', 'interface', 'navigate', 'find'].includes(word))) {
      return 'navigation_help';
    }
    
    return 'general_inquiry';
  }

  private async generateResponse(
    query: string, 
    intent: string, 
    context?: any, 
    conversation?: ConversationHistory
  ): Promise<AssistanceResponse> {
    let response = '';
    let confidence = 0.7;
    let suggestions: string[] = [];
    let relatedTopics: string[] = [];
    let actions: AssistanceAction[] = [];

    switch (intent) {
      case 'create_strategy':
        response = `I can help you create a trading strategy! Here are your options:

**Visual Strategy Builder:**
- Drag-and-drop interface, perfect for beginners
- Pre-built components for common trading logic
- No coding required

**Code-Based Strategy:**
- Full HaasScript support for advanced users
- Complete customization and flexibility
- Professional development tools

**Recommended Steps:**
1. Start with the Strategy Creation guided tour
2. Choose your development approach
3. Define your trading logic
4. Add risk management rules
5. Backtest your strategy

Would you like me to start the guided tour or navigate to the Strategy Development section?`;
        
        confidence = 0.85;
        suggestions = [
          'Start strategy creation tour',
          'Learn about visual vs code strategies',
          'Understand backtesting process'
        ];
        relatedTopics = ['strategy-development', 'visual-editor', 'haasscript-basics'];
        actions = [
          {
            type: 'start_tour',
            label: 'Start Strategy Creation Tour',
            data: { tourId: 'strategy-creation' }
          },
          {
            type: 'navigate',
            label: 'Go to Strategy Development',
            data: { route: '/strategy-development' }
          }
        ];
        break;

      case 'troubleshooting':
        response = `I'm here to help you troubleshoot! To provide the best assistance, I need more details:

**Common Issues:**
- Connection problems with exchanges or data providers
- Strategy execution issues
- Performance or speed problems
- Data feed errors
- Interface or navigation problems

**Quick Diagnostics:**
- Check your internet connection
- Verify API credentials in Settings
- Look for error messages in the system logs
- Try restarting the application

Could you describe the specific problem you're experiencing? Include any error messages you're seeing.`;
        
        confidence = 0.75;
        suggestions = [
          'Check system logs',
          'Verify API connections',
          'Restart application'
        ];
        relatedTopics = ['troubleshooting', 'system-logs', 'api-configuration'];
        actions = [
          {
            type: 'navigate',
            label: 'View System Logs',
            data: { route: '/settings/logs' }
          },
          {
            type: 'navigate',
            label: 'Check API Settings',
            data: { route: '/settings/api' }
          }
        ];
        break;

      case 'navigation_help':
        response = `I can help you navigate the platform! Here's an overview of the main sections:

**Dashboard:** Your central hub for monitoring portfolio and market conditions
**Market Intelligence:** AI-powered market analysis and opportunity detection
**Strategy Development:** Tools for creating and testing trading strategies
**Risk Management:** Risk monitoring and control systems
**Analytics:** Performance analysis and reporting tools
**Settings:** Configuration and preferences

**Navigation Tips:**
- Use the sidebar to switch between sections
- The search function can help you find specific features
- Hover over icons for tooltips and descriptions
- Use keyboard shortcuts for quick navigation

What specific area would you like to explore, or would you prefer to take the welcome tour?`;
        
        confidence = 0.80;
        suggestions = [
          'Take the welcome tour',
          'Explore specific sections',
          'Learn keyboard shortcuts'
        ];
        relatedTopics = ['dashboard-overview', 'navigation', 'interface-basics'];
        actions = [
          {
            type: 'start_tour',
            label: 'Start Welcome Tour',
            data: { tourId: 'first-time-user' }
          },
          {
            type: 'open_help',
            label: 'Interface Guide',
            data: { topicId: 'dashboard-overview' }
          }
        ];
        break;

      default:
        // Search help topics for relevant information
        const searchResults = helpService.searchHelpTopics(query);
        
        if (searchResults.length > 0) {
          const topResult = searchResults[0];
          response = `I found some relevant information about "${query}":

${topResult.content.substring(0, 300)}...

This topic covers: ${topResult.tags.join(', ')}

Would you like me to open the full help topic or provide more specific assistance?`;
          
          confidence = 0.65;
          suggestions = [
            'Open full help topic',
            'Get more specific help',
            'Search for related topics'
          ];
          relatedTopics = [topResult.id, ...topResult.relatedTopics];
          actions = [
            {
              type: 'open_help',
              label: `Open "${topResult.title}"`,
              data: { topicId: topResult.id }
            }
          ];
        } else {
          response = `I'd be happy to help! I can assist you with:

- **Creating and managing trading strategies**
- **Understanding platform features and navigation**
- **Troubleshooting technical issues**
- **Risk management and portfolio optimization**
- **Market analysis and data interpretation**

Could you provide more details about what you're looking for? For example:
- "How do I create a trading strategy?"
- "I'm having connection problems"
- "How do I set up risk management?"
- "Where can I find market analysis tools?"`;
          
          confidence = 0.50;
          suggestions = [
            'Ask about strategy creation',
            'Get help with troubleshooting',
            'Learn about risk management',
            'Explore market analysis tools'
          ];
          relatedTopics = ['getting-started', 'faq', 'platform-overview'];
          actions = [
            {
              type: 'start_tour',
              label: 'Take Welcome Tour',
              data: { tourId: 'first-time-user' }
            },
            {
              type: 'open_help',
              label: 'Browse Help Topics',
              data: { section: 'topics' }
            }
          ];
        }
        break;
    }

    return {
      id: `response_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      query,
      response,
      confidence,
      suggestions,
      relatedTopics,
      actions,
      timestamp: new Date()
    };
  }

  getConversationHistory(sessionId: string): ConversationHistory | null {
    return this.conversations.get(sessionId) || null;
  }

  clearConversation(sessionId: string): void {
    this.conversations.delete(sessionId);
  }

  getSuggestions(partialQuery: string): string[] {
    const suggestions: string[] = [];
    const query = partialQuery.toLowerCase();

    // Add suggestions based on common queries
    for (const [key] of this.commonQueries) {
      if (key.includes(query) || query.includes(key.split(' ')[0])) {
        suggestions.push(key);
      }
    }

    // Add suggestions based on help topics
    const helpTopics = helpService.searchHelpTopics(partialQuery);
    helpTopics.slice(0, 3).forEach(topic => {
      suggestions.push(topic.title);
    });

    return suggestions.slice(0, 5);
  }

  // Analytics and improvement
  recordFeedback(responseId: string, feedback: 'helpful' | 'not_helpful', comment?: string): void {
    // Record feedback for improving responses
    console.log(`Feedback for ${responseId}: ${feedback}`, comment);
  }

  getPopularQueries(): Array<{ query: string; count: number }> {
    // Return popular queries for analytics
    return Array.from(this.commonQueries.keys()).map(query => ({
      query,
      count: Math.floor(Math.random() * 100) // Placeholder
    }));
  }
}

// Create singleton instance
export const aiAssistanceService = new AIAssistanceService();

export default aiAssistanceService;