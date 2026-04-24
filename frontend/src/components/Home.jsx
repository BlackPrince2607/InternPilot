import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import ResumeUploader from './ResumeUploader'
import Preferences from './preferences'

function Home() {
  const navigate = useNavigate()

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8">
        <motion.section
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: 'easeOut' }}
          className="overflow-hidden rounded-[28px] border border-white/10 bg-slate-950/75 shadow-2xl shadow-slate-950/40 backdrop-blur"
        >
          <div className="border-b border-white/10 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 px-6 py-6 sm:px-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl">
                <div className="mb-3 inline-flex items-center rounded-full border border-blue-400/30 bg-blue-400/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.24em] text-blue-200">
                  InternPilot AI
                </div>
                <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                  Upload once. Parse instantly. Match faster.
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">
                  Turn your resume into a structured candidate profile, then move straight into
                  preferences and internship matches with a smoother, production-grade workflow.
                </p>
              </div>

              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/matches')}
                className="inline-flex items-center justify-center rounded-2xl border border-emerald-400/30 bg-emerald-400/10 px-5 py-3 text-sm font-semibold text-emerald-200 shadow-lg shadow-emerald-950/30 transition hover:border-emerald-300/40 hover:bg-emerald-400/15"
              >
                View Matches
              </motion.button>
            </div>
          </div>

          <div className="grid gap-8 px-4 py-6 sm:px-6 lg:grid-cols-[1.35fr_0.9fr] lg:px-8">
            <ResumeUploader />
            <Preferences />
          </div>
        </motion.section>
      </div>
    </main>
  )
}

export default Home
      
