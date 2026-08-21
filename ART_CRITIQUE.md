# Art Critique — measured against isometric pixel art convention

Reviewing `proof/shop.png` against the established craft rules for isometric
pixel art, rather than against taste. Every claim below is measured.

**References used:**
[Pixel Parmesan, *Fundamentals of Isometric Pixel Art*](https://pixelparmesan.com/blog/fundamentals-of-isometric-pixel-art) ·
[SLYNYRD, *Pixelblog 41 — Isometric Pixel Art*](https://www.slynyrd.com/blog/2022/11/28/pixelblog-41-isometric-pixel-art) ·
[Pixune, *The Artistry of Isometric Games*](https://pixune.com/blog/defining-isometric-games-art/)

Genre comparables: Songs of Conquest, RollerCoaster Tycoon, Travellers Rest,
Bear and Breakfast, Coffee Talk, Stardew Valley.

---

## What is good

### 1. Projection is exactly right — and this is the rule everything else rests on

Every source names the same foundation: **2:1 line slopes (26.57 degrees), not
true 30-degree isometry**, because 2-step lines produce clean pixel stairs and
30 degrees produces what SLYNYRD calls "jaggy rhythm".

We measure `0.500000000000`. Not approximately — exactly, because it is a camera
matrix rather than a hand-drawn angle. This is the strongest structural advantage
the 3D-intermediate approach buys, and it is the one thing hand-pixelled art most
often gets subtly wrong across a large asset set.

### 2. Three-face value separation passes

Pixel Parmesan states the readability rule directly: a light source should hit
the top face fully and one side partially, "as each face will have a different
value, making it easier to read visually."

Measured, on the wood ramp (7 steps):

| face | N·L | lambert | ramp step |
|---|---|---|---|
| top | 0.811 | 0.846 | **5.08** |
| left (+x) | 0.569 | 0.623 | **3.74** |
| right (+y) | 0.000 | 0.100 | **0.60** |

Separation of 1.33 and 3.14 steps between adjacent faces. Comfortably distinct,
so box forms read as solid volumes. This is satisfied by the light rig rather
than by an artist remembering it per asset.

### 3. Cast shadows now ground the objects

Added this pass, and it was the largest single visual improvement. Pixel Parmesan
is explicit that cast shadows are the primary grounding device and should align
to the isometric grid. Before: props floated. After: they sit.

See `proof/shadow_comparison.png`.

### 4. Palette discipline holds at scale

35 distinct colours in a 272k-pixel frame, **zero off-palette**, no pure black,
no pure white. Consistent key light across all 8 directions (measured highlight
centroid spread 2.2 x 1.0 px).

---

## What is bad

### 1. The top of every ramp is dead — worst single finding

Wood ramp histogram across the frame:

```
step 0:    6188   3.0%  ##
step 1:   35964  17.6%  ################
step 2:   17256   8.4%  ########
step 3:   13384   6.6%  ######
step 4:    2012   1.0%
step 5:  129416  63.3%  ############################################################
step 6:      68   0.0%
```

**Step 6 gets 0.0%.** The brightest wood never appears anywhere in the scene,
because nothing is brighter than a flat top face under a single key light. Step 4
is nearly as dead at 1.0%.

We spent real effort building perceptually-spaced 7-step ramps and are using
about four of them. Worse, `lamp_glow` — a spot colour that exists precisely to
be a light source — is **never used at all**, because no material maps to it.

The genre comparables all solve this the same way: they stage **light pools**.
Window shafts across the floor, warm circles under pendant lamps, a bright rim
where daylight hits the counter. Those are what justify the top of a ramp. We
have pendant lamps and windows modelled, and neither emits light.

### 2. 63% of the frame is a single ramp step

The floor is one unbroken plane of `wood_5`. Every comparable breaks the floor:
RollerCoaster Tycoon with pathway tiling, Stardew with plank seams and rugs,
Travellers Rest with worn boards. Flat floor is the clearest tell of a blockout.

The manifest already lists `floor_tile_check`, `floor_wood_worn` and
`floor_rug_round` — they are simply not placed. Cheap fix, large payoff.

### 3. Chromatic monotony — 75% of the frame is one material

| ramp | share |
|---|---|
| wood | 75.0% |
| cream | 18.6% |
| neutral | 3.0% |
| foliage | 1.5% |
| sky | 1.0% |
| rose | 0.8% |

Cozy interiors in the comparables are chromatically *busy* — that is much of what
makes them read as lived-in. `foliage`, `sky` and `rose` together hold 3.3% of
the frame. The palette is far richer than the scene uses.

### 4. No focal hierarchy

The service counter — the thing the player actually interacts with — carries the
same detail density and contrast as empty floor. The comparables consistently
give the interaction zone the strongest local contrast and the densest detail,
which is how the eye knows where to go. Ours is uniform, so the composition has
no centre.

### 5. The Ghibli premise is in the palette but not on screen

The entire palette was built around warm-light / cool-shadow hue shifting, which
is the defining Ghibli move. The scene never stages it: there is no cool daylight
falling through the windows against warm interior lamplight. One directional key
plus flat fill cannot express the idea the palette was designed for.

This is the gap between having the right colours and using them.

### 6. Silhouettes are below the readable threshold in places

At the room framing, scale is 27.2 px per world unit. Chair legs are 0.08 units
= **2.2 px**. Table pedestals ~4.9 px. Pixel art convention is to exaggerate and
chunk up these members precisely because realistic proportions disappear at low
resolution. Ours are modelled at realistic thickness and consequently read as
wire.

---

## Ranked fixes

| # | Fix | Cost | Payoff |
|---|---|---|---|
| 1 | Emissive light pools from lamps and windows | medium | unlocks the top 2 ramp steps; stages the warm/cool premise |
| 2 | Place floor variation — tiles, rug, worn boards | low | breaks the 63% single-step plane |
| 3 | Thicken small members (legs, rails, frames) to a 3–4 px floor | low | silhouette readability |
| 4 | Add small props for chromatic variety at the counter | low | fixes 75% monotony |
| 5 | Raise local contrast in the service zone | medium | gives the composition a centre |

Items 2, 3 and 4 are hours of work. Item 1 is the real one, and it is also the
one that turns the palette from a nice document into the thing on screen.

---

## The honest summary

The **structural** layer is genuinely good and would be hard to beat by hand:
exact projection, provable face separation, consistent lighting across
directions, zero palette violations, grounded shadows. That is precisely what a
factory should be good at.

The **staging** layer is weak: flat lighting, unbroken floor, no focal point, no
warm/cool play. That is precisely what a factory is not good at, and what the
human critique loop exists to catch.

Which is the expected division. The measurements just make it concrete: we built
the half that automates well, and the half that needs art direction still needs
art direction.

---

# Second pass — what the ranked fixes actually did

The five ranked fixes above were implemented. Re-measuring the same frame, so
the numbers are comparable rather than impressionistic.

## Fix 1 — staged light (was: "the top of every ramp is dead")

Implemented as `LightRig` in `tools/mesh.py`: warm pools under each pendant, a
wash over the service counter, and glow inside each window.

Projected window shafts were tried and abandoned, which is worth recording as a
negative result. The key light is anchored to the camera basis, so at azimuth 45
its world direction runs essentially along +x. An isometric room may only draw
its two *far* walls, and a shaft cast through those lands either as a 0.15-tile
sliver against the skirting or outside the floor entirely — both measured. Making
shafts reach would require a sun direction that disagrees with the cast shadows.
A backlit window is therefore lit as a bright pane plus an interior pool, which
is what one actually looks like from indoors and stays correct from all eight
azimuths rather than one.

Wood ramp usage across the frame:

| step | before | after |
|---|---|---|
| 0 | 3.0% | 10.4% |
| 1 | 17.6% | 3.0% |
| 2 | 8.4% | 16.2% |
| 3 | 6.6% | 22.2% |
| 4 | 1.0% | 10.2% |
| 5 | **63.3%** | 3.9% |
| 6 | **0.0%** | 1.3% |

Peak single step **63.3% → 22.2%**. Dead steps (under 0.5%) **1 → 0**. The whole
ramp is now in use, which means the warm-highlight / cool-shadow hue rotation the
palette was built around is finally on screen rather than in the JSON.

## The light direction was itself the bug

Sweeping the rig against explicit targets surfaced something the first critique
missed. With the original key at `(-0.50, 0.55, 0.67)`, the floor measured ramp
step **3.3** and a character's face measured **3.1** — the ground was brighter
than the faces. That is not a tuning error, it is geometric: a floor's normal
aligns with a steep key, and a face is a vertical plane that misses it. It is why
the room read as a lit stage rather than a lit interior.

Lowering the key to `(-0.70, 0.14, 0.70)` gives floor **2.98**, faces **4.30**,
with three-face separation still **1.42 / 1.57** steps — better balanced than the
old 1.33 / 3.14. Interior fill was also turned horizontal, since indoors the
bounce comes off walls rather than out of a sky.

## Fix 2 — floor variation, and two ways to get it wrong

Both traps were hit before the fix landed, and both are cheap to repeat:

1. **Too much.** Half-tile boards with a two-step-dark seam turned the floor into
   a barcode that pulled the eye off every prop.
2. **Thin boxes have sides.** Planks laid as separate boxes leave a vertical face
   at every joint. Those normals point sideways, so they shade to the *bottom* of
   the ramp — a near-black grid across **15%** of the floor, produced by geometry
   only ever meant to be a tone change. Making the overlays 0.0018 tall did not
   help: subpixel side faces still win the depth test along the whole run, still
   measuring **7.6%** at step 0.

The floor is now one slab with **zero-thickness quad** overlays. A quad has no
sides, so a seam can only ever be the one step it asks for.

## Fix 3/4 — chromatic monotony

| ramp | before | after |
|---|---|---|
| wood | 75.0% | 67.3% |
| cream | 18.6% | 18.0% |
| rose | 0.8% | 4.1% |
| neutral | 3.0% | 3.8% |
| sky | 1.0% | 3.6% |
| foliage | 1.5% | 3.1% |

The three minority ramps held **3.3%** of the frame between them; they now hold
**10.8%**. Still 0.00% off-palette.

## Dithering was applied everywhere it could be, not where it should be

Not in the original list, and visible once the light had gradients to render.
Ordered dither ran across the full 0..1 range between steps, putting a checker on
every shaded surface — static, not pixel art. Hand artists lay a dither band at
the step boundary and leave the flats flat. Restricting the Bayer threshold to a
band around the boundary halved isolated-pixel speckle, **15.3% → 7.2%**.

## New promoted checks

Per the ratchet, three review findings became automated checks:

- `character.check_contrast` — hair within 0.13 lightness of skin merges into the
  face. `commuter` shipped at 0.004; both colours were individually legal, so no
  per-pixel check could ever have seen it.
- `character.check_direction_stability` — a pixel floor at game scale. Note the
  first version of this check was *wrong*: it compared widest to narrowest
  direction and failed anything over 15%, but a humanoid genuinely is about half
  as wide from the side. Chasing that to zero would mean modelling a cylinder.
- `layout.seating_faces_tables` — two of the four chairs at every round table had
  their backs to the table. Individually valid geometry, wrong only in relation to
  a neighbour, which is exactly the class a per-sprite critic cannot see.

## Still open

- No focal hierarchy. The counter is brighter than it was but does not yet own the
  composition.
- Cast shadows are soft and read as smears at this light elevation.
- Chair frames are thin enough at room scale to read as spindly.
- Large empty floor in the lower right; the room is under-dressed, not under-lit.

---

# Third pass — dressing, focal hierarchy, and a fix that made things worse first

## The library was the bottleneck, not the placement

Occupancy measured **58%** of floor tiles with an 8-tile bare rectangle. The
cause was not lazy layout: every mesh in the blockout library was already on the
floor. Eleven assets added (bench, armchair, side table, coat rack, sandwich
board, wall shelf, wall sign, cake stand, basket, trash bin, flower vase),
occupancy **58% → 69%**, largest bare rectangle **8 → 6** tiles, placements
**67 → 85**.

## Dressing alone made the composition worse

Worth recording plainly, because it is the sort of thing that looks like
progress. Filling the dead zones raised occupancy and *lowered* legibility: props
were added uniformly, which flattens hierarchy rather than building it.

Edge density by ninth measured **19.1% – 25.9%, a 1.36x spread** — essentially
flat. The counter ninth, the thing the player actually interacts with, measured
*below* the middle of the room. A composition with no peak gives the eye nowhere
to land, and adding evenly-spread detail makes that worse, not better.

Two measured causes:

**The backdrop was the brightest thing in the frame.** The far wall in plain
cream measured **0.77–0.78** mean lightness, well clear of everything else, so
the eye was pulled to the top edge. A backdrop should be the quietest surface
present. Dropped to `cream-2`: top row **0.77/0.67/0.78 → 0.70/0.64/0.73**.

**Uniform material.** 67% of the frame was the wood ramp, so furniture did not
separate from furniture. Painted chair frames fixed this — but the first attempt
used `-1` offsets, which measure **L=0.70 on the sky ramp: identical to wood step
4**. The chairs differed only in hue, read as equal-weight pastel blocks, and
pulled focus off the counter. Painted furniture has to sit *below* the wood in
value: at `-3` it separates by hue and recedes by value, which is the point.

Net: focal spread **1.36x → 1.48x**, wood **67.3% → 62.7%**, minority ramps
**10.8% → 15.5%**.

## Placement rotated about the wrong point

`transformed` rotates about the local origin, so a prop placed at 200 degrees
lands nowhere near the coordinates written for it — an armchair intended for
(3.0, 7.5) actually occupied x 2.19–3.21, y 6.35–7.37 and collided with a stool
a metre away. `Layout.add(centre=True)` pivots about the mesh's own XY centre, so
`at` means what it reads as. Hand-written placements are only maintainable if the
coordinates are honest.

## New promoted check: member thickness

`art_review.check_member_thickness` rasterizes an asset at the scale it is
actually seen (27.2 px/unit) and measures runs of solid pixels, rather than
auditing box dimensions — which say nothing about what the projection produces.

The metric took two attempts, and the first was wrong in an instructive way. It
flagged the *thinnest* member, and duly fired on a pendant lamp's cord, a cup's
handle and a sign's brackets — all of which are meant to be thin and are a
rounding error of their asset's area. What reads as wire is an object most of
whose *mass* is thin. The metric is now the share of solid pixels in runs under
4 px, capped at 20%.

Findings it produced: chair stiles at 1 px; 4-top legs at 1 px; a sandwich board
built from zero-thickness quads at 3 px, because a standing plane seen near
edge-on collapses to a line — quads are right for floor overlays and wrong for
anything vertical; and table clutter at 23% of mass under the floor, sized up
because a table of specks reads as dirt rather than as an occupied table. All
assets now clear it.

## Still open

- Focal spread is 1.48x. Better than flat, not yet a composition with a centre.
  The counter needs to win on contrast, not just on prop count.
- Cast shadows remain soft and read as smears at this light elevation.
- The room is now legibly furnished but the near-right quadrant is still the
  weakest area.

---

# Fourth pass — the room as a room

The third pass ended with the counter needing to "win on contrast, not just on
prop count", and with the tooling to say whether it did. Building that tooling is
where this pass started, and it immediately produced a number that could not be
true.

## The measurement was broken before the thing it measured

`focal_report` projects the counter's world bounds to screen pixels and compares
lightness and local contrast inside against outside. It reported:

```
focal zone (service counter): mean L 0.719 vs 0.600 elsewhere (+0.120)
                              contrast 0.000 vs 0.560 (-0.560)   DOES NOT lead the eye
```

A region containing a counter, an espresso machine, a register and a pastry case
cannot have a local contrast of exactly zero. The verdict was confident, precise
and worthless. The cause was one line: the projection subtracted the
crop-to-content offset from coordinates that index the *uncropped* buffer, so the
rect landed off the counter and collapsed.

The lesson is not "check your arithmetic". It is that **a metric confident enough
to print a verdict is confident enough to be believed**, and the only thing that
caught this was the value being impossible rather than merely wrong. Anything
slightly wrong would have been acted on. The check now refuses to report at all
if fewer than 200 pixels fall inside the box.

## Then the render disagreed with the fixed metric

With the projection corrected the counter led on both axes and the tool printed
`reads as the centre`. Looking at the render, it did not. Three defects the
metric was structurally unable to see:

**Everything lived in one value band.** Floor, walls and nearly every prop
between L 0.55 and 0.75. Nothing was dark, so nothing had anything to be bright
against — a focal lead of +0.09 local contrast is what a composition with no
value structure can offer. Dropping the floor field one step to `wood-1` gives
the room a ground in the literal sense: a value everything else is measured up
from.

**The floor was ruled into stripes.** Board tone varied per *course*, so every
tone change was a stripe one unit deep and the full width of the room: five lines
longer and higher-contrast than any prop, pointing nowhere. Two earlier attempts
tuned the *direction* of the offset (`-1`, then `+1`) and neither helped, because
the defect was never the offset. It was that the unit of variation was the wrong
shape. Real flooring varies board to board; the tone now scatters, with staggered
butt joints from a fixed LCG so the floor is byte-identical between runs. A floor
that reshuffles per render makes every before/after table in this document
meaningless.

**The wall was head height.** 1.6 units, against 1.59-unit characters — a ceiling
exactly at the top of everyone's head, which is why the room read as a dollhouse
tray. Only the two far walls are ever drawn and they sit behind every object in
the scene, so raising them to 2.45 cannot occlude anything. Windows moved up with
it (sill 0.38 → 0.58, head 1.22 → 1.82) and a picture rail splits the enlarged
field, which had otherwise gone back to being the biggest quiet mass in frame.

## New promoted check: screen-space occlusion

`Layout.collisions()` is a plan-view test, and it is necessary but not
sufficient. In a dimetric view two objects several tiles apart project to the
same pixels and the near one erases the far one — the composite shows a
silhouette nobody modelled. That is what "that corner is mush" means when a human
says it, and nothing in the layout could see it, because in plan view the objects
are nowhere near each other.

`Layout.screen_occlusion()` projects each placement's bounds through the shipping
camera and fires when a pair overlaps by more than 45% of the smaller *and* sits
at least 1.2 tiles apart in depth. The depth gate is what separates a genuine
occlusion from a chair legibly tucked at a table, which overlaps on screen
precisely because it is meant to.

What it found:

| finding | why it mattered |
|---|---|
| `char#queue1` hid **56%** of `char#queue0` | the queue ran *into* the view axis: two customers 1.5 tiles apart in world, 0.1 apart on screen, reading as one smeared figure |
| `decor#coats` hid 65% of `bar#2` | a coat rack standing a tile in front of the window bar |
| `char#seat1` hid 43% of `stool#0` | the lounge sat in the same screen column as the bar stools, two tiles nearer |
| `seat#arm1` hid 36% of `stool#1` | same cause |

All cleared. A queue in an isometric view has to run *across* the frame, and the
lounge moved right by a tile — moving the *bar* made it worse, because the
occluders were the things in the wrong place.

**The first version of this check was itself wrong, and its numbers are worth
recording as a caution.** It hand-rolled the screen basis from sin/cos of the
azimuth instead of using `DimetricCamera`, and got three things wrong: `u` came
out sign-flipped, `v` was off by up to a third of a tile on tall objects, and
depth ignored `z` entirely — so the depth gate, the entire point of the check,
measured the wrong axis. It reported 74%, 67%, 49% and 82% for the four findings
it produced. Under the shipping camera those are 56%, 33%, 11% and 11%.

Two of the four were real. The other two were artefacts of the broken
projection: a menu board behind an espresso machine measures 11%, exactly what a
correctly tucked chair measures, because the two boxes overlap in a narrow
vertical band that bounding boxes cannot resolve. That defect was real and worth
fixing, but this check did not find it and does not claim to.

A check that disagrees with the renderer is not a check. The lesson is the same
one as `focal_report` above, one level up: **re-deriving a projection that
already ships is how a verification tool ends up confidently measuring
something else.**

## New promoted check: buried detail

The espresso machine carried two group heads and two portafilters modelled at
y=0.28 inside a carcass spanning y 0.15–0.85 — fully enclosed, contributing not
one pixel in any frame, while on the counter it read as a blank grey slab. This
is the most expensive kind of defect, because it hides as *effort*: the mesh
insists it is detailed.

The obvious metric is the share of triangles that never win a pixel, and
measuring it proves why that is useless: a closed box shows at most three of its
six faces, so **every solid asset scores about 67% "buried"** and the check fires
on all eighteen props. That is not a defect, it is what solid geometry costs.

What matters is a triangle that *faces the camera* and still reaches no pixel,
because something else is in front of it. At a 30% threshold that flags 4 of 24
assets, and three were real:

- **bookshelf**, 86% — shelves and books modelled inside a solid carcass box. On
  screen, a plain wooden slab standing where a bookcase was meant to be.
- **register**, 33% — the screen on the far side of its own bezel. A till with no
  display.
- **pastry_case**, 48% — 69 triangles of glass on the side away from the camera,
  backed by a view straight through to the wall.

The remaining two are exempted by name with a reason, the same role `TUCK_OK`
plays for collisions: a four-legged table hides its far legs behind its own top,
and a lidded display case has an interior its top pane covers. Both would still
be true if the asset were re-modelled from scratch. An allowlist is what lets the
threshold stay tight enough to catch the real thing.

## Two bugs found by looking, not by measuring

**Outline colour was randomised per process.** The outline pass identified each
material by `hash(m) % 251`. With ~30 materials collisions are near-certain by
the birthday bound, and Python randomises string hashing per process, so *which*
materials collided changed every run. The visible symptom was foliage-green edges
around the wooden counter. The invisible one was worse: the room render was not
reproducible, which quietly invalidates every before/after comparison here.
Material ids now come from a sorted index.

**Every sprite in the atlas was filed under the wrong facing.** `DIRECTIONS`
began at `"s"` for azimuth 45. The character's front is +y; projected through the
2:1 dimetric basis, +y at azimuth 45 lands at screen down-*right*. The tuple was
correct in ordering and wrong by exactly one step — the worst size of error to
have, because the sheet looks perfect, every frame is correctly rendered, and a
game reading `atlas.json` draws a character walking south using the south-east
sprite. Eight sprites all subtly turned, in a way that reads as "the animation
feels off" rather than as a bug with a location.

The order is not a convention to be chosen. It follows from the front being +y
and the camera being 2:1 dimetric, so `derived_directions()` now recomputes it
from the camera basis and `check_direction_labels()` fails if the tuple drifts. A
derived constant cannot agree with a mistake.

## New promoted check: palette spread per character

`check_contrast` catches hair disappearing into a face. It does not catch a
figure built entirely from one ramp, where every part is individually a legal,
well-separated tone and the character still reads as one dark mass because there
is no hue change anywhere to give the eye an edge. `commuter` shipped that way —
neutral shirt, neutral trousers, neutral hair, neutral bag — and at the till it
was a silhouette-shaped hole in the room. No spec may now spend more than half
its parts on one ramp.

## Where the numbers landed

| | third pass | fourth pass |
|---|---|---|
| focal zone lightness lead | not measurable | **+0.064 L** |
| focal zone contrast lead | not measurable | **+0.094** |
| wood share of frame | 62.7% | **59.8%** |
| minority ramps | 15.5% | **17.5%** |
| screen-space occlusions | 4, unmeasured | **0** |
| assets with buried detail | 3, unmeasured | **0** |
| automated checks in the ratchet | 7 | **11** |

The four added: screen-space occlusion, buried detail, per-character palette
spread, and derived direction labels. All eleven run from `manifest.py --check`.

## Still open

- Local contrast is measured as a p95−p05 spread of lightness, which is quantized
  by the palette itself and therefore lands on a handful of values. It separates
  "has structure" from "flat" and should not be read more finely than that.
- The near-right quadrant is dressed but is still the weakest area of the
  composition.
- Stages 1–3 (SDXL concept → TRELLIS 2 mesh → UniRig rig) remain specified and
  unbuilt; everything above is the deterministic render half of the factory.

---

# Fifth pass — generators, not placements

This pass started from a question rather than a defect: *are we building tools to
make art assets, or just making the assets?*

Counting settles it. `assetlib.py` held 135 hand-written primitive calls, and
`build_room` held 85 hand-typed coordinates. `PIPELINE.md` stages 1–3 (SDXL
concept → TRELLIS mesh → UniRig rig) are the generative half and remain unbuilt,
which means the library was a *placeholder standing where generated meshes should
arrive* — and four passes of art critique had been spent polishing the
placeholder. Every fix was real, and each one was promoted into a check, but the
ratio was wrong.

The second question was whether the result was close to the target. It was worth
re-reading what the target actually says, because the answer was being measured
against the wrong thing.

## The target was never painted Ghibli

`style_bible.yaml` is explicit:

> Not soft-rendered Ghibli — Ghibli's *colour science* filtered through a locked
> palette and hard pixel edges.
> **precedent:** SNES-era JRPG backgrounds (Secret of Mana, Terranigma, Illusion
> of Gaia) already solved this.

Measured against *that*, the colour work was already done — and the fact that the
whole room render uses 38 distinct colours is the idiom working, not evidence
against it. SNES tiles ran 16 colours per palette.

| rule from the bible | measured | |
|---|---|---|
| warm light / cool shadow hue shift ("the single most defining rule") | 5/6 ramps warm toward light; wood runs 42.9° → 3.3° from the warm anchor | pass |
| high-key value distribution | 60.3% of the frame above L 0.50, median 0.600 | pass |
| modest chroma, peaking mid-tones, never neon | mean 0.065, max 0.113 | pass |
| almost never pure black or white | 0.67% at the extremes | pass |

The bible also names three substitutions for the Ghibli qualities a locked
palette cannot have. Two were built. The third —
`atmosphere: value compression toward the ramp's light end, not blur` — had never
been implemented, in four passes, because a substitution table reads like prose
and nobody had treated it as a spec.

So the gap was never colour. It was **form**: every surface an axis-aligned
primitive, six chairs pixel-identical to each other, every edge machine-straight,
and large unbroken areas landing on exactly one ramp step. And none of that
needs a pencil. All five fixes below are generators.

## Aerial perspective

Twenty lines against an existing spec. Depth is already in the z-buffer; distant
surfaces are pulled toward `haze_to` in proportion to the *square* of normalised
depth, which both lifts them and compresses their contrast, since everything
converges on one value as the weight rises. Squared, so the near two-thirds of
the room is untouched and the effect only builds where depth actually reads.

## Surface grain

The largest single change. Applied to the **lambert**, not the colour, so the
existing quantizer turns it into legal palette steps for free and it can never
produce an off-ramp pixel.

Three decisions did the work:

**Blocky, not smooth.** Interpolated noise resolves to a soft gradient that the
ramp quantizer then re-hardens into contour bands — the exact artefact
`pixelize` exists to prevent. Blocky cells quantize cleanly because they are
already flat.

**World space, not screen space.** In screen space the pattern would crawl across
a rotating sprite between the eight azimuths, the same class of mistake as
screen-space dithering.

**Anisotropic per material.** This is what separates grain from dirt. Isotropic
noise on wood produces round blotches that read as stains, because wood has no
round features — it has long ones. Squashing the lattice on x by 0.42 stretches
each cell into a streak along the board.

Amplitude is capped below one ramp step everywhere: grain breaks a flat field, it
does not add a second value structure competing with the lighting.

**And it immediately went wrong in an instructive place.** Skin is drawn on the
wood ramp — the warm mid-browns are exactly right for it — so at 0.85 of a step
the barista's face came out streaked with plank grain. Two materials that want
the same colour and opposite treatment need separate names, so `skin` is now its
own entry in `MATERIAL_RAMPS` resolving to `wood`, and grain resolves by
material before falling back to ramp.

## Warp, and why it displaces by position

Every prop was a perfect primitive, so six chairs were six pixel-identical
chairs. `warp` offsets vertices by a smooth function of **world position** rather
than per vertex. That is the whole trick: `add_box` emits its own eight vertices
per box, so displacing each independently would open seams between counter
modules and take a chair apart at the joints. Two coincident vertices evaluate
the same function and move together, so connectivity survives without the mesh
needing to know about it. Variation comes free — the same chair at two positions
samples the field twice and warps differently, with no per-instance seed.

It also broke a check, correctly. The crate stack touches at *exactly* z=0.52,
and an exact z-separation test fails the moment anything perturbs a vertex; a
stack that had been right for four passes reported a 100% collision. Stacked
props now get a 5 cm skin, which real interpenetration (measured in tenths of a
tile) clears easily.

## The checks became a solver

This is the answer to the opening question.

For four passes `collisions`, `grounded` and `screen_occlusion` were
*validators*: they graded 85 hand-typed coordinates and said which were wrong.
The same predicates, run **before** a placement instead of after, are a
constraint solver. Propose a position, test it, keep or discard. Density stops
being authoring work and becomes a number.

`Layout.scatter` places 19–33 props per run depending on how much room the
regions have. A saturated region returning fewer than asked is the solver
working, not failing. Two things it taught immediately:

- The first pass scattered crates along the **near** edges, where they stood in
  front of the whole room. The far walls are x=0 and y=0; clutter belongs against
  those, because the near sides are open to the camera.
- A generated vase landed 0.82 up in clear air just past the end of the bar, and
  `grounded` caught it after the fact. A solver that can check a rule afterwards
  can check it beforehand, so support is now tested at proposal time and the rule
  never fires.

`factory(i)` receives the instance index, because ten scattered plants calling a
zero-argument factory would be ten identical plants — which defeats the point of
having made the plant procedural.

## Plants that grow

The two plants being replaced were a sphere on a pot, and five spheres in a
hand-typed list of offsets — the same shrub everywhere, in the one place an
interior is supposed to look least manufactured.

`leafy_plant` is the standard recursion cut down to what survives at 27 px per
world unit. Leaves carry the mass and stems only imply direction, because a
0.02-unit stem is half a pixel. Droop compounds — each segment keeps 55% of the
previous rise and all of the outward lean — because straight radiating stems read
as a starburst, the one shape that never occurs in a pot. Leaves flatten toward
the top so the plant does not read as a stack of balls, which is precisely what
the five-sphere version looked like.

`check_buried_detail` then reported 55% of a 420-triangle canopy hidden behind
its own leaves. Both halves of that got answered: the exemption covers *hidden*
— overlapping leaves are what a canopy is — and the leaf prisms dropped from 8
sides to 6 to cover *420 triangles*. An allowlist entry that silences a warning
without first asking whether it had a point is how a ratchet turns back into
decoration.

## And the crate

One `add_box`. Defensible while crates sat in a corner; indefensible once the
generated pass began scattering them, because 0.76 tiles square of unbroken wood
at one ramp step is the most blockout-looking object that can be put on screen.
Now slatted, with the slats drawn as value a thousandth of a unit proud of each
face — and only on the three faces this camera can see, because
`check_buried_detail` would report the rest as buried and would be right.

## Chairs, and what does not survive downsampling

Fourteen chairs in the reference room, all one mesh. The first generator varied
the back *infill* -- slat, ladder, spindle, cross -- which was four styles'
worth of code that produced eight chairs identical apart from colour. At the
room's 27 px per world unit the gap between the two stiles is about six pixels
and every infill inside it resolved to the same two-pixel smudge.

This is the rig's lesson at a different scale. There, a pose reads from limb
*direction* and not from articulation, because at 46 px there is no room for
articulation. Here, a chair reads from its *outline* and not from its joinery.
So the styles vary silhouette instead -- low bentwood, tall and open, a top rail
overhanging into a T, a filled panel to two-thirds height -- and each draws its
own stiles, because height and overhang are most of the difference. Outline
survives downsampling; interior detail does not.

That immediately produced a legitimate occlusion report: a tall back covers 45%
of the chair opposite it at the same round table. Four chairs around one table
are placed as a unit at fixed offsets, so how much they overlap on screen is a
property of the group's geometry rather than of anyone's placement -- give one a
tall back and this is simply what happens. Members of the same group are now
exempt from `screen_occlusion`; two chairs from *different* tables landing on
each other is still a defect and still fires.

## Where the numbers landed

| | fourth pass | fifth pass |
|---|---|---|
| bible substitutions implemented | 2 of 3 | **3 of 3** |
| props in the reference room | 85, all hand-placed | **104, of which 19 generated** |
| distinct plant meshes | 2 | **one generator, a different plant per seed** |
| hand-written primitive calls in `assetlib` | 135 | **131, and the growth is now in generators** |
| surfaces with texture | none | **wood, plaster, foliage, fabric** |
| focal zone contrast lead | +0.094 | **+0.133** |

## Still open

- `assetlib.py` is still mostly hand-written primitive calls. `leafy_plant` and
  `chair` show what the replacement looks like -- one generator, a seed, and
  variation that costs nothing per instance -- but tables, counters, benches and
  the espresso machine are all still single fixed meshes.
- Stages 1–3 remain unbuilt. Everything here is still the deterministic render
  half — but the scatter solver is the first piece that *generates* rather than
  verifies, and it runs on the checks the earlier passes built.
- Grain is a single global amplitude per material. Wear should concentrate where
  hands and feet go, not spread evenly.

---

# Sixth pass — everything stops being typed

The fifth pass closed with three open items. Two of them were the same item
seen from different sides: `assetlib.py` is still mostly fixed meshes, and
grain spreads evenly when wear should concentrate. Both say the room is
described rather than grown.

Working through them turned out to be one job, not several. The floor's wear,
eight props, and finally the cast are all the same move — take something that
was written down and derive it instead — and every one of them turned up a
defect in the thing it replaced. Three of the metrics written to judge the
results were themselves wrong, in three different ways, and are worth as much
of this document as the work they were measuring.

The third open item, stages 1–3, needs a GPU and model weights and stays
unbuilt. But the *seam* they attach to did not need either, so it exists now:
`ingest.py` binds an arbitrary mesh to the palette and the tile grid. That is a
pipeline matter rather than an art one and it is written up in `PIPELINE.md`,
except for one finding that belongs here — three plausible ways to bind an
arbitrary colour to a palette ramp are wrong, and each is wrong on exactly the
case the previous one fixed.

## Wear is derived, not authored

Grain gave every wooden surface the same texture everywhere. That is what a
factory finish looks like; a floor looks nothing like it. Real wear is
concentrated — pale scuffed tracks in front of a counter and around every
chair, untouched boards under the furniture and in the corners.

The whole argument for tracking placements is that the room already knows
where people stand, because it knows where the chairs are. `rots` even
records which way each seat faces, so "in front of" is exact rather than
estimated. Hand-placing wear would be the same mistake as hand-placing the
dressing, one pass after the scatter solver made that argument.

`Layout.wear_field()` returns pools for the seats, the service run, and the
route from each till to each seat. Getting the routes right took three tries,
and the failures are the interesting part.

**The tills' centroid as one origin** put the fan's apex a couple of tiles
clear of the counter and left a bare stripe between the queue band and the
routes — across the one stretch of floor that is certainly walked on.

**One origin per placement** gave nine, because a six-module counter is six
placements and one counter. That is 207 routes, and the room came out
uniformly worn: the exact failure the field exists to fix, arrived at from
the opposite direction.

**Thinning the origins onto a 1.8-unit grid** gives the two service runs
there actually are.

There was a fourth attempt before any of those, which picked a single walkway
as the emptiest lane across the room. It is worth recording because it looked
principled and was not. The lane scores came out 4.6 against 6.9 over 23
candidates — a shallow minimum over what is essentially noise, so the walkway
would have relocated on any change to the dressing. Two real endpoints beat
one argmin.

Two implementation notes that were both defects first:

`at` takes the max over pools, so a stretch crossed by nine routes wore
exactly as much as one crossed by a single route, and half the room came out
uniformly faint. Cells now carry a traffic count and reinforce, which makes
the trunk darker than the fringe for the reason it should be.

The lift is denominated in **ramp steps**, not in grain amplitude. Tied to
grain it maxed at 0.086 against a step of 0.20, so the quantizer rounded
nearly all of it away and the entire field moved 2.5% of pixels. This is the
recurring shape of every bug in a quantized pipeline: an effect that is
perfectly correct in the continuous domain and invisible after rounding. On
steps it moves 5.2%, and the floor now has a value story — pale routes
through the middle, dark unworn boards at the corners and the near edge.

`WearField` bakes its plan view to a 0.12-unit grid on first query: 0.38 µs
against 27 µs exact. A few hundred hypots per lit pixel is a render's worth
of work spent re-deriving a field that does not change during the render.

## Tables became a generator

The room seats fourteen people at four tables, and every one of them was one
of two fixed meshes. Tables are the largest pieces of furniture in frame and
were still coming out of a catalogue of two.

`table()` varies the base — posts, splayed, pedestal, trestle — plus top
shape, thickness and overhang. What does *not* vary is anything inside the
outline, for the reason the chair backs recorded a pass earlier: interior
detail is gone by the time the frame is downsampled, and the silhouette is
not.

Raked legs needed a primitive the library did not have. `add_box` is
axis-aligned, which is why every leg so far had been vertical, and a splayed
member is most of what separates one furniture silhouette from another.
`strut()` draws a square-section beam between two points, keeping the
cross-section axis-aligned in x/y even when the member leans — a rotated
square section lands on the pixel grid at an angle and shimmers between the
eight azimuths, and at 27 px per unit a leg is two pixels wide, so there is
no cross-section detail to lose.

Three things the tables got wrong on the way:

**The base was laid out on the table's bounding box**, which under a round
top is not the top's outline. The splayed feet landed 0.57 from the centre of
a disc of radius 0.50 and stuck out past the edge they were holding up. The
base footprint is now derived from the top's shape.

**Leg thickness went from tree trunks to wire in one step.** 0.085 read as
trunks under a disc; the correction to 0.052 read as spider legs. Each base
style now scales the radius itself, because a lone raked leg carries more
load — and should look like it does — than one of four posts.

**Clutter sat at a hardcoded z.** Varying the top thickness without telling
anyone where the top ended up would leave every cup in the room floating or
sunk by up to 4 cm, and `grounded` would then have reported it as a placement
bug rather than as the generator's. `table()` returns its `top_z`.

## Two random-number bugs, in a pipeline whose whole value is reproducibility

The table generator gave seeds 1, 3 and 5 the same base style and 2 and 4
another. Seeding an LCG with `seed * k + c` and reading its top bits leaves
nearby seeds correlated, and the seeds in a room are consecutive integers.
`_mix()` is an avalanche step, so one bit of seed changes about half the bits
of state.

Mixing the seed fixed the *seeds* and left the *stream* weak: the chair's
second draw picks its back style, and over forty consecutive seeds one of
four styles came up 3 times against an expected 10. A generator whose variety
is that lopsided is barely a generator. `rnd()` now mixes per draw rather than
taking an LCG step, and the four table bases land at 24/21/18/17 over eighty
seeds.

Both of these were invisible in the room render. Four chairs of the wrong
four are still four chairs.

## The generator sheet, and a metric that was lying

`proof/generators.png` existed but nothing generated it — it had been made
ad hoc. That is a problem for a pipeline whose premise is that humans direct
and critique what the machine generates, because a generator is not
reviewable through one sample. The question about a generator is whether its
*range* is any good, and that needs a row.

`preview_generators.py` renders one row per generator and one column per
seed, through the shipping path. Where a row comes out as the same shape
eight times, the sheet says so directly instead of leaving it to be noticed
in a room render three passes later.

Its first metric was **distinct silhouettes**, and it reported 8/8 for every
row — including rows where the eye plainly saw one object. This is
`check_buried_detail`'s first metric all over again: distinctness is a
threshold at one pixel, so it measures whether anything moved rather than how
much. Jaccard distance between silhouettes measures magnitude, and it
separates the rows honestly:

| generator | silhouette spread |
|---|---|
| `table_round` | 19% |
| `bookshelf` | 18% |
| `table_4top` | 30% |
| `chair` | 34% |
| `chair, cushioned` | 41% |
| `plant_small` | 47% |
| `plant_large` | 53% |

The furniture generators produce meaningfully but modestly different shapes;
the plants are genuinely different objects each time. That gap is real and
the old metric hid it behind a row of 8/8.

The measurement then became the twelfth check. A contact sheet needs someone to
look at it, and the failure this catches is invisible in the thing anyone
actually looks at: a room full of furniture renders perfectly whether or not
the furniture came from a working generator. `check_generator_range` fires at
0% spread on a seed that is accepted and ignored, and at 0% on a style table
one branch wide, which are the two ways this rots. The floor is set at 12%,
under the furniture's measured 17% rather than at it -- the check is there to
catch a dead generator, and tightening it toward the plants' 41% would be
asserting that cafe chairs ought to vary as much as houseplants, which is a
taste call nobody has made.

## The bookshelf, and a metric that was wrong in the other direction

The books were one `FABRIC` box per shelf -- three coloured slabs, in the one
object in a cafe that has an obvious reason to carry a dozen unrelated hues.

Modelling individual spines does not survive the room.
`check_member_thickness` puts the floor at 4 px, which at 27.2 px per unit is
0.147 of a tile, so a modelled spine is as wide as a hand and a shelf holds
four of them: a shelf of ledgers. So the crate's idiom, which was invented for
exactly this. The block is real geometry and steps in height, and the spines
are flat quads a thousandth of a unit proud of its face at different ramp
steps. Nothing can be thinner than a pixel because nothing is being modelled,
and nothing can leave the palette because a ramp step is all a spine ever is.

Then the new check reported the seeded bookshelf at **0% spread**, and it was
right twice over for two different reasons, neither of them the one I assumed.

**The metric was measuring the wrong thing.** It compared silhouettes, on the
argument that the outline is what survives the downsample. That is true of a
chair and false of a bookcase: an open-fronted carcass has the same outline
whatever is on its shelves. Resolving *materials* per pixel subsumes the
silhouette case -- an uncovered pixel is a pixel whose material is None -- and
counts a change of interior as the change it is. Every generator's number went
up, the chair from 22% to 34%, which is the metric finally seeing detail that
was there all along.

**And the spines were genuinely invisible.** At 0.018-0.048 wide they were
sub-pixel at room scale throughout: aliasing between azimuths and contributing
almost nothing to any frame. Being drawn as value rather than geometry exempts
a detail from `check_member_thickness`; it does not exempt it from the pixel
grid. They are 0.076-0.128 now, and divided across the shelf rather than laid
left to right until one will not fit -- which had been leaving a third of every
section bare, reading as a gap rather than as a book.

## Winding, which nothing could have caught

Underneath both of those was a third defect. The spine quads on the shelf front
were written (left, right, up, back), which is the order anyone writes, and
that produces a normal pointing *into* the carcass. Culled by every visibility
check in the tree. Lit against a normal facing away from the key light in the
passes that do not cull. And perfectly convincing on a contact sheet, which is
how it survived being written.

A scan of the whole library turned up no other case -- `flower_vase` reports 48
faces pointing away from every azimuth, and they are the far hemispheres of
three spheres, which is what a closed sphere is. So rather than build a check
with a known false-positive class for a bug that has occurred once,
`add_quad` now takes an optional `facing` vector and flips the winding itself.
One argument, and the mistake stops being writable. The boxes, prisms and
cylinders do not pass it, because their winding was fixed and verified at the
point they were written.

## The counter run, and which face is the front

Nine identical boxes -- six service modules and three window-bar modules --
make the single largest mass in frame, and the front of each was one flat face
at one ramp step. That is the most blockout-looking thing an interior can put
on screen at that size.

The treatments are drawn as value, never as geometry, for two reasons beyond
the usual one: the modules have to keep tiling flush, and anything modelled
proud of the front is the first thing a customer walks into.

What the counter turned up that the bookshelf did not is that **the front is
not always +y**. The service run tiles along x, so its front is the +y face.
The window bar tiles along *y*, so its +y face is the joint between two
modules, and detail put there is sealed inside the run -- present in the mesh,
paid for in triangles, and never once rendered. The camera sees +x and +y, but
which of those a given object presents depends on how its neighbours are laid
out, and only the room knows that. So `front` is a parameter.

The style table lists plain twice out of six. A run with four distinct fronts
in six modules reads as a showroom rather than as a fitted counter, and the
failure mode of a generator is not always too little variety.

Choosing where the run *starts* stayed the room's job. At seed base 4 the six
modules come out drawers / shelf / plain / plain / beaded / plain; most bases
give four plains in six, and a few give three different fronts in a row. The
generator is equally correct either way -- what a run opens on is composition,
and composition is placement.

The first version drew all of it one ramp step down from the carcass, and the
generator sheet showed eight modules that were, to the eye, identical. One step
is enough to break a flat field -- that is what grain is calibrated to -- and
not enough to say "this is a drawer and that is a shelf" at 27 px per unit.
Panels went to two steps and the recess to four, and the measured spread went
from 2.6% to 7%. The point is that the sheet caught this and the room render
had not: a counter partly hidden behind three customers can look busy while
carrying no information at all.

And it forced the check to grow a per-generator floor. A counter module
measures 3% spread, which is not a bug: the front is one of three faces this
camera sees, and the style table is weighted toward plain on purpose. A single
threshold cannot express both "a plant that stopped varying is broken" and "a
cabinet that varies like a plant is broken". Every relaxed floor now carries
the reason it is relaxed, the same role `ACCEPTED_BURIAL` plays for occlusion,
and the relaxed one still bites -- point `counter` at an unseeded mesh and it
fires at 0% against its own floor. That floor is set at 4%, under the measured
7% rather than at it -- the same calibration discipline the occlusion
thresholds needed, where defaults chosen looser than the scan that found the
defect left the check blind.

## Three ways to bind a colour, all wrong

`ingest.py` is pipeline plumbing and lives in `PIPELINE.md`, but one part of it
is a colour problem and belongs here. Given an arbitrary RGB from a generated
mesh, which palette material is it?

The obvious answer — nearest colour — is the one answer that must not be
used. Everything downstream is built on one material meaning one ramp: grain
resolves by ramp, tone offsets compose within a ramp, `check_palette_spread`
counts ramps per character. A binder free to trade lightness against hue would
scatter a single object across three ramps wherever a shadow fell near a step
of something else, and hand all of that a mesh it cannot reason about. So the
ramp has to be chosen as an *identity* and the step as a shade of it.

Three attempts at "identity", each broken by the case the last one fixed:

**Hue angle, with a chroma threshold forcing greys to `neutral`.** Wrong
because `neutral` in this palette is not achromatic — it is a cool violet-grey
at chroma 0.016–0.022, so a threshold anywhere near its own chroma swallows
every quiet colour in the palette. A warm off-white bound to `neutral+2` at dE
0.124 with `cream` sitting two steps away. Worth noting how invisible this
would have been in a render: `neutral+2` is a perfectly reasonable colour for
an off-white object.

**Each ramp's chroma-weighted mean (a, b).** Fixed the off-white and broke dark
colours, because chroma is a function of lightness. A dark brown carries about
a third the chroma of a mid brown, so comparing it against `wood`'s overall
signature put it nearer pale `cream`, and (60, 45, 35) bound to `cream-2` at dE
0.408.

**(a, b) at each ramp's step nearest in lightness.** Still bound that brown to
`cream-2`, because `cream` has no dark end: its "nearest" step was 0.41 away in
L, and the chromaticity comparison was being made between two colours nowhere
near each other in value. A ramp that cannot reach the source's lightness was
competing as though it could.

What works is treating a ramp as a **curve** rather than a set of colours, and
measuring distance to the polyline. The nearest point on a curve that stops
short *is* its endpoint, so a ramp is charged for the lightness it cannot
reach, and no threshold is needed anywhere — a grey lands on `neutral` because
`neutral` is the nearest chromaticity, which is the honest reason rather than a
special case.

## Seven more generators, and a thing that is not a silhouette

`table`, `chair`, `bookshelf` and `counter` covered the furniture a person
looks at. What was left was the stuff a room is *filled* with, and the scatter
solver had quietly made that worse: it places crates, baskets, cups and vases
by the dozen, and every one of them was the same mesh, so raising the density
had multiplied the repetition rather than hiding it.

Most of these have no silhouette worth varying. A crate is a box. What one
crate has that another does not is its height, how far its carcass is inset,
and how many bands divide it -- three numbers, and that is the whole of it. A
stool is a disc on a post, so height is nearly all of it, plus a foot ring on
about half of them, which is four pixels and the only thing that tells two
stools of the same height apart.

The vase was the one worth doing properly. Three identical vases on three
tables is the same tell as three identical plants and slightly worse, because
a vase of flowers is the object in a cafe that most obviously came from
somebody choosing them. It now grows two to four stems at a random turn, each
with an actual stem rather than a head hovering above a neck, and it measures
62% spread -- the most varied thing in the library.

The crate then repeated the table's mistake before it was even placed: it
gets *stacked*, and once its height varied, whatever sat on it floated. The
same `top_z` fix, for the same reason -- a generator that changes a dimension
without saying so leaves `grounded` reporting a placement bug that is really
the generator's.

The dressing pass dropped from 19 placed props to 18 with nothing else
changed, which is the solver doing its job: crates and baskets of varying size
no longer all fit where uniform ones did.

| generator | screen spread |
|---|---|
| `counter` | 7% (floor 4%) |
| `bookshelf` | 18% |
| `table_round` | 19% |
| `stool` | 21% |
| `basket` | 30% |
| `table_4top` | 30% |
| `crate` | 32% |
| `chair` | 34% |
| `chair, cushioned` | 41% |
| `plant_small` | 47% |
| `plant_large` | 53% |
| `flower_vase` | 62% |

## The roster stops being typed

Nine hand-written character specs were the largest asset left in a repo that is
supposed to be a factory, and characters are the thing it exists to produce. A
game wants forty extras, and nobody should be choosing forty pairs of trousers.

`generate_spec` proposes a character and tests it. That is the whole design,
and it is the same move `Layout.scatter` made with `collisions` and `grounded`:
`check_contrast` and `check_palette_spread` were both promoted from human
rejections and are both predicates on a finished spec, so running them *before*
accepting a proposal turns two graders into a solver.

**The first version cheated, and measuring caught it.** It offered seven hair
tones, all hand-picked to pass contrast against a mid-wood skin, and across 200
generated specs `check_contrast` fired exactly **zero times**. That is a random
draw with a check bolted to the side: the constraint had been solved by hand,
and the check was decoration. Offering every offset of every plausible hair
ramp instead -- including the mid browns that vanish into a face -- makes it
reject 43% of proposals, and it is the check rather than a person that decides
which twelve of twenty-one tones are usable.

The ramps stayed a choice, and the offsets did not. That distinction is the
line between art direction and constraint solving. `rose` was in the hair list
for one run and the generator put pink hair on an extra, which is a costume
this art direction does not make -- so `rose` came out. Which *shades* of brown
work is not a taste question and belongs to the check.

## And then the generator found a defect in the hand-written roster

Looking at the first sheet of extras, one had a rose shirt over rose trousers
and rendered as a single pink column. `check_palette_spread` passed it at
exactly its 50% limit, correctly: it counts **ramps**, and its job is to stop a
figure being built entirely from one. It cannot see two different ramps landing
on the same value.

`check_waistline` compares shirt and trousers in OKLab L, at a floor of one
ramp step. Run against the roster it had never been near, it failed two of the
nine archetypes immediately -- `elder` shipped with a wood shirt **0.004** in
value from neutral trousers, and `friend` foliage over rose at 0.020. Both had
survived five passes of human critique.

This is the ratchet running in a direction it had not run before. Every check
so far was promoted from a person rejecting something. This one was promoted
from a person rejecting something *the machine made*, and it then found two
defects in what the people had made. At 46 px of figure the waist is one edge,
and losing it costs more than any of the detail this pipeline spends triangles
on.

The seventeenth is the same argument one level up. Those three checks are all
predicates on *one* spec, so a generator can satisfy all of them forty times
and hand back forty variations of one person. `check_roster_variety` measures
the **minimum** pairwise distance on screen rather than the mean, because a
mean is dominated by the pairs that are already fine and says nothing about the
two that collide — and it is those two a player notices.

Its floor was guessed at 20% and would never have fired. Measured, the nine
hand-written archetypes have a closest pair at 45% and twenty generated extras
at 48%, both with medians around 80%, so it sits at 38%: under the evidence
rather than at it, which is the discipline the occlusion thresholds needed two
passes ago. Two specs differing only by one step of shirt colour measure
exactly 38% and are rejected, which is the right place for the line.

The measurement also says something worth recording. The generated cast came
out *more* varied at its closest pair than the hand-written one — nine
archetypes written by a person include two that are nearly the same person, and
nobody noticed across five passes of critique.

The sixteenth check is the other half of that: the generated extras have to
pass everything the hand-written roster does. They are proposed against exactly
those predicates, so a failure there means the solver has stopped consulting
one of them -- which is invisible on the sheet, because a sheet only shows what
was accepted. Disable one predicate in the solver and six of twelve extras fail
downstream.

## Where the numbers landed

| | fifth pass | sixth pass |
|---|---|---|
| bases the tables can be built on | 2 fixed meshes | **4 styles × top shape, thickness, overhang** |
| seeded generators in the library | 3 | **11** |
| hand-written character specs | 9, and no way to make a tenth | **9, plus a solver that makes as many as asked** |
| floor texture | one amplitude everywhere | **derived from where the seats and tills are** |
| high-key share of frame | 63.8% | **66.7%** |
| generator range | unmeasured | **measured, per generator, with a floor each** |
| the seam stages 1–3 attach to | described | **built, and checked from both ends** |
| automated checks in the ratchet | 11 | **17** |

Median L, chroma and the extremes are unmoved, the checks stay clean, and the
render is still byte-identical across processes.

## Still open

- The espresso machine, bench, armchair and pastry case are still fixed
  meshes. Eleven others show the shape of the replacement, and these four are
  the props the room holds exactly one of — which is why they are last, not
  why they are fine.
- The extras are now checked against each other as well as individually, but
  only in one direction. Nothing measures whether a generated cast is varied in
  the ways that *matter* rather than merely different — twenty extras could
  differ only in shirt colour and clear the pairwise floor comfortably while
  reading as one silhouette repeated twenty times.
- `ingest.py` binds an arbitrary mesh to the palette and the tile grid, so the
  seam stages 1–3 attach to now exists and is checked. Nothing feeds it yet,
  which is exactly why it needed checks: an adapter that is never exercised is
  an adapter that is wrong by the time something arrives.
- Stages 1–3 (SDXL concept → TRELLIS 2 mesh → UniRig rig) remain unbuilt.
  Everything here is still the deterministic render half.
- Furniture screen spread sits at 19–34% against the plants' 47–53%. That is
  not obviously wrong — a cafe buys chairs from a catalogue and a greenhouse
  does not — but nobody has decided what the target is, and an unowned number
  drifts.
