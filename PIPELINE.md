# Pipeline Architecture

**Goal: an automated factory that generates the sprite set for a 2D game, given
a clear art direction. Humans critique the quality of what it produces.**

The division of labour is the design:

| | owns | why |
|---|---|---|
| **Factory** | generating every sprite, every direction, every frame | volume |
| **Automated tier** | spec conformance — palette, alpha, grid, projection, pivots | cheap, exhaustive, deterministic |
| **Humans** | *does it look good* | not automatable, and the entire point |

Art stops being the constraint once this works. Content becomes the constraint,
which is the intended outcome.

---

## Why generation goes through 3D

Pure 2D diffusion plus post-processing fails three requirements *structurally*:

- **Projection consistency** — models drift a few degrees per generation, and no
  post-process can re-project a 2D sprite to a corrected angle.
- **Direction coherence** — eight independent generations of "the same" chair are
  eight different chairs.
- **Temporal coherence** — at 48–64 px, one pixel of frame-to-frame jitter reads
  as noise.

All three are normally fixed by a human retouching frames. At factory volume
that is precisely the cost being eliminated, so correctness has to be
**structural** — guaranteed by construction, not corrected afterward.

The answer is the Diablo 2 / Fallout / Age of Empires 2 technique: model once,
render deterministically.

```
STAGE 1  concept art     SDXL + style LoRA          [AI]
STAGE 2  mesh            TripoSR (TRELLIS 2 blocked) [AI]
STAGE 3  rig             UniRig (SIGGRAPH '25)      [AI]
STAGE 4  motion          HY-Motion 1.0 / Kimodo     [AI]
STAGE 5  render          orthographic, 8 azimuths   [CODE, deterministic]
STAGE 6  pixelize        ramp-quantize + dither     [CODE, deterministic]
STAGE 7  metadata        pivot/footprint from mesh  [CODE, exact]
STAGE 8  auto-review     spec conformance           [CODE]
STAGE 9  human critique  aesthetic judgement        [HUMAN]
STAGE 10 engine export   Godot SpriteFrames         [CODE, deterministic]
```

| Requirement | 2D approach | 3D intermediate |
|---|---|---|
| 2:1 dimetric projection | drifts | camera matrix, exact (verified to 12 dp) |
| 8 directions consistent | eight objects | one mesh, 8 azimuths |
| Frame-to-frame coherence | jitter | zero by construction |
| Fixed key light | violated | fixed light rig |
| Pivot / footprint | inferred | mesh bbox, exact |

---

## Stage 6 is where "looks rendered" is won or lost

Measured, not asserted. **Quantize the lighting, not the image.**

The naive chain — smooth-shade, average during downsample, snap to nearest
palette colour — fails twice. Averaging manufactures colours the palette does not
contain, and nearest-colour search has no idea what material it is shading. A
cream ceramic cup renders **blue-grey**, because its shadow side lands nearer the
violet `neutral` ramp than its own. That artifact *is* what "shrunk 3D render"
means.

Instead: bind each material to a ramp, map the lambert term to a discrete ramp
*index*, dither only between adjacent steps of that same ramp, and take the modal
rather than mean colour when downsampling.

| | naive | ramp-quantized |
|---|---|---|
| distinct colours | 17 | 10 |
| cross-ramp leak | **157 px (11.8%)** | **0** |
| cross-ramp adjacency | 6.0% | 2.7% |

Contamination is not reduced. It is impossible.

---

## Stages 8 and 9: the critique loop

The factory generates faster than anyone can look, so critique is itself a
throughput problem.

    python tools/render_batch.py                       # generate
    python tools/review_queue.py build "sprites/*.png" # auto-review + contact sheet
    # humans fill verdict + reason in review/verdicts.jsonl
    python tools/review_queue.py stats                 # what to automate next

**Stage 8** rejects spec violations before a human wastes attention on them:
palette membership, 1-bit alpha, pixel-grid alignment, ramp coherence,
silhouette, canvas bleed, plus cross-sprite checks over a whole direction set.

