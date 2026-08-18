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
