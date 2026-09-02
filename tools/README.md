# tools

    pip install pyyaml pillow
    python tools/palette_forge.py

Generates and validates the locked palette from `style_bible.yaml`, writing
`palette/palette.{json,gpl,png}`. Exits non-zero on any constraint failure, so
it can gate CI. The `.gpl` loads directly into Aseprite and GIMP.

`oklab.py` is the colour-space layer: OKLab/OKLCh conversion plus hue-preserving
sRGB gamut mapping. Pure stdlib.

## Style packs

`style_bible.yaml` is the first of what `tools/style.py` calls a *style pack* --
every producer's art direction, not just the palette: `art_direction` /
`palette` / `rendering` / `decisions` (the original schema, unchanged) plus
`materials:`, `rig:`, `checks:` (new). `cozy_ghibli` is that root file, kept
exactly where every script already expects it; a second style pack lives at
`styles/<name>/bible.yaml`.

    python tools/style.py --list          # every style pack found
    python tools/style.py --check NAME    # bible loads, required keys present

Only `materials:`/`checks:`/`rig:` exist so far as *data* -- `assetlib.py` and
`character.py` don't read them yet, because both hardcode their WOOD/CERAMIC/...
and proportion values as function default arguments, which Python binds at
`def` time, before any `--style` flag can be parsed. See `NEXT.md`, "Style
packs: generalizing beyond one art direction", for the full status and what a
second style pack needs next.

## Why the palette is computed rather than picked

Two properties become *checkable* instead of hoped for:

- **Perceptual separation.** Every pair is at least `min_delta_e` apart in OKLab,
  so no two entries collapse into each other under quantization.
- **The warm-light / cool-shadow rule.** Shadows bend toward a cool anchor hue,
  highlights toward a warm one. This single rule carries most of what reads as
  "Ghibli", and as a parameter it cannot be forgotten on asset 180.

## What the validator found

It rejected four structurally broken palettes before this one passed, and each
rejection was a real design error rather than a tuning nit:

1. Two wood ramps 15 degrees apart with overlapping lightness - always collide.
   Merged into one 7-step ramp.
2. `cream` and `skin` converge at the light end, because aggressive chroma
   falloff desaturates every warm highlight toward the same near-white.
3. Three separate warm ramps plus cream will not pack into a high-key,
   low-chroma gamut at 40 colours. Skin now comes from `wood` - they are the
   same hue family, and `wood_3..wood_6` are textbook flesh tones.
4. Bending red shadows toward violet produces plum, which reads as bruising on
   skin-adjacent surfaces. Hence the per-ramp `cool_amount` override.

None of those would have been obvious by eye until a hundred assets in.

## Proving the shading claim

    python tools/prove_shading.py     # -> proof/comparison.png

`isorender.py` is a small orthographic dimetric raytracer standing in for the
Blender stage, so the deterministic half of the pipeline could be built and
tested before any DCC dependency exists. `verify_projection()` asserts that a
ground-plane unit square projects at exactly 2:1 rather than trusting the
arithmetic - it measures 0.500000000000.

`pixelize.py` implements the conformance stage, and deliberately implements
*both* quantization strategies so the difference can be measured:

| | naive | ramp-quantized |
|---|---|---|
| distinct colours | 17 | 10 |
| ramps touched | wood, cream, foliage, **neutral** | wood, cream, foliage |
| cross-ramp leak | **157 px (11.8%)** | **0** |

The naive path smooth-shades, averages during downsample, then snaps each pixel
to its nearest palette entry. Both later steps are the problem: averaging
manufactures colours that were never in the palette, and nearest-colour search
has no idea what material it is shading. In the comparison sheet this shows up
unmistakably - the cream ceramic cup renders **blue-grey**, because its shadow
side landed nearer the violet `neutral` ramp than to its own. That artifact is
precisely what "looks like a shrunk 3D render" means.

The ramp-quantized path binds each material to a ramp, maps the lambert term to
a discrete ramp *index*, and emits that exact colour. Gradients are recovered by
ordered dithering between adjacent steps **of the same ramp**. Downsampling
takes the modal colour, never the mean. Cross-ramp contamination is not reduced;
it is impossible.

Outline colour is the bounding surface's own darkest ramp step, so "tinted per
surface" and "never pure black" hold by construction rather than by choice.

