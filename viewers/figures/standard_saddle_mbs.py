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





# =============================================================================
# MESH SPACING TO K
# =============================================================================

def _compute_K(arc_lengths, mesh_spacing, k_min=5):
    """
    Convert a target mesh spacing (metres) to K, the number of
    mesh nodes placed along each curve segment.

    The rule: K = max(k_min, round(avg_segment_arc / mesh_spacing)).

    The engine takes a single K for both curves. We compute it
    from the average segment arc length.
    """
    if len(arc_lengths) == 0:
        return int(k_min), 0.0
    avg_arc = float(np.mean(arc_lengths))
    if mesh_spacing <= 0:
        mesh_spacing = 0.5
    K_float = avg_arc / mesh_spacing
    K = int(round(K_float))
    if K < int(k_min):
        K = int(k_min)
    return K, avg_arc


# =============================================================================
# MAIN BUILDER
# =============================================================================

def _build_saddle_mbs(span, apex, rise, curve_type,
                       anchor_count, mesh_spacing, transverse_count,
                       warp_pretension, weft_pretension,
                       edge_cable_pretension,
                       attachment_type, tiedown_pretension):
    """
    Build the two curves, call the engine (topology="twosided"),
    solve_fdm, and return the solved mesh for the viewer.

    Returns a dict with:
        X, Y, Z           : (n_interior, M) surfaces for drawing
        boundary_solved   : the solved boundary nodes, list of 3D
        curves_A_anchors  : (n_anchors, 3) curve A anchor points
        curves_B_anchors  : (n_anchors, 3) curve B anchor points
        tip_P0            : 3D point of tip P0
        tip_P1            : 3D point of tip P1
        diagnostics       : audit trail dict
    """
    # ---- 1. Beam curve geometry (200 sample points).
    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)

    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    # ---- 2. Build the two curves and the two tips.
    curve_A, curve_B, tip_P0, tip_P1, seg_types, arc_lengths, total_arc = \
        _build_saddle_curves(x, z_beam, y1, y2, span, anchor_count)

    # ---- 3. K from mesh spacing.
    K, avg_arc = _compute_K(arc_lengths, mesh_spacing)

    # ---- 4. Force density scalars.
    if len(arc_lengths) == 0:
        L_avg = max(0.1, avg_arc)
    else:
        L_avg = float(np.mean(arc_lengths))
    if L_avg < 1e-9:
        L_avg = 1.0

    warp_q = max(0.1, float(warp_pretension)) * 1000.0 / L_avg
    weft_q = max(0.1, float(weft_pretension)) * 1000.0 / L_avg
    edge_q = max(0.1, float(edge_cable_pretension)) * 1000.0 / L_avg

    # ---- 5. Segment types from attachment method.
    if str(attachment_type).lower() == "cable_supported":
        seg_types_engine = ["cable"] * len(seg_types)
    else:
        seg_types_engine = ["beam"] * len(seg_types)

    # ---- 6. Call the engine.
    result = build_mesh_universal(
        topology="twosided",
        curves=[curve_A, curve_B],
        corner_points=[tip_P0, tip_P1],
        segment_types=seg_types_engine,
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
    diag = result["diagnostics"]

    # ---- 7. Solve.
    res = solve_fdm(points, edges, fixed_indices, q)
    coords = res["coordinates"]

    # ---- 8. Reshape the interior for drawing.
    n_interior = diag["topo_n_interior"]
    M = diag["transverse_count"]
    n_nodes = points.shape[0]

    X = np.zeros((n_interior, M))
    Y = np.zeros((n_interior, M))
    Z = np.zeros((n_interior, M))
    for i in range(n_interior):
        for j in range(M):
            k = 1 + i * M + j
            X[i, j] = coords[k, 0]
            Y[i, j] = coords[k, 1]
            Z[i, j] = coords[k, 2]

    # Boundary_solved is the full node list, for drawing.
    boundary_solved = coords

    # ---- 9. Diagnostics.
    disp = np.linalg.norm(coords - points, axis=1)
    order = np.argsort(disp)[::-1]
    top_disp = []
    for rank, k in enumerate(order[:20]):
        if k == 0:
            i_idx = -1
            j_idx = -1
        elif k == n_nodes - 1:
            i_idx = n_interior
            j_idx = -1
        else:
            i_idx = (int(k) - 1) // M
            j_idx = (int(k) - 1) % M
        top_disp.append({
            "rank": rank + 1,
            "node": int(k),
            "i": int(i_idx),
            "j": int(j_idx),
            "disp": float(disp[k]),
        })

    # Triangle areas (interior only; tips are separate).
    tri_areas = []
    for i in range(n_interior - 1):
        for j in range(M - 1):
            a = 1 + i * M + j
            b = 1 + (i + 1) * M + j
            c = 1 + i * M + (j + 1)
            d = 1 + (i + 1) * M + (j + 1)
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
        "n_anchors": int(anchor_count),
        "n_segments": len(seg_types),
        "n_interior": int(n_interior),
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
                "type": seg_types_engine[idx],
                "arc_length": float(arc_lengths[idx]),
            }
            for idx in range(len(seg_types_engine))
        ],
        "structural_connections": [],
    }

    return {
        "X": X, "Y": Y, "Z": Z,
        "boundary_solved": boundary_solved,
        "curves_A_anchors": curve_A,
        "curves_B_anchors": curve_B,
        "tip_P0": tip_P0,
        "tip_P1": tip_P1,
        "K": K,
        "M": M,
        "n_interior": n_interior,
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
    curves_A = built["curves_A_anchors"]
    curves_B = built["curves_B_anchors"]
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
    anchor_L_x = [a[0] for a in curves_A]
    anchor_L_y = [a[1] for a in curves_A]
    anchor_L_z = [a[2] for a in curves_A]
    anchor_R_x = [a[0] for a in curves_B]
    anchor_R_y = [a[1] for a in curves_B]
    anchor_R_z = [a[2] for a in curves_B]

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
            x=[a[0] for a in curves_A],
            y=[a[1] for a in curves_A],
            z=[a[2] for a in curves_A],
            mode="markers+lines",
            line=dict(color="#f1c40f", width=4),
            marker=dict(color="#f39c12", size=7),
            name="Fabric edge cable (L)",
            showlegend=True,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=[a[0] for a in curves_B],
            y=[a[1] for a in curves_B],
            z=[a[2] for a in curves_B],
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
    curves_A = built["curves_A_anchors"]
    curves_B = built["curves_B_anchors"]
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
    anchor_L_x = [a[0] for a in curves_A]
    anchor_L_y = [a[1] for a in curves_A]
    anchor_L_z = [a[2] for a in curves_A]
    anchor_R_x = [a[0] for a in curves_B]
    anchor_R_y = [a[1] for a in curves_B]
    anchor_R_z = [a[2] for a in curves_B]

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
            x=[a[0] for a in curves_A],
            y=[a[1] for a in curves_A],
            z=[a[2] for a in curves_A],
            mode="markers+lines",
            line=dict(color="#f1c40f", width=4),
            marker=dict(color="#f39c12", size=7),
            name="Fabric edge cable (L)",
            showlegend=True,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=[a[0] for a in curves_B],
            y=[a[1] for a in curves_B],
            z=[a[2] for a in curves_B],
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
        st.markdown("**Boundary model** - 2 curves, 2 shared tips:")
        c0, c0b, c0c = st.columns(3)
        c0.metric("Anchors per curve", diag["n_anchors"])
        c0b.metric("Interior columns", diag["n_interior"])
        c0c.metric("K", diag["K"])

        st.markdown("**Mesh (universal engine, twosided topology):**")
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
# This file is Step 5 of the UI migration. It is the MBS version of
# the Standard Saddle viewer, wired to the topology engine with
# topology="twosided".
#
# The two tips are SINGLE nodes. No degenerate column. No fold.
#
# The viewer is live: viewers/results_viewer.py already dispatches
# to this file for variant_key == "standard_saddle".
#
# Files untouched by this rewrite:
#   engine/form_finding.py
#   engine/membrane_boundary.py
#   engine/membrane_surface.py
#   engine/mesh_universal.py
#   viewers/figures/standard_saddle.py
#   every other viewer
# =============================================================================





