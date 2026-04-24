import { useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowRight, CheckCircle2, FileText, UploadCloud } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const _motion = motion
void _motion

const PHASES = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  PARSING: 'parsing',
  DONE: 'done',
}

function PhaseLoader({ phase }) {
  const parsing = phase === PHASES.PARSING

  return (
    <div className="relative flex h-24 w-24 items-center justify-center">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: parsing ? 1.8 : 2.4, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-0 rounded-full border border-cyan-300/15 border-t-cyan-300/90 border-r-blue-400/70"
      />
      <motion.div
        animate={{
          scale: parsing ? [0.95, 1.08, 0.95] : [1, 1.04, 1],
          opacity: [0.7, 1, 0.7],
        }}
        transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute inset-3 rounded-full bg-[radial-gradient(circle,rgba(34,211,238,0.35),rgba(59,130,246,0.12),transparent_72%)] blur-sm"
      />
      <motion.div
        animate={{
          y: [0, parsing ? -5 : -3, 0],
          scale: [1, parsing ? 1.08 : 1.04, 1],
        }}
        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
        className="relative flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-white/8 shadow-[0_0_40px_rgba(34,211,238,0.12)] backdrop-blur"
      >
        <div className="h-5 w-5 rounded-full bg-gradient-to-br from-rose-500 via-amber-400 to-emerald-400 shadow-[0_0_18px_rgba(34,211,238,0.25)]" />
      </motion.div>
    </div>
  )
}

