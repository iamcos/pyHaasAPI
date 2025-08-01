import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'

function LabDetails() {
  const [lab, setLab] = useState(null)
  const [error, setError] = useState(null)
  const [backtestId, setBacktestId] = useState('')
  const [geminiPrompt, setGeminiPrompt] = useState('')
  const [suggestedParams, setSuggestedParams] = useState(null)
  const [templateName, setTemplateName] = useState('')
  const [templates, setTemplates] = useState([])
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [backtestStart, setBacktestStart] = useState('')
  const [backtestEnd, setBacktestEnd] = useState('')
  const [isBacktestRunning, setIsBacktestRunning] = useState(false)
  const pollingIntervalRef = useRef(null)
  const { lab_id } = useParams()

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/labs/${lab_id}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch lab details')
        }
        return response.json()
      })
      .then(data => {
        setLab(data)
        // Fetch templates for this script once lab data is available
        fetchTemplates(data.script_id)
      })
      .catch(error => setError(error.message))
  }, [lab_id])

  const fetchTemplates = (scriptId) => {
    fetch(`http://127.0.0.1:8000/templates?script_id=${scriptId}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch templates')
        }
        return response.json()
      })
      .then(data => setTemplates(data))
      .catch(error => setError(error.message))
  }

  const handleSave = () => {
    fetch(`http://127.0.0.1:8000/labs/${lab_id}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lab)
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to save lab details')
        }
        alert('Lab details saved successfully!')
      })
      .catch(error => setError(error.message))
  }

  const handleInputChange = (event, parameter_key) => {
    const newLab = { ...lab }
    const parameter = newLab.parameters.find(p => p.key === parameter_key)

    // Determine input type and update value accordingly
    if (typeof parameter.options[0] === 'boolean') {
      parameter.options[0] = event.target.checked
    } else if (typeof parameter.options[0] === 'number') {
      parameter.options[0] = parseFloat(event.target.value)
    } else {
      parameter.options[0] = event.target.value
    }
    setLab(newLab)
  }

  const handleProcessBacktest = (btId) => {
    fetch(`http://127.0.0.1:8000/backtests/process?lab_id=${lab_id}&backtest_id=${btId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to process backtest results')
        }
        alert('Backtest results processed successfully!')
      })
      .catch(error => setError(error.message))
  }

  const handleGenerateParams = () => {
    if (!backtestId) {
      alert('Please process a backtest first or provide a backtest ID.')
      return
    }

    fetch(`http://127.0.0.1:8000/gemini/generate-params?prompt=${encodeURIComponent(geminiPrompt)}&backtest_id=${backtestId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to generate parameters')
        }
        return response.json()
      })
      .then(data => setSuggestedParams(data))
      .catch(error => setError(error.message))
  }

  const handleSaveTemplate = () => {
    if (!templateName) {
      alert('Please enter a template name.')
      return
    }
    if (!lab || !lab.script_id || !lab.parameters) {
      alert('Lab data not available to save template.')
      return
    }

    fetch('http://127.0.0.1:8000/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        template_name: templateName,
        script_id: lab.script_id,
        parameters: lab.parameters
      })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to save template')
        }
        alert('Template saved successfully!')
        setTemplateName('')
        fetchTemplates(lab.script_id) // Refresh templates list
      })
      .catch(error => setError(error.message))
  }

  const handleLoadTemplate = () => {
    if (!selectedTemplate) {
      alert('Please select a template to load.')
      return
    }

    fetch(`http://127.0.0.1:8000/templates/${selectedTemplate}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to load template')
        }
        return response.json()
      })
      .then(data => {
        const newLab = { ...lab, parameters: data.parameters_json }
        setLab(newLab)
        alert('Template loaded successfully!')
      })
      .catch(error => setError(error.message))
  }

  const handleStartBacktest = () => {
    if (!backtestStart || !backtestEnd) {
      alert('Please enter both start and end Unix timestamps for the backtest.')
      return
    }

    setIsBacktestRunning(true)
    fetch(`http://127.0.0.1:8000/labs/${lab_id}/start-backtest?start_unix=${backtestStart}&end_unix=${backtestEnd}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to start backtest')
        }
        return response.json()
      })
      .then(data => {
        alert('Backtest started successfully! Polling for completion...')
        // Assuming the response contains the backtest ID or a way to identify it
        // For now, we'll assume the backtest ID is returned directly in data.result.backtest_id
        // You might need to adjust this based on the actual API response
        const startedBacktestId = data.result.backtest_id || lab_id; // Fallback if no specific ID
        setBacktestId(startedBacktestId)
        startPollingBacktestStatus(startedBacktestId)
      })
      .catch(error => {
        setError(error.message)
        setIsBacktestRunning(false)
      })
  }

  const startPollingBacktestStatus = (btId) => {
    pollingIntervalRef.current = setInterval(() => {
      fetch(`http://127.0.0.1:8000/labs/${lab_id}/status`)
        .then(response => response.json())
        .then(data => {
          // Assuming data.status indicates completion. Adjust based on actual API response.
          // For Haas API, LabExecutionUpdate.status == 3 (COMPLETED)
          if (data.status === 3) { 
            clearInterval(pollingIntervalRef.current)
            setIsBacktestRunning(false)
            alert('Backtest completed! Processing results...')
            handleProcessBacktest(btId)
          } else {
            console.log('Backtest still running...', data.status)
          }
        })
        .catch(error => {
          console.error('Error polling backtest status:', error)
          clearInterval(pollingIntervalRef.current)
          setIsBacktestRunning(false)
          setError(error.message)
        })
    }, 5000); // Poll every 5 seconds
  }

  const renderParameterInput = (parameter) => {
    const value = parameter.options[0];

    if (typeof value === 'boolean') {
      return (
        <input
          type="checkbox"
          checked={value}
          onChange={e => handleInputChange(e, parameter.key)}
        />
      );
    } else if (typeof value === 'number') {
      return (
        <input
          type="number"
          value={value}
          onChange={e => handleInputChange(e, parameter.key)}
        />
      );
    } else {
      return (
        <input
          type="text"
          value={value}
          onChange={e => handleInputChange(e, parameter.key)}
        />
      );
    }
  };

  if (error) {
    return <div style={{ color: 'red' }}>{error}</div>
  }

  if (!lab) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h2>{lab.name}</h2>
      <p>ID: {lab.lab_id}</p>
      <form>
        {lab.parameters.map(parameter => (
          <div key={parameter.key}>
            <label>{parameter.key}</label>
            {renderParameterInput(parameter)}
          </div>
        ))}
      </form>
      <button onClick={handleSave}>Save Lab Parameters</button>
      <hr />
      <h3>Parameter Templates</h3>
      <div>
        <input
          type="text"
          placeholder="New Template Name"
          value={templateName}
          onChange={e => setTemplateName(e.target.value)}
        />
        <button onClick={handleSaveTemplate}>Save Current as Template</button>
      </div>
      <div>
        <select onChange={e => setSelectedTemplate(e.target.value)} value={selectedTemplate}>
          <option value="">Select a template</option>
          {templates.map(template => (
            <option key={template.id} value={template.id}>
              {template.name}
            </option>
          ))}
        </select>
        <button onClick={handleLoadTemplate}>Load Template</button>
      </div>
      <hr />
      <h3>Start Backtest</h3>
      <div>
        <label>Start Unix Timestamp:</label>
        <input type="number" value={backtestStart} onChange={e => setBacktestStart(e.target.value)} />
      </div>
      <div>
        <label>End Unix Timestamp:</label>
        <input type="number" value={backtestEnd} onChange={e => setBacktestEnd(e.target.value)} />
      </div>
      <button onClick={handleStartBacktest} disabled={isBacktestRunning}>
        {isBacktestRunning ? 'Backtest Running...' : 'Start Backtest'}
      </button>
      <hr />
      <h3>Process Backtest Results</h3>
      <input
        type="text"
        placeholder="Enter Backtest ID"
        value={backtestId}
        onChange={e => setBacktestId(e.target.value)}
      />
      <button onClick={handleProcessBacktest}>Process Backtest</button>
      <hr />
      <h3>Generate Parameters with Gemini</h3>
      <input
        type="text"
        placeholder="Enter prompt for Gemini (e.g., 'more aggressive')"
        value={geminiPrompt}
        onChange={e => setGeminiPrompt(e.target.value)}
      />
      <button onClick={handleGenerateParams}>Generate Parameters</button>
      {suggestedParams && (
        <div>
          <h4>Suggested Parameters:</h4>
          <pre>{JSON.stringify(suggestedParams, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default LabDetails