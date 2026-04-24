import { useId, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import api from '../lib/api'
import GooeyLoader from './ui/loader'

const _motion = motion
void _motion

const PHASES = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  PARSING: 'parsing',
  SUCCESS: 'success',
  ERROR: 'error',
}

const sectionMotion = {
  initial: { opacity: 0, y: 22 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.45, ease: 'easeOut' },
}

function formatBytes(bytes) {
  if (!bytes) {
    return '0 KB'
  }

  const units = ['B', 'KB', 'MB', 'GB']
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** exponent

  return `${value.toFixed(value >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`
}

function flattenSkillGroups(skills = {}) {
  return [
    { label: 'Languages', items: skills.languages || [] },
    { label: 'Frameworks', items: skills.frameworks || [] },
    { label: 'Tools', items: skills.tools || [] },
    { label: 'Databases', items: skills.databases || [] },
  ]
}

function UploadActionButton({ children, disabled, onClick, tone = 'primary' }) {
  const tones = {
    primary:
      'bg-blue-500 text-white hover:bg-blue-400 shadow-lg shadow-blue-950/35 disabled:bg-blue-500/40',
    secondary:
      'border border-white/10 bg-white/5 text-slate-100 hover:bg-white/10 disabled:text-slate-500',
  }

  return (
    <motion.button
      whileHover={disabled ? undefined : { scale: 1.03 }}
      whileTap={disabled ? undefined : { scale: 0.98 }}
      disabled={disabled}
      onClick={onClick}
      className={`inline-flex items-center justify-center rounded-2xl px-5 py-3 text-sm font-semibold transition duration-200 disabled:cursor-not-allowed hover:shadow-[0_0_24px_rgba(34,211,238,0.18)] ${tones[tone]}`}
    >
      {children}
    </motion.button>
  )
}