**Stage 9** is a contact sheet with findings already annotated. Humans judge only
what survived, and only on aesthetics.

## Stage 10: engine export

The factory's own output format (loose PNGs + `manifest.json`) is not what a
game engine consumes. `tools/export_godot.py` turns it into real Godot 4
resources:

    python tools/export_godot.py

Three steps, chained because each is a real dependency of the next:

1. `tools/package_godot.py` stages `out/sprites/*.png` + the per-asset world
   facts from `manifest.json` into `godot_export/project/` (gitignored,
   regenerated every run).
2. `godot --headless --import` -- Godot's resource loader refuses to `load()`
   a PNG that has never been through an import pass; this generates the
   `.import` sidecars that make it a real, file-backed `Texture2D`. Skipping
   this and loading raw pixels via `Image.load()` +
   `ImageTexture.create_from_image()` "works", but every `.tres` that
   references the result embeds the pixel data inline instead of a path --
   confirmed empirically: a single 64x64 sprite's `.tres` came out over
   60,000 characters that way, versus ~130 as a proper `[ext_resource]` line.
3. `build_all.gd` reads `build_manifest.json` and builds one `SpriteFrames`
   resource per asset -- 8 `AtlasTexture` frames, indexed by direction (game
   code sets `.frame = direction_index` directly; there's no animation here,
   just 8 fixed poses of a camera-fixed rig). World facts that have no native
   `SpriteFrames` slot (height, footprint, anchor, walkable, and the
   per-direction pivot/bbox/azimuth) ride along as resource metadata,
   readable in GDScript via `get_meta()`.

Output: `godot_export/project/resources/<asset>.tres`, 22 resources / 92KB for
the current library, referencing the staged PNGs by path rather than
duplicating them.

Reference-image ("examples") conditioning in `concept.py` -- the other half
of "prompts and examples in, engine-usable assets out" -- is built; see the
"Reference images" section below.

### The loop is a ratchet

Every rejection carries a reason. Reasons that recur get promoted into stage 8,
so **human review volume falls as the factory matures**. `stats` reports which
reasons are recurring hardest, so the next check to write is never a guess:

```
judged 8/8   accepted 4   rejected 4

recurring rejection reasons (automation candidates):
    3  (75.0%)  crate top face too close in value to saucer - silhouette merges  <-- worth automating
    1  (25.0%)  cup reads flat, needs a rim highlight

4 rejected sprites passed every automated check.
  That gap is exactly what the next check should cover.
```

**This has already happened once.** The first batch rotated the camera with a
world-fixed light, so the lit face drifted around the object between directions.
Every frame was individually valid, so no per-sprite check caught it — but it was
obvious to a person scanning the contact sheet. The fix was conceptual: in an
isometric game the camera is fixed and the *object* rotates, so the key light
belongs in the camera basis. That finding is now `check_direction_set`, and it
will never need a human again.

**And it keeps happening.** The checks promoted since fall into two kinds, and
the second kind is the one worth naming:

*Checks that encode a rule.* Hair must clear skin in lightness; a member under
4 px reads as wire; seating faces its table; nothing floats.

*Checks that encode a **projection**.* These have no analogue in a 2D pipeline
and they are where the 3D-intermediate approach earns its cost, because the
defect only exists once geometry meets a specific camera:

| check | what it catches |
|---|---|
| `Layout.screen_occlusion` | two props several tiles apart in plan view that land on the same pixels, so the near one erases the far one |
| `check_buried_detail` | geometry that faces the camera and still never wins a pixel — detail modelled where it cannot be seen |
| `check_direction_labels` | sprite facings derived from the camera basis rather than declared, so the atlas cannot be off by a rotation |
| `measured_symmetry` | how many azimuths actually produce different sprites, which sets the render budget |

Each of these was written after a human said some version of "that area is
mush", which is not actionable, and each turned that into a specific pair of
object names and a percentage, which is.

