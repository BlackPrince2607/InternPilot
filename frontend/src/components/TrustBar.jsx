import { motion } from 'framer-motion'

const universities = ['IIT', 'NIT', 'BITS', 'VIT', 'DTU', 'IIIT']

function TrustBar() {
  return (
    <section id="about" className="border-y border-white/8 bg-white/[0.02] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-5">
        <p className="text-center text-xs font-semibold uppercase tracking-[0.28em] text-slate-400">
          Trusted by 1000+ students
        </p>

        <div className="flex w-full flex-wrap items-center justify-center gap-x-10 gap-y-4">
          {universities.map((name, index) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 0.5, y: 0 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ duration: 0.35, delay: index * 0.06, ease: 'easeOut' }}
              className="text-lg font-semibold tracking-[0.32em] text-slate-500"
            >
              {name}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default TrustBar
