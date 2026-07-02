import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const [timedOut, setTimedOut] = useState(false)

  useEffect(() => {
    if (!loading) return
    const timer = setTimeout(() => setTimedOut(true), 10000)
    return () => clearTimeout(timer)
  }, [loading])

  if (loading && !timedOut) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-cyan-500/30 border-t-cyan-400 mx-auto" />
          <p className="text-slate-300">Loading...</p>
        </div>
      </div>
    )
  }

  if (timedOut || (!loading && !isAuthenticated)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="text-center max-w-sm px-4">
          <p className="text-white font-semibold text-lg">
            Taking too long
          </p>
          <p className="text-slate-400 mt-2 text-sm">
            Check your connection and try refreshing the page.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 rounded-2xl bg-blue-500 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-400"
          >
            Refresh
          </button>
        </div>
      </div>
    )
  }

  return children
}

export default ProtectedRoute
