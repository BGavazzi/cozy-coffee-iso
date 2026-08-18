# cozy-coffee-iso

Art direction and a **review tool** for an isometric pixel-art cozy coffee shop sim.

**Art is not the binding constraint on this project — content is.** Systems,
progression, recipes, customer behaviour, economy and dialogue are what a cozy sim
lives or dies on. Art needs to be *consistent*, not *automated*, and consistency is
a review problem rather than a generation problem.

So this repo does not make art. It tells you what is wrong with art someone else
made — hand-pixelled, AI-generated, rendered, or bought.

## Use it

    pip install -r tools/requirements.txt
    python tools/art_review.py sprite.png
    python tools/art_review.py "sprites/*.png" --json

Findings are ranked and each carries a concrete fix. It is **not** pass/fail:
severity is a claim about confidence, not authority. A note may well be the right
artistic call and the tool cannot tell.

```
sprite.png
  [warning] ramp-coherence: cross-ramp adjacency is 6.0% (clean toon shading
            measures ~2.5%); ramps present: {'cream': 176, 'neutral': 157, ...}
         -> Shading appears to wander between colour families rather than staying
            on one ramp. Typical cause is matching shaded pixels to the nearest
            palette colour instead of picking a step of the surface's own ramp.
```

## What's here

- **[ASSET_SPEC.md](ASSET_SPEC.md)** — the rubric. Projection, palette, per-asset
  contract, asset manifest.
- **[PIPELINE.md](PIPELINE.md)** — what the reviewer checks and why.
- **[style_bible.yaml](style_bible.yaml)** — the single control surface. Edit this;
  the palette and the reviewer both read from it.
- **`tools/`** — reviewer, palette forge, and test fixtures.

## Art direction

Studio Ghibli colour sensibility expressed through 16-bit pixel-art constraints —
explicitly *not* the soft-rendered diffusion "Ghibli filter" look, whose gradients
and diffuse edges are exactly what a locked palette and 1-bit alpha destroy. The
precedent is SNES-era JRPG background art (Secret of Mana, Terranigma), which
already borrowed Ghibli's palette and light handling while staying inside pixel-art
limits.

The 40-colour palette is **computed in OKLab, not hand-picked**, so two properties
are checkable rather than hoped for: every pair is provably far enough apart to
survive quantization, and the warm-light / cool-shadow hue shift — the single rule
doing most of the "Ghibli" work — is a parameter that cannot be forgotten on asset
180.

    python tools/palette_forge.py    # regenerate; exits non-zero on constraint failure

Loads into Aseprite via `palette/palette.gpl`.

## Settled

- 2:1 dimetric projection, camera elevation 30 degrees (verified to 12 decimals)
- 64x32 base tile, single fixed 14x10 room, camera locked
- 40-colour locked palette, no pure black, no pure white
- One fixed key light from upper-left
