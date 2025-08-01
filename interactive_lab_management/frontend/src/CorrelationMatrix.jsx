import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'

function CorrelationMatrix() {
  const [backtests, setBacktests] = useState([])
  const [selectedBacktests, setSelectedBacktests] = useState([])
  const [correlationMatrix, setCorrelationMatrix] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Fetch all backtests to allow selection
    fetch('http://127.0.0.1:8000/backtests')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch backtests for correlation')
        }
        return response.json()
      })
      .then(data => setBacktests(data))
      .catch(error => setError(error.message))
  }, [])

  const handleCheckboxChange = (backtestId) => {
    setSelectedBacktests(prevSelected =>
      prevSelected.includes(backtestId)
        ? prevSelected.filter(id => id !== backtestId)
        : [...prevSelected, backtestId]
    )
  }

  const handleCalculateCorrelation = () => {
    if (selectedBacktests.length < 2) {
      alert('Please select at least two backtests for correlation analysis.')
      return
    }

    fetch('http://127.0.0.1:8000/backtests/correlation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ backtest_ids: selectedBacktests })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to calculate correlation matrix')
        }
        return response.json()
      })
      .then(data => setCorrelationMatrix(data.correlation_matrix))
      .catch(error => setError(error.message))
  }

  if (error) {
    return <div style={{ color: 'red' }}>{error}</div>
  }

  return (
    <div>
      <h2>Correlation Matrix Analysis</h2>
      <h3>Select Backtests:</h3>
      <div>
        {backtests.map(backtest => (
          <div key={backtest.id}>
            <input
              type="checkbox"
              id={`backtest-${backtest.id}`}
              checked={selectedBacktests.includes(backtest.id)}
              onChange={() => handleCheckboxChange(backtest.id)}
            />
            <label htmlFor={`backtest-${backtest.id}`}>
              {backtest.script_id} - {backtest.market} (ROI: {backtest.roi.toFixed(2)}%)
            </label>
          </div>
        ))}
      </div>
      <button onClick={handleCalculateCorrelation}>Calculate Correlation</button>

      {correlationMatrix && (
        <div>
          <h3>Correlation Matrix:</h3>
          <Plot
            data={[
              {
                z: Object.values(correlationMatrix).map(row => Object.values(row)),
                x: Object.keys(correlationMatrix),
                y: Object.keys(Object.values(correlationMatrix)[0]),
                type: 'heatmap',
                colorscale: 'Viridis',
              },
            ]}
            layout={{
              title: 'Backtest Correlation Heatmap',
              xaxis: { title: 'Backtest' },
              yaxis: { title: 'Backtest' },
            }}
            style={{ width: '100%', height: '600px' }}
          />
        </div>
      )}
    </div>
  )
}

export default CorrelationMatrix
