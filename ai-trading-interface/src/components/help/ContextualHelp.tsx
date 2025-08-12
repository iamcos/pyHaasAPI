/**
 * Contextual Help Component
 * Provides contextual help tooltips and hints based on user actions and component state
 */

import React, { useState, useEffect, useRef } from 'react';
import { helpService } from '../../services/helpService';

interface ContextualHelpProps {
  component: string;
  trigger: string;
  children?: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  className?: string;
}

export const ContextualHelp: React.FC<ContextualHelpProps> = ({
  component,
  trigger,
  children,
  position = 'top',
  delay = 1000,
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [helpContent, setHelpContent] = useState<string | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const help = helpService.getContextualHelp(component, trigger);
    if (help) {
      setHelpContent(help.content);
      
      // Show help after delay
      timeoutRef.current = setTimeout(() => {
        setIsVisible(true);
      }, delay);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [component, trigger, delay]);

  const handleDismiss = () => {
    setIsVisible(false);
    helpService.markHelpViewed(component, trigger);
  };

  const handleLearnMore = () => {
    // Could open help center with related topic
    handleDismiss();
  };

  if (!isVisible || !helpContent) {
    return <>{children}</>;
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {children}
      
      {/* Contextual Help Tooltip */}
      <div className={`absolute z-50 ${getPositionClasses(position)}`}>
        <div className="bg-blue-600 text-white p-4 rounded-lg shadow-lg max-w-sm">
          {/* Arrow */}
          <div className={`absolute ${getArrowClasses(position)}`} />
          
          {/* Content */}
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg className="w-5 h-5 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-sm leading-relaxed">{helpContent}</p>
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-blue-500">
            <button
              onClick={handleLearnMore}
              className="text-xs text-blue-200 hover:text-white underline"
            >
              Learn more
            </button>
            <div className="flex space-x-2">
              <button
                onClick={handleDismiss}
                className="text-xs bg-blue-500 hover:bg-blue-400 px-2 py-1 rounded"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const getPositionClasses = (position: string): string => {
  switch (position) {
    case 'top':
      return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
    case 'bottom':
      return 'top-full left-1/2 transform -translate-x-1/2 mt-2';
    case 'left':
      return 'right-full top-1/2 transform -translate-y-1/2 mr-2';
    case 'right':
      return 'left-full top-1/2 transform -translate-y-1/2 ml-2';
    default:
      return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
  }
};

const getArrowClasses = (position: string): string => {
  switch (position) {
    case 'top':
      return 'top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-blue-600';
    case 'bottom':
      return 'bottom-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-blue-600';
    case 'left':
      return 'left-full top-1/2 transform -translate-y-1/2 w-0 h-0 border-t-4 border-b-4 border-l-4 border-transparent border-l-blue-600';
    case 'right':
      return 'right-full top-1/2 transform -translate-y-1/2 w-0 h-0 border-t-4 border-b-4 border-r-4 border-transparent border-r-blue-600';
    default:
      return 'top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-blue-600';
  }
};

// Hook for triggering contextual help
export const useContextualHelp = (component: string) => {
  const triggerHelp = (trigger: string) => {
    // This would typically be handled by the ContextualHelp component
    // but can be used to programmatically trigger help
    const help = helpService.getContextualHelp(component, trigger);
    return help;
  };

  return { triggerHelp };
};

export default ContextualHelp;