import Navbar from './Navbar'

function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
    </div>
  )
}

export default AppLayout