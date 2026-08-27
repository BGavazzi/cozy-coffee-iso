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

## The accessory that was not there

The open item from the last section was that nothing measured whether a cast
varied in the ways that *matter*. Measuring it took one function and produced a
worse answer than expected: over the eight sprite directions, with materials
discarded so only coverage remained, the nine hand-written archetypes had a
closest pair at **4.3%** and twenty generated extras had a pair at **0.0%** —
two figures whose outlines matched to the pixel.

`check_roster_variety` had been passing both casts at a floor of 38% the whole
time. It compares materials as well as coverage, so two identical shapes in
different shirts disagree on most of their pixels and score as different
people. The metric was not wrong, it was answering a different question, and
the question it was not answering is the one that survives a downsample.

### The fix that did nothing

The first attempt was `silhouette_key`: a tuple of the parameters believed to
change the outline — hair style, accessory, bulk in 0.06 buckets — with the
roster built incrementally and a proposal rejected if its key was already cast.

It produced output byte-identical to the unmodified generator. Twenty extras
gave twenty distinct keys, so the rejection never fired once, while the cast
still contained the 0.0% pair. The two colliding characters had *different*
keys: `('cap', None, 20)` and `('cap', 'cup', 20)`. They differed by an
accessory, and the accessory was worth nothing.

This is worth stating plainly because the mechanism looked right and was
inert. A key is a guess about which parameters reach the outline, standing in
for the outline. At 3.6 ms a view there was never a reason to guess —
`screen_materials` already renders the figure that the checks grade, so the
generator can grade the same render.

### Three of four accessories did not exist

Measured against the same figure with no accessory, as a share of pixels
changed, averaged over the eight directions:

| accessory | before | after |
|---|---|---|
| `scarf` | **0.0%**, at every azimuth | 10.7% |
| `cup` | 1.2% | 21.7% |
| `bag` | 12.8% | 12.8% |

The scarf was a prism at 0.86 of the torso radius — drawn *inside* the body it
was supposed to be wrapped around. Widening it to fill the neck did not help
either: a collar at 0.202 still measured 0.0%, because the head above and the
shoulder cap below already close that gap at every angle. **An accessory only
exists in outline once it beats the widest part of the figure.** Past the
0.2475 shoulder the numbers climb steeply, and 0.295 reads as a knitted wrap.

A tail hanging down the front was added on the assumption it would break the
profile, and it is worth 1.8 points against the collar's 10 — because +y near
the centreline projects *inside* the torso's screen width at every diagonal
view. Sticking out toward the camera is not sticking out.

The cup had a second problem underneath the first. It lived in the body mesh,
so it stayed at the hip through every frame of a walk while the hand supposedly
holding it swung away. Held accessories now merge into the arm and pose with
it, and the arm takes a standing forward swing, which is both the fix for the
animation and the reason the cup is now the strongest accessory in the set: it
is out in front of the chest where nothing else on the figure is.

Chasing that turned up a third thing. The `Pose` docstring says positive swings
a limb forward; measured, negative does, on arms and legs alike. No clip caught
it in six passes because a walk cycle swings symmetrically.

### And the hand-written roster again

With the accessories fixed, the generated cast went from 0.0% to 8.5% at its
closest pair and the hand-written one went to 4.3% — now the worse of the two,
for the second pass running. `reader` and `friend` were both a bob at bulk 1.0,
one with a scarf and one without: the same person, and the scarf had been
invisible. Seven of the nine archetypes are bulk exactly 1.0.

Rather than pick a repair, the fix was searched: every hair style × accessory ×
bulk for that one slot, scored on its distance to the rest of the cast. A cap
at bulk 0.90 with no accessory scores 14.2% against the 4.3% it replaced, and
keeps `friend` the plain figure it was written to be. The roster minimum is now
**10.0%**.

Widening the scarf then pushed the seated `reader` over the 35% occlusion floor
against the pastry case two tiles behind it, which is the check doing its job:
a figure that got bigger occludes more. The case moved 0.3 of a tile.

`check_cast_silhouette` is the eighteenth check, floored at 7% — under the
8.5% and 10.0% the two casts now measure, and well above the 0.0%, 1.3% and
4.3% it was written for.

## The last four fixed meshes, and a search a person was doing by hand

The armchair, the bench, the espresso machine and the pastry case were the four
props the room holds exactly one or two of, and they had stayed fixed meshes
for six passes on the reasoning that a prop appearing once does not need a
range. That reasoning is wrong for a factory. A generator that can only make
*this* cafe is a description of this cafe.

They vary in the three things that are the outline and in nothing else:

| generator | screen spread over 8 seeds |
|---|---|
| `armchair` | 45% |
| `bench` | 38% |
| `espresso_machine` | 33% |
| `pastry_case` | 22% |

The armchair is the widest range in the library after the plants and the vase,
and the reason is one style out of four: `_arm_none`. A slipper chair shares no
outline with a club chair, and the temptation with an armchair generator is to
make four kinds of arm. A generator whose every output has arms has three
settings.

Two things are deliberately *not* varied. The espresso machine and the pastry
case keep their width, because both are fitted to a counter run of one-tile
modules and a generator free to resize a built-in will eventually hang it off
the end. And `seed=None` reproduces the old fixed mesh vertex-for-vertex on all
four, checked against the previous commit — the pastry case failed that on the
first attempt, because dividing three pastries evenly across the case is not
where three pastries used to be.

### The search a person was doing by hand

Seeding the pastry case made it taller. The taller case covered 39% of a crate
two tiles behind it, `screen_occlusion` said so, and the fix was to print the
case height for eight seeds and type in one that passed. Then seeding the
espresso machine gave it an optional raised back panel, the panel covered 41%
of a menu board, and the fix was about to be the same thing again.

That is a person running a search, and the search is what this file has been
converting into code for two passes. `Layout.scatter` solves for a *position*
with the seed fixed. `Layout.add_seeded` solves for a *seed* with the position
fixed, which is the case a fitted prop actually has: the espresso machine goes
where the counter is, and what is free to vary is which machine it is. Both run
the same `_conflicts` predicate, so the rule that rejects a proposal is the rule
that would have failed the render.

It rejects seed 1 for both counter props and settles on 2 and 4. The four seats
pass on their first try, which is the correct outcome for a solver and not
evidence it is idle — `scatter` returning a full count is not a bug either.

What this exposed is worth more than the two seeds. **Both collisions were
between two hand-placed props.** `scatter` has tested occlusion at proposal time
since the fifth pass, and neither of these ever went through it, so the room had
a whole class of placement that only the after-the-fact check could see. The
ordering matters too, and it is a real constraint rather than an implementation
detail: `add_seeded` can only solve against what is already in the room, so the
pastry case is now placed after the crates and the espresso machine after the
menu boards, out of the tidy blocks they read best in. A prop that has to clear
its neighbours goes in after them.

## The room was the last authored asset

Six passes went into turning the things *in* the room into generators. The room
itself was still 249 lines of code holding 48 hand-written coordinates:
`assetlib` could make any number of chairs, and there was exactly one place to
put them.

`floorplan.py` proposes a plan — room size, glazing, which wall the service run
takes, where the seating goes — and tests it. What comes out is zones, not
props: a plan says "a lounge belongs in this rectangle facing this way", and
the existing generators fill it. Eleven rules, each one demonstrated to fire
against a deliberately broken plan before being trusted, because a rule that
has never rejected anything is indistinguishable from a rule that cannot.

Circulation is the one that needed a real algorithm. Two zones can leave a
legal-looking 1.4-wide gap that is a dead end, and a corridor can be wide at
both ends and pinched in the middle; neither is visible in a comparison of
rectangle edges. So the floor is eroded by a body radius and flood-filled from
the door, and every seating zone has to be in the result. `proof/floorplans.png`
shades that region underneath everything else, because it is the only rule here
that cannot be reviewed by reading the numbers.

### A search that rejects everything is not a strict search

The first generator drew the run and the windows independently and cut the
seating out of a "free area" that did not know which wall the counter was on.
It passed **6 proposals in 2157**, and the two failures it kept re-drawing were
both ones it had the information to avoid: the back bar crossed the glass 4754
times, and the seating landed on the till or the queue 5900 times.

That is not the solver being strict, it is the proposal being uninformed, and
the difference is not cosmetic. `generate` returns its least-bad attempt rather
than looping — the bargain `scatter` makes when a region runs out of room — so
**21 of 60 seeds were returning a plan that failed its own rules**, silently,
because a fallback looks exactly like an answer. Choosing the windows around
the back bar and cutting the seating from the floor the service band actually
leaves took acceptance from 0.3% to 78% and the plan cost from 790 ms to 6 ms.

### Two thresholds that were quietly choosing the layout

The sheet showed five plans in six with the counter on the same wall. The
measurement said horizontal runs were accepted at 2.8% against vertical at
12.5%, and the cause was the daylight rule: a horizontal counter eats 3.2 tiles
of depth, so every seat below it is out of reach of the only wall on that side
with glass in it. The rule was right and the layout was wrong — a five-tile
counter on a fourteen-tile wall leaves nine tiles of window, and that is where
a cafe puts its seats. Seating now takes the strip beside the run as well as
the one below it.

Then the rule itself turned out to be a cliff. It asked whether a zone's *near
edge* fell within reach of a window, which made a block spanning y 3.6–8.0
exactly as dark as one spanning 6.0–8.0: a threshold standing in for a
quantity, the same mistake the silhouette metric made when it counted distinct
outlines instead of measuring how far apart they were. Measured as lit area
instead, the bias inverted rather than vanishing — 48 plans against 12, the
other way.

What settled it was asking what the exemplar scores. **The reference room — the
only cafe here that six passes of art direction have signed off on — puts 30%
of its seats within daylight reach, and 27% by footprint area.** The floor was
set at 45%. A threshold above the known-good case is as wrong as one below the
defect, and it is the more dangerous of the two, because it does not look
blind. It looks strict. At 22% the acceptance rates are 72% and 60%, the wall
mix is 38 to 22, and the generated plans come out slightly better lit than the
room they were calibrated against.

| | before | after |
|---|---|---|
| proposals accepted | 0.3% | **67%** |
| seeds returning a plan that fails its own rules | 21 of 60 | **0 of 60** |
| cost per plan | 790 ms | **7 ms** |
| service run on the wall the rules preferred | 5 in 6 | **38 / 22** |
| largest single seating block | 93 tiles | **24, capped at 34** |
| mean layout distance between plans | unmeasured | **43%** |

`check_plan_range` takes the **mean** pairwise distance where
`check_roster_variety` insists on the minimum, and that is a real distinction
rather than an inconsistency: a cast of extras stands in one room together, so
the two that collide are the two a player sees. Two floor plans are never in
frame together. The closest pair over forty seeds is 6% and that is not a
defect.

The reference room stays hand-authored. It is the exemplar a person critiques,
six passes of art direction live in its coordinates, and it is now also the
thing the plan rules are calibrated against — which is a better job for it than
being the only room the pipeline can make.

## And then something rendered one

A plan generator with no consumer is an adapter, which is the position
`ingest.py` is still in and the reason both needed checks before anything fed
them. `build_plan.py` fills the zones: the counter run tiles along the service
zone, the seating comes from `Layout.scatter`, the fitted props from
`add_seeded`. No coordinate in that file is a number about a particular room —
everything is derived from a zone — and that is the whole difference between a
room and a room generator.

`render` had to be extracted from `render_room.main` first, and it had to be
the *same* function rather than a similar one: the material-id mapping, the
outline pass and the crop between them are three places a second copy would
drift, and a proof image rendered through a near-copy of the shipping pipeline
is not proof of anything. The reference room came out byte-identical after the
extraction.

Five things went wrong, and four of them were caught by checks written for
hand-typed work three passes ago.

**Two of the four chair rotations were backwards.** A chair's back is at −y, so
the side seats needed 270 and 90 and got 90 and 270. `seating_faces_tables`
reported it on every side chair in every room — 8 to 14 failures per room on
the first run. A check written to grade rotations somebody typed caught the
same mistake made by a loop.

**The solver was looser than its own validator.** Two vases scattered onto
tables were accepted at proposal time and reported as floating afterwards,
because `grounded` allows 0.03 of gap and the support test inside `_conflicts`
allowed 0.06. A solver whose predicate is weaker than the check it exists to
satisfy is not a solver, it is a source of warnings. One constant now.

**Ordering, three more times.** `add_seeded` can only solve against what is
already in the room. Menu boards hung after the espresso machine were boards
the machine never had to avoid, and 38–47% of one was covered in seven rooms
out of twelve. Moving them earlier did not fix it either: the machine is 2.0
tiles wide whatever its seed, so no seed moves it off the board. **When the
solver has no move to make, the constraint belongs in the proposal** — the same
conclusion the floor plan reached about its windows and its back bar. The
boards now start past the machine.

**Approximating a rule instead of asking it.** Denser scatter put chairs
between two tables, serving one and backing onto the other.
`seating_faces_tables` judges a seat against whichever table is *nearest*, so
the obvious fix was a "is my table the closest one" test at placement — and it
left one chair in twelve rooms still failing. Calling the real predicate on the
candidate leaves none. Reimplementing a validator inside the solver that is
supposed to satisfy it reproduces its conclusion approximately, which is the
one thing a constraint solver may not do.

**And the focal box was degenerate, from the other direction.**
`focal_report`'s own docstring records a mis-projected box giving a contrast of
exactly 0.000 — "a number a real region cannot have". Handed a box padded out
to the customer side, it gave the focal region and the rest of the frame
*identical* readings of 0.546. Two regions agreeing to three decimals is the
same tell as one impossible number: the box had grown until inside and outside
were the same sample. Sized to the counter the way the reference room's is
written by hand, the generated rooms read +0.039 to +0.093 of contrast against
the reference room's stable +0.133.

| | reference room | generated from a plan |
|---|---|---|
| coordinates typed by hand | 48 | **0** |
| props | 104 | 51–83 depending on the plan |
| collisions, floating, facing, occlusion | 0 | **0 across twelve rooms** |
| focal contrast lead | +0.133 | +0.039 to +0.093 |

The reference room is still the better room, and saying so is the point. It
holds six passes of judgement that no rule in `floorplan.py` encodes — why the
queue runs across the view rather than into it, why the crates go against the
far walls, why one bench is pink. What the generator has is that it can make a
different cafe, and that every one it makes satisfies twenty-one checks a
person had to be surprised by first.

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
| seeded generators in the library | 3 | **15** |
| hand-written character specs | 9, and no way to make a tenth | **9, plus a solver that makes as many as asked** |
| floor texture | one amplitude everywhere | **derived from where the seats and tills are** |
| high-key share of frame | 63.8% | **66.7%** |
| generator range | unmeasured | **measured, per generator, with a floor each** |
| the seam stages 1–3 attach to | described | **built, and checked from both ends** |
| automated checks in the ratchet | 11 | **21** |
| closest pair in the cast, by outline alone | 0.0% and 4.3%, unmeasured | **10.1% and 10.0%** |

Median L, chroma and the extremes are unmoved, the checks stay clean, and the
render is still byte-identical across processes.

## Still open

- The generated rooms are dressed but not *composed*. Every check passes and
  the counter leads the eye, but nothing decides that the crates belong against
  the far wall rather than the near one, or that a bench wants a different ramp
  from the four chairs beside it. Those are the judgements the reference room's
  48 coordinates are actually made of, and the ratchet has not caught up to
  them because nobody has yet been surprised by their absence in a way that
  could be written down as a rule.
### And the two generators met

A generated room is now occupied. The cast is `C.generate_roster`, so the
character solver makes people the room has never seen and the room solver sorts
them into the three places a cafe's occupants go — the staff side of the run, the
queue band, and whatever seats got placed. Neither generator knows about the
other; the plan supplies all three.

The queue is stepped along the screen-horizontal, which is the reference room's
finding reapplied: two customers 1.5 tiles apart in world space sat 0.1 apart on
screen and the near one hid 74% of the far one. Occupants also fixed the focal
reading — the barista puts skin and a dark apron right where the eye is supposed
to land, and the counter's contrast lead went from +0.054 to **+0.101**.

One defect here is invisible to every check in the ratchet. `C.build(seated=True)`
authored the legs about a hip at SEAT_Z 0.45 whatever it was sitting on, so a
customer put on a 0.70 bar stool is ground-clamped, does not float, and sits in
mid-air beside it at dining height. `grounded` asks how far an underside is from
the floor, and there is nothing wrong with the answer.

The rig now takes its seat height, which mattered for armchairs too: their
cushions land anywhere from 0.48 to 0.52 once the base style and seat jitter are
applied, so every seated figure had been sitting up to 0.07 inside one. Stools
stay unoccupied on purpose — a person on a bar stool is held up by their
backside with their feet on a rail, and that is a different support model, not a
longer shin.

Getting the seat height took a second fix underneath the first. Reading it from
the placement's bounding box gives the top of the *backrest*, 0.95, which
excluded every chair in the room from the filter and left the rooms with three
occupants. `chair` and `armchair` now report `seat_z` the way `table` reports
`top_z` — the same lesson as the clutter that sat at a hardcoded height while
the table thickness varied underneath it, arrived at from a third direction.

- Bar stools and benches are still never sat on, because perching needs a
  support model `grounded` does not have: a figure held up by its hips has no
  underside meeting anything.
### A number that says a generator moved, and a sheet that says where

`check_plan_range` measured the plan generator at 43% mean layout distance and
said nothing, which was correct — 43% is a real spread. What a scalar cannot
say is that the whole spread sits *inside* one idea, and a contact sheet of six
plans made that obvious in a second: a straight run against a far wall with the
seating in strips, six times. This is the same relationship the generator sheet
has to `check_generator_range`. The number says a generator moved; the sheet
says whether it had anywhere interesting to move to.

A second seating topology answers it. Perimeter blocks hug the walls and leave
the middle clear, which is what a cafe does when the floor is wide rather than
long — and it is a different room rather than a reparameterised one, because the
circulation runs through the centre instead of down aisles between blocks. Mean
layout distance goes to **50%**, and two plans in six now read as the other kind
of cafe.