That is the whole thesis of the factory in one example.

---

## Portability

The art direction is an **input**, not a hardcode. `style_bible.yaml` holds the
palette ramps, hue-shift rule, outline and dithering conventions, and projection.
Swapping it retargets the factory at a different game. The cozy coffee shop is
case study one, chosen because a coffee shop interior exercises wood, ceramic,
foliage, fabric and skin — most of the material range a 2D game needs.

---

## Status

| Stage | State |
|---|---|
| 1 (concept) | working — `concept.py`, SDXL + fitness gate, prompt or prompt+reference (IP-Adapter) |
| 2 (mesh) | working — `lift.py` reconstructs a mesh via TripoSR (TRELLIS 2 blocked, see below) |
| 3 (rig) | blocked on this workstation's toolchain (UniRig needs `nvcc` + MSVC), not rejected — but **the seam it attaches to is built and checked**: `ingest.py` binds an arbitrary mesh to the palette and the tile grid |
| 4 (motion) | working as a **procedural rig** — `character.py` poses, `animate.py` clips. Stands in for HY-Motion the way the rasterizer stands in for Blender |
| 5 (render) | working — exact 2:1, 8 azimuths, camera-space key. **Consumes OBJ meshes** via `mesh.py`, or analytic primitives as a fixture |
| 6 (pixelize) | working — `pixelize.py`, ramp-quantized, zero contamination |
| 7 (metadata) | working — `animate.py` emits `atlas.json`: frame rects, per-clip anchors, fps, direction order |
| 8 (auto-review) | working — `art_review.py` and friends, **21 checks**, all run by `manifest.py --check` |
| 9 (human critique) | working — `review_queue.py`, contact sheet + ratchet |
| 10 (engine export) | working — `export_godot.py`, 22 Godot `SpriteFrames` resources built from the current sprite library |

`isorender.py` is a software raytracer and `mesh.py` an orthographic rasterizer,
both standing in for Blender so the deterministic half runs with no GPU or DCC
dependency. Stages 4-9 are complete end to end.

## The seam where stages 1-3 attach

Stage 5 has always been described as consuming OBJ meshes, and that was true of
meshes this repo wrote itself, whose `usemtl` tokens are already palette
materials like `wood-2`. It was never true of anything a generator produces. A
mesh out of TRELLIS arrives with vertex colours or an MTL full of arbitrary RGB,
Y-up because almost everything upstream of a game engine is, and an arbitrary
scale and origin. Each of those is a hard stop, and none of them needs a GPU to
solve — so `ingest.py` is built and under check now, and stages 1-3 stop being
hypothetical.

**Binding is the interesting half, and it is not nearest-colour.** Everything
downstream is built on one material meaning one ramp: grain resolves by ramp,
tone offsets compose within a ramp, `check_palette_spread` counts ramps per
character. So a ramp is chosen as an *identity* — by distance to the ramp
treated as a curve through OKLab — and only then is the step chosen by
lightness. A binder free to trade lightness against hue would scatter one
object across several ramps wherever a shadow fell near a step of something
else, and hand all of the above a mesh it cannot reason about.

Three versions were wrong before that one was right, and each failed on a case
the previous one fixed:

| approach | failure |
|---|---|
| hue angle, with a chroma threshold forcing greys to `neutral` | `neutral` here is *not* achromatic — it is a cool violet-grey at chroma 0.016–0.022, so a threshold near its own chroma swallows every quiet colour. A warm off-white bound to `neutral+2` at dE 0.124 with `cream` two steps away. |
| each ramp's chroma-weighted mean (a, b) | chroma is a function of lightness. A dark brown carries a third the chroma of a mid brown, so it scored nearer pale `cream` than `wood`. |
| (a, b) at each ramp's nearest step in lightness | `cream` has no dark end, so its "nearest" step was 0.41 away in L — a ramp that cannot reach the source's lightness was competing as though it could. |

