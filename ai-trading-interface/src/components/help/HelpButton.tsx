/**
 * Help Button Component
 * Floating help button that provides quick access to help system
 */

import React, { useState } from 'react';
import { Button } from '../ui/Button';
import HelpCenter from './HelpCenter';
import TourGuide from './TourGuide';
import AIAssistant from './AIAssistant';
import { helpService } from '../../services/helpService';

interface HelpButtonProps {
  className?: string;
  position?: 'fixed' | 'relative';
}

export const HelpButton: React.FC<HelpButtonProps> = ({
  className = '',
  position = 'fixed'
}) => {
  const [isHelpCenterOpen, setIsHelpCenterOpen] = useState(false);
  const [isTourActive, setIsTourActive] = useState(false);
  const [isAIAssistantOpen, setIsAIAssistantOpen] = useState(false);
  const [showQuickMenu, setShowQuickMenu] = useState(false);

  const handleOpenHelpCenter = () => {
    setIsHelpCenterOpen(true);
    setShowQuickMenu(false);
  };

  const handleOpenAIAssistant = () => {
    setIsAIAssistantOpen(true);
    setShowQuickMenu(false);
  };

  const handleStartWelcomeTour = () => {
    if (helpService.startTour('first-time-user')) {
      setIsTourActive(true);
      setShowQuickMenu(false);
    }
  };

  const handleTourComplete = () => {
    setIsTourActive(false);
    // Could show completion message or redirect to next steps
  };

  const handleTourExit = () => {
    setIsTourActive(false);
  };

  const recommendedTours = helpService.getRecommendedTours();
  const completionStats = helpService.getCompletionStats();

  return (
    <>
      {/* Help Button */}
      <div 
        className={`${position === 'fixed' ? 'fixed bottom-6 right-6 z-40' : ''} ${className}`}
        data-tour="help-button"
      >
        <div className="relative">
          {/* Quick Menu */}
          {showQuickMenu && (
            <div className="absolute bottom-16 right-0 bg-white rounded-lg shadow-xl border border-gray-200 p-4 w-80 mb-2">
              <div className="space-y-4">
                {/* Quick Actions */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-800 mb-2">Quick Actions</h3>
                  <div className="space-y-2">
                    <button
                      onClick={handleOpenAIAssistant}
                      className="w-full text-left p-2 hover:bg-gray-50 rounded-lg flex items-center space-x-3"
                    >
                      <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      <div>
                        <div className="text-sm font-medium">Ask AI Assistant</div>
                        <div className="text-xs text-gray-500">Get instant help with any question</div>
                      </div>
                    </button>

                    <button
                      onClick={handleOpenHelpCenter}
                      className="w-full text-left p-2 hover:bg-gray-50 rounded-lg flex items-center space-x-3"
                    >
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                      <div>
                        <div className="text-sm font-medium">Browse Help Topics</div>
                        <div className="text-xs text-gray-500">Search documentation and guides</div>
                      </div>
                    </button>
                    
                    <button
                      onClick={handleStartWelcomeTour}
                      className="w-full text-left p-2 hover:bg-gray-50 rounded-lg flex items-center space-x-3"
                    >
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <div>
                        <div className="text-sm font-medium">Take Welcome Tour</div>
                        <div className="text-xs text-gray-500">Learn the basics in 10 minutes</div>
                      </div>
                    </button>
                  </div>
                </div>

                {/* Progress */}
                {completionStats.totalTours > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-800 mb-2">Your Progress</h3>
                    <div className="flex items-center space-x-3">
                      <div className="flex-1">
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>Tours Completed</span>
                          <span>{completionStats.completedTours}/{completionStats.totalTours}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${completionStats.completionRate}%` }}
                          ></div>
                        </div>
                      </div>
                      <div className="text-sm font-bold text-blue-600">
                        {Math.round(completionStats.completionRate)}%
                      </div>
                    </div>
                  </div>
                )}

                {/* Recommended Tours */}
                {recommendedTours.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-800 mb-2">Recommended</h3>
                    <div className="space-y-1">
                      {recommendedTours.slice(0, 2).map(tour => (
                        <button
                          key={tour.id}
                          onClick={() => {
                            if (helpService.startTour(tour.id)) {
                              setIsTourActive(true);
                              setShowQuickMenu(false);
                            }
                          }}
                          className="w-full text-left p-2 hover:bg-gray-50 rounded-lg"
                        >
                          <div className="text-sm font-medium text-blue-600">{tour.title}</div>
                          <div className="text-xs text-gray-500">~{tour.estimatedTime} min • {tour.difficulty}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Footer */}
                <div className="pt-2 border-t border-gray-100">
                  <button
                    onClick={handleOpenHelpCenter}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    View all help topics →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Main Help Button */}
          <Button
            onClick={() => setShowQuickMenu(!showQuickMenu)}
            className="rounded-full w-14 h-14 shadow-lg hover:shadow-xl transition-all duration-200 bg-blue-600 hover:bg-blue-700"
            title="Help & Support"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </Button>

          {/* Notification Badge */}
          {recommendedTours.length > 0 && (
            <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {recommendedTours.length}
            </div>
          )}
        </div>
      </div>

      {/* Click outside to close menu */}
      {showQuickMenu && (
        <div 
          className="fixed inset-0 z-30" 
          onClick={() => setShowQuickMenu(false)}
        />
      )}

      {/* AI Assistant */}
      <AIAssistant
        isOpen={isAIAssistantOpen}
        onClose={() => setIsAIAssistantOpen(false)}
      />

      {/* Help Center Modal */}
      <HelpCenter
        isOpen={isHelpCenterOpen}
        onClose={() => setIsHelpCenterOpen(false)}
      />

      {/* Tour Guide */}
      <TourGuide
        isActive={isTourActive}
        onComplete={handleTourComplete}
        onExit={handleTourExit}
      />
    </>
  );
};

export default HelpButton;