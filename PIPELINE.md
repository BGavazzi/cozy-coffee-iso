# Pipeline Architecture — Fully Automated Asset Generation

**Operating constraints (fixed by project direction):**

1. **Maximum quality.** 8 directions everywhere. No quality traded for frame count.
2. **No human touches a pixel.** AI or code performs all creation *and* all validation.
   Humans participate only in creative direction — guiding, approving concepts, setting
   the style bible.

These two constraints rule out the pure-2D approach. What follows is what they require
instead.

---

## 1. Why 2D diffusion + post-processing cannot satisfy this

A 2D pipeline (SDXL → downsample → quantize) fails three requirements *structurally*,
not incidentally:

- **Projection consistency.** Models drift a few degrees per generation. In an isometric
  scene mismatched angles are the most visible possible defect, and there is no
  deterministic post-process that can re-project a 2D sprite to a corrected angle.
- **8-direction coherence.** Eight independently generated views of "the same" chair are
  eight different chairs. Nothing in the 2D chain ties them to one object.
- **Temporal coherence.** At 48–64 px, one pixel of frame-to-frame jitter reads as noise.
  No current image or video model holds sub-pixel coherence at that scale.

All three are normally solved by a human cleaning up frames. That option is excluded.
So correctness must become **structural** — guaranteed by construction rather than
achieved by correction.

---

## 2. The architecture: 3D intermediate, pre-rendered to sprites

This is the technique behind Diablo 2, Fallout 1/2, Age of Empires 2 and StarCraft, and
it is the correct answer here for precisely the same reason it was correct then: when
sprite output must be consistent across hundreds of assets and thousands of frames, you
model once and render deterministically.

```
┌─ HUMAN: creative direction ──────────────────────────────────────┐
│  style bible · palette · silhouette rules · concept approve/reject│
└────────────────────────┬─────────────────────────────────────────┘
                         │
   STAGE 1  concept art        SDXL + style LoRA          [AI]
   STAGE 2  mesh               TRELLIS 2                  [AI]
   STAGE 3  rig                UniRig                     [AI]
   STAGE 4  motion             HY-Motion 1.0 / Kimodo     [AI]
   STAGE 5  render             Blender headless, ortho    [CODE, deterministic]
   STAGE 6  pixelize           NN downsample + quantize   [CODE, deterministic]
   STAGE 7  metadata           from mesh geometry         [CODE, exact]
   STAGE 8  validate           closed loop + auto-repair  [CODE]
                         │
                         └──► escalate unfixable to creative direction
```

Stages 5–8 are fully deterministic. Same inputs, same bytes out.

---

## 3. What each guarantee becomes

| Requirement | 2D approach | 3D intermediate |
|---|---|---|
| 2:1 dimetric projection | Hoped for, drifts | **Camera matrix. Exact.** |
| 8 directions consistent | Eight different objects | **One mesh, 8 azimuths** |
| Frame-to-frame coherence | Jitter, needs cleanup | **Zero jitter by construction** |
| Fixed light direction | Violated constantly | **Fixed light rig** |
| Pivot / footprint | Inferred from silhouette | **Mesh world-space bbox, exact** |
| Palette | Deterministic either way | Deterministic |

---

## 4. Stage detail

### Stage 1 — Concept art `[AI, 2D]`

SDXL + style LoRA trained on the approved reference set. Produces a clean, well-lit
three-quarter concept per asset. **This is the only human gate:** creative direction
approves or rejects the *concept*. Rejection re-rolls with adjusted conditioning.

Output requirements: single subject, neutral background, even lighting, no dramatic
perspective. TRELLIS 2 reconstructs better from flat, legible input than from
atmospheric art.

### Stage 2 — Mesh `[AI]`

[TRELLIS 2](https://github.com/microsoft/TRELLIS) (Microsoft Research, 4B params,
open source, commercial-use permitted). On 8 GB: `low_memory_mode` with 8-bit
bitsandbytes quantization, 512×512 input, 512³ voxel resolution.

**Known limitation:** thin geometry (chair legs, cup handles, plant fronds) degrades at
512³. Partly hidden by the downsample to 64 px, but genuinely breaks on the thinnest
features. Renting a 24 GB GPU for this stage alone is the clean mitigation.

### Stage 3 — Rig `[AI]`

