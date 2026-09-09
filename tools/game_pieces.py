"""Parametric tabletop pieces using the cafe factory's existing mesh primitives.

This is the procedural producer, not SDXL output. Gameplay traits select actual
geometry. The shared renderer still owns projection, shading and pixelization.
"""
from mesh import Mesh
from assetlib import merge, strut


def oval(at, radii, material):
    m = Mesh()
    m.add_sphere((0, 0, 0), 1, material, segments=16, rings=10)
    m.verts = [tuple(at[i] + v[i] * radii[i] for i in range(3)) for v in m.verts]
    return m


def build(kind: str, traits=(), variant=None):
    if kind not in {'tick', 'tack', 'toe', 'egg', 'stone', 'lure', 'wild'}:
        raise ValueError(f'Unsupported procedural body family: {kind}')
    if set(traits) - {'armored', 'fertile', 'charged', 'rooted'}:
        raise ValueError('Unsupported trait geometry')
    if 'fertile' in traits and kind != 'tick':
        raise ValueError('Only ticks carry brood eggs')
    m = Mesh()
    if kind == 'tick':
        m = merge(oval((0, -0.06, 0.25), (0.23, 0.28, 0.16), 'foliage'),
                  oval((0, 0.2, 0.22), (0.16, 0.14, 0.12), 'foliage+1'))
        # Four anatomically separate paired legs. No limb count sampled by AI.
        for side in (-1, 1):
            for j, y in enumerate((-0.24, -0.10, 0.04, 0.18)):
                knee = (side * (0.34 + (j % 2) * 0.045), y, 0.16)
                foot = (side * (0.42 + (j % 2) * 0.03), y + (j - 1.5) * 0.055, 0.025)
                strut(m, (side * 0.13, y, 0.22), knee, 0.032, 'foliage-1')
                strut(m, knee, foot, 0.027, 'foliage-1')
        for side in (-1, 1):
            m = merge(m, oval((side * 0.07, 0.302, 0.255), (0.035, 0.025, 0.037), 'neutral-4'))
        if 'armored' in traits:
            m = merge(m, oval((0, -0.075, 0.355), (0.25, 0.26, 0.095), 'neutral+1'))
            for side in (-1, 1):
                m = merge(m, oval((side * 0.18, 0.02, 0.417), (0.025, 0.025, 0.02), 'gold_coin'))
        if 'fertile' in traits:
            for x, y in ((-0.12, -0.13), (0.12, -0.13), (0, 0.045)):
                m = merge(m, oval((x, y, 0.47), (0.085, 0.095, 0.115), 'cream'))
    elif kind == 'tack':
        m.add_prism((0, 0, 0), 0.025, 0.025, 0.31, 'neutral+1', segments=8)
        m.add_prism((0, 0, 0.28), 0.23, 0.23, 0.09, 'rose', segments=16)
        m = merge(m, oval((0, 0, 0.37), (0.22, 0.22, 0.065), 'rose+1'))
        if variant == 'hatchery-trap-v1':
            for x in (-0.12, 0.12):
                m = merge(m, oval((x, 0, 0.48), (0.075, 0.09, 0.10), 'cream'))
            strut(m, (-0.12, 0, 0.42), (0.12, 0, 0.42), 0.022, 'wood')
        if variant == 'snare-tack-v1':
            for side in (-1, 1):
                strut(m, (side * 0.12, 0, 0.39), (side * 0.27, 0, 0.12), 0.026, 'wood')
            m = merge(m, oval((0, 0.02, 0.16), (0.18, 0.035, 0.04), 'sky'))
    elif kind == 'toe':
        m = merge(oval((0, 0, 0.15), (0.19, 0.3, 0.15), 'skin+1'),
                  oval((0, 0.17, 0.267), (0.13, 0.105, 0.036), 'cream'))
        if variant == 'mimic-toe-v1':
            for side in (-1, 1):
                for y in (-0.10, 0.04):
                    strut(m, (side * 0.11, y, 0.10), (side * 0.28, y, 0.04), 0.022, 'foliage-1')
            m = merge(m, oval((0, -0.19, 0.17), (0.09, 0.055, 0.05), 'foliage'))
    elif kind == 'egg':
        m = oval((0, 0, 0.22), (0.17, 0.17, 0.22), 'cream')
        if variant == 'decoy-egg-v1':
            m.add_prism((0, 0, 0.48), 0.055, 0.055, 0.16, 'neutral+1', segments=8)
            m = merge(m, oval((0, 0, 0.44), (0.12, 0.12, 0.035), 'rose'))
    elif kind == 'stone':
        m.add_prism((0, 0, 0), 0.28, 0.25, 0.24, 'neutral', segments=5)
        m = merge(m, oval((0.1, 0, 0.25), (0.14, 0.13, 0.025), 'foliage-1'))
    elif kind == 'lure':
        m = oval((0, 0, 0.19), (0.22, 0.22, 0.19), 'sky')
        m.add_cylinder((0, 0, 0.30), 0.10, 0.15, 'sky+1', segments=12)
        m.add_cylinder((0, 0, 0.44), 0.115, 0.07, 'wood+1', segments=12)
        m = merge(m, oval((0, 0.209, 0.21), (0.08, 0.023, 0.09), 'lamp_glow'))
    elif kind == 'wild':
        m = oval((0, 0, 0.18), (0.23, 0.23, 0.18), 'rose')
        m.faces = [(vi, ni, 'sky' if sum(m.verts[i][0] for i in vi) > 0 else mat)
                   for vi, ni, mat in m.faces]
        strut(m, (0, 0, 0.31), (0, 0, 0.50), 0.025, 'foliage')
        m = merge(m, oval((0.10, 0, 0.46), (0.12, 0.04, 0.045), 'foliage+1'))
    if 'armored' in traits and kind != 'tick':
        m.add_prism((0, 0, 0.07), 0.245, 0.245, 0.07, 'neutral+1', segments=12)
    if 'charged' in traits:
        m = merge(m, oval((0, 0.06, m.bounds()[1][2] + 0.045), (0.07, 0.07, 0.07), 'lamp_glow'))
    if 'rooted' in traits:
        for side in (-1, 1):
            strut(m, (0, 0, 0.04), (side * 0.31, 0.15, 0.025), 0.035, 'wood')
    return m
