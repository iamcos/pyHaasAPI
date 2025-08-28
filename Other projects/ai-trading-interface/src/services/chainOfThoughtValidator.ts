import type { ChainOfThoughtStep, Alternative } from '@/types'

// Validation result interface
export interface ValidationResult {
  isValid: boolean
  score: number // 0-1 overall quality score
  issues: ValidationIssue[]
  suggestions: string[]
  confidence: number
}

export interface ValidationIssue {
  type: 'logical_gap' | 'low_confidence' | 'inconsistency' | 'missing_data' | 'circular_reasoning'
  severity: 'low' | 'medium' | 'high'
  stepId: string
  description: string
  suggestion: string
}

// Chain-of-Thought validation service
export class ChainOfThoughtValidator {
  private confidenceThreshold = 0.5
  private logicalGapThreshold = 0.3
  private consistencyThreshold = 0.7

  // Main validation method
  validateChainOfThought(steps: ChainOfThoughtStep[]): ValidationResult {
    if (steps.length === 0) {
      return {
        isValid: false,
        score: 0,
        issues: [{
          type: 'missing_data',
          severity: 'high',
          stepId: '',
          description: 'No reasoning steps provided',
          suggestion: 'Provide at least one reasoning step'
        }],
        suggestions: ['Add reasoning steps to explain the decision process'],
        confidence: 0
      }
    }

    const issues: ValidationIssue[] = []
    const suggestions: string[] = []

    // Sort steps by step number to ensure proper order
    const sortedSteps = [...steps].sort((a, b) => a.step - b.step)

    // Validate individual steps
    sortedSteps.forEach(step => {
      const stepIssues = this.validateStep(step)
      issues.push(...stepIssues)
    })

    // Validate step sequence
    const sequenceIssues = this.validateSequence(sortedSteps)
    issues.push(...sequenceIssues)

    // Validate logical consistency
    const consistencyIssues = this.validateConsistency(sortedSteps)
    issues.push(...consistencyIssues)

    // Check for circular reasoning
    const circularIssues = this.detectCircularReasoning(sortedSteps)
    issues.push(...circularIssues)

    // Generate suggestions based on issues
    const generatedSuggestions = this.generateSuggestions(issues, sortedSteps)
    suggestions.push(...generatedSuggestions)

    // Calculate overall score
    const score = this.calculateOverallScore(sortedSteps, issues)

    // Determine if chain is valid
    const isValid = issues.filter(i => i.severity === 'high').length === 0 && score >= 0.6

    // Calculate confidence in validation
    const confidence = this.calculateValidationConfidence(sortedSteps, issues)

    return {
      isValid,
      score,
      issues,
      suggestions,
      confidence
    }
  }

  // Validate individual step
  private validateStep(step: ChainOfThoughtStep): ValidationIssue[] {
    const issues: ValidationIssue[] = []

    // Check confidence level
    if (step.confidence < this.confidenceThreshold) {
      issues.push({
        type: 'low_confidence',
        severity: step.confidence < 0.3 ? 'high' : 'medium',
        stepId: step.id,
        description: `Step has low confidence (${(step.confidence * 100).toFixed(0)}%)`,
        suggestion: 'Consider gathering more data or using alternative approaches'
      })
    }

    // Check reasoning quality
    if (step.reasoning.length < 20) {
      issues.push({
        type: 'missing_data',
        severity: 'medium',
        stepId: step.id,
        description: 'Reasoning explanation is too brief',
        suggestion: 'Provide more detailed explanation of the reasoning process'
      })
    }

    // Check for vague language
    const vagueTerms = ['maybe', 'possibly', 'might', 'could be', 'seems like']
    const hasVagueLanguage = vagueTerms.some(term => 
      step.reasoning.toLowerCase().includes(term)
    )

    if (hasVagueLanguage) {
      issues.push({
        type: 'low_confidence',
        severity: 'low',
        stepId: step.id,
        description: 'Reasoning contains uncertain language',
        suggestion: 'Use more definitive language or provide confidence qualifiers'
      })
    }

    return issues
  }

