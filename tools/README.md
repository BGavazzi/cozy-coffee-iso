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
