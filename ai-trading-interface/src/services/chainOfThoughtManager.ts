import { chainOfThoughtValidator, type ValidationResult } from './chainOfThoughtValidator'
import { useAIStore } from '@/stores/aiStore'
import type { ChainOfThoughtStep, Alternative } from '@/types'

// Chain-of-Thought session interface
export interface ChainOfThoughtSession {
  id: string
  title: string
  description: string
  steps: ChainOfThoughtStep[]
  validation: ValidationResult
  metadata: {
    createdAt: Date
    updatedAt: Date
    context: string
    tags: string[]
    source: string
  }
  statistics: {
    totalSteps: number
    avgConfidence: number
    duration: number
    validationScore: number
  }
}

// Chain-of-Thought analytics
export interface ChainOfThoughtAnalytics {
  totalSessions: number
  totalSteps: number
  avgSessionLength: number
  avgConfidence: number
  avgValidationScore: number
  commonIssues: Array<{
    type: string
    count: number
    percentage: number
  }>
  confidenceDistribution: Array<{
    range: string
    count: number
    percentage: number
  }>
  timeDistribution: Array<{
    period: string
    count: number
  }>
}

// Chain-of-Thought Manager
export class ChainOfThoughtManager {
  private sessions: Map<string, ChainOfThoughtSession> = new Map()
  private aiStore = useAIStore

