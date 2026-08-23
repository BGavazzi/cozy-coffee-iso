# Next

**All 14 tasks below have been executed.** Each has a write-up in
`ART_CRITIQUE.md` (search for the task's subject, e.g. "the concept fitness
gate" for C1). One-line status per task:

- A1 batch driver — built (`tools/factory.py`).
- A2 manifest overwrite — fixed, merges by asset.
- A3 stage 7 world facts — fixed, `mesh_geometry()` feeds the manifest.
- B1 `--smooth` no-op — fixed, `compute_vertex_normals()`.
- B2 albedo check not gated — fixed, `check_albedo_regression()` wired in.
- B3 spread floor never fired — proven non-redundant, kept.
- B4 detail floor bracket — widened to 40 plans; margin narrowed, not
  widened; floor kept, L-run concentration recorded as unexplained.
- B5 counter orientation — measured at 600 plans (66% worse-lit); left open,
  cause still untraced.
- C1 wider subject set — 31 subjects run; `MIN_FILL` bracketed, two
  false-rejection classes found in `MAX_SOFT_ALPHA` (thin edges, glass).
- C2 wider speckle bracket — 22 lifted objects measured; floor confirmed,
  not moved.
- C3 basket crescent frames — diagnosed as stage 2 (single-view
  reconstruction), not a bug.
- C4 auto-uprighting — search found to be search-range-sensitive on the same
  object; left undone, more firmly than before.
- D1 UniRig CUDA check — same `nvcc`/MSVC blocker as TRELLIS 2.
- D2 style LoRA — scoped down to a before-baseline measurement (mean 0.111,
  worst 0.306 of albedo L); training one is future work.
- D3 assetlib parameter coverage — instrumented all `_mix`-based generators;
  no dead draws found across 53 sites.
- D4 fifth topology — scoped, not built; double-run/galley named as the
  candidate.

Kept below as a record of what was asked, not as an open queue.

---

A worklist written to be picked up cold. Every task states where the code is,
what "done" means, and what to measure. Tasks are ordered within each tier by
value; tiers are ordered by how much they unblock.

Read `ART_CRITIQUE.md` before touching anything that produces art — the
"Still open" section at the end is the live list of known weaknesses, and most
of these tasks are drawn from it.

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

**Windows gotchas that have cost time before**

- Large bash heredocs mangle content. Write a patch script into the scratchpad
  and run it with the venv python, or use the Write tool.
- Background commands piped through `grep`/`tail` buffer their output. Use
  `python -u` redirected to a file.
- Foreground `sleep` is blocked. Poll with `until <check>; do sleep N; done`.

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
5. **Branch and PR, never commit to the default branch.**

**Gates — both must be clean before any commit**

```
.venv/Scripts/python.exe tools/manifest.py --check            # 26 checks, takes ~4 min
.venv/Scripts/python.exe tools/build_plan.py --focal-scan 12  # slower, 0 of 12 must fail
```

Stage-8 review on generated sprites:

```
.venv/Scripts/python.exe tools/review_queue.py build "out/sprites/*_dir*.png"
```

---

## Tier A — the factory has no front door

Everything works and nothing is wired together. This is the biggest gap
between what the repo claims and what it does.

### A1. A batch driver: subject list in, reviewed sprites out

Right now producing one prop is five manual commands, and the state between
them is undocumented. There is no way to say "make me these forty things."

Build `tools/factory.py` taking a YAML or JSON subject list:

```yaml
- name: teapot
  prompt: a ceramic teapot
  height: 0.28
- name: stool
  prompt: a small wooden stool
  height: 0.45
```

and running concept → lift → ingest → render → review for each, skipping any
stage whose output already exists (so a failed run resumes), and writing a
single summary of what passed, what was gated at which stage, and why.

- **Files:** new `tools/factory.py`; calls into `concept.py`, `lift.py`,
  `ingest.py`, `render_batch.py`, `review_queue.py`.
- **Load the TripoSR model once** for the whole batch, not per subject —
  `lift.lift()` already accepts a `model=` argument for this.
- **Acceptance:** `factory.py subjects.yaml` produces sprites and a report for
  a ten-subject list without manual intervention, and re-running it is a no-op.
- **[GPU]**

### A2. `manifest.json` is overwritten by every render

`render_batch.py` writes `out/sprites/manifest.json` fresh each run, so after
rendering teapot, basket and kettle the file describes only the kettle.
Verified: 8 entries, one asset.

- **File:** `tools/render_batch.py:142`.
- Merge by asset name instead of overwriting, or have A1 own the manifest and
  make `render_batch` return its rows.
- **Acceptance:** three consecutive renders leave 24 rows covering 3 assets.

### A3. Stage 7 is half-built

The sprite manifest carries `bbox`, `pivot` and `coverage` in pixels. It does
not carry the world-space facts a game needs: footprint in tiles, height,
whether the asset is walkable, its anchor in tile coordinates. `ingest()`
already computes most of this into its `geometry` report and then throws it
away.

- **Files:** `tools/ingest.py` (`ingest` returns `report["geometry"]`),
  `tools/render_batch.py`.
- **Acceptance:** the manifest for a lifted prop states footprint and height in
  tile units, and those numbers match `assets.yaml` conventions for an
  equivalent authored prop.

---

## Tier B — known defects, each with a measurement waiting

### B1. `--smooth` is a silent no-op on every lifted mesh

`rasterize` only interpolates normals when `mesh.normals` is populated
(`tools/mesh.py:~560`). TripoSR writes no `vn` lines — verified, zero in
`out/mesh/teapot.obj` — so `render_batch --smooth` changed nothing on all three
lifted props, identical to four decimal places. A flag that silently does
nothing is exactly the class of bug this repo has caught three times already.

Two acceptable fixes, and the choice should be measured not assumed:

- compute area-weighted vertex normals in `ingest.fit()` so `--smooth` works, or
- have `--smooth` report loudly when the mesh has no normals to interpolate.

Prefer the first if smoothing measurably improves any reading; the second if
it does not. Measure with the speckle metric and by eye on the kettle.

- **Acceptance:** either `--smooth` changes output, or it says why it cannot.

### B2. `check_albedo_centre` is not in the gate

It runs inside `ingest()` and its findings land in `report["warnings"]`, which
only the CLI prints. `manifest.py --check` exercises `ingest` through
`check_roundtrip` and `check_transform` on synthetic meshes, so the albedo
check never runs in the suite.

- **Files:** `tools/ingest.py`, `tools/manifest.py:~204`.
- Add a synthetic case: build a mesh with a deliberately under-exposed vertex
  colour field, run it through `ingest`, assert the warning fires; and a
  correctly-lit one, assert silence.
- **Acceptance:** the check is reachable from `manifest.py --check` and
  verified in both directions.

### B3. The mean furniture-spread floor has never fired

`DEFAULT_SPREAD_FLOOR = 0.15` (`tools/art_review.py:462`) has never rejected anything the
closest-pair floor (0.045, properly bracketed) did not also reject. It is
either redundant or set too low to matter. Both are worth knowing.

- Sweep it upward across the twelve-plan scan until it rejects something the
  closest-pair floor does not, and see whether that room is actually bad.
- **Acceptance:** either the floor is re-bracketed against a real defect, or it
  is deleted with the measurement recorded in `ART_CRITIQUE.md`.

### B4. The detail floor's bracket is 0.010 wide

Three measured defects at −0.005 to −0.009 against a weakest good room at
+0.005. It is the tightest floor in the suite and its margin is smaller than
the difference between two adjacent rooms.

- Widen the sample: run `--focal-scan` over 40+ plans instead of 12 and see
  whether the distribution separates or the floor is inside the noise.
- **Acceptance:** a stated bracket over a larger sample, or an honest note that
  the metric cannot support a floor at this resolution.

### B5. Counter orientation costs 0.04 of focal lead

A run whose long face points +y is raked by the key at N·L = −0.116; +x gets
+0.874. Over twelve rooms the two groups do not overlap. Left open because the
reference room is itself a facing-0 run that reads fine, so the orientation is
weak rather than broken.

- Candidate fixes: a fill light, a per-face ambient floor, or biasing the
  floor-plan generator toward +x-facing runs. The first two change every
  rendered pixel in the repo, so measure before touching.
- **Acceptance:** either the gap closes with a cause rather than a knob, or a
  written argument for why facing-0 runs are acceptable as they are.

---

## Tier C — calibration, because most floors rest on three samples

### C1. Widen the stage-1 subject set [GPU]

Four subjects have ever been through `concept.py`; three passed. The fitness
gate's thresholds (`MIN_FILL 0.12`, `MAX_FILL 0.72`, `MAX_SOFT_ALPHA 0.10`,
`MAX_SECOND_BLOB 0.15`) are bracketed by almost nothing.