## Asset manifest

    python tools/manifest.py            # summary + render budget
    python tools/manifest.py --queue 1  # work queue for a priority tier
    python tools/manifest.py --check    # validate against the style bible

`assets.yaml` enumerates **106 distinct assets** across tiles, props, characters,
FX and UI, each declaring footprint, height, palette ramps, rotational symmetry
and priority tier.

### Symmetry is the budget

Eight azimuths is the worst case, not the default. A round table is identical
from every angle (1 render), a square crate repeats every 90 degrees (2), only
asymmetric objects need all 8. Declaring symmetry per asset is free and cuts
**43% of the static render budget**:

| section | if all 8 | actual | avoided |
|---|---|---|---|
| tiles | 128 | 63 | 51% |
| props | 512 | 322 | 37% |
| fx | 400 | 208 | 48% |
| **static total** | **1040** | **593** | **43%** |

### But characters are the real budget

Characters are **80% of all renders** (2416 of 3023), because 8 customer
archetypes share motion clips but each still needs its own 8 azimuths x 32
frames. Cutting one archetype saves more than every prop optimisation combined.
That is the number to argue about when scoping, and it is not obvious until the
manifest is machine-readable.

### Validation

`--check` cross-references every declared material against `style_bible.yaml`,
catches duplicate ids and bad symmetry classes, warns when tier-1 furniture
would not leave room to walk, and flags palette ramps no asset uses — dead weight
in a 40-colour budget. It caught four stale ramp names on first run.

## Building the declared props

    python tools/furnish.py             # build every mapped prop
    python tools/furnish.py --list      # what maps to what, and what does not
    python tools/furnish.py --only chair_wood table_4top

`assets.yaml` declares 64 props; `assetlib.py` has been building most of that
furniture procedurally since the room renderer existed. Nothing connected the
two — `render_room.py` and `build_plan.py` both parameterise builders inline at
the call site, so there was no id-to-builder mapping anywhere in the repo, and
only **2 of 64** declared props had sprites. Both by accident: the built sprites
are named after `subjects_c1.yaml`, and two of those names happen to collide
with a declared id.

`furnish.py` is that mapping, and running it takes the library to **56 of 64**.
Everything downstream is `ingest.fit` and `render_batch` called directly, not
reimplemented: mesh, fit, eight azimuths, footprint, manifest merge.

**The remaining 8 are reported, not guessed at.** `--list` prints each unmapped
id with the reason it has no recipe. A `sink_double` rendered from `counter()`
would pass every automated check in this repo and be wrong in the only way that
matters, so a recipe is written only where a builder genuinely makes the
declared object, and a recipe that reuses a builder for a related id carries a
note that `--list` prints.

### Scale comes from the manifest

Every mesh is fit to its declared height, so the manifest is authoritative
rather than the builder's own proportions. The declared footprint is then a
**cap, not a target** — `fp` is a layout reservation, so a chair measuring 0.65
tiles inside its 1-tile reservation is correct and only overflow is a defect.
Seven props overflow when fit to their declared height and are refit to the
reservation, with the height they actually achieved printed: two declared
numbers and a builder's proportions cannot all three hold, and the one with a
downstream consumer wins.

### What the review found

Across the 448 sprites this produces, `art_review.py` reports **zero blockers**.
The 57 blockers remaining in `out/sprites/` all belong to the 32 SDXL-path
assets and are all `speckle` — the recorded ceiling for high-frequency detail.
That is the session's "things versus abstractions" finding as a number: geometry
with a semantic role wants to be rendered, not generated.

Two defects the checks could not have caught, both found by opening the PNG:
`sandwich_board` had a docstring describing a lean over geometry that had none
(`add_box` is axis-aligned, so two parallel panels and a hinge is a box — it
rendered as a doorway, and now leans via `pivot_rot`), and `plant_succulent`
was `leafy_plant` at a short height, which is a plant correctly grown of the
wrong species. One defect the checks did catch: `saucer` and `cup_latte` were
byte-identical, because `fit` scales uniformly and per-asset framing then makes
scale invisible in the image. That is now `check_distinct`.

## Text

    python tools/bitmap_font.py           # build the shipping sizes
    python tools/bitmap_font.py --check   # sweep cap heights 5..20
    python tools/bitmap_font.py --demo    # text inside the nine-slice chrome

`NEXT.md` item 3 read: "No font, no bitmap glyph set, nothing that renders a
word in the palette." 90 glyphs now do.

### Skeletons, not a pixel grid

