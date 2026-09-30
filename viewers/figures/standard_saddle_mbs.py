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
    # tfi_split_index tells the engine where Beam L ends and
    # Beam R begins on the boundary row. For anchor_count anchors
    # per beam, each segment contributes K boundary nodes, so
    # Beam L occupies indices [0, (anchor_count-1)*K) and Beam R
    # occupies [(anchor_count-1)*K, 2*(anchor_count-1)*K).
    result = build_mesh_universal(
        boundary_loop=boundary_loop,
        segment_types=segment_types,
        fill="tfi",
        subdivisions_per_segment=K,
        transverse_count=transverse_count,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q,
        tfi_split_index=anchor_count * K,
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





# =============================================================================
# TRIANGLE CONVERTER
# =============================================================================

def _grid_to_triangles(X, Y, Z):
    """Convert an (n_i, M) grid into a flat list of triangles for Mesh3d."""
    n_i, M = X.shape
    node_x = X.reshape(-1)
    node_y = Y.reshape(-1)
    node_z = Z.reshape(-1)

    tri_i = []
    tri_j = []
    tri_k = []

    for i in range(n_i - 1):
        for j in range(M - 1):
            a = i * M + j
            b = (i + 1) * M + j
            c = i * M + (j + 1)
            d = (i + 1) * M + (j + 1)

            tri_i.append(a)
            tri_j.append(b)
            tri_k.append(c)

            tri_i.append(b)
            tri_j.append(d)
            tri_k.append(c)

    return node_x, node_y, node_z, tri_i, tri_j, tri_k


def _add_kader_track(fig, x, z_beam, y_beam, show_legend=False):
    """Draw the continuous kader track along a beam."""
    fig.add_trace(go.Scatter3d(
        x=x, y=y_beam, z=z_beam,
        mode="lines",
        line=dict(color="#f39c12", width=2),
        showlegend=show_legend,
        name="Kader track" if show_legend else None,
        hoverinfo="skip",
    ))


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def build_standard_saddle():
    """Standard Saddle: two curved beams, membrane, tie-downs, supports."""
    span = float(st.session_state.get("ws_ss_span", 10.0))
    apex = float(st.session_state.get("ws_ss_apex", 15.0))
    rise = float(st.session_state.get("ws_ss_rise", 6.2))
    curve_type = st.session_state.get("ws_ss_curve_type", "parabolic")
    n_intervals = int(st.session_state.get("ws_ss_tiedown_intervals", 2))
    uplift = float(st.session_state.get("ws_ss_uplift_angle", 45))
    spread = float(st.session_state.get("ws_ss_spread_angle", 30))
    warp_pre = float(st.session_state.get("ws_ss_warp_pretension", 2.0))
    weft_pre = float(st.session_state.get("ws_ss_weft_pretension", 2.0))
    edge_pre = float(st.session_state.get("ws_ss_edge_cable_pretension", 5.0))
    attach_type = str(st.session_state.get("ws_ss_attachment_type", "kader"))

    anchor_count = int(st.session_state.get("ws_ss_anchor_count", 7))
    mesh_spacing = float(st.session_state.get("ws_ss_mesh_spacing", 0.5))
    transverse_count = int(st.session_state.get("ws_ss_transverse_count", 8))
    tiedown_pretension = float(
        st.session_state.get("ws_ss_tiedown_pretension", 2.5)
    )

    if span <= 0 or apex <= 0 or rise <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Invalid geometry - check inputs",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#f39c12", size=16),
        )
        return apply_common_layout(fig, 10.0)

    built = _build_saddle_mbs(
        span=span, apex=apex, rise=rise, curve_type=curve_type,
        anchor_count=anchor_count,
        mesh_spacing=mesh_spacing,
        transverse_count=transverse_count,
        warp_pretension=warp_pre,
        weft_pretension=weft_pre,
        edge_cable_pretension=edge_pre,
        attachment_type=attach_type,
        tiedown_pretension=tiedown_pretension,
    )
    X_surf = built["X"]
    Y_surf = built["Y"]
    Z_surf = built["Z"]
    anchors_L = built["anchors_L"]
    anchors_R = built["anchors_R"]
    diag = built["diagnostics"]

    # ---- Beam curves for drawing.
    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)
    s, total = arclength_parametrisation(x, z_beam)
    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=x, y=y1, z=z_beam,
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        name="Beam L",
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=y2, z=z_beam,
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        name="Beam R",
    ))

    # ---- Membrane mesh.
    node_x, node_y, node_z, tri_i, tri_j, tri_k = _grid_to_triangles(
        X_surf, Y_surf, Z_surf
    )
    fig.add_trace(go.Mesh3d(
        x=node_x, y=node_y, z=node_z,
        i=tri_i, j=tri_j, k=tri_k,
        color="#4a7a9c",
        opacity=0.55,
        flatshading=True,
        name="Membrane",
        showlegend=False,
        hoverinfo="skip",
    ))

    # ---- Anchors along both beams.
    anchor_L_x = [a[0] for a in anchors_L]
    anchor_L_y = [a[1] for a in anchors_L]
    anchor_L_z = [a[2] for a in anchors_L]
    anchor_R_x = [a[0] for a in anchors_R]
    anchor_R_y = [a[1] for a in anchors_R]
    anchor_R_z = [a[2] for a in anchors_R]

    fig.add_trace(go.Scatter3d(
        x=anchor_L_x, y=anchor_L_y, z=anchor_L_z,
        mode="markers",
        marker=dict(color="#f39c12", size=6, symbol="circle"),
        name="Anchors (Beam L)",
        showlegend=False,
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter3d(
        x=anchor_R_x, y=anchor_R_y, z=anchor_R_z,
        mode="markers",
        marker=dict(color="#f39c12", size=6, symbol="circle"),
        name="Anchors (Beam R)",
        showlegend=False,
        hoverinfo="skip",
    ))

    # ---- Attachment method drawing.
    if attach_type == "cable_supported":
        fig.add_trace(go.Scatter3d(
            x=[a[0] for a in anchors_L],
            y=[a[1] for a in anchors_L],
            z=[a[2] for a in anchors_L],
            mode="markers+lines",
            line=dict(color="#f1c40f", width=4),
            marker=dict(color="#f39c12", size=7),
            name="Fabric edge cable (L)",
            showlegend=True,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=[a[0] for a in anchors_R],
            y=[a[1] for a in anchors_R],
            z=[a[2] for a in anchors_R],
            mode="markers+lines",
            line=dict(color="#f1c40f", width=4),
            marker=dict(color="#f39c12", size=7),
            name="Fabric edge cable (R)",
            showlegend=False,
            hoverinfo="skip",
        ))
    else:
        _add_kader_track(fig, x, z_beam, y1, show_legend=True)
        _add_kader_track(fig, x, z_beam, y2, show_legend=False)

    # ---- Tie-downs.
    if n_intervals == 4:
        per_beam_fractions = [0.175, 0.825]
    elif n_intervals == 8:
        per_beam_fractions = [0.175, 0.225, 0.775, 0.825]
    else:
        per_beam_fractions = [0.175, 0.825]

    for frac in per_beam_fractions:
        idx = find_index_at_arclength_fraction(s, total, frac)
        x_tie = x[idx]
        beam_z = z_beam[idx]

        for side, y_beam in ((-1, y1[idx]), (+1, y2[idx])):
            drop = beam_z
            if drop <= 0:
                drop = 0.5
            horizontal = drop / math.tan(math.radians(uplift)) \
                if uplift > 0 else drop
            x_offset = horizontal * 0.5
            y_offset = horizontal * 0.5 * math.tan(math.radians(spread))

            if x_tie < 0:
                anchor_x = x_tie - x_offset
            elif x_tie > 0:
                anchor_x = x_tie + x_offset
            else:
                anchor_x = x_tie + x_offset

            anchor_y = y_beam + side * y_offset

            fig.add_trace(go.Scatter3d(
                x=[x_tie, anchor_x],
                y=[y_beam, anchor_y],
                z=[beam_z, 0],
                mode="lines",
                line=dict(color="#f1c40f", width=2, dash="dot"),
                showlegend=False,
                hoverinfo="skip",
            ))

            fig.add_trace(go.Scatter3d(
                x=[anchor_x], y=[anchor_y], z=[0],
                mode="markers",
                marker=dict(color="#f1c40f", size=5, symbol="square"),
                showlegend=False,
                hoverinfo="skip",
            ))

    # ---- Ground supports.
    fig.add_trace(go.Scatter3d(
        x=[-span / 2.0, span / 2.0],
        y=[0, 0],
        z=[0, 0],
        mode="markers",
        marker=dict(color="#2ecc71", size=10, symbol="diamond"),
        name="Ground supports",
    ))

    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="lines",
        line=dict(color="#f1c40f", width=2, dash="dot"),
        name="Tie-down cables",
    ))

    fig = apply_common_layout(fig, rise)

    # ---- Diagnostics expander. The audit trail.
    with st.expander("FDM diagnostics (temporary)", expanded=False):
        st.markdown("**Boundary model** - 12 anchors, 12 segments:")
        c0, c0b, c0c = st.columns(3)
        c0.metric("Anchors", diag["n_anchors"])
        c0b.metric("Segments", diag["n_segments"])
        c0c.metric("K", diag["K"])

        st.markdown("**Mesh (universal engine, TFI fill):**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nodes", diag["n_nodes"])
        c2.metric("Edges", diag["n_edges"])
        c3.metric("Fixed", diag["n_fixed"])
        c4.metric("Free", diag["n_free"])

        st.markdown("**FDM solver residual** - after solve_fdm:")
        d1, d2, d3 = st.columns(3)
        d1.metric("Residual", "%.4e" % diag["residual_norm"])
        d2.metric("Min tri area", "%.6e" % diag["min_tri_area"])
        d3.metric("Mean tri area", "%.6e" % diag["mean_tri_area"])

        st.markdown("**Fabric attachment:** " + diag["attachment_type"])
        st.markdown("**Tie-down pretension (kN):** "
                    + ("%.2f" % diag["tiedown_pretension"])
                    + "  (not yet wired into FDM)")

        st.markdown("**Top 20 largest node displacements:**")
        rows = []
        for entry in diag["top_displacements"]:
            rows.append(
                "rank " + str(entry["rank"]) +
                "  node " + str(entry["node"]) +
                "  (i=" + str(entry["i"]) + ", j=" + str(entry["j"]) + ")" +
                "  disp=" + ("%.4f" % entry["disp"])
            )
        st.code("\n".join(rows), language="text")

        st.markdown("**Structural connections** - the second list. "
                    "Empty today. Populated in Stage 3.")
        st.markdown("- (none)")

    return fig


# =============================================================================
# END OF viewers/figures/standard_saddle_mbs.py
# =============================================================================
#
# This file is Step 2D of the UI migration. It is the MBS version of
# the Standard Saddle viewer, rewritten to call the universal mesh
# engine.
#
# It is NOT yet wired into the app. viewers/results_viewer.py still
# dispatches to the old standard_saddle.py.
#
# To swap: in viewers/results_viewer.py, find the branch for
# variant_key == "standard_saddle" and change the import to point
# to this file. One line. One commit. Step 2D.5.
#
# The fold is dead. The universal mesh engine has no column at
# the support. The support is a single anchor. There is no
# degenerate column. The mesh converges to a point.
#
# Files untouched by this addition:
#   engine/form_finding.py
#   engine/membrane_boundary.py
#   engine/membrane_surface.py
#   engine/mesh_universal.py
#   viewers/figures/standard_saddle.py
#   viewers/results_viewer.py
#   ui/workshops/saddle_standard.py
#   data/recipes/standard_saddle.py
#   every other viewer
# =============================================================================





