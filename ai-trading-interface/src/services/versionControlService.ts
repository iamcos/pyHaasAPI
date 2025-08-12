import { 
  StrategyVersion, 
  VersionChange, 
  StrategyBranch, 
  MergeRequest, 
  MergeConflict,
  VersionControlConfig 
} from '../types/versionControl';
import { HaasScriptStrategy } from '../types/strategy';
import { DiffService } from './diffService';

export class VersionControlService {
  private versions: Map<string, StrategyVersion[]> = new Map();
  private branches: Map<string, StrategyBranch[]> = new Map();
  private mergeRequests: Map<string, MergeRequest[]> = new Map();
  private config: VersionControlConfig = {
    autoVersioning: true,
    maxVersionsPerStrategy: 50,
    autoCleanup: true,
    cleanupThreshold: 90,
    requireCommitMessages: true,
    enableBranching: true,
    defaultBranch: 'main',
    enableMergeRequests: true,
    autoBackup: true,
    backupInterval: 24
  };

  /**
   * Create a new version of a strategy
   */
  createVersion(
    strategy: HaasScriptStrategy, 
    commitMessage: string, 
    branchName: string = 'main'
  ): StrategyVersion {
    const strategyVersions = this.versions.get(strategy.id) || [];
    const lastVersion = strategyVersions.length > 0 
      ? Math.max(...strategyVersions.map(v => v.version))
      : 0;

    const previousVersion = strategyVersions.find(v => v.version === lastVersion);
    const changes = previousVersion 
      ? this.calculateChanges(previousVersion.code, strategy.code)
      : [];

    const newVersion: StrategyVersion = {
      id: `${strategy.id}_v${lastVersion + 1}`,
      strategyId: strategy.id,
      version: lastVersion + 1,
      name: strategy.name,
      description: strategy.description,
      code: strategy.code,
      parameters: strategy.parameters || [],
      createdAt: new Date(),
      author: 'User', // TODO: Get from auth context
      commitMessage,
      tags: strategy.tags || [],
      parentVersionId: previousVersion?.id,
      branchName,
      isActive: true,
      changes
    };

    // Deactivate previous version
    if (previousVersion) {
      previousVersion.isActive = false;
    }

    strategyVersions.push(newVersion);
    this.versions.set(strategy.id, strategyVersions);

    // Auto-cleanup if enabled
    if (this.config.autoCleanup) {
      this.cleanupOldVersions(strategy.id);
    }

    return newVersion;
  }

  /**
   * Get all versions for a strategy
   */
  getVersions(strategyId: string): StrategyVersion[] {
    return this.versions.get(strategyId) || [];
  }

  /**
   * Get a specific version
   */
  getVersion(strategyId: string, version: number): StrategyVersion | null {
    const versions = this.versions.get(strategyId) || [];
    return versions.find(v => v.version === version) || null;
  }

  /**
   * Get the active version for a strategy
   */
  getActiveVersion(strategyId: string): StrategyVersion | null {
    const versions = this.versions.get(strategyId) || [];
    return versions.find(v => v.isActive) || null;
  }

  /**
   * Rollback to a previous version
   */
  rollbackToVersion(strategyId: string, targetVersion: number): StrategyVersion | null {
    const versions = this.versions.get(strategyId) || [];
    const targetVersionObj = versions.find(v => v.version === targetVersion);
    
    if (!targetVersionObj) {
      throw new Error(`Version ${targetVersion} not found for strategy ${strategyId}`);
    }

    // Create a new version based on the target version
    const rollbackVersion: StrategyVersion = {
      ...targetVersionObj,
      id: `${strategyId}_v${Math.max(...versions.map(v => v.version)) + 1}`,
      version: Math.max(...versions.map(v => v.version)) + 1,
      createdAt: new Date(),
      commitMessage: `Rollback to version ${targetVersion}`,
      parentVersionId: versions.find(v => v.isActive)?.id,
      changes: this.calculateChanges(
        versions.find(v => v.isActive)?.code || '',
        targetVersionObj.code
      )
    };

    // Deactivate current active version
    const currentActive = versions.find(v => v.isActive);
    if (currentActive) {
      currentActive.isActive = false;
    }

    versions.push(rollbackVersion);
    this.versions.set(strategyId, versions);

    return rollbackVersion;
  }

  /**
   * Create a new branch
   */
  createBranch(
    strategyId: string, 
    branchName: string, 
    baseVersionId: string,
    description: string = ''
  ): StrategyBranch {
    const branches = this.branches.get(strategyId) || [];
    
    // Check if branch already exists
    if (branches.some(b => b.name === branchName)) {
      throw new Error(`Branch ${branchName} already exists`);
    }

    const newBranch: StrategyBranch = {
      name: branchName,
      strategyId,
      baseVersionId,
      headVersionId: baseVersionId,
      createdAt: new Date(),
      author: 'User', // TODO: Get from auth context
      description,
      isActive: true,
      isProtected: branchName === this.config.defaultBranch
    };

    branches.push(newBranch);
    this.branches.set(strategyId, branches);

    return newBranch;
  }

