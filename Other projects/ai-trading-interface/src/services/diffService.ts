import { DiffResult, DiffLine } from '../types/versionControl';

export class DiffService {
  /**
   * Compare two code strings and return detailed diff information
   */
  static compareCode(oldCode: string, newCode: string): DiffResult {
    const oldLines = oldCode.split('\n');
    const newLines = newCode.split('\n');
    
    const diff = this.computeLCS(oldLines, newLines);
    const diffLines = this.generateDiffLines(diff, oldLines, newLines);
    
    return {
      additions: diffLines.filter(line => line.type === 'addition'),
      deletions: diffLines.filter(line => line.type === 'deletion'),
      modifications: diffLines.filter(line => line.type === 'modification'),
      unchanged: diffLines.filter(line => line.type === 'unchanged'),
      summary: this.generateSummary(diffLines)
    };
  }

  /**
   * Compute Longest Common Subsequence for diff algorithm
   */
  private static computeLCS(oldLines: string[], newLines: string[]): number[][] {
    const m = oldLines.length;
    const n = newLines.length;
    const lcs: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        if (oldLines[i - 1].trim() === newLines[j - 1].trim()) {
          lcs[i][j] = lcs[i - 1][j - 1] + 1;
        } else {
          lcs[i][j] = Math.max(lcs[i - 1][j], lcs[i][j - 1]);
        }
      }
    }

    return lcs;
  }

  /**
   * Generate diff lines from LCS computation
   */
  private static generateDiffLines(lcs: number[][], oldLines: string[], newLines: string[]): DiffLine[] {
    const diffLines: DiffLine[] = [];
    let i = oldLines.length;
    let j = newLines.length;
    let lineNumber = 1;

    const changes: Array<{ type: 'add' | 'delete' | 'same', oldIndex?: number, newIndex?: number }> = [];

    // Backtrack through LCS to find changes
    while (i > 0 || j > 0) {
      if (i > 0 && j > 0 && oldLines[i - 1].trim() === newLines[j - 1].trim()) {
        changes.unshift({ type: 'same', oldIndex: i - 1, newIndex: j - 1 });
        i--;
        j--;
      } else if (j > 0 && (i === 0 || lcs[i][j - 1] >= lcs[i - 1][j])) {
        changes.unshift({ type: 'add', newIndex: j - 1 });
        j--;
      } else if (i > 0) {
        changes.unshift({ type: 'delete', oldIndex: i - 1 });
        i--;
      }
    }

    // Convert changes to diff lines
    let oldLineNum = 1;
    let newLineNum = 1;

    for (const change of changes) {
      switch (change.type) {
        case 'same':
          diffLines.push({
            lineNumber: lineNumber++,
            content: oldLines[change.oldIndex!],
            type: 'unchanged',
            oldLineNumber: oldLineNum++,
            newLineNumber: newLineNum++
          });
          break;

        case 'add':
          diffLines.push({
            lineNumber: lineNumber++,
            content: newLines[change.newIndex!],
            type: 'addition',
            newLineNumber: newLineNum++
          });
          break;

        case 'delete':
          diffLines.push({
            lineNumber: lineNumber++,
            content: oldLines[change.oldIndex!],
            type: 'deletion',
            oldLineNumber: oldLineNum++
          });
          break;
      }
    }

    // Post-process to identify modifications (adjacent deletions and additions)
    return this.identifyModifications(diffLines);
  }

  /**
   * Identify modifications by pairing adjacent deletions and additions
   */
  private static identifyModifications(diffLines: DiffLine[]): DiffLine[] {
    const result: DiffLine[] = [];
    let i = 0;

    while (i < diffLines.length) {
      const current = diffLines[i];
      const next = diffLines[i + 1];

      // Check if current deletion is followed by addition (potential modification)
      if (current.type === 'deletion' && next && next.type === 'addition') {
        const similarity = this.calculateSimilarity(current.content, next.content);
        
        // If lines are similar enough, treat as modification
        if (similarity > 0.5) {
          result.push({
            lineNumber: current.lineNumber,
            content: next.content,
            type: 'modification',
            oldLineNumber: current.oldLineNumber,
            newLineNumber: next.newLineNumber,
            context: `Changed from: ${current.content}`
          });
          i += 2; // Skip both lines
          continue;
        }
      }

      result.push(current);
      i++;
    }

    return result;
  }

  /**
   * Calculate similarity between two strings (0-1 scale)
   */
  private static calculateSimilarity(str1: string, str2: string): number {
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;
    
    if (longer.length === 0) return 1.0;
    
    const editDistance = this.levenshteinDistance(longer, shorter);
    return (longer.length - editDistance) / longer.length;
  }

  /**
   * Calculate Levenshtein distance between two strings
   */
  private static levenshteinDistance(str1: string, str2: string): number {
    const matrix: number[][] = [];

    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }

    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1, // substitution
            matrix[i][j - 1] + 1,     // insertion
            matrix[i - 1][j] + 1      // deletion
          );
        }
      }
    }

    return matrix[str2.length][str1.length];
  }

  /**
   * Generate summary statistics for the diff
   */
  private static generateSummary(diffLines: DiffLine[]) {
    const additions = diffLines.filter(line => line.type === 'addition').length;
    const deletions = diffLines.filter(line => line.type === 'deletion').length;
    const modifications = diffLines.filter(line => line.type === 'modification').length;
    const totalChanges = additions + deletions + modifications;

    let complexity: 'low' | 'medium' | 'high' = 'low';
    if (totalChanges > 50) {
      complexity = 'high';
    } else if (totalChanges > 20) {
      complexity = 'medium';
    }

    return {
      totalChanges,
      linesAdded: additions,
      linesDeleted: deletions,
      linesModified: modifications,
      complexity
    };
  }

  /**
   * Generate a human-readable diff summary
   */
  static generateDiffSummary(diff: DiffResult): string {
    const { summary } = diff;
    
    if (summary.totalChanges === 0) {
      return 'No changes detected';
    }

    const parts = [];
    
    if (summary.linesAdded > 0) {
      parts.push(`+${summary.linesAdded} additions`);
    }
    
    if (summary.linesDeleted > 0) {
      parts.push(`-${summary.linesDeleted} deletions`);
    }
    
    if (summary.linesModified > 0) {
      parts.push(`~${summary.linesModified} modifications`);
    }

    return `${parts.join(', ')} (${summary.complexity} complexity)`;
  }

  /**
   * Apply a diff to create a new version of code
   */
  static applyDiff(originalCode: string, diff: DiffResult): string {
    const lines = originalCode.split('\n');
    const result: string[] = [];
    
    let originalIndex = 0;
    
    for (const diffLine of [...diff.unchanged, ...diff.additions, ...diff.modifications].sort((a, b) => a.lineNumber - b.lineNumber)) {
      // Add unchanged lines up to current position
      while (originalIndex < (diffLine.oldLineNumber || diffLine.lineNumber) - 1) {
        if (originalIndex < lines.length) {
          result.push(lines[originalIndex]);
        }
        originalIndex++;
      }
      
      // Handle the diff line
      switch (diffLine.type) {
        case 'unchanged':
          result.push(diffLine.content);
          originalIndex++;
          break;
          
        case 'addition':
          result.push(diffLine.content);
          // Don't increment originalIndex for additions
          break;
          
        case 'modification':
          result.push(diffLine.content);
          originalIndex++;
          break;
      }
    }
    
    // Add remaining original lines
    while (originalIndex < lines.length) {
      result.push(lines[originalIndex]);
      originalIndex++;
    }
    
    return result.join('\n');
  }
}