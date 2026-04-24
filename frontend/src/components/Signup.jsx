import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import SignInFlow from './ui/sign-in-flow'

export default function Signup() {
  const navigate = useNavigate()
  const { signUp, isAuthenticated } = useAuth()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

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
    setNotice('')

    try {
      const { data, error: signUpError } = await signUp(email, password)
      if (signUpError) {
        setError(signUpError.message || 'Unable to create account.')
        return
      }

      if (!data?.session) {
        setNotice('Account created. Check your email to verify your account, then sign in.')
        return
      }

      navigate('/app', { replace: true })
    } catch (err) {
      setError(err?.message || 'Unable to create account.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <SignInFlow
      mode="signup"
      onSubmit={handleSubmit}
      loading={submitting}
      error={error || notice}
      messageTone={notice && !error ? 'info' : 'error'}
    />
  )
}
