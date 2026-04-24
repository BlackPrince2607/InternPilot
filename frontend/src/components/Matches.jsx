import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Building2, ChevronDown, MapPin, SearchX } from 'lucide-react'
import api from '../lib/api'
import { InlineAlert } from './ui/feedback'

function scoreTone(score) {
  if (score >= 80) return 'border-emerald-400/25 bg-emerald-500/15 text-emerald-200'
  if (score >= 60) return 'border-blue-400/25 bg-blue-500/15 text-blue-200'
  return 'border-white/15 bg-white/5 text-slate-200'
}

function confidenceTone(level) {
  const normalized = String(level || 'Low').toLowerCase()
  if (normalized === 'high') return 'border-emerald-400/25 bg-emerald-500/15 text-emerald-200'
  if (normalized === 'medium') return 'border-blue-400/25 bg-blue-500/15 text-blue-200'
  return 'border-white/15 bg-white/5 text-slate-300'
}

function Matches() {
  const [allMatches, setAllMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [infoMessage, setInfoMessage] = useState('')
  const [applyFeedback, setApplyFeedback] = useState('')
  const [activeConfidence, setActiveConfidence] = useState('All')
  const [activeDomain, setActiveDomain] = useState('All')
  const [expanded, setExpanded] = useState({})

  const fetchMatches = async () => {
    setLoading(true)
    setError('')
    setApplyFeedback('')
    try {
      const res = await api.get('/matches/')
      setAllMatches(res.data.matches || [])
      setInfoMessage(res.data.meta?.message || '')
    } catch (err) {
      const isTimeout = err.code === 'ECONNABORTED' || (err.message || '').toLowerCase().includes('timeout')
      const msg =
        (isTimeout && 'Matching took too long. Please retry in a few seconds.') ||
        err.response?.data?.error ||
        err.response?.data?.detail ||
        err.message ||
        'Failed to load matches.'
      setError(msg)
      setAllMatches([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMatches()
  }, [])

  const confidences = useMemo(() => {
    const values = new Set(['All'])
    allMatches.forEach((job) => values.add(job.confidence_level || 'Low'))
    return Array.from(values)
  }, [allMatches])

  const domains = useMemo(() => {
    const values = new Set(['All'])
    allMatches.forEach((job) => values.add(job.domain || 'general'))
    return Array.from(values)
  }, [allMatches])

  const filteredMatches = useMemo(() => {
    return allMatches.filter((job) => {
      const confidenceOk = activeConfidence === 'All' || (job.confidence_level || 'Low') === activeConfidence
      const domainOk = activeDomain === 'All' || (job.domain || 'general') === activeDomain
      return confidenceOk && domainOk
    })
  }, [allMatches, activeConfidence, activeDomain])

  const averageScore = useMemo(() => {
    if (!filteredMatches.length) {
      return 0
    }
    const total = filteredMatches.reduce((sum, job) => sum + Number(job.final_score || 0), 0)
    return total / filteredMatches.length
  }, [filteredMatches])

  const handleApply = async (job) => {
    setApplyFeedback('')
    try {
      await api.post('/tracker/record-apply', { job_id: job.job_id })
      setApplyFeedback('Application tracked. Opening role link...')
    } catch {
      setApplyFeedback('Could not track this application, but opening role link now.')
    }

    if (job.apply_url) {
      window.open(job.apply_url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div className="space-y-5">
      <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="rounded-[24px] border border-white/10 bg-slate-900/70 p-6">
        <h1 className="text-3xl font-semibold text-white">Your Matches</h1>
        <p className="mt-2 text-sm text-slate-400">Ranked by AI based on your resume and preferences.</p>
      </motion.section>

      {error ? (
        <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="rounded-[24px] border border-rose-500/30 bg-rose-500/10 p-6">
          <p className="text-lg font-semibold text-rose-100">Unable to load matches</p>
          <p className="mt-2 text-sm text-rose-100/90">{error}</p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={fetchMatches}
            className="mt-4 rounded-2xl bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-400"
          >
            Retry
          </motion.button>
        </motion.section>
      ) : null}

      {infoMessage && !error ? <InlineAlert tone="info" message={infoMessage} /> : null}
      {applyFeedback ? <InlineAlert tone="success" message={applyFeedback} /> : null}

      <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="grid gap-5 rounded-[24px] border border-white/10 bg-white/5 p-6 backdrop-blur sm:grid-cols-2">
        <div>
          <p className="text-sm text-slate-400">Total matches</p>
          <p className="mt-2 text-3xl font-semibold text-white">{filteredMatches.length}</p>
        </div>
        <div>
          <p className="text-sm text-slate-400">Average score</p>
          <p className="mt-2 text-3xl font-semibold text-white">{averageScore.toFixed(1)}%</p>
        </div>
      </motion.section>

      {!loading ? (
        <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="rounded-[24px] border border-white/10 bg-white/5 p-6 backdrop-blur">
          <div className="space-y-4">
            <div>
              <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-400">Confidence</p>
              <div className="flex flex-wrap gap-2">
                {confidences.map((item) => (
                  <motion.button
                    key={`confidence-${item}`}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => setActiveConfidence(item)}
                    className={`rounded-full border px-3 py-1 text-xs ${
                      activeConfidence === item
                        ? 'border-blue-400/30 bg-blue-500/15 text-blue-100'
                        : 'border-white/10 bg-white/5 text-slate-300'
                    }`}
                  >
                    {item}
                  </motion.button>
                ))}
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-400">Domain</p>
              <div className="flex flex-wrap gap-2">
                {domains.map((item) => (
                  <motion.button
                    key={`domain-${item}`}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => setActiveDomain(item)}
                    className={`rounded-full border px-3 py-1 text-xs ${
                      activeDomain === item
                        ? 'border-blue-400/30 bg-blue-500/15 text-blue-100'
                        : 'border-white/10 bg-white/5 text-slate-300'
                    }`}
                  >
                    {item}
                  </motion.button>
                ))}
              </div>
            </div>
          </div>
        </motion.section>
      ) : null}

      {loading ? (
        <section className="grid gap-5 lg:grid-cols-2">
          {Array.from({ length: 6 }).map((_, idx) => (
            <motion.div
              key={`match-skeleton-${idx}`}
              animate={{ opacity: [0.35, 0.75, 0.35] }}
              transition={{ duration: 1.3, repeat: Infinity, delay: idx * 0.15 }}
              className="h-72 rounded-[24px] border border-white/10 bg-slate-900/70 p-6"
            />
          ))}
        </section>
      ) : null}

      {!loading && !error && filteredMatches.length === 0 ? (
        <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="rounded-[24px] border border-dashed border-white/10 bg-white/5 p-8 text-center">
          <SearchX className="mx-auto h-10 w-10 text-slate-400" />
          <h2 className="mt-3 text-xl font-semibold text-white">No matches yet</h2>
          <p className="mt-2 text-sm text-slate-400">Upload your resume and set preferences to see matches.</p>
        </motion.section>
      ) : null}

      {!loading && filteredMatches.length > 0 ? (
        <section className="grid gap-5 lg:grid-cols-2">
          {filteredMatches.map((job) => {
            const score = Number(job.final_score || 0)
            const expandedKey = String(job.job_id || `${job.title}-${job.company}`)
            const isExpanded = !!expanded[expandedKey]
            return (
              <motion.article
                key={expandedKey}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-[24px] border border-white/10 bg-slate-900/70 p-6"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-xl font-semibold text-white">{job.title || 'Untitled role'}</h3>
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${scoreTone(score)}`}>
                    {score.toFixed(1)}%
                  </span>
                </div>

                <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-300">
                  <span className="inline-flex items-center gap-2">
                    <Building2 className="h-4 w-4" />
                    {job.company || 'Unknown company'}
                  </span>
                  <span className="inline-flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    {job.location || 'Unknown location'}
                  </span>
                </div>

                <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-950/70">
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: Math.max(0, Math.min(score / 100, 1)) }}
                    transition={{ duration: 0.4, ease: 'easeOut' }}
                    className="h-full origin-left rounded-full bg-gradient-to-r from-blue-500 to-emerald-400"
                  />
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {(job.matched_skills || []).slice(0, 6).map((skill) => (
                    <span key={`${expandedKey}-match-${skill}`} className="rounded-full border border-blue-400/30 bg-blue-500/15 px-3 py-1 text-xs text-blue-100">
                      {skill}
                    </span>
                  ))}
                  {(job.missing_skills || []).slice(0, 4).map((skill) => (
                    <span key={`${expandedKey}-missing-${skill}`} className="rounded-full border border-rose-400/30 bg-rose-500/15 px-3 py-1 text-xs text-rose-100">
                      {skill}
                    </span>
                  ))}
                </div>

                <motion.button
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => setExpanded((prev) => ({ ...prev, [expandedKey]: !prev[expandedKey] }))}
                  className="mt-4 inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-100"
                >
                  Why this matches
                  <ChevronDown className={`h-4 w-4 transition ${isExpanded ? 'rotate-180' : ''}`} />
                </motion.button>

                <AnimatePresence>
                  {isExpanded ? (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden"
                    >
                      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-300">
                        {(job.reasons || []).map((reason, idx) => (
                          <li key={`${expandedKey}-reason-${idx}`}>{reason}</li>
                        ))}
                      </ul>
                    </motion.div>
                  ) : null}
                </AnimatePresence>

                {job.skill_gaps?.length ? (
                  <div className="mt-4 rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4">
                    <p className="text-sm font-semibold text-amber-100">Skill gaps</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-100/90">
                      {job.skill_gaps.map((gap, idx) => (
                        <li key={`${expandedKey}-gap-${idx}`}>{gap}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div className="mt-5 flex items-center justify-between gap-3">
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${confidenceTone(job.confidence_level)}`}>
                    {job.confidence_level || 'Low'} confidence
                  </span>
                  <motion.button
                    whileHover={job.apply_url ? { scale: 1.02 } : undefined}
                    whileTap={job.apply_url ? { scale: 0.98 } : undefined}
                    onClick={() => handleApply(job)}
                    disabled={!job.apply_url}
                    className="rounded-2xl bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-400 disabled:opacity-60"
                  >
                    {job.apply_url ? 'Apply Now' : 'Apply URL Unavailable'}
                  </motion.button>
                </div>
              </motion.article>
            )
          })}
        </section>
      ) : null}
    </div>
  )
}

export default Matches