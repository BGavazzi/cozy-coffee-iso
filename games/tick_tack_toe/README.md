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
- Procedural fallback produced ten assets, eight directions each, using the
  same Mesh/strut primitives, fit, render_sprite, frame_all, palette and review.
  All 80 frames had zero technical blockers; contact sheet inspected. This is
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

Export checks explicit reviewed build keys, the absence of blockers, and pixel
hashes before copying. Changing generation inputs creates a new identity that
requires a new review; do not blindly update approval keys to make export pass.
`latest-build.json` refers only to the latest selected batch, not all history.

## Building the same recipe under a second style pack

`pieces.json` declares one `"style"` (`snes_rpg`) because a recipe has to say
what its prompts and traits were written against. That is not the same claim
as "this recipe can only render in that style" -- `--style` on `game_factory.py`
overrides the manifest's own field for one run, without editing the file:

```text
python tools/game_factory.py games/tick_tack_toe/pieces.json --producer procedural --style cozy_ghibli
python tools/preview_game.py out/games/tick_tack_toe/latest-build_cozy_ghibli.json --out proof/tick_tack_toe/all-pieces_cozy_ghibli.png
```

All 13 pieces (procedural producer, both parent traits, both variants) built
clean under `cozy_ghibli` with zero technical blockers, same as the existing
`snes_rpg` set -- verified by rendering both and looking at them side by side
(`proof/tick_tack_toe/all-pieces_snes_rpg.png` /
`proof/tick_tack_toe/all-pieces_cozy_ghibli.png`), not assumed from the checks
passing. This works with no change to `game_pieces.py`'s geometry because both
style packs declare the same six ramp names (`wood`, `cream`, `foliage`, `sky`,
`rose`, `neutral`) plus the same three spot colours (`lamp_glow`, `accent_read`,
`gold_coin`) -- `game_pieces.py` references those names directly rather than
through a `style.materials` role indirection the way `assetlib.py`'s cafe props
do. That is a real, load-bearing assumption, not a coincidence to leave
undocumented: a THIRD style pack that renamed or dropped any of those six ramps
or three spot colours would break every procedural piece in this file with a
`KeyError`, not a wrong colour. Migrating to role indirection is a reasonable
follow-up if or when a third style is ever on the table -- not done here, since
it is real work with no payoff against the two styles that currently exist,
and this repo's own convention is to build the thing being asked for, not the
generalization a hypothetical third case might someday want.

`latest-build.json` (no `--style` flag) always means "whatever this manifest's
own `style` field says" -- every existing command above keeps working
unchanged. Passing `--style` writes to `latest-build_<style>.json` instead, so
a style experiment never clobbers the manifest's own default build.

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
