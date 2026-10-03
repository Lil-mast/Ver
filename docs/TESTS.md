# TESTS — which scans to show

Use this when demoing **Neuro** so the audience sees both outcomes clearly.

**Files live under:**

`data/brats2020/BraTS2020_training_data/content/data/`

---

## Why most files look “fine”

Each patient is a stack of many 2D cuts through the brain.

- **Near the top or bottom** of the stack → often no tumor in the labels (empty / “all clear”).
- **Near the middle** → tumor is usually visible in the ground-truth labels.

So if you pick random early files (`slice_5`, `slice_15`, even `slice_31`), the demo will often say everything is OK. That is expected.

---

## Quick demo script (2 files)

| Step | File | What to say |
|------|------|-------------|
| 1 | `volume_1_slice_10.h5` | “Looking clear — go grab some KFC.” |
| 2 | `volume_1_slice_68.h5` | “Heads up — this one looks suspicious; get checked urgently.” |

---

## “Needs attention” — strong tumor labels

Best picks (lots of labeled tumor tissue in the mask):

| File | Notes |
|------|--------|
| **`volume_1_slice_68.h5`** | Strongest on patient 1 — **prefer this** |
| `volume_1_slice_66.h5` | Same patient, also strong |
| `volume_1_slice_70.h5` | Same patient |
| `volume_1_slice_72.h5` | Same patient |
| `volume_40_slice_56.h5` | Different patient, strong |
| `volume_37_slice_66.h5` | Different patient, strong |
| `volume_9_slice_66.h5` | Different patient, strong |

### Patient 1 — where the tumor shows up

On `volume_1`, labeled tumor is tiny until the mid-30s, then grows. Rough guide:

| Slices | What you’ll see in labels |
|--------|---------------------------|
| ~5–28 | Essentially clear (0 tumor pixels) |
| ~30–40 | Small / early tumor |
| ~50–90 | **Big, obvious tumor** — use these for demos |
| ~140+ | Often clear again |

---

## “All clear” — no tumor in labels

Good contrast files for the fun KFC line:

| File |
|------|
| `volume_1_slice_5.h5` |
| `volume_1_slice_10.h5` |
| `volume_1_slice_15.h5` |
| `volume_1_slice_20.h5` |
| `volume_1_slice_25.h5` |
| `volume_1_slice_28.h5` |
| `volume_2_slice_5.h5` |
| `volume_2_slice_10.h5` |

---

## How to run the demo

```bash
# Terminal A — API
cd /path/to/Ver
source .venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal B — UI
cd frontend
pnpm dev
```

1. Open http://localhost:5173  
2. Drop a **clear** file → expect **All clear**  
3. Drop a **tumor** file (e.g. `volume_1_slice_68.h5`) → expect **Needs attention**  
4. Point at: **The brain scan** → **Where it looks odd** → **Scan with findings marked**

---

## Important caveat

The green/red banner uses the **AI’s prediction**, not the official labels.

- The tables above describe what is in the **dataset labels** (ground truth).
- If the model still says “clear” on `volume_1_slice_68.h5`, the checkpoint is probably still the early synthetic smoke train — retrain on real BraTS for a sharper demo:

```bash
source .venv/bin/activate
python scripts/train.py --epochs 5 --max-patients 8
# then restart uvicorn
```

---

## Related

- [README](README.md) — setup and API  
- [Blog: Teaching the computer to see](docs/blog/teaching-the-computer-to-see.md)  
- [Dev log](docs/dev-log.md)