  /**
   * Get all branches for a strategy
   */
  getBranches(strategyId: string): StrategyBranch[] {
    return this.branches.get(strategyId) || [];
  }

  /**
   * Merge branches
   */
  mergeBranches(
    strategyId: string,
    sourceBranch: string,
    targetBranch: string,
    commitMessage: string
  ): { success: boolean; conflicts?: MergeConflict[]; newVersion?: StrategyVersion } {
    const branches = this.branches.get(strategyId) || [];
    const versions = this.versions.get(strategyId) || [];

    const sourceBranchObj = branches.find(b => b.name === sourceBranch);
    const targetBranchObj = branches.find(b => b.name === targetBranch);

    if (!sourceBranchObj || !targetBranchObj) {
      throw new Error('Source or target branch not found');
    }

    const sourceVersion = versions.find(v => v.id === sourceBranchObj.headVersionId);
    const targetVersion = versions.find(v => v.id === targetBranchObj.headVersionId);

    if (!sourceVersion || !targetVersion) {
      throw new Error('Source or target version not found');
    }

    // Check for conflicts
    const conflicts = this.detectMergeConflicts(sourceVersion.code, targetVersion.code);
    
    if (conflicts.length > 0) {
      return { success: false, conflicts };
    }

    // Perform merge
    const mergedCode = this.performMerge(sourceVersion.code, targetVersion.code);
    
    // Create new version on target branch
    const mergedVersion: StrategyVersion = {
      id: `${strategyId}_v${Math.max(...versions.map(v => v.version)) + 1}`,
      strategyId,
      version: Math.max(...versions.map(v => v.version)) + 1,
      name: targetVersion.name,
      description: targetVersion.description,
      code: mergedCode,
      parameters: [...targetVersion.parameters, ...sourceVersion.parameters],
      createdAt: new Date(),
      author: 'User',
      commitMessage: `Merge ${sourceBranch} into ${targetBranch}: ${commitMessage}`,
      tags: [...new Set([...targetVersion.tags, ...sourceVersion.tags])],
      parentVersionId: targetVersion.id,
      branchName: targetBranch,
      isActive: true,
      changes: this.calculateChanges(targetVersion.code, mergedCode)
    };

    // Deactivate previous active version on target branch
    const previousActive = versions.find(v => v.branchName === targetBranch && v.isActive);
    if (previousActive) {
      previousActive.isActive = false;
    }

    versions.push(mergedVersion);
    this.versions.set(strategyId, versions);

    // Update branch head
    targetBranchObj.headVersionId = mergedVersion.id;

    // Mark source branch as merged if it's not the default branch
    if (sourceBranch !== this.config.defaultBranch) {
      sourceBranchObj.mergedAt = new Date();
      sourceBranchObj.mergedBy = 'User';
      sourceBranchObj.isActive = false;
    }

    return { success: true, newVersion: mergedVersion };
  }

  /**
   * Create a merge request
   */
  createMergeRequest(
    strategyId: string,
    title: string,
    description: string,
    sourceVersionId: string,
    targetVersionId: string
  ): MergeRequest {
    const mergeRequests = this.mergeRequests.get(strategyId) || [];
    const versions = this.versions.get(strategyId) || [];

    const sourceVersion = versions.find(v => v.id === sourceVersionId);
    const targetVersion = versions.find(v => v.id === targetVersionId);

    if (!sourceVersion || !targetVersion) {
      throw new Error('Source or target version not found');
    }

    const conflicts = this.detectMergeConflicts(sourceVersion.code, targetVersion.code);

    const mergeRequest: MergeRequest = {
      id: `mr_${Date.now()}`,
      title,
      description,
      sourceStrategyId: strategyId,
      sourceVersionId,
      targetStrategyId: strategyId,
      targetVersionId,
      author: 'User',
      createdAt: new Date(),
      status: 'pending',
      conflicts,
      reviewers: [],
      comments: [],
      autoMerge: conflicts.length === 0
    };

    mergeRequests.push(mergeRequest);
    this.mergeRequests.set(strategyId, mergeRequests);

    return mergeRequest;
  }

  /**
   * Get merge requests for a strategy
   */
  getMergeRequests(strategyId: string): MergeRequest[] {
    return this.mergeRequests.get(strategyId) || [];
  }

