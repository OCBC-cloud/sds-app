# =============================================================================
# SDSe Engine - Membrane Surface Builder
# =============================================================================
# Purpose: build the initial 3D coordinates of a membrane surface
# from two beam curves.
#
# The surface is a lens: two curved beams meeting at two tips.
# This module produces the (n_u, n_v, 3) grid of coordinates that
# the MBS engine uses as initial_points.
#
# The mesh density along the beam is set by TWO numbers:
#   n_anchors               user-defined anchor count (say 7)
#   subdivisions_per_segment    extra nodes between anchors (say 5)
#
# The nodes along the beam are then:
#   n_u = n_anchors + (n_anchors - 1) * subdivisions_per_segment
#
# With n_anchors=7, subdivisions=5: n_u = 7 + 6*5 = 37 nodes.
#
# This decouples the mesh density from the structural anchor count.
# The user thinks about the structure. The engine thinks about the
# mesh. The two are separate.
#
# History:
#   2026-09-25 - First build.
#   2026-09-25 - Add subdivisions_per_segment. Decouple anchor count
#                from mesh density. Captures curvature between anchors.
# =============================================================================

import numpy as np


def _arclength_parametrise(points):
    pts = np.asarray(points, dtype=float)
    if len(pts) < 2:
        return np.array([0.0]), 0.0
    diff = np.diff(pts, axis=0)
    seg = np.linalg.norm(diff, axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg)))
    return s, float(s[-1])


def _resample_by_arclength(points, n_target):
    pts = np.asarray(points, dtype=float)
    if len(pts) < 2:
        fallback = pts[0] if len(pts) else [0.0, 0.0, 0.0]
        return np.tile(fallback, (n_target, 1))

    s, total = _arclength_parametrise(pts)
    if total < 1e-9:
        return np.tile(pts[0], (n_target, 1))

    out = np.zeros((n_target, 3))
    for k in range(n_target):
        target = (k / (n_target - 1.0)) * total
        idx = int(np.searchsorted(s, target, side="right") - 1)
        idx = max(0, min(idx, len(pts) - 2))
        seg_start = s[idx]
        seg_end = s[idx + 1]
        if seg_end - seg_start < 1e-12:
            out[k] = pts[idx]
        else:
            t = (target - seg_start) / (seg_end - seg_start)
            out[k] = pts[idx] * (1.0 - t) + pts[idx + 1] * t
    return out


def _compute_n_u(n_anchors, subdivisions_per_segment):
    """Return the number of grid nodes along the beam."""
    if n_anchors is None or n_anchors < 2:
        raise ValueError("n_anchors must be at least 2")
    if subdivisions_per_segment is None or subdivisions_per_segment < 0:
        raise ValueError("subdivisions_per_segment must be >= 0")
    return n_anchors + (n_anchors - 1) * subdivisions_per_segment


def build_surface(beam_L_points, beam_R_points,
                  n_anchors, subdivisions_per_segment,
                  n_v,
                  sag_fraction=0.15, taper_ends=True):
    """
    Build the (n_u, n_v, 3) grid of a lens membrane surface.

    Parameters
    ----------
    beam_L_points : (N, 3) array
    beam_R_points : (N, 3) array
    n_anchors : int
        User-defined anchor count along the beam.
    subdivisions_per_segment : int
        Extra nodes placed between consecutive anchors.
    n_v : int
        Number of grid nodes across the width.
    sag_fraction : float
        Sag of the membrane middle, as a fraction of the local
        width. 0.0 means flat. Default 0.15.
    taper_ends : bool
        If True, collapse the grid at u=0 and u=n_u-1 to a single
        point (the tip coordinate).

    Returns
    -------
    grid : (n_u, n_v, 3) array
    """
    beam_L = np.asarray(beam_L_points, dtype=float)
    beam_R = np.asarray(beam_R_points, dtype=float)
    if beam_L.shape != beam_R.shape:
        raise ValueError("beam_L_points and beam_R_points must have the "
                         "same shape.")
    if beam_L.ndim != 2 or beam_L.shape[1] != 3:
        raise ValueError("beam points must be (N, 3)")

    n_u = _compute_n_u(n_anchors, subdivisions_per_segment)

    # ---- Resample both beams to n_u points along arc length.
    L_resampled = _resample_by_arclength(beam_L, n_u)
    R_resampled = _resample_by_arclength(beam_R, n_u)

    # ---- Build the grid.
    grid = np.zeros((n_u, n_v, 3))
    for i in range(n_u):
        pL = L_resampled[i]
        pR = R_resampled[i]
        width_vec = pR - pL
        width = float(np.linalg.norm(width_vec))

        for j in range(n_v):
            v = j / (n_v - 1.0)
            base = pL * (1.0 - v) + pR * v
            sag_profile = 4.0 * v * (1.0 - v)
            sag_amount = sag_fraction * width * sag_profile
            pt = base.copy()
            pt[2] -= sag_amount
            grid[i, j] = pt

    # ---- Taper the ends if requested.
    if taper_ends:
        left_tip = 0.5 * (L_resampled[0] + R_resampled[0])
        right_tip = 0.5 * (L_resampled[-1] + R_resampled[-1])
        for j in range(n_v):
            grid[0, j] = left_tip
            grid[n_u - 1, j] = right_tip

    return grid


# =============================================================================
# END OF engine/membrane_surface.py
# =============================================================================





