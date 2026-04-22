import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

function Signup() {
  const { signUp } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const handleSignup = async () => {
    if (!email || !password) {
      setErrorMessage('Please enter email and password')
      return
    }

    setLoading(true)
    setErrorMessage('')

    const { data, error } = await signUp(email, password)

    if (error) {
      setErrorMessage(error.message)
      setLoading(false)
      return
    }

    if (data.session) {
      navigate('/app')
    } else {
      navigate('/login', {
        state: {
          message: 'Signup successful. Check your email for a confirmation link, then log in.',
        },
      })
    }

    setLoading(false)
  }

  return (
    <div style={{ textAlign: 'center', marginTop: '100px' }}>
      <h2>Signup</h2>

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        style={{ display: 'block', margin: '10px auto', padding: '8px' }}
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={{ display: 'block', margin: '10px auto', padding: '8px' }}
      />

      <button
        onClick={handleSignup}
        disabled={loading}
        style={{ padding: '10px 20px', marginTop: '10px' }}
      >
        {loading ? 'Signing up...' : 'Signup'}
      </button>

      {errorMessage && (
        <p style={{ color: 'red', marginTop: '12px' }}>{errorMessage}</p>
      )}

      <div style={{ marginTop: '20px' }}>
        <p>Already have an account?</p>
        <button onClick={() => navigate('/login')}>
          Go to Login
        </button>
      </div>
    </div>
  )
}

export default Signup
