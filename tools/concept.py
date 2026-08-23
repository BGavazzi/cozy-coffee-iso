#!/usr/bin/env python3
"""Stage 1: a concept image of one prop, matted, fit for stage 2 to lift.

`PIPELINE.md` has listed this stage since the first pass and nothing had ever
run it. What makes it more than a call to a diffusion model is that stage 2's
*input* contract is narrow and every part of it is measurable on the PNG:

  - one object, fully inside the frame -- an image-to-3D model reconstructs
    what it can see, so a cropped object is a cropped mesh and no amount of
    `ingest` puts the missing half back;
  - one object, not two -- stage 2 has no way to be told which is the subject;
  - filling enough of the frame to carry detail, and not so much that it
    crowds the edge;
  - a matte that is actually decided, because a soft or uncertain alpha
    becomes a fringe of backdrop-coloured geometry.

So this file is a generator and a gate, in the shape the rest of the repo
already uses: `concept()` proposes, `check_concept_fitness()` grades.

## Two measured failures, and why the backdrop is not a prompt problem

The first version asked SDXL for "a plain seamless light grey backdrop" and
thresholded the object out of it by colour distance. That cannot work, and the
sweep says so precisely: on a grey stoneware teapot, below a tolerance of 0.11
the soft ground shadow joins the pot into one mass that reaches the frame edge,
and by 0.14 the pot's own lid has started dissolving into the backdrop. The two
failures cross before either clears. **There is no threshold.**

The second version derived a chroma key from the palette -- searching sRGB for
the colour furthest from all 37 palette colours, which is a vivid violet at
dE 0.270, five times the tolerance, and notably NOT the conventional green or
magenta, because green sits on `foliage` and magenta on `rose`. It was a good
derivation and it failed on contact with the model: asking for a purple
backdrop produced *a purple teapot*. The colour word bled onto the subject, and
the separation check reported the object coming within dE 0.121 of its own
background.

Grey fails by similarity, chroma fails by bleed, and both are failures of
**threshold matting** rather than of the prompt. So the backdrop is neither
asked for nor thresholded: the image is segmented, which is what every
image-to-3D pipeline does with its input anyway. The checks then read the alpha
channel, where "can this be cut out" is not an inference from colour but the
question the matte already answered.

The chroma-key search is deleted rather than kept. It was a correct answer to
the wrong question, and leaving it in the file would make it look like a
setting.

    python tools/concept.py "a rustic stoneware teapot" --seed 1 -o out/x.png
    python tools/concept.py --check out/x.png

## Reference images ("examples")

`--reference PATH` conditions generation on an image as well as the prompt,
via SDXL IP-Adapter (`h94/IP-Adapter`, ~1.2 GB, downloaded once to the same
HF cache as the base model). This is deliberately IP-Adapter and not
img2img: img2img denoises the reference's own layout, which imports whatever
camera angle and framing the reference happened to have -- exactly the
per-object drift `STYLE`'s fixed camera clause exists to prevent (see the
module docstring above). IP-Adapter instead conditions the UNet on the
reference's *appearance* (material, colour, silhouette language) while the
text prompt and `STYLE` still own composition, so a reference photo shot
head-on at eye level does not leak its camera into the render the way an
img2img pass would.

    python tools/concept.py "a ceramic mug" --reference photos/mug.jpg \
        --ip-scale 0.45 --seed 1 -o out/x.png

`--ip-scale` (0-1, default 0.45) trades off prompt vs. reference. Measured
directly, one reference (a matte-ceramic teapot photo with a copper handle)
against one prompt that names a conflicting material ("a glass vase"), same
seed, sweeping the scale:

| scale | result |
|---|---|
| 0.3 | glass preserved; body proportions alone pull toward the reference's bulbous shape |
| 0.4-0.5 | glass still preserved; the reference's handle(s) start appearing on the vase |
| 0.6 | material overridden -- "glass vase" renders in opaque matte ceramic |
| 0.85 | near-reproduction of the reference, copper accent colour included; the prompt's material and object identity are both lost |

The transition from "reference nudges shape" to "reference overrides the
prompt's own material" falls between 0.5 and 0.6 for this pair, so 0.45 sits
just under it -- visible reference influence while the prompt still wins on
what the object *is*. This is one reference/prompt pair, not the swept
bracket the fitness floors above have; a reference whose material doesn't
conflict with the prompt (the common case -- most references will be roughly
what's being asked for) will tolerate a higher scale before losing the
prompt. Treat 0.45 as a starting point to raise or lower by eye, not a
calibrated constant.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# SDXL and TripoSR together are ~8 GB, and the default cache
# (%USERPROFILE%\.cache\huggingface) sits on the same drive as everything
# else on this machine. It has failed once already -- a snapshot with a blob
# missing from an interrupted download, `_create_symlink` raising
# `FileNotFoundError` on a file that should have been there -- while a
# complete, working cache sat unused one drive letter away. Set here rather
# than left as an undocumented thing every session has to remember to export:
# `setdefault` so an operator's own HF_HOME, if any, still wins.
import os as _os
_os.environ.setdefault("HF_HOME", str(ROOT.parent / ".hf-cache"))

# Fixed for every prop, because the factory's argument is that consistency
# comes from the setup rather than from the prompt. A prompt that varies per
# object is a prompt that produces a different camera per object, which is the
# drift `PIPELINE.md` rejects 2D generation for in the first place.
#
# "3d render of" rather than "product photograph of" on measurement, not
# taste: the photographic phrasing brought a vignette with it every time --
# 0.110 and 0.109 of lightness across the backdrop on two prompt variants,
# against a 0.100 cap -- and the render phrasing came in flat. The camera
# clause matters for a reason that is easy to state backwards: it does NOT set
# the sprite's projection, since stage 5 re-renders the mesh at its own fixed
# dimetric camera. It decides which surfaces stage 2 ever sees. An eye-level
# photograph hides the top of a lid, and a surface no view contains is a
# surface the reconstruction invents.
STYLE = ("3d render of {subject}, single isolated object, centred, "
         "high three-quarter view looking down, plain flat neutral "
         "background, soft even lighting, no cast shadow, no ground plane, "
         "full object in frame with generous margin")

NEGATIVE = ("cropped, cut off, out of frame, multiple objects, group, "
            "cast shadow, drop shadow, ground plane, floor, table, "
            "vignette, gradient background, busy background, "
            "scene, room, hands, people, text, watermark, signature, "
            "blurry, depth of field, bokeh, reflection, mirror, eye level")

MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
MATTE_MODEL = "u2net"
IP_ADAPTER_REPO = "h94/IP-Adapter"
IP_ADAPTER_SUBFOLDER = "sdxl_models"
IP_ADAPTER_WEIGHT = "ip-adapter_sdxl.bin"
DEFAULT_IP_SCALE = 0.45  # see "Reference images" above for the measured sweep

# Stage-2 fitness floors.
MIN_FILL = 0.12          # object share of the frame
MAX_FILL = 0.72
EDGE_MARGIN = 0.02       # clear border, as a fraction of the short side
MAX_SECOND_BLOB = 0.15   # runner-up mass, relative to the object itself
MAX_SOFT_ALPHA = 0.10    # share of the matte that is neither in nor out
DETACHED_SOFT_FLOOR = 0.65  # of the soft pixels that trip MAX_SOFT_ALPHA,
# the share with no confident pixel nearby. Bracketed against the 31-subject
# C1 set: fern and bicycle (thin fronds / spokes, real generations, false
# rejections) measured 36-47%; bottle (glass, also a false rejection) 54%;
# bread_loaf, croissant and book (duplicate ghost instances, a genuine
# segmentation failure) measured 73-89%. 65% sits in the 19-point gap between
# the worst false rejection and the best genuine defect.

_SESSION = None


def _pipe(device: str = "cuda"):
    """Load SDXL once, with the memory budget this machine actually has.

    8 GB is enough for SDXL at fp16 only with the UNet and the text encoders
    taking turns in VRAM, which is what `enable_model_cpu_offload` arranges. It
    costs perhaps a third of the speed and it is the difference between running
    and not running, so it is not optional here.
    """
    import torch
    from diffusers import StableDiffusionXLPipeline
    pipe = StableDiffusionXLPipeline.from_pretrained(
        MODEL, torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
    if device == "cuda":
        pipe.enable_model_cpu_offload()
        # diffusers 0.40 moved slicing onto the VAE; the pipeline-level
        # shortcut is gone. Guarded rather than pinned, because this file has
        # to keep working across a library the repo does not control.
        if hasattr(pipe, "enable_vae_slicing"):
            pipe.enable_vae_slicing()
        elif hasattr(getattr(pipe, "vae", None), "enable_slicing"):
            pipe.vae.enable_slicing()
    else:
        pipe = pipe.to(device)
    pipe.set_progress_bar_config(disable=True)
    pipe._ip_loaded = False
    pipe._cpu_offloaded = (device == "cuda")
    return pipe


def _set_reference(pipe, reference: Path | str | None) -> None:
    """Load or unload IP-Adapter on `pipe` so it matches whether this call has
    a reference image.

    Once loaded, diffusers' IP-Adapter cross-attention processors require an
    `ip_adapter_image` on every call to that pipeline -- so a shared pipe
    processing a mixed batch (some subjects with a reference, some without,
    which is the common case) has to toggle the adapter on and off per
    subject rather than load it once. The weight download is one-time and
    cached; re-attaching an already-downloaded adapter to the UNet costs no
    network time and is fast enough to do per-subject.

    `load_ip_adapter()` attaches a CLIP vision encoder that did not exist
    when `_pipe()` first called `enable_model_cpu_offload()`, so it never got
    an offload hook and sits wherever `from_pretrained` put it -- CPU, while
    everything else on this 8 GB card runs on CUDA. Confirmed the hard way:
    `RuntimeError: Input type (torch.cuda.HalfTensor) and weight type
    (torch.HalfTensor) should be the same` inside the encoder's first conv.
    Re-running `enable_model_cpu_offload()` after `load_ip_adapter()`
    re-attaches hooks to every current submodule, image encoder included.
    """
    have = getattr(pipe, "_ip_loaded", False)
    if reference and not have:
        pipe.load_ip_adapter(IP_ADAPTER_REPO, subfolder=IP_ADAPTER_SUBFOLDER,
                              weight_name=IP_ADAPTER_WEIGHT)
        if getattr(pipe, "_cpu_offloaded", False):
            pipe.enable_model_cpu_offload()
        pipe._ip_loaded = True
    elif not reference and have:
        pipe.unload_ip_adapter()
        pipe._ip_loaded = False


def matte(img):
    """Cut the object out. Returns RGBA.

    Runs on CPU through onnxruntime, which costs a second or two against the
    twenty-five that generation costs, so it is not worth contending with SDXL
    for VRAM.
    """
    global _SESSION
    from rembg import new_session, remove
    if _SESSION is None:
        _SESSION = new_session(MATTE_MODEL)
    return remove(img, session=_SESSION).convert("RGBA")


def concept(subject: str, seed: int = 1, steps: int = 28,
            size: int = 1024, out: Path | str | None = None,
            pipe=None, reference: Path | str | None = None,
            ip_scale: float = DEFAULT_IP_SCALE) -> Path:
    """One matted concept image, deterministic in `seed`.

    Deterministic because every other stage of this pipeline is, and a stage
    that is not reproducible cannot be bisected when the sprite three stages
    downstream comes out wrong. The un-matted render is kept beside it: when a
    matte goes wrong it is the only way to tell a bad segmentation from a bad
    generation, and those have opposite fixes.

    `reference`, if given, conditions generation on an image via IP-Adapter
    in addition to `subject`'s text prompt -- see the module docstring's
    "Reference images" section for why this is IP-Adapter rather than
    img2img.
    """
    import torch
    from PIL import Image
    pipe = pipe or _pipe()
    _set_reference(pipe, reference)
    kwargs = {}
    if reference:
        pipe.set_ip_adapter_scale(ip_scale)
        kwargs["ip_adapter_image"] = Image.open(reference).convert("RGB")
    g = torch.Generator(device="cpu").manual_seed(seed)
    img = pipe(prompt=STYLE.format(subject=subject),
               negative_prompt=NEGATIVE, num_inference_steps=steps,
               guidance_scale=6.5, width=size, height=size,
               generator=g, **kwargs).images[0]
    out = Path(out or ROOT / "out" / "concept" / f"{seed:03d}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out.with_name(out.stem + "_raw.png"))
    matte(img).save(out)
    out.with_suffix(".json").write_text(json.dumps(
        {"subject": subject, "seed": seed, "steps": steps, "size": size,
         "model": MODEL, "matte": MATTE_MODEL, "style": STYLE,
         "negative": NEGATIVE, "reference": str(reference) if reference else None,
         "ip_scale": ip_scale if reference else None}, indent=1))
    return out


def _blobs(fg, w, h):
    """4-connected components of the matte, biggest first.

    Returns [(size, pixels)], because every question below turns out to be
    about ONE of these rather than about the foreground as a whole. An earlier
    version measured frame contact over all foreground pixels and reported a
    teapot with two tiles of clear margin as "reaches the frame edge" -- the
    ground shadow had drifted into the border band. The shadow is foreground.
    It is not the object.
    """
    seen = bytearray(len(fg))
    out = []
    for start in range(len(fg)):
        if not fg[start] or seen[start]:
            continue
        stack, part = [start], []
        seen[start] = 1
        while stack:
            i = stack.pop()
            part.append(i)
            x, y = i % w, i // w
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if fg[j] and not seen[j]:
                        seen[j] = 1
                        stack.append(j)
        out.append((len(part), part))
    out.sort(key=lambda t: -t[0])
    return out


def check_concept_fitness(png: Path | str) -> list[str]:
    """Is this image something stage 2 can lift, measured on the matte.

    Every floor here is about the RECONSTRUCTION and not about whether the
    picture is attractive. Judging the picture is stage 9's job and a human's;
    judging whether it survives the next stage is exactly the mechanical
    question the ratchet exists to take off a human.

    An image with no alpha is matted on the way in, so the gate can be pointed
    at anything -- including the raw render saved beside each result, which is
    how a bad segmentation gets told apart from a bad generation.
    """
    from PIL import Image
    img = Image.open(png)
    if img.mode != "RGBA" or img.getchannel("A").getextrema() == (255, 255):
        img = matte(img.convert("RGB"))
    w, h = img.size
    a = list(img.getchannel("A").getdata())
    out = []

    # Alpha that is neither in nor out. A matte model is confident about most
    # pixels and hedges on a thin rim; a wide band of hedging means it never
    # found an object, and every hedged pixel becomes a fringe of
    # backdrop-coloured geometry once stage 2 lifts it.
    #
    # That is one cause of a wide hedge band, not the only one. C1 (31
    # subjects) found the same ratio tripped by fern and bicycle -- legitimate
    # generations whose subject is made of many thin edges, each contributing
    # its own ring of antialiased soft-alpha -- and by bottle, which is glass
    # and is supposed to be partly see-through. Ratio alone can't tell those
    # apart from bread_loaf and croissant, where SDXL drew a faint duplicate
    # instance the matte model couldn't commit to either way.
    #
    # The two causes have different SHAPES. A rim of soft pixels tracing a
    # fine silhouette stays close to the confident interior everywhere along
    # its length. A duplicate ghost or a low-contrast failure is its own
    # region, mostly far from anything the matte was ever sure about. Soft
    # pixels with no confident pixel within a few px of them are "detached";
    # the detached share separates the two causes cleanly on the 31-subject
    # set (see DETACHED_SOFT_FLOOR).
    soft_pts = [(i % w, i // w) for i, v in enumerate(a) if 24 < v < 232]
    inside = sum(1 for v in a if v >= 232)
    if inside and len(soft_pts) / inside > MAX_SOFT_ALPHA:
        interior = {(i % w, i // w) for i, v in enumerate(a) if v >= 232}
        rad = 3
        detached = 0
        for x, y in soft_pts:
            if not any((x + dx, y + dy) in interior
                      for dy in range(-rad, rad + 1)
                      for dx in range(-rad, rad + 1)):
                detached += 1
        frac = detached / len(soft_pts)
        if frac > DETACHED_SOFT_FLOOR:
            out.append(f"{Path(png).name}: {len(soft_pts) / inside:.0%} of "
                       f"the matte is half-transparent (cap "
                       f"{MAX_SOFT_ALPHA:.0%}), and {frac:.0%} of that has no "
                       f"confident pixel nearby (floor {DETACHED_SOFT_FLOOR:.0%}) "
                       f"-- a second, unresolved shape, not a fine edge")

    fg = bytearray(1 if v >= 128 else 0 for v in a)
    blobs = _blobs(fg, w, h)
    if not blobs:
        return out + [f"{Path(png).name}: nothing was segmented out of this "
                      f"image at all"]
    obj = blobs[0][1]

    fill = len(obj) / (w * h)
    if fill < MIN_FILL:
        out.append(f"{Path(png).name}: object fills {fill:.1%} of frame "
                   f"(floor {MIN_FILL:.0%}) -- too little resolution on the "
                   f"thing being reconstructed")
    elif fill > MAX_FILL:
        out.append(f"{Path(png).name}: object fills {fill:.1%} of frame "
                   f"(cap {MAX_FILL:.0%}) -- crowding the edge")

    m = max(1, int(min(w, h) * EDGE_MARGIN))
    if any((i % w) < m or (i % w) >= w - m
           or (i // w) < m or (i // w) >= h - m for i in obj):
        out.append(f"{Path(png).name}: object reaches the frame edge -- "
                   f"an image-to-3D model reconstructs what it can see, "
                   f"and a cropped object is a cropped mesh")

    # Against the OBJECT, not against the total. A stray speck is a second
    # component and will always exist at some size; a second *object* is a
    # component comparable to the first. Asking "how big is the runner-up
    # relative to the winner" separates those; "what share of the foreground
    # is the winner" does not.
    second = blobs[1][0] / max(1, blobs[0][0]) if len(blobs) > 1 else 0.0
    if second > MAX_SECOND_BLOB:
        out.append(f"{Path(png).name}: a second mass {second:.0%} the size of "
                   f"the main one (cap {MAX_SECOND_BLOB:.0%}) -- more than "
                   f"one object, so stage 2 has no single subject")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("subject", nargs="?")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--steps", type=int, default=28)
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("-o", "--out")
    ap.add_argument("--reference", metavar="IMG",
                    help="condition generation on this image via IP-Adapter, "
                         "in addition to the text prompt")
    ap.add_argument("--ip-scale", type=float, default=DEFAULT_IP_SCALE,
                    help=f"reference influence, 0-1 (default {DEFAULT_IP_SCALE})")
    ap.add_argument("--check", metavar="PNG", nargs="+",
                    help="grade existing images for stage-2 fitness and exit")
    args = ap.parse_args()

    if args.check:
        bad = []
        for p in args.check:
            msgs = check_concept_fitness(p)
            bad += msgs
            print(f"{p}: {'ok' if not msgs else 'UNFIT'}")
            for m in msgs:
                print(f"  {m}")
        return 1 if bad else 0

    if not args.subject:
        ap.error("a subject, or --check")
    out = concept(args.subject, args.seed, args.steps, args.size, args.out,
                  reference=args.reference, ip_scale=args.ip_scale)
    print(f"wrote {out}")
    msgs = check_concept_fitness(out)
    for m in msgs:
        print(f"  {m}")
    return 1 if msgs else 0


if __name__ == "__main__":
    raise SystemExit(main())
