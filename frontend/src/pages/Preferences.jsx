import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowRight, MapPin, Plus, ToggleLeft, ToggleRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const _motion = motion
void _motion

const ROLE_OPTIONS = ['Frontend', 'Backend', 'Full Stack', 'ML/AI', 'Data Science', 'DevOps']
const LOCATION_OPTIONS = ['Bangalore', 'Mumbai', 'Delhi NCR', 'Hyderabad', 'Remote']

function Chip({ active, children, onClick }) {
  return (
    <motion.button
      type="button"
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className={`rounded-full border px-4 py-2 text-sm font-medium transition duration-200 ${
        active
          ? 'border-cyan-300/40 bg-cyan-400/15 text-cyan-100 shadow-[0_0_24px_rgba(34,211,238,0.18)]'
          : 'border-white/10 bg-white/5 text-slate-300 hover:border-cyan-300/20 hover:bg-white/10 hover:text-white'
      }`}
    >
      {children}
    </motion.button>
  )
}

export default function Preferences() {
  const navigate = useNavigate()
  const [selectedRoles, setSelectedRoles] = useState([])
  const [selectedLocations, setSelectedLocations] = useState([])
  const [customLocation, setCustomLocation] = useState('')
  const [remoteOnly, setRemoteOnly] = useState(false)

  const maxRolesReached = selectedRoles.length >= 3
  const maxLocationsReached = selectedLocations.length >= 5

  const toggleRole = (role) => {
    setSelectedRoles((current) => {
      if (current.includes(role)) {
        return current.filter((item) => item !== role)
      }

      if (current.length >= 3) {
        return current
      }

      return [...current, role]
    })
  }

  const toggleLocation = (location) => {
    setSelectedLocations((current) => {
      if (current.includes(location)) {
        return current.filter((item) => item !== location)
      }

      if (current.length >= 5) {
        return current
      }

      return [...current, location]
    })
  }

  const addCustomLocation = () => {
    const value = customLocation.trim()
    if (!value || selectedLocations.includes(value) || selectedLocations.length >= 5) return
    setSelectedLocations((current) => [...current, value])
    setCustomLocation('')
  }

  const handleCustomKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      addCustomLocation()
    }
  }

  const canGenerate = useMemo(() => selectedRoles.length > 0, [selectedRoles])

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#020617] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(59,130,246,0.14),transparent_28%),linear-gradient(180deg,#020617_0%,#020617_100%)]" />
      <motion.div
        animate={{ opacity: [0.28, 0.6, 0.28], scale: [1, 1.05, 1] }}
        transition={{ duration: 9, repeat: Infinity, ease: 'easeInOut' }}
        className="pointer-events-none absolute left-1/2 top-10 h-[32rem] w-[32rem] -translate-x-1/2 rounded-full bg-cyan-400/10 blur-3xl"
      />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
        <motion.section
          initial={{ opacity: 0, y: 24, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.55, ease: 'easeOut' }}
          className="w-full max-w-4xl overflow-hidden rounded-[32px] border border-white/10 bg-white/5 shadow-[0_30px_120px_rgba(0,0,0,0.6)] backdrop-blur-xl"
        >
          <div className="border-b border-white/10 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 px-6 py-8 sm:px-10">
            <p className="text-xs font-medium uppercase tracking-[0.34em] text-cyan-300/80">
              InternPilot
            </p>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                  Set your preferences
                </h1>
                <p className="mt-3 text-sm text-slate-300 sm:text-base">Help us match you better</p>
              </div>
              <div className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-sm font-medium text-cyan-100">
                Step 2 of 2
              </div>
            </div>
          </div>

          <div className="px-6 py-8 sm:px-10 sm:py-10">
            <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
              <motion.div
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
                className="rounded-[28px] border border-white/10 bg-white/5 p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]"
              >
                <div className="mb-5">
                  <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
                    Roles
                  </p>
                  <h2 className="mt-2 text-xl font-semibold text-white">
                    Choose up to 3 focus areas
                  </h2>
                </div>

                <div className="flex flex-wrap gap-3">
                  {ROLE_OPTIONS.map((role) => (
                    <Chip key={role} active={selectedRoles.includes(role)} onClick={() => toggleRole(role)}>
                      {role}
                    </Chip>
                  ))}
                </div>

                <p className="mt-4 text-sm text-slate-400">
                  {maxRolesReached
                    ? 'You’ve selected the maximum number of roles.'
                    : `${selectedRoles.length}/3 selected`}
                </p>

                <div className="mt-8">
                  <div className="mb-5 flex items-center gap-2">
                    <MapPin size={16} className="text-cyan-300" />
                    <div>
                      <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
                        Locations
                      </p>
                      <h2 className="mt-1 text-xl font-semibold text-white">
                        Add up to 5 locations
                      </h2>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {LOCATION_OPTIONS.map((location) => (
                      <Chip
                        key={location}
                        active={selectedLocations.includes(location)}
                        onClick={() => toggleLocation(location)}
                      >
                        {location}
                      </Chip>
                    ))}
                  </div>

                  <div className="mt-4 flex gap-3">
                    <input
                      value={customLocation}
                      onChange={(e) => setCustomLocation(e.target.value)}
                      onKeyDown={handleCustomKeyDown}
                      placeholder="Add location"
                      className="min-w-0 flex-1 rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white placeholder:text-slate-500 outline-none transition focus:border-cyan-400/40 focus:ring-2 focus:ring-cyan-400/15"
                    />
                    <motion.button
                      type="button"
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={addCustomLocation}
                      disabled={maxLocationsReached}
                      className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm font-medium text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <Plus size={16} />
                      Add
                    </motion.button>
                  </div>

                  <p className="mt-4 text-sm text-slate-400">
                    {maxLocationsReached
                      ? 'You’ve selected the maximum number of locations.'
                      : `${selectedLocations.length}/5 selected`}
                  </p>

                  <div className="mt-8 rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
                          Work Type
                        </p>
                        <h3 className="mt-2 text-lg font-semibold text-white">Remote first</h3>
                      </div>
                      <button
                        type="button"
                        onClick={() => setRemoteOnly((value) => !value)}
                        className="inline-flex items-center gap-2 text-sm font-medium text-slate-200 transition hover:text-white"
                      >
                        {remoteOnly ? (
                          <ToggleRight className="text-cyan-300" />
                        ) : (
                          <ToggleLeft className="text-slate-500" />
                        )}
                        <span>{remoteOnly ? 'Enabled' : 'Optional'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: 'easeOut', delay: 0.05 }}
                className="flex flex-col justify-between rounded-[28px] border border-white/10 bg-slate-950/55 p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"
              >
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
                    Summary
                  </p>
                  <h2 className="mt-2 text-xl font-semibold text-white">Your current setup</h2>

                  <div className="mt-6 space-y-4">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Roles</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {selectedRoles.length ? (
                          selectedRoles.map((role) => (
                            <span
                              key={role}
                              className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 py-1.5 text-xs font-medium text-cyan-100"
                            >
                              {role}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-slate-500">No roles selected yet</span>
                        )}
                      </div>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Locations</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {selectedLocations.length ? (
                          selectedLocations.map((location) => (
                            <span
                              key={location}
                              className="rounded-full border border-blue-300/20 bg-blue-400/10 px-3 py-1.5 text-xs font-medium text-blue-100"
                            >
                              {location}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-slate-500">No locations selected yet</span>
                        )}
                      </div>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                        Work Type
                      </p>
                      <p className="mt-3 text-sm text-slate-200">
                        {remoteOnly ? 'Remote only' : 'Open to remote or hybrid'}
                      </p>
                    </div>
                  </div>
                </div>

                <motion.button
                  type="button"
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => navigate('/matches')}
                  disabled={!canGenerate}
                  className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-5 py-4 text-sm font-semibold text-slate-950 shadow-[0_0_30px_rgba(34,211,238,0.18)] transition hover:shadow-[0_0_42px_rgba(34,211,238,0.28)] disabled:cursor-not-allowed disabled:bg-cyan-400/40 disabled:text-slate-950/70"
                >
                  Generate Matches
                  <ArrowRight size={16} />
                </motion.button>
              </motion.div>
            </div>
          </div>
        </motion.section>
      </div>
    </main>
  )
}
