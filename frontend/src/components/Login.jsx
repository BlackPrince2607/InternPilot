import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import SignInFlow from './ui/sign-in-flow'

export default function Login() {
  const navigate = useNavigate()
  const { signIn, isAuthenticated } = useAuth()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/app', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleSubmit = async (email, password) => {
    if (!email || !password) {
      setError('Email and password are required.')
      return
    }

    setSubmitting(true)
    setError('')

    try {
      const { error: signInError } = await signIn(email, password)
      if (signInError) {
        setError(signInError.message || 'Unable to sign in.')
        return
      }

      navigate('/app', { replace: true })
    } catch (err) {
      setError(err?.message || 'Unable to sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  return <SignInFlow mode="login" onSubmit={handleSubmit} loading={submitting} error={error} />
}