- The plan generator still puts its counter in a straight run against a far
  wall. An island, an L-shaped run and a counter that faces the door are all
  cafes it cannot propose, and an island in particular would change the
  circulation problem rather than the furniture arrangement — you can walk
  round it, and the flood fill would have something to say about that.
- Cast variety is now measured on shape as well as colour, and the generator
  solves for it. What is still unmeasured is whether an accessory or a hair
  style is *distinguishable* rather than merely present: the scarf went from
  0.0% to 10.7% of outline, which proves it exists, not that a player can tell
  it from a collar. That needs a different instrument.
### Two more numbers a character is allowed to be

Bulk had been the only continuous shape parameter a character has, and seven of
the nine archetypes sit at exactly 1.0 of it. `leg_len` and `stance` are the
other two, both measured against the outline before being given a range rather
than after — the discipline the accessories had to be taught: 0.88 of leg is
worth 4.5% and a stance of 1.40 about 4%, the same order as an accessory.

Leg length moves the *hip*, not the figure. Scaling the whole character would
scale the head, and a scaled head reads as a child rather than as a tall
person; the ankle stays on the floor and everything above the hip rides up. It
does nothing at all when seated, which is correct — hips sit at the seat
whatever the legs are — and the seated rig is unchanged to the vertex.

The generated cast's closest pair went from 8.5% to **10.1%**, which is the
generator's own early-exit floor, so the solver is now working right up to its
target. Raising that floor to 14% buys 0.8 of a point for three times the
search, which is where this stops paying.
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

---

# Sixth pass — three composition questions that came back clean, and the one that did not

The open note said generated rooms were *dressed but not composed*: nothing
decided that crates belong against the far wall, or that a bench wants a
different ramp from the chairs beside it. That is a claim, and it had never
been measured. Four ways of measuring it, three of which said the claim was
wrong.

## Depth staging: already there

Tall things belong upstage. Measured as the height of every prop against its
screen depth, in thirds of the floor:

| | far third | middle | near third |
|---|---|---|---|
| reference room | mean top 1.09, max 1.93 | 0.83, max 1.49 | 0.80, **max 1.14** |
| 12 generated rooms | 0.92, max 1.93 | 0.86, max 1.93 | 0.70, **max 1.23** |

Both stage the same way and the generated rooms actually keep the foreground
*lower*. Three props in twelve rooms broke the reference's 1.14 ceiling. The
one apparent difference — a 1.93 prop mid-room, where the reference tops out at
1.49 — turned out to be the espresso machine and the back bar of a peninsula,
which are mid-room because a peninsula is mid-room. No check written.

## Ramp balance: a proxy that lied

By face count the generated rooms looked badly off: **43–47% foliage** against
the reference's 30%, with cream collapsing 13% → 6%. That is a real number and
it means nothing. Plants are high-poly and low-pixel; a fern is a hundred faces
you can barely see.

By rendered pixel, classified to the nearest palette entry:

| | neutral | wood | cream | foliage | rose | sky |
|---|---|---|---|---|---|---|
| reference | 43 | 35 | 13 | 4 | 2 | 2 |
| strip room | 44 | 38 | 11 | 3 | 3 | 1 |
| peninsula | 43 | 38 | 11 | 4 | 2 | 2 |
| perimeter | 43 | 39 | 10 | 3 | 2 | 2 |

Within four points everywhere. This is the same lesson the silhouette key
taught — *measure the render, not the proxy* — arriving from the opposite
direction: there the proxy said everything was fine when it was not, here it
said everything was broken when it was not.

## Accent distribution: also there

An accent that clumps in one corner is decoration; an accent spread across the
frame is composition. Counting eighth-of-frame cells containing any rose,
foliage or sky pixel: reference **59%** of occupied cells, generated rooms
53%, 58%, 61%. No difference to find.

## Focal contrast: the one real gap

The counter did read as the centre, but by less than the reference did, and the
two weakest rooms were the two with the most ceiling lamps. The rig gave every
seating zone over 8 m² its own lamp, which in a finely-divided room is a lamp
per 36 m² against the reference room's one per 45. Every one of them lifts the
periphery that the negative pools exist to sink. **A room does not light itself
more brightly for having been divided more finely.**

Lamp count now comes from the floor's area and goes to the biggest zones, and
the rig takes light out of three corners rather than two, as the reference
does. Contrast over five seeds **+0.098 → +0.110** on the old focal box and
**+0.103 → +0.114** on the new one — the same +0.012 either way, which is what
makes it the rig and not the instrument.

The focal box itself was wrong for a peninsula, for the same reason the
shelving was: it assumed the counter backs onto a wall, so it swept a strip of
empty floor into the focal region. It now comes from the run and the back bar
together. Changed because the old box was wrong, not because the new one reads
higher — an instrument chosen for its reading is not an instrument.

## The focal check was measuring a picture nobody sees

Committed at a render size of 160, chosen because one seed read the same there
as at 240. Swept properly over three seeds and three sizes it does not agree at
all:

| | 160 | 320 | 480 |
|---|---|---|---|
| reference room | +0.146 | **+0.133** | **+0.133** |
| seed 1 | +0.155 | +0.146 | +0.107 |
| seed 2 | +0.093 | +0.054 | +0.048 |
| seed 3 | +0.084 | +0.039 | **+0.014** |

Contrast is a 5–95 percentile spread — a tail statistic — so it moves as more
resolution resolves more distinct values, but *only where there is detail to
resolve*. The reference room holds its reading and the generated rooms lose
theirs. That is not the instrument drifting, it is the two rooms differing: the
generated periphery is as detailed as its centre and gains contrast as fast as
the counter does.

Mean L, a first moment, is stable across all three sizes for every room. It was
therefore available as a metric that would have kept the check green. Picking
it would have been choosing the measurement that agreed with the answer already
written down. The check moved to 320 instead, near the size that ships, and was
re-verified to fire: the old rig fails 2 of 3 rooms there, one of them at
**−0.015**, a counter *darker* than its own room.

## Perching, and one rule in two copies

Bar stools stand at 0.62–0.76 and the seated rig folds a leg for 0.45, so every
stool in every generated room was furniture nobody used. Twelve rooms filled
every chair and left the window bar empty, which is not a cafe, it is a
showroom.

Perching is a different rig, not a longer shin. The seated rig folds the leg
into a right angle and puts the foot on the floor; the perch rig hangs it
nearly straight and puts the foot on a stool's foot ring, or on nothing. And
critically it does **not** ground-clamp — clamping a perched figure drags it
down the stool until it is standing beside it. `stool()` now publishes
`seat_z` and `rail_z` the way `chair()` publishes `seat_z`, and feet land on
the ring to the centimetre (0.25 → 0.25, 0.24 → 0.24) or hang at full stretch
where there is none, which is a pose and not a failure to find support.

The support model had to be generalised for it, because *a perched figure is
held up by its hips and `grounded` asks about undersides*. The new clause is
narrow: a surface must pass **through** the figure and lie within one leg's
length of its soles, so it excuses a person on a stool and not a person
hovering beside a bookshelf. Verified on all four cases including both
negatives.

Then nothing perched. `_conflicts` had its own private copy of the support
test — the same duplication that produced the 0.03/0.06 tolerance bug, fixed
that time by unifying the *constant* and leaving the duplicated *logic* in
place to do it again. It duly did: the check accepted perching and the solver
still refused it, silently, so the window bar stayed empty for a second reason
after the first was fixed. Both now call one `Layout._supported`. **Two copies
of a rule are one rule and one bug waiting for someone to edit only one of
them.**

Occupied window bars also moved the focal numbers, which was not the point of
the change: seed 2 from +0.054 to +0.101 and seed 3 from +0.039 to +0.084 at
320.

## The fix that was applied to the instance and not to the class

The scarf was fixed for being invisible in outline — 0.0% to 10.7%. The same
test was never re-run on the other three accessories. Holding the body fixed
and swapping only the accessory, over the eight sprite directions:

| | none | apron | scarf | bag | cup |
|---|---|---|---|---|---|
| **none** | – | **3.2%** | 7.5% | 11.8% | 21.3% |
| **apron** | 3.2% | – | 7.9% | 13.5% | 21.9% |
| **scarf** | 7.5% | 7.9% | – | 17.1% | 20.3% |
| **bag** | 11.8% | 13.5% | 17.1% | – | 29.5% |
| **cup** | 21.3% | 21.9% | 20.3% | 29.5% | – |

The apron was worth **3.2%** against wearing nothing: a flat panel between the
shoulders, inside the widest part of the figure at every azimuth — precisely
what the scarf had been. By rendered material it reads 14.6%, so it was visible
as colour and absent as shape, which is the failure mode the whole silhouette
programme exists to catch.

An apron's real outline is its skirt flaring past the hips and its ties
standing out at the waist. Given those — 0.285 at the hem against the 0.2475
shoulder — apron/none goes **3.2% → 7.4%** and apron/scarf 7.9% → 11.6%.

`check_accessory_distinct` is check 23, floor 0.055, bracketed by the 0.032 of
the flat apron and the 0.074 of the weakest pair after the fix, and verified to
fire on the old geometry. `None` is a row in the matrix on purpose: *does this
differ from no accessory* is the same question as *does it exist*, so one test
covers presence and legibility and nothing passes by being merely unlike the
other three.

**A fix applied to the instance rather than to the class leaves the rest of the
class broken and the log saying it was handled.**

## An L, and a decision three readers were reconstructing

The L run is modelled as the main run plus a short `service_return` arm rather
than as a second `service` zone. Not a dodge of the "a cafe has one service
run" rule — it is what an L is: one counter with a short arm at the till end.
Modelling it as two would also have been the expensive kind of wrong, since
seven places in `build_plan` read `plan.of("service")[0]` and every one would
have quietly served the first arm and ignored the second.

Nothing in the L code checks that the arm leaves room to walk round it.
`blocking()` selects by kind, so naming the kind puts the arm in the erosion
grid and the flood fill judges it on the same terms as everything else. *A
generator that must be taught each new obstacle separately is a generator with
a list; this one has a rule.*

First cut: **0 L plans in 60 seeds**, all 20 proposals rejected. Both reasons
were the proposal's to fix, not the checker's — 9 on *service_return stands in
the queue*, which is true and describes a cafe where the line forms inside the
counter, and 8 on the seating being cut from a service band that had grown
while the rectangle describing it had not. With the queue stepping aside for
the arm and the seating floor starting past the deeper of the two: **14 of 60
plans, 61% acceptance**, and what still fails is the daylight rule.

### The topology was implied, so three readers implied it differently

`build_plan` read `backbar.y0 < 0.05` to decide whether the run hugs a wall.
The proof sheet had its own version. A sweep written to count the three
topologies used a third, and it was simply wrong: it reported **zero
peninsulas in sixty seeds**, and there were sixteen. For a few minutes that
looked exactly like a regression in the generator.

`Plan.topology` now records what the generator chose and the readers read it.
Three readers reconstructing one decision from its consequences will get three
answers, and the wrong one is indistinguishable from a real bug.

Over 60 seeds: **30 wall runs, 16 peninsulas, 14 L runs**, 0 errors, 7 ms each.

## The mean said the generators moved; the closest pair said they repeated

`check_cast_silhouette` has graded people on their most similar two from the
start — a cast is only as varied as its closest pair. The generators were still
being graded on an *average*, and the average hid exactly what it exists to
catch:

| generator | mean spread | closest pair |
|---|---|---|
| espresso_machine | 33% | **0.0%** — pixel-identical |
| table_4top | 30% | **0.3%** |
| table_round | 19% | 1.7% |
| chair | 34% | 3.0% |

Those are the instances a player actually compares: four chairs round one table
come from four consecutive seeds.

The cause was the same in every case — **one discrete axis, plus jitter below
the raster**. The chair varied on four back styles and a leg radius of ±0.010,
which is a third of a pixel at room scale; any two seeds drawing the same back
were the same chair. *Variation that exists in the mesh and dies in the raster
is not variation.*

What each one got is an axis that reaches the outline:

- **chair** — a leg style (square, tapered, splayed, turned) and a seat height
  of 0.415–0.49. Height is the best of the three because it moves the back, the
  legs and the cushion together, and `chair` already publishes `seat_z` and the
  seated rig already reads it, so a shorter chair seats a person correctly with
  no matching change anywhere. **3.0% → 11.1%**
- **table** — height, the biggest lever a table has and the one it was not
  pulling; thickness and overhang were varying by one and two pixels.
  `top_z` already propagates it. **0.3% → 5.2%**
- **espresso_machine** — shell height and an optional second steam wand. Its
  width is deliberately fixed (it is a built-in), so height was the only
  dimension left that reaches the outline, and the group and cup counts are all
  interior. **0.0% → 9.0%**
- **table_round** — round tops were sending the trestle style to the pedestal,
  so a disc had three bases with one drawn twice. It gets a tripod instead.
  *Collapsing a style onto another style is how a generator loses range without
  losing a branch: the code still has four cases and the output has three.*
  **2.9% → 5.7%**

`CLOSEST_PAIR_FLOOR = 0.045`, bracketed by the 0.000/0.003/0.029 of the defects
and the 5.2% of the weakest generator after the fix, and verified to fire on all
four against the pre-fix library — where the mean-spread floor caught none of
them. Generators with their own floor are exempt: the counter's modules are
meant to tile flush and two identical ones are the point.

Every unseeded mesh is byte-identical to before, so existing sprite sheets are
untouched.

## The counter was under-dressed, and the contrast metric could not tell me

The focal check went red after the generator work, on one room, at +0.045
against a floor of 0.060. Finding out why took four wrong answers and then a
discovery about the instrument.

**Where the gap actually was.** The reference room carries **eleven** clutter
items within 3.5 tiles of its till — cups, a cake stand, vases, a clutter
cluster — and the generated rooms carried **none**. A bare counter has nothing
for the eye to land *on* once the light has sent it there. Generated focal zones
went from 14–20 props to 19–29 against the reference's 30.

Three hypotheses were measured and discarded first, and the discarding is the
point:

- **prop density per square metre** does not predict contrast — the room with
  the densest periphery relative to its centre reads *strongest*;
- **a mid-field negative pool**, aimed at rooms whose counter is far from any
  corner, moved the reading by **0.000** in three variants. It would have been
  a knob, and it was tested before it was shipped;
- **counter orientation** looked like a signal at n=2 and dissolved at n=4.

**A rule in two copies, for the third time in this file.** Reserving counter
length for dressing changed nothing, because the kit was tallied in one loop
and re-decided in another, both carrying the same `length - 0.3`. The tally
dropped the grinder and the placement loop put it back. After the support test
and the shelving span, this is the third instance, and the fix was the same
each time: decide once.

**A transcription slip, visible in the frame long before the numbers.** The
counter's core light pool sat at `cy + 0.35` where the reference room's
hand-placed pools sit at their run's centre — so a 2.6-radius core was half a
tile off the counter, over the queue. And the offset was in `y` regardless of
orientation, so it slid *along* a vertical run instead of across it, which is
why vertical-run rooms looked fine and hid it. Side by side, one room's counter
is a warm pool and the other's is a dim corner; the numbers said +0.107 and
+0.045 without saying why.

### Why none of it moved the reading: the metric is quantized

Every intervention left the weak room at **exactly +0.045** — inside 0.546,
outside 0.502, to the thousandth, four times running. A number that will not
move under changes that visibly alter the frame is the same tell as a
degenerate box.

The frame contains **37 distinct lightness values**. It has to: the whole point
of this pipeline is that lighting is quantized to palette ramps. Contrast here
is a 5–95 *percentile spread* — a tail statistic over 37 discrete levels — so it
is a step function whose steps are about as wide as the margin the floor was
sitting in. Mean L is a first moment over ~50 000 pixels and moved with every
change (0.603 → 0.591).

This is also the real explanation for the earlier resolution sweep, where
contrast collapsed from 320 to 480 and mean L held. Same cause, found from the
other end.

**Rejecting mean L earlier was right for the wrong reason.** It was rejected as
"the metric that agreed with the answer already written down", which was the
correct instinct with no evidence behind it. The evidence is now in: contrast is
quantized by construction and mean L is not, and that is a property of the
instrument rather than a preference for its reading.

### What the check became

Both metrics, both floors low. That is a retreat from the first version and it
is the honest one:

| | good L / C | broken L / C |
|---|---|---|
| seed 1 | +0.118 / +0.146 | +0.109 / +0.087 |
| seed 2 | +0.032 / +0.093 | +0.023 / +0.039 |
| seed 3 | +0.042 / +0.045 | +0.024 / **−0.054** |
| seed 4 | +0.080 / +0.099 | +0.069 / +0.048 |
| **reference** | **+0.024** / +0.133 | — |

Neither column supports an absolute floor that *ranks* composition. The
reference room has the lowest mean L of anything measured, below every broken
room — it builds its centre out of contrast, a dark machine against a lit
counter, not out of brightness. And a good room's contrast (+0.045) sits below
a broken room's (+0.087), because these are different rooms and not two
readings of one.

The first version put the floor at 0.060 on contrast alone, calibrated on three
samples, and it was grading *how well* the counter leads. The check now grades
*whether* it leads — mean L above 0.015 and contrast above 0.010 — which is the
most this instrument can carry. It passes all four rooms and the reference, and
still fires on the one whose counter is **less** contrasty than its own
periphery.

What both metrics agree on is direction: every room got worse on both under the
broken rig. A check that only ever sees one version of a room cannot use that.
**Asking the weaker question honestly beats asking the stronger one
unreliably.**

# Ninth pass — the generator arrived and it was shading the object twice

Every pass before this one critiqued art the repo had written itself. This one
is the first where a model outside the repo produced the geometry and the
colour, and the first rejection was not subtle: the teapot came through
`concept → lift → ingest → render_batch` as a **near-black blob with a correct
silhouette**. Recognisably a teapot in outline, unrecognisable as anything in
this palette.

## Two defects, and only one of them had a check

Stage 8 blocked the first eight sprites outright:

    art appears to be 8x upscaled (97% of 8x8 blocks are uniform)

