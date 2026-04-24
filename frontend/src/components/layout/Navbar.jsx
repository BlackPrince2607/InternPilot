import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'

const MotionLink = motion(Link)

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/app' },
  { label: 'Matches', to: '/matches' },
  { label: 'Cold Email', to: '/cold-email' },
  { label: 'Tracker', to: '/tracker' },
]

function linkClasses(active) {
  return `inline-flex items-center border-b-2 px-1 py-2 text-sm font-medium transition ${
    active ? 'border-blue-400 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
  }`
}

function Navbar() {
  const [open, setOpen] = useState(false)
  const { isAuthenticated, user, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  if (!isAuthenticated) {
    return null
  }

  const handleSignOut = async () => {
    await signOut()
    navigate('/')
  }

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <MotionLink
          to="/app"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="text-lg font-semibold tracking-tight text-white"
        >
          InternPilot
        </MotionLink>

        <nav className="hidden items-center gap-6 md:flex">
          {NAV_ITEMS.map((item) => (
            <MotionLink
              key={item.to}
              to={item.to}
              whileHover={{ y: -1 }}
              whileTap={{ y: 0 }}
              className={linkClasses(location.pathname === item.to)}
            >
              {item.label}
            </MotionLink>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <p className="max-w-40 truncate text-sm text-slate-300">{user?.email || 'Unknown user'}</p>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={handleSignOut}
            className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-100 hover:bg-white/10"
          >
            Sign Out
          </motion.button>
        </div>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setOpen((value) => !value)}
          className="rounded-2xl border border-white/10 bg-white/5 p-2 text-slate-100 md:hidden"
          aria-label="Toggle navigation"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </motion.button>
      </div>

      <AnimatePresence>
        {open ? (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden border-t border-white/10 bg-slate-950/90 md:hidden"
          >
            <div className="space-y-3 px-4 py-4 sm:px-6">
              {NAV_ITEMS.map((item) => (
                <MotionLink
                  key={item.to}
                  to={item.to}
                  whileHover={{ x: 2 }}
                  whileTap={{ x: 0 }}
                  onClick={() => setOpen(false)}
                  className={`block rounded-2xl border px-4 py-3 text-sm font-medium ${
                    location.pathname === item.to
                      ? 'border-blue-400/40 bg-blue-500/10 text-white'
                      : 'border-white/10 bg-white/5 text-slate-300'
                  }`}
                >
                  {item.label}
                </MotionLink>
              ))}
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
                <p className="truncate">{user?.email || 'Unknown user'}</p>
              </div>
              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={handleSignOut}
                className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-slate-100"
              >
                Sign Out
              </motion.button>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </header>
  )
}

export default Navbar