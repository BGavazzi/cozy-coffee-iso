# Cozy Coffee Shop — Isometric Pixel Art Asset Spec

Working document. This is the technical contract the ComfyUI pipeline must satisfy.
Nothing ships that fails the conformance gate in section 6.

---

## 1. Projection (locked — do not revisit)

| Property | Value | Why |
|---|---|---|
| Projection | **2:1 dimetric** (26.57°) | 2-across-1-up gives uniform pixel stair-steps. True 30° isometric produces irregular steps that break at low res. |
| Base tile footprint | **64 × 32 px** diamond | Large enough that a espresso machine reads clearly; small enough that a room fits one screen. |
| Tile grid | X right-down, Y left-down | Standard screen-space dimetric. |
| Character height | 48–64 px | ~1.5–2 tile heights. Keeps faces readable without dwarfing props. |

**Risk:** diffusion models do not hold projection angle. Every generated asset drifts a
few degrees and mismatched angles are the most visible failure mode in an iso scene.
Mitigation is geometric control (depth ControlNet from 3D blockouts, or a fixed
reference grid in the conditioning), plus a hand-correction pass. Prompting alone
will not solve this.

---

## 2. Palette

- **32–40 colors, locked.** Extracted once from the reference set, then enforced.
- Warm bias, low saturation contrast. Cozy reads as *mid-tones*, not high dynamic range.
- Outline color: dark warm brown or desaturated purple. **Never pure black** — pure
  black outlines kill the cozy register instantly.
- Day / evening / night handled as **palette swaps**, not re-authored art. One ramp per
  mood, same indices.

Palette is the single strongest consistency lever across 250 assets. Stronger than
any LoRA. Enforce it deterministically, never by prompt.

---

## 3. Lighting & shadow

- **Single fixed light source**, screen-space upper-left (= NW in grid terms).
- Every asset shades to that one direction. No exceptions, no ambient variation.
- Drop shadow: flat ellipse or dithered blob at the footprint base, uniform opacity.

Models violate light direction constantly and *inconsistently*. This is the second
most visible "assembled, not designed" tell after projection drift.

---

## 4. Asset manifest

### 4.1 Tiles (~40)

**Floors** — wood plank, checkerboard tile, polished concrete, rug inserts (3 variants).
Must be seamlessly tileable. *Author deterministically or by hand — generation loses here.*

**Walls** — the hard tiling problem:
- NE-facing segment, NW-facing segment
- Inner corner, outer corner
- Door cut (×2 orientations), window cut (×2 orientations)
- Baseboard / trim variants

### 4.2 Props (~80 statics)

Each prop declares a **footprint in tile units** (1×1, 1×2, 2×2). Footprint is authored
metadata — it cannot be inferred from the image.

| Group | Items |
|---|---|
| Service | counter segments (straight/corner/end), espresso machine, grinder, pastry display, register, sink, fridge, drip brewer |
| Seating | 2-seat table, 4-seat table, bar stool, chair (**×4 rotations**), sofa, armchair |
| Dressing | bookshelf, plants (4 kinds), menu chalkboard, wall art, hanging lamp, floor lamp, crates, coat rack, rug |
| Small | cups, saucers, bean bags, napkin holder, tip jar, laptop, books |

### 4.3 Characters

**Directions: 4** (NE, NW, SE, SW), horizontally mirrored where the silhouette allows.
8-direction nearly doubles the frame count for marginal readability gain at this scale.

**Barista (player) — ~84 unique frames**

| Action | Frames | × Dir | Total |
|---|---|---|---|
| idle | 2 | 4 | 8 |
| walk | 4 | 4 | 16 |
| carry-walk | 4 | 4 | 16 |
| brew / interact | 4 | 4 | 16 |
| wipe / clean | 4 | 4 | 16 |
| serve | 3 | 4 | 12 |

**Customers — ~44 unique frames, then 8 recolors**

One base rig: walk (4f), sit-idle (2f), sip (3f), wait-impatient (2f) × 4 directions.
Archetype variety comes from **palette / outfit / hair swaps over an identical
silhouette** — not from 8 separately authored characters. This is the single biggest
scope saving in the project, and it is exactly the task diffusion is good at.

