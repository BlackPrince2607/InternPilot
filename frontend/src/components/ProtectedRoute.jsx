import { useAuth } from '../context/AuthContext'
import { Navigate } from 'react-router-dom'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  // ⏳ While checking session
  if (loading) {
    return <div>Loading...</div>
  }

  // ❌ Not logged in → redirect
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // ✅ Logged in → allow access
  return children
}

export default ProtectedRoute