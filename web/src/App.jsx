import { useMemo, useRef, useState } from 'react'
import axios from 'axios'
import {
  Chart,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import './App.css'

Chart.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

function App() {
  const [credentials, setCredentials] = useState({
    username: 'demo',
    password: 'demo123',
  })
  const [isConnected, setIsConnected] = useState(false)
  const [statusMessage, setStatusMessage] = useState('')
  const [latestDataset, setLatestDataset] = useState(null)
  const [history, setHistory] = useState([])
  const [authError, setAuthError] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  const client = useMemo(() => {
    if (!credentials.username || !credentials.password) return null
    return axios.create({
      baseURL: API_BASE_URL,
      auth: {
        username: credentials.username,
        password: credentials.password,
      },
    })
  }, [credentials])

  const fetchData = async () => {
    if (!client) {
      setAuthError('Please supply username and password first.')
      return
    }
    setLoading(true)
    setAuthError('')
    try {
      const [latestResponse, historyResponse] = await Promise.all([
        client
          .get('/datasets/latest/')
          .catch((error) => {
            if (error.response && error.response.status === 404) {
              return { data: null }
            }
            throw error
          }),
        client.get('/datasets/history/'),
      ])
      setLatestDataset(latestResponse.data)
      setHistory(historyResponse.data)
      setIsConnected(true)
      setStatusMessage('Connected to backend successfully.')
    } catch (error) {
      setIsConnected(false)
      if (error.response && error.response.status === 401) {
        setAuthError('Authentication failed. Double-check your credentials.')
      } else {
        setAuthError(
          error?.response?.data?.detail ||
            'Unable to reach backend. Is the server running?',
        )
      }
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!client || !selectedFile) {
      setStatusMessage('Pick a CSV file and ensure you are authenticated.')
      return
    }
    setUploading(true)
    setStatusMessage('Uploading CSV ...')
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      const { data } = await client.post('/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setLatestDataset(data)
      await fetchHistoryOnly()
      setStatusMessage(`Uploaded ${selectedFile.name} successfully.`)
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      setStatusMessage(
        error?.response?.data?.detail || 'Upload failed. Please try again.',
      )
    } finally {
      setUploading(false)
    }
  }

  const fetchHistoryOnly = async () => {
    if (!client) return
    try {
      const historyResponse = await client.get('/datasets/history/')
      setHistory(historyResponse.data)
    } catch {
      setStatusMessage('Unable to refresh history right now.')
    }
  }

  const handleDownloadPdf = async (datasetId) => {
    if (!client) return
    try {
      const response = await client.get(`/datasets/${datasetId}/pdf/`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      let derivedName = 'equipment-report.pdf'
      const disposition = response.headers['content-disposition']
      if (disposition) {
        const match = disposition.match(/filename="(.+)"/)
        if (match?.[1]) {
          derivedName = match[1]
        }
      }
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', derivedName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      setStatusMessage('Unable to download PDF right now.')
    }
  }

  const handleSampleLoad = async () => {
    try {
      const response = await fetch('/sample_equipment_data.csv')
      const blob = await response.blob()
      const file = new File([blob], 'sample_equipment_data.csv', {
        type: 'text/csv',
      })
      setSelectedFile(file)
      setStatusMessage('Sample file ready. Press Upload to send it to the API.')
    } catch (error) {
      setStatusMessage('Sample file missing. Please use your own CSV instead.')
    }
  }

  const renderChart = () => {
    if (!latestDataset?.summary?.type_distribution) return null
    const labels = Object.keys(latestDataset.summary.type_distribution)
    if (!labels.length) return null

    const data = {
      labels,
      datasets: [
        {
          label: 'Equipment Count',
          backgroundColor: '#0ea5e9',
          borderColor: '#0284c7',
          borderWidth: 1,
          data: labels.map(
            (label) => latestDataset.summary.type_distribution[label],
          ),
        },
      ],
    }

    return (
      <div className="panel">
        <div className="panel-header">
          <h3>Type Distribution</h3>
        </div>
        <Bar data={data} />
      </div>
    )
  }

  const renderTable = () => {
    if (!latestDataset?.data?.length) return null
    const headers = Object.keys(latestDataset.data[0])
    return (
      <div className="panel">
        <div className="panel-header">
          <h3>Data Preview</h3>
          <span>{latestDataset.data.length} rows</span>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                {headers.map((header) => (
                  <th key={header}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {latestDataset.data.map((row, index) => (
                <tr key={index}>
                  {headers.map((header) => (
                    <td key={header}>{row[header]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  const renderSummaryCards = () => {
    if (!latestDataset?.summary) return null
    const { summary } = latestDataset
    const cards = [
      { label: 'Total Equipment', value: summary.total_equipment },
      { label: 'Avg Flowrate', value: summary.avg_flowrate },
      { label: 'Avg Pressure', value: summary.avg_pressure },
      { label: 'Avg Temperature', value: summary.avg_temperature },
    ]
    return (
      <div className="summary-grid">
        {cards.map((card) => (
          <div key={card.label} className="summary-card">
            <p className="label">{card.label}</p>
            <p className="value">{card.value ?? '—'}</p>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="app-shell">
      <header>
        <div>
          <h1>Chemical Equipment Visualizer</h1>
          <p>Unified dashboard for the Django analytics backend.</p>
        </div>
        <button className="ghost" onClick={fetchData} disabled={loading}>
          {loading ? 'Connecting...' : 'Refresh'}
        </button>
      </header>

      <section className="panel">
        <div className="panel-header">
          <h3>Authenticate</h3>
          <span>
            Backend URL: <code>{API_BASE_URL}</code>
          </span>
        </div>
        <div className="form-grid">
          <label>
            Username
            <input
              value={credentials.username}
              onChange={(event) =>
                setCredentials((prev) => ({
                  ...prev,
                  username: event.target.value,
                }))
              }
              placeholder="demo"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={credentials.password}
              onChange={(event) =>
                setCredentials((prev) => ({
                  ...prev,
                  password: event.target.value,
                }))
              }
              placeholder="demo123"
            />
          </label>
          <button type="button" onClick={fetchData} disabled={loading}>
            {loading ? 'Checking...' : 'Connect'}
          </button>
        </div>
        {authError && <p className="error-text">{authError}</p>}
        {isConnected && !authError && (
          <p className="success-text">{statusMessage}</p>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>CSV Upload</h3>
          <div className="actions">
            <button className="ghost" onClick={handleSampleLoad}>
              Load bundled sample
            </button>
            <button onClick={handleUpload} disabled={uploading || !selectedFile}>
              {uploading ? 'Uploading...' : 'Upload CSV'}
            </button>
          </div>
        </div>
        <div className="upload-row">
          <input
            type="file"
            accept=".csv"
            ref={fileInputRef}
            onChange={(event) => setSelectedFile(event.target.files[0])}
          />
          {selectedFile && <span>{selectedFile.name}</span>}
        </div>
        {statusMessage && <p className="status-text">{statusMessage}</p>}
      </section>

      {renderSummaryCards()}
      <div className="grid-two">
        {renderChart()}
        <div className="panel">
          <div className="panel-header">
            <h3>Upload History</h3>
            <span>Last 5 uploads</span>
          </div>
          {!history.length && <p>No uploads yet.</p>}
          <ul className="history-list">
            {history.map((item) => (
              <li key={item.id}>
                <div>
                  <p className="item-title">{item.file_name}</p>
                  <p className="item-meta">
                    {new Date(item.uploaded_at).toLocaleString()} •{' '}
                    {item.summary?.total_equipment || 0} rows
                  </p>
                </div>
                <button className="ghost" onClick={() => handleDownloadPdf(item.id)}>
                  PDF
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {renderTable()}
    </div>
  )
}

export default App
