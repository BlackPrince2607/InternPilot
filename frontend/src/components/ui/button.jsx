function buttonVariants({ variant = 'default', size = 'default', className = '' } = {}) {
  const base =
    'inline-flex cursor-pointer items-center justify-center rounded-xl font-medium backdrop-blur-md transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0b0f19] disabled:pointer-events-none disabled:opacity-50'

  const variants = {
    default:
      'border border-white/20 bg-gradient-to-r from-blue-500/90 via-blue-400/85 to-violet-500/90 px-5 text-white shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:scale-[1.02] hover:border-white/30 hover:bg-white/20 hover:shadow-[0_0_26px_rgba(59,130,246,0.38)]',
    secondary:
      'border border-white/20 bg-white/10 text-slate-100 shadow-[0_0_20px_rgba(59,130,246,0.16)] hover:scale-[1.02] hover:bg-white/20 hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]',
    ghost: 'border border-transparent text-slate-300 hover:bg-white/6 hover:text-white',
  }

  const sizes = {
    default: 'h-11 px-5 text-sm',
    lg: 'h-12 px-6 text-sm sm:h-13 sm:px-7',
    sm: 'h-9 px-4 text-sm',
  }

  return [base, variants[variant], sizes[size], className].filter(Boolean).join(' ')
}

function Button({ className, variant, size, asChild = false, ...props }) {
  const Comp = asChild ? 'span' : 'button'

  return <Comp className={buttonVariants({ variant, size, className })} {...props} />
}

export { Button, buttonVariants }