Both halves are checked, and both checks were verified to fail before being
trusted. `check_roundtrip` is exhaustive rather than sampled: every step of
every bindable ramp is a colour the palette definitely contains, so each has
exactly one right answer, and a stub binder that answers `neutral` for
everything reports 36 of 37. `check_transform` runs a library chair out to a
real OBJ and MTL — Y-up, scaled 37x, shifted off the origin, every material
renamed — and asserts it comes back grounded, centred, at the height asked for,
with its materials intact, and **not mirrored**. That last one needs its own
instrument: a reflection has the same bounds, the same height and the same
materials, so the first four assertions all pass on one. Signed volume is what
catches it, and a mirrored asset renders perfectly right up until it is a
character with a bag on the wrong shoulder in half of its directions.

## Stage 4: motion, and why the rig is six numbers

`character.Pose` carries six limb angles, a vertical offset and a twist. That is
the entire rig, and the smallness is the design rather than a shortcut: at 46 px
of figure a pose is read from limb *direction* and body height, not from joint
articulation. An elbow is one pixel. A spine chain would cost render time across
3023 frames and change nothing on screen.

Two things fall out of that constraint rather than being animated by hand:

**The walk bob is derived, not keyed.** Posed figures are ground-clamped so the
lowest vertex rests on the floor. Because swinging a leg about its hip shortens
its vertical reach, the body drops when the legs are spread and rides high when
they are together — the exact vertical rhythm a hand-animated cycle is drawn
with, for free. Measured amplitude 0.036 units, 1.0 px at room scale.

**The foot does not rotate with the leg.** An ankle keeps it flat. Rotating it
rigidly drove its rear corner into the floor, and since the figure is
ground-clamped that lifted the whole body and *inverted* the bob — mid-stride
rode higher than legs-together. After contralateral swing, that is the most
visible thing a walk cycle can get wrong.

The one clip that changes rig mid-way is `sit`. With no knee to bend, a
continuous lowering cannot be posed, so it uses the two-part shape every
low-resolution game uses: lean and drop on the standing rig, then cut to the
seated rig and settle. At 12 fps the cut is invisible.

**The mesh seam is open.** `render_batch.py --mesh asset.obj` runs the full chain
from arbitrary geometry, so stages 1-4 now have somewhere to deliver.
Rasterization is used rather than raytracing because orthographic projection is
affine, which makes a scanline z-buffer both exact and far faster. It was
cross-checked against the raytracer on the same scene tessellated: **99.40%
material agreement**, 0.7% coverage difference, mean lambert error 0.014 -- the
residual being faceted tessellation approximating analytic surfaces.

## Stages 1 and 2 run

Both are built and both produce output on the machine this repo is developed
on: an RTX 4070 Laptop, 8.6 GB of VRAM, driver 595.95. That is the 8 GB this
document assumed, and the assumption held.

### Stage 1 -- `tools/concept.py`

SDXL base at 1024, one prompt template, then `rembg` (u2net) for the matte, then
a fitness gate. The gate is the point. Four subjects were generated and three
passed; the fern was rejected at 12% soft alpha against a 10% cap, because
frond edges are exactly what a segmenter cannot commit to and a half-transparent
edge becomes a halo of wrong-ramp pixels four stages later.

Two matting approaches were tried and thrown away before `rembg`, and both
failures are informative:

- **Threshold the plain grey backdrop.** Swept tolerance from 0.055 to 0.18.
  Below 0.11 the contact shadow joins the subject and the blob reaches the
  frame edge; at 0.14 the teapot's lid dissolves into the background. The two
  failures cross. There is no threshold, not a badly chosen one.
- **Chroma key on a colour the palette does not contain** (153, 0, 255). It
  produced a purple teapot -- the backdrop colour bleeds onto the subject
  during diffusion, which is a property of the generator and not of the key.
  The separation check caught it at dE 0.121. The machinery was deleted rather
  than left in as a setting.

