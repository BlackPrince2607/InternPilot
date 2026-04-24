import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

function CTA() {
  return (
    <section id="contact" className="px-4 py-20 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="mx-auto max-w-5xl rounded-[32px] border border-white/10 bg-slate-950/70 p-[1px] shadow-[0_30px_80px_-35px_rgba(59,130,246,0.5)]"
      >
        <div className="rounded-[31px] bg-[linear-gradient(135deg,rgba(59,130,246,0.10),rgba(11,15,25,0.94)_35%,rgba(139,92,246,0.10))] px-6 py-14 text-center backdrop-blur-xl sm:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.26em] text-slate-400">
            Start Today
          </p>
          <h2 className="mt-4 text-3xl font-semibold tracking-[-0.03em] text-white sm:text-4xl">
            Start landing internships today
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-slate-400">
            Build a clearer search process, find stronger-fit roles, and send outreach with more
            confidence.
          </p>
          <div className="mt-8">
            <Link to="/signup">
              <Button size="lg">Sign Up Free</Button>
            </Link>
          </div>
        </div>
      </motion.div>
    </section>
  )
}

export default CTA
