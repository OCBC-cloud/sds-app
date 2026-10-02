# =============================================================================
# SDSe - Standard Saddle Figure Builder (MBS version)
# =============================================================================
# Builds the 3D figure for the Standard Saddle variant, using
# the universal triangulated mesh engine.
#
# See engine/SPEC_mesh_triangulation.md.
#
# Architecture (settled 2026-09-30):
#   The boundary is a closed loop of 3D points. The triangulated
#   engine fills the interior with triangles, respecting the
#   boundary. The tips are boundary vertices - no fan needed, no
#   degenerate column. The triangulation closes them naturally.
#
# The two beam curves:
#   Beam L: from far tip P0, along the beam, to near tip P1.
#   Beam R: from near tip P1, back along the beam, to far tip P0.
#
# The closed boundary loop:
#   Beam L forward (all anchors), then Beam R interior (skip both
#   tips since they are shared). The loop is closed by convention.
#
# Anchors and segments:
#   The anchors are the two tips plus the intermediate anchors
#   along each beam. Segments between them are classified by
#   attachment_type: "kader" -> all beam, "cable_supported" ->
#   all cable.
#
# History:
#   2026-09-29 - Step 2C. First MBS version. Hand-built mesh.
#   2026-09-30 - Step 2D. Wired to a structured engine.
#   2026-09-30 - Step 5. Rewritten to use the triangulated engine.
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
from engine.mesh_triangulated import build_mesh_triangulated


# =============================================================================
# BOUNDARY LOOP
# =============================================================================

def _build_boundary_loop(x, z_beam, y1, y2, span, anchor_count,
                          attachment_type):
    """
    Build the closed boundary loop, the anchor indices, and
    the segment types for the triangulated engine.

    Layout:
        Beam L:  anchor_count anchors from far tip P0 to near tip P1.
        Beam R:  anchor_count anchors from near tip P1 to far tip P0.
        The two tips are shared. The closed loop is:
            Beam L anchors[0..N-1]
            + Beam R anchors[1..N-2] (skip both tips)
        Total loop size: 2 * anchor_count - 2.

    Anchor indices into the loop:
        anchors = [0, 1, 2, ..., anchor_count-1, anchor_count, ...,
                   2*anchor_count-3]
        Every loop index is an anchor, because the beam is
        segmented between consecutive anchors. So anchors =
        list(range(loop_size)).

    Actually: for the saddle, the segment count between the two
    beams is (anchor_count - 1) per beam. We place anchor points
    at every loop vertex. The segment types list is one per
    loop vertex pair.

    Returns:
        boundary_loop : (n, 3) array
        anchors       : list of int (all loop vertices)
        seg_types     : list of str, length = n (loops around)
    """
    n_pts = len(x)
    s, total = arclength_parametrisation(x, z_beam)
    if total <= 0:
        s = np.linspace(0.0, 1.0, n_pts)
        total = 1.0

    # Anchors at equal arc fractions, including both tips.
    arc_targets = np.linspace(0.0, total, anchor_count)

    # Beam L: far tip -> near tip.
    beam_L = np.zeros((anchor_count, 3))
    for k, target in enumerate(arc_targets):
        bx = float(np.interp(target, s, x))
        bz = float(np.interp(target, s, z_beam))
        by = float(np.interp(target, s, y1))
        beam_L[k] = (bx, by, bz)

    # Beam R: near tip -> far tip (reverse).
    beam_R = np.zeros((anchor_count, 3))
    for k, target in enumerate(arc_targets[::-1]):
        bx = float(np.interp(target, s, x))
        bz = float(np.interp(target, s, z_beam))
        by = float(np.interp(target, s, y2))
        beam_R[k] = (bx, by, bz)

    # Closed loop: Beam L forward, Beam R interior (skip both tips).
    boundary_loop = np.vstack([beam_L, beam_R[1:-1]])
    n_loop = boundary_loop.shape[0]

    # Every loop vertex is an anchor.
    anchors = list(range(n_loop))

    # Segment types. All "beam" for kader. All "cable" for
    # cable_supported.
    if str(attachment_type).lower() == "cable_supported":
        seg_types = ["cable"] * n_loop
    else:
        seg_types = ["beam"] * n_loop

    return boundary_loop, anchors, seg_types





