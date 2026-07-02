import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import SignInFlow from './ui/sign-in-flow'
import { CenterLoader } from './ui/feedback'

export default function Login() {
  const navigate = useNavigate()
  const { signIn, isAuthenticated, loading } = useAuth()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/app', { replace: true })
    }
  }, [isAuthenticated, loading, navigate])

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

  if (loading) {
    return <CenterLoader title="Checking session" subtitle="Preparing your secure sign-in flow..." />
  }

  return <SignInFlow mode="login" onSubmit={handleSubmit} loading={submitting} error={error} />
}
