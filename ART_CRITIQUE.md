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

## Reopened: the seven-object speckle floor above was also only one lever tried

The entry above, and `check_speckle`'s own Finding message, said "there is no
render setting that fixes this: three were measured and none moved the
number" and concluded the fix was to reject the mesh or ask stage 1 for a
smoother subject. That is true of render settings and was never the whole
answer -- render settings are a generation-stage lever, and the defect
survives all the way to the rendered pixels regardless of which
generation-stage lever gets pulled. A post-process aimed at the pixels
themselves had never been tried: `render_batch.py`, `pixelize.py`, and
`art_review.py` had zero mentions of despeckling anywhere in their history.

This is the exact shape of the UI icon speckle case two entries up (see "The
UI icon roster grew to 20, one PR fixed one, and four still fail" and its
own reopening) -- two rounds of attempted fixes shared one lever (there,
the prompt; here, render settings) while the check itself measures a
downstream property (rendered pixel adjacency) neither lever touches
directly.

`pixelize.py` gained a `despeckle(px, target, min_agree=2, max_passes=5)`
function -- the same conservative two-rule design proven on UI icons,
generalized: only reassign a pixel that is isolated by the exact 4-neighbour
rule the check gates on, and only reassign it to a colour that at least 2 of
its up to 8 neighbours (4 orthogonal + 4 diagonal) already agree on. Wired
into `render_batch.render_sprite` -- the core rendering function shared by
every asset type in the factory, not just lifted props -- right after
`downsample_modal` and before the outline pass, so outline pixels (which are
deliberately different from their fill neighbours) are never mistaken for
speckle.

Measured against every cached `evening`-variant render already on disk (750
frames spanning props, tiles, UI, and characters) at the exact
`check_speckle` isolated-pixel ratio:

    fails before despeckle: 59 / 750 frames
    fails after despeckle:   0 / 750 frames
    regressions:              0 (no already-passing frame moved closer to
                                  the floor, let alone across it)

basket, the worst known offender, went from 12.7-16.3% across all 8 azimuths
to 0.0-0.2%. Fourteen objects had at least one failing frame in this cache --
more than the seven named above (also bicycle, bottle, cake_slice, fern, and
an unrelated stress-test render) -- and all fourteen clear the gate after the
pass, 0 frames failing across all of them. Spot-checked by eye, not just by
the numbers: a failing frame goes from illegible cross-ramp static to a
shape with a legible shaded/lit region split; an already-passing frame
(candle, french_press) is visually unchanged apart from a handful of stray
pixels -- nothing that was contributing to legible detail was touched.

Re-verified end to end, not just on the cache: re-rendered basket fresh from
its cached mesh (`out/mesh/basket.obj`) through the real, now-patched
`render_batch.py`, and `art_review.py` reports nothing to flag on all 8
frames. Re-rendered all 32 cached meshes fresh the same way (256 frames) --
255 clean, one narrow miss (`wooden_spoon`, one azimuth, 10.6% against a
10.5% floor, exactly one pixel over). That pixel has no 2-of-8-neighbour
colour majority -- a genuine point on the spoon handle's thin silhouette,
which is precisely the case the conservative reassignment rule is designed
to leave alone rather than paint over. Documented honestly rather than
declared closed: this is a real, narrow, unfixed residual, not evidence the
approach doesn't work.

