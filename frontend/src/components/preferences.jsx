import { useEffect, useState } from 'react'
import api from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { motion } from 'framer-motion'
import { InlineAlert } from './ui/feedback'

const ROLES = [
  'Backend Intern',
  'Frontend Intern',
  'Full Stack Intern',
  'ML/AI Intern',
  'Data Science Intern',
  'DevOps Intern',
  'Mobile Intern',
]

const LOCATIONS = [
  // Tier 1
  'Bangalore',
  'Mumbai', 
  'Delhi NCR',
  'Pune',
  'Hyderabad',
  'Chennai',
  // Tier 2
  'Kolkata',
  'Ahmedabad',
  'Jaipur',
  'Chandigarh',
  'Kochi',
  'Indore',
  'Bhubaneswar',
  'Coimbatore',
  'Vizag',
  'Noida',
  // Special
  'Remote',
  'Hybrid',
  'Pan India',
]

const DOMAINS = [
  'Backend',
  'Frontend', 
  'Full Stack',
  'ML/AI',
  'Data Science',
  'DevOps',
  'Mobile',
]

const STIPEND_OPTIONS = [
  { label: 'Any', value: 0 },
  { label: '₹5k+/mo', value: 5000 },
  { label: '₹10k+/mo', value: 10000 },
  { label: '₹20k+/mo', value: 20000 },
]

