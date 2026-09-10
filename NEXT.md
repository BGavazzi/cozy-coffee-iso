# Next

## Where the open work actually is — read this first

`ART_CRITIQUE.md`'s **final "Still open" section** is the live queue. Nothing
else in this file is. At the time of writing it holds:

- **Stages 1-3** (SDXL concept -> TRELLIS 2 mesh -> UniRig rig) need a GPU and
  model weights. The seam (`ingest.py`) is built and checked; nothing feeds it.
- **Counter orientation costs the focal lead 0.04** and nothing compensates.
  Deliberately not "fixed" -- a rig boosted until the metric agreed would be a
  knob rather than a cause.
- **The focal reading falls with render resolution** in generated rooms and
  holds in the reference one. The gap is stated rather than tuned away.
- **Furniture screen spread's mean floor (0.15)** has never rejected anything
  its closest-pair floor (0.045) did not also reject -- redundancy, or a floor
  set too low to fire.
- **The detail floor's bracket is 0.010 wide** -- the tightest in the suite,
  and the first whose margin is smaller than the gap between two adjacent
  rooms.

Plus one prerequisite recorded in the status list below: the **`build_plan.py`
multi-counter audit** (5 sites hard-code `plan.of("service")[0]`), which is
what actually blocks the double-run topology.

**The Tier A/B/C/D sections far below are CLOSED and preserved only as a
record of what was once asked.** Their headings still advertise open work
("nobody has looked at it yet", "ready to build", "still open") because the
text is kept verbatim. Reading them as a backlog has already cost one pass
real effort on work finished long before. Start from the list above instead.


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
- **Landed (PR #43): `fridge_under` and `tip_jar` fixed;
  `check_generator_range`'s `GENERATORS` widened from 15 to 24 seeded
  builders, each decision measured rather than assumed.** Found in passing
  while bracketing `DEFAULT_SPREAD_FLOOR` (PR #40, `spread-floor-audit`,
  unmerged as of this branch): `assetlib.fridge_under`
  and `assetlib.tip_jar` both took a `seed` parameter and never read it in the
  body — every seed rendered the identical mesh (measured 0.0% mean, 0.0%
  closest-pair spread). Both now vary geometry the same way their file's
  other seeded generators do (`fridge_under`: handle position/length, plinth
  height; `tip_jar`: coin-fill height, jar radius, label-band height).
  `GENERATORS` covered 15 of the file's 24 seeded builders; the other 9 —
  `leafy_plant`, `succulent`, `book_stack`, `pastry_plate`, `bean_sack`,
  `wall_art_framed`, `plant_hanging`, plus the two fixed above — were each
  rendered across six independent 8-seed windows and run through the check's
  own spread math before deciding. Four (`leafy_plant`, `succulent`,
  `book_stack`, `plant_hanging`) clear both default floors with wide margin,
  added unconditionally. Five are real but small by design — `pastry_plate`
  (pastry radius only, ±3%), `bean_sack` (base radius only, ±4%),
  `fridge_under` and `tip_jar` (the fix above), `wall_art_framed` (a 4-way
  categorical hue pick whose closest pair is 0.0% in every window by the
  pigeonhole principle, not by defect) — each added with an `own` floor
  bracketed against 0.0% (what the fixed bug actually measured) rather than
  excluded outright, following `counter`'s existing exemption pattern.
  Verified failable both ways: all five `own`-gated generators, simulated
  with the exact pre-fix bug (seed pinned regardless of loop index), measured
  0.0% and were caught; the shipped, fixed code passes clean,
  `check_generator_range()` returns zero findings. `tools/manifest.py
  --check` and `tools/build_plan.py --focal-scan 12` verified byte-identical
  pass/fail against `origin/main` via `git stash`, both directions. Proof:
  `proof/generators.png`, regenerated with all 24 rows. Write-up:
  `ART_CRITIQUE.md`, "`fridge_under` and `tip_jar`: a seed parameter that did
  nothing, and nine generators put through the same measurement".

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
gap, and the detail floor's 0.010-wide bracket. None of the four passes
touched a generator, check, or threshold in the sprite/room pipeline, so
check these before assuming anything moved.

**Furniture screen spread's possibly-redundant floor is resolved** (branch
`spread-floor-audit`): not redundant, floor stays at 0.15. Write-up:
`ART_CRITIQUE.md`, "The screen-spread floor's redundancy question, closed
with a real generator instead of synthetic noise". Found along the way and
worth its own item: `assetlib.fridge_under` and `assetlib.tip_jar` both take
a `seed` and never read it inside their body — every seed renders the
identical mesh, measured 0.0% mean and 0.0% closest-pair spread. Neither is
in `art_review.GENERATORS`, so nothing currently gates it; `check_generator_range`
covers 15 of the 24 seeded builders in `assetlib.py`. Not fixed here — wiring
two generators' randomness and deciding whether to widen `GENERATORS` to the
other 9 seeded builders (`leafy_plant`, `succulent`, `book_stack`,
`pastry_plate`, `bean_sack`, `wall_art_framed`, `plant_hanging`, plus the two
above) is a separate task from the floor question this branch answered.

---

**The list below (A1, B1, C1, C2, D1) is done and written up in
`ART_CRITIQUE.md`; B2 is done too, written up in its own bullet below
instead (the `galley-multicounter` PR, not yet folded into
`ART_CRITIQUE.md`).** One-line status:

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
- B2 double-run (galley) topology — built. The audit found every `[0]` site
  named plus one the earlier scoping pass missed (`main()`'s own inlined
  copy of `focal_box`), and each needed a genuinely different fix rather
  than one "loop it" patch: `light_rig` sums pools per run and ranks dark
  corners by distance to the NEAREST run; `build()`'s whole counter-fill
  section (kit, back counter, back bar shelving, menu boards, counter-top
  clutter) moved inside a `for run_idx, run in enumerate(runs)` loop, paired
  with its own back bar by list position; `_people()` places a barista and
  a queue per run, splitting the roster instead of every queue drawing the
  same two customers. N==1 verified byte-identical first: the 12-plan focal
  scan's L/C/D readings matched the pre-refactor run to three decimals,
  topology for topology, including both documented failures, BEFORE the
  galley branch was added to `floorplan.generate()`.
  Galley's own proposal-level acceptance rate is 76.5% (17 tried, 13 kept
  over 400 seeds) — inside the other four's 56–77% range, so the branch
  isn't fighting its own constraints. Its SHARE of `generate()`'s output is
  lower (13/400, 3.2%) than the other four (14–35%), but that is its lower
  draw probability (0.22, same as island) times "first proposal to pass
  wins" starving a rarer branch of turns, not poor tuning — `check_plan_range`
  and `check_generated_plans(40)` both still read clean.
  Verification caught one real bug: kit items (espresso machine, grinder,
  register) on the mirrored far run floated with nothing underneath them.
  Every existing topology's kit placement anchors near the wall and trusts
  the mesh to extend toward the customer from there; a mirrored run's wall
  is on the opposite (high-coordinate) edge, so the same anchor pushed the
  item's bulk past the counter into open floor. Fixed with the same
  centre-and-rotate technique the counter modules already needed, anchored
  to the run's own depth midpoint instead of a wall-relative offset.
  One real, left-open finding: `focal_box` unions every service/backbar/
  service_return zone, which for a galley spans the ENTIRE room depth (both
  runs are on opposite walls) rather than a strip near one. Over the 12-plan
  scan this reads as designed on contrast (all 3 galley plans clear +0.045,
  floor +0.030) but weak on mean L (2 of 3 fail: -0.012, -0.019, sole pass
  +0.031) and weaker still on detail (3 of 3 fail: -0.019, -0.042, -0.013)
  — so all 3 galley plans miss at least one floor, a 100% fail rate over
  the topology's only 3 occurrences in the sample. Widened to a 40-plan
  scan to see if a bigger sample would soften this: it didn't — no new
  galley seed appeared in plans 13-40 (13/400 ≈ 3.2% share means ~1-2
  expected over 28 more plans, so 0 is unlucky but not alarming on its
  own), and the 3 existing galley plans reproduced their 12-plan numbers
  exactly, still 3/3 failing. The other four topologies' 40-plan fail rates
  — wall run 1/12, peninsula 1/13, island 1/6, L run 2/6 — sit in the same
  band as their known pre-existing baseline noise (e.g. plan 10's -0.011,
  corrected in this pass from a stale -0.002); galley's 3/3 is categorically
  different, a structural miss tied to focal_box's box size, not scan luck.
  This is very likely D1's box-size-vs-detail relationship, now much more
  pronounced because a galley's box is a genuine two-counter union rather
  than one wide L run — not fixed here, because loosening `MIN_FOCAL_L`/
  `MIN_FOCAL_DETAIL` to admit it would be tuning the instrument to the
  answer. `check_focal_contrast`'s `n` moved 4→5 instead, so galley enters
  the "one room per topology" suite check rather than being silently
  skipped by scan order (at seed=1 it now sorts ahead of wall run in the
  scan, which would otherwise have dropped wall run from the sample
  instead) — `manifest.py --check` now reports galley's L/detail miss
  alongside the two already-documented failures, honestly rather than
  quietly.
  Rendered and viewed both orientations: `proof/galley_room.png` (seed 8,
  horizontal) and `proof/galley_room_vertical.png` (seed 12, vertical) —
  the vertical one reads clean at a glance, both counters staffed and lit
  with seating between them; the horizontal one's far counter visibly reads
  flatter, consistent with the finding above. Neither is "one lit counter
  and one bare one" — `check_built_rooms`-equivalent checks (collisions,
  grounded, seating-faces-tables, screen occlusion) are clean across all 13
  galley seeds found in the first 400.

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
- ~~A character portrait / dialogue bust~~ — `portrait.py`, 9 of 9 roster
  characters.

**Still missing, ranked by how much a small game would feel it**

1. **Autotile / terrain rules, and openings.** Floors and walls both ship
   (`tileset.py`, below) and a corner assembles correctly, but there is no
   terrain metadata — nothing that says which tile to place where when a
   designer paints a region. ~~and no doorway or window opening in the wall
   set~~ **Done** -- `wall_window`/`wall_door`, two more entries in
   `make_wall_patterns`' returned dict, same `pattern(t, z, v) -> str`
   convention `wall_plain`/`wall_panel` already used. `wall_window`'s sill/
   head (0.58/1.82) are `assetlib.py`'s `wall_run()` numbers ported
   unchanged, safely, because both files' `z` is the same world-space wall
   height against the same `WALL_HEIGHT` -- no pixel grid to re-measure
   against. `wall_door`'s head is taller (2.05), not the window's, because
   this tile has to fit a person under it. Below and above the opening, both
   delegate straight to `wall_plain` rather than re-deriving its skirting/
   rail bands, so a window or door tile is guaranteed, not just observed, to
   join a plain wall tile with no seam. The one piece of shared machinery
   this needed: `wall_door`'s pattern returns `None` for the actual opening
   -- a real hole, not a material -- so `render_wall_tile` now treats `None`
   as "leave this pixel transparent" instead of resolving it through
   `material()`, and `check_collapse` skips it instead of either crashing or
   flagging a false collapse. Terrain metadata and the placement rules that
   would consume these variants automatically are still not started -- that
   half is the much bigger job this entry used to describe as one thing, and
   remains one.
