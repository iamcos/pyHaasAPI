import React, { useState, useEffect } from 'react';
import { VisualScriptEditor } from './VisualScriptEditor';
import { StrategyTranslationModal } from './StrategyTranslationModal';
import { StrategyVersionControl } from './StrategyVersionControl';
import { useStrategyStore } from '../../stores/strategyStore';
import { HaasScriptStrategy, ValidationError as HaasScriptValidationError, StrategyTemplate } from '../../types/strategy';
import { TranslationResult } from '../../types/translation';
import { StrategyVersion } from '../../types/versionControl';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Modal } from '../ui/Modal';

export const StrategyDevelopmentStudio: React.FC = () => {
  const {
    strategies,
    currentStrategy,
    templates,
    validationErrors,
    createStrategy,
    updateStrategy,
    setCurrentStrategy,
    duplicateStrategy,
    deleteStrategy,
    createFromTemplate,
    exportStrategy,
    importStrategy,
    setValidationErrors
  } = useStrategyStore();

  const [showNewStrategyModal, setShowNewStrategyModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showTranslationModal, setShowTranslationModal] = useState(false);
  const [newStrategyName, setNewStrategyName] = useState('');
  const [newStrategyDescription, setNewStrategyDescription] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<StrategyTemplate | null>(null);
  const [importData, setImportData] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showVersionControl, setShowVersionControl] = useState(false);

  // Auto-select first strategy if none selected
  useEffect(() => {
    if (!currentStrategy && strategies.length > 0) {
      setCurrentStrategy(strategies[0]);
    }
  }, [strategies, currentStrategy, setCurrentStrategy]);

  const handleCreateStrategy = () => {
    if (newStrategyName.trim()) {
      createStrategy(newStrategyName.trim(), newStrategyDescription.trim());
      setNewStrategyName('');
      setNewStrategyDescription('');
      setShowNewStrategyModal(false);
    }
  };

  const handleCreateFromTemplate = () => {
    if (selectedTemplate && newStrategyName.trim()) {
      createFromTemplate(selectedTemplate.id, newStrategyName.trim());
      setNewStrategyName('');
      setSelectedTemplate(null);
      setShowTemplateModal(false);
    }
  };

  const handleImportStrategy = () => {
    if (importData.trim()) {
      const imported = importStrategy(importData.trim());
      if (imported) {
        setImportData('');
        setShowImportModal(false);
      } else {
        alert('Failed to import strategy. Please check the format.');
      }
    }
  };

  const handleTranslationComplete = (result: TranslationResult) => {
    // Translation result is already handled by the modal
    // The new strategy is created automatically
    console.log('Translation completed:', result);
  };

  const handleVersionChange = (version: StrategyVersion) => {
    // Update the current strategy with the version data
    if (currentStrategy) {
      updateStrategy(currentStrategy.id, {
        code: version.code,
        parameters: version.parameters,
        version: version.version
      });
    }
  };

  const handleExportStrategy = (strategy: HaasScriptStrategy) => {
    const exported = exportStrategy(strategy.id);
    if (exported) {
      // Create download link
      const blob = new Blob([exported], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${strategy.name.replace(/\s+/g, '_')}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const handleDuplicateStrategy = (strategy: HaasScriptStrategy) => {
    const newName = prompt('Enter name for duplicated strategy:', `${strategy.name} (Copy)`);
    if (newName) {
      duplicateStrategy(strategy.id, newName);
    }
  };

  const handleDeleteStrategy = (strategy: HaasScriptStrategy) => {
    if (confirm(`Are you sure you want to delete "${strategy.name}"?`)) {
      deleteStrategy(strategy.id);
    }
  };

  const renderSidebar = () => (
    <div className={`bg-white border-r border-gray-200 transition-all duration-300 ${
      sidebarCollapsed ? 'w-12' : 'w-80'
    }`}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!sidebarCollapsed && (
            <h2 className="text-lg font-semibold">Strategies</h2>
          )}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            {sidebarCollapsed ? '→' : '←'}
          </Button>
        </div>
        
        {!sidebarCollapsed && (
          <div className="mt-4 space-y-2">
            <Button
              onClick={() => setShowNewStrategyModal(true)}
              className="w-full"
            >
              New Strategy
            </Button>
            <div className="grid grid-cols-3 gap-2">
              <Button
                variant="secondary"
                onClick={() => setShowTemplateModal(true)}
                size="sm"
              >
                Template
              </Button>
              <Button
                variant="secondary"
                onClick={() => setShowTranslationModal(true)}
                size="sm"
              >
                Translate
              </Button>
              <Button
                variant="secondary"
                onClick={() => setShowImportModal(true)}
                size="sm"
              >
                Import
              </Button>
            </div>
          </div>
        )}
      </div>

      {!sidebarCollapsed && (
        <div className="p-4 overflow-y-auto">
          {strategies.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p>No strategies yet.</p>
              <p className="text-sm">Create your first strategy to get started.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {strategies.map((strategy) => (
                <Card
                  key={strategy.id}
                  className={`p-3 cursor-pointer transition-colors ${
                    currentStrategy?.id === strategy.id
                      ? 'bg-blue-50 border-blue-200'
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setCurrentStrategy(strategy)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm truncate">{strategy.name}</h3>
                      {strategy.description && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {strategy.description}
                        </p>
                      )}
                      <div className="flex items-center mt-2 space-x-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                          strategy.isValid
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {strategy.isValid ? '✓ Valid' : '✗ Invalid'}
                        </span>
                        <span className="text-xs text-gray-400">
                          v{strategy.version}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex flex-col space-y-1 ml-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleExportStrategy(strategy);
                        }}
                        title="Export Strategy"
                      >
                        ↓
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDuplicateStrategy(strategy);
                        }}
                        title="Duplicate Strategy"
                      >
                        ⧉
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteStrategy(strategy);
                        }}
                        title="Delete Strategy"
                        className="text-red-600 hover:text-red-700"
                      >
                        ✗
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderNewStrategyModal = () => (
    <Modal
      open={showNewStrategyModal}
      onClose={() => setShowNewStrategyModal(false)}
      title="Create New Strategy"
    >
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Strategy Name *
          </label>
          <input
            type="text"
            value={newStrategyName}
            onChange={(e) => setNewStrategyName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter strategy name"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={newStrategyDescription}
            onChange={(e) => setNewStrategyDescription(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Describe your strategy (optional)"
          />
        </div>
        
        <div className="flex justify-end space-x-2 pt-4">
          <Button
            variant="secondary"
            onClick={() => setShowNewStrategyModal(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreateStrategy}
            disabled={!newStrategyName.trim()}
          >
            Create Strategy
          </Button>
        </div>
      </div>
    </Modal>
  );

  const renderTemplateModal = () => (
    <Modal
      open={showTemplateModal}
      onClose={() => setShowTemplateModal(false)}
      title="Create from Template"
    >
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Template
          </label>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {templates.map((template) => (
              <Card
                key={template.id}
                className={`p-3 cursor-pointer transition-colors ${
                  selectedTemplate?.id === template.id
                    ? 'bg-blue-50 border-blue-200'
                    : 'hover:bg-gray-50'
                }`}
                onClick={() => setSelectedTemplate(template)}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-sm">{template.name}</h4>
                    <p className="text-xs text-gray-500 mt-1">{template.description}</p>
                    <div className="flex items-center mt-2 space-x-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                        template.difficulty === 'beginner'
                          ? 'bg-green-100 text-green-800'
                          : template.difficulty === 'intermediate'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {template.difficulty}
                      </span>
                      <span className="text-xs text-gray-400">{template.category}</span>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
        
        {selectedTemplate && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Strategy Name *
            </label>
            <input
              type="text"
              value={newStrategyName}
              onChange={(e) => setNewStrategyName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter strategy name"
            />
          </div>
        )}
        
        <div className="flex justify-end space-x-2 pt-4">
          <Button
            variant="secondary"
            onClick={() => setShowTemplateModal(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreateFromTemplate}
            disabled={!selectedTemplate || !newStrategyName.trim()}
          >
            Create from Template
          </Button>
        </div>
      </div>
    </Modal>
  );

  const renderImportModal = () => (
    <Modal
      open={showImportModal}
      onClose={() => setShowImportModal(false)}
      title="Import Strategy"
    >
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Strategy JSON Data
          </label>
          <textarea
            value={importData}
            onChange={(e) => setImportData(e.target.value)}
            rows={10}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            placeholder="Paste exported strategy JSON here..."
          />
        </div>
        
        <div className="flex justify-end space-x-2 pt-4">
          <Button
            variant="secondary"
            onClick={() => setShowImportModal(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={handleImportStrategy}
            disabled={!importData.trim()}
          >
            Import Strategy
          </Button>
        </div>
      </div>
    </Modal>
  );

  return (
    <div className="flex h-full bg-gray-50">
      {/* Sidebar */}
      {renderSidebar()}
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {currentStrategy ? (
          <>
            {/* Header */}
            <div className="bg-white border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-xl font-semibold">{currentStrategy.name}</h1>
                  {currentStrategy.description && (
                    <p className="text-gray-600 text-sm mt-1">{currentStrategy.description}</p>
                  )}
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${
                    validationErrors.length === 0
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {validationErrors.length === 0 ? '✓ Valid' : `${validationErrors.length} Issues`}
                  </span>
                  
                  <Button
                    variant="secondary"
                    onClick={() => setShowVersionControl(!showVersionControl)}
                  >
                    {showVersionControl ? 'Hide' : 'Show'} Version Control
                  </Button>
                  
                  <Button
                    variant="secondary"
                    onClick={() => handleExportStrategy(currentStrategy)}
                  >
                    Export
                  </Button>
                </div>
              </div>
            </div>
            
            {/* Editor and Version Control */}
            <div className="flex-1 flex">
              <div className="flex-1">
                <VisualScriptEditor
                  strategy={currentStrategy}
                  onStrategyChange={(updatedStrategy) => {
                    updateStrategy(currentStrategy.id, updatedStrategy);
                  }}
                  onValidationChange={setValidationErrors}
                />
              </div>
              
              {showVersionControl && (
                <div className="w-96 border-l border-gray-200 bg-white">
                  <div className="p-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold">Version Control</h3>
                  </div>
                  <div className="p-4 overflow-y-auto" style={{ height: 'calc(100vh - 200px)' }}>
                    <StrategyVersionControl
                      strategy={currentStrategy}
                      onVersionChange={handleVersionChange}
                    />
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Strategy Development Studio
              </h2>
              <p className="text-gray-600 mb-8">
                Create and edit HaasScript trading strategies with visual tools and AI assistance.
              </p>
              <div className="flex flex-wrap gap-4 justify-center">
                <Button onClick={() => setShowNewStrategyModal(true)}>
                  Create New Strategy
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setShowTemplateModal(true)}
                >
                  Use Template
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setShowTranslationModal(true)}
                >
                  Translate External Strategy
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Modals */}
      {renderNewStrategyModal()}
      {renderTemplateModal()}
      {renderImportModal()}
      
      <StrategyTranslationModal
        open={showTranslationModal}
        onClose={() => setShowTranslationModal(false)}
        onTranslationComplete={handleTranslationComplete}
      />
    </div>
  );
};