**Not a full retraction.** The render-settings conclusion still holds --
three were measured and none moved the number, and that finding is
unchanged. What was wrong was stopping there. `check_speckle`'s own Finding
message is updated to match: a Finding today means a narrow miss survived a
pass that already closed the wide cases, not that the mesh needs rejecting
outright.

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
- ~~The **focal reading still falls with render resolution**...~~ **Resolved,
  not the way this bullet expected.** Re-measured (see "Focal detail:
  resolution-confirmed, not resolution-invariant"): contrast itself turned
  out to have healed as a side effect of later, unrelated composition fixes
  -- it no longer comes near its floor at any resolution from 160 to 480. The
  same falls-with-resolution problem had moved to detail (edge density,
  added after this bullet was written) instead, confirmed live: plan 1 failed
  at 320 and passed at 480 with no content change. A ratio reformulation was
  measured and proven unable to fix a verdict at a floor fixed at 0 (a
  sign-preserving transform). Fixed at the decision-rule level instead: a
  failure at 320 is now confirmed with one render at 480 before it is
  reported, and only counts if it fails both (`FOCAL_CONFIRM_TARGET`,
  `tools/build_plan.py`). This is resolution-*confirmed*, not
  resolution-*invariant* -- a defect visible only at some third resolution
  neither 320 nor 480 would still slip through, named honestly in that
  section rather than claimed away.
- ~~**Furniture screen spread** now has an owner for its *closest pair* (0.045,
  bracketed by measurement) but the mean-spread floor of 0.15 is still close to
  the original guess. It has never rejected anything the closest-pair floor did
  not also reject, which is either redundancy or a floor set too low to fire.~~
  **Resolved, not redundant.** Widening the survey from the 15 generators
  `check_generator_range` gates to all 24 seeded builders in `assetlib.py`
  found no case, on anything currently shipped, where the mean floor fires
  and the closest-pair floor does not. Degrading the real `bookshelf`
  generator on two independent axes did: silent at 15.4%, fires at 14.8%, a
  measured 0.6-point bracket either side of 0.15. See "The screen-spread
  floor's redundancy question, closed with a real generator instead of
  synthetic noise" below.
- ~~**The detail floor's bracket is 0.010 wide.**~~ Closed: see "The detail
  floor's bracket, closed: the noise is bigger than the signal" below. The
  0.010 never held even on the sample that produced it (two same-dressing
  rooms were already 0.028 apart), and at n=50 the per-dressing-state spread
  is 0.075-0.145 against a shelf's own ~0.02-0.03 mean effect -- a 3-6x
  signal-to-noise gap no threshold placement closes. Left at 0.0 and
  recorded as a population-rate check (roughly 1 in 8-9 wall/L runs), not a
  per-room verdict.
- **Added 2026-09-13: the galley topology fails composition (mean-L and/or
  detail) on 3 of 3 occurrences in a fresh 12-plan scan (100%, matching its
  own build commit's 100% at n=40)**, confirmed identical under both style
  packs. This is NOT new -- commit `71451c3` already measured and explicitly
  declined to fix it ("loosening MIN_FOCAL_L/MIN_FOCAL_DETAIL to admit it
  would be tuning the instrument to the answer"), it just never made it into
  this file's prose until "A real, already-measured galley finding was never
  folded out of its own commit message" below. Do not loosen either floor to
  admit galley; the mechanism (its focal box spans the full room depth, not
  a strip near one wall) is understood and accepted, not a bug.
- ~~**Added 2026-09-13: 4 of 20 `cat: ui` icons (`ui_coin`, `ui_icon_bagel`,
  `ui_icon_pastry`, `ui_icon_sandwich`) fail the speckle gate under BOTH
  styles.**~~ Closed 2026-09-15: not by a better prompt (two attempts, still
  correctly rejected), but by a downstream despeckle pass on the rendered
  pixels -- see "Reopened: the 'left open' call above was wrong about which
  lever was untried" below. `python tools/ui_forge.py` now builds 20/20 under
  both styles. One caveat carried forward, not closed: passing the gate is
  not the same as reading well -- `ui_coin`'s default-seed result still reads
  poorly despite passing clean; see that section's own last paragraph.

---

# The screen-spread floor's redundancy question, closed with a real generator instead of synthetic noise

The earlier close of this ("The mean spread floor: never fired is not the
same question as redundant", above) settled it with 2000 synthetic pixels
flipped at random -- a valid argument in principle, but not a shape anything
in this repo ships, and the "Still open" list kept restating the question
afterward anyway, floor number and all, because nothing tied the resolution
back to the bullet. This closes it with the shipped `bookshelf` generator
itself, degraded on purpose, and with the survey widened past the 15
generators `check_generator_range` actually gates.

## The full library, not just the 15 that are checked

`check_generator_range` iterates `art_review.GENERATORS`, 15 entries.
`assetlib.py` has 24 functions taking a `seed`; nine were never folded in --
`leafy_plant`, `succulent`, `fridge_under`, `tip_jar`, `book_stack`,
`pastry_plate`, `bean_sack`, `wall_art_framed`, `plant_hanging`. Running the
same measurement `check_generator_range` uses (mean and closest-pair screen
spread, 8 seeds) over all 24:

| generator | mean | closest | mean fires (0.15) | closest fires (0.045) |
|---|---|---|---|---|
| `fridge_under` | 0.0% | 0.0% | fires | fires |
| `tip_jar` | 0.0% | 0.0% | fires | fires |
| `bean_sack` | 6.9% | 1.0% | fires | fires |
| `pastry_plate` | 7.0% | 2.1% | fires | fires |
| `counter` | 7.5% | -- | (own floor 0.04, clears) | exempt, own floor |
| `wall_art_framed` | 36.5% | 0.0% | clears | **fires** |
| `bookshelf` | 18.4% | 15.9% | clears | clears |
| remaining 16 | 20.1%-91.2% | 5.2%-45.7% | clear | clear |

Two findings outside the question asked, worth recording rather than quietly
fixed: `fridge_under` and `tip_jar` both measure 0.0% on both floors because
neither builder's body calls its own `rnd()` -- the `seed` parameter is
accepted and never read. That is a real defect, and this floor gets no credit
for it, because neither generator was ever in the set it runs against. Left
for a follow-up in `NEXT.md` rather than fixed here -- wiring two generators'
randomness is a different task than the one this section answers.
`wall_art_framed` reproduces the expected *opposite* case from the original
"Still open" note above (`proof/spread_floor_ungated.png`): mean 36.5%, closest
0.0%, the closest-pair floor catching a defect the average washes out. On the
question actually asked -- restricted to everything currently gated or
gateable -- the mean floor still never fires alone on the shipped library.

## "Never fired on the library" still isn't "cannot fire"

Bracketing it the way the closest-pair floor was bracketed means building a
defect, not describing one abstractly. Two independent knobs on the real
`bookshelf` generator, both plausible regressions rather than synthetic
noise: shrinking the amplitude of its own `rnd()` calls toward their midpoint
(a variance leak), and truncating its spine palette (a material-variety
collapse). Both run through the shipped `_books` helper unmodified -- these
are real frames, not stand-ins. `proof/spread_floor_bracket.png`:

| variant | mean | closest | mean fires | closest fires |
|---|---|---|---|---|
| bookshelf, shipped | 18.4% | 15.9% | | |
| amplitude k=0.40 | 15.9% | 11.1% | | |
| amplitude k=0.35 | 15.4% | 10.6% | | |
| amplitude k=0.30 | 14.8% | 9.3% | **fires** | |
| amplitude k=0.20 | 11.2% | 5.8% | **fires** | |
| amplitude k=0.10 | 10.8% | 5.3% | **fires** | |
| 3 of 10 spine colours | 15.2% | 11.6% | | |
| 2 of 10 spine colours | 12.8% | 8.9% | **fires** | |
| 1 of 10 spine colours | 5.8% | 3.0% | **fires** | **fires** |

The floor sits exactly where the amplitude sweep crosses: k=0.35 (15.4%) is
silent, k=0.30 (14.8%) fires, and 0.15 sits in the **0.6-point gap** between
them -- tighter than the closest-pair floor's 2.3-point bracket, but real on
both sides, held to the same standard the detail floor's 0.010-wide bracket
was. The spine axis gives a second, independent bracket agreeing with the
first rather than merely not contradicting it: silent at 3 of 10 (15.2%),
fires at 2 of 10 (12.8%), 2.4 points wide.

At both crossings the closest-pair floor stays silent -- 9.3% and 8.9%, both
comfortably over 4.5% -- until the degradation is severe enough that both
floors agree (1 of 10 spines: mean 5.8%, closest 3.0%). That is four separate
constructed cases (k=0.30, k=0.20, k=0.10, 2-of-10 spines) where the mean
floor catches a regression the closest-pair floor's own arithmetic cannot
see by construction: closest pair only ever looks at the two most similar
frames, and a generator whose whole population has drifted toward the middle
can keep those two frames comfortably apart while every *other* pair has
collapsed with them. `proof/spread_floor_bracket.png` shows this by eye --
the shipped and k=0.40 rows carry cool colours (teal, sky-blue) the k=0.30
row has lost almost entirely, eight columns of the same warm rose-brown.

## Verdict: not redundant, floor unchanged

**Set too low to fire** would mean 0.15 is loose, missing real regressions on
the current library. It isn't: nothing in the shipped 24-generator library
sits between 0.045 and 0.15 doing something both floors should have caught,
and raising the floor would make it fire on `bookshelf`'s own shipped output
(18.4%) before anything is actually wrong -- the same mistake this file has
already made once tuning the *other* floor too tight, one level up.

**Redundant** would mean the mean floor never disagrees with the closest-pair
floor on anything real or realistic. It does, four separate times, on a
generator this repo ships, degraded two independent and plausible ways. A
redundant floor cannot do that by construction.

The floor stays at **0.15**. The reason it has never fired on the real
library is now demonstrated rather than assumed: not because it can't, but
because none of the 24 generators currently ship the "differs a little, none
differs much" failure it exists to catch.

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

~~**Not built this pass.**~~ **Built two passes later, and this section was
never updated to say so.** Commit `71451c3` ("Build the galley (double-run)
topology, auditing every plan.of("service")[0] site", 2026-09-04, already on
`main`) did exactly the audit this section called for: `light_rig()` now sums
lit pools per run and ranks dark corners by distance to the nearest one;
`build()`'s whole counter-fill section moved inside a `for run_idx, run in
enumerate(runs)` loop paired with its own back bar by list position; `_people()`
splits the customer/barista roster per run instead of duplicating it; the
hand-inlined duplicate of `focal_box()` (hard-coded to `service[0]`/
`backbar[0]`) was deleted in favour of calling the already multi-run-safe
`focal_box()` itself. Verified N==1 byte-identical against the pre-refactor
four-topology output before the new `galley` branch was ever added to
`floorplan.generate()`'s shared `rnd()` stream, so the audit itself changed
nothing observable until the fifth topology actually used it. If this section
is being read as a todo, it is not one -- check `git log -- tools/floorplan.py`
before trusting any "not built" claim in this file, this one was 12 days
stale even before this correction.

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

## The detail floor's bracket, closed: the noise is bigger than the signal

The "Still open" list above carried the bracket as **0.010 wide** -- three
measured defects at -0.005 to -0.009 against a weakest good room at +0.005,
on the 12-plan sample the wall-shelf/sign fix was measured against. Two
things have happened to that number since it was written, both already on
record separately (`leafy_plant` unified onto `_mix`; `NEXT.md`'s Gates
section) but never brought back to close this bullet out: the same 12 plans
now read plan 1 at -0.002 and plan 10 at -0.011, two rooms the original
bracket counted as "good," on unmodified shipped code. The bracket has
already been crossed by ordinary codebase churn, not by anyone touching the
counter's composition. That is worth stating plainly before re-measuring:
whatever number this section lands on next, it will not stay put either.

Widened to the same n=50 the original 12-plan sample never got (raw data:
`proof/detail_floor_scan50.txt`, same `build()`/`render()` calls
`check_focal_contrast`/`_focal_scan` make, target 320): 7 of 50 negative
(14%, plans 1, 10, 16, 18, 23, 24, 37) -- close to B4's 12.5% on 40 plans,
so the rate itself has held up. The bracket has not: weakest fail is plan
1 at -0.002, weakest pass is plan 6 (peninsula, +0.002) or plan 29 (wall
run, +0.004) -- a 0.002-0.004 gap, not 0.010, echoing B4's own 40-plan
finding (0.002-0.006) on a completely different generator state. Three
independent samples now (12, 40, 50), three different points in this
file's history, and the margin has never once come back wider than it went
in.

**The reason isn't the threshold -- it's the signal-to-noise ratio.** Group
the 50 by the back-wall dressing they actually received (`decor#wshelf`
count; peninsulas and islands never qualify for a shelf at all, `on_wall`
is false for them):

| dressing state | n | detail lead range | mean |
|---|---|---|---|
| wall/L run, 0 shelves, sign+2 menus | 5 | -0.014 to +0.061 | +0.0116 |
| wall/L run, 1 shelf, sign+2 menus | 21 | -0.017 to +0.128 | +0.0369 |

The causal signal reproduces cleanly at this scale -- a shelf still adds
about 0.02-0.03 to the mean, matching the original 60-seed correlation
(+0.0154 vs +0.0383) to within rounding. But the **spread inside a single
dressing state** is 0.075 for zero shelves and 0.145 for one -- three to six
times the signal a shelf is worth. Plan 10 (no shelf) fails at -0.011; plan
22, the identical dressing state -- sign, two menus, no shelf, same wall-run
topology -- passes at +0.061, a 0.072 gap between two rooms whose back wall
carries the literal same objects. Rendered both
(`proof/detail_floor_plan10_fail.png`, `proof/detail_floor_plan22_pass.png`)
at the shipped 480px target, not just the check's 320: plan 10 reads -0.013,
plan 22 reads +0.037, so the gap survives resolution too -- this is not
the 320-vs-480 instability PR #41 fixed, it is a second, independent source
of margin loss on top of it. Plan 16 sharpens the same point from the other
side: it HAS a shelf and still reads -0.017, worse than plan 10's shelf-less
-0.011 -- having the fix present is not sufficient either, in a population
this noisy.

**No threshold placement fixes a 3-6x signal-to-noise gap.** Verified rather
than asserted: raising the floor to clear plan 1's -0.002 (say, +0.010)
would newly reject plan 6, a peninsula at +0.002 with no wall behind its
counter to dress in the first place -- punishing a topology for a defect it
is structurally incapable of having. Lowering it to clear plan 16's -0.017
would stop catching plan 10 and plan 23 without recovering anything, since
both are already the genuine article the floor exists for (zero shelves,
negative at both resolutions). Every number between -0.017 and +0.061 either
lets a real shelf-less room through or fails a room that was never eligible
for a shelf at all, because both populations already overlap at every point
in that range.

**Left at 0.0.** Not because 0.010 was ever real margin -- it wasn't, even
on the sample that produced it, as plan 4 and plan 10 show: both zero
shelves, both measured on the very same commit the 0.010 bracket cites,
already 0.028 apart (+0.033 vs +0.005) before any RNG churn touched either
one. The floor was never resting on a 0.010 cushion; it was resting on a
12-room sample too small to show that the cushion was already thinner than
the noise. What changes here is the claim, not the constant: this check
answers a population question (roughly one wall/L run in eight to nine
reads under-detailed, consistently across three sample sizes and two
generator states) and does not answer a per-room one. A single room failing
within a few thousandths of 0.0 is not evidence of a defect in that room
specifically -- plan 22 sitting 0.072 away from plan 10's identical dressing
proves the metric cannot tell them apart at that resolution. Treat a
near-boundary `check_focal_contrast` detail failure the way this file
already treats a near-boundary contrast reading: as the weaker, honest
question, not the stronger one the number's precision implies.

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

**Re-checked 2026-09-17, could not be reproduced.** Auditing this file's
other "accepted limitation" claims for the same untried-lever pattern that
closed the two speckle floors (PR #80, #81), this one looked like a natural
next candidate for `--reference` (the multi-image IP-Adapter conditioning
that shipped later in this same section, never actually tested against a
still-failing collage case). Before spending GPU time on that, tried to
reproduce today's baseline first -- and couldn't. `"a woven wicker basket"`
at seeds 1 through 10 (seed 4 fails on an unrelated frame-fill/crowding
finding, not collage) all pass `check_concept_fitness` cleanly: soft-alpha
ratio 2.3-7.7% against the same 10% cap, two orders of magnitude under the
54584% recorded above, and visually confirmed by eye across all nine --
every one a single, clean, isolated basket, zero tiling. `NEGATIVE` is
byte-identical to what it was when this entry was written (still exactly
"... + collage, grid, tiled", per its own comment in `concept.py`), so this
is not a prompt change closing the gap. Left unexplained rather than
guessed at: the most likely cause is drift in a downloaded model weight
(SDXL checkpoint, matte model, or both) between whenever this entry's run
happened and today, which this repo's own code has no way to pin down after
the fact. Recorded as the honest current state -- passing, today, on this
machine, for this prompt -- not as a fix, since nothing in this repo
changed to cause it. `--reference` remains genuinely untested against a
live collage failure; there wasn't one to test it against this pass.

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

## Re-checked after the despeckle fix: the gate clears, the knight still doesn't look like one

Both remedies tried above (coarser marching cubes, a simplified prompt) were
generation-stage levers, same category as the 3D lifted-object speckle
case's "three render settings, none moved the number" (see "Reopened: the
seven-object speckle floor above was also only one lever tried") -- worth
checking whether this ceiling was the same mistake a third time, now that
`render_batch.render_sprite` runs every sprite through `pixelize.despeckle`.

It is not, and the distinction is worth recording precisely. Re-rendered the
frog knight fresh from its cached mesh (`out/mesh/the_frog_knight_from_
chrono_trigger.obj`) through the now-patched pipeline: `art_review.py`
reports **nothing to flag on all 8 frames** -- the 11-12% speckle blocker and
the 17-25% cross-ramp adjacency warning both clear, the latter apparently as
a side effect of the same fix (adjacent-but-different-ramp noise was
speckle's cross-ramp case, and cleaning the noise cleaned both checks at
once).

Looked at the actual sprites (`out/knight_grid.png`, all 8 azimuths, 8x
upscaled) before calling anything closed. They do not read as a knight.
They read as a hunched, monochrome frog-creature -- single skin-ramp
throughout, no cape, no armour, no rapier as a separate legible object (a
thin same-coloured line in two frames is the closest thing to a weapon
silhouette). This is exactly what the original entry predicted a passing
gate would not fix: **the mesh itself has no cape, no separable limbs, no
rapier** -- geometry that was never reconstructed, not colour noise sitting
on top of geometry that was. A pixel-level despeckle pass cannot invent
missing topology; it can only clean the colour of topology that exists.

**The honest conclusion is two findings, not one retraction:**
- The character ceiling itself -- TripoSR cannot reconstruct articulated,
  accessorized subjects at this fidelity -- is unchanged and still correctly
  scoped as "needs a better reconstructor" (TRELLIS 2, still blocked on this
  workstation's toolchain). Nothing in this pass argues otherwise.
- But the *checks* that were standing in as an imperfect proxy for "does
  this look like the intended subject" are now a measurably weaker proxy
  than before: a mesh this visibly wrong now sails through `art_review.py`
  with zero findings. That was already possible in principle (the checks
  never claimed to verify subject identity), but this is the first measured
  case of it actually happening, and it means a human look at character-kind
  output stays necessary even after the pipeline reports clean -- the gate
  passing is no longer even weak evidence that a character-kind asset reads
  as its subject.

## A second re-check, opposite result: `bread_loaf`'s "genuinely bad" 5/8 was speckle after all

The frog knight (previous section) was a warning not to assume the despeckle
fix generalizes. `bread_loaf` is the other side of the same check:
`concept.py`'s `MIN_FILL` rationale and `factory.py`'s `RETRY_SEEDS` comment
both cite it as the sharpest counter-example to "reseeding helps" -- "gated
on seed 1, passed on seed 2, reached stage 5 -- and its sprites are still
5-of-8 blocked, identical to before," attributed to the mesh itself: "a loaf
is an amorphous form TripoSR cannot resolve, not because it was small." That
5/8 number predates `pixelize.despeckle` (this same branch).

**Correction, same day, before this section's first draft had even been
committed:** the paragraph here originally claimed `bread_loaf` "fell
outside" the 32-mesh batch the speckle fix's own coverage check re-rendered
two sections up ("Reopened: the seven-object speckle floor... 255 clean, one
narrow miss (`wooden_spoon`)") and so had never actually been re-checked
against the new lever. That claim was never verified before being written,
and it does not hold up: `out/mesh/bread_loaf.obj` is one of exactly 32
cached mesh files on disk, all dated 2026-08-23 through 2026-08-26 --- days
before the despeckle commit (`6ce3604`, 2026-09-16) that says "all 32 cached
meshes re-rendered fresh (256 frames), 255 clean, one honest narrow miss
(`wooden_spoon`)." Arithmetic alone rules out `bread_loaf` sitting outside
that count and still failing: one miss total, across all 256 frames, means
every other mesh in the batch -- `bread_loaf` included -- already came back
clean at that commit. The fix's own coverage check had already covered this
case in aggregate; nobody had just written it down by name. This is the
exact stale-unverified-claim mistake this file's "29%" entry describes
catching once already, repeated in miniature by the paragraph that was
citing that entry as precedent -- corrected here rather than quietly amended,
per this file's own practice.

What survives the correction: the concrete re-render below is still real,
independent confirmation for this specific named subject (the original
32-mesh result was an aggregate count, never broken out per-mesh in any
doc), and the `concept.py`/`factory.py` comments it corrects were still
citing a stale number regardless of whether that number had technically
already been superseded upstream. What does not survive: any claim that this
was newly-discovered coverage, or that the fix needed anything further to
reach `bread_loaf`.

Re-ran it directly. `main` (pre-despeckle), fresh render from the cached mesh
(`out/mesh/bread_loaf_bound.obj`): `art_review.py` reports 5 of 8 frames
blocked on `speckle`, 11.4-13.5% against the 10.5% floor -- reproduces the
recorded number exactly. Same mesh, same render, this branch (post-despeckle):
**0 of 8 blocked.** Confirmed by eye, not just the count -- upscaled
before/after contact sheet (`out/bread_loaf_before_after.png`, all 8
azimuths, 6x): the crust's mottled light/dark pattern and the sliced-loaf
silhouette read identically in both rows; nothing that made it legible as
bread got smoothed away, matching the "stray pixels only" pattern already
confirmed for `candle`/`french_press` in the original despeckle measurement.

So the mechanism `factory.py`'s own comment names for `bread_loaf` --
"amorphous form TripoSR cannot resolve" -- was the wrong explanation for the
specific 5/8 number, even though it may still be true of the mesh's
geometry in some other respect this pass did not measure. What was actually
failing those 5 frames was the identical fine-grained-surface speckle named
for basket's weave and cutting_board's wood grain two sections up, on a
grainy crust instead of a woven basket -- the same cause, the same fix. Per
the correction above, that fix had already reached this subject at the
original despeckle commit; this pass names it and shows it, rather than
being the thing that closes it.

**What this does and does not change:**
- `bread_loaf`'s stage-1 gate story is untouched -- reseeding still does not
  fix it, for the reason already given (reseeding hunts a concept image that
  satisfies stage-1 heuristics; despeckle operates three stages later, on
  rendered pixels, and neither lever touches what the other measures).
  `factory.py`'s `RETRY_SEEDS` conclusion stands.
- The specific claim that `bread_loaf` is a *counter-example* to reseeding
  because its reconstruction is "genuinely bad" does not stand as stated --
  the sprites that made it look bad are now clean. Whether the underlying
  mesh geometry is *also* fine or also flawed in some way despeckle can't
  touch is a question this pass did not answer either way, and is left
  explicitly open rather than guessed at.
- `concept.py`'s `MIN_FILL` argument (fill share does not predict blocked-
  frame count) does not depend on this specific number -- but the two
  examples it leads with, `basket` 8/8 and `cutting_board` 7/8, are the same
  pre-despeckle blocked-frame counts as `bread_loaf`'s, both already
  independently confirmed clean by the original despeckle pass. The
  qualitative point (fill is not predictive) is not contradicted by fixing a
  downstream artifact that was orthogonal to fill either way, but the exact
  numbers quoted next to `basket`/`cutting_board`/`bread_loaf` in that
  comment are now stale and worth a maintenance pass, not re-derived here --
  re-deriving the full twenty/thirty-two-subject sweep behind that argument
  is a larger undertaking than one hour's check, and doing it partially
  would risk the exact stale-transcription mistake the "29%" entry above
  already caught and corrected once.

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

**Measured at full scale afterwards rather than left as a projection: the
batch now runs 29 of 31 clean, against 22 of 31 before.** The estimate above
said "somewhere around 28/31", which is close enough to be worth noting and
not close enough to have been worth trusting -- the point of running it was
that the difference between 28 and 29 is two real assets. `bottle`,
`wine_glass`, `cake_slice`, `wooden_spoon`, `book`, `fern` and `bicycle` all
came through.

The two survivors are worth separating. `bread_loaf` is correctly gated and
was independently confirmed bad (5 of 8 frames blocked when forced through).
`croissant` is gated on soft alpha and a second mass at 95% of the main one
-- genuinely two croissants in frame -- and yet the forced run above produced
eight clean, recognisable crescents from a croissant concept. So it may be a
second false rejection, on a different check, and the honest position is that
one clean run is not enough to indict `MAX_SECOND_BLOB` the way twenty
subjects indicted `MIN_FILL`. Recorded as a lead, not a finding.

One thing the batch did **not** test, and the report says so explicitly:
`seed_used` is absent on every row, because retries only fire for a concept
generated in that run and all 31 concepts already existed on disk. The
29/31 is entirely the threshold correction. Auto-reseed contributed nothing
to it.

### Forcing the last two, and what reseeding actually bought

Re-running the two survivors with `--force` finally exercised the retry path
in anger, and the report shows it working exactly as designed:
`bread_loaf` gated on seed 1, retried, `seed_used: 2`, "gate passed on seed
2 after 1 reseed(s)". `croissant` passed at seed 1. Both reached stage 5,
taking the library to 32 assets.

Then the obvious question, which is the one this whole session has been
about: did passing the gate mean the sprites are any good?

    croissant     0/8 blocked      genuinely recovered
    bread_loaf    5/8 blocked      exactly as bad as before

`bread_loaf` is the finding. Reseeding pushed it through the stage-1 gate
and produced **nothing usable** -- the identical 5-of-8 failure measured
back when it was forced through manually. A loaf is an amorphous form with
no stable silhouette; no seed fixes that. What enough seeds *will* eventually
do is find a concept that happens to satisfy stage 1's heuristics while
still reconstructing badly, because stage 1 is a proxy for reconstruction
quality and a proxy can be satisfied without the thing it proxies for
improving at all.

So auto-reseed carries a hazard worth naming plainly: **it optimises against
the gate, and the gate is not the goal.** Retry hard enough and it becomes a
mild form of tuning to the metric -- the same failure this file caught the
focal-contrast check committing, in a different costume. `RETRY_SEEDS = 2`
is modest enough that it cannot grind far, and it was chosen from measurement
rather than to be safe, which is luck rather than judgement. The safeguard
that actually matters is downstream: `art_review` reads the sprites
themselves and blocked `bread_loaf` both times, correctly, without caring
what stage 1 thought. That is the check to trust, and the reason `MIN_FILL`
could be relaxed so far without danger.

The honest scoreboard, then, is not "31/31". It is 30 subjects with usable
sprites, one (`bread_loaf`) with sprites that exist and are bad, and a gate
that no longer says so. Whether stage 1 should be able to reject an
amorphous subject on principle -- rather than being talked round by a
retry -- is a real open question, and a better one than any number here.

## Answering that question: a real signal that still should not be a gate

The library now carries its own ground truth. Thirty-two subjects have
sprites, and `art_review` scores each set 0-8 blocked frames, so "does this
concept reconstruct well" is a label rather than an opinion. That makes the
question testable in the way `MIN_FILL` never was before it shipped: does
anything measurable *in the concept image* predict the blocked count?

Three candidates, correlated against blocked frames across all 32:

    silhouette compactness (perimeter / sqrt area)   +0.256
    internal lightness spread (p90 - p10)            +0.077
    internal lightness gradient (mean |dL| per px)   +0.658

The first two are nothing. The third is a strong signal and it makes
physical sense: mean adjacent-pixel lightness difference is a texture
reading, and texture is precisely what a single-view reconstructor turns
into noisy geometry. The ranking passes the eye test too -- `basket` 0.0396,
`bread_loaf` 0.0340, the frog knight 0.0270 at the top; `teapot` 0.0042,
`teacup_stack` 0.0048, `umbrella` 0.0071 at the bottom.

(That number is also a lesson in checking the instrument. The first pass
measured this at +0.011 and would have been filed as a third null result --
because the subsample took every seventh pixel, so the "adjacent" pair it
differenced almost never actually was adjacent, and most subjects scored a
flat 0.0000. A metric returning suspicious zeros is a broken metric, not a
finding. Sampling whole rows instead moved it from +0.011 to +0.658.)

And it still should not become a stage-1 blocker, because the distributions
overlap badly:

    bad  (>=3 blocked, n=10)   0.0075 .. 0.0396
    good (0 blocked,   n=18)   0.0030 .. 0.0263

    cut 0.018   catches 7/10 bad, wrongly rejects 2/18 good
    cut 0.025   catches 5/10 bad, wrongly rejects 1/18 good
    cut 0.028   catches 3/10 bad, wrongly rejects 0/18 good

There is no cut that separates them. Every setting that catches most of the
failures also throws away good work, which is `MIN_FILL`'s exact sin in a
more sophisticated costume -- and it would be easy to ship, because +0.658
sounds like enough. It is not. A correlation strong enough to be interesting
is not the same as a boundary sharp enough to gate on, and the difference is
whether the two populations actually separate.

So the answer to the open question is **no, on the evidence available**:
stage 1 cannot reliably reject an amorphous subject, and the best predictor
found so far is a good warning and a bad gate. That is not a failure of the
search. It is the reason the architecture already works -- `art_review`
reads the finished sprites, needs no proxy, and blocked `bread_loaf` twice
without being asked. Any future attempt at this should have to clear the
overlap table above rather than a correlation coefficient.

## Icons split by whether they depict a thing, and reseeding earns its keep

Running the remaining twelve `cat: ui` entries gave 9 of 12 past the speckle
check, and this time **auto-reseed did real work**: `ui_clock_day` needed
seed 3, `ui_heart_mood`, `ui_icon_cappuccino` and `ui_icon_latte` needed seed
2. That is the honest counterweight to `bread_loaf` above. Speckle genuinely
is seed-dependent -- a different draw gives flatter shapes with fewer stray
pixels -- whereas an amorphous loaf is the same loaf at every seed. Reseeding
works exactly where the failure is noise and fails exactly where it is
structure, which is what it was measured to do.

Looking at the twelve rendered icons rather than their scores splits them
cleanly, and not along the axis the checks measure:

    depicts an object   clock_day, heart_mood, cappuccino, cold_brew,
                        espresso, latte, tea            -- 7, all usable
    UI chrome           dialogue_frame, ticket, nameplate, upgrade_frame,
                        star_rating, coin               -- 5 wrong, 1 gated

Every drink and object icon works. Every piece of abstract UI *chrome*
fails, and fails the same way: asked for a speech bubble, SDXL renders a
photographed tablet with a picture in it; asked for a nameplate banner, a
framed panel; asked for a torn paper ticket, a framed picture again. The
star is an eight-pointed burst instead of a five-pointed star. None of these
are speckle failures -- `dialogue_frame`, `ticket` and `upgrade_frame` all
passed the isolated-pixel check comfortably. They are *wrong-shape*
failures, which no metric in this repo can see and none should be invented
to see, because "is this the thing I asked for" is the human tier.

The pattern is the prop/character split again in a third costume: **this
pipeline makes things, not abstractions.** A cup is a thing and SDXL has
seen a million of them. A dialogue frame is geometry with a semantic role --
nine-slice borders, defined corners, a fill region -- and a diffusion model
has no reason to produce it as flat vector chrome rather than as a
photograph of something frame-shaped. That is not a prompt to tune; it is
the wrong tool. UI chrome belongs in `assetlib` alongside the furniture,
authored procedurally, where a rounded rect with a two-pixel border is four
lines of code and exactly right every time.

So the honest count for the category is **7 usable of 14 declared**, not
9 of 12 -- and the correct next move is not more seeds but moving the six
chrome entries out of `ui_forge`'s prompt table and into procedural code.

## The clearest proof yet that the stage-1 gate is a proxy

`ui_icon_pastry` was the last unbuilt entry in the UI category, so it got a
run with `--retry-seeds 6` instead of the default 2. It passed on seed 4.
The result is a pale cream blob with black scribbles through it, cropped at
the frame edge, with no croissant shape anywhere in it -- and it is the best
demonstration this repo has of what reseeding against a gate actually buys.

The seeds, in order:

    seed 1   0.2% frame coverage   -- the subject was matted away entirely
    seed 2   11.4% isolated
    seed 3   18.1% isolated
    seed 4   PASSED

Seeds 2 and 3 are *recognisable croissants*. Seed 4, the one that passed, is
not a croissant at all. The gate did not find a better image; it found an
image whose defects happen not to be the two defects it measures. This is
the `bread_loaf` hazard `factory.RETRY_SEEDS` warns about, and it is much
sharper here, because with `bread_loaf` the gate at least passed something
that still looked like bread. **The icon was deleted rather than shipped**,
and the category count stays at 14 of 15.

Seed 1's failure was the interesting one, though, because it names a
mechanism rather than a symptom. A golden croissant on `UI_STYLE`'s "plain
white background" gives `matte()` almost nothing to cut against, and 99.8%
of the frame went. So: does a pale subject want a different background
clause? Measured, same subject, same three seeds, only that clause changed:

    background    seed 1              seed 2              seed 3
    white         0.2% cover          23.4% cover         23.3% cover
    grey          39.2% cover         19.6% cover         23.7% cover

Which looks like a win and is not. Opening the six icons shows what the
numbers cannot: the grey background does not get matted *out*, it gets
matted *in*. Grey seed 1's 39.2% "coverage" is a slab of background sitting
behind a small croissant, and it is the worst of the six. The white
background is doing its job; the failure at seed 1 was that a pale subject
on white is a hard separation, not that the clause is wrong.

The remaining defect is the subject itself. Every usable draw here is a
croissant covered in fine dark flecks -- laminated pastry is high-frequency
light-and-dark detail by nature, and high-frequency detail is exactly what
quantizes to isolated pixels. That puts `ui_icon_pastry` in the same class
as `bread_loaf` and the frog knight: not a seed problem, not a prompt
problem, a subject whose surface fights the target resolution. Recorded as a
ceiling, not as a task.

Two things follow that are worth doing rather than noting. The gate stays
exactly as it is -- 11.4% really is speckled, and the cap is not what went
wrong here. And `--retry-seeds` keeps its default of 2, because the whole
lesson of this run is that the number is not free: every extra seed is
another chance to satisfy the proxy without satisfying the eye.

## Drawing the chrome, and three things only looking caught

That move is now made: `tools/ui_chrome.py` draws the six failing pieces
plus an empty star, as a grid of material tokens resolved through the same
palette ramps and the same `apply_outline` the sprites use. All seven clear
`ui_forge`'s own gate rather than a softer one, at 32, 64 and 128 px --
worst isolated-pixel ratio 6.1% / 3.6% / 1.6% against the 6.2% cap.

The interesting part is not that they pass. Procedural output passing a
speckle check is close to tautological, since nothing procedural speckles.
It is that **three separate defects showed up here, and not one of them was
visible to any check in this repo until something was built to look.**

*One.* The nine-slice insets were wrong on the first run, and
`check_nine_slice` caught it: the bubble's bottom inset was set from where
the body ends rather than from where the rounded corner ends, so four rows
of corner sat inside the vertical stretch band and would have smeared every
time a dialogue box grew taller. This is the one case where a check did the
work -- and only because the check was written to verify the specific claim
the metadata makes ("these bands tile"), rather than to score the image.
That is the difference between a check and a metric, and it is worth being
precise about: `MIN_FILL` was a metric standing in for a claim nobody had
stated. `check_nine_slice` is a claim, checked.

It also moved once, for a reason: it originally read the material Canvas and
now reads the resolved pixels. `apply_outline` runs between the two and can
turn a uniform band non-uniform at its edges, so checking the materials was
checking the easier of two available things.

*Two.* The star's edge is now floored at 2 px instead of scaling freely,
because at `--target 32` a proportional 1.1 px edge is a one-pixel *diagonal*
run, and a one-pixel diagonal has no four-neighbour of its own colour
anywhere along it: 7.8% isolated, 13.3% for the empty variant. Two readings
were available. The cap is calibrated on generated icons, where isolated
pixels genuinely are speckle, so it is arguably over-strict on a deliberate
thin diagonal -- and raising it would have let the art through. That is
tuning the check to fit the art, the mistake this file already records twice
in one session. The art moved instead, and thickening an edge at 32 px is
what a pixel artist does anyway.

*Three*, and the one with no check behind it at all. The coin's first
highlight was a small crescent near the centre, and at 64 px it read as a
crescent moon sitting on a yellow circle. It measured 1.1% isolated -- one of
the cleanest numbers in the set -- and it was wrong. A specular has to hug
the edge it is reflecting off; anything drawn inland is a shape, not a
highlight. Nothing found that except opening the PNG.

Which is the same lesson as the generated frames, arriving from the opposite
direction. Generation produced things that scored well and were the wrong
shape; drawing produced a thing that scored well and was the wrong shape. The
metrics are not failing at their jobs -- speckle and coverage are real and
they catch real defects. They simply have nothing to say about whether the
picture is of the right thing, and no amount of adding metrics will change
that, which is exactly why `review_queue.py` exists and why the honest
category count is the one an eye produced, not the one the report did.

## UI art, and the same wrong-check mistake made twice in one session

`assets.yaml` declares fourteen `cat: ui` entries and none of them had ever
been rendered -- the largest declared-but-unbuilt category in the manifest.
The reason is structural: the pipeline is concept → mesh → 8 azimuths, and
an icon has no mesh and one azimuth. Sending an icon through `lift.py` would
ask TripoSR to invent depth for something deliberately flat, which is the
character-ceiling mistake pointed the other way.

`tools/ui_forge.py` takes the short path -- generate, matte, snap, downsample,
outline -- reusing `concept.concept()`'s `positive_override` (the same custom
escape hatch the Gradio UI exposes) and `pixelize`'s existing functions, so
no new generation or quantization code exists. Stages 2-5 are skipped because
they have nothing to contribute, which is a different statement from skipping
them because they are slow.

Two things went wrong, and both are worth keeping because they are the same
mistake in different clothes.

**The check could not fail.** The first `check_icon` tested coverage and
palette-exactness. Palette-exactness is guaranteed by construction -- the
snap only ever picks palette colours -- and coverage is nearly always fine,
so the check passed all three of the first icons generated. Pointing
`art_review` at the same three files blocked every one of them on isolated
pixels: 13.4%, 19.1%, 33.5% against its 6.2% authored-art floor, and the eye
agreed with the instrument. That is `MIN_FILL` again, one file over and
within the same session -- a threshold that cannot reject the failure it
exists to catch. The speckle reading is now the check, and deliberately at
`art_review`'s own number rather than a softer one invented to let this tool
pass: an icon and a sprite are the same kind of object once they are
palette-quantized pixels.

**The quantization order was backwards.** `downsample_mean_then_snap` averages
a block and then snaps the average, which salt-and-peppers anything with fine
detail: adjacent blocks average to slightly different RGB and land on
different ramp steps. `downsample_modal` cannot do that -- its docstring says
"invents nothing", it only ever picks a colour already dominant in the block
-- but it assumes palette-exact input, which the 3D path gets free from
`shade_toon` and the 2D path did not have. Snapping every pixel first and
then taking the mode puts the flat path in the condition the modal
downsampler was written for:

        mean-then-snap   snap-then-modal
        18.8%            15.5%    ui_coin
        13.2%             1.5%    ui_icon_espresso
        39.1%             5.8%    ui_star_rating

Two of three cross from blocked to comfortably under the floor, and the fix
is one line of ordering plus reusing the function that already existed
rather than writing a de-speckler.

Where that leaves it, stated plainly rather than as three-for-three:
`ui_icon_espresso` is genuinely production-clean -- flat shapes, cup, handle
and saucer all reading at 64px. `ui_coin` is still gated at 14.7%, correctly,
because the generated coin is an ornate relief medallion and no quantizer
rescues that; it needs a reseed or a plainer prompt. `ui_star_rating` passes
the speckle check at 5.8% and is still **wrong** -- an eight-pointed
starburst where the prompt asked for a five-pointed star. No metric here can
see that, and none should be invented to: "is it the shape I asked for" is
the human tier this repo has always said is the whole point. One clean, one
correctly rejected, one that needs a person to look at it is an honest first
result for a category that had nothing in it an hour ago.

## `fridge_under` and `tip_jar`: a seed parameter that did nothing, and nine generators put through the same measurement

PR #40's screen-spread audit found this in passing while bracketing
`DEFAULT_SPREAD_FLOOR`: `assetlib.fridge_under(seed)` and `assetlib.tip_jar
(seed)` both take a `seed` argument and never read it in the body -- no
`_mix(seed)` call, no `rnd()` closure, every seed rendering the byte-identical
mesh (measured 0.0% mean spread, 0.0% closest pair, both ways of asking the
same question). The same audit found `check_generator_range`'s `GENERATORS`
list covers 15 of `assetlib.py`'s 24 seeded builders (functions taking
`seed: int | None = None`, one exception -- `leafy_plant` and `plant_hanging`
default to a concrete int rather than `None`, and are seeded builders anyway),
nine ungated: `leafy_plant`, `succulent`, `book_stack`, `pastry_plate`,
`bean_sack`, `wall_art_framed`, `plant_hanging`, `fridge_under`, `tip_jar`.
Both findings were flagged and deliberately not fixed on that branch. This
entry is that fix.

**The fix itself is the pattern every other seeded generator in the file
already uses.** `book_stack`, `bean_sack` and `pastry_plate` sit a few
hundred lines away from both broken functions using exactly the
`st = None if seed is None else _mix(seed)` / `rnd()` closure pattern that
was missing -- this wasn't a design question, it was two functions that
skipped a step every neighbour took.

`fridge_under` varies handle height (0.66-0.76) and length (0.09-0.14), plus
plinth height (0.03-0.05) -- the same scale of change `counter`'s own front
treatments get, deliberately, because a closed appliance's silhouette is
fixed by design and only the value detail on its face is supposed to move.
`tip_jar` varies coin-fill height (0.05-0.19, the dominant term -- a jar an
hour into a shift and one at closing are the same object at different fill),
jar radius (+/-1.5%) and label-band height (0.13-0.18), all bounded so the
label never clears the glass rim.

**Measuring whether to widen `GENERATORS`, not assuming it.** Each of the
nine ungated builders was rendered across six independent 8-seed windows
(seeds 1-8, 9-16, 17-24, 51-58, 101-108, 201-208) and run through
`check_generator_range`'s own `screen_materials` / `_screen_spread` /
`_pair_disagreement` math, at a per-generator `span` sized from each mesh's
actual projected extent at azimuth 45 (the same way the existing 15 entries'
spans were evidently sized -- projected width/height times a ~1.0-1.15
margin matched against `chair`, `crate`, `armchair`, `stool`, `bookshelf`'s
own span/extent ratios):

    generator          mean spread (range across 6 windows)   closest pair
    leafy_plant        46.9% - 53.1%                           30.0% - 37.4%
    succulent          29.9% - 34.3%                           14.0% - 22.2%
    book_stack         86.1% - 94.3%                           44.9% - 53.3%
    plant_hanging      57.0% - 67.1%                           35.3% - 47.9%
    wall_art_framed    26.8% - 37.9%                            0.0% (every window)
    tip_jar             8.7% - 12.8% (pre-fix: 0.0%)             0.3% - 3.6%
    pastry_plate        5.7% -  9.0% (pre-fix: 0.0%)             0.4% - 2.6%
    bean_sack           4.4% -  8.1%                             0.0% - 0.7%
    fridge_under         1.0% -  1.6% (pre-fix: 0.0%)            0.0% - 0.5%

Four (`leafy_plant`, `succulent`, `book_stack`, `plant_hanging`) clear both
`DEFAULT_SPREAD_FLOOR` (0.15) and `CLOSEST_PAIR_FLOOR` (0.045) with wide,
stable margin across every window -- added with no `own` override, same as
the 15 already there.

The other five are real but genuinely subtle by design, the exact shape that
let `fridge_under`/`tip_jar`'s total-silence bug go unnoticed. Rather than
leave them out on that basis alone, each got an `own` floor bracketed between
0.0% (the measured value of the actual pre-fix bug -- what "seed silently
ignored" looks like on this instrument) and its own weakest mean across the
six windows, set at roughly half the weakest value:

- `pastry_plate` (own 0.03): only pastry radius varies, +/-3% of a
  0.10-0.13 range -- the module's own docstring says laminated detail
  quantizes to speckle, so value steps carry the object, not shape change.
- `bean_sack` (own 0.02): only base radius varies, +/-4% of a 0.30-0.34
  range -- a sack's slump is supposed to read as the same sack every time.
- `fridge_under` (own 0.005): the fix above, on a fixed-silhouette closed
  box -- a few pixels of handle and plinth move against a large flat face.
- `tip_jar` (own 0.05): the fix above; `own` is also load-bearing here for
  a second reason -- two of the six windows drew a closest pair under 1%,
  well under `CLOSEST_PAIR_FLOOR`, by chance rather than by defect, so the
  pair check needs to be off, not just the mean bar loosened.

`wall_art_framed` is a different case from the other four: its mean (26.8%
-37.9%) comfortably clears the *default* floor unassisted. Its closest pair
is 0.0% in **every** one of the six windows, and that is structural, not
incidental -- the picture's hue is one of four categorical choices (`sky-1`,
`foliage-1`, `rose-1`, `wood+1`), so eight draws from four buckets collide by
the pigeonhole principle almost every time. `own` is set to the *unchanged*
default mean floor (0.15) purely to invoke the "an `own` override skips the
pair check" mechanism `counter` already established ("counter's modules are
meant to tile flush and two identical ones are the point") -- here, two
identical hues are the expected outcome of a 4-way enum, not a defect, and
gating on the pair floor here would fire on every healthy run.

**Verified failable both ways**, the discipline this repo asks for on every
new gate: simulated the exact pre-fix bug on all five `own`-gated generators
(calling each with a fixed `seed=1` regardless of the loop index, which is
what "seed silently ignored" looks like from the outside) -- all five
measured 0.0% mean and were correctly caught by their new floor. All nine
also pass clean on the actual shipped, fixed code: `check_generator_range()`
returns zero findings.

`proof/generators.png` (regenerated by `tools/preview_generators.py`, which
reads its rows straight from `GENERATORS`) carries all 24 seeded builders
now instead of 15+1 -- looked at directly rather than trusted from the
numbers: `fridge_under`'s row genuinely does look like eight nearly-identical
fridges at a glance, which is correct for a closed appliance and is exactly
why it needed the tightest floor of the nine rather than exclusion; `tip_jar`
visibly varies coin-fill level across its row; `wall_art_framed` visibly
cycles through distinct hues; the four unconditional adds show clearly
different silhouettes seed to seed.

**Verified no regression.** `tools/manifest.py --check` and
`tools/build_plan.py --focal-scan 12`, run against `origin/main` via `git
stash` and again with this diff applied: byte-identical outcomes both ways
-- `manifest.py --check` 1 error / 8 warnings (the known plan-1 wall-run
`-0.002` case), `build_plan.py --focal-scan 12` 2 of 12 fail (plan 1
`-0.002`, plan 10 `-0.011`) -- both pre-existing on `origin/main`, matching
PR #40's own re-measurement of that baseline (not `NEXT.md`'s stale "1 of
12"), neither introduced here. `check_generator_range`'s nine new entries
add zero new warnings either way, because they all pass.

---

## Focal detail: resolution-confirmed, not resolution-invariant

The "Still open" list has carried one line unchanged since the sixth pass:
contrast is a percentile spread, it falls with render resolution in generated
rooms, the scan and the suite check grade at 320 while the shipped render is
480, and the gap is "stated rather than tuned away." Re-measuring it end to
end, on current code, found the original claim had quietly stopped being
true and a different one had taken its place under the same name.

### Contrast healed; nobody re-checked it

Re-swept the sixth pass's own 160/320/480 table on today's code, across the
suite check's own four-room sample (`check_focal_contrast(n=4, seed=1)`
picks plans 1/2/3/8 -- one wall run, one peninsula, one island, one L run)
plus the reference room:

| room | 160 | 240 | 320 | 400 | 480 |
|---|---|---|---|---|---|
| reference | +0.178 | +0.133 | +0.133 | +0.133 | +0.133 |
| plan 1, wall run | +0.146 | +0.101 | +0.101 | +0.101 | +0.101 |
| plan 2, peninsula | +0.101 | +0.101 | +0.101 | +0.101 | +0.087 |
| plan 3, island | +0.146 | +0.146 | +0.146 | +0.126 | +0.101 |
| plan 8, L run | +0.138 | +0.146 | +0.101 | +0.101 | +0.101 |

Every reading stays at least 0.047 clear of the 0.030 floor -- most 3-6x
clear -- across the whole range. The sixth pass's steep collapse (seed 3:
+0.084 at 160 down to +0.014 at 480, nearly touching the floor) is gone.
Nothing in this pass targeted contrast: the hull-clipped focal region, the
wall shelf/sign dressing and the back-counter height/lamp retune (all landed
since, for unrelated reasons) each changed how much of the frame is counter
versus periphery, and between them the metric stopped being marginal. One
softer signal survives -- plan 11's contrast margin compresses 0.087 to 0.047
from 320 to 480 in the twelve-plan sample below, real but nowhere near
crossing -- worth naming rather than rounding off. An unrelated set of
composition fixes closed the measurement gap this bullet described, and it
was never revisited to check.

### The same mechanism moved to detail

`check_focal_contrast`'s third reading -- edge density, added in the eighth
pass, after this bullet was already written -- inherited exactly the
resolution sensitivity contrast was measured to have and then apparently
lost. Same rooms, same sweep, the detail LEAD (`di - do` from
`render_room.focal_report`):

| room | 160 | 240 | 320 | 400 | 480 |
|---|---|---|---|---|---|
| reference | +0.116 | +0.103 | +0.096 | +0.080 | +0.071 |
| plan 1, wall run | +0.003 | +0.001 | −0.002 | −0.005 | +0.001 |
| plan 8, L run | +0.107 | +0.071 | +0.064 | +0.056 | +0.044 |
| plan 10, wall run | +0.022 | −0.013 | −0.011 | −0.010 | −0.013 |

Every room's detail lead shrinks with resolution, the hand-authored
reference room included (+0.116 to +0.071, −39% relative) -- this is not a
generated-room-only effect. Confirmed directly against the live suite:
`build_plan.py --focal-scan 12` at 320 (today's default) reads **2 of 12
fail**; the identical twelve plans at 480 read **1 of 12**. Plan 1 is the
difference -- −0.002 at 320 (FAIL, floor 0.0), +0.001 at 480 (pass) -- same
seed, same dressing, same lighting, only the render target changed. That is
the exact failure mode the original bullet described, on the metric that
replaced the one it was written about. `manifest.py --check`'s own
`check_focal_contrast()` (the fast suite gate, not just the deep scan) was
already carrying this as a documented, accepted case -- NEXT.md's gate
section names it directly ("`check_focal_contrast` fails plan 1 (wall run)
by −0.002") -- so this was not a hypothetical, it was live in both gates.

### A ratio reformulation was measured and rejected

The natural fix for "a lead shrinks toward zero as resolution grows" is to
normalize it: `(di - do) / (di + do)` instead of the raw difference, so a
shrink common to both operands cancels. Swept alongside the raw numbers,
same four rooms:

| room | 160 | 240 | 320 | 400 | 480 |
|---|---|---|---|---|---|
| reference (norm) | +0.124 | +0.123 | +0.128 | +0.119 | +0.117 |
| plan 1 (norm) | +0.002 | +0.003 | −0.003 | −0.008 | +0.002 |
| plan 8 (norm) | +0.119 | +0.092 | +0.094 | +0.088 | +0.077 |
| plan 10 (norm) | +0.026 | −0.019 | −0.018 | −0.018 | −0.026 |

It works exactly as advertised for rooms that are not marginal: the
reference room's relative range across 160-480 drops from 39% (raw) to 9%
(normalized); plan 8's drops from 59% to roughly half that. It does nothing
for plan 1's flip, or for any flip at a floor fixed at exactly 0 --
`sign(a - b) == sign((a - b) / (a + b))` whenever `a + b > 0`, algebraically,
so a sign-preserving transform of the statistic cannot move a room to the
other side of a zero floor. Confirmed on the numbers, not just the algebra:
plan 1's normalized lead is +0.002 / +0.003 / **−0.003** / −0.008 / +0.002 --
it flips at the same targets as the raw lead, just with smaller digits. A
real result and a genuine non-fix, recorded so the next pass does not
re-propose it.

### Why: the renderer, not the statistic

Both `shade_toon`'s ordered dither (`pixelize.py`, `DITHER_LO/HI = 0.36,
0.64`) and `mesh.py`'s world-space surface grain (`GRAIN_BY_RAMP`, 0.3-0.85
of a ramp step) perturb the lambert value by an amount capped below one ramp
step, with a footprint that is fixed in **world** units -- a dither band
tied to the light geometry, a grain lattice tied to the material. The
raster's `downsample_modal` (`factor=3`, constant regardless of target)
resolves a perturbation once the real-world size of one output pixel
(`camera span / target`) shrinks below that footprint's width; below that
threshold the perturbation is outvoted by its neighbours and the surface
reads flat. Raising `target` shrinks every output pixel's world footprint,
so the same fixed-size dither/grain band crosses from "outvoted" to
"resolved" at a different target for a large flat surface (the counter) than
for the many small objects a busy periphery is made of -- which is exactly
the asymmetry measured, on both contrast (originally) and detail (now).

More resolution genuinely reveals more real, palette-quantized detail,
unevenly between zones. That is correct rendering behaviour, not a bug, and
no reformulation of a screen-space pixel statistic removes it -- the fix
would have to grade composition off world-space material samples instead of
raster pixels, immune to how many pixels a surface happens to occupy. That
is a rearchitecture of what the check measures, not a tuning pass, and it is
scoped and left for a future pass the same way the fifth topology and the
style LoRA were.

### The fix: confirm, don't normalize

Since the number cannot be made resolution-invariant, the VERDICT is made
resolution-independent a different way: a room that fails at `FOCAL_TARGET`
(320) gets one confirming render at `FOCAL_CONFIRM_TARGET` (480 --
`render_room.py`'s and this file's own delivery default), and is only
reported if it fails at **both**. A room that passes at 320 never pays for
the second render, so the common case (10 of 12 rooms) costs nothing extra;
only actual failures do, and there are at most a handful per run.

Verified on the live suite, both gates:

```
tools/build_plan.py --focal-scan 12
  ...
  plan  1  wall run   L +0.040  C +0.101  D -0.002   ok   RESCUED at 480 (L +0.039 C +0.101 D +0.001)
  ...
  plan 10  wall run   L +0.031  C +0.101  D -0.011   FAIL
  ...
  1 of 12 rooms fail the focal floors (8%), 1 rescued by the 480 confirmation
```

`check_focal_contrast()` -- the function `manifest.py --check` actually
calls, n=4, picking plans 1/2/3/8 -- now returns **zero** messages, closing
the case NEXT.md's gate section carried as an accepted failure. Plan 10, the
one defect in the sample that is real (negative at every resolution from 240
through 480, not just 320), still fires in both the scan and a direct call
to `check_focal_contrast(seed=10, n=1)` -- the confirmation catches the
resolution-dependent false positive without spending the real one a pass.
Proof renders: `proof/focal_plan1_320.png` vs `proof/focal_plan1_480.png`
(same room, the flip), `proof/focal_plan10_320.png` vs
`proof/focal_plan10_480.png` (same room, still failing both ways).

**Left honestly incomplete:** this is confirmation, not invariance. A room
whose defect only shows up at some third resolution neither 320 nor 480
would still slip through -- the fix trades "wrong at whichever resolution
you happened to pick" for "wrong only if two specific, load-bearing
resolutions agree it's wrong," which is the practical claim the delivered
game actually needs, not the abstract one this bullet originally asked for.

## A real, already-measured galley finding was never folded out of its own commit message

`tools/manifest.py --check` currently prints 3 composition `ERROR`s under
both style packs -- one on an L run, two on a galley -- neither mentioned
anywhere in this file's prose. Chased both down rather than assuming either
was new.

**Plan numbering shifted when galley was added.** The commit that built the
galley topology (`71451c3`) added a new branch to `floorplan.generate()`'s
shared `rnd()` stream, which changes which seed draws which topology from
that point on -- "plan 1" or "plan 10" in a pre-`71451c3` write-up (like the
section directly above this one) is not the same room as "plan 1"/"plan 10"
today. Re-ran `build_plan.py --focal-scan 12` fresh to get current identities
rather than assume the old numbers still mean the same rooms:

```
  plan  1  L run      L +0.062  C +0.146  D -0.001   FAIL
  plan  8  galley     L -0.012  C +0.045  D -0.019   FAIL
  plan 10  galley     L -0.019  C +0.054  D -0.042   FAIL
  plan 12  galley     L +0.031  C +0.054  D -0.013   FAIL
  4 of 12 rooms fail the focal floors (33%)
```

**Today's plan 1 (L run) is the already-known, already-rescued case, not a
new one.** `check_focal_contrast()` (what `manifest.py --check` actually
calls) already carries the `FOCAL_CONFIRM_TARGET=480` confirmation described
in the section directly above -- a failure at the scan's default 320 gets one
more render at 480 before it's reported, and only a roughly-1-in-12 room
fails both. `manifest.py --check`'s ERROR line names the specific room, not
whether it was confirmed; this is consistent with that section's own finding
(a resolution-dependent false positive lives around this rate) rather than
evidence of a fresh regression.

**Today's 3 galley failures are not new either -- they are commit `71451c3`'s
own already-measured, already-decided-against-fixing finding, just never
surfaced into this file.** That commit's message (`git log --format=%B -1
71451c3`) states it directly: across a widened 40-plan scan, galley clears
the contrast floor on all 3 of its occurrences but fails mean-L and/or detail
on all 3 (100%, vs 8-33% for the other four topologies) -- "a structural
consequence of the box's size... not fixed here because loosening
MIN_FOCAL_L/MIN_FOCAL_DETAIL to admit it would be tuning the instrument to
the answer." `focal_box()` unions every service/backbar/service_return zone;
a galley's box spans the room's full depth (both runs on opposite walls)
rather than a strip near one wall, which is presumably why L and D both read
low -- the same box-size-vs-detail mechanism D1 (Tier D, closed) already
named for L run's corner, more severe here because a galley's box is larger
still. Re-verified live in this pass at n=12 (3/3 galley occurrences fail,
matching the commit's own 3/3 at n=40) and confirmed it is not style-specific
-- `manifest.py --check --style snes_rpg` shows the identical two galley
composition messages, expected since this is pure geometry/luminance math,
independent of palette.

**Not a task.** Recorded here, matching the commit's own reasoning, so a
future pass does not re-discover this and loosen the floor to admit it --
that would hide the actual mechanism (a topology-specific focal-box-size
effect) behind a threshold picked to make one topology's numbers agree,
exactly the failure mode `check_focal_contrast`'s own resolution-confirmation
fix (section above) was careful to avoid for a different reason.

## The UI icon roster grew to 20, and the speckle gate now fails 5 of them under both styles, not 2 under one

An earlier note (this file, "UI art has a path now") measured 2 of the then-14
`cat: ui` icons failing snes_rpg's speckle gate. Re-running the full roster
fresh, live on current code, found two things wrong with that number: the
roster is now 20 entries (six more added since), and the failures are not
snes_rpg-specific at all.

```
python tools/ui_forge.py --style cozy_ghibli   -> 13/20 built
python tools/ui_forge.py --style snes_rpg      -> 12/20 built
```

Five icons fail under **both** styles: `ui_coin`, `ui_icon_bagel`,
`ui_icon_muffin`, `ui_icon_pastry`, `ui_icon_sandwich`. Two more fail under
`cozy_ghibli` only (`ui_icon_cookie`, `ui_nameplate`) and three under
`snes_rpg` only (`ui_clock_day`, `ui_heart_mood`, `ui_star_rating`) -- the
single-style failures are consistent with the file's own established finding
that speckle is seed-dependent (`--retry-seeds` is stochastic; a name passing
one style and not the other on a given run is not evidence of a style-specific
cause without a repeat sample). The cross-style overlap is the real signal:
whatever is wrong with these five is upstream of either palette.

**Root cause, seen directly in the concept images:** all five ask, explicitly
or by the object's own nature, for something SDXL renders with fine surface
detail regardless of the `UI_STYLE` wrapper's "no shading, no gradient" -- a
gold coin gets engraved rim rivets, embossed numerals and radial brush lines;
a bagel gets literal seed/crumb speckle; a sandwich's bread crust gets crumb
flecks. `out/ui/ui_coin_concept_raw.png` shows this plainly: a mint-quality
coin with an embossed "1", rivets around the rim, and fine radial hairlines,
none of which the prompt asked for.

**Two real fix attempts, two different strategies, one real result:**

1. Targeted negation per icon (`"a round gold coin, smooth flat face, no
   engraving, no texture"`, `"a plain bagel, smooth ring shape, no seeds, no
   bread texture"`, etc.) -- no reliable improvement. `ui_coin` went
   11.2% -> 11.5% (cap 6.2%), `ui_icon_bagel` 12.5% -> 14.8% (worse).
2. Generic anti-texture framing instead of per-object negation (`"solid flat
   colour, no grain, no specks"`) -- still no reliable improvement on the same
   four: coin 11.4%, bagel 12.7%, pastry 14.5%, sandwich 21.8%, all still
   gated, all within noise of the originals. A second `ui_coin` concept image
   under this framing came back with the SAME rivets and embossed numeral,
   confirming this is the same diffusion-negation weakness this repo already
   measured for a design-doc subject elsewhere (see `games/lantern_path`,
   PR #73/#74) -- a strong object prior (mint coin, bread crumb) survives
   explicit "no X" phrasing in the prompt.
3. Raising `--retry-seeds` was NOT attempted -- already measured and rejected
   by this file's own earlier finding, one section up in this same area of
   the code: a higher retry count found a passing seed for `ui_icon_pastry`
   that was not recognisably a croissant, while genuinely good croissants at
   lower seeds failed. More seeds buys gate-satisfaction, not quality, and
   that finding is why `--retry-seeds` defaults to 2.

One of the five WAS fixed, genuinely, not by gaming the gate: `ui_icon_muffin`
originally asked for "two blueberries" -- two small, distinct, dark
specks -- which is close to a textbook isolated-pixel trigger. Dropping the
blueberries and adding "solid flat colour, no grain, no specks" passed
cleanly under both styles (verified: `cozy_ghibli` seed 1 direct pass this
run, `snes_rpg` seed 3 after 2 reseeds) and still reads as a muffin --
visually confirmed, not just gate-confirmed, at 6x nearest-neighbour scale
under both palettes.

**Left open, the same way speckle-from-reconstruction was left open:** coin,
bagel, pastry, and sandwich are recorded as a real, measured, cross-style
limitation of the 2D icon path for subjects whose default SDXL depiction
carries strong fine-detail priors that "no X" phrasing does not reliably
suppress. Their prompts are reverted to the pre-this-pass originals in code
(no proven benefit from the two attempts above, so no reason to carry an
unproven diff) -- this section is the record, not the prompt text. A future
pass with a genuinely different lever (a different icon-generation model, or
accepting a visibly-imperfect-but-recognisable render the way the character
ceiling accepts a lumpy blob) could revisit this; more reseeds and more
negation words, on this evidence, will not.

## `ui_forge.check_icon`'s speckle floor was never actually `art_review`'s number, despite every account since this file's first commit saying it was

With canonical accepted-limitation claims and the multi-PR reconciliation
sweep both exhausted (Hour 72), this hour went looking in a different place
the untried-lever pattern can hide: not a check's *logic*, but a constant a
check trusts without re-deriving, the same shape as Hour 43's wrong-scale
`check_member_thickness` bug and Hour 53's buried-detail-offset bug, just
found this time in a threshold rather than a geometry constant.

`tools/ui_forge.py`'s `MAX_ISOLATED = 0.062`, with the comment directly
above it: "Same number `art_review` blocks sprites on, and deliberately the
same... they get held to one standard rather than to a softer one." The
file's own creating commit (`77ccdcb`, "Add ui_forge.py") says the same
thing in different words: "It now uses art_review's own number." Both are
wrong, and have been since the moment they were written.

`git log -p --all -- tools/art_review.py | grep "MAX_ISOLATED ="` returns
exactly one hit, across every commit on every branch in this repository:
`MAX_ISOLATED = 0.105`, set 2026-08-23 (`a747436`) and never touched again
anywhere. `ui_forge.py` was created three days later, 2026-08-26, already
carrying `0.062` -- a number that was never `art_review`'s at any point in
this repository's history, not "used to be and drifted," just wrong from
the first commit. The confusion is not a one-off typo either: PR #80's own
`ART_CRITIQUE.md` (an earlier incarnation of this audit loop, predating
this session -- see Hour 69's finding about that PR) independently repeats
it while investigating the frog-knight character ceiling: "a check whose
floor is 'authored art measures under 6.2% on its busiest frame'" --
checked directly against `art_review.py` on that same PR's own branch,
which is 0.105, not 0.062. Whoever wrote both passages believed 6.2% was
`art_review`'s real number; it never was.

**Practical effect**: every icon `ui_forge.py` has ever built was checked
against a floor 41% stricter than the sprite standard it was explicitly
designed to match ("the same kind of object... held to one standard"). Not
a softer gate that let bad art through -- the opposite, a harder gate than
intended, silently rejecting or forcing reseeds on icons that would have
cleared the standard the code claims to enforce.

**Fix**: `tools/ui_forge.py` no longer defines its own `MAX_ISOLATED`.
`from art_review import MAX_ISOLATED` replaces the hand-typed literal, so
the two constants cannot drift apart silently again -- the same "fix the
architecture, not the symptom" lever the despeckle-into-`render_sprite`
wiring (PR #81) used, applied to a constant instead of a function call.

**Verified**: `import ui_forge; ui_forge.MAX_ISOLATED == art_review.MAX_ISOLATED
== 0.105` directly, at the Python level, no assumption. `check_icon` re-run
against two synthetic fixtures -- a solid single-colour icon (0 problems,
same as before) and a full checkerboard (100.0% isolated, still fails
loudly at the new floor's `10.5%` cap, same as it would have at the old
6.2% cap -- genuine speckle isn't a borderline case either way, confirming
the check still catches what it exists to catch). `ui_forge.py --help`
still parses. 40-test suite passes unchanged.

**What could not be verified**: whether any specific real icon's pass/fail
verdict actually flips, because no real `ui_forge`-produced icon PNG exists
on disk this session (`out/ui/*.png` holds only `ui_chrome.py`'s procedural
output -- coin, cursors, frames -- torch/SDXL has been unavailable every
hour of this loop) and every historical isolated-pixel percentage recorded
in `ART_CRITIQUE.md` for real generated icons (13.4%, 19.1%, 33.5%, and the
frog knight's 11-12%) sits well above both 6.2% and 10.5%, so none of the
recorded cases happen to fall in the 6.2%-10.5% band where the fix would
have changed a verdict. The fix is provably correct on its own terms
(constants now match, by construction) even though no cached evidence
happens to demonstrate a flipped verdict.

## Closing the last gap in the PR-reconciliation sweep: every multi-PR file cluster in the open pile is now directly verified, not just trusted

This session's own PR-conflict reconciliation habit (Hours 44/47/48/55/63/64/70/71) has, each time, checked a specific slice of the open pile -- a named list of PRs sharing a file, or a newly-added PR against an older cluster. What hadn't been done, until this hour: a full, from-scratch inventory of every `tools/*.py` file touched by two or more of the 46 currently-open PRs, cross-checked against what this session's own memory already claims was reconciled -- because that memory record is itself a claim that can drift, same as any other doc in this repo, and the standing lesson from Hour 63/69 is to verify claims rather than carry them forward.

Built the inventory directly: diffed every open PR's branch against `main` (`git diff --name-only main...origin/<branch> -- tools/`), grouped by file, kept files touched by 2+ PRs. Result: seven files, `manifest.py` (8 PRs), `art_review.py` (8), `character.py` (4), `ui_forge.py` (2), `render_batch.py` (2), `assetlib.py` (2), `animate.py` (2). Checked each against memory's own record of what had already been reconciled:

- `manifest.py`'s 8 PRs (#83/86/88/91/92/93/94/101) -- exactly Hour 48's own 7-way sequential-merge list plus the ART_CRITIQUE.md/NEXT.md doc-append routine; matches.
- `art_review.py`'s 8 PRs (#81/83/87/93/95/102/103/109) -- exactly Hour 55's "art_review.py/assetlib.py-touching pile" list; matches.
- `character.py`'s 4 PRs (#88/89/94/117) -- Hour 48's 7-way sweep covers 88/89/94 pairwise, Hour 63 added 94x117, Hour 64 added 88x117 and 89x117; fully covered.
- `render_batch.py`'s 2 PRs (#81/#100) -- Hour 64, direct.
- `ui_forge.py`'s 2 PRs (#80/#121) -- Hour 69, direct (this is the one pair that WAS a real conflict, already corrected).

Two pairs had never been named as checked anywhere in memory, so they were the actual news this hour:

**`animate.py` (#81 vs #94).** `git merge-tree` flagged it "changed in both," which past hours (see the routine-vs-real distinction established since Hour 44) have learned not to trust without reading the actual hunks or running a real merge. Read first: #94's hunk changes the `roster` line in `demo()` to call `C.roster_for(args.style, ...)`; #81's change is 60 lines away, a docstring-only edit to `render_frame()` explaining why despeckle deliberately doesn't apply there. Confirmed with a real scratch-branch merge (`git checkout -b`, merge #81, commit, merge #94) rather than trusting the diff read: `Auto-merging tools/animate.py` -- clean, no conflict markers, only the routine `ART_CRITIQUE.md` tail-append needed resolving. Branch discarded after.

**`assetlib.py` (#83 vs #109).** Same story -- bundled into Hour 55's prose as part of the "art_review.py/assetlib.py-touching pile" but never verified as its own pair with its own evidence. Real scratch merge: `Auto-merging tools/art_review.py`, `Auto-merging tools/assetlib.py`, both clean; again only `ART_CRITIQUE.md`.

**Result: every file this session's own multi-PR-overlap inventory finds is now directly, individually verified clean** -- not inferred from a bundled description, not carried forward from an earlier hour's summary. No code changes; this is reconciliation bookkeeping, the same shape as Hours 44/47/48/55/63/64/70/71, closing the one part of that habit (a from-scratch file-overlap inventory, rather than checking a hand-picked list) that hadn't been done yet this session.

## Continuing the pre-Hour-58 pile sweep: PR #90's eye-visibility fix, re-verified fresh rather than trusted, and it retroactively strengthens Hour 62's own finding

Hour 70 spot-checked three early branches for conflicts; this hour picked
one more, chosen for direct relevance rather than at random: PR #90
(`organic-rig-eyes-single-azimuth`, "Hour 23") widened
`organic_rig.py`'s `check_eyes_visible` from a single hardcoded azimuth
(90) to three (45/90/135), the exact single-azimuth-blindness bug class
this session hunted extensively in its own Hours 20-49 window -- directly
relevant because Hours 61/62/67 all touched `organic_rig.py`'s eye
material and rendering, and none of them cross-checked this branch first.

**Re-ran it fresh rather than trusting the commit message.** Checked out
the branch, ran `organic_rig.py --style snes_rpg --check` live: clean.
Confirmed the widened azimuth set is actually present
(`EYES_VISIBLE_AZIMUTHS = (45.0, 90.0, 135.0)`) and `check_eyes_visible()`
genuinely returns `[]` today, not an assumption carried from the original
commit. Reproduced the fix's own verification method to confirm the near-
miss it found is still real, not a stale number: raised `MIN_EYE_PIXELS`
5 -> 5 (one above the real 3px floor) and re-ran -- `drifter: left eye
renders 4px at azimuth 45 (need 5)`, the exact member, angle and pixel
count the original commit recorded, reproduced live, today, on unrelated
current code.

**Reconciliation, not just verification.** `git merge-tree main
origin/organic-rig-eyes-single-azimuth origin/gates-catalog-organic-rig-
roster` (PR #90 vs PR #82): zero conflict markers, not even the routine
`ART_CRITIQUE.md` one. `git merge-tree main
origin/organic-rig-eyes-single-azimuth origin/organic-rig-never-actually-
renders-a-scene` (PR #90 vs this session's own PR #122): exactly one
conflict block, confined to the usual `ART_CRITIQUE.md` tail-append;
`NEXT.md` merges clean. No real code conflict either way.

**What this retroactively confirms about Hour 62's own work**: Hour 62
ran `organic_rig.py`'s checks and reported all four roster members clean,
`hair_mat=wood-4` not colliding with `EYE`, but did so against `main`'s
default single-azimuth `check_eyes_visible` -- the *weaker* version, since
PR #90's 3-azimuth widening was never merged. That result still holds
under the *stronger* check verified here (same `[]` outcome, `drifter`'s
own near-miss is about a DIFFERENT thing -- occlusion margin at 45 degrees,
not a hair/eye material collision), so Hour 62's conclusion was correct,
just not tested against the toughest available version of the check at the
time. Worth stating precisely rather than leaving as an unstated gap: not
every hour's own verification automatically incorporates every other
unmerged branch's strengthened checks, and this is the kind of thing a
reconciliation pass exists to catch.

No code changes -- PR #90 already contains the real fix, still valid,
still unmerged, still worth keeping. This branch just confirms it rather
than leaving it untouched in the pile.

## Spot-checking the pre-Hour-58 part of the open-PR pile after Hour 69's discovery, plus two fresh candidates -- all clean

Hour 69 found that PR #80's own commits are labelled "Hour 10/11 of the
recurring audit" and carry this session's own session ID -- meaning a large
early stretch of this same run (roughly Hour 1 through Hour 57) produced
real, shipped PRs that fell out of context after compaction, and one of
them (PR #80) had already fixed a bug this session rediscovered
independently two hours ago. That makes the earlier part of the pile a real
risk, not a curiosity, so this hour spot-checked three more early-numbered
branches directly rather than assuming Hour 69 was the only collision.

**PR #82 (`gates-catalog-organic-rig-roster`, "Hour 7")**: adds
`organic_rig.py`'s three check functions to `gates.py`'s own catalog. Read
in light of Hour 67's finding (`organic_rig.py`'s geometry never renders a
real scene) to make sure the two didn't contradict each other -- they
don't: PR #82 is about whether `gates.py --list` completely enumerates
every `check_*` function that exists, which is orthogonal to whether the
producer that check function grades is wired into content generation.
`organic_rig.py` legitimately owns real, catalogued checks; it just doesn't
own any shipped pixels yet. No overlap, no correction needed.

**PR #84 (`docs-wicker-basket-collage-recheck`, "Hour 4")** and **PR #93
(`symmetry-claims-style-blind`)**: both fully self-contained, both already
verified and closed by their own commit messages (a stale collage-defect
claim re-tested and found not reproducible; a bare `measured_symmetry()`
call found style-blind and threaded, confirmed no live casualty on either
style). Neither touches a file this session's later hours have shipped a
fix to. No conflict, nothing to add.

**Two fresh, unrelated candidates, checked for completeness rather than
left unexamined because the pile-audit found nothing:**

- `bitmap_font.py`'s glyph set (`GLYPHS`, 90 keys) covers full printable
  ASCII, which sounds like a natural "is coverage tested against what
  actually ships" question in this session's usual shape. It isn't a live
  one: `grep -rn "label:\|display_name:" assets.yaml` and a search for any
  strings/localization file both come back empty -- there is no real
  in-game text content declared anywhere yet for a coverage check to grade
  against. Structurally the same "no live casualty" shape as several
  earlier findings this session, just for content that doesn't exist yet
  rather than a code path that doesn't run yet.
- `wall_trim`/`wall_trim_shadow` (the two bible keys added by `279d1a8`,
  the commit that forced the style re-lock this file already documents):
  confirmed `grep -rn "wall_trim\b" tools/*.py` returns exactly one consuming file,
  `tileset.py`, already threaded call-time correctly (PR #38's
  `make_wall_patterns(materials)` factory, verified clean Hour 57). No
  second, parallel hardcoded reference anywhere else to drift from it.

No code changes. Doc-only, real due diligence, nothing new to fix.

## Following up on the last two hours' bug shapes elsewhere in the codebase -- five checked, all clean

The last two hours found real problems by asking two specific questions
that hadn't been asked of most of the codebase yet: "do two producers
silently compete for the same output path" (`ui_forge.py`/`ui_chrome.py`,
the previous section) and "does a check's pass actually match what ships,
or only what the check's own author assumed ships" (`organic_rig.py`, two
sections up). Applied both questions to five more files this hour rather
than re-reading either finding as closed. No new bug -- an honest null
result, but a real one, five real sub-investigations deep rather than a
skim.

**`bitmap_font.py`: is the cap-height axis tested the way the weight axis
already was found to be (Hour 56)?** Checked directly rather than assuming
symmetry between the two axes. It is, and better: `SIZES = (7, 9, 11, 13)`
is explicitly derived from `survey(lo=5, hi=20)` sweeping every cap in that
range through the full `check()` suite, and `--check` reprints the sweep
and hard-fails if `SIZES` ever claims a cap the sweep doesn't actually
pass -- the claim is self-verifying on every run, not asserted once and
trusted. `check_render` (the pixel-level check, `px`/`w`/`h`) is called
against the real written sheet for every one of the four shipped sizes
inside `main()`'s own build loop, with `args.style` threaded through --
confirmed by reading the call site, not inferred from the function
signature.

**`palette_swap.py`: does its variant output collide with any base
producer's own path, the same shape as the `ui_forge`/`ui_chrome` bug?** It
doesn't, by construction: `swap()` writes into `out/variants/<name>/`, a
namespace no base producer (`furnish.py`, `ui_chrome.py`, `ui_forge.py`,
`tileset.py`, `animate.py`) ever writes into, sibling to but disjoint from
`out/sprites/`, `out/ui/`, `out/tiles/`, `sprites/`. This file's own module
docstring also already documents, in detail, the exact multi-convention
directory mess (`out/sprites/<style>/` vs `out/ui_<style>/` vs `out/ui/
<style>/` vs `out/tiles_<style>/`) that made the `ui_forge`/`ui_chrome`
collision possible in the first place, and already guards its own
traversal against it (`sources_for()`'s `skip` sets) -- the file that would
have been most likely to repeat this bug is the one that already
diagnosed and fixed the general problem, for itself, before this session
started.

**`review_queue.py`: same style-threading question this session has hunted
all along.** `build()`'s `load_palette(load_style(style).palette_path)`
call is already correctly threaded, and its own comment names the exact
Hour-25-class bug (`art_review.py`'s pre-PR-#31 bare `load_palette()`) it
was written not to repeat. `check_direction_set` is geometry-plus-pixel
(consistent key-light direction across a real direction set), no separate
"tested config" to drift from a "shipped config" -- it grades whatever
`records` it's handed.

**`character.py`'s `_palette()` fallback**: a lazy, call-time default
(`ramps or _palette()`), the same "sentinel-resolved-at-call-time" idiom
this repo already committed to for exactly this reason (NEXT.md, PR #38).
Confirmed the real call site that matters (`manifest.py`'s
`generate_roster(12, seed=1, ramps=ramps)`, already audited Hour 60) passes
`ramps` explicitly, so `_palette()`'s hardcoded `cozy_ghibli` default is
never actually reached from the style-aware pipeline.

**`fx.py`'s `check_loops`**: re-confirmed pure-geometry, no ramp or camera
argument anywhere in its signature or body -- structurally cannot carry the
cross-style-blindness bug class by construction, same conclusion Hour 56
already reached, re-verified by reading the current function rather than
trusting the earlier note.

No code changes. Doc-only, same as every other hour this map stayed clean.

## Self-correction: "organic_rig.py is what actually ships" doesn't mean what this session's own memory took it to mean

Not a bug in the repo -- a precision failure in how this hourly loop's own
persistent notes read an already-accurate but genuinely ambiguous sentence
in this file's sibling doc, worth correcting honestly rather than letting it
keep compounding (same standard as the Hour 63 PR #117 provenance
correction, applied here to this session's memory instead of a PR body).

NEXT.md's own text (the `character.CUSTOMERS`-under-`snes_rpg` finding)
says: "`organic_rig.py` is what actually ships for a `cylinder_sphere`
style." True in the sense it was written for -- `style_approve.py`'s
`REQUIRED_PRODUCERS_ANY_OF` gate treats `organic_rig.py` as `snes_rpg`'s
real character-roster *evidence*, because its geometry is the one that
actually matches the style's declared `rig.primitive: cylinder_sphere`.
This session's own project memory read that sentence more literally, twice
(Hour 50: "organic_rig.py is what ships"; Hour 60: "REAL shipped characters
use organic_rig.py not character.py's box/prism rig"), and both times used
it as settled fact rather than re-checking it against the code.

**Checked directly rather than continuing to assume.** `grep -rn "import
character\|import organic_rig" tools/*.py`: `character` is imported by
`animate.py`, `build_plan.py`, `manifest.py`, `portrait.py`,
`preview_characters.py`, `preview_clips.py`, and `render_room.py`.
`organic_rig` is imported by none of them -- only by its own test/lock
tooling. `render_room.py` -- the tool that composes the actual shop scene
for both styles, including the `--style snes_rpg` render that fed
`style_approve.py`'s `llm:focal_hierarchy` evidence -- calls
`C.build(C.BARISTA)` and `C.build(C.CUSTOMERS[who], ...)` unconditionally,
with no branch on `args.style` or `rig.primitive` anywhere near those call
sites. `grep -n "rig.primitive" tools/*.py` returns exactly two files:
`organic_rig.py` (its own docstring) and `style_approve.py` (the gate's
comment explaining why the "any of" set exists) -- no content producer
reads it at all.

**Settled by looking, not just grepping**: `proof/shop_snes_rpg.png` (the
real, current, `--style snes_rpg` shop render) shows flat-topped, angular
characters -- box/prism silhouettes, the same rig shape `cozy_ghibli`'s
scene uses. `proof/organic_rig.png` (`organic_rig.py`'s own demo sheet, a
*different* four-person roster -- `scout`/`archivist`/`drifter`/`smith`,
not `character.CUSTOMERS`' `barista`/`reader`/`elder`/... at all) shows
round-headed, rounder-bodied characters. The two do not match, because the
first was never built with the second's code.

**What this actually means, stated precisely instead of compressed into
"ships":** `organic_rig.py`'s cylinder/sphere geometry has never appeared in
any real rendered room, animation, or portrait this repo has shipped, for
either style, including in the snes_rpg approval evidence that cites it. Its
entire footprint is its own `--check`/`--lock`/`--demo` output. It satisfies
`style_approve.py`'s gate honestly -- the gate only ever claimed to check
that *some* producer's declared-correct geometry passes its own checks, not
that the producer is wired into content generation -- and NEXT.md's
`character.py:roster` / `approved: false` lock entry for `snes_rpg` already
says this plainly if read carefully. But "is what actually ships" is the
kind of phrase that reads as stronger than that on a fast pass, and this
session's own memory is the proof: it produced a wrong belief twice without
ever being corrected by re-reading the code, until this hour's check.

**No code changes.** This is an existing, already-deliberate architecture
gap (`[[project_cozy_coffee_iso_multigenre_pivot_review]]`'s own "two
character rigs, never unified, deferred" line already names it correctly)
-- nothing here argues for wiring `organic_rig.py` into `render_room.py`
this hour, only for stating what is and isn't true about what already
ships. This session's own persistent memory has been corrected to match.

## A real fix instead of a claim to re-check: `ui_forge.py`'s default run silently un-fixed `ui_chrome.py`'s own fix

Not an accepted-limitation audit this hour -- a live footgun, found while
chasing this session's own project-memory note that `ui_coin`'s SDXL result
"doesn't read well as a coin, a gate-vs-eye gap, not fixed." That note is
itself stale (`tools/ui_chrome.py` replaced the generated coin with a drawn
one a while ago, and it reads instantly -- see `coin()`'s own docstring),
but chasing why the note was ever true surfaced something still real.

`ui_chrome.py`'s own module docstring says its output "lands in `out/ui/`
beside the generated icons and **deliberately overwrites** the chrome ids
`ui_forge` produced badly." That sentence is only true if `ui_chrome.py`
runs *after* `ui_forge.py`, every time. Nothing enforces that order.

Checked the actual overlap rather than assuming: `set(ui_forge.UI_PROMPTS) &
set(ui_chrome.CHROME)` is six ids -- `ui_coin`, `ui_dialogue_frame`,
`ui_nameplate`, `ui_star_rating`, `ui_ticket`, `ui_upgrade_frame` -- and for
the *default* style both tools resolve to the exact same output path
(`out/ui/<id>.png`; `check_ui`'s own docstring already documents that the
two producers' directory conventions "collapse to the same single `out/ui/`"
for the default style, though it never draws the ownership-collision
conclusion from that fact). `ui_forge.py`'s own module docstring's first
example command was, until this hour, literally
`python tools/ui_forge.py  # every ui entry in assets.yaml` -- the plain,
no-flags, "regenerate everything" invocation anyone would reach for first,
and it silently regenerates all six chrome ids through SDXL again.

**No check would catch the regression.** `ui_chrome.coin()`'s own docstring
already records that the SDXL coin "passed every check... both times" it
was tried, despite reading as a muddy blob by eye -- the isolated-pixel/
coverage gates `ui_forge.py` uses are exactly the checks this session
hunts for measuring the wrong thing, here not because a fix used the wrong
lever but because the *provenance* of which tool last wrote the file was
never something any check looked at.

**Fixed at the source rather than with a provenance check**: `ui_forge.py`
now imports `ui_chrome.CHROME` and excludes its six keys from the *default*
run entirely (`CHROME_OWNED`, `tools/ui_forge.py`) -- nothing to regenerate
means nothing to silently regress. An explicit `--only ui_coin` still works
for deliberate comparison, with a printed warning naming the risk and
pointing at re-running `ui_chrome.py` afterward. The module docstring's own
example command changed from the six-id-colliding `--only ui_coin,ui_ticket`
to a genuinely `ui_forge`-owned pair (`ui_icon_espresso,ui_icon_latte`).

Verified without SDXL (unavailable this session, same as every other hour):
the filtering logic lives entirely above the `import concept`/SDXL-load
line, so it was exercised directly -- default run: 14 `UI_PROMPTS` entries
in, exactly the 6 chrome ids skipped with a printed message, `ui_coin`
confirmed absent from `wanted`. Forced run (`--only ui_coin,
ui_icon_espresso`): both ids present, warning printed for the chrome one
only. `python tools/ui_forge.py --help` still parses cleanly (argparse
alone, no SDXL needed). Zero-regression: `manifest.py`'s `check_ui` doesn't
reference `UI_PROMPTS` at all (grepped, confirmed) so it's untouched by
this change; the 40-test suite passes unchanged. No visual re-render needed
-- this fix touches which ids `ui_forge.py` is willing to *attempt*, not
what any producer draws.

## Correction: this was not a fresh discovery, and PR #80 already fixed it, more completely, two days earlier

Found doing this hour's PR-reconciliation sweep against `tools/ui_forge.py`,
the same practice that caught the Hour 61/63 provenance error on
`character.py`'s `reader`/`EYE` collision. `git merge-tree main
origin/despeckle-icon-pipeline origin/ui-forge-chrome-ownership-collision`
returns three real conflict blocks in `tools/ui_forge.py` itself, not just
the routine `ART_CRITIQUE.md` tail-append -- both branches independently
edit the exact same region of `UI_PROMPTS` and the module docstring's
`--only` example, in the same direction.

PR #80's third commit (`ae13323`, dated 2026-09-17, titled "remove the six
chrome-owned ids from `UI_PROMPTS`, generated for nothing") is the same
finding this branch's own section above claims: `set(UI_PROMPTS) &
set(CHROME)` is the identical six ids, both write to the identical
`out/ui/<id>.png` path, and a plain `python tools/ui_forge.py` silently
regenerated all six through SDXL. Its own message even changed the module
docstring's `--only` example to the identical replacement pair
(`ui_icon_espresso,ui_icon_latte`) this branch picked independently.

**PR #80's fix is more complete than this branch's.** Two differences:

- **Scope**: PR #80 deletes the six ids from `UI_PROMPTS` outright, so
  `--only ui_coin` now hits the "unknown ui ids" error path -- no path back
  to generating a chrome-owned id via SDXL at all. This branch instead kept
  a soft default-exclude with an explicit-`--only` override. `ui_chrome.py`'s
  own docstring ("It is not a prompt to tune. It is the wrong tool.") argues
  for PR #80's harder stance, and it matches this repo's own established
  precedent (`ui_icon_pastry`'s generative path was deleted outright when
  rejected, not left reachable behind a flag) more closely than this
  branch's softer one did.
- **Depth**: PR #80 also found and removed a second, related piece of dead
  code this branch never looked for -- `UI_SEED_OVERRIDE["ui_coin"] = 3`
  (added in PR #80's own second commit, tuning which SDXL seed `ui_coin`
  used) became unreachable the moment `ui_coin` left `UI_PROMPTS`, and PR
  #80 removed it with a comment explaining why the tuning was correct at
  the time but the artifact it improved was already dead. This branch's fix
  left that entry untouched because it never knew to look for it.

**Same shape as the Hour 63 correction, applied to this branch instead of a
different one**: a real fix, independently re-derived and independently
verified (both branches confirm the same six-id overlap, the same shared
output path, the same zero-regression result), that turns out to already
exist, earlier and more complete, on a PR this session hadn't cross-checked
against before publishing. The underlying diagnosis in both cases was
correct -- this is not a "the finding was wrong" correction, it is a
"the finding was not new, and a better version of the fix already existed"
correction, the second time this exact shape has happened this session
(the first being `character.py`'s `reader` collision vs PR #24/#94).

**No new code change here.** The honest recommendation for whoever
reconciles the open PR pile: prefer PR #80's version of this fix over this
branch's -- it is earlier, stricter (matches `ui_chrome.py`'s own stated
doctrine), and catches a second dead-code consequence this branch missed.
This branch's own fix is not wrong, just redundant and slightly softer;
left open rather than closed, per standing practice, for him to reconcile
directly.

## Auto-uprighting: tried the "genuinely different objective" the earlier finding invited -- it doesn't help either

"Auto-uprighting: the objective is not well-defined, not just object-specific"
(above) tried one lever repeatedly -- widening the pitch/roll search box
around the same flatness-spread objective (minimize the XY spread of the
lowest-1%-by-height vertices) -- found a second, distant optimum outside the
original box on the teapot, and closed with: "Left undone... don't
re-attempt without a different objective, not just a wider search." That is
exactly this session's own untried-lever question, stated in the file's own
words, so it was worth actually trying rather than re-reading as settled.

**The different objective:** stability, not flatness. A real resting object's
centre of mass sits over its base's footprint; a spurious flat patch
invented on the unseen side of a single-view reconstruction has no reason to
satisfy that. Implemented independently (not a reproduction of the original, unsaved
script -- a fresh one-off, same convention as every other proof image in
this file: the render is committed, the throwaway generator isn't): for a
candidate rotation, take
the lowest-1% slab as before, build its 2D convex hull in XY, and score how
far the whole-mesh centroid sits inside that hull (positive = stable,
negative = centroid hangs outside the footprint). A 21x21 pitch/roll grid
(-60 to +60 degrees, step 6) on the same three real meshes the original
finding named (`out/mesh/teapot_bound.obj`, `basket_bound.obj`,
`kettle_bound.obj`):

| mesh | baseline (0,0) flat / stab | best-by-flatness | best-by-stability | objectives agree? |
|---|---|---|---|---|
| teapot | 0.1273 / 0.0013 | (-36,-30) 0.1071 / 0.0040 | (-48,6) 0.1152 / 0.0253 | no |
| basket | 0.1513 / -0.0014 | (-12,-48) 0.1203 / 0.0236 | (6,-60) 0.1461 / 0.0311 | no |
| kettle | 0.1775 / 0.0083 | (-60,42) 0.1087 / -0.0053 | (-54,-18) 0.2019 / 0.0248 | no |

(Absolute numbers aren't comparable to the original finding's -- different
metric definition, same real meshes -- the shape of the result is what
matters.) Two things already argue against stability being the fix: it
disagrees with the flatness objective's own pick on all three objects, and
the grid itself is rough for *both* objectives -- 28 to 68 local optima out
of 441 grid points, not two or three well-separated candidates. A search
that bumpy isn't converging on "the true base" under either objective; it's
finding whichever nearby dent the 6-degree grid happened to land near.

**Settled by rendering all three candidates and looking, the same standard
this file holds every other finding to** (`proof/upright_stability_probe.png`,
18 real renders -- baseline, best-flat, best-stability, two azimuths each,
three meshes, real `render_sprite` output through the shipped rasterizer and
`cozy_ghibli` palette, not a mockup). The result is the opposite of what the
stability hypothesis predicted: **the untouched baseline -- zero rotation,
exactly what ships today -- reads better by eye than either "corrected"
orientation, on all three objects.** The kettle's baseline is clearly
legible as a kettle (spout, handle, lid, resting flat); both correction
attempts turn it into an unreadable tilted lump. The teapot's baseline shows
a recognisable spout and body; both corrections make it read worse, not
better. The basket's best-by-stability pick is the most telling failure
specifically: it rotates the object to foreground the concave scoop this
file's own earlier pass ("the basket's crescent frames... an honest crescent,
a scooped shell shape, present in the geometry itself") already identified
as the reconstructor's invented unseen side -- stability scored that
scooped face as a *more* stable base than the real one, which is the
objective being actively fooled by the same artifact flatness was fooled by,
not a fix for it.

**Verdict: the different objective was tried, and it doesn't generalize
either.** Both flatness and stability chase whichever locally-convincing
patch a single-view reconstruction happened to invent on the side it never
saw; neither has any way to know that patch is fake, because -- as the
"far side... cannot be verified by machine" bullet already says two sections
up -- the information needed to tell real base from invented artifact isn't
in the mesh at all. The strongest evidence for leaving this undone isn't
"we didn't find the right search box," it's that *doing nothing* already
beats both searches on every object tested. No code changes ship from this
finding -- there is no auto-upright tool in the pipeline to change, and this
result argues against ever building one on top of either objective, not for
tuning one further. `NEXT.md`'s "Auto-uprighting is not a well-posed search"
bullet gets a pointer to this section rather than a rewrite, since nothing
here contradicts it -- it corroborates it from a direction the original
bullet explicitly invited someone to check.

## PR-conflict reconciliation, re-run at the pile's largest size yet (39 open PRs) -- the two clusters never cross-checked before both come back clean

This file's own reconciliation habit (Hours 44, 47, 48, 55, 63) checks
whether open PRs that touch the same file actually merge cleanly against
each other, not just against `main` individually -- `git merge-tree` shows
every real conflict, and this file's own tail-append pattern (every hourly
section lands at the same position on a `main`-based branch) produces one
`changed in both` block on ART_CRITIQUE.md for nearly every pair, which is
routine and harmless, not a real conflict. The risk that actually matters is
a second `changed in both` block, inside a *code* file, with its own
`<<<<<<<`/`>>>>>>>` markers.

The pile is now 39 open PRs (up from 26 at Hour 48's sweep), and two file
clusters had never been checked pairwise before: `tools/character.py` (4
PRs touch it: #88, #89, #94, #117) and `tools/render_batch.py` (2 PRs: #81,
#100). #94 vs #117 was already checked at Hour 63 (clean); #88 vs #89 vs #94
were checked as part of Hour 48's original sweep (clean). The genuinely new
pairs this hour: #88 vs #117, #89 vs #117 (both new since #117 shipped at
Hour 61), and #81 vs #100 (never checked against each other at all).

```
git merge-tree main origin/direction-stability-not-wired origin/reader-hair-eye-collision-snes-rpg   # #88 vs #117
git merge-tree main origin/eye-legibility-single-azimuth origin/reader-hair-eye-collision-snes-rpg    # #89 vs #117
git merge-tree main origin/render-sprite-grain-wear-unwired origin/despeckle-lifted-objects           # #100 vs #81
```

First two: exactly one `<<<<<<<`/`>>>>>>>` pair each, both confined to
`ART_CRITIQUE.md`'s tail (`git show <branch>:tools/character.py` for both
sides diffs clean against the merge base -- neither #88 nor #89 touches
`character.py`'s `CUSTOMERS`/`hair_mat` fields at all, only `organic_rig.py`
and `portrait.py`'s check wiring). Routine, not a finding.

Third pair looked ambiguous at first glance -- `grep -c "<<<<<<<"` on the
raw output returned 1, which could in principle land inside either of the
two `changed in both` blocks the diff contains (one for `ART_CRITIQUE.md`
starting at line 1 of the output, one for `NEXT.md`/`tools/render_batch.py`
starting later). Resolved by reading the actual conflicting text rather than
trusting the line-number heuristic: the `<<<<<<< .our` marker sits
immediately after PR #100's own last ART_CRITIQUE.md paragraph
("...left unmerged."), and the content between it and `>>>>>>> .their` is
entirely PR #81's own prose additions to this same file (three full
sections, "third re-check"/"despeckle's own scope claim"/"`MAX_ISOLATED`'s
own calibration" -- all ART_CRITIQUE.md text, zero lines of Python). No
`tools/render_batch.py` content appears between the markers anywhere.
Confirmed independently via a direct diff extraction
(`sed -n '/tools\/render_batch.py/,/^$/p'` on the same merge-tree output):
PR #81 adds one `from ... import despeckle` line and one
`px = despeckle(px, target)` call; PR #100 changes unrelated `grain`/
`key_gain`/`ambient` default-parameter lines elsewhere in the same
function. The two diffs sit near each other in the file but never touch the
same line -- `render_batch.py` merges clean between #100 and #81.

**Result: all three previously-unchecked pairs, including the two file
clusters that had never been cross-checked at this pile size, merge clean.**
No real code conflict found anywhere in this sweep. Left as a documented
negative result, same as Hours 48 and 55's re-runs -- the pile growing from
26 to 39 open PRs hasn't introduced a cross-PR conflict in either of the two
clusters most likely to carry one (the file four PRs touch, and the file
two PRs both add a line to near each other in the same function). Branch
`character-py-render-batch-reconciliation-checked`, new, unrelated to any
other open PR's subject -- left unmerged.

## Checked whether Hour 61's eye-collision bug generalizes further -- it doesn't; `concept.py`'s `check_concept_fitness` run live against real cached data -- clean

**Does the `hair_mat == EYE` collision reach further than `reader`?** Two
angles, both closed. First: does `portrait.py` ever build a bust for a
GENERATED character (where the proposal loop could draw the same collision
by chance, same as `check_spec_coverage`'s own generated-extras concern)?
Grepped every caller in the repo -- nothing outside `portrait.py` itself
calls `build()`/`check()`, and neither of those ever calls
`generate_roster`/`generate_spec`. Portraits are only ever built for the 9
named `ROSTER` members; there's no generated population for this collision
to hide in. Second: does `organic_rig.py`'s own roster (the one whose
`check_eyes_visible` originally caught `archivist`) have another live
instance? Ran all three of its checks fresh: `check_roster`,
`check_eyes_visible`, `check_direction_stability` -- all `[]`. All four of
its roster members (`scout`, `archivist`, `drifter`, `smith`) already carry
`hair_mat="wood-4"`, not `EYE`'s own material. Nothing left to fix on either
rig for this bug shape.

**Pivoted to `concept.py`'s `check_concept_fitness`, untouched this session.**
Unlike `ui_forge.py`'s icon gate, this one doesn't need SDXL to evaluate --
it grades an already-matted PNG on disk (alpha-band width, fill fraction,
edge-crop, second-blob size), so the 32 real cached, non-adversarial
concept images in `out/concept/` (confirmed real production output, not a
test fixture) are genuine testable ground. Ran it fresh against all of them
(one, `teapot_1.png`, has no alpha channel and would need `rembg` to re-matte
-- not installed in this environment, skipped, same shape of gap as
`torch`/SDXL elsewhere):

```
32 testable images -> 0 problems
```

Also swept `out/kind_test/`, `out/neg_test/`, `out/probe_style/`,
`out/final_test/` (26 more testable images) for completeness -- 19 problems
surfaced there, but every one is a deliberately adversarial fixture by its
own filename (`mario_plus_NEG_BASE`, `basket_plus_anti-collage`,
`style_probe_basket_dir2` cropped at the frame edge on purpose) left over
from the check's own development, described in its own docstring as the
"C1 31-subject set" calibration study -- these are expected failures that
prove the check still correctly rejects bad input, not live defects.

`check_concept_fitness` also has no `ramps`/style parameter at all (pure
alpha-channel and blob geometry on a 2D image) and no azimuth -- structurally
immune to both of this session's two established bug shapes by construction,
the same way `check_direction_labels` (Hour 60) and `check_distinct`
(Hour 59) are. Called from three real production sites (`concept.py`'s own
`main()`, `concept_ui.py`'s GUI, and `factory.py`'s actual generation loop,
`factory.py:188/198`) -- genuinely load-bearing, not dead code.

**Finding: no new live bug this hour.** Both follow-ups to Hour 61's fix
closed cleanly (no generalization, nothing left on either rig), and
`check_concept_fitness` -- heavily used, never individually audited before
this session -- passes clean against every real, non-adversarial cached
image available to test it with. Honest null result.

## `portrait.py`'s `reader` shipped with an invisible left eye under `snes_rpg` -- a live, currently-failing check, not a documented limitation

Ran `portrait.py`'s own three deterministic checks (`check_distinct`,
`check_determinism`, `check_palette_exact`) plus `check_eyes_visible` for
real, both styles, rather than reading them cold -- no SDXL dependency here,
unlike `ui_forge.py`'s icons. `--style cozy_ghibli`: clean, 9/9. `--style
snes_rpg`:

```
BLOCKER  reader: left eye renders 0 px against bare skin (need 3) -- occluded or off-frame
```

Real, reproducible, currently on `main` -- not a cached or historical
failure. `manifest.py --check` never calls `portrait.py`'s checks at all
(confirmed by grep, consistent with Hour 51's finding that portraits aren't
wired into the export pipeline for either style), so this failure is
invisible to the aggregate gate; it is not invisible to the tool's own
`--check`, which is what actually caught it.

**Root cause, found by isolating the two renders rather than guessing.**
`reader`'s `hair_mat` was `"neutral-2"` -- literally `character.EYE`'s own
material, not merely close to it. Comparing `plain` (bare head+hair) against
`eyed` (bare + one eye box) pixel-for-pixel: `cozy_ghibli` left eye 30px
different, `snes_rpg` left eye 0px, right eye clean at 31px/109px in both --
so this is not off-frame (zero pixels landed where `plain` was `None`, ruled
out directly) and not a whole-render collapse, just this one eye, this one
style. `bob` hair sits mostly in front of the left eye at this azimuth; the
narrow sliver of eye that still peeks through only read as an edge in
`cozy_ghibli` because each face's own lambert shading happened to land on a
different step of a long-enough neutral ramp -- same material, different
final pixel, by luck of the lighting. `snes_rpg`'s shorter neutral ramp
rounds both faces' shading to the identical step, and the "different
pixel" that made the eye visible disappears entirely.

**Same mechanism this repo has already named twice**, in two different
functions: `organic_rig.py`'s own `check_eyes_visible` caught the identical
shape of bug for `archivist` (`hair_mat="neutral-3"`, one step from `EYE`'s
`neutral-2`) and fixed it by moving the hair material away from `EYE`
entirely (NEXT.md, `hair_mat` -> `wood-4`) rather than relying on lighting
to keep them apart. `reader`'s case is more extreme -- exact material match,
not one step off -- and lived in a different rig (`character.py`'s box/prism,
not `organic_rig.py`'s cylinder/sphere) and a different check function
(`portrait.py`'s bust render, not the full-body one). Two other roster
members share the same `hair_mat="neutral-2"` (`barista`, `artist`) and pass
clean under both styles -- their hairstyles (`bun`, `curly`) don't overlap
the eye position the way `bob` does at this azimuth, so the collision alone
isn't sufficient; it took this specific hairstyle for it to bite.

**Fix: `reader.hair_mat` -> `"wood-4"`**, the exact value the `archivist`
precedent already validated. `tools/character.py`'s `CUSTOMERS` list.

**Verification:**
- `portrait.py --check --style snes_rpg`: 1 BLOCKER -> 0, `9 portraits:
  palette-exact, distinct, both eyes visible on every one, deterministic`.
- `portrait.py --check --style cozy_ghibli`: stayed clean, and the margin
  improved -- left eye 30px -> 110px, right eye 31px -> 125px (both now on
  the same distinct-material footing right eye always had).
- `snes_rpg` after the fix: left eye 0px -> 110px, right eye 109px.
- `character.py`'s own `--style snes_rpg` run: identical 4-blocker list
  before and after (`elder`/`reader`/`regular`/`writer` contrast/waistline
  -- the already-known, already-accepted-as-not-fixed-by-design findings,
  confirmed via `git stash` A/B on the exact same command) -- `reader`'s own
  waistline blocker is a shirt/trousers value gap, unrelated to hair, and is
  untouched by this fix. `check_palette_spread`'s "no more than half a
  figure on one ramp" rule stays clear: `wood-4` hair alongside `wood`
  trousers is exactly 2 of 4 parts (50%, the limit, not over it).
- `manifest.py --check`, both styles: byte-identical error/warning counts
  before and after (`cozy_ghibli` 3/8, `snes_rpg` 10/8) -- expected, since
  `manifest.py` never calls `portrait.py` at all; this confirms the fix is
  isolated, not that it was exercised there.
- 40-test suite: 40 passed.
- Visual, not just metric: rendered `reader`'s portrait at 8x nearest-
  neighbour under both styles and looked at it. Both eyes clearly legible in
  both -- hair reads as a warm brown/maroon instead of a near-black that
  happened to double as the eye's own colour.

## Correction to the section above: this was not a fresh discovery, and the record should say so

Doing this hour's usual PR-reconciliation sweep (the pattern Hours 44/47/48/
55 established) against the newest PRs turned up something the sweep isn't
usually for: a provenance problem in the section directly above, on this
same branch. `git merge-tree` against PR #94 (`roster-fields-style-blind`,
Hour 27, unmerged) surfaced its own `ART_CRITIQUE.md` text quoting `portrait.py
--check --style snes_rpg` reporting the exact same `reader` failure --
already fixed on `main` at merge time? No: reading it in full showed PR #94
was explicitly describing it as a "separate, pre-existing `reader`
eye-occlusion blocker from PR #24 ... left exactly as-is." Pulled PR #24
directly (`gh pr view 24`) rather than trusting the cross-reference: it is
**merged**, on `main` today, titled "Fix the same --style-ignored-by-the-check
bug in portrait.py and manifest.py," and its own body already contains this:

```
python tools/portrait.py --check --style snes_rpg
BLOCKER  reader: left eye renders 0 px against bare skin (need 3)

`reader`'s `hair_mat` (`neutral-2`) and `character.EYE` (also `neutral-2`)
are literally the same ramp+offset -- that pair separates enough under
`cozy_ghibli`'s specific RGB values to read as two things; under
`snes_rpg`'s darker, more compressed `neutral` ramp it doesn't.
```

Same defect, same numbers, same root-cause explanation, word for word the
mechanism the section above worked out independently -- written by an
earlier hour of this same session, merged into `main` already. PR #24 judged
it "fine, not a blocker" (`style_approve.py`'s OR-logic already lets
`organic_rig.py` satisfy `snes_rpg`'s character-roster requirement) and
recorded it honestly rather than suppressing it: `styles/snes_rpg/lock.json`
carries a real `portrait.py:roster` entry with `approved: false`. PR #94
re-ran the same check an unknown number of hours later, found the blocker
still there, and deliberately left it alone as out of that PR's own scope.

**So the section above's own framing -- "a live, currently-failing check,
not a documented limitation" -- has it backwards.** It *was* a documented,
already-explained, twice-independently-reconfirmed limitation, explicitly
accepted as non-blocking by two earlier passes. What was genuinely new this
hour was not the finding, it was the FIX: nobody had actually applied
`archivist`'s own already-proven lever (move the hair off `EYE`'s literal
material) to this specific case before, despite two separate hours writing
down exactly why it would work. The verification above (real before/after
numbers, zero-regression checks, visual inspection) is unaffected by this
correction and stands as written -- only the "this is new" claim in the
heading and opening paragraphs was wrong, and this section exists so a
future hour reads the accurate provenance instead of re-trusting the
original framing.

**Reconciliation, checked rather than assumed.** PR #24 is already merged,
so there's nothing to reconcile there. PR #94 is still open: `tools/character.py`
merges clean against it (PR #94's fix lives entirely in a separate
`ROSTER_OVERRIDES` table added later in the file and never touches
`reader`'s `hair_mat`, only `reader`'s `trousers` under `snes_rpg`
specifically -- the two changes are on non-overlapping fields and
non-overlapping lines, confirmed via `git merge-tree`, not assumed from the
prose). Only `ART_CRITIQUE.md` conflicts, at the routine tail-append point
every open PR on this file conflicts at -- not a real problem, the same
shape Hours 44/47/48/55 already established for this file specifically.

## Four more candidates checked this hour -- one already fixed on an open branch, three genuinely clean

**`character.py`'s `check_waistline`/`check_spec_coverage`.** Both looked
like plausible single-config-blindness candidates going in. Neither is:
`check_waistline(ramps, roster=None)` takes `ramps` as a required positional
(cannot be called bare) and `manifest.py` runs it twice -- once against the
fixed `ROSTER` (`manifest.py:383`) and once against a 12-seed generated
extras cast (`manifest.py:405-408`, `_c.check_waistline(ramps, _extras)`) --
so the generated population this session's other bugs have hidden behind
(`check_generator_range`'s `counter`, `check_spec_coverage`'s own `skin`/
`blush` history) is already inside this check's real coverage, not outside
it. `check_spec_coverage` is correctly `ramps=ramps` threaded at its own
call site (`manifest.py:398`). Read, not run -- no new numbers, no fix.

**`organic_rig.py`'s `check_roster`/`check_eyes_visible`/
`check_direction_stability` wiring into `manifest.py --check`.** This is
exactly the shape of gap this session hunts -- `snes_rpg`'s real shipped
characters come from `organic_rig.py`, not `character.py`'s box/prism rig,
so if `manifest.py --check --style snes_rpg` never called the former, its
own character-roster gate would be checking a non-shipping producer while
the real one went unverified. Checked whether that's still true on `main`:
it isn't, on a branch already in flight. `gh pr view 101` names its own
branch `manifest-check-missing-organic-rig`, and `git show` on it confirms
`organic_rig.check_roster`/`check_eyes_visible`/`check_direction_stability`
are already wired in, gated on `rig.primitive == cylinder_sphere`. Hour 50's
own memory entry undersold this PR as "gated the box/prism checks off" --
it did that too, but the organic-rig wiring is the larger, already-complete
half. Nothing new to ship; re-confirmed via the actual diff, not the
one-line summary.

**`palette_forge.py`'s `check_separation`, run live, both styles.**
Unconditional in `palette_forge.py main()` (`palette_forge.py:465`) --
every real palette build already self-checks this, no `--proof`-style gate.
Ran fresh for real numbers rather than trusting that:

```
python tools/palette_forge.py --style cozy_ghibli
  closest palettes base/golden_hour at 0.0358 (floor 0.035)
  all constraints pass; 4 variants

python tools/palette_forge.py --style snes_rpg
  closest palettes evening/overcast at 0.0471 (floor 0.035)
  all constraints pass; 4 variants
```

`cozy_ghibli`'s base/golden_hour pair sits 0.0008 above the floor -- a real
near-miss, but not a new one: the check's own docstring already names this
exact case and value ("`golden_hour` sits just over it at 0.0358 by design,
because late afternoon is meant to be a warm reading of the base palette
rather than a different world"). Measured value matches the documented one
exactly; nothing drifted.

**`animate.py`'s `check_direction_labels`.** Self-verifying by
construction -- re-derives the `DIRECTIONS` tuple from the camera basis and
compares, no seed or style axis to under-test. Ran it directly: `[]`, clean.

**Finding: no new live bug this hour.** One candidate (`organic_rig.py`
wiring) turned out to already be fixed on an open, unmerged PR rather than
still-open ground; the other three are correctly built and currently
passing with real numbers behind them. Honest null result.

## `furnish.py`'s `check_distinct`, rebuilt from scratch for the whole real library, both styles -- clean, and by a structure that can't have the `counter`-shaped bug

Started this hour on `ingest.py`'s `check_roundtrip` -- `manifest.py:458`
calls it bare (`check_roundtrip()`, no `ramps`) on `main`, which looked like
exactly the style-threading gap Hour 52 fixed for its two neighbours in the
same import line. It already isn't: read the still-open, unmerged
`ingest-checks-style-blind` branch (PR #92) directly rather than trusting
memory's summary, and its own manifest.py already threads
`check_roundtrip(ramps=ramps)` and `check_transform(ramps=ramps,
checks=active.checks)`, with a comment explaining `check_albedo_regression`
is deliberately left bare. Nothing new here -- re-confirmed already-done
work, not re-shipped.

Moved to `furnish.py`'s `check_distinct`, untouched by this session so far.
Its own docstring records a real historical bug: `saucer` and `cup_latte`
both resolved to `cup_and_saucer`, and because every prop is framed to fill
its 64px box, the declared-height difference between them vanished in the
rendered pixels -- two ids, one asset, nothing else in the per-asset-checked
pipeline could see it. The check hashes all 8 directions of every real
report and flags any two ids whose full sprite sets are byte-identical.

**Structurally the right shape already -- checked, not assumed.** Unlike
`art_review.py`'s old `GENERATORS` table (the source of the `counter`
`front="x"` bug, Hour 53), `check_distinct` takes `reports` built directly
from `RECIPES` and `assets.yaml`'s own declared parameters
(`furnish.py:446`, `build_one(asset_id, declared[asset_id],
RECIPES[asset_id], ...)`) -- there is no separate, shadow parameter table
for it to fall out of sync with the real one. The 7 props that hit the
footprint cap (`espresso_machine_2group`, `pastry_case`, `table_2top_round`,
`table_4top`, `table_communal`, `plant_monstera`, `crate_stack` -- exactly
the class the docstring's own historical bug came from, scale clamped away)
are the real, live candidates for a repeat of that collision, not a
synthetic worst case.

**Ran the real, full 56-recipe library fresh, both styles, not from cache**
(`out/sprites/`'s existing PNGs predate this session and can't prove
`check_distinct` still passes on the CURRENT code):

```
python tools/furnish.py --style cozy_ghibli   # 2m10s, 448 sprites
  56 distinct sprite sets -- no two ids render the same eight images

python tools/furnish.py --style snes_rpg      # 2m12s, 448 sprites
  56 distinct sprite sets -- no two ids render the same eight images
```

896 real sprite renders total (56 assets x 8 directions x 2 styles), zero
collisions, including among the 7 footprint-capped props -- the exact
scenario `check_distinct` exists to catch. `ramps` is threaded correctly per
`--style` (`furnish.py:441-442`, resolved from `load_style(args.style)`, not
a module constant). `git status` after both runs: nothing tracked changed
(`out/sprites/` is gitignored build output).

**Finding: no live bug.** `check_distinct` is real, correctly wired, tests
the actual declared recipe parameters rather than a copy of them, and passes
clean on a genuine from-scratch rebuild of the entire prop library for both
styles. Honest null result -- the saucer/cup_latte failure mode this check
exists for has not recurred.

## Ran the real Godot round-trip export, both styles, real binary -- clean, and one near-miss chased down to already-correct architecture

`export_godot.py`'s three round-trip checks (`check_nine_slice_roundtrip`,
`check_palette_lut_godot`, `check_font_layout`) need an actual Godot 4.3
binary -- unlike the SDXL/TripoSR stages, this one turned out to be genuinely
available in this environment (`D:/vibes/.godot-tool/Godot_v4.3-stable_win64_console.exe`
resolves and exists), so this is real, testable ground this hourly loop
hadn't exercised end-to-end before.

**First run, `--style cozy_ghibli`, came back with `0 fonts` and no
`check_font_layout` output at all** -- looked, for a moment, like the same
"declared but not built" shape as `out/ui/`'s empty icon library or
`tileset.py`'s `--proof`-gated `check_manifest_placement` (Hour 57). Traced
it: `out/ui/font/font.json` genuinely didn't exist in this environment --
nothing in this session had run `bitmap_font.py` yet, and `check_font_layout`
silently returns `[]` when `build.get("font", {}).get("sizes")` is empty,
same as `check_nine_slice_roundtrip` does for an empty icon set. Built the
font for real (`python tools/bitmap_font.py --style cozy_ghibli`, 4 sheets,
90 glyphs) and re-ran the export -- `check_font_layout` then genuinely fired.

**Chased whether the silent-skip itself is the bug, and it isn't.**
`package_godot.py`'s `stage()` follows the identical `if dir.exists(): stage;
if content: include` shape for every category -- sprites, anim, UI, tiles,
font, all four other categories, not just this one -- so treating fonts as a
special case would have been inventing an inconsistency, not fixing one.
The real question is whether anything upstream is responsible for catching
"declared but not built" before export, the way `manifest.py --check`
already does for the UI icon library. Grepped `manifest.py` directly rather
than assuming: `check_ui` already contains exactly this gate --
`"ui_font declared and no out/ui/font/font.json -- run tools/bitmap_font.py"`
(`manifest.py:217-219`) -- so `export_godot.py` silently trusting that an
earlier, already-correct gate ran first is the intended layering, not a gap.
No code change here; a real hypothesis, checked against the actual code, and
retired.

**With the real prerequisite built, ran the full pipeline for both styles,
for real, not from cache:**

```
python tools/bitmap_font.py --style cozy_ghibli   # 4 sheets, 90 glyphs
python tools/ui_chrome.py  --style cozy_ghibli    # (already on disk)
python tools/export_godot.py --style cozy_ghibli  # exit 0
  3 nine-slice margins match the drawn insets
  Godot reads all 5 palettes x 40 colours exactly, at nearest filtering
  32 string widths match between Godot and bitmap_font

python tools/bitmap_font.py --style snes_rpg      # 4 sheets, 90 glyphs
python tools/ui_chrome.py  --style snes_rpg       # 10/10 chrome pieces
python tools/export_godot.py --style snes_rpg     # exit 0
  3 nine-slice margins match the drawn insets
  Godot reads all 5 palettes x 32 colours exactly, at nearest filtering
  32 string widths match between Godot and bitmap_font
```

Zero BLOCKER lines, either style. Both runs used the real Godot 4.3 binary
(`--headless --import`, then `--script build_all.gd`), not a mock or a
Python-side approximation -- `check_palette_lut_godot` specifically reads the
palette texture back through Godot's own resource loader and TextServer,
which is the whole point of the check (a compression artifact or a filter
setting that Pillow-side checks can't see). `git status` after both runs:
nothing tracked changed (`godot_export/project*/`, `out/ui/font/`, and
`out/ui_snes_rpg/` are all gitignored build/export output, as expected).

**One already-known finding reconfirmed, not rediscovered.** `main` (this
branch's base) still carries `check_font_layout`'s pre-fix, weight-blind
`bitmap_font.measure(text, cap)` call (no `weight=` argument) -- exactly the
bug the still-open, unmerged `font-layout-weight-blind` branch (PR #97)
already found and fixed. It didn't fire in either run above because both
`bitmap_font.py` runs used weight=1, the only weight this codebase's own
shipped pipeline ever builds (Hour 56's own grep confirmed this) -- so
`measure()`'s implicit weight=1 happens to agree with Godot's real, actually-
weight-1 layout. Consistent with PR #97's own description ("never fired in
practice, reproducibly wrong at any non-default font weight"), not a new
data point, and not re-litigated further here.

**Finding: no new live bug.** This is the first time this hourly loop has
run the real Godot round-trip end to end for both styles rather than reading
the check functions or testing a narrower slice of them. All three checks
are correctly style-threaded (ramps/bible/font sizes all resolved per
`--style`, confirmed by the different palette color counts -- 40 for
`cozy_ghibli`, 32 for `snes_rpg` -- both read back correctly through Godot)
and all pass clean against the real, freshly-built, real-Godot-verified
export for both styles. Honest null result; the one real hypothesis chased
this hour (silent-skip as a masked gap) checked out as already-correct
layering once verified against `manifest.py`'s own code, not assumed.

## `tileset.py`'s three checks, run against the real shipped tile atlases -- clean, correctly threaded, no gap

`ui_forge.py`'s `check_icon` was the first candidate this hour: deterministic,
needs no GPU to re-evaluate once a PNG exists. Dead end before it started --
`out/ui/` has zero PNGs on disk in this environment (`manifest.py --check`'s
own "24 declared but not built" warning already says so), and Torch/SDXL are
confirmed unavailable in this session's Python env (Hour 47, reconfirmed
Hour 57), so there is no way to produce fresh ones either. Nothing to test
against; abandoned rather than forced.

`tileset.py` is different: `out/tiles/` (`cozy_ghibli`) and
`out/tiles_snes_rpg/` (`snes_rpg`) both hold real, already-built tile atlases
and `tileset.json` manifests -- genuine, non-GPU-dependent shipped data, a
good candidate for the same "was the real configuration ever tested" audit
`counter`'s `front="x"` bug (Hour 53) came from.

**The three checks, and how they're wired.** `check_lattice(width)` is pure
integer arithmetic (is the lattice step on whole pixels) -- no style
dependency, correctly bare. `check_collapse(fn, variants, width, ramps, ...)`
and `check_manifest_placement(meta, width, ramps, ..., wall_patterns=...)`
both take `ramps` and (for placement) `wall_patterns`, both resolved inside
`build()` from `style.materials`/`style.palette_path` for whichever
`--style` was passed (`tileset.py:901-906`) -- not module-level constants,
not a default bound at import time. This is the style-threading shape Hours
52/55 spent real effort confirming or fixing elsewhere in this codebase; here
it was already correct.

**The one real gap: `check_manifest_placement` only runs behind `--proof`.**
`build()` gates it (`tileset.py:993-1006`) along with the 3x3 tiling proofs
and the room-corner composite -- a plain `tileset.py --style X` (no flag)
never calls it. Grepping every caller in the repo, exactly one place passes
`proof=True`: `concept_ui.py`'s `run_procedural`, wired to a button in a
Gradio-style dev preview app (`concept_ui.py:289`, its own comment explains
why -- "the half of the library that always works" was terminal-only until
this tab existed). `manifest.py --check` never touches `tileset.py` at all
(confirmed: zero references outside a docstring mention), and no pytest file
references `check_manifest_placement`. So in this repo's actual automated
surface (the test suite, `manifest.py --check`), this check never runs --
only a human clicking a specific dev-tool button exercises it.

**That's a real coverage gap, but not the `counter`-shaped bug.** The
`counter` bug was a check silently validating a configuration
(`front="y"`) the real pipeline doesn't ship, while the one it does ship
(`front="x"`) was never touched by any check at any azimuth. Here the
question is different and testable directly: does `check_manifest_placement`
still pass when actually run, today, against the real on-disk atlases, at
the one width (`64px`, `tileset.py`'s own default) this codebase has ever
shipped tiles at -- nothing else calls `tileset.py` with a `--width`
override, so 64px is not an undertested value, it's the only one that
exists.

Ran it directly, both styles, matching exactly what `concept_ui.py`'s button
does:

```
python tools/tileset.py --proof --style cozy_ghibli   # exit 0
python tools/tileset.py --proof --style snes_rpg       # exit 0
```

Both printed `manifest placement: rebuilt from tileset.json alone,
pixel-identical` alongside clean `check_lattice`/`check_collapse` output and
clean 3x3/3-tile tiling proofs for every floor and wall type. No BLOCKER
lines, either style. `git status` after both runs shows nothing tracked
changed (`out/` is gitignored, as expected for build output).

**Finding: no live casualty.** The check is real, correctly threaded, and
currently passing against the actual shipped tile atlases for both styles --
unlike the icon-speckle and `counter` cases, there is no discrepancy between
what's tested and what's shipped to point a fix at. The only defect is
process: a real correctness check (`gates.py` itself lists it as a
deterministic gate, "can a consumer rebuild the room from the published
numbers alone?") is reachable only by manually running `--proof` or clicking
through a dev-tool tab, not by anything CI or the test suite would run. That
is worth naming so a future regression in this specific check doesn't sit
silently unnoticed the way `out/ui/`'s absence sits unnoticed until someone
greps for it -- but it is a coverage note, not a bug to fix, and this hour
ships no code change against it.

## A sweep of the checks this session hadn't touched yet -- one already fixed, the rest genuinely clean

Five files' check suites had never been looked at this session:
`bitmap_font.py` (5 checks), `package_godot.py` (`check_anim_layout`,
`check_palette_lut`), `floorplan.py` (`check_plan`), `palette_swap.py` (4
checks), `fx.py` (`check_loops`). Read each for the two shapes this session
keeps finding -- a hardcoded single azimuth/config tested when the real
pipeline ships several, and a bare call where a real style/palette should
be threaded -- and ran what could be run for real.

**`bitmap_font.py`'s `weight` parameter is not the counter-`front` bug.**
`check()`'s `weight=1` default looked like the same shape as `check_generator_
range`'s untested-parameter gap two hours ago. It isn't: `grep` across
`ui_chrome.py`, `manifest.py` and `package_godot.py` finds no call anywhere
in the shipped pipeline that ever passes a non-default weight -- the game
only ever sets type at weight 1, so testing weight 1 is testing what ships,
not missing a variant. (The genuinely weight-blind bug in this file's own
*layout* functions, `measure`/`wrap`/`fit_cap`, was already found and fixed
on PR #98 -- a different bug, in different functions, correctly scoped
there and not re-litigated here.) `check_render`'s `style` parameter is
already threaded from its own caller, not bare.

**`package_godot.py`'s two checks are pure structure, by construction.**
`check_anim_layout` compares declared rect geometry against a sheet size,
`check_palette_lut` already takes and correctly receives `style_name` from
its caller. Neither has a hardcoded single-config gap.

**`floorplan.py`'s `check_plan` is pure zone-overlap geometry** -- tile
coordinates, window positions, service-run counts. No palette, no camera,
nothing a style or azimuth sweep could expose.

**`fx.py`'s `check_loops` compares a clip's phase-0 and phase-1 vertex
positions** -- motion-loop correctness, not appearance. Same category.

**`palette_swap.py` had already found and fixed the exact bug class this
session hunts, before this session started** -- its own module docstring
records it: every one of the file's four directory traversals inherited a
"default-only blindness" even though `main()` had already threaded
`--style` through the palette math, exactly the bare-call/hardcoded-default
shape this session keeps finding elsewhere, already caught and fixed with
a `sources_for(style)` resolver. Re-verified live rather than trusted:
`python tools/palette_swap.py --all --check --style snes_rpg` -- 468 PNGs,
29 distinct colours, all resolve to a base-palette identity, all 4 variant
tables injective, all 12 sampled assets survive base -> variant -> base
byte-identically. Clean, for real, today.

**Not a task.** No code changed. One already-shipped fix confirmed still
correct under `--style snes_rpg`, five otherwise-untouched check suites
confirmed free of the two bug shapes this session targets.

## A pass over `manifest.py --check`'s remaining bare calls, and `portrait.py`'s fixed azimuth -- both confirmed correct as they are

Two threads this hour, neither turning up a fix, both worth recording so a
future pass does not re-open either.

**Every bare (no-`ramps`) call left in `manifest.py`'s `check()` is bare for
a real reason, not a missed spot.** This session has repeatedly found bare
calls that should have carried `ramps`/`checks` (`check_focal_contrast`,
`check_roundtrip`/`check_transform`/`check_albedo_regression`,
`check_symmetry_claims`'s `measured_symmetry`), all still open on their own
PRs on `main` today. Read every OTHER bare call still in `check()` looking
for one more of the same shape:

- `_c.check_palette_spread()` -- counts *ramp names* (`material(p)[0]` on
  each part's material token) and their share of a roster's parts. Never
  touches an actual RGB value or the `ramps` dict at all -- "neutral" is the
  same string and the same problem whichever style's palette resolves it.
- `_c.check_roster_variety()`, `_c.check_cast_silhouette()`,
  `_c.check_accessory_distinct()` -- all silhouette/shape-only by their own
  docstrings ("the shape-only half of `check_roster_variety`"), comparing
  covered-pixel sets, not colours. `check_accessory_distinct` hardcodes
  `accessory_mat="rose"` for every comparison, which looks like a style leak
  at first read -- it isn't, because the measurement is alpha coverage, not
  hue, and any bindable ramp produces the same silhouette.
- `check_built_rooms()`, `check_stool_occupancy()` (`build_plan.py`) --
  pure geometry: collisions, grounding, seating rotation, occlusion,
  perch-rate. No material lookup anywhere in either function's body.

All five are correctly parameter-free. Confirmed by reading each function's
own body for a `ramps`/palette/colour touch point, not by pattern-matching
the call site -- this is the same distinction "geometry-only, not
style-specific" drew for `check_generator_range`'s `counter` fix two hours
ago, applied here as a check rather than an assumption.

**`portrait.py`'s `check_eyes_visible` uses a fixed `PORTRAIT_AZIMUTH = 90`,
which looked at first glance like the single-azimuth bug class this session
has found repeatedly (`check_buried_detail`, `check_member_thickness`,
`check_eye_legibility`, ...). It isn't, and the module says so directly:**
"A portrait never rotates, so `PORTRAIT_AZIMUTH = 90`: dead [on]" -- a
portrait is a single fixed-angle UI headshot, architecturally never
rendered at a second azimuth, the same category `screen_occlusion`'s fixed
45 deg camera fell into (Hour 49). Confirmed rather than taken on faith:
`grep` for any second call to `render_sprite`/`DimetricCamera` in
`portrait.py` with a different azimuth turns up none -- every portrait
render in this file uses the one constant.

**Also checked, mechanically: does the pile of open PRs need reconciling
again now that #109/#110 exist?** `git merge-tree` against every other open
PR touching `tools/art_review.py`/`tools/assetlib.py` (#83, #87, #93, #95,
#102, #103, #81) -- eight pairwise merges, all clean except the routine
`ART_CRITIQUE.md` doc-append conflict every pair in this pile has. Matches
Hour 48's finding that this pile's PRs insert independent blocks rather than
rewrite shared lines; no new reconciliation burden from this hour's own two
PRs.

**Not a task.** No code changed, nothing to fix -- three separate checks,
three confirmations that the code already does the right thing.

## Checked whether `counter`'s buried-detail bug is a pattern, not a one-off -- it isn't

`counter(front="x")`'s bug (a separate PR, `counter-front-x-buried-detail`)
was `check_generator_range` never exercising a non-default parameter that a
real shipped call site uses. Several other `GENERATORS` entries share that
same shape -- `check_generator_range`'s factory always calls the generator
with only `seed` set, and a handful of these generators take a second
parameter that real code overrides. Worth checking whether front="x" was
one instance of a broader coverage gap or a true one-off.

Found three real, non-default configurations `check_generator_range` never
tests: `basket(fill=...)` (`render_room.py`/`build_plan.py` ship both
`"foliage"` and `"rose"`, never the default `FABRIC`), `chair(cushion=...,
frame=...)` (`furnish.py`'s `chair_metal`/`chair_cushioned` catalog entries,
and `render_room.py`'s cushioned window-bar chairs), and `table_round(top=
...)` (`render_room.py`'s three cafe tables, `"cream"` and `"wood"`, never
the default `WOOD` passed positionally as a no-op). `bench`'s own
`cushion`/`frame` parameters, by contrast, are never overridden anywhere in
this repo's real call sites -- not a candidate, same conclusion either way
without needing to test it.

Measured all three at their real shipped values, at `check_generator_range`'s
own exact span/floor for each generator (15% floor throughout):

```
table_round  top=wood (default)    23.45%
table_round  top=cream (real)      27.23%
chair        cushion=None,frame=wood (default)      40.48%
chair        cushion=None,frame=metal (chair_metal)  40.48%
chair        cushion=rose,frame=wood (real, window)  48.47%
basket       fill=fabric (default)  29.82%
basket       fill=foliage (real)    29.82%
basket       fill=rose (real)       29.82%
```

All eight comfortably clear the 15% floor. **Does not generalize, and the
reason is mechanical, not luck.** `front` in `counter()` changes WHICH AXIS
the detail geometry sits on -- a placement bug, wrong by construction for
one of its two branches. `fill`/`cushion`/`frame`/`top` in `basket`/`chair`/
`table_round` only ever swap one material NAME for another at screen
positions the geometry already varies by seed regardless of which material
is bound there -- `screen_materials` measures whether the resolved material
differs pixel-to-pixel between seeds, and a global material-role swap moves
every seed's output the same way, so it cannot by itself collapse spread the
way a buried, always-identical face can. The bug class the front="x" fix
closed is specifically "an untested parameter changes GEOMETRY," not
"an untested parameter exists" -- confirmed by finding several of the
second kind and none of them mattering.

**Not a task.** No code changed. Doc-only, same branch convention as the
other confirmed-non-generalizing findings this session (`screen_occlusion`,
`check_roster_variety`, `portrait.py`'s accepted limitation). 40-test suite
unaffected (nothing here touches code).

## `check_generator_range`'s single azimuth wasn't the bug; the untested configuration was

This session has repeatedly found generator/asset checks blind to one fixed
`azimuth=45.0` while a real prop ships at all 8. `check_generator_range`
(`art_review.py`) has that exact same default, so it was the obvious next
thing to sweep -- and an 8-azimuth pass over all 24 seeded generators did
flip 5 of them (`bookshelf`, `pastry_case`, `counter`, `fridge_under`,
`wall_art_framed`) from passing at 45 deg to failing at others.

**That result doesn't survive contact with how this pipeline actually
uses azimuth, though.** Every prop here is rendered by `furnish.py` at all
8 real camera azimuths regardless of declared `sym` (`sym` is purely a
`manifest.py` render-*budget* accounting concept -- confirmed by reading
`furnish.py`'s own placement loop, which never consults it), so the naive
"sweep the raw camera azimuth around an unrotated mesh" test looked like
the right shape of question. But the architecture doctrine this session
already established for `screen_occlusion` (azimuth check, Hour 49) applies
here too: **the camera is fixed at 45 deg and objects rotate**, not the
other way round. Re-tested the 5 flips at the one real camera azimuth
(45) crossed with the only rotations this codebase's own placement code
ever actually uses (0/90/180/270, `Layout.scatter`'s `rot_choices`, and the
specific hand-authored rotations in `build_plan.py`): `bookshelf` at its
two real shipped rotations (0, 270, `build_plan.py`'s back-bar shelving)
reads 21.6%/21.4% against its 15% floor -- clean. `pastry_case` and
`fridge_under` are clean at every rotation. `wall_art_framed` isn't placed
anywhere in this repo's real room compositions at all (catalog-only, in
`furnish.py`'s `Recipe` table, never called from `build_plan.py` or
`render_room.py`) -- no live casualty regardless. **Four of five: does not
generalize**, same conclusion as `screen_occlusion` and `check_roster_variety`
before it, for the same architectural reason.

**The fifth, `counter`, is a real, live, currently-shipping bug -- but not
the azimuth-blindness one.** `counter()` takes a `front` parameter ("y" or
"x", which face carries the seed-driven style detail) that `check_generator_range`
never varies -- its `GENERATORS` entry is `lambda A, s: A.counter(seed=s)`,
always the default `front="y"`. `render_room.py`'s window bar run (line 170)
places the real, shipped counter with `front="x"` explicitly -- "the window
bar tiles along y, so its +y face is a joint between two modules and its
front is +x," per the generator's own docstring. That configuration was
never exercised by the check at any azimuth, single or swept.

Measured directly: `front="x"`, 8 seeds, real camera (45 deg), 0.25% screen
spread against the shared 4% floor -- 7 of 8 seeds produce byte-identical
on-screen materials, only seed 8 differs by one pixel's worth. `front="y"`,
same seeds, same azimuth: 7.47%, clean, genuinely varying (drawers, shelf,
beaded styles all show up). Confirmed by eye, not just by the metric --
rendered `screen_materials`' own colour-mapped output at 4x for both
`front="y"` seeds 1/2 (clearly different: plain vs. two drawer lines) and
`front="x"` seeds 1/2 (visually identical, both plain, no drawer lines on
the right face at all).

**Root cause, found by reading `counter()`'s own geometry, not guessed:**
the carcass box is `add_box((0.0, 0.06, base), (1.0, 0.94, top), WOOD)` --
inset on y (0.06-0.94, "so two neighbours never share a reveal," per its own
comment) but spanning the FULL x range (0.0-1.0, "so a run tiles
seamlessly"). The style-detail quad is drawn a fixed 0.9412 proud of
whichever axis is the "front," and 0.9412 sits just past the carcass's own
y1=0.94 boundary -- correct, visible, for `front="y"`. For `front="x"` the
same 0.9412 sits *inside* the carcass's own x-range (which runs to 1.0), not
past it -- the detail quad is drawn 0.06 units inside solid wood, fully
buried by the carcass's own geometry from every camera angle. One shared
constant, two different boundaries it was supposed to clear, correct for
one and silently wrong for the other -- the same shape of bug
`check_buried_detail` exists to catch, just never exercised on this asset's
non-default configuration.

**Fixed at the source, in `assetlib.counter()`:** `face` is now
`0.9412` for `front="y"` and `1.0012` for `front="x"` (the carcass's own
x1=1.0, plus the identical 0.0012 proud-of-surface margin the y case
already used). Verified: `front="x"` spread goes from 0.25% to 8.56% (now
comparable to `front="y"`'s 7.47%, same seeds, same randomly-chosen styles,
now actually visible on screen); rendered and eyeballed the fix directly --
seed 2's drawer lines now show on the right (+x) face exactly as they
already did on the left (+y) face for the equivalent `front="y"` case.
`front="y"`'s own mesh is confirmed byte-identical before/after (hashed
every seed's vertex+material data) -- this is a `front="x"`-only fix.

**Closed the coverage gap too, not just the bug**, matching this session's
own established convention (`check_roundtrip`, `check_albedo_regression`,
and others all got a check-side fix alongside the code-side one): added
`counter_front_x` as its own `GENERATORS` entry, `lambda A, s:
A.counter(seed=s, front="x")`, same 4% floor. Confirmed it actually catches
what it's meant to -- reverted just the `assetlib.py` fix with the new
entry still in place, and it fires exactly as expected (`counter_front_x:
screen spread 0% over 8 seeds`); restored the fix, clean again.

**Geometry-only, not style-specific** -- `counter()`'s mesh construction has
no palette/ramp dependency, so this affects `cozy_ghibli` and `snes_rpg`
identically (verified: 7.47%/8.56% either way, independent of which
style's ramps get bound downstream). Unlike most of this session's findings,
there was no cross-style calibration question to ask here at all.

**Verified end to end.** `manifest.py --check --style cozy_ghibli`: 3 errors
before this branch's own baseline, 2 after -- not from anything this fix
targeted directly, but the already-known, already-documented noise-floor
case (`check_focal_contrast`'s "plan 1, L run," sitting at D -0.001 against
a 0.000 floor, see "Focal detail: resolution-confirmed, not
resolution-invariant" and "A real, already-measured galley finding..."
above) flipped to a pass once the counter's front carried real detail pixels
again -- consistent with that section's own finding that a defect sitting
exactly on a zero floor can flip either way on an unrelated change, not a
deliberate fix, and not claimed as one. The two galley errors (`71451c3`'s
own already-decided-against-fixing finding) are unchanged, as expected --
unrelated topology. `--style snes_rpg`: 10 errors before, 9 after, same
L-run flip, same unrelated 7 character-roster/eye-legibility errors and 2
galley errors untouched. 40-test suite: 40 passed. `check_generator_range()`
and `check_spread_floor_regression()`: both clean before and after.

## Checked whether `manifest.py`'s "accepted limitation, still fires as a blocker" bug generalizes to `portrait.py`'s own accepted `snes_rpg` gap -- it doesn't

`manifest.py --check --style snes_rpg` was, until the previous fix,
reporting 7 findings against `character.py`'s box/prism roster as
build-blocking errors even though NEXT.md's own accepted-limitation
doctrine says that roster doesn't ship for `cylinder_sphere` styles --
the "accepted" framing covered the roster difference, not the noise the
command kept producing every run.

`portrait.py --check --style snes_rpg` carries the identical-looking
accepted-limitation shape: it also builds portraits from `character.py`'s
box/prism `head()`/`hair()`, also fails under `snes_rpg` (`reader`'s left
eye renders 0px against bare skin -- `hair_mat` and `character.EYE` collide
on `snes_rpg`'s more compressed `neutral` ramp), and NEXT.md's own writeup
(PR #24) explicitly accepts it the same way: *"`style_approve.py` doesn't
require `portrait.py` or `manifest.py` to pass, only `character.py` OR
`portrait.py` OR `organic_rig.py` for the character-roster requirement, and
`organic_rig.py`'s entry already satisfies it."* Given the previous section
found that exact style of claim understated in practice, checked whether
this one is too, rather than trusting the prose a second time.

**It holds up.** Three things verified directly, not assumed:

1. `style_approve.py`'s `REQUIRED_PRODUCERS_ANY_OF = ("character.py",
   "portrait.py", "organic_rig.py")` or-logic (`tools/style_approve.py:56-76`)
   is genuinely implemented the way the comment claims -- `current_approved`
   checks `lock.json` for *any* approved, current entry across the three
   named producers, not all three, so `organic_rig.py`'s own passing entry
   really does satisfy the requirement regardless of `portrait.py`'s
   `approved: false` row. Read the code, not just the docstring.
2. `gates.py` (the 62-check deterministic/llm/taste catalog this loop
   already fully audited for wiring, Hour 47) has no aggregate pass/fail
   mode at all -- `--help` shows only `--list` and `--producer`, informational
   commands, so there is no second gate anywhere that could re-block on
   `portrait.py`'s failure independently of `style_approve.py`'s already-
   verified or-logic.
3. `grep -n "portrait" tools/package_godot.py tools/export_godot.py` returns
   nothing at all, for either file. Portraits are not part of the shipped
   export pipeline yet, for ANY style -- not a `snes_rpg`-specific gap, a
   not-yet-integrated feature that applies equally to `cozy_ghibli`. There is
   no path by which a wrong-rig portrait could reach a real build today.

So the two cases look identical from their NEXT.md/ART_CRITIQUE.md prose
alone -- both "accepted because `organic_rig.py` covers it" -- but differ in
one load-bearing way: `manifest.py`'s box/prism checks fed one unconditional
`errs` list with no or-logic at all, so "accepted" was true of the roster
and false of the command's actual behaviour. `portrait.py`'s failure feeds
`style_approve.py`'s real or-gate, correctly implemented, and reaches no
export path either way. The mechanism the "accepted" claim depends on is
present and working here, not merely asserted.

No functional fix shipped, no code changed -- this is a legitimate "checked
whether the previous bug generalizes, and for this sibling case it doesn't,
because the machinery the claim rests on was independently verified to
exist and work" result, same discipline as the ramp-coherence, character-
scale, roster-variety, and screen-occlusion null results already on record.

## Checked whether `screen_occlusion`'s fixed `azimuth=45.0` is the same bug as the sprite checks -- it isn't, and the numbers show exactly why

`Layout.screen_occlusion(azimuth: float = 45.0, share: float = 0.35, depth:
float = 0.8)` has the identical signature shape as every check this loop has
already found and fixed for single-azimuth blindness --
`check_member_thickness`, `check_buried_detail`, `check_cast_silhouette`,
`check_eye_legibility`, `organic_rig`'s eye check. All five of those measure
a *sprite* that genuinely ships at all 8 real rotation azimuths, and were
wrong to only ever check one. `screen_occlusion` looked, from the signature
alone, like the same shape of gap: it is called from `manifest.py` and
`build_plan.py` with no azimuth argument, defaulting to 45.0, and nothing
in the codebase ever calls it at any other angle.

**Tested it before assuming that pattern repeats.** Ran the hand-authored
reference room (`render_room.build_room()`, "six passes of art direction
live in its 48 coordinates" per its own module docstring) through
`screen_occlusion` at all 8 real sprite azimuths:

| azimuth | findings |
|---|---|
| 45 (the default) | **0** |
| 0 | 16 |
| 90 | 12 |
| 135 | 17 |
| 180 | 18 |
| 225 | 9 |
| 270 | 14 |
| 315 | 15 |

That is not a small or ambiguous gap -- the hand-tuned room is completely
clean at exactly one angle and has real, named, double-digit overlaps
(`decor#coats` hiding 99% of `decor#gbasket#0` at az=0, `prop#espresso`
hiding 100% of two cups at az=135, and so on) at every other angle tested.
Ran the same sweep against three `build_plan.generate()`-produced rooms
(seeds 1/2/3, algorithmic placement, not hand-tuned) to check this wasn't an
artifact of one hand-authored scene: all three show the identical shape --
0 findings at 45, 5-13 findings at every other angle (seed 1: 6/7/9/8/12/9/9
across 0/90/135/180/225/270/315; seed 2: 5/7/13/9/5/10/8; seed 3:
6/9/10/7/8/6/13).

**Traced why, rather than stopping at "the numbers look the same shape as a
bug."** `screen_occlusion` is a pure geometry check -- it projects each
placement's world-space bounding box through `DimetricCamera(azimuth)` and
compares 2D screen-space overlap (`tools/layout.py:306-374`). It never
rasterizes a pixel, never touches a ramp or a palette, so the cross-style-
calibration bug class (the OTHER established shape this loop has found,
`check_speckle`/`check_light_direction`) cannot apply to it at all --
there's no rendered image for a style to bias. That leaves only the
single-azimuth question, and the codebase's own architecture doctrine
answers it directly (`README.md`, on the first time this exact mistake
happened with a *different* check): "in an isometric game the camera is
fixed and the *object* rotates." Props and characters rotate -- they ship
sprite sheets covering all 8 real azimuths, which is why checking only one
was a real bug for them. The room itself does not rotate; there is no
camera-pan feature, no per-angle room export, and `build_plan.py`'s own
placement algorithm calls `screen_occlusion(45.0)` internally as a
constraint DURING generation (`tools/build_plan.py:1257`), actively placing
objects to avoid occlusion at that one angle and no other. The three
generated rooms above are clean at 45 not by luck but because the generator
was optimizing for exactly that.

So the sharp 0-vs-double-digit swing across azimuths, which would be
alarming evidence of a coverage gap for a sprite check, is instead exactly
what correct behaviour looks like for a check whose subject only ever
exists at one camera angle: it proves the room was actually validated at
the one view that matters, not that seven other views were silently
skipped. No functional fix shipped, no code changed -- the default is
correct as written. A legitimate "checked whether the pattern generalizes,
and it doesn't, here is the mechanistic and numeric reason" result, same
discipline as the ramp-coherence, character-scale, and roster-variety null
results already on record.

## Checked whether the open-PR pile has a hidden reconciliation burden beyond `check_member_thickness`/`check_buried_detail` -- it doesn't

Two earlier fixes on `member-thickness-ship-scale` (PR #103) each had to be
combined with an independently-opened sibling PR that rewrote the exact same
function body (`check_member_thickness` vs `member-thickness-single-azimuth`,
PR #95; `check_buried_detail` vs `buried-detail-azimuth-coverage`, PR #87).
Both times, merging the two PRs separately would have produced a real git
conflict, because both edited the same lines of the same function. With 26
open PRs against this repo, worth checking whether that was two isolated
incidents or the edge of something bigger waiting to bite whenever these get
merged for real.

**Where else are multiple open PRs touching the same file.** `gh pr diff
<n> --name-only` across all 26 open PRs, excluding the two docs files every
PR touches (`ART_CRITIQUE.md`, sometimes `NEXT.md`), surfaces two more
clusters beyond the already-known `tools/art_review.py` one (which Hour 47
already checked against #103's current diff and found clean):

- `tools/manifest.py`'s `check(man, style)` function -- independently edited
  by seven open PRs: #83 (table-communal-generator-coverage, lines
  ~440-448), #88 (direction-stability-not-wired, ~397-414), #91
  (focal-contrast-style-blind, ~478-507), #92 (ingest-checks-style-blind,
  ~452-495), #93 (symmetry-claims-style-blind, ~346-361), #94
  (roster-fields-style-blind, ~329-386), #101
  (manifest-check-missing-organic-rig, ~427-458). Several of those ranges
  overlap or sit within a few lines of each other -- on the strength of that
  alone, this looked like the same shape of problem as the two already-fixed
  cases.
- `tools/character.py` -- independently edited by three open PRs: #88
  (`check_direction_stability`), #89 (eye-legibility-single-azimuth,
  `check_cast_silhouette`/`check_eye_legibility`), #94
  (`place()`/`main()`).

**Tested the hypothesis instead of trusting the line-number proximity.**
`git merge-tree --write-tree <a> <b>` (read-only, no branch or working-tree
change) against every pairwise combination: 21 pairs among the seven
`manifest.py` branches, 3 pairs among the three `character.py` branches, all
24 pairs run against `origin/<branch>` refs directly. Result: **every single
pair merges `tools/manifest.py` and `tools/character.py` cleanly.** The only
conflict `git merge-tree` reports for any pair is in `ART_CRITIQUE.md` --
expected and uninteresting, since every one of these PRs appends its own
prose section near that file's end; two independent appends to the same
file always textually conflict and take ten seconds to resolve by hand,
which is not the same class of problem as two PRs rewriting the same
function body.

Pairwise-clean doesn't prove a full N-way sequential merge stays clean (an
early merge can shift line numbers under a later one), so went further:
built a disposable local branch off `main` (`_scratch_conflict_test`, never
pushed, deleted immediately after) and ran a real sequential `git merge` of
all seven `manifest.py`-touching branches, one at a time, auto-resolving
only the expected `ART_CRITIQUE.md` conflict at each step (content doesn't
matter for this test) and otherwise letting git merge for real. At every one
of the seven steps, `tools/manifest.py` (and, incidentally,
`tools/art_review.py` and `tools/character.py` where a given branch also
touched them) auto-merged with **zero conflicts**. The resulting file
parses (`ast.parse`) and runs for real: `python tools/manifest.py --check
--style cozy_ghibli` on the fully-combined tree completes in 6m10s, exit
code 0, `3 errors, 16 warnings` -- error count unchanged from `main`'s
baseline (3), warnings risen from `main`'s 8 to 16, consistent with seven
independently-authored new checks each contributing roughly one new warning
line, no crash, no `Finding`/message ever double-counted or malformed.

**Why this differs from the two cases that DID need reconciling, stated
mechanistically rather than just "checked, it's fine":** `check_member_
thickness` and `check_buried_detail` each had two open PRs *rewriting the
same existing lines* -- both changing what the function's body already did.
These seven `manifest.py` PRs each *insert a new, independent block* into a
long linear function without touching any line another PR also touches --
git's three-way merge handles disjoint insertions landing within a few
lines of each other just fine; it only requires manual resolution when two
sides edit the identical lines. Line-range proximity in a diff header is not
the same signal as an actual collision, and this hour's original hypothesis
(guessed from proximity alone, before running `merge-tree`) would have been
wrong if reported without the check.

**No functional fix shipped, no branch touching `tools/manifest.py` or
`tools/character.py` created** -- there was nothing to fix. This is a
verified "checked whether the reconciliation-burden pattern generalizes to
the rest of the open-PR pile, and for these ten PRs it doesn't" result, the
same discipline as Hour 41's `check_speckle`-sibling check and Hour 45/46's
non-generalization findings. Net effect for him: PRs #83, #88, #89, #91,
#92, #93, #94, #101 can be merged in any order without the kind of manual
code reconciliation #95 and #87 needed against #103 -- only the routine
`ART_CRITIQUE.md` append conflict, same as merging any two PRs from this
loop ever will.

## Checked whether `check_cast_silhouette`'s single-azimuth fix generalizes to its material-based sibling `check_roster_variety` -- it doesn't

`check_cast_silhouette`'s own docstring records a real, already-fixed defect:
the shape-only cast-distinctness check used to compare a single fixed
azimuth, and "a pair that separates at 45 and collapses at 0 is a pair that
collapses one frame in eight" -- so it now runs over all 8 real sprite
directions. Its sibling, `check_roster_variety` (the colour-and-shape,
material-based half of the same "are any two characters the same person"
question -- "the character version of `check_generator_range`") still
declares `azimuth: float = 45.0` as a single default and has never been
extended past it. Same file, same purpose family, same author's own lesson
sitting three functions away -- worth checking whether it was ever applied
here.

**Measured directly rather than assumed.** Computed `check_roster_variety`'s
pairwise material spread (`screen_materials` + `_screen_spread`, the same
instrument the check itself uses) across all 8 real ship azimuths for the
real roster (barista + 8 customers) and the real generated-extras call
(`generate_roster(12, seed=1)`, exactly as `manifest.py --check` invokes it).
Every pair, at every azimuth, cleared the 38% floor with room to spare --
tightest real margin 41.9% (`barista`/`artist` at azimuth 270, floor 38%).
Not satisfied with one population: stress-tested 60 generated extras across
5 seeds (`C(60,2)` = 1,770 pairs x 8 azimuths = 14,160 measurements) for any
pair that clears 45 degrees but drops under the floor at another azimuth.
**Zero.**

**Mechanistic reason this check resists the bug class its sibling had,** the
same shape of explanation the ramp-coherence cross-style check earned
earlier this session: `check_cast_silhouette` compares OUTLINE, a thin
boundary that a hat or a limb can fully hide behind at the wrong angle.
`check_roster_variety` compares MATERIAL COVERAGE -- large, mostly-
uncontested blocks of shirt/trousers/hair colour that stay visible, just
partially reshuffled by occlusion, across nearly every azimuth a humanoid
figure is viewed from. The metric that is fragile to viewing angle is the
one built on a thin, easily-occluded feature; the one built on broad colour
regions is not, independent of which specific check it lives in.

Not a bug, and not tuned to make it look that way: the floor (0.38) and the
real margins (42-62%) both predate this check, and the azimuth sweep only
added measurement, no threshold changes. Documented per this session's
standing instruction to record a checked-and-doesn't-generalize result
honestly, the same as the frog-knight case and `check_direction_stability`'s
scale check earlier this session.

## Checked whether `check_member_thickness`'s wrong-scale bug generalizes to `character.py`'s equivalent -- it doesn't

`check_member_thickness`'s fix (this session) found `ROOM_PX_PER_UNIT`
(27.2, "the room framing") was being used as if it were furniture's real
ship scale when `furnish.py`'s per-object `frame_all` framing actually varies
1.2x-4.9x from it. `character.py` has the exact same shape of constant --
`GAME_PX_PER_UNIT = 27.2` ("Room framing resolves 27.2 px per world unit...
a limb or a body narrower than this many pixels there stops reading as a
shape") -- used by `check_direction_stability` with a hardcoded `span=0.95`,
the same pattern that was wrong for furniture. Worth checking whether it is
also wrong here.

**It isn't, and the reason is structural, not luck.** Characters ship
through `animate.build_sheet()`, which calls `fit(spec, clip_specs)` to get
each character's own real per-character span across every pose in every
clip -- `furnish.py`'s `frame_all` equivalent, confirmed by reading the
production path (`build_sheet` is what `package_godot.py` packs, the same
way `frame_all`'s sprite was confirmed to be furniture's real ship path).
Unlike furniture, which ranges from a teacup to a bookshelf, every character
is the same humanoid rig at the same declared height -- so the real per-
character span has almost nowhere to drift.

Measured directly rather than assumed: the real roster (barista + 8
customers) all land within 1-3% of the assumed 0.95 (0.9410 to 0.9745), and
12 generated extras (`generate_roster`, seed 1 -- deliberately the more
parameter-varied population) land within 1-2% (0.9397 to 0.9667). Went one
step further than a span comparison, since a small span difference could
still flip a verdict near the floor: recomputed every character's actual
per-direction pixel width at BOTH the assumed 0.95 and their own real `fit`
span, and diffed the pass/fail call against `MIN_SILHOUETTE_PX` (9) for all
21 characters x 8 directions = 168 checks. **Zero verdicts flip.** The
closest real case to the floor, `student`, measures 10.23px at the assumed
scale -- 1.23px of margin, comfortably wider than the largest span-driven
error observed (about 0.3px).

Not a bug: `check_direction_stability`'s comment already frames this as "the
scale the sprite is actually seen," and for characters specifically, that
claim holds up under measurement the same way it stopped holding up for
furniture. The difference is the object population, not the check's design --
a fixed camera assumption is only as wrong as the size variance of the
things it's assumed for, and humanoid characters have almost none.

## `check_light_direction`'s 4% floor is also cozy_ghibli-calibrated -- and it fails the opposite way `check_speckle` did

An earlier pass here found `check_speckle`'s `MAX_ISOLATED` floor was
calibrated against cozy_ghibli's rendered output alone and drifted under
snes_rpg (two meshes crossed the floor under snes_rpg that passed under
cozy_ghibli on identical geometry). The next pass tested three sibling
`art_review.py` checks for the same vulnerability (`check_ramp_coherence`,
`check_extremes`, `check_grid`) and found none of them shared it, leaving
`check_light_direction` untested on the theory that light direction is "a
rendering-stage constant shared by both styles, not a palette property." That
theory was wrong. Tested directly, on real renders:

Nine real `assetlib.py` props (`counter`, `chair`, `bookshelf`,
`espresso_machine`, `table_round`, `pastry_case`, `grinder`, `register`,
`stool`), each rendered at all 8 azimuths under both styles via the real
`furnish.py` call convention (`frame_all` then `render_sprite`), run directly
through `check_light_direction`:

```
cozy_ghibli: 8/72 frames flagged
snes_rpg:    5/72 frames flagged
```

Most of that gap is one mesh. `table_round` (a real, shipped generator --
`furnish.py`'s `table_2top_round` recipe) flags 4 of 8 azimuths under
cozy_ghibli and 0 of 8 under the byte-identical mesh, camera, and light under
snes_rpg:

```
azimuth   cozy_ghibli dy   snes_rpg dy   floor
 90       +4.06 FLAG       +1.24         2.56px (h*0.04 @ 64px)
180       +4.96 FLAG       +1.90
270       +4.06 FLAG       +1.24
360       +4.96 FLAG       +1.90
 45/135/225/315  (all under floor, both styles)
```

**Mechanism, confirmed by counting bands, not guessed:** at azimuth 90,
cozy_ghibli's ramp gives the render 6 distinct OKLab-L steps; snes_rpg's
gives it 4 (the style's own "fewer shading bands" design intent, working as
designed). The check picks its "lit" set as the top 20% of pixels by L. Under
cozy_ghibli, the brightest step is narrow -- 5.8% of all lit pixels, tightly
isolating the tabletop rim + pedestal-front highlight, which sits low and
left on screen (+dy, -dx). Under snes_rpg, that same brightest step is wide
enough (11.9% of lit pixels) to also absorb the tabletop's whole flat top
face, which is spread evenly across the top half of the sprite -- diluting
the "top 20%" selection toward the object's vertical centre and pulling dy
under the floor. Visually confirmed at 8x scale
(`table_round_dir1_cozy_ghibli.png` / `_snes_rpg.png`, this pass): the same
highlight is visibly present and in the same place in both renders: it is
the *measurement*, not the light, that moves.

**No live casualty, this time by construction rather than by luck:**
`check_light_direction` is the one check in this file whose own docstring
already says "a rough check, hence only a note" -- `NOTE` severity, the
lowest of the three. Confirmed directly: `art_review.py`'s own CLI returns 0
regardless of findings at any severity (`main()`, no exit-code branch on
`BLOCKER`/`WARNING`/`NOTE`), and grepping `gates.py`/`manifest.py` finds
`check_light_direction` cataloged in `gates.py`'s deterministic-check list
with its own docstring as rationale, but never invoked from `manifest.py
--check` or any other gate that turns findings into a build failure. Nothing
currently blocks, silently passes-when-it-shouldn't, or fails-when-it-
shouldn't at a level that stops a build either way -- the only real effect is
that a human running `art_review.py` directly on a cozy_ghibli render gets an
advisory note a snes_rpg render of the same object would not.

Documented rather than redesigned, same discipline as `MAX_ISOLATED`: a
comment above `check_light_direction()` in `art_review.py` now carries this
measurement and names the real fix (weight by the OKLab gap between adjacent
bands instead of a fixed pixel-count percentile) without attempting it in
this pass. **Confirms the bug class from the `check_speckle` finding
generalizes past a single check** -- and shows it can cut in either
direction: `check_speckle`'s floor became *more* likely to fire under
snes_rpg's coarser palette, `check_light_direction`'s became *less* likely
to, because the two checks route the same "fewer bands" property through
different math (colour-identity adjacency vs. percentile-of-lightness
spatial centroid).

## `manifest.py --check` never once called the rig that actually ships for `snes_rpg`

NEXT.md's own PR #23/#24 writeups record, honestly, that `character.py`'s
`CUSTOMERS` roster fails `check_contrast`/`check_waistline` under `snes_rpg`
(elder/reader/regular/writer, the same four names this file's own recent
entries keep re-measuring) and conclude it doesn't matter: *"this specific
roster is cozy_ghibli-specific, and that's fine, because `style_approve.py`
already derives `snes_rpg`'s character-roster evidence from `organic_rig.py`
instead."* That sentence is true of `style_approve.py`. It was never checked
against `manifest.py --check` itself, the command a person actually runs to
sanity the pipeline -- and it isn't true there.

`grep -n "organic_rig" tools/manifest.py` on `main` returns nothing.
`manifest.py`'s `check()` calls seven different `character.py` functions
against the box/prism roster, unconditionally, for every style -- and never
once calls `organic_rig.check_roster`, `check_eyes_visible`, or
`check_direction_stability`, for any style, ever. Concretely, under
`--style snes_rpg`: the four box/prism blockers above are real lines in this
command's own output (confirmed, fresh run: `10 errors` total, includes all
four by name), while `organic_rig.py` -- `style_approve.py`'s own required
evidence for this style, the rig real output actually uses -- contributes
zero lines, pass or fail, because it is never called. A person reading this
command's output has exactly the picture the accepted-limitation note above
warned against: informed in detail about a roster real output does not use,
uninformed about the one it does.

This is the same shape as PR #86 (`check_ui` validating the wrong style's
font) and PR #91-93 (composition/binder/symmetry checks measuring
`cozy_ghibli`'s numbers under every style) -- a check exercising the wrong
asset for the active style -- except here the failure mode is not "wrong
numbers," it's "zero numbers": nothing this command runs would notice if
`organic_rig.py`'s own cast broke tomorrow.

Checked whether `organic_rig.py`'s checks could just be added unconditionally,
the way `character.py`'s already are: no. `organic_rig.build()` indexes rig
dict keys (`head_radius`, `torso_radius`, ...) that only a
`rig.primitive: cylinder_sphere` bible defines --
`organic_rig.check_eyes_visible(style_name="cozy_ghibli")` raises a bare
`KeyError: 'head_radius'`, confirmed directly by calling it. `cozy_ghibli`'s
own `style_bible.yaml` declares `rig.primitive: box_prism`;
`snes_rpg`'s declares `cylinder_sphere` (`grep -A2 "^rig:"` on both bibles).
So the dispatch has to be conditional on that field, and nothing in the
codebase reads it programmatically today -- `style_approve.py`'s own
`REQUIRED_PRODUCERS_ANY_OF` comment explains the distinction in prose but the
actual mechanism there is "any of three producers has an approved lock
entry," which never needed to branch on `primitive` in code.

Fixed: `manifest.py`'s `check()` now reads `active.rig.get("primitive")` and,
only when it is `"cylinder_sphere"`, calls `organic_rig.check_roster`,
`check_eyes_visible`, and `check_direction_stability` against `active.name`,
folding their messages into the same `errs` list every other character check
already uses. `cozy_ghibli` (`box_prism`) skips the block entirely, so the
new code path never executes there and cannot regress it.

Verified, not assumed: `manifest.py --check --style cozy_ghibli` before and
after this change is line-for-line identical (`3 errors, 9 warnings`, same
messages). `manifest.py --check --style snes_rpg` before and after is
identical too (`10 errors, 8 warnings`, same messages) -- `organic_rig.py`'s
own cast is currently clean (confirmed separately: `check_roster`,
`check_eyes_visible`, and `check_direction_stability` each return zero
findings against `snes_rpg` today), so the new block adds real coverage
without adding noise. Proved the coverage is real, not cosmetic, by
injecting a deliberate defect -- monkeypatched one `organic_rig.ROSTER`
entry's hair colour to exactly match its skin colour (zero contrast by
construction) and re-ran `check()`: a new line appeared,
`ERROR scout: hair 'skin+1' is 0.000 from skin (need 0.13) -- head reads as
one lump`, `10 errors` became `11`. `main`'s `manifest.py` would report
`10 errors` either way -- silent to a real regression in the rig that ships.
40-test suite passes.

## Follow-up: the fix above added the coverage that was missing, but left the noise it had already diagnosed running

The section above adds `organic_rig`'s three checks for `cylinder_sphere`
styles and is careful to note, in its own words, that the pre-existing
box/prism checks "kept reporting on a roster real output never uses." That
sentence was left as an observation, not acted on: the nine checks above it
in `manifest.py`'s `check()` (`check_palette_spread`, `check_contrast`,
`check_waistline`, `check_eye_legibility`, `check_spec_coverage`, the three
generated-extras checks, `check_roster_variety`, `check_cast_silhouette`,
`check_accessory_distinct`) still ran unconditionally for every style,
still fed `errs` (build-blocking), and still fired against `character.py`'s
own `ROSTER`/`CUSTOMERS` -- a cast confirmed to share zero names with
`organic_rig.ROSTER` (`elder`/`reader`/`regular`/`writer`/... vs
`scout`/`archivist`/`drifter`/`smith`/...), the independently-authored roster
that is the one this style actually ships.

That is precisely NEXT.md's own PR #23/#24 "accepted limitation": *"this
specific roster is cozy_ghibli-specific, and that's fine, because
`style_approve.py` already derives `snes_rpg`'s character-roster evidence
from `organic_rig.py` instead."* The word "accepted" describes the roster
difference, not the noise -- and `manifest.py --check --style snes_rpg`
reported that noise as build-blocking every single run, for a cast that has
never shipped as `snes_rpg` art and, on the codebase's own current design,
never will.

**Measured before touching anything.** Fresh `manifest.py --check` on both
styles, on this branch, before this commit:

| style | errors | breakdown |
|---|---|---|
| cozy_ghibli | 3 | (unrelated to this section) |
| snes_rpg | **10** | 4 already-documented box/prism blockers (elder hair/skin, reader/regular/writer waistline) **+ 3 not previously named in this file**: `check_eye_legibility` failing at skin tones `skin-2`/`skin-3`/`skin-4` (0.147 against a 0.15 floor) -- the box/prism block's own eye-visibility check, also firing on a cast that doesn't ship, also never mentioned as part of the "4 blockers" this repo's own memory of itself had settled on. Plus 3 unrelated composition errors (galley/L-run, PR #77's already-accepted finding). |

The 3-skin-tone eye-legibility failures are a real addition to the record,
not a restatement: every prior mention of this limitation (this file, NEXT.md,
this session's own running notes) named exactly 4 box/prism blockers. There
were 7.

**Fix:** wrapped the nine box/prism checks in `if active.rig.get("primitive")
!= "cylinder_sphere":`, the exact mirror of the `== "cylinder_sphere"` gate
the section above already added for `organic_rig`. `box_prism` styles (today:
`cozy_ghibli`) run every one of these checks exactly as before -- the branch
is never taken for them, so there is no way for it to regress that style.

**Verified, both directions, full runs, not `--only` slices:**

| | cozy_ghibli | snes_rpg |
|---|---|---|
| before | 3 errors, 9 warnings | 10 errors, 8 warnings |
| after | 3 errors, 9 warnings (byte-identical) | **3 errors**, 8 warnings |

`snes_rpg` dropped by exactly the 7 box/prism findings named above; the 3
composition errors and all 8 warnings (occlusion, `plant_hanging`, the
`ui_snes_rpg` not-built notice) are untouched, character for character.
`cozy_ghibli` is unchanged to the line. 40-test suite passes.

This does not touch `organic_rig.py`'s own detection or its checks (both
added by the section above, unmodified here) -- it only stops a second,
non-shipping producer's failures from being reported as if they blocked the
style that does ship. Left on this same branch/PR rather than a new one,
since it directly completes the reconciliation that PR's own write-up had
already diagnosed but not finished.

## The entire prop library ships without the texture treatment rooms and characters get

"Surface grain" (this file, above) is documented as "the largest single
change" to this project's rendering -- world-space, anisotropic, per-material
tonal noise that breaks up flat blockout surfaces, calibrated hardest on
`wood` (0.85 of a ramp step, the largest amplitude in `GRAIN_BY_RAMP`) because
wood holds the largest unbroken flat areas. `render_room.py`, `animate.py`
and `preview_characters.py` all call `mesh.rasterize()` directly with
`grain=1.0, ramps=ramps`. `render_batch.render_sprite()` -- the function
`furnish.py` renders the *entire prop library* through, per that same
function's own comment two paragraphs up about a different, already-fixed
gap ("this call site was missed, which matters because `furnish.py` renders
the entire prop library through it") -- never exposed `grain` or `wear` at
all. Every chair, bookshelf, counter and shelf in this game ships with
perfectly flat wood, while every room background and every character does
not.

Found by a second AST scan, complementary to the unused-parameter one that
found the last two hours' fixes: this time scanning for a function that
calls a sibling sharing a parameter name without forwarding it. Most of the
18 hits were namesake collisions with unrelated meanings (`target` means
"output resolution" in `render_sprite` and "world-space camera aim point" in
`rasterize` -- a false positive, not a bug). This one wasn't a false
positive in the usual sense either -- `render_sprite` didn't even expose
`grain`, so there was no parameter to accidentally drop; it's the same
"sibling call site missed" shape the function's own nearby comment already
names, in a place nobody had looked for a second instance of it.

**Measured, not assumed -- and the first surprise was the metric itself.**
Comparing the *distinct colour count* of a `bookshelf`/`chair` render with
`grain=0` vs `grain=1` at `furnish.py`'s real `--target 64 --factor 4`
showed zero difference (13 vs 13, 7 vs 7) -- which would have wrongly closed
this as a non-issue. Grain doesn't add new colours; it moves EXISTING ramp
steps around spatially. Comparing per-pixel identity instead: 246 of 4096
final pixels differ on `bookshelf` alone. The raw pre-quantization lambert
buffer differs on 22,982 of 65,536 pixels (max deviation 0.11, comfortably
under the one-ramp-step cap `GRAIN_BY_RAMP` documents). Visually confirmed
at 8x scale across three real props (`bookshelf`, `chair`, `counter`, seed
1, azimuth 45, real furnish.py resolution): every flat wood surface gains
visible mottled texture with grain on, most clearly on the bookshelf's side
panel and the counter's front face -- reading exactly like the "wood grain"
effect this file already documents for rooms, because it *is* that effect,
applied to a surface category that was never wired to receive it.

**Fixed narrowly: the capability, not the default.** `render_sprite` gains
`grain: float = 0.0, wear=None`, forwarded to `rasterize` (`ramps` only
passed through when `grain > 0`, matching `rasterize`'s own gate). Default
stays 0.0 -- `render_sprite` has callers `render_room.py`/`animate.py`/
`preview_characters.py` don't: `character.py`, `organic_rig.py` and
`portrait.py` all call it twice per eye-legibility check to diff a `plain`
head against an `eyed` one pixel-for-pixel, and grain is world-space noise
that would put false positives into that diff. A default flip belongs to
whichever call site opts in deliberately, not to this shared function.

**Zero regression, confirmed.** Hashed `render_sprite`'s real pixel output
for 3 props x 2 azimuths, pre- and post-fix (`git stash`), byte-identical on
every one -- no existing caller passes `grain`, so none of them moved.
`character.py`'s own `main()` (0 blockers) and `organic_rig.py`'s (silhouette
stability holds, roster clears contrast/waistline) both re-run clean.
40-test suite passes.

**Left open, deliberately: whether `furnish.py` should actually opt in.**
That is a whole-prop-library visual change -- every already-shipped sprite
would look different -- and this session's own standing discipline is not to
make that call unilaterally (see the albedo-floor recalibration and the
per-style roster-override scoping, both deferred for the same reason). The
capability is real, measured, and visually positive on every sample tried;
turning it on for the shipped library is a decision for a human looking at
the images, not a line this PR changes. Branch
`render-sprite-grain-wear-unwired`, new (unrelated to any other open PR's
subject) -- left unmerged.

## `isorender.py`'s own projection assertion ignored the tolerance it declared

Same discovery method as last hour's `bitmap_font` finding (an AST scan for
function parameters never read in their own body), a different hit:
`verify_projection(tol: float = 1e-6)` -- the function `isorender.py`'s own
module docstring points to as proof the 2:1 dimetric projection claim
"asserts it rather than trusting the arithmetic" -- accepted a `tol`
argument and then asserted against a hardcoded `1e-6` literal instead of the
parameter with that name. Every real call (`prove_shading.py`; `tileset.py`,
twice) uses the default, so this never diverged in the shipped pipeline --
same "no live casualty" shape as this session's font-weight findings, not a
hypothetical one.

**Confirmed the bug directly, not just by reading it.** The camera's own
trig currently measures a deviation of ~5.6e-17 from the true 0.5 ratio
(floating-point precision, not a real defect). Calling
`verify_projection(tol=1e-20)` -- deliberately far stricter than that real
deviation, which should fail if `tol` were honored -- **passed silently**,
because the hardcoded `1e-6` was checked instead of the requested `1e-20`.
That is airtight proof the parameter was decorative: a request for
sub-attometer precision was silently downgraded to micron-scale precision
with no error.

**Fixed by checking against `tol` instead of the literal.** One-line change:
`assert abs(ratio - 0.5) < tol`. Verified default-call behavior is
byte-identical (`verify_projection()` still returns the exact same
`0.49999999999999994`, same as before the fix); `tol=1e-20` now correctly
raises; a genuinely loose `tol=1e-3` still passes, as it always did. Real
callers re-run end to end post-fix: `prove_shading.py` ("projection check:
0.500000000000 (exactly 2:1)") and `tileset.py --style cozy_ghibli` (both
call sites, floor and wall tiling, unchanged output). 40-test suite passes.

Branch `isorender-verify-projection-tol-blind`, new (unrelated to any other
open PR's subject) -- left unmerged.

## `bitmap_font.py`'s own layout helpers were weight-blind, same bug class as the Godot font-layout check, one file over

The font-layout check `export_godot.py` fixed elsewhere this session
(`check_font_layout`, see that section) was one symptom of a wider habit
inside `bitmap_font.py` itself: `raster`/`glyph_box`/`ink_of`/`draw` all
correctly thread `weight` through to the actual rasterizer, but `measure` --
the function every width-based layout decision in this file goes through --
never took a `weight` argument at all, and silently rasterized at
`glyph_box`'s own default of 1 no matter what was actually being measured.
Found by scanning every function in `tools/*.py` for a parameter that is
never referenced in its own body (the same shape as `fridge_under`/`tip_jar`'s
ignored `seed`, from earlier this session): `fit_cap`'s own `weight`
parameter never reached `measure`, so a caller asking "does this fit at
weight 2" silently got weight 1's answer.

That alone would be a dead-parameter finding with no live path -- nothing in
this repo calls `fit_cap` today (`ui_chrome.py` mentions it only in a
comment). But the same defect reaches further than `fit_cap`: `render_line`
-- the function `bitmap_font.py`'s own `--sample`/`--weight` CLI flags call
directly -- sizes its output canvas with `measure(text, cap, tracking)`
(weight-blind) and then draws the real ink with `draw(..., weight=weight)`
(weight-correct). At weight 1 the two numbers agree by construction. At any
other weight they don't, and `ui_chrome.Canvas.put`'s own bounds check
(`0 <= x < self.w`) silently drops whatever ink falls outside the
under-sized canvas -- so the rightmost several pixels of a bold sample line
are rasterized and then thrown away, with no error and no BLOCKER, reachable
by running the tool exactly as its own module docstring demonstrates
(`python tools/bitmap_font.py --sample "..." --weight 2`).

**Measured, not assumed.** Built real weight-2 renders via `render_line`
itself (the actual production function, not an approximation) across five
sample strings from the real UI copy and all four shipped cap sizes, and
compared the canvas width it produced against the real ink extent `ink_of`
reports at that same weight:

    text              cap   canvas_w (pre-fix)   real ink needs   pixels silently dropped
    Flat White         7           47                  57                   30
    Flat White        13          100                 110                   46
    0123456789         7           50                  60                   44
    0123456789        13          109                 119                   55
    Order #42          7           45                  54                   35
    Order #42         13           97                 106                   43
    gjpqy               7           26                  31                   11
    gjpqy              13           53                  58                    6

Every sample at every cap loses ink at weight 2, 6-55 real pixels depending
on string length and cap size -- the trailing 1-2 characters' rightmost
strokes, consistently. Visually confirmed at 8x nearest-neighbour scale
(`out/font_sample.png`, `--sample "Flat White" --cap 13 --weight 2`): the
pre-fix render's closing "e" is visibly sheared off; the same render with
the fix applied shows a complete "White".

`fit_cap` has the identical shape without needing Canvas at all: at
`weight=2` it kept returning the exact same cap `weight=1` would have
picked, for every sample and width tried, because it was calling the same
weight-blind `measure`. Checked against the REAL weight-2 ink extent
(`ink_of`, which does honor weight): the caps it picked routinely didn't
fit -- e.g. `'Flat White'` at a 100px box, `fit_cap` said cap 13 fit at
either weight, but cap 13's real weight-2 ink is 108px, 8px over the box it
was declared to fit.

**Fixed at the root, not per-caller.** `measure` gained a keyword-only
`weight: int = 1` parameter, threaded to `glyph_box` exactly the way
`ink_of`/`raster` already do. `wrap` gained the same, threaded into its own
`measure` calls, since a wrap decision has the identical shape (a width
comparison against text at a specific weight). `fit_cap` and `render_line`
already accepted `weight` in their own signatures -- both just stopped
dropping it, now passing it into `measure`. `block`'s `**kw`-forwarded
`weight` is threaded into its own `wrap` call; its separate
`glyph_box("A", cap)` call for line-height math is deliberately left at
weight 1 -- checked directly (`glyph_box('A', cap, 1)` vs `glyph_box('A',
cap, 2)` across all four shipped caps), height and baseline are identical at
every weight, only advance changes, so that call was never the bug.

**Zero regression at weight 1** (the only weight this repo has ever shipped,
same fact PR #97's own finding established): captured `measure`, `wrap`,
`fit_cap`, `render_line` and `check`'s output across 7 sample strings, 4
call patterns and all 4 shipped cap sizes before and after the fix (70
comparisons, `render_line`'s own rendered pixels hashed rather than
eyeballed) -- identical on every one. `bitmap_font.py --check` still reports
legible caps 7-20 and `SIZES = (7, 9, 11, 13)` unchanged. 40-test suite
passes.

Left as `weight=1` default everywhere, same as every other function in this
file -- this is a coverage-gap fix, not a behavior change, for the same
reason PR #97's was: nothing in the shipped pipeline calls any of these
functions with a non-default weight today. The gap was real regardless,
silently corrupting output the moment anything did, and the discovery method
(scan every function for a parameter never read in its own body) is
general -- worth re-running periodically rather than trusting this pass
caught everything of this shape once. Branch `bitmap-font-weight-blind-layout`,
new (unrelated to PR #97's `export_godot.py` subject, though the same root
cause) -- left unmerged.

---

## `export_godot.py`'s font check recomputes a number the build already got right, weight-blind

`NEXT.md`'s own migration-order notes name `export_godot.py` as one of two
files "not yet looked at closely enough to know whether it carries the same
accepted-but-ignored risk" as the `--style`-accepted-but-unthreaded bug
class PRs #23-#25 fixed elsewhere (`art_review.py`, the other file that
notes name, was already audited and found clean in PR #31). Looked at it
closely this pass.

`check_font_layout` (`tools/export_godot.py`) runs Godot's own TextServer
headless against the exported `.tres` font and compares each string's real
layout width to `bitmap_font.measure(text, cap)` -- the "bitmap_font says"
side of the check. `measure()` recomputes every glyph's advance from
scratch via `glyph_box(ch, cap)`, which defaults its `weight` parameter to
1 and never receives anything else, no matter what weight the font actually
being checked was built at. Nothing in this repo passes `--weight` other
than 1 today (checked: no call site in `package_godot.py`/`manifest.py`,
no `weight` key in either style's `bible.yaml`), so this has never actually
diverged -- but it is a real, reproducible latent gap, the same shape as
this session's other "coverage gap, no live casualty" fixes, not a
hypothetical one.

Measured directly, not assumed: built the font twice via `bitmap_font.py`'s
own real `atlas()`/`raster()` functions, once at `--weight 1` (today's only
real setting) and once at `--weight 2`, then compared `measure()`'s
recomputed width against each glyph's REAL advance (the one `atlas()`
already baked into `font.json` at build time, the same number `stage_font()`
passes through unchanged into the `.tres` Godot actually loads) across all
four cap sizes and all eight of `verify_font.gd`'s own real sample strings:

    weight=1 (today's only real build):  0 divergences / 32 comparisons
    weight=2 (hypothetical, same code):  32 divergences / 32 comparisons,
                                          `measure()` under-reporting every
                                          string by 4-10px depending on cap

At weight 1 the two computations agree byte-for-byte on every sample --
confirming this has never fired a false pass or false fail under any build
this repo has actually shipped. At weight 2 `measure()` is wrong on all 32,
because a bolder stroke genuinely does push a glyph's rightmost ink pixel
further right (`raster()`'s own comment: "the advance is the ink's own
right edge... MEASURED rather than declared"), and `measure()`'s hardcoded
weight=1 recomputation cannot see that.

**Fixed by not recomputing at all.** `atlas()` already writes each glyph's
real, weight-correct advance into `font.json`'s `glyphs` dict, which
`package_godot.stage_font()` already passes through unchanged into `build`.
`check_font_layout` now sums `build["font"]["sizes"][cap]["glyphs"][ch]
["advance"]` for each character instead of calling `bitmap_font.measure()`
-- reading the number that was actually shipped rather than re-deriving an
approximation of it, one fewer place for the check's own reference value to
drift from the real build. `bitmap_font`'s only remaining role in this
check was the now-removed import; nothing else in `export_godot.py`
changed. Verified: the 0-divergence / 32-divergence numbers above were
produced by the exact comparison the patched function now performs
in-process (font built fresh into a scratch `--out`, not the tracked
`out/ui/font/`, and removed after); the check's OTHER half -- whether
Godot's TextServer agrees with what `atlas()` baked in -- is untouched,
same `verify_font.gd` script, same subprocess call. 40-test suite passes.

Branch `font-layout-weight-blind`, new (unrelated to any other open PR's
subject) -- left unmerged.

### Addendum: the same proof, run against the live Godot engine, not just in-process

The verification above was explicitly scoped to an isolated in-process
comparison -- `bitmap_font.atlas()`/`measure()` called directly in Python,
never touching a running Godot instance -- because building the complete
asset library locally to run the full `export_godot.py main()` pipeline
(stage -> headless Godot `--import` -> headless Godot `--script
build_all.gd` -> round-trip checks) was judged too expensive to justify at
the time. That gap is closed here.

`NEXT.md`'s own historical notes (an earlier, already-landed PR) record a
cheap way to get real, non-fabricated content into an otherwise-empty local
`out/` tree without building the whole library: `furnish.py --only <ids>`.
Used it to build two real props (`grinder_burr`, `chair_wood`), then built a
real `--weight 2` font via `bitmap_font.py --style cozy_ghibli --weight 2`
(the same non-default weight the isolated proof above used), then ran the
complete, unmodified `export_godot.py` pipeline with this branch's fix
applied -- real staging, a real headless Godot 4.3 `--import` pass, a real
headless `--script build_all.gd` build, and the real round-trip check. Full
result:

    -- round-trip check --
      Godot reads all 5 palettes x 40 colours exactly, at nearest filtering
      32 string widths match between Godot and bitmap_font

All 32 comparisons pass against live Godot TextServer output, at the exact
weight (2) where the pre-fix code was proven wrong on all 32 in isolation.

That alone doesn't prove the fix was load-bearing for this run, though --
it's also what a no-op check would report. So the contrast was run too:
captured the same real `VERIFY_FONT_JSON:` output this pipeline run produced
(via Godot's `verify_font.gd`, re-invoked directly, no need to re-run the
import/build_all steps since their artifacts already existed) and replayed
the OLD pre-fix comparison logic (`bitmap_font.measure(text, cap)`, the
weight-blind recompute) against it in Python:

    32/32 flagged as false BLOCKERs by the pre-fix code, against this
    exact same real Godot output -- 4-10px under-reported per string,
    matching the isolated proof's numbers exactly (e.g. cap 13
    '0123456789': Godot 117px vs OLD recompute 107px, diff 10px)

So on the identical real engine output: the fix reports a clean pass, the
pre-fix code reports 32 false positives. This upgrades the finding from "an
isolated Python-only proof, believed to generalize to the real pipeline" to
"proven against live Godot engine output, with the old code's failure mode
reproduced on that same output as the control." No further code change --
`check_font_layout` is unchanged from the fix above.

Local build state used for this: `furnish.py --only grinder_burr
chair_wood` and the weight=2 font build wrote into the real (gitignored,
never committed) `out/sprites/`, `out/ui/font/`, and
`godot_export/project/resources/` locations rather than a scratch dir,
because `export_godot.py`'s full pipeline doesn't support redirecting
output elsewhere. The weight=2 test font was removed afterward to restore
pre-test state; the two furnished props were left (harmless additions to an
already-populated local sprite cache, not tracked by git either way).

## The key-light-drift check's remaining hypothesis, tested and closed

"The key-light-drift check was right about the drift and wrong about the
cause" (above) left one door open: the dominant-ramp restriction it tried
was an *approximation* of per-pixel material identity, and the section
ended on "a fix that actually separates the two signals needs the raw
per-pixel material id `rasterize()` already computes and `review_queue.py`
never receives -- it only ever sees the final quantized PNG." That reads as
an untried lever, exactly the shape this file exists to chase down, so it
was chased down this pass.

The buffer isn't actually missing. `render_batch.render_sprite()` computes
it already -- `mat_small`, the real per-face material token from
`mesh.rasterize()` carried through the same modal downsample the final PNG
gets -- and just never returns it, because its only consumer today is
`apply_outline()` inside the same function. Pulled it out (calling
`rasterize()` and `downsample_modal()` again, outside `render_sprite`, on
the same 8 real ship azimuths via `frame_all()` for exact parity with what
`factory.py` actually renders) and restricted each frame's brightest-pixel
pool to the asset's own cross-frame-stable body material -- the token with
the largest *minimum* per-frame area share across all 8 directions, not a
per-frame guess, which is a more principled selector than "dominant ramp"
was.

Verified the harness first: re-measuring the *unrestricted* spread through
this real pipeline (real `_bound.obj` meshes from `out/mesh/`, real
`frame_all()` span/centre fit, real `render_sprite()`, target 64 / factor 4,
`cozy_ghibli` palette -- not a hand-rolled approximation) reproduced the
already-published numbers exactly: kettle 3.5x4.5, candle 5.1x3.9. That
match is what makes the restricted numbers below trustworthy rather than an
artefact of a different measurement space.

    object          unrestricted (pass/fail)   body-material-restricted
    kettle          3.5x4.5   [ok]              12.1x7.5   [fail]
    candle          5.1x3.9   [ok]               7.8x14.5  [fail]
    french_press    3.2x4.9   [ok]                6.4x15.3 [fail]
    teapot         11.5x5.7   [fail, x only]      6.6x18.7 [fail, worse]
    cutting_board    9.2x9.7  [fail]             29.3x32.5 [fail, worse]
    picture_frame  10.6x21.1  [fail]              28.4x28.3 [fail, worse]
    wall_clock     21.1x17.7  [fail]              17.9x14.1 [fail, ~same]

Strictly worse than the already-rejected dominant-ramp attempt, on every
axis that attempt was measured against. All three round-object controls
broke, not just candle. Neither case dominant-ramp partly helped (teapot,
cutting_board) improved -- both got noisier instead. Getting the real
buffer did not unlock the fix the docstring deferred to it.

The reason is in `ingest.py`'s `bind_colour()`: a material token is a ramp
name plus a lightness-step offset from that ramp's own middle step --
`"neutral"` vs `"neutral-1"` vs `"neutral+2"` are three different tokens,
not one. "This frame's dominant material" is therefore finer-grained than
"this frame's dominant ramp" was, and measured min per-frame share for the
chosen body-material token ranged 3%-43% across these seven objects -- even
a visually-uniform round surface like a kettle's body is split across
several step tokens by ordinary toon shading, so restricting the pool to
one throws away most of the very population (a broad tonal gradient across
the whole curved surface) that keeps a round object's centroid estimate
stable in the first place. This is the same failure shape as the
dominant-ramp attempt, not a different one that a finer key happens to
share -- both are "restrict the brightest-pixel pool by material identity,"
and any granularity of that idea, tested twice now, costs more stability on
round objects than it buys on flat ones.

**Verdict: does not generalize, and the specific hope this file's own
prior entry left open is now closed, not just untried.** `check_direction_set`
is unchanged -- still fires on 19 of 22, still correctly scoped to the three
round objects as a regression guard, per the existing writeup. The
docstring's "doesn't have that buffer today" line is updated in place to
"has the buffer, tried it, it's worse" so a future pass doesn't re-derive
and re-try the same idea a third time. No code behavior changed; this is a
documentation-only commit, verified only by the numbers above (there is no
image to inspect -- nothing about the check's shipped behavior or any
sprite's pixels moved).

## `check_member_thickness`'s own sibling in `review_library()` had the exact
## single-azimuth gap its neighbour was already fixed for

`review_library()` runs two mesh checks over every `assetlib.py` generator:
`check_buried_detail` (fixed for exactly this shape in an earlier pass, its
own docstring stating the fix in plain terms -- "pass all eight for anything
that ships as a rotating sprite") and, one call above it in the same
function, `check_member_thickness` -- still hardcoded to `DimetricCamera
(45.0)`, never touched. Every asset it checks IS one of those rotating
sprites: `furnish.build_one` renders and saves 8 real PNGs per asset,
unconditionally, at `45 + k*45` for `k in range(8)` -- `assets.yaml`'s `sym`
field only trims the render BUDGET accounting elsewhere, it does not change
which raw angles `furnish.py` actually generates a file for. So a flat panel
that goes edge-on at some other angle ships a real, saved sprite this check
never looked at.

**Swept all 55 library assets across the real 8-azimuth set, not assumed.**
One already-known failure (`plant_hanging`, previously reported at 35% from
its single 45-degree sample) reproduces, now at a slightly different
worst-case number from a different azimuth (38% at 135). Four assets that
pass cleanly at 45 degrees fail hard at 180 (their own worst angle, matching
this file's established "the default is the best case, not a blind spot
hiding a pass" shape from the `table_communal` azimuth sweep): `menu_board`
and `wall_sign` (both declared `2fold` in `assets.yaml`) and `wall_art_framed`
(also `2fold`) all measure **100%** thin at 180 degrees -- the panel is
rendered edge-on, ~1px wide, a vertical sliver where a flat rectangle should
be. `sandwich_board` (`chalkboard_easel`, declared `sym: none` -- genuinely
ships all 8 distinct frames, no symmetry-based ambiguity possible) measures
**23%**, over the 20% floor, at the same 180-degree angle -- and this exact
asset is already NAMED in the check's own docstring as a documented finding
("a sandwich board built from zero-thickness quads measured 3px... a
standing plane seen near edge-on collapses to a line"), just measured at the
one angle (45) where that collapse happens to be mild.

**Visually confirmed, not just numerically.** Rendered all four at all 8 real
ship azimuths (`proof/member_thickness_edge_on.png`): six of eight frames
show a normal, legible flat panel for every asset; the 180-degree frame (and,
for the three `2fold` panels, the 0-degree frame too, matching their declared
symmetry) shows a thin diagonal line or a razor-thin sliver -- unmistakably a
"stray wire," exactly the failure class `MAX_THIN_SHARE` exists to catch.

**A methodology choice that would have silently shipped a check that still
couldn't see the defect, caught before writing the fix, not after.** The
first design pooled every requested azimuth's runs into one combined share
(sum thin pixels / sum total pixels across all 8 views) -- the natural
generalization of the single-view formula. Ran it against the real library
before committing to it: **every one of the four edge-on cases dropped back
under the 20% floor**, because a fully edge-on view contributes almost no
pixels at all, so its 100%-thin run barely moves a ratio dominated by the
other seven, mostly-solid views. Pooling was the wrong lever for exactly the
same reason a global roster recolour was the wrong lever in an earlier hour's
finding: it touches a different, less-targeted quantity (an ACROSS-VIEW
average) than what the check actually needs to answer ("does ANY real,
shipped frame of this asset read as wire"). Fixed by judging each requested
azimuth independently and reporting the worst one, not the pooled average --
confirmed this is what actually surfaces all four cases before shipping it.

**Verified, both styles, zero regression on everything already passing.**
`check_member_thickness(mesh, name, floor_px, azimuths=(45.0,))` -- signature
extended, default unchanged, so any other caller is unaffected by
construction (`review_library` is its only caller in this repo). Full
55-asset library swept at the real 8-azimuth set: exactly the five findings
above, nothing else newly fails, nothing that previously failed newly
passes. `manifest.py --check --style cozy_ghibli`: 3 errors (unchanged), 8
warnings -> 12 (four new, additive, non-blocking -- this check has always
reported through `warns`, not `errs`). `--style snes_rpg`: 10 errors
(unchanged, this check is pure mesh geometry with no palette involved --
same 4 new warnings, same numbers, confirming style-independence rather
than assuming it). 40-test suite passes unchanged.

**Left unfixed on purpose, same discipline as `check_buried_detail`'s own
four findings.** This is a coverage-gap fix, not a geometry fix -- the four
panels' actual thinness at 180 degrees is real, new information, not
something this branch claims to have solved. A menu board, a wall sign and a
framed art print are all meant to hang flush against a wall; whether the
game ever actually presents a player with their 180-degree view (backing
onto the wall) is a placement-and-camera question this check cannot answer
and this hour did not investigate -- recorded here rather than assumed
either way.

## `character.py`'s "accepted, not-fixed-by-design" roster finding (PR #23)
## reproduces, and had a real, untried third lever

`NEXT.md`'s PR #23 write-up, later re-confirmed unchanged by PR #27's
`animate.py --style` work, documents `character.py --style snes_rpg` failing
`check_contrast` on `elder` (hair 0.088 from skin, need 0.13) and
`check_waistline` on `reader`/`regular`/`writer` (shirt-vs-trousers 0.022 /
0.040 / 0.080, need 0.085) -- and explicitly frames this as accepted, not
fixed: "fixing the roster's colours risks breaking `cozy_ghibli`'s clean
pass, and fixing the check floors would defeat their purpose." Re-ran both
checks against the current checkout to confirm the claim before touching
anything -- it reproduces exactly, same four names, same numbers:

```
elder: hair 'cream+1' is 0.088 from skin (need 0.13) -- head reads as one lump
[waist] reader: shirt 'foliage' and trousers 'wood' are 0.022 apart in value (need 0.085)
[waist] regular: shirt 'rose' and trousers 'wood' are 0.040 apart in value (need 0.085)
[waist] writer: shirt 'sky' and trousers 'wood' are 0.080 apart in value (need 0.085)
```

**Root cause, confirmed by dumping both palettes' ramp L-values, not
guessed:** `snes_rpg`'s palette is deliberately more saturated and lower-band
than `cozy_ghibli`'s, and its `wood` ramp's mid-value dropped from L=0.600
(cozy) to L=0.559 (snes) while `foliage`/`rose`/`sky` all compressed toward
it from above (foliage 0.696->0.581, rose 0.716->0.600, sky 0.700->0.639) --
four ramps that were comfortably spread apart under `cozy_ghibli`'s own
lightness range converge under `snes_rpg`'s. `elder`'s skin tone (L=0.861 in
snes_rpg, vs 0.700 in cozy) also happens to land almost inside its own
`cream` hair ramp's range (0.681-0.949) under `snes_rpg` specifically, which
is why `cream+1` -- fine under cozy -- reads as one lump there.

**Both checks are pure OKLab-L comparisons on literal ramp+offset tokens
(`ramps[ramp][index]`), not on rendered pixels.** Unlike PR #80/#81's UI/3D
speckle, there is no downstream pixel/deterministic post-process available
here at all -- the check never looks at a rendered pixel, so a despeckle-
shaped fix is structurally not on the table for this one. The two levers PR
#23 considered (recolour the shared roster globally, or loosen the check
floor) are the only two that touch a *global* variable. Neither was checked
against a **third, narrower lever**: override the specific failing fields
**per style**, leaving `cozy_ghibli`'s own assignments completely untouched.

**Verified empirically, not assumed:**

- `character.ROSTER_OVERRIDES["snes_rpg"]` patches `elder.hair_mat` ->
  `"cream-3"` (same ramp, three steps darker -> gap 0.180, clears 0.13) and
  `reader`/`regular`/`writer`'s `trousers` -> `"wood-1"` (one step darker ->
  gaps 0.170/0.189/0.228, all clear 0.085). All four picked by scanning the
  ramps' own step tables for a legal offset that clears the floor, not by
  guessing once and hoping.
- `character.py --style snes_rpg`: 4 blockers -> **0 blockers**.
  `character.py --style cozy_ghibli`: 0 blockers before and after (the
  override table has no `cozy_ghibli` entry, so `roster_for("cozy_ghibli",
  ...)` returns the input list unchanged -- structurally unreachable, not
  just re-tested).
- `check_palette_spread` and `check_roster_variety` (screen-space pairwise
  distinctness, which involves an actual render pass) both still pass on the
  overridden `snes_rpg` roster -- the fix doesn't trade one failing check for
  another.
- **Zero-regression, proven with real renders, not inferred:** sha256 of
  `elder`/`reader`/`regular`/`writer`/`barista` rendered under
  `--style cozy_ghibli` (azimuth 0, `render_batch.render_sprite`) is
  byte-identical before and after this change (`git stash` A/B, all 5
  hashes match). The 40-test suite passes unchanged.
- **Visually confirmed, both fields:** `elder`'s hair goes from pale ivory
  that visually blends into the hairline at the forehead to a clearly
  separated tan/khaki that still reads as an appropriate light/grey elderly
  hair colour. `reader`/`regular`/`writer`'s trousers, rendered seated
  (`character.build(spec, seated=True)`, azimuth 45, where the leg is
  actually exposed on screen) go from a value that nearly matches the shirt
  to a visibly darker, distinct step -- looked at directly, not inferred from
  the numbers alone.

**Shipped for real, not just at check-time:** the override was threaded into
the actual rendering path, not only the check. `animate.py`'s own roster
construction (`[C.BARISTA] + C.CUSTOMERS`, the literal list that becomes
every `snes_rpg` sprite sheet) now resolves through `character.roster_for
(args.style, ...)` too -- otherwise the check would pass while the shipped
sprites still carried the uncorrected colours, the exact "a check that
cannot fail for the thing it claims to certify" anti-pattern this file's own
discipline rule already names. `portrait.py`'s `check`/`build`/`demo` got the
same threading, since a portrait bust is a dead-on closeup where `elder`'s
hair/skin collision is at least as visible as on the 46px sprite.

**A fourth, live call site was found only by re-running `manifest.py --check`
after the fix, not by grepping ahead of time.** An earlier pass this hour
grepped for `check_eyes_visible`/`check_determinism`/`check_palette_exact`
(`portrait.py`'s OWN checks) across `manifest.py` and found no match, which
correctly ruled those out. But `manifest.py` separately calls
`character.check_contrast`/`check_waistline`/`check_palette_spread` directly
on the bare `C.ROSTER` (added by PR #78, "fix-manifest-missing-contrast-
check" -- itself a fix for this exact call being absent, landed before this
session's window and not visible in a name-only grep for `portrait.py`'s
functions). Re-running `manifest.py --check --style snes_rpg` after the
`character.py`/`animate.py`/`portrait.py` changes above still showed the
same four errors, unchanged, 10 total -- the override existed but this call
site never used it. Threaded `character.roster_for(active.name)` into
`manifest.py`'s three call sites (`check_contrast`, `check_waistline`,
`check_palette_spread`; `check_eye_legibility`/`check_spec_coverage` measure
different fields, untouched). `manifest.py --check --style snes_rpg`:
10 errors -> 6, the remaining six being the separate, pre-existing skin-tone
eye-legibility and room-composition findings this fix does not touch.
`--style cozy_ghibli`: 3 errors, 8 warnings, unchanged before and after. The
40-test suite passes after this addition too. Recorded here as a reminder
that a name-grep proves absence only at the moment it's run -- rerunning the
actual check after a fix is what caught the site the grep couldn't see.

**This is a scoped patch, not the general fix, and that's stated rather than
hidden.** The general fix is giving `CharacterSpec`'s colour fields a
per-style `materials:` role instead of a literal ramp token -- the same
deferred `assetlib.py`/`character.py` import-order generalization this
file's earlier `wall_panel()` finding (PR #29) already pointed at, still not
attempted here. `ROSTER_OVERRIDES` is a small, explicit, four-entry table
that only ever applies to `snes_rpg` and only to the four fields it names;
it does not generalize to a fifth style without a fifth hand-picked entry.
That's an honest limitation of this fix, not a claim that the deeper
generalization is unnecessary.

**Net result:** the "accepted, not-fixed-by-design" framing in PR #23/NEXT.md
was half right -- the two levers it named really don't work without a
tradeoff -- but the finding as a whole does not hold: a real, safe, verified
third lever existed and was never tried. `portrait.py --check --style
snes_rpg` still reports the separate, pre-existing `reader` eye-occlusion
blocker from PR #24 (a hair-geometry issue, unrelated to this fix, left
exactly as-is -- not touched, not hidden).

## `check_symmetry_claims`'s own `measured_symmetry` was bare -- a closed blind spot, not a defect

Same sweep as the `check_focal_contrast` and `ingest.py` findings above:
`manifest.py`'s FX symmetry cross-check, `check_symmetry_claims(fx_declared,
fx_meshes)`, called `measured_symmetry(mesh)` bare -- no `ramps` -- despite
that function already accepting one. `measured_symmetry` doesn't compare
silhouettes; its own docstring is explicit that a first version comparing
the raw lambert buffer was wrong and it compares "the quantized sprite" --
full colour, after `shade_toon`'s ramp-step quantization -- for exact
pixel-equality across rotations. That is a structurally palette-dependent
comparison: two materials that quantize to visually indistinguishable bins
under one palette's specific ramp spacing need not under another's, so a
mesh could measure MORE symmetric than it truly is under one style and
fewer under another, purely from where ramp boundaries happen to fall.

Measured across all 8 FX generators (`fx.FX`), both palettes' own real
ramps, at the exact `0.25` progress value `manifest.py` samples:

| effect | cozy | snes |
|---|---|---|
| fx_steam_cup | 1 | 1 |
| fx_steam_machine | 8 | 8 |
| fx_pour_coffee | 1 | 1 |
| fx_pour_milk | 1 | 1 |
| fx_door_swing | 4 | 4 |
| fx_ceiling_fan | 2 | 2 |
| fx_rain_window | 8 | 8 |
| fx_order_ready | 1 | 1 |

Identical on every single one. No live casualty today -- the same shape as
PR #88's `check_direction_stability` wiring fix, not PR #91/#92's real
surfaced defects. Threaded `ramps` through `check_symmetry_claims` and
`manifest.py`'s call site anyway: it is a real structural gap (a future FX
generator or a future style's ramp spacing could trip it, and nothing here
would have caught that before this fix, regardless of which `--style` was
being checked), it is fully safe to close (proven by the table above, not
assumed), and it costs nothing -- `manifest.py --check --style cozy_ghibli`
and `--style snes_rpg` are both byte-identical before and after, 10/3 errors
respectively, unchanged. 40-test unittest suite passes unchanged.

Fixed in `tools/art_review.py` (`check_symmetry_claims`) and
`tools/manifest.py` (its call site) -- branch `symmetry-claims-style-blind`,
left unmerged.

## `ingest.py`'s own binder checks were bare too -- one clean fix, one real finding too big to rush

Same sweep as `check_focal_contrast` (the section above this one on the branch
that fix shipped on): `manifest.py`'s comment on the neighbouring UI check
already documents fixing "accepted the flag but measured cozy_ghibli's
colours the whole time" (PR #23/#24/#25) for the character checks. Three call
sites lower, `check_roundtrip`, `check_transform` and `check_albedo_regression`
-- the stage 1-3 mesh-binder validation, `tools/ingest.py` -- were still
called bare.

**`check_roundtrip`: real coverage gap, no live casualty.** It exhaustively
walks every step of the ACTIVE palette's own bindable ramps and asserts each
one binds back to itself. Bare, it only ever walked cozy_ghibli's 37 steps,
regardless of `--style` -- a future snes_rpg-specific binder defect could
not have shown up here no matter which style was being checked. Threaded
`ramps` through; both styles currently read clean (`[]`), so this closes a
real gap with nothing hiding behind it today -- same shape as PR #88's
`check_direction_stability` fix.

**`check_transform`: a bug inside the fix for the bug.** This function
already accepted `ramps` and used it correctly to write its adversarial
fixture's MTL -- but then handed that file to its own nested `ingest(obj,
up="y", height=want_h)` call BARE, so the binder that actually validates the
round trip re-derived cozy_ghibli's palette internally regardless of what
`ramps` this function itself received. Threading `ramps` only into
`manifest.py`'s call site, without also fixing this nested call, would have
made things WORSE than the status quo: under `--style snes_rpg` it would
have written the fixture's colours in snes_rpg's own RGB and then asked the
binder to match them against cozy_ghibli's ramps instead -- a guaranteed,
entirely artificial mismatch with nothing to do with a real defect. Caught
before shipping that by reading what the nested call actually does, not just
threading a parameter and trusting the signature. Fixed both layers.

**`check_albedo_regression`: the fixture bug was real, and fixing it
surfaced something bigger.** One of its two `rebind_case` fixtures was a
hardcoded literal, `(169, 113, 81)` -- "a colour already living on the
library's own middle step," per its own comment, and specifically
cozy_ghibli's `wood` ramp's middle step, by coincidence of which palette
this file was authored against. Bare, this never showed: `ramps` was always
cozy_ghibli's own file either way. Fixed to derive the test colour from the
ACTIVE palette instead (`ramps["wood"][len(ramps["wood"]) // 2]`, matching
`check_roundtrip`'s own "middle step is the canonical, named one"
convention) -- but snes_rpg's own derived wood-mid colour, `(173, 88, 72)`,
STILL trips `check_albedo_centre` as "too dark." That is not a fixture bug
any more; it is `check_albedo_centre`'s own `ALBEDO_L_FLOOR`/`ALBEDO_L_CEIL`
constants (0.596-0.845), which were measured once, empirically, against
"every one of the thirty meshes in assetlib" under cozy_ghibli's palette
specifically, and never re-derived for snes_rpg.

Measured across the same 10-asset sample `check_roundtrip` already builds,
median OKLab L per mesh, cozy_ghibli vs snes_rpg's own real palette:

| asset     | cozy  | snes  |
|-----------|-------|-------|
| floor     | 0.500 | 0.411 |
| counter   | 0.600 | 0.559 |
| chair     | 0.600 | 0.559 |
| table     | 0.600 | 0.559 |
| plant     | 0.696 | 0.581 |
| bookshelf | 0.600 | 0.559 |
| crate     | 0.600 | 0.559 |
| menu      | 0.600 | 0.559 |
| espresso  | 0.596 | 0.479 |
| pastry    | 0.716 | 0.639 |

`espresso` is the prop that DEFINES cozy_ghibli's own floor at 0.596 (its
docstring cites it as "the weakest known-good"). Under snes_rpg's own real
colours it reads 0.479 -- and 8 of these 10 sampled assets fall entirely
below the floor. This is not one unlucky material: `check_transform`'s own
adversarial fixture (a real library chair, not a synthetic colour) trips the
exact same warning once its nested `ingest()` call is properly threaded --
"bound albedo median L 0.559 is too dark" -- confirming this from a second,
independent, real-asset path, not just the regression test's synthetic one.

If `check_albedo_centre` were ever actually exercised on a real snes_rpg
mesh in production -- nothing has yet; GPU reconstruction is style-agnostic
and could reach snes_rpg any time -- it would very likely reject nearly
every correctly-authored, on-palette snes_rpg prop as "too dark," a
systematic false-positive blocker for that style's own ingestion path, not
a rare edge case.

**Left open, on purpose, not manufactured into a rushed fix:** recalibrating
`ALBEDO_L_FLOOR`/`ALBEDO_L_CEIL` per style needs the same empirical
discipline that produced the cozy_ghibli numbers in the first place -- a
real measurement across that style's own authored asset range, not a number
picked to make one fixture pass. That is a separate, larger pass. Shipped
today: `check_roundtrip` and `check_transform` are fully fixed and threaded
in `manifest.py`; `check_albedo_regression`'s fixture no longer hardcodes a
cozy_ghibli-specific literal, but its `manifest.py` call site is
deliberately left bare until the floor/ceiling question above is actually
resolved, with a comment pointing here. `check_transform`'s fix is shipped
anyway, even though it now surfaces the same real finding via a real chair
asset (`manifest.py --check --style snes_rpg` gains one new ERROR from
this) -- the nested-`ingest()` bug it fixes is real and independent of the
floor/ceiling question, and hiding a real defect to avoid an uncomfortable
but honest new error would be the wrong trade, the same call this session
made for `table_communal` (PR #83) and the L-run/galley/island composition
findings (PR #91).

Fixed in `tools/ingest.py` (`check_transform`, `check_albedo_regression`)
and `tools/manifest.py` (all three call sites) -- branch
`ingest-checks-style-blind`, left unmerged. `manifest.py --check --style
cozy_ghibli` is byte-identical before and after; the 40-test unittest suite
passes unchanged.

---

## The albedo floor's deferred recalibration is harder than it looked, and for a reason that predates snes_rpg entirely

Came back to the "separate, larger pass" left open above with time actually
budgeted for it, expecting to run the same measurement discipline that
produced `ALBEDO_L_FLOOR`/`ALBEDO_L_CEIL` once for `cozy_ghibli` and once
more for `snes_rpg`. It surfaced something the deferred write-up didn't
anticipate: the reference corpus that discipline runs against has already
moved, for the DEFAULT style too, not just the new one.

`ALBEDO_L_FLOOR`'s own comment says the bracket comes from "every one of the
thirty meshes in `assetlib`." Counted fresh with `review_library()`'s own
filter (the same one `check_member_thickness`/`check_buried_detail` sweep
the library with): 55, not 30. `assetlib.py` grew after the floor was set
and nobody re-measured. Re-running the measurement against today's full 55
under `cozy_ghibli` -- the style this floor is supposedly already correct
for -- finds two real outliers already outside 0.596-0.845:

    mesh            cozy_ghibli L   snes_rpg L
    bean_hopper          0.500         0.411
    book_stack            0.969         0.949

`bean_hopper` is not a mis-authored prop -- three stacked prisms of `wood-1`
(a step darker than the `wood` ramp's own middle) are the coffee beans
themselves, the majority of its visible surface, a deliberately dark object.
`book_stack`/`sugar_caddy`/`tip_jar`/`table_clutter` cluster the light end
the same legitimate way. Neither is a defect; both are outside the
documented bracket regardless of which style's palette resolves them.

That reframes the deferred snes_rpg number, and makes it harder, not just
later. Widening `ALBEDO_L_FLOOR` to legitimately admit `bean_hopper` under
snes_rpg's own ramps needs a floor near 0.41 -- and 0.408 is the exact
median L `delight()`'s own docstring cites as the motivating bug this check
exists to catch: the pre-fix teapot regression, "a near-black blob with the
right silhouette." A floor loose enough to admit every legitimately dark
authored prop is a floor that can no longer tell a legitimately dark prop
from an undelit reconstruction -- the two things this check is asked to do
(fit the real library's range; still catch the bug it was built for) are
close enough to genuinely conflict. That is not a snes_rpg-specific problem
-- the same tension exists for `cozy_ghibli`'s own numbers today, snes_rpg's
darker palette just makes the low end of it worse (bean_hopper 0.500 to
0.411, a full 0.089 closer to the 0.408 regression value).

**Verdict: still correctly left open, now for a sharper, verified reason.**
This is not "the recalibration hasn't happened yet" -- it's "a single global
median-L threshold may be the wrong shape for what this check is trying to
distinguish, independent of which style's number gets picked," which is a
bigger question than either style's own floor/ceiling and shouldn't be
answered by picking a number under time pressure. Nothing changed in
`ingest.py`'s checked-in behaviour -- `ALBEDO_L_FLOOR`/`ALBEDO_L_CEIL` are
unmoved, `check_albedo_centre` is unmoved, and (confirmed by direct grep)
neither is ever actually invoked against `assetlib.py`'s own authored
meshes in any live path -- only inside `ingest()` itself and inside
`check_albedo_regression`'s synthetic fixture, so today's finding has no
live consequence, the same as the snes_rpg finding it extends. The 55-mesh
sweep and its numbers are recorded here, plus a matching comment in
`tools/ingest.py` next to the constants themselves, so a future pass starts
from "the corpus moved and the floor's own tolerance is already tight
against the regression it guards" instead of re-discovering both facts from
zero. Doc-only follow-up commit on branch `ingest-checks-style-blind`
(same branch, directly extends this PR's own deferred finding) -- 40-test
suite passes, `manifest.py --check` unchanged both styles (nothing wired to
this measurement in either direction).

## The narrower question inside the deferred one had an answer, and a live bug behind it

The write-up above correctly left the wide question open -- what should a
single global `ALBEDO_L_FLOOR`/`CEIL` even mean once outliers like
`bean_hopper` sit closer to the 0.408 defect value than to either style's
own typical range. It also, correctly, never asked the narrower question
underneath it: not "where should the outlier-inclusive envelope sit" but
"do `cozy_ghibli`'s existing constants already encode a *method*, one that
could be re-run per style without touching the outlier question at all."

They do. `ALBEDO_L_FLOOR` 0.596, `ALBEDO_L_TARGET` 0.600, `ALBEDO_L_CEIL`
0.845 are, to the thousandth, the OKLab-L middle step of `neutral`, `wood`
and `cream` respectively -- not a hand-picked bracket, a description of
where this palette's three most common material ramps sit. Applying the
identical derivation to `snes_rpg`'s own ramps:

    ramp      cozy_ghibli mid   snes_rpg mid
    neutral        0.5961           0.4786
    wood           0.5998           0.5592
    cream          0.8454           0.8604

This is the "typical family" reading, not the "outlier envelope" one --
`bean_hopper`'s 0.411 stays outside `snes_rpg`'s new 0.479 floor exactly as
it already sits outside `cozy_ghibli`'s 0.596 floor today, so the tension
documented above between "fit the library" and "still catch the regression"
is neither widened nor resolved by this fix, just left exactly where it
was. What the per-style mid values give instead is real: `check_albedo_centre`
and its two style-blind neighbours in this file were failing snes_rpg on
their own reference fixtures, not on any of the 55-mesh outliers.

Confirmed both were live before this fix, called directly with each style's
own ramps:

    check_albedo_regression(ramps=snes_ramps):
      "regression: check_albedo_centre fired on wood-mid (173, 88, 72),
       a colour the active palette authors directly -- false positive"

    check_transform(ramps=snes_ramps):
      "unexpected warning: bound albedo median L 0.559 is too dark; every
       authored prop lands in 0.596-0.845. A reconstructed colour field
       carries the concept image's lighting and has to be de-lit before
       binding, or the renderer shades it twice."

The second one is the more serious of the two: it isn't a synthetic
fixture complaining about itself, it's `check_transform`'s real chair
fixture -- correctly transformed, correctly bound, real geometry -- failing
its own unrelated geometric assertions because `ingest()`'s internal
`check_albedo_centre` call, called with no style context, measured the
chair's real 0.559 median L against `cozy_ghibli`'s floor and rejected it.
A geometry check failing for a colour reason is exactly the shape this
session has been hunting all along: one lever (widening the global floor,
already tried and correctly rejected above) tested against a check that
was actually measuring something else (which style's ramps produced the
colour being judged).

The fix threads the already-built, previously entirely unused
`Style.checks` override (`tools/style.py`'s own docstring anticipated this
exact case: "a new style earns its own [floor], once it has real renders to
measure rather than a guess") through `ingest.py`'s `check_albedo_centre`,
`bind_vertex_colours`, `ingest()`, `check_albedo_regression` and
`check_transform`, and through `manifest.py`'s two call sites --
`check_albedo_regression()` was still bare even after this PR's first
commit wired `check_transform`'s `ramps`, which is why only the chair bug,
not the wood-mid one, would have shown up in a full `--check` run before
this fix. `styles/snes_rpg/bible.yaml` now carries
`albedo_l_floor: 0.479`, `albedo_l_ceil: 0.860`, `albedo_l_target: 0.559`;
`cozy_ghibli`'s `checks: {}` stays empty, so its behaviour is provably
unchanged, not just assumed so.

Verified, not assumed, on this branch (`ingest-checks-style-blind`):
stashed the fix to capture a true "before" -- `check_albedo_regression`/
`check_transform` reproduce both messages above exactly, for `snes_rpg`
only. Restored the fix -- both return `[]` for both styles, and
`cozy_ghibli`'s `check_albedo_regression`/`check_transform` output is
identical before and after (`checks={}` falls back to the exact same
globals). `check_albedo_regression`'s own internal defect fixtures --
the near-black-blob regression case and the uniform 0.408 case -- still
report `[]` for both styles, meaning `delight()`'s own defect-catching
behaviour is untouched, not loosened. `manifest.py --check --style
cozy_ghibli`: 3 errors, 9 warnings, matching this branch's pre-fix baseline
exactly (byte-identical). `manifest.py --check --style snes_rpg`: 10
errors, 8 warnings, zero of them `ingest:`-prefixed -- the chair-fixture
bug is gone from the real pipeline, not just the isolated call; the 10
remaining errors are the pre-existing box/prism character-roster and
composition findings this branch doesn't carry Hour 50's separate fix for,
unrelated to albedo and out of scope here. 40-test suite: 40 passed.
Follow-up commit on branch `ingest-checks-style-blind` (same branch,
directly completes this PR's own deferred subject).

## `check_focal_contrast` was grading every style's room against cozy_ghibli's palette

The L-run detail-floor investigation above ("The detail floor at 40 plans")
tried two levers on the same rendered pixels -- back-wall dressing
structure, shelf count -- and closed both without explaining the L-run
concentration, concluding "the floor is real... the failing rooms are a
consistent, repeatable topology-skewed population." That conclusion was
correct for what it tested, but everything it tested shared a lever neither
version of the check ever varied: which palette the room was rendered in.

`manifest.py --check --style <name>` resolves `ramps` once from the active
style (`tools/manifest.py`, the block starting "Resolved once against the
active style, not cozy_ghibli always") and threads it through
`check_contrast`, `check_waistline`, `check_eye_legibility`,
`check_spec_coverage` and `generate_roster` -- the fix for the PR #23/#24/#25
bug class. `check_built_rooms`, `check_focal_contrast` and
`check_stool_occupancy`, three call sites lower in the same `try` block,
were still called bare. Two of those three don't care --
`check_built_rooms` reads `collisions()`/`grounded()`/
`seating_faces_tables()`/`screen_occlusion()`, and `check_stool_occupancy`
counts items by name prefix; neither reads a pixel, confirmed by
fingerprinting `build()`'s own output (vert/face/item counts and every
item's position) across three repeated calls on the same plan before ruling
this out rather than assuming it from the function names -- fully
deterministic, so palette genuinely cannot move either verdict.

`check_focal_contrast` is the one that does read pixels -- it renders the
whole frame and measures brightness/contrast/detail lead over the counter --
and its own `render()` call, inside a nested `read_room()`, never received
`ramps` either. `render()` has the identical `ramps or load_palette()`
fallback that `character.py`'s `_palette()` has, so every focal-contrast
reading this check has ever produced, under any `--style`, was against
cozy_ghibli's colours. `tools/build_plan.py --focal-scan`, the manual sibling
of this same instrument, had the same gap for a more direct reason: its
`main()` already resolves `ramps` from `--style` for every other mode on
that parser, but `--focal-scan` returns before that block runs, so the flag
existed on the parser and was simply never read on that path.

**Real before/after**, from `manifest.py --check --style snes_rpg` itself,
not a standalone script (a standalone script threading `ramps` only into
`render()` and not into `build()` gives a THIRD, wrong, answer -- see the
methodology note below):

Before (bug present, cozy_ghibli's render used for both styles):
```
ERROR  composition: plan 1 (L run): counter carries -0.001 detail against
       its room (floor +0.000) -- the busiest thing in frame is not the
       counter
ERROR  composition: plan 8 (galley): counter is only -0.012 brighter than
       its room (floor +0.015) -- no centre
ERROR  composition: plan 8 (galley): counter carries -0.019 detail against
       its room (floor +0.000) -- the busiest thing in frame is not the
       counter
10 errors, 8 warnings
```

After (fixed, snes_rpg's own palette used):
```
ERROR  composition: plan 1 (L run): counter is +0.001 in contrast against
       its room (floor +0.030) -- the periphery has as much to look at
ERROR  composition: plan 3 (island): counter is +0.000 in contrast against
       its room (floor +0.030) -- the periphery has as much to look at
ERROR  composition: plan 8 (galley): counter is only -0.008 brighter than
       its room (floor +0.015) -- no centre
ERROR  composition: plan 8 (galley): counter carries -0.017 detail against
       its room (floor +0.000) -- the busiest thing in frame is not the
       counter
11 errors, 8 warnings
```

`cozy_ghibli`'s own `manifest.py --check` output is byte-identical before
and after (the fix only changes what a NON-default `--style` sees), and the
40-test unittest suite passes unchanged.

Three distinct shapes in one fix, not one:

- **Plan 1 (L run) changed failure reason, not verdict.** Under
  cozy_ghibli's own render it fails DETAIL (-0.001, resolution-confirmed at
  -0.005 @480). Under snes_rpg's own render, properly built with
  `ramps=snes_rpg` (not just re-coloured), it passes detail (+0.004) but
  fails CONTRAST instead (+0.001 against a 0.030 floor). Before the fix,
  `--style snes_rpg` reported cozy_ghibli's detail failure text and numbers
  for this room -- a real error, for the wrong reason, in a room whose own
  actual defect is a different one.
- **Plan 3 (island) was entirely invisible under snes_rpg before the fix.**
  It renders cleanly under cozy_ghibli's own palette (no error, any style,
  before or after), so the bug's cozy_ghibli-blind render also happened to
  pass for this room, and the check reported nothing. snes_rpg's own render
  fails contrast (+0.000 against 0.030) -- a real, previously entirely
  unmeasured defect specific to that style's palette on this room.
- **Plan 8 (galley) is a real defect under both palettes, numbers only.** It
  fails brightness and detail under cozy_ghibli's own render (-0.012/-0.019)
  and under snes_rpg's own render (-0.008/-0.017, both less severe but both
  still below floor, both resolution-confirmed). The bug didn't hide this
  one or invent it -- cozy_ghibli's numbers were reported for `--style
  snes_rpg` too, close enough in sign and rough magnitude that nothing here
  looked obviously wrong from the error text alone.

**Methodology note, caught before it shipped a wrong finding:** an initial
standalone verification script called `build(plan)` bare and threaded
`ramps` only into the `render()` call, i.e. re-coloured a cozy_ghibli-BUILT
room instead of building a genuine snes_rpg one. `_people()` ->
`generate_roster(n, seed, ramps)` uses the palette during generation, not
just for final colour, so a different `ramps` at `build()` time can change
which roster gets placed and where -- a re-coloured cozy_ghibli room is not
the same room as an actually-built snes_rpg one. That script reported plan
1 passing cleanly under snes_rpg (+0.078 contrast, comfortably over floor);
the real, properly-threaded check reports +0.001, failing. `render()` itself
was confirmed deterministic (three repeated calls on one `Layout`, identical
to the millipixel) before trusting either number, which is what surfaced the
`build()`-argument difference as the actual cause rather than leaving
render-randomness as an open, unresolved doubt. The shipped fix threads
`ramps` into both `build()` and `render()`, matching `main()`'s own already-
correct pattern for its default render path.

Fixed in `tools/build_plan.py` (`check_focal_contrast`, `_focal_scan`,
`main`) and `tools/manifest.py` (the `check_focal_contrast` call site) --
branch `focal-contrast-style-blind`, left unmerged.

## `organic_rig.py`'s own `check_eyes_visible` had the same single-azimuth shape as `character.py`'s

Third and fourth hour running this same audit against a `check_*` function
that renders a figure to test eye legibility: `check_generator_range`
(Hour 20), `check_direction_stability` (Hour 21), `check_eye_legibility`
(Hour 22), and now `organic_rig.py`'s own `check_eyes_visible` -- a
different file, the `snes_rpg`-only cylinder/sphere rig's equivalent of
`character.py`'s check, built independently but with the identical blind
spot: one hardcoded azimuth (90, not 45 this time), never varied.

**Swept all 8 azimuths across the 4-member `ROSTER`.** Unlike `character.
py`'s version of this sweep (this file, "`check_eye_legibility` only ever
rendered azimuth 45"), the occlusion split here is clean and MEMBER-
independent rather than tone-dependent -- every one of 0/180/225/270/315
reads 0-2px for every roster member, consistently, no exceptions. A side or
back view genuinely does not show this rig's face at all; that is correct,
not a defect, and there is no ambiguous middle set to leave out this time.

45, 90 and 135 all show real, comfortably nonzero eye pixels for every
member. But 90 -- the one angle ever checked -- turned out to be this
check's own best case by a wide margin:

    member      az=45 (near eye)   az=90 (both eyes)   az=135 (near eye)
    scout             8                 18 / 18               6
    archivist          9                20 / 20               9
    drifter             4                20 / 20               8
    smith               5                20 / 20               7

`drifter`'s near eye at 45 measures 4px against the 3px floor -- a genuine,
if narrow, near-miss invisible to the only angle this check ever rendered.
Visually confirmed: an upscaled render at 45 shows only a faint dark sliver
past the head's silhouette where 90 shows two clearly legible eye squares.

**Fix.** `check_eyes_visible` gained an `azimuths` parameter, defaulting to
`EYES_VISIBLE_AZIMUTHS = (45.0, 90.0, 135.0)` instead of the bare `90.0` it
always rendered.

**Verified no regression.** Nothing in the safe three-azimuth set actually
fails at the real 3px floor -- this closes a coverage gap and surfaces a
narrow near-miss, it does not expose a live defect, the same shape Hour
21's `check_direction_stability` fix took. Old single-azimuth call
(`azimuths=(90.0,)`) still returns the exact pre-fix message set (zero).
Proved the wiring has teeth rather than trusting the diff: temporarily
raised `MIN_EYE_PIXELS` from 3 to 5 (which puts `drifter`'s 4px in range),
re-ran `organic_rig.py --check`, got exactly the expected new problem
(`drifter: left eye renders 4px at azimuth 45...`), reverted immediately
after. `organic_rig.py --check` (real floor) still reports clean. Full
40-test suite unchanged.

**Not wired into `manifest.py --check`, and deliberately left that way
this hour.** Unlike `character.py`'s checks, `organic_rig.py`'s `check()`
is reachable only via its own CLI (`--check`/`--lock`) and, transitively,
`style_approve.py`'s lockfile-approval gate -- never `manifest.py --check`
directly. `style_approve.py`'s own comment explains why `organic_rig.py`
exists as a separate, `ANY_OF` producer rather than a required one:
`character.py` "still only knows box/prism" for any style (the import-
order gap `NEXT.md` already documents), so `manifest.py`'s character block
has no notion of which rig primitive is active and cannot safely branch to
this file's checks without becoming aware of that -- a real, separate,
already-scoped piece of architecture work, not a wiring oversight to close
in passing the way `check_direction_stability`'s manifest gap was.

New branch (`organic-rig-eyes-single-azimuth`), unrelated to any other
currently open PR's subject. Left unmerged per standing practice.

## `check_eye_legibility` only ever rendered azimuth 45

Hours 20 and 21 both found real defects by asking whether a check's real
caller exercised the same range the shipped asset actually varies over --
`check_generator_range`'s pair floor, then `check_direction_stability`'s
roster. `check_eye_legibility` is the third `character.py` gate with the
same shape and the same fixed camera angle, and its own docstring already
names the mechanism as inherently angle-dependent: "the eyes sit on the
shaded front facet, so the lambert moves them... and only a render knows
that." Lambert value is a function of the light-vs-surface angle, which
changes with azimuth by definition -- a check built on that premise and
then hardcoded to one azimuth was checking its own claim at a single,
unverified sample point.

**Swept all 8 azimuths across all 7 skin tones and found a clean three-way
split, not a uniform "more angles helps":**

    tone           0     45     90    135    180    225    270    315
    skin-4        --    .196   .161   .196    --    .103*   --     --
    skin-3        --    .196   .256   .256   .204   .204     --     --
    skin-2        --    .196   .248   .353   .304   .304     --     --
    skin-1        --    .256   .341   .450   .404   .404     --     --
    skin         .103*  .353   .437   .547   .504   .504     --     --
    skin+1       .204   .450   .533   .644   .602   .602     --    .204
    skin+2       .304   .547   .533   .644   .602   .602     --    .304

    (-- = no differing pixels between the plain and eyed render; floor .15)

- **270 is fully occluded for every tone, no exceptions** -- the back of
  the head, correctly showing no face. Not a defect at any tone.
- **45, 90, 135, 225 show real, non-zero eye-vs-skin pixels for every
  tone, no exceptions** -- geometrically unambiguous face-on angles.
  Visually confirmed on `skin-4`: an upscaled render at 45/90 shows two
  clearly legible eye squares; the same tone at 225 shows only a bare
  sliver, matching its 0.103 measurement.
- **0, 180, 315 are ambiguous.** Whether they show any differing pixels at
  all depends on which skin tone is asked -- pure geometric occlusion
  cannot do that, since occlusion doesn't know what colour the surface is.
  These are very likely more instances of "eyes render pixel-identical to
  skin," an even more severe version of the defect this check exists to
  catch, at darker tones specifically -- but nothing here can yet
  distinguish that from a genuine grazing-profile view, and a wrong guess
  either way is worse than an honest gap. Left OUT of the fix, recorded as
  open rather than resolved by assumption.

**Fix.** `check_eye_legibility` gained an `azimuths` parameter, defaulting
to the four decisively safe angles (`EYE_LEGIBILITY_AZIMUTHS = (45.0, 90.0,
135.0, 225.0)`) instead of the bare `45.0` it always rendered. `manifest.py
--check`'s call site needed no change -- it was already calling the
function bare (`check_eye_legibility(ramps)`), so the widened default
reaches it automatically, the same way narrowing a default closes a gap
without touching every caller.

**Two different outcomes per style, reported honestly as two different
outcomes rather than one generalized claim:**

- **`cozy_ghibli`: a genuinely new defect.** The old single-azimuth check
  reported zero eye-legibility errors here. The sweep found one:
  `skin-4` at azimuth 225 measures 0.103 against the 0.15 floor -- a real,
  previously invisible failure, now an `ERROR` (3 -> 4).
- **`snes_rpg`: confirmation, not discovery, plus one new fact.** NEXT.md
  already documents this style's `skin-4`/`skin-3`/`skin-2` near-misses at
  0.147 (PR #24) -- all three were already caught by the old 45-only
  check, already counted in the existing 10-error baseline. The sweep adds
  no new FAILING TONE, but does add real information: `skin-4` and
  `skin-3` measure the *identical* 0.147 at all four checked azimuths, not
  a range -- meaning this specific defect is a palette-proximity fact (the
  skin/eye OKLab distance is nearly constant regardless of viewing angle
  under this compressed ramp), not the shading-angle artifact the
  mechanism section above describes for `cozy_ghibli`. `skin-2` fails only
  at 45 (0.147) and clears the floor at 90/135/225 (0.266/0.266/0.152).
  Error count rises 10 -> 16, entirely from repeating three already-known
  root causes at the newly-checked angles, not from new subjects -- recorded
  as such rather than left to look like six new defects. NEXT.md's own PR
  #24 write-up updated with a pointer here rather than left stale.

**Verified no regression.** Old single-azimuth call
(`check_eye_legibility(ramps, azimuths=(45.0,))`) still returns exactly
the pre-fix message sets for both styles, confirming the change is additive
at the API surface. Full 40-test suite unchanged. `manifest.py --check`
runtime: ~2.4 minutes, in line with existing cost (the sweep adds 3x the
renders for one check out of dozens in the suite).

New branch (`eye-legibility-single-azimuth`), unrelated to any other
currently open PR's subject. Left unmerged per standing practice.

## `check_direction_stability` was never in `manifest.py --check`, and checked one archetype when it did run

Hour 20's `check_generator_range` fix (this file, "the 45-degree default was
hiding five more collisions") found its bug by asking whether a check's real
caller exercised the same range the shipped asset actually varies over.
Applied the same question to every other `character.py` gate rather than
stopping at one success, and it landed on a second, structurally different
gap in a check that sits right next to the ones `manifest.py`'s own comments
already record fixing.

**Not wired in at all.** `grep -n "direction_stability" tools/manifest.py`
returns nothing. `check_contrast`'s call site in `manifest.py` carries a
comment naming the exact failure mode this is: "`character.py`'s own
`main()` has always run [a check] against the fixed roster... but
`manifest.py --check` never called it here... invisible to this command
specifically" -- written about `check_contrast`, already fixed for it, and
for `check_waistline`/`check_eye_legibility`/`check_spec_coverage` beside
it. `check_direction_stability` -- the check for a character shrinking to an
unreadable sliver at some rotation, arguably the most visually severe
failure mode this file has on record -- sits one function away from all
four and was never carried into the same fix. It only ran via `python
tools/character.py`'s own separate `main()`, or transitively through
`character.py --lock` feeding `style_approve.py`'s gate -- neither is part
of the automated `manifest.py --check` pass this repo treats as the
authoritative per-commit gate.

**And when it did run, one archetype.** `check_direction_stability(spec=
None)` defaulted to `CUSTOMERS[2]` ("regular") alone, not `ROSTER` -- unlike
every sibling check (`check_contrast`, `check_waistline`, `check_palette_
spread`), which already iterate `roster or ROSTER`. Measured the whole
roster's minimum silhouette width against the 9px floor to see what that
one-archetype default was missing:

    barista     12.1px    reader      14.0px    student    10.2px (tightest)
    regular     15.9px    commuter    15.3px    artist     14.0px
    elder       11.3px    writer      15.3px    friend     15.1px

`regular`, the one archetype actually checked, sits at 15.9px -- the
roster's most COMFORTABLE margin, not its tightest. `student`, at 10.2px
against a 9px floor (13% headroom, the closest anything comes to failing),
was never checked by any automated path. Nothing currently fails -- this is
a live coverage gap with no live casualty yet, the same "not a bug today,
a bug waiting on the next roster edit" shape `check_contrast`'s own history
already lived through once (the `elder` hair-vs-skin defect that motivated
wiring it in was found on a re-run, not by the check existing in the first
place).

**Fix.** `check_direction_stability` now takes `roster=None` and iterates
`roster or ROSTER`, matching its siblings exactly; `manifest.py --check`
gained a call against the real roster and, alongside `check_contrast`/
`check_waistline`, against the 12 generated extras too.

**Proved the wiring has teeth, not just trusted the diff.** Temporarily
tightened `MIN_SILHOUETTE_PX` from 9 to 11 (only `student`'s 10.2px falls
in that gap) and re-ran `manifest.py --check`: two new `ERROR` lines
appeared, `student dir3`/`dir7`, ordinary error count 3 -> 5. Reverted the
floor immediately after. This is the same class of proof PR #78's fixture
gave `check_albedo_regression` and Hour 20's forced 45-degree-vs-swept
comparison gave `check_generator_range` -- a check that has never been
observed catching anything is unverified, whatever its code reads like.

**Verified no regression at the real floor.** `manifest.py --check`, both
styles: 3 errors / 10 errors respectively, unchanged from the documented
baseline, 0 new errors from either the full hand-written roster or the 12
generated extras -- the roster genuinely clears 9px everywhere, this closes
a blind spot rather than exposing a live defect. Runtime: ~2.5 minutes for
the full suite, in line with its existing multi-minute cost; the added 168
renders (9 roster members + 12 extras, x8 directions) are a small fraction
of it. Full 40-test suite unchanged. `python tools/character.py` (no args)
still runs clean, now against the same full roster instead of one spec.

New branch (`direction-stability-not-wired`), unrelated to any currently
open PR's own subject. Left unmerged per standing practice.

## `check_buried_detail` was checking the one angle furniture doesn't ship as

The check's own docstring already says it: `azimuths` defaults to the single
view the room composite uses, and to "pass all eight for anything that ships
as a rotating sprite." Its only real caller, `review_library()` (run from
`manifest.py --check`), never did -- `check_buried_detail(assets)`, no
`azimuths` argument, every call since the check was promoted. Every asset in
that `assets` dict comes from `assetlib.py`, and every `assetlib.py` prop
`furnish.py` builds *is* exactly what the docstring is warning about:
`build_one` renders each one at `45 + k*AZIMUTH_STEP` for `k` in `0..7` and
ships all eight as the sprite sheet ("these sprites are rendered at all 8
azimuths, so the reservation has to hold with the object turned" -- the
comment sits four lines from that loop). The check that exists specifically
to catch detail modelled where the camera can't reach it was only ever
looking at one of the eight cameras that actually reach it.

Confirmed before touching anything: ran `check_buried_detail` on the current
`review_library()` asset set two ways. At the single default azimuth (today's
behaviour) it flags 6 props. Swept across all eight of `furnish.py`'s own
azimuths, it flags 10 -- the same 6, at higher and more accurate shares
(`bean_hopper` 41% -> 42%, `drip_brewer` 39% -> 55%, matching the worst angle
rather than one arbitrary one), plus four never flagged at all before:
`bookshelf` 38%, `chair` 31%, `menu_board` 52%, `wall_art_framed` 32%.

`bookshelf` is not a new defect -- it is the *original* one this check was
promoted for ("shelves and books modelled inside a solid carcass box... a
plain wooden slab standing where a bookcase was meant to be", two sections
up). That fix was real at the one angle anyone looked at. Rendered all eight
of its own shipped directions fresh (`out/bookshelf_8dir.png`, 8x
nearest-neighbour) to check by eye, not just by number: directions 0-2 show
a real bookshelf, visible shelves and books, exactly as the earlier fix
intended. Directions 3, 4, 6, 7 are flat, featureless slabs -- the identical
"plain wooden slab" defect the original finding described, on the five-eighths
of the object nobody was looking at when that fix shipped. The fix closed the
complaint at the one camera angle that generated it and left the other seven
untouched, because nothing that ran afterward ever checked them.

**The fix here is the wiring, not the geometry.** `review_library()` now
passes `[45.0 + k*AZIMUTH_STEP for k in range(8)]` -- `furnish.py`'s own
azimuth list, imported from the same `isorender.AZIMUTH_STEP` constant
rather than re-typing `45.0` a second, divergeable way -- instead of relying
on the single-view default. This is a check-coverage fix, not a mesh fix, in
the same spirit as `check_contrast` never being run against the fixed
`CUSTOMERS` roster (manifest.py, PR #78) and `check_ui` validating the
wrong style's font path (PR #86): a check with a real, documented blind
spot that nothing had ever closed.

**Verified zero regression on the blocking gate:** `manifest.py --check`
still reports exactly 3 errors, same messages, same numbers, byte-identical
to the documented baseline -- `check_buried_detail`'s findings feed `warns`,
not `errs`, so widening its coverage cannot flip the gate this repo's own
doctrine treats as "must be clean before any commit." What changes is the
warning count: 8 -> 12. Four of those are new, real, and not fixed here --
`bookshelf`, `chair`, `menu_board`, and `wall_art_framed` each have genuine
buried geometry on the majority of their shipped rotations, the same class
of defect the original three (`bookshelf`, `register`, `pastry_case`) were,
and closing them is per-asset modelling work, not a check change --
deliberately left failing rather than quietly widening `ACCEPTED_BURIAL` to
make the new warnings disappear, the same discipline `table_communal` (PR
#83) was left under for the same reason.

## `check_ui` was still checking the wrong style's font, ten minutes after the fix that made it possible to

Not the "prompt-vs-pixel lever" pattern this file's UI-icon sections have
been chasing -- a different, adjacent kind of drift, closer to the galley
finding above: a claim that was true when written and false by the time
anyone read it again, sitting in code rather than prose this time.

`manifest.py`'s `check_ui` docstring said plainly: `ui_font` is checked
against one hardcoded path "because `bitmap_font.py` has no `--style` flag
at all yet." True when that sentence was written (`ee4a645`, 18:32:29) --
false ten minutes later, in the very next commit on the same branch
(`2df849d`, 18:42:13, "bitmap_font.py: --style, closing the last real
`load_palette()` gap"). `bitmap_font.py` has written its output to
`out/ui/<style>/font/` for a non-default style ever since. `check_ui`'s
own `font_index` never moved off `out/ui/font/font.json`.

**Confirmed as a live bug, not a stale comment, before touching anything.**
Built `cozy_ghibli`'s font only (`bitmap_font.py`, no `--style`), then ran
`manifest.py --check --style snes_rpg` (with `out/ui_snes_rpg/` present
via `ui_chrome.py`, so the check reaches the font logic rather than
short-circuiting on "no ui output at all yet"): **no `ui_font` warning at
all**, under `snes_rpg`, with `snes_rpg`'s own font never built. The check
was silently reading `cozy_ghibli`'s `font.json` -- whichever style's file
happened to exist -- regardless of `--style`.

**The fix:** `font_index` now resolves through `forge_dir`, the same
per-style path `check_ui` already computes correctly for every other
`ui_forge`-owned id two lines above it (`out/ui/font/font.json` for the
default style, `out/ui/<style>/font/font.json` otherwise) -- reusing an
existing correct value rather than re-deriving the same path a second,
divergeable way. The sheet-existence check a few lines down had the
identical hardcoded-default bug in the same block and got the same fix.
The warning message now names the actual path and command
(`tools/bitmap_font.py --style snes_rpg`) instead of always printing the
default one.

**Confirmed failable both directions, live.** With `snes_rpg`'s font still
unbuilt: `warning ui: ui_font declared and no out/ui/snes_rpg/font/font.json
-- run tools/bitmap_font.py --style snes_rpg`. Built it
(`bitmap_font.py --style snes_rpg`); the warning cleared. **Verified no
regression** on the default style, where `forge_dir` and the old hardcoded
path are byte-identical by construction: `manifest.py --check` still
reports the documented baseline exactly, 3 errors (plan 1 L-run, plan 8
galley brightness and detail), unchanged.

## `table_communal`: a coverage gap that was hiding a real defect, half-fixed

Auditing `art_review.py`'s `GENERATORS` list (what `check_generator_range`
actually measures) against every seeded builder in `assetlib.py`, the same
kind of two-directional cross-check that found `gates.py`'s missing
`organic_rig.check_roster` entry, turned up two more: `furnish.py` calls
`assetlib.table()` directly for `table_2top_square` and `table_communal`,
neither of which was ever added to `GENERATORS`. `table_round` and
`table_4top` -- both of which delegate to the same `table()` -- were covered
and passing, so this looked like simple bookkeeping at first.

`table_2top_square` is: adding it passes cleanly (28.3% mean spread, 6.1%
closest pair, both comfortably clear of the 15%/4.5% floors). `table_communal`
is not. Its closest pair measured **0.48%** -- two of eight seeds render
almost pixel-identical, the exact "seed is barely changing the shape" failure
mode `check_generator_range`'s own docstring exists to catch, invisible until
now purely because this recipe was never on the list it checks.

**The mechanism, traced rather than guessed.** `table()`'s randomized draws
(height, top thickness, overhang, base style, leg radius) are identical
per-seed regardless of the table's own `w`/`d` -- the RNG doesn't know how
big the table is. Tracing seeds 1-8 directly: seeds 1 and 3 both drew
`_base_pedestal` ("Column on a splayed foot. **The cafe two-top.**" -- its own
docstring). A single small central column, on a table communal-sized at
4.0x2.0m, occupies a tiny and visually near-constant fraction of the
silhouette regardless of which few centimetres of thickness/overhang/leg-
radius the seed happened to draw -- so two pedestal seeds on this table are
close to indistinguishable, a defect invisible on a `table_round` or
`table_2top_square` (1.0x1.0m) precisely because the SAME absolute-unit
variation is a much larger fraction of a much smaller table.

**The fix, and what it did and didn't close.** `_base_trestle`'s own
docstring already names the size this style belongs to instead: "Two end
frames joined by a spine. **The long communal table.**" -- the code already
knew which style suited which size, it just never enforced it. Added a
size guard in `table()`, the same pattern already used to redirect `_base_
trestle` to `_base_tripod` under a round top: `_base_pedestal` is excluded
above `max(w, d) >= 2.5` and substituted with `_base_trestle`. Seeds 1/3's
pair improved from 0.48% to 4.62%, clearing the pair floor outright.

That fix is real and it is not the whole story. Excluding pedestal collapsed
its seeds onto the remaining three styles, and doing that exposed a
**second, pre-existing** collision that had been hiding behind the worse
one: seeds 5 and 6 both drew `_base_posts` and measured 4.22% apart -- under
the 4.5% floor, and present in the UNFIXED generator too, just never the
closest pair because 1-vs-3 was always closer. `_base_posts` places four legs
at `x0 + r*2.2` / `x1 - r*2.2`-style insets, so leg position does shift with
the randomized radius `r` -- just, again, by centimetres against a 4-metre
top. The general mechanism is not "pedestal is wrong," it is "every style's
variety here is an absolute-unit draw, and a communal-scale table dilutes
absolute units into invisibility regardless of which style holds them."

**Left failing, deliberately, not given a custom floor.** `wall_art_framed`
and three other generators in `GENERATORS` do carry an `own` floor, and each
one is a case where the measured, honest ceiling of a *deliberately* subtle
generator sits under the default bar for a stated reason (a sack's slump
looking the same on purpose; a hue drawn from 4 buckets colliding by the
pigeonhole principle). `table_communal` is not that: a communal table's base
style and leg arrangement are exactly the kind of first-order silhouette
change `table_round`/`table_4top`/`table_2top_square` all vary cleanly on.
Setting `own` low enough to pass would be tuning the instrument to the
answer -- the same trade this file has rejected everywhere else it was
proposed (counter orientation, the detail floor's bracket, the mean-spread
floor). `check_generator_range()` now correctly reports `table_communal`
failing on both the mean and the pair floor, which is the honest state: a
real defect, found by closing a coverage gap, half-closed by a real and
verified fix, with a second, precisely diagnosed cause left as recorded,
open work -- most likely closed properly by giving long tables a size-
appropriate leg-count or leg-layout variation rather than more of the same
few-centimetre radius/thickness draw, which is a real design pass, not a
one-line fix.

## `check_generator_range`'s own corner-view default was hiding five more collisions, not just `table_communal`'s

Before accepting the entry above's "a real design pass, not a one-line fix"
as the end of it, asked the same question Hour 15 asked of
`check_buried_detail`: every measurement of `table_communal` on record --
this file's own, and `check_generator_range`'s real caller in
`manifest.py` -- shares one lever, a fixed 45-degree azimuth, while
`furnish.py.build_one` ships every one of these generators as an
8-direction rotating sprite. Had a genuinely different lever (more angles)
ever been tried on this specific check, the way it was on `check_buried_
detail`? It had not. Swept `table_communal` across all 8 azimuths a real
sprite ships at, closest pair per angle:

    az    45    90   135   180   225   270   315   360
    lo  3.91  0.00  3.91  0.00  3.91  0.00  3.91  0.00

The default 45-degree check is `table_communal`'s OWN BEST CASE, not a
representative one -- every axis-aligned angle (90/180/270/360) is
PIXEL-IDENTICAL between its closest pair, worse than the 3.9% the existing
write-up above already treats as a real failure. This is the opposite
generalization from buried_detail's (there, the default hid a defect a
wider sweep exposed as real; here, the default was already failing, and a
wider sweep confirms the same defect is more severe than measured, not that
it secretly passes elsewhere).

**Swept the other 18 seed-variety generators the same way**, not just the
one already known to be broken -- the buried_detail precedent was itself a
warning against trusting one subject's result as the whole picture:

    name               az=45 (default)   worst-of-8   worst azimuth
    table_4top               5.2%           2.6%           90   NEW FAIL
    bookshelf                15.9%          0.0%          180   NEW FAIL
    bench                    9.0%           0.9%          180   NEW FAIL
    espresso_machine         9.0%           4.0%          225   NEW FAIL
    pastry_case               7.6%          3.0%          180   NEW FAIL
    (14 others: worst-of-8 stays clear of the 4.5% floor)

Five of nineteen generators -- over a quarter -- pass the check that ships
today and fail at a real angle the sprite sheet actually renders. All five
collisions land on an axis-aligned angle (90/180/225/270), none on a
diagonal one, which is a physically consistent mechanism and not
measurement noise: a corner-on (45-family) camera sees two faces of a boxy
object at once, so a base/leg/shelf-contents difference on either face
shows; a face-on (90-family) camera sees exactly one face and occludes
whatever the far side changed, so two seeds that differ only there collapse
to one silhouette.

**Visually confirmed, not just numerically.** `bookshelf` seeds 1 and 2 at
45 degrees show clearly different book colours and arrangement on the
shelves -- correctly read as different by the existing check. The same two
seeds at 180 degrees are both a flat, featureless orange plank: the
bookshelf's closed side panel, with every shelf and book that distinguishes
them on the opposite face, completely hidden. Not a rendering bug --
`screen_materials`' own docstring already named this exact mechanism for
silhouette alone ("an open-fronted carcass has the same outline whatever is
on its shelves"); here the same occlusion swallows the *interior* detail
the earlier fix (comparing materials, not silhouette) was written to catch,
because at this specific angle there is no interior showing at all.

**The fix: same wiring pattern as `check_buried_detail`.**
`check_generator_range` gained a `pair_azimuths` parameter (default
`(45.0,)`, preserving every existing caller's behaviour byte-for-byte
unless it opts in), and now checks the closest pair at every azimuth in
that tuple rather than only the mean's single `azimuth`, reporting whichever
angle is worst. `manifest.py --check`'s real call site was updated to pass
all 8 real ship azimuths, the same `45.0 + k * AZIMUTH_STEP` sweep Hour 15
wired into `review_library()`.

**Verified no regression.** `manifest.py --check`, both styles, before and
after, on this branch: errors unchanged (3 / 10, matching PR #83's own
baseline), warnings +5 each style (the five new generator names above,
identical set under `cozy_ghibli` and `snes_rpg` -- expected, since
`screen_materials` resolves material identity, not colour, so this
mechanism is palette-independent by construction). Runtime cost: the sweep
adds roughly 4 seconds to `check_generator_range` (0.9s to 4.9s) for
checking 8 angles instead of 1 on 15 generators -- negligible against
`manifest.py --check`'s multi-minute total. Full 40-test suite unchanged.

**Left failing, deliberately, same reasoning as `table_communal` above.**
None of the five newly-exposed generators gets an `own` floor -- their
variety is not deliberately subtle, it is a first-order silhouette/interior
change with a blind angle, and the honest fix is either giving the
`table()`-style absolute-unit draws a size-relative version (as attempted
for `table_communal`) or, for `bookshelf`/`bench`/`espresso_machine`/
`pastry_case`, auditing what part of each object's variety lives only on
the face an axis-aligned camera occludes. That is real per-generator
geometry work, five instances of it, correctly out of scope for a check-
wiring fix -- recorded here, not silently absorbed into a looser floor.

Follow-up commit on this same branch (PR #83), continuing its own named
check function rather than opening an unrelated topic. Left unmerged per
standing practice.

## A third re-check, a genuinely mixed result: the basket that invented `check_speckle` was never re-tested against the fix it inspired

Two sections up, "Four fixes, none of which worked, which is the finding"
still reads, unedited since before this branch existed: *"There is no render
setting. The remedy is upstream -- a subject whose surface is smooth at this
scale, or a better reconstructor."* That basket -- the diagnostic subject
whose 0.127-0.163 isolated-pixel share fixed `MAX_ISOLATED` at 0.105 in the
first place -- was never part of either despeckle verification pass, this
branch's own 32-cached-mesh sweep or the bread_loaf and character-ceiling
follow-ups above: it isn't a shipped asset (no `basket`/`wicker_basket` id
anywhere in `assets.yaml` or `subjects.yaml`), so nothing that iterates the
real library would ever touch it. It sat in this file as a citation, not a
render, while everything around it got re-tested.

Re-ran it directly, the same way as `bread_loaf`. `main` (pre-despeckle),
fresh render from `out/mesh/basket_bound.obj`: `art_review.py` reports 8 of 8
frames blocked at **12.7%-16.3%** -- reproduces the recorded range in this
file exactly, direction for direction. This branch (post-despeckle), same
mesh, same render: **7 of 8 blocked, 11.1%-13.2%** -- one frame (`dir1`, the
thinnest silhouette of the set) now clears; every other frame is lower than
its `main` counterpart by 2-4 points but still above the 10.5% floor.
Confirmed by eye, not just the count: an upscaled 8x before/after contact
sheet (`out/basket_recheck/before_after.png`, all 8 azimuths) shows the two
rows are close to indistinguishable -- the same dense cream/wood/neutral
salt-and-pepper mix survives in both, unlike `bread_loaf`'s crust or the
character-ceiling gate, where despeckle's effect was either total or a side
effect large enough to see.

So this is a third outcome, not a repeat of either prior re-check. `bread_loaf`
(two sections up) fully generalized: despeckle was the untried lever and it
closed the gate outright, 5/8 blocked to 0/8. The frog knight (three sections
up) did not generalize at all: the gate cleared but the sprite still didn't
read as its subject, a topology problem no pixel pass can touch. The basket
is neither -- despeckle **measurably helps** (worst frame 16.3% -> 13.2%,
average isolated-pixel share down about a quarter) **without closing the
gate**, because its speckle is wider than the single-pixel-with-no-majority
case the conservative two-rule pass is designed to remove: a woven surface's
fine detail survives as small multi-pixel clusters, not lone dots, on a mesh
this coarse at 64px. That is the literal mechanism the four original fixes
already diagnosed -- "sub-pixel detail in the source... one 64px pixel covers
hundreds of triangles of it" -- and despeckle, a real fifth lever the
original four attempts never included, still runs into the same wall for
*this specific subject*. The two-sections-up passage's "there is no render
setting" is narrowly accurate as written (despeckle is not a render setting,
it is exactly the downstream pixel lever this file elsewhere credits with
fixing UI icons, lifted objects generally, and bread_loaf specifically) but
its confident tone reads, after this check, as broader than the evidence
now supports for the one subject it was built on. Left as the historical
record with this section as the honest update, not rewritten in place --
same practice as the frog-knight and bread_loaf follow-ups.

**What this does and does not change:** `check_speckle`'s floor and mechanism
are untouched -- this was a re-verification of an old, non-shipped diagnostic
case, not a new fix, and nothing here argues for loosening `MAX_ISOLATED` or
special-casing `basket` to pass. The basket was never going to ship regardless
of this result; its only role is as the number that calibrated the floor, and
that calibration is unaffected by whether despeckle later helps it. What
changes is confidence in generalizing from any single re-checked case to "the
speckle floor is now solved everywhere despeckle runs" -- `bread_loaf`
supported that reading, this doesn't, and the honest position is that
despeckle's coverage is measured per-subject, not assumed.

## Despeckle's own scope claim, checked: three render paths never got the fix, and none of them needed it

This branch's own commit message and the addendum above describe despeckle
as wired into "the shared rendering path for every asset type in the
factory, not just lifted props" (`render_batch.render_sprite`). That is a
testable claim about the code, not just about visual results, and it does
not hold literally: `render_room.py`, `animate.py`, and
`preview_characters.py` each call `rasterize`/`shade_toon`/
`downsample_modal`/`apply_outline` directly, and none of the three goes
through `render_sprite` at all -- `grep -n "despeckle(" tools/*.py` shows
exactly one call site, inside `render_sprite` itself. Two of the three even
say, in their own code, that they match the "real" path: `animate.
render_frame`'s docstring called itself "exactly the path a static asset
takes," and `preview_characters.render_one`'s comment said its grain setting
was "matching `animate.render_frame`" specifically so the preview sheet
would not drift from the shipping render. Neither statement has been true,
in the despeckle sense, since the commit two sections up.

Checked whether this is a live gap or a documentation-precision issue only,
the same way `check_generator_range`'s azimuth blindness (Hour 20) and
`check_collapse`'s width blindness (Hour 34) were checked before deciding
whether anything needed fixing: despeckle exists to remove one specific
noise pattern -- the per-vertex/per-pixel colour left behind by TripoSR mesh
reconstruction or SDXL concept art. `grep -rn "load_obj|ingest" tools/
render_room.py tools/animate.py tools/preview_characters.py tools/layout.py
tools/assetlib.py` returns nothing: none of those five files ever load an
ingested OBJ. `render_room.build_room()` -- and `build_plan.build()`, the
generator that file's own composition checks (`check_focal_contrast` and
friends) render through the same `render_room.render()` -- places every
piece of furniture exclusively through `assetlib.py`'s own procedural
generators (`counter`, `chair`, `table_round`, `grinder`, `plant_small`,
...). `animate.py` and `preview_characters.py` rasterize exclusively
`character.build()` output. Neither source has ever passed through TripoSR
or the SDXL matte pipeline, so there is no noisy per-vertex colour for
despeckle to remove in the first place, regardless of which branch renders
it.

Confirmed empirically, not just by absence of a code path: rendered the real
demo room fresh (`python tools/render_room.py`, this branch, unmodified) and
ran `check_speckle` directly against the output -- 0 findings, clean, the
same result it would give on `main` before despeckle existed, because
nothing in the room's geometry carries the defect either way.

**Conclusion: the coverage gap is real as a fact about the code -- three
render paths bypass despeckle entirely -- but has no live casualty, because
none of the three ever renders content that could speckle. No functional fix
ships here; wiring despeckle into `render_room.py`/`animate.py`/
`preview_characters.py` defensively, with no measured defect for it to
catch, would be exactly the "tuning the instrument to an answer nobody
asked" this repo's own doctrine argues against.** What is worth fixing is
the record: the commit message's "every asset type in the factory"
overstates `render_sprite`'s actual reach, and the two docstrings quoted
above were stale in this one specific respect. Corrected in place, same
branch: `animate.render_frame` and `preview_characters.render_one` now say
which parts of the path are actually shared (camera, quantization, palette,
outline) and name despeckle as the one deliberate, harmless exception, with
a pointer back to this section.

## `MAX_ISOLATED`'s own calibration was cozy_ghibli-only, and it doesn't fully hold under `snes_rpg` -- despeckle already covers the gap anyway

`check_speckle`'s floor comment (`tools/art_review.py`) is explicit about what
it was measured against: "Over ten authored props at eight directions each...
Three props lifted through TripoSR read 0.045 (kettle, good), 0.078 (teapot,
acceptable) and 0.153 (basket, rejected)." Every one of those renders,
checked, was `cozy_ghibli` -- `snes_rpg` didn't exist yet when this floor was
set. Whether 0.105 is the right cut for a style with a genuinely different
palette (fewer, more saturated ramps, per `snes_rpg`'s own bible) was never
tested. Checked it directly, on this branch, re-rendering real meshes under
both styles' real palettes:

**Authored/procedural geometry (`assetlib.py`, what the entire real
`furnish.py` catalog is built from) is unaffected or slightly safer under
`snes_rpg`** -- `pastry_case` (the worst authored case in the original
calibration, ~0.062) measures 0.062 under `cozy_ghibli` and 0.067 under
`snes_rpg` here; `espresso_machine`, `grinder`, `table_round` all read flat
or lower. No risk on this side, consistent with the floor's own margin
("authored art is an order of magnitude below it and cannot trip it" --
still true under both styles).

**TripoSR-lifted geometry drifts upward under `snes_rpg`, consistently,
across every mesh tested** (`out/mesh/*_bound.obj`, max isolated share per
8-frame set):

    mesh            cozy_ghibli   snes_rpg
    kettle          0.057         0.073
    teapot          0.080         0.076
    coffee_cup      0.099         0.099
    wine_glass      0.072         0.096
    cheese_wheel    0.092         0.110  <- crosses the 0.105 floor
    candle          0.090         0.121  <- crosses the 0.105 floor
    cutting_board   0.148         0.188  (already failing under cozy_ghibli)
    newspaper       0.129         0.167  (already failing under cozy_ghibli)
    basket          0.163         0.221  (already failing under cozy_ghibli)

Two meshes that pass cleanly under `cozy_ghibli` fail under `snes_rpg` on
the identical geometry -- the same directional drift the four already-
failing meshes show, just crossing the line rather than moving inside it.
Mechanism, not coincidence: `snes_rpg`'s fewer, more saturated ramps mean
coarser quantization steps, so the same per-vertex reconstruction noise is
more likely to land two adjacent samples on opposite sides of a ramp
boundary -- sharper cross-ramp adjacency, same underlying noise, worse
isolated-pixel score.

**Checked whether this is currently a live defect, not just a risk.**
`grep -c "Recipe(" tools/furnish.py` -- 56 recipes, every one a `lambda s:
A.xxx(...)` call into `assetlib.py`'s procedural generators (confirmed by
`grep -n "load_obj|ingest\.load" tools/furnish.py`: zero hits beyond the
`ingest.fit`/`mesh_geometry` import, which normalizes ANY mesh's scale and
is not itself a load path). The one declared exception is real:
`assets.yaml`'s `teapot` entry has no `Recipe`, and `furnish.py`'s own
`UNMAPPED_REASON["teapot"]` says why -- `"already built on the SDXL path"`.
Checked what that path actually shipped: `out/variants/{evening,golden_hour,
night,overcast}/props/teapot_dir*.png` are real, committed sprites --
measured directly against those files (not a reproduction), max isolated
share **0.080** across all four lighting variants, comfortably under the
floor, matching the reproduction above almost exactly. But
`out/sprites_snes_rpg/` -- the one place `snes_rpg`'s own prop library would
live -- contains no lifted content at all, `teapot` included (`ls
out/sprites_snes_rpg/*.png`: `crate_cup` and `barista` only, the analytic
demo scene and the animate.py sheet). `snes_rpg`'s real prop library, lifted
or procedural, has never actually been rendered to completion. So: a real,
measured, directional gap in the floor's own generality, and **no live
casualty today**, because there is nothing currently shipped under
`snes_rpg` for it to misjudge -- the same shape as this file's `check_
collapse` and `render_room`/`animate` findings elsewhere in this session,
not the shape of PR #100's grain finding.

**Checked whether this branch's own fix already covers it, rather than
assuming.** `despeckle(px, target, min_agree=2, max_passes=5)` takes no
`ramps`/`style` argument -- it operates purely on already-quantized pixel
adjacency, so nothing about its own logic should care which palette produced
the input. Confirmed directly: ran the two crossing meshes, plus `teapot`
and `kettle`, back through `despeckle()` under `snes_rpg`:

    mesh            before (snes_rpg)   after despeckle
    cheese_wheel    0.110                0.001
    candle          0.121                0.000
    teapot          0.076                0.001
    kettle          0.073                0.001

Closed completely, at the same conservative margin this branch's other
verifications show, with zero additional code -- the fix already shipped on
this branch is general across styles because nothing about it is
style-specific, not because anyone tested it that way at the time. **No
functional change ships from this section either** -- `MAX_ISOLATED` stays
at 0.105 (loosening it would be exactly the "tune the instrument to the
answer" move this repo's doctrine rejects, and it doesn't need loosening:
despeckle already keeps every case tested inside it). The value here is
confidence, recorded rather than assumed: the day someone actually renders
`snes_rpg`'s prop library against real TripoSR-lifted meshes, this branch's
fix is already the reason `check_speckle` won't need a second, style-specific
fix on top of the first one.

## Reopened: the "left open" call above was wrong about which lever was untried

"A genuinely different lever... more reseeds and more negation words, on this
evidence, will not [work]" turned out to be correct about reseeds and prompt
negation specifically, and wrong about having exhausted the levers. Both
prior fix attempts changed the SDXL *prompt* -- what gets drawn. Neither
touched the *pixel pipeline* downstream of it -- how a drawn image becomes a
64px icon -- which is where `flat_pixelize`'s own history shows the other
half of this exact problem was already fixed once before (the mean-vs-modal
downsample bug, see that function's docstring). That precedent was sitting
in the same file and wasn't applied here.

**The mechanism:** `downsample_modal` (correctly, by design) preserves
whatever a source block's majority colour is, so real fine surface detail at
1024px -- a coin's engraved rivets, a bagel's seed texture, a sandwich crust's
crumb flecks -- survives the downsample as genuine isolated-pixel scatter,
not an artifact of quantization. That is different in kind from the bug
`downsample_modal` was built to fix, and no amount of prompt-side negation
reliably suppresses SDXL's prior for that detail (confirmed, independently,
three separate times across this file: `firefly_token`, the two icon-prompt
attempts above). But the check that gates on it (`check_icon`'s isolated-
pixel ratio) is a *pixel-adjacency* measure, which means a *pixel-adjacency*
fix is answering the actual question, where a prompt-text fix never could.

**`_despeckle`** (`tools/ui_forge.py`, added after this section was first
written) reassigns a pixel to its neighbourhood's modal colour only when (a)
it is isolated by the exact same 4-neighbour rule the check uses, so nothing
it touches could have been keeping an icon under the cap, and (b) at least 2
of its up-to-8 neighbours already agree on a replacement, so a genuine
silhouette corner or thin point -- not misdrawn, just locally unique -- is
left alone rather than guessed at. Measured on real SDXL renders, both
styles, the exact four icons this section called an accepted limitation:

```
icon              style        before   after
ui_coin           cozy_ghibli   14.7%    1.8%
ui_icon_bagel     cozy_ghibli    9.8%    4.2%
ui_icon_sandwich  cozy_ghibli   17.9%    7.1%
ui_coin           snes_rpg      15.5%    4.1%
ui_icon_bagel     snes_rpg      12.1%    4.2%
ui_icon_sandwich  snes_rpg      17.7%    6.4%
```

Five of six clear the 6.2% gate outright; the sixth (sandwich) goes from a
wide miss to a narrow one the existing `--retry-seeds 2` budget closes in
practice -- confirmed by actually running the full roster: **all four
previously-permanent failures (`ui_coin`, `ui_icon_bagel`, `ui_icon_pastry`,
`ui_icon_sandwich`) now build clean under both styles**, `ui_icon_pastry`
and `ui_icon_sandwich` needing one reseed each, `ui_coin` and `ui_icon_bagel`
needing none. `python tools/ui_forge.py --style cozy_ghibli` and `--style
snes_rpg` both now report **20/20 icons built**, up from 13/20 and 12/20.
Checked for regression against ten already-passing icons: every one measures
equal or strictly lower isolated-pixel ratio after the change, never higher
-- expected, since the two conservative rules above guarantee the function
never touches a pixel that was contributing to a pass.

**Not a full retraction of the earlier finding -- the diffusion-negation
conclusion holds.** What was wrong was treating "prompt levers exhausted"
as "levers exhausted." The right lesson, generalized: when a check measures
a property of the *rendered pixels* (isolated-pixel ratio, contrast, spread)
rather than a property of *what the artist drew* (subject fidelity,
composition), a fix aimed at the pixel property directly should be
considered before -- or at least alongside -- a fix aimed at the prompt,
because the two are not the same lever even when they move the same number.

**Passing is not the same as reading well, and this is not the same claim.**
Building all 20 icons clean does not mean all 20 read as their intended
subject -- `ui_coin` at its default seed (1) passes the gate at 1.8%
isolated pixels and still does not read clearly as "a round gold coin": the
render is dominated by a dark, low-legibility interior. A quick 5-seed
comparison for this one icon (same prompt, same despeckle) found seed 3
reads clearly as a gold coin with a visible emblem, and 4 of the 5 seeds
pass the gate outright now that despeckle is in the pipeline (before, this
few seeds would likely have found zero clean passes). Not fixed here: the
shipped pipeline still takes the first seed that passes, not the best of
several, and nothing in `_despeckle` or the check it satisfies can tell a
murky composition from a legible one -- that is exactly the "the eye has to
look" gap this file has named before (`ui_icon_pastry`'s own seed-4
non-croissant, `MAX_RETRY_SEEDS`'s comment). Recorded so a future pass does
not assume a clean build number means a reviewed-and-approved icon set.

## `ui_coin`: the gap above, closed for the one icon it was measured on

Re-checked the paragraph above rather than just re-reading it: re-rendered
`ui_coin` at seed 1 and seed 3 fresh, both styles, on this same branch.
Both pass `check_icon` cleanly (confirmed by the CLI's own `OK` result, no
`--retry-seeds` needed at either seed). Looked at all four renders before
touching anything (`out/ui_coin_test/compare.png` -- seed 1 vs seed 3 under
`cozy_ghibli`; `compare_styles.png` -- seed 3 under `cozy_ghibli` vs
`snes_rpg`): seed 1 is a dark, murky disc with no readable emblem, exactly
as the paragraph above describes. Seed 3 is unambiguously a round gold coin
with a visible circular emblem, under both styles -- `snes_rpg`'s version
reads with fewer shading bands and more saturation, consistent with that
style's own bible, not a defect of the seed choice.

**The fix:** `ui_forge.py` gains `UI_SEED_OVERRIDE`, a per-icon seed table
consulted before the global `--seed` default, with `ui_coin: 3` as its only
entry. This is deliberately narrow -- a measured, looked-at override for
the one icon this was actually checked on, not a policy change to how
seeds are chosen generally. Nothing about `_despeckle` or `check_icon`
changed; this is a different lever again, one level up from both: neither
a prompt change nor a pixel post-process, but picking the already-best
member of a set the pipeline was already capable of producing and already
had measured.

**Verified no regression.** Full `ui_forge.py` run, both styles, no
`--only`: **20/20 icons built** under `cozy_ghibli` and **20/20** under
`snes_rpg`, same as before this change (the fix touches one icon's seed,
not the gate or the despeckle pass, so every other icon's behaviour is
untouched by construction, and the full-roster count confirms it rather
than assuming it). `ui_coin`'s output from each full-batch run is
byte-identical (sha256) to the standalone seed-3 renders looked at above,
confirming the override actually takes effect in the real CLI path, not
just in an isolated test.

**Left as narrow as the evidence.** The paragraph above's real point
stands: nothing here lets the pipeline tell a murky composition from a
legible one on its own, for any *other* icon that might have the same
problem without anyone having looked. This closes the one instance that
was already measured and named, not the general gap.

## `ui_icon_milk`: a shelf of bottles, not a bottle, passing the same gate `ui_coin` did

The paragraph directly above names the risk in the abstract -- "any *other*
icon that might have the same problem without anyone having looked." Went
looking rather than leaving it hypothetical. `NEXT.md`'s "Item/inventory
icons beyond drinks" entry still claimed "the honest count is 2 of 6" for
`ui_icon_muffin`/`cookie`/`bagel`/`sandwich`/`milk`/`beans`, unchanged since
before `_despeckle` landed on this branch (the commit that added it never
touched that paragraph). Rebuilt all six fresh on this branch, both styles,
to find out what was actually still true rather than trusting either the
old "2 of 6" claim or the newer despeckle commit message's "20/20" in the
aggregate: **6 of 6 now clear the gate, both styles** --
`_despeckle` (already shipped for `ui_coin`/`bagel`/`pastry`/`sandwich`)
turns out to have quietly carried `cookie` and (combined with the earlier
prompt fix) `muffin` over the line too, never counted. `NEXT.md`'s "2 of
6"/"stays open" wording is stale, not wrong-in-spirit -- it describes a
real state this branch has since moved past without saying so.

Looked at all six before calling that the end of it, the same discipline
the paragraph above used for `ui_coin`: **five read as intended.** The
sixth, `ui_icon_milk`, does not. `out/item4_verify_sheet.png` (built for
this pass) shows it plainly under both styles: not a milk bottle but a
shelf of a dozen bottles, some barely distinguished from each other --
`check_icon`'s isolated-pixel rule has nothing to say about how many
objects are in frame, so a shelf full of small, mutually-adjacent bottle
shapes reads as clean pixel adjacency to the gate while reading as the
wrong picture to a person. Exactly `ui_coin`'s gap, on a subject nobody
had pointed the same question at yet.

**Swept seeds 1-6** (`ui_forge.forge()` called directly, `retries=0`, so
each seed's real image is seen rather than masked by auto-reseed) under
`cozy_ghibli`: seed 1 (today's silent default) is the shelf; seeds 3, 5
and 6 are each a single, clearly-readable glass milk bottle (seeds 2 and 4
fail a different, earlier check -- frame-fill -- and never reach an image
worth judging). Confirmed seed 3 also reads as one bottle under
`snes_rpg`, not just `cozy_ghibli` -- same cross-style check `ui_coin`'s
fix got.

**The fix:** `UI_SEED_OVERRIDE` gains `ui_icon_milk: 3`, same mechanism,
same narrowness -- a looked-at, measured override for the one icon this
was actually checked on. Picked 3 as the first passing seed found in the
sweep rather than picking a "best of three" by additional subjective
ranking, matching how `ui_coin`'s own seed was chosen.

**Verified no regression.** Full `ui_forge.py` run, both styles, no
`--only`: **20/20 built** under `cozy_ghibli` and **20/20** under
`snes_rpg`, same counts as before this change. `ui_icon_milk`'s output
from each full-batch run is byte-identical (sha256) to the standalone
seed-3 renders looked at above, confirming the override takes effect in
the real CLI path.

While the sweep tool was already warmed up, looked at the other five
"beyond drinks" icons too rather than stopping at the one that prompted
this section: `ui_icon_muffin` under `cozy_ghibli` currently ships on
seed 2 (`ui_forge.py`'s own auto-reseed picks the first seed that clears
the gate after seed 1's frame-fill failure) -- and seed 2 draws **two**
cupcakes plus a small dark artifact on the larger one's crown, not one
muffin. Same gap, third instance: passes `check_icon` (object count is
invisible to a pixel-adjacency rule), fails the eye. Swept seeds 1-7:
2, 5 and 7 are each a multi-object composition (two cupcakes; a
muffin-tin display of roughly a dozen; two muffins stacked); 3 and 6 are
each a single, clean muffin. `snes_rpg`'s own auto-reseed already lands
on seed 3 for this icon (confirmed clean earlier in this file, "one
sibling icon WAS genuinely fixed"), so `UI_SEED_OVERRIDE["ui_icon_muffin"]
= 3` closes both styles with the same one seed rather than two per-style
picks. Verified the same way as `ui_icon_milk` above: full run, both
styles, 20/20 built each, `ui_icon_muffin`'s `cozy_ghibli` output
byte-identical (sha256) to the standalone seed-3 test; `snes_rpg`'s output
unchanged from before this commit (it already reached seed 3 on its own).
`ui_icon_bagel`, `ui_icon_cookie` and `ui_icon_sandwich` were also looked
at in the same contact sheet and read as intended in both styles --
checked, not assumed, but genuinely nothing to fix there today.

**Left exactly as narrow as before.** Three icons in this family now carry
a seed override for the identical reason (`ui_coin`, `ui_icon_milk`,
`ui_icon_muffin`), which is enough of a pattern to name plainly: any icon
whose prompt invites SDXL toward a "collection" framing (a shelf, a
display case, a stack, a plate of several) rather than one object is a
candidate for this exact gap, and nothing in `check_icon` or `_despeckle`
checks for that automatically -- both operate on pixels within one frame,
not on how many objects that frame contains. Still not fixed in general --
the eye still has to look, one icon at a time.

## The six chrome ids were still being generated, silently, for nothing

A commit from well before this audit loop started already decided this
question once: `ui_chrome.py`'s own message says plainly, "the six chrome
ids belong in procedural code rather than in a diffusion prompt," and
lists why -- `ui_coin`, `ui_ticket`, `ui_dialogue_frame`, `ui_nameplate`,
`ui_upgrade_frame` and `ui_star_rating` are wrong-*shape* failures (a
speech bubble photographed as a tablet, a star rendered as an eight-point
burst, the coin "gated muddy"), and shape is not something `check_icon`'s
isolated-pixel rule can see. `ui_chrome.py` was built to draw all six
instead, deterministically, no GPU, no seed. `manifest.py`'s own
`check_ui` docstring already calls `ui_coin` "a CHROME key" in its
comments, as if the question were long settled.

It was settled in prose and in the drawing code. It was never settled in
`ui_forge.py`'s own `UI_PROMPTS` dict, which still listed all six --
meaning every full `ui_forge.py` run has been spending real SDXL time (and
this file's own `--retry-seeds` budget) generating six icons nobody was
going to use. `ui_chrome.py` writes into the identical `out/ui/<id>.png`
path `ui_forge.py` does, and this repo's own `README.md` documents running
`ui_forge.py` and then `ui_chrome.py`, in that order -- so in every
build that follows the documented steps, `ui_chrome.py`'s output silently
overwrote `ui_forge.py`'s, every time, for six of the twenty declared `cat:
ui` entries.

**Confirmed, not assumed, before touching anything.** `set(ui_forge.
UI_PROMPTS) & set(ui_chrome.CHROME)` returns exactly those six ids.
Rebuilt `ui_coin` alone through `ui_forge.py`, saved a copy, then ran
`ui_chrome.py --only ui_coin` and compared: two different files (sha256
`583e35f...` vs `4404921...`), and looking at both makes the intent
obvious at a glance -- `ui_forge.py`'s SDXL coin is the same kind of
overworked, textured render this file has already recorded for `ui_coin`
above; `ui_chrome.py`'s is a flat gold disc with a clean ring highlight,
exactly the shape the chrome commit set out to draw. The two-directional
coverage-audit technique this loop has used on `gates.py`, `GENERATORS`
and `REQUIRED_PRODUCERS` in earlier hours applies here too, just checking
set membership between two producers' own dicts instead of a producer
against a catalog -- and it found a real gap the same way.

**One honest consequence worth naming directly, not burying:** the
`ui_coin` seed-tuning two sections above (`UI_SEED_OVERRIDE["ui_coin"] =
3`, added earlier this same audit loop) was real work, correctly measured
and correctly verified at the time -- seed 3 genuinely does read as a coin
where seed 1 doesn't. It was never wrong. It was tuning a producer whose
output turns out to never reach the shipped library, for a reason that has
nothing to do with seeds. That is not the frog-knight case (a finding that
turned out not to generalize) -- it is a finding that was correct and
irrelevant, which is a different and equally worth-recording outcome: the
measurement stands, the artifact it improved was already dead.

**The fix:** removed all six ids from `ui_forge.py`'s `UI_PROMPTS`,
removed the now-unreachable `UI_SEED_OVERRIDE["ui_coin"]` entry (left a
comment explaining why it is gone rather than deleting the context
silently), and fixed the module docstring's own `--only ui_coin,ui_ticket`
example, which named two ids this change removes from what `--only` can
select. `ui_icon_pastry`'s own precedent -- deleted from `UI_PROMPTS`
outright once its generative path was rejected, not merely left to fail
quietly -- is the standard this change follows, applied to six ids that
were never actually failing, just never actually used.

**Verified no regression, both styles, both tools.** `ui_forge.py`:
14/14 built under `cozy_ghibli` and 14/14 under `snes_rpg` (was 20/20;
the six removed ids are the entire difference, by construction).
`ui_chrome.py`: unchanged, 10/10 both styles -- it never read
`UI_PROMPTS`, so nothing about its own six chrome ids' output could have
moved. `manifest.py --check`: identical to the documented baseline on both
styles -- `cozy_ghibli` 3 errors (unchanged: plan 1 L-run, plan 8 galley
brightness and detail), `snes_rpg` 10 errors (unchanged: the 4 character
blockers, the 3 skin blockers, the 3 composition errors) -- confirming
this is a compute-and-consistency fix, not a coverage change: every `cat:
ui` id the manifest audits was already present on disk before this change
(via `ui_chrome.py`) and still is after it.

## `check_member_thickness` was checking a scale nothing ships at, and it was wrong about the one thing it currently flags

"New promoted check: member thickness" (this file, much earlier) describes
`art_review.check_member_thickness` as rasterizing "at the scale it is
actually seen (27.2 px/unit)." That was true when it was written. It is not
true today: `furnish.py`'s per-object sprite -- `frame_all(mesh)` fitting
each asset to fill its own 64px canvas -- is what `package_godot.py` actually
packages and ships, not a fixed room-embedded camera. `render_room.py`, the
thing that DOES use a fixed camera, writes to `proof/shop.png` and is never
referenced by the export tooling; its own docstring calls it an integration
test, not a shipped path.

**Measured the gap rather than assumed it.** `frame_all`'s span, converted to
an effective px/unit at the real 64px target, against the check's fixed
27.2, across 16 real `assetlib.py` props:

```
prop            real ppu   room ppu   ratio
counter          41.3        27.2      1.5x
table_round       60.4        27.2      2.2x
register          80.6        27.2      3.0x
tip_jar          124.3        27.2      4.6x
succulent        132.5        27.2      4.9x
```

Every one of the 16 sampled ran higher, never lower -- small objects most of
all, because `frame_all` fills a small object's own canvas the same as a
large one's, where the fixed camera renders a small object as a small shape
adrift in mostly-empty space. Since the same floor (4px) is being compared
against a systematically UNDER-estimated real scale, the fixed-scale check
can only ever be too strict, never too lax -- it cannot hide a genuinely thin
member from a player, but it can flag one that reads fine in its real,
shipped form.

**It was already doing that.** `review_library()`'s entire live output before
this pass was one `check_member_thickness` finding: `plant_hanging: 35% of
its mass is in runs under 4 px at room scale (limit 20%) -- reads as wire`.
Re-measured at `plant_hanging`'s own real span (0.466, vs the fixed camera's
1.15): **0%, clean pass.** The fixed camera renders `plant_hanging` small and
adrift; its real per-object sprite fills the frame the way every shipped
sprite does, and the same geometry reads fine.

**The fix:** `check_member_thickness` gained optional `span`/`centre`
parameters that, when given, replace the fixed camera with `frame_all`'s real
values and render at the real 64px target instead of a `ppu`-derived
resolution. `review_library()` now computes and passes both per asset. Kept
the old `ppu`-based path as the default for any other caller, since nothing
else in the codebase calls this function directly.

**Wiring `span` alone was not enough, and this file's own words about
verifying in both directions applied here too.** The fixed path's
`target=(0.5, 0.5, 0.5)` assumes every asset sits centred in its own tile,
which is only ever approximately true. Passing the tighter real `span`
against that same wrong look-at point produced two assets that rendered
**fully empty** (`cup_and_saucer`, `cup_espresso` -- a span tight enough to
fill their real sprite missed their actual off-centre geometry entirely) and
one spurious **100%** finding (`wall_sign`, clipped rather than genuinely
thin) -- caught by re-running immediately after the first version of this
fix, before it was called done. Wiring `frame_all`'s `centre` through as well
(the same value `furnish.py` already passes to `render_sprite`) cleared all
three.

**Verified the check still has teeth, not just that it goes quiet.** A
synthetic 0.02-unit rod (thinner than any real prop's structural member, at a
plausible coffee-shop scale) still flags 100% thin mass at its own real ship
span; a 0.12-unit post of the same height, rendered the same way, passes
clean. The relaxation only removes a false positive; it does not remove the
check's ability to catch a true one.

**Zero regression, checked both styles.** `check_buried_detail` (the other
half of `review_library()`, untouched by this change) reports the same 6
findings before and after. `manifest.py --check` warning count drops by
exactly 1 under both `--style cozy_ghibli` and `--style snes_rpg` -- the
`plant_hanging` line disappearing, nothing else moving -- consistent with a
style-agnostic geometry check whose one live finding was a false positive,
not a style-specific one.

## The scale fix above was still an incomplete picture -- a second, independently-opened fix on the same function needed folding in

Auditing what else touches `check_member_thickness` before calling the scale
fix done found `member-thickness-single-azimuth`, an open PR against the SAME
function, opened independently and reaching a structurally identical insight
from the other axis: the check has always rasterized a single fixed 45 degree
view, but `furnish.build_one` ships every asset at all 8 real azimuths
unconditionally, and a flat member that goes edge-on at some other angle can
collapse to a stray line there without ever showing at 45. That fix already
measured worst-of-8 (not pooled -- pooling dilutes a genuine edge-on collapse
below the floor by averaging it against seven mostly-solid views) and
verified it against this file's own recorded edge-on-collapse cases.

Neither fix alone is a complete account of what `furnish.py` renders: the
scale fix (above) still only looked at one azimuth; the azimuth fix still
measured all 8 through the fixed room camera. Combined them on this branch --
`check_member_thickness` now takes both `span`/`centre` (real per-object
scale) and `azimuths` (worst-of-N, not pooled), and `review_library()` passes
the real 8-azimuth ship set alongside the real span/centre it already
computed.

**Verified together, not just merged together.** Re-ran `review_library()`:
still 6 findings, all `check_buried_detail`, `check_member_thickness`
contributing zero -- the real library has no member that is thin at its real
scale from ANY of its 8 real ship angles, not just the one this check used to
look at. That is new information, not an assumption: printed the raw
per-azimuth share for four real flat-panel props (`wall_sign`, `menu_board`,
`sandwich_board`, `coat_rack`) to confirm the machinery produces real,
varying numbers rather than trivially returning zero everywhere --
`sandwich_board` measures 0% at six azimuths and 3% at the two it goes most
edge-on, `coat_rack` 0-1%, both nowhere near the 20% floor but genuinely
different by angle.

**Positive control, since the real library currently has nothing to catch:**
built a synthetic 0.01-thick flat panel that is normal-looking from most
angles and goes fully edge-on at two of the eight. At azimuth 45 alone (the
old default) it measures 0% and passes clean -- the exact blind spot the
azimuth fix exists for. Across all 8 real azimuths at its own real span, it
measures 100% thin mass at azimuths 180 and 360, correctly flagged: `thin_
panel: 100% of its mass is in runs under 4px at ship scale at azimuth 180
(limit 20%) -- reads as wire`.

**Cost, measured rather than waved away:** `manifest.py --check` now runs in
~2m55s for `cozy_ghibli` (member thickness alone went from ~24 rasterizes to
~192, one per asset per real azimuth). Correct and still fast enough to run
by hand or in CI; not free.

**Left for him to reconcile, not resolved here:** `member-thickness-single-
azimuth` remains open as its own PR with its own history and is NOT closed by
this commit -- this branch folds its insight in and supersedes it
functionally, but closing someone else's open PR is a call for him to make,
not this pass. Flagging directly: merging both `member-thickness-ship-scale`
and `member-thickness-single-azimuth` as separate PRs will conflict, since
both rewrite the same function body differently. This branch is the version
that has both fixes verified together; the standalone azimuth PR is now
redundant with it but is left standing for him to close or not.

## `review_library()`'s other half had the same unfinished reconciliation, and finishing it found 4 real defects

Auditing what else touches `review_library()` (the function both fixes above
edited) before calling this branch done found the same shape of loose end
one function over: `buried-detail-azimuth-coverage`, another already-open PR
against this exact function, adds `azimuths=all_azimuths` to the
`check_buried_detail(assets)` call at the bottom of `review_library()` --
`check_buried_detail`'s own docstring already says "pass all eight for
anything that ships as a rotating sprite," the identical lesson this
branch's `check_member_thickness` fix just re-derived independently for its
neighbour in the same function. This branch's `review_library()` still
called `check_buried_detail(assets)` bare, so it would conflict with that
PR the same way it conflicted with `member-thickness-single-azimuth` --
completed it here rather than leaving a second half-reconciled function.

`review_library()` already computes `ship_azimuths` for the member-thickness
call (added this branch, this session); reused it for `check_buried_detail`
rather than recomputing a second local list.

**This one was not cosmetic.** Before: 6 `check_buried_detail` findings
(`bean_hopper`, `drip_brewer`, `lamp_table`, `pourover_stand`,
`sandwich_board`, `tip_jar`), all still present after. After: 10 -- 4 new,
real defects invisible at the single azimuth this check has always run at:
`bookshelf`, `chair`, `menu_board`, `wall_art_framed`. Spot-verified `chair`
by hand (`front_facing` per azimuth, not trusted from the aggregate number):
25.0% buried at azimuth 45 alone (the check's old default, passes clean
against the 30% floor) but the geometry the check pools across all 8 real
ship azimuths lands at 30.6%, rounding to the 31% the check now reports --
a real object whose occluded-detail share crosses the floor only once every
angle it actually ships at is counted, not at the one angle it used to be
judged by.

**Verified end to end, both styles.** `manifest.py --check` warnings rise by
exactly 4 under both `--style cozy_ghibli` (8->12) and `--style snes_rpg`
(7->11), error counts unchanged in both -- matching the 4 new `check_buried_
detail` lines precisely, nothing else moving.

**Cost, updated honestly:** `manifest.py --check` now runs ~4m10s per style
(`check_buried_detail` went from checking each asset at 1 azimuth to 8, on
top of `check_member_thickness`'s own 8x from the prior commit). Slower, and
still a command meant to be run by hand or in CI, not per-request -- the
same tradeoff already accepted for the scale/azimuth fix above, now paid
twice in the same function for a check that was genuinely missing real
coverage both times.

**Same reconciliation note as above, not repeated in full:**
`buried-detail-azimuth-coverage` remains open and is NOT closed by this
commit. Merging it separately against this branch will conflict on the same
line this branch already rewrote; this branch's version has both fixes
verified together.

## `tileset.py`'s checks were never in `manifest.py --check`, closing the gap that finding named but didn't fix

An earlier pass ("the one real gap: `check_manifest_placement` only runs
behind `--proof`") found and measured this precisely: `tileset.py`'s own
`build()` runs `check_lattice`/`check_collapse`/`check_manifest_placement`
on every invocation and blocks on failure, but `manifest.py --check` --
the automated, no-rebuild-required gate this whole session has spent real
effort hardening for every other producer -- never imports `tileset` at
all. That pass concluded honestly ("a coverage note, not a bug to fix")
and shipped no code, because the check was live-verified passing against
the real shipped atlases and nothing was actively broken. Re-checking this
hour whether that conclusion still stood after ~15 more hours of nobody
picking it up: it did, and the gap was still open, so this closes it.

**Scoped to the two checks that don't need a prior build.**
`check_lattice(width)` is pure integer arithmetic and `check_collapse(...)`
renders live and measures the render -- both compute everything fresh, the
same discipline every other check in `manifest.py`'s block already
follows (`check_generator_range`, `check_focal_contrast`, `check_buried_
detail`, ...). `check_manifest_placement` stays proof-gated on purpose: it
compares a fresh projection against PNG atlases already on disk, and
wiring it into `--check` would make this command's own correctness depend
on whatever `out/tiles*/` happens to contain from a previous, unrelated
build -- a real dependency this command has never had for anything else,
not a gap to match the other two checks' shape.

Wired both, once per style (via `active.materials` -> `make_wall_patterns`,
the same resolution `tileset.build()` itself uses, not a module-level
default): `check_lattice(64)` -- 64 is the only tile width this codebase
has ever shipped, confirmed earlier by this same investigation -- and
`check_collapse` for every floor pattern in `PATTERNS` at the floor's own
lambert, and every wall pattern in `make_wall_patterns(active.materials)`
crossed with every axis in `WALL_AXES`, each at that axis's own lambert
and `WALL_HEIGHT` -- the identical loop shape and lambert derivation
`tileset.build()` uses for the same two checks, not a re-derived copy.

**Verified the wiring has teeth, not just that it stays quiet.** Degraded
a copy of the live palette (every ramp longer than one step collapsed to
its own first colour, repeated) and ran `check_collapse` against the real
`floor_checker` pattern through it directly: fired immediately -- "4
materials resolve to only 2 colours at lambert 0.641... (cream, cream-1,
wood-1, wood-1-1)" -- confirming a real regression in this shape would be
caught, not silently absorbed by a wiring mistake.

**Zero regression, both styles.** `manifest.py --check`: 3 errors/17
warnings, byte-identical to before. `--style snes_rpg`: 4 errors/18
warnings, byte-identical to before. Both match the two live-verified-clean
results the earlier pass already established for the real shipped
atlases, now reached the same way `check_generator_range` and every other
producer's checks are -- automatically, on every `--check` run, not only
when someone remembers to pass `--proof` to a different command. Full
40-test suite: 40 passed.

Fixed in `tools/manifest.py` (`check()`, right after `check_stool_
occupancy`) -- branch `tileset-checks-wired-into-manifest-check`, left
unmerged.
