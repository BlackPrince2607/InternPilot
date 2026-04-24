import { Link } from 'react-router-dom'

const links = [
  { label: 'About', sectionId: 'about' },
  { label: 'Privacy', sectionId: 'features' },
  { label: 'FAQ', sectionId: 'faq' },
  { label: 'Contact', sectionId: 'contact' },
]

function Footer() {
  const handleSectionNavigation = (sectionId) => {
    requestAnimationFrame(() => {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }

  return (
    <footer className="border-t border-white/8 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 text-sm text-slate-400 sm:flex-row">
        <p className="font-medium text-slate-300">InternPilot</p>
        <div className="flex flex-wrap items-center justify-center gap-6">
          {links.map((link) => (
            <Link
              key={link.label}
              to="/"
              onClick={() => handleSectionNavigation(link.sectionId)}
              className="transition-colors duration-200 hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </footer>
  )
}

export default Footer
