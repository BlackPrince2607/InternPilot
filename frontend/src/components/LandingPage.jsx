import CTA from '@/components/CTA'
import DemoSection from '@/components/DemoSection'
import Features from '@/components/Features'
import Footer from '@/components/Footer'
import Hero from '@/components/Hero'
import HowItWorks from '@/components/HowItWorks'
import TrustBar from '@/components/TrustBar'

function LandingPage() {
  return (
    <main className="min-h-screen bg-[#0b0f19] text-slate-100">
      <Hero />
      <TrustBar />
      <HowItWorks />
      <Features />
      <DemoSection />
      <CTA />
      <Footer />
    </main>
  )
}

export default LandingPage
