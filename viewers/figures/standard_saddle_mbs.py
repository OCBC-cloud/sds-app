# =============================================================================
# SDSe - Standard Saddle Figure Builder (MBS version)
# =============================================================================
# Builds the 3D figure for the Standard Saddle variant, using the
# universal mesh engine for form-finding.
#
# This file is the MBS replacement for viewers/figures/standard_saddle.py.
# The old file stays live. Once this file is proven, the dispatcher
# in viewers/results_viewer.py is swapped to point here.
#
# Architecture (settled 2026-09-30):
#   The boundary is an IMAGINARY construction line. Its only job
#   is to divide the shape into anchors and segments. After that
#   it is gone. It is NOT a physical member.
#
#   Anchors are REAL points where two segments meet.
#
#   Segments are REAL members. For the Standard Saddle, every
#   segment is a beam. A cable cannot hold midair; only a beam
#   or a wall can carry the beam line across a span.
#
#   The FABRIC EDGE is what toggles between attachment methods:
#     - Kader Guider    - fabric continuously attached to the beam.
#                         No bow. Beam holds the edge.
#     - Cable Supported - fabric attached only at anchors. The
#                         fabric edge is a cable that bows between
#                         anchors. The bow is controlled by the
#                         edge cable pretension.
#
# Boundary model for the Standard Saddle:
#   12 anchors. 12 segments.
#   7 anchors per beam (both tips included).
#   5 interior anchors per beam + 2 shared tips.
#   All 12 segments are "beam" members.
#
# Temporary mapping (until the engine gains an explicit
# fabric-edge parameter):
#   kader            -> all segments classified "beam"
#   cable_supported  -> all segments classified "cable"
#
#   The engine's hold rule then produces the right mesh:
#   "beam" segments are held along their length, "cable"
#   segments are held only at anchors. The fabric bows.
#
# Structural connections (Part V doctrine):
#   A separate list lives alongside the mesh constraint list.
#   Empty today. Populated in Stage 3 when the structural
#   engine lands.
#
# History:
#   2026-09-29 - Step 2C. First MBS version. Hand-built mesh.
#   2026-09-30 - Step 2D. Rewritten to call the universal mesh
#                engine. Boundary loop is 12 anchors, 12 segments.
#                Vocabulary fixed: Kader Guider, Cable Supported.
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
# BOUNDARY LOOP
# =============================================================================

def _build_boundary_loop(x, z_beam, y1, y2, span, anchor_count):
    """
    Build the closed boundary loop for the Standard Saddle.

    The loop contains 2 * anchor_count - 2 unique anchors:
      - anchor_count anchors on Beam L (both tips included),
      - anchor_count anchors on Beam R (both tips included),
      - the 2 tips are shared, so counted once.

    For anchor_count = 7, the loop has 12 unique anchors.
    Segments: 12.

    Return:
        boundary_loop : list of (x, y, z) tuples.
        anchors_beam_L : list of (x, y, z) for Beam L anchors.
        anchors_beam_R : list of (x, y, z) for Beam R anchors.
        arclength_segments : list of arc lengths for the 12 segments.
        total_arc : total arc length along Beam L (same for Beam R).
    """
    n_pts = len(x)
    s, total = arclength_parametrisation(x, z_beam)
    if total <= 0:
        s = np.linspace(0.0, 1.0, n_pts)
        total = 1.0

    # Beam L anchors at equal arc fractions [0, 1/N, 2/N, ..., (N-1)/N].
    # This includes the far tip at fraction 0 but NOT the near tip
    # at fraction 1. The near tip will come from Beam R's list.
    fracs_L = np.linspace(0.0, 1.0, anchor_count + 1)[:-1]

    beam_L = []
    for frac in fracs_L:
        target = frac * total
        bx = float(np.interp(target, s, x))
        bz = float(np.interp(target, s, z_beam))
        # y on Beam L is y1 (negative side).
        by = float(np.interp(target, s, y1))
        beam_L.append((bx, by, bz))

    # Beam R anchors at equal arc fractions, but traversed in reverse
    # so the loop closes correctly. Start at the near tip (fraction 1.0
    # on Beam L's arc) and go back toward the far tip.
    fracs_R = np.linspace(1.0, 0.0, anchor_count + 1)[:-1]

    beam_R = []
    for frac in fracs_R:
        target = frac * total
        bx = float(np.interp(target, s, x))
        bz = float(np.interp(target, s, z_beam))
        # y on Beam R is y2 (positive side).
        by = float(np.interp(target, s, y2))
        beam_R.append((bx, by, bz))

    boundary_loop = beam_L + beam_R

    # Segment arc lengths. Each segment lies on one beam (either L or R).
    # Beam L segments: between consecutive anchors of beam_L, plus the
    #   segment from the last beam_L anchor to beam_R[0].
    # Beam R segments: between consecutive anchors of beam_R, plus the
    #   segment from the last beam_R anchor back to beam_L[0].
    arclength_segments = []
    loop_n = len(boundary_loop)
    for k in range(loop_n):
        p0 = np.array(boundary_loop[k])
        p1 = np.array(boundary_loop[(k + 1) % loop_n])
        arclength_segments.append(float(np.linalg.norm(p1 - p0)))

    return boundary_loop, beam_L, beam_R, arclength_segments, total





