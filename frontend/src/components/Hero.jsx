import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import ShaderAnimation from '@/components/ui/shader-animation'

const containerMotion = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.55,
      ease: 'easeOut',
      staggerChildren: 0.12,
    },
  },
}

const itemMotion = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' } },
}

function Hero() {
  const handleScrollToHowItWorks = () => {
    requestAnimationFrame(() => {
      document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }

  return (
    <section className="relative min-h-screen overflow-hidden bg-[#0b0f19]">
      <div className="absolute inset-0 z-0">
        <ShaderAnimation />
      </div>
      <div className="absolute inset-0 z-10 bg-[linear-gradient(180deg,rgba(2,6,23,0.16),rgba(2,6,23,0.42)_55%,rgba(2,6,23,0.68))]" />
      <div className="absolute inset-x-0 top-0 z-20 px-4 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <div className="mx-auto flex max-w-6xl items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-lg sm:px-5">
          <Link to="/" className="text-sm font-semibold tracking-[0.18em] text-white uppercase">
            InternPilot
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" size="sm" className="border-white/10 bg-white/4">
                Login
              </Button>
            </Link>
            <Link to="/signup">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </div>
      <motion.div
        variants={containerMotion}
        initial="hidden"
        animate="visible"
        className="relative z-20 mx-auto flex min-h-screen w-full max-w-4xl flex-col items-center justify-center px-6 text-center"
      >
        <motion.div
          variants={itemMotion}
          className="mb-6 inline-flex items-center rounded-full border border-white/15 bg-white/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-200 backdrop-blur-md"
        >
          AI Internship Copilot
        </motion.div>

        <motion.h1
          variants={itemMotion}
          className="max-w-4xl text-5xl font-semibold tracking-[-0.04em] text-white sm:text-6xl lg:text-7xl"
        >
          Land Internships Without the Cold Email Struggle
        </motion.h1>

        <motion.p
          variants={itemMotion}
          className="mt-6 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg"
        >
          Upload your resume. Get matched with real opportunities. Send smarter emails.
        </motion.p>

        <motion.div
          variants={itemMotion}
          className="mt-10 flex flex-col items-center gap-3 sm:flex-row"
        >
          <Link to="/signup">
            <Button size="lg">Get Started</Button>
          </Link>
          <Link to="/" onClick={handleScrollToHowItWorks}>
            <Button variant="secondary" size="lg">
              See How It Works
            </Button>
          </Link>
        </motion.div>

        <motion.div
          variants={itemMotion}
          className="mt-12 flex flex-wrap items-center justify-center gap-4 text-sm text-slate-400"
        >
          <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1.5 backdrop-blur-md">
            Resume parsing in minutes
          </span>
          <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1.5 backdrop-blur-md">
            Match-first internship discovery
          </span>
          <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1.5 backdrop-blur-md">
            Cleaner outreach workflow
          </span>
        </motion.div>
      </motion.div>
    </section>
  )
}

export default Hero
