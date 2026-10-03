import { useCallback, useEffect, useMemo, useState, type DragEvent } from 'react'
import './App.css'

type Health = {
  status: string
  model_loaded: boolean
  device: string
}

type PredictResponse = {
  source: string
  image_size: number[]
  class_pixel_counts: Record<string, number>
  has_ground_truth: boolean
  gt_class_pixel_counts?: Record<string, number> | null
  image_png_base64: string
  mask_png_base64: string
  overlay_png_base64: string
}

const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

/** Ignore tiny speckles — need a real blob of “suspicious” tissue. */
const TUMOR_PIXEL_THRESHOLD = 80

function b64Src(b64: string) {
  return `data:image/png;base64,${b64}`
}

function tumorPixelCount(counts: Record<string, number>): number {
  return Object.entries(counts).reduce((sum, [cls, n]) => {
    if (cls === '0') return sum
    return sum + n
  }, 0)
}

function verdictFromCounts(counts: Record<string, number>): {
  found: boolean
  headline: string
  detail: string
} {
  const tumorPx = tumorPixelCount(counts)
  if (tumorPx >= TUMOR_PIXEL_THRESHOLD) {
    return {
      found: true,
      headline: 'Heads up — this scan looks suspicious.',
      detail:
        'Our AI thinks there may be a tumor here. In a real clinic this would mean: get checked urgently — don’t wait it out.',
    }
  }
  return {
    found: false,
    headline: 'Looking clear — no tumor spotted.',
    detail:
      'Nothing worrying showed up on this one. Demo verdict: you’re free to go grab some KFC. (Still a demo, not a doctor.)',
  }
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [apiStatus, setApiStatus] = useState<'checking' | 'ready' | 'offline'>('checking')
  const [healthTick, setHealthTick] = useState(0)
  const [file, setFile] = useState<File | null>(null)
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PredictResponse | null>(null)

  useEffect(() => {
    let cancelled = false
    const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

    ;(async () => {
      let attempt = 0
      while (!cancelled) {
        attempt += 1
        setApiStatus((prev) => (prev === 'ready' ? prev : 'checking'))
        try {
          const ctrl = new AbortController()
          const timer = setTimeout(() => ctrl.abort(), 60_000)
          const r = await fetch(`${API_BASE}/health`, { signal: ctrl.signal })
          clearTimeout(timer)
          if (!r.ok) throw new Error(`API ${r.status}`)
          const h = (await r.json()) as Health
          if (cancelled) return
          setHealth(h)
          setApiStatus(h.status === 'ok' ? 'ready' : 'offline')
          if (h.status === 'ok') return
        } catch {
          if (cancelled) return
          setHealth(null)
          setApiStatus('offline')
        }
        // Keep waking free-tier / redeploys until healthy
        await sleep(Math.min(4_000 + attempt * 2_000, 15_000))
      }
    })()

    return () => {
      cancelled = true
    }
  }, [healthTick])

  const verdict = useMemo(
    () => (result ? verdictFromCounts(result.class_pixel_counts) : null),
    [result],
  )

  const onFiles = useCallback((list: FileList | null) => {
    const next = list?.[0] ?? null
    setError(null)
    setResult(null)
    if (!next) {
      setFile(null)
      return
    }
    const lower = next.name.toLowerCase()
    if (!lower.endsWith('.h5') && !lower.endsWith('.hdf5')) {
      setError('Please pick a brain-scan file ending in .h5')
      setFile(null)
      return
    }
    setFile(next)
  }, [])

  const runPredict = useCallback(async () => {
    if (!file) return
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      const body = new FormData()
      body.append('file', file)
      const res = await fetch(`${API_BASE}/predict`, {
        method: 'POST',
        body,
      })
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || `Something went wrong (${res.status})`)
      }
      const data = (await res.json()) as PredictResponse
      setResult(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not check this scan — is the helper service running?',
      )
    } finally {
      setBusy(false)
    }
  }, [file])

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDrag(false)
    onFiles(e.dataTransfer.files)
  }

  return (
    <div className="shell">
      <header className="hero">
        <h1 className="brand">Neuro</h1>
        <p className="tagline">
          Drop in a brain scan. We’ll check it for a possible tumor — and give
          you a plain-English answer.
        </p>
      </header>

      <div className="status-row">
        <span className="pill">
          <span
            className={`dot ${
              apiStatus === 'ready' && health?.model_loaded
                ? ''
                : apiStatus === 'checking'
                  ? 'warn'
                  : 'bad'
            }`}
          />
          {apiStatus === 'checking'
            ? 'Waking API… free tier can take a minute'
            : health
              ? health.model_loaded
                ? 'Ready to check scans'
                : 'Service is up, but the AI brain isn’t loaded yet'
              : 'API still waking — retrying automatically'}
        </span>
        {apiStatus !== 'ready' && (
          <button
            type="button"
            className="btn ghost"
            onClick={() => {
              setApiStatus('checking')
              setHealthTick((n) => n + 1)
            }}
          >
            Retry now
          </button>
        )}
      </div>

      <section className="workspace">
        <div
          className={`upload-zone${drag ? ' drag' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDrag(true)
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={onDrop}
        >
          <input
            type="file"
            accept=".h5,.hdf5,application/x-hdf5,application/octet-stream"
            onChange={(e) => onFiles(e.target.files)}
            aria-label="Upload a brain scan file"
          />
          <div className="upload-copy">
            <strong>Drop a brain scan here</strong>
            <span>or click to choose a .h5 file from your computer</span>
          </div>
        </div>

        <div className="actions">
          <button
            type="button"
            className="btn primary-pulse"
            disabled={!file || busy || !health?.model_loaded}
            onClick={() => void runPredict()}
          >
            {busy ? 'Checking the scan…' : 'Check for a tumor'}
          </button>
          <button
            type="button"
            className="btn ghost"
            disabled={!file && !result}
            onClick={() => {
              setFile(null)
              setResult(null)
              setError(null)
            }}
          >
            Start over
          </button>
          {file ? <span className="file-name">Selected: {file.name}</span> : null}
        </div>

        {error ? <p className="error">{error}</p> : null}

        {result && verdict ? (
          <div className="results">
            <div
              className={`verdict ${verdict.found ? 'urgent' : 'clear'}`}
              role="status"
            >
              <p className="verdict-kicker">
                {verdict.found ? 'Needs attention' : 'All clear'}
              </p>
              <h2 className="verdict-title">{verdict.headline}</h2>
              <p className="verdict-detail">{verdict.detail}</p>
            </div>

            <h3 className="panel-title">What you’re looking at</h3>
            <div className="gallery">
              <figure className="frame">
                <figcaption>The brain scan</figcaption>
                <img
                  src={b64Src(result.image_png_base64)}
                  alt="The original brain scan"
                />
              </figure>
              <figure className="frame">
                <figcaption>Where it looks odd</figcaption>
                <img
                  src={b64Src(result.mask_png_base64)}
                  alt="Areas the AI thinks may be abnormal"
                />
              </figure>
              <figure className="frame">
                <figcaption>Scan with findings marked</figcaption>
                <img
                  src={b64Src(result.overlay_png_base64)}
                  alt="Brain scan with possible tumor areas highlighted"
                />
              </figure>
            </div>

            <p className="note">
              Fun demo only — not real medical advice. A clinician would still
              read the full study. Colored patches = “hey, look here,” not a
              prescription.
            </p>
          </div>
        ) : null}
      </section>
    </div>
  )
}
