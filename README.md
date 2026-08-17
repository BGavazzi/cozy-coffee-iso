# cozy-coffee-iso

Design and technical spec for an **isometric pixel-art cozy coffee shop sim**, plus the
asset-generation pipeline that has to feed it.

The interesting problem here isn't the game — it's that "usable sprite" is a *technical
contract*, not an aesthetic one: fixed canvas, footprint-anchored pivot, 1-bit alpha,
locked palette, one light direction, consistent 2:1 dimetric projection. Diffusion
models are natively bad at every one of those. So the architecture separates the two
concerns: **generation decides appearance, and a deterministic stage enforces spec**,
with an auto-reject gate between them.

Two project constraints drive the design: **maximum quality (8 directions everywhere)**,
and **no human ever touches a pixel** — AI or code does all creation *and* all validation,
with humans limited to creative direction.

## What's here

- **[PIPELINE.md](PIPELINE.md)** — the architecture those constraints require, and why
  pure 2D diffusion cannot satisfy them
- **[ASSET_SPEC.md](ASSET_SPEC.md)** — projection and palette decisions, the full asset
  manifest with frame-count math, the per-asset technical contract, and the closed-loop
  conformance gate

## The short version, if you only read one thing

You cannot get 8-direction, temporally-coherent, spec-exact pixel animation out of image
diffusion plus post-processing — not without a human fixing frames. So don't. **Go through
3D and pre-render**, the way Diablo 2, Fallout, Age of Empires 2 and StarCraft did, for
exactly the same reason: when nobody can fix a pixel afterward, correctness has to be
*structural* rather than hoped for.

```
concept art (SDXL)  →  mesh (TRELLIS 2)  →  rig (UniRig)  →  motion (HY-Motion)
                    →  render (Blender, ortho, 8 azimuths)
                    →  pixelize (nearest-neighbor + palette quantize)
                    →  validate (closed loop, auto-repair, bounded retry)
```

Projection drift becomes impossible — it's a camera matrix. Eight directions become eight
azimuths of one mesh, consistent by construction. Frame jitter goes to zero. Pivots and
footprints are computed from mesh geometry rather than guessed from silhouettes.

And the economics invert: extra directions cost render time instead of authoring time, so
"all 8" stops being expensive and becomes the default.

**The honest trade:** the hard problem *moves* rather than disappearing. Geometry and
coherence get solved, but a rendered 3D scene looks rendered. Toon shading with flat ramps
and aggressive palette quantization close most of that gap — not all of it. That residual
is a creative-direction and shader-authoring problem, which is exactly where human effort
should go under these constraints.

## Status

Spec and architecture only — no code yet. Recommended first build is the deterministic
half (render → pixelize → metadata → validate) driven by a placeholder mesh, proving the
contract end to end before spending GPU time on generation.
