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

    python tools/render_batch.py                        # generate a direction set
    python tools/review_queue.py build "sprites/*.png"   # auto-review + contact sheet
    # fill verdict + reason in review/verdicts.jsonl
    python tools/review_queue.py stats                   # what to automate next

## The loop is a ratchet

Every human rejection carries a reason. Reasons that recur get promoted into the
automated tier, so **human review volume falls as the factory matures**. `stats`
names the next check to write rather than leaving it to guesswork.

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
- **`tools/`** — renderer, pixelizer, palette forge, reviewer, review queue

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
