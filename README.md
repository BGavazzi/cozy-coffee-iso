# cozy-coffee-iso

An **automated factory for 2D game sprites**, driven by a clear art direction —
with humans doing the part that cannot be automated: critiquing whether the
output actually looks good.

Art stops being the constraint once this works. Content becomes the constraint,
which is the point.

## The division of labour

| | owns | why |
|---|---|---|
| **Factory** | every sprite, every direction, every frame | volume |
| **Automated review** | spec conformance | cheap, exhaustive, deterministic |
| **Humans** | *does it look good* | not automatable, and the entire point |

## Run it

    pip install -r tools/requirements.txt

    python tools/palette_forge.py        # compute + validate the 40-colour palette
    python tools/animate.py --fx         # the deliverable: sheets + atlas.json
    python tools/render_room.py          # whole-shop composite (integration test)

    # review surfaces -- what a human actually looks at
    python tools/preview_clips.py --who barista   # clip strips + looping GIFs
    python tools/preview_characters.py            # roster + 8 directions
    python tools/review_queue.py build "sprites/*.png"
    # fill verdict + reason in review/verdicts.jsonl
    python tools/review_queue.py stats            # what to automate next

    # the gates
    python tools/manifest.py --check     # runs all eighteen checks
    python tools/character.py            # hair contrast, palette spread, silhouette floor
    python tools/fx.py                   # loop seams

## The loop is a ratchet

Every human rejection carries a reason. Reasons that recur get promoted into the
automated tier, so **human review volume falls as the factory matures**. `stats`
names the next check to write rather than leaving it to guesswork.

Eighteen checks have been promoted so far: camera-space key light, hair/skin
contrast, per-character palette spread, waistline separation, silhouette pixel
floor, seating orientation, member thickness, grounding, declared-symmetry
verification, screen-space occlusion, buried detail, derived direction labels,
generator range, generated-spec conformance, roster variety, cast silhouette,
palette-binding round trip, and ingest transform. Most found a bug the moment they were written — floating counters,
back-to-front chairs, five wrong symmetry claims costing 31% of the effects
budget, a queue of customers stacked into a single smear, an espresso machine
whose entire mechanism was modelled inside its own carcass, and eight sprite
sheets filed one facing off from the direction they actually depict.

The newest one measures something the others cannot see. A generator can rot
without breaking anything: a base style left out of the style table, a seed
accepted and then ignored, a random stream weak enough that one branch of four
is reached a third as often as the rest. Every one of those still renders a
room full of furniture — four chairs of the wrong four are still four chairs —
so `check_generator_range` asks whether consecutive seeds actually produce
different silhouettes. Its first version counted *distinct* silhouettes and
scored a perfect 8 of 8 for generators the eye read as a single object, because
distinctness is a threshold at one pixel. It measures distance now.

The last two guard the seam where stages 1–3 will attach — `ingest.py`, which
binds an arbitrary mesh to the palette and the tile grid. Nothing feeds it yet,
which is precisely why it needs checks: an adapter that is never exercised is an
adapter that is wrong by the time something arrives. Both were verified to fail
before being trusted, and one of them needed an instrument the other four
assertions could not provide, because a mirrored mesh has the same bounds, the
same height and the same materials as the original.

The newest one came from the machine rather than from a person, which is the
loop closing. `generate_spec` proposes a character and tests it against the
checks until it passes — the same move `Layout.scatter` made with the placement
checks, applied to what this factory actually exists to produce. Looking at the
first sheet of generated extras showed one whose shirt and trousers landed on
the same value, so the figure had no waist. `check_palette_spread` counts
*ramps* and cannot see that; `check_waistline` was written, and it immediately
failed two of the nine hand-written archetypes. `elder` had shipped with a wood
shirt 0.004 in value from neutral trousers.

Then the same argument one level up. Those three checks are all predicates on
*one* spec, and a generator satisfying all three forty times can still return
forty variations of one person — each individually legal, collectively a crowd
with one extra in it. `check_roster_variety` measures the **minimum** pairwise
distance, not the mean, because the mean is dominated by the pairs that are
already fine and a player notices the two that collide. Its floor was guessed
at 20% and would never have fired; measured, the hand roster's closest pair is
45% and twenty generated extras' is 48%, so it sits at 38% — under the evidence
rather than at it. The generated cast turned out to be *more* varied at its
closest pair than the one a person wrote.

The sprite factory takes them directly:

    python tools/animate.py --extras 40

Forty extras cost exactly as much thought as zero and forty times the render —
12,800 additional frames, none of them written down anywhere. That sentence is
the entire claim this repo makes, and it is now a flag rather than a plan.

