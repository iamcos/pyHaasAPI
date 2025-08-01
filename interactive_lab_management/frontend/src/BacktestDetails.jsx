import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import Plot from 'react-plotly.js'

function BacktestDetails() {
  const [backtest, setBacktest] = useState(null)
  const [error, setError] = useState(null)
  const [monteCarloResults, setMonteCarloResults] = useState(null)
  const [timeSeriesDecompositionResults, setTimeSeriesDecompositionResults] = useState(null)
  const { backtest_id } = useParams()

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/backtests/${backtest_id}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch backtest details')
        }
        return response.json()
      })
      .then(data => setBacktest(data))
      .catch(error => setError(error.message))
  }, [backtest_id])

  const handleMonteCarlo = () => {
    fetch(`http://127.0.0.1:8000/backtests/${backtest_id}/monte-carlo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to run Monte Carlo simulation')
        }
        return response.json()
      })
      .then(data => setMonteCarloResults(data.monte_carlo_results))
      .catch(error => setError(error.message))
  }

  const handleTimeSeriesDecomposition = () => {
    fetch(`http://127.0.0.1:8000/backtests/${backtest_id}/time-series-decomposition`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to run Time Series Decomposition')
        }
        return response.json()
      })
      .then(data => setTimeSeriesDecompositionResults(data))
      .catch(error => setError(error.message))
  }

  if (error) {
    return <div style={{ color: 'red' }}>{error}</div>
  }

  if (!backtest) {
    return <div>Loading...</div>
  }

  // Prepare data for equity curve
  const trades = JSON.parse(backtest.trades)
  const equityCurve = []
  let currentEquity = 10000; // Starting equity, adjust as needed

  trades.forEach(trade => {
    currentEquity += trade.Profit; // Assuming 'Profit' key exists in trade data
    equityCurve.push(currentEquity);
  });

  const equityTrace = {
    x: Array.from(Array(equityCurve.length).keys()), // Simple index for now
    y: equityCurve,
    mode: 'lines',
    name: 'Equity Curve',
  };

  const layout = {
    title: 'Equity Curve',
    xaxis: { title: 'Trade Number' },
    yaxis: { title: 'Equity' },
  };

  return (
    <div>
      <h2>Backtest Details (ID: {backtest.id})</h2>
      <p>Script ID: {backtest.script_id}</p>
      <p>Market: {backtest.market}</p>
      <p>Start Time: {new Date(backtest.start_time).toLocaleString()}</p>
      <p>End Time: {new Date(backtest.end_time).toLocaleString()}</p>
      <p>ROI: {backtest.roi.toFixed(2)}%</p>
      <p>Max Drawdown: {backtest.max_drawdown.toFixed(2)}%</p>
      <p>Sharpe Ratio: {backtest.sharpe_ratio.toFixed(2)}</p>
      <p>Sortino Ratio: {backtest.sortino_ratio.toFixed(2)}</p>
      <p>Qualitative Assessment: {backtest.qualitative_assessment}</p>

      <h3>Equity Curve</h3>
      <Plot
        data={[equityTrace]}
        layout={layout}
        style={{ width: '100%', height: '400px' }}
      />

      <h3>Trades</h3>
      <pre>{JSON.stringify(JSON.parse(backtest.trades), null, 2)}</pre>

      <h3>Log</h3>
      <pre>{JSON.stringify(JSON.parse(backtest.log), null, 2)}</pre>

      <hr />
      <h3>Advanced Analysis</h3>
      <div>
        <button onClick={handleMonteCarlo}>Run Monte Carlo Simulation</button>
        {monteCarloResults && (
          <div>
            <h4>Monte Carlo Simulation Results:</h4>
            <Plot
              data={[
                {
                  x: Array.from(Array(monteCarloResults.length).keys()),
                  y: monteCarloResults,
                  type: 'histogram',
                  name: 'Monte Carlo Results',
                },
              ]}
              layout={{ title: 'Monte Carlo Simulation of Final Equity' }}
              style={{ width: '100%', height: '400px' }}
            />
          </div>
        )}
      </div>
      <div>
        <button onClick={handleTimeSeriesDecomposition}>Run Time Series Decomposition</button>
        {timeSeriesDecompositionResults && (
          <div>
            <h4>Time Series Decomposition Results:</h4>
            <Plot
              data={[
                {
                  x: Array.from(Array(timeSeriesDecompositionResults.observed.length).keys()),
                  y: timeSeriesDecompositionResults.observed,
                  mode: 'lines',
                  name: 'Observed',
                },
                {
                  x: Array.from(Array(timeSeriesDecompositionResults.trend.length).keys()),
                  y: timeSeriesDecompositionResults.trend,
                  mode: 'lines',
                  name: 'Trend',
                },
                {
                  x: Array.from(Array(timeSeriesDecompositionResults.seasonal.length).keys()),
                  y: timeSeriesDecompositionResults.seasonal,
                  mode: 'lines',
                  name: 'Seasonal',
                },
                {
                  x: Array.from(Array(timeSeriesDecompositionResults.resid.length).keys()),
                  y: timeSeriesDecompositionResults.resid,
                  mode: 'lines',
                  name: 'Residual',
                },
              ]}
              layout={{ title: 'Time Series Decomposition' }}
              style={{ width: '100%', height: '600px' }}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default BacktestDetails
