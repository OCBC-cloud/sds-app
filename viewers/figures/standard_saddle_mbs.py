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





# =============================================================================
# MESH SPACING TO K
# =============================================================================

def _compute_K(arclength_segments, mesh_spacing, k_min=5):
    """
    Convert a target mesh spacing (metres) to K, the number of
    mesh nodes placed along each segment of the boundary row.

    The rule (recorded in the handoff):
        K = max(k_min, round(segment_arc / mesh_spacing))

    Since the engine takes a single K for all segments, we compute
    a single K from the AVERAGE segment arc length. On a symmetric
    saddle the segments are nearly equal, so the single-K
    approximation is good.

    Parameters
    ----------
    arclength_segments : list of float
        Arc length of each segment on the boundary loop.
    mesh_spacing : float
        Target mesh spacing in metres.
    k_min : int
        Lower bound. The engine requires K >= 1. We default to 5
        so the mesh is not too coarse at the smallest spacing.

    Returns
    -------
    K : int
        Nodes per segment.
    avg_arc : float
        Average segment arc length, for the diagnostics.
    """
    if len(arclength_segments) == 0:
        return int(k_min), 0.0
    avg_arc = float(np.mean(arclength_segments))
    if mesh_spacing <= 0:
        mesh_spacing = 0.5
    K_float = avg_arc / mesh_spacing
    K = int(round(K_float))
    if K < int(k_min):
        K = int(k_min)
    return K, avg_arc


# =============================================================================
# SEGMENT TYPES FROM ATTACHMENT METHOD
# =============================================================================

def _segment_types_for_attachment(attachment_type, n_segments):
    """
    Map the fabric attachment method to the engine's segment types.

    TEMPORARY MAPPING (until the engine gains an explicit
    fabric-edge parameter):
        kader            -> all segments "beam"
        cable_supported  -> all segments "cable"

    The physical member on every segment is a beam in both cases.
    The classification here is a MESH decision: whether the fabric
    edge is held along its length or released between anchors.
    Part V doctrine: mesh constraint and structural member are
    two different things. This function only affects the mesh.

    The real member (beam) will be recorded in the structural
    connections list in Stage 3.
    """
    a = str(attachment_type).lower()
    if a == "cable_supported":
        return ["cable"] * int(n_segments)
    # Default and kader both map to beam.
    return ["beam"] * int(n_segments)


# =============================================================================
# FORCE DENSITIES
# =============================================================================

def _compute_force_densities(points, edges,
                             warp_pretension, weft_pretension,
                             edge_cable_pretension):
    """
    Compute the per-edge force density scalars.

    Units: pretension in kN/m -> N/m. L_avg in metres.
    q = T * 1000 / L_avg

    The engine builds the FULL per-edge q vector itself from
    warp_q, weft_q, edge_q and the segment types. This viewer
    only computes the three scalars.
    """
    n_edges = len(edges)
    if n_edges == 0:
        return 1.0, 1.0, 1.0, 1.0
    total_len = 0.0
    pts = np.asarray(points)
    for (a, b) in edges:
        total_len += float(np.linalg.norm(pts[b] - pts[a]))
    L_avg = total_len / float(n_edges)
    if L_avg < 1e-9:
        L_avg = 1.0

    warp_q = max(0.1, float(warp_pretension)) * 1000.0 / L_avg
    weft_q = max(0.1, float(weft_pretension)) * 1000.0 / L_avg
    edge_q = max(0.1, float(edge_cable_pretension)) * 1000.0 / L_avg

    return L_avg, warp_q, weft_q, edge_q





# =============================================================================
# MAIN BUILDER
# =============================================================================

