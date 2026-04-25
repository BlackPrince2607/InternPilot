import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Copy, ExternalLink, MailCheck, Send } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import api from '../lib/api'
import { InlineAlert } from './ui/feedback'

const panelClass = 'rounded-[24px] border border-white/10 bg-slate-900/70 p-6'
const inputClass = 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-blue-400/40 focus:outline-none'

const defaultForm = {
  company_name: '',
  recipient_email: '',
  job_title: '',
  job_description: '',
  user_note: '',
}

const TONES = [
  {
    id: 'professional',
    label: 'Professional',
    desc: 'Formal, structured, company-researched',
  },
  {
    id: 'casual',
    label: 'Casual',
    desc: 'Friendly, real, no corporate fluff',
  },
  {
    id: 'concise',
    label: 'Concise',
    desc: 'Under 100 words, straight to the ask',
  },
]

function ColdEmail() {
  const location = useLocation()
  const [form, setForm] = useState(defaultForm)
  const [jobId, setJobId] = useState(null)
  const [emailData, setEmailData] = useState(null)
  const [selectedTone, setSelectedTone] = useState('professional')
  const [autoFoundRecipient, setAutoFoundRecipient] = useState('')
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [markingSent, setMarkingSent] = useState(false)
  const [error, setError] = useState('')
  const [historyError, setHistoryError] = useState('')
  const [copied, setCopied] = useState(false)
  const [sentMarked, setSentMarked] = useState(false)

  const handleChange = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }))
  }

  const loadHistory = async () => {
    setHistoryLoading(true)
    setHistoryError('')
    try {
      const res = await api.get('/cold-email/history')
      setHistory(res.data.emails || [])
    } catch (e) {
      setHistoryError(e.response?.data?.detail || e.response?.data?.error || e.message || 'Failed to load history')
      setHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  useEffect(() => {
    const prefill = location.state?.prefill
    if (prefill) {
      setForm((prev) => ({
        ...prev,
        company_name: prefill.company_name || prev.company_name,
        job_title: prefill.job_title || prev.job_title,
        job_description: prefill.job_description || prev.job_description,
      }))
      if (prefill.job_id) {
        setJobId(prefill.job_id)
      }
    }
  }, [location.state])

  const handleGenerate = async () => {
    setError('')
    setSentMarked(false)
    setCopied(false)
    setAutoFoundRecipient('')

    if (!form.company_name.trim()) {
      setError('Company name is required.')
      return
    }

    setGenerating(true)
    try {
      const res = await api.post('/cold-email/generate', {
        company_name: form.company_name,
        recipient_email: form.recipient_email || '',
        job_id: jobId || undefined,
        job_title: form.job_title || undefined,
        job_description: form.job_description || undefined,
        user_note: form.user_note || undefined,
        tone: selectedTone,
      })

      const resolvedRecipient = res.data.recipient_email || ''
      if (!form.recipient_email && resolvedRecipient) {
        setForm((prev) => ({ ...prev, recipient_email: resolvedRecipient }))
        setAutoFoundRecipient(resolvedRecipient)
      }

      setEmailData({
        email_id: res.data.email_id || res.data.id || res.data.email?.id || null,
        subject: res.data.subject || res.data.email?.subject || '(No subject)',
        body: res.data.body || res.data.email?.body || '',
        mailto_url: res.data.mailto_url || res.data.email?.mailto_url || '',
      })

      await loadHistory()
    } catch (e) {
      setError(e.response?.data?.detail || e.response?.data?.error || e.message || 'Failed to generate email.')
    } finally {
      setGenerating(false)
    }
  }

  const handleRegenerate = async () => {
    setEmailData(null)
    await handleGenerate()
  }

  const handleCopy = async () => {
    if (!emailData) {
      return
    }

    await navigator.clipboard.writeText(`Subject: ${emailData.subject}\n\n${emailData.body}`)
    setCopied(true)
  }

  const handleMarkSent = async () => {
    if (!emailData?.email_id) {
      setError('Missing email id for sent tracking.')
      return
    }

    setMarkingSent(true)
    setError('')
    try {
      await api.post('/cold-email/record-sent', { email_id: emailData.email_id })
      setSentMarked(true)
      await loadHistory()
    } catch (e) {
      setError(e.response?.data?.detail || e.response?.data?.error || e.message || 'Failed to mark sent.')
    } finally {
      setMarkingSent(false)
    }
  }

  const hasHistory = useMemo(() => history.length > 0, [history])

  return (
    <div className="space-y-5">
      <motion.section
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        className={panelClass}
      >
        <h1 className="text-3xl font-semibold text-white">Cold Email Assistant</h1>
        <p className="mt-2 text-sm text-slate-400">Generate tailored outreach emails and track sent status.</p>
      </motion.section>

      {error ? <InlineAlert tone="error" title="Action failed" message={error} /> : null}

      <section className="grid gap-5 lg:grid-cols-2">
        <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className={panelClass}>
          <h2 className="text-xl font-semibold text-white">Generate Email</h2>
          <div className="mt-4 space-y-4">
            <input className={inputClass} placeholder="Company name" value={form.company_name} onChange={handleChange('company_name')} />
            <input className={inputClass} placeholder="Recipient email (optional)" value={form.recipient_email} onChange={handleChange('recipient_email')} />
            <input className={inputClass} placeholder="Job title (optional)" value={form.job_title} onChange={handleChange('job_title')} />
            <textarea className={`${inputClass} min-h-24`} placeholder="Job description (optional)" value={form.job_description} onChange={handleChange('job_description')} />
            <textarea className={`${inputClass} min-h-24`} placeholder="Anything specific you want to mention?" value={form.user_note} onChange={handleChange('user_note')} />

            <div className="space-y-2">
              <p className="text-sm font-medium text-slate-200">Email Tone</p>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {TONES.map((tone) => (
                  <motion.button
                    key={tone.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setSelectedTone(tone.id)}
                    className={`rounded-2xl border p-3 text-left transition ${
                      selectedTone === tone.id
                        ? 'border-blue-400/40 bg-blue-500/20 text-white'
                        : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/8'
                    }`}
                  >
                    <p className="text-sm font-semibold">{tone.label}</p>
                    <p className="mt-1 text-xs text-slate-400">{tone.desc}</p>
                  </motion.button>
                ))}
              </div>
            </div>

            <motion.button
              whileHover={generating ? undefined : { scale: 1.01 }}
              whileTap={generating ? undefined : { scale: 0.99 }}
              onClick={handleGenerate}
              disabled={generating}
              className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-500 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-400 disabled:opacity-60"
            >
              <Send className="h-4 w-4" />
              {generating ? 'Generating...' : 'Generate Email'}
            </motion.button>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className={panelClass}>
          <h2 className="text-xl font-semibold text-white">Email Preview</h2>
          {!emailData ? (
            <div className="mt-4 rounded-[24px] border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">
              Generate an email from the form to see subject and body preview.
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              {autoFoundRecipient ? (
                <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3 text-sm">
                  <p className="font-medium text-emerald-200">Contact email found automatically</p>
                  <p className="mt-1 text-emerald-100/80">{autoFoundRecipient}</p>
                </div>
              ) : null}

              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Subject</p>
                <p className="mt-2 text-sm font-medium text-white">{emailData.subject}</p>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-slate-950 p-4">
                <pre className="whitespace-pre-wrap text-sm leading-6 text-slate-200">{emailData.body}</pre>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <motion.button
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={handleCopy}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-slate-100"
                >
                  <Copy className="h-4 w-4" />
                  Copy
                </motion.button>

                <motion.a
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  href={emailData.mailto_url || '#'}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-slate-100"
                >
                  <ExternalLink className="h-4 w-4" />
                  Open in Mail
                </motion.a>

                <motion.button
                  whileHover={markingSent ? undefined : { scale: 1.01 }}
                  whileTap={markingSent ? undefined : { scale: 0.99 }}
                  onClick={handleMarkSent}
                  disabled={markingSent}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-blue-500 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-400 disabled:opacity-60"
                >
                  <MailCheck className="h-4 w-4" />
                  {markingSent ? 'Saving...' : 'Mark as Sent'}
                </motion.button>
              </div>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={handleRegenerate}
                disabled={generating}
                className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-white/10"
              >
                Regenerate with same inputs
              </motion.button>

              {copied ? <InlineAlert tone="success" message="Copied to clipboard." /> : null}
              {sentMarked ? <InlineAlert tone="success" message="Marked as sent ✓" /> : null}
            </div>
          )}
        </motion.div>
      </section>

      <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className={panelClass}>
        <h2 className="text-xl font-semibold text-white">Email History</h2>
        {historyError ? <InlineAlert tone="error" className="mt-4" message={historyError} /> : null}

        {historyLoading ? (
          <div className="mt-4 space-y-3">
            {Array.from({ length: 3 }).map((_, idx) => (
              <motion.div
                key={`hist-skeleton-${idx}`}
                animate={{ opacity: [0.35, 0.75, 0.35] }}
                transition={{ duration: 1.4, repeat: Infinity, delay: idx * 0.2 }}
                className="h-16 rounded-2xl border border-white/10 bg-white/5"
              />
            ))}
          </div>
        ) : null}

        {!historyLoading && !hasHistory ? (
          <div className="mt-4 rounded-[24px] border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">
            No emails generated yet. Use the form above to get started.
          </div>
        ) : null}

        {!historyLoading && hasHistory ? (
          <div className="mt-4 space-y-3">
            {history.map((email, idx) => (
              <div key={`${email.id || email.email_id || idx}`} className="rounded-[24px] border border-white/10 bg-white/5 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-white">{email.company_name || 'Unknown company'}</p>
                    <p className="mt-1 text-sm text-slate-300">{email.subject || '(No subject)'}</p>
                    <p className="mt-1 text-xs text-slate-400">{email.recipient_email || 'No recipient'}</p>
                  </div>
                  <span
                    className={`rounded-full border px-3 py-1 text-xs ${
                      email.sent_at ? 'border-emerald-500/30 bg-emerald-500/15 text-emerald-200' : 'border-white/10 bg-white/5 text-slate-300'
                    }`}
                  >
                    {email.sent_at ? 'Sent' : 'Draft'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </motion.section>
    </div>
  )
}

export default ColdEmail