import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

function BacktestHistory() {
  const [backtests, setBacktests] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/backtests')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch backtest history')
        }
        return response.json()
      })
      .then(data => setBacktests(data))
      .catch(error => setError(error.message))
  }, [])

  if (error) {
    return <div style={{ color: 'red' }}>{error}</div>
  }

  return (
    <div>
      <h2>Backtest History</h2>
      <ul>
        {backtests.map(backtest => (
          <li key={backtest.id}>
            <Link to={`/backtests/${backtest.id}`}>
              Script: {backtest.script_id}, Market: {backtest.market}, ROI: {backtest.roi.toFixed(2)}%
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default BacktestHistory
