import React, { useEffect, useState } from 'react'
import { tradingService } from '@/services/tradingService'
import { useTradingStore } from '@/stores/tradingStore'
import { Card } from '@/components/ui/Card'
import { Alert } from '@/components/ui/Alert'

interface DashboardStats {
  portfolioValue: number
  todaysPnL: number
  activeStrategies: number
  riskScore: 'Low' | 'Medium' | 'High'
}

interface MarketData {
  symbol: string
  price: number
  change24h: number
}

export function Dashboard() {
  const { accounts, bots, labs, loading, error } = useTradingStore()
  const [stats, setStats] = useState<DashboardStats>({
    portfolioValue: 0,
    todaysPnL: 0,
    activeStrategies: 0,
    riskScore: 'Medium'
  })
  const [marketData, setMarketData] = useState<MarketData[]>([])
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting')
  const [debugLog, setDebugLog] = useState<string[]>([])

  const addDebugLog = (message: string) => {
    setDebugLog(prev => [...prev.slice(-9), `${new Date().toLocaleTimeString()}: ${message}`])
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      addDebugLog('🔄 Starting dashboard data load...')
      setConnectionStatus('connecting')
      
      // Check connection first
      addDebugLog('🔍 Checking connection...')
      const isConnected = await tradingService.checkConnection()
      addDebugLog(`✅ Connection check result: ${isConnected}`)
      
      if (!isConnected) {
        addDebugLog('❌ Connection failed')
        setConnectionStatus('error')
        return
      }
      
      setConnectionStatus('connected')
      addDebugLog('🎯 Connection successful, loading data...')
      
      // Load all data in parallel
      const results = await Promise.allSettled([
        tradingService.loadAccounts(),
        tradingService.loadBots(),
        tradingService.loadLabs(),
        loadMarketData()
      ])
      
      addDebugLog(`📊 Data load results: ${results.map(r => r.status).join(', ')}`)
      
      // Calculate stats from loaded data
      calculateStats()
      addDebugLog('✅ Dashboard data loaded successfully')
      
    } catch (error) {
      addDebugLog(`❌ Failed to load dashboard data: ${error}`)
      setConnectionStatus('error')
    }
  }

  const loadMarketData = async () => {
    try {
      // Load market data for major pairs
      const markets = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']
      const marketPromises = markets.map(async (symbol) => {
        try {
          const snapshot = await tradingService.updateMarketPrice(symbol)
          return {
            symbol,
            price: snapshot?.price || 0,
            change24h: snapshot?.change24h || 0
          }
        } catch (error) {
          console.error(`Failed to load ${symbol} data:`, error)
          return {
            symbol,
            price: 0,
            change24h: 0
          }
        }
      })
      
      const results = await Promise.all(marketPromises)
      setMarketData(results)
    } catch (error) {
      console.error('Failed to load market data:', error)
    }
  }

  const calculateStats = () => {
    // Calculate portfolio value from accounts
    const totalBalance = accounts.reduce((sum, account) => sum + (account.balance || 0), 0)
    
    // Count active bots
    const activeBots = bots.filter(bot => bot.status === 'active').length
    
    // Simple risk calculation based on active strategies
    let riskScore: 'Low' | 'Medium' | 'High' = 'Low'
    if (activeBots > 5) riskScore = 'High'
    else if (activeBots > 2) riskScore = 'Medium'
    
    setStats({
      portfolioValue: totalBalance,
      todaysPnL: 0, // Would need historical data to calculate
      activeStrategies: activeBots,
      riskScore
    })
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  }

  const formatPercentage = (value: number) => {
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  if (connectionStatus === 'error') {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <Alert type="error" className="mb-6">
            <h3 className="font-medium">Connection Error</h3>
            <p>Unable to connect to the trading server. Please ensure the MCP server is running.</p>
            <button 
              onClick={loadDashboardData}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry Connection
            </button>
          </Alert>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">AI Trading Interface</h1>
          <p className="text-gray-600 mt-2">
            Welcome to your intelligent trading dashboard
            {connectionStatus === 'connecting' && (
              <span className="ml-2 text-blue-600">• Connecting...</span>
            )}
            {connectionStatus === 'connected' && (
              <span className="ml-2 text-green-600">• Connected</span>
            )}
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Portfolio Value</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {loading.accounts ? '...' : formatCurrency(stats.portfolioValue)}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Today's P&L</p>
                <p className="text-2xl font-semibold text-green-600">
                  {formatCurrency(stats.todaysPnL)}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Strategies</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {loading.bots ? '...' : stats.activeStrategies}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center">
              <div className={`p-2 rounded-lg ${
                stats.riskScore === 'Low' ? 'bg-green-100' :
                stats.riskScore === 'Medium' ? 'bg-yellow-100' : 'bg-red-100'
              }`}>
                <svg className={`w-6 h-6 ${
                  stats.riskScore === 'Low' ? 'text-green-600' :
                  stats.riskScore === 'Medium' ? 'text-yellow-600' : 'text-red-600'
                }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Risk Score</p>
                <p className={`text-2xl font-semibold ${
                  stats.riskScore === 'Low' ? 'text-green-600' :
                  stats.riskScore === 'Medium' ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {stats.riskScore}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Market Overview */}
          <Card>
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Market Overview</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {marketData.length === 0 ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="text-sm text-gray-500 mt-2">Loading market data...</p>
                  </div>
                ) : (
                  marketData.map((market) => (
                    <div key={market.symbol} className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-600">{market.symbol}</span>
                      <div className="text-right">
                        <div className="text-sm font-semibold text-gray-900">
                          {market.price > 0 ? formatCurrency(market.price) : 'N/A'}
                        </div>
                        <div className={`text-xs ${market.change24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {market.change24h !== 0 ? formatPercentage(market.change24h) : 'N/A'}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </Card>

          {/* System Status */}
          <Card>
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">System Status</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-green-400' : 
                    connectionStatus === 'connecting' ? 'bg-yellow-400' : 'bg-red-400'
                  }`}></div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">
                      MCP Server: {connectionStatus === 'connected' ? 'Connected' : 
                                  connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {accounts.length} accounts, {bots.length} bots, {labs.length} labs loaded
                    </p>
                  </div>
                </div>
                
                {error.accounts && (
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-red-900">Account Error</p>
                      <p className="text-xs text-red-500">{error.accounts}</p>
                    </div>
                  </div>
                )}
                
                {error.bots && (
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-red-900">Bot Error</p>
                      <p className="text-xs text-red-500">{error.bots}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>

        {/* Debug Panel */}
        <div className="mt-8 bg-gray-50 border border-gray-200 rounded-lg p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-gray-800">Debug Log</h3>
              <div className="mt-2 text-xs text-gray-600 font-mono bg-white p-3 rounded border max-h-40 overflow-y-auto">
                {debugLog.length === 0 ? (
                  <div className="text-gray-400">No debug messages yet...</div>
                ) : (
                  debugLog.map((log, index) => (
                    <div key={index} className="mb-1">{log}</div>
                  ))
                )}
              </div>
              <button 
                onClick={loadDashboardData}
                className="mt-2 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
              >
                Reload Data
              </button>
            </div>
          </div>
        </div>

        {/* Welcome Message */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">Welcome to AI Trading Interface!</h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  This is your comprehensive AI-powered trading platform connected to HaasOnline. 
                  Click the blue help button in the bottom-right corner to get started.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}