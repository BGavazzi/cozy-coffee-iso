# Tick Tack Toe producer adapter

This adapts the cafe factory instead of replacing it with another image service.
`pieces.json` is the game's asset input, not cafe content. Source checkout was
created separately to preserve the original dirty worktree and NEXT.md changes.

## What ran

- The original 17 open PRs' histories were consolidated through PR #64 into main
  at `4b30bbd666a1da88798e7b2f143c81e68248948a`. The native-stack records #40–#43
  were subsequently closed rather than individually marked merged; their code
  is present in that integration commit. New #65/#66 appeared after the snapshot.
- Both cafe gates were run: manifest **3 errors / 8 warnings**, focal scan
  **4/12 failures**, matching the already documented combined-stack composition
  problems. The focal scan exits 0 despite reported failures. No floor changed.
- Real SDXL + TripoSR Tick pilot completed all render stages, but was rejected:
  upright horned monster concept instead of a tick, and a speckle blocker in
  direction 7 (10.7% isolated pixels vs the existing 6.2% threshold).
- Procedural fallback produced fifteen assets, eight directions each, using the
  same Mesh/strut primitives, fit, render_sprite, frame_all, palette and review.
  All 120 frames had zero technical blockers; contact sheet inspected. This is
  agent-reviewed prototype art, **not human approval or final canonical art**.

## Commands (from this checkout)

Use the existing Python environment at `D:/vibes/cozy-coffee-iso/.venv/Scripts/python.exe`.

```text
python tools/game_factory.py games/tick_tack_toe/pieces.json --plan
python tools/game_factory.py games/tick_tack_toe/pieces.json --only tick
python tools/game_factory.py games/tick_tack_toe/pieces.json --producer procedural
python tools/preview_game.py out/games/tick_tack_toe/latest-build.json --out proof/tick_tack_toe/all-pieces.png
python tools/test_game_factory.py
python tools/export_game.py out/games/tick_tack_toe/latest-build.json --review games/tick_tack_toe/visual-review.json --out D:/vibes/tick-tack-toe/public/pieces
```

Export checks explicit reviewed build keys or an explicitly approved sprite
hash, the absence of blockers, and pixel hashes before copying. Changing
pixels requires a new review; a code-only build-key change can reuse approval
when the exact reviewed bytes are unchanged, and the exporter preserves the
existing canonical filename. Do not blindly update approval keys to make
export pass. `latest-build.json` refers only to the latest selected batch, not
all history. A successful export also writes `export-audit.json` beside the
batch, recording the build key, canonical key, pixel hash, approval basis, and
final filename for every copied asset.

`tools/promote_game_content.py` is the separate content-promotion ledger. It
does not mutate the catalog: a proposal is `promoted` only when admission,
simulation, render, blocker, and visual-review gates all pass. Blocked output
includes a stable `blocked_reasons` list containing the failed check names, so
an authoring queue can explain the next action instead of silently stalling.

## Current boundary

The procedural vocabulary is seven explicit body families plus four visible
trait modifiers. It does not invent arbitrary meshes or animations. The seed
and prompt drive SDXL; procedural body construction is deterministic from kind
and traits, not random seeded variation. The declared art-direction prose is
documentation; per-piece prompts and the actual style palette drive generation.

Build keys include recipe, palette, bible, local Python source, package versions,
and observed model-cache references. They do not pin remote model revisions or
hash every installed weight/vendor dependency. Strict archival replay remains
future work. Do not call this a complete dependency lock or an infinite factory.

Next: a bounded rule grammar and semantic recipe proposals; additional shape
families; animation; reference-conditioned generative assets that meet silhouette
requirements; selective stage-level caching instead of whole-build invalidation.