  /**
   * Calculate changes between two code versions
   */
  private calculateChanges(oldCode: string, newCode: string): VersionChange[] {
    const diff = DiffService.compareCode(oldCode, newCode);
    const changes: VersionChange[] = [];

    // Convert diff to version changes
    diff.additions.forEach(line => {
      changes.push({
        type: 'addition',
        lineNumber: line.lineNumber,
        newContent: line.content,
        description: `Added: ${line.content.trim()}`,
        impact: this.assessChangeImpact(line.content)
      });
    });

    diff.deletions.forEach(line => {
      changes.push({
        type: 'deletion',
        lineNumber: line.lineNumber,
        oldContent: line.content,
        description: `Deleted: ${line.content.trim()}`,
        impact: this.assessChangeImpact(line.content)
      });
    });

    diff.modifications.forEach(line => {
      changes.push({
        type: 'modification',
        lineNumber: line.lineNumber,
        oldContent: line.context,
        newContent: line.content,
        description: `Modified: ${line.content.trim()}`,
        impact: this.assessChangeImpact(line.content)
      });
    });

    return changes;
  }

  /**
   * Assess the impact of a code change
   */
  private assessChangeImpact(content: string): 'low' | 'medium' | 'high' {
    const trimmed = content.trim().toLowerCase();
    
    // High impact changes
    if (trimmed.includes('buy(') || trimmed.includes('sell(') || 
        trimmed.includes('closeposition(') || trimmed.includes('setstoploss(') ||
        trimmed.includes('settakeprofit(')) {
      return 'high';
    }
    
    // Medium impact changes
    if (trimmed.includes('if ') || trimmed.includes('while ') || 
        trimmed.includes('for ') || trimmed.includes('function ')) {
      return 'medium';
    }
    
    // Low impact changes (comments, variables, etc.)
    return 'low';
  }

  /**
   * Detect merge conflicts between two code versions
   */
  private detectMergeConflicts(sourceCode: string, targetCode: string): MergeConflict[] {
    const conflicts: MergeConflict[] = [];
    const diff = DiffService.compareCode(targetCode, sourceCode);
    
    // Simple conflict detection: if same line is modified in both versions
    const sourceLines = sourceCode.split('\n');
    const targetLines = targetCode.split('\n');
    
    for (let i = 0; i < Math.max(sourceLines.length, targetLines.length); i++) {
      const sourceLine = sourceLines[i] || '';
      const targetLine = targetLines[i] || '';
      
      if (sourceLine.trim() !== targetLine.trim() && 
          sourceLine.trim() !== '' && 
          targetLine.trim() !== '') {
        conflicts.push({
          lineNumber: i + 1,
          sourceContent: sourceLine,
          targetContent: targetLine,
          resolved: false
        });
      }
    }
    
    return conflicts;
  }

  /**
   * Perform automatic merge of two code versions
   */
  private performMerge(sourceCode: string, targetCode: string): string {
    // Simple merge strategy: use target as base and apply non-conflicting changes from source
    const diff = DiffService.compareCode(targetCode, sourceCode);
    return DiffService.applyDiff(targetCode, diff);
  }

  /**
   * Clean up old versions based on configuration
   */
  private cleanupOldVersions(strategyId: string): void {
    const versions = this.versions.get(strategyId) || [];
    
    if (versions.length <= this.config.maxVersionsPerStrategy) {
      return;
    }

    // Keep the most recent versions and important ones (tagged, branched, etc.)
    const sortedVersions = versions.sort((a, b) => b.version - a.version);
    const toKeep = sortedVersions.slice(0, this.config.maxVersionsPerStrategy);
    
    // Also keep versions that are:
    // - Active
    // - Tagged
    // - Branch heads
    // - Recent (within cleanup threshold)
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - this.config.cleanupThreshold);
    
    const importantVersions = versions.filter(v => 
      v.isActive || 
      v.tags.length > 0 || 
      v.createdAt > cutoffDate ||
      this.isBranchHead(strategyId, v.id)
    );

    const finalVersions = [...new Set([...toKeep, ...importantVersions])];
    this.versions.set(strategyId, finalVersions);
  }

  /**
   * Check if a version is a branch head
   */
  private isBranchHead(strategyId: string, versionId: string): boolean {
    const branches = this.branches.get(strategyId) || [];
    return branches.some(b => b.headVersionId === versionId);
  }

  /**
   * Get version control configuration
   */
  getConfig(): VersionControlConfig {
    return { ...this.config };
  }

  /**
   * Update version control configuration
   */
  updateConfig(newConfig: Partial<VersionControlConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Export version history for backup
   */
  exportVersionHistory(strategyId: string): any {
    return {
      versions: this.versions.get(strategyId) || [],
      branches: this.branches.get(strategyId) || [],
      mergeRequests: this.mergeRequests.get(strategyId) || [],
      exportedAt: new Date(),
      config: this.config
    };
  }

  /**
   * Import version history from backup
   */
  importVersionHistory(strategyId: string, data: any): void {
    if (data.versions) {
      this.versions.set(strategyId, data.versions);
    }
    if (data.branches) {
      this.branches.set(strategyId, data.branches);
    }
    if (data.mergeRequests) {
      this.mergeRequests.set(strategyId, data.mergeRequests);
    }
  }
}

export const versionControlService = new VersionControlService();