#!/usr/bin/env python3
"""Turn a folder of reference images into a `factory.py` subject list.

`concept.py` has taken reference images for a while and `factory.py` has
accepted a `reference:` key for as long, but the only way to feed it forty
photos was to hand-write forty YAML entries -- name, prompt, height, path,
each one typed. That is the actual ceiling on "point this at a pile of
references and get sprites", and it is a text-munging problem rather than a
model problem, which makes it embarrassing to leave in the way.

    python tools/scaffold_subjects.py photos/ -o subjects.yaml
    python tools/scaffold_subjects.py photos/ --kind character
    python tools/scaffold_subjects.py photos/ --merge subjects.yaml

Two layouts, both meaningful:

    photos/teapot.jpg            -> one subject, one reference image
    photos/espresso_machine/     -> one subject, every image in it as a
      front.jpg  side.jpg          reference

The second is not a convenience. `concept.py` loads N images into N
independent IP-Adapter slots and blends them in UNet cross-attention, so
several views of the same object condition better than one -- and a folder
per subject is the natural way to express that without inventing a syntax.

**Height is left null on purpose and the factory will refuse to run.**
`ingest.fit()` has no way to tell a teapot from a table, and neither does a
filename. Filling in a plausible default would put a wrong number in every
row where a missing one is at least loud: a mug scaled to a table's height
reaches stage 5 and produces a sprite that is confidently the wrong size,
which is worse than an error. So the scaffold writes `height: null`, prints
how many need filling, and `factory.py` names every offender if you run it
anyway. Forty numbers to type beats forty records to author.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "subject"


def _prompt_from(name: str) -> str:
    """A filename is a name, not a prompt, and the gap matters.

    `STYLE` in `concept.py` already supplies "flat neutral background",
    lighting and framing, so what belongs here is the noun phrase and an
    article. "teapot" alone conditions noticeably worse than "a teapot" --
    SDXL reads a bare noun as more of a label and more of a product shot --
    and the article costs one token out of the 77 available.
    """
    words = name.replace("_", " ").strip()
    article = "an" if words[:1].lower() in "aeiou" else "a"
    return f"{article} {words}"


def scan(folder: Path) -> list[dict]:
    """Files become one-reference subjects; directories become multi."""
    subs = []
    for entry in sorted(folder.iterdir()):
        if entry.is_dir():
            refs = sorted(p for p in entry.iterdir()
                          if p.suffix.lower() in IMAGE_EXT)
            if not refs:
                continue
            name = _slug(entry.name)
            subs.append({
                "name": name,
                "prompt": _prompt_from(name),
                "height": None,
                # Left exactly as the caller wrote them -- relative if the
                # folder argument was relative, absolute if it was absolute.
                # An earlier version tried to rebase everything onto the repo
                # root and crashed on the first reference folder that lived
                # somewhere else, which is the normal case for a pile of
                # photos.
                "reference": [p.as_posix() for p in refs],
            })
        elif entry.suffix.lower() in IMAGE_EXT:
            name = _slug(entry.stem)
            subs.append({
                "name": name,
                "prompt": _prompt_from(name),
                "height": None,
                "reference": entry.as_posix(),
            })
    return subs


def merge(existing: list[dict], scanned: list[dict]) -> tuple[list[dict], int]:
    """Keep every field already filled in; add only genuinely new names.

    Re-running the scaffold after adding photos should not cost you the
    heights you typed the first time. Existing rows win outright rather than
    being field-merged, because a merge that "improves" a row you edited is
    a merge that quietly disagrees with you.
    """
    known = {s["name"] for s in existing}
    added = [s for s in scanned if s["name"] not in known]
    return existing + added, len(added)


def _q(text: str) -> str:
    """Quote a scalar if flow-style YAML would misread it.

    The subject lists here are flow mappings on one line. A space is safe --
    a plain scalar inside `{...}` runs to the next comma or brace, which is
    why the hand-written lists get away with `prompt: a ceramic teapot`. A
    colon is not, and every Windows absolute path has one (`C:/photos/...`),
    as does any name with a comma or a bracket in it. Quote only those, so
    the common case stays as readable as the files a human wrote.

    Round-trip verified against `yaml.safe_load`, not reasoned about: this
    file writes YAML by hand and the only thing that makes that acceptable is
    checking that the result parses back to what went in.
    """
    if text and not any(ch in text for ch in ",{}[]:#'\"") :
        return text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump(subs: list[dict]) -> str:
    """Hand-rolled rather than `yaml.dump`, because the existing subject
    lists are one flow-style row per subject and stay readable that way;
    round-tripping them through PyYAML reformats every line into block style
    and makes the diff of adding one subject look like a rewrite."""
    lines = ["# Scaffolded by tools/scaffold_subjects.py.",
             "# height is in TILE UNITS (a person is ~1.6) and must be filled",
             "# in -- factory.py refuses to run while any row is null.",
             ""]
    for s in subs:
        h = "null" if s["height"] is None else s["height"]
        ref = s["reference"]
        if isinstance(ref, list):
            ref_s = "[" + ", ".join(_q(r) for r in ref) + "]"
        else:
            ref_s = _q(ref)
        row = (f"- {{name: {s['name']}, prompt: {_q(s['prompt'])}, "
               f"height: {h}, reference: {ref_s}")
        for key in ("kind", "ip_scale", "seed"):
            if s.get(key) is not None:
                row += f", {key}: {s[key]}"
        lines.append(row + "}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="directory of reference images")
    ap.add_argument("-o", "--out", default="subjects.yaml")
    ap.add_argument("--kind", choices=("prop", "character"),
                    help="written onto every row; see concept.py's "
                         "NEGATIVE_CHARACTER for what it changes")
    ap.add_argument("--ip-scale", type=float, default=None,
                    help="reference strength, written onto every row "
                         "(concept.py's default applies when omitted)")
    ap.add_argument("--merge", metavar="FILE",
                    help="start from an existing subject list and add only "
                         "names it does not already have, so heights you "
                         "have already filled in survive a re-scan")
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"{folder} is not a directory", file=sys.stderr)
        return 1

    subs = scan(folder)
    if not subs:
        print(f"no images in {folder} (looked for "
              f"{', '.join(sorted(IMAGE_EXT))})", file=sys.stderr)
        return 1
    for s in subs:
        if args.kind:
            s["kind"] = args.kind
        if args.ip_scale is not None:
            s["ip_scale"] = args.ip_scale

    added = len(subs)
    if args.merge:
        import yaml
        prev = yaml.safe_load(Path(args.merge).read_text(encoding="utf-8"))
        subs, added = merge(prev or [], subs)

    out = Path(args.out)
    out.write_text(dump(subs), encoding="utf-8")
    missing = sum(1 for s in subs if s.get("height") is None)
    multi = sum(1 for s in subs if isinstance(s.get("reference"), list))
    print(f"{len(subs)} subjects ({added} new, {multi} with multiple "
          f"reference views) -> {out}")
    if missing:
        print(f"{missing} still need a height in tile units. factory.py "
              f"will name them and refuse to run until they are filled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
