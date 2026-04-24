import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BriefcaseBusiness, Mail } from 'lucide-react'
import api from '../lib/api'
import { InlineAlert } from './ui/feedback'

const cardClass = 'rounded-[24px] border border-white/10 bg-slate-900/70 p-8'

function Tracker() {
  const [stats, setStats] = useState({ jobs_applied_count: 0, emails_sent_count: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadStats = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/tracker/stats')
      setStats({
        jobs_applied_count: res.data.jobs_applied_count || 0,
        emails_sent_count: res.data.emails_sent_count || 0,
      })
    } catch (e) {
      setError(e.response?.data?.detail || e.response?.data?.error || e.message || 'Failed to load tracker stats.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStats()
  }, [])

  return (
    <div className="space-y-5">
      <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className={cardClass}>
        <h1 className="text-3xl font-semibold text-white">Tracker</h1>
        <p className="mt-2 text-sm text-slate-400">Monitor outreach activity and application progress.</p>
      </motion.section>

      {error ? <InlineAlert tone="error" title="Unable to load tracker" message={error} /> : null}

      {loading ? (
        <section className="grid gap-5 md:grid-cols-2">
          {Array.from({ length: 2 }).map((_, idx) => (
            <motion.div
              key={`tracker-skeleton-${idx}`}
              animate={{ opacity: [0.35, 0.75, 0.35] }}
              transition={{ duration: 1.4, repeat: Infinity, delay: idx * 0.2 }}
              className="h-48 rounded-[24px] border border-white/10 bg-slate-900/70"
            />
          ))}
        </section>
      ) : null}

      {!loading ? (
        <section className="grid gap-5 md:grid-cols-2">
          <motion.article initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className={cardClass}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">Applications Sent</p>
                <p className="mt-3 text-5xl font-bold text-white">{stats.jobs_applied_count}</p>
              </div>
              <BriefcaseBusiness className="h-8 w-8 text-blue-300" />
            </div>
          </motion.article>

          <motion.article initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className={cardClass}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">Cold Emails Sent</p>
                <p className="mt-3 text-5xl font-bold text-white">{stats.emails_sent_count}</p>
              </div>
              <Mail className="h-8 w-8 text-blue-300" />
            </div>
          </motion.article>
        </section>
      ) : null}

      <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className={cardClass}>
        <div className="flex flex-wrap gap-3">
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Link to="/matches" className="inline-flex items-center rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-100">
              Find more roles →
            </Link>
          </motion.div>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Link to="/cold-email" className="inline-flex items-center rounded-2xl bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-400">
              Generate an email →
            </Link>
          </motion.div>
        </div>

        <div className="mt-5 rounded-2xl border border-blue-500/20 bg-blue-500/10 px-4 py-3 text-sm text-blue-100">
          Full Kanban board coming soon
        </div>
      </motion.section>
    </div>
  )
}

export default Tracker