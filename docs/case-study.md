# Case Study: Neuro

A short framing of the problem, who it is for, and why the product exists.

---

## The idea

Radiologists and oncology teams need **early, precise** reads on imaging studies — especially MRI for brain tumours — but volume is high, subtle lesions are easy to miss, and pixel-level delineation for treatment planning is slow and operator-dependent.

Neuro is a medical image analysis platform that uses deep learning to **detect and segment** pathologies (starting with brain tumours on multi-modal MRI), then expose those results through a clean API so tools and, later, a frontend can fit into real clinical and research workflows.

Tagline: **Precision that heals — faded green, focused care.**

---

## The problem

| Pain | Reality today |
|------|----------------|
| Scale | Imaging demand outpaces specialist time |
| Consistency | Manual contours vary between readers and sessions |
| Latency | Waiting on detailed segmentation delays planning |
| Coverage | Expertise is uneven across sites and overnight coverage |

Generic computer-vision demos rarely survive contact with clinical data: anisotropic volumes, multi-sequence MRI, strict evaluation (Dice, Hausdorff), and deployment constraints (GPU, privacy, auditability).

---

## Audience

**Primary**

- Research labs and clinical AI teams training / validating segmentation models on BraTS-like and institutional data
- ML engineers building reproducible medical imaging pipelines on NVIDIA hardware

**Secondary (as product surface matures)**

- Radiology / neuro-oncology collaborators who need trustworthy overlays and metrics, not notebooks
- Health-tech product teams integrating inference behind their own UX (via FastAPI)

**Not the first target**

- Unsupervised consumer use; regulated bedside deployment without institutional validation and governance

---

## Value proposition

1. **Clinical-shaped CV** — segmentation and classification tuned for medical metrics and volumetric MRI, not ImageNet defaults
2. **Research → production path** — train and evaluate with MONAI/PyTorch; serve with FastAPI; frontend later
3. **Honest scope** — start where the data and literature are strongest (e.g. BraTS-style brain MRI), then extend modality by modality

---

## Narrative arc

```
Clinical need (missed / slow lesion delineation)
        ↓
Research-grade models on public + private imaging
        ↓
Reproducible training & clinical metrics
        ↓
FastAPI inference for partners and internal tools
        ↓
Frontend for human review and workflow (upcoming)
```

---

## Success looks like

- Measurable overlap and boundary quality on held-out cases (Dice, HD95, sensitivity/specificity)
- Runs that another team can reproduce with uv and shared configs
- An API a frontend (or partner system) can call without reverse-engineering a training script
- Clear path to more modalities once the MRI segmentation loop is solid

---

## Related

- [Blog: Teaching the computer to see (so far)](blog/teaching-the-computer-to-see.md)
- [Technical Architecture](architecture.md) — models, imaging pipeline, serving
- [README](../README.md) — overview and quick start
