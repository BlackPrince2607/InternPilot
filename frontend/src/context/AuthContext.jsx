import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)

  // Get session on load
  useEffect(() => {
    const getSession = async () => {
      const { data } = await supabase.auth.getSession()
      setSession(data.session || null)
      setUser(data.session?.user || null)
      setLoading(false)
    }

    getSession()

    // Listen for auth changes
    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session || null)
        setUser(session?.user || null)
        setLoading(false)
      }
    )

    return () => listener.subscription.unsubscribe()
  }, [])

  // Sign up
  const signUp = async (email, password) => {
    return await supabase.auth.signUp({ email, password })
  }

  // Sign in
  const signIn = async (email, password) => {
    return await supabase.auth.signInWithPassword({ email, password })
  }
  
  // Sign out
  const signOut = async () => {
    const response = await supabase.auth.signOut()
    setSession(null)
    setUser(null)
    return response
  }

  return (
    <AuthContext.Provider
      value={{ user, session, signUp, signIn, signOut, loading, isAuthenticated: !!session }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
