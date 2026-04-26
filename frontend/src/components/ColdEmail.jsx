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
    desc: 'Formal, structured, company-researched style',
  },
  {
    id: 'friendly',
    label: 'Friendly',
    desc: 'Warm and approachable while staying polished',
  },
  {
    id: 'confident',
    label: 'Confident',
    desc: 'Assertive and impact-focused pitch',
  },
  {
    id: 'casual',
    label: 'Casual',
    desc: 'Conversational, human, no buzzword fluff',
  },
]

function ColdEmail() {
  const location = useLocation()
  const [form, setForm] = useState(defaultForm)
  const [jobId, setJobId] = useState(null)
  const [emailData, setEmailData] = useState(null)
  const [selectedTone, setSelectedTone] = useState('professional')
  const [isRegenerating, setIsRegenerating] = useState(false)
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
        recipient_email: prefill.recipient_email || prev.recipient_email,
        job_title: prefill.job_title || prev.job_title,
        job_description: prefill.job_description || prev.job_description,
      }))
      if (prefill.job_id) {
        setJobId(prefill.job_id)
      }
      if (prefill.recipient_email) {
        setAutoFoundRecipient(prefill.recipient_email)
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
        company_domain: location.state?.prefill?.company_domain || undefined,
        company_website: location.state?.prefill?.company_website || undefined,
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
        tone: res.data.tone || selectedTone,
      })

      await loadHistory()
    } catch (e) {
      setError(e.response?.data?.detail || e.response?.data?.error || e.message || 'Failed to generate email.')
    } finally {
      setGenerating(false)
    }
  }

  const handleRegenerate = async () => {
    setIsRegenerating(true)
    setEmailData(null)
    try {
      await handleGenerate()
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleLoadDraft = (email) => {
    setForm((prev) => ({
      ...prev,
      company_name: email.company_name || prev.company_name,
      recipient_email: email.recipient_email || prev.recipient_email,
      user_note: prev.user_note,
    }))
    if (email.tone && TONES.some((t) => t.id === email.tone)) {
      setSelectedTone(email.tone)
    }
    setEmailData({
      email_id: email.id || null,
      subject: email.subject || '(No subject)',
      body: email.body || '',
      mailto_url: '',
      tone: email.tone || selectedTone,
    })
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
              <select
                value={selectedTone}
                onChange={(event) => setSelectedTone(event.target.value)}
                className={`${inputClass} bg-slate-900`}
              >
                {TONES.map((tone) => (
                  <option key={tone.id} value={tone.id}>
                    {tone.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-400">
                {TONES.find((tone) => tone.id === selectedTone)?.desc}
              </p>
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
                disabled={generating || isRegenerating}
                className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-white/10"
              >
                {isRegenerating ? 'Regenerating...' : 'Regenerate with same inputs'}
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
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="rounded-full border border-blue-400/30 bg-blue-500/15 px-2 py-0.5 text-[11px] text-blue-100">
                        Tone: {email.tone || 'professional'}
                      </span>
                      <button
                        onClick={() => handleLoadDraft(email)}
                        className="rounded-full border border-white/20 bg-white/5 px-2 py-0.5 text-[11px] text-slate-200 transition hover:bg-white/10"
                      >
                        Load draft
                      </button>
                    </div>
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