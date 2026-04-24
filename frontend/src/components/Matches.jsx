import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'

function Matches() {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const fetchMatches = async () => {
      try {
        setError('')
        const res = await api.get('/matches')
        setMatches(res.data.matches || [])
      } catch (err) {
        console.error('Error fetching matches:', err)
        const errorMsg = err.response?.data?.error || err.response?.data?.detail || err.message || 'Failed to load matches'
        setError(errorMsg)
        setMatches([])
      } finally {
        setLoading(false)
      }
    }

    fetchMatches()
  }, [])

  if (loading) {
    return (
      <div style={styles.center}>
        <div style={styles.loader} />
        <h3>🔄 Finding best matches for you...</h3>
        <p style={{ color: '#888', marginTop: '10px', fontSize: '14px' }}>This may take a few moments</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <button onClick={() => navigate('/app')} style={styles.backButton}>
            ← Back
          </button>
          <h2>🎯 Your Matches</h2>
        </div>
        <div style={styles.errorBox}>
          <p style={{ fontWeight: 'bold', marginBottom: '8px' }}>Unable to load matches</p>
          <p style={{ fontSize: '14px', color: '#ccc' }}>{error}</p>
          <p style={{ fontSize: '13px', color: '#999', marginTop: '12px' }}>Make sure you've uploaded a resume and saved your preferences.</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      
      {/* Header */}
      <div style={styles.header}>
        <button onClick={() => navigate('/app')} style={styles.backButton}>
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
        matches.map((job) => (
          <div key={job.job_id || `${job.title}-${job.company}`} style={styles.card}>
            
            {/* Title */}
            <h3 style={styles.title}>{job.title}</h3>

            {/* Company + Location */}
            <p style={styles.subtitle}>
              {job.company || 'Unknown Company'} • {job.location || 'Unknown Location'}
            </p>

            {/* Score */}
            <div style={styles.scoreText}>
              Match Score: <strong>{job.final_score}%</strong>
            </div>

            {/* Progress Bar */}
            <div style={styles.progressBar}>
              <div
                style={{
                  ...styles.progressFill,
                  width: `${job.final_score}%`
                }}
              />
            </div>

            <div style={styles.metaRow}>
              <span>Confidence: {job.confidence_level || 'Medium'}</span>
              <span>Domain: {job.domain || 'general'}</span>
            </div>

            {job.matched_skills?.length ? (
              <div style={styles.tagRow}>
                {job.matched_skills.slice(0, 6).map((skill) => (
                  <span key={skill} style={styles.tag}>
                    {skill}
                  </span>
                ))}
              </div>
            ) : null}

            {/* Reasons */}
            <div style={styles.reasonBox}>
              <strong>Why this matches:</strong>
              <ul style={styles.reasonList}>
                {(job.reasons || job.why || []).map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>

            {job.skill_gaps?.length ? (
              <div style={styles.reasonBox}>
                <strong>Skill gaps:</strong>
                <ul style={styles.reasonList}>
                  {job.skill_gaps.map((gap, i) => (
                    <li key={i}>{gap}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {/* 🔥 Future Feature Button */}
            <button
              style={styles.applyButton}
              onClick={async () => {
                try {
                  if (job.job_id) {
                    await api.post('/tracker/record-apply', { job_id: job.job_id })
                  }
                } catch (err) {
                  console.error('Failed to record apply:', err)
                }

                if (job.apply_url) {
                  window.open(job.apply_url, '_blank', 'noopener,noreferrer')
                }
              }}
              disabled={!job.apply_url}
            >
              Apply Now
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
  metaRow: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: '12px',
    color: '#a3a3a3',
    fontSize: '14px',
    marginBottom: '12px'
  },
  center: {
    textAlign: 'center',
    marginTop: '50px'
  },
  loader: {
    display: 'inline-block',
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    border: '4px solid #333',
    borderTop: '4px solid #4caf50',
    marginBottom: '20px'
  },
  errorBox: {
    background: '#ff6b6b',
    border: '1px solid #cc5555',
    borderRadius: '12px',
    padding: '20px',
    marginTop: '20px',
    color: 'white'
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