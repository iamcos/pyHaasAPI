/**
 * AI Assistant Component
 * Interactive AI-powered chat assistant for help and guidance
 */

import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { aiAssistanceService, AssistanceResponse, AssistanceAction } from '../../services/aiAssistanceService';
import { helpService } from '../../services/helpService';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  actions?: AssistanceAction[];
  suggestions?: string[];
}

interface AIAssistantProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}

export const AIAssistant: React.FC<AIAssistantProps> = ({
  isOpen,
  onClose,
  initialQuery
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const sessionId = useRef(Math.random().toString(36).substr(2, 9));

  useEffect(() => {
    if (isOpen) {
      // Add welcome message
      if (messages.length === 0) {
        setMessages([{
          id: 'welcome',
          type: 'assistant',
          content: `Hello! I'm your AI assistant. I can help you with:

• Creating and managing trading strategies
• Understanding platform features
• Troubleshooting issues
• Risk management guidance
• Market analysis questions

What would you like help with today?`,
          timestamp: new Date(),
          suggestions: [
            'How do I create a trading strategy?',
            'I need help with connection issues',
            'How do I set up risk management?',
            'Show me around the platform'
          ]
        }]);
      }

      // Handle initial query
      if (initialQuery && inputValue !== initialQuery) {
        setInputValue(initialQuery);
        handleSendMessage(initialQuery);
      }

      // Focus input
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, initialQuery]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Get suggestions as user types
    if (inputValue.trim().length > 2) {
      const newSuggestions = aiAssistanceService.getSuggestions(inputValue);
      setSuggestions(newSuggestions);
      setShowSuggestions(newSuggestions.length > 0);
    } else {
      setShowSuggestions(false);
    }
  }, [inputValue]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (message?: string) => {
    const query = message || inputValue.trim();
    if (!query) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: query,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setShowSuggestions(false);

    try {
      const response = await aiAssistanceService.getAssistance({
        query,
        context: {
          currentPage: window.location.pathname,
          userAction: 'chat_query'
        },
        sessionId: sessionId.current
      });

      const assistantMessage: Message = {
        id: response.id,
        type: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
        actions: response.actions,
        suggestions: response.suggestions
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        type: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionClick = (action: AssistanceAction) => {
    switch (action.type) {
      case 'navigate':
        // Navigate to specified route
        window.location.hash = action.data.route;
        onClose();
        break;
      
      case 'open_help':
        // Open help center with specific topic
        onClose();
        // This would trigger opening the help center
        break;
      
      case 'start_tour':
        // Start guided tour
        if (helpService.startTour(action.data.tourId)) {
          onClose();
          // Tour will be handled by TourGuide component
        }
        break;
      
      case 'execute_command':
        // Execute specific command
        console.log('Executing command:', action.data.command);
        break;
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
    setShowSuggestions(false);
    handleSendMessage(suggestion);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFeedback = (messageId: string, feedback: 'helpful' | 'not_helpful') => {
    aiAssistanceService.recordFeedback(messageId, feedback);
    // Update UI to show feedback was recorded
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold">AI Assistant</h2>
              <p className="text-sm text-gray-500">Ask me anything about the platform</p>
            </div>
          </div>
          <Button onClick={onClose} variant="outline" size="sm">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3/4 ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                {message.type === 'assistant' && (
                  <div className="flex items-center space-x-2 mb-1">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <span className="text-xs text-gray-500">AI Assistant</span>
                  </div>
                )}
                
                <div className={`rounded-lg p-3 ${
                  message.type === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  
                  {/* Actions */}
                  {message.actions && message.actions.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {message.actions.map((action, index) => (
                        <Button
                          key={index}
                          onClick={() => handleActionClick(action)}
                          size="sm"
                          variant="outline"
                          className="mr-2 mb-2"
                        >
                          {action.label}
                        </Button>
                      ))}
                    </div>
                  )}
                  
                  {/* Suggestions */}
                  {message.suggestions && message.suggestions.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm text-gray-600 mb-2">You might also ask:</p>
                      <div className="space-y-1">
                        {message.suggestions.map((suggestion, index) => (
                          <button
                            key={index}
                            onClick={() => handleSuggestionClick(suggestion)}
                            className="block text-sm text-blue-600 hover:text-blue-800 hover:underline"
                          >
                            "{suggestion}"
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Feedback for assistant messages */}
                {message.type === 'assistant' && message.id !== 'welcome' && (
                  <div className="flex items-center space-x-2 mt-2">
                    <span className="text-xs text-gray-500">Was this helpful?</span>
                    <button
                      onClick={() => handleFeedback(message.id, 'helpful')}
                      className="text-xs text-green-600 hover:text-green-800"
                    >
                      👍 Yes
                    </button>
                    <button
                      onClick={() => handleFeedback(message.id, 'not_helpful')}
                      className="text-xs text-red-600 hover:text-red-800"
                    >
                      👎 No
                    </button>
                  </div>
                )}
                
                <div className="text-xs text-gray-400 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span className="text-sm text-gray-600">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 p-4">
          <div className="relative">
            {/* Suggestions dropdown */}
            {showSuggestions && (
              <div className="absolute bottom-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg mb-2 max-h-40 overflow-y-auto">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 text-sm"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
            
            <div className="flex space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
              <Button
                onClick={() => handleSendMessage()}
                disabled={!inputValue.trim() || isLoading}
                className="px-4"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </Button>
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-2">
            <p className="text-xs text-gray-500">
              Press Enter to send, Shift+Enter for new line
            </p>
            <div className="flex space-x-2">
              <button
                onClick={() => handleSuggestionClick('How do I create a strategy?')}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Strategy Help
              </button>
              <button
                onClick={() => handleSuggestionClick('I need troubleshooting help')}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Troubleshooting
              </button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AIAssistant;