  // Validate step sequence
  private validateSequence(steps: ChainOfThoughtStep[]): ValidationIssue[] {
    const issues: ValidationIssue[] = []

    for (let i = 1; i < steps.length; i++) {
      const currentStep = steps[i]
      const previousStep = steps[i - 1]

      // Check for logical gaps between steps
      const logicalGap = this.detectLogicalGap(previousStep, currentStep)
      if (logicalGap > this.logicalGapThreshold) {
        issues.push({
          type: 'logical_gap',
          severity: logicalGap > 0.7 ? 'high' : 'medium',
          stepId: currentStep.id,
          description: `Logical gap detected between step ${previousStep.step} and ${currentStep.step}`,
          suggestion: 'Add intermediate reasoning steps to bridge the logical gap'
        })
      }

      // Check step numbering
      if (currentStep.step !== previousStep.step + 1) {
        issues.push({
          type: 'inconsistency',
          severity: 'low',
          stepId: currentStep.id,
          description: `Step numbering inconsistency: expected ${previousStep.step + 1}, got ${currentStep.step}`,
          suggestion: 'Ensure steps are numbered sequentially'
        })
      }
    }

    return issues
  }

  // Validate logical consistency across steps
  private validateConsistency(steps: ChainOfThoughtStep[]): ValidationIssue[] {
    const issues: ValidationIssue[] = []

    // Check for contradictory statements
    for (let i = 0; i < steps.length; i++) {
      for (let j = i + 1; j < steps.length; j++) {
        const contradiction = this.detectContradiction(steps[i], steps[j])
        if (contradiction) {
          issues.push({
            type: 'inconsistency',
            severity: 'high',
            stepId: steps[j].id,
            description: `Contradiction detected between step ${steps[i].step} and ${steps[j].step}`,
            suggestion: 'Resolve the contradictory statements or explain the change in reasoning'
          })
        }
      }
    }

    // Check confidence consistency
    const confidences = steps.map(s => s.confidence)
    const confidenceVariance = this.calculateVariance(confidences)
    
    if (confidenceVariance > 0.3) {
      issues.push({
        type: 'inconsistency',
        severity: 'medium',
        stepId: steps[steps.length - 1].id,
        description: 'High variance in confidence levels across steps',
        suggestion: 'Review steps with significantly different confidence levels'
      })
    }

    return issues
  }

  // Detect circular reasoning
  private detectCircularReasoning(steps: ChainOfThoughtStep[]): ValidationIssue[] {
    const issues: ValidationIssue[] = []
    const reasoningTexts = steps.map(s => s.reasoning.toLowerCase())

    // Simple circular reasoning detection based on repeated concepts
    for (let i = 0; i < reasoningTexts.length; i++) {
      for (let j = i + 2; j < reasoningTexts.length; j++) {
        const similarity = this.calculateTextSimilarity(reasoningTexts[i], reasoningTexts[j])
        if (similarity > 0.8) {
          issues.push({
            type: 'circular_reasoning',
            severity: 'medium',
            stepId: steps[j].id,
            description: `Potential circular reasoning between step ${steps[i].step} and ${steps[j].step}`,
            suggestion: 'Ensure each step builds upon previous ones without repeating the same reasoning'
          })
        }
      }
    }

    return issues
  }

