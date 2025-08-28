import React, { useState, useCallback } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { strategyTranslator } from '../../services/strategyTranslator';
import { 
  ExternalStrategy, 
  TranslationResult, 
  StrategyTranslationConfig,
  TranslationStep,
  OptimizationSuggestion 
} from '../../types/translation';
import { useStrategyStore } from '../../stores/strategyStore';

interface StrategyTranslationModalProps {
  open: boolean;
  onClose: () => void;
  onTranslationComplete: (result: TranslationResult) => void;
}

export const StrategyTranslationModal: React.FC<StrategyTranslationModalProps> = ({
  open,
  onClose,
  onTranslationComplete
}) => {
  const { createStrategy } = useStrategyStore();
  
  const [sourceCode, setSourceCode] = useState('');
  const [sourceFormat, setSourceFormat] = useState<ExternalStrategy['sourceFormat']>('pine_script');
  const [strategyName, setStrategyName] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationResult, setTranslationResult] = useState<TranslationResult | null>(null);
  const [showChainOfThought, setShowChainOfThought] = useState(false);
  const [config, setConfig] = useState<StrategyTranslationConfig>({
    sourceFormat: 'pine_script',
    targetOptimizations: ['performance', 'readability', 'haas_best_practices'],
    preserveComments: true,
    generateDocumentation: true,
    includeOriginalCode: true,
    validationLevel: 'comprehensive',
    aiAssistance: true
  });

  const handleTranslate = useCallback(async () => {
    if (!sourceCode.trim() || !strategyName.trim()) {
      alert('Please provide both source code and strategy name');
      return;
    }

    setIsTranslating(true);
    setTranslationResult(null);

    try {
      const result = await strategyTranslator.translateStrategy(
        sourceCode,
        sourceFormat,
        { ...config, sourceFormat },
        strategyName
      );

      setTranslationResult(result);
    } catch (error) {
      console.error('Translation failed:', error);
      alert('Translation failed. Please check the console for details.');
    } finally {
      setIsTranslating(false);
    }
  }, [sourceCode, sourceFormat, strategyName, config]);

  const handleAcceptTranslation = useCallback(() => {
    if (!translationResult || !translationResult.success) return;

    // Create a new strategy with the translated code
    const newStrategy = createStrategy(strategyName, 'Translated from external strategy');
    
    // Update the strategy with translated code and parameters
    const updatedStrategy = {
      ...newStrategy,
      code: translationResult.haasScriptCode,
      parameters: translationResult.translatedParameters.map(param => ({
        ...param,
        id: `${newStrategy.id}_${param.name}`
      }))
    };

    onTranslationComplete(translationResult);
    onClose();
  }, [translationResult, strategyName, createStrategy, onTranslationComplete, onClose]);

  const renderSourceFormatSelector = () => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Source Format
      </label>
      <select
        value={sourceFormat}
        onChange={(e) => setSourceFormat(e.target.value as ExternalStrategy['sourceFormat'])}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="pine_script">Pine Script (TradingView)</option>
        <option value="tradingview">TradingView Strategy</option>
        <option value="mql4">MQL4 (MetaTrader 4)</option>
        <option value="mql5">MQL5 (MetaTrader 5)</option>
        <option value="ninjatrader">NinjaTrader</option>
        <option value="custom">Custom Format</option>
      </select>
    </div>
  );

  const renderConfigurationOptions = () => (
    <div className="space-y-4">
      <h4 className="font-medium text-gray-900">Translation Options</h4>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Optimizations
        </label>
        <div className="space-y-2">
          {['performance', 'readability', 'haas_best_practices'].map(opt => (
            <label key={opt} className="flex items-center">
              <input
                type="checkbox"
                checked={config.targetOptimizations.includes(opt as any)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setConfig(prev => ({
                      ...prev,
                      targetOptimizations: [...prev.targetOptimizations, opt as any]
                    }));
                  } else {
                    setConfig(prev => ({
                      ...prev,
                      targetOptimizations: prev.targetOptimizations.filter(o => o !== opt)
                    }));
                  }
                }}
                className="mr-2"
              />
              <span className="text-sm capitalize">{opt.replace('_', ' ')}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.preserveComments}
            onChange={(e) => setConfig(prev => ({ ...prev, preserveComments: e.target.checked }))}
            className="mr-2"
          />
          <span className="text-sm">Preserve Comments</span>
        </label>

        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.generateDocumentation}
            onChange={(e) => setConfig(prev => ({ ...prev, generateDocumentation: e.target.checked }))}
            className="mr-2"
          />
          <span className="text-sm">Generate Documentation</span>
        </label>

        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.includeOriginalCode}
            onChange={(e) => setConfig(prev => ({ ...prev, includeOriginalCode: e.target.checked }))}
            className="mr-2"
          />
          <span className="text-sm">Include Original Code</span>
        </label>

        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.aiAssistance}
            onChange={(e) => setConfig(prev => ({ ...prev, aiAssistance: e.target.checked }))}
            className="mr-2"
          />
          <span className="text-sm">AI Assistance</span>
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Validation Level
        </label>
        <select
          value={config.validationLevel}
          onChange={(e) => setConfig(prev => ({ ...prev, validationLevel: e.target.value as any }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="basic">Basic</option>
          <option value="comprehensive">Comprehensive</option>
          <option value="strict">Strict</option>
        </select>
      </div>
    </div>
  );

  const renderTranslationResult = () => {
    if (!translationResult) return null;

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">Translation Result</h4>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded text-sm ${
              translationResult.success 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {translationResult.success ? 'Success' : 'Failed'}
            </span>
            <span className="text-sm text-gray-500">
              Confidence: {Math.round(translationResult.confidence * 100)}%
            </span>
          </div>
        </div>

        {/* Errors */}
        {translationResult.errors.length > 0 && (
          <Card className="p-3 bg-red-50 border-red-200">
            <h5 className="font-medium text-red-800 mb-2">Errors</h5>
            <div className="space-y-1">
              {translationResult.errors.map((error, index) => (
                <div key={index} className="text-sm text-red-700">
                  {error.line && `Line ${error.line}: `}{error.message}
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Warnings */}
        {translationResult.warnings.length > 0 && (
          <Card className="p-3 bg-yellow-50 border-yellow-200">
            <h5 className="font-medium text-yellow-800 mb-2">Warnings</h5>
            <div className="space-y-1">
              {translationResult.warnings.map((warning, index) => (
                <div key={index} className="text-sm text-yellow-700">
                  {warning.line && `Line ${warning.line}: `}{warning.message}
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Generated Code Preview */}
        {translationResult.success && (
          <div>
            <h5 className="font-medium text-gray-900 mb-2">Generated HaasScript Code</h5>
            <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto max-h-60">
              {translationResult.haasScriptCode}
            </pre>
          </div>
        )}

        {/* Optimization Suggestions */}
        {translationResult.optimizationSuggestions.length > 0 && (
          <div>
            <h5 className="font-medium text-gray-900 mb-2">Optimization Suggestions</h5>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {translationResult.optimizationSuggestions.map((suggestion, index) => (
                <Card key={index} className="p-3 bg-blue-50 border-blue-200">
                  <div className="flex items-start justify-between">
                    <div>
                      <h6 className="font-medium text-blue-900">{suggestion.title}</h6>
                      <p className="text-sm text-blue-700 mt-1">{suggestion.description}</p>
                    </div>
                    <div className="flex space-x-1">
                      <span className={`px-2 py-1 rounded text-xs ${
                        suggestion.impact === 'high' ? 'bg-red-100 text-red-800' :
                        suggestion.impact === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {suggestion.impact}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        suggestion.effort === 'complex' ? 'bg-red-100 text-red-800' :
                        suggestion.effort === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {suggestion.effort}
                      </span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Chain of Thought */}
        <div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowChainOfThought(!showChainOfThought)}
          >
            {showChainOfThought ? 'Hide' : 'Show'} Chain of Thought
          </Button>
          
          {showChainOfThought && (
            <div className="mt-2 space-y-2 max-h-60 overflow-y-auto">
              {translationResult.chainOfThought.map((step, index) => (
                <Card key={index} className="p-3 bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div>
                      <h6 className="font-medium text-gray-900">
                        Step {step.step}: {step.description}
                      </h6>
                      <p className="text-sm text-gray-600 mt-1">{step.reasoning}</p>
                      {step.output && (
                        <pre className="text-xs text-gray-500 mt-2 bg-white p-2 rounded max-h-20 overflow-y-auto">
                          {step.output}
                        </pre>
                      )}
                    </div>
                    <span className="text-xs text-gray-500 capitalize">{step.phase}</span>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Translate External Strategy"
      size="xl"
    >
      <div className="space-y-6">
        {!translationResult ? (
          <>
            {/* Strategy Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Strategy Name *
              </label>
              <input
                type="text"
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter strategy name"
              />
            </div>

            {/* Source Format */}
            {renderSourceFormatSelector()}

            {/* Source Code */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source Code *
              </label>
              <textarea
                value={sourceCode}
                onChange={(e) => setSourceCode(e.target.value)}
                rows={12}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder={`Paste your ${sourceFormat} code here...`}
              />
            </div>

            {/* Configuration */}
            {renderConfigurationOptions()}

            {/* Actions */}
            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <Button
                onClick={handleTranslate}
                disabled={isTranslating || !sourceCode.trim() || !strategyName.trim()}
              >
                {isTranslating ? 'Translating...' : 'Translate Strategy'}
              </Button>
            </div>
          </>
        ) : (
          <>
            {/* Translation Result */}
            {renderTranslationResult()}

            {/* Actions */}
            <div className="flex justify-end space-x-2 pt-4">
              <Button
                variant="secondary"
                onClick={() => {
                  setTranslationResult(null);
                  setSourceCode('');
                  setStrategyName('');
                }}
              >
                Translate Another
              </Button>
              <Button variant="secondary" onClick={onClose}>
                Close
              </Button>
              {translationResult.success && (
                <Button onClick={handleAcceptTranslation}>
                  Accept Translation
                </Button>
              )}
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};