import { useState, useEffect } from 'react'
import ResumeUploader from './components/ResumeUploader'
import Preferences from './components/preferences'
import './App.css'

function App() {
  const [message, setMessage] = useState('')

  useEffect(() => {
    // Test API connection
    fetch('http://localhost:8000')
      .then(res => res.json())
      .then(data => setMessage(data.message))
      .catch(err => console.error(err))
  }, [])

  return (
    <div className="App">
      <h1>InternPilot AI</h1>
      <ResumeUploader />
      <hr />
      <Preferences />
    </div>
  )
}

export default App
