import { 
  StrategyComparison, 
  StrategyComparisonItem, 
  ComparisonMetrics, 
  ComparisonInsight, 
  ComparisonRecommendation,
  PerformanceSnapshot 
} from '../types/versionControl';
import { HaasScriptStrategy } from '../types/strategy';
import { DiffService } from './diffService';

export class StrategyComparisonService {
  /**
   * Compare multiple strategies or versions
   */
  compareStrategies(
    strategies: HaasScriptStrategy[],
    comparisonType: 'version' | 'strategy' | 'performance' = 'strategy',
    name: string = 'Strategy Comparison'
  ): StrategyComparison {
    const comparisonItems = strategies.map(strategy => this.convertToComparisonItem(strategy));
    const metrics = this.calculateComparisonMetrics(comparisonItems);
    const insights = this.generateInsights(comparisonItems, metrics);
    const recommendations = this.generateRecommendations(comparisonItems, metrics, insights);

    return {
      id: `comparison_${Date.now()}`,
      name,
      strategies: comparisonItems,
      createdAt: new Date(),
      comparisonType,
      metrics,
      insights,
      recommendations
    };
  }

  /**
   * Compare two specific strategies in detail
   */
  compareTwo(strategy1: HaasScriptStrategy, strategy2: HaasScriptStrategy): {
    codeDiff: any;
    parameterDiff: any;
    performanceDiff: any;
    similarity: number;
    recommendations: string[];
  } {
    const codeDiff = DiffService.compareCode(strategy1.code, strategy2.code);
    const parameterDiff = this.compareParameters(strategy1.parameters || [], strategy2.parameters || []);
    const performanceDiff = this.comparePerformance(strategy1.performance, strategy2.performance);
    const similarity = this.calculateCodeSimilarity(strategy1.code, strategy2.code);
    const recommendations = this.generateTwoWayRecommendations(strategy1, strategy2, codeDiff, similarity);

    return {
      codeDiff,
      parameterDiff,
      performanceDiff,
      similarity,
      recommendations
    };
  }

  /**
   * Convert strategy to comparison item
   */
  private convertToComparisonItem(strategy: HaasScriptStrategy): StrategyComparisonItem {
    return {
      strategyId: strategy.id,
      name: strategy.name,
      version: strategy.version,
      code: strategy.code,
      parameters: strategy.parameters || [],
      performance: strategy.performance ? {
        ...strategy.performance,
        backtestPeriod: {
          start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Default 30 days ago
          end: new Date()
        },
        marketConditions: ['normal'] // Default market condition
      } : undefined,
      metadata: {
        author: strategy.author,
        createdAt: strategy.createdAt,
        tags: strategy.tags || [],
        branchName: 'main' // Default branch
      }
    };
  }

  /**
   * Calculate comprehensive comparison metrics
   */
  private calculateComparisonMetrics(strategies: StrategyComparisonItem[]): ComparisonMetrics {
    const metrics: ComparisonMetrics = {
      codeComplexity: {},
      performanceScore: {},
      riskScore: {},
      maintainabilityScore: {},
      similarity: {}
    };

    // Calculate individual metrics for each strategy
    strategies.forEach(strategy => {
      metrics.codeComplexity[strategy.strategyId] = this.calculateCodeComplexity(strategy.code);
      metrics.performanceScore[strategy.strategyId] = this.calculatePerformanceScore(strategy.performance);
      metrics.riskScore[strategy.strategyId] = this.calculateRiskScore(strategy.performance);
      metrics.maintainabilityScore[strategy.strategyId] = this.calculateMaintainabilityScore(strategy.code);
    });

    // Calculate pairwise similarities
    for (let i = 0; i < strategies.length; i++) {
      for (let j = i + 1; j < strategies.length; j++) {
        const key = `${strategies[i].strategyId}_vs_${strategies[j].strategyId}`;
        metrics.similarity[key] = this.calculateCodeSimilarity(
          strategies[i].code, 
          strategies[j].code
        );
      }
    }

    return metrics;
  }

