import { useState } from 'react'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'

const ROLES = [
  "Backend Intern",
  "Frontend Intern", 
  "Full Stack Intern",
  "ML/AI Intern",
  "Data Science Intern",
  "DevOps Intern",
  "Mobile Intern"
]

const LOCATIONS = [
  "Bangalore",
  "Mumbai",
  "Delhi NCR",
  "Pune",
  "Hyderabad",
  "Chennai",
  "Remote"
]

function Preferences() {
  const [selectedRoles, setSelectedRoles] = useState([])
  const [selectedLocations, setSelectedLocations] = useState([])
  const [remoteOk, setRemoteOk] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const { user } = useAuth()

  const API_URL = 'http://localhost:8000/api/v1'

  const toggleItem = (item, list, setList) => {
    if (list.includes(item)) {
      setList(list.filter(i => i !== item))
    } else {
      setList([...list, item])
    }
  }

  const handleSave = async () => {
    if (selectedRoles.length === 0 || selectedLocations.length === 0) {
      setError('Please select at least one role and location')
      return
    }

    try {
      await axios.post(`${API_URL}/preferences/save`, {
      user_id: user.id,
      preferred_roles,
      preferred_locations,
      remote_ok
    })

      setSaved(true)
      setError('')
    } catch (err) {
      setError('Failed to save preferences')
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Your Preferences</h2>

      {/* Roles */}
      <div style={{ marginBottom: '30px' }}>
        <h3>Preferred Roles</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {ROLES.map(role => (
            <button
              key={role}
              onClick={() => toggleItem(role, selectedRoles, setSelectedRoles)}
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: '2px solid #007bff',
                backgroundColor: selectedRoles.includes(role) ? '#007bff' : 'white',
                color: selectedRoles.includes(role) ? 'white' : '#007bff',
                cursor: 'pointer'
              }}
            >
              {role}
            </button>
          ))}
        </div>
      </div>

      {/* Locations */}
      <div style={{ marginBottom: '30px' }}>
        <h3>Preferred Locations</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {LOCATIONS.map(loc => (
            <button
              key={loc}
              onClick={() => toggleItem(loc, selectedLocations, setSelectedLocations)}
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: '2px solid #28a745',
                backgroundColor: selectedLocations.includes(loc) ? '#28a745' : 'white',
                color: selectedLocations.includes(loc) ? 'white' : '#28a745',
                cursor: 'pointer'
              }}
            >
              {loc}
            </button>
          ))}
        </div>
      </div>

      {/* Remote */}
      <div style={{ marginBottom: '30px' }}>
        <label>
          <input
            type="checkbox"
            checked={remoteOk}
            onChange={(e) => setRemoteOk(e.target.checked)}
            style={{ marginRight: '10px' }}
          />
          Open to Remote Work
        </label>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}
      {saved && <p style={{ color: 'green' }}>✅ Preferences saved!</p>}

      <button
        onClick={handleSave}
        style={{
          padding: '12px 30px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          fontSize: '16px'
        }}
      >
        Save Preferences
      </button>
    </div>
  )
}

export default Preferences