import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'

function Matches() {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchMatches = async () => {
      try {
        const res = await api.get('/matches')
        setMatches(res.data.matches)
      } catch (err) {
        console.error('Error fetching matches:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchMatches()
  }, [])

  if (loading) {
    return (
      <div style={styles.center}>
        <h3>🔄 Finding best matches for you...</h3>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      
      {/* Header */}
      <div style={styles.header}>
        <button onClick={() => navigate('/')} style={styles.backButton}>
          ← Back
        </button>
        <h2>🎯 Your Matches</h2>
      </div>

      {/* Empty State */}
      {matches.length === 0 ? (
        <div style={styles.center}>
          <p>No matches yet.</p>
          <p>Upload your resume & set preferences.</p>
        </div>
      ) : (
        matches.map((job, idx) => (
          <div key={idx} style={styles.card}>
            
            {/* Title */}
            <h3 style={styles.title}>{job.title}</h3>

            {/* Company + Location */}
            <p style={styles.subtitle}>
              {job.company} • {job.location}
            </p>

            {/* Score */}
            <div style={styles.scoreText}>
              Match Score: <strong>{job.score}%</strong>
            </div>

            {/* Progress Bar */}
            <div style={styles.progressBar}>
              <div
                style={{
                  ...styles.progressFill,
                  width: `${job.score}%`
                }}
              />
            </div>

            {/* Reasons */}
            <div style={styles.reasonBox}>
              <strong>Why this matches:</strong>
              <ul style={styles.reasonList}>
                {job.why.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>

            {/* 🔥 Future Feature Button */}
            <button style={styles.applyButton}>
              Generate Email ✉️
            </button>

          </div>
        ))
      )}
    </div>
  )
}

export default Matches

// 🎨 Styles
const styles = {
  container: {
    maxWidth: '700px',
    margin: '0 auto',
    padding: '20px',
    color: 'white'
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '20px'
  },
  backButton: {
    padding: '8px 12px',
    background: '#222',
    border: 'none',
    borderRadius: '6px',
    color: 'white',
    cursor: 'pointer'
  },
  center: {
    textAlign: 'center',
    marginTop: '50px'
  },
  card: {
    background: '#111',
    border: '1px solid #2a2a2a',
    borderRadius: '12px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.4)'
  },
  title: {
    marginBottom: '5px'
  },
  subtitle: {
    color: '#aaa',
    marginBottom: '10px'
  },
  scoreText: {
    marginBottom: '8px'
  },
  progressBar: {
    height: '10px',
    background: '#222',
    borderRadius: '10px',
    overflow: 'hidden',
    marginBottom: '12px'
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #4caf50, #8bc34a)'
  },
  reasonBox: {
    marginTop: '10px',
    marginBottom: '15px'
  },
  reasonList: {
    marginTop: '5px',
    paddingLeft: '18px',
    color: '#ccc'
  },
  applyButton: {
    padding: '10px',
    width: '100%',
    borderRadius: '8px',
    border: 'none',
    background: '#4caf50',
    color: 'white',
    cursor: 'pointer',
    fontWeight: 'bold'
  }
}