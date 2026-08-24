#!/usr/bin/env python3
"""A local web UI for stage 1 (`concept.py`), so `--ip-scale` and a reference
image can be eyeballed interactively instead of round-tripping the CLI.

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
session, the same one-pipe-per-session model `factory.py` uses for a batch.
Nothing here is a new code path: every generation goes through
`concept.concept()` and every fitness read goes through
`concept.check_concept_fitness()`, so what this UI shows is exactly what a
batch run would produce for the same inputs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "out" / "concept_ui"

_pipe_holder = {}


def _get_pipe():
    if "pipe" not in _pipe_holder:
        import concept as C
        _pipe_holder["pipe"] = C._pipe()
    return _pipe_holder["pipe"]


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


def build_app():
    import gradio as gr
    import concept as C

    with gr.Blocks(title="Cozy Coffee -- Stage 1 concept generation") as app:
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
            with gr.Column():
                raw_out = gr.Image(label="Raw render")
                matte_out = gr.Image(label="Matted (stage-2 input)", image_mode="RGBA")
                status = gr.Textbox(label="Fitness gate", lines=4)

        kind.change(lambda k: gr.update(visible=(k == "custom")),
                    inputs=kind, outputs=custom_group)

        go.click(generate,
                  inputs=[kind, subject, reference, ip_scale, seed, steps, size,
                          positive_override, negative_override],
                  outputs=[raw_out, matte_out, status])
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
