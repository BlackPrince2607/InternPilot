import { useEffect, useRef } from 'react'
import { useReducedMotion } from 'framer-motion'

const ORBS = [
  {
    baseX: 0.18,
    baseY: 0.22,
    radius: 0.34,
    amplitudeX: 0.07,
    amplitudeY: 0.08,
    speed: 0.00022,
    color: '64, 156, 255',
  },
  {
    baseX: 0.78,
    baseY: 0.28,
    radius: 0.3,
    amplitudeX: 0.06,
    amplitudeY: 0.06,
    speed: 0.00018,
    color: '132, 92, 246',
  },
  {
    baseX: 0.48,
    baseY: 0.8,
    radius: 0.38,
    amplitudeX: 0.08,
    amplitudeY: 0.05,
    speed: 0.00014,
    color: '34, 211, 238',
  },
]

function ShaderAnimation({ className = '' }) {
  const canvasRef = useRef(null)
  const shouldReduceMotion = useReducedMotion()

  useEffect(() => {
    console.log('ShaderAnimation mounted')

    const canvas = canvasRef.current
    if (!canvas) {
      return undefined
    }

    const context = canvas.getContext('2d')
    if (!context) {
      console.error('ShaderAnimation: 2D canvas context unavailable')
      return undefined
    }

    let frameId = 0
    let width = 0
    let height = 0
    let dpr = Math.min(window.devicePixelRatio || 1, 2)

    const resize = () => {
      const parent = canvas.parentElement
      if (!parent) {
        return
      }

      width = parent.clientWidth || window.innerWidth
      height = parent.clientHeight || window.innerHeight
      dpr = Math.min(window.devicePixelRatio || 1, 2)

      canvas.width = Math.floor(width * dpr)
      canvas.height = Math.floor(height * dpr)
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`

      context.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    const drawBackground = () => {
      const background = context.createLinearGradient(0, 0, 0, height)
      background.addColorStop(0, 'rgba(6, 10, 18, 0.08)')
      background.addColorStop(0.55, 'rgba(6, 10, 18, 0.18)')
      background.addColorStop(1, 'rgba(6, 10, 18, 0.42)')
      context.fillStyle = background
      context.fillRect(0, 0, width, height)
    }

    const drawOrb = (orb, time, index) => {
      const phase = time * orb.speed + index * 1.8
      const x = width * (orb.baseX + Math.sin(phase) * orb.amplitudeX)
      const y = height * (orb.baseY + Math.cos(phase * 1.2) * orb.amplitudeY)
      const radius = Math.max(width, height) * orb.radius

      const gradient = context.createRadialGradient(x, y, 0, x, y, radius)
      gradient.addColorStop(0, `rgba(${orb.color}, 0.42)`)
      gradient.addColorStop(0.35, `rgba(${orb.color}, 0.2)`)
      gradient.addColorStop(1, `rgba(${orb.color}, 0)`)

      context.globalCompositeOperation = 'lighter'
      context.fillStyle = gradient
      context.beginPath()
      context.arc(x, y, radius, 0, Math.PI * 2)
      context.fill()
    }

    const drawNoise = () => {
      context.globalCompositeOperation = 'source-over'
      context.fillStyle = 'rgba(255, 255, 255, 0.035)'

      for (let i = 0; i < 28; i += 1) {
        const x = Math.random() * width
        const y = Math.random() * height
        const size = Math.random() * 1.5 + 0.5
        context.fillRect(x, y, size, size)
      }
    }

    const render = (time) => {
      context.clearRect(0, 0, width, height)
      drawBackground()

      ORBS.forEach((orb, index) => {
        drawOrb(orb, shouldReduceMotion ? 0 : time, index)
      })

      drawNoise()

      if (!shouldReduceMotion) {
        frameId = window.requestAnimationFrame(render)
      }
    }

    resize()
    render(0)

    const handleResize = () => {
      resize()
      if (shouldReduceMotion) {
        render(0)
      }
    }

    window.addEventListener('resize', handleResize)

    if (!shouldReduceMotion) {
      frameId = window.requestAnimationFrame(render)
    }

    return () => {
      window.removeEventListener('resize', handleResize)
      if (frameId) {
        window.cancelAnimationFrame(frameId)
      }
    }
  }, [shouldReduceMotion])

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
    >
      <canvas
        ref={canvasRef}
        className="h-full w-full"
        data-testid="shader-animation-canvas"
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.12),transparent_30%),linear-gradient(180deg,rgba(7,11,20,0.02),rgba(7,11,20,0.22)_56%,rgba(7,11,20,0.5))]" />
    </div>
  )
}

export default ShaderAnimation