A pixel font is normally authored by placing pixels, one glyph at a time, at one
size — which is why bitmap fonts ship as "8px", "16px", and nothing between.
Every glyph here is a set of **polylines** on a shared metric grid, stroked by an
integer line algorithm at whatever cap height is asked for. Size, weight,
letterspacing and palette are parameters; the letterforms are the only data.

That is the split every producer here makes. `assetlib` describes a chair as
geometry; `ui_chrome` describes a frame as rects and discs. A letterform is the
irreducible part — 'A' is a cultural convention and cannot be derived from a
rule — so it is the part written down, and nothing else is.

### Which sizes ship is measured

| cap | result |
|---|---|
| 5 | `8`/`S` and `c`/`o` and `i`/`l` collide; `A` and `4` lose their counters |
| 6 | `a`/`o` collide; `A` and `4` still filled in |
| **7–20** | **clean** |

`SIZES` ships 7, 9, 11 and 13. `check_counters` is what sets the floor: an 'e'
whose aperture has closed is not a smaller 'e', it is a blob, and that is a
question about *topology* — no palette or coverage metric can see it, because
both measure colour.

### What the checks found

Four defects, none of which a person would reliably catch by eye:

- **Hand-declared advances disagreed with their own ink.** `1` and `Q` put
  pixels outside their cell, at cap 9 and cap 17 only, where rounding lands ink
  one pixel further right than it lands the advance. Advances are now *measured*
  off the rasterised ink, which cannot be inconsistent with it — and that makes
  the font proportional for free.
- **Every advance was one unit too tight**, so "HH" set the two facing stems
  adjacent and read as a single 2px bar.
- **Python's `round` is banker's rounding.** `round(1.5)` is 2 but `round(2.5)`
  is 2 and `round(4.5)` is 4. Mirror-symmetric letterforms therefore came out
  asymmetric at some sizes and not others — `W` with unequal halves, `^` with
  one leg short. Half-up rounding throughout, and both glyphs re-cut onto
  integer offsets from an integer centre.
- **`"` merged into a thick apostrophe** — its two strokes landed on adjacent
  columns at cap 7.

Each check was verified to fail before it was believed: aliasing `0` to `O`
trips `check_distinct`; a solid `e` trips `check_counters`; an overshooting `T`
trips `check_bounds`; removing one pixel from the advance trips `check_pairs` on
5923 of 7921 pairs. Worth recording what *doesn't* trip it: setting `SPACING` to
zero does not, because the gap is floored at 1 — so `check_pairs` guards the
advance rule, not the spacing constant.

### The isolated-pixel metric needed correcting, not relaxing

Rendered text failed `ui_forge`'s `MAX_ISOLATED` gate at 9–14% against a 6.2%
cap. A one-pixel diagonal — which is what `X`, `/` and `V` *are* at cap 7 — has
no orthogonal neighbour at all. So the threshold stays and the neighbourhood
changes, from four neighbours to eight, justified by measurement rather than by
convenience:

| | 4-conn | 8-conn |
|---|---|---|
| font sheet cap 7 | 11.5% | **1.5%** |
| `ui_dialogue_frame` | 0.3% | 0.0% |
| `chair_wood_dir0` | 1.1% | 0.0% |
| random palette noise | 90.3% | **80.6%** |

The last row is the one that matters: the reading that stops punishing a
diagonal still separates art from noise fifty-fold. The 4-neighbour reading is
left alone everywhere else, where a pixel with no orthogonal neighbour genuinely
is a downsample artefact.

### Exported as a font, not as baked strings

`build_all.gd` writes a `FontFile` per size — no anti-aliasing, no hinting, no
subpixel positioning, no MSDF, all for the same reason `_line` has none: every
one of them blends pixels this pipeline guarantees are palette-exact.

`export_godot.check_font_layout` then measures strings with those resources
through Godot's own TextServer and compares against `bitmap_font.measure`:
**32 of 32 widths match across four sizes.** This is the only export whose
*behaviour* can be checked headless — the nine-slice round-trip can confirm its
margins are the numbers that were drawn and cannot confirm the engine lays them
out right. The samples are adversarial: `iiii` and `MMMM` would tie if the font
had silently fallen back to a monospaced cell, and `A B C` is the only one that
exercises the space glyph.

## Characters and layout

    python tools/preview_characters.py   # roster + one archetype x 8 directions
    python tools/render_room.py          # full shop, reports collisions

