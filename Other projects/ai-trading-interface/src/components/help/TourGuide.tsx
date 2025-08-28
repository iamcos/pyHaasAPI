/**
 * Tour Guide Component
 * Handles guided tours with step-by-step instructions and highlighting
 */

import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../ui/Button';
import { helpService, GuidedTour, TourStep } from '../../services/helpService';

interface TourGuideProps {
  isActive: boolean;
  onComplete: () => void;
  onExit: () => void;
}

export const TourGuide: React.FC<TourGuideProps> = ({
  isActive,
  onComplete,
  onExit
}) => {
  const [currentTourData, setCurrentTourData] = useState<{
    tour: GuidedTour;
    step: TourStep;
    stepIndex: number;
  } | null>(null);
  const [highlightElement, setHighlightElement] = useState<Element | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const overlayRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isActive) {
      const tourData = helpService.getCurrentTourStep();
      setCurrentTourData(tourData);
      
      if (tourData) {
        highlightTargetElement(tourData.step);
      }
    } else {
      setCurrentTourData(null);
      setHighlightElement(null);
    }
  }, [isActive]);

  useEffect(() => {
    if (currentTourData) {
      highlightTargetElement(currentTourData.step);
    }
  }, [currentTourData]);

  useEffect(() => {
    if (highlightElement && tooltipRef.current) {
      updateTooltipPosition();
    }
  }, [highlightElement, currentTourData]);

  const highlightTargetElement = (step: TourStep) => {
    // Remove previous highlights
    document.querySelectorAll('.tour-highlight').forEach(el => {
      el.classList.remove('tour-highlight');
    });

    // Find target element
    let targetElement: Element | null = null;
    
    if (step.target === 'body') {
      targetElement = document.body;
    } else {
      targetElement = document.querySelector(step.target);
    }

    if (targetElement) {
      setHighlightElement(targetElement);
      
      // Add highlight class
      if (step.target !== 'body') {
        targetElement.classList.add('tour-highlight');
      }

      // Scroll element into view
      if (step.target !== 'body') {
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
          inline: 'center'
        });
      }

      // Trigger action if specified
      if (step.action && step.target !== 'body') {
        setTimeout(() => {
          switch (step.action) {
            case 'click':
              // Don't actually click, just show the user where to click
              break;
            case 'hover':
              targetElement?.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
              break;
            case 'focus':
              if (targetElement instanceof HTMLElement) {
                targetElement.focus();
              }
              break;
          }
        }, 500);
      }
    } else {
      console.warn(`Tour target not found: ${step.target}`);
      setHighlightElement(null);
    }
  };

  const updateTooltipPosition = () => {
    if (!highlightElement || !tooltipRef.current || !currentTourData) return;

    const elementRect = highlightElement.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    let x = 0;
    let y = 0;

    switch (currentTourData.step.position) {
      case 'top':
        x = elementRect.left + elementRect.width / 2 - tooltipRect.width / 2;
        y = elementRect.top - tooltipRect.height - 10;
        break;
      case 'bottom':
        x = elementRect.left + elementRect.width / 2 - tooltipRect.width / 2;
        y = elementRect.bottom + 10;
        break;
      case 'left':
        x = elementRect.left - tooltipRect.width - 10;
        y = elementRect.top + elementRect.height / 2 - tooltipRect.height / 2;
        break;
      case 'right':
        x = elementRect.right + 10;
        y = elementRect.top + elementRect.height / 2 - tooltipRect.height / 2;
        break;
      case 'center':
        x = viewportWidth / 2 - tooltipRect.width / 2;
        y = viewportHeight / 2 - tooltipRect.height / 2;
        break;
    }

    // Ensure tooltip stays within viewport
    x = Math.max(10, Math.min(x, viewportWidth - tooltipRect.width - 10));
    y = Math.max(10, Math.min(y, viewportHeight - tooltipRect.height - 10));

    setTooltipPosition({ x, y });
  };

  const handleNext = () => {
    const hasNext = helpService.nextTourStep();
    if (hasNext) {
      const tourData = helpService.getCurrentTourStep();
      setCurrentTourData(tourData);
    } else {
      // Tour completed
      onComplete();
    }
  };

  const handlePrevious = () => {
    const hasPrevious = helpService.previousTourStep();
    if (hasPrevious) {
      const tourData = helpService.getCurrentTourStep();
      setCurrentTourData(tourData);
    }
  };

  const handleSkip = () => {
    const canSkip = helpService.skipTourStep();
    if (canSkip) {
      const tourData = helpService.getCurrentTourStep();
      setCurrentTourData(tourData);
    }
  };

  const handleExit = () => {
    helpService.exitTour();
    
    // Remove highlights
    document.querySelectorAll('.tour-highlight').forEach(el => {
      el.classList.remove('tour-highlight');
    });
    
    onExit();
  };

  if (!isActive || !currentTourData) {
    return null;
  }

  const { tour, step, stepIndex } = currentTourData;
  const progress = ((stepIndex + 1) / tour.steps.length) * 100;

  return (
    <>
      {/* Overlay */}
      <div
        ref={overlayRef}
        className="fixed inset-0 z-50 pointer-events-none"
        style={{
          background: step.target === 'body' 
            ? 'rgba(0, 0, 0, 0.5)' 
            : `radial-gradient(circle at ${highlightElement ? 
                highlightElement.getBoundingClientRect().left + highlightElement.getBoundingClientRect().width / 2 : 0}px ${highlightElement ? 
                highlightElement.getBoundingClientRect().top + highlightElement.getBoundingClientRect().height / 2 : 0}px, 
                transparent ${highlightElement ? Math.max(highlightElement.getBoundingClientRect().width, highlightElement.getBoundingClientRect().height) / 2 + 10 : 0}px, 
                rgba(0, 0, 0, 0.5) ${highlightElement ? Math.max(highlightElement.getBoundingClientRect().width, highlightElement.getBoundingClientRect().height) / 2 + 20 : 0}px)`
        }}
      />

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="fixed z-50 pointer-events-auto"
        style={{
          left: tooltipPosition.x,
          top: tooltipPosition.y,
          maxWidth: '400px'
        }}
      >
        <div className="bg-white rounded-lg shadow-xl border border-gray-200 p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-semibold text-gray-800">{step.title}</h3>
              {step.optional && (
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">Optional</span>
              )}
            </div>
            <button
              onClick={handleExit}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>{tour.title}</span>
              <span>{stepIndex + 1} of {tour.steps.length}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Content */}
          <div className="mb-6">
            <p className="text-gray-700 leading-relaxed">{step.content}</p>
            
            {step.action && (
              <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm text-blue-800">
                    {step.action === 'click' && 'Click on the highlighted element to continue'}
                    {step.action === 'hover' && 'Hover over the highlighted element'}
                    {step.action === 'focus' && 'Focus on the highlighted element'}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <div className="flex space-x-2">
              {stepIndex > 0 && (
                <Button
                  onClick={handlePrevious}
                  variant="outline"
                  size="sm"
                >
                  Previous
                </Button>
              )}
              
              {step.optional && (
                <Button
                  onClick={handleSkip}
                  variant="outline"
                  size="sm"
                >
                  Skip
                </Button>
              )}
            </div>

            <div className="flex space-x-2">
              <Button
                onClick={handleExit}
                variant="outline"
                size="sm"
              >
                Exit Tour
              </Button>
              
              <Button
                onClick={handleNext}
                size="sm"
              >
                {stepIndex === tour.steps.length - 1 ? 'Complete' : 'Next'}
              </Button>
            </div>
          </div>
        </div>

        {/* Arrow pointing to target */}
        {step.position !== 'center' && (
          <div
            className={`absolute w-3 h-3 bg-white border transform rotate-45 ${
              step.position === 'top' ? '-bottom-1.5 left-1/2 -translate-x-1/2 border-r-0 border-b-0' :
              step.position === 'bottom' ? '-top-1.5 left-1/2 -translate-x-1/2 border-l-0 border-t-0' :
              step.position === 'left' ? '-right-1.5 top-1/2 -translate-y-1/2 border-l-0 border-b-0' :
              step.position === 'right' ? '-left-1.5 top-1/2 -translate-y-1/2 border-r-0 border-t-0' : ''
            }`}
          />
        )}
      </div>

      {/* Global styles for tour highlighting */}
      <style jsx global>{`
        .tour-highlight {
          position: relative;
          z-index: 51;
          box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5), 0 0 0 8px rgba(59, 130, 246, 0.2);
          border-radius: 4px;
          transition: all 0.3s ease;
        }
        
        .tour-highlight::before {
          content: '';
          position: absolute;
          top: -2px;
          left: -2px;
          right: -2px;
          bottom: -2px;
          border: 2px solid #3b82f6;
          border-radius: 6px;
          pointer-events: none;
          animation: tour-pulse 2s infinite;
        }
        
        @keyframes tour-pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
          }
        }
      `}</style>
    </>
  );
};

export default TourGuide;