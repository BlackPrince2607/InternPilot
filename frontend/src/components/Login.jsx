import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useLocation, useNavigate } from 'react-router-dom'

function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const handleLogin = async () => {
    if (!email || !password) {
      setErrorMessage('Please enter email and password')
      return
    }

    setLoading(true)
    setErrorMessage('')

    const { error } = await signIn(email, password)

    if (error) {
      setErrorMessage(error.message)
    } else {
      navigate('/')
    }

    setLoading(false)
  }

  return (
    <div style={{ textAlign: 'center', marginTop: '100px' }}>
      <h2>Login</h2>

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
        onClick={handleLogin}
        disabled={loading}
        style={{ padding: '10px 20px', marginTop: '10px' }}
      >
        {loading ? 'Logging in...' : 'Login'}
      </button>

      {location.state?.message && (
        <p style={{ color: 'green', marginTop: '12px' }}>{location.state.message}</p>
      )}

      {errorMessage && (
        <p style={{ color: 'red', marginTop: '12px' }}>{errorMessage}</p>
      )}

      <div style={{ marginTop: '20px' }}>
        <p>Don't have an account?</p>
        <button onClick={() => navigate('/signup')}>
          Go to Signup
        </button>
      </div>
    </div>
  )
}

export default Login