`character.py` assembles figures from six part slots -- legs, torso, arms, head,
hair, accessory -- rather than authoring each one whole. Nine characters in the
preview are the same parts library with different short specs, so a tenth
archetype costs a few lines instead of a mesh. The render budget is unchanged;
the **authoring** budget collapses, which is the number that mattered.

Proportions are chibi-leaning on purpose. The first pass was 4:1 height to width
and read as a totem pole at 40 px; cozy comparables sit nearer 2.5:1. There is
also a `seated=True` pose, because parking a standing figure at seat height reads
as standing *on* the chair.

`layout.py` derives footprints from mesh XY bounds and reports overlaps
exceeding a share of the smaller object. Not all overlap is a defect -- a chair
tucked under a table is correct -- so specific pairs are whitelisted and the test
is proportional rather than binary. It caught two chairs from adjacent tables
sharing a square at 67% overlap on first run.

## Character portraits

    python tools/portrait.py           # roster -> out/portraits/<name>.png
    python tools/portrait.py --check   # eye visibility, distinctness, determinism
    python tools/portrait.py --demo    # -> proof/portraits.png

`portrait.py` builds a dialogue bust for each roster character: `head()` and
`hair()` reused directly from `character.py` for shape and material identity,
a bust-height `chest()` slice standing in for the full body, and real brow,
mouth, eye and blush geometry authored fresh at portrait scale, because
`character.face()`'s flat sprite-scale marks -- correct at 12px of head --
render a blank mannequin once that head fills a 96px canvas. The camera is a
bespoke dead-on view (`azimuth=90`, `elevation=15`), not the sprite rig's
corner-view `frame_all`, since a portrait never rotates and gains nothing from
the 8-direction framing a rotating sprite needs.

### What the checks found

Four checks run over the full 9-character roster: palette-exactness,
pairwise distinctness, per-eye visibility, and render determinism. The
eye-visibility check is the one worth describing, because its first version
passed while an eye was genuinely, fully invisible. It compared bare skin
against the complete face -- eyes, brows, mouth, blush -- as one image-half
diff; enough contrast came from the brows and blush alone to clear the
threshold even with the eye itself occluded. Rewritten to isolate exactly one
eye against bare skin, feature by feature, it then found a real defect: at an
early camera angle and margin, `bob`'s eyes rendered **zero** pixels of
difference from bare skin.

Root cause was a hidden-surface bug, not a camera-angle bug. Face geometry
was authored proud of `head()`'s own facet (`HEAD_RY * FACET + 0.004`), which
is the surface it visually sits on -- but `hair()` draws every style's main
cap at a *larger* radius (`HEAD_RY + 0.022`) than the head it covers, so
hair's front facet can be the nearer surface to the camera even when the
head's own facet is cleared. The fix widens the margin to clear `hair()`'s
facet, not just `head()`'s. Its one measured effect on the shipped nine,
once the camera was set to the simpler dead-on `azimuth=90` rather than the
off-axis angle first tried to dodge the (mis-diagnosed) problem: `reader`'s
brows go from invisible to rendered. Smaller claim than "the eyes were
broken" -- and the checked one.

### A bug one level down

Building the portrait producer surfaced a real defect in code it merely
exercises harder than its usual caller: `render_batch.render_sprite`'s
outline pass assigned material ids with `hash(m) % 251` for its downsample
pass. Python randomises string hashing per process, so which pair of a
scene's materials collided -- and which outline pixels silently took an
unrelated ramp's colour as a result -- changed on every run. A prop rarely
carries enough distinct materials to make this visible; a character bust,
crowding skin, hair, shirt, eyes, brows and mouth into a small canvas, does.
`render_room.py` and `preview_characters.py` already carried a fix (a sorted
material index instead of a hash), but `render_batch.py` -- the function
`furnish.py`'s entire prop factory renders through -- had been missed. Fixed
at the source, plus the same fix backported into `prove_shading.py`'s local
copy of the same pattern.

### One artifact, left as a characteristic

A faceted seam is visible where the octagonal `chest()` prism meets the round
head silhouette, at some strength on every character and most visible on the
widest `bulk` values (`commuter`, `elder`), where the torso's facets push
past the head's own width. It is the same kind of modal-downsample aliasing
this pipeline already accepts on other faceted silhouettes, not a defect
specific to portraits, so it is recorded rather than chased with more
geometry.