That is `check_grid`, doing exactly its job on a bug it was never written for.
`render_batch` was using the camera's default span of 1.25, which is sized for
the analytic room; a 0.28 m prop rendered as a **nine-pixel dot** in a 64 px
frame, and nine pixels of teapot in a 64 px frame is indistinguishable from an
8× upscale. A check aimed at one failure caught a different one because both
produce the same evidence. That is the argument for grading pixels rather than
grading intent.

The second defect had no check at all. Once framed, the sprites were the right
size, the right shape, and the wrong colour — and every existing check passed
them. `ramp-coherence` reported 4.9% cross-ramp adjacency on one frame and
notes on the rest. Nothing said *this object is black*.

## Why it was black, which is not a colour problem

A photograph is albedo times lighting. A single-view reconstructor cannot
separate them, so TripoSR's vertex colours arrive with the concept image's key
light already multiplied in. `bind_colour` picks the ramp step nearest the
source's lightness — its **lit** lightness — and then the renderer applies
lambert on top of that. The lighting runs twice, and twice-shaded mid-grey is
black.

This is the sharpest instance yet of a principle the second pass wrote down as
*quantize the lighting, not the image*. The seam had been built against a
hypothetical MTL full of albedo, and the first real generator handed it
something else.

## The measurement that decided the fix

The temptation is to normalise: rescale the field's lightness range to the
palette's. Measuring first says not to.

| | albedo median L | p05–p95 band |
|---|---|---|
| thirty `assetlib` props | **0.596 – 0.845** | 0.000 – 0.585 |
| TripoSR teapot | **0.408** | 0.481 |

Every one of the thirty authored meshes lands inside that median range. Not
most — all of them, with seventeen sitting on 0.600 exactly, because the
library is built out of ramp middles. That is not a coincidence worth
preserving for its own sake; it is what *the renderer supplies the shading*
looks like in numbers.

The teapot's median is 0.188 below a floor nothing authored goes near. Its
band is comfortably **inside** the authored range — an espresso machine is
busier. So the median is wrong and the contrast is not, and `ingest.delight`
shifts the one without touching the other. Compressing the band would have
destroyed the two-tone structure the reconstructor genuinely recovered, in
order to fix a problem it did not have.

Corroboration that the shift is right rather than merely flattering: **worst
bind distance fell from dE 0.146 to 0.071.** The palette was authored as
albedo, so albedo binds to it better than lit colour does. Nothing in
`delight` optimises for that number, which is what makes it evidence.

## The floor is the widest in the suite, for once

`check_albedo_centre` reads the materials a mesh ended up with, so a bad
`delight` and a bad MTL fail by the same route. Its bracket is a measured
defect at 0.408 against a weakest known-good at 0.596 — **0.188 wide**, against
the detail floor's 0.010. Worth noting because most of this file is arguments
about margins of a hundredth; this one was never in doubt.

## Two axis bugs that neither crashed nor looked wrong

The marching-cubes shim reverses vertex columns to match what TripoSR expects
back. A reflection reverses winding, and reversed winding renders identically
in anything that ignores facing. The tell was `ingest.signed_volume`:
**−0.1612** before the face flip, **+0.1612** after.

Separately, `load_obj` read only the first three floats of a `v` line, so
TripoSR's per-vertex colour was discarded and the whole teapot bound to one
material. Fixing the reader was not enough — `orient` and `fit` rebuild the
mesh and did not carry the new field, so the vertex-colour branch in `ingest`
never fired and everything bound to `neutral` with no warning anywhere. Three
places, one fact, and the failure at each of them was silent.

An upright search was run too, on the theory that a mesh reconstructed from a
prompt asking for *a high three-quarter view looking down* would arrive
pitched by that elevation. Scoring candidate rotations by the flatness of the
lowest 1% of vertices, the best was pitch 2° roll 12° against 0° 0° — base
spread 0.0081 versus 0.0235. Real but small, and not the tumbling that was
suspected. Left uncorrected, because a 12° roll fitted to one teapot's base is
a knob.

## The check that was proposed and discarded

A single-view reconstructor invents the far side of an object, and this
teapot's back is invented. The obvious next check is turntable consistency —
grade the silhouette-area sequence across the eight directions.

It would measure nothing. The eight frames are a **consistent** turnaround; the
geometry they consistently describe is wrong. Any image-space metric over the
direction set is satisfied exactly by a rigid mesh however badly reconstructed.
This is a property of stage 2, not a gap in stage 8, and it is precisely what
stage 9 exists for. Recorded here because a check that cannot fail is worse
than no check: it reports confidence it has not earned.

## Three subjects, and the shift held for all three

Fitting a constant to one teapot is fitting a constant to one teapot, so the
other two concepts that cleared stage 1 were lifted as well:

| | field albedo median L | after `delight` |
|---|---|---|
| teapot | 0.408 | 0.600 |
| basket | 0.494 | 0.600 |
| kettle | 0.329 | 0.600 |

All three below the authored floor, spread over 0.165 of each other. A fixed
offset would have been wrong for two of them; a median-to-target shift is right
for all three. Reconstructed colour fields are *systematically* under-exposed
relative to authored albedo, by an amount that varies per object — which is
what "the concept image's lighting is baked in" predicts, since the amount
depends on how the generator lit that particular subject.

The kettle is the best sprite this pipeline has produced from a model: clean
silhouette at all eight directions, legible as a kettle from every one of them,
palette-coherent. The teapot is acceptable from the front and degrades around
the back. The basket is unusable.

## The basket, and a check that had to be invented for it

The basket came through as a **salt-and-pepper storm** — scattered dark and
pale pixels across the whole surface, where a wicker weave had been
reconstructed as surface detail. Twenty-one sprites went through stage 8 and
every one of them passed. Nothing in the suite asks whether a sprite has any
coherent structure at all.

`check_grid` asks the opposite question — whether the art is secretly an
upscale — so the shape of the answer was already there. The reading is the
share of opaque pixels matching **none** of their four neighbours, on colour
rather than lightness, because the basket's speckle alternates dark `wood` and
pale `cream` and a lightness metric reports that as ordinary contrast.

| | isolated-pixel share |
|---|---|
| ten authored props, eight directions each | median **0.0002 – 0.0201**, worst single frame **0.0615** |
| kettle (good) | 0.037 – 0.057 |
| teapot (acceptable) | 0.066 – 0.084 |
| basket (rejected on sight) | **0.127 – 0.163** |

Floor at **0.105**, bracketed by the weakest thing worth keeping at 0.084
against the best frame of the thing that is not at 0.127 — a 0.043-wide
bracket, four times the detail floor's. Authored art sits an order of magnitude
below it and cannot trip it. Run against all twenty-one sprites it blocks
exactly the eight basket frames and nothing else.

The worst authored frame is a pastry case at 0.0615, whose glass is *meant* to
be busy. That the ceiling of legitimate business sits below the floor of
illegible noise is the reason this check can exist at all.

## Four fixes, none of which worked, which is the finding

The check's first `fix` text said *smooth the colour field upstream*. That was
a guess, so it was tested, and then three more were:

1. **Laplacian smoothing of the vertex colours** over the mesh's 1-ring, 2/4/8
   passes. Basket 0.148 → 0.135. Eight passes on a 77,000-vertex mesh covers a
   neighbourhood far smaller than one output pixel.
2. **Interpolated vertex normals** (`--smooth`). Identical to four decimal
   places, on all three props.
3. **Supersampling harder** — factor 2, 4, 8, 12. Flat. The downsample picks a
   representative sample rather than averaging, *by design*: averaging colour
   is the one thing this architecture forbids, because it is what makes
   cross-ramp contamination impossible.
4. **Flat single material**, as a diagnostic rather than a fix. Basket
   0.149/0.153 → 0.088/0.045, so about half its speckle is chromatic and half
   is geometric. The teapot went the other way, 0.058 → 0.078: its two-tone
   colour field is *suppressing* noise, and stripping it exposes the lambert
   speckle underneath.

So the noise is sub-pixel detail in the source, and at 64 px one pixel covers
hundreds of triangles of it. There is no render setting. The remedy is upstream
— a subject whose surface is smooth at this scale, or a better reconstructor —
and the check now says so instead of offering advice that was never tested.

Worth naming: the first version of that `fix` string was plausible, specific,
and wrong, and it would have shipped as guidance. Every other floor in this
file was bracketed by measurement while its remedy was asserted.

## Two of the generator's seven dimensions had one value each

An audit of `generate_spec` over a hundred seeds, counting distinct values per
dimension:

| dimension | distinct values |
|---|---|
| shirt | 24 |
| hair_mat | 21 |
| trousers | 17 |
| hair_style | 6 |
| accessory_kind | 4 |
| **skin** | **1** |
| **blush** | **1** |

Neither was an art-direction decision. Both were dataclass defaults that the
proposal loop never drew from, sitting unnoticed beside five dimensions that
were working. A hundred generated extras, all one skin tone, all blushing.

Adding them to the draw is two lines. The reason it had not been done is the
interesting part.

## The eyes could not survive it, and the check that would have said so did not exist

`face()` drew the eyes as `skin + "-4"` — four steps down the surface's own
ramp, which is the idiom `pixelize.material` exists for and which is right
almost everywhere. Rendered heads across seven skin tones, eye-to-face
separation in OKLab:

| eye material | skin−4 | −3 | −2 | −1 | skin | +1 | +2 |
|---|---|---|---|---|---|---|---|
| `skin + "-4"` *(shipped)* | **0.000** | **0.000** | 0.103 | 0.204 | 0.304 | 0.404 | 0.504 |
| `neutral-3` | 0.076 | 0.076 | 0.161 | 0.256 | 0.353 | 0.450 | 0.547 |
| **`neutral-2`** | **0.196** | 0.196 | 0.196 | 0.256 | 0.353 | 0.450 | 0.547 |
| `neutral-1` | 0.304 | 0.304 | 0.304 | 0.304 | 0.353 | 0.450 | 0.547 |

Zero at the two darkest tones. Not faint — *absent*. The head renders as one
flat colour with a blush and no face.

The mechanism is clamping, and the reason no existing check saw it is that the
existing check is analytic. Eyes sit on the **front** facet, which the key
already shades a step or two down, so `-4` from there hits the ramp floor —
and so does the shaded cheek around them. At `skin-1` the palette-step gap
computes to a comfortable 0.201 while the sprite shows a blank face, because
both colours clamped to the same step. `check_contrast` has been comparing
hair against a lit reference for eight passes and been right to, because hair
is on top of the head; the same arithmetic is simply wrong for a feature on the
shaded side.

**A rig whose eyes are a skin offset cannot draw a dark-skinned face.** That is
a property of the drawing idiom, not of the palette, and it had been quietly
capping the cast at one complexion. The precedent for breaking the idiom was
four lines away in the same function: blush has always been `rose+1` on a skin
surface. An eye is a different material from a cheek in every art style there
is.

`neutral-2` over `neutral-1` because that flat 0.304 in the last row is the eye
clamping too — it holds its gap by getting *lighter* as the skin darkens, and a
mid-grey eye on a pale face is a weaker mark than a near-black one. `neutral-2`
floors at 0.196 and stays dark at the light end.

### The check renders, and it measures the right distance

`check_eye_legibility` finds the eye pixels by difference — one head with a
face, one without — so it does not need to know where in the frame they landed
and keeps working if the eye line moves. Floor at **0.15**, bracketed by the
old rule's 0.103 at `skin-2`, which renders blank, against `neutral-2`'s worst
tone at 0.196.

It measures full OKLab distance rather than lightness, and the first version
did not. At the dark end the eye and the cheek separate on **hue** — a cool
near-black on a warm red-brown — and the lightness-only reading called that
0.039 and rejected art that reads perfectly well. Nine passes of this file have
used lightness as the readability proxy and it has been right every time until
the one case where two colours of equal value sit next to each other.

Verified in both directions: clean on the shipped rig, and two failures when
`EYE` is put back to `neutral-3`.

With that in place, skin goes into the proposal with **every** offset offered
rather than a hand-picked safe subset — the argument `HAIR_MATS` makes at
length — and over a hundred seeds the generator now produces 7 skin tones and
both blush states, with zero specs failing any check.

## The audit was worth more than the fix

Finding two dead dimensions by hand raises the obvious question of how many
other audits have never been run, and the answer is to stop running audits by
hand. `check_spec_coverage` is that table, promoted: it generates a hundred
specs and reports any field whose modal value takes more than 80% of them.

Modal share rather than distinct count, so a dimension that varies once in a
hundred seeds is caught as well as one that never varies. The bracket is the
measured before-and-after: `skin` and `blush` at **100%**, against `blush`
itself at **59%** now that it is drawn — with `accessory_kind` at 38% (a
quarter of its vocabulary is `None` on purpose) and `hair_style` at 24%. The
cap sits in the gap between 59 and 100 rather than anywhere near 24, because
booleans are the tight case by construction and always will be.

This is the check `check_generator_range` could not be. That one asks the
outcome-level question for the asset library — do consecutive seeds produce
different silhouettes — and it would never have caught this, because a cast
can differ in shirt and trousers and hair and hat and still be one face
repeated nine times. **A dimension that is never drawn from is invisible in
every downstream metric.** The only place it shows is in the spec, and until
now nothing looked there.

Verified in both directions, which for this check means pinning `skin` and
`blush` back to their old defaults and watching both fire at 100%.

## `--smooth` had nothing to interpolate, on any mesh, ever

Chasing NEXT.md's B1, the question was whether `--smooth` does anything to a
lifted prop. It does not, and neither does it do anything to an authored one
-- this was a dead flag from the day it was added, not a lifted-mesh
regression.

The mechanism: `rasterize`'s smooth branch fires only when a face's normal-
index tuple is set and `mesh.normals` is non-empty. `add_box`/`add_quad`/
`add_prism` never set that index -- every authored mesh renders on flat
per-face normals by construction, which is correct for a low-poly look and was
never meant to interpolate. `load_obj` sets it only by parsing `vn` lines and
`v//vn` face syntax, and no OBJ in this pipeline has ever contained one:
verified zero `vn` lines in TripoSR's raw export, and `save_obj` -- the writer
`ingest.py` uses for every `_bound.obj` -- never wrote them either. Three
supersampling factors and eight passes of this file exercised `--smooth`
without exercising anything.

`mesh.compute_vertex_normals` fills this in on a mesh already in memory,
without touching the OBJ format on disk: one area-weighted normal per vertex,
each face's normal-index reset to its own vertex indices (exact, since they
are aligned 1:1). Measured on all three lifted props, median isolated-pixel
share over eight directions:

| | flat | smooth |
|---|---|---|
| teapot | 0.0649 | 0.0621 |
| basket | 0.1545 | 0.1463 |
| kettle | 0.0460 | 0.0431 |

Real and consistent -- every direction moved, not just the median -- and
small, 4-9%. It does not flip a verdict: the basket is still far above the
speckle floor and the other two still comfortably under it. Worth keeping
because it costs nothing and every direction improved, and worth stating
plainly that it is not the fix for anything -- the basket's noise is still
sub-pixel surface detail, which no amount of normal smoothing touches, and the
measurement confirms rather than contradicts the ninth pass's finding that
there is no render setting for that problem.

## `check_albedo_centre` had never been driven into failing

It runs inside `ingest()` on every real call, but nothing in the suite calls
`ingest()` with a mesh built to actually trip it -- `check_roundtrip` and
`check_transform` both exercise the binder with library geometry, which is
already correctly exposed by construction. A check that has only ever seen
clean input is unverified in the direction that matters.

Writing the fixture found something about `delight` worth stating precisely.
`bind_vertex_colours` runs `delight` before binding, and `delight` shifts by
the field's own MEDIAN. Three deliberately adversarial vertex-colour fields
were tried against it -- 90% near-black with a 10% near-white minority, the
mirror of that, and a tight 50/50 split -- and every one of them came out
clean after the shift. That is not a weak search; it is what shifting a median
means. Clamping at [0, 1] can only ever compress the tail on one side of the
median rank, and the rank itself is untouched unless the target is degenerate,
which 0.600 is not. **The vertex-colour path is close to unbreakable by
construction, and no fixture should pretend otherwise.**

`rebind` -- the MTL path, for any mesh that names its own materials with
arbitrary RGB rather than per-vertex colour, which is what `PIPELINE.md`
originally specified for TRELLIS -- has no such protection. Nothing shifts an
MTL's declared colours before they are bound. `check_albedo_regression` tests
both paths honestly: a dark MTL colour (L~0.16) must trip the check, a colour
already on the palette's own middle step must not, and the real teapot's
field median (0.408) run through the actual `delight` path must come out
silent. Verified failing in the direction that matters by breaking the floor
to 0.999 and watching two of the three cases fire.

## The mean spread floor: never fired is not the same question as redundant

NEXT.md B3 asked whether `DEFAULT_SPREAD_FLOOR` has ever rejected anything the
closest-pair floor did not also reject. It has never fired on the current
library at all -- the weakest generator, bookshelf, sits at 18.4% mean spread
against a 15% floor, a 3.4-point margin that was chosen deliberately when the
floor was last tuned.

"Never fired" does not distinguish "redundant" from "the library is healthy,"
so a synthetic case was built to separate the two questions directly rather
than waiting for a real generator to regress: 2000 pixels, 8 seeds, each an
independent 7% random flip from a shared base. No two seeds are near-
duplicates and none strays far from the rest -- uniform noise, which is
exactly the failure mode the mean floor's docstring has claimed since the
second pass to catch and the closest-pair floor structurally cannot see.

Measured: mean 13.0%, closest pair 12.3%. The mean floor (15%) fires; the
closest-pair floor (4%) does not. Two floors disagreeing on a case built to
separate them is what non-redundancy looks like, and a redundant floor cannot
produce that result by construction. `check_spread_floor_regression` promotes
this from a one-off measurement into a permanent assertion, seeded so the
result does not depend on redrawing it.

The floor stays at 0.15, unchanged. What changed is that "it has never fired"
is now known to mean the library has never regressed this way, not that the
check has nothing to catch.

## Counter orientation: the accepted population is 66% worse-lit, and the coin is not why

