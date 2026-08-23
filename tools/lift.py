#!/usr/bin/env python3
"""Stage 2: lift a matted concept image into a mesh, then hand it to `ingest`.

`PIPELINE.md` names TRELLIS 2 for this stage and TRELLIS is not what runs here.
The reason is specific and worth writing down rather than quietly substituting:

TRELLIS needs three CUDA extensions compiled from source -- `nvdiffrast`,
`diff-gaussian-rasterization` and a sparse-conv backend. Compiling them needs
`nvcc` and an MSVC host compiler. This machine has an RTX 4070 and the driver,
but no CUDA toolkit and no C++ workload in its Visual Studio install, and pip's
`nvidia-cuda-nvcc-cu12` ships only `ptxas.exe` on Windows. Getting there means
two admin-level system installs of roughly 10 GB, which is a decision about
somebody's workstation rather than a decision about this repo.

So stage 2 is TripoSR: a pure-PyTorch transformer, ~1.7 GB of weights, no
compiled extensions and no rasteriser. It is a weaker reconstructor than
TRELLIS and the pipeline doc should say so. What it buys is that stages 1 and 2
actually connect to `ingest` today, on hardware that exists, which is worth
more than a better model that does not run.

Its one compiled dependency, `torchmcubes`, has no Windows wheel. Rather than
patch the vendored source -- a patch that has to be re-applied on every clone
and is invisible when it rots -- a `torchmcubes` module backed by
`skimage.measure.marching_cubes` is injected into `sys.modules` before TripoSR
is imported. The vendor tree stays pristine and the substitution lives in the
file that depends on it.

    python tools/lift.py proof/concept/teapot.png --height 0.28 -o out/teapot.obj
"""
from __future__ import annotations

import argparse
import sys
import types
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
VENDOR = ROOT / "vendor" / "TripoSR"
MODEL = "stabilityai/TripoSR"


def _install_mcubes_shim() -> None:
    """Provide `torchmcubes.marching_cubes` on top of scikit-image.

    The axis order is the whole subtlety. TripoSR builds its grid with
    `meshgrid(..., indexing="ij")`, so the density volume's axes are (x, y, z),
    and it then reorders the returned vertices `[..., [2, 1, 0]]` -- which only
    makes sense if `torchmcubes` hands back (z, y, x). `skimage` returns
    vertices in array-index order, so the columns are reversed here to match
    what the caller is about to undo. Getting this wrong does not crash; it
    produces a mesh that is correct and mirrored, which `ingest`'s signed
    volume would catch and a glance at a render would not.
    """
    import numpy as np
    import torch
    from skimage import measure

    def marching_cubes(volume, threshold: float = 0.0):
        vol = volume.detach().cpu().numpy() if hasattr(volume, "detach") \
            else np.asarray(volume)
        verts, faces, _, _ = measure.marching_cubes(vol, level=threshold)
        # Reversing the vertex columns is a reflection, so the winding has to
        # be reversed with them or every normal points inward. It does not
        # crash and it does not look wrong in a viewer that ignores winding --
        # the tell is `ingest.signed_volume`, which read -0.1612 on the first
        # teapot and +0.1612 once the faces were flipped.
        return (torch.from_numpy(np.ascontiguousarray(verts[:, ::-1])).float(),
                torch.from_numpy(np.ascontiguousarray(faces[:, ::-1])).long())

    mod = types.ModuleType("torchmcubes")
    mod.marching_cubes = marching_cubes
    sys.modules["torchmcubes"] = mod


# TripoSR pins `transformers==4.35.0` and its checkpoint stores the ViT image
# tokenizer under that release's key layout. transformers 5.x refactored ViT --
# `encoder.layer.N.attention.attention.query` became `layers.N.attention.q_proj`
# and so on -- so the state dict misses every attention weight in all twelve
# layers.
#
# Downgrading transformers is the obvious fix and the wrong one: SDXL in stage 1
# runs on diffusers 0.40 against transformers 5, and pinning the whole venv back
# to 4.35 for stage 2 would trade a working stage for a broken one. The rename
# is mechanical and total, so it is expressed as a rename.
_VIT_RENAMES = (
    (".attention.attention.query", ".attention.q_proj"),
    (".attention.attention.key", ".attention.k_proj"),
    (".attention.attention.value", ".attention.v_proj"),
    (".attention.output.dense", ".attention.o_proj"),
    (".intermediate.dense", ".mlp.fc1"),
    (".output.dense", ".mlp.fc2"),
)