# =============================================================================
# MESH BUILDER
# =============================================================================

def _build_saddle_mbs(span, apex, rise, curve_type,
                       anchor_count, mesh_spacing, transverse_count,
                       warp_pretension, weft_pretension,
                       edge_cable_pretension,
                       attachment_type, tiedown_pretension):
    """
    Build the boundary loop, call the triangulated engine,
    solve FDM. Return everything the viewer needs.

    The transverse_count and mesh_spacing are used only as
    hints for the target edge length. The triangulated engine
    chooses the actual density.

    Returns a dict with:
        points            (n_nodes, 3) array (solved)
        triangles         list of (a, b, c)
        boundary_loop     (n, 3) input boundary
        anchors           list of int
        seg_types         list of str
        diagnostics       dict
    """
    # ---- 1. Beam curve geometry.
    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)

    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    # ---- 2. Boundary loop and metadata.
    boundary_loop, anchors, seg_types = _build_boundary_loop(
        x, z_beam, y1, y2, span, anchor_count, attachment_type
    )

    # ---- 3. Target edge length from mesh spacing.
    # If mesh_spacing is > 0, use it. Otherwise the engine
    # computes its own default from the boundary.
    if mesh_spacing is not None and mesh_spacing > 0:
        target_len = float(mesh_spacing)
    else:
        target_len = None

    # ---- 4. Force density scalars.
    # The engine takes warp_q, weft_q, edge_q directly.
    # Convert from pretension (kN/m) using the average segment
    # length as the reference.
    n = boundary_loop.shape[0]
    total_len = 0.0
    for i in range(n):
        p0 = boundary_loop[i]
        p1 = boundary_loop[(i + 1) % n]
        total_len += float(np.linalg.norm(p1 - p0))
    L_avg = total_len / float(n)
    if L_avg < 1e-9:
        L_avg = 1.0

    warp_q = max(0.1, float(warp_pretension)) * 1000.0 / L_avg
    weft_q = max(0.1, float(weft_pretension)) * 1000.0 / L_avg
    edge_q = max(0.1, float(edge_cable_pretension)) * 1000.0 / L_avg

    # ---- 5. Call the engine.
    result = build_mesh_triangulated(
        boundary_loop=boundary_loop,
        anchor_indices=anchors,
        segment_types=seg_types,
        target_edge_length=target_len,
        plan_plane=None,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q,
    )

    points = result["points"]
    points_initial = result["points_initial"]
    edges = result["edges"]
    triangles = result["triangles"]
    fixed_indices = result["fixed_indices"]
    q = result["q"]
    diag = result["diagnostics"]

    # ---- 6. The engine already form-found the mesh.
    # build_mesh_triangulated runs solve_fdm internally at
    # step 8. The viewer reads the result. It does not call
    # solve_fdm again. This matches the professional FDM
    # workflow: the form-finder owns the solve, the results
    # page reads the answer.
    coords = points

    # ---- 7. Diagnostics.
    n_nodes = coords.shape[0]

    disp = np.linalg.norm(coords - points_initial, axis=1)
    order = np.argsort(disp)[::-1]
    top_disp = []
    for rank, k in enumerate(order[:20]):
        top_disp.append({
            "rank": rank + 1,
            "node": int(k),
            "disp": float(disp[k]),
        })

    # Triangle areas on the solved mesh.
    tri_areas = []
    for (a, b, c) in triangles:
        p0 = coords[a]
        p1 = coords[b]
        p2 = coords[c]
        area = 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0)))
        tri_areas.append(area)
    tri_areas = np.array(tri_areas) if tri_areas else np.array([0.0])

    diagnostics = {
        "residual_norm": float(res["residual_norm"]),
        "n_free": int(res["n_free"]),
        "n_fixed": int(res["n_fixed"]),
        "n_nodes": int(n_nodes),
        "n_edges": len(edges),
        "n_triangles": len(triangles),
        "n_anchors": len(anchors),
        "n_segments": len(seg_types),
        "target_edge_length": float(target_len) if target_len else 0.0,
        "L_avg": float(L_avg),
        "min_tri_area": float(tri_areas.min()),
        "mean_tri_area": float(tri_areas.mean()),
        "max_tri_area": float(tri_areas.max()),
        "attachment_type": str(attachment_type),
        "tiedown_pretension": float(tiedown_pretension),
        "top_displacements": top_disp,
        "structural_connections": [],
    }

    built = {
        "points": coords,
        "triangles": triangles,
        "boundary_loop": boundary_loop,
        "anchors": anchors,
        "seg_types": seg_types,
        "diagnostics": diagnostics,
    }
    return built





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

    anchor_count = int(st.session_state.get("ws_ss_anchor_count", 15))
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

    # ---- Build the mesh via the triangulated engine.
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
    coords = built["points"]
    triangles = built["triangles"]
    boundary_loop = built["boundary_loop"]
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

    # ---- Membrane mesh from the engine's triangles.
    node_x = coords[:, 0].tolist()
    node_y = coords[:, 1].tolist()
    node_z = coords[:, 2].tolist()
    tri_i = [int(t[0]) for t in triangles]
    tri_j = [int(t[1]) for t in triangles]
    tri_k = [int(t[2]) for t in triangles]

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
    anchor_x = [float(boundary_loop[i][0]) for i in range(len(boundary_loop))]
    anchor_y = [float(boundary_loop[i][1]) for i in range(len(boundary_loop))]
    anchor_z = [float(boundary_loop[i][2]) for i in range(len(boundary_loop))]

    fig.add_trace(go.Scatter3d(
        x=anchor_x, y=anchor_y, z=anchor_z,
        mode="markers",
        marker=dict(color="#f39c12", size=5, symbol="circle"),
        name="Anchors",
        showlegend=False,
        hoverinfo="skip",
    ))

    # ---- Attachment method drawing.
    if attach_type == "cable_supported":
        fig.add_trace(go.Scatter3d(
            x=anchor_x, y=anchor_y, z=anchor_z,
            mode="lines",
            line=dict(color="#f1c40f", width=3),
            name="Fabric edge cable",
            showlegend=True,
            hoverinfo="skip",
        ))
    else:
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_beam,
            mode="lines",
            line=dict(color="#f39c12", width=2),
            showlegend=True,
            name="Kader track",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_beam,
            mode="lines",
            line=dict(color="#f39c12", width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

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
                anchor_x_t = x_tie - x_offset
            elif x_tie > 0:
                anchor_x_t = x_tie + x_offset
            else:
                anchor_x_t = x_tie + x_offset

            anchor_y_t = y_beam + side * y_offset

            fig.add_trace(go.Scatter3d(
                x=[x_tie, anchor_x_t],
                y=[y_beam, anchor_y_t],
                z=[beam_z, 0],
                mode="lines",
                line=dict(color="#f1c40f", width=2, dash="dot"),
                showlegend=False,
                hoverinfo="skip",
            ))

            fig.add_trace(go.Scatter3d(
                x=[anchor_x_t], y=[anchor_y_t], z=[0],
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

    # ---- Diagnostics expander.
    with st.expander("FDM diagnostics (temporary)", expanded=False):
        st.markdown("**Boundary loop:**")
        c0, c0b, c0c = st.columns(3)
        c0.metric("Loop vertices", diag["n_anchors"])
        c0b.metric("Segments", diag["n_segments"])
        c0c.metric("Target edge", "%.3f" % diag["target_edge_length"])

        st.markdown("**Triangulated mesh:**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nodes", diag["n_nodes"])
        c2.metric("Edges", diag["n_edges"])
        c3.metric("Triangles", diag["n_triangles"])
        c4.metric("Fixed", diag["n_fixed"])

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
# This file is Step 5 of the migration. It uses the triangulated
# mesh engine (engine/mesh_triangulated.py). The tips close
# naturally by triangulation. No fan, no degenerate column.
#
# Files untouched by this rewrite:
#   engine/form_finding.py
#   engine/mesh_universal.py         (still live as fallback)
#   engine/mesh_universal_test.py    (still live)
#   engine/mesh_triangulated.py
#   engine/mesh_triangulated_test.py
# =============================================================================