NEXT.md B5 asked for a measurement before touching anything -- the light rig
and any per-pixel fill are repo-wide changes, and the eighth pass already
established the mechanism: a counter facing +x reads at N.L = +0.874, one
facing +y at N.L = -0.116, from the fixed camera-space key at azimuth 45.
What was never measured is how much of the generated population actually
lands in the dark orientation, or why.

`Zone.facing` looked, on a first read, like a dead field -- every keyword-form
`Zone(...)` call in `floorplan.py` omits it, which is what a `grep "facing="`
finds. It is not dead: every one of those calls sets it *positionally*, as a
sixth argument on the next line down. Worth recording only because it is
exactly the kind of false lead this file has warned about before, and this
time it was caught before being written down as a finding rather than after.

With `facing` read correctly, 600 generated plans split by which of the two
key-light dot products their counter's front face gets:

| topology | better-lit (+0.874) | worse-lit (-0.116) |
|---|---|---|
| wall run | 105 | 144 |
| L run | 34 | 66 |
| island | 35 | 53 |
| peninsula | 31 | 132 |
| **overall** | **205 (34%)** | **395 (66%)** |

Two-thirds of generated rooms put the counter in the dark orientation. The
proposal loop draws one shared coin, `horizontal = rnd() < 0.62`, and for wall
run / L run / island `horizontal=True` maps to the WORSE facing while for
peninsula it maps to the BETTER one -- so a naive reading of the 62% coin
predicts wall-run-family rooms skewing 62% worse (close to the measured
58-66%) and peninsula skewing 62% BETTER. Peninsula measures the opposite:
81% worse. Checked whether a downstream `continue` was rejecting proposals
asymmetrically by comparing accepted `run_len` distributions between the two
facings at n=600 -- means within 0.15 of each other, same range, no signal.
Peninsula's skew is real and confirmed larger than the coin bias predicts, and
its specific rejection path was not traced to a single line; it is buried in
the later seating-rectangle checks (`main`/`side`, `MIN_SEAT_RECT_W/D`), which
is where a follow-up should look.

**Not fixed, for the reason NEXT.md flagged in advance.** Rebalancing the coin
would help wall-run/L-run/island roughly in line with prediction and would
need a SEPARATE, opposite change for peninsula given its inverted mapping --
a per-topology probability, not a shared one, which is a real change to the
generator's acceptance-rate behaviour and not a one-line flip. Untraced
peninsula-specific rejection mechanism means a naive per-topology rebalance
could easily just move the skew rather than close it. Given every wall-run/
L-run/island room in the twelve-plan sample already passes the focal floors
(see the widened B4 measurement below, which complicates this further), the
population skew costs SCORE, not PASS/FAIL -- and spending a repo-wide-risk
change to move a score that already clears its gate is the wrong trade this
session.

## The basket's crescent frames: stage 2, not stage 5

NEXT.md C3 asked where the basket's two flat, crescent-shaped frames (dir1 and
dir5, 90 degrees and 270 degrees) come from -- framing, rasteriser, or the
reconstruction itself. The mesh reports watertight with positive volume, so
it was not obvious which.

Ruled out by measurement before looking at a single pixel: the basket's
projected silhouette width and its depth extent along the camera axis are
both LARGEST at dir1/dir5 of all eight directions (0.348 and 0.341 against a
mean of about 0.29 elsewhere). Whatever is wrong is not the object going thin
edge-on to the camera, which was the obvious first guess.

Settled by rendering the raw lambert buffer directly -- full resolution, no
pixelization, no palette, greyscale shading only -- at dir0, dir1 and dir5.
Dir0 shows a basket: visible weave, a rim, a body with real volume. Dir1 and
dir5 show an honest crescent, a scooped shell shape, present in the geometry
itself before a single downstream stage touches it. **This is stage 2, not
stage 5 or stage 7.** The rasteriser and the framing are exonerated by the
same evidence that would have convicted them: if this were a rendering
artifact it would not appear in an unquantized buffer with no palette
involved.

This is the same limitation the ninth pass named -- a single-view
reconstructor invents what it cannot see, and nothing downstream can verify
the invention -- with a second, now visually confirmed, data point. The
basket's photograph showed roughly a 3/4 front view; the profile at 90/270 is
close to the least-constrained angle TripoSR had to guess, and here it guessed
a concave scoop instead of a rounded body. Consistent with the "Still open"
note directly below, which is why no new check is proposed: a check that
could catch this would have to know what a basket's side looks like, which is
exactly the information a single photograph does not carry.

## Auto-uprighting: the objective is not well-defined, not just object-specific

NEXT.md C4 asked to re-run the base-flatness pitch/roll search across more
objects and decide whether the correction it finds is a systematic camera
offset (adopt it) or per-object noise (leave it). The eighth pass's teapot
result -- pitch 2, roll 12, spread 0.0081 against 0.0235 level -- was found
with roll searched only to +-20 degrees in steps of 4.

Widening the search to +-30 degrees in steps of 2 was meant to add resolution.
It found a BETTER-scoring optimum at pitch 46, roll -24 -- spread 0.0068,
lower than the original -- entirely outside the box the original search
covered. Restricting the wider search back to the original bounds reproduces
0.0081 at (2, 12) exactly, so this is not a bug in the search; it is a second,
deeper optimum the narrower box never saw.

Both optima are real flat patches, not degenerate artifacts: the lowest-1%
vertex cluster at (2, 12) spans x -0.22..0.09, y -0.20..0.21; at (46, -24) it
spans x -0.03..0.20, y -0.27..-0.17. Both are extended regions consistent with
"a base," not a pinpoint on the spout or a handle. **The teapot has two
comparably flat surfaces at very different orientations, and the objective
cannot tell them apart.** The likely source: a single-view reconstructor with
weak priors often fills in the unseen side as a roughly planar continuation of
the visible silhouette rather than inventing real curvature back there --
which produces a broad, genuinely flat, entirely spurious surface that scores
just as well as the true bottom.

Basket and kettle, same wide search:

| | baseline spread | best pitch/roll | best spread |
|---|---|---|---|
| teapot | 0.0235 | +46 / -24 | 0.0068 |
| basket | 0.0177 | +28 / +30 | 0.0055 |
| kettle | 0.0048 | -2 / -2 | 0.0027 |

Kettle's correction is small and near zero in both axes -- consistent with a
mesh that does not have this ambiguity, or with a genuine near-upright
reconstruction. Teapot and basket both land far from zero in directions that
were never checked against a second local optimum for basket specifically,
because by this point the shape of the problem was already clear: the search
is not robust to its own bounds on the object it was originally calibrated
against, which is a stronger reason to leave it unadopted than "it varies
between objects" -- it is not stable for a single object either.

**Left undone**, more firmly than before. Fitting a rotation to whichever
optimum a search box happens to include is not a systematic camera offset; it
is a coin flip between the real base and an artifact this pipeline already
knows to expect on the unseen side of every single-view reconstruction.

## Stage 3 (UniRig): same blocker as TRELLIS, before any GPU time is spent

NEXT.md D1 asked to check UniRig's dependency list for compiled CUDA
extensions before investing in rigging, on the theory that if it needs `nvcc`
the same way TRELLIS 2 does, that finding alone is the deliverable.

It does. `requirements.txt` pulls in `flash_attn` directly, and the README's
install steps additionally require `spconv` (built from source against the
local CUDA toolkit) and `torch_scatter` / `torch_cluster` from PyTorch
Geometric's wheel index -- wheels that only exist for specific
torch/CUDA/Python combinations and fall back to source compilation otherwise.
The README's own words on the flash-attention step: "installation errors are
common here," pointing users at the upstream repo's install guide rather than
giving one itself.

This machine has no `nvcc` (`where nvcc` / `nvcc --version` both fail) --
already the reason TRELLIS 2 is blocked, recorded under "Not tasks" below.
UniRig's dependency list hits the identical wall before a single rig is
attempted: three packages that want to compile CUDA code against a toolkit
that was never installed, on top of `bpy==4.2` (Blender as a Python module,
a large and separately fragile dependency for Python-version compatibility).

Also worth weighing before revisiting: characters in this repo are already
analytic meshes with hand-authored clips that read well. UniRig would buy
variety in body shape, not motion quality -- the README's 8GB VRAM floor for
generation is itself tight against the 8.6GB card once SDXL or TripoSR is
also resident, so even unblocked, batch use alongside stage 1/2 would be
close to the wire.

**Left undone**, same category as TRELLIS 2: blocked on admin-level system
installs (CUDA toolkit + MSVC host compiler), not rejected on merit. Revisit
together with TRELLIS if the workstation ever changes.

## The concept fitness gate at 31 subjects: two thresholds real, two false-rejection classes found

NEXT.md C1 asked to run 25-30 café-appropriate subjects through `concept.py`
and bracket its four thresholds, which had only ever seen four subjects, three
of them passing. `subjects_c1.yaml` (teapot, basket, kettle plus 28 new props)
went through `factory.py` end to end: 31 attempted, 22 reached stage 5 clean,
9 gated, all 9 at the concept stage -- nothing that cleared concept was later
lost to lift, ingest or render.

`MAX_FILL 0.72` and `MAX_SECOND_BLOB 0.15` fired zero times across 31
subjects. Still effectively unbracketed on the defect side; loosening them is
not indicated by this sample, but neither is confidence that 0.72 or 0.15 are
the right numbers rather than merely numbers nothing here reached.

`MIN_FILL 0.12` fired three times, all within 1.1 points of the floor:
wine_glass 11.7%, cake_slice 11.2%, wooden_spoon 10.9%. This is a real bracket
now on the defect side. The passing side isn't logged per-subject by
`factory.py` (it records failure readings, not every threshold's value on a
pass), so the weakest known-good fill percentage is still unmeasured --
logging fitness readings on every subject, not just gated ones, is the
natural follow-up before this floor can be called fully bracketed.

`MAX_SOFT_ALPHA 0.10` fired six times, from 12% to 67%, and looking at the
actual images splits them into three causes the single threshold cannot tell
apart:

- **Genuine bad generations.** bread_loaf (67%) and croissant (42%) are both
  SDXL producing multiple overlapping instances, several of them barely
  distinguishable from the background (near-black loaves on black, near-white
  croissants on white) -- real segmentation confusion over a real generation
  defect. The gate is correct to reject these.
- **A genuine segmentation problem on a clean single subject.** book (15%)
  is one object, plainly generated, on a near-white background with a soft
  drop shadow -- low subject/background contrast defeats the matte. Also a
  correct rejection, different cause.
- **Legitimately hard silhouettes, false rejections.** fern (12%, the case
  NEXT.md named to re-examine) and bicycle (16%) are both clean, usable
  generations whose subjects are inherently made of many thin edges -- fern
  fronds, bicycle spokes -- each edge contributing its own ring of
  antialiased partial-alpha pixels. More perimeter, more soft-alpha area, at
  the same generation quality. The gate is measuring the geometry of the
  silhouette, not the quality of the segmentation.
- **A fourth pattern the sample surfaced that C1 didn't ask about:**
  bottle (13%) is not thin-edged or badly generated -- it is glass, and glass
  is supposed to be partially transparent. `MAX_SOFT_ALPHA` cannot distinguish
  "the matte is unsure where the object stops" from "the object is see-through
  by design," and that will recur for every jar, glass or bottle this factory
  is ever asked to make, which is a real fraction of a café's prop list.

**Verdict:** `MIN_FILL` is bracketed and should stay. `MAX_FILL` and
`MAX_SECOND_BLOB` are unexercised, not validated -- leave them, flag them as
still resting on nothing. `MAX_SOFT_ALPHA` is doing two jobs at one number:
catching real defects (bread_loaf, croissant, book) while also rejecting
subjects whose correctness looks like the same signal (fern, bicycle,
bottle). Not loosening it blind -- that would let bread_loaf-class failures
through -- but it is now a named, evidenced case for a second check (edge
density from the matte's own alpha gradient, or a material/transparency
allowance) rather than one scalar cap standing in for three different
questions.

## The speckle floor at 22 lifted objects: still one basket's problem, now confirmed to be seven objects' problem

NEXT.md C2 asked to feed C1's output through to sprites and re-measure
`MAX_ISOLATED = 0.105`, which rested on three lifted objects with the defect
side represented by one basket. C1's batch produced 22 lifted, rendered
objects (176 sprite frames). Running `check_speckle` on every frame:

7 of 22 objects have at least one frame over the floor -- basket (12.7-16.3%,
all 8 frames), cutting_board (11.5-14.8%, 7 of 8), stack_of_books (13.0-15.9%,
3 of 8), newspaper (11.3-12.9%, 3 of 8), flower_pot (12.4-12.8%, 2 of 8),
rolling_pin (11.1-13.0%, 3 of 8), potted_plant (one frame, 11.7%). The other
15 sit well clear, worst case coffee_cup at 9.9% on its single busiest frame.

Looked at all seven by eye, none were false positives. Two mechanisms:

- **Fine printed or woven surface detail**, the same cause already named for
  basket's weave: cutting_board's wood grain, newspaper's print texture,
  stack_of_books's page and cover detail all show the identical salt-and-
  pepper pattern basket did, cross-ramp (dark against cream) and visibly
  wrong at 4x zoom.
- **Foliage.** flower_pot and potted_plant both speckle on the leaves --
  green and white/cream alternating per-vertex, the same noise mechanism
  applied to thin high-frequency plant geometry instead of a flat textured
  surface. This is a new-to-this-measurement cause, not previously named.

rolling_pin is the closest call: the fluctuation is within-ramp (wood shade
against wood shade) rather than cross-ramp, so it reads far more subtly than
basket at a glance, but the scattered pale highlight fragments on 3 of 8
frames are the same failure at lower contrast, not a different one -- kept
on the defect side.

**Re-stated bracket:** weakest known-good is coffee_cup at 9.9% (its single
worst frame); weakest genuine defect is potted_plant's one failing frame at
11.7%. Narrower than the original 8.4-12.7% gap, but the floor at 10.5% still
sits inside it, and the extra volume resolves C2's actual question: the
defect side was never one basket, it is a real and now-multi-cause
population, and 15 of 22 real lifted props clear it with margin.

**Floor unchanged.** Every new failure was confirmed by eye as a genuine
defect, so there is no case for loosening it, and the closest good/bad pair
(coffee_cup / potted_plant) does not argue for moving it either direction --
it argues the floor was already close to correctly placed on three objects,
which the original bracket's honesty (`ART_CRITIQUE.md`'s prior entry) rather
undersold.

## Parameter-coverage audit for assetlib: no dead draws found, one design note

NEXT.md D3 asked whether `assetlib`'s seeded generators have the character
generator's bug -- randomized parameters that are drawn but never actually
move the output, the same shape of thing `check_generator_range` catches at
the silhouette level but cannot localize to a specific dimension. The named
obstacle was that these generators do not expose their draws the way the
character generator's spec dict does.

They do not, but every one of them funnels its randomness through one shared
helper, `_mix()`, called from an identically-named local closure `rnd()` in
every generator. That is a single patch point: wrap `_mix`, walk the call
stack past the `rnd` frame to whichever line actually consumed the float, and
every draw in the library is now visible without touching a single generator.

13 seeded generators exist. 12 call `_mix`/`rnd()`; `leafy_plant` rolls its
own separate LCG inline (different constants, same shape) -- an
inconsistency worth flattening later, not a bug: all 8 of its draws feed
visibly into stem angle, lean, rise and leaf radius.

Across the 12 instrumented generators, 40 seeds each: 53 distinct RNG
consumption sites, and at every one of them the drawn float differs across
all 40 seeds. No dead sites -- nothing reproduces the character generator's
failure at the input level.

Outcome-level cross-check, because varying inputs proving nothing was C1's
whole point: geometry signature (vertex count, face count, bounding box)
across 40 seeds. 10 of 12 generators land at 39 or 40 distinct signatures --
essentially every seed a different mesh. Two came back suspicious at first
pass -- counter at 3 signatures, bookshelf at 1 -- until re-reading their own
docstrings: both are explicitly built to draw *value, not geometry* (counter:
"All of them are drawn as value, never as geometry"; bookshelf's spines are
flat quads at different ramp steps inside a fixed carcass). Geometry
signature is the wrong instrument for a generator that varies material, not
shape. Re-measured on the material set each mesh actually uses: counter shows
4 distinct sets (matching its small number of front styles, one of which --
plain -- is deliberately listed twice in `FRONT_STYLES`), bookshelf shows 36
of 40 distinct, spanning nine ramp families. Both genuinely vary; the first
metric just wasn't the one their own design promised to move.

**Verdict:** no dead parameters found in `assetlib` at either the input or
the output layer, across 53 draw sites and 12 generators. The obstacle D3
named -- draws that don't expose themselves -- is fixed by the `_mix` wrap
above cheaply enough to leave as a standing instrument (rerun the same script
after touching any generator's RNG-driven branch, before trusting the change
did what it was meant to). `leafy_plant`'s separate RNG implementation is the
one loose end: harmless today, worth unifying if a fourteenth generator is
ever added copy-pasted from it instead of from the `_mix` pattern the rest of
the file agreed on.

## The detail floor at 40 plans: the margin got thinner, not wider

NEXT.md B4 flagged `MIN_FOCAL_DETAIL` as the tightest floor in the suite --
three measured defects at -0.005 to -0.009 against a weakest good room at
+0.005, on a 12-plan sample -- and asked whether a wider sample separates the
distribution or shows the floor sitting inside the noise.

`MIN_FOCAL_DETAIL = 0.0` exactly (`tools/build_plan.py:121`). Widened to 40
plans: 5 fail (12.5%), all wall run / L run / island, never peninsula (0 of
12). Same shape as the 12-plan sample. But the actual margin, read off the
full 40:

- Weakest fail: plan 10 (wall run), detail -0.002.
- Weakest pass: plan 24 (L run), detail **-0.000** -- prints negative, is
  `>= 0.0`, passes only because IEEE754 signed zero compares equal to
  positive zero. The next strictly-positive pass is plan 6 at +0.004.

That is a 0.002-0.006 gap, not the 0.010 the 12-plan sample reported. More
data did not separate the distribution -- it found a room sitting exactly on
the floor's own threshold and closed the margin from the good side.

