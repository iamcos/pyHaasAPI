import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as monaco from 'monaco-editor';
import { Editor } from '@monaco-editor/react';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';
import { HaasScriptStrategy, ValidationError as HaasScriptValidationError, DragDropComponent } from '../../types/strategy';
import { HaasScriptValidator } from '../../services/haasScriptValidator';
import { registerHaasScriptLanguage } from '../../services/haasScriptLanguage';
import { DRAG_DROP_COMPONENTS, getComponentsByCategory, generateCodeFromComponent } from '../../services/dragDropComponents';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Modal } from '../ui/Modal';

interface VisualScriptEditorProps {
  strategy: HaasScriptStrategy;
  onStrategyChange: (strategy: HaasScriptStrategy) => void;
  onValidationChange: (errors: HaasScriptValidationError[]) => void;
}

interface DroppedComponent {
  id: string;
  componentId: string;
  parameters: Record<string, any>;
  position: { line: number; column: number };
}

export const VisualScriptEditor: React.FC<VisualScriptEditorProps> = ({
  strategy,
  onStrategyChange,
  onValidationChange
}) => {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const [validator] = useState(() => new HaasScriptValidator());
  const [validationErrors, setValidationErrors] = useState<HaasScriptValidationError[]>([]);
  const [droppedComponents, setDroppedComponents] = useState<DroppedComponent[]>([]);
  const [showComponentModal, setShowComponentModal] = useState(false);
  const [selectedComponent, setSelectedComponent] = useState<DragDropComponent | null>(null);
  const [componentParameters, setComponentParameters] = useState<Record<string, any>>({});
  const [draggedComponent, setDraggedComponent] = useState<DragDropComponent | null>(null);

  const componentCategories = getComponentsByCategory();

  // Initialize Monaco Editor with HaasScript language
  useEffect(() => {
    registerHaasScriptLanguage();
  }, []);

  // Validate script on code changes
  const handleCodeChange = useCallback((value: string | undefined) => {
    if (!value) return;

    const updatedStrategy = {
      ...strategy,
      code: value,
      updatedAt: new Date()
    };

    // Validate the script
    const validationResult = validator.validateScript(value);
    const errors = [...validationResult.errors, ...validationResult.warnings];
    
    setValidationErrors(errors);
    onValidationChange(errors);

    // Update strategy with validation results
    updatedStrategy.validationErrors = errors;
    updatedStrategy.isValid = validationResult.isValid;

    onStrategyChange(updatedStrategy);
  }, [strategy, validator, onStrategyChange, onValidationChange]);

  // Handle editor mount
  const handleEditorDidMount = (editor: monaco.editor.IStandaloneCodeEditor) => {
    editorRef.current = editor;

    // Set up validation markers
    const updateMarkers = () => {
      if (validationErrors.length > 0) {
        const markers = validationErrors.map(error => ({
          startLineNumber: error.line,
          startColumn: error.column,
          endLineNumber: error.line,
          endColumn: error.column + 10,
          message: error.message,
          severity: error.severity === 'error' 
            ? monaco.MarkerSeverity.Error 
            : error.severity === 'warning'
            ? monaco.MarkerSeverity.Warning
            : monaco.MarkerSeverity.Info
        }));

        monaco.editor.setModelMarkers(editor.getModel()!, 'haasscript', markers);
      }
    };

    updateMarkers();
  };

  // Handle drag end for components
  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    const { source, destination } = result;

    // If dropped on editor area
    if (destination.droppableId === 'editor-drop-zone') {
      const componentId = result.draggableId;
      const component = DRAG_DROP_COMPONENTS.find(c => c.id === componentId);
      
      if (component) {
        setSelectedComponent(component);
        setDraggedComponent(component);
        
        // Initialize parameters with default values
        const defaultParams: Record<string, any> = {};
        component.parameters.forEach(param => {
          defaultParams[param.name] = param.defaultValue;
        });
        setComponentParameters(defaultParams);
        
        setShowComponentModal(true);
      }
    }
  };

  // Handle component parameter configuration
  const handleComponentConfirm = () => {
    if (!selectedComponent || !editorRef.current) return;

    const instanceId = Date.now().toString();
    const generatedCode = generateCodeFromComponent(
      selectedComponent,
      componentParameters,
      instanceId
    );

    // Insert code at cursor position
    const editor = editorRef.current;
    const position = editor.getPosition();
    const range = new monaco.Range(
      position?.lineNumber || 1,
      position?.column || 1,
      position?.lineNumber || 1,
      position?.column || 1
    );

    editor.executeEdits('insert-component', [{
      range,
      text: generatedCode + '\n'
    }]);

    // Track dropped component
    const droppedComponent: DroppedComponent = {
      id: instanceId,
      componentId: selectedComponent.id,
      parameters: { ...componentParameters },
      position: { line: position?.lineNumber || 1, column: position?.column || 1 }
    };

    setDroppedComponents(prev => [...prev, droppedComponent]);
    setShowComponentModal(false);
    setSelectedComponent(null);
    setComponentParameters({});
  };

  // Render component palette
  const renderComponentPalette = () => (
    <div className="w-80 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto">
      <h3 className="text-lg font-semibold mb-4">Components</h3>
      
      <DragDropContext onDragEnd={handleDragEnd}>
        {Object.entries(componentCategories).map(([category, components]) => (
          <div key={category} className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-2">{category}</h4>
            <Droppable droppableId={category} isDropDisabled>
              {(provided) => (
                <div {...provided.droppableProps} ref={provided.innerRef}>
                  {components.map((component, index) => (
                    <Draggable
                      key={component.id}
                      draggableId={component.id}
                      index={index}
                    >
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          className={`p-3 mb-2 bg-white border border-gray-200 rounded-lg cursor-move hover:shadow-md transition-shadow ${
                            snapshot.isDragging ? 'shadow-lg' : ''
                          }`}
                        >
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">{component.icon}</span>
                            <div>
                              <div className="font-medium text-sm">{component.name}</div>
                              <div className="text-xs text-gray-500">{component.description}</div>
                            </div>
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </div>
        ))}
      </DragDropContext>
    </div>
  );

  // Render validation panel
  const renderValidationPanel = () => (
    <div className="h-48 bg-gray-50 border-t border-gray-200 p-4 overflow-y-auto">
      <h3 className="text-lg font-semibold mb-2">Validation Results</h3>
      
      {validationErrors.length === 0 ? (
        <div className="text-green-600 flex items-center">
          <span className="mr-2">✅</span>
          No validation errors found
        </div>
      ) : (
        <div className="space-y-2">
          {validationErrors.map((error, index) => (
            <div
              key={index}
              className={`p-2 rounded border-l-4 ${
                error.severity === 'error'
                  ? 'bg-red-50 border-red-400 text-red-700'
                  : error.severity === 'warning'
                  ? 'bg-yellow-50 border-yellow-400 text-yellow-700'
                  : 'bg-blue-50 border-blue-400 text-blue-700'
              }`}
            >
              <div className="flex items-start">
                <span className="font-medium mr-2">
                  Line {error.line}:
                </span>
                <span>{error.message}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // Render parameter configuration modal
  const renderParameterModal = () => (
    <Modal
      open={showComponentModal}
      onClose={() => setShowComponentModal(false)}
      title={`Configure ${selectedComponent?.name}`}
    >
      {selectedComponent && (
        <div className="space-y-4">
          <p className="text-gray-600">{selectedComponent.description}</p>
          
          {selectedComponent.parameters.map((param) => (
            <div key={param.name}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {param.name}
                {param.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              
              {param.type === 'select' ? (
                <select
                  value={componentParameters[param.name] || param.defaultValue}
                  onChange={(e) => setComponentParameters(prev => ({
                    ...prev,
                    [param.name]: e.target.value
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {param.validation?.options?.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              ) : param.type === 'boolean' ? (
                <input
                  type="checkbox"
                  checked={componentParameters[param.name] ?? param.defaultValue}
                  onChange={(e) => setComponentParameters(prev => ({
                    ...prev,
                    [param.name]: e.target.checked
                  }))}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              ) : (
                <input
                  type={param.type === 'number' ? 'number' : 'text'}
                  value={componentParameters[param.name] ?? param.defaultValue}
                  onChange={(e) => setComponentParameters(prev => ({
                    ...prev,
                    [param.name]: param.type === 'number' ? Number(e.target.value) : e.target.value
                  }))}
                  min={param.validation?.min}
                  max={param.validation?.max}
                  step={param.validation?.min ? 0.1 : undefined}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              )}
              
              <p className="text-xs text-gray-500 mt-1">{param.description}</p>
            </div>
          ))}
          
          <div className="flex justify-end space-x-2 pt-4">
            <Button
              variant="secondary"
              onClick={() => setShowComponentModal(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleComponentConfirm}>
              Add Component
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-1">
        {/* Component Palette */}
        {renderComponentPalette()}
        
        {/* Editor Area */}
        <div className="flex-1 flex flex-col">
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="editor-drop-zone">
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={`flex-1 relative ${
                    snapshot.isDraggingOver ? 'bg-blue-50' : ''
                  }`}
                >
                  <Editor
                    height="100%"
                    language="haasscript"
                    theme="haasscript-dark"
                    value={strategy.code}
                    onChange={handleCodeChange}
                    onMount={handleEditorDidMount}
                    options={{
                      minimap: { enabled: true },
                      fontSize: 14,
                      lineNumbers: 'on',
                      roundedSelection: false,
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                      tabSize: 2,
                      insertSpaces: true,
                      wordWrap: 'on',
                      contextmenu: true,
                      quickSuggestions: true,
                      suggestOnTriggerCharacters: true,
                      acceptSuggestionOnEnter: 'on',
                      folding: true,
                      foldingStrategy: 'indentation',
                      showFoldingControls: 'always'
                    }}
                  />
                  
                  {snapshot.isDraggingOver && (
                    <div className="absolute inset-0 bg-blue-100 bg-opacity-50 flex items-center justify-center pointer-events-none">
                      <div className="bg-blue-500 text-white px-4 py-2 rounded-lg">
                        Drop component here to add to script
                      </div>
                    </div>
                  )}
                  
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </div>
      </div>
      
      {/* Validation Panel */}
      {renderValidationPanel()}
      
      {/* Parameter Configuration Modal */}
      {renderParameterModal()}
    </div>
  );
};