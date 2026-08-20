# cozy-coffee-iso

An **automated factory for 2D game sprites**, driven by a clear art direction —
with humans doing the part that cannot be automated: critiquing whether the
output actually looks good.

Art stops being the constraint once this works. Content becomes the constraint,
which is the point.

## The division of labour

| | owns | why |
|---|---|---|
| **Factory** | every sprite, every direction, every frame | volume |
| **Automated review** | spec conformance | cheap, exhaustive, deterministic |
| **Humans** | *does it look good* | not automatable, and the entire point |

## Run it

    pip install -r tools/requirements.txt

    python tools/palette_forge.py        # compute + validate the 40-colour palette
    python tools/animate.py --fx         # the deliverable: sheets + atlas.json
    python tools/render_room.py          # whole-shop composite (integration test)

    # review surfaces -- what a human actually looks at
    python tools/preview_clips.py --who barista   # clip strips + looping GIFs
    python tools/preview_characters.py            # roster + 8 directions
    python tools/review_queue.py build "sprites/*.png"
    # fill verdict + reason in review/verdicts.jsonl
    python tools/review_queue.py stats            # what to automate next

    # the gates
    python tools/manifest.py --check     # budget, ramps, clips, symmetry claims
    python tools/character.py            # hair contrast, silhouette floor
    python tools/fx.py                   # loop seams

## The loop is a ratchet

Every human rejection carries a reason. Reasons that recur get promoted into the
automated tier, so **human review volume falls as the factory matures**. `stats`
names the next check to write rather than leaving it to guesswork.

Seven checks have been promoted so far: camera-space key light, hair/skin
contrast, silhouette pixel floor, seating orientation, member thickness,
grounding, and declared-symmetry verification. Three of them found bugs the
moment they were written — floating counters, back-to-front chairs, and five
wrong symmetry claims that were costing 31% of the effects budget.

This has already happened once. The first batch rotated the camera with a
world-fixed light, so the lit face drifted around the object between directions.
Every frame was individually valid — no per-sprite check could catch it — but it
was obvious to a person scanning the contact sheet. The fix was conceptual: in an
isometric game the camera is fixed and the *object* rotates, so the key light
belongs in the camera basis. That finding is now an automated check and will
never need a human again.

## Why generation goes through 3D

2D diffusion plus post-processing fails projection consistency, direction
coherence and frame-to-frame coherence *structurally*. All three are normally
fixed by a human retouching frames — exactly the cost a factory exists to remove.
So correctness is made structural instead: model once, render deterministically
across 8 azimuths. Diablo 2 and Age of Empires 2 solved it this way for the same
reason.

Projection is verified, not assumed: a ground-plane unit square measures
`0.500000000000` — exactly 2:1 dimetric.

## What's here

- **[PIPELINE.md](PIPELINE.md)** — the nine stages, what is built, what is not
- **[ASSET_SPEC.md](ASSET_SPEC.md)** — the rubric: projection, palette, per-asset contract
- **[style_bible.yaml](style_bible.yaml)** — the art direction, as an **input**.
  Swap it to retarget the factory at a different game.
- **`tools/`** — renderer, pixelizer, palette forge, rig, effects, reviewers

### Output

`animate.py` writes `sprites/`: one sheet per character (rows are directions,
clips stacked in row-blocks) plus `atlas.json` with frame rects, fps and
**per-clip anchors**. Anchors are per clip because a seated clip's contact point
is the seat and a standing clip's is the floor — one anchor for both plants every
sitting customer either in the chair or above it.

## The rig is six numbers

`character.Pose` is six limb angles, a vertical offset and a twist. That is the
whole rig, and the smallness is the design: at 46 px of figure a pose reads from
limb *direction* and body height, not from articulation — an elbow is one pixel.

Two behaviours fall out of constraints rather than being animated:

- **The walk bob is derived.** Posed figures are ground-clamped, and swinging a
  leg about its hip shortens its vertical reach, so the body drops when the legs
  spread and rides high when they close. Measured 1.0 px at room scale.
- **The foot does not rotate with the leg.** An ankle keeps it flat. Rotating it
  rigidly drove its corner into the floor, and since the figure is
  ground-clamped that lifted the body and *inverted* the bob.

## Art direction (case study one)

Studio Ghibli colour sensibility through 16-bit pixel-art constraints — expressly
*not* the soft-rendered diffusion "Ghibli filter", whose gradients and diffuse
edges are exactly what a locked palette and 1-bit alpha destroy. The precedent is
SNES-era JRPG background art, which already borrowed Ghibli's palette and light
while staying inside pixel-art limits.

The 40-colour palette is **computed in OKLab, not hand-picked**, so two properties
are provable rather than hoped for: every pair survives quantization distinctly,
and the warm-light / cool-shadow hue shift — the rule doing most of the "Ghibli"
work — is a parameter that cannot be forgotten on asset 180.

    python tools/palette_forge.py     # exits non-zero on constraint failure

Loads into Aseprite via `palette/palette.gpl`.

A coffee shop interior was chosen deliberately: it exercises wood, ceramic,
foliage, fabric and skin — most of the material range a 2D game needs.