function DualProgressBar({ progress }) {
  const fill = Math.max(0, Math.min(progress, 100))
  const sideFill = Math.min(fill, 50) * 2
  const leftWidth = `${sideFill}%`
  const rightWidth = `${sideFill}%`
  const centerOpacity = fill >= 48 && fill <= 58 ? 1 : 0.55

  return (
    <div className="relative h-2 overflow-hidden rounded-full bg-slate-950/60 ring-1 ring-white/10">
      <motion.div
        animate={{ opacity: [0.2, 0.55, 0.2], scaleX: [0.98, 1, 0.98] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.16),transparent_55%)] blur-md"
      />
      <motion.div
        initial={false}
        animate={{ width: leftWidth }}
        transition={{ duration: 0.45, ease: 'easeOut' }}
        className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-cyan-500 via-sky-400 to-emerald-400 shadow-[0_0_22px_rgba(34,211,238,0.42)]"
      />
      <motion.div
        initial={false}
        animate={{ width: rightWidth }}
        transition={{ duration: 0.45, ease: 'easeOut' }}
        className="absolute right-0 top-0 h-full rounded-full bg-gradient-to-l from-cyan-500 via-sky-400 to-emerald-400 shadow-[0_0_22px_rgba(34,211,238,0.42)]"
      />
      <motion.div
        animate={{ opacity: [0.2, 0.85, 0.2], scaleX: [0.9, 1.15, 0.9] }}
        transition={{ duration: 1.3, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute left-1/2 top-0 h-full w-20 -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgba(255,255,255,0.9),rgba(255,255,255,0.15),transparent_70%)] blur-md"
        style={{ opacity: centerOpacity }}
      />
      <motion.div
        animate={{ x: ['-120%', '220%'] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute left-0 top-0 h-full w-1/3 bg-gradient-to-r from-transparent via-white/35 to-transparent blur-sm"
      />
    </div>
  )
}

function StatusBanner({ title, message, tone }) {
  const tones = {
    error: 'border-rose-500/25 bg-rose-500/10 text-rose-100',
    success: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-100',
    info: 'border-blue-500/25 bg-blue-500/10 text-blue-100',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className={`rounded-2xl border px-4 py-3 backdrop-blur shadow-lg ${tones[tone]}`}
    >
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-1 text-sm opacity-90">{message}</p>
    </motion.div>
  )
}

function ParsingState() {
  return (
    <motion.div
      key="parsing"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="rounded-[24px] border border-cyan-400/20 bg-slate-900/70 p-5 shadow-xl shadow-black/20"
    >
      <div className="space-y-5">
        <GooeyLoader phase="parsing" />
        <div className="rounded-2xl border border-white/8 bg-white/5 px-4 py-4">
          <h3 className="text-lg font-semibold text-white">Analyzing resume...</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            We’ve uploaded your file. Now the backend is extracting text, skills, and project
            signals into a structured candidate profile.
          </p>
          <div className="mt-4 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-cyan-200/80">
            <motion.span
              animate={{ opacity: [0.25, 1, 0.25], scale: [0.9, 1.1, 0.9] }}
              transition={{ duration: 1.1, repeat: Infinity, ease: 'easeInOut' }}
              className="h-2 w-2 rounded-full bg-cyan-300"
            />
            <motion.span
              animate={{ opacity: [0.25, 1, 0.25], scale: [0.9, 1.1, 0.9] }}
              transition={{ duration: 1.1, repeat: Infinity, delay: 0.12, ease: 'easeInOut' }}
              className="h-2 w-2 rounded-full bg-sky-300"
            />
            <motion.span
              animate={{ opacity: [0.25, 1, 0.25], scale: [0.9, 1.1, 0.9] }}
              transition={{ duration: 1.1, repeat: Infinity, delay: 0.24, ease: 'easeInOut' }}
              className="h-2 w-2 rounded-full bg-emerald-300"
            />
            <span>AI analyzing</span>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <motion.div
                key={index}
                animate={{ opacity: [0.35, 0.9, 0.35], scale: [0.98, 1, 0.98] }}
                transition={{ duration: 1.4, repeat: Infinity, delay: index * 0.18 }}
                className="h-18 rounded-2xl border border-white/8 bg-gradient-to-br from-white/5 to-cyan-400/5"
              />
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function ResultCard({ parsedData, onReset }) {
  const skillGroups = flattenSkillGroups(parsedData.skills)

  return (
    <motion.section
      key="result"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-6"
    >
      <div className="rounded-[24px] border border-emerald-500/20 bg-emerald-500/8 p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-emerald-200">Resume parsed successfully</p>
            <p className="mt-1 text-sm text-emerald-100/80">
              Your profile is now ready for preference-based matching.
            </p>
          </div>
          <UploadActionButton tone="secondary" onClick={onReset}>
            Upload another resume
          </UploadActionButton>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <motion.div
          whileHover={{ y: -4 }}
          className="rounded-[24px] border border-white/10 bg-slate-900/70 p-6 shadow-xl shadow-black/20"
        >
          <div className="mb-4">
            <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
              Personal info
            </p>
            <h3 className="mt-2 text-xl font-semibold text-white">
              {parsedData.name || 'Unnamed candidate'}
            </h3>
          </div>

          <dl className="space-y-4 text-sm">
            <div className="rounded-2xl border border-white/8 bg-white/4 px-4 py-3">
              <dt className="text-slate-400">Email</dt>
              <dd className="mt-1 text-slate-100">{parsedData.email || 'Not detected'}</dd>
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/4 px-4 py-3">
              <dt className="text-slate-400">College</dt>
              <dd className="mt-1 text-slate-100">{parsedData.college || 'Not detected'}</dd>
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/4 px-4 py-3">
              <dt className="text-slate-400">Graduation year</dt>
              <dd className="mt-1 text-slate-100">
                {parsedData.graduation_year || 'Not detected'}
              </dd>
            </div>
          </dl>
        </motion.div>

        <motion.div
          whileHover={{ y: -4 }}
          className="rounded-[24px] border border-white/10 bg-slate-900/70 p-6 shadow-xl shadow-black/20"
        >
          <div className="mb-5">
            <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
              Skills inventory
            </p>
            <h3 className="mt-2 text-xl font-semibold text-white">Detected skills</h3>
          </div>

          <div className="space-y-5">
            {skillGroups.map((group) => (
              <div key={group.label}>
                <p className="mb-3 text-sm font-medium text-slate-300">{group.label}</p>
                <div className="flex flex-wrap gap-2">
                  {group.items.length > 0 ? (
                    group.items.map((item) => (
                      <motion.span
                        key={`${group.label}-${item}`}
                        whileHover={{ y: -2 }}
                        className="rounded-full border border-blue-400/20 bg-blue-400/10 px-3 py-1.5 text-xs font-medium text-blue-100"
                      >
                        {item}
                      </motion.span>
                    ))
                  ) : (
                    <span className="text-sm text-slate-500">No {group.label.toLowerCase()} detected</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <div>
        <div className="mb-4">
          <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
            Projects
          </p>
          <h3 className="mt-2 text-xl font-semibold text-white">Experience signals from your work</h3>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {parsedData.projects?.length ? (
            parsedData.projects.map((project, index) => (
              <motion.article
                key={`${project.name || 'project'}-${index}`}
                whileHover={{ y: -6, scale: 1.01 }}
                className="rounded-[24px] border border-white/10 bg-slate-900/70 p-5 shadow-xl shadow-black/20"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-lg font-semibold text-white">
                      {project.name || `Project ${index + 1}`}
                    </h4>
                    <p className="mt-2 text-sm leading-6 text-slate-300">
                      {project.description || 'No description extracted.'}
                    </p>
                  </div>
                  <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[11px] font-medium text-emerald-200">
                    Project
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {project.technologies?.length ? (
                    project.technologies.map((tech) => (
                      <span
                        key={`${project.name}-${tech}`}
                        className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200"
                      >
                        {tech}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-slate-500">No technologies extracted</span>
                  )}
                </div>
              </motion.article>
            ))
          ) : (
            <div className="rounded-[24px] border border-dashed border-white/10 bg-slate-900/40 p-6 text-sm text-slate-400">
              No project cards were extracted from this resume yet.
            </div>
          )}
        </div>
      </div>
    </motion.section>
  )
}

function ResumeUploader() {
  const fileInputId = useId()
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [phase, setPhase] = useState(PHASES.IDLE)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [parsedData, setParsedData] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const { isAuthenticated, signOut, user } = useAuth()

  const isBusy = phase === PHASES.UPLOADING || phase === PHASES.PARSING

  const resetState = () => {
    setFile(null)
    setPhase(PHASES.IDLE)
    setUploadProgress(0)
    setError('')
    setSuccessMessage('')
    setParsedData(null)
    setIsDragging(false)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  const validateAndSetFile = (selectedFile) => {
    if (!selectedFile) {
      return
    }

    const isPdf =
      selectedFile.type === 'application/pdf' || selectedFile.name.toLowerCase().endsWith('.pdf')

    if (!isPdf) {
      setFile(null)
      setPhase(PHASES.ERROR)
      setError('Only PDF resumes are supported right now. Please choose a .pdf file.')
      setSuccessMessage('')
      setParsedData(null)
      return
    }

    setFile(selectedFile)
    setPhase(PHASES.IDLE)
    setError('')
    setSuccessMessage('File selected. You’re ready to upload and parse.')
    setParsedData(null)
    setUploadProgress(0)
  }

  const handleFileChange = (event) => {
    validateAndSetFile(event.target.files?.[0] || null)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    validateAndSetFile(event.dataTransfer.files?.[0] || null)
  }

  const handleUpload = async () => {
    if (!isAuthenticated) {
      setPhase(PHASES.ERROR)
      setError('Please log in before uploading your resume.')
      return
    }

    if (!file) {
      setPhase(PHASES.ERROR)
      setError('Choose a PDF resume first, then start the upload.')
      return
    }

    setPhase(PHASES.UPLOADING)
    setUploadProgress(0)
    setError('')
    setSuccessMessage('')
    setParsedData(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const uploadRes = await api.post('/resumes/upload', formData, {
        onUploadProgress: (progressEvent) => {
          if (!progressEvent.total) {
            return
          }

          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          setUploadProgress(progress)
        },
      })

      setUploadProgress(100)
      setPhase(PHASES.PARSING)

      const parseRes = await api.post(`/resumes/parse/${uploadRes.data.resume_id}`)
      if (!parseRes.data?.parsed_data) {
        throw new Error('Parsed resume data is missing from response')
      }

      setParsedData(parseRes.data.parsed_data)
      setPhase(PHASES.SUCCESS)
      setSuccessMessage('Resume uploaded and parsed successfully.')
    } catch (err) {
      const detail = err.response?.data?.error || err.response?.data?.detail || err.message
      const status = err.response?.status

      setPhase(PHASES.ERROR)
      setParsedData(null)

      if (status === 401) {
        setError('Your session expired. Please log in again before uploading.')
      } else if (phase === PHASES.PARSING || /parsing/i.test(detail || '')) {
        setError(detail || 'The upload worked, but parsing failed. Please try again.')
      } else {
        setError(detail || 'Upload failed. Please try again.')
      }
    }
  }

  return (
    <motion.section
      {...sectionMotion}
      className="rounded-[24px] border border-white/10 bg-white/5 p-5 shadow-lg shadow-black/20 backdrop-blur sm:p-6"
    >
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="mb-2 inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.24em] text-slate-300">
            Resume parsing
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
            Turn your resume into a structured profile
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Drop in a PDF resume and we’ll upload it, parse it, and transform it into clean data
            for matching.
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-left text-sm">
          <p className="font-medium text-slate-200">{user?.email || 'Unknown user'}</p>
          <p className="mt-1 text-slate-400">Authenticated with Supabase</p>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5">
          <motion.div
            whileHover={{ y: -4 }}
            onDragEnter={(event) => {
              event.preventDefault()
              if (!isBusy) {
                setIsDragging(true)
              }
            }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={(event) => {
              event.preventDefault()
              setIsDragging(false)
            }}
            onDrop={isBusy ? undefined : handleDrop}
            whileHover={{ scale: 1.006 }}
            transition={{ type: 'spring', stiffness: 220, damping: 20 }}
            className={`group relative overflow-hidden rounded-[28px] border border-dashed p-6 transition sm:p-8 ${
              isDragging
                ? 'border-cyan-300/60 bg-cyan-500/10 shadow-2xl shadow-cyan-950/30'
                : 'border-white/15 bg-slate-950/70'
            }`}
          >
            {phase === PHASES.UPLOADING ? (
              <div className="absolute inset-x-0 top-0 px-5 pt-5 sm:px-8">
                <DualProgressBar progress={uploadProgress} />
              </div>
            ) : null}

            <motion.div
              animate={{ opacity: [0.55, 0.95, 0.55] }}
              transition={{ duration: 4.5, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(45,212,191,0.12),transparent_55%),radial-gradient(circle_at_bottom_right,rgba(59,130,246,0.10),transparent_45%)]"
            />
            <div className="absolute inset-0 bg-gradient-to-b from-white/5 via-transparent to-cyan-400/5 opacity-60" />
            <motion.div
              animate={{ opacity: [0.12, 0.28, 0.12], x: ['-6%', '6%', '-6%'] }}
              transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.14),transparent_58%)] blur-2xl"
            />
            <motion.div
              animate={{ opacity: [0.15, 0.45, 0.15], rotate: [0, 4, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute -right-20 top-4 h-40 w-40 rounded-full bg-cyan-400/10 blur-3xl"
            />
            <div className="relative">
              <motion.div
                animate={{
                  boxShadow: [
                    '0 0 0 0 rgba(34,211,238,0.12)',
                    '0 0 0 14px rgba(34,211,238,0.04)',
                    '0 0 0 0 rgba(34,211,238,0.12)',
                  ],
                }}
                transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
                className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-400/20 bg-cyan-500/10 text-2xl text-cyan-200 shadow-[0_0_24px_rgba(34,211,238,0.15)]"
              >
                ✦
              </motion.div>
              <h3 className="text-xl font-semibold tracking-tight text-white">
                Drag & drop your PDF resume
              </h3>
              <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400">
                Or browse from your device. We only accept PDF files, and the upload is tied to
                your authenticated account.
              </p>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <label
                  htmlFor={fileInputId}
                  className="inline-flex cursor-pointer items-center justify-center rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition duration-200 hover:scale-[1.02] hover:bg-white/10 hover:shadow-[0_0_24px_rgba(34,211,238,0.12)]"
                >
                  Choose file
                </label>
                <UploadActionButton disabled={!file || isBusy} onClick={handleUpload}>
                  {phase === PHASES.UPLOADING
                    ? 'Uploading...'
                    : phase === PHASES.PARSING
                      ? 'Parsing...'
                      : 'Upload & parse resume'}
                </UploadActionButton>
                <UploadActionButton tone="secondary" disabled={isBusy} onClick={() => signOut()}>
                  Log out
                </UploadActionButton>
              </div>

              <AnimatePresence initial={false}>
                {isBusy ? (
                  <motion.div
                    key="busy-state"
                    initial={{ opacity: 0, y: 10, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -10, scale: 0.98 }}
                    className="mt-6"
                  >
                    <GooeyLoader phase={phase} />
                  </motion.div>
                ) : null}
              </AnimatePresence>

              <input
                ref={inputRef}
                id={fileInputId}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                className="sr-only"
              />

              <AnimatePresence initial={false}>
                {file && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.99 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -10, scale: 0.99 }}
                    className="mt-6 flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="text-sm font-medium text-white">{file.name}</p>
                      <p className="mt-1 text-sm text-slate-400">{formatBytes(file.size)}</p>
                    </div>
                    <button
                      onClick={resetState}
                      className="text-sm font-medium text-slate-300 transition hover:text-white"
                    >
                      Remove file
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>

              <AnimatePresence initial={false}>
                {phase === PHASES.SUCCESS && successMessage ? (
                  <StatusBanner
                    key="success-state"
                    tone="success"
                    title="Upload complete"
                    message={successMessage}
                  />
                ) : null}
              </AnimatePresence>
            </div>
          </motion.div>

          <AnimatePresence mode="wait">
            {phase === PHASES.UPLOADING ? (
              <motion.div
                key="uploading"
                initial={{ opacity: 0, y: 12, scale: 0.99 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.99 }}
                className="rounded-[24px] border border-cyan-500/20 bg-slate-900/70 p-5 shadow-xl shadow-black/20"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-white">Uploading…</p>
                    <p className="mt-1 text-sm text-slate-400">
                      Sending your file to secure storage before parsing starts.
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-cyan-200">{uploadProgress}%</span>
                </div>
                <div className="mt-3 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.22em] text-cyan-200/80">
                  <motion.span
                    animate={{ opacity: [0.25, 1, 0.25], y: [0, -2, 0] }}
                    transition={{ duration: 1.1, repeat: Infinity, ease: 'easeInOut' }}
                    className="inline-block"
                  >
                    Uploading
                  </motion.span>
                  <motion.span
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ duration: 0.9, repeat: Infinity, ease: 'easeInOut' }}
                    className="inline-block"
                  >
                    •
                  </motion.span>
                  <motion.span
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ duration: 0.9, repeat: Infinity, delay: 0.15, ease: 'easeInOut' }}
                    className="inline-block"
                  >
                    •
                  </motion.span>
                  <motion.span
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ duration: 0.9, repeat: Infinity, delay: 0.3, ease: 'easeInOut' }}
                    className="inline-block"
                  >
                    •
                  </motion.span>
                </div>
                <div className="mt-4">
                  <DualProgressBar progress={uploadProgress} />
                </div>
              </motion.div>
            ) : phase === PHASES.PARSING ? (
              <ParsingState key="parsing" />
            ) : null}
          </AnimatePresence>

          <AnimatePresence initial={false}>
            {error ? (
              <StatusBanner
                key="error"
                tone="error"
                title="Something went wrong"
                message={error}
              />
            ) : successMessage && phase !== PHASES.SUCCESS ? (
              <StatusBanner key="info" tone="info" title="Ready to go" message={successMessage} />
            ) : null}
          </AnimatePresence>
        </div>

        <div className="space-y-5">
          <motion.div
            whileHover={{ y: -4 }}
            className="rounded-[24px] border border-white/10 bg-slate-900/70 p-6 shadow-xl shadow-black/20"
          >
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
                  Workflow
                </p>
                <h3 className="mt-2 text-lg font-semibold text-white">What happens next</h3>
              </div>
              <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
                2-step pipeline
              </div>
            </div>

            <div className="space-y-4">
              {[
                ['1', 'Upload', 'We store the PDF in Supabase Storage under your account.'],
                ['2', 'Parse', 'The backend extracts text and asks Groq for structured output.'],
                ['3', 'Match-ready', 'Your parsed profile can now feed preferences and job matching.'],
              ].map(([step, title, text]) => (
                <div
                  key={step}
                  className="flex gap-4 rounded-2xl border border-white/8 bg-white/4 px-4 py-4"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-500 text-sm font-semibold text-white">
                    {step}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{title}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-400">{text}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            whileHover={{ y: -4 }}
            className="rounded-[24px] border border-white/10 bg-slate-900/70 p-6 shadow-xl shadow-black/20"
          >
            <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
              Accepted format
            </p>
            <h3 className="mt-2 text-lg font-semibold text-white">PDF only</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              If you upload a non-PDF file, the UI will block the action and show a clean error
              message before any network call is made.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="mt-6">
        <AnimatePresence mode="wait">
          {phase === PHASES.SUCCESS && parsedData ? (
            <motion.div
              key="success-reveal"
              initial={{ opacity: 0, y: 16, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.45, ease: 'easeOut' }}
              className="relative"
            >
              <div className="pointer-events-none absolute inset-0 rounded-[28px] bg-emerald-400/10 blur-2xl" />
              <ResultCard parsedData={parsedData} onReset={resetState} />
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
    </motion.section>
  )
}

export default ResumeUploader