[UniRig](https://github.com/VAST-AI-Research/UniRig) (SIGGRAPH 2025, Tsinghua + Tripo).
Predicts skeleton and skinning weights across characters, animals, and organic shapes.
1–5 s inference. Static props skip this stage entirely.

### Stage 4 — Motion `[AI]`

[HY-Motion 1.0](https://hunyuanmotion.net/) (Tencent, open source, ~1B params, produces
clean looping game-character motion) or [Kimodo](https://github.com/nv-tlabs/kimodo)
(NVIDIA, SMPL-X support). Both emit SMPL-H, retargeted onto the UniRig skeleton.

Clip library to generate: `idle`, `walk`, `carry_walk`, `brew`, `wipe`, `serve`, `pour`,
`sit_down`, `sit_idle`, `sip`, `wait_impatient`, `talk`, `stand_up`, `leave`.

Loops must close exactly — first and last pose identical — enforced in validation.

### Stage 5 — Render `[CODE, deterministic]`

Blender headless (`blender -b -P render.py`).

**Camera — the exact numbers:**
- Orthographic projection.
- `RotX = 60°` → camera elevation 30° → screen-space edge slope of `arctan(1/2) = 26.57°`,
  i.e. exactly 2 pixels across per 1 pixel up. This is what makes clean pixel stair-steps.
  *(True isometric would be `RotX = 54.736°`, which gives 1:1.155 and irregular steps.
  Do not use it.)*
- `RotZ = 45° + k·45°` for `k = 0..7` → the eight directions.
- Render at an **integer multiple** of target resolution (8× — a 64×32 tile renders at
  512×256) so the downsample is an exact block average/pick.

**Shading:** NPR/toon only. Flat, banded ramps — never smooth gradients. Smooth shading
survives quantization badly and is the main reason naive 3D-to-pixel looks like shrunk
3D rather than pixel art.

**Lights:** one fixed key from screen-space upper-left (NW), plus flat fill. Identical
across every asset and every azimuth, never touched.

### Stage 6 — Pixelize `[CODE, deterministic]`

In strict order:
1. Nearest-neighbor downsample by the integer factor to native resolution.
2. Quantize to the locked palette (ordered dithering only where the style bible allows).
3. Alpha threshold to 1-bit. Hard edges, zero fringe.
4. Selective outline pass per the style bible convention.

### Stage 7 — Metadata `[CODE, exact]`

Because the source is 3D, this is computed rather than guessed:
- **Footprint** — mesh XY bounding box in world space, in tile units.
- **Pivot** — footprint center projected through the same camera matrix. Exact, and
  therefore Y-sorting is exact.
- Frame rects, animation loop points, direction index.

Emitted as JSON alongside the sheet. This stage is why the 3D path solves depth-sorting
that the 2D path could only approximate.

### Stage 8 — Validate `[CODE, closed loop]`

Not a pass/fail report — a control loop.

**Deterministically auto-repairable** (fix silently, re-verify):
palette drift · alpha fringe · canvas dimensions · off-grid detail · pivot placement ·
outline inconsistency · non-closing animation loop

**Detectable, not auto-repairable** (bounded retry with adjusted parameters, max 3):
degenerate mesh · silhouette area outside tolerance · footprint mismatch vs. declared ·
frame-to-frame delta above threshold · direction-set inconsistency

**Escalate to creative direction** (the human's sanctioned role):
anything that fails 3 retries, plus aesthetic judgement, which no validator can make.

---

## 5. Revised scope — 8 directions everywhere

Frame counts that were prohibitive in 2D become render time here.

| Set | Unique frames | × 8 dir | Notes |
|---|---|---|---|
| Barista | 46 | **368** | idle 4, walk 8, carry 8, brew 6, wipe 6, serve 4, pour 6, sit 4 |
| Customer base rig | 32 | **256** | walk 8, sit_idle 4, sip 4, wait 4, talk 4, leave 8 |
| Customers × 8 archetypes | — | **2048** | shared motion clips, swapped mesh + palette |
| Props (static) | 80 | **640** | one render per azimuth |
| Tiles | ~40 | — | procedural, no 3D needed |
| FX | ~12 loops | — | Blender particles, same render path |
| UI | ~30 | — | 2D only, no conformance constraints |

**≈ 3,400 rendered frames.** At ~2–4 s/frame that is a few hours unattended — the
correct trade when machine time replaces human time.

---

## 6. Honest assessment of the residual risk

**The hard problem moves rather than disappearing.** In 2D, consistency was hard and
hand-authored character was free. Here it is exactly inverted: geometry, projection, and
coherence are solved, but *a rendered 3D scene looks rendered*. Toon shading, flat ramps,
and aggressive palette quantization close most of the gap. They do not close all of it.

A low-denoise img2img style pass would close more — and is viable for **static props**,
where there is no temporal dimension to disturb. It must **not** be applied to animation
frames, because per-frame diffusion reintroduces exactly the jitter this architecture
exists to eliminate.

So the residual quality question is not "will assets be consistent" — they will be,
provably. It is "will they read as pixel art or as small 3D renders." That is a question
of creative direction and shader authoring, which is where human effort should go under
these constraints.

**Second risk:** 8 GB runs every stage, but sequentially and slowly, and TRELLIS 2 is at
its floor. Budget for cloud GPU on stage 2 if mesh quality becomes the binding limit.

---

## 7. Human interface

The complete human-facing control surface:

- **`style_bible.yaml`** — reference set, locked palette, outline convention, shading
  ramp definitions, silhouette rules, prop manifest, prompt templates.
- **Concept approval queue** — approve/reject stage-1 concepts.
- **Escalation queue** — assets that failed 3 retries, plus aesthetic calls.

No pixel editing. No frame fixing. Everything downstream of concept approval is machine
work, and everything from stage 5 onward is deterministic and reproducible.
