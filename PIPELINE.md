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

**And it keeps happening.** The checks promoted since fall into two kinds, and
the second kind is the one worth naming:

*Checks that encode a rule.* Hair must clear skin in lightness; a member under
4 px reads as wire; seating faces its table; nothing floats.

*Checks that encode a **projection**.* These have no analogue in a 2D pipeline
and they are where the 3D-intermediate approach earns its cost, because the
defect only exists once geometry meets a specific camera:

| check | what it catches |
|---|---|
| `Layout.screen_occlusion` | two props several tiles apart in plan view that land on the same pixels, so the near one erases the far one |
| `check_buried_detail` | geometry that faces the camera and still never wins a pixel — detail modelled where it cannot be seen |
| `check_direction_labels` | sprite facings derived from the camera basis rather than declared, so the atlas cannot be off by a rotation |
| `measured_symmetry` | how many azimuths actually produce different sprites, which sets the render budget |

Each of these was written after a human said some version of "that area is
mush", which is not actionable, and each turned that into a specific pair of
object names and a percentage, which is.

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
| 1–3 (concept, mesh, rig) | specified, tooling verified available, not built — but **the seam they attach to is built and checked**: `ingest.py` binds an arbitrary mesh to the palette and the tile grid |
| 4 (motion) | working as a **procedural rig** — `character.py` poses, `animate.py` clips. Stands in for HY-Motion the way the rasterizer stands in for Blender |
| 5 (render) | working — exact 2:1, 8 azimuths, camera-space key. **Consumes OBJ meshes** via `mesh.py`, or analytic primitives as a fixture |
| 6 (pixelize) | working — `pixelize.py`, ramp-quantized, zero contamination |
| 7 (metadata) | working — `animate.py` emits `atlas.json`: frame rects, per-clip anchors, fps, direction order |
| 8 (auto-review) | working — `art_review.py` and friends, **20 checks**, all run by `manifest.py --check` |
| 9 (human critique) | working — `review_queue.py`, contact sheet + ratchet |

`isorender.py` is a software raytracer and `mesh.py` an orthographic rasterizer,
both standing in for Blender so the deterministic half runs with no GPU or DCC
dependency. Stages 4-9 are complete end to end.

## The seam where stages 1-3 attach

Stage 5 has always been described as consuming OBJ meshes, and that was true of
meshes this repo wrote itself, whose `usemtl` tokens are already palette
materials like `wood-2`. It was never true of anything a generator produces. A
mesh out of TRELLIS arrives with vertex colours or an MTL full of arbitrary RGB,
Y-up because almost everything upstream of a game engine is, and an arbitrary
scale and origin. Each of those is a hard stop, and none of them needs a GPU to
solve — so `ingest.py` is built and under check now, and stages 1-3 stop being
hypothetical.

**Binding is the interesting half, and it is not nearest-colour.** Everything
downstream is built on one material meaning one ramp: grain resolves by ramp,
tone offsets compose within a ramp, `check_palette_spread` counts ramps per
character. So a ramp is chosen as an *identity* — by distance to the ramp
treated as a curve through OKLab — and only then is the step chosen by
lightness. A binder free to trade lightness against hue would scatter one
object across several ramps wherever a shadow fell near a step of something
else, and hand all of the above a mesh it cannot reason about.

Three versions were wrong before that one was right, and each failed on a case
the previous one fixed:

| approach | failure |
|---|---|
| hue angle, with a chroma threshold forcing greys to `neutral` | `neutral` here is *not* achromatic — it is a cool violet-grey at chroma 0.016–0.022, so a threshold near its own chroma swallows every quiet colour. A warm off-white bound to `neutral+2` at dE 0.124 with `cream` two steps away. |
| each ramp's chroma-weighted mean (a, b) | chroma is a function of lightness. A dark brown carries a third the chroma of a mid brown, so it scored nearer pale `cream` than `wood`. |
| (a, b) at each ramp's nearest step in lightness | `cream` has no dark end, so its "nearest" step was 0.41 away in L — a ramp that cannot reach the source's lightness was competing as though it could. |

Both halves are checked, and both checks were verified to fail before being
trusted. `check_roundtrip` is exhaustive rather than sampled: every step of
every bindable ramp is a colour the palette definitely contains, so each has
exactly one right answer, and a stub binder that answers `neutral` for
everything reports 36 of 37. `check_transform` runs a library chair out to a
real OBJ and MTL — Y-up, scaled 37x, shifted off the origin, every material
renamed — and asserts it comes back grounded, centred, at the height asked for,
with its materials intact, and **not mirrored**. That last one needs its own
instrument: a reflection has the same bounds, the same height and the same
materials, so the first four assertions all pass on one. Signed volume is what
catches it, and a mirrored asset renders perfectly right up until it is a
character with a bag on the wrong shoulder in half of its directions.

## Stage 4: motion, and why the rig is six numbers

`character.Pose` carries six limb angles, a vertical offset and a twist. That is
the entire rig, and the smallness is the design rather than a shortcut: at 46 px
of figure a pose is read from limb *direction* and body height, not from joint
articulation. An elbow is one pixel. A spine chain would cost render time across
3023 frames and change nothing on screen.

Two things fall out of that constraint rather than being animated by hand:

**The walk bob is derived, not keyed.** Posed figures are ground-clamped so the
lowest vertex rests on the floor. Because swinging a leg about its hip shortens
its vertical reach, the body drops when the legs are spread and rides high when
they are together — the exact vertical rhythm a hand-animated cycle is drawn
with, for free. Measured amplitude 0.036 units, 1.0 px at room scale.

**The foot does not rotate with the leg.** An ankle keeps it flat. Rotating it
rigidly drove its rear corner into the floor, and since the figure is
ground-clamped that lifted the whole body and *inverted* the bob — mid-stride
rode higher than legs-together. After contralateral swing, that is the most
visible thing a walk cycle can get wrong.

The one clip that changes rig mid-way is `sit`. With no knee to bend, a
continuous lowering cannot be posed, so it uses the two-part shape every
low-resolution game uses: lean and drop on the standing rig, then cut to the
seated rig and settle. At 12 fps the cut is invisible.

**The mesh seam is open.** `render_batch.py --mesh asset.obj` runs the full chain
from arbitrary geometry, so stages 1-4 now have somewhere to deliver.
Rasterization is used rather than raytracing because orthographic projection is
affine, which makes a scanline z-buffer both exact and far faster. It was
cross-checked against the raytracer on the same scene tessellated: **99.40%
material agreement**, 0.7% coverage difference, mean lambert error 0.014 -- the
residual being faceted tessellation approximating analytic surfaces.

Next up is stage 2. `torch 2.11.0+cu128` with working CUDA is already present in
the ComfyUI venv and 104 GB is free on the drive; TRELLIS 2 additionally needs
`bitsandbytes` and `gguf` for 8-bit `low_memory_mode` at 512^3.
