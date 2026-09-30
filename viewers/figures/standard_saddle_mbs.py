# =============================================================================
# SDSe - Standard Saddle Figure Builder (MBS version)
# =============================================================================
# Builds the 3D figure for the Standard Saddle variant, using the
# universal mesh engine with the TWOSIDED topology.
#
# Architecture (settled 2026-09-30):
#   The boundary is an IMAGINARY construction line. Its only job
#   is to divide the shape into anchors and curves. It is NOT a
#   physical member.
#
#   The saddle is a TWO-SIDED region:
#     - Curve A (Beam L): from far tip P0 to near tip P1.
#     - Curve B (Beam R): from near tip P1 back to far tip P0.
#     - The two tips P0 and P1 are SINGLE nodes in the mesh.
#       They are NOT duplicated as columns.
#
#   The FABRIC EDGE is what toggles between attachment methods:
#     - Kader Guider    - fabric continuously attached to the beam.
#     - Cable Supported - fabric attached only at anchors. Bows.
#
#   The mesh engine produces a twosided mesh with the tips as
#   single shared nodes. No degenerate column. No fold.
#
# Boundary model for the Standard Saddle:
#   2 curves. 2 tips. All curve segments are "beam" members.
#
# Structural connections (Part V doctrine):
#   A separate list. Empty today. Populated in Stage 3.
#
# History:
#   2026-09-29 - Step 2C. First MBS version. Hand-built mesh.
#   2026-09-30 - Step 2D. Wired to the universal engine (broken
#                because the engine was on the fill API).
#   2026-09-30 - Step 5. Rewritten for the topology API.
#                topology="twosided". Tips are single nodes.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go

import streamlit as st

from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
    find_index_at_arclength_fraction,
)
from engine.form_finding import solve_fdm
from engine.mesh_universal import build_mesh_universal


# =============================================================================
# BOUNDARY CURVES
# =============================================================================

def _build_saddle_curves(x, z_beam, y1, y2, span, anchor_count):
    """
    Build the two boundary curves and the two tips.

    Curve A (Beam L): ordered from far tip P0 to near tip P1.
    Curve B (Beam R): ordered from near tip P1 back to far tip P0.

    The tips are the endpoints of both curves. They are the same
    physical points. The engine represents them as SINGLE nodes.

    Both curves have `anchor_count` anchors. Each curve has
    anchor_count - 1 segments.

    Returns:
        curve_A       : (anchor_count, 3) array, far tip -> near tip
        curve_B       : (anchor_count, 3) array, near tip -> far tip
        tip_P0        : 3D point at the far tip
        tip_P1        : 3D point at the near tip
        seg_types     : list of segment types, length
                        (anchor_count - 1) * 2
                        (Curve A segments first, then Curve B)
        arc_lengths   : list of segment arc lengths, same length
        total_arc     : total arc length along one curve
    """
    n_pts = len(x)
    s, total = arclength_parametrisation(x, z_beam)
    if total <= 0:
        s = np.linspace(0.0, 1.0, n_pts)
        total = 1.0

    # Anchors at equal arc fractions. Because both curves share the
    # two tips, use anchor_count points spanning [0, 1] inclusive.
    arc_targets = np.linspace(0.0, total, anchor_count)

    # Curve A: Beam L, far tip -> near tip.
    curve_A = np.zeros((anchor_count, 3))
    for k, target in enumerate(arc_targets):
        bx = float(np.interp(target, s, x))
        bz = float(np.interp(target, s, z_beam))
        by = float(np.interp(target, s, y1))
        curve_A[k] = (bx, by, bz)

    # Curve B: Beam R, near tip -> far tip (reverse order).
    curve_B = np.zeros((anchor_count, 3))
    for k, target in enumerate(arc_targets[::-1]):
        bx = float(np.interp(target, s, x))
        bz = float(np.interp(target, s, z_beam))
        by = float(np.interp(target, s, y2))
        curve_B[k] = (bx, by, bz)

    tip_P0 = curve_A[0]
    tip_P1 = curve_A[-1]

    # Segment types: all "beam". One entry per segment on each
    # curve, curve A first, then curve B.
    n_seg_per_curve = anchor_count - 1
    seg_types = ["beam"] * (n_seg_per_curve * 2)

    # Segment arc lengths.
    arc_lengths = []
    for curve in (curve_A, curve_B):
        for i in range(n_seg_per_curve):
            p0 = curve[i]
            p1 = curve[i + 1]
            arc_lengths.append(float(np.linalg.norm(p1 - p0)))

    return curve_A, curve_B, tip_P0, tip_P1, seg_types, arc_lengths, total





