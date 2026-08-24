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
    python tools/concept_ui.py

Opens http://127.0.0.1:7860. SDXL loads on the first Generate click (10-20s)
and stays resident for the rest of the session, the same one-pipe-per-session
model `factory.py` uses for a batch. Nothing here is a new code path: every
generation goes through `concept.concept()` and every fitness read goes
through `concept.check_concept_fitness()`, so what this UI shows is exactly
what a batch run would produce for the same inputs.
"""
from __future__ import annotations

import sys
import tempfile
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


def generate(subject, reference_path, ip_scale, seed, steps, size):
    import concept as C

    if not subject or not subject.strip():
        return None, None, "Enter a subject / prompt first."

    pipe = _get_pipe()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Overwritten each run rather than accumulated -- this is a scratch
    # interface for iterating on one generation at a time, not a batch
    # output directory. `factory.py subjects.yaml` is still what produces
    # the library.
    out = OUT_DIR / "current.png"

    kwargs = {}
    if reference_path:
        kwargs["reference"] = reference_path
        kwargs["ip_scale"] = float(ip_scale)

    png = C.concept(subject.strip(), seed=int(seed), steps=int(steps),
                     size=int(size), out=out, pipe=pipe, **kwargs)
    raw = png.with_name(png.stem + "_raw.png")
    msgs = C.check_concept_fitness(png)
    status = ("PASSES the stage-2 fitness gate" if not msgs
              else "FAILS the stage-2 fitness gate:\n" + "\n".join(f"- {m}" for m in msgs))
    return str(raw), str(png), status


def build_app():
    import gradio as gr
    import concept as C

    with gr.Blocks(title="Cozy Coffee -- Stage 1 concept generation") as app:
        gr.Markdown(
            "## Stage 1: concept art\n"
            "Prompt alone, or prompt + a reference image conditioned via "
            "IP-Adapter. Same code path as `factory.py` and the CLI -- "
            "nothing generated here is a special case.")
        with gr.Row():
            with gr.Column():
                subject = gr.Textbox(label="Subject / prompt",
                                      placeholder="a ceramic teapot")
                reference = gr.Image(label="Reference image (optional)",
                                      type="filepath")
                ip_scale = gr.Slider(
                    0.0, 1.0, value=C.DEFAULT_IP_SCALE, step=0.05,
                    label="ip_scale -- reference influence",
                    info="0.3-0.5 usually nudges shape while the prompt's "
                         "own material holds; 0.6+ can override it "
                         "entirely. Measured on one pair, not universal -- "
                         "watch the raw output and adjust by eye.")
                with gr.Row():
                    seed = gr.Number(value=1, precision=0, label="seed")
                    steps = gr.Number(value=28, precision=0, label="steps")
                    size = gr.Number(value=1024, precision=0, label="size")
                go = gr.Button("Generate", variant="primary")
            with gr.Column():
                raw_out = gr.Image(label="Raw render")
                matte_out = gr.Image(label="Matted (stage-2 input)", image_mode="RGBA")
                status = gr.Textbox(label="Fitness gate", lines=4)

        go.click(generate, inputs=[subject, reference, ip_scale, seed, steps, size],
                  outputs=[raw_out, matte_out, status])
    return app


def main() -> int:
    app = build_app()
    app.launch(inbrowser=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
