# Review Pipeline

**Scope: we give feedback on art. We do not make it.**

Art is not the binding constraint on this project — content is. Systems,
progression, recipes, customer behaviour, dialogue and economy are what a cozy
sim lives or dies on, and they are where effort should go. Art needs to be
*consistent*, not *automated*. Consistency is a review problem, and review is
cheap. Generation is expensive and was the wrong thing to build.

So the deliverable is a **critic**: something that reads a sprite made by
anyone — hand-pixelled, AI-generated, rendered, bought — and reports what is
inconsistent with the spec, where, and what to do about it.

`ASSET_SPEC.md` is therefore not a manufacturing contract. It is the rubric.

---

## What the reviewer checks

`tools/art_review.py` reads an image and emits ranked findings. It is
deliberately **not** pass/fail. Severity is a claim about *confidence*, not
authority — a note may well be the right artistic call and the tool cannot tell.

| Check | Severity | Detects |
|---|---|---|
| `alpha` | blocker | semi-transparent pixels; spec requires 1-bit |
| `grid` | blocker | art that was upscaled and is off its native pixel grid |
| `palette` | blocker / warning | off-palette colours, with the nearest legal entry named |
| `ramp-coherence` | warning / note | shading that wanders between colour families |
| `extremes` | warning | pure black or pure white |
| `silhouette` | warning / note | canvas-edge bleed, sparse or unreadable shapes |
| `light-direction` | note | highlights not sitting upper-left |

Every finding carries a concrete fix, not just a complaint.

    python tools/art_review.py sprite.png            # human-readable
    python tools/art_review.py "sprites/*.png" --json  # machine-readable

---

## The one check worth explaining

`ramp-coherence` exists because of a specific, measured failure mode.

When shading is matched to the *nearest palette colour* rather than picked from
the surface's own ramp, it wanders between colour families as the gradient
moves. A cream ceramic cup renders **blue-grey**, because its shadow side lands
nearer the violet `neutral` ramp than its own. That single artifact is what
"looks like a shrunk 3D render" actually means, and it is the most common way a
technically-valid sprite still looks wrong.

It shows up as an elevated rate of adjacent pixels belonging to different ramps:

| | clean toon shading | nearest-colour matched |
|---|---|---|
| cross-ramp adjacency | 2.7% | **6.0%** |
| ramps touched | 3 | 4 (incl. spurious `neutral`) |

**Stated limit:** from pixels alone this cannot *prove* contamination. A
deliberately grey cup and a contaminated cream one are identical bytes. The
check reports suspicion and names its evidence; the artist decides. That is the
correct division of labour for a critic.

Guidance for whoever is making the art: pick shading steps from the surface's
own ramp, dither only between adjacent steps of that same ramp, and never
downsample by averaging — averaging manufactures colours the palette does not
contain.

---

## Tooling

| Tool | Role |
|---|---|
| `tools/art_review.py` | the reviewer — the actual product |
| `tools/palette_forge.py` | generates + validates the locked palette from `style_bible.yaml` |
| `tools/oklab.py` | perceptual colour space, used by both |
| `tools/isorender.py` | test-fixture renderer; produces sample sprites to review |
| `tools/pixelize.py` | reference implementation of correct vs naive quantization |

`isorender.py` and `pixelize.py` are **fixtures and reference, not production**.
They exist so the reviewer can be tested against known-good and known-bad input,
and so the shading guidance above can be demonstrated rather than asserted.

---

## Descoped: the generation architecture

An earlier revision specified a full generation pipeline — concept art via SDXL,
mesh via TRELLIS 2, rigging via UniRig, motion via HY-Motion, deterministic
Blender render across 8 azimuths. It is recorded in this repo's history rather
than deleted, because the reasoning still holds *if* asset volume ever becomes
the bottleneck.

It is not the plan. Two reasons:

1. **Art is the lesser constraint.** Building a factory optimises the thing that
   was not limiting.
2. **It solved consistency by removing humans**, when consistency is achievable
   far more cheaply by telling humans precisely what is inconsistent.

The one durable finding from that work is the quantization result above, which
now lives on as review guidance instead of as a render stage.