- Run 25–30 café-appropriate subjects: mugs, chairs, plants, signage, crates,
  pastry cases, lamps, bottles, books, a bicycle.
- Record pass/fail and the reading that decided each.
- **Acceptance:** each of the four thresholds has a stated bracket — a measured
  defect on one side, a weakest known-good on the other — or is loosened with
  the false rejection named. The fern rejected at 12% soft alpha is the first
  case to re-examine: fronds may be a legitimately hard subject rather than a
  bad generation.

### C2. Widen the speckle bracket [GPU]

`MAX_ISOLATED = 0.105` rests on three lifted objects: kettle 0.037–0.057,
teapot 0.066–0.084, basket 0.127–0.163. The authored side is solid (ten props,
eight directions each) but the defect side is one basket.

- Feed C1's output through to sprites and re-measure.
- **Acceptance:** at least six lifted objects on each side of the floor, and a
  re-stated bracket. Expect the floor to move.

### C3. The basket's crescent frames were never diagnosed

In `proof/lifted_props.png`, basket directions 1 and 5 render as flat crescents
while the other six are volumetric. The mesh reports watertight with positive
volume, so this is not obviously a reconstruction hole.

- Determine whether it is a framing artifact, a genuine reconstruction
  collapse, or a rasteriser edge case. Render the raw mesh from those two
  azimuths at high resolution before pixelization to isolate the stage.
