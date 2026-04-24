function Card({ className = '', ...props }) {
  return (
    <div
      className={`rounded-2xl border border-white/10 bg-white/5 shadow-lg shadow-black/20 backdrop-blur-lg transition duration-300 hover:shadow-[0_0_30px_rgba(59,130,246,0.12)] ${className}`}
      {...props}
    />
  )
}

function CardContent({ className = '', ...props }) {
  return <div className={`p-6 ${className}`} {...props} />
}

export { Card, CardContent }