2. ~~**A character portrait / dialogue bust.**~~ **Done** --
   `tools/portrait.py`. Reuses `character.head()`/`hair()` for shape and
   material identity (a portrait provably matches its sprite; a generated
   one could not promise that) and authors real brow/mouth/eye geometry on
   top rather than blowing up `face()`'s flat sprite-scale marks, which was
   tried first and renders a mannequin at 96px. Camera is dead-on
   (`azimuth=90`), not the sprite rig's corner view, on a bust crop
   (`chest()`) rather than the full standing figure. Four checks --
   palette-exactness, distinctness, per-eye visibility against bare skin,
   determinism -- pass on all 9 roster characters; `proof/portraits.png`.
   Found and fixed a real bug one level down along the way: `render_batch
   .render_sprite`'s outline pass assigned material ids with `hash(m) %
   251`, non-deterministic and collision-prone across a process, which
   `furnish.py`'s whole prop library was rendering through unnoticed until a
   portrait's higher material density made the wrong-colour outline pixels
   visible. One cosmetic artifact is left as a known characteristic, not
   chased further: a faceted seam where the octagonal `chest()` prism meets
   the round head, more visible on wider `bulk` values, present at some
   strength on every character.
3. ~~**Text.**~~ **Done** -- `tools/bitmap_font.py`. 90 glyphs as stroke
   skeletons rather than pixel grids, so size, weight and letterspacing are
   parameters and the letterforms are the only data. Which cap heights ship
   was measured rather than chosen: 5 collides '8' with 'S' and 6 collides
   'a' with 'o', and 'A' and '4' lose their counters at both, so the floor is
   7. Exported as `FontFile` per size, and Godot's own TextServer agrees with
   `bitmap_font.measure` on 32 of 32 string widths across four sizes. The
   `ui_ticket` ruled lines are now an option (`ruled=False`) rather than a
   fact -- and the claim they stood on, that text "would be mush at this
   size", turned out half right: a 36px writing area takes "Latte" at cap 9
   and takes "Flat White" at no shipping size at all.
4. **Item/inventory icons beyond drinks.** Six subjects added to
   `UI_PROMPTS` -- `ui_icon_muffin`, `ui_icon_cookie`, `ui_icon_bagel`,
   `ui_icon_sandwich`, `ui_icon_milk`, `ui_icon_beans` -- and the honest
   count is 2 of 6, not 6 of 6. `ui_icon_milk` and `ui_icon_beans` clear the
   speckle gate cleanly in both styles. The other four do not, in either
   style, after four rounds of wording aimed at the specific cause each
   round's renders showed: a bagel that kept rendering as a glazed,
   sprinkled donut regardless of "no glaze, no icing"; a chocolate chip
   cookie whose chip count SDXL will not take a number for, so it never
   quantizes flat; a muffin whose fluted wrapper and blueberry drip streaks
   survive every "no paper liner" instruction; a sandwich that stacked
   itself into a two-layer club sandwich until "single layer, not stacked"
   fixed the shape but not the speckle. See `proof/ui_icons_subjects.png`,
   built and read by eye, not by gate score alone -- one snes_rpg pass
   (`ui_icon_milk` seed 1) was a shelf of a dozen bottles, not one, and
   another (`ui_icon_cookie` seed 2) was two cookies on a plate; both
   cleared `MAX_ISOLATED` on pixel count and were rejected anyway, then
   re-seeded to genuine single-subject passes. Recorded rather than
   loosened: same standard the `dialogue_frame`/`nameplate` wrong-shape
   finding set above (see this file's UI-art log). The ceiling here is
   texture density, not shape complexity --
   embedded chips, berries, seeds and layered fillings exceed the
   modal-downsample speckle budget in a way a single-region cup, bottle or
   bag does not. `UI_PROMPTS` stays open; six more lines does not close
   this entry.
5. ~~**Cursors and pointer states.**~~ **Done** -- `ui_chrome.py` gains
   three: `ui_cursor_pointer` (a standard 7-point arrow, not an original
   design -- unlike `star_rating`/`coin`, a cursor is a shape every player
   already knows, so inventing one would cost recognisability for nothing),
   `ui_cursor_hand` (a fist with an extended index finger and a thumb, for
   clickable targets), `ui_cursor_wait` (an hourglass, static rather than
   animated, since one frame is what this pipeline ships). All three are
   smaller than every other chrome piece (32px against 64) and two are
   genuinely concave, which made `_star`'s own border-inset trick fail
   worse than before it was fixed: shrinking a polygon's vertices toward a
   shared point self-intersects at concave corners instead of insetting
   uniformly, and measured 10-13% isolated pixels against the 6.2% cap.
   `_inset_mask` replaces it with erosion on a rasterized mask, which
   cannot self-intersect, and clears the cap on all three (5.4% / 1.5% /
   6.0% worst-case). The six lines took longer than six lines.
6. ~~**A palette-swap path.**~~ **Done.** `palette_swap.py`, four variants in
   `style_bible.yaml`, `proof/variants.png`. Two things worth carrying
   forward. First, the swap is a lookup and not a re-quantization, which is
   only possible because the library measured exactly 40 colours with none
   off-palette -- that measurement is the feature's foundation, so
   `--check` re-takes it rather than trusting it. Second, the first set of
   variants was swept to maximise each variant's own internal `min_delta_e`,
   which is the wrong objective: a variant is never quantized against, so the
   sweep was climbing a phantom constraint, and it converged `evening` and
   `night` to 0.0057 apart -- one palette shipped twice. `check_separation`
   now gates the distance BETWEEN shipped palettes, and the proof sheet is
   what made the collapse visible in the first place.
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

## Style packs: generalizing beyond one art direction (in progress)

This whole pipeline was written against one art direction -- `style_bible.yaml`'s
Ghibli-through-pixel-constraints look. The ask now is a second, SNES-JRPG-flavoured
one, built as a real generalization rather than a reskin: procedural wherever
possible, reusable across future styles and games, not hardcoded to the coffee
shop. Two research passes mapped the actual coupling first, and it was narrower
than "rewrite everything": the palette forge is already data-driven from YAML,
and the SDXL prop-prompt stage carries no style language at all -- style is
applied entirely downstream, in the deterministic shading stage. The real
blocker is `character.py`'s rig, built only from `add_box`/`add_prism` (flat,
faceted, blocky) with proportions partly named and partly inlined as magic
numbers -- and the encouraging find there: `add_cylinder`/`add_sphere` already
exist and are already load-bearing throughout `assetlib.py` (cups, teapots) and
`fx.py` (steam, droplets). An organic-reading character rig does not need new
primitive code, it needs `character.py` rewritten to use primitives the
codebase already trusts elsewhere.

**Landed (PR #12): the style-pack data model and the safe half of the plumbing.**
`tools/style.py` loads a "style pack" -- one `bible.yaml` extending today's
schema with three new top-level keys: `materials:` (semantic role -> material
token, replacing `assetlib.py`'s hardcoded WOOD/CERAMIC/GLASS/... constants),
`rig:` (character proportions + primitive vocabulary + target resolution,
recorded from `character.py`'s own constants), `checks:` (per-style overrides
for today's hardcoded numeric floors, empty until a style has real renders to
measure against). `cozy_ghibli` is the existing root `style_bible.yaml` --
unmoved, so every unflagged script call resolves to exactly the path and
output it already did; the migration is additive-only, verified byte-identical
end to end (`palette_forge.py`, `character.py`, `portrait.py --check`,
`palette_swap.py --check`'s full 755-PNG round-trip). Two real, small,
independently-safe code changes rode along: `palette_forge.validate()`'s
warm/cool hue-bend rule is now an opt-out (`require_warm_cool_shift: false`) --
it's this style's defining choice, not a property every style must share --
and `pixelize.apply_outline()` gained `enabled`/`colour_step` parameters,
defaulting to today's exact behaviour, for a style whose look leans on internal
value contrast instead of a drawn line.

**Deliberately not landed yet, and why:** `assetlib.py`'s material constants
and `character.py`'s rig constants are recorded as data in `materials:`/`rig:`
now, but neither module reads them yet. The reason is a real constraint found
mid-implementation, not an oversight: both modules use these as function
*default arguments* (`def table(top=WOOD, ...)`), which Python binds once at
`def` time -- at module import, before any `--style` flag has been parsed. Making
them genuinely switchable needs either an early args-peek (resolve `--style`
before the module that consumes it is imported) or converting every default to
a lazy per-call lookup, and that is real, separate work across every entry-point
script's import order, not a data change. Slated as the next slice, along with
the SNES-flavoured palette + rendering pack itself, the organic cylinder/sphere
character rig (the biggest lump of new authored geometry, comparable in effort
to the portrait producer -- needs visual iteration, not just a refactor), and
check-threshold overrides written once that rig's real renders exist to measure
against.

**Scoping call, flagged rather than pre-decided:** "SNES RPG" here means the
*aesthetic* -- saturated, fewer shading bands, bold or minimal outlines, rounder
low-poly silhouettes -- not literal hardware constraints (15-colour-per-sprite
subpalettes, a fixed master palette). Hardware-accurate palette partitioning is
a large side quest with little visual payoff on a modern rendering target.

**Landed (PR #13, stacked on #12): the gate catalog.** The wider objective
behind this whole initiative, stated directly: taste is the one thing a
machine can't be handed, so everything else is a matter of defining the right
gate for the problem. This repo already had 62 of them -- `check_*` functions
built one hard-won defect at a time, scattered across twenty files with no
shared vocabulary. `tools/gates.py` catalogs all 62 (sourced from each
check's own docstring via an AST scan, not hand-paraphrased, so it can't
drift into misdescribing one), classified into the three kinds a real review
applies in order: `deterministic` (all 62 existing checks), `llm` (a vision
model asked to judge what no numeric floor captures well -- real category,
honestly empty; the focal-contrast/composition family is named as the
strongest candidate, since `ART_CRITIQUE.md` records a multi-pass history of
that exact check being re-derived because it approximates a judgment call
with an ever-more-specific proxy, but wiring an actual model is a deliberate
decision left for later, not a data change), and `taste` (the human opening
the proof sheet -- every feature this repo has shipped waited on this,
written down as a gate or not).

**Landed (PR #14, stacked on #13): provenance and staleness.** `tools/
lockfile.py` answers approval chaining and precedence flagging directly: an
approval is only true of one (output, upstream version) pair, and nothing
before this noticed when that pair changed. One `lock.json` per style pack
(beside its `bible.yaml`), keyed `producer:scope`, records which gates were
checked and a content hash of the bible at that moment -- no version number
to remember to bump, the bible's own bytes are the version. `portrait.py
--check --lock` is the first real producer wired to it, cross-referencing
`gates.py`'s own catalog for the gate names rather than typing them by hand.
Demonstrated end to end, not just unit-tested: recorded the real roster as
approved, edited `style_bible.yaml`, confirmed `lockfile.py --status` flips
that same entry to `STALE` and exits non-zero, reverted the edit, confirmed
it flips back. `lock.json` is committed -- the point is a persistent,
shared record, not a local scratch file.

**Landed (PR #15, stacked on #14): the `llm` gate kind, made real rather
than left as an empty category.** No external API is wired, deliberately --
`tools/llm_gate.py`'s own docstring makes the case: the agent operating this
repo already IS a vision-capable LLM, in the loop for every judgment call
this pipeline has ever needed a human for, so routing that same judgment
through a `Rubric`/`Verdict` contract costs nothing, commits to no vendor,
and needs no credential to manage. A future automated backend (an actual API
call, for judging at a volume no interactive session could keep up with) is
a real, separate cost/vendor decision this file does not make. Demonstrated
for real against `proof/shop_big.png` -- this repo's own "the reference room
is still the better room" -- applying the first rubric (`focal_hierarchy`,
the composition-judgment family `gates.py` named as the strongest llm-gate
candidate): PASS, with real reasoning (the espresso machine's cool-grey break
against the warm palette, reinforced by the chalkboard signage above it),
recorded into the SAME `lock.json` a deterministic `--lock` call writes, so
staleness tracking covers both kinds identically -- verified a rejected
verdict is stored but never flagged stale, since it was never approved in
the first place.

**Landed (PR #16, stacked on #15): two more real producers wired to
`--lock`.** `character.py` and `palette_forge.py` each gained the same
opt-in flag `portrait.py` did. `character.py --lock` records exactly the
four checks its own `__main__` already ran (`check_contrast`,
`check_palette_spread`, `check_waistline`, `check_direction_stability`) --
honestly a subset of the nine `gates.py` catalogs for it, not silently
expanded to all nine, since that would be a behaviour change past what was
asked. `palette_forge.py --lock` records `validate` + `check_separation`,
its real gate logic, even though `validate` doesn't match the `check_*`
naming convention `gates.py`'s catalog scans for -- recorded under its real
name rather than skipped for not fitting the pattern. Both verified
byte-identical to their pre-`--lock` output when the flag is omitted.
`lock.json` now carries four real, independently-recorded entries:
`portrait.py:roster`, `character.py:roster`, `palette_forge.py:
palette+variants`, `render_room.py:proof/shop_big.png`.

**Landed (PR #17, stacked on #16): the "one of each class, approved, placed
in engine" gate, made checkable.** `cozy_ghibli` already satisfies this in
practice -- `render_room.py`'s whole-shop composite and `export_godot.py`'s
export happen to cover every class this game needs -- but nothing made that
an explicit, re-checkable requirement before now. `tools/style_approve.py`
computes it entirely from `lock.json`: a style is APPROVED when it has an
approved, current character-roster entry (`character.py` and/or
`portrait.py`), an approved, current `palette_forge.py` entry, and at least
one approved, current `llm:focal_hierarchy` verdict -- the actual "does this
read as one coherent world" question. Deliberately not "every gate passes":
most of `gates.py`'s 62 are per-producer regression checks, not questions
about whether a STYLE holds together as a whole. `cozy_ghibli` passes today
on the entries #14-#16 already recorded. Demonstrated the negative case the
same way `lockfile.py`'s staleness was demonstrated: edited `style_bible
.yaml`, confirmed all three requirements correctly flip to failing (not just
one), reverted, confirmed APPROVED again. This is the gate a second style
pack (the SNES-flavoured one, or any future one) will have to clear before
it's safe to generate a real asset library against.

**Landed (PR #18, stacked on #17): the first real second style pack --
`styles/snes_rpg/bible.yaml`, palette only.** Same computed-not-picked
machinery as `cozy_ghibli` (`palette_forge.py` needed zero code changes,
confirming the earlier research finding that it's genuinely style-agnostic)
-- only new numbers. Targets 16-bit JRPG character/monster sprite work
specifically (Chrono Trigger, Secret of Evermore), not that era's more
Ghibli-adjacent background painting: fewer, harder-countable shading bands
(4-5 steps per ramp instead of `cozy_ghibli`'s 5-7), far less aggressive
chroma falloff (0.10 vs 0.26, so saturation holds toward both ends of a
ramp instead of washing to pastel), hue held close to constant per ramp
rather than painterly warm/cool-shifted (`cool_amount`/`warm_amount` at
0.05 vs `cozy_ghibli`'s ~0.22-0.24), and `require_warm_cool_shift: false`
in its own constraints -- an explicit opt-out of the one hard-coded rule in
`palette_forge.validate()`, not a failure to meet it. One real collision
found and fixed the same way `cozy_ghibli`'s own history recorded similar
ones: `accent_read` at hue 8 landed 0.0121 apart from `rose`'s own mid-ramp
(hue 6, similar lightness) against a 0.035 floor -- pushed to hue 30
(orange) to separate. Visually reviewed against the rendered swatch sheet
(`styles/snes_rpg/palette/palette.png`, committed) before being called
done, same as every palette this repo has shipped. Character rig, materials
and check-threshold wiring for this style are separate, not-yet-started
work -- `style_approve.py --style snes_rpg` correctly reports NOT approved
until they exist, which is the gate working as designed, not a bug.

**Landed (PR #19, stacked on #18): the organic cylinder/sphere character
rig, built and rendered for real.** `tools/organic_rig.py` -- a new,
self-contained producer, not a `character.py` rewrite (same relationship
`portrait.py` has to `character.py`), because it sidesteps the import-order
problem entirely: it reads `styles/<name>/bible.yaml`'s `rig:` block
directly through `tools/style.py` rather than through module-level default
arguments bound at `def` time.

Building it surfaced a real correction, not just new geometry: the earlier
`rig:` schema carried over `torso_rx`/`torso_ry`-style independent radii
from the prism rig, but `add_cylinder`/`add_sphere` (`tools/mesh.py`) only
take ONE radius -- a true circle. That is strictly better for the exact
property the prism rewrite exists for: `add_prism`'s own docstring measures
a box at 53% silhouette swing between face-on and corner-on views and an
octagon at ~8%, while a true circle's projected width is identical at every
azimuth by construction. `styles/snes_rpg/bible.yaml`'s `rig:` block was
corrected to `torso_radius`/`head_radius`/`leg_radius`/`arm_radius` (single
values) to match. `check_direction_stability` in `organic_rig.py` measures
this claim directly rather than asserting it -- both rigs' silhouette swing
across the same 8 azimuths, organic against `character.BARISTA`'s own prism
swing -- and the organic rig wins on the numbers, not just by construction.

Scoped to a static standing figure (legs, torso, arms, head, minimal face,
one hair cap) through the "upright, unposed" case only -- explicitly not
the 15-clip pose system, seated/perched legs, or `character.hair`'s six
styles. Each of those is a real, separate authoring pass the same size as
this one; porting all of them at once would be an unreviewed batch, which
is exactly what this repo's own process argues against.

One real visual bug found by rendering and looking, same as everywhere else
in this repo: the first hair sphere (1.08x head radius, offset 0.28 head
radii up) was large enough to swallow nearly the entire head from every
camera angle, reading as a grey metal helmet rather than hair -- worse, its
material (`neutral+1`, a cool blue-grey ramp meant for metal surfaces) made
it look even more like armor. Fixed by shrinking to 0.86x radius at a
smaller +0.16 offset (crown-and-back coverage, face left clear) and
switching to `wood-3` (dark brown, off the same ramp `SKIN` reads from,
consistent with how the existing roster's own hair materials work). Visually
confirmed at azimuth 90 -- eyes and blush read clearly, matching
`portrait.py`'s own finding that a dead-on camera is what facial detail
actually needs. Proof sheet: `proof/organic_rig.png`, all 8 azimuths, looked
at before being called done.

`style_approve.py`'s `REQUIRED_PRODUCERS_ANY_OF` gained `organic_rig.py`:
for a `primitive: cylinder_sphere` style, it is the only one of the three
character producers that builds that style's own declared geometry today,
so requiring only `character.py`/`portrait.py` would make such a style
permanently unapprovable on a technicality unrelated to whether its
characters read correctly. With this plus a real `palette_forge.py --style
snes_rpg --lock` entry, `style_approve.py --style snes_rpg` is down to one
remaining reason (no `llm:focal_hierarchy` verdict) -- which correctly
requires a real composed scene, itself blocked on `furnish.py`/
`render_room.py` being wired to this style, still separate, not-yet-started
work.

**Landed (PR #20, stacked on #19): `snes_rpg` reaches APPROVED for real --
and the deferred `assetlib.py` import-order blocker turns out mostly not to
be one.** Three findings, in the order they happened:

1. Rendering an existing `assetlib.py` prop (`table()`) under `snes_rpg`'s
   palette with ZERO code changes -- just passing `load_palette(style.
   palette_path)` -- produced a correctly-styled result. The reason: `WOOD`,
   `CERAMIC`, etc. are semantic role names (`"wood"`, `"cream"`, ...), and
   both real style packs' `materials:` blocks happen to map every role to
   the SAME ramp name (`wood -> wood`, `ceramic -> cream`, ...) -- only the
   ramp's own colours differ per style, which is exactly the axis
   `load_palette` already varies. The import-order problem this file
   flagged three times over is real in the abstract (a style that wanted to
   remap a role to a DIFFERENT ramp name would hit it, because those
   constants really are bound as function defaults at `def` time), but no
   style that exists today needs that, so it was blocking nothing real.
   Confirmed on five more props spanning wood, fabric, foliage and ceramic
   materials (`table_4top`, `chair_wood`, `armchair`, `plant_monstera`,
   `cup_espresso`) side by side against `cozy_ghibli` -- all five read
   correctly, distinctly punchier and more saturated, with no cross-ramp
   bleeding. This closes most of what NEXT.md previously called "separate,
   real geometry-authoring work" down to a much smaller and already-landed
   change (below).

2. `furnish.py` and `render_room.py` gained `--style` (default
   `cozy_ghibli`, exact prior behaviour when omitted -- verified: the
   default-path room render reproduces `ART_CRITIQUE.md`'s own recorded
   focal-contrast figure, `+0.133`, exactly). Both were genuinely small,
   mechanical changes -- swap a hardcoded `load_palette()` for
   `load_palette(style.palette_path)`, default `--out` to a style-named
   subpath so a non-default render can't silently overwrite the shipped
   proof image. `render_room.py --style snes_rpg` produced a full composed
   room, `proof/shop_snes_rpg.png` -- same layout as the shipped
   `proof/shop.png`, same characters (still the box/prism rig; `character.py`
   itself is the one real remaining piece that needs the rig: block wired
   in, see above), completely re-shaded. Focal contrast measured HIGHER
   under this palette than the original, `+0.166` vs `+0.133` -- snes_rpg's
   higher chroma and harder value steps sharpen the counter-vs-field
   separation rather than softening it, not just a different-looking room
   but a stronger one by this repo's own composition metric.

3. Judged `proof/shop_snes_rpg.png` against the `focal_hierarchy` rubric
   honestly (PASS -- reasoning in `styles/snes_rpg/lock.json`) and recorded
   it with `--style snes_rpg` (missing that flag the first time silently
   recorded the verdict into `cozy_ghibli`'s own `lock.json` instead --
   caught by re-running `style_approve.py --style snes_rpg` and seeing it
   still fail, removed the misfiled entry, re-recorded correctly).

`python tools/style_approve.py --style snes_rpg` now reports **APPROVED** --
the first style pack other than `cozy_ghibli` to clear the "one of each
class, approved, placed in engine" bar this repo set for itself. What's
still real, separate, not-yet-started work: `character.py` itself does not
yet build `snes_rpg`'s declared cylinder/sphere rig (the room above uses the
existing prism customers, correctly re-shaded, not `organic_rig.py`'s
figures merged into a scene); and `character.hair`'s six styles have no
organic-rig equivalent yet.

**Landed (PR #21, stacked on #20): `build_plan.py`'s curated floor plan
gained the same `--style` wiring.** Same small, mechanical pattern as
`furnish.py`/`render_room.py` -- a `--style` flag, `ramps` threaded through
to the shared `render_room.render()` call, `--out` defaulting to a
style-suffixed path. `build_plan.py --style snes_rpg` -> `proof/
plan_room_snes_rpg.png`, a second, independently-generated composed scene
(different layout topology than `render_room.py`'s own `build_room()`) --
worth having because this is the actual producer `proof/shop_big.png`,
the ORIGINAL `focal_hierarchy` verdict's scope, came from.

Judged and recorded honestly: PASS, but the weaker of the two `snes_rpg`
scenes so far (`+0.078` focal contrast vs the other scene's `+0.166`) --
this layout's counter is a long, thin run rather than a compact cluster,
and the magenta cushioned chairs scattered through the seating area compete
with it more than the first scene's plants did. Recorded anyway, as
additional real evidence rather than cherry-picking the stronger result --
`style_approve.py` only needs one passing verdict to grant APPROVED, and it
already had one; this is a second, independent data point, and an honest
weaker-but-still-passing one is more useful than a hidden failed attempt
would have been.

**Landed (PR #22, stacked on #21): three more `organic_rig.py` hairstyles --
`long`, `bun`, `cap` -- alongside the existing `short`.** `bob` and `curly`
are still not here: both rely on a partial (non-360deg) ring in the
box/prism original, which `add_cylinder`/`add_sphere` cannot express without
new primitive code, a real, separate job rather than something to fake.

Two rendering mistakes found by looking, not assumed away, the same
discipline `short`'s own fix (PR #19) established:

- The demo's hairstyle row was first rendered at azimuth 90 (face-on) --
  the one azimuth that CANNOT show `long`/`bun`, because both are placed
  behind the head (negative y) specifically so they clear the face. Every
  style looked identical to `short` until the row was moved to azimuth 225
  (a back-left corner view), which is where the geometry actually lives.
- Even at the right azimuth, the first `long`/`bun` placements were too
  close to the crown sphere to read as separate shapes -- `long`'s cylinder
  barely poked past the head sphere's own silhouette (offset -0.65 head_r,
  when the sphere's own back edge is already at -1.0 head_r at crown
  height), and `bun`'s sphere mostly overlapped the cap rather than
  protruding from it. Both pushed further out and, for `bun`, shrunk --
  `bun` specifically needed to be SMALLER and further out to read as a
  distinct knot rather than a thicker cap.

`cap` needed no correction: a short wide cylinder (brim) plus a smaller one
(crown) is the one style a cylinder is the obviously correct primitive for,
not a stand-in for a box, and it read correctly on the first render.

`organic_rig.py --demo` now shows two rows: the existing 8-azimuth
silhouette-swing sheet, and a new one comparing all four hairstyles side by
side at azimuth 225.

**Landed (PR #23, stacked on #22): a real correctness bug in `character.py
--style`, fixed, plus the negative result it uncovered, recorded honestly.**
`character.py`'s `main()` accepted `--style` since PR #16 but only used it
to pick which style's `lock.json` got the recorded result -- the roster's
own material checks (`check_contrast`, `check_waistline`) always loaded
`load_palette()` with no argument, i.e. always `cozy_ghibli`'s palette,
regardless of `--style`. `character.py --check --style snes_rpg` therefore
always passed, because it never actually measured `snes_rpg`'s colours --
a check that cannot fail for the thing it claims to certify, which this
file's own discipline rule (below) says is worse than no check. Fixed:
`ramps = load_palette(load_style(args.style).palette_path)`.

Running it for real immediately found a genuine, measured failure:
`character.CUSTOMERS`'s hardcoded material choices -- written and tuned
against `cozy_ghibli`'s palette -- do NOT all clear `character.py`'s own
contrast/waistline floors under `snes_rpg`'s punchier, more compressed
lightness distribution. Four blockers: `elder`'s hair sits 0.088 from skin
(needs 0.13), and `reader`/`regular`/`writer` each have a shirt/trousers
pair too close in value for a waistline to read (0.022/0.040/0.080 against
an 0.085 floor).

Not fixed, and deliberately not: neither the roster's material choices nor
the check floors. Lowering the floor to make the failures disappear would
defeat the check's own purpose -- insufficient contrast is a real visual
defect regardless of which style is being validated, and this file's own
discipline rule 1 says never pick a threshold because it makes a problem go
away. Editing the roster's colours to satisfy `snes_rpg` risks quietly
breaking `cozy_ghibli`'s own currently-clean pass, for a spec list that
isn't even the geometry that ships for `snes_rpg` in the first place --
`character.CUSTOMERS` is `character.py`'s own box/prism roster,
`organic_rig.py` is what actually ships for a `cylinder_sphere` style. The
honest conclusion, recorded rather than hidden (`styles/snes_rpg/
lock.json`, `character.py:roster` entry, `approved: false`): this specific
roster is cozy_ghibli-specific, and that's fine, because `style_approve.py`
already derives `snes_rpg`'s character-roster evidence from
`organic_rig.py` instead -- confirmed unaffected, still APPROVED. This is
exactly why `REQUIRED_PRODUCERS_ANY_OF` is an "any of" set rather than
requiring `character.py` specifically.

**Landed (PR #24, stacked on #23): the same `--style`-ignored-by-the-actual-
check bug, found and fixed in `portrait.py` and `manifest.py` too.** Having
just found it once in `character.py`, checked every other producer
accepting `--style` for the same pattern rather than assuming it was
isolated. It was not: `portrait.py`'s `check()`/`build()`/`demo()` and
`manifest.py`'s `check()` all hardcoded `load_palette()` with no argument
in one or more places, so `--style snes_rpg` picked which `lock.json` a
result went into without ever measuring `snes_rpg`'s actual colours.

Both fixed the same way -- `ramps` resolved once from the active style and
threaded through every call site (`check`/`build`/`demo` in `portrait.py`
each gained a `ramps=None` parameter; `manifest.py`'s `check()` resolves
`ramps` once and passes it to `check_waistline`, `check_eye_legibility`,
`check_spec_coverage`, `check_contrast`, and `generate_roster`, replacing a
half-dozen bare `load_palette()`/`_lp()` calls). `check_ui`'s own
`load_palette()` is untouched and correctly so: it audits files already on
disk under `out/ui/`, which `ui_forge.py`/`ui_chrome.py` never claimed to
build per-style in the first place -- a different, larger, genuinely
not-yet-started gap, not a bug in this one.

Running both for real found more of the same honest picture:

- `portrait.py --check --style snes_rpg`: `reader`'s left eye renders 0px
  against bare skin. Its `hair_mat` (`neutral-2`) and `character.EYE`
  (also `neutral-2`) are literally the same ramp+offset -- under
  `cozy_ghibli`'s specific RGB values that pair still separates enough to
  read; under `snes_rpg`'s darker, more compressed `neutral` ramp it
  doesn't. Same root cause as PR #23's finding, different check, different
  specific collision.
- `manifest.py --check --style snes_rpg`: the same three waistline
  failures PR #23 already found (consistent -- both producers measure the
  same roster against the same palette), plus three new near-misses:
  `check_eye_legibility` measures eyes 0.147 from the face at skin tones
  `skin-4`/`skin-3`/`skin-2` against a 0.15 floor -- close, not a wide miss,
  but a real one specific to this palette's darker skin steps.

None of these threaten either style's approval: `style_approve.py` doesn't
require `portrait.py` or `manifest.py` to pass, only `character.py` OR
`portrait.py` OR `organic_rig.py` for the character-roster requirement, and
`organic_rig.py`'s entry already satisfies it. Recorded honestly rather
than suppressed, same as PR #23 -- `styles/snes_rpg/lock.json` now has a
real `portrait.py:roster` entry with `approved: false`.

**Landed (PR #25, stacked on #24): `--style` for `ui_chrome.py` -- the last
producer that could take it without needing the GPU.** `ui_forge.py` (SDXL
icons) and `ui_chrome.py` (procedural chrome -- dialogue frames, coins, star
ratings) were the two remaining producers with no `--style` at all, not the
accepts-but-ignores bug the last two PRs fixed. `ui_forge.py` needs `concept.
_pipe()` (SDXL, the GPU stage NEXT.md's own environment section flags) to
even run, so wiring and verifying it belongs with the GPU-bound work, not
this compute-light thread. `ui_chrome.py` has no such dependency -- purely
procedural, same category as `assetlib.py`'s builders -- so it got the same
small, mechanical `--style` treatment as `furnish.py`/`render_room.py`/
`build_plan.py`: a flag, `ramps` resolved from the active style and threaded
into `build()` (which gained an `out_dir` parameter, default `UI_DIR`, so a
non-default style writes to `out/ui_<style>` instead of silently sharing
the default style's output directory).

Verified by rendering three chrome pieces (`ui_dialogue_frame`, `ui_coin`,
`ui_star_rating`) under both styles side by side: all six pass their own
checks, and `snes_rpg`'s render is visibly, coherently punchier -- brighter
cream, a harder maroon outline in place of the muted rose one, sharper gold
on the coin -- not just a different-looking accident.

**Landed (PR #26, stacked on #25): `bob` and `curly`, the last two of
`character.hair`'s six styles, ported to `organic_rig.py` -- and the claim
that they needed new primitive code, corrected.** PR #22 held both back on
the stated reason that both rely on a partial (non-360deg) ring the
box/prism original has, which `add_cylinder`/`add_sphere` cannot express.
That claim was never actually tested against the real geometry -- it was
tried here, and it was wrong for both:

- `character.hair`'s `curly` never used a partial ring at all. It is a
  bigger cap plus two small FULL-sphere puffs at the sides -- the same
  full-ring idiom `bun` already uses, just two of them, symmetric. Ported
  directly, no new geometry needed.
- `character.hair`'s `bob` box only ever occupies the region a full,
  head-centred cylinder ALSO occupies once the head sphere's own opacity
  is accounted for. A centred cylinder sized at or past the head's own
  radius is invisible wherever it falls inside the head's silhouette (the
  head draws in front of it) and visible only where it pokes past that
  silhouette -- which is exactly "wraps around the sides and back, stays
  clear of the front" without clipping anything. This only works because
  the hair sits within the head sphere's own z-range (crown to jaw); it
  would NOT generalize to something that needs to hang lower, which is
  why `long`'s own back-offset technique (PR #19) is still the right one
  for its case -- two different problems that happen to want two different
  solutions, not one technique that should have been used for both.

Verified at both the back-corner azimuth (`organic_rig.py --demo`'s own
row, now six styles wide) and dead-on (`azimuth 90`, checked separately,
not shown in the committed sheet): both new styles read as visibly, clearly
distinct from `short` and from each other -- `bob` noticeably fuller
coverage toward the jaw, `curly` a distinctly bumpier silhouette from the
side puffs -- and both leave the eyes visible in every view checked.

`HAIR_STYLES` now has all six of `character.hair`'s styles; `organic_rig.py`
has no more deliberately-deferred hairstyle work.

**Landed (PR #28, stacked on #26): a real eye-visibility check for
`organic_rig.py`'s roster, and the bug it caught -- `archivist` shipping
with invisible eyes.** `check_roster` (PR #22) only ever ran
`character.check_contrast`/`check_waistline` against `ROSTER` -- both test
hair-vs-skin and shirt-vs-trousers, neither tests hair colour against
`C.EYE` itself. `archivist`'s `hair_mat="neutral-3"` sat one step from
`C.EYE`'s `neutral-2` on this style's own compressed neutral ramp, and
`bob`'s full head-wrap coverage put that hair directly behind the eye
boxes: found by zooming into the rendered portrait and seeing two blank
sockets, not by any check failing.

`check_eyes_visible` closes the gap, ported from `portrait.py`'s own
version of the same check: build the figure (torso, head, hair, arms) with
NO eyes, then again with exactly one eye box added, render both, count
differing pixels. No axis assumption about which half of frame is which
eye, no other feature's contrast to hide behind -- if adding the eye
changed fewer than `MIN_EYE_PIXELS` (3, same floor `portrait.py` uses), it
isn't visibly there, whether the cause is hair occlusion or colour
collision. Wired into `check()` alongside `check_direction_stability` and
`check_roster`, and into `--lock`'s recorded gate list, so this class of
bug is caught automatically on every future roster edit, not just by
manual visual spot-check.

Fix: `archivist.hair_mat` -> `wood-4` (already proven safe by
`check_contrast`/`check_waistline` for every other roster member). Full
roster -- `check_eyes_visible` included -- passes; re-rendered
`proof/organic_rig.png` shows archivist's eyes clearly against the bob
hair, visually confirmed alongside the numeric pass.

**Landed (PR #29, stacked on #28): `--style` for `tileset.py`, plus one more
honest, measured rejection under `snes_rpg`.** Mechanical wiring, same
pattern as `furnish.py`/`render_room.py`/`build_plan.py`/`ui_chrome.py`:
`build()` resolves `ramps` from the active style's palette instead of a bare
`load_palette()`, and writes to `out/tiles_<style>/` for a non-default style
rather than overwriting `out/tiles/`. `check_manifest_placement` gained an
`out_dir` parameter for the same reason. Regression-checked byte-identical
against `out/tiles/` under the default style before touching anything else.

Running it for real against `snes_rpg` surfaced a genuine finding, not a
wiring bug: `wall_panel_x`/`wall_plain_x` both fail `check_collapse` --
`cream-2` (the picture rail), `wood-1` and `wood-2` (the panel trim) resolve
to only 2 distinguishable colours at that wall's lambert value under this
style's compressed lightness range. `wall_panel()`'s literal ramp-name
choices were authored for `cozy_ghibli` and never touched since -- the same
"shared content, never chosen for this style" shape as `character.CUSTOMERS`
(PR #23) and `portrait.ROSTER` (PR #24), not the "hair colour vs. this
style's own new roster" shape PR #28 just fixed. Confirmed visually, not
just numerically: `out/tiles_snes_rpg/_room_corner.png`'s left (x-axis)
wall shows the picture rail and trim blurring together, while the right
(y-axis) wall -- clear of this collision -- reads distinctly banded.

Left as a recorded, honest rejection rather than patched: `wall_panel`'s
three trim colours are hardcoded literals, not sourced from a per-style
`materials:` role (that generalization is the same deferred
`assetlib.py`/`character.py` import-order work PR #12 already flagged, not
new scope for a CLI-plumbing PR). `tileset.py --style snes_rpg --proof`
exits 1 on this finding, as it should -- a real, unfixed defect, not a
silently-passing check.

**Landed (PR #30, stacked on #29): `--style` for `render_batch.py`, the
last GPU-free producer in the plumbing list.** Same mechanical pattern:
`ramps` resolved from the active style instead of a bare `load_palette()`,
`--out` defaults to `sprites/` for the default style (unchanged, its own
existing gitignore line) or `out/sprites_<style>/` for a non-default one --
deliberately nested under `out/`, not a new top-level `sprites_<style>/`,
because `out/` is already blanket-ignored and a sibling directory next to
`sprites/` would not be. Caught by checking `git status` after the first
`--style snes_rpg` run and seeing the new directory as untracked rather
than assuming the convention from `tileset.py`'s `out/tiles_<style>/`
(which lives under `out/` already) would automatically carry over.

Regression-checked byte-identical (`crate_cup_dir0.png`'s sha256, before
and after the change, under the default style) both before this fix and
again after it. `--style snes_rpg` renders the analytic test scene cleanly
against the new palette -- visually checked, no material-collision finding
here since the crate/cup scene's own materials were never audited against
`tileset.py`'s wall trim in the first place.

Every producer `NEXT.md`'s own migration-order plan named as GPU-free
(`furnish.py`, `render_room.py`, `build_plan.py`, `character.py`,
`portrait.py`, `manifest.py`, `ui_chrome.py`, `tileset.py`, now
`render_batch.py`) has `--style` wired through its actual checks, not just
its `--lock` bookkeeping. `ui_forge.py`/`art_review.py`/`export_godot.py`
remain -- the first needs `concept.py`'s SDXL pipeline to run at all (GPU),
and the other two have not yet been looked at closely enough to know
whether they carry the same accepted-but-ignored risk; left for a future
PR rather than assumed clean.

**Landed (PR #31, stacked on #30): `art_review.py` audited, and given a
`--style` convenience flag -- it turned out clean, not another instance of
the accepted-but-ignored bug.** `art_review.py` never claimed `--style`
support at all before this; it already took an arbitrary `--palette` path
or variant name, and `load_palette()` reads any `palette.json` in that
format regardless of which style produced it -- `--palette
styles/snes_rpg/palette/palette.json` already worked, just not
conveniently. The file's other palette-shaped default,
`measured_symmetry(ramps=None)`, is a real optional parameter a caller
already supplies explicitly (it is not reachable from `main()`'s own image-
review path at all) -- not a CLI flag silently ignored by the check it
claims to drive, which is the actual shape of the bug PRs #23/#24 fixed.
Nothing to fix there.

Added `--style NAME` as sugar for that same `--palette <path>` call,
resolved via `style.load_style(name).palette_path`; `--palette` still wins
if both are given, and an unknown style name surfaces `load_style`'s own
error rather than a new one. Verified against both a default-style and a
`snes_rpg` sprite, plus the unknown-style-name error path.

`export_godot.py` deliberately NOT touched here: it stages real files into
a generated, Godot-imported project tree (`godot_export/project/`) and
shells out to an actual Godot binary for the import/build/round-trip-check
steps. A second style's export needs a real design decision (a parallel
project tree? a re-run of the headless import against a different staged
source?) that a mechanical CLI-flag pass would be guessing at, not the kind
of "same pattern nine times" plumbing the rest of this list has been --
flagged as a boundary rather than attempted unscoped, same reasoning as
`ui_forge.py`'s GPU dependency.

**Landed (PR #34, stacked on #31): the full 56-prop library, swept through
`snes_rpg`, not just "one of each."** Every producer up to this point had
been verified against a single representative asset per class (one
character roster, one composed room, one tileset). `style_approve.py`'s own
docstring says that's deliberate -- "one of each asset class" is the
approval bar, not "every asset" -- but nobody had actually run the whole
`furnish.py` catalogue through the new style and looked, so it remained an
assumption rather than a measurement.

`furnish.py --style snes_rpg` builds all 56 props, 448 sprites, zero
crashes, zero footprint-cap surprises beyond the same 7 props that already
cap under `cozy_ghibli` (identical list, same reasons -- a builder/fp-height
mismatch unrelated to palette). `art_review.py --style snes_rpg --json` over
the full set: 0 blockers, 72 `ramp-coherence` warnings, 96 `light-direction`
notes.

The number that matters is the comparison, not the count in isolation: the
identical sweep against `cozy_ghibli` also produces exactly 72
`ramp-coherence` warnings, on the exact same 17 props (`book_stack`,
`pastry_case`, `plant_hanging`, `shelf_wall`, ... -- full list in the PR).
Byte-for-byte the same defect set under both palettes, because
`ramp-coherence` measures which MATERIAL ramps sit adjacent in the mesh,
which is style-independent geometry, not a colour-legibility question a new
palette could newly break. `light-direction`'s note count differs (96 vs
134) but that's expected and not a defect -- it's graded on OKLab lightness
percentile position, which a different palette's lightness distribution
naturally shifts, and it's a NOTE, not a WARNING, precisely because the
check's own docstring calls it "a rough check."

Spot-checked two visual outliers before trusting the numbers alone, per this
track's own discipline: `wall_art_framed` renders as a flat, detail-free
canvas under `snes_rpg` -- confirmed identical under `cozy_ghibli` too, so
it's how the prop is authored (a plain-colour canvas in a wood frame), not a
style regression. A full 56-prop contact sheet was rendered and reviewed
before writing this up; every prop reads as its own distinct, legible
silhouette.

Net finding: the prop library generalizes cleanly across styles with zero
new defects at full scale, not just at the "one of each" sample size
`style_approve.py` requires. No code changed -- this is a verification pass,
and its result is that there was nothing here to fix.

**Landed (PR #36, stacked on #35): `--style` for `ui_forge.py`, the last
GPU-bound producer in the plumbing list, and a real run against `snes_rpg`
rather than a paper wiring change.** Same mechanical pattern as every other
producer on this list: `ramps` resolved from `load_style(args.style)
.palette_path` instead of a bare `load_palette()`, threaded through
`forge()`'s existing quantize/outline call via a new `ui_dir` parameter
(default `UI_DIR`, unchanged for the default style). Output nesting matches
`furnish.py`'s own `out/sprites/<style>` convention specifically --
`out/ui/<style>` for a non-default style -- rather than `tileset.py`/
`render_batch.py`'s `_<style>` suffix convention; both live under `out/`,
already blanket-gitignored, so this was a convention to match rather than a
gitignore gap to fix. PR #30's `sprites/`-has-its-own-line gap doesn't apply
here: `UI_DIR` was `out/ui` from day one.

Regression-checked for the default style two ways, since a fresh clone had
no prior `out/ui/` content to hash against. First: `load_palette(load_style
("cozy_ghibli").palette_path)` is dict-equal to the old bare `load_palette()`
call -- both resolve to the same `palette/palette.json` and parse it the same
way -- so the deterministic quantize/outline stage runs on an identical
ramps object before and after this change, by construction, not just by
argument. Second: a live run (`--only ui_icon_espresso --retry-seeds 0`, no
`--style` flag) passed on the first seed and wrote to the unchanged
`out/ui/` path.

Ran the full 14-icon batch for real against `snes_rpg` (default
`--retry-seeds 2`, so 3 seeds per icon): **9/14 passed the speckle gate.**
Looked at all fourteen, not just the count -- `proof/ui_forge_snes_rpg.png`,
gated icons included via a reconstructed quantize/outline pass over their
last attempted seed's concept image (never written to disk on failure,
since `forge()` only saves the final PNG on success), so a gated icon's
actual shape is visible next to its failure reason rather than trusted blind:

- The five drinks (`ui_icon_cappuccino`, `ui_icon_cold_brew`,
  `ui_icon_espresso`, `ui_icon_latte`, `ui_icon_tea`) pass and read
  correctly -- the same "5 drinks usable" finding `cozy_ghibli`'s own UI
  pass recorded, reproduced under a second palette. A direct
  `ui_icon_espresso` cozy_ghibli-vs-snes_rpg comparison (same proof sheet)
  confirms the quantize/outline/palette stage re-shades a correctly-read
  icon cleanly, no cross-ramp bleeding.
- `ui_dialogue_frame` and `ui_nameplate` pass the metric with the wrong
  shape -- `ui_dialogue_frame` renders as a blue technical dial/gadget icon,
  not a speech bubble; `ui_nameplate` renders as a cassette-player-style
  device panel, not a banner. Same class of gate-proxy false positive
  `ART_CRITIQUE.md` already recorded for these two ids under `cozy_ghibli`
  ("photographed pictures-in-frames" and "a framed panel" respectively),
  reproduced under a second palette rather than newly discovered -- the
  metric's blindness to shape is style-independent by construction, since
  `check_icon` never inspects the palette at all.
- `ui_coin` and `ui_icon_pastry` gate for the same documented reasons as
  under `cozy_ghibli`: the coin renders muddy, and the pastry's lamination
  is exactly the high-frequency-detail-quantizes-to-speckle ceiling
  `ART_CRITIQUE.md`'s "clearest proof yet" entry already named. Not new, not
  style-specific, not chased further for the same reason it wasn't chased
  there.
- `ui_star_rating` gates worse than under `cozy_ghibli` (34.2% isolated) on
  the same burst-shaped-rather-than-star ceiling.
- `ui_clock_day` and `ui_heart_mood` are the one genuinely new finding: both
  passed under `cozy_ghibli` (after one and two reseeds respectively) but
  fail all three seeds under `snes_rpg` at the same `--retry-seeds 2`
  budget -- and looking at them, both are still legible, correctly-shaped
  icons (a clock face with tick marks, a heart with internal linework), not
  the wrong-shape or missing-subject failures above. `concept()` takes no
  style or palette argument, so the raw SDXL image for a given seed is
  bit-identical between the two style runs -- the entire difference in
  outcome is produced by the quantize/outline stage, i.e. by the palette
  alone, which rules out seed luck as the explanation. `snes_rpg`'s bible
  deliberately specifies fewer, harder-edged shading bands (4-5 steps vs
  `cozy_ghibli`'s 5-7) and far less chroma falloff (PR #18), which quantizes
  the same fine internal linework these two subjects carry into more
  isolated pixels than `cozy_ghibli`'s softer palette does. Recorded as a
  genuine, style-specific defect and left that way -- lowering
  `MAX_ISOLATED` or raising `--retry-seeds` to make it disappear would be
  exactly the proxy-gaming this file's own comment on `--retry-seeds`
  already warns against.

`ui_forge.py` was the last GPU-bound producer `NEXT.md`'s migration-order
plan named; every producer on that original plumbing list (`furnish.py`,
`render_room.py`, `build_plan.py`, `character.py`, `portrait.py`,
`manifest.py`, `ui_chrome.py`, `tileset.py`, `render_batch.py`,
`art_review.py`, now `ui_forge.py`) has `--style` wired through its real
checks. `export_godot.py` remains the one deliberately-flagged boundary
case (PR #31).

---

**Landed (PR #37, stacked on #36): `--style` for `export_godot.py`, the
design decision PR #31 deliberately left unattempted.** The real question
PR #31 flagged -- does a second style's export get its own Godot project
tree, or does one tree get re-staged and re-imported per run -- was decided
with evidence, not guessed: `build_all.gd`, `verify_font.gd` and
`verify_palette.gd` were read in full, and none of the three contains a
style-specific path, constant, or branch. All three address everything
through `res://`, which Godot resolves against whatever directory `--path`
names, and read their inputs (`build_manifest.json`, `assets/`) from that
same directory -- so the exact same three files, unmodified, build and
verify whichever style's assets were staged into whatever project they're
pointed at.