def _remap_vit(ckpt: dict) -> dict:
    """Old-transformers ViT keys -> the current layout.

    Order matters: `.attention.output.dense` has to be rewritten before the
    bare `.output.dense` rule, or the attention projection is renamed to
    `mlp.fc2` and the weights land in the wrong module with matching shapes --
    a silent, plausible, completely wrong model.
    """
    out = {}
    for k, v in ckpt.items():
        if k.startswith("image_tokenizer.model.encoder.layer."):
            k = k.replace("image_tokenizer.model.encoder.layer.",
                          "image_tokenizer.model.layers.", 1)
            for old, new in _VIT_RENAMES:
                if old in k:
                    k = k.replace(old, new, 1)
                    break
        out[k] = v
    return out


def _model(device: str = "cuda", chunk: int = 8192):
    if not VENDOR.exists():
        raise SystemExit(
            f"{VENDOR} is missing. git clone --depth 1 "
            f"https://github.com/VAST-AI-Research/TripoSR {VENDOR}")
    _install_mcubes_shim()
    sys.path.insert(0, str(VENDOR))
    import torch
    from huggingface_hub import hf_hub_download
    from omegaconf import OmegaConf
    from tsr.system import TSR

    cfg = OmegaConf.load(hf_hub_download(repo_id=MODEL,
                                         filename="config.yaml"))
    OmegaConf.resolve(cfg)
    m = TSR(cfg)
    ckpt = torch.load(hf_hub_download(repo_id=MODEL, filename="model.ckpt"),
                      map_location="cpu", weights_only=True)
    missing, unexpected = m.load_state_dict(_remap_vit(ckpt), strict=False)
    # Reported rather than swallowed. `strict=False` is what makes the rename
    # possible and it is also what would let a half-loaded model run and
    # produce confident rubbish, so the count is printed every time.
    if missing or unexpected:
        print(f"  state dict: {len(missing)} missing, "
              f"{len(unexpected)} unexpected")
        for k in list(missing)[:4] + list(unexpected)[:4]:
            print(f"    {k}")
    m.renderer.set_chunk_size(chunk)
    return m.to(device)


def _prepare(png: Path | str, ratio: float = 0.85):
    """Matted RGBA in, the grey composite TripoSR was trained on out.

    Stage 1 already segmented the object, so the rembg pass TripoSR's own
    `run.py` performs is skipped -- running it twice would re-matte an image
    that is already alpha, and a second opinion from the same model is not a
    better one. What is kept is the 0.5-grey composite, which is not cosmetic:
    the model saw grey behind every training image, and a transparent or black
    background is out of distribution.
    """
    import numpy as np
    from PIL import Image
    sys.path.insert(0, str(VENDOR))
    from tsr.utils import resize_foreground

    img = Image.open(png).convert("RGBA")
    img = resize_foreground(img, ratio)
    a = np.array(img).astype(np.float32) / 255.0
    rgb = a[:, :, :3] * a[:, :, 3:4] + 0.5 * (1.0 - a[:, :, 3:4])
    return Image.fromarray((rgb * 255.0).astype(np.uint8))


def lift(png: Path | str, out: Path | str | None = None,
         resolution: int = 256, device: str = "cuda", model=None) -> Path:
    """Concept image -> OBJ. Vertex colours, no texture.

    Colour comes back as per-vertex RGB rather than a texture map, and that is
    the right shape for what happens next: `ingest.rebind` binds arbitrary
    colour to palette ramps, so a texture would only be resampled away. It also
    sidesteps TripoSR's texture baker, which needs `xatlas` and a GL context.
    """
    import torch
    model = model or _model(device)
    img = _prepare(png)
    with torch.no_grad():
        codes = model([img], device=device)
    mesh = model.extract_mesh(codes, has_vertex_color=True,
                              resolution=resolution)[0]
    out = Path(out or Path(png).with_suffix(".obj"))
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(out))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("png")
    ap.add_argument("-o", "--out")
    ap.add_argument("--resolution", type=int, default=256)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    out = lift(args.png, args.out, args.resolution, args.device)
    import trimesh
    m = trimesh.load(str(out), process=False)
    print(f"wrote {out}")
    print(f"  {len(m.vertices)} verts, {len(m.faces)} tris")
    print(f"  extent {m.extents[0]:.3f} x {m.extents[1]:.3f} "
          f"x {m.extents[2]:.3f}")
    print(f"  watertight {m.is_watertight}  volume {m.volume:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
