import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import './App.css'
import LabDetails from './LabDetails'
import BacktestHistory from './BacktestHistory'
import BacktestDetails from './BacktestDetails'
import CorrelationMatrix from './CorrelationMatrix'

function LabList() {
  const [labs, setLabs] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/labs')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch labs')
        }
        return response.json()
      })
      .then(data => setLabs(data))
      .catch(error => setError(error.message))
  }, [])

  if (error) {
    return <div style={{ color: 'red' }}>{error}</div>
  }

  return (
    <div>
      <h2>Labs</h2>
      <ul>
        {labs.map(lab => (
          <li key={lab.lab_id}>
            <Link to={`/labs/${lab.lab_id}`}>{lab.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

function App() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [host, setHost] = useState('127.0.0.1')
  const [port, setPort] = useState(8090)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/status')
      .then(response => response.json())
      .then(data => setStatus(data.status))
      .catch(error => setError(error.message))
  }, [])

  const handleLogin = () => {
    const loginData = status === 'needs_creds' ? { email, password } : {}
    if (status === 'needs_server') {
      loginData.host = host
      loginData.port = port
    }

    fetch('http://127.0.0.1:8000/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginData)
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Login failed')
        }
        alert('Login successful!')
        setStatus('ok')
      })
      .catch(error => setError(error.message))
  }

  if (status === 'needs_creds') {
    return (
      <div className="App">
        <h2>Enter Credentials</h2>
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        <button onClick={handleLogin}>Login</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>
    )
  }

  if (status === 'needs_server') {
    return (
      <div className="App">
        <h2>Enter Server Details</h2>
        <input type="text" placeholder="Host" value={host} onChange={e => setHost(e.target.value)} />
        <input type="number" placeholder="Port" value={port} onChange={e => setPort(e.target.value)} />
        <button onClick={handleLogin}>Connect</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>
    )
  }

  if (status === 'ok') {
    return (
      <Router>
        <div className="App">
          <nav>
            <Link to="/">Labs</Link> | <Link to="/backtests">Backtest History</Link> | <Link to="/correlation">Correlation Analysis</Link>
          </nav>
          <Routes>
            <Route path="/" element={<LabList />} />
            <Route path="/labs/:lab_id" element={<LabDetails />} />
            <Route path="/backtests" element={<BacktestHistory />} />
            <Route path="/backtests/:backtest_id" element={<BacktestDetails />} />
            <Route path="/correlation" element={<CorrelationMatrix />} />
          </Routes>
        </div>
      </Router>
    )
  }

  return <div className="App">Loading...</div>
}

export default App
