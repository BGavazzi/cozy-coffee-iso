"""Perceptual colour space helpers (OKLab / OKLCh) and sRGB gamut mapping.

Pure stdlib. OKLab is used throughout because palette work needs *perceptual*
uniformity: two colours a fixed distance apart in OKLab look equally different,
which is what makes "no two palette entries collapse under quantization" a
checkable property. The same claim in sRGB or HSV is false.

Reference: Bjorn Ottosson, https://bottosson.github.io/posts/oklab/
"""
from __future__ import annotations

import math

Rgb = tuple[float, float, float]      # 0..1 sRGB
Lab = tuple[float, float, float]      # OKLab
Lch = tuple[float, float, float]      # L, C, h(degrees)


# --- sRGB transfer function -------------------------------------------------

def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


# --- OKLab ------------------------------------------------------------------

def linear_rgb_to_oklab(r: float, g: float, b: float) -> Lab:
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = _cbrt(l), _cbrt(m), _cbrt(s)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def oklab_to_linear_rgb(L: float, a: float, b: float) -> Rgb:
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def _cbrt(x: float) -> float:
    return math.copysign(abs(x) ** (1 / 3), x)


# --- OKLCh (polar OKLab; hue in degrees) ------------------------------------

def lab_to_lch(L: float, a: float, b: float) -> Lch:
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360.0


def lch_to_lab(L: float, C: float, h: float) -> Lab:
    rad = math.radians(h)
    return L, C * math.cos(rad), C * math.sin(rad)


# --- sRGB round trips -------------------------------------------------------

def srgb_to_oklab(rgb255: tuple[int, int, int]) -> Lab:
    lin = tuple(srgb_to_linear(c / 255.0) for c in rgb255)
    return linear_rgb_to_oklab(*lin)


def oklab_to_srgb255(L: float, a: float, b: float) -> tuple[int, int, int]:
    lin = oklab_to_linear_rgb(L, a, b)
    return tuple(max(0, min(255, round(linear_to_srgb(_clamp01(c)) * 255))) for c in lin)


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def in_gamut(L: float, a: float, b: float, eps: float = 1e-4) -> bool:
    return all(-eps <= c <= 1.0 + eps for c in oklab_to_linear_rgb(L, a, b))


def gamut_clip(L: float, C: float, h: float) -> Lch:
    """Reduce chroma until the colour fits sRGB, preserving L and hue.

    Preserving hue matters more than preserving chroma here: the palette's
    warm-light/cool-shadow rule is a *hue* relationship, and naive RGB clamping
    shifts hue badly on saturated colours.
    """
    if in_gamut(*lch_to_lab(L, C, h)):
        return L, C, h
    lo, hi = 0.0, C
    for _ in range(24):
        mid = (lo + hi) / 2
        if in_gamut(*lch_to_lab(L, mid, h)):
            lo = mid
        else:
            hi = mid
    return L, lo, h


# --- distance ---------------------------------------------------------------

def delta_e(c1: Lab, c2: Lab) -> float:
    """Euclidean distance in OKLab. ~0.02 is a just-noticeable difference."""
    return math.dist(c1, c2)


def hue_delta(h1: float, h2: float) -> float:
    """Signed shortest angular distance h1 -> h2, in (-180, 180]."""
    return (h2 - h1 + 180.0) % 360.0 - 180.0
