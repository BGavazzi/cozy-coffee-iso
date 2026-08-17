# cozy-coffee-iso

Design and technical spec for an **isometric pixel-art cozy coffee shop sim**, plus the
asset-generation pipeline that has to feed it.

The interesting problem here isn't the game — it's that "usable sprite" is a *technical
contract*, not an aesthetic one: fixed canvas, footprint-anchored pivot, 1-bit alpha,
locked palette, one light direction, consistent 2:1 dimetric projection. Diffusion
models are natively bad at every one of those. So the architecture separates the two
concerns: **generation decides appearance, and a deterministic stage enforces spec**,
with an auto-reject gate between them.

## What's here

- **[ASSET_SPEC.md](ASSET_SPEC.md)** — the full thing:
  - Projection and palette decisions, and why 2:1 dimetric rather than true isometric
  - Complete asset manifest (~250 assets, ~130 animation frames) with frame-count math
  - Per-asset technical contract (§5) and the conformance auto-reject gate (§6)
  - An honest read on where AI generation actually helps and where it loses to doing it by hand (§7)

## Status

Spec only — no pipeline code yet. Four open decisions are listed at the end of the spec;
they're what blocks building.

## The short version, if you only read one thing

Point AI generation at the ~200 static *variations* (the 40th chair, customer outfit
recolors, texture variants), not at the ~130 animation frames. At 48–64 px, one pixel of
frame-to-frame jitter reads as noise, and no current model holds sub-pixel temporal
coherence at that scale. Animate by hand.

That makes this a **variation engine with a hard conformance gate**, not a sprite generator.
