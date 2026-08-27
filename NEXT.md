# Next

**Both halves of "prompts and examples in, engine-usable assets out" are
done.** They landed as two separate PRs against roughly the same base, so:

- **Godot export** (PR #5, merged). `tools/export_godot.py` (stage → import
  → build, `PIPELINE.md` "Stage 10") turns `out/sprites/` + `manifest.json`
  into 22 Godot 4 `SpriteFrames` resources, one per asset, 8 direction
  frames each, world facts carried as metadata. Write-up:
  `ART_CRITIQUE.md`, "Godot export: the resource loader was the whole
  problem, and it has one fix".
- **Reference-image conditioning** (PR #6). `tools/concept.py`'s
  `concept()` takes an optional `reference` image, conditioning SDXL via
  IP-Adapter alongside the text prompt -- `--reference PATH [--ip-scale N]`
  on the CLI, `reference`/`ip_scale` fields on a `factory.py` subject spec.
  Found and fixed a real bug along the way (the IP-Adapter image encoder
  isn't covered by `enable_model_cpu_offload()`'s hooks) and swept
  `--ip-scale` rather than guessing it. Write-up: `ART_CRITIQUE.md`,
  "Reference images: one real bug, one measured knob". Proof:
  `proof/reference_image_conditioning.png`.
- **A local UI sits in front of the reference-image path** (same PR #6).
  `tools/concept_ui.py` (Gradio, `pip install gradio && python
  tools/concept_ui.py`) wraps the same `concept()`/`check_concept_fitness()`
  calls the CLI uses -- prompt box, reference upload, `ip_scale` slider --
  because the sweep found there's no single right `--ip-scale`, only a
  per-reference one, which is exactly the kind of judgement this repo puts
  in front of a human rather than automating. Verified live through a real
  browser: generated end to end, fitness gate correctly failed a genuinely
  bad multi-object generation with the same messages the CLI gives.
  Write-up: `ART_CRITIQUE.md`, "`--ip-scale` doesn't get one right answer,
  so it got a slider instead".
- **`kind`, multi-reference, and a custom prompt escape hatch** (same PR
  #6, later pass). A phone-triggered failure (SDXL collaging "Frog from
  Chrono Trigger" into ~30 tiled frogs) led to finding and fixing a real
  bug: CLIP silently truncates any prompt past 77 tokens, so a first
  anti-collage negative-prompt fix mostly wasn't reaching the model at all.
  `concept()` now checks token length itself and warns on overflow.
  `NEGATIVE` gained the three words that actually survived the ceiling;
  `kind="character"` swaps in a separate token-budget-aware
  `NEGATIVE_CHARACTER` for prompts naming a specific character (measured:
  fixes frog and a knight, reduces but doesn't fix Mario-tier fame).
  `reference`/`ip_scale` now take a list -- multiple images each load as
  their own IP-Adapter slot, blended by the UNet, not averaged in Python;
  verified live with two simultaneous references producing one coherent
  object. `concept_ui.py` gained a Prop/Character/Custom selector (custom
  exposes full positive/negative prompt override fields, for anything
  outside the isolated-single-object framing) with an example-prompt panel,
  and was re-verified live end to end after the rewrite. Write-up:
  `ART_CRITIQUE.md`, "The collage failure mode, and the 77-token ceiling
  that was already most of the way there".
- **A "Continue -> mesh + sprites" button carries the UI past stage 1**
  (same PR #6, later pass). Until now `concept_ui.py` stopped at the
  render; getting to a sprite meant dropping to the CLI. Continue calls the
  same `lift.lift()` / `ingest.ingest()` / `render_batch.py` /
  `review_queue.py build` functions `factory.py` calls for a batch, adds a
  `height` field the UI was missing, and promotes the scratch concept into
  `out/concept/<slug>.png` under `factory.py`'s own naming convention
  before running the later stages -- so a subject worked up in the UI is
  recognised as already-done if it's later added to a `subjects.yaml` under
  the same name. Verified twice: once in-process against a staged teapot
  concept, once live through a real browser click producing an actual
  8-direction pixel sprite sheet of a mug (footprint 0.125) at
  `review/sheet.png`. Write-up: `ART_CRITIQUE.md`, "The UI stopped at the
  render; a 'Continue' button now carries it to a sprite sheet".

- **UI art has a path now** (same PR #6, later pass). `tools/ui_forge.py`
  builds the fourteen `cat: ui` entries `assets.yaml` has always declared and
  never rendered — the largest declared-but-unbuilt category. Flat 2D, so it
  skips stages 2-5 entirely (an icon has no mesh and one azimuth), reusing
  `concept()`'s custom-prompt override and `pixelize`'s own functions rather
  than adding a generation path. Two real fixes came out of it: the first
  `check_icon` couldn't fail (coverage + palette-exactness only, while
  `art_review` blocked all three icons on speckle), and the quantization
  order was backwards — snap-then-modal instead of mean-then-snap took
  espresso from 13.2% isolated pixels to 1.5%. First result is honest rather
  than clean: 1 production-ready, 1 correctly gated, 1 that passes the metric
  with the wrong shape. Write-up: `ART_CRITIQUE.md`, "UI art, and the same
  wrong-check mistake made twice in one session".
  **Full-category result, and the ceiling it found:** the remaining twelve
  entries then ran as a batch — 9 of 12 past the speckle check, with
  auto-reseed doing genuine work for once (`ui_clock_day` seed 3;
  `ui_heart_mood`, `ui_icon_cappuccino`, `ui_icon_latte` seed 2), which is
  the honest counterweight to the `bread_loaf` false positive below: speckle
  really is seed-dependent, an amorphous loaf really is not. But looking at
  the rendered icons rather than their scores splits them along an axis no
  check measures: **all 7 object-depicting icons are usable (the five drinks,
  `clock_day`, `heart_mood`) and all 6 pieces of abstract UI chrome are
  wrong** — `dialogue_frame` and `ticket` render as photographed
  pictures-in-frames, `nameplate` as a framed panel, `star_rating` as an
  8-point burst, `coin` gated muddy. Three of those passed the isolated-pixel
  check comfortably; they are wrong-*shape* failures, and no metric here can
  see shape. Honest category count is **7 usable of 14 declared**, not 9 of
  12. The fix is not more seeds: nine-slice frames and banners are geometry
  with a semantic role, which belongs in `assetlib` as procedural code next
  to the furniture, where a rounded rect with a 2px border is four lines and
  exactly right every time. Same "things, not abstractions" ceiling as the
  character work, in a third costume. Write-up: `ART_CRITIQUE.md`, "Icons
  split by whether they depict a thing".
- **UI chrome is drawn now, not generated** (same PR #6, later pass).
  `tools/ui_chrome.py` is the answer to the finding above: the six chrome
  ids plus an empty star, authored as a grid of material tokens and resolved
  through the same palette ramps and the same `apply_outline` the sprites
  use. No GPU, no seed, deterministic. All seven clear `ui_forge`'s own gate
  at 32 / 64 / 128 px (worst isolated ratio 6.1% / 3.6% / 1.6% against the
  6.2% cap), so the category is now **14 usable of 15 declared** —
  `ui_icon_pastry` still gated and `ui_coin`'s generated version retired.
  The pastry was chased and deliberately not shipped: at `--retry-seeds 6`
  it passed on seed 4 with an image that is not a croissant, while seeds 2
  and 3 were recognisable croissants that failed. Deleted rather than
  counted, and the sharpest evidence yet that the stage-1 gate is a proxy.
  A background-clause remedy was measured and rejected — grey lifts the
  coverage number but gets matted *in* rather than out. `ART_CRITIQUE.md`,
  "The clearest proof yet that the stage-1 gate is a proxy".
  `tools/preview_ui.py` builds the contact sheet, labelled by producer.
  The part worth having beyond correctness is **nine-slice metadata**, which
  generation cannot produce at all: `out/ui/nine_slice.json` carries insets
  for the bubble, banner and badge, `check_nine_slice` verifies the stretch
  bands are uniform *on the resolved pixels*, and `expand()` performs the
  stretch so the numbers are exercised rather than filed. Three defects came
  out of the build and only one of them was machine-visible; write-up:
  `ART_CRITIQUE.md`, "Drawing the chrome, and three things only looking
  caught".
- **The UI has three tabs now, not one** (same PR #6, later pass).
  `concept_ui.py` reached stage 1 and, after an earlier pass, stages 2-5.
  Everything added since — `ui_chrome.py`, `tileset.py`, the widened
  `package_godot.py` — was reachable only from a terminal, which made the
  half of the library that always works the half nobody could see. So:
  *Concept → sprite* unchanged, *Drawn: chrome + tiles* running both
  procedural producers with their previews and their proofs, and *Export to
  Godot* running the stage + import + build chain and reporting the resource
  count. Both new handlers exercised directly, not just rendered: 7/7 chrome
  pieces, tiles clean including the pixel-identical manifest rebuild, and 54
  Godot resources.
- **Ground tiles and walls, with the tiling proved rather than eyeballed**
  (same PR #6, later pass). `tools/tileset.py` builds three floor types
  (plain, plank, checker; 7 variants) and four wall types (plain and
  wainscot, on each of the two visible runs), the first per-tile output
  this repo has had — `render_room.py` composites a whole shop into one
  image, which is a proof, not a level. Ground tiles are the third case for
  procedural authoring after furniture and UI chrome, and for the same
  reason: a tile's silhouette is not an artistic choice, it is the projection
  of a unit square.
  Built by inverse-projecting each screen pixel onto the ground plane through
  the repo's own `DimetricCamera` basis and testing the half-open unit
  square, so coverage is exact by construction — an affine map sends every
  point to exactly one square. That leaves one way to get it wrong and it is
  the interesting one: **the lattice step must land on whole pixels**, which
  at 2:1 means the tile width must be a multiple of 4. Checked
  (`check_lattice` rejects 50 and names the fractional step), and `--proof`
  lays a 3x3 patch and counts coverage per pixel — a seam is a pixel claimed
  zero times, an overlap one claimed twice, and both are invisible at a
  glance on a flat-toned floor while being fatal on a real one. All three
  types: every interior pixel covered exactly once.
  No outline pass, deliberately. A floor is not an object, and outlining it
  draws the dark diamond grid `assetlib.floor()` already records hitting
  twice by other means.
  **Walls cost one property floors get free.** Horizontally they tile the
  same way. Vertically they cannot: one world unit of height is
  `sqrt(6)/4 * W` pixels, irrational at every tile width, so wall tiles carry
  their full height and never stack. Stated in the manifest
  (`walls_stack: false`) rather than left to be discovered.
  Two more defects came out of the wall pass, and both were mine:
  - Tiles were being lit with a bare `dot(normal, light)` while every other
    surface in the repo goes through `mesh.rasterize`'s ambient/key/fill/
    bounce model. Invisible on a floor; on the +y wall it produced lambert
    **0** — pinned to the darkest step of every ramp, skirting board
    included. Now imported from `render_room.py`'s own call.
  - The wainscot then vanished on the shadowed wall, because `cream-2`
    already resolves to step 0 of a 5-step ramp there and no offset can
    escape downward. `check_collapse` catches this class — two materials
    resolving to one colour on one surface — and the fix was to carry the
    detail in timber rather than in tone. A detail that exists on half a
    corner is worse than a detail that does not exist.
  **The check that catches a wrong published number.** `room_corner()` places
  tiles by projecting world coordinates, which proves the picture and not the
  manifest. `check_manifest_placement` rebuilds the same scene using nothing
  but `tileset.json` and the atlas PNGs and requires it to be pixel-identical.
  Verified failable: a one-pixel error in a wall's `origin_offset` moves 753
  pixels.
  Exported: two Godot `TileSet` resources (`ground.tres`, `walls.tres`), 7
  atlas sources. Adding this fourth producer cost four lines in the stager and
  one function in `build_all.gd`, which is the test of whether the
  three-section manifest shape was right. Wall draw offsets ride as resource
  metadata rather than as `TileData.texture_origin` — the offset is verified,
  converting it into Godot's frame is a second step headless Godot cannot
  check, and publishing an unverified conversion would be worse than
  publishing the verified number and saying so.
  *(The module landed a commit early, riding along on the `ui_icon_pastry`
  commit's `git add -A`. Noted rather than rewritten, since the branch was
  already pushed.)*
- **A folder of photos is now a subject list** (same PR #6, later pass).
  `tools/scaffold_subjects.py` walks a directory and writes the
  `factory.py` YAML: name, prompt and reference filled in per image, with a
  *subdirectory* becoming one subject carrying several reference views —
  which matters because `concept.py` loads N images into N independent
  IP-Adapter slots and blends them in cross-attention, so several views
  condition better than one. `--merge` re-scans without losing heights or
  prompts already edited by hand. **Heights stay null on purpose**: a
  filename cannot tell `ingest.fit()` a mug from a table, and a plausible
  default would put a wrong number in every row where a missing one is at
  least loud — a mug scaled to a table's height reaches stage 5 and produces
  a sprite that is confidently the wrong size. `factory._load_subjects` now
  checks the whole file up front and names every offender, because learning
  about row 31 after thirty SDXL generations is the expensive way to learn
  it. The hand-written YAML is emitted rather than `yaml.dump`'d, to keep the
  one-flow-row-per-subject shape the existing lists have, and the emitter is
  verified by `safe_load` round-trip rather than reasoned about.
- **The export gap is closed — all three producers reach Godot** (same PR #6,
  later pass). `package_godot.py` read only `out/sprites/manifest.json`,
  whose shape is 8 direction frames per asset, so neither a packed animation
  sheet nor a single-frame icon fitted and neither was exported. The entry
  this replaces said the two halves wanted solving together rather than one
  at a time, and that was right: the fix both needed was for the build
  manifest to have three sections instead of one.
  - static props → `SpriteFrames`, unchanged
  - `atlas.json` characters and FX → `SpriteFrames` with one animation per
    *(clip, facing)* named `"<clip>_<dir>"`, regions cut from the packed
    sheet, at the clip's own fps. The row arithmetic is resolved in Python
    and shipped as explicit rects, because `animate.py`'s layout has been
    one row off before and that failure is invisible in every frame and
    wrong in all of them.
  - `out/ui/` → `StyleBoxTexture` for the three nine-slice pieces, with
    `AXIS_STRETCH_MODE_TILE` so the engine repeats the centre band the way
    `expand()` does rather than interpolating and inventing colours. Plain
    icons get no wrapper resource — the imported PNG already *is* the
    `Texture2D` a `Control` wants — and are load-checked instead of being
    given output for the sake of a count.
  Verified end to end against real Godot 4.3: 35 resources built (32 props +
  3 styleboxes, 11 icons load-checked), and a new round-trip step re-reads
  the written `.tres` and compares nine-slice margins against the drawn
  insets. **Confirmed failable** — swapping left and right in the resource is
  caught and named.
  The animation branch is exercised too, after `animate.py --fx` produced
  3032 frames across 9 characters and 8 effects: **52 resources** total (32
  props + 17 animation SpriteFrames + 3 styleboxes), `barista.tres` carrying
  336 AtlasTextures across 56 named `<clip>_<dir>` animations. One real bug
  on the way — `animate.py` writes to `sprites/` and the static factory
  writes to `out/sprites/`, two gitignored directories one word apart, and
  the first version of this pointed at the wrong one. Renaming either is its
  own change, so the path carries a comment instead.
  `check_anim_layout` guards the row arithmetic: a rect outside the packer's
  own declared `sheet_size`, or two clips claiming the same cell. Both
  **confirmed failable** by perturbing a resolved layout — the first reports
  the offending clip and cell, the second names both claimants.
  **Known limit, stated rather than glossed:** headless Godot has no
  renderer, so the engine's own nine-slice stretch is never rendered and
  compared. The two implementations agree by construction and by margin, not
  by a compared render; the pixels are verified only on the Python side via
  `expand()` and `preview_ui.py`.
- **`MIN_FILL` corrected, 0.12 → 0.02** (same PR #6, later pass). The
  stage-1 frame-fill floor had no bracketing recorded and was rejecting
  better work than it admitted. Its premise (fill predicts reconstruction
  quality) tested against 20 library subjects at 14-41% fill: no
  relationship — the two worst sprite sets in the library (`basket` 8/8
  blocked, `cutting_board` 7/8) are among the best-filling. Five sub-floor
  concepts forced through the full pipeline: 2.6% clean, 8.9% bad, 10.9%
  clean, 10.9% mixed, 11.9% clean. The mechanism is that
  `render_batch.frame_all()` refits the camera to the mesh, so concept fill
  never became sprite resolution. Re-gated at seed 1 under the corrected
  floor: **8 of 9 previously-gated subjects now pass, and the one still
  rejected (`bread_loaf`) is the one that genuinely renders badly.**
  Write-up: `ART_CRITIQUE.md`, "`MIN_FILL` was rejecting better work than it
  was admitting".
- **Auto-reseed on a gated concept** (same PR #6, later pass).
  `factory.py`'s `RETRY_SEEDS = 2` retries a concept that fails the stage-1
  gate on the next seed up, twice, before giving up. Measured on six of the
  nine subjects the last full batch gated: five passed, all on the first
  retry. The sixth (`wooden_spoon`) failed at every seed for a structural
  reason -- a long thin object is systematically small in frame once
  `STYLE`'s generous-margin clause is honoured -- so this is a bounded fix,
  not a general one. `--retry-seeds 0` restores the old behaviour. Write-up:
  `ART_CRITIQUE.md`, "The 29% that was being thrown away".
  **Known hazard:** reseeding optimises against the gate, and the gate is a
  proxy. `bread_loaf` gated on seed 1, passed on seed 2, and its sprites are
  still 5-of-8 blocked — identical to before. Enough retries find a concept
  that satisfies stage 1 without reconstructing better. 2 is modest enough
  not to grind far; `art_review` downstream is what actually protects the
  library. Open question worth more than any number here: should stage 1 be
  able to reject an amorphous subject on principle, rather than being talked
  round by a retry? **Investigated, answer is no on current evidence.**
  Three concept-image metrics correlated against `art_review`'s blocked-frame
  count across all 32 subjects: silhouette compactness +0.256, lightness
  spread +0.077, internal lightness gradient **+0.658**. The third is a real
  texture signal and still cannot gate — bad spans 0.0075-0.0396, good spans
  0.0030-0.0263, and every cut catching most failures also discards good
  work (0.018 → 7/10 bad caught, 2/18 good lost). Shipping it would be
  `MIN_FILL`'s error in a better disguise. Recorded as a warning-grade
  signal; any future attempt must clear the overlap table in
  `ART_CRITIQUE.md`, "Answering that question", not just a correlation.

**Not yet started**: no subject in `subjects_c1.yaml` (or any shipped
subject list) actually uses a reference image yet -- this built and
verified the capability, not a curated reference library to point it at.
`kind="character"` likewise has no subject exercising it in a shipped list.
**The full batch has not been re-run since auto-reseed landed**, so the
22/31 → ~28/31 improvement is projected from a six-subject sample, not
measured. Re-running `factory.py subjects_c1.yaml` is the way to settle it.

**The calibration backlog is untouched across all four passes, not
forgotten** — see `ART_CRITIQUE.md`'s most recent "Still open" list: counter
orientation (0.04 focal-lead cost), the focal-reading-falls-with-resolution
gap, furniture screen spread's possibly-redundant floor, and the detail
floor's 0.010-wide bracket. None of the four passes touched a generator,
check, or threshold in the sprite/room pipeline, so check these before
assuming anything moved.

---

**The list below (A1, B1, C1, C2, D1, B2) is done and written up in
`ART_CRITIQUE.md`.** One-line status:

- A1 key-light drift — diagnosed: `camera_light()` is correctly per-azimuth;
  the check's own fix message was wrong and is now corrected. Measurement
  unchanged (19/22 still fire) — a tried ramp-restriction fix broke a clean
  case and wasn't shipped.
- B1 `MAX_SOFT_ALPHA` split — built `DETACHED_SOFT_FLOOR`, bracketed on a
  19-point gap; fern/bicycle/bottle now pass, genuine defects still fail.
- C1 bind dE logging — `worst_bind_de` now in `ingest()`'s report and
  `factory.py`'s per-subject result.
- C2 `leafy_plant` RNG unification — done; flips one borderline room (plan
  1) across the detail floor as a documented, verified side effect, not a
  new bug (see gate note below).
- D1 L-run detail concentration — partial lead found (focal-box area is
  2.2x wall run's, weak -0.245 correlation with detail within L run) but a
  direct counter-example (plan 38: largest box, near-best detail) rules it
  out as a sufficient explanation. Left open, one layer deeper than before.
- B2 double-run topology — scoped correctly this time and NOT built: 8
  places in `build_plan.py` consume `plan.of("service")`/`plan.of("backbar")`,
  4 hard-coded to `[0]`. A naive build renders one lit counter and one bare
  one. Real cost is a `build_plan.py` audit, left for a dedicated pass.

Kept below as a record, not an open queue. Read `ART_CRITIQUE.md`'s final
"Still open" section before touching anything that produces art — it is a
pass-by-pass historical log, not a live tracker, but the most recent entries
are this list's source material.

---

## What a game still needs that this does not make

Asked directly -- *what is missing from an end-to-end art pipeline for a
small game* -- with the honest answer rather than the flattering one. The
list is short on purpose: things this repo could plausibly produce and does
not, not every asset any game has ever shipped.

**Closed since this question was first asked**

- ~~UI art~~ — 14 usable of 15 declared, split between a generative path for
  object icons and a procedural one for chrome.
- ~~Engine export for animations and UI~~ — all three producers now build
  Godot resources, 52 of them.
- ~~Hand-authoring a subject list per reference photo~~ —
  `scaffold_subjects.py`.

**Still missing, ranked by how much a small game would feel it**

1. **Autotile / terrain rules, and openings.** Floors and walls both ship
   (`tileset.py`, below) and a corner assembles correctly, but there is no
   terrain metadata — nothing that says which tile to place where when a
   designer paints a region, and no doorway or window opening in the wall
   set. Both are rule-and-variant work on top of geometry that is now proved,
   which is a much smaller job than the one this entry used to describe.
2. **A character portrait / dialogue bust.** The rig renders 46px-tall
   figures; a dialogue box wants a face. Different framing, different
   resolution, and probably a different producer again -- generation is
   plausible here in a way it is not for a walk cycle, since a portrait is a
   single view of a thing.
3. **Text.** No font, no bitmap glyph set, nothing that renders a word in
   the palette. Every UI mockup in this repo has ruled lines where text
   would go, including the drawn `ui_ticket`, and that is a placeholder
   rather than a style decision.
4. **Item/inventory icons beyond drinks.** The generative icon path works
   and is proven; what is missing is subjects, not machinery. This is a
   `UI_PROMPTS` list to extend, and it is item 4 rather than item 1 for
   exactly that reason.
5. **Cursors and pointer states.** Trivially procedural, genuinely required,
   and nobody has written the six lines.
6. **A palette-swap path.** One shop, several times of day or seasons, is a
   normal thing for this genre to want, and the ramps are computed rather
   than picked -- which is the hard half already done. Nothing exercises it.
7. **Rigging from a generated mesh** (UniRig) and **TRELLIS 2** — both
   blocked on this workstation's toolchain rather than on design, and both
   already recorded below.

**Deliberately not on this list**

Audio, writing, level design, and anything that is not art. Also: a
general-purpose character pipeline. Stage 2's single-view reconstruction
fuses limbs, capes and held weapons into a blob, both prompt remedies were
measured and one made it worse, and calling that a "gap" implies a fix is
scheduled. It is a ceiling, and it is recorded as one.

---

## How this repo expects work to be done

**Environment**

- Python is `.venv/Scripts/python.exe`. The system `python` on PATH has no
  numpy, no torch, no PIL. Use the venv binary explicitly for everything.
- Stages 1–2 need the GPU (RTX 4070 Laptop, 8.6 GB). Tasks below are marked
  **[GPU]** where they do.
- HF cache is at `D:\vibes\.hf-cache`. Vendored TripoSR at `vendor/TripoSR`
  (gitignored — `git clone --depth 1 https://github.com/VAST-AI-Research/TripoSR vendor/TripoSR` if missing).
- `sprites/`, `out/`, `.venv/`, `vendor/` are gitignored. Anything meant to be
  reviewed goes in `proof/`.
- `tools/factory.py subjects_c1.yaml` reproduces the 22-object lifted library
  most of these tasks measure against; it resumes (skips finished stages), so
  re-running it after `git pull` is cheap.

**Windows gotchas that have cost time before**

- Large bash heredocs mangle content. Write a patch script into the scratchpad
  and run it with the venv python, or use the Write tool.
- Background commands piped through `grep`/`tail` buffer their output. Use
  `python -u` redirected to a file.
- Foreground `sleep` is blocked. Poll with `until <check>; do sleep N; done`.
- **Check `git fetch origin main` before branching.** The last pass spent two
  extra days of work on a branch whose PR had already been merged upstream,
  because local `main` was never re-fetched. Confirm `git log main..origin/main`
  is empty before starting, not after.

**Discipline (this is not optional — it is the thing the repo is about)**

1. **Bracket every floor between a measured defect and the weakest known-good.**
   Never pick a threshold because it looks round. State the bracket width in
   the code comment; if it is thin, say so rather than widening it.
2. **Verify a new check fails in both directions.** Clean on shipped code, and
   firing when you deliberately reintroduce the defect. A check that cannot
   fail is worse than no check — it reports confidence it has not earned.
3. **Test the remedy before the check recommends it.** The speckle check
   shipped its first `fix` string with plausible, specific, untested advice.
   Three of the four remedies later measured did nothing.
4. **Record negative results.** Things that did not work are the most valuable
   half of `ART_CRITIQUE.md`.
5. **Branch and PR, never commit to the default branch — and confirm the PR
   actually merged before building on top of the branch again.**

**Gates — both must be clean before any commit**

```
.venv/Scripts/python.exe tools/manifest.py --check            # 26 checks, takes ~4 min, 1 currently fails
.venv/Scripts/python.exe tools/build_plan.py --focal-scan 12  # slower, 1 of 12 currently fails
```

Neither is clean right now, and both are the same underlying story: the
detail floor sits at exactly 0.0 with a measured 0.002-0.006 margin
(`ART_CRITIQUE.md`, "The detail floor at 40 plans"), thin enough that small,
unrelated changes flip a borderline room across it.

- `build_plan.py --focal-scan 12` fails plan 10 by -0.002 — a real,
  documented, accepted case.
- `manifest.py --check`'s `check_focal_contrast` fails plan 1 (wall run) by
  -0.002 — this one is new as of the RNG-unification pass (`ART_CRITIQUE.md`,
  "`leafy_plant` unified onto `_mix`"): a different draw from `leafy_plant`'s
  now-shared RNG stream shifted plan 1's detail reading across the same
  floor. Verified by isolating the change with `git stash`; not a bug in the
  RNG swap, a demonstration of how thin the floor's margin really is.

Don't treat a *new* failure in either run as equally acceptable without
checking whether it's one of these two known cases or something else.

Stage-8 review on generated sprites:

```
.venv/Scripts/python.exe tools/review_queue.py build "out/sprites/*_dir*.png"
```

---

## Tier A — one finding nobody has looked at yet

### A1. Key light drifts across the direction set, and it's never been triaged

`review_queue.py`'s set-level check (`tools/review_queue.py:~65-87`) measures
how much a sprite's brightest-pixel centroid moves across its 8 directions.
During A1's original smoke test — back when only 3 lifted objects existed —
it flagged teapot (8.4×12.7px spread) and basket (10.9×5.9px), and passed
kettle (3.5×4.5px). Nobody has looked at it since; it has never been run
against the 22-object library `factory.py` now produces, and the check's own
fix message names a specific, testable hypothesis: *"Anchor the light to the
camera basis, not world space — in an isometric game the camera is fixed and
the object rotates."*

- Run `review_queue.py build` against all 22 lifted objects' sprite sets and
  read the drift number for each, not just pass/fail.
- If most lifted objects fail and authored `assetlib` props don't, that
  points at something specific to the lift/render path for reconstructed
  meshes (`render_batch.py` or `mesh.py`), not a per-object fluke.
- Test the camera-basis hypothesis directly: is the key light's direction
  computed once in world space and reused across all 8 azimuths, when it
  should be recomputed per-azimuth the way `camera_light()` already does for
  the shading pass? Read `render_batch.py` and `isorender.py`'s light setup
  before assuming the fix is where the check's message guesses it is.
- **Acceptance:** a stated pass/fail count across all 22 objects, a named
  cause (not just a repeated guess), and either a fix with before/after
  drift numbers or a written argument for why the drift is acceptable.
- **[GPU not required]** — this only touches already-lifted meshes.

---

## Tier B — scoped last pass, ready to build

### B1. Split `MAX_SOFT_ALPHA` into what it's actually catching

C1 (31 subjects) found this single threshold conflating three unrelated
causes: genuine bad generations (bread_loaf, croissant — SDXL producing
overlapping ghost instances), a real segmentation failure on a clean subject
(book — low subject/background contrast), and legitimately-thin-or-
transparent subjects that are false rejections (fern, bicycle, bottle).
One scalar cap cannot separate these, and loosening it blind would let the
first class back in.

- Read the soft-alpha computation in `tools/concept.py` (`check_concept_fitness`
  or wherever `MAX_SOFT_ALPHA` is evaluated) and add a second signal: edge
  perimeter density (soft-alpha pixels per unit of silhouette boundary length,
  which should be high for fern/bicycle without the matte itself being wrong)
  or a duplicate-instance detector (connected-component count on the alpha
  channel — bread_loaf and croissant both show multiple disconnected blobs).
- Verify the new check clears fern and bicycle while still rejecting
  bread_loaf, croissant and book, per this repo's own discipline of testing
  in both directions.
- **Acceptance:** fern and bicycle pass; bread_loaf, croissant and book still
  fail; bottle's transparency case is handled explicitly (allowed, or flagged
  differently from a segmentation failure) rather than accidentally.
- **[GPU]** — needs `concept.py`'s SDXL pipeline to regenerate or re-score
  the existing 31-subject set.

### B2. Build the double-run (galley) topology

D4 scoped this and deliberately didn't build it: two parallel service runs
facing each other across the main aisle, reusing the existing run/back/queue
`Zone` triple twice instead of once. `ART_CRITIQUE.md`'s "A fifth topology"
entry has the full reasoning, including why it's the topology most likely to
stress B5's counter-orientation gap and B4's L-run-skewed detail floor (it's
the one layout where two runs face opposite directions in the same room).

- Add the branch to `floorplan.generate()` (`tools/floorplan.py:~314`)
  following the existing four branches' pattern: own clearance constants,
  own `blocked_x`/`blocked_y` for window routing, guarded early `continue`s
  on infeasible geometry.
- **Do not skip the acceptance-rate check.** The function's own docstring
  records a branch that passed 0.3% of proposals because two constraints
  didn't know about each other. Run `check_plan_range` and confirm the new
  topology's rejection rate is in the same range as the other four before
  calling it done.
- Run it through the standard 12-plan and a widened 40-plan focal scan
  alongside the other four topologies — this is the direct test of whether
  the focal/detail checks generalise or were fitted to the sample, which is
  the question D4 was originally asked to answer.
- **Acceptance:** the topology appears in `generate()`'s output at a
  reasonable rate, passes `check_plan`, and the focal/detail scan results for
  it are reported next to the other four's, not folded in silently.

---

## Tier C — small, well-scoped instrumentation

### C1. Log bind dE per subject, the same way albedo shift already is

D2's before-baseline used `delight()`'s already-logged albedo correction
(`"de-lit: albedo median L X -> 0.600"`) because it's the only per-subject
number `factory.py` currently captures. `ingest.rebind()` and
`bind_vertex_colours()` already compute a worst-vertex-colour-bind dE
(`tools/ingest.py:639`, `:669`) — it's just never surfaced past a CLI print.

- Have `factory.py`'s `run_subject()` capture that dE the same way it already
  captures the albedo-shift detail string, and write it into
  `out/factory_report.json`.
- **Acceptance:** re-running `factory.py subjects_c1.yaml --force <name>` on
  a few subjects shows a bind-dE number in the report, and the worst case
  across the 22-object library is stated — this is the second half of D2's
  before-baseline, the half that wasn't measured last pass.

### C2. Unify `leafy_plant`'s RNG with the rest of `assetlib`

D3's instrumentation found `leafy_plant` is the one generator using its own
inline LCG (`tools/assetlib.py:~989`, glibc-style constants) instead of the
shared `_mix()` every other seeded generator uses. Not a bug — all 8 of its
draws were confirmed to vary and feed real geometry — but it means the
`_mix`-wrapping instrument built for D3 can't see into it, and the next
generator copy-pasted from `leafy_plant` inherits the inconsistency.

- Replace the inline `st = (seed * 2654435761 + 1013904223) & 0x7FFFFFFF` /
  `st = (st * 1103515245 + 12345) & 0x7FFFFFFF` pair with a call to `_mix()`.
- **Acceptance:** `leafy_plant`'s output changes (a new RNG stream means new
  plants, expected and fine — confirm by eye it still looks like a plant,
  not a regression check), and re-running D3's instrumentation script shows
  it as a normal `_mix`-based generator with real draw sites.

---

## Tier D — one real lead, still open

### D1. B4's L-run concentration is unexplained

The 40-plan focal scan found L run fails the detail floor at 3 of 8 (37.5%)
against wall run's 6.7%, island's 20%, and peninsula's 0%. Two hypotheses
were chased and ruled out this pass: back-wall dressing structure (identical
between failing and passing rooms of the same topology) and shelf count
(weakly correlated in the wrong direction — more shelves track *higher* mean
detail, not lower).

- A concrete next lead: L run is the one topology whose service run turns a
  corner. Check whether the focal box (`focal_box()` in `build_plan.py`)
  is measuring detail across the corner consistently, or whether the corner
  itself dilutes the sampled region compared to a straight run.
- Compare L run's `run_len` and corner-angle distribution against its
  detail-lead readings across the existing 60-seed sample — the raw data
  from the shelf-count correlation run can be re-read for this without a new
  render pass.
- **Acceptance:** either a mechanism named and the floor adjusted with that
  as its argument, or a stated conclusion that the concentration is real but
  its cause is below this metric's resolution — matching B4's own honest
  conclusion rather than manufacturing a fix for a 0.002-wide margin.

---

## Not tasks — accepted limitations, recorded so they are not rediscovered

- **This is a prop pipeline, not a character pipeline, and the ceiling is
  stage 2.** `kind="character"` fixes the concept *image* for a named
  character; TripoSR then reconstructs it as a lumpy semi-fused blob. The
  frog knight blocks on 4 of 8 frames (11-12% isolated pixels against a
  6.2% floor) with no separable limbs or weapon. Two cheap remedies were
  measured and both failed: `--resolution 128` was a wash (still 4/8
  blocked), and simplifying the prompt to reduce occlusion made it **worse**
  (8/8 blocked, 15.3% mean) because "weapon held clear of the body" gives
  the reconstructor thin unsupported geometry, which is the thing it handles
  worst. The lever is a better reconstructor (TRELLIS 2, blocked below), not
  prompt engineering. Scope line: object-shaped things without articulation.
  See `ART_CRITIQUE.md`, "The character ceiling is stage 2, not stage 1".
- **The far side of a single-view reconstruction cannot be verified by
  machine.** The eight frames are a consistent turnaround of geometry that is
  wrong on the back, so no image-space metric over the direction set can see
  it. A silhouette-consistency check was proposed and discarded for exactly
  this reason: it cannot fail. Stage 9 exists for this. The basket's crescent
  frames (C3, prior pass) are this limitation, not a bug.
- **TRELLIS 2 and UniRig are both blocked on this machine**, not rejected.
  Both need `nvcc` and an MSVC host compiler for CUDA extensions the box
  doesn't have the toolchain for (TRELLIS: three extensions; UniRig:
  `flash_attn`, `spconv`, `torch_scatter`/`torch_cluster`). Roughly 10 GB of
  admin-level installs either way. Revisit only if someone decides to change
  the workstation.
- **Speckle has no downstream fix.** Colour-field smoothing, interpolated
  normals and supersampling at 2/4/8/12 were all measured and none moved the
  number. The downsample picks a representative sample rather than averaging,
  by design, because averaging colour is what makes cross-ramp contamination
  impossible.
- **Auto-uprighting is not a well-posed search.** Widening the pitch/roll
  search range on the same teapot found a second, deeper, differently-
  oriented optimum outside the original bounds — both are genuine flat
  surface patches, not artifacts, meaning single-view reconstructions can
  have two comparably-flat sides (the true base and an invented flat back)
  that the objective cannot distinguish. Left undone; don't re-attempt
  without a different objective, not just a wider search.
- **A style LoRA is real future work, not a task-sized item.** D2's
  before-baseline (mean 0.111, worst 0.306 of albedo L) is measured; training
  or sourcing a matched LoRA needs a curated reference set and its own
  training/eval loop, out of scope for a pass alongside anything else here.