**Reference images.** `concept()` takes an optional `reference` image,
conditioning generation via SDXL IP-Adapter alongside the text prompt --
the "examples" half of "a factory that takes prompts and examples". IP-Adapter
rather than img2img, deliberately: img2img denoises the reference's own
layout, importing whatever camera angle it happened to be shot at, which is
exactly the per-object drift the fixed `STYLE` camera clause exists to
prevent. IP-Adapter conditions on the reference's *appearance* while the
prompt and `STYLE` keep owning composition.

One real bug and one real measurement here:

- **The image encoder `load_ip_adapter()` attaches isn't covered by the
  offload hooks `enable_model_cpu_offload()` set up when the pipe was first
  built** -- it stays on CPU while everything else runs on CUDA, and the
  first call crashes: `RuntimeError: Input type (torch.cuda.HalfTensor) and
  weight type (torch.HalfTensor) should be the same`. Fixed by re-running
  `enable_model_cpu_offload()` after `load_ip_adapter()`, which re-attaches
  hooks to every current submodule.
- **`--ip-scale` was swept, not guessed**, one reference (a matte ceramic
  teapot photo, copper handle) against a deliberately conflicting prompt
  ("a glass vase"), same seed: 0.3 only nudges body proportions, 0.4-0.5
  add the reference's handle(s) while the vase stays glass, 0.6 overrides the
  material entirely (renders in opaque ceramic), 0.85 nearly reproduces the
  reference outright, copper accent included. Shipped default is 0.45 -- just
  under where the prompt starts losing. One pair, not the swept bracket the
  fitness floors above have; a reference that doesn't fight the prompt on
  material will tolerate a higher scale.

Because there is no single right `--ip-scale`, `tools/concept_ui.py` puts a
slider in front of a human instead of hard-coding a second guess: a small
local Gradio app over the same `concept()`/`check_concept_fitness()` calls
the CLI and `factory.py` use, showing the raw render, the matte, and the
fitness gate's exact findings for whatever's just been generated. `pip
install gradio && python tools/concept_ui.py`, opens
`http://127.0.0.1:7860`.

`--reference` and `--ip-scale` also take multiple values (`--reference a.jpg
b.jpg`): each image loads as its own IP-Adapter slot rather than being
averaged, so two references genuinely blend rather than one silently
overriding the other. `--kind character` swaps in a dedicated negative
prompt (`NEGATIVE_CHARACTER`) tuned for prompts naming a specific character
or franchise, which pulls SDXL toward fan-art/character-sheet training data
harder than a generic prop noun does -- see `ART_CRITIQUE.md`, "The collage
failure mode, and the 77-token ceiling that was already most of the way
there", including the measured limits (helps, doesn't universally fix
famous-enough subjects). `--positive-override`/`--negative-override` bypass
`STYLE`/`NEGATIVE` entirely for anything outside the isolated-single-object
framing both presets assume; `concept_ui.py`'s "custom" kind exposes the
same two fields with example prompts shown alongside them.

### Stage 2 -- `tools/lift.py`, and why it is not TRELLIS

TRELLIS 2 needs three CUDA extensions compiled from source: `nvdiffrast`,
`diff-gaussian-rasterization`, and a sparse-conv backend. Compiling them needs
`nvcc` and an MSVC host compiler. This machine has the driver and the card but
no CUDA toolkit and no C++ workload in its Visual Studio install, and pip's
`nvidia-cuda-nvcc-cu12` ships only `ptxas.exe` on Windows. Getting there is two
admin-level system installs of roughly 10 GB -- a decision about somebody's
workstation, not a decision about this repo.

So stage 2 is **TripoSR**: pure PyTorch, ~1.7 GB of weights, no compiled
extensions, no rasteriser. It is a weaker reconstructor and this document
should say so. What it buys is that stages 1 and 2 connect to `ingest` today,
on hardware that exists.

Three things had to be worked around, and each is in the file rather than in a
patch someone has to remember to re-apply:

- **`torchmcubes` has no Windows wheel.** A `torchmcubes` module backed by
  `skimage.measure.marching_cubes` is injected into `sys.modules` before
  TripoSR imports. The vendor tree stays pristine. The subtlety is axis order:
  reversing the vertex columns to match what the caller expects is a
  reflection, so the winding has to be reversed with it. Getting that wrong
  does not crash and does not look wrong in a viewer -- `ingest.signed_volume`
  read **-0.1612** before the flip and **+0.1612** after.
- **The checkpoint is transformers 4.35 and the venv is 5.15.** ViT was
  refactored in between, so every attention weight in all twelve layers went
  missing. Downgrading would break stage 1, so the rename is expressed as a
  rename. Order matters: `.attention.output.dense` has to be rewritten before
  the bare `.output.dense` rule, or an attention projection lands in `mlp.fc2`
  with matching shapes -- silent, plausible, completely wrong.
- **`load_obj` dropped vertex colours.** TripoSR writes colour on the `v` line
  and emits no MTL; a reader that takes only the first three floats turns a
  two-tone teapot into one uniform material without failing anything. `orient`
  and `fit` then had to carry the new field, because they did not, and the
  vertex-colour branch in `ingest` never fired -- everything bound to
  `neutral`, silently, with no warning anywhere.

### The defect the seam actually had: double shading

The first teapot to survive all of that rendered as a **near-black blob with a
correct silhouette**. Stage 8 did not catch it. The cause is structural and
worth stating plainly: a photograph is albedo times lighting, a reconstructor
cannot separate them, so TripoSR's vertex colours arrive with the concept
image's key light already multiplied in. `bind_colour` then picks the ramp step
nearest the source's lightness -- which is its *lit* lightness -- and the
renderer applies lambert on top. The lighting runs twice.

The fix is a shift, and the size of the shift was measured rather than tuned:

| | albedo median L | p05-p95 band |
|---|---|---|
| thirty `assetlib` props | **0.596 - 0.845** | 0.000 - 0.585 |
| TripoSR teapot | **0.408** | 0.481 |

Every one of the thirty authored meshes lands in that median range -- not most,
all, with seventeen sitting on 0.600 exactly, because the library is built out
of ramp middles. The teapot is 0.188 below a floor nothing authored goes near.
Its *band*, meanwhile, is comfortably inside the authored range; an espresso
machine is busier. So the median is wrong and the contrast is not, and
`ingest.delight` shifts the one without touching the other. Compressing the
band would have destroyed the two-tone structure the reconstructor actually
recovered, to fix a problem it did not have.

Corroboration that the shift is right rather than merely flattering: the worst
bind distance **fell from dE 0.146 to 0.071**. The palette was authored as
albedo, so albedo binds to it better than lit colour does. Nothing about
`delight` optimises for that number.

`check_albedo_centre` reads the bound result and reports a median outside
0.596-0.845, so a bad `delight` and a bad MTL fail by the same route.

### The framing bug underneath it

`render_batch` used `DimetricCamera`'s default span of 1.25, sized for the
analytic room scene. A 0.28 m prop came out as a nine-pixel dot -- and stage 8
*did* catch that one, blocking all eight sprites with *"art appears to be 8x
upscaled (97% of 8x8 blocks are uniform)"*. `frame_all` now computes one span
as the **maximum across all eight azimuths** and one **fixed world centre**.
Per-direction fitting would have fixed the size and broken something worse: the
prop would breathe and drift as it turned.

### What no check can do here

A single-view reconstructor invents the far side of the object, and the teapot's
back is invented. No image-space check on the direction set can catch it,
because the mesh is genuinely rigid -- the eight frames are a consistent
turnaround of the wrong geometry. This is a property of stage 2, not a gap in
stage 8, and it is what stage 9 is for. A metric proposed here and discarded:
silhouette-area consistency across directions, which would have measured
nothing, because it is satisfied exactly by a rigid mesh however wrong.

### Stage 3

Unbuilt. It is only needed for characters, and props do not rig.
