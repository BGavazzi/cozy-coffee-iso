# tools

    pip install pyyaml pillow
    python tools/palette_forge.py

Generates and validates the locked palette from `style_bible.yaml`, writing
`palette/palette.{json,gpl,png}`. Exits non-zero on any constraint failure, so
it can gate CI. The `.gpl` loads directly into Aseprite and GIMP.

`oklab.py` is the colour-space layer: OKLab/OKLCh conversion plus hue-preserving
sRGB gamut mapping. Pure stdlib.

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
