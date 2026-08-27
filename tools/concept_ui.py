#!/usr/bin/env python3
"""A local web UI for stage 1 (`concept.py`), so `--ip-scale` and a reference
image can be eyeballed interactively instead of round-tripping the CLI --
and a "Continue" step that carries a passing concept the rest of the way
through stages 2-5 (`lift.py`, `ingest.py`, `render_batch.py`) to a sprite
contact sheet, so a whole subject can be taken from prompt to reviewable
asset without leaving the browser.

Three tabs now, because a generation is not the only thing this repo makes:

    Concept -> sprite     stage 1, then stages 2-5 on the same concept
    Drawn: chrome + tiles `ui_chrome.py` and `tileset.py` -- no GPU, no seed
    Export to Godot       `package_godot.py` + two headless Godot passes

The second tab exists for a reason worth stating. Everything on the first is
slow and uncertain and wants watching; the drawn producers are neither, and
being reachable only from a terminal made the half of the library that
always works the half nobody could see.

`PIPELINE.md`'s "Reference images" section measured that `--ip-scale`'s
right value depends on how much the reference's own material/shape conflicts
with the prompt -- there is no single good default, only a per-reference one.
That is exactly the kind of judgement call this repo puts in front of a
human rather than automating (`PIPELINE.md`'s stage 9), so it gets an
interface a human can actually turn a knob in, not another CLI flag to
re-invoke blind.

    pip install gradio    # not in tools/requirements.txt, same reason torch
                           # and diffusers aren't -- installed once per machine
    python tools/concept_ui.py                # localhost only
    python tools/concept_ui.py --lan           # reachable from other devices
                                                # on the same network (phone,
                                                # tablet) -- binds 0.0.0.0
                                                # instead of 127.0.0.1

Opens http://127.0.0.1:7860 (or the machine's LAN IP with --lan). SDXL loads
on the first Generate click (10-20s) and stays resident for the rest of the
session, the same one-pipe-per-session model `factory.py` uses for a batch;
TripoSR loads the same way on the first Continue click. Nothing here is a
new code path: every generation goes through `concept.concept()`, every
fitness read through `concept.check_concept_fitness()`, and Continue calls
`lift.lift()` / `ingest.ingest()` / `render_batch.py` / `review_queue.py`
directly -- the same functions `factory.py` calls for a batch, so what this
UI produces is exactly what a batch run would produce for the same inputs.

Generate writes scratch output to `out/concept_ui/` only, overwritten each
run. Continue is the promotion step: it copies the current scratch concept
into `out/concept/<name>.png` and writes mesh/sprites under `out/mesh/` and
`out/sprites/` using `factory.py`'s own naming convention, so a subject
worked up here is recognised as already-done stage 1 (and further) if it's
later added to a `factory.py` subject list under the same name.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "out" / "concept_ui"
CONCEPT_DIR = ROOT / "out" / "concept"
MESH_DIR = ROOT / "out" / "mesh"
SPRITE_DIR = ROOT / "out" / "sprites"
REVIEW_DIR = ROOT / "review"

_pipe_holder = {}
_lift_model_holder = {}


def _get_pipe():
    if "pipe" not in _pipe_holder:
        import concept as C
        _pipe_holder["pipe"] = C._pipe()
    return _pipe_holder["pipe"]


def _get_lift_model():
    if "model" not in _lift_model_holder:
        import lift as L
        _lift_model_holder["model"] = L._model()
    return _lift_model_holder["model"]


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (text or "").strip().lower()).strip("_")
    return s or "untitled"


def generate(kind, subject, reference_files, ip_scale, seed, steps, size,
              positive_override, negative_override):
    import concept as C

    custom = (kind == "custom")
    if custom:
        if not (positive_override or "").strip():
            return None, None, "Custom mode needs a positive prompt."
    elif not subject or not subject.strip():
        return None, None, "Enter a subject / prompt first."

    pipe = _get_pipe()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Overwritten each run rather than accumulated -- this is a scratch
    # interface for iterating on one generation at a time, not a batch
    # output directory. `factory.py subjects.yaml` is still what produces
    # the library.
    out = OUT_DIR / "current.png"

    refs = reference_files or []
    kwargs = {}
    if refs:
        kwargs["reference"] = refs
        kwargs["ip_scale"] = float(ip_scale)
    if custom:
        kwargs["positive_override"] = positive_override.strip()
        if (negative_override or "").strip():
            kwargs["negative_override"] = negative_override.strip()
    else:
        kwargs["kind"] = kind

    label = (subject or "").strip() or "(custom)"
    png = C.concept(label, seed=int(seed), steps=int(steps), size=int(size),
                     out=out, pipe=pipe, **kwargs)
    raw = png.with_name(png.stem + "_raw.png")
    msgs = C.check_concept_fitness(png)
    status = ("PASSES the stage-2 fitness gate" if not msgs
              else "FAILS the stage-2 fitness gate:\n" + "\n".join(f"- {m}" for m in msgs))
    return str(raw), str(png), status


def continue_to_sprites(subject, height):
    """Take the current scratch concept the rest of the way: lift -> ingest
    -> render -> contact sheet, using the same functions `factory.py` calls
    for a batch subject. Not gated on the fitness gate having passed --
    `lift`/`ingest` will simply do a worse job on a concept that failed it,
    the same way a human running the CLI by hand could choose to anyway.
    """
    import lift as L
    import ingest as I
    from mesh import save_obj

    src = OUT_DIR / "current.png"
    if not src.exists():
        return None, "Generate a concept first."
    if not height:
        return None, "Set a height (in tile units -- 1.0 is roughly counter " \
                      "height) before continuing; ingest.fit() has no other " \
                      "way to tell a teapot from a table."

    name = _slug(subject)
    CONCEPT_DIR.mkdir(parents=True, exist_ok=True)
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)

    # Promotes the scratch result into the layout `factory.py` expects, so a
    # subject worked up here is recognised as already-done if it's later
    # added to a subject list under this same name.
    shutil.copyfile(src, CONCEPT_DIR / f"{name}.png")
    raw_src = OUT_DIR / "current_raw.png"
    if raw_src.exists():
        shutil.copyfile(raw_src, CONCEPT_DIR / f"{name}_raw.png")
    json_src = OUT_DIR / "current.json"
    if json_src.exists():
        shutil.copyfile(json_src, CONCEPT_DIR / f"{name}.json")

    lines = []
    try:
        model = _get_lift_model()
        raw_obj = MESH_DIR / f"{name}.obj"
        L.lift(CONCEPT_DIR / f"{name}.png", out=raw_obj, model=model)
    except Exception as e:
        return None, f"stage 2 (lift) failed: {type(e).__name__}: {e}"

    try:
        mesh, report = I.ingest(raw_obj, height=float(height))
    except Exception as e:
        return None, f"stage 3 (ingest) failed: {type(e).__name__}: {e}"
    bound_obj = MESH_DIR / f"{name}_bound.obj"
    save_obj(mesh, bound_obj)
    g = report["geometry"]
    lines.append(f"lift + ingest: height {g['height']:.3f}, footprint "
                 f"{g['footprint']:.3f}")
    lines += [f"warning: {w}" for w in report["warnings"]]

    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "render_batch.py"),
         "--mesh", str(bound_obj), "--name", name,
         "--out", str(SPRITE_DIR), "--target", "64"],
        capture_output=True, text=True, timeout=300, cwd=str(ROOT))
    if proc.returncode != 0:
        lines.append("stage 4-5 (render) failed:")
        lines.append(proc.stderr[-1000:])
        return None, "\n".join(lines)
    lines.append(f"8 sprites -> {SPRITE_DIR}")

    # Same contact-sheet builder `factory.py` calls at the end of a batch --
    # writes review/sheet.png, overwriting whatever the last build put there.
    rel_pattern = str(SPRITE_DIR.relative_to(ROOT) / f"{name}_dir*.png")
    review_proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "review_queue.py"),
         "build", rel_pattern],
        capture_output=True, text=True, cwd=str(ROOT))
    if review_proc.returncode != 0:
        lines.append("review_queue.py build failed:")
        lines.append(review_proc.stderr[-500:])
        return None, "\n".join(lines)

    sheet = REVIEW_DIR / "sheet.png"
    lines.append(f"contact sheet -> {sheet}")
    return str(sheet), "\n".join(lines)


EXAMPLES_MD = """
**Prop** (default) -- a short noun phrase, no camera language needed;
`STYLE` adds "3d render of ..., single isolated object, centred,
three-quarter view..." automatically:

- `a rustic stoneware teapot`
- `a woven wicker basket`
- `a small brass table lamp with a fabric shade`

**Character** -- same idea, but for anything with a face, a pose, or a
name. Naming a specific franchise character still risks the collage
failure on very iconic ones (Mario-tier fame) even with this fix -- an
original description is the safer bet:

- `a stout dwarf blacksmith with a braided beard and a leather apron`
- `a small green frog wearing a tattered cloak and carrying a rapier`
  (not "Frog from Chrono Trigger" -- naming the source pulls harder
  toward fan-art/character-sheet imagery than describing the design does)

**Custom** -- for anything that doesn't fit a single isolated object shot
at all: a flat icon, a different camera angle, a specific art style.
Positive prompt replaces `STYLE` entirely (write the whole thing,
including composition/background/lighting); negative prompt is optional
and replaces `NEGATIVE` entirely if given, otherwise falls back to the
prop default:

- Positive: `flat 2d icon of a coffee bean, vector style, centred,
  plain white background, no shading, no gradient`
"""


def run_procedural(target: int, tile_width: int):
    """The two producers that need no GPU, no seed and no prompt.

    They live behind a button here for a plain reason: everything else in
    this app is a generation, and a generation is slow, uncertain and worth
    watching. `ui_chrome` and `tileset` are neither -- they are deterministic
    and take a couple of seconds -- but they were only reachable from a
    terminal, which made the half of the library that always works the half
    nobody could see. `ART_CRITIQUE.md` records the same asymmetry in the art
    itself: the pipeline makes things, and the abstractions are drawn.

    Returns (chrome preview, room corner, log).
    """
    import ui_chrome
    import tileset as T
    from pixelize import load_palette

    lines, ramps = [], load_palette()
    try:
        results = [ui_chrome.build(name, target / 64.0, ramps)
                   for name in ui_chrome.CHROME]
        ok = sum(1 for r in results if r["ok"])
        lines.append(f"chrome: {ok}/{len(results)} pieces at {target}px")
        for r in results:
            if not r["ok"]:
                lines.append(f"  FAIL {r['name']}: {r['detail']}")
    except Exception as e:
        lines.append(f"chrome failed: {type(e).__name__}: {e}")

    try:
        rc = T.build(tile_width, proof=True)
        lines.append(f"tiles: {'ok' if rc == 0 else 'PROBLEMS -- see console'}"
                     f" at {tile_width}px")
    except Exception as e:
        lines.append(f"tiles failed: {type(e).__name__}: {e}")

    chrome_png = ROOT / "out" / "ui" / "_preview.png"
    try:
        import preview_ui
        chrome_png = preview_ui.build(3)
    except Exception as e:
        lines.append(f"chrome preview failed: {type(e).__name__}: {e}")

    corner = ROOT / "out" / "tiles" / "_room_corner.png"
    return (str(chrome_png) if chrome_png.exists() else None,
            str(corner) if corner.exists() else None,
            "\n".join(lines))


def run_export():
    """Stage + import + build, straight through to Godot resources."""
    import export_godot as E
    import package_godot as P
    lines = []
    try:
        build = P.stage()
        lines.append(P.summarise(build))
    except Exception as e:
        return f"staging failed: {type(e).__name__}: {e}"
    godot = E.find_godot(None)
    if not godot.exists():
        return "\n".join(lines + [
            f"staged, but no Godot binary at {godot} -- set $GODOT_BIN or "
            f"run tools/export_godot.py --godot-bin PATH to finish the "
            f"import and build passes."])
    try:
        E.run_godot(godot, ["--import"])
        E.run_godot(godot, ["--script", "build_all.gd"])
    except SystemExit as e:
        return "\n".join(lines + [str(e)])
    problems = E.check_nine_slice_roundtrip(build)
    lines += problems or ["nine-slice margins match the drawn insets"]
    n = len(list((E.PROJECT_DIR / "resources").rglob("*.tres")))
    lines.append(f"{n} resources -> {E.PROJECT_DIR / 'resources'}")
    return "\n".join(lines)


def build_app():
    import gradio as gr
    import concept as C

    with gr.Blocks(title="Cozy Coffee -- asset factory") as app:
      with gr.Tab("Concept -> sprite"):
        gr.Markdown(
            "## Stage 1: concept art\n"
            "Prompt alone, or prompt + one or more reference images "
            "conditioned via IP-Adapter. Same code path as `factory.py` "
            "and the CLI -- nothing generated here is a special case.")
        with gr.Row():
            with gr.Column():
                kind = gr.Radio(["prop", "character", "custom"], value="prop",
                                 label="Kind",
                                 info="Prop and character pick a tuned "
                                      "negative prompt for you (see Examples "
                                      "below); custom hands you full control.")
                subject = gr.Textbox(label="Subject / prompt",
                                      placeholder="a ceramic teapot")
                with gr.Group(visible=False) as custom_group:
                    positive_override = gr.Textbox(
                        label="Positive prompt (replaces STYLE entirely)",
                        lines=3,
                        placeholder="3d render of a coffee bean icon, flat "
                                    "vector style, centred, plain white "
                                    "background, no shading")
                    negative_override = gr.Textbox(
                        label="Negative prompt (optional -- replaces NEGATIVE "
                              "entirely if given)",
                        lines=2)
                reference = gr.File(label="Reference image(s), optional",
                                     file_count="multiple",
                                     file_types=["image"])
                ip_scale = gr.Slider(
                    0.0, 1.0, value=C.DEFAULT_IP_SCALE, step=0.05,
                    label="ip_scale -- reference influence (applies to all "
                          "references)",
                    info="0.3-0.5 usually nudges shape while the prompt's "
                         "own material holds; 0.6+ can override it "
                         "entirely. Measured on one pair, not universal -- "
                         "watch the raw output and adjust by eye. Multiple "
                         "references each get their own conditioning slot, "
                         "not a blend.")
                with gr.Row():
                    seed = gr.Number(value=1, precision=0, label="seed")
                    steps = gr.Number(value=28, precision=0, label="steps")
                    size = gr.Number(value=1024, precision=0, label="size")
                go = gr.Button("Generate", variant="primary")
                with gr.Accordion("Examples / prompt tips", open=False):
                    gr.Markdown(EXAMPLES_MD)
                gr.Markdown("---\n### Stage 2-5: mesh + sprites")
                height = gr.Number(
                    value=0.28, label="height (tile units)",
                    info="How tall the object is relative to a 1.0-tile "
                         "person -- ingest.fit() scales the mesh by this, "
                         "not by its longest axis, so a wide table doesn't "
                         "come out short. A mug is roughly 0.12, a chair "
                         "back roughly 0.9, a counter roughly 1.0.")
                cont = gr.Button("Continue -> mesh + sprites")
            with gr.Column():
                raw_out = gr.Image(label="Raw render")
                matte_out = gr.Image(label="Matted (stage-2 input)", image_mode="RGBA")
                status = gr.Textbox(label="Fitness gate", lines=4)
                sheet_out = gr.Image(label="Sprite contact sheet (8 directions)")
                sprite_status = gr.Textbox(label="Stage 2-5", lines=6)

        kind.change(lambda k: gr.update(visible=(k == "custom")),
                    inputs=kind, outputs=custom_group)

        go.click(generate,
                  inputs=[kind, subject, reference, ip_scale, seed, steps, size,
                          positive_override, negative_override],
                  outputs=[raw_out, matte_out, status])
        cont.click(continue_to_sprites, inputs=[subject, height],
                   outputs=[sheet_out, sprite_status])

      with gr.Tab("Drawn: chrome + tiles"):
        gr.Markdown(
            "## The half that needs no model\n"
            "UI chrome and ground tiles are **drawn**, not generated -- see "
            "`ART_CRITIQUE.md`, \"Icons split by whether they depict a "
            "thing\". A speech bubble and a floor tile are geometry with a "
            "semantic role, so SDXL renders them as photographs of "
            "something frame-shaped and a few lines of code render them "
            "correctly, at any size, on every run.\n\n"
            "No GPU, no seed, a couple of seconds. Every piece is held to "
            "the same speckle and palette checks the generated icons pass, "
            "and the tiles additionally prove their own tiling: a 3x3 "
            "coverage count per floor type, a 3-tile run per wall, and a "
            "room corner rebuilt from `tileset.json` alone and required to "
            "be pixel-identical to the projected one.")
        with gr.Row():
            chrome_target = gr.Number(value=64, precision=0,
                                      label="icon size (px)")
            tile_w = gr.Number(value=64, precision=0,
                               label="tile width (px, multiple of 4)",
                               info="Height is half. A width that is not a "
                                    "multiple of 4 puts the lattice step on "
                                    "half pixels and is rejected.")
        draw_go = gr.Button("Draw chrome + tiles", variant="primary")
        with gr.Row():
            chrome_out = gr.Image(label="UI: generated icons and drawn chrome")
            corner_out = gr.Image(label="Tiles: room corner")
        draw_status = gr.Textbox(label="Result", lines=8)
        draw_go.click(run_procedural, inputs=[chrome_target, tile_w],
                      outputs=[chrome_out, corner_out, draw_status])

      with gr.Tab("Export to Godot"):
        gr.Markdown(
            "## Stage 10: engine export\n"
            "Stages every producer -- props, animation sheets, UI, tiles -- "
            "then runs Godot headless twice: an import pass so the PNGs "
            "become real file-backed textures, and a build pass that writes "
            "`SpriteFrames`, `StyleBoxTexture` and `TileSet` resources.\n\n"
            "Needs a Godot 4.3 binary (`$GODOT_BIN`, or the portable build "
            "at the path `export_godot.py` names). Without one this still "
            "stages the files and says so rather than failing.")
        export_go = gr.Button("Stage + import + build", variant="primary")
        export_status = gr.Textbox(label="Result", lines=12)
        export_go.click(run_export, inputs=None, outputs=export_status)

    return app


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lan", action="store_true",
                     help="bind 0.0.0.0 instead of 127.0.0.1, reachable from "
                          "other devices on the same network")
    ap.add_argument("--port", type=int, default=7860)
    args = ap.parse_args()

    app = build_app()
    host = "0.0.0.0" if args.lan else "127.0.0.1"
    app.launch(inbrowser=not args.lan, server_name=host, server_port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
