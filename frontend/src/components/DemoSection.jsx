import { motion, useReducedMotion } from 'framer-motion'
import { ArrowUpRight, CheckCircle2 } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'

function DemoSection() {
  const shouldReduceMotion = useReducedMotion()

  return (
    <section id="faq" className="px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-6xl items-center gap-10 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.26em] text-blue-300/80">
            Product Preview
          </p>
          <h2 className="mt-4 text-3xl font-semibold tracking-[-0.03em] text-white sm:text-4xl">
            See the signal before you spend time applying
          </h2>
          <p className="mt-4 max-w-xl text-base leading-7 text-slate-400">
            InternPilot gives students a clear read on fit so they can focus on the internships
            worth pursuing and write better outreach from the start.
          </p>
          <div className="mt-8 space-y-4 text-sm text-slate-300">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-300" />
              Match scores tied to resume skills and preferences
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-300" />
              Clear explanations for why a role fits
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-300" />
              Faster decision-making for outreach and applications
            </div>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.45, ease: 'easeOut' }}
          className="relative"
        >
          <motion.div
            animate={shouldReduceMotion ? undefined : { y: [0, -10, 0] }}
            transition={shouldReduceMotion ? undefined : { duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            style={{ willChange: 'transform' }}
            className="relative"
          >
            <div className="absolute inset-0 rounded-[32px] bg-gradient-to-br from-blue-500/15 via-violet-500/10 to-cyan-400/10 blur-3xl" />
            <Card className="relative rounded-[28px] border-white/12 bg-slate-950/70">
              <CardContent className="p-6 sm:p-7">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm text-slate-400">Match preview</p>
                    <h3 className="mt-2 text-2xl font-semibold text-white">Backend Engineer Intern</h3>
                    <p className="mt-2 text-sm text-slate-400">Stripe • Remote</p>
                  </div>
                  <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3 text-right">
                    <p className="text-xs uppercase tracking-[0.22em] text-emerald-300">Match</p>
                    <p className="mt-1 text-2xl font-semibold text-white">92%</p>
                  </div>
                </div>

                <div className="mt-8 space-y-5">
                  <div>
                    <div className="mb-3 flex items-center justify-between text-sm">
                      <span className="text-slate-300">Skills match</span>
                      <span className="text-slate-400">Python, FastAPI, SQL</span>
                    </div>
                    <div className="h-2.5 overflow-hidden rounded-full bg-white/8">
                      <div className="h-full w-[92%] rounded-full bg-gradient-to-r from-blue-500 via-cyan-400 to-violet-500" />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-md">
                    <p className="text-sm font-medium text-white">Why this role fits</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {['Strong backend alignment', 'Remote-friendly', 'Projects match stack'].map(
                        (item) => (
                          <span
                            key={item}
                            className="rounded-full border border-white/10 bg-slate-900/80 px-3 py-1 text-xs text-slate-300"
                          >
                            {item}
                          </span>
                        )
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-2xl border border-blue-400/15 bg-blue-500/8 px-4 py-4 backdrop-blur-md">
                    <div>
                      <p className="text-sm font-medium text-white">Ready to generate outreach</p>
                      <p className="mt-1 text-sm text-slate-400">
                        Build a sharper intro using your real resume signals
                      </p>
                    </div>
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/6 text-slate-200">
                      <ArrowUpRight className="h-4 w-4" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}

export default DemoSection
