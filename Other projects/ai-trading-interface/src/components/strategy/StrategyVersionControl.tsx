import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { useStrategyStore } from '../../stores/strategyStore';
import { versionControlService } from '../../services/versionControlService';
import { strategyComparisonService } from '../../services/strategyComparisonService';
import { DiffService } from '../../services/diffService';
import { 
  StrategyVersion, 
  StrategyComparison, 
  DiffResult,
  StrategyBranch,
  MergeRequest 
} from '../../types/versionControl';
import { HaasScriptStrategy } from '../../types/strategy';

interface StrategyVersionControlProps {
  strategy: HaasScriptStrategy;
  onVersionChange: (version: StrategyVersion) => void;
}

export const StrategyVersionControl: React.FC<StrategyVersionControlProps> = ({
  strategy,
  onVersionChange
}) => {
  const { updateStrategy } = useStrategyStore();
  
  const [versions, setVersions] = useState<StrategyVersion[]>([]);
  const [branches, setBranches] = useState<StrategyBranch[]>([]);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [showCommitModal, setShowCommitModal] = useState(false);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [showBranchModal, setShowBranchModal] = useState(false);
  const [commitMessage, setCommitMessage] = useState('');
  const [branchName, setBranchName] = useState('');
  const [branchDescription, setBranchDescription] = useState('');
  const [comparison, setComparison] = useState<StrategyComparison | null>(null);
  const [diffResult, setDiffResult] = useState<DiffResult | null>(null);
  const [activeTab, setActiveTab] = useState<'versions' | 'branches' | 'comparison'>('versions');

  useEffect(() => {
    loadVersions();
    loadBranches();
  }, [strategy.id]);

  const loadVersions = () => {
    const strategyVersions = versionControlService.getVersions(strategy.id);
    setVersions(strategyVersions);
  };

  const loadBranches = () => {
    const strategyBranches = versionControlService.getBranches(strategy.id);
    setBranches(strategyBranches);
  };

  const handleCommit = () => {
    if (!commitMessage.trim()) {
      alert('Please enter a commit message');
      return;
    }

    const newVersion = versionControlService.createVersion(strategy, commitMessage);
    setVersions(prev => [...prev, newVersion]);
    setCommitMessage('');
    setShowCommitModal(false);
    onVersionChange(newVersion);
  };

  const handleRollback = (version: number) => {
    if (confirm(`Are you sure you want to rollback to version ${version}?`)) {
      const rolledBackVersion = versionControlService.rollbackToVersion(strategy.id, version);
      if (rolledBackVersion) {
        setVersions(prev => [...prev, rolledBackVersion]);
        
        // Update the strategy with the rolled back code
        updateStrategy(strategy.id, {
          code: rolledBackVersion.code,
          parameters: rolledBackVersion.parameters,
          version: rolledBackVersion.version
        });
        
        onVersionChange(rolledBackVersion);
      }
    }
  };

  const handleCreateBranch = () => {
    if (!branchName.trim()) {
      alert('Please enter a branch name');
      return;
    }

    const activeVersion = versionControlService.getActiveVersion(strategy.id);
    if (!activeVersion) {
      alert('No active version found');
      return;
    }

    try {
      const newBranch = versionControlService.createBranch(
        strategy.id,
        branchName,
        activeVersion.id,
        branchDescription
      );
      setBranches(prev => [...prev, newBranch]);
      setBranchName('');
      setBranchDescription('');
      setShowBranchModal(false);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to create branch');
    }
  };

  const handleCompareVersions = () => {
    if (selectedVersions.length !== 2) {
      alert('Please select exactly 2 versions to compare');
      return;
    }

    const version1 = versions.find(v => v.id === selectedVersions[0]);
    const version2 = versions.find(v => v.id === selectedVersions[1]);

    if (!version1 || !version2) {
      alert('Selected versions not found');
      return;
    }

    // Create mock strategies for comparison
    const strategy1: HaasScriptStrategy = {
      id: version1.strategyId,
      name: version1.name,
      description: version1.description,
      code: version1.code,
      parameters: version1.parameters,
      version: version1.version,
      createdAt: version1.createdAt,
      updatedAt: version1.createdAt,
      author: version1.author,
      tags: version1.tags,
      validationErrors: [],
      isValid: true
    };

    const strategy2: HaasScriptStrategy = {
      id: version2.strategyId,
      name: version2.name,
      description: version2.description,
      code: version2.code,
      parameters: version2.parameters,
      version: version2.version,
      createdAt: version2.createdAt,
      updatedAt: version2.createdAt,
      author: version2.author,
      tags: version2.tags,
      validationErrors: [],
      isValid: true
    };

    const comparisonResult = strategyComparisonService.compareStrategies(
      [strategy1, strategy2],
      'version',
      `${version1.name} v${version1.version} vs v${version2.version}`
    );

    const diff = DiffService.compareCode(version1.code, version2.code);

    setComparison(comparisonResult);
    setDiffResult(diff);
    setShowComparisonModal(true);
  };

  const renderVersionsTab = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Version History</h3>
        <div className="space-x-2">
          <Button
            onClick={() => setShowCommitModal(true)}
            size="sm"
          >
            Create Version
          </Button>
          <Button
            onClick={handleCompareVersions}
            variant="secondary"
            size="sm"
            disabled={selectedVersions.length !== 2}
          >
            Compare Selected
          </Button>
        </div>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {versions.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No versions yet. Create your first version to start tracking changes.
          </div>
        ) : (
          versions
            .sort((a, b) => b.version - a.version)
            .map((version) => (
              <Card
                key={version.id}
                className={`p-4 ${version.isActive ? 'bg-blue-50 border-blue-200' : ''}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      checked={selectedVersions.includes(version.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedVersions(prev => [...prev, version.id]);
                        } else {
                          setSelectedVersions(prev => prev.filter(id => id !== version.id));
                        }
                      }}
                      className="mt-1"
                    />
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium">
                          Version {version.version}
                          {version.isActive && (
                            <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                              Active
                            </span>
                          )}
                        </h4>
                        <span className="text-sm text-gray-500">
                          {version.branchName}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {version.commitMessage}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>{version.author}</span>
                        <span>{version.createdAt.toLocaleDateString()}</span>
                        <span>{version.changes.length} changes</span>
                      </div>
                      {version.tags.length > 0 && (
                        <div className="flex space-x-1 mt-2">
                          {version.tags.map(tag => (
                            <span
                              key={tag}
                              className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    {!version.isActive && (
                      <Button
                        onClick={() => handleRollback(version.version)}
                        variant="secondary"
                        size="sm"
                      >
                        Rollback
                      </Button>
                    )}
                  </div>
                </div>

                {version.changes.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <h5 className="text-sm font-medium mb-2">Changes:</h5>
                    <div className="space-y-1">
                      {version.changes.slice(0, 3).map((change, index) => (
                        <div key={index} className="text-xs">
                          <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                            change.type === 'addition' ? 'bg-green-500' :
                            change.type === 'deletion' ? 'bg-red-500' :
                            'bg-yellow-500'
                          }`} />
                          <span className="text-gray-600">{change.description}</span>
                          <span className={`ml-2 px-1 py-0.5 rounded text-xs ${
                            change.impact === 'high' ? 'bg-red-100 text-red-700' :
                            change.impact === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {change.impact}
                          </span>
                        </div>
                      ))}
                      {version.changes.length > 3 && (
                        <div className="text-xs text-gray-500">
                          +{version.changes.length - 3} more changes
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </Card>
            ))
        )}
      </div>
    </div>
  );

  const renderBranchesTab = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Branches</h3>
        <Button
          onClick={() => setShowBranchModal(true)}
          size="sm"
        >
          Create Branch
        </Button>
      </div>

      <div className="space-y-2">
        {branches.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No branches yet. Create a branch to work on features independently.
          </div>
        ) : (
          branches.map((branch) => (
            <Card key={branch.name} className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium">{branch.name}</h4>
                    {branch.isProtected && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
                        Protected
                      </span>
                    )}
                    {!branch.isActive && branch.mergedAt && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        Merged
                      </span>
                    )}
                  </div>
                  {branch.description && (
                    <p className="text-sm text-gray-600 mt-1">{branch.description}</p>
                  )}
                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                    <span>{branch.author}</span>
                    <span>{branch.createdAt.toLocaleDateString()}</span>
                    {branch.mergedAt && (
                      <span>Merged {branch.mergedAt.toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  {branch.isActive && branch.name !== 'main' && (
                    <Button
                      onClick={() => {
                        // TODO: Implement merge functionality
                        console.log('Merge branch:', branch.name);
                      }}
                      variant="secondary"
                      size="sm"
                    >
                      Merge
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );

  const renderComparisonTab = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Version Comparison</h3>
      <p className="text-gray-600">
        Select two versions from the Versions tab to compare them here.
      </p>
      
      {comparison && diffResult && (
        <div className="space-y-4">
          <Card className="p-4">
            <h4 className="font-medium mb-2">Comparison Summary</h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Total Changes:</span>
                <span className="ml-2 font-medium">{diffResult.summary.totalChanges}</span>
              </div>
              <div>
                <span className="text-gray-500">Complexity:</span>
                <span className={`ml-2 font-medium ${
                  diffResult.summary.complexity === 'high' ? 'text-red-600' :
                  diffResult.summary.complexity === 'medium' ? 'text-yellow-600' :
                  'text-green-600'
                }`}>
                  {diffResult.summary.complexity}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Insights:</span>
                <span className="ml-2 font-medium">{comparison.insights.length}</span>
              </div>
            </div>
          </Card>

          {comparison.insights.length > 0 && (
            <Card className="p-4">
              <h4 className="font-medium mb-2">Insights</h4>
              <div className="space-y-2">
                {comparison.insights.map((insight, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded border-l-4 ${
                      insight.severity === 'critical' ? 'bg-red-50 border-red-400' :
                      insight.severity === 'warning' ? 'bg-yellow-50 border-yellow-400' :
                      'bg-blue-50 border-blue-400'
                    }`}
                  >
                    <h5 className="font-medium text-sm">{insight.title}</h5>
                    <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                    {insight.recommendation && (
                      <p className="text-sm text-gray-700 mt-2">
                        <strong>Recommendation:</strong> {insight.recommendation}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'versions', label: 'Versions', count: versions.length },
            { id: 'branches', label: 'Branches', count: branches.length },
            { id: 'comparison', label: 'Comparison' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'versions' && renderVersionsTab()}
      {activeTab === 'branches' && renderBranchesTab()}
      {activeTab === 'comparison' && renderComparisonTab()}

      {/* Commit Modal */}
      <Modal
        open={showCommitModal}
        onClose={() => setShowCommitModal(false)}
        title="Create New Version"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Commit Message *
            </label>
            <textarea
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Describe the changes made in this version..."
            />
          </div>
          
          <div className="flex justify-end space-x-2 pt-4">
            <Button
              variant="secondary"
              onClick={() => setShowCommitModal(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCommit}
              disabled={!commitMessage.trim()}
            >
              Create Version
            </Button>
          </div>
        </div>
      </Modal>

      {/* Branch Modal */}
      <Modal
        open={showBranchModal}
        onClose={() => setShowBranchModal(false)}
        title="Create New Branch"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Branch Name *
            </label>
            <input
              type="text"
              value={branchName}
              onChange={(e) => setBranchName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="feature/new-indicator"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={branchDescription}
              onChange={(e) => setBranchDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Describe the purpose of this branch..."
            />
          </div>
          
          <div className="flex justify-end space-x-2 pt-4">
            <Button
              variant="secondary"
              onClick={() => setShowBranchModal(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateBranch}
              disabled={!branchName.trim()}
            >
              Create Branch
            </Button>
          </div>
        </div>
      </Modal>

      {/* Comparison Modal */}
      <Modal
        open={showComparisonModal}
        onClose={() => setShowComparisonModal(false)}
        title="Version Comparison"
        size="xl"
      >
        <div className="space-y-4">
          {comparison && diffResult && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <Card className="p-4">
                  <h4 className="font-medium mb-2">Changes Summary</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Additions:</span>
                      <span className="text-green-600">+{diffResult.summary.linesAdded}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Deletions:</span>
                      <span className="text-red-600">-{diffResult.summary.linesDeleted}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Modifications:</span>
                      <span className="text-yellow-600">~{diffResult.summary.linesModified}</span>
                    </div>
                  </div>
                </Card>

                <Card className="p-4">
                  <h4 className="font-medium mb-2">Recommendations</h4>
                  <div className="space-y-1">
                    {comparison.recommendations.slice(0, 3).map((rec, index) => (
                      <div key={index} className="text-sm">
                        <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                          rec.impact === 'high' ? 'bg-red-500' :
                          rec.impact === 'medium' ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`} />
                        {rec.title}
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              <div className="max-h-96 overflow-y-auto">
                <h4 className="font-medium mb-2">Code Diff</h4>
                <pre className="bg-gray-100 p-4 rounded text-sm">
                  {DiffService.generateDiffSummary(diffResult)}
                </pre>
              </div>
            </>
          )}
          
          <div className="flex justify-end pt-4">
            <Button onClick={() => setShowComparisonModal(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};