# Pipeline Architecture

**Goal: an automated factory that generates the sprite set for a 2D game, given
a clear art direction. Humans critique the quality of what it produces.**

The division of labour is the design:

| | owns | why |
|---|---|---|
| **Factory** | generating every sprite, every direction, every frame | volume |
| **Automated tier** | spec conformance — palette, alpha, grid, projection, pivots | cheap, exhaustive, deterministic |
| **Humans** | *does it look good* | not automatable, and the entire point |

Art stops being the constraint once this works. Content becomes the constraint,
which is the intended outcome.

---

## Why generation goes through 3D

Pure 2D diffusion plus post-processing fails three requirements *structurally*:

- **Projection consistency** — models drift a few degrees per generation, and no
  post-process can re-project a 2D sprite to a corrected angle.
- **Direction coherence** — eight independent generations of "the same" chair are
  eight different chairs.
- **Temporal coherence** — at 48–64 px, one pixel of frame-to-frame jitter reads
  as noise.

All three are normally fixed by a human retouching frames. At factory volume
that is precisely the cost being eliminated, so correctness has to be
**structural** — guaranteed by construction, not corrected afterward.

The answer is the Diablo 2 / Fallout / Age of Empires 2 technique: model once,
render deterministically.

```
STAGE 1  concept art     SDXL + style LoRA          [AI]
STAGE 2  mesh            TRELLIS 2 (8GB @ 512^3)    [AI]
STAGE 3  rig             UniRig (SIGGRAPH '25)      [AI]
STAGE 4  motion          HY-Motion 1.0 / Kimodo     [AI]
STAGE 5  render          orthographic, 8 azimuths   [CODE, deterministic]
STAGE 6  pixelize        ramp-quantize + dither     [CODE, deterministic]
STAGE 7  metadata        pivot/footprint from mesh  [CODE, exact]
STAGE 8  auto-review     spec conformance           [CODE]
STAGE 9  human critique  aesthetic judgement        [HUMAN]
```

| Requirement | 2D approach | 3D intermediate |
|---|---|---|
| 2:1 dimetric projection | drifts | camera matrix, exact (verified to 12 dp) |
| 8 directions consistent | eight objects | one mesh, 8 azimuths |
| Frame-to-frame coherence | jitter | zero by construction |
| Fixed key light | violated | fixed light rig |
| Pivot / footprint | inferred | mesh bbox, exact |

---

## Stage 6 is where "looks rendered" is won or lost

Measured, not asserted. **Quantize the lighting, not the image.**

The naive chain — smooth-shade, average during downsample, snap to nearest
palette colour — fails twice. Averaging manufactures colours the palette does not
contain, and nearest-colour search has no idea what material it is shading. A
cream ceramic cup renders **blue-grey**, because its shadow side lands nearer the
violet `neutral` ramp than its own. That artifact *is* what "shrunk 3D render"
means.

Instead: bind each material to a ramp, map the lambert term to a discrete ramp
*index*, dither only between adjacent steps of that same ramp, and take the modal
rather than mean colour when downsampling.

| | naive | ramp-quantized |
|---|---|---|
| distinct colours | 17 | 10 |
| cross-ramp leak | **157 px (11.8%)** | **0** |
| cross-ramp adjacency | 6.0% | 2.7% |

Contamination is not reduced. It is impossible.

---

## Stages 8 and 9: the critique loop

The factory generates faster than anyone can look, so critique is itself a
throughput problem.

    python tools/render_batch.py                       # generate
    python tools/review_queue.py build "sprites/*.png" # auto-review + contact sheet
    # humans fill verdict + reason in review/verdicts.jsonl
    python tools/review_queue.py stats                 # what to automate next

**Stage 8** rejects spec violations before a human wastes attention on them:
palette membership, 1-bit alpha, pixel-grid alignment, ramp coherence,
silhouette, canvas bleed, plus cross-sprite checks over a whole direction set.

**Stage 9** is a contact sheet with findings already annotated. Humans judge only
what survived, and only on aesthetics.

### The loop is a ratchet

Every rejection carries a reason. Reasons that recur get promoted into stage 8,
so **human review volume falls as the factory matures**. `stats` reports which
reasons are recurring hardest, so the next check to write is never a guess:

```
judged 8/8   accepted 4   rejected 4

recurring rejection reasons (automation candidates):
    3  (75.0%)  crate top face too close in value to saucer - silhouette merges  <-- worth automating
    1  (25.0%)  cup reads flat, needs a rim highlight

4 rejected sprites passed every automated check.
  That gap is exactly what the next check should cover.
```

**This has already happened once.** The first batch rotated the camera with a
world-fixed light, so the lit face drifted around the object between directions.
Every frame was individually valid, so no per-sprite check caught it — but it was
obvious to a person scanning the contact sheet. The fix was conceptual: in an
isometric game the camera is fixed and the *object* rotates, so the key light
belongs in the camera basis. That finding is now `check_direction_set`, and it
will never need a human again.

That is the whole thesis of the factory in one example.

---

## Portability

The art direction is an **input**, not a hardcode. `style_bible.yaml` holds the
palette ramps, hue-shift rule, outline and dithering conventions, and projection.
Swapping it retargets the factory at a different game. The cozy coffee shop is
case study one, chosen because a coffee shop interior exercises wood, ceramic,
foliage, fabric and skin — most of the material range a 2D game needs.

---

## Status

| Stage | State |
|---|---|
| 1–4 (concept, mesh, rig, motion) | specified, tooling verified available, not built |
| 5 (render) | working — exact 2:1, 8 azimuths, camera-space key. **Consumes OBJ meshes** via `mesh.py`, or analytic primitives as a fixture |
| 6 (pixelize) | working — `pixelize.py`, ramp-quantized, zero contamination |
| 7 (metadata) | partial — pivot/footprint from silhouette; needs mesh bbox |
| 8 (auto-review) | working — `art_review.py`, 7 checks + direction-set |
| 9 (human critique) | working — `review_queue.py`, contact sheet + ratchet |

`isorender.py` is currently a software raytracer standing in for Blender, so the
deterministic half runs with no GPU or DCC dependency. Stages 5–9 are complete
end to end; stages 1–4 replace the placeholder scene with generated meshes.