- **Acceptance:** the stage is named. If it is the rasteriser, it is a bug
  affecting authored art too and jumps to Tier B.

### C4. Auto-uprighting was measured and left undone

A search over pitch and roll scoring base flatness (lowest 1% of vertices,
z-spread) found the teapot's best at pitch 2° / roll 12°, spread 0.0081 versus
0.0235 at zero. Real but small, and fitting 12° of roll to one teapot's base is
a knob.

- Re-run the search across everything C1 produces. If the correction is
  consistent in sign and magnitude it is a systematic camera offset from stage
  1's "high three-quarter view" prompt and belongs in `ingest.orient()`. If it
  scatters, it is per-object noise and should stay undone.
- **Acceptance:** a table of best pitch/roll across ≥10 objects, and a decision
  with the table as its argument.

---

## Tier D — stages that do not exist yet

### D1. Stage 3, rigging [GPU]

`PIPELINE.md` names UniRig. Only characters need it; props do not rig. Note
that characters are currently analytic meshes with hand-authored clips that
work well, so this stage buys variety in *body shape*, not motion quality —
scope it accordingly before investing.

Check UniRig's dependency list for compiled CUDA extensions first. If it needs
`nvcc` the same way TRELLIS does, it is blocked on the same two admin-level
system installs, and that finding is itself the deliverable.

### D2. Stage 1 has no style LoRA

`PIPELINE.md` specifies "SDXL + style LoRA" and `concept.py` runs base SDXL
with a prompt template. Every lifted prop therefore arrives in a photographic
style that `delight` and the palette bind have to fight.

- A style LoRA matched to the target look would reduce the correction each
  downstream stage applies. Measure the reduction — the bind dE and the albedo
  shift are both direct readings of how far the source is from the house style.
- **Acceptance:** a before/after on worst bind dE and albedo median shift
  across the same subject set.

### D3. Parameter-coverage audit for the asset library

`check_spec_coverage` audits the character generator's dimensions. `assetlib`'s
seeded generators have no equivalent — `check_generator_range` measures
silhouette distance, which is the outcome, not the inputs. The character bug
proved those are different questions: a cast can differ in shirt, trousers,
hair and hat and still be one face repeated.

- The obstacle is that `assetlib` generators do not expose their draws. Either
  return a spec alongside the mesh, or instrument the RNG.
- **Acceptance:** every seeded generator in `assetlib` has each of its
  randomized parameters shown to vary, or the dead ones are fixed.

### D4. More floor-plan topologies

Four exist: wall run, peninsula, L run, island. The focal and detail checks are
calibrated against those four, and three of the four negative detail readings
came from one topology. A fifth would test whether the checks generalise or
were fitted to the sample.

---

## Not tasks — accepted limitations, recorded so they are not rediscovered

- **The far side of a single-view reconstruction cannot be verified by
  machine.** The eight frames are a consistent turnaround of geometry that is
  wrong on the back, so no image-space metric over the direction set can see
  it. A silhouette-consistency check was proposed and discarded for exactly
  this reason: it cannot fail. Stage 9 exists for this.
- **TRELLIS 2 is blocked on this machine**, not rejected. Three CUDA extensions
  need `nvcc` and an MSVC host compiler; the box has the driver and the card
  but no toolkit and no C++ workload. Roughly 10 GB of admin-level installs.
  Revisit only if someone decides to change the workstation.
- **Speckle has no downstream fix.** Colour-field smoothing, interpolated
  normals and supersampling at 2/4/8/12 were all measured and none moved the
  number. The downsample picks a representative sample rather than averaging,
  by design, because averaging colour is what makes cross-ramp contamination
  impossible.
