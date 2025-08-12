/**
 * Help Center Component
 * Main interface for accessing help topics, guided tours, and documentation
 */

import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { helpService, HelpTopic, GuidedTour } from '../../services/helpService';

interface HelpCenterProps {
  isOpen: boolean;
  onClose: () => void;
  initialTopic?: string;
}

export const HelpCenter: React.FC<HelpCenterProps> = ({
  isOpen,
  onClose,
  initialTopic
}) => {
  const [activeTab, setActiveTab] = useState<'search' | 'topics' | 'tours' | 'getting-started'>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<HelpTopic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<HelpTopic | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);
  const [availableTours, setAvailableTours] = useState<GuidedTour[]>([]);
  const [recommendedTours, setRecommendedTours] = useState<GuidedTour[]>([]);

  useEffect(() => {
    if (isOpen) {
      setCategories(helpService.getCategories());
      setAvailableTours(helpService.getAvailableTours());
      setRecommendedTours(helpService.getRecommendedTours());

      // Load initial topic if provided
      if (initialTopic) {
        const topic = helpService.getHelpTopic(initialTopic);
        if (topic) {
          setSelectedTopic(topic);
          setActiveTab('topics');
        }
      }
    }
  }, [isOpen, initialTopic]);

  useEffect(() => {
    if (searchQuery.trim()) {
      const results = helpService.searchHelpTopics(searchQuery, selectedCategory);
      setSearchResults(results);
    } else {
      setSearchResults([]);
    }
  }, [searchQuery, selectedCategory]);

  const handleStartTour = (tourId: string) => {
    if (helpService.startTour(tourId)) {
      onClose();
      // Tour will be handled by the TourGuide component
    }
  };

  const renderSearchTab = () => (
    <div className="space-y-4">
      <div className="flex space-x-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search help topics..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Categories</option>
          {categories.map(category => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
      </div>

      {searchQuery && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold">Search Results ({searchResults.length})</h3>
          {searchResults.length === 0 ? (
            <p className="text-gray-500">No results found for "{searchQuery}"</p>
          ) : (
            <div className="space-y-2">
              {searchResults.map(topic => (
                <Card key={topic.id} className="p-4 cursor-pointer hover:bg-gray-50" onClick={() => setSelectedTopic(topic)}>
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-blue-600">{topic.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        {topic.content.substring(0, 150)}...
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded">{topic.category}</span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          topic.difficulty === 'beginner' ? 'bg-green-100 text-green-800' :
                          topic.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {topic.difficulty}
                        </span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {!searchQuery && (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-600 mb-2">Search Help Topics</h3>
          <p className="text-gray-500">Enter a search term to find relevant help topics and guides.</p>
        </div>
      )}
    </div>
  );

  const renderTopicsTab = () => (
    <div className="space-y-4">
      <div className="flex space-x-4">
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Categories</option>
          {categories.map(category => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {categories.map(category => {
          if (selectedCategory && selectedCategory !== category) return null;
          
          const categoryTopics = helpService.getHelpTopicsByCategory(category);
          
          return (
            <div key={category} className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-800">{category}</h3>
              <div className="space-y-2">
                {categoryTopics.map(topic => (
                  <Card key={topic.id} className="p-4 cursor-pointer hover:bg-gray-50" onClick={() => setSelectedTopic(topic)}>
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold text-blue-600">{topic.title}</h4>
                        <div className="flex items-center space-x-2 mt-2">
                          <span className={`text-xs px-2 py-1 rounded ${
                            topic.difficulty === 'beginner' ? 'bg-green-100 text-green-800' :
                            topic.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {topic.difficulty}
                          </span>
                          {topic.tags.map(tag => (
                            <span key={tag} className="text-xs bg-gray-100 px-2 py-1 rounded">{tag}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderToursTab = () => {
    const completionStats = helpService.getCompletionStats();
    
    return (
      <div className="space-y-6">
        {/* Progress Overview */}
        <Card className="p-4">
          <h3 className="text-lg font-semibold mb-4">Your Progress</h3>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
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
            <div className="text-2xl font-bold text-blue-600">
              {Math.round(completionStats.completionRate)}%
            </div>
          </div>
        </Card>

        {/* Recommended Tours */}
        {recommendedTours.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Recommended for You</h3>
            <div className="space-y-2">
              {recommendedTours.map(tour => (
                <Card key={tour.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-blue-600">{tour.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{tour.description}</p>
                      <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded">{tour.category}</span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          tour.difficulty === 'beginner' ? 'bg-green-100 text-green-800' :
                          tour.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {tour.difficulty}
                        </span>
                        <span className="text-xs text-gray-500">~{tour.estimatedTime} min</span>
                      </div>
                    </div>
                    <Button
                      onClick={() => handleStartTour(tour.id)}
                      size="sm"
                      className="ml-4"
                    >
                      Start Tour
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* All Tours */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">All Tours</h3>
          <div className="space-y-2">
            {availableTours.map(tour => {
              const isCompleted = helpService.getCompletionStats().completedTours > 0; // Simplified check
              
              return (
                <Card key={tour.id} className={`p-4 ${isCompleted ? 'bg-green-50' : ''}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-semibold text-blue-600">{tour.title}</h4>
                        {isCompleted && (
                          <span className="text-green-600">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{tour.description}</p>
                      <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded">{tour.category}</span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          tour.difficulty === 'beginner' ? 'bg-green-100 text-green-800' :
                          tour.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {tour.difficulty}
                        </span>
                        <span className="text-xs text-gray-500">~{tour.estimatedTime} min</span>
                        <span className="text-xs text-gray-500">{tour.steps.length} steps</span>
                      </div>
                      {tour.prerequisites && tour.prerequisites.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs text-gray-500">
                            Prerequisites: {tour.prerequisites.join(', ')}
                          </span>
                        </div>
                      )}
                    </div>
                    <Button
                      onClick={() => handleStartTour(tour.id)}
                      size="sm"
                      variant={isCompleted ? 'outline' : 'primary'}
                      className="ml-4"
                    >
                      {isCompleted ? 'Retake' : 'Start Tour'}
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const renderGettingStartedTab = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome to AI Trading Interface!</h2>
        <p className="text-gray-600 mb-6">
          Get started quickly with these essential resources and guided tours.
        </p>
      </div>

      {/* Quick Start Actions */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Quick Start</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Button
            onClick={() => handleStartTour('first-time-user')}
            className="p-4 h-auto flex flex-col items-center space-y-2"
          >
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>Take the Welcome Tour</span>
          </Button>
          
          <Button
            onClick={() => {
              const topic = helpService.getHelpTopic('getting-started');
              if (topic) setSelectedTopic(topic);
            }}
            variant="outline"
            className="p-4 h-auto flex flex-col items-center space-y-2"
          >
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span>Read Getting Started Guide</span>
          </Button>
        </div>
      </Card>

      {/* Essential Topics */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Essential Topics</h3>
        <div className="space-y-3">
          {['dashboard-overview', 'strategy-development'].map(topicId => {
            const topic = helpService.getHelpTopic(topicId);
            if (!topic) return null;
            
            return (
              <div
                key={topicId}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                onClick={() => setSelectedTopic(topic)}
              >
                <div>
                  <h4 className="font-medium">{topic.title}</h4>
                  <p className="text-sm text-gray-600">{topic.category}</p>
                </div>
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Next Steps */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Next Steps</h3>
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">1</div>
            <div>
              <h4 className="font-medium">Complete the Welcome Tour</h4>
              <p className="text-sm text-gray-600">Get familiar with the interface and key features</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">2</div>
            <div>
              <h4 className="font-medium">Connect to HaasOnline</h4>
              <p className="text-sm text-gray-600">Configure your trading bot connection in Settings</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">3</div>
            <div>
              <h4 className="font-medium">Create Your First Strategy</h4>
              <p className="text-sm text-gray-600">Use the Strategy Development tools to build a trading strategy</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );

  const renderTopicDetail = () => {
    if (!selectedTopic) return null;

    const relatedTopics = helpService.getRelatedTopics(selectedTopic.id);

    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button
            onClick={() => setSelectedTopic(null)}
            variant="outline"
            size="sm"
          >
            ← Back
          </Button>
          <div>
            <h2 className="text-xl font-bold">{selectedTopic.title}</h2>
            <div className="flex items-center space-x-2 mt-1">
              <span className="text-sm bg-gray-100 px-2 py-1 rounded">{selectedTopic.category}</span>
              <span className={`text-sm px-2 py-1 rounded ${
                selectedTopic.difficulty === 'beginner' ? 'bg-green-100 text-green-800' :
                selectedTopic.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {selectedTopic.difficulty}
              </span>
            </div>
          </div>
        </div>

        <Card className="p-6">
          <div className="prose max-w-none">
            <div dangerouslySetInnerHTML={{ __html: selectedTopic.content.replace(/\n/g, '<br>') }} />
          </div>
        </Card>

        {selectedTopic.videoUrl && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Video Tutorial</h3>
            <div className="aspect-w-16 aspect-h-9">
              <iframe
                src={selectedTopic.videoUrl}
                title={`${selectedTopic.title} Video Tutorial`}
                className="w-full h-64 rounded-lg"
                allowFullScreen
              />
            </div>
          </Card>
        )}

        {selectedTopic.externalLinks && selectedTopic.externalLinks.length > 0 && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Additional Resources</h3>
            <div className="space-y-2">
              {selectedTopic.externalLinks.map((link, index) => (
                <a
                  key={index}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 text-blue-600 hover:text-blue-800"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  <span>{link.title}</span>
                </a>
              ))}
            </div>
          </Card>
        )}

        {relatedTopics.length > 0 && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Related Topics</h3>
            <div className="space-y-2">
              {relatedTopics.map(topic => (
                <div
                  key={topic.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                  onClick={() => setSelectedTopic(topic)}
                >
                  <div>
                    <h4 className="font-medium">{topic.title}</h4>
                    <p className="text-sm text-gray-600">{topic.category}</p>
                  </div>
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <div className="flex flex-col h-full max-h-[80vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold">Help Center</h1>
          <Button onClick={onClose} variant="outline" size="sm">
            Close
          </Button>
        </div>

        {selectedTopic ? (
          <div className="flex-1 overflow-y-auto p-6">
            {renderTopicDetail()}
          </div>
        ) : (
          <>
            {/* Tabs */}
            <div className="flex border-b border-gray-200">
              {[
                { key: 'getting-started', label: 'Getting Started' },
                { key: 'search', label: 'Search' },
                { key: 'topics', label: 'Browse Topics' },
                { key: 'tours', label: 'Guided Tours' }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`px-6 py-3 text-sm font-medium ${
                    activeTab === tab.key
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === 'search' && renderSearchTab()}
              {activeTab === 'topics' && renderTopicsTab()}
              {activeTab === 'tours' && renderToursTab()}
              {activeTab === 'getting-started' && renderGettingStartedTab()}
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};

export default HelpCenter;