`sprites/` is generated output and is not in the repo — run `animate.py` to
build it. The default is the nine-character roster the reference room uses;
`--extras` is additive on top.

Its floor is per-generator, and every relaxed one carries the reason it is
relaxed. A single number is the wrong shape here: the default catches a
generator that has died, but a counter module that varied as much as a
houseplant would be a defect rather than a success, since a run of six fitted
cabinets showing four different fronts reads as a showroom. An unexplained
loosened threshold is how a ratchet turns back into decoration.

This has already happened once. The first batch rotated the camera with a
world-fixed light, so the lit face drifted around the object between directions.
Every frame was individually valid — no per-sprite check could catch it — but it
was obvious to a person scanning the contact sheet. The fix was conceptual: in an
isometric game the camera is fixed and the *object* rotates, so the key light
belongs in the camera basis. That finding is now an automated check and will
never need a human again.

## The checks are also the generator

`collisions`, `grounded` and `screen_occlusion` began as validators: they graded
hand-typed coordinates and reported which were wrong. Run *before* a placement
rather than after, the same predicates are a constraint solver — propose a
position, test it, keep or discard.

    made = L.scatter(lambda i: A.plant_small(seed=40 + i),
                     region=(0.5, 0.45, 13.4, 1.55), count=6, name="decor#plant")

Density stops being authoring work and becomes a number. A saturated region
returning fewer props than asked is the solver working, not failing. This is the
first part of the pipeline that *generates* rather than verifies, and it is built
entirely out of the checks the earlier passes accumulated — which is the argument
for accumulating them.

## Why generation goes through 3D

2D diffusion plus post-processing fails projection consistency, direction
coherence and frame-to-frame coherence *structurally*. All three are normally
fixed by a human retouching frames — exactly the cost a factory exists to remove.
So correctness is made structural instead: model once, render deterministically
across 8 azimuths. Diablo 2 and Age of Empires 2 solved it this way for the same
reason.

Projection is verified, not assumed: a ground-plane unit square measures
`0.500000000000` — exactly 2:1 dimetric.

## What's here

- **[PIPELINE.md](PIPELINE.md)** — the nine stages, what is built, what is not
- **[ASSET_SPEC.md](ASSET_SPEC.md)** — the rubric: projection, palette, per-asset contract
- **[style_bible.yaml](style_bible.yaml)** — the art direction, as an **input**.
  Swap it to retarget the factory at a different game.
- **`tools/`** — renderer, pixelizer, palette forge, rig, effects, reviewers

### Output

`animate.py` writes `sprites/`: one sheet per character (rows are directions,
clips stacked in row-blocks) plus `atlas.json` with frame rects, fps and
**per-clip anchors**. Anchors are per clip because a seated clip's contact point
is the seat and a standing clip's is the floor — one anchor for both plants every
sitting customer either in the chair or above it.

## The rig is six numbers

`character.Pose` is six limb angles, a vertical offset and a twist. That is the
whole rig, and the smallness is the design: at 46 px of figure a pose reads from
limb *direction* and body height, not from articulation — an elbow is one pixel.

Two behaviours fall out of constraints rather than being animated:

- **The walk bob is derived.** Posed figures are ground-clamped, and swinging a
  leg about its hip shortens its vertical reach, so the body drops when the legs
  spread and rides high when they close. Measured 1.0 px at room scale.
- **The foot does not rotate with the leg.** An ankle keeps it flat. Rotating it
  rigidly drove its corner into the floor, and since the figure is
  ground-clamped that lifted the body and *inverted* the bob.

## Art direction (case study one)

Studio Ghibli colour sensibility through 16-bit pixel-art constraints — expressly
*not* the soft-rendered diffusion "Ghibli filter", whose gradients and diffuse
edges are exactly what a locked palette and 1-bit alpha destroy. The precedent is
SNES-era JRPG background art, which already borrowed Ghibli's palette and light
while staying inside pixel-art limits.

The 40-colour palette is **computed in OKLab, not hand-picked**, so two properties
are provable rather than hoped for: every pair survives quantization distinctly,
and the warm-light / cool-shadow hue shift — the rule doing most of the "Ghibli"
work — is a parameter that cannot be forgotten on asset 180.

    python tools/palette_forge.py     # exits non-zero on constraint failure

Loads into Aseprite via `palette/palette.gpl`.

A coffee shop interior was chosen deliberately: it exercises wood, ceramic,
foliage, fabric and skin — most of the material range a 2D game needs.