That finding decided both halves of the design at once. First,
`godot_export/project_<style>/` -- a full, separate sibling project
directory per non-default style, `godot_export/project/` untouched for the
default -- rather than one project re-staged in place per run, because a
shared tree would make each style's build overwrite the other's on disk and
tie the default's own regression bar to "nobody ran a different style more
recently," which is exactly the kind of fragile coupling this track's
discipline exists to avoid. Second, because the tracked GDScript is
genuinely style-agnostic, that per-style directory does NOT get its own
independently-tracked copies of `project.godot`/`build_all.gd`/
`verify_*.gd` -- two tracked copies of files with identical behaviour is a
pure drift risk (a fix landing in one and not the other) with nothing to
show for it. Instead `export_godot.stage_style_project()` copies the four
files from `godot_export/project/`'s own tracked originals into the style
directory fresh on every run, the same "regenerated from source every time"
contract `assets/`/`resources/` already have. `godot_export/project_*/` was
added to `.gitignore` as a whole tree (not the assets/resources/.godot
subset `project/` uses), since nothing under a style directory is tracked.
Checked with `git status --porcelain --ignored` after the first `--style
snes_rpg` run and confirmed `godot_export/project_snes_rpg/` shows `!!`
(ignored) with nothing untracked -- PR #30's own gitignore-gap mistake, not
repeated.