def _build_saddle_mbs(span, apex, rise, curve_type,
                       anchor_count, mesh_spacing, transverse_count,
                       warp_pretension, weft_pretension,
                       edge_cable_pretension,
                       attachment_type, tiedown_pretension):
    """
    Build the boundary loop, call the universal mesh engine,
    solve_fdm, and return the solved mesh for the viewer.

    Returns
    -------
    dict with keys:
        X, Y, Z           : (n_i, M) surfaces for drawing
        boundary_solved   : (n_i, 3) solved boundary row
        anchors_L         : Beam L anchors (for drawing)
        anchors_R         : Beam R anchors (for drawing)
        anchor_indices_L  : mesh node indices on Beam L
        anchor_indices_R  : mesh node indices on Beam R
        K                 : nodes per segment
        M                 : transverse count
        n_i               : boundary row size
        diagnostics       : audit trail dict
    """
    # ---- 1. Beam curve geometry (200 sample points).
    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)

    # y1 and y2 are the two beam edge curves in plan.
    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    # ---- 2. Boundary loop. 12 anchors, 12 segments.
    boundary_loop, anchors_L, anchors_R, arc_segs, total_arc = \
        _build_boundary_loop(x, z_beam, y1, y2, span, anchor_count)

    # ---- 3. K from mesh spacing.
    K, avg_arc = _compute_K(arc_segs, mesh_spacing)

    # ---- 4. Segment types from attachment method.
    n_segments = len(boundary_loop)
    segment_types = _segment_types_for_attachment(
        attachment_type, n_segments
    )

    # ---- 5. Force density scalars.
    if len(arc_segs) == 0:
        L_avg = max(0.1, avg_arc)
    else:
        L_avg = float(np.mean(arc_segs))
    if L_avg < 1e-9:
        L_avg = 1.0

    warp_q = max(0.1, float(warp_pretension)) * 1000.0 / L_avg
    weft_q = max(0.1, float(weft_pretension)) * 1000.0 / L_avg
    edge_q = max(0.1, float(edge_cable_pretension)) * 1000.0 / L_avg

    # ---- 6. Call the engine.
    result = build_mesh_universal(
        boundary_loop=boundary_loop,
        segment_types=segment_types,
        fill="tfi",
        subdivisions_per_segment=K,
        transverse_count=transverse_count,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q,
    )

    points = result["points"]
    edges = result["edges"]
    fixed_indices = result["fixed_indices"]
    q = result["q"]

    # ---- 7. solve_fdm.
    res = solve_fdm(points, edges, fixed_indices, q)
    coords = res["coordinates"]

    n_i = result["diagnostics"]["n_i"]
    M = result["diagnostics"]["transverse_count"]
    n_nodes = result["diagnostics"]["n_nodes"]

    # ---- 8. Reshape to (n_i, M) for drawing.
    X = np.zeros((n_i, M))
    Y = np.zeros((n_i, M))
    Z = np.zeros((n_i, M))
    for i in range(n_i):
        for j in range(M):
            k = i * M + j
            X[i, j] = coords[k, 0]
            Y[i, j] = coords[k, 1]
            Z[i, j] = coords[k, 2]

    boundary_solved = np.zeros((n_i, 3))
    for i in range(n_i):
        boundary_solved[i] = coords[i * M + 0]

    # ---- 9. Anchor indices for drawing.
    anchor_indices = []
    for a in range(len(boundary_loop)):
        i_anchor = a * K
        if i_anchor < n_i:
            anchor_indices.append(i_anchor * M)
    anchor_indices_L = anchor_indices[:anchor_count]
    anchor_indices_R = anchor_indices[anchor_count:]

    # ---- 10. Diagnostics.
    disp = np.linalg.norm(coords - points, axis=1)
    order = np.argsort(disp)[::-1]
    top_disp = []
    for rank, k in enumerate(order[:20]):
        i_idx = int(k // M)
        j_idx = int(k % M)
        top_disp.append({
            "rank": rank + 1,
            "node": int(k),
            "i": i_idx,
            "j": j_idx,
            "disp": float(disp[k]),
        })

    # Triangle areas of the solved mesh.
    tri_areas = []
    for i in range(n_i - 1):
        for j in range(M - 1):
            a = i * M + j
            b = (i + 1) * M + j
            c = i * M + (j + 1)
            d = (i + 1) * M + (j + 1)
            for tri in ((a, b, c), (b, d, c)):
                p0 = coords[tri[0]]
                p1 = coords[tri[1]]
                p2 = coords[tri[2]]
                area = 0.5 * float(np.linalg.norm(
                    np.cross(p1 - p0, p2 - p0)
                ))
                tri_areas.append(area)
    tri_areas = np.array(tri_areas) if tri_areas else np.array([0.0])

    diagnostics = {
        "residual_norm": float(res["residual_norm"]),
        "n_free": int(res["n_free"]),
        "n_fixed": int(res["n_fixed"]),
        "n_nodes": int(n_nodes),
        "n_edges": len(edges),
        "n_anchors": len(boundary_loop),
        "n_segments": len(segment_types),
        "n_i": int(n_i),
        "M": int(M),
        "K": int(K),
        "avg_segment_arc": float(avg_arc),
        "L_avg": float(L_avg),
        "min_tri_area": float(tri_areas.min()),
        "mean_tri_area": float(tri_areas.mean()),
        "max_tri_area": float(tri_areas.max()),
        "attachment_type": str(attachment_type),
        "tiedown_pretension": float(tiedown_pretension),
        "top_displacements": top_disp,
        "boundary_segments": [
            {
                "index": idx + 1,
                "type": segment_types[idx],
                "arc_length": float(arc_segs[idx]),
            }
            for idx in range(len(segment_types))
        ],
        "structural_connections": [],
    }

    return {
        "X": X, "Y": Y, "Z": Z,
        "boundary_solved": boundary_solved,
        "anchors_L": anchors_L,
        "anchors_R": anchors_R,
        "anchor_indices_L": anchor_indices_L,
        "anchor_indices_R": anchor_indices_R,
        "K": K,
        "M": M,
        "n_i": n_i,
        "diagnostics": diagnostics,
    }





