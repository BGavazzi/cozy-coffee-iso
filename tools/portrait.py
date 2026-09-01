#!/usr/bin/env python3
"""Character portraits: a dialogue bust for the rig `character.py` already builds.

    python tools/portrait.py              # roster -> out/portraits/<name>.png
    python tools/portrait.py --check       # eye visibility, distinctness, determinism
    python tools/portrait.py --demo        # -> proof/portraits.png contact sheet

`NEXT.md` item 2: "The rig renders 46px-tall figures; a dialogue box wants a
face. Different framing, different resolution, and probably a different
producer again." All three turned out true, and the reason is the same reason
`character.py` gives for its own approach: "Value detail, not geometry detail
... at 12 px of head there is no room to model [eyes, brows, a collar seam]."
That rule is correct at 12px and wrong at 96px. Blowing up the existing
`character.face()` -- two flat eye boxes and nothing else -- renders a blank
box with two dots on it, which is legible as a person at sprite scale and
reads as a mannequin at portrait scale. So this file does not reuse `face()`;
it reuses `head()` and `hair()` for shape and skin/hair-material identity
(guaranteeing a portrait is recognizably the SAME character as its sprite,
which a generated one could not promise) and authors real brow and mouth
geometry on top, sized for a canvas roughly ten times larger.

Two further departures from the sprite camera, both found by rendering and
looking rather than by reasoning about it first:

**The camera faces the character, not the corner.** The sprite rig uses
azimuth 45 -- a corner view, chosen so a rotating figure reads from every one
of 8 directions. A portrait never rotates, so `PORTRAIT_AZIMUTH = 90`: dead
on, both eyes equidistant from the camera, the character looking at the
player rather than past them.

That number was not the first one tried. Worried that a dead-on view would
put hair directly between the camera and the face, an earlier version backed
off to azimuth 70 -- and at 70, with the face geometry sitting only as proud
as `character.face()`'s own (`HEAD_RY * FACET + 0.004`, just past `head()`'s
facet), the `bob` hairstyle's eyes rendered ZERO pixels against bare skin.
Both were true at once: the corner-view backoff was solving a problem that
`PORTRAIT_AZIMUTH = 90` does not actually have (the shipped roster's eyes
render fine dead-on at that same margin -- checked directly, not assumed),
and the margin was too thin regardless of angle, because `hair()` draws every
style's main cap at a LARGER radius (`HEAD_RY + 0.022`) than the head it
covers, so its own front facet sits further forward and can be the nearer
surface at some angles even when the head's facet is cleared. `FACE_Y` now
clears `hair()`'s facet, not just `head()`'s (see `face_detail`), which is
what a dead-on camera actually needed: not a smaller face margin bug on the
roster tested, but a margin that will still hold for a hairstyle or a
generated proportion this file has not seen yet. Its one measured effect on
the shipped nine is `reader`'s brows, invisible under the old margin at 90 and
clearly rendered under the new one -- a smaller claim than "the eyes were
broken," and the true one.

`check_eyes_visible` is what makes any of this a checked fact rather than an
impression: its first version compared bare skin against the full
eyes+brows+mouth+blush together, and passed at azimuth 70 with the eyes fully
invisible, because the brows alone supplied enough contrast to hide behind.
It was rewritten to isolate one eye at a time against bare skin -- see its
docstring for that story, and for why an image-half split could not have
worked at any azimuth but 90 regardless.

**The frame is a bust, not a cropped body.** `chest()` is a shoulder-cap slice
of the same proportions `character.torso()` uses, not the full standing
figure. A floating head with no shoulders reads as decapitated at this scale;
the full body reintroduces legs and arms that a dialogue box has no room for
and re-opens every pose question `character.Pose` exists to avoid.

Both are why this needs its own camera framing rather than `render_batch`'s
`frame_all`: that function sizes one span across the 8 STANDARD sprite
azimuths, which is the wrong span for a single custom-azimuth, custom-crop
camera that never appears in that set.

A real bug surfaced while building this and is fixed in this same change,
upstream of portraits entirely: `render_batch.render_sprite`'s outline pass
assigned material ids with `hash(m) % 251`. Python randomises string hashing
per process, so which pair of a bust's ~12 materials collided -- and
therefore which outline pixels silently borrowed an unrelated ramp's colour
-- changed on every run. It was caught here because a portrait crowds more
materials into fewer pixels than a prop does, but `furnish.py` renders the
entire prop library through the same function, and `render_room.py` /
`preview_characters.py` already carry the fix this port backports. See the
comment at the call site for the measured collision odds.

One cosmetic artifact was found and left alone rather than "fixed": a
jagged, sawtooth seam where the octagonal `chest()` prism meets the round
head silhouette, most visible on `commuter` and `elder` -- the two widest
`bulk` values in the roster, which push the torso's octagon facets past the
head's own width. Checked directly: the same notch is present, fainter, on
every character, including `bulk=1.0` ones like `barista`; it scales with
torso width and shirt/skin colour contrast, it does not appear only on one
character. It is the same kind of faceted-silhouette aliasing `character.py`
already accepts in its own renders, not a portrait-specific regression, so
it is documented here rather than chased with more geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import character as C  # noqa: E402
from assetlib import merge  # noqa: E402
from isorender import DimetricCamera, dot  # noqa: E402
from mesh import Mesh  # noqa: E402
from pixelize import audit, load_palette  # noqa: E402
from render_batch import render_sprite  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "out" / "portraits"

# Dead-on. See the module docstring: the eye-occlusion this was once backed
# off from was `FACE_Y` sitting behind `hair()`'s facet, not the angle, and a
# symmetric frontal view reads better than any off-axis compromise once that
# is fixed.
PORTRAIT_AZIMUTH = 90.0
PORTRAIT_ELEVATION = 15.0   # shallower than the sprite rig's 30 -- a portrait
                            # is looked at, not looked down on.
TARGET = 128
FACTOR = 4

# Bust geometry, in the same tile-unit frame `character.py` uses.
CHEST_Z, CHEST_H = 0.80, 0.14

# How proud of the head facial detail sits. Shared by `face_detail()` and
# `_eye_box()` (used only by `check_eyes_visible`) so the check can never drift
# from what actually gets built -- it was exactly that kind of drift, an
# `_eye_box` hand-copied at a different offset, that let the first version of
# the check pass while every eye in the roster was invisible. See
# `face_detail`'s docstring for why the margin is measured off `hair()`'s
# facet rather than `head()`'s.
FACE_Y = (C.HEAD_RY + 0.022) * C.FACET + 0.014
EYE_LINE = C.HEAD_Z + 0.62 * (C.HEAD_TOP - C.HEAD_Z)


def face_detail(skin: str, blush: bool = True) -> Mesh:
    """Eyes, brows and a mouth as real geometry, not `character.face()`'s tone
    offsets.

    Proud of `hair()`'s own front facet, not just `head()`'s -- and that is
    not the same margin. `character.face()` sits at `HEAD_RY * FACET + 0.004`,
    just proud of the HEAD, which is all sprite scale needs. `hair()` draws
    every style's main cap at a LARGER radius (`HEAD_RY + 0.022`), so its own
    front facet sits further forward, and `character.face()`'s margin does not
    clear it.

    At `PORTRAIT_AZIMUTH = 90` the shipped roster's eyes happen to clear the
    old, head-only margin regardless -- this is not fixing a broken eye on
    the nine hand-written archetypes, checked directly rather than assumed.
    What it fixes, visibly, is `reader`'s brows (`bob` hair): invisible under
    the old margin, two clear marks under this one. And what it buys beyond
    what is visible today is the reason to keep it -- `+0.014` clears every
    hairstyle's cap by construction, because every style shares the same
    enlarged radius, so it does not depend on which nine proportions happened
    to get hand-authored or which ones `generate_spec` happens to draw next.
    The margin that only barely works on a known roster is the kind of thing
    that fails quietly on the first spec nobody tested -- see
    `check_spec_coverage` in `character.py` for the general version of that
    worry, applied there to a different dimension.
    """
    m = Mesh()
    y, ez = FACE_Y, EYE_LINE
    for sx in (-0.072, 0.072):
        m.add_box((sx - 0.042, y, ez - 0.044), (sx + 0.042, y + 0.016, ez + 0.032), C.EYE)
        m.add_box((sx - 0.046, y, ez + 0.052), (sx + 0.046, y + 0.014, ez + 0.072),
                  skin + "-3")
    m.add_box((-0.038, y, ez - 0.145), (0.038, y + 0.014, ez - 0.115), "rose-1")
    if blush:
        for sx in (-0.150, 0.150):
            m.add_box((sx - 0.036, y, ez - 0.120), (sx + 0.036, y + 0.008, ez - 0.058),
                      "rose+1")
    return m


def chest(mat: str, bulk: float = 1.0) -> Mesh:
    """A shoulder-cap slice, not the full `character.torso()`.

    Reuses `TORSO_RX`/`TORSO_RY` so a portrait's shoulders are the same width
    as the sprite's, rather than a second guess at the character's build.
    """
    m = Mesh()
    rx, ry = C.TORSO_RX * bulk, C.TORSO_RY * bulk
    m.add_prism((0.0, 0.0, CHEST_Z), rx, ry, CHEST_H, mat, segments=8)
    m.add_prism((0.0, 0.0, 0.90), rx * 0.99, ry * 0.99, 0.04, mat + "+1", segments=8)
    return m


def build_bust(spec: C.CharacterSpec) -> Mesh:
    return merge(chest(spec.shirt, spec.bulk), C.head(spec.skin),
                face_detail(spec.skin, spec.blush), C.hair(spec.hair_style, spec.hair_mat))


def frame_single(mesh: Mesh, cam: DimetricCamera, margin: float = 0.08):
    """Span and centre for exactly the camera passed in.

    `render_batch.frame_all` sizes its span across the 8 STANDARD sprite
    azimuths, which is the wrong question for a camera that is not one of
    them -- using it here framed every bust as if the widest of eight
    rotating views might appear, leaving a bust occupying a third of its
    canvas. One camera, one span.
    """
    us = [dot(v, cam.right) for v in mesh.verts]
    vs = [dot(v, cam.up) for v in mesh.verts]
    lo, hi = mesh.bounds()
    centre = tuple((lo[i] + hi[i]) / 2 for i in range(3))
    span = max((max(us) - min(us)) / 2, (max(vs) - min(vs)) / 2)
    return span * (1 + margin), centre


def render_bust(spec: C.CharacterSpec, target: int = TARGET, factor: int = FACTOR,
                ramps=None):
    ramps = ramps or load_palette()
    mesh = build_bust(spec)
    cam = DimetricCamera(PORTRAIT_AZIMUTH, elevation_deg=PORTRAIT_ELEVATION)
    span, centre = frame_single(mesh, cam)
    return render_sprite(mesh, PORTRAIT_AZIMUTH, target, factor, ramps,
                         span=span, centre=centre)


# --- checks -------------------------------------------------------------------

def _eye_box(sx: float, skin: str) -> Mesh:
    """One eye, alone -- no brow, mouth or blush to contaminate the signal.

    Same `FACE_Y`/`EYE_LINE` `face_detail` builds with, not a re-derived copy.
    """
    m = Mesh()
    y, ez = FACE_Y, EYE_LINE
    m.add_box((sx - 0.042, y, ez - 0.044), (sx + 0.042, y + 0.016, ez + 0.032), C.EYE)
    return m


MIN_EYE_PIXELS = 3   # a single stray antialiased pixel is not a visible eye


def check_eyes_visible(roster=None, ramps=None) -> list[str]:
    """Does EACH eye, specifically, render enough pixels to read as an eye?

    First version of this check compared bare skin against the full
    `face_detail()` -- eyes, brows, mouth and blush all at once -- split at
    the frame's own centre column into a "left" and "right" reading. It
    passed at every azimuth tried, including the one where `bob` hair hid
    both eyes completely (`FACE_Y` sat behind `hair()`'s facet, not in front
    of it -- see `face_detail`'s docstring): the brows sit at a different z
    and cleared the hairline on their own, and the mouth and blush render
    regardless of the eyes, so the combined signal was never zero. A second,
    independent problem meant the split could not have isolated eyes even if
    the signal had been clean: at any azimuth off a dead-on 90 the mesh's true
    left/right symmetry axis does not project to a vertical screen line, so
    "which half is which eye" was already the wrong question.

    Both problems disappear by building each eye ALONE and counting its own
    pixels against bare skin, wherever on screen it lands. No axis assumption,
    no other feature's contrast to hide behind -- which is exactly what let
    this version catch the defect the first version could not see.
    """
    ramps = ramps or load_palette()
    roster = roster if roster is not None else C.ROSTER
    cam = DimetricCamera(PORTRAIT_AZIMUTH, elevation_deg=PORTRAIT_ELEVATION)
    out = []
    for spec in roster:
        bare_mesh = merge(chest(spec.shirt, spec.bulk), C.head(spec.skin),
                          C.hair(spec.hair_style, spec.hair_mat))
        span, centre = frame_single(bare_mesh, cam)
        _, plain = render_sprite(bare_mesh, PORTRAIT_AZIMUTH, TARGET, FACTOR, ramps,
                                 span=span, centre=centre)
        for side, sx in (("left", -0.072), ("right", 0.072)):
            one_eye = merge(bare_mesh, _eye_box(sx, spec.skin))
            _, eyed = render_sprite(one_eye, PORTRAIT_AZIMUTH, TARGET, FACTOR, ramps,
                                    span=span, centre=centre)
            n = sum(1 for a, b in zip(plain, eyed)
                   if a is not None and b is not None and a != b)
            if n < MIN_EYE_PIXELS:
                out.append(f"{spec.name}: {side} eye renders {n} px against bare "
                          f"skin (need {MIN_EYE_PIXELS}) -- occluded or off-frame")
    return out


def check_distinct(reports: dict[str, bytes]) -> list[str]:
    """No two characters render the same PNG bytes.

    The same failure `furnish.check_distinct` was written for, applied to
    portraits: two names, two files, one picture. Whole-file hashing rather
    than a silhouette diff, because unlike a prop's 8 directions a portrait is
    ONE image and the whole point is that it differs by more than outline.
    """
    seen: dict[str, list[str]] = {}
    for name, data in reports.items():
        seen.setdefault(hashlib.sha256(data).hexdigest(), []).append(name)
    return [f"{', '.join(names)} render identical portraits"
           for names in seen.values() if len(names) > 1]


def check_determinism(roster=None, ramps=None) -> list[str]:
    """Same spec, rendered twice, byte-identical.

    Directly guards the defect that motivated backporting the sorted-index
    material-id fix into `render_batch.render_sprite`: under `hash(m) % 251`
    this check would fail roughly one run in four (birthday bound over ~12
    materials, 251 buckets), and which character failed would change between
    runs because Python randomises string hashing per process. It cannot fail
    now for that reason; if it ever does again, the id scheme regressed.
    """
    ramps = ramps or load_palette()
    roster = roster if roster is not None else C.ROSTER
    out = []
    for spec in roster:
        a, _ = render_bust(spec, ramps=ramps)
        b, _ = render_bust(spec, ramps=ramps)
        if a.tobytes() != b.tobytes():
            out.append(f"{spec.name}: two renders of the same spec differ")
    return out


def check_palette_exact(pngs: dict[str, list], ramps=None) -> list[str]:
    ramps = ramps or load_palette()
    out = []
    for name, px in pngs.items():
        rep = audit(px, ramps)
        if rep["off_palette"]:
            out.append(f"{name}: {rep['off_palette_pct']}% off-palette "
                      f"({rep['off_palette']} px)")
    return out


def check(roster=None) -> list[str]:
    ramps = load_palette()
    roster = roster if roster is not None else C.ROSTER
    pngs, blobs = {}, {}
    for spec in roster:
        img, px = render_bust(spec, ramps=ramps)
        pngs[spec.name] = px
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format="PNG")
        blobs[spec.name] = buf.getvalue()

    problems = []
    problems += check_palette_exact(pngs, ramps)
    problems += check_distinct(blobs)
    problems += check_eyes_visible(roster, ramps)
    problems += check_determinism(roster, ramps)
    return problems


# --- build ---------------------------------------------------------------------

def build(roster=None, target: int = TARGET, factor: int = FACTOR) -> dict:
    ramps = load_palette()
    roster = roster if roster is not None else C.ROSTER
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for spec in roster:
        img, _ = render_bust(spec, target, factor, ramps)
        img.save(OUT_DIR / f"{spec.name}.png")
        manifest[spec.name] = {"file": f"{spec.name}.png", "size": [target, target]}
    (OUT_DIR / "portraits.json").write_text(json.dumps(manifest, indent=2),
                                            encoding="utf-8")
    return manifest


def demo(roster=None, out: Path | None = None) -> str:
    """Contact sheet: the whole roster, at 3x nearest for review."""
    from PIL import Image
    roster = roster if roster is not None else C.ROSTER
    ramps = load_palette()
    imgs = [(spec.name, render_bust(spec, ramps=ramps)[0]) for spec in roster]
    w, h = imgs[0][1].size
    cols = 5
    rows = (len(imgs) + cols - 1) // cols
    pad, label_h = 6, 12
    sheet = Image.new("RGBA", (cols * (w + pad) + pad, rows * (h + label_h + pad) + pad),
                      (30, 26, 32, 255))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(imgs):
        x = pad + (i % cols) * (w + pad)
        y = pad + (i // cols) * (h + label_h + pad)
        sheet.alpha_composite(im, (x, y))
        d.text((x, y + h + 1), name, fill=(196, 190, 200))
    sheet = sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST)
    path = (out or ROOT / "proof") / "portraits.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path)
    return str(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--target", type=int, default=TARGET)
    args = ap.parse_args()

    if args.check:
        problems = check()
        if problems:
            for p in problems:
                print(f"  BLOCKER  {p}", file=sys.stderr)
            print(f"\n{len(problems)} problem(s)")
            return 1
        print(f"{len(C.ROSTER)} portraits: palette-exact, distinct, both eyes "
              f"visible on every one, deterministic")
        return 0

    if args.demo:
        print(demo())
        return 0

    manifest = build(target=args.target)
    print(f"{len(manifest)} portraits -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
