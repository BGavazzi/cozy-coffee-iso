# Cozy Coffee Shop — Isometric Pixel Art Asset Spec

Working document. This is the technical contract the generation pipeline must satisfy.
Nothing ships that fails the conformance gate in section 6.

**Project constraints:** maximum quality, 8 directions everywhere; AI or code performs
all creation and validation, with humans limited to creative direction. See
**[PIPELINE.md](PIPELINE.md)** for the architecture those constraints require — a 3D
intermediate stage, pre-rendered to sprites, which makes most of the contract below
structurally guaranteed rather than merely checked.

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

**Directions: 8** — `RotZ = 45° + k·45°`, `k = 0..7`. No mirroring; each azimuth is a
true render of the same mesh, so all eight are consistent by construction.

Under the 3D pipeline, additional directions cost render time rather than authoring
time, so 8-direction is the default rather than a luxury.

**Barista (player) — 46 unique frames × 8 directions = 368**

| Action | Frames | × 8 dir |
|---|---|---|
| idle | 4 | 32 |
| walk | 8 | 64 |
| carry-walk | 8 | 64 |
| brew / interact | 6 | 48 |
| wipe / clean | 6 | 48 |
| serve | 4 | 32 |
| pour | 6 | 48 |
| sit | 4 | 32 |

**Customers — 32 unique frames × 8 directions = 256 per archetype**

walk (8f), sit-idle (4f), sip (4f), wait-impatient (4f), talk (4f), leave (8f).

One base rig and **one shared motion clip set**; the 8 archetypes differ by mesh and
palette swap only. Motion is authored once and retargeted, so archetype count scales
almost free: **2,048 frames total** across all eight.

### 4.4 FX (~12 short loops, 3–4 frames each)

Cup steam, espresso drip, coffee pour, door swing, ceiling fan, rain on window,
"order ready" bubble, coin pickup, satisfaction hearts, cat tail flick.

### 4.5 UI (~30)

Order tickets, drink type icons (8–10), currency, day-end summary frame, dialogue box
and nameplate, upgrade icons, day/night clock.

### Total: **≈3,400 rendered frames** across ~250 distinct assets

Machine time, not human time — a few hours unattended. See PIPELINE.md §5.

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

## 6. Conformance gate (closed loop, no human in it)

Because no human may repair a pixel, this is a **control loop**, not a report. Three
tiers by what the machine can do about a failure.

**Tier 1 — auto-repair deterministically, then re-verify:**
- Palette drift — any pixel outside the locked palette
- Alpha fringe — any pixel with `0 < alpha < 255`
- Off-grid detail — effective block size ≠ 1 at native res
- Canvas mismatch — dimensions ≠ declared spec
- Pivot placement — recomputed from mesh geometry
- Outline convention inconsistency
- Animation loop not closing — first pose ≠ last pose

**Tier 2 — detect, then bounded retry with adjusted parameters (max 3 attempts):**
- Degenerate or blobby mesh (thin-feature collapse)
- Silhouette area outside tolerance for the asset class
- Footprint mismatch vs. declared tile units
- Frame-to-frame delta above jitter threshold
- Direction-set inconsistency across the 8 azimuths

**Tier 3 — escalate to creative direction:**
- Anything that fails 3 retries
- Aesthetic judgement, which no validator can make

Tiers 1 and 2 are the whole reason the pipeline can run unattended. Tier 3 is the
human's sanctioned interface, and it is deliberately the *only* one.

**Structurally guaranteed, therefore not checked:** projection angle and light direction.
Both are fixed properties of the camera and light rig (PIPELINE.md §4, stage 5), so they
cannot vary. In a 2D pipeline both would need runtime validation.

---

## 7. Division of labour across the pipeline

Under the no-human-cleanup constraint, the question is not "where does AI help" but
"which stage owns each guarantee." Assignments:

| Asset class | Path |
|---|---|
| Props, furniture | concept → mesh → 8-azimuth render → pixelize |
| Characters | concept → mesh → rig → motion → render → pixelize |
| **Tiles** | **procedural code.** Seamless tiling is a solved deterministic problem; generation cannot guarantee a seam-free edge |
| **FX** | Blender particles / shader, rendered through the same camera path |
| **UI** | 2D generation only — no projection or footprint constraints apply |

**Generation is never the last step.** Every asset with a conformance contract passes
through deterministic render and pixelize stages, so no generated pixel reaches the game
unmediated. That is what allows the human out of the loop.

**Where diffusion is still explicitly excluded:**
- **Per-frame img2img on animations.** Restyling frames independently reintroduces exactly
  the jitter the 3D path exists to eliminate. Permitted on static props only, where there
  is no temporal dimension to disturb.
- **Tileable surfaces**, per the table above.

The pipeline is a **deterministic renderer fed by generative concepting**, not a sprite
generator. Correctness is structural; only appearance is generated.

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

## 10. Decisions

**Settled:**
- **8 directions everywhere.** Cheap under the 3D path; quality is the priority.
- **No human pixel work.** All creation and validation is AI or code. Humans do creative
  direction only — style bible, concept approval, Tier-3 escalation.

**Still open:**
1. **Reference set** — which games define the target style? Drives the palette, the outline
   convention, and the shading ramps. This is now the *only* blocking input, and it is a
   creative-direction call by definition.
2. **Room scale** — single fixed room, or scrolling / multi-room? Affects tile budget.
3. **Mesh quality budget** — accept TRELLIS 2 at 512³ on the local 8 GB (thin geometry will
   degrade), or rent a 24 GB GPU for stage 2?

## 11. Sequencing

Build the deterministic half first — stages 5–8 — driven by a hand-placed placeholder
mesh. That proves the camera, the pixelizer, the metadata, and the conformance loop end to
end before any GPU time goes into generation. If the render-and-pixelize path produces a
spec-perfect 8-direction sprite from a known-good mesh, everything upstream is a
swappable input.
