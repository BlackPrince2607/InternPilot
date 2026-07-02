import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import api from '../lib/api'
import { CenterLoader, InlineAlert } from '../components/ui/feedback'

function createDownloadName(index) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  return `internpilot-image-${index + 1}-${timestamp}.png`
}

export default function Images() {
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState('')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const canGenerate = useMemo(() => prompt.trim().length >= 3 && !loading, [prompt, loading])

  const handleGenerate = async () => {
    if (!canGenerate) {
      setError('Enter at least 3 characters in your prompt.')
      return
    }

    setLoading(true)
    setError('')
    setNotice('')

    try {
      const res = await api.post('/images/generate', { prompt: prompt.trim() })
      const image = {
        id: res.data.image_id || `${Date.now()}`,
        prompt: res.data.prompt || prompt.trim(),
        image_url: res.data.image_url,
        provider: res.data.provider || 'placeholder',
      }
      setItems((prev) => [image, ...prev])
      setNotice(`Image generated using provider: ${image.provider}.`)
      setPrompt('')
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Failed to generate image.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (imageUrl, index) => {
    try {
      const a = document.createElement('a')
      a.href = imageUrl
      a.download = createDownloadName(index)
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    } catch {
      setError('Could not download this image.')
    }
  }

  if (loading && items.length === 0) {
    return <CenterLoader title="Generating first image" subtitle="This can take a few seconds depending on provider settings." />
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <section className="rounded-[28px] border border-white/10 bg-slate-950/70 p-6 shadow-2xl shadow-black/30 backdrop-blur sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.24em] text-fuchsia-200/80">Generative Tools</p>
              <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">Image Generator</h1>
              <p className="mt-2 text-sm text-slate-300">
                Create prompt-based images, review results, and download assets for your portfolio.
              </p>
            </div>
            <button
              onClick={() => navigate('/app')}
              className="rounded-2xl border border-white/15 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/10"
            >
              Back to App
            </button>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-[1fr_auto]">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the image you want: eg. Isometric workspace with laptop, charts, and internship roadmap"
              rows={4}
              className="w-full rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-fuchsia-300/40"
            />
            <button
              onClick={handleGenerate}
              disabled={!canGenerate}
              className="h-fit rounded-2xl border border-fuchsia-400/30 bg-fuchsia-500/15 px-5 py-3 text-sm font-semibold text-fuchsia-100 transition hover:bg-fuchsia-500/25 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Generating...' : 'Generate'}
            </button>
          </div>
        </section>

        {error ? <InlineAlert tone="error" message={error} /> : null}
        {notice && !error ? <InlineAlert tone="success" message={notice} /> : null}

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item, index) => (
            <article
              key={item.id}
              className="overflow-hidden rounded-[24px] border border-white/10 bg-slate-900/70 shadow-lg shadow-black/20"
            >
              {item.image_url ? (
                <img src={item.image_url} alt={item.prompt} className="h-60 w-full object-cover" />
              ) : (
                <div className="flex h-60 items-center justify-center text-sm text-slate-400">No preview</div>
              )}
              <div className="space-y-3 p-4">
                <p className="line-clamp-3 text-sm text-slate-200">{item.prompt}</p>
                <div className="flex items-center justify-between gap-2">
                  <span className="rounded-full border border-white/15 bg-white/5 px-2.5 py-1 text-xs text-slate-300">
                    {item.provider}
                  </span>
                  <button
                    onClick={() => handleDownload(item.image_url, index)}
                    className="rounded-xl border border-emerald-400/30 bg-emerald-500/15 px-3 py-1.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-500/25"
                  >
                    Download
                  </button>
                </div>
              </div>
            </article>
          ))}
        </section>

        {!loading && items.length === 0 ? (
          <section className="rounded-[24px] border border-dashed border-white/15 bg-slate-900/55 p-8 text-center">
            <h2 className="text-xl font-semibold text-white">No images generated yet</h2>
            <p className="mt-2 text-sm text-slate-400">Write a prompt and click Generate to create your first image.</p>
          </section>
        ) : null}
      </div>
    </main>
  )
}
