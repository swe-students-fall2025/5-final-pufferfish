import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [apiStatus, setApiStatus] = useState('')

  const handleClick = async () => {
    setCount((count) => count + 1)

    try {
      const response = await fetch('/api/health')
      if (!response.ok) {
        throw new Error('Request failed')
      }

      const data = await response.json()
      setApiStatus(`API status: ${data.status}`)
    } catch (error) {
      console.error('Error calling /api/health', error)
      setApiStatus('API call failed')
    }
  }

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={handleClick}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
        {apiStatus && <p>{apiStatus}</p>}
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