Rendered the two closest cases side by side (`plan10` fail vs `plan24` pass,
both cluttered, busy service-counter rooms) to see whether the number tracks
anything visible. It does not, at this margin: neither reads as flatter or
less detailed than the other by eye. The floor's own comment already says as
much for the frame it was built on -- this confirms it is not an artifact of
that one frame.

**Topology concentration, new in the wider sample:** L run fails at 3 of 8
(37.5%), island 1 of 5 (20%), wall run 1 of 15 (6.7%), peninsula 0 of 12
(0%). L run is 20% of the sample and 60% of the failures.

Two hypotheses chased and closed:

- **Back-wall dressing structure.** Compared item lists between failing and
  passing island rooms of identical topology (failing plan 18 vs passing
  plans 3/12/15/32) -- identical dressing (sign, menu, shelf, counter/bar).
  Ruled out; not a missing-prop bug.
- **Shelf count.** Correlated `wshelf` count against detail lead across 60
  seeds, wall-run/L-run only: 0 shelves -> +0.0154 mean, 2/5 fail; 1 shelf ->
  +0.0383 mean, 2/26 fail; 2 shelves -> +0.0597 mean, 0/3 fail. Suggestive --
  zero-shelf rooms fail more often -- but `n=5` and `n=3` at the extremes are
  too small to call it, and more shelves tracking *higher* mean detail (not
  lower) argues against shelf count being what drags L run down specifically.

**Verdict:** the floor is real -- it is not tripping on noise alone, the
failing rooms are a consistent, repeatable topology-skewed population across
three independent samples now (12, 40, and the 60-seed correlation run) --
but its margin does not support the confidence a 0.0 threshold implies. Left
at 0.0, since nothing here argues for a different number and the failures
are genuine rather than false positives. Recorded rather than re-bracketed:
the honest statement NEXT.md asked for is that 40 plans narrowed the gap
instead of widening it, the L-run concentration is real and unexplained, and
neither dressing content nor shelf count is the mechanism.

## No style LoRA: the before-baseline is now measured, training one is not this session's job

NEXT.md D2 asked for a before/after on worst bind dE and albedo median shift,
with and without a style LoRA on stage 1's SDXL. Training or sourcing a LoRA
matched to this repo's house look is a separate project -- a curated
reference set, a training run, and its own evaluation loop -- not a
measurement task, and doing it inside this pass would mean shipping an
untested model into a pipeline whose entire discipline is measure-before-
trusting. Scoped down to the half that is a measurement: the before-baseline,
so a future LoRA has a real number to beat instead of a vague "SDXL fights
the palette."

C1's batch logged `delight()`'s correction for every subject that needed
one -- 17 of 22, the ones whose raw albedo median landed off 0.600 by enough
to trigger it. Read off those logs directly:

- Mean correction: 0.111 of L.
- Worst: wall_clock, raw median 0.294 -> corrected to 0.600, a shift of
  0.306 -- close to half the entire visible lightness range, on a single
  object, from prompt and lighting alone.
- Everything else sits between 0.023 (creamer) and 0.170 (flower_pot); the
  wall_clock case is a clear outlier at more than 3x the mean, not
  representative of the typical correction.

This is the number a style LoRA would be judged against: a working LoRA
should pull the mean well under 0.111 and the wall_clock-class worst case
well under 0.306. Bind dE was not pulled this pass -- it is not logged by
the current pipeline the way the albedo shift is, and adding that
instrumentation is a smaller, separable task worth doing before the LoRA
question is revisited, not with it.

**Left undone**, correctly scoped rather than attempted: not blocked like
UniRig or TRELLIS, just sized for a different, dedicated pass.

## A fifth topology: scoped, not built

NEXT.md D4 asked whether a fifth floor-plan topology would test the focal and
detail checks' generality or expose that they were fitted to wall run,
peninsula, L run and island. Read `floorplan.generate()` (`tools/floorplan.py:314`)
to size the work before attempting it.

Every existing topology is the same three-`Zone` skeleton --  service run,
back bar, queue -- placed differently, each branch hand-tuned against
`check_plan` with its own clearance constants (`ISLAND_CLEAR`,
`BACKBAR_DEPTH`, `MIN_SEAT_RECT_W/D`) and its own `blocked_x`/`blocked_y`
span so `_windows` routes glass around the run instead of through it. The
function's own docstring records what happens when this is rushed: the first
version of this generator passed 6 of 2157 proposals (0.3%) because two
branches didn't know about each other's constraints. That is the real cost
of a fifth branch written without the same iteration the first four got --
not a syntax risk, an acceptance-rate risk that would burn `generate()`'s
120-try budget silently and either starve the factory of that topology or
quietly fall back to a worse plan, the exact failure mode the docstring
warns a rejection-heavy proposal invites.

That is a multi-hour design-and-tune task on its own, with the same
measure-before-shipping discipline the rest of this file has been applying
all session -- not something to improvise inside a pass already carrying
thirteen other tasks. Scoped down to naming the candidate rather than
building it: a **double run** (galley) layout, two parallel service runs
facing each other across the main aisle, is a real café floor plan the
current four don't cover and reuses every piece already in hand (two
run/back/queue triples instead of one, windows blocked on whichever axis
both runs share). It is also the topology most likely to stress the
checks that matter here -- B5's counter-orientation gap and B4's L-run-
skewed detail floor are both about which way a service run faces the camera,
and a double run is the one layout where two runs face opposite directions
in the same room.

**Left undone.** Recorded so the next pass building it starts from a named
target and a stated cost, not from "topologies: four."

## Still open

- **Stage 3** (UniRig) is unbuilt. Stages 1 and 2 run on the local RTX 4070 —
  see `PIPELINE.md` for why stage 2 is TripoSR and not TRELLIS 2. Rigging is
  only needed for characters, and props do not rig.
- **The far side of a single-view reconstruction is unverifiable by machine.**
  Stated above; listed here so it is not mistaken for an oversight.
- The **focal reading falls with render resolution** in generated rooms and
  holds in the reference one, because contrast is a percentile spread over 37
  quantized lightness levels and the generated periphery resolves as much new
  detail as the centre. The check runs at 320 against a delivered 480. The gap
  is measured and stated rather than tuned away.
- **The plan generator cannot propose an island.** Three topologies exist (wall
  run, peninsula, L run); an island is the fourth and the only one left that
  changes circulation rather than furniture.
- **Furniture screen spread** now has an owner for its *closest pair* (0.045,
  bracketed by measurement) but the mean-spread floor of 0.12 is still the
  original guess. It has never rejected anything the closest-pair floor did not
  also reject, which is either redundancy or a floor set too low to fire.

---

# Seventh pass — the island, and a floor that had never fired

## The mean-spread floor was blind

Flagged in the open list as possibly redundant. Testing it properly meant
degrading a generator on purpose — a bookshelf emitting only *N* distinct
meshes from eight seeds:

| distinct | mean | closest | floor 0.12 | floor 0.15 | pair floor |
|---|---|---|---|---|---|
| 1 | 0.0% | 0.0% | fail | fail | fail |
| 2 | 10.8% | 0.0% | fail | fail | fail |
| 3 | 14.1% | 0.0% | **PASS** | fail | fail |
| 4 | 16.3% | 0.0% | **PASS** | **PASS** | fail |
| 8 | 18.4% | 15.9% | PASS | PASS | PASS |

A generator that has lost **half its range** sails through both mean floors and
is caught only by the closest pair, which has been reporting 0.0% since the
second row. At 0.12 the mean did not fire until six of eight seeds collided.

It is kept rather than deleted, because it catches the mode the closest pair
cannot see — every instance differing a little and none differing much — but
retuned to 0.15, three points under the weakest real generator. A secondary
instrument, labelled as one.

## The island

The fourth and last counter arrangement, and the only one left that changes
circulation rather than furniture: it touches no wall, the floor becomes a
ring, and every seat has to be reachable the long way round when the short way
is blocked. Nothing in the island code tests that — `blocking()` selects by
kind and the erosion grid does the rest, the same bargain the L run made.

It is also the only arrangement that **frees every wall for glass**. The other
three pin a counter or a back bar against one and hand `_windows` a blocked
span to route around; an island hands it `None`. That is not a special case so
much as the absence of a constraint, and it is a real reason cafes build them.

Two bugs, both of them the same bugs a previous topology had:

- **The duplicated `zones += [run, back, queue]`** — written from the peninsula
  as a template, which reproduced the peninsula's own first-cut failure
  exactly. Every proposal failed *a cafe has one service run*. That is what a
  template is for and also what it costs.
- **The proposal was uninformed, for the third time in this generator.** Placed
  anywhere in the band its wall clearances allowed, the island pushed the main
  seating rectangle under the 4.0 × 3.5 minimum and died on a guard further
  down: **7 island proposals reached the checker in sixty seeds**. Bounding the
  island's position by the floor it has to *leave* took that to 42% acceptance
  and **5 plans of 60**. After the windows and the L run's queue, the lesson has
  not changed: a constraint the proposal can satisfy for free should not be left
  to the checker.

The consumer needed one change, and the shape of it matters. `on_wall` had been
written as `topology != "peninsula"`, so an island inherited two chalkboards on
a wall across the room from the counter they price. It is now the set that
*does* hug a wall — `("wall run", "L run")` — because a list of exceptions is
wrong every time a fifth thing arrives and a list of members is not. Tall
shelving is gated on the same test: a 1.9 stack standing free on an island is a
partition between the barista and the room, which is the one thing an island
exists not to be.

60 seeds: **20 wall runs, 23 peninsulas, 12 L runs, 5 islands**, 0 errors,
8 ms each.

## Widening the focal check found a room, and six explanations that were not it

Making the check pick **one seed per topology** rather than the first four
seeds — the fix its own comment had predicted would be needed, one commit
before it was — immediately surfaced a wall run whose counter reads **+0.000**
contrast against its room at 320 and **−0.014** at 480. `focal_report` prints
*DOES NOT lead the eye* for it in words.

Six structural explanations were measured and none was the cause:

| hypothesis | measurement | verdict |
|---|---|---|
| over-dressed room | occupancy 44% vs the reference's **47%** | the reference is denser |
| prop density per m² | 0.66 vs reference 0.62 | marginal, and the densest-periphery room reads strongest |
| bare back wall | 2 shelves + 2 boards vs the reference's 1 + 2 | it has *more* |
| bare counter | 7 clutter items, top of the range | no |
| oversized kit | already reduced to 2 | no |
| lighting | three pool variants, incl. mid-field negative | moved it by 0.000 |

Recording that the cause is unfound is better than shipping a seventh guess as
a fix.

### The floor is negative now, and that is the honest placement

The metric moves in steps of roughly 0.04. Any floor between 0 and 0.04 sits
*inside one step*, and whether a marginal room clears it is decided by which
side of a bin boundary it lands on — the same room reads +0.000 and −0.014 one
resolution apart. So contrast is asked only what it can answer at that
granularity: that the counter is not **materially less** interesting than the
room around it. That still catches the broken rig at −0.054 and it no longer
adjudicates a step. Brightness, which is continuous, carries the positive
requirement.

A stronger check needs a metric that is not a percentile. **Edge density in
palette-index space** is the obvious candidate — continuous over ~50 000 pixels
— with the caveat this file already records from the first attempt at a focal
metric: darkening a corner *adds* ramp transitions, so it can only ever be a
zone-versus-rest comparison and never a search for where the focal point is.

Verified in both directions after the retune: clean on the good rig across all
four topologies, and the broken rig now fails the same room on **both** metrics
— brightness +0.005 against a floor of 0.015, contrast −0.054 against −0.020.
The two floors catch it independently, which is what having two is for.

## Edge density: the successor metric, tested before it was written in

The previous section named edge density in palette-index space as the obvious
replacement for the quantized percentile. It was measured before being adopted,
and it **is the wrong instrument** — for the job it was proposed for:

| room | good rig | broken rig |
|---|---|---|
| wall run | 0.310 vs 0.346 = **−0.037** | 0.309 vs 0.346 = −0.037 |
| peninsula | 0.364 vs 0.323 = +0.041 | 0.369 vs 0.323 = +0.046 |
| island | 0.374 vs 0.287 = +0.086 | 0.371 vs 0.296 = +0.076 |
| L run | 0.370 vs 0.306 = +0.064 | 0.371 vs 0.310 = +0.061 |

Good rig and broken rig read the **same to within 0.01 in every room**. Edge
density counts material transitions, and the light rig does not add or remove
transitions — it moves the ramp steps they sit between. So the metric is blind
to precisely the failure the focal check exists to catch, and a check built on
it would have been green through a rig that puts the counter at −0.054.

It is a good instrument for a different question, though, and it answered the
one that six structural hypotheses had failed to. The failing wall run's focal
zone has **fewer** material transitions than its own room, alone among the four
topologies. Its periphery reads 0.346 against the others' 0.287–0.323 — the
busiest of the four — which agrees with its occupancy (44%, the highest) and
its props per square metre (0.66, the highest). *The counter is not
under-dressed; the room around it is over-dressed, uniformly.*

That is a real, continuous, lighting-independent measure of the thing the
critique originally called "dressed but not composed", and it is the first
instrument that has separated the failing room from the passing ones. Two
different questions, two different instruments: mean L catches a badly lit
counter, edge density catches a room with no hierarchy of detail.

### Correction: it is the focal zone, not the periphery

The section above concluded *the room around it is over-dressed, uniformly*.
The reference room's own edge reading, which had not come back yet when that
was written, says the opposite:

| | focal zone | periphery | lead |
|---|---|---|---|
| **reference room** | **0.391** | 0.328 | +0.063 |
| failing wall run | **0.310** | 0.346 | −0.037 |
| peninsula | 0.364 | 0.323 | +0.041 |
| island | 0.374 | 0.287 | +0.086 |
| L run | 0.370 | 0.306 | +0.064 |

The failing room's periphery (0.346) is barely above the reference's (0.328).
Its **focal zone** is the outlier — 0.310 against every other zone measured at
0.364 to 0.391. And prop density agrees: that room runs 0.60 props per square
metre against the reference's 0.68, so it is not a crowded room at all.

So the counter *is* under-detailed, in material variety rather than in item
count: its zone holds twenty items in 11.9 m², more per square metre than the
L run's twenty in 17.9, and they are pale clutter on a pale counter with one
figure behind it where the L run has three. Edge density counts transitions,
and six cream objects on a cream counter are one object as far as an outline is
concerned — which is the silhouette lesson again, arriving in a third place.

## The sample was optimistic, and here is by how much

The suite check renders one room per topology — four renders, about a minute.
Scanning twelve consecutive plans instead:

**2 of 12 fail**, and *neither is one the suite check looks at*. One wall run at
−0.054 contrast, and one island whose counter is **darker** than its room
(−0.018 mean L).

A 17% escape rate is worth stating rather than hiding behind a green check.
Twelve rooms is three minutes, and a check nobody runs protects nothing, so the
deep scan is a flag rather than a suite entry:

```
python tools/build_plan.py --focal-scan 12
```

It exits non-zero on any failure, so it can be wired into a slower gate. What
it reports is a defect in the **generator**, not in the check.

## The occlusion rule was protecting the plants from the customers

Perching regressed from ten occupants across twelve rooms to **one**, silently,
and stayed that way through several commits. Nothing failed: the stools were
placed, the rig worked, the support model worked. The rooms simply had nobody
at the window bar, which looks exactly like a room where nobody sat down.

`screen_occlusion` was rejecting every perched figure with

```
char#probe hides 53% of decor#gplantW#1 (1.4 apart in depth)
```

The rule was symmetric, so of any two objects the one placed *second* lost —
and characters are placed last, so they lost to scatter decor every time. When
an unrelated change moved the plants behind the stools, the whole feature
switched off.

That is not a mis-calibration, it is the wrong hierarchy. **A person in front
of a plant is a scene; a plant in front of a person is a problem.** The check
exists so that modelled geometry is not invisible, and a fern behind a customer
has not been wasted — it has been stood behind. The exemption is asymmetric and
one-directional: decor hiding a character still fires.

Perching went 1 → 5 across twelve rooms with zero issues, and the rejections
that remain are correct — the second figure on a four-stool bar is refused
because a seated customer would hide 39% of it, which is character-on-character
and exactly what the rule is for.

The general lesson is about the *shape* of the bug rather than the rule. **A
feature that silently switches off looks identical to a feature that had
nothing to do.** The perch count was never asserted anywhere, so twelve empty
window bars read as twelve quiet cafes.

### Check 24: is the furniture used

Promoted directly from the regression above, because the shape of that bug is
the reason to have it. Perching switched off and stayed off for several
commits without failing anything — every other check asks whether the room is
*correct*, and an empty window bar is perfectly correct.

There turned out to be **two** independent causes, and the second only surfaced
once the first was fixed and the number was counted again:

| state | stools occupied |
|---|---|
| symmetric occlusion rule | 1 of 23 — **4%** |
| after the char/decor exemption | 7 of 25 — 28% |
| after placing people before the dressing | 10 of 25 — **40%** |

The second cause was ordering. `scatter` already rejects a conflicting
placement, so whichever of people and dressing goes down first wins the floor,
and the dressing was winning it: a six-stool window bar came out empty because
plants had been scattered along the same strip and a perched figure's legs
landed inside one. A real collision, correctly rejected, caused entirely by the
order. **This is the occlusion hierarchy again, one level up** — there a person
may stand in front of a plant, here a person gets the seat and the plant goes
somewhere else.

The check is a **rate** across eight rooms, floor 0.20, bracketed by the 4% of
the broken state and the 39% the shipped code measures. A rate rather than a
per-room rule because a room whose only stool is awkwardly placed should be
allowed to stay empty, and a generator that never seats anyone anywhere should
not.

On verification, honestly: the 4% was measured on live code before either fix,
so the bracket is real, but it cannot be reproduced now by reverting only the
occlusion asymmetry — with people placed first there are no plants behind the
stools for the symmetric rule to trip on. The two fixes overlap and either
alone suffices. What was verified against shipped code is that the failure path
executes: at a floor of 0.45 it reports *7 of 18 stools occupied across 8 rooms
(39%)*. A check whose failure path has never run is not a check.

# Eighth pass — the instrument was averaging in the thing it was excluding