function ProgressLine({ progress }) {
  const safe = Math.max(0, Math.min(progress, 100))

  return (
    <div className="relative h-1.5 overflow-hidden rounded-full bg-white/5">
      <motion.div
        initial={false}
        animate={{ width: `${safe}%` }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
        className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-cyan-300 via-sky-400 to-blue-500 shadow-[0_0_20px_rgba(34,211,238,0.5)]"
      />
      <motion.div
        animate={{ x: ['-120%', '220%'] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute left-0 top-0 h-full w-1/3 bg-gradient-to-r from-transparent via-white/45 to-transparent blur-sm"
      />
    </div>
  )
}

function SuccessBadge() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm font-medium text-emerald-100 shadow-[0_0_40px_rgba(16,185,129,0.16)]"
    >
      <CheckCircle2 size={16} />
      Your profile is ready
    </motion.div>
  )
}

export default function Onboarding() {
  const navigate = useNavigate()
  const inputRef = useRef(null)
  const timersRef = useRef([])
  const intervalRef = useRef(null)
  const [phase, setPhase] = useState(PHASES.IDLE)
  const [progress, setProgress] = useState(0)
  const [fileName, setFileName] = useState('')
  const [isDragging, setIsDragging] = useState(false)

  const clearTimers = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
  }

  useEffect(() => clearTimers, [])

  const startFlow = () => {
    clearTimers()
    setPhase(PHASES.UPLOADING)
    setProgress(0)

    intervalRef.current = window.setInterval(() => {
      setProgress((value) => {
        const next = Math.min(100, value + Math.max(2, (100 - value) * 0.08))
        if (next >= 100) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
        return next
      })
    }, 80)

    timersRef.current.push(
      window.setTimeout(() => {
        clearInterval(intervalRef.current)
        intervalRef.current = null
        setProgress(100)
        setPhase(PHASES.PARSING)
      }, 2000),
    )

    timersRef.current.push(
      window.setTimeout(() => {
        setPhase(PHASES.DONE)
      }, 4000),
    )
  }

  const handleFile = (file) => {
    if (!file) return
    setFileName(file.name)
    startFlow()
  }

  const onInputChange = (event) => {
    handleFile(event.target.files?.[0] || null)
  }

  const onDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    handleFile(event.dataTransfer.files?.[0] || null)
  }

  const headline = useMemo(() => {
    if (phase === PHASES.DONE) return 'Your profile is ready'
    if (phase === PHASES.PARSING) return 'Analyzing your profile...'
    if (phase === PHASES.UPLOADING) return 'Uploading your resume...'
    return 'Turn your resume into opportunities'
  }, [phase])

  const subtext = useMemo(() => {
    if (phase === PHASES.DONE) {
      return 'Your data is structured, polished, and ready for the next step.'
    }
    if (phase === PHASES.PARSING) {
      return 'We’re extracting skills, projects, experience, and matching signals.'
    }
    if (phase === PHASES.UPLOADING) {
      return 'Your file is moving into the pipeline. Parsing starts immediately after upload.'
    }
    return 'Upload once. We handle parsing, matching, and outreach.'
  }, [phase])

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#020617] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.12),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(59,130,246,0.14),transparent_30%),linear-gradient(180deg,#020617_0%,#020617_100%)]" />
      <motion.div
        animate={{ opacity: [0.35, 0.65, 0.35], scale: [1, 1.04, 1] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        className="pointer-events-none absolute left-1/2 top-16 h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-cyan-400/10 blur-3xl"
      />
      <motion.div
        animate={{ opacity: [0.2, 0.4, 0.2], x: [-10, 10, -10] }}
        transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
        className="pointer-events-none absolute right-[-8rem] top-1/3 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl"
      />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
        <motion.section
          initial={{ opacity: 0, y: 28, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="relative w-full max-w-4xl overflow-hidden rounded-[32px] border border-white/10 bg-white/5 shadow-[0_30px_120px_rgba(0,0,0,0.6)] backdrop-blur-xl"
        >
          <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.06),transparent_30%,rgba(34,211,238,0.05),transparent_70%)]" />
          <motion.div
            animate={{ opacity: [0.25, 0.65, 0.25], scaleX: [0.97, 1, 0.97] }}
            transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
            className="pointer-events-none absolute inset-0 rounded-[32px] border border-cyan-400/10"
          />

          <div className="relative px-6 py-8 sm:px-10 sm:py-10">
            <div className="mx-auto max-w-3xl">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.34em] text-cyan-300/75">
                    InternPilot
                  </p>
                  <h1 className="mt-4 text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                    {headline}
                  </h1>
                  <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
                    {subtext}
                  </p>
                </div>

                <div className="hidden shrink-0 rounded-full border border-white/10 bg-white/5 p-3 shadow-[0_0_40px_rgba(34,211,238,0.10)] sm:block">
                  <UploadCloud className="h-6 w-6 text-cyan-300" />
                </div>
              </div>

              <div className="mt-10">
                <AnimatePresence mode="wait" initial={false}>
                  {phase === PHASES.IDLE ? (
                    <motion.div
                      key="idle"
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -18 }}
                      transition={{ duration: 0.35, ease: 'easeOut' }}
                      className="space-y-6"
                    >
                      <motion.label
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                        onDragEnter={(event) => {
                          event.preventDefault()
                          setIsDragging(true)
                        }}
                        onDragOver={(event) => event.preventDefault()}
                        onDragLeave={(event) => {
                          event.preventDefault()
                          setIsDragging(false)
                        }}
                        onDrop={onDrop}
                        className={`group relative block cursor-pointer overflow-hidden rounded-2xl border border-dashed px-6 py-16 text-center transition duration-300 sm:px-10 ${
                          isDragging
                            ? 'border-cyan-300/70 bg-cyan-400/10 shadow-[0_0_0_1px_rgba(34,211,238,0.24),0_0_50px_rgba(34,211,238,0.18)]'
                            : 'border-white/15 bg-white/[0.03] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]'
                        }`}
                      >
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.10),transparent_48%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent)] opacity-80 transition group-hover:opacity-100" />
                        <motion.div
                          animate={{ opacity: [0.18, 0.5, 0.18], scale: [0.98, 1.02, 0.98] }}
                          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                          className="absolute inset-0 rounded-2xl bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.08),transparent_58%)] blur-2xl"
                        />
                        <div className="relative mx-auto flex max-w-xl flex-col items-center">
                          <div className="flex h-20 w-20 items-center justify-center rounded-3xl border border-cyan-400/20 bg-cyan-400/10 shadow-[0_0_30px_rgba(34,211,238,0.12)]">
                            <FileText className="h-8 w-8 text-cyan-200" />
                          </div>
                          <p className="mt-6 text-xl font-medium text-white sm:text-2xl">
                            Drag & drop your resume
                          </p>
                          <p className="mt-3 text-sm leading-6 text-slate-400 sm:text-base">
                            Drop a PDF here, or click to browse. We’ll structure it into a premium
                            candidate profile.
                          </p>

                          <input
                            ref={inputRef}
                            type="file"
                            accept=".pdf,application/pdf"
                            onChange={onInputChange}
                            className="sr-only"
                          />

                          <motion.div
                            whileHover={{ scale: 1.03 }}
                            whileTap={{ scale: 0.98 }}
                            className="mt-8 inline-flex items-center gap-2 rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 shadow-[0_0_30px_rgba(34,211,238,0.22)] transition hover:shadow-[0_0_40px_rgba(34,211,238,0.28)]"
                            onClick={() => inputRef.current?.click()}
                          >
                            Choose file
                            <ArrowRight size={16} />
                          </motion.div>

                          {fileName ? (
                            <motion.p
                              initial={{ opacity: 0, y: 8 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="mt-5 text-sm text-cyan-200/90"
                            >
                              Selected: {fileName}
                            </motion.p>
                          ) : null}
                        </div>
                      </motion.label>
                    </motion.div>
                  ) : null}

                  {phase === PHASES.UPLOADING ? (
                    <motion.div
                      key="uploading"
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -18 }}
                      transition={{ duration: 0.35, ease: 'easeOut' }}
                      className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] px-6 py-16 text-center"
                    >
                      <div className="absolute inset-x-0 top-0 px-6 pt-6">
                        <ProgressLine progress={progress} />
                      </div>
                      <motion.div
                        animate={{ opacity: [0.65, 1, 0.65], y: [0, -4, 0] }}
                        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
                        className="mx-auto flex max-w-lg flex-col items-center"
                      >
                        <PhaseLoader phase={PHASES.UPLOADING} />
                        <p className="mt-6 text-2xl font-medium text-white">Uploading your resume...</p>
                        <p className="mt-3 text-sm leading-6 text-slate-400">
                          {progress.toFixed(0)}% complete
                        </p>
                      </motion.div>
                    </motion.div>
                  ) : null}

                  {phase === PHASES.PARSING ? (
                    <motion.div
                      key="parsing"
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -18 }}
                      transition={{ duration: 0.35, ease: 'easeOut' }}
                      className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] px-6 py-16 text-center"
                    >
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2.2, repeat: Infinity, ease: 'linear' }}
                        className="mx-auto"
                      >
                        <PhaseLoader phase={PHASES.PARSING} />
                      </motion.div>
                      <p className="mt-6 text-2xl font-medium text-white">Analyzing your profile...</p>
                      <p className="mt-3 text-sm leading-6 text-slate-400">
                        Extracting skills, projects, experience, and matching signals.
                      </p>
                      <div className="mt-6 flex items-center justify-center gap-2">
                        {[0, 1, 2].map((index) => (
                          <motion.span
                            key={index}
                            animate={{ opacity: [0.2, 1, 0.2], y: [0, -2, 0] }}
                            transition={{
                              duration: 1,
                              repeat: Infinity,
                              delay: index * 0.14,
                              ease: 'easeInOut',
                            }}
                            className="h-2.5 w-2.5 rounded-full bg-cyan-300"
                          />
                        ))}
                      </div>
                    </motion.div>
                  ) : null}

                  {phase === PHASES.DONE ? (
                    <motion.div
                      key="done"
                      initial={{ opacity: 0, y: 18, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ duration: 0.45, ease: 'easeOut' }}
                      className="relative overflow-hidden rounded-2xl border border-emerald-400/20 bg-emerald-400/8 px-6 py-16 text-center"
                    >
                      <motion.div
                        animate={{ opacity: [0.25, 0.8, 0.25], scale: [0.96, 1.03, 0.96] }}
                        transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
                        className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(34,197,94,0.18),transparent_52%)] blur-2xl"
                      />
                      <div className="relative mx-auto max-w-xl">
                        <div className="mb-4 flex justify-center">
                          <SuccessBadge />
                        </div>
                        <motion.div
                          animate={{ scale: [1, 1.04, 1] }}
                          transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
                          className="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-emerald-400/20 bg-emerald-400/12 shadow-[0_0_40px_rgba(34,197,94,0.16)]"
                        >
                          <CheckCircle2 className="h-8 w-8 text-emerald-200" />
                        </motion.div>
                        <p className="mt-6 text-2xl font-medium text-white">
                          Your profile is ready
                        </p>
                        <p className="mt-3 text-sm leading-6 text-slate-300">
                          Your resume has been transformed into a structured profile.
                        </p>

                        <motion.button
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => navigate('/preferences')}
                          className="mt-8 inline-flex items-center gap-2 rounded-full bg-emerald-300 px-6 py-3 text-sm font-semibold text-slate-950 shadow-[0_0_30px_rgba(34,197,94,0.22)] transition hover:shadow-[0_0_42px_rgba(34,197,94,0.3)]"
                        >
                          Continue to Preferences
                          <ArrowRight size={16} />
                        </motion.button>
                      </div>
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </motion.section>
      </div>
    </main>
  )
}
