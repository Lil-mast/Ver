import { useCallback, useEffect, useState, type DragEvent } from 'react'
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

function b64Src(b64: string) {
  return `data:image/png;base64,${b64}`
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PredictResponse | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch(`${API_BASE}/health`)
      .then(async (r) => {
        if (!r.ok) throw new Error(`API ${r.status}`)
        return r.json() as Promise<Health>
      })
      .then((h) => {
        if (!cancelled) setHealth(h)
      })
      .catch(() => {
        if (!cancelled) {
          setHealth(null)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

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
      setError('Choose a BraTS HDF5 slice (.h5 / .hdf5).')
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
        throw new Error(detail || `Predict failed (${res.status})`)
      }
      const data = (await res.json()) as PredictResponse
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed')
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
        <h1 className="brand">
          Verdant<span>Med</span>
        </h1>
        <p className="tagline">
          Precision that heals — upload a BraTS MRI slice and see the
          segmentation overlay.
        </p>
      </header>

      <div className="status-row">
        <span className="pill">
          <span className={`dot ${health?.status === 'ok' ? '' : 'bad'}`} />
          {health
            ? `API ${health.status} · ${health.device}${
                health.model_loaded ? ' · weights loaded' : ' · no checkpoint'
              }`
            : 'API unreachable — start uvicorn on :8000'}
        </span>
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
            aria-label="Upload BraTS HDF5 slice"
          />
          <div className="upload-copy">
            <strong>Drop a slice here</strong>
            <span>or click to choose volume_*_slice_*.h5</span>
          </div>
        </div>

        <div className="actions">
          <button
            type="button"
            className="btn primary-pulse"
            disabled={!file || busy || !health?.model_loaded}
            onClick={() => void runPredict()}
          >
            {busy ? 'Segmenting…' : 'Run segmentation'}
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
            Clear
          </button>
          {file ? <span className="file-name">{file.name}</span> : null}
        </div>

        {error ? <p className="error">{error}</p> : null}

        {result ? (
          <div className="results">
            <h2 className="panel-title">Result</h2>
            <div className="gallery">
              <figure className="frame">
                <figcaption>Slice</figcaption>
                <img src={b64Src(result.image_png_base64)} alt="MRI slice" />
              </figure>
              <figure className="frame">
                <figcaption>Mask</figcaption>
                <img src={b64Src(result.mask_png_base64)} alt="Predicted mask" />
              </figure>
              <figure className="frame">
                <figcaption>Overlay</figcaption>
                <img
                  src={b64Src(result.overlay_png_base64)}
                  alt="Segmentation overlay"
                />
              </figure>
            </div>
            <p className="counts">
              {Object.entries(result.class_pixel_counts).map(([cls, n]) => (
                <span key={cls}>
                  class {cls}: <strong>{n}</strong> px
                </span>
              ))}
            </p>
            <p className="note">
              Overlay quality follows the loaded checkpoint. Retrain on real
              BraTS patients for stronger masks — see the project README.
            </p>
          </div>
        ) : null}
      </section>
    </div>
  )
}
