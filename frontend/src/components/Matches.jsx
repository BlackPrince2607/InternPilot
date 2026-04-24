import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import api from '../lib/api'
import { CenterLoader, InlineAlert } from './ui/feedback'

function scoreTone(score) {
  if (score >= 80) return 'text-emerald-200 bg-emerald-500/15 border-emerald-400/25'
  if (score >= 60) return 'text-blue-200 bg-blue-500/15 border-blue-400/25'
  return 'text-amber-200 bg-amber-500/15 border-amber-400/25'
}

function Matches() {
  const navigate = useNavigate()
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [applyFeedback, setApplyFeedback] = useState('')
  const [infoMessage, setInfoMessage] = useState('')

  useEffect(() => {
    const fetchMatches = async () => {
      try {
        setError('')
        const res = await api.get('/matches/')
        setMatches(res.data.matches || [])
        setInfoMessage(res.data.meta?.message || '')
      } catch (err) {
        const isTimeout = err.code === 'ECONNABORTED' || (err.message || '').toLowerCase().includes('timeout')
        const errorMsg =
          (isTimeout && 'Matching took too long. Please retry in a few seconds.') ||
          err.response?.data?.error ||
          err.response?.data?.detail ||
          err.message ||
          'Failed to load matches.'
        setError(errorMsg)
        setMatches([])
      } finally {
        setLoading(false)
      }
    }

    fetchMatches()
  }, [])

  const handleApply = async (job) => {
    setApplyFeedback('')

    try {
      if (job.job_id) {
        await api.post('/tracker/record-apply', { job_id: job.job_id })
      }
      setApplyFeedback('Application intent recorded. Opening job link...')
    } catch {
      setApplyFeedback('Could not record this apply event, but opening the job link now.')
    }

    if (job.apply_url) {
      window.open(job.apply_url, '_blank', 'noopener,noreferrer')
    }
  }

  if (loading) {
    return <CenterLoader title="Finding your best matches" subtitle="This can take a few seconds while we rank jobs against your profile." />
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <section className="rounded-[28px] border border-white/10 bg-slate-950/70 p-6 shadow-2xl shadow-black/30 backdrop-blur sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.24em] text-cyan-200/80">Match Engine</p>
              <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">Your internship matches</h1>
              <p className="mt-2 text-sm text-slate-300">
                Ranked using your latest parsed resume and saved preferences.
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => navigate('/app')}
                className="rounded-2xl border border-white/15 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/10"
              >
                Back to App
              </button>
              <button
                onClick={() => navigate('/preferences')}
                className="rounded-2xl border border-cyan-400/30 bg-cyan-500/10 px-4 py-2 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-500/15"
              >
                Edit Preferences
              </button>
            </div>
          </div>
        </section>

        {error ? (
          <InlineAlert
            tone="error"
            title="Unable to load matches"
            message={`${error} Upload a resume and save your preferences, then retry.`}
          />
        ) : null}

        {infoMessage && !error ? <InlineAlert tone="info" message={infoMessage} /> : null}

        {applyFeedback ? <InlineAlert tone="info" message={applyFeedback} /> : null}

        {!error && matches.length === 0 ? (
          <section className="rounded-[24px] border border-dashed border-white/15 bg-slate-900/60 p-8 text-center">
            <h2 className="text-xl font-semibold text-white">No matches yet</h2>
            <p className="mt-2 text-sm text-slate-400">
              Upload your resume and save your target roles/locations to generate recommendations.
            </p>
          </section>
        ) : null}

        <section className="grid gap-5">
          {matches.map((job) => (
            <article
              key={job.job_id || `${job.title}-${job.company}`}
              className="rounded-[24px] border border-white/10 bg-slate-900/70 p-5 shadow-lg shadow-black/20"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-xl font-semibold text-white">{job.title}</h3>
                  <p className="mt-1 text-sm text-slate-300">
                    {job.company || 'Unknown Company'} • {job.location || 'Unknown Location'}
                  </p>
                </div>
                <div className={`rounded-full border px-3 py-1 text-sm font-semibold ${scoreTone(job.final_score || 0)}`}>
                  Match {(job.final_score || 0).toFixed ? (job.final_score || 0).toFixed(1) : job.final_score}%
                </div>
              </div>

              <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-950/70">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-cyan-400 to-blue-500"
                  style={{ width: `${Math.min(Math.max(job.final_score || 0, 0), 100)}%` }}
                />
              </div>

              <div className="mt-4 grid gap-2 text-sm text-slate-300 sm:grid-cols-3">
                <p>Confidence: {job.confidence_level || 'Medium'}</p>
                <p>Domain: {job.domain || 'General'}</p>
                <p>Experience: {job.experience_level || 'Not specified'}</p>
              </div>

              {job.matched_skills?.length ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {job.matched_skills.slice(0, 8).map((skill) => (
                    <span
                      key={`${job.job_id}-${skill}`}
                      className="rounded-full border border-blue-400/25 bg-blue-500/10 px-3 py-1 text-xs text-blue-100"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : null}

              {job.reasons?.length ? (
                <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <p className="text-sm font-semibold text-slate-100">Why this matches</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
                    {job.reasons.map((reason, index) => (
                      <li key={`${job.job_id}-reason-${index}`}>{reason}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {job.skill_gaps?.length ? (
                <div className="mt-4 rounded-2xl border border-amber-400/20 bg-amber-500/10 px-4 py-3">
                  <p className="text-sm font-semibold text-amber-100">Skill gaps</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-100/90">
                    {job.skill_gaps.map((gap, index) => (
                      <li key={`${job.job_id}-gap-${index}`}>{gap}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <button
                onClick={() => handleApply(job)}
                disabled={!job.apply_url}
                className="mt-5 w-full rounded-2xl border border-emerald-400/30 bg-emerald-500/15 px-4 py-3 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/25 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {job.apply_url ? 'Apply Now' : 'Apply URL Unavailable'}
              </button>
            </article>
          ))}
        </section>
      </div>
    </main>
  )
}

export default Matches