## The focal region was a box drawn around a diamond

`focal_report` takes a world-space box, projects its eight corners, and grades
the pixels inside. Inside *what*, though: the eight corners of an axis-aligned
box project to a **hexagon** in a 2:1 dimetric, and the code was taking their
axis-aligned bounding box in pixel space.

How much that matters, measured rather than assumed — hull area over bounding
box area, per room:

| | fill |
|---|---|
| twelve generated rooms | **51% – 64%** |
| the reference room | 52% |

So between a third and a half of every focal reading was the floor in front of
the counter and the wall behind it: the exact *elsewhere* the focal zone is
supposed to be brighter and busier than. Clipping the region to the projected
convex hull, at 480, without touching a single room:

| plan | topology | bbox L | hull L | bbox C | hull C |
|---|---|---|---|---|---|
| 1 | wall run | +0.025 | +0.030 | **−0.014** | **+0.101** |
| 2 | peninsula | +0.037 | +0.075 | +0.040 | +0.087 |
| 3 | island | +0.066 | +0.064 | +0.087 | +0.062 |
| 4 | wall run | +0.020 | +0.020 | +0.039 | +0.101 |
| 5 | peninsula | +0.078 | +0.048 | +0.107 | +0.101 |
| 6 | peninsula | +0.054 | +0.072 | +0.094 | +0.087 |
| 7 | wall run | +0.107 | +0.116 | +0.062 | +0.101 |
| 8 | L run | +0.057 | +0.065 | +0.099 | +0.101 |
| 9 | L run | +0.029 | +0.031 | **+0.000** | +0.053 |
| 10 | wall run | +0.026 | +0.026 | +0.039 | +0.101 |
| 11 | wall run | +0.020 | +0.018 | **−0.054** | **+0.047** |
| 12 | island | −0.015 | **−0.033** | +0.045 | +0.146 |

Lowest contrast in twelve rooms: **−0.054 → +0.047**.

**This is why six structural hypotheses came back clean.** The seventh pass
measured occupancy, prop density, back-wall dressing, counter dressing, kit
size and three lighting variants against the wall run that read +0.000, and
recorded that the cause was unfound. Every one of those hypotheses was about
the room. None of them was about the rectangle.

And the reference room is the reason it survived so long. Its fill is 52% — no
better than anyone's — yet clipping moves its reading by nothing at all:
contrast **+0.133 either way**, brightness +0.024 → +0.019. The instrument was
calibrated on the one room where it happened to be accurate.

### The hull test, and reading the winding instead of assuming it

First version hard-coded the sign of the edge cross product and reported *only
0 px inside the projected hull* — the whole frame classified as outside. Pixel
coordinates flip y, so a chain wound counter-clockwise in world space comes out
clockwise here. The winding is now read off the hull's own signed area, which
costs one shoelace sum per frame and cannot be got wrong by a coordinate
convention.

## The contrast check had been working for the wrong reason

The floors are bracketed against a deliberately broken light rig — the old
per-zone lamp scheme that lights every seating area and takes light out of only
two corners. At 320, under the hull clip:

| plan | good L | broken L | good C | broken C |
|---|---|---|---|---|
| 1 wall run | +0.032 | +0.014 | +0.101 | +0.047 |
| 2 peninsula | +0.074 | +0.054 | +0.101 | +0.047 |
| 3 island | +0.051 | +0.032 | +0.146 | +0.047 |
| 4 wall run | +0.018 | −0.001 | +0.146 | +0.086 |
| 9 L run | +0.028 | +0.011 | +0.053 | −0.001 |
| 11 wall run | +0.018 | −0.004 | +0.079 | +0.039 |
| 12 island | −0.031 | −0.045 | +0.138 | +0.079 |
| reference | +0.019 | — | +0.133 | — |

Brightness drops in **every** room when the rig breaks, by a consistent 0.017
to 0.022. Contrast drops too, but from a good range of 0.053–0.146 to a broken
range of −0.001–0.086, which overlaps: a single floor catches **1 of 7**.

It used to catch most of them, and that is the finding rather than a
regression. The broken rig's whole defect is that it lights the **periphery**.
A focal box stuffed with a third to a half periphery pixels moved when the
periphery moved. *The check was detecting the regression by measuring the very
pixels it existed to exclude.*

So the floor is **+0.030** — positive for the first time, bracketed between the
broken rig at −0.001 and the weakest good room at +0.047 — and it is a floor,
not the instrument. Brightness carries the detection.

## Counter orientation, which the sixth pass had already rejected

Sorting the twelve hull readings by which way the run faces:

| run facing | brightness lead |
|---|---|
| 90° — long face points **+x** | +0.064, +0.065, +0.072, +0.075, +0.116 |
| 0° — long face points **+y** | −0.033, +0.018, +0.020, +0.026, +0.030, +0.031, +0.048 |

**No overlap.** Twelve rooms, four topologies, two clean groups.

The cause is one line of the lighting model. `LIGHT_CAM` resolves at azimuth 45
to a world key of **(0.874, −0.116, 0.471)**, and the counter's front is its
single largest visible surface:

| run | visible long face | N·L |
|---|---|---|
| facing 90 | +x | **+0.874** |
| facing 0 | +y | **−0.116** |

One counter is lit head-on and the other is raked at grazing incidence, and the
floor plan flips a coin between them and compensates for neither.

Not fixed, and deliberately. The **reference room's own counter is a facing-0
run** and reads +0.019, sitting in the middle of the weak group — so facing 0
is *weak, not broken*, and a rig that boosted it would be tuning the lighting
until the metric agreed rather than fixing a room. It goes on the open list
with a number attached, where "counter orientation: no effect" used to sit on
the rejected list without one. It was rejected through the blurred instrument.

## The island had a back bar zone and nothing in it

`on_wall` excludes islands and peninsulas from tall shelving, on the grounds
that a 1.9 stack standing free is a partition between the barista and the room.
That is right about shelving and was wrong to leave the zone empty: **a back
bar is a counter before it is a shelf**, and a run with nothing behind it loses
the vertical mass a wall run gets for free.

| plan | before | after |
|---|---|---|
| 2 peninsula | +0.074 | +0.124 |
| 3 island | +0.051 | +0.123 |
| 5 peninsula | — | +0.080 |
| 6 peninsula | — | +0.120 |
| 12 island | **−0.031** | **+0.017** |

### The height was chosen for the wrong reason and kept for the right one

At the service counter's own 0.92 the back bar reads 52–55% hidden behind the
run, and `screen_occlusion` calls that an error. Raising it looked like the
fix. The projection says it cannot be: the run sits 1.1 nearer in depth, which
lifts it 0.39 up the screen, so the back bar's top only clears the run's above
**h = 1.37** — past chest height and into the partition an island exists not to
be. Swept 1.10 to 1.32, the hidden share moved 49% to 44%. What the back bar
actually shows is its **end**, because the same depth offset shifts it 0.78
sideways.

So the occlusion is exempted for what it is, and the height is chosen on the
focal reading instead — where it turns out to matter for a different reason
than the one it was proposed for, the exposed end being taller:

| | worst island | best island |
|---|---|---|
| h = 0.92 | +0.017 | +0.123 |
| h = 1.24 | **+0.037** | +0.136 |

**The occlusion rule has now objected to a correct relationship twice** — first
a customer standing in front of a plant, now a back bar standing behind the
counter it serves. Both are cases where the overlap is a property of a fixed
pair rather than of anyone's placement, which is exactly what the existing
furniture-group exemption already says about the four chairs of a table set. So
the run and its back bar are named into that group (`counter#bar_*`) rather
than given a new special case. A rule that needs a third exemption of the same
shape is a rule that is missing a concept, and the concept is "these two were
placed as one thing".

Adding `h` to `A.counter` changed every counter in the library, on a parameter
whose default was supposed to change nothing: `0.92 - 0.10` is
`0.8200000000000001` and the literal it replaced was `0.82`. Rounded, and the
five counter variants hash identical to their committed selves again.

## Where this leaves it

`--focal-scan 12`, at 320 — the same resolution the suite check uses, which it
was not before; the flag defaulted to 480 and the escape rate in its own
docstring was measured against floors calibrated elsewhere:

```
  plan  1  wall run   L +0.032  C +0.101   ok
  plan  2  peninsula  L +0.138  C +0.101   ok
  plan  3  island     L +0.136  C +0.146   ok
  plan  4  wall run   L +0.018  C +0.146   ok
  plan  5  peninsula  L +0.093  C +0.101   ok
  plan  6  peninsula  L +0.125  C +0.101   ok
  plan  7  wall run   L +0.109  C +0.101   ok
  plan  8  L run      L +0.059  C +0.101   ok
  plan  9  L run      L +0.028  C +0.053   ok
  plan 10  wall run   L +0.026  C +0.101   ok
  plan 11  wall run   L +0.018  C +0.079   ok
  plan 12  island     L +0.037  C +0.146   ok

  0 of 12 rooms fail the focal floors (0%)
```

**2 of 12 to 0 of 12**, and the two failures had nothing in common. Plan 11 was
an instrument error and no room changed. Plan 12 was a real defect and one room
changed. Reporting them together as "the escape rate is closed" would hide
that.

Two rooms clear the brightness floor by 0.003 — plans 4 and 11, both facing-0
wall runs, both in the group the orientation section leaves open. That is where
the next failure will come from, and it is written down before it happens
rather than after.

## Re-reading the edge density through the corrected region

The seventh pass measured edge density in palette-index space and concluded
that the failing wall run's focal zone is *under-detailed*, not that its room
is over-dressed. Those readings were taken through the old bounding-box
region, so they inherit the same third-to-a-half of floor and wall as
everything else. Re-run under the hull clip, same rooms, same two rigs:

| room | focal | periphery | lead, hull | lead, bbox |
|---|---|---|---|---|
| **reference room** | 0.422 | 0.330 | **+0.092** | +0.063 |
| wall run (seed 1) | 0.333 | 0.341 | **−0.008** | −0.037 |
| L run (seed 8) | 0.370 | 0.311 | +0.058 | +0.064 |
| peninsula (seed 2) | 0.344 | 0.329 | +0.015 | +0.041 |
| island (seed 3) | 0.356 | 0.303 | +0.053 | +0.086 |

The wall run and the L run are unchanged rooms, so those two rows compare
directly; the peninsula and the island have gained a back bar since and do not.

**The conclusion survives and the magnitudes do not.** The failing wall run
still reads below its own periphery and the reference still reads far above it,
and the gap between them is 0.100 either way — but the wall run's deficit
shrank fourfold, −0.037 to −0.008, and the reference's lead grew by half. A
claim that was carried on a number four times too large was still pointing the
right way, which is luck and worth naming as luck.

Good rig and broken rig still read the same to within 0.012 in every room, so
edge density remains blind to lighting, which is what made it useless as a rig
check and useful as a detail-hierarchy one.

One thing it does add: the room that reads worst here is seed 1, a **facing-0**
run, and edge density has nothing to do with the key direction. If the
orientation penalty were purely the raking key it should not appear in a
lighting-independent metric. It does. Four rooms cannot separate that from
topology, though — seed 1 is also the only wall run in the sample — so this is
a thread, not a finding.

## The thread was real and it was not orientation

The edge re-read left a thread: the worst room on a lighting-independent metric
was a facing-0 run, which the raking key cannot explain. Four rooms could not
separate that from topology. Twelve can.

| plan | topology | facing | focal detail lead |
|---|---|---|---|
| 11 | wall run | 0 | **−0.009** |
| 1 | wall run | 0 | **−0.008** |
| 10 | wall run | 0 | **−0.005** |
| 2 | peninsula | 90 | +0.015 |
| 6 | peninsula | 90 | +0.016 |
| 4 | wall run | 0 | +0.018 |
| 9 | L run | 0 | +0.024 |
| 7 | wall run | 90 | +0.042 |
| 12 | island | 0 | +0.046 |
| 5 | peninsula | 0 | +0.052 |
| 3 | island | 90 | +0.053 |
| 8 | L run | 90 | +0.058 |

Grouped by facing the two sets overlap almost completely — facing 0 spans
−0.009 to +0.052 and facing 90 spans +0.015 to +0.058. **Orientation does not
explain this one.** Grouped by topology, every negative room is a wall run.

So the thread dies as an orientation story and lives as a topology one, and
the explanation is the same wall that the brightness section credited:

- a wall run's focal region contains 1.5 m of **lit vertical mass**, which is
  why wall runs read brightest;
- that mass is 1.5 m of **one flat ramp step**, which is why they read
  flattest.

Two metrics disagreeing about the same rooms, for one structural reason, each
of them right.

## The wall was a surface nobody used

The reference room is a wall run too, and it reads **+0.092** — above every
generated room in the table. What its back wall carries that a generated one
does not:

| | reference | generated wall run |
|---|---|---|
| menu boards | 2 | 2 |
| open wall shelving | **2** | **0** |
| hanging sign | **1** | **0** |

`A.wall_shelf` has been in the library since the second pass and was only ever
called for the *window bar's* worktop. `A.wall_sign` has been in it just as
long, with a docstring reading *"this is a focal device, not decoration — it is
the one bright, high-contrast object over the interaction zone, which is how
the composition tells the player where to look."*

**No generated room has ever had one.** A focal device that the focal check
never saw, sitting in the library the whole time the focal check was being
argued about. Two hundred lines of this file are about what the counter needs;
the answer was already written down in a docstring above the counter.

With the band between the counter top and the boards dressed:

| plan | before | after |
|---|---|---|
| 11 wall run | −0.009 | **+0.011** |
| 1 wall run | −0.008 | **+0.006** |
| 10 wall run | −0.005 | **+0.005** |
| 4 wall run | +0.018 | +0.033 |
| 9 L run | +0.024 | +0.036 |
| 7 wall run | +0.042 | +0.071 |
| 8 L run | +0.058 | +0.082 |

Minimum over twelve rooms **−0.009 → +0.005**, no room negative, and the five
wall-less rooms read bit-identical, which is the scope the change was supposed
to have. Brightness barely moved — plans 4 and 10 gained 0.004 and 0.002, plan
7 lost 0.007 — which is the point: this is detail, not mass, and the metric
that found it is the only one that reports it.

### Proposed and tested, because an index is not a footprint

First version handed out tiles by index: menus 0 and 1, shelves 2 and 3, the
sign in the middle. That put the sign through a shelf in three rooms and
through a menu board in three more, because `A.wall_shelf(1.6)` is two tiles
wide. The back bar shelving above already learned this and the rule is the same
rule, so it is the same loop — propose, test against `_conflicts`, keep or
drop. The sign goes first and takes the middle, because it is the one object
here with a place it needs to be.

### The floor, and how thin it is

Promoted into `check_focal_contrast` as a third reading off the same four
renders rather than as a twenty-fifth check, so the suite costs nothing extra.

Zero is not a tuned constant, it is the sign change: below it the busiest thing
in frame is not the thing the composition is pointing at. The bracket is
**0.010 wide** — three measured defects at −0.005, −0.008 and −0.009 against a
weakest good room at +0.005 — and thin is the honest report rather than a
reason to round the floor somewhere more comfortable. A wall run that loses its
shelf will fail this, and should.

Verified in both directions on shipped code: clean at 0.000, and at a floor of
0.020 it reports *plan 1 (wall run): counter carries +0.006 detail against its
room* and *plan 2 (peninsula): +0.015*. Those two numbers match the standalone
edge script to three decimals, which is the check and the experiment agreeing
through two separate implementations.

## Still open

- **Stages 1–3** (SDXL concept → TRELLIS 2 mesh → UniRig rig) need a GPU and
  model weights. The seam (`ingest.py`) is built and checked; nothing feeds it.
- **Counter orientation costs the focal lead 0.04 and nothing compensates.**
  A run whose long face points +y is raked by the key at N·L = −0.116; one
  pointing +x gets +0.874. Over twelve rooms the two groups do not overlap.
  Left open rather than fixed because the reference room is itself a facing-0
  run reading +0.019, so the orientation is weak and not broken, and a rig
  boosted until the metric agreed would be a knob rather than a cause. The two
  rooms nearest the floor (+0.018, against 0.015) are both in this group.
- The **focal reading still falls with render resolution** in generated rooms
  and holds in the reference one, because contrast is a percentile spread over
  37 quantized lightness levels. The scan and the suite check now at least
  grade at the same 320; the delivered render is 480 and the gap is stated
  rather than tuned away.
- **Furniture screen spread** now has an owner for its *closest pair* (0.045,
  bracketed by measurement) but the mean-spread floor of 0.15 is still close to
  the original guess. It has never rejected anything the closest-pair floor did
  not also reject, which is either redundancy or a floor set too low to fire.
- **The detail floor's bracket is 0.010 wide.** Three measured defects at
  −0.005 to −0.009 against a weakest good room at +0.005. It is the tightest
  floor in the suite and the first one whose margin is smaller than the
  difference between two adjacent rooms.

---

## The key-light-drift check was right about the drift and wrong about the cause

The refreshed worklist's one item nobody had triaged: `review_queue.py`'s
set-level check (`check_direction_set`) compares a sprite's brightest-region
centroid across its 8 directions and, if it moves more than 6px, says the
key light is anchored to world space instead of the camera. Run against the
current 22-object lifted library instead of the 3 it was last checked
against: 19 of 22 fire.

That is not 19 lighting bugs. Re-read `mesh.rasterize()` and
`render_batch.render_sprite()` line by line: `light = camera_light(cam)` is
called fresh inside `rasterize()`, and `render_sprite()` builds a fresh
`DimetricCamera(azimuth)` per direction before calling it. The key is
genuinely re-resolved into world space every azimuth. The bug this check was
built to catch -- a world-fixed light, from the first batch, per its own
docstring -- is not back.

The three passes are the tell: kettle, candle, french_press are the three
objects in the library closest to a body of revolution -- round in plan, so
almost nothing about their lit region moves in screen space as they turn.
Rendered wall_clock's and picture_frame's full 8-direction sheets to check
the failures by eye: wall_clock is a thin disc whose two bright frames show
its cream face and whose other six show a plain grey back or a dark edge --
the object's own geometry alternates between showing its one bright material
and not showing it, which a body of revolution never does. picture_frame's
pale photo inset is off-centre on the object and simply changes screen
position as the camera orbits it. Neither is the key light moving; both are
"top 20% brightest pixels" picking up albedo, which most objects in a café
have more of than a kettle does.