  // Generate suggestions based on issues and steps
  private generateSuggestions(issues: ValidationIssue[], steps: ChainOfThoughtStep[]): string[] {
    const suggestions: string[] = []

    // Count issue types
    const issueTypes = issues.reduce((acc, issue) => {
      acc[issue.type] = (acc[issue.type] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    // Generate general suggestions based on issue patterns
    if (issueTypes.low_confidence > steps.length * 0.5) {
      suggestions.push('Consider gathering more supporting data to increase confidence in reasoning')
    }

    if (issueTypes.logical_gap > 0) {
      suggestions.push('Add intermediate steps to make the reasoning flow more logical')
    }

    if (issueTypes.inconsistency > 0) {
      suggestions.push('Review the reasoning chain for contradictions and resolve them')
    }

    if (issueTypes.circular_reasoning > 0) {
      suggestions.push('Ensure each reasoning step adds new information or perspective')
    }

    // Add suggestions based on step characteristics
    const avgConfidence = steps.reduce((sum, s) => sum + s.confidence, 0) / steps.length
    if (avgConfidence < 0.6) {
      suggestions.push('Overall confidence is low - consider alternative approaches or additional validation')
    }

    if (steps.length < 3) {
      suggestions.push('Consider adding more reasoning steps for a more thorough analysis')
    }

    if (steps.length > 10) {
      suggestions.push('Consider consolidating some steps to make the reasoning more concise')
    }

    return suggestions
  }

  // Calculate overall quality score
  private calculateOverallScore(steps: ChainOfThoughtStep[], issues: ValidationIssue[]): number {
    let score = 0.8 // Base score

    // Adjust for average confidence
    const avgConfidence = steps.reduce((sum, s) => sum + s.confidence, 0) / steps.length
    score += (avgConfidence - 0.5) * 0.4 // -0.2 to +0.2

    // Penalize for issues
    issues.forEach(issue => {
      switch (issue.severity) {
        case 'high':
          score -= 0.15
          break
        case 'medium':
          score -= 0.08
          break
        case 'low':
          score -= 0.03
          break
      }
    })

    // Bonus for good step count
    if (steps.length >= 3 && steps.length <= 7) {
      score += 0.05
    }

    // Bonus for alternatives consideration
    const stepsWithAlternatives = steps.filter(s => s.alternatives && s.alternatives.length > 0)
    if (stepsWithAlternatives.length > 0) {
      score += 0.1 * (stepsWithAlternatives.length / steps.length)
    }

    return Math.max(0, Math.min(1, score))
  }

  // Calculate validation confidence
  private calculateValidationConfidence(steps: ChainOfThoughtStep[], issues: ValidationIssue[]): number {
    let confidence = 0.8

    // Higher confidence with more steps (up to a point)
    if (steps.length >= 3) {
      confidence += 0.1
    }

    // Lower confidence with many issues
    const highSeverityIssues = issues.filter(i => i.severity === 'high').length
    confidence -= highSeverityIssues * 0.15

    // Lower confidence with very low or very high step confidence variance
    const confidences = steps.map(s => s.confidence)
    const variance = this.calculateVariance(confidences)
    if (variance > 0.4 || variance < 0.05) {
      confidence -= 0.1
    }

    return Math.max(0.1, Math.min(1, confidence))
  }

  // Helper methods
  private detectLogicalGap(step1: ChainOfThoughtStep, step2: ChainOfThoughtStep): number {
    // Simple heuristic: large confidence drop might indicate logical gap
    const confidenceDrop = step1.confidence - step2.confidence
    if (confidenceDrop > 0.3) {
      return confidenceDrop
    }

    // Check if step2 reasoning builds on step1
    const similarity = this.calculateTextSimilarity(step1.reasoning, step2.reasoning)
    if (similarity < 0.1) {
      return 0.5 // Moderate gap if no apparent connection
    }

    return 0
  }

  private detectContradiction(step1: ChainOfThoughtStep, step2: ChainOfThoughtStep): boolean {
    // Simple contradiction detection based on opposing keywords
    const opposingPairs = [
      ['increase', 'decrease'],
      ['buy', 'sell'],
      ['bullish', 'bearish'],
      ['positive', 'negative'],
      ['good', 'bad'],
      ['high', 'low'],
      ['strong', 'weak']
    ]

    const text1 = step1.reasoning.toLowerCase()
    const text2 = step2.reasoning.toLowerCase()

    return opposingPairs.some(([word1, word2]) => 
      (text1.includes(word1) && text2.includes(word2)) ||
      (text1.includes(word2) && text2.includes(word1))
    )
  }

  private calculateTextSimilarity(text1: string, text2: string): number {
    // Simple word overlap similarity
    const words1 = new Set(text1.toLowerCase().split(/\s+/))
    const words2 = new Set(text2.toLowerCase().split(/\s+/))
    
    const intersection = new Set([...words1].filter(x => words2.has(x)))
    const union = new Set([...words1, ...words2])
    
    return intersection.size / union.size
  }

  private calculateVariance(numbers: number[]): number {
    const mean = numbers.reduce((sum, n) => sum + n, 0) / numbers.length
    const squaredDiffs = numbers.map(n => Math.pow(n - mean, 2))
    return squaredDiffs.reduce((sum, sq) => sum + sq, 0) / numbers.length
  }

  // Configuration methods
  setConfidenceThreshold(threshold: number): void {
    this.confidenceThreshold = Math.max(0, Math.min(1, threshold))
  }

  setLogicalGapThreshold(threshold: number): void {
    this.logicalGapThreshold = Math.max(0, Math.min(1, threshold))
  }

  setConsistencyThreshold(threshold: number): void {
    this.consistencyThreshold = Math.max(0, Math.min(1, threshold))
  }
}

// Create singleton instance
export const chainOfThoughtValidator = new ChainOfThoughtValidator()

export default chainOfThoughtValidator