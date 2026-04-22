import { motion } from 'framer-motion'
import { BriefcaseBusiness, FileUp, Send } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'

const steps = [
  {
    icon: FileUp,
    title: 'Upload Resume',
    description: 'Drop in your resume once and turn it into a structured candidate profile.',
  },
  {
    icon: BriefcaseBusiness,
    title: 'AI Matches Jobs',
    description: 'See internship opportunities ranked against your skills, role fit, and goals.',
  },
  {
    icon: Send,
    title: 'Send Smart Emails',
    description: 'Write sharper outreach with context that actually sounds relevant to the role.',
  },
]

function HowItWorks() {
  return (
    <section id="how-it-works" className="px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.26em] text-blue-300/80">
            How It Works
          </p>
          <h2 className="mt-4 text-3xl font-semibold tracking-[-0.03em] text-white sm:text-4xl">
            Three steps from resume to outreach
          </h2>
          <p className="mt-4 text-base leading-7 text-slate-400">
            InternPilot keeps the process focused so students spend less time guessing and more
            time applying with intent.
          </p>
        </div>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {steps.map((step, index) => {
            const Icon = step.icon

            return (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.4, delay: index * 0.08, ease: 'easeOut' }}
                whileHover={{ y: -6, scale: 1.02 }}
              >
                <Card className="group h-full overflow-hidden border-white/10 bg-white/[0.045]">
                  <CardContent className="relative h-full p-7">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(96,165,250,0.15),transparent_55%)] opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
                    <div className="relative">
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-blue-400/20 bg-blue-500/10 text-blue-200 shadow-lg shadow-blue-950/20">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="mt-6 flex items-center gap-3">
                        <span className="text-sm text-slate-500">0{index + 1}</span>
                        <h3 className="text-xl font-semibold text-white">{step.title}</h3>
                      </div>
                      <p className="mt-4 text-sm leading-7 text-slate-400">{step.description}</p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export default HowItWorks