Tried the obvious fix -- restrict the brightest-pixel pool to each frame's
dominant palette ramp before measuring, so a cream face can't out-compete a
grey edge for the centroid. Measured before/after on all 22: fixed 2
(teapot; cutting_board close), and broke a clean pass -- candle went from
5.1x3.9 (ok) to 3.4x16.2 (fail), because narrowing the pool to one ramp left
too few pixels and the centroid got noisier than the cross-material signal
it removed. Not shipped, per this repo's own rule about testing a remedy
before a check recommends it. A fix that actually separates the two signals
needs the raw per-pixel material id `rasterize()` already computes and
`review_queue.py` never receives -- it only ever sees the final quantized
PNG.

**Shipped instead:** the check's own fix message, which was flatly wrong
(asserting an unfixed world-space bug that isn't there), rewritten to name
the real, evidenced cause and point at the three round objects as the ones
whose failure would actually mean something. The measurement itself is
unchanged -- still fires on the same 19, because no tested fix reduced that
number without costing a false negative elsewhere. This is the same shape of
result as C4's auto-uprighting: the diagnosis was worth writing down more
than the number was worth moving.

---

## `MAX_SOFT_ALPHA`, split by shape instead of by number

The prior pass's finding: one threshold, three causes. Genuine bad
generations (bread_loaf, croissant -- duplicate ghost instances), a real
segmentation failure on a clean subject (book -- low contrast against a
near-white background), and legitimately hard subjects that are false
rejections (fern's fronds, bicycle's spokes, bottle's glass). Fixing the
ratio's cap would have let the first two back in; leaving it alone kept
rejecting the third.

The three causes turned out to have different SHAPES, not just different
ratios. A fine silhouette's soft-alpha pixels form a rim: every one of them
sits within a few pixels of a confident interior pixel, because they're
tracing an edge. A duplicate ghost or a low-contrast failure is its own
region, mostly far from anything the matte was ever sure about. Built a
second signal on exactly that difference -- of the pixels that are soft, what
share have no confident (alpha >= 232) pixel within a 3px box -- and measured
it against the same 31-subject set:

| | detached share |
|---|---|
| bread_loaf, croissant, book (genuine defects) | 73-89% |
| fern, bicycle, bottle (false rejections) | 36-54% |
| coffee_cup, sugar_bowl, creamer, cheese_wheel (clean passes) | 19-27% |

A 19-point gap between the worst false rejection and the best genuine
defect. `DETACHED_SOFT_FLOOR = 0.65` sits in it. Wired into
`check_concept_fitness` (`tools/concept.py`) as a second condition: the ratio
cap still has to fire first (unchanged, still the cheap common case), and
only then does the detached-share check decide whether it's a rim or a
region.

Verified in both directions on the same 31 subjects: fern, bicycle and
bottle now pass; bread_loaf, croissant and book still fail, with the same
message plus the detached-share reading; every subject that passed before
still passes (the new condition only ever removes a failure, it cannot add
one, since it's a stricter AND on top of the existing cap). 23 of 29 subjects
pass now, up from 20 -- and the 3 that flipped are exactly the 3 named as
false rejections, nothing else moved.

---

## Bind dE, logged the way albedo shift already was

Small, mechanical, named in the prior pass: `ingest.rebind()` and
`bind_vertex_colours()` (`tools/ingest.py`) already compute a worst-case
vertex-colour bind dE; it only ever reached a human as a conditional warning
string, never as a number `factory.py` could log unconditionally the way
`delight()`'s albedo correction already is.

Added `worst_bind_de` to `ingest()`'s report dict on both binding paths (the
vertex-colour path already computed `worst`; the MTL/`rebind()` path gets it
as `max(d for _, _, d in table)`), and `factory.py` now copies it into each
subject's result. Verified directly against an existing raw mesh rather than
through a full GPU re-run -- a 31-subject re-generation hung partway through
this session on GPU memory pressure unrelated to this change (see below) --
`ingest('out/mesh/teapot.obj', height=0.28)` returns `worst_bind_de: 0.128`
in the report, confirming the field is populated on the path every lifted
object takes.

This is the second half of the prior pass's before-baseline for a style
LoRA: albedo shift was already logged (mean 0.111, worst 0.306), bind dE was
not. Now both are, for whenever that question comes back.

**Operational note, not a code finding:** the verification run stalled on
`mug` after `teapot` succeeded -- GPU memory at 7.6/8.2GB with the process
reporting 0% CPU for a sustained period (confirmed via two `Get-Process`
samples 5s apart, identical CPU time). Killed and GPU memory recovered to
0.9GB. Twenty-five stale PIDs showed up in `nvidia-smi --query-compute-apps`
at the time, suggesting Windows CUDA context cleanup lags process exit
across a long session that has loaded and unloaded SDXL/TripoSR many times.
Not chased further -- worth knowing if a future multi-subject GPU run hangs
the same way.

---

## `leafy_plant` unified onto `_mix`

Mechanical: the one generator with its own inline LCG (`tools/assetlib.py`)
now calls the shared `_mix()` every other seeded generator uses, in place of
its own `(seed * 2654435761 + 1013904223)` / `(st * 1103515245 + 12345)`
pair. Verified both ways -- the plant is still a plant (checked vertex/face
counts and bounding box across two seeds, both reasonable and different from
each other), and re-running D3's instrumentation script against it now
reports 8 real draw sites with 0 dead, the same shape of result the other 12
generators already had, where before it reported 0 sites because the
instrument had nothing to see.

One side effect, caught by re-running `manifest.py --check` after all of
this pass's edits: `check_focal_contrast` now fails on plan 1 (wall run),
"counter carries -0.002 detail against its room (floor +0.000)" -- a check
that was clean before this pass. Isolated with `git stash push --
tools/assetlib.py`: reverting only the RNG change makes it pass again, so
this is that change and nothing else. Plan 1's dressing draws a potted
plant; a different draw from `leafy_plant`'s new RNG stream shifted the
room's detail composition by enough to cross a floor B4 already measured at
0.000 with a 0.002-0.006 margin on either side.

This is not a new defect -- it is B4's own finding (the detail floor's
margin is thinner than a single generator's RNG stream) confirmed from a
completely unrelated direction. Kept the RNG fix rather than reverting it:
a real cleanup should not be held hostage to a floor already on record as
too thin to bear this kind of weight, and reverting it to keep one borderline
room passing would be exactly the "tune until the metric agrees" move C4
already rejected for a different check. `NEXT.md`'s gate note is updated to
name both known-thin-margin cases -- `build_plan.py --focal-scan 12`'s plan
10 and `manifest.py --check`'s plan 1 -- so neither reads as a surprise to
whoever hits it next.

---

## The double-run topology: scoped wrong the first time

D4 called this "shovel-ready" -- reuse the run/back/queue triple a second
time, mirrored on the far wall. Read `build_plan.py` before writing a second
generator branch: eight places consume `plan.of("service")` or
`plan.of("backbar")`, and four of them do it as `[0]` -- a single, hard-coded
index, not a loop. `light_rig()` is one of them, and its own comment already
records the cost of getting this wrong once: a fixed offset generalized from
the reference room's one counter pushed the light pool off a *different*
counter's face entirely, and the fix was measured in points of mean L on the
counter, not noticed by eye until it was.

Adding a second `Zone("service", ...)` under that pattern doesn't fail
loudly. It renders a room with one lit, dressed counter and a second, bare
one sitting in relative dark -- the exact defect class this repo has already
found and fixed twice (`light_rig`'s own history, and the "counter was
under-dressed" entry earlier in this file). A topology whose entire promised
value is stress-testing which way a counter faces is not worth shipping in
the one shape that silently produces an under-lit counter.

**Not built this pass.** The real cost is a `build_plan.py` audit across all
eight touch points -- deciding per site whether the second run should be
treated identically to the first (lit, dressed, walkable) or is a
lower-fidelity display counter that only needs blocking/collision -- not the
`floorplan.py` branch alone. Left for a pass that can give `build_plan.py`
the same attention `floorplan.py` got.

---

## L run's corner is real, and it isn't the whole story

D1's lead: L run turns a corner, and `focal_box()` (`tools/build_plan.py`)
bounds the focal region as the union of `service` + `backbar` +
`service_return` -- an L run's box necessarily includes the arm, a wall run's
doesn't. Measured directly, filtering the 60-seed sample to wall run and L
run and computing each plan's actual focal-box area alongside its detail
reading:

| | n | focal-box area | mean detail |
|---|---|---|---|
| wall run | 24 | 8.30-12.96 (mean 10.43) | +0.0401 |
| L run | 10 | 17.92-26.80 (mean 23.41) | +0.0206 |

L run's box is 2.2x wall run's on average, and its mean detail is roughly
half. That is consistent with dilution -- a bigger region to average
"busiest thing in frame" over pulls the mean toward whatever the arm and the
corner contribute, which is presumably less than the run itself.

Consistent is not sufficient. The correlation between area and detail
*within* L run alone is -0.245 -- the right sign, too weak to carry the
finding on its own -- and there is a direct counter-example: plan 38 has the
single largest focal box in the L-run sample (26.80) and one of its best
detail readings (+0.052), while plan 8 has the smallest box (17.92) and
the second-best. If dilution by area were the whole mechanism, the ranking
would run the other way.

**Left as B4 left it, one layer deeper.** The corner enlarges the box, the
box enlarging correlates weakly with worse detail, and neither claim
survives being asked to explain plan 38 or plan 8 on its own. This is a real
partial lead, not a found cause -- worth keeping in mind for whoever
eventually builds the double-run topology (B2), since that layout's focal
box would be larger still by the same mechanism, deliberately, and would
test whether "the box got bigger" was ever really the story or just the one
variable this pass had a way to measure.

---

## Godot export: the resource loader was the whole problem, and it has one fix

The factory produces sprites; nothing consumed them. Building
`tools/export_godot.py` (stage → import → build, see `PIPELINE.md` "Stage 10")
found exactly one real obstacle, and it explains a class of failure worth
naming precisely: Godot's `load()` refuses a PNG that has never been through
an editor import pass (`No loader found for resource`), and the obvious
workaround -- `Image.load()` + `ImageTexture.create_from_image()` -- "works"
in the sense that it produces a texture and `ResourceSaver.save()` returns
`OK`. It just doesn't produce the resource you asked for: the texture isn't
backed by a file resource, so anything referencing it (an `AtlasTexture`,
here) has nothing to point a lightweight `[ext_resource]` at, and gets the
raw pixel data inlined as a `[sub_resource type="Image"]` block instead.
Measured directly on one 64x64 sprite: 61143 characters embedded inline
versus 420 once the same sprite was properly imported first.

The fix is `godot --headless --import` before anything touches `load()` --
confirmed to work on the standard (non-export-template) 4.3 binary despite
`--help` tagging `--import` as an editor-build capability. No GUI window
opens; it imports every asset under the project root and exits. Full pipeline
run across the 22-object library: 176 frames staged, imported, and built into
22 `SpriteFrames` resources (92KB total, referencing 1.5MB of staged PNGs by
path) with per-direction pivot/bbox/azimuth and per-asset
height/footprint/anchor/walkable carried as resource metadata -- lossless
relative to `manifest.json`, just reshaped into Godot's vocabulary.

At the time this was written, reference-image conditioning (below) was the
deferred "examples" half of the product goal. It's since been built.

---

## Reference images: one real bug, one measured knob

`concept()` gained an optional `reference` image, conditioning SDXL via
IP-Adapter alongside the text prompt -- see `PIPELINE.md`'s "Reference
images" for why IP-Adapter and not img2img (img2img imports the reference's
own camera angle, which is exactly the drift the fixed `STYLE` clause exists
to prevent).

**The bug**: `load_ip_adapter()` attaches a CLIP vision encoder that did not
exist when `_pipe()` first called `enable_model_cpu_offload()`, so it never
got an offload hook and sat on CPU while everything else ran on CUDA. First
call crashed inside the encoder's own first conv layer:
`RuntimeError: Input type (torch.cuda.HalfTensor) and weight type
(torch.HalfTensor) should be the same`. Not a guess -- read directly off the
traceback, which named `modeling_clip.py`'s `patch_embedding` as the failing
op. Fixed by re-running `enable_model_cpu_offload()` after
`load_ip_adapter()`; accelerate's offload hooks attach per-module at call
time, so a module added after the first `enable_model_cpu_offload()` call
just never got one until a second call swept it up too.

**The knob**: `--ip-scale` needed a default, and picking one meant actually
sweeping it rather than guessing round numbers -- this repo's own rule 1
("bracket every floor between a measured defect and the weakest known-good")
applied even though this isn't a pass/fail gate. One reference (a matte
ceramic teapot photo, copper handle) against a prompt naming a conflicting
material ("a glass vase"), same seed, six points on the sweep:

| ip_scale | glass vase renders as |
|---|---|
| 0.3 | glass, body proportions alone pull toward the reference |
| 0.4 | glass, gains one handle + spout |
| 0.45 | glass, gains two handles |
| 0.5 | glass, two handles, more pronounced |
| 0.6 | **opaque matte ceramic** -- material overridden |
| 0.85 | near-reproduction of the reference, copper accent included |

The first pass through this shipped 0.6 as the default on the strength of a
guess ("0.3 barely shifted colour, 0.8 pulled proportions through") that
turned out wrong in both directions once actually measured -- 0.6 already
loses the prompt's material entirely. Default corrected to 0.45, just under
where the transition happens for this pair. `proof/reference_image_conditioning.png`
is the contact strip: reference, prompt-only baseline, 0.45, 0.6.

One reference/prompt pair, not the swept bracket the fitness floors have.
Recorded as a starting point and a warning against guessing constants this
file's own discipline says to measure, not as a calibrated default -- a
reference that doesn't fight the prompt on material should tolerate a
higher scale before losing it.

**Not done**: no subject in `subjects_c1.yaml` uses a reference yet. This
pass built and verified the capability; pointing it at real reference photos
is separate work.

---

## `--ip-scale` doesn't get one right answer, so it got a slider instead

The sweep above is the argument against hard-coding a second guess at
`--ip-scale`: the right value depends on how much a specific reference
conflicts with a specific prompt, which is not something to automate a
threshold for -- it's a judgement call, the kind this repo already routes to
a human at stage 9 rather than pretending a metric could make it. `tools/
concept_ui.py` is a small local Gradio app over the same `concept()` and
`check_concept_fitness()` the CLI and `factory.py` call -- prompt box,
reference upload, `ip_scale` slider, and the raw render / matte / fitness
verdict shown for whatever just generated.

Verified live rather than just import-checked: launched the server, drove it
through an actual Chrome tab via the browser-automation MCP, typed "a wicker
basket", hit Generate, and watched it through the real ~40s SDXL round trip
(pipe load included, first call). It worked, and it caught something real on
the way: this particular seed generated a 4x3 grid of baskets instead of one
isolated object, and the fitness gate reported it correctly and specifically
-- "a second mass 48% the size of the main one (cap 15%)", among four
findings -- the same message the CLI would have printed, because it's the
same function. The reference-image upload path wasn't driven through the
browser itself (the browser session's file-upload permissions only allow
files explicitly shared with it, unrelated to anything in this app), but
`generate()` passes the uploaded path straight into the identical
`concept(reference=..., ip_scale=...)` call the six-point sweep above
already exercised directly and confirmed working.

**The calibration backlog has not moved across either of these passes and is
not forgotten**: `counter orientation` (0.04 focal-lead cost, unresolved),
the `focal reading falls with render resolution` gap, `furniture screen
spread`'s possibly-redundant mean floor, and the `detail floor`'s
0.010-wide bracket (see the "Still open" list above this entry) are all
exactly where they were left. Neither the Godot export work nor the
reference-image work touched a generator, a check, or a threshold, so
neither could have moved them either way.

## The collage failure mode, and the 77-token ceiling that was already most of the way there

A phone-triggered generation of "Frog character from chrono trigger" came
back gated with three findings, all pointing at the same thing: SDXL had
rendered a tiled sheet of roughly thirty small frogs instead of one isolated
object, and `check_concept_fitness()` caught it correctly ("a second mass
100% the size of the main one" among others). This is a known SDXL failure
mode -- the model falls back on grid/collage/character-sheet training data
when a prompt reads as "a thing with many variants" rather than "one thing"
-- and it's more likely for named characters and generic multi-instance
nouns (baskets, coins) than for prompts that already read as singular
objects.

The first fix attempt added roughly a dozen anti-collage terms to `NEGATIVE`
-- "collage, grid, tiled, tiled pattern, sticker sheet, character sheet,
reference sheet, model sheet, turnaround, multiple poses, many variations,
repeated, pattern, array" -- and re-ran the frog prompt. It came back clean.
Case closed, except a routine "how many tokens is this now" check turned up
`transformers`' own warning: 105 tokens against SDXL's CLIP tokenizer,
which hard-truncates at 77 (BOS/EOS included) with no error and no default
warning of its own. Counting where 77 actually landed in the string showed
only "collage, grid, tiled" -- the first three added words -- had survived;
every other term added, including the two most specific ones ("character
sheet", "turnaround"), was silently past the cliff and never reached the
model. The fix had "worked" for the wrong reason: the base 68-token
`NEGATIVE` plus those three words was the entire effective change, and the
other nine terms were decoration. This is exactly the kind of failure this
repo's discipline exists to catch -- bracket the floor, verify with the
actual instrument, don't trust a fix that wasn't measured against what the
model actually receives -- so `concept()` now checks
`len(pipe.tokenizer(text).input_ids)` itself and prints to stderr whenever
a prompt or negative crosses 77, for `negative_extra`/`positive_extra`/the
override fields where a silent truncation could otherwise ship unnoticed
again.

`NEGATIVE` was trimmed back to exactly the surviving, verified addition (75
tokens total: the original 68 plus ", collage, grid, tiled"). Re-run against
the frog prompt at the same seed: clean, no findings. Re-run against a
teapot at the same seed, as a regression check: unchanged, still clean.
Re-run against a wicker basket that had independently collaged in an
earlier pass (a different, generic-noun instance of the same failure mode,
not the same bug as the frog's): **still fails**, and worse on the numbers
-- 54584% soft-alpha ratio against a 5664% un-fixed baseline. This is
recorded as a negative result rather than smoothed over: the anti-collage
negative helps the failure mode it was measured against and is not a
universal fix. Some collage failures are seed-specific, not prompt-specific,
and the honest remedy there is "change the seed," which `factory.py`
already supports per-subject.

Frog's specific case -- a small, non-photoreal creature described by name --
also raised a question the repo hadn't answered yet: `character.py` is
fully procedural and part-based, built for original café-cast archetypes
(barista, customer), and never takes a text prompt at all; `concept.py` was
built around the isolated-single-prop framing. Neither covers "a specific
named character," which pulls SDXL toward fan-art and character-sheet
training data harder than a generic noun does -- the exact pressure that
produces the collage failure in the first place. Rather than add a third
generator, `concept()` gained a `kind` parameter (`prop`, the existing
default, or `character`) that swaps in a dedicated `NEGATIVE_CHARACTER`
string instead of adding to the same one -- it had to be a swap, not an
addition, to stay under the same 77-token ceiling that caused the first
problem. It drops four lower-value terms ("depth of field, bokeh,
reflection, mirror") to make room for three targeted ones ("character
sheet, turnaround, multiple poses"), landing at 72 tokens.

Measured against three character-style prompts at seed 1, base `NEGATIVE`
vs. `NEGATIVE_CHARACTER`: frog passes under both (the base fix already
covered it); a knight ("a knight character with sword and shield") passes
under both; Mario ("Mario from super mario bros" -- about as heavily
represented in character-sheet and fan-art training data as a prompt can
get) fails under both, but `NEGATIVE_CHARACTER` cuts the severity a real
amount -- soft-alpha ratio 162643% down to 2156%, detached-mass fraction
100% down to 90%. Reported as what it is: a genuine reduction, not a fix.
Some subjects are famous enough that no negative-prompt string is going to
out-compete their training-data weight; `--reference` (below) is the
better lever there, or a less iconic description.

All three of `concept()`'s own current numbers were re-verified end to end
through the shipped function itself, not hand-rolled duplicates of its
logic, immediately before shipping: frog×`kind=prop` clean, frog×
`kind=character` clean, teapot×`kind=prop` unchanged (regression-clean),
and a deliberately 106-token `negative_extra` confirmed to both print the
new stderr warning and still run rather than error.

**Multiple references, not one.** The same session's other open question --
can `--reference` take more than one image -- turned out to be yes, but not
by averaging. diffusers' IP-Adapter conditioning requires one image per
loaded adapter *slot*: N reference images means loading the same IP-Adapter
checkpoint N times as N independent slots
(`subfolder=[...]*N, weight_name=[...]*N`), each conditioned on a different
image, with the blending happening inside the UNet's cross-attention rather
than in Python. `concept()`'s `reference` argument now accepts a single
path or a list, `ip_scale` accordingly accepts a single value or one per
reference, and `_set_reference()` reloads the adapter whenever the slot
count changes between calls sharing one pipe (the same one-pipe-per-session
model `factory.py` already uses). Verified live: a teapot and a basket as
two simultaneous references produced one coherent object, not two
overlaid, confirming the UNet is doing real per-slot blending and not just
taking the last image loaded.

`tools/concept_ui.py` picked up all three changes: a Prop / Character /
Custom radio (custom exposes full positive/negative override text boxes,
for anything that doesn't fit the isolated-single-object framing those two
presets assume -- a flat icon, a different camera angle), a multi-file
reference upload replacing the single-image one, and an examples panel
showing what a good prompt looks like in each mode, including the specific
warning that naming a source franchise pulls harder toward the collage
failure than describing the design does. Verified live through the browser:
built the layout, toggled Custom to confirm the override fields actually
show and hide, then ran a real generation ("a brass coffee grinder") through
the full ~40s SDXL round trip and watched the fitness gate report PASSES.

**The calibration backlog is still exactly where the previous entry left
it** -- none of this touched a generator, a check, or a threshold either.

## The UI stopped at the render; a "Continue" button now carries it to a sprite sheet

A concept passing the fitness gate is not a finished asset -- it is stage
1's output, and everything a person could see of it in `concept_ui.py` was
a raw render and a matte. Getting from there to something reviewable meant
dropping to the CLI: `lift.py`, then `ingest.py` with a hand-typed
`--height`, then `render_batch.py`, invoked one at a time or bundled into a
`subjects.yaml` entry for `factory.py`. That's the right shape for a batch
of forty; it's friction for "is this one thing worth pursuing at all,"
which is exactly the question the UI exists to answer quickly.

`concept_ui.py` gained a `height` field and a "Continue -> mesh + sprites"
button. It does not call anything new -- `lift.lift()`, `ingest.ingest()`,
`render_batch.py`, and `review_queue.py build` are the same four calls
`factory.py`'s `run_subject()` makes for a batch, invoked directly instead
of through a subject-list YAML. TripoSR loads once and stays resident the
same way the SDXL pipe does, via the same `_pipe_holder`-style cache
pattern.

The one design decision worth recording: Generate's output
(`out/concept_ui/current.png`) is scratch, overwritten every run, by
existing design -- so Continue's first act is to *promote* it, copying the
current concept into `out/concept/<slug of the subject text>.png` before
running the later stages. Slugged names land in exactly the paths
`factory.py` already checks for existing output
(`out/mesh/<name>.obj`, `out/sprites/<name>_dir*.png`), so a subject worked
up here and later added to a `subjects.yaml` under the same name is
recognised as already done through however many stages got run in the UI --
the two paths share state instead of silently duplicating it.

Verified live and end to end, twice: once by staging a known-good matted
concept directly and calling `continue_to_sprites()` in-process (teapot,
height 0.28 -- produced a real bound OBJ and an 8-direction pixel contact
sheet at `review/sheet.png`, all under the exact `factory.py` naming
convention), and once through an actual browser session driving the real
button -- typed "browser continue test mug", generated, passed the fitness
gate, set height 0.12, clicked Continue, and watched TripoSR load cold and
the sheet fill in with 8 real sprite frames of the mug, footprint 0.125,
status text confirming all three output paths. Both runs' artifacts were
removed afterward along with the manifest entries they added; `review/
sheet.png` and `review/verdicts.jsonl` are tracked files and were restored
to their prior committed state rather than left showing test output.

## The character ceiling is stage 2, not stage 1, and two cheap fixes both failed

The `kind="character"` work above fixed the *concept image* for a named
character. It said nothing about whether the rest of the pipeline could do
anything with one, and the honest answer, now measured, is no.

Taking the passing frog concept all the way through (`lift` → `ingest` →
`render_batch` → `review_queue`, height 1.2) produces a sprite set that
`art_review.py` blocks on 4 of 8 frames: 11-12% of opaque pixels match none
of their four neighbours, against a check whose floor is "authored art
measures under 6.2% on its busiest frame". Every frame also warns on
cross-ramp adjacency at 17-25% against clean toon shading's ~2.5%. The
mesh is a lumpy semi-fused blob -- no cape, no separable limbs, no rapier,
and nothing a person would call a knight.

Benchmarked against the real thing rather than against a feeling: the
original SNES sprite sheet was looked at directly (viewed for comparison
only; nothing copied, saved, or reproduced). Its ~60 frames are flat colour
fields inside a dark outline, six to eight colours a frame, with limbs and
the sword separately legible at 32px. That cleanliness is a property of
being hand-authored -- every pixel a decision -- and it sets the bar the
cross-ramp check is already encoding. Our frames are not a worse drawing of
the same thing; they are a different class of object, geometric noise
rendered faithfully.

Two cheap remedies were proposed and both tested before either was
believed:

- **Coarser marching cubes** (`lift.py --resolution 128` against the default
  256), on the theory that a coarser grid cannot represent the
  high-frequency surface noise the blocker is catching. Result: a wash.
  Still 4 of 8 blocked, blocker 11.5% → 10.9% mean, cross-ramp 21.5% →
  19.7%. Both inside noise. This rules out voxel size as the cause: the
  reconstruction is producing the wrong *shape*, not a correct shape sampled
  too finely.
- **Simplifying the prompt to reduce occlusion** ("arms visible at sides, no
  cloak, weapon held clear of the body, simple silhouette"), on the theory
  that a cloak and a held weapon are exactly the self-intersecting geometry
  a single view cannot resolve. Result: **measurably worse, on every frame**
  -- 8 of 8 blocked, blocker mean 15.3%, cross-ramp mean 28.2%. The reason
  is visible in the sheet and is worth keeping: asking for the weapon *clear
  of the body* gave TripoSR a thin unsupported protrusion to reconstruct,
  and thin unsupported geometry is the single thing single-view
  reconstruction is worst at, because there is no volume to anchor it
  against. The change did partly work on the axis it targeted -- legs
  separate into a real bipedal stance in several frames, more humanoid than
  baseline's undifferentiated blob-bottom -- and it still lost, because the
  floating blade cost more than the stance gained.

So the character ceiling is TripoSR, and neither prompt engineering nor a
reconstruction parameter moves it. The lever that would is a better
reconstructor -- TRELLIS 2 -- which remains blocked on this workstation's
toolchain for the reasons already recorded under accepted limitations, and
which is a decision about somebody's hardware rather than about this repo.

**What this does not say** is that the pipeline is broken. It says the
pipeline is a *prop* pipeline. The same batch that cannot make a frog knight
took 22 of 31 café props to clean sprites, and the teapot and mug taken
through the new Continue button both came out auto-clean with no blockers at
all. The honest scope line is object-shaped things without articulation,
and it should be written down as such rather than discovered per-subject.

## The 29% that was being thrown away, and the one kind that stays thrown away

If the scope line is "props," then the number that matters for throughput is
the prop batch's own: 22 of 31 clean, 9 gated. Worth looking at what those 9
actually were before accepting them as the cost of doing business, because
**every one of them failed at stage 1**, not at reconstruction -- and several
by a hair: 11.7%, 11.2% and 10.9% against a 12% frame-fill floor. Nothing
retried them. A human had to notice and re-run with `--force`.

An earlier entry above established, while chasing the basket's collage, that
this class of failure is *seed*-specific rather than prompt-specific, and
concluded "the honest remedy there is reseed and retry." That was a
conclusion drawn from one subject, so before automating it, it got measured
on six: the three near-miss frame-fill failures and the three soft-alpha
ones, at seeds 2, 3 and 4. Five of the six passed.

**That first measurement was wrong, and finding out why matters more than
the number did.** The end-to-end check afterwards -- force `book` through
`factory.py` and watch the retry fire -- showed `book` passing on seed *1*,
with no retry at all. The report those nine failures came from predates B1's
`MAX_SOFT_ALPHA` / `DETACHED_SOFT_FLOOR` split, and `NEXT.md` says plainly
that fern and bicycle now pass under the recalibrated check. So the sweep had
taken its seed-1 baseline from a stale file and only ever re-run seeds 2-4:
any subject the recalibration had already fixed looked like a reseed rescue
while reseeding did nothing. A measurement that never re-establishes its own
baseline is measuring the baseline's age.

Re-run properly -- seed 1, all nine, current gate -- three of the nine
(`book`, `fern`, `bicycle`) already pass and were never reseeding's to
rescue. Every remaining soft-alpha failure is gone too; the six still gated
now fail on frame fill or a second mass, not on alpha at all. Against that
corrected baseline the honest tally is **three genuine rescues of four
tested**: `wine_glass` (11.9%), `cake_slice` (10.9%) and `croissant` (2.6%)
all pass on seed 2, and `wooden_spoon` fails at every seed. `bottle` and
`bread_loaf` were not tested above seed 1. Three of four is still a good
enough return to keep the feature; five of six was never real.

`wooden_spoon` is the interesting failure, and it is why this is a bounded
fix rather than a general one. It failed at **every** seed -- 7.7%, 11.9%,
5.4% frame fill -- and the reason is not noise. A long thin object is
systematically small in frame once `STYLE`'s "full object in frame with
generous margin" clause has been honoured: the margin is sized to the
spoon's length, which leaves its width occupying almost nothing. Reseeding
cannot change the aspect ratio of a spoon. That is a framing/floor question,
taken up separately below, and it turns out to be the more interesting one.

So `RETRY_SEEDS = 2` in `factory.py`, not 3: the third attempt bought nothing
in the sample and costs a full generation per subject. Retries apply only to
a concept generated in the current run -- an existing `out/concept/<name>.png`
is still respected exactly as before, because "skip what is already done" is
what makes a half-finished batch resumable, and quietly overwriting a
previous run's output to chase a gate would trade one surprise for another.
When a retry does succeed it is recorded in the report (`seed_used`, plus a
note in `detail`) rather than passing silently: a subject that needed three
attempts has a marginal prompt, and that is worth seeing even though the
asset came out fine.

Projected against the last full batch: three of the nine already pass on the
recalibrated gate without any of this, and reseeding should convert most of
the remaining near-misses, leaving the spoon-shaped ones -- call it 22/31 to
somewhere around 28/31. Projected, not measured. The full batch has not been
re-run, and after the baseline mistake above, an unmeasured projection is
exactly the kind of number that deserves the label.

## `MIN_FILL` was rejecting better work than it was admitting

Correcting the reseed baseline left every surviving stage-1 failure looking
like the same thing: `bottle` 10.9%, `wooden_spoon` 11.1%, `wine_glass`
11.9%, `cake_slice` 10.9% -- four of six sitting within a point and a half
of `MIN_FILL = 0.12`. A cluster that tight against a threshold is either a
real boundary or an arbitrary one, and `MIN_FILL`'s comment is one line
long ("object share of the frame") with none of the bracketing every other
floor in this file carries. That absence was the tell.

Its stated reason is "too little resolution on the thing being
reconstructed" -- a claim that fill predicts reconstruction quality. That is
testable against work already on disk. Twenty library subjects that passed
the floor, scored by how many of their eight frames `art_review` blocks:

    14.1% rolling_pin    3/8      27.6% sugar_bowl      0/8
    19.8% coffee_cup     0/8      28.8% french_press    0/8
    21.8% table_lamp     0/8      28.9% book            0/8
    22.3% umbrella       0/8      31.1% basket          8/8
    25.8% candle         0/8      32.0% kettle          0/8
    26.6% mason_jar      0/8      33.7% teapot          0/8
    27.3% creamer        0/8      34.2% newspaper       3/8
    27.4% potted_plant   1/8      35.2% teacup_stack    0/8
    27.5% flower_pot     2/8      35.5% stack_of_books  3/8
                                  37.5% cutting_board   7/8
                                  40.6% cheese_wheel    0/8

There is no relationship. The two worst sets in the library -- `basket` at
8/8 and `cutting_board` at 7/8 -- are among the *best*-filling subjects
there are, and mean blocked frames are higher above 25% fill (1.50) than
below it (0.75). Whatever makes a sprite set bad, it is not how much of the
concept frame the object occupied.

That sample cannot speak below 14.1%, though, and the reason is a selection
effect rather than an absence: the floor stopped anything lower from ever
being built. So three sub-floor concepts were forced through `lift` →
`ingest` → `render_batch` → `art_review` anyway:

    11.9% wine_glass    0/8 blocked
    10.9% bottle        0/8 blocked
    10.9% cake_slice    2/8 blocked

Two of the three are perfectly clean, and the group mean (0.67) is *better
than the library average the floor admits* (1.35). `MIN_FILL` is not
protecting stage 2 from anything. It is rejecting work that outperforms what
it lets through, and it has been doing so silently -- four subjects in the
last batch, gated on a threshold with no measurement behind it.

The obvious next move was to find where the claim *does* become true, since
an object occupying twelve pixels surely cannot be reconstructed. The two
lowest-fill concepts in existence went through the same treatment, and the
answer is that it does not become true anywhere measurable:

     2.6% croissant    0/8 blocked
     8.9% bread_loaf   5/8 blocked

The *lowest*-fill subject there is came out clean, and the one above it came
out bad. Looking at the frames settles what the numbers only imply:
`croissant` is eight recognisable crescents with good silhouette and
colour -- a genuinely usable asset that the floor had been discarding -- and
`wine_glass` at 11.9% reads clearly as a glass, stem and base included.
`bread_loaf` really is bad, blobby and inconsistent between directions.

The mechanism, once seen, is obvious and is the whole explanation:
`render_batch.frame_all()` refits the camera span to the mesh's own bounds
across all eight azimuths. A small object gets framed to fill the sprite
regardless of how much of the *concept* it occupied, so concept fill was
never going to survive into the sprite as resolution. `bread_loaf` fails
because a loaf is an amorphous form with no stable silhouette for TripoSR to
recover, which has nothing to do with its size in frame.

So `MIN_FILL` drops from 0.12 to 0.02 -- placed just under `croissant`, the
weakest thing actually shown to work, rather than pretending to a bracket
the data does not support, and left in place only to catch degenerate
segmentation. Re-gating the nine at seed 1 under the corrected floor:
**eight now pass, and the one still rejected is `bread_loaf`** -- the one
that genuinely produces bad sprites. The gate went from rejecting six
subjects of which four were good, to rejecting one that deserves it.

Two things worth saying plainly about what this does to the entry above it.
First, most of what auto-reseed was rescuing, it was rescuing from a
threshold that should not have been there: `wine_glass`, `cake_slice` and
`bottle` all pass on seed 1 now, no retry involved. Reseeding keeps its
value for genuine seed noise -- collage, a stray second mass -- but it was
treating a symptom, and the honest ordering is that the threshold was the
bug. Second, `wooden_spoon`, whose stubbornness prompted this whole line of
enquiry, passes too. The spoon was never the problem; the floor was.

The general lesson is the one this file keeps relearning: a threshold with
no bracket recorded is a guess, and a guess that gates work is expensive in
a direction nobody measures, because the things it rejects leave no trace.
`MIN_FILL` cost this library four usable assets per batch for as long as it
has existed, and nothing anywhere reported that.