  /**
   * Calculate code complexity score
   */
  private calculateCodeComplexity(code: string): number {
    const lines = code.split('\n').filter(line => line.trim() && !line.trim().startsWith('//'));
    const conditions = (code.match(/if\s*\(/g) || []).length;
    const loops = (code.match(/(for|while)\s*\(/g) || []).length;
    const functions = (code.match(/function\s+\w+/g) || []).length;
    const indicators = (code.match(/(RSI|EMA|SMA|MACD|BB)\s*\(/g) || []).length;

    // Weighted complexity calculation
    return Math.round(
      lines.length * 0.1 +
      conditions * 2 +
      loops * 3 +
      functions * 1.5 +
      indicators * 0.5
    );
  }

  /**
   * Calculate performance score (0-100)
   */
  private calculatePerformanceScore(performance?: PerformanceSnapshot): number {
    if (!performance) return 0;

    const returnScore = Math.max(0, Math.min(100, performance.totalReturn * 10 + 50));
    const sharpeScore = Math.max(0, Math.min(100, performance.sharpeRatio * 25 + 50));
    const drawdownScore = Math.max(0, 100 - Math.abs(performance.maxDrawdown) * 100);
    const winRateScore = performance.winRate * 100;

    return Math.round((returnScore + sharpeScore + drawdownScore + winRateScore) / 4);
  }

  /**
   * Calculate risk score (0-100, higher = riskier)
   */
  private calculateRiskScore(performance?: PerformanceSnapshot): number {
    if (!performance) return 50; // Default medium risk

    const drawdownRisk = Math.abs(performance.maxDrawdown) * 100;
    const volatilityRisk = performance.volatility * 50;
    const winRateRisk = (1 - performance.winRate) * 100;

    return Math.round(Math.min(100, (drawdownRisk + volatilityRisk + winRateRisk) / 3));
  }

  /**
   * Calculate maintainability score (0-100)
   */
  private calculateMaintainabilityScore(code: string): number {
    const lines = code.split('\n');
    const totalLines = lines.length;
    const commentLines = lines.filter(line => line.trim().startsWith('//')).length;
    const emptyLines = lines.filter(line => line.trim() === '').length;
    const longLines = lines.filter(line => line.length > 100).length;
    
    const commentRatio = totalLines > 0 ? commentLines / totalLines : 0;
    const structureScore = emptyLines / totalLines; // Good spacing
    const readabilityPenalty = longLines / totalLines; // Long lines are harder to read

    const score = (commentRatio * 40) + (structureScore * 30) + ((1 - readabilityPenalty) * 30);
    return Math.round(Math.max(0, Math.min(100, score * 100)));
  }

  /**
   * Calculate code similarity between two strategies
   */
  private calculateCodeSimilarity(code1: string, code2: string): number {
    const lines1 = code1.split('\n').map(line => line.trim()).filter(line => line && !line.startsWith('//'));
    const lines2 = code2.split('\n').map(line => line.trim()).filter(line => line && !line.startsWith('//'));

    if (lines1.length === 0 && lines2.length === 0) return 1;
    if (lines1.length === 0 || lines2.length === 0) return 0;

    const commonLines = lines1.filter(line => lines2.includes(line)).length;
    const totalUniqueLines = new Set([...lines1, ...lines2]).size;

    return totalUniqueLines > 0 ? commonLines / totalUniqueLines : 0;
  }

  /**
   * Generate insights from comparison
   */
  private generateInsights(strategies: StrategyComparisonItem[], metrics: ComparisonMetrics): ComparisonInsight[] {
    const insights: ComparisonInsight[] = [];

    // Performance insights
    const performanceScores = Object.values(metrics.performanceScore);
    const bestPerformer = Object.keys(metrics.performanceScore).reduce((a, b) => 
      metrics.performanceScore[a] > metrics.performanceScore[b] ? a : b
    );
    const worstPerformer = Object.keys(metrics.performanceScore).reduce((a, b) => 
      metrics.performanceScore[a] < metrics.performanceScore[b] ? a : b
    );

    if (performanceScores.length > 1) {
      insights.push({
        type: 'performance',
        title: 'Performance Leader',
        description: `Strategy ${bestPerformer} shows the best overall performance with a score of ${metrics.performanceScore[bestPerformer]}`,
        affectedStrategies: [bestPerformer],
        severity: 'info',
        recommendation: 'Consider analyzing the successful patterns in this strategy'
      });

      if (metrics.performanceScore[bestPerformer] - metrics.performanceScore[worstPerformer] > 30) {
        insights.push({
          type: 'performance',
          title: 'Significant Performance Gap',
          description: `Large performance difference detected between strategies (${metrics.performanceScore[bestPerformer] - metrics.performanceScore[worstPerformer]} points)`,
          affectedStrategies: [bestPerformer, worstPerformer],
          severity: 'warning',
          recommendation: 'Review underperforming strategy for potential improvements'
        });
      }
    }

    // Risk insights
    const riskScores = Object.values(metrics.riskScore);
    const highRiskStrategies = Object.keys(metrics.riskScore).filter(id => metrics.riskScore[id] > 70);
    
    if (highRiskStrategies.length > 0) {
      insights.push({
        type: 'risk',
        title: 'High Risk Strategies Detected',
        description: `${highRiskStrategies.length} strategies show high risk levels (>70)`,
        affectedStrategies: highRiskStrategies,
        severity: 'critical',
        recommendation: 'Implement additional risk management measures'
      });
    }

    // Code quality insights
    const complexityScores = Object.values(metrics.codeComplexity);
    const avgComplexity = complexityScores.reduce((a, b) => a + b, 0) / complexityScores.length;
    const highComplexityStrategies = Object.keys(metrics.codeComplexity).filter(id => 
      metrics.codeComplexity[id] > avgComplexity * 1.5
    );

    if (highComplexityStrategies.length > 0) {
      insights.push({
        type: 'code_quality',
        title: 'High Complexity Strategies',
        description: `${highComplexityStrategies.length} strategies have above-average complexity`,
        affectedStrategies: highComplexityStrategies,
        severity: 'warning',
        recommendation: 'Consider refactoring for better maintainability'
      });
    }

    // Similarity insights
    const similarities = Object.values(metrics.similarity);
    const highSimilarityPairs = Object.keys(metrics.similarity).filter(key => 
      metrics.similarity[key] > 0.8
    );

    if (highSimilarityPairs.length > 0) {
      insights.push({
        type: 'logic',
        title: 'Similar Strategies Detected',
        description: `${highSimilarityPairs.length} strategy pairs show high similarity (>80%)`,
        affectedStrategies: highSimilarityPairs.flatMap(pair => pair.split('_vs_')),
        severity: 'info',
        recommendation: 'Consider consolidating similar strategies or diversifying approaches'
      });
    }

    return insights;
  }

  /**
   * Generate recommendations based on comparison
   */
  private generateRecommendations(
    strategies: StrategyComparisonItem[], 
    metrics: ComparisonMetrics, 
    insights: ComparisonInsight[]
  ): ComparisonRecommendation[] {
    const recommendations: ComparisonRecommendation[] = [];

    // Performance-based recommendations
    const bestPerformer = Object.keys(metrics.performanceScore).reduce((a, b) => 
      metrics.performanceScore[a] > metrics.performanceScore[b] ? a : b
    );

    const worstPerformers = Object.keys(metrics.performanceScore).filter(id => 
      metrics.performanceScore[id] < metrics.performanceScore[bestPerformer] * 0.7
    );

    worstPerformers.forEach(strategyId => {
      recommendations.push({
        type: 'optimize',
        title: 'Optimize Underperforming Strategy',
        description: `Strategy ${strategyId} could benefit from optimization based on patterns from ${bestPerformer}`,
        targetStrategy: strategyId,
        sourceStrategy: bestPerformer,
        confidence: 0.8,
        impact: 'high',
        effort: 'moderate',
        actions: [
          {
            type: 'code_change',
            description: 'Analyze and adopt successful patterns from best performer',
            automated: false
          },
          {
            type: 'parameter_update',
            description: 'Optimize parameters based on successful configuration',
            automated: true
          },
          {
            type: 'test_run',
            description: 'Run backtest to validate improvements',
            automated: true
          }
        ]
      });
    });

    // Risk management recommendations
    const highRiskStrategies = Object.keys(metrics.riskScore).filter(id => metrics.riskScore[id] > 70);
    
    highRiskStrategies.forEach(strategyId => {
      recommendations.push({
        type: 'optimize',
        title: 'Reduce Risk Exposure',
        description: `Strategy ${strategyId} shows high risk levels and needs risk management improvements`,
        targetStrategy: strategyId,
        confidence: 0.9,
        impact: 'high',
        effort: 'moderate',
        actions: [
          {
            type: 'code_change',
            description: 'Add or improve stop-loss and take-profit mechanisms',
            automated: false
          },
          {
            type: 'parameter_update',
            description: 'Adjust position sizing and risk parameters',
            automated: true
          }
        ]
      });
    });

    // Merge recommendations for similar strategies
    const highSimilarityPairs = Object.keys(metrics.similarity).filter(key => 
      metrics.similarity[key] > 0.9
    );

    highSimilarityPairs.forEach(pair => {
      const [strategy1, strategy2] = pair.split('_vs_');
      const betterPerformer = metrics.performanceScore[strategy1] > metrics.performanceScore[strategy2] 
        ? strategy1 : strategy2;
      const worsePerformer = betterPerformer === strategy1 ? strategy2 : strategy1;

      recommendations.push({
        type: 'merge',
        title: 'Merge Similar Strategies',
        description: `Strategies ${strategy1} and ${strategy2} are very similar (${Math.round(metrics.similarity[pair] * 100)}% similarity)`,
        targetStrategy: betterPerformer,
        sourceStrategy: worsePerformer,
        confidence: 0.85,
        impact: 'medium',
        effort: 'easy',
        actions: [
          {
            type: 'code_change',
            description: 'Consolidate unique features from both strategies',
            automated: false
          }
        ]
      });
    });

    return recommendations;
  }

  /**
   * Generate recommendations for two-way comparison
   */
  private generateTwoWayRecommendations(
    strategy1: HaasScriptStrategy, 
    strategy2: HaasScriptStrategy, 
    codeDiff: any, 
    similarity: number
  ): string[] {
    const recommendations: string[] = [];

    if (similarity > 0.8) {
      recommendations.push('Strategies are very similar - consider merging or diversifying');
    } else if (similarity < 0.2) {
      recommendations.push('Strategies are very different - good for diversification');
    }

    if (codeDiff.summary.totalChanges > 50) {
      recommendations.push('Significant code differences detected - review changes carefully');
    }

    if (strategy1.performance && strategy2.performance) {
      const perf1 = strategy1.performance;
      const perf2 = strategy2.performance;

      if (perf1.totalReturn > perf2.totalReturn * 1.2) {
        recommendations.push(`${strategy1.name} shows significantly better returns`);
      } else if (perf2.totalReturn > perf1.totalReturn * 1.2) {
        recommendations.push(`${strategy2.name} shows significantly better returns`);
      }

      if (Math.abs(perf1.maxDrawdown) < Math.abs(perf2.maxDrawdown) * 0.8) {
        recommendations.push(`${strategy1.name} has better risk management`);
      } else if (Math.abs(perf2.maxDrawdown) < Math.abs(perf1.maxDrawdown) * 0.8) {
        recommendations.push(`${strategy2.name} has better risk management`);
      }
    }

    return recommendations;
  }

  /**
   * Compare parameters between strategies
   */
  private compareParameters(params1: any[], params2: any[]): any {
    const comparison = {
      common: [] as any[],
      unique1: [] as any[],
      unique2: [] as any[],
      different: [] as any[]
    };

    const params1Map = new Map(params1.map(p => [p.name, p]));
    const params2Map = new Map(params2.map(p => [p.name, p]));

    // Find common parameters
    params1.forEach(param => {
      const param2 = params2Map.get(param.name);
      if (param2) {
        if (param.value === param2.value) {
          comparison.common.push({ name: param.name, value: param.value });
        } else {
          comparison.different.push({
            name: param.name,
            value1: param.value,
            value2: param2.value
          });
        }
      } else {
        comparison.unique1.push(param);
      }
    });

    // Find unique parameters in strategy 2
    params2.forEach(param => {
      if (!params1Map.has(param.name)) {
        comparison.unique2.push(param);
      }
    });

    return comparison;
  }

  /**
   * Compare performance between strategies
   */
  private comparePerformance(perf1?: any, perf2?: any): any {
    if (!perf1 || !perf2) {
      return { available: false };
    }

    return {
      available: true,
      totalReturn: {
        strategy1: perf1.totalReturn,
        strategy2: perf2.totalReturn,
        difference: perf1.totalReturn - perf2.totalReturn,
        winner: perf1.totalReturn > perf2.totalReturn ? 'strategy1' : 'strategy2'
      },
      sharpeRatio: {
        strategy1: perf1.sharpeRatio,
        strategy2: perf2.sharpeRatio,
        difference: perf1.sharpeRatio - perf2.sharpeRatio,
        winner: perf1.sharpeRatio > perf2.sharpeRatio ? 'strategy1' : 'strategy2'
      },
      maxDrawdown: {
        strategy1: perf1.maxDrawdown,
        strategy2: perf2.maxDrawdown,
        difference: Math.abs(perf1.maxDrawdown) - Math.abs(perf2.maxDrawdown),
        winner: Math.abs(perf1.maxDrawdown) < Math.abs(perf2.maxDrawdown) ? 'strategy1' : 'strategy2'
      },
      winRate: {
        strategy1: perf1.winRate,
        strategy2: perf2.winRate,
        difference: perf1.winRate - perf2.winRate,
        winner: perf1.winRate > perf2.winRate ? 'strategy1' : 'strategy2'
      }
    };
  }
}

export const strategyComparisonService = new StrategyComparisonService();