### 4.4 FX (~12 short loops, 3–4 frames each)

Cup steam, espresso drip, coffee pour, door swing, ceiling fan, rain on window,
"order ready" bubble, coin pickup, satisfaction hearts, cat tail flick.

### 4.5 UI (~30)

Order tickets, drink type icons (8–10), currency, day-end summary frame, dialogue box
and nameplate, upgrade icons, day/night clock.

### Total realistic first-playable: **~250 unique assets** (~130 animation frames)

---

## 5. Per-asset technical contract

Every exported asset satisfies all of:

1. **Canvas** — fixed power-of-two or tile-multiple bounds, no auto-crop, no alpha trim.
2. **Pivot** — **bottom-center of the tile footprint, NOT the sprite bounding box.**
   Isometric Y-sorting depends on this. Wrong pivot = a chair renders in front of the
   table it is tucked under.
3. **Alpha** — 1-bit. Hard edges. Zero semi-transparent fringe, zero antialiasing.
4. **Palette** — every pixel is an exact member of the locked palette.
5. **Grid** — sits on the true pixel grid at native res (no off-grid detail from
   downsampling a high-res generation).
6. **Outline** — uniform convention across the whole set (selective outline recommended).
7. **Metadata** — emits JSON: frame rects, pivot, footprint in tile units, Y-sort anchor,
   animation loop points.

---

## 6. Conformance gate (auto-reject)

An asset that fails any check does not enter the project. This gate is the difference
between a pipeline and a slot machine.

- [ ] Palette drift — any pixel outside the locked palette
- [ ] Alpha fringe — any pixel with 0 < alpha < 255
- [ ] Off-grid detail — effective block size ≠ 1 at native res
- [ ] Canvas mismatch — dimensions ≠ declared spec
- [ ] Footprint mismatch — silhouette base ≠ declared tile footprint
- [ ] Projection drift — measured edge slope ≠ 2:1 within tolerance
- [ ] Light direction — highlight centroid not in the NW quadrant
- [ ] Missing metadata — no pivot or footprint declared

---

## 7. Where AI generation earns its place

**Real wins — point the pipeline here:**
- Prop and furniture variation at volume (the 40th chair, not the first)
- Customer outfit / hair / skin recolors over a fixed silhouette
- Wall and floor texture variants
- UI icons
- Promotional key art (no conformance constraints at all)

**Not worth it:**
- Seamless tileable floors — deterministic tiling is faster and actually seamless
- **Animation in-betweens** — at 48–64 px, one pixel of frame-to-frame jitter reads as
  noise. No current model holds sub-pixel temporal coherence at this scale. Video
  models (LTX etc.) are useless here for the same reason.
- Anything with a strict geometric footprint, without depth conditioning

**Method:** generate at 768–1024 px in-style → deterministic downsample →
palette quantize → conformance gate. Animate by hand or procedurally
(2-frame idle, 4-frame walk carries this genre).

The pipeline is a **variation engine with a hard conformance gate**, not a sprite
generator. That framing is both more honest and more useful.

---

## 8. Hardware reality

RTX 4070 Laptop, 8 GB VRAM.

- SDXL + pixel-art LoRA is the operating point. SD1.5 LoRA trains comfortably;
  SDXL LoRA is tight but viable at 768 px with gradient checkpointing + 8-bit Adam.
- Qwen-Image-Edit only fits at Q2_K / Q3_K_S — visibly degraded, skip for now.
- At 8 GB you cannot share the GPU with another loaded ComfyUI workflow. If another
  instance is running, stop it before sprite work rather than running both.

---

## 9. Non-art needs

- **Engine:** Godot 4 — good isometric TileMap and Y-sort support out of the box.
- **Sim loop:** spawn → order → brew → serve → satisfaction → money → upgrade.
- Cozy games are carried by *feel* — audio, palette, and tiny idle animations — far
  more than by systems depth. Budget accordingly.

---

## 10. Open decisions

1. Reference set — which games define the target style? (Drives palette + outline convention.)
2. 4-direction confirmed, or is 8 wanted for the player specifically?
3. Room scale — single fixed room, or scrolling / multi-room?
4. Is hand cleanup in Aseprite acceptable in the loop, or must output be terminal?