`package_godot.stage()` gained a `style_name` parameter and a new
`style_paths()` helper resolving `manifest_path`/`sprites_dir`/
`project_dir`/`ui_dir`/`tiles_dir`. It deliberately does NOT invent one
uniform per-style convention -- it matches whichever convention each
upstream producer's OWN `--style` flag already committed to on disk:
`furnish.py`'s nested `out/sprites/<style>/`, and `tileset.py`/
`ui_chrome.py`'s sibling-with-suffix `out/tiles_<style>/`/`out/ui_<style>/`.
`sprites/atlas.json` (`animate.py`'s output) is the one input left
unparameterized: `animate.py` has no `--style` flag at all yet, unlike
every other producer this file stages from, so there is no per-style atlas
to resolve to -- staying with the one fixed path is accurate, not an
oversight, and the animation section simply stages nothing for either style
until that producer is generalized too (a real, separate, not-yet-started
gap, same shape as `ui_forge.py`'s GPU dependency).

Regression evidence, and a real finding about the bar itself: comparing
`.tres` output byte-for-byte turned out not to be possible AT ALL, even
between two consecutive runs of fully unmodified code -- Godot's own
`ResourceSaver` assigns a random hash suffix to every `ext_resource`/
`sub_resource` id on every save (confirmed by running the untouched
pre-change code twice in a row and diffing the output: only those id
tokens differed). The real bar applied instead: `build_manifest.json`
(pure JSON, no Godot-assigned ids) came back byte-identical, same sha256,
across three separate runs -- unmodified code twice, this change's code
once. All 56 `.tres` files came back structurally identical between
unmodified and modified code once the random id tokens are canonicalized
by first-appearance order (a small normalizing script, not a semantic
diff) -- 0 mismatches across all 56 files. `godot_export/project/` itself
is untouched by any `--style snes_rpg` run, by construction, so the
default's own tree was never at risk of drifting regardless.

The real `snes_rpg` pipeline run, staged from the 448-sprite sweep PR #33
already produced: stage, headless import, headless build and both
round-trip checks all passed cleanly, 56 resources written to
`godot_export/project_snes_rpg/resources/`. Looked at, not just counted:
`armchair.tres` references `res://assets/armchair/armchair_dir0.png`
correctly inside its own project tree, and that staged PNG is byte-identical
to `out/sprites/snes_rpg/armchair_dir0.png` (and differs from the default
style's own `armchair_dir0.png`, confirming the two styles' assets never
cross-contaminate). The palette LUT's pixel values were read back directly
and compared against a fresh `palette_forge.forge()` call for `snes_rpg`'s
own bible -- exact match -- independently of `verify_palette.gd`'s own
in-engine check reporting the same thing ("Godot reads all 1 palettes x 32
colours exactly, at nearest filtering"). That "1 palette" was a real fact
about `snes_rpg`'s `bible.yaml` at the time, not a bug: it declared no
`golden_hour`/`evening`/`night`/`overcast` variants yet, unlike
`cozy_ghibli`'s five rows -- day/night palette variants for this style were
separate, not-yet-started work.

~~That gap is closed.~~ **Done** (branch `snes-palette-variants`):
`styles/snes_rpg/bible.yaml` now declares the same four variants, swept
against `snes_rpg`'s own base palette rather than copied from
`cozy_ghibli`'s numbers -- its higher base chroma (`chroma_falloff` 0.10 vs
0.26) and tighter `min_lightness` (0.12 vs 0.15) mean the two packs'
strengths genuinely differ. `golden_hour` is bounded by `max_lightness` via
`cream`'s highlight end, same failure shape as `cozy_ghibli`'s own; `evening`
and `night` are both bounded by `min_lightness` via `neutral`'s shadow end
(unlike `cozy_ghibli`, where only `golden_hour`/`night` are bounded);
`overcast` never hit a hard constraint even swept toward near-zero chroma,
so it ships at a moderate, chroma-driven strength instead. `check_separation`
passes clean on all five (base + four variants); closest pair is
evening/overcast at 0.0471 against the 0.035 floor, and evening/night --
the pair that collapsed to 0.0057 in `cozy_ghibli`'s own rejected first
sweep -- sit 0.0569 apart here. Proof sheet: `proof/variants_snes.png`.

Two honest gaps, not fixed here because fixing them is out of this PR's
scope: `out/ui/` (and `out/ui_snes_rpg/`) don't exist in this environment
-- `ui_forge.py --style` is separate, in-flight work -- so the nine-slice
round-trip and font-layout checks both no-op cleanly for both styles
(empty `ui`/`font` sections in the build manifest, not a failure) rather
than being exercised against real content; and `sprites/atlas.json`
(`animate.py`'s output) was missing from `ROOT/sprites/` in this
environment (only a stray, differently-nested `sprites/sprites/atlas.json`
existed), so the `anim` section staged nothing for either style -- exactly
the gap `package_godot.stage()`'s existing `atlas_path.exists()` guard is
already built to degrade through, not a new failure this PR introduced.

Every producer `NEXT.md`'s migration-order list named is now `--style`-wired
except `animate.py` (never carried a `--style` flag to begin with, and
picking up that gap is new scope, not a rider on this one) -- `ui_forge.py`
landed the same way one PR earlier (#36, above).

---

**Landed (PR #38, stacked on #31): the import-order blocker solved for real,
scoped to the one place with a measured defect -- `tools/tileset.py`'s wall
trim -- not the much larger `assetlib.py`/`character.py` version of the same
problem.** PR #29 found `wall_panel_x`/`wall_plain_x` failing `check_collapse`
under `snes_rpg`: the picture rail and wainscot batten, hardcoded as literal
`WOOD + "-1"`/`WOOD + "-2"` tokens imported from `assetlib.py` at module load,
collapsed to the same colour as each other at that wall's lambert. Left as a
recorded rejection rather than patched, because fixing it meant actually
solving the import-order problem `style.py`'s own docstring has flagged since
PR #12, not routing around it.

**The choice, and why.** `style.py` names two fixes: an early `sys.argv`
peek before the consuming module imports (so a module-level default can be
bound correctly the first time), or converting bound-at-def-time defaults
into a lazy, call-time lookup. Took the second, same reasoning `style.py`'s
own docstring gives for preferring it -- an args-peek is a global side
effect every future entry point has to know exists, a call-time lookup is
local and unit-testable with no dependency on `sys.argv` ever having been
parsed. Concretely: `tileset.py`'s `wall_plain`/`wall_panel` used to be
module-level functions closed over `WOOD`/`WALL_FIELD`, imported once from
`assetlib.py` at parse time -- literals no `--style` flag could ever reach,
the identical shape of bug `assetlib.py`'s own `table(top=WOOD, ...)`-style
defaults have, just one indirection further away. They're now built by a new
factory, `make_wall_patterns(materials: dict)`, called once per `build()`
run with the active style's OWN `materials:` dict and returning ordinary
closures already bound to the right tokens -- `build()`, `room_corner()`
and every check that takes a `pattern` function are otherwise unchanged,
because the factory preserves the exact `pattern(t, z, v)` calling
convention every wall/floor pattern function already shared. `room_corner()`
gained a `wall_patterns: dict | None = None` parameter, resolved to
`cozy_ghibli`'s own patterns if omitted -- the sentinel-resolved-at-call-time
idiom applied one layer up, for the one caller (none, today) that might
invoke it directly without going through `build()`.

**Scope boundary, stated rather than assumed away:** this does NOT touch
`assetlib.py`'s or `character.py`'s own def-time-bound material/rig
constants (the original PR #12 finding) -- over 150 call sites across
`assetlib.py` alone use `WOOD`/`CERAMIC`/`FABRIC`/... as function defaults.
PR #20 already measured that none of them currently need a role remapped to
a DIFFERENT ramp name (both style packs map every role to the same ramp,
only the ramp's own RGB values differ), so rewriting all of them now would
be exactly the "sweeping change nobody looked at" this track's own process
argues against, for zero currently-measured benefit. What changed is
narrower and load-bearing: `tileset.py`'s wall trim needed not just a
different ramp's colours (already handled, for free, by `ramps` being
resolved per-style) but a different OFFSET along that ramp per style, which
`materials:` role names alone can't express without also carrying the tone
offset -- exactly the `wall_field`/`floor_field` idiom already used, now
extended to two more roles.

**The actual fix, brute-forced against the measured requirement, not
picked by eye.** Two new required material roles, `wall_trim` and
`wall_trim_shadow` (`style.REQUIRED_MATERIAL_ROLES` now has eleven, not
nine). `cozy_ghibli` got `wood-1`/`wood-2` -- the exact literals it already
had, so its render is unchanged. `snes_rpg`'s bible carried the same two
literals forward unexamined in PR #29 and they collided: at the x-wall's
lambert (0.28511), `wood`'s 5-step ramp indexes to base step 1, so `wood-1`
clamps to step 0 and `wood-2` ALSO clamps to step 0 (one step further down
goes negative first) -- the ramp has no headroom below `wood-1` at this
lambert, so the "further step" silently becomes the SAME step instead of a
darker one. Brute-forced every `(ramp, offset1, offset2)` triple with both
offsets in `[-4, +4]` across every multi-step ramp in the palette (200
combinations cleared the bar of "`wall_field`, `wall_trim` and
`wall_trim_shadow` resolve to three distinct colours" at BOTH the broken
x-wall's lambert AND the already-working y-wall's lambert -- checking only
the broken wall would risk silently breaking the one that already worked).
Picked the smallest-magnitude survivor over the widest-margin one (several
combinations forced the ramp's two endpoints regardless of lambert, a flat
un-shaded trim -- a bigger visual change than this defect calls for):
`wall_trim` stays `wood-1`, unchanged; only `wall_trim_shadow` moves, from
`wood-2` to plain `wood` (offset 0 -- one real step lighter than `wood-1` at
every lambert, since it can never clamp below `wood-1` the way `wood-2`
did). Bracket: the floor is a hard "3 distinct colours, not 2", not a
tunable number, and the weakest passing margin in the whole search was this
exact pair -- oklab dE 0.152 at the x-wall, 0.154 at the y-wall -- the tight
edge of the bracket, not a comfortable middle chosen after the fact.

**A second bug the fix itself surfaced, caught by the check that exists for
exactly this.** The first working version of `make_wall_patterns` still
failed `check_manifest_placement` under `snes_rpg` -- 1152 pixels different
between the projected room and the one rebuilt from `tileset.json` alone.
Not a placement-arithmetic bug: `check_manifest_placement`'s own `ref =
room_corner(width, ramps, n=n)` call didn't pass `wall_patterns` through,
so it silently fell back to `room_corner`'s `cozy_ghibli` default while the
`out` half of the same comparison read the REAL `snes_rpg` atlas PNGs
already on disk -- comparing the right style's tiles against the wrong
style's projection. Exactly the class of silent-default bug PR #23/#24
found and fixed in `character.py`/`portrait.py`/`manifest.py`'s own
`--style`-accepted-but-ignored pattern, rediscovered here one layer deeper.
Fixed the same way: `wall_patterns` threaded through `check_manifest_placement`
and `build()`'s call into it.

**Regression, proven not asserted.** Hashed every file `tileset.py --proof`
writes under `out/tiles/` (16 files: 3 floor atlases + proofs, 4 wall
atlases + proofs, the room corner, `tileset.json`) against a build from
before this change, twice -- once after the `make_wall_patterns` change
alone, again after the `check_manifest_placement` fix -- sha256 identical
both times, full stop, under the default `cozy_ghibli` style. `--style
snes_rpg --proof` exits 0 for the first time on this track: `check_collapse`
clean on both `wall_panel_x`/`wall_plain_x`, `check_manifest_placement`
clean. Verified the check fails in both directions, not just found passing:
rebuilt `wall_panel`'s closures with the OLD `wood-2` value swapped back in
for `wall_trim_shadow` and confirmed `check_collapse` reports the exact same
"3 materials resolve to only 2 colours ... (cream-2, wood-1, wood-2)"
message PR #29 recorded, then confirmed it goes clean again with the shipped
value -- the check can fail, and doesn't, for the right reason.

**Looked at the render**, the discipline this whole track insists on:
`out/tiles_snes_rpg/_room_corner.png`, both walls. Cropped and zoomed the
top-of-wall picture-rail band on the x-axis (left) wall side by side against
a render using the old, broken `wood-2` value -- the broken version's rail
reads as a near-black sliver almost indistinguishable from the tile's own
outline stroke; the fixed version's rail is a clearly lighter, distinctly
separate band on BOTH walls now, not just the y-axis one PR #29 already had
working. `out/tiles/_room_corner.png` (default style) visually unchanged
from before, matching the byte-identical hash result.

---

**Landed (PR #27, stacked on #26): `--style` for `animate.py`, the last
producer without it.** Same mechanical pattern every other producer in the
list has used: `ramps` resolved via `load_palette(load_style(args.style)
.palette_path)` instead of the bare `load_palette()` the module hardcoded at
line ~259 (always `cozy_ghibli`, regardless of any flag, because there was
no flag). `--extras`/`--extras-seed` already threaded `ramps` into
`C.generate_roster` correctly before this change — verified by reading, not
assumed, and confirmed again here with a live `--extras` render under
`snes_rpg` (`out/sprites_snes_rpg_extras_smoke3/extra07.png`, later
cleaned up as gitignored scratch output).

Output path follows the convention PR #30 established for `render_batch.py`,
not a new one invented for this file: `--out` defaults to `sprites/` for the
default style (unchanged — its own existing `.gitignore` line) or
`out/sprites_<style>/` for a non-default one, nested under the
blanket-ignored `out/` rather than a sibling top-level directory. Verified
directly rather than assumed: `--style snes_rpg` (no `--out`) wrote to
`out/sprites_snes_rpg/`, and `git status --porcelain --ignored` afterward
showed only `!! out/` — nothing untracked, confirmed with
`git check-ignore -v` against the written files.

**Regression check.** Default style, same character/seed/clip
(`--only barista`, no `--extras`): sha256 of `sprites/barista.png` identical
before and after the change (`1b2720429fd49528f485050d5c07becc76888f6bbf8d57dbc005dbefbb866a83`)
— a pure threading change, zero behaviour change for the shipped style.

**Real render, visually confirmed.** `animate.py --only barista --style
snes_rpg` produced a full sheet against the new palette; a side-by-side of
the `walk`/`s` frame strip under both styles is at
`proof/animate_style_compare_barista_walk_s.png` — `snes_rpg` reads
visibly harder-edged and more saturated (magenta dress, darker cooler
shadow steps) against `cozy_ghibli`'s softer pastel pink/cream, as expected
from the two palettes' own bibles.

**The four-name roster finding (PR #23) reproduces exactly, not
differently.** `animate.py`'s `ROSTER` uses `character.py`'s hardcoded
`CharacterSpec`s, which resolve against ramp *role* names and so pick up any
style's palette automatically — but `character.py --style snes_rpg`'s own
`check_contrast`/`check_waistline` still fail the same four specs PR #23
already found and left as an accepted, not-fixed-by-design finding: `elder`
(hair/skin 0.088 vs 0.13 needed), `reader` (0.022 vs 0.085), `regular`
(0.040 vs 0.085), `writer` (0.080 vs 0.085). Re-run here as a consistency
check, not a new investigation — `animate.py` doesn't call those checks
itself (it renders whatever `character.build()` hands it, geometry and all),
so this PR neither fixes nor worsens that finding. It is still true that
fixing the roster's colours risks breaking `cozy_ghibli`'s clean pass, and
that fixing the check floors would defeat their purpose.

**`package_godot.py` scope decision, stated rather than left implicit.**
This checkout's `package_godot.py` and `export_godot.py` currently carry
*zero* `--style` wiring — no `--style` flag, no style-suffixed path, on
either file (confirmed: `grep -n style tools/package_godot.py
tools/export_godot.py` matches nothing). `package_godot.py`'s `stage_anim`
reads a single fixed `ATLAS = ROOT / "sprites" / "atlas.json"`, which is now
only half the story: a `--style snes_rpg` run of `animate.py` writes its
atlas to `out/sprites_snes_rpg/atlas.json` instead, and nothing stages it.
Fixing that coherently means giving `package_godot.py` its own `--style`
(to pick the atlas path) and `export_godot.py` — the actual three-step
orchestrator per its own docstring — a matching flag and a style-suffixed
project tree, which is a real, separate feature (not a rider on a CLI-
plumbing PR), the same size of change PR #30's own writeup deferred for
`ui_forge.py`/`art_review.py`/`export_godot.py` at the time. Left undone
here, on purpose, not silently: the Godot export path stages nothing for a
non-default style until that pair of files is generalized together, same
as it staged nothing for `animate.py`'s clips before this PR — the
difference is this is now the *only* remaining gap, not one of several.

---

**Landed (PR #50, stacked on #47-#49): `package_godot.py` resolves a
per-style atlas, closing the one gap PR #37's own writeup flagged as
"real, separate, not-yet-started."** `animate.py` picked up `--style` in
PR #27 (landed on `animate-style`); this is the other half PR #37 declined
to guess at rather than invent.

**The convention, verified by running it, not assumed.** `animate.py
--style snes_rpg --only barista` was actually run against this checkout: it
wrote to `out/sprites_snes_rpg/atlas.json`, not a path this PR picked by
analogy to `furnish.py`'s nested `out/sprites/<style>/` or
`tileset.py`/`ui_chrome.py`'s `out/tiles_<style>/` — a third convention,
matching `animate.py`'s own `--out` default exactly. `style_paths()` (the
helper PR #47/#48 already built, extended here rather than duplicated) now
returns an `atlas_path` key alongside its five existing ones: `ATLAS`
(`sprites/atlas.json`, unchanged) for the default style,
`out/sprites_<style>/atlas.json` for any other. `stage()`'s `atlas_path`
parameter changed from a hardcoded `= ATLAS` default to `= None`, resolved
through `style_paths()` the same way its other four path arguments already
were — an explicit caller-supplied value still wins, same contract as
before.

**A real bug, caught before it shipped, not a hypothetical.** Running
`package_godot.py --style snes_rpg` against the pre-fix code (to get a
baseline) showed `1 characters + 0 effects, 7 clips, 336 frames` in the
summary — looked like it was already working. It wasn't: the staged
`godot_export/project_snes_rpg/assets/anim/barista.png` sha256
(`1b272042...`) matched the *default* style's `sprites/barista.png`
byte-for-byte, not `out/sprites_snes_rpg/barista.png`
(`d9eab0d8...`) — the old hardcoded `ATLAS` constant was silently staging
`cozy_ghibli`'s animation sheet into a `snes_rpg` export, the "worse" case
this gap's own writeup named but hadn't measured. After the fix, the same
byte comparison confirms the staged PNG now matches the real `snes_rpg`
atlas and no longer matches the default's.

**Clean degrade, checked per style, not just for the default.** Renamed
`out/sprites_snes_rpg/atlas.json` out of the way and re-ran
`package_godot.py --style snes_rpg`: exit 0, no `anim` key in
`build_manifest.json`, same no-op behaviour the `atlas_path.exists()` guard
already gave the default style before this change — a style with no
`animate.py` run yet degrades the same way a missing atlas always has,
rather than crashing.

**Real Godot run, not just staged files.** `out/`'s manifests don't exist
in this checkout (`furnish.py` had never been run here) — built a minimal
two-prop scope (`furnish.py --only grinder_burr chair_wood`, both styles)
to get real inputs rather than fabricate them. `export_godot.py --style
snes_rpg` then ran the full three-step pipeline against the real Godot 4.3
binary at `D:/vibes/.godot-tool/...`: stage, headless `--import`, headless
`build_all.gd`, both round-trip checks, exit 0. `build_all.gd` reported
"built 2 prop SpriteFrames, **1 animation SpriteFrames**" — before this
fix, per PR #37's own honest record, that number was 0 for every
non-default style. `godot_export/project_snes_rpg/resources/anim/
barista.tres` now exists and its `ext_resource` correctly points at
`res://assets/anim/barista.png`, the byte-verified `snes_rpg` sheet.

**Regression, both halves.** Default style: `package_godot.py` (no
`--style`) staged into `godot_export/project/assets` with every file's
sha256 identical to a pre-change baseline, `build_manifest.json` included —
zero behaviour change, because `atlas_path`'s style-resolved default for
`cozy_ghibli` is the exact same `ATLAS` constant it always was. Ran the
real Godot pipeline against the default style too (`export_godot.py`, no
`--style`): "built 2 prop SpriteFrames, 1 animation SpriteFrames" — same
count as before this change, since the default's atlas was already being
found via the old hardcoded path.

**Scope boundary, stated rather than assumed away.** `out/ui/` and
`out/tiles/` (default and per-style) don't exist in this environment
either, same gap PR #37 already recorded — the `ui`/`font`/`tiles`
sections of `build_manifest.json` stay empty and no-op cleanly for both
styles, not exercised against real content here. This PR closes exactly
the one gap it names (the atlas), nothing wider.

**Landed (PR #52): `--style` for `factory.py` — found by an external
review, not this session's own audit, and worth recording as two separate
findings.** `factory.py` had zero `--style` support: no flag in `main()`'s
argparse, and a bare `ramps = load_palette()` at line ~271 that always
resolved `cozy_ghibli` regardless of caller intent. This wasn't caught by
the systematic style-flag sweep earlier in this session because
`factory.py` is a different pipeline category — SDXL concept -> TripoSR
mesh -> sprite (`concept.py`/`lift.py`/`ingest.py`) — from the procedural
`assetlib.py` builders that sweep covered. An external architecture review
found it instead; independently confirmed by reading the code.

**Fixing the bare `load_palette()` call alone would have been cosmetic.**
`run_subject(spec, pipe, model, ramps, retries)`'s `ramps` parameter is
never actually consumed for rendering — stages 1–3 (concept/lift/ingest)
touch no palette at all, and stage 4–8, the only place a palette matters,
happens in a `subprocess.run([..., "render_batch.py", ...])` call that
wasn't being told which style to use, at all, before this PR. Threaded
`style` and a resolved `sprite_dir` through `run_subject`'s signature so
the subprocess actually receives `--style` — the real wire, not the
decorative one.

**Output convention: `furnish.py`'s, not `render_batch.py`'s own.** Sprites
now land in `out/sprites/` for the default style, `out/sprites/<style>/`
for anything else, matching `furnish.py`'s nested convention for the same
"generated props" category — not `render_batch.py`'s own standalone
`out/sprites_<style>/` (that convention exists because *its* default lives
at a differently-gitignored top-level `sprites/`; `factory.py`'s sprite
output was already entirely under `out/`, so no new `.gitignore` line was
needed — confirmed with `git check-ignore -v` against a scratch file at the
new path).

**Concept/mesh caching stays shared across styles, correctly.**
`concept.py`, `lift.py`, and `ingest.py` take no style parameter at all, so
a `teapot.png`/`teapot.obj`/`teapot_bound.obj` from one `--style` run is
byte-identical to another's — verified by reading all three signatures, not
assumed. No per-style nesting needed there, and reusing the cache is
correct, not a collision risk.

**Noted, not fixed: the same bug class survives one level deeper.**
`ingest.py`'s own `ingest()` (line ~620) has a bare `ramps = load_palette()`
too, used to decide which material each vertex binds to — so the bind
*label* is always chosen against `cozy_ghibli`'s palette even under a
non-default `--style`; only the final render's colours vary. Left alone:
fixing it means changing a shared library function with its own other
callers, a separate piece of work, not a rider on this CLI-plumbing PR.

**Verification is honest about its GPU limitation, not padded.** No SDXL/
TripoSR pipeline run happened in this pass — the GPU was assumed busy
elsewhere and the task explicitly ruled out loading either model. What was
checked instead: `import factory` and `python -m py_compile` both succeed;
`factory.py --help` builds the parser and shows the new flag without
touching GPU code; `grep -n "load_palette(" tools/factory.py` shows exactly
one call site, style-resolved, no bare calls left; the default-style path
is provably byte-identical by inspection (`load_style("cozy_ghibli")
.palette_path` resolves to the exact same `ROOT/"palette"/"palette.json"`
bare `load_palette()` always used; `sprite_dir` for the default style is
the same constant as before; the subprocess's added `--style cozy_ghibli`
is a no-op, matching `render_batch.py`'s own default). What genuinely
cannot be confirmed without a GPU, stated plainly: whether a real `--style
snes_rpg` run actually produces sprites shaded in that palette end-to-end.
That claim is not made here.

---

**Landed (PR #53): `ingest.py` closes the follow-up PR #52 explicitly
noted and declined to fix inline.** PR #52 wired `--style` for
`factory.py`'s CLI plumbing and, in its "Noted, not fixed" section, named
a second instance of the exact same bug class one level deeper: `ingest()`
had a bare `ramps = load_palette()`, always resolving `cozy_ghibli`
regardless of caller intent — but `ingest()` is a shared library module
with its own callers, not a CLI-plumbing rider, so PR #52 scoped it out
on purpose rather than folding it in unreviewed.

**Worse than the surface-level version of this bug, because `ingest()`
doesn't just render the wrong colour — it can pick the wrong material
entirely.** `bind_vertex_colours()` and `rebind()` use `ramps` to find the
nearest-matching ramp for a raw RGB colour, and `cozy_ghibli` and
`snes_rpg` have different actual RGB values per ramp name. A colour that
lands on `neutral` under one palette can land on `sky` under the other —
a material *label* assigned once, at ingest time, that nothing downstream
re-derives even when the final render does pick up the right style's
colours.

**Fixed the one function in this file that didn't already follow its own
idiom.** `check_roundtrip`, `check_transform`, and `check_albedo_regression`
all already wrote `ramps = ramps or load_palette()`; `ingest()` was the
holdout. Gave it `ramps: dict | None = None` with the same idiom, added
`--style NAME` to `main()` (default `cozy_ghibli`, resolved the same way
`render_batch.py`/`build_plan.py` already do), and threaded the fix
through to `factory.py`: `run_subject()` already received a `ramps`
parameter from `main()`'s own `load_palette()` call but dropped it before
calling `I.ingest()` — same bug, one hop further down the call chain. Now
passed through rather than re-derived.

**Real, not hypothetical — measured through the actual `ingest()` call,
not `bind_colour()` in isolation.** Bound `(0, 72, 96)` against both real
palette JSONs: `ramps=None` and explicit `ramps=cozy_ghibli` both land it
on `neutral-2` (dE 0.065, confirming the default is unchanged); explicit
`ramps=snes_rpg` lands the identical colour on `sky-2` (dE 0.007) — a
different ramp identity, and both bindings sit well inside the 0.16 bind
tolerance, so neither is an edge-of-tolerance replacement being mistaken
for a real divergence. A broader 24-step RGB grid scan found 266 colours
where `cozy_ghibli` and `snes_rpg` disagree on the nearest ramp; the
reported pair was chosen because both sides bind cleanly.

**Regression, checked by stash, not by inspection.** Captured `ingest()`'s
full output — geometry, verts, faces, vcolors, and report, across both the
MTL/rebind path (the same adversarial Y-up/scaled/offset/renamed-material
round trip `check_transform` uses) and the vertex-colour path, plus the
three self-tests — with no `ramps` argument, the only calling convention
that exists anywhere in the repo today. Ran it against the working tree,
`git stash` to the pre-change code, ran it again, `git stash pop` to
restore the fix: the two JSON snapshots are byte-identical.

---

**Landed (PR #54): `review_queue.py` gets `--style`, the audit-tool gap
PR #31 didn't cover.** PR #31 audited `art_review.py` for the accepted-
but-ignored `--style` bug and found it clean, but scoped itself to that
one file. `review_queue.py` -- the batch contact-sheet tool that sits one
layer above `art_review.py`, calling its `load_palette()`/`review()`
directly -- had the actual bug: `build()` called `load_palette()` bare, no
argument, always resolving `cozy_ghibli`'s palette regardless of what
style the matched files were rendered under, and `main()`'s argparse had
no `--style` at all.

Fix mirrors `art_review.py`'s own convention: `build()` gained a
`style: str = DEFAULT_STYLE` parameter resolved via
`load_palette(load_style(style).palette_path)`, and `main()`'s `build`
subcommand gained `--style NAME` (default `cozy_ghibli`). `build()` takes
arbitrary glob patterns, which could in principle span more than one
style's output in one invocation -- kept to one `--style` per invocation
rather than per-file inference, matching how every producer this session
added the flag, and documented inline as the caller's responsibility to
avoid (one style-consistent glob per run). Checked `review()`'s other
internal logic in full: nothing beyond `by_rgb`/`ramps`/`entries` as
passed in, no separate hardcoded assumption to fix; `check_direction_set()`
(the key-light-drift cross-sprite check) works on raw OKLab lightness from
pixel RGB, not the palette, so it needed no change.

Verified with real renders (`furnish.py --only plant_succulent`, both
styles, GPU-free), not just that it runs: reviewing the `snes_rpg` render
under the OLD bare-`load_palette()` behaviour produced 8/8 false
off-palette blockers; under `--style snes_rpg` it's 6/8 auto-clean, 0
blockers. The key-light-drift check also reads genuinely differently by
style on the same geometry (cozy_ghibli "consistent" 3.4x5.5px vs.
snes_rpg "drifts" 3.1x6.9px). Regression check: `verdicts.jsonl` and
`sheet.png` for the same default-style input, no `--style` flag, are
byte-identical before and after (stash-based before/after).

---

**Landed (PR #55, stacked on #50): `manifest.py`'s `check_ui` finally reads
the active `--style`, closing the one gap PR #24 explicitly left alone.**
PR #24 fixed every other bare `load_palette()` in this file but named
`check_ui`'s hardcoded `ui_dir = ROOT / "out" / "ui"` and `load_palette()`
as "a different, larger, genuinely not-yet-started gap, not a bug in this
one" — its stated reason being that `ui_forge.py`/`ui_chrome.py` "never
claimed to build per-style in the first place." That prerequisite is gone:
PR #25 gave `ui_chrome.py` `--style`, PR #36 gave `ui_forge.py` the same.
This is that deferred follow-up, now that there is real per-style content
for `check_ui` to find.

**Two directories, not one, because the two producers never agreed on a
convention.** `ui_forge.py` nests a non-default style under the default's
own directory, matching `furnish.py` — `out/ui/<style>/`. `ui_chrome.py`
uses a sibling-with-suffix, matching `tileset.py` — `out/ui_<style>/`.
`package_godot.py`'s `style_paths()` (PR #47/#48) already documented this
exact split for its own purposes and made the same call this PR makes —
match each producer's own real convention rather than invent a third — but
it only threads the suffix half through its single `ui_dir` field, so it
silently stages nothing from `ui_forge.py`'s nested directory for a
non-default style. That's a real, separate gap in `package_godot.py`, not
introduced or fixed here — noted below, not chased, because fixing it means
touching a different, working, shipped file for a problem this PR's scope
is auditing, not staging.

`check_ui` now resolves both directories from the active `style.Style` (the
same object `check()` already loads, threaded through rather than
re-resolved) and checks a declared id against both — a CHROME id
(`ui_dialogue_frame`, `ui_nameplate`, `ui_upgrade_frame`, `ui_ticket`,
`ui_star_rating`, `ui_star_rating_empty`, `ui_coin`) is found in the suffix
directory, a forge-only id (the drink icons, the clock, the heart) in the
nested one — rather than checking one and silently missing the other's
output. For the default style both conventions collapse to the same
`out/ui/`, unchanged from before. `ui_font` stays pointed at
`out/ui/font/font.json` regardless of style: `bitmap_font.py` has no
`--style` flag at all yet, a separate not-yet-started gap of its own, the
same category `check_ui` itself was in before this PR.

**Verified against real on-disk assets, not just by code reading.** Ran
`tools/ui_chrome.py --style snes_rpg` for real (purely procedural, no GPU) —
7/7 chrome pieces built to `out/ui_snes_rpg/`. GPU turned out to be
available in this environment, so `tools/ui_forge.py --only
ui_coin,ui_icon_espresso --retry-seeds 0 --style snes_rpg` was also run for
real, not skipped: `ui_icon_espresso` built to `out/ui/snes_rpg/`,
`ui_coin` gated on the same documented speckle ceiling PR #36 already
recorded for it. `manifest.py --check --style snes_rpg` against that real
on-disk state, before this fix, reported the exact same wrong thing as
`--check` with no `--style` at all — "15 declared but not built," including
`ui_icon_espresso` even though it was sitting on disk, because the old code
never looked anywhere but the hardcoded default `out/ui/`. After the fix,
the same command correctly reports "7 declared but not built" (exactly the
seven ids genuinely not yet built for `snes_rpg`: the five remaining
drinks, the clock, the heart) and zero off-palette or isolated-pixel
warnings for the eight it found — confirming both that it now locates
files in either real directory and that it audits them against
`snes_rpg`'s actual palette rather than `cozy_ghibli`'s.

**Regression, checked the way PR #36/#52 did it: real output, not
assumption.** `manifest.py --check` (no `--style`) captured in full before
and after this change, same on-disk state both times (git-stash-based
before/after, not a fresh clone, since `out/ui/` already existed from the
`snes_rpg` run above by the time of capture) — **byte-identical**,
including the pre-existing `ui: 15 declared but not built` warning and
`ui_font` warning, neither of which this PR touches the wording of for the
default style.

---

**Landed (PR #56): `--style` for `tools/bitmap_font.py`, the same
accepted-but-ignored / never-added bug fixed across `factory.py` (PR #52),
`ingest.py` (PR #53) and `review_queue.py` (PR #54).** `bitmap_font.py` is
the repo's actual in-game bitmap font renderer, not a dev preview tool
(its own module docstring: "No font, no bitmap glyph set, nothing that
renders a word in the palette... this is that") — and it had FOUR bare
`load_palette()` calls (`render_line()`, `atlas()`, `load_ramps()`,
`demo()`), every one always resolving `cozy_ghibli`, plus a `main()`
argparse with no `--style` flag at all to begin with.

All four now resolve `load_palette(load_style(style).palette_path)`, with
`style` threaded as a parameter down from `main()`'s new `--style NAME`
(default `cozy_ghibli`) through `render_line`, `atlas`, `load_ramps`,
`check_render` (which calls `load_ramps` for its off-palette audit) and
`demo`. Same idiom every other producer in this sweep uses; no new palette
resolution path invented.

**Output path, verified rather than guessed.** `--out` defaulted to a fixed
`out/ui/font`; it now defaults to `out/ui/font` for `cozy_ghibli` or
`out/ui/<style>/font` for anything else, still overridable explicitly. That
nests the style directory the way `ui_forge.py` does for its own
`out/ui/<style>/` — not `ui_chrome.py`'s sibling-suffix `out/ui_<style>`
— because `bitmap_font.py`'s default already lives *under* `out/ui/`, same
as `ui_forge.py`'s and unlike `ui_chrome.py`'s bare `out/ui`. Confirmed by
actually running it: `--style snes_rpg --sample "Flat White  $4.50"` (no
`--out`) wrote to `out/ui/snes_rpg/font/font_sample.png`, and
`git check-ignore -v` confirms both that path and the default
`out/ui/font/font_sample.png` are covered by the existing blanket `out/`
`.gitignore` line — no new entry needed.

**Real palette difference, not just "didn't crash."** Rendered the same
sample string under both styles and diffed the actual ink RGB values
written to the PNGs: `cozy_ghibli` writes `(35,35,44)`/`(63,63,75)`
(neutral charcoal), `snes_rpg` writes `(9,18,31)`/`(43,54,71)` (navy) — a
real, different palette resolved per style rather than the same bytes
under a new flag. Side-by-side proof at
`proof/bitmap_font_style_compare_sample.png`.

**Regression check.** Same sample string, same `--cap`/`--weight`, no
`--style` flag: sha256 of `font_sample.png` is byte-identical before and
after this change
(`fe89984c22d0bd6134eaa1eb0b3fd48ac8c8b35f60c5377cbf9478ff0fa67103`) —
a pure threading change, zero behaviour change for the shipped style.

`bitmap_font.py --check` was left untouched — it sweeps geometry (glyph
collisions, counters, bounds, pairwise ink contact) and never touches a
palette, so there is no bare `load_palette()` in that path to fix and no
style-dependent behaviour to verify there.

---

**Landed (PR #57, stacked on #50): `package_godot.py` stages a non-default
style's UI from BOTH real directories, PR #55's own flagged follow-up.**
PR #55 (`manifest.py`'s `check_ui`, audit side) found and fixed the fact that
`ui_forge.py` and `ui_chrome.py` picked two different per-style conventions
for `out/ui/`, and explicitly named the staging side of the identical
problem as "a real, separate gap... noted in `NEXT.md`" rather than fixing
it there, since that meant touching a different, working file. This is that.

**The split, unchanged from PR #55's finding, now also covers the font.**
`style_paths()`'s single `ui_dir` field could only ever resolve to
`ui_chrome.py`'s sibling-suffix convention (`out/ui_<style>/`), so
`stage()` was staging chrome pieces for a non-default style and silently
missing `ui_forge.py`'s icons entirely (`out/ui/<style>/`) — and, it turns
out, `bitmap_font.py`'s font too, one level under that same nested
directory (`out/ui/<style>/font`), which is the convention the open,
unmerged `bitmap-font-style` branch (PR #56) lands (read directly from
that branch, not guessed — `tools/bitmap_font.py` on this branch still has
no `--style` flag at all, a separate, not-yet-started gap noted below).
`style_paths()` now returns `ui_forge_dir`/`ui_chrome_dir` instead of one
`ui_dir`; `stage_ui()` merges both (de-duplicated via `dict.fromkeys`, so
the default style — where they're literally the same `Path` — collapses
to the exact single-directory behaviour it always had); `stage_font()`
takes `ui_forge_dir` specifically, matching the nested convention its
source actually uses.

**A real bug, measured before and after, not assumed fixed.** Real content
already existed on disk in this environment from prior work: `ui_chrome.py
--style snes_rpg` was re-run for real here too (GPU-free, 7/7 chrome pieces
confirmed fresh to `out/ui_snes_rpg/`). `bitmap_font.py --style snes_rpg`
cannot be run for real on this branch — confirmed by trying it: `error:
unrecognized arguments: --style snes_rpg` — so `bitmap_font.py` (no
`--style`) was run for real instead (`out/ui/font/`, 4 real sheets + real
`font.json`) and that real output copied to `out/ui/snes_rpg/font/`, the
exact path a `--style`-aware `bitmap_font.py` will write to, to exercise
`stage_font()`'s nested-lookup against real bytes rather than a fabricated
fixture. `ui_forge.py --style snes_rpg` was NOT run fresh — GPU check at
the time (`torch.cuda.is_available()` → True, but `nvidia-smi` showing
~46% of this 8 GB card's VRAM already held by other running applications)
judged the GPU not clearly free for a new SDXL job; verified instead by
code inspection of its `--style` path logic (`ui_dir = ROOT / "out" / "ui"
/ args.style` for non-default, matching `style_paths()`'s `ui_forge_dir`
exactly) plus the real `out/ui/snes_rpg/ui_icon_espresso.png` already
sitting on disk from an earlier genuine run in this environment.

Before the fix, `package_godot.stage("snes_rpg")` staged **7 UI pieces (7
drawn, 0 generated)** and no `font` key at all — every chrome piece, zero
icons, zero font, exactly PR #55's finding reproduced on the staging side.
After the fix, the same call stages **8 UI pieces (7 drawn, 1 generated)**
— `ui_icon_espresso` now present, `source: generated` — and a real `font`
key with all 4 shipped cap heights. `godot_export/project_snes_rpg/assets/`
gained `ui_icon_espresso.png` and a whole `font/` subtree that didn't exist
in the pre-fix output at all.

**Missing-directory degrade, checked directly, not inferred.** Called
`stage_ui()`/`stage_font()` with paths that don't exist on disk (both
missing, and one-of-two missing) — every case returns `{}` cleanly, no
exception, matching the "stage nothing, don't fail" contract every other
stager here already has for a style nobody's run a producer against yet.

**Regression, the default style.** `package_godot.stage("cozy_ghibli")`
before and after: identical `summarise()` output, identical file list under
`assets/`, and sha256-identical on every file including
`build_manifest.json` — zero behaviour change, because `ui_forge_dir` and
`ui_chrome_dir` both resolve to the same `out/ui/` `Path` for the default
style, `dict.fromkeys` collapses them to one entry, and `stage_ui()`/
`stage_font()` run the exact single-directory path they always did.

**Scope boundary, stated rather than assumed away.** `bitmap_font.py`
itself still has no `--style` flag on this branch — that's PR #56, open
and unmerged, not touched here. This PR only makes `package_godot.py`
correctly consume whichever of the two real directories a style's UI
output actually lands in; it does not change what any of the three
producers write.

---

**Landed (PR #51, stacked on #50): `palette_swap.py`'s audit side gets the
same `--style` treatment its own palette math already had.** Same bug class
as PR #24/#25/#29/#36's "`--style` accepted but the actual scan stays
hardcoded to the default" — this time in `SOURCES`, a flat module constant
pointed at `cozy_ghibli`'s own four output directories and read, unchanged,
by all four of `library_colours()`, `swap()` (both loops) and
`sample_assets()`, even though `main()` already threaded `args.style` through
`load_bible()`.

**The conventions, verified by running each producer against this checkout,
not assumed.** `out/` was empty here, so real content was generated for both
styles (`furnish.py`, `tileset.py`, `ui_chrome.py`, `animate.py`, all
CPU-only; `ui_forge.py` is GPU-bound and confirmed instead by reading its
`ui_dir = (UI_DIR if args.style == DEFAULT_STYLE else ROOT / "out" / "ui" /
args.style)` line directly). Four different conventions, from four
independent producers: `furnish.py` props nest a non-default style
UNDER the default's own directory (`out/sprites/<style>/`); `tileset.py`
tiles and `ui_chrome.py` UI use a sibling-with-suffix
(`out/tiles_<style>/`, `out/ui_<style>/`); `ui_forge.py` UI nests, the same
shape as `furnish.py` but a THIRD, independent convention from
`ui_chrome.py`'s own UI output; `animate.py` anim sheets use a fourth shape,
`sprites/` (repo root) for the default and `out/sprites_<style>/` for
anything else. New `sources_for(style)` resolves all of it, returning both
UI roots for a non-default style since two producers write two different
places for the same category.

**A second, real bug the nested convention causes, caught by running it, not
guessed at.** `out/sprites/<style>/` and `out/ui/<style>/` sit one level
INSIDE the exact directories the *default* style's own scan walks, so the
old flat `SOURCES` — and a naive per-style rewrite that just swapped in new
paths without addressing this — would still have the default style's
`rglob` walk straight into another style's nested output and report it as
stray. Measured before the fix: a real `out/sprites/snes_rpg/` from
`furnish.py --style snes_rpg` turned up as 10 "unmapped" colours under
`palette_swap.py --check --style cozy_ghibli`. `sources_for()` now hands the
default style's `props`/`ui` roots a `skip` set of every other style's
nested subdirectory, and the new `_pngs()` helper (replacing every bare
`root.rglob("*.png")`) respects it.

**Check results, both directions, real content.** `--check --style
cozy_ghibli`: 39 PNGs, 32 colours, all mapped, all 4 variant tables
injective, all samples round-trip — zero cross-contamination from the
`snes_rpg` content sitting in nested sibling directories. `sources_for()`
and `library_colours()` confirmed directly for `snes_rpg`: resolves to its
own nested props dir, suffix UI dir, (not-yet-existing, gracefully skipped)
nested UI dir, suffix tiles dir, suffix anim dir — 31 PNGs, 21 colours, all
of them within `snes_rpg`'s own forged base palette, zero leaked from
`cozy_ghibli`. `palette_swap.py --check --style snes_rpg`'s full CLI path
crashes on `variants[0]` — `styles/snes_rpg/bible.yaml` declares `variants:
{}` — but this is the same pre-existing, unrelated gap the sibling
`snes-palette-variants` branch already found and is fixing there; not this
PR's scope, and not touched here.

**Regression.** File count dropped from the old code's 55 (`cozy_ghibli`
scan bug-inflated by the leaked `snes_rpg` nested props) to the new code's
39 real `cozy_ghibli` files — a drop that looks alarming out of context but
is the fix working, not an under-scan: both counts are small because this
checkout's `out/` started empty and only a two-prop/one-character subset was
generated for real per style, not because anything the default style
actually owns stopped being scanned.
**Landed (PR #41, stacked on #39 and #40): the focal-detail check is now
resolution-confirmed, not resolution-invariant.** Closes `ART_CRITIQUE.md`'s
longest-open "Still open" item -- the focal reading falling with render
resolution -- by re-measuring it end to end instead of trusting the note.
Write-up: `ART_CRITIQUE.md`, "Focal detail: resolution-confirmed, not
resolution-invariant".

Two findings, then a fix:

- **Contrast healed on its own.** Swept 160-480 across the suite check's own
  four-room sample plus the reference room: every reading now clears the
  0.030 floor by at least 0.047, most by 3-6x. The steep collapse the
  original bullet measured (down to +0.014, nearly crossing) is gone -- an
  unrelated string of composition fixes (hull-clipped focal region, wall
  shelf/sign, back-counter height) closed it as a side effect, never
  re-verified until now.
- **The same problem re-appeared on detail** (edge density, added after that
  bullet was written). Every room's detail lead shrinks with resolution,
  the reference room included. Live and current: `build_plan.py
  --focal-scan 12` read 2 of 12 fail at 320, 1 of 12 at 480 -- plan 1
  flipped from FAIL to pass with zero content change. `manifest.py
  --check`'s own `check_focal_contrast()` (the fast gate, not just the deep
  scan) was already carrying this exact case as an accepted failure, named
  directly in this file's own Gates section.

A ratio reformulation of the detail lead -- `(di-do)/(di+do)` instead of the
raw difference -- was measured and rejected: it shrinks the drift for
healthy rooms but is proven, algebraically and numerically, unable to change
a single verdict at a floor fixed at exactly 0 (a sign-preserving
transform). Root cause is the renderer, not the statistic -- `shade_toon`'s
dither and `mesh.py`'s surface grain are fixed-real-world-size
perturbations that `downsample_modal` only resolves once a render target's
per-pixel world footprint shrinks below their width, which happens at a
different target for the counter than for the busy periphery. A truly
resolution-invariant version would grade off world-space material samples
instead of raster pixels -- scoped and left, the same way the fifth
topology and the style LoRA were.

**The fix:** `FOCAL_CONFIRM_TARGET = 480` in `tools/build_plan.py`. A room
that fails at the check's own 320 gets one confirming render at the
delivery resolution and is only reported if it fails both. Passing rooms
(10 of 12) never pay for the second render.

Verified both gates, live:

    .venv/Scripts/python.exe tools/build_plan.py --focal-scan 12
    -> 1 of 12 fail (8%), 1 rescued by the 480 confirmation (plan 1)

Direct call, before and after: `check_focal_contrast()` (the function
`manifest.py --check` actually runs) reported plan 1's -0.002 detail as a
failure before this change and reports zero messages after. The full
`manifest.py --check` run confirms it end to end: **0 errors, 8 warnings**
(the same 8 pre-existing, unrelated occlusion/declared-but-unbuilt-UI
warnings), where it used to be 1 error on this exact case. Plan 10 -- the
one real defect in the sample, negative at every resolution from 240
through 480 -- still fires in both the scan and a direct
`check_focal_contrast(seed=10, n=1)` call. Proof: `proof/focal_plan1_320.png`
vs `proof/focal_plan1_480.png` (the flip, same room, same seed); `proof/
focal_plan10_320.png` vs `proof/focal_plan10_480.png` (still failing, both
resolutions).

**Left honestly incomplete:** this is confirmation at two specific
resolutions, not invariance at any resolution -- a defect visible only at
some third target would still slip through. That is the practical claim the
shipped game needs (the checked and the delivered resolution now agree), not
the abstract one the original bullet asked for.

---

**Landed (PR #44, stacked on #39-#43): `build_plan.py`'s roster generation
was still hardcoded to `cozy_ghibli`, the same `--style`-ignored-by-a-check
bug found in `character.py` (PR #23), `manifest.py`/`portrait.py` (PR #24)
and `art_review.py` (PR #31) -- one more call site the sweep had not
reached.** `main()` correctly built `ramps` from `--style` and threaded it
into the final `render()` call, but `build(plan)` runs BEFORE that render
call and is what actually creates the people: `build()` -> `_people()` ->
`C.generate_roster(n, seed)`, called with no third argument, so it fell
through to `generate_roster`'s own default, `ramps or _palette()`, which
hardcodes `load_palette()` -- `cozy_ghibli`, unconditionally. Every barista,
queue customer and seated customer in a `--style snes_rpg` room was
generated against `cozy_ghibli`'s colours: `check_contrast`,
`check_palette_spread` and `check_waistline` all ran on the wrong palette,
same as PR #23 found for `character.py`'s own `--check` path, just reached
through a different producer.

Fixed by threading `ramps` one hop further than PR #21's own `--style`
wiring did: `build(plan, ramps=None)` -> `_people(..., ramps=None)` ->
`C.generate_roster(n, seed, ramps)`, and `main()`'s `ramps = load_palette(...)`
block moved earlier, above the `build()` call it now feeds, rather than
staying where it only fed `render()`. Default `ramps=None` preserved at
every hop, so nothing about `cozy_ghibli` (or any caller that omits
`--style`) changes -- `check_built_rooms`, `check_focal_contrast` and
`_focal_scan` all call `build(plan)` with no ramps and are untouched by
construction, not by re-verification alone.

Audited every other `C.generate_roster(`/`C.generate_spec(` call site in the
repo for the same gap: `animate.py`, `manifest.py` and
`preview_characters.py` already pass `ramps` explicitly. `build_plan.py`'s
`_people()` was the only silent fallback left.

Verified both directions:

- **The bug is real and the fix changes real output.** `build_plan.py
  --style snes_rpg` rendered before and after the fix from the identical
  plan seed: mesh vertex/triangle counts differ (47214/19994 before,
  46974/19898 after) and multiple characters' garment/hair materials
  visibly change colour -- a queue customer's shirt goes from cream to
  magenta, a counter-side figure's trousers from grey to cream-and-green.
  Proof: `proof/people_style_fix_before_after_snes_rpg.png` (full room) and
  `proof/people_style_fix_before_after_snes_rpg_zoom.png` (3x crop on the
  diff region). One honest side effect, disclosed rather than hidden: the
  regenerated room's focal contrast reads `+0.000` ("DOES NOT lead the eye")
  against the `+0.078` recorded in `styles/snes_rpg/lock.json`'s existing
  `build_plan.py:proof/plan_room_snes_rpg.png` verdict -- a different,
  correctly-styled roster standing at the counter reads differently under
  `snes_rpg`'s harder value steps. The tracked proof PNG and its lock entry
  were deliberately left untouched here (re-judging a room is
  `style_approve.py`'s job, not a threading fix's), so that comparison is
  reported, not silently shipped as a changed tracked asset.
- **`cozy_ghibli` (the default) is byte-identical.** `build_plan.py --seed 3`
  (no `--style`) rendered before and after: identical MD5. `manifest.py
  --check` (1 error, 8 warnings, the known plan-1 wall-run case) and
  `build_plan.py --focal-scan 12` (2 of 12 fail, plans 1 and 10) both
  produced byte-identical stdout before and after, confirming this is a
  pure threading fix with zero behaviour change for the shipped style.

**Landed (`style-relock`, stacked on the #52-#62 chain): both style packs
re-locked for real after `279d1a8` (`wall_trim`/`wall_trim_shadow` added to
`style_bible.yaml`) changed `cozy_ghibli`'s bible hash out from under every
existing approval without anyone re-running the gates that produced them.
`style_approve.py --style cozy_ghibli` and `--style snes_rpg` both reported
NOT approved going in; `lockfile.py --status` showed every `cozy_ghibli`
entry STALE. Every one of the three requirements was genuinely re-run
against the CURRENT bible, not rubber-stamped:

- `character.py --style cozy_ghibli --lock`: 0 blockers, approved for real.
- `organic_rig.py --style snes_rpg --lock`: snes_rpg's `rig.primitive` is
  still `cylinder_sphere`, so `character.py` (box/prism only) is not this
  style's real evidence — `organic_rig.py` is, per `style_approve.py`'s own
  `REQUIRED_PRODUCERS_ANY_OF` reasoning. Passed for real, silhouette
  stability holds.
- `palette_forge.py --style cozy_ghibli --lock`: all constraints pass,
  output byte-identical to before (`wall_trim` didn't touch the `palette:`
  block). `snes_rpg`'s own `palette_forge.py` entry was already approved at
  the current hash — untouched, nothing to re-run.
- `llm:focal_hierarchy`, judged for real against freshly re-rendered scenes
  (not the stale pre-`279d1a8` PNGs sitting in `proof/`, regenerated first):
  `render_room.py --style cozy_ghibli --target 900 --out proof/shop_big.png`
  (PASS, same known counter-orientation softness as before, 0.04 cost,
  +0.119 measured this run), `render_room.py --style snes_rpg` (PASS,
  +0.166, the strongest focal contrast recorded for any scene in this repo),
  `build_plan.py --style snes_rpg` (PASS, weaker at +0.078 — the long-run
  counter layout, recorded honestly as secondary evidence rather than
  dropped). `snes_rpg`'s two proof PNGs came back byte-identical to their
  pre-relock versions — its bible didn't pick up `wall_trim` from `279d1a8`
  (already had its own), so nothing visually changed there; only
  `shop_big.png` differs (thin trim band now visible on the walls).
  `portrait.py --check --lock --style cozy_ghibli` also re-verified clean
  while at it, closing the one stale entry `character.py` alone didn't need
  but left lying around.

`style_approve.py` now reports **APPROVED** for both styles. Everything CPU
procedural work as expected — no GPU contention, confirmed rather than
assumed. Only `lock.json`/`styles/snes_rpg/lock.json` and the two
freshly-rendered proof PNGs changed; no `bible.yaml` content touched.

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
.venv/Scripts/python.exe tools/manifest.py --check            # 26 checks, takes ~4 min, clean
.venv/Scripts/python.exe tools/build_plan.py --focal-scan 12  # slower, 1 of 12 currently fails
```

Both used to fail on the same underlying story: the detail floor sits at
exactly 0.0, and its per-dressing-state noise (0.075-0.145 at n=50) runs
3-6x a shelf's own mean effect (~0.02-0.03) -- closed out at scale as a
population-rate check rather than tracked as an open margin
(`ART_CRITIQUE.md`, "The detail floor's bracket, closed: the noise is bigger
than the signal", PR #42). As of the focal-resolution-confirmation pass
(`ART_CRITIQUE.md`, "Focal detail: resolution-confirmed, not
resolution-invariant", PR #41):

- `manifest.py --check`'s `check_focal_contrast` no longer fails on plan 1.
  It used to (-0.002, from the RNG-unification pass) -- that failure turned
  out to be resolution-dependent (it passes at 480, the delivery
  resolution), and the check now confirms a 320 failure against a 480
  render before reporting it, so the resolution-only flip no longer counts.
- `build_plan.py --focal-scan 12` still fails plan 10, correctly -- a real,
  accepted defect, negative at every resolution from 240 through 480 (not
  -0.002 as this file previously recorded; that number was a stale
  transcription -- the measured margin is -0.011 at 320, -0.013 at 480).

**Correction, found while sorting merge conflicts across the open PR stack
(not yet root-caused, flagging rather than guessing):** the "clean" claim
above holds for PR #41 checked against its own narrower base, but running
`manifest.py --check` at the tip of the fully-combined stack through PR #43
(which also includes PR #39's galley/multi-counter topology) is **not**
clean -- it currently reports 3 errors: plan 1 (L run) fails
`check_focal_contrast`'s detail floor by -0.001, and plan 8 (galley) fails
it twice, -0.012 against the centre floor and -0.019 against the detail
floor. This looks like a real interaction between the galley topology's
known focal-contrast weakness (see `NEXT.md`'s galley entry above) and the
now-razor-thin detail floor (PR #42, left at exactly 0.0) rather than a bug
in either PR alone, but that is a hypothesis, not a measurement -- needs its
own follow-up pass once this stack is merged, not fixed blind here.

Don't treat a *new* failure in either run as equally acceptable without
checking whether it's plan 10 or something else.

Stage-8 review on generated sprites:

```
.venv/Scripts/python.exe tools/review_queue.py build "out/sprites/*_dir*.png"
```

---

**Landed (PR #42, stacked on #39, #40, #41): the detail floor's "Still open"
bracket, closed.** `ART_CRITIQUE.md` had carried `MIN_FOCAL_DETAIL`'s bracket
as "0.010 wide" since the wall-shelf/sign fix, never revisited even after two
later, unrelated passes (`leafy_plant` unified onto `_mix`; the L-run-corner
dilution check) each independently brushed against the same margin without
closing the bullet out. Re-measured at n=50 (`proof/detail_floor_scan50.txt`)
instead of the original 12: the rate holds (14% vs B4's 12.5% on 40 plans)
but the bracket does not — weakest fail/pass gap is 0.002-0.004, not 0.010,
and two rooms sharing the *identical* back-wall dressing state (sign, two
menus, zero shelves) land 0.072 apart (plan 10 at -0.011, plan 22 at +0.061;
proof: `proof/detail_floor_plan10_fail.png`, `proof/
detail_floor_plan22_pass.png`, both confirmed at the shipped 480px target
too). Grouped by dressing state, the per-state spread (0.075-0.145) runs
3-6x the shelf's own mean effect (~0.02-0.03) — a signal-to-noise ratio no
single threshold between -0.017 and +0.061 can resolve without either
punishing peninsulas/islands for a defect they're structurally incapable of
(no wall to dress) or losing rooms with the actual defect.

**Verdict: left at 0.0**, same constant, correction is to the claim rather
than the number — recorded as a population-rate check (~1 in 8-9 wall/L
runs), not a per-room verdict; a lone borderline failure is not proof that
specific room is under-dressed. `tools/build_plan.py`'s `MIN_FOCAL_DETAIL`
comment and `ART_CRITIQUE.md`'s "Still open" list are both updated in place
rather than left to drift further. No logic changed —
`manifest.py --check` (1 error, 8 warnings) and `build_plan.py --focal-scan
12` (2 of 12 fail: plan 1 -0.002, plan 10 -0.011) are byte-for-byte the same
before and after this branch's diff.

---

## Tier A — CLOSED (historical record, not open work)

> **These four Tier sections are CLOSED.** Every item below (A1, B1, C1, C2,
> D1, B2) was completed or deliberately resolved, and each one's outcome is
> in the status list further up this file and written up in full in
> `ART_CRITIQUE.md`. The task text is preserved verbatim as a historical
> record, not an active backlog. Do not reopen these items from their wording.

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

## Tier B — CLOSED (historical record, not open work)

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

## Tier C — CLOSED (historical record, not open work)

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

## Tier D — CLOSED (historical record, not open work)

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
