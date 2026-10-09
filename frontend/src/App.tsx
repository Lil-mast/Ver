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

type DemoCase = {
  id: string
  title: string
  source: string
  summary: string
  where: string
  nerdy: string
  has_tumor: boolean
  images: {
    scan: string
    label: string
    overlay: string
  }
}

const DEMO_CASES: DemoCase[] = [
  {
    id: 'clear',
    title: 'Clear reference',
    source: 'volume_1_slice_10.h5',
    summary: 'No tumor pixels are marked in this slice’s reference label. Demo verdict: clear for this cut, so you can go grab some KFC. It still says nothing about the rest of a scan.',
    where: 'Nowhere on this slice: the reference label contains no marked tumor pixels. A clear single cut does not mean the full scan is clear.',
    nerdy: '240 × 240 pixels · 4 MRI channels (T1, T1ce, T2, FLAIR) · 0 / 57,600 tumor-labeled pixels.',
    has_tumor: false,
    images: {
      scan: '/demos/clear/scan.png',
      label: '/demos/clear/label.png',
      overlay: '/demos/clear/overlay.png',
    },
  },
  {
    id: 'tumor-a',
    title: 'Tumor example A',
    source: 'volume_1_slice_68.h5',
    summary: 'The expert reference label marks tumor tissue on this slice.',
    where: 'On the displayed slice, the labeled region sits around the center and extends toward the right side of the image. Image-orientation metadata is not included, so this view cannot reliably identify anatomical left or right.',
    nerdy: '240 × 240 pixels · 5,040 labeled pixels (8.8%) · label centroid at x=52%, y=39% of the displayed image · 3 non-background label classes.',
    has_tumor: true,
    images: {
      scan: '/demos/tumor-a/scan.png',
      label: '/demos/tumor-a/label.png',
      overlay: '/demos/tumor-a/overlay.png',
    },
  },
  {
    id: 'tumor-b',
    title: 'Tumor example B',
    source: 'volume_40_slice_56.h5',
    summary: 'The expert reference label marks tumor tissue on this slice.',
    where: 'On the displayed slice, the labeled region is left of center and extends across the middle. Image-orientation metadata is not included, so this view cannot reliably identify anatomical left or right.',
    nerdy: '240 × 240 pixels · 4,881 labeled pixels (8.5%) · label centroid at x=29%, y=53% of the displayed image · 3 non-background label classes.',
    has_tumor: true,
    images: {
      scan: '/demos/tumor-b/scan.png',
      label: '/demos/tumor-b/label.png',
      overlay: '/demos/tumor-b/overlay.png',
    },
  },
]

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
  const [demoCase, setDemoCase] = useState<DemoCase | null>(null)

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
    () =>
      result
        ? verdictFromCounts(result.class_pixel_counts)
        : demoCase
          ? {
              found: demoCase.has_tumor,
              headline: demoCase.title,
              detail: demoCase.summary,
            }
          : null,
    [result, demoCase],
  )

  const onFiles = useCallback((list: FileList | null) => {
    const next = list?.[0] ?? null
    setError(null)
    setResult(null)
    setDemoCase(null)
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
      setDemoCase(null)
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
            disabled={!file && !result && !demoCase}
            onClick={() => {
              setFile(null)
              setResult(null)
              setDemoCase(null)
              setError(null)
            }}
          >
            Start over
          </button>
          {file ? <span className="file-name">Selected: {file.name}</span> : null}
        </div>

        <section className="demo-picker" aria-labelledby="demo-heading">
          <div>
            <h2 id="demo-heading" className="panel-title">Or explore a sample case</h2>
            <p className="demo-caption">Three paired BraTS examples, ready without an API connection.</p>
          </div>
          <div className="demo-buttons">
            {DEMO_CASES.map((sample) => (
              <button
                type="button"
                className={`btn ghost demo-button${demoCase?.id === sample.id ? ' selected' : ''}`}
                key={sample.id}
                onClick={() => {
                  setDemoCase(sample)
                  setResult(null)
                  setFile(null)
                  setError(null)
                }}
              >
                {sample.title}
              </button>
            ))}
          </div>
        </section>

        {error ? <p className="error">{error}</p> : null}

        {(result || demoCase) && verdict ? (
          <div className="results">
            <div
              className={`verdict ${verdict.found ? 'urgent' : 'clear'}`}
              role="status"
            >
              <p className="verdict-kicker">
                {demoCase ? 'Dataset reference label' : verdict.found ? 'Needs attention' : 'All clear'}
              </p>
              <h2 className="verdict-title">{verdict.headline}</h2>
              <p className="verdict-detail">{verdict.detail}</p>
            </div>

            {demoCase ? (
              <div className="case-notes">
                <article>
                  <h3>Where is it?</h3>
                  <p>{demoCase.where}</p>
                </article>
                <article>
                  <h3>The nerdy bit</h3>
                  <p>{demoCase.nerdy}</p>
                </article>
              </div>
            ) : null}

            <h3 className="panel-title">What you’re looking at</h3>
            <div className="gallery">
              <figure className="frame">
                <figcaption>The brain scan</figcaption>
                <img
                  src={demoCase ? demoCase.images.scan : b64Src(result!.image_png_base64)}
                  alt="The original brain scan"
                />
              </figure>
              <figure className="frame">
                <figcaption>{demoCase ? 'Expert reference label' : 'Where it looks odd'}</figcaption>
                <img
                  src={demoCase ? demoCase.images.label : b64Src(result!.mask_png_base64)}
                  alt={demoCase ? 'Expert dataset reference label' : 'Areas the AI thinks may be abnormal'}
                />
              </figure>
              <figure className="frame">
                <figcaption>Scan with findings marked</figcaption>
                <img
                  src={demoCase ? demoCase.images.overlay : b64Src(result!.overlay_png_base64)}
                  alt={demoCase ? 'Brain scan overlaid with the expert reference label' : 'Brain scan with possible tumor areas highlighted'}
                />
              </figure>
            </div>

            <p className="note">
              {demoCase
                ? `BraTS 2020 sample (${demoCase.source}). Colored areas show the expert dataset label, not a model prediction. Demo only — not medical advice.`
                : 'Fun demo only — not real medical advice. A clinician would still read the full study. Colored patches = “hey, look here,” not a prescription.'}
            </p>
          </div>
        ) : null}
      </section>
    </div>
  )
}