  // Create a new reasoning session
  createSession(
    title: string,
    description: string,
    context: string = '',
    tags: string[] = []
  ): string {
    const sessionId = `cot-session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    
    const session: ChainOfThoughtSession = {
      id: sessionId,
      title,
      description,
      steps: [],
      validation: {
        isValid: true,
        score: 1,
        issues: [],
        suggestions: [],
        confidence: 1
      },
      metadata: {
        createdAt: new Date(),
        updatedAt: new Date(),
        context,
        tags,
        source: 'user'
      },
      statistics: {
        totalSteps: 0,
        avgConfidence: 0,
        duration: 0,
        validationScore: 1
      }
    }

    this.sessions.set(sessionId, session)
    return sessionId
  }

  // Add a step to a session
  addStepToSession(sessionId: string, step: ChainOfThoughtStep): void {
    const session = this.sessions.get(sessionId)
    if (!session) {
      throw new Error(`Session ${sessionId} not found`)
    }

    // Add step to session
    session.steps.push(step)
    session.metadata.updatedAt = new Date()

    // Update statistics
    this.updateSessionStatistics(session)

    // Revalidate the session
    session.validation = chainOfThoughtValidator.validateChainOfThought(session.steps)

    // Update the session
    this.sessions.set(sessionId, session)

    // Also add to global store
    this.aiStore.getState().addChainOfThoughtStep(step)
  }

  // Add multiple steps to a session
  addStepsToSession(sessionId: string, steps: ChainOfThoughtStep[]): void {
    const session = this.sessions.get(sessionId)
    if (!session) {
      throw new Error(`Session ${sessionId} not found`)
    }

    // Add all steps
    session.steps.push(...steps)
    session.metadata.updatedAt = new Date()

    // Update statistics
    this.updateSessionStatistics(session)

    // Revalidate the session
    session.validation = chainOfThoughtValidator.validateChainOfThought(session.steps)

    // Update the session
    this.sessions.set(sessionId, session)

    // Also add to global store
    steps.forEach(step => {
      this.aiStore.getState().addChainOfThoughtStep(step)
    })
  }

  // Get a session
  getSession(sessionId: string): ChainOfThoughtSession | null {
    return this.sessions.get(sessionId) || null
  }

  // Get all sessions
  getAllSessions(): ChainOfThoughtSession[] {
    return Array.from(this.sessions.values()).sort((a, b) => 
      b.metadata.updatedAt.getTime() - a.metadata.updatedAt.getTime()
    )
  }

  // Search sessions
  searchSessions(query: string, filters?: {
    tags?: string[]
    minScore?: number
    dateRange?: { start: Date; end: Date }
  }): ChainOfThoughtSession[] {
    const sessions = this.getAllSessions()
    
    return sessions.filter(session => {
      // Text search
      if (query) {
        const searchText = `${session.title} ${session.description} ${session.steps.map(s => s.reasoning).join(' ')}`.toLowerCase()
        if (!searchText.includes(query.toLowerCase())) {
          return false
        }
      }

      // Tag filter
      if (filters?.tags && filters.tags.length > 0) {
        const hasMatchingTag = filters.tags.some(tag => 
          session.metadata.tags.includes(tag)
        )
        if (!hasMatchingTag) {
          return false
        }
      }

      // Score filter
      if (filters?.minScore && session.validation.score < filters.minScore) {
        return false
      }

      // Date range filter
      if (filters?.dateRange) {
        const sessionDate = session.metadata.createdAt
        if (sessionDate < filters.dateRange.start || sessionDate > filters.dateRange.end) {
          return false
        }
      }

      return true
    })
  }

  // Validate a session
  validateSession(sessionId: string): ValidationResult {
    const session = this.sessions.get(sessionId)
    if (!session) {
      throw new Error(`Session ${sessionId} not found`)
    }

    const validation = chainOfThoughtValidator.validateChainOfThought(session.steps)
    
    // Update session validation
    session.validation = validation
    session.metadata.updatedAt = new Date()
    this.sessions.set(sessionId, session)

    return validation
  }

  // Get session analytics
  getSessionAnalytics(sessionId: string): {
    stepAnalysis: Array<{
      step: ChainOfThoughtStep
      issues: any[]
      score: number
    }>
    overallMetrics: {
      coherenceScore: number
      confidenceProgression: number[]
      logicalFlow: number
    }
  } {
    const session = this.sessions.get(sessionId)
    if (!session) {
      throw new Error(`Session ${sessionId} not found`)
    }

    // Analyze each step
    const stepAnalysis = session.steps.map(step => {
      const stepIssues = session.validation.issues.filter(issue => issue.stepId === step.id)
      const stepScore = this.calculateStepScore(step, stepIssues)
      
      return {
        step,
        issues: stepIssues,
        score: stepScore
      }
    })

    // Calculate overall metrics
    const confidenceProgression = session.steps.map(s => s.confidence)
    const coherenceScore = this.calculateCoherenceScore(session.steps)
    const logicalFlow = this.calculateLogicalFlow(session.steps)

    return {
      stepAnalysis,
      overallMetrics: {
        coherenceScore,
        confidenceProgression,
        logicalFlow
      }
    }
  }

  // Generate insights for a session
  generateSessionInsights(sessionId: string): {
    strengths: string[]
    weaknesses: string[]
    recommendations: string[]
    patterns: string[]
  } {
    const session = this.sessions.get(sessionId)
    if (!session) {
      throw new Error(`Session ${sessionId} not found`)
    }

    const insights = {
      strengths: [] as string[],
      weaknesses: [] as string[],
      recommendations: [] as string[],
      patterns: [] as string[]
    }

    // Analyze strengths
    if (session.validation.score > 0.8) {
      insights.strengths.push('High overall reasoning quality')
    }

    const avgConfidence = session.statistics.avgConfidence
    if (avgConfidence > 0.8) {
      insights.strengths.push('Consistently high confidence levels')
    }

    const stepsWithAlternatives = session.steps.filter(s => s.alternatives && s.alternatives.length > 0)
    if (stepsWithAlternatives.length > session.steps.length * 0.5) {
      insights.strengths.push('Good consideration of alternative approaches')
    }

    // Analyze weaknesses
    const highSeverityIssues = session.validation.issues.filter(i => i.severity === 'high')
    if (highSeverityIssues.length > 0) {
      insights.weaknesses.push(`${highSeverityIssues.length} high-severity reasoning issues`)
    }

    if (avgConfidence < 0.5) {
      insights.weaknesses.push('Low average confidence in reasoning')
    }

    if (session.steps.length < 3) {
      insights.weaknesses.push('Reasoning chain may be too brief')
    }

    // Generate recommendations
    insights.recommendations.push(...session.validation.suggestions)

    if (session.steps.length > 10) {
      insights.recommendations.push('Consider consolidating some reasoning steps')
    }

    // Identify patterns
    const confidenceVariance = this.calculateVariance(session.steps.map(s => s.confidence))
    if (confidenceVariance > 0.3) {
      insights.patterns.push('High variance in confidence levels across steps')
    }

    const reasoningLengths = session.steps.map(s => s.reasoning.length)
    const avgLength = reasoningLengths.reduce((sum, len) => sum + len, 0) / reasoningLengths.length
    if (avgLength < 50) {
      insights.patterns.push('Reasoning explanations tend to be brief')
    } else if (avgLength > 200) {
      insights.patterns.push('Reasoning explanations tend to be detailed')
    }

    return insights
  }

  // Get overall analytics across all sessions
  getOverallAnalytics(): ChainOfThoughtAnalytics {
    const sessions = this.getAllSessions()
    const allSteps = sessions.flatMap(s => s.steps)
    const allIssues = sessions.flatMap(s => s.validation.issues)

    // Basic statistics
    const totalSessions = sessions.length
    const totalSteps = allSteps.length
    const avgSessionLength = totalSessions > 0 ? totalSteps / totalSessions : 0
    const avgConfidence = allSteps.length > 0 
      ? allSteps.reduce((sum, s) => sum + s.confidence, 0) / allSteps.length 
      : 0
    const avgValidationScore = sessions.length > 0
      ? sessions.reduce((sum, s) => sum + s.validation.score, 0) / sessions.length
      : 0

    // Common issues analysis
    const issueTypes = allIssues.reduce((acc, issue) => {
      acc[issue.type] = (acc[issue.type] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const commonIssues = Object.entries(issueTypes)
      .map(([type, count]) => ({
        type,
        count,
        percentage: (count / allIssues.length) * 100
      }))
      .sort((a, b) => b.count - a.count)

    // Confidence distribution
    const confidenceRanges = [
      { range: '0-20%', min: 0, max: 0.2 },
      { range: '20-40%', min: 0.2, max: 0.4 },
      { range: '40-60%', min: 0.4, max: 0.6 },
      { range: '60-80%', min: 0.6, max: 0.8 },
      { range: '80-100%', min: 0.8, max: 1.0 }
    ]

    const confidenceDistribution = confidenceRanges.map(range => {
      const count = allSteps.filter(s => s.confidence >= range.min && s.confidence < range.max).length
      return {
        range: range.range,
        count,
        percentage: allSteps.length > 0 ? (count / allSteps.length) * 100 : 0
      }
    })

    // Time distribution (last 30 days)
    const now = new Date()
    const timeRanges = [
      { period: 'Today', days: 1 },
      { period: 'This Week', days: 7 },
      { period: 'This Month', days: 30 }
    ]

    const timeDistribution = timeRanges.map(range => {
      const cutoff = new Date(now.getTime() - range.days * 24 * 60 * 60 * 1000)
      const count = sessions.filter(s => s.metadata.createdAt >= cutoff).length
      return {
        period: range.period,
        count
      }
    })

    return {
      totalSessions,
      totalSteps,
      avgSessionLength,
      avgConfidence,
      avgValidationScore,
      commonIssues,
      confidenceDistribution,
      timeDistribution
    }
  }

  // Export session data
  exportSession(sessionId: string): string {
    const session = this.sessions.get(sessionId)
    if (!session) {
      throw new Error(`Session ${sessionId} not found`)
    }

    return JSON.stringify(session, null, 2)
  }

  // Import session data
  importSession(sessionData: string): string {
    try {
      const session: ChainOfThoughtSession = JSON.parse(sessionData)
      
      // Generate new ID to avoid conflicts
      const newId = `cot-session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      session.id = newId
      
      // Update timestamps
      session.metadata.createdAt = new Date(session.metadata.createdAt)
      session.metadata.updatedAt = new Date()
      
      // Revalidate
      session.validation = chainOfThoughtValidator.validateChainOfThought(session.steps)
      
      // Update statistics
      this.updateSessionStatistics(session)
      
      this.sessions.set(newId, session)
      return newId
    } catch (error) {
      throw new Error(`Failed to import session: ${error}`)
    }
  }

  // Delete a session
  deleteSession(sessionId: string): boolean {
    return this.sessions.delete(sessionId)
  }

  // Clear all sessions
  clearAllSessions(): void {
    this.sessions.clear()
  }

  // Private helper methods
  private updateSessionStatistics(session: ChainOfThoughtSession): void {
    const steps = session.steps
    
    session.statistics.totalSteps = steps.length
    session.statistics.avgConfidence = steps.length > 0
      ? steps.reduce((sum, s) => sum + s.confidence, 0) / steps.length
      : 0

    if (steps.length > 1) {
      const timestamps = steps.map(s => new Date(s.timestamp).getTime())
      session.statistics.duration = Math.max(...timestamps) - Math.min(...timestamps)
    } else {
      session.statistics.duration = 0
    }

    session.statistics.validationScore = session.validation.score
  }

  private calculateStepScore(step: ChainOfThoughtStep, issues: any[]): number {
    let score = step.confidence

    // Penalize for issues
    issues.forEach(issue => {
      switch (issue.severity) {
        case 'high':
          score -= 0.3
          break
        case 'medium':
          score -= 0.15
          break
        case 'low':
          score -= 0.05
          break
      }
    })

    // Bonus for alternatives
    if (step.alternatives && step.alternatives.length > 0) {
      score += 0.1
    }

    // Bonus for supporting data
    if (step.data) {
      score += 0.05
    }

    return Math.max(0, Math.min(1, score))
  }

  private calculateCoherenceScore(steps: ChainOfThoughtStep[]): number {
    if (steps.length < 2) return 1

    let coherenceSum = 0
    for (let i = 1; i < steps.length; i++) {
      // Simple coherence based on confidence consistency
      const confidenceDiff = Math.abs(steps[i].confidence - steps[i-1].confidence)
      const stepCoherence = 1 - confidenceDiff
      coherenceSum += stepCoherence
    }

    return coherenceSum / (steps.length - 1)
  }

  private calculateLogicalFlow(steps: ChainOfThoughtStep[]): number {
    if (steps.length < 2) return 1

    // Simple logical flow based on step numbering and reasoning progression
    let flowScore = 1
    
    for (let i = 1; i < steps.length; i++) {
      // Check step numbering
      if (steps[i].step !== steps[i-1].step + 1) {
        flowScore -= 0.1
      }
    }

    return Math.max(0, flowScore)
  }

  private calculateVariance(numbers: number[]): number {
    if (numbers.length === 0) return 0
    
    const mean = numbers.reduce((sum, n) => sum + n, 0) / numbers.length
    const squaredDiffs = numbers.map(n => Math.pow(n - mean, 2))
    return squaredDiffs.reduce((sum, sq) => sum + sq, 0) / numbers.length
  }
}

// Create singleton instance
export const chainOfThoughtManager = new ChainOfThoughtManager()

export default chainOfThoughtManager