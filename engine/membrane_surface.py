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
# Inputs:
#   beam_L_points    (N, 3) array of points on Beam L
#   beam_R_points    (N, 3) array of points on Beam R
#   n_u              number of grid nodes along the beam
#   n_v              number of grid nodes across the width
#   sag_fraction     sag of the membrane middle as a fraction of width
#   taper_ends       if True, collapse the grid at u=0 and u=n_u-1 to
#                    a single point (the tip). If False, keep full width.
#
# Output:
#   (n_u, n_v, 3) array of coordinates.
#
# Assumptions:
#   - Beam L and Beam R are ordered from the SAME tip to the SAME tip.
#     Both arrays must have the same length.
#   - The two beams converge at u=0 and u=n_u-1 (the tips), where
#     both beams have y = 0.
#
# The surface is built by:
#   1. Interpolating beam_L and beam_R along arc length, to n_u points.
#   2. For each u index, interpolating across the width from Beam L
#      to Beam R, to n_v points.
#   3. Applying a sag across the width, weighted so that it is zero at
#      the beam edges and maximum at the middle.
#   4. If taper_ends is True, collapsing all v-nodes at u=0 and u=n_u-1
#      to a single point (the tip coordinate).
#
# History:
#   2026-09-25 - First build. Fills the gap in
#                SPEC_saddle_viewer_fd.md — the spec does not
#                describe how the initial mesh is drawn.
# =============================================================================

import numpy as np


def _arclength_parametrise(points):
    """
    Given an (N, 3) array of points, return cumulative arc length.
    """
    pts = np.asarray(points, dtype=float)
    if len(pts) < 2:
        return np.array([0.0]), 0.0
    diff = np.diff(pts, axis=0)
    seg = np.linalg.norm(diff, axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg)))
    return s, float(s[-1])


def _resample_by_arclength(points, n_target):
    """
    Resample an (N, 3) array of points into n_target points, equally
    spaced by arc length.

    Returns (n_target, 3) array.
    """
    pts = np.asarray(points, dtype=float)
    if len(pts) < 2:
        return np.tile(pts[0] if len(pts) else [0.0, 0.0, 0.0],
                       (n_target, 1))

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


def build_surface(beam_L_points, beam_R_points, n_u, n_v,
                  sag_fraction=0.15, taper_ends=True):
    """
    Build the (n_u, n_v, 3) grid of a lens membrane surface.

    Parameters
    ----------
    beam_L_points : (N, 3) array
    beam_R_points : (N, 3) array
    n_u : int
        Number of grid nodes along the beam.
    n_v : int
        Number of grid nodes across the width.
    sag_fraction : float
        Sag of the membrane middle, as a fraction of the local width.
        0.0 means flat. Default 0.15.
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

    # ---- 1. Resample both beams to n_u points along arc length.
    # The two beams may not have the same arc length distribution,
    # so we resample each independently.
    L_resampled = _resample_by_arclength(beam_L, n_u)
    R_resampled = _resample_by_arclength(beam_R, n_u)

    # ---- 2. Build the grid.
    grid = np.zeros((n_u, n_v, 3))
    for i in range(n_u):
        pL = L_resampled[i]
        pR = R_resampled[i]

        # Compute the width at this u.
        width_vec = pR - pL
        width = float(np.linalg.norm(width_vec))

        for j in range(n_v):
            v = j / (n_v - 1.0)

            # Straight-line interpolation between beam points.
            base = pL * (1.0 - v) + pR * v

            # Sag across the width. Maximum at the middle (v=0.5),
            # zero at the beam edges (v=0 or v=1).
            # Sag is applied in the z direction only, downward.
            sag_profile = 4.0 * v * (1.0 - v)
            sag_amount = sag_fraction * width * sag_profile

            pt = base.copy()
            pt[2] -= sag_amount

            grid[i, j] = pt

    # ---- 3. Taper the ends if requested.
    if taper_ends:
        # At u=0 and u=n_u-1, all v-nodes collapse to a single point.
        # The point is the tip — the first (or last) beam sample.
        # Compute the tip as the mean of the two beam points at that u
        # (they should already coincide, but averaging is safe).
        left_tip = 0.5 * (L_resampled[0] + R_resampled[0])
        right_tip = 0.5 * (L_resampled[-1] + R_resampled[-1])

        for j in range(n_v):
            grid[0, j] = left_tip
            grid[n_u - 1, j] = right_tip

    return grid


# =============================================================================
# END OF engine/membrane_surface.py
# =============================================================================