function Preferences() {
  const [selectedRoles, setSelectedRoles] = useState([])
  const [selectedDomains, setSelectedDomains] = useState([])
  const [selectedLocations, setSelectedLocations] = useState([])
  const [stipendMin, setStipendMin] = useState(0)
  const [remoteOk, setRemoteOk] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    const loadPreferences = async () => {
      if (!isAuthenticated) {
        return
      }

      setLoading(true)
      try {
        const res = await api.get('/preferences/me')
        const prefs = res.data.preferences

        if (!prefs) {
          return
        }

        setSelectedRoles(prefs.preferred_roles || [])
        setSelectedDomains(prefs.preferred_domains || [])
        setSelectedLocations(prefs.preferred_locations || [])
        setStipendMin(prefs.stipend_min || 0)
        setRemoteOk(!!prefs.remote_ok)
      } catch (err) {
        if (err.response?.status !== 404) {
          setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to load preferences')
        }
      } finally {
        setLoading(false)
      }
    }

    loadPreferences()
  }, [isAuthenticated])

  const toggleItem = (item, list, setList, maxItems) => {
    if (list.includes(item)) {
      setList(list.filter((value) => value !== item))
    } else if (!maxItems || list.length < maxItems) {
      setList([...list, item])
    } else {
      setError(`Pick up to ${maxItems} domains`)
    }
  }

  const handleSave = async () => {
    if (!isAuthenticated) {
      setError('Please log in before saving preferences')
      return
    }

    if (selectedRoles.length === 0 || selectedLocations.length === 0) {
      setError('Please select at least one role and location')
      return
    }

    setSaving(true)
    setError('')
    setSaved(false)

    try {
      await api.post('/preferences/save', {
        preferred_roles: selectedRoles,
        preferred_locations: selectedLocations,
        preferred_domains: selectedDomains,
        stipend_min: stipendMin,
        remote_ok: remoteOk,
      })

      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Your session expired. Please log in again.')
      } else {
        setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to save preferences')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.aside
      initial={{ opacity: 0, x: 18 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.45, delay: 0.1, ease: 'easeOut' }}
      className="h-fit rounded-[24px] border border-white/10 bg-white/5 p-5 shadow-lg shadow-black/20 backdrop-blur sm:p-6"
    >
      <div className="mb-6">
        <div className="mb-2 inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.24em] text-slate-300">
          Preferences
        </div>
        <h2 className="text-xl font-semibold text-white">Tune your target internships</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          Save the roles and locations you actually want so your matches stay focused.
        </p>
      </div>

      <div className="mb-7">
        <h3 className="mb-3 text-sm font-medium text-slate-200">Preferred Roles</h3>
        <div className="flex flex-wrap gap-2">
          {ROLES.map((role) => (
            <motion.button
              key={role}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleItem(role, selectedRoles, setSelectedRoles)}
              className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                selectedRoles.includes(role)
                  ? 'border-blue-400/40 bg-blue-500 text-white shadow-lg shadow-blue-950/35'
                  : 'border-white/10 bg-slate-900/70 text-slate-300 hover:border-blue-300/30 hover:text-white'
              }`}
            >
              {role}
            </motion.button>
          ))}
        </div>
      </div>

      <div className="mb-7">
        <h3 className="mb-3 text-sm font-medium text-slate-200">Target Domain</h3>
        <p className="mb-3 text-xs text-slate-500">
          Pick up to 3. Leave empty to auto-detect from your resume.
        </p>
        <div className="flex flex-wrap gap-2">
          {DOMAINS.map((domain) => (
            <motion.button
              key={domain}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleItem(domain, selectedDomains, setSelectedDomains, 3)}
              className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                selectedDomains.includes(domain)
                  ? 'border-violet-400/40 bg-violet-500 text-white shadow-lg shadow-violet-950/35'
                  : 'border-white/10 bg-slate-900/70 text-slate-300 hover:border-violet-300/30 hover:text-white'
              }`}
            >
              {domain}
            </motion.button>
          ))}
        </div>
      </div>

      <div className="mb-7">
        <h3 className="mb-3 text-sm font-medium text-slate-200">Preferred Locations</h3>
        <div className="flex flex-wrap gap-2">
          {LOCATIONS.map((loc) => (
            <motion.button
              key={loc}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleItem(loc, selectedLocations, setSelectedLocations)}
              className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                selectedLocations.includes(loc)
                  ? 'border-emerald-400/40 bg-emerald-500 text-white shadow-lg shadow-emerald-950/35'
                  : 'border-white/10 bg-slate-900/70 text-slate-300 hover:border-emerald-300/30 hover:text-white'
              }`}
            >
              {loc}
            </motion.button>
          ))}
        </div>
      </div>

      <div className="mb-7">
        <h3 className="mb-3 text-sm font-medium text-slate-200">Minimum Stipend</h3>
        <div className="flex flex-wrap gap-2">
          {STIPEND_OPTIONS.map((option) => (
            <motion.button
              key={option.value}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setStipendMin(option.value)}
              className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                stipendMin === option.value
                  ? 'border-emerald-400/40 bg-emerald-500 text-white shadow-lg shadow-emerald-950/35'
                  : 'border-white/10 bg-slate-900/70 text-slate-300 hover:border-emerald-300/30 hover:text-white'
              }`}
            >
              {option.label}
            </motion.button>
          ))}
        </div>
      </div>

      <label className="mb-6 flex cursor-pointer items-center gap-3 rounded-2xl border border-white/10 bg-slate-900/60 px-4 py-3 text-sm text-slate-200">
        <span className="relative flex h-5 w-5 items-center justify-center">
          <input
            type="checkbox"
            checked={remoteOk}
            onChange={(e) => setRemoteOk(e.target.checked)}
            className="peer sr-only"
          />
          <span className="h-5 w-5 rounded border border-white/20 bg-slate-950 peer-checked:border-emerald-400 peer-checked:bg-emerald-500" />
          <span className="pointer-events-none absolute text-xs font-bold text-white opacity-0 peer-checked:opacity-100">
            ✓
          </span>
        </span>
        Open to remote work
      </label>

      {error ? <InlineAlert tone="error" message={error} className="mb-4" /> : null}
      {saved && !error ? <InlineAlert tone="success" message="Preferences saved." className="mb-4" /> : null}

      <motion.button
        whileHover={saving ? undefined : { scale: 1.03 }}
        whileTap={saving ? undefined : { scale: 0.98 }}
        onClick={handleSave}
        disabled={saving || loading}
        className="inline-flex w-full items-center justify-center rounded-2xl bg-blue-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-950/35 transition hover:bg-blue-400 disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {saving ? 'Saving...' : 'Save Preferences'}
      </motion.button>
    </motion.aside>
  )
}

export default Preferences
