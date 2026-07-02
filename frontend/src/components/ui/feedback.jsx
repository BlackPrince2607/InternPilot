export function InlineAlert({ tone = 'info', title, message, className = '' }) {
  const toneClasses = {
    info: 'border-blue-500/25 bg-blue-500/10 text-blue-100',
    success: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-100',
    error: 'border-rose-500/25 bg-rose-500/10 text-rose-100',
    warning: 'border-amber-500/25 bg-amber-500/10 text-amber-100',
  }

  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${toneClasses[tone]} ${className}`}>
      {title ? <p className="font-semibold">{title}</p> : null}
      {message ? <p className={title ? 'mt-1 opacity-90' : ''}>{message}</p> : null}
    </div>
  )
}

export function CenterLoader({ title = 'Loading...', subtitle }) {
  return (
    <div className="flex min-h-[45vh] flex-col items-center justify-center px-4 text-center">
      <div className="mb-4 h-11 w-11 animate-spin rounded-full border-4 border-cyan-500/30 border-t-cyan-300" />
      <p className="text-base font-semibold text-slate-100">{title}</p>
      {subtitle ? <p className="mt-2 max-w-md text-sm text-slate-400">{subtitle}</p> : null}
    </div>
  )
}
