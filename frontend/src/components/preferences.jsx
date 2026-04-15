import { useEffect, useState } from 'react'
import api from '../lib/api'
import { useAuth } from '../context/AuthContext'

const ROLES = [
  'Backend Intern',
  'Frontend Intern',
  'Full Stack Intern',
  'ML/AI Intern',
  'Data Science Intern',
  'DevOps Intern',
  'Mobile Intern',
]

const LOCATIONS = [
  'Bangalore',
  'Mumbai',
  'Delhi NCR',
  'Pune',
  'Hyderabad',
  'Chennai',
  'Remote',
]

function Preferences() {
  const [selectedRoles, setSelectedRoles] = useState([])
  const [selectedLocations, setSelectedLocations] = useState([])
  const [remoteOk, setRemoteOk] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    const loadPreferences = async () => {
      if (!isAuthenticated) {
        return
      }

      try {
        const res = await api.get('/preferences/me')
        const prefs = res.data.preferences

        if (!prefs) {
          return
        }

        setSelectedRoles(prefs.preferred_roles || [])
        setSelectedLocations(prefs.preferred_locations || [])
        setRemoteOk(!!prefs.remote_ok)
      } catch (err) {
        if (err.response?.status !== 404) {
          setError(err.response?.data?.detail || 'Failed to load preferences')
        }
      }
    }

    loadPreferences()
  }, [isAuthenticated])

  const toggleItem = (item, list, setList) => {
    if (list.includes(item)) {
      setList(list.filter((value) => value !== item))
    } else {
      setList([...list, item])
    }
  }

  const handleSave = async () => {
    if (!isAuthenticated) {
      setError('Please log in before saving preferences')
      return
    }

    if (selectedRoles.length === 0 || selectedLocations.length === 0) {
      setError('Please select at least one role and location')
      return
    }

    try {
      await api.post('/preferences/save', {
        preferred_roles: selectedRoles,
        preferred_locations: selectedLocations,
        remote_ok: remoteOk,
      })

      setSaved(true)
      setError('')
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Your session expired. Please log in again.')
      } else {
        setError(err.response?.data?.detail || 'Failed to save preferences')
      }
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Your Preferences</h2>

      <div style={{ marginBottom: '30px' }}>
        <h3>Preferred Roles</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {ROLES.map((role) => (
            <button
              key={role}
              onClick={() => toggleItem(role, selectedRoles, setSelectedRoles)}
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: '2px solid #007bff',
                backgroundColor: selectedRoles.includes(role) ? '#007bff' : 'white',
                color: selectedRoles.includes(role) ? 'white' : '#007bff',
                cursor: 'pointer',
              }}
            >
              {role}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: '30px' }}>
        <h3>Preferred Locations</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {LOCATIONS.map((loc) => (
            <button
              key={loc}
              onClick={() => toggleItem(loc, selectedLocations, setSelectedLocations)}
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: '2px solid #28a745',
                backgroundColor: selectedLocations.includes(loc) ? '#28a745' : 'white',
                color: selectedLocations.includes(loc) ? 'white' : '#28a745',
                cursor: 'pointer',
              }}
            >
              {loc}
            </button>
          ))}
        </div>
      </div>

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
      {saved && <p style={{ color: 'green' }}>Preferences saved.</p>}

      <button
        onClick={handleSave}
        style={{
          padding: '12px 30px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          fontSize: '16px',
        }}
      >
        Save Preferences
      </button>
    </div>
  )
}

export default Preferences
