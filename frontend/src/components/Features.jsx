import { motion } from 'framer-motion'
import { BrainCircuit, ClipboardList, Mail, ScanSearch } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'

const features = [
  {
    icon: ScanSearch,
    title: 'AI Resume Parsing',
    description: 'Extract skills, education, and project signals into a clean candidate profile.',
  },
  {
    icon: BrainCircuit,
    title: 'Smart Job Matching',
    description: 'Prioritize internship opportunities based on what actually fits your background.',
  },
  {
    icon: Mail,
    title: 'Cold Email Generator',
    description: 'Draft faster outreach with clearer context, stronger relevance, and less guesswork.',
  },
  {
    icon: ClipboardList,
    title: 'Application Tracking',
    description: 'Keep your search organized across saved roles, outreach, and interview progress.',
  },
]

function Features() {
  return (
    <section id="features" className="px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="flex max-w-3xl flex-col gap-4">
          <p className="text-sm font-semibold uppercase tracking-[0.26em] text-violet-300/80">
            Features
          </p>
          <h2 className="text-3xl font-semibold tracking-[-0.03em] text-white sm:text-4xl">
            Everything you need to run a tighter internship search
          </h2>
          <p className="max-w-2xl text-base leading-7 text-slate-400">
            Designed to help students move from messy job hunting toward a clearer, faster, more
            confident process.
          </p>
        </div>

        <div className="mt-12 grid gap-5 md:grid-cols-2">
          {features.map((feature, index) => {
            const Icon = feature.icon

            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.4, delay: index * 0.06, ease: 'easeOut' }}
                whileHover={{ y: -6, scale: 1.02 }}
              >
                <Card className="group h-full border-white/10 bg-white/[0.045]">
                  <CardContent className="h-full p-7">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-violet-400/20 bg-violet-500/10 text-violet-200 transition duration-200 group-hover:shadow-[0_0_32px_rgba(139,92,246,0.18)]">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="mt-6 text-xl font-semibold text-white">{feature.title}</h3>
                    <p className="mt-3 text-sm leading-7 text-slate-400">{feature.description}</p>
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

export default Features
