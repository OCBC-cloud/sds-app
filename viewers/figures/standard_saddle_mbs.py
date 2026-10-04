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
#   Beam L forward (all points), then Beam R interior (skip both
#   tips since they are shared). The loop is closed by convention.
#
# Anchors and segments (Step 2E, 2026-10-04):
#   The anchors are the attachment points. They are placed at
#   equal arc fractions along each beam. Between consecutive
#   anchors, the boundary is subdivided into interior points
#   spaced by mesh_spacing.
#
#   The engine then holds the anchors. It holds or releases the
#   interior points based on the segment type:
#     kader            -> all segments are "beam"  -> all held.
#     cable_supported  -> all segments are "cable" -> released.
#
#   In cable_supported mode, the released points move to a new
#   equilibrium. The edge cable runs between the anchors and
#   carries the load.
#
# History:
#   2026-09-29 - Step 2C. First MBS version. Hand-built mesh.
#   2026-09-30 - Step 2D. Wired to a structured engine.
#   2026-09-30 - Step 5. Rewritten to use the triangulated engine.
#   2026-10-04 - Step 2E. Anchors and subdivision. Cable toggle
#                finally works. Edge cable drawn between anchors.
#                Edge cable length reported.
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
from data.materials import CABLE_PROPERTIES


# =============================================================================
# CABLE SIZE PICKER (internal)
# =============================================================================

def _pick_cable_diameter(cable_type, material, pretension_kN,
                          safety_factor=5.0):
    """
    Pick the smallest cable diameter in the given family whose
    breaking load exceeds pretension * safety_factor.

    Returns a dict with the chosen entry's fields, or None.
    The user does not see this. It is reported in diagnostics.
    """
    family = None
    if cable_type == "6x19":
        family = CABLE_PROPERTIES.get("Strand", {})
    elif cable_type == "Locked Coil":
        family = CABLE_PROPERTIES.get("Locked Coil", {})
    elif cable_type == "Spiral":
        family = CABLE_PROPERTIES.get("Spiral", {})

    if not family:
        return None

    required_kN = float(pretension_kN) * float(safety_factor)

    # Sort the family by area, ascending.
    entries = []
    for name, props in family.items():
        if name == "default":
            continue
        try:
            A_mm2 = float(props.get("A", 0.0))
            f_u = float(props.get("f_u", 0.0))
        except Exception:
            continue
        if A_mm2 <= 0 or f_u <= 0:
            continue
        breaking_kN = A_mm2 * f_u / 1000.0
        entries.append({
            "name": name,
            "d": float(props.get("d", 0.0)),
            "A": A_mm2,
            "f_u": f_u,
            "E": float(props.get("E", 0.0)),
            "kg_m": float(props.get("kg_m", 0.0)),
            "breaking_kN": breaking_kN,
        })

    entries.sort(key=lambda e: e["A"])
    for e in entries:
        if e["breaking_kN"] >= required_kN:
            return e

    # Nothing satisfies the requirement. Return the largest.
    if entries:
        return entries[-1]
    return None


# =============================================================================
# BOUNDARY LOOP
# =============================================================================

def _build_boundary_loop(x, z_beam, y1, y2, span, anchor_count,
                          mesh_spacing, attachment_type):
    """
    Build the closed boundary loop, the anchor indices, and
    the segment types for the triangulated engine.

    Layout (Step 2E):
        Beam L:  anchor_count anchors from far tip P0 to near tip P1.
                 Between consecutive anchors, sub interior points.
        Beam R:  anchor_count anchors from near tip P1 to far tip P0.
                 Between consecutive anchors, sub interior points.
        The two tips are shared.
        The closed loop is:
            Beam L all points,
            then Beam R interior (skip both tips, they are already
            in Beam L).

    Anchors: only the true anchor points. Not every loop point.

    Segments: one per consecutive anchor pair. All "beam" for kader,
    all "cable" for cable_supported.

    Returns:
        boundary_loop : (n, 3) array
        anchors       : list of int, indices into boundary_loop
        seg_types     : list of str, one per segment
        anchor_pos    : (anchor_count * 2 - 2, 3) array of the
                        anchor points themselves
    """
    n_pts = len(x)
    s, total = arclength_parametrisation(x, z_beam)
    if total <= 0:
        s = np.linspace(0.0, 1.0, n_pts)
        total = 1.0

    # Anchor arc-length targets on one beam: anchor_count equally
    # spaced values from 0 to total.
    arc_targets = np.linspace(0.0, total, anchor_count)

    # Subdivision between consecutive anchors: derived from
    # mesh_spacing and the segment arc length.
    if anchor_count > 1:
        seg_arc = total / float(anchor_count - 1)
    else:
        seg_arc = total
    if mesh_spacing is None or mesh_spacing <= 0:
        sub = 1
    else:
        sub = int(round(seg_arc / float(mesh_spacing)))
        if sub < 1:
            sub = 1
        if sub > 20:
            sub = 20

    # Build one beam's point list (anchor + interior points).
    def _beam_points(y_curve, reverse=False):
        pts = []
        anchors_local = []
        for k in range(anchor_count):
            target = arc_targets[k]
            bx = float(np.interp(target, s, x))
            bz = float(np.interp(target, s, z_beam))
            by = float(np.interp(target, s, y_curve))
            anchors_local.append(len(pts))
            pts.append((bx, by, bz))
            # Interior points between this anchor and the next.
            if k < anchor_count - 1 and sub > 0:
                a0 = arc_targets[k]
                a1 = arc_targets[k + 1]
                for j in range(1, sub + 1):
                    frac = float(j) / float(sub + 1)
                    target_mid = a0 + (a1 - a0) * frac
                    mx = float(np.interp(target_mid, s, x))
                    mz = float(np.interp(target_mid, s, z_beam))
                    my = float(np.interp(target_mid, s, y_curve))
                    pts.append((mx, my, mz))
        if reverse:
            # Reverse the order but keep track of anchors.
            n = len(pts)
            rev_pts = [pts[n - 1 - i] for i in range(n)]
            rev_anchors = [n - 1 - a for a in anchors_local]
            return rev_pts, rev_anchors
        return pts, anchors_local

    # Beam L: far tip -> near tip.
    beam_L_pts, beam_L_anchors = _beam_points(y1, reverse=False)

    # Beam R: near tip -> far tip. Reverse so its first point
    # is the near tip (already in Beam L) and its last is the
    # far tip (also in Beam L).
    beam_R_pts, beam_R_anchors = _beam_points(y2, reverse=True)

    # Assemble the loop.
    # Beam L: all points.
    # Beam R: skip the first (near tip) and the last (far tip).
    loop_pts = list(beam_L_pts)
    # Beam R interior points: skip index 0 (near tip) and index n-1 (far tip).
    for i in range(1, len(beam_R_pts) - 1):
        loop_pts.append(beam_R_pts[i])

    boundary_loop = np.asarray(loop_pts, dtype=float)
    n_loop = boundary_loop.shape[0]

    # Build the anchors list, in loop order.
    # Beam L anchors are already at the correct loop indices.
    anchors = list(beam_L_anchors)
    # Beam R anchors: map to loop indices. Beam R interior points
    # start at loop index len(beam_L_pts) and correspond to
    # beam_R indices 1..n-2.
    offset = len(beam_L_pts)
    for a in beam_R_anchors:
        if a == 0:
            # Near tip. Same as beam_L_anchors[-1].
            continue
        if a == len(beam_R_pts) - 1:
            # Far tip. Same as beam_L_anchors[0].
            continue
        loop_idx = offset + (a - 1)
        anchors.append(loop_idx)

    anchors = sorted(set(anchors))

    # Segment types: one per consecutive anchor pair.
    n_seg = len(anchors)
    if str(attachment_type).lower() == "cable_supported":
        seg_types = ["cable"] * n_seg
    else:
        seg_types = ["beam"] * n_seg

    # Anchor positions, for drawing and length computation.
    anchor_pos = boundary_loop[anchors]

    return boundary_loop, anchors, seg_types, anchor_pos


# =============================================================================
# MESH BUILDER
# =============================================================================

def _build_saddle_mbs(span, apex, rise, curve_type,
                       anchor_count, mesh_spacing, transverse_count,
                       warp_pretension, weft_pretension,
                       edge_cable_pretension,
                       attachment_type, tiedown_pretension,
                       edge_cable_type, edge_cable_material,
                       tiedown_cable_type, tiedown_cable_material):
    """
    Build the boundary loop, call the triangulated engine,
    solve FDM. Return everything the viewer needs.

    Returns a dict with the engine output plus diagnostics.
    """
    # ---- 1. Beam curve geometry.
    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)

    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    # ---- 2. Boundary loop and metadata.
    boundary_loop, anchors, seg_types, anchor_pos = _build_boundary_loop(
        x, z_beam, y1, y2, span, anchor_count, mesh_spacing,
        attachment_type,
    )

    # ---- 3. Target edge length from mesh spacing.
    if mesh_spacing is not None and mesh_spacing > 0:
        target_len = float(mesh_spacing)
    else:
        target_len = None

    # ---- 4. Force density scalars.
    n = boundary_loop.shape[0]
    total_len = 0.0
    for i in range(n):
        p0 = boundary_loop[i]
        p1 = boundary_loop[(i + 1) % n]
        total_len += float(np.linalg.norm(p1 - p0))
    L_avg = total_len / float(n)
    if L_avg < 1e-9:
        L_avg = 1.0

    # Ratio-anchored force density, ratio limit 4.0.
    baseline_kN_per_m = 2.0
    ratio_limit = 4.0

    warp_input = max(0.1, float(warp_pretension))
    weft_input = max(0.1, float(weft_pretension))

    mean_input = 0.5 * (warp_input + weft_input)
    if mean_input < 1e-9:
        mean_input = 1.0

    warp_rel = warp_input / mean_input
    weft_rel = weft_input / mean_input

    if warp_rel / weft_rel > ratio_limit:
        warp_rel = ratio_limit * weft_rel
    if weft_rel / warp_rel > ratio_limit:
        weft_rel = ratio_limit * warp_rel

    warp_q = baseline_kN_per_m * warp_rel * 1000.0 / L_avg
    weft_q = baseline_kN_per_m * weft_rel * 1000.0 / L_avg
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

    coords = result["points"]
    points_initial = result["points_initial"]
    edges = result["edges"]
    triangles = result["triangles"]
    fixed_indices = result["fixed_indices"]
    q = result["q"]
    diag = result["diagnostics"]

    # ---- 6. Edge cable: length, mass, diameter.
    edge_cable_length_m = 0.0
    edge_cable_entries = []
    if str(attachment_type).lower() == "cable_supported":
        # Sum of anchor-to-anchor distances along the loop.
        n_a = len(anchors)
        for k in range(n_a):
            a = anchor_pos[k]
            b = anchor_pos[(k + 1) % n_a]
            edge_cable_length_m += float(np.linalg.norm(b - a))

    chosen_edge = _pick_cable_diameter(
        edge_cable_type, edge_cable_material,
        float(edge_cable_pretension),
    )
    chosen_tiedown = _pick_cable_diameter(
        tiedown_cable_type, tiedown_cable_material,
        float(tiedown_pretension),
    )

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

    tri_areas = []
    for (a, b, c) in triangles:
        p0 = coords[a]
        p1 = coords[b]
        p2 = coords[c]
        area = 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0)))
        tri_areas.append(area)
    tri_areas = np.array(tri_areas) if tri_areas else np.array([0.0])

    diagnostics = {
        "residual_norm": float(diag.get("residual_norm", 0.0)),
        "n_free": int(diag.get("n_free", 0)),
        "n_fixed": int(len(fixed_indices)),
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
        "anchor_count": int(anchor_count),
        "mesh_spacing": float(mesh_spacing),
        "edge_cable_length_m": float(edge_cable_length_m),
        "edge_cable_type": str(edge_cable_type),
        "edge_cable_material": str(edge_cable_material),
        "edge_cable_pretension_kN": float(edge_cable_pretension),
        "edge_cable_chosen": chosen_edge,
        "tiedown_cable_type": str(tiedown_cable_type),
        "tiedown_cable_material": str(tiedown_cable_material),
        "tiedown_pretension_kN": float(tiedown_pretension),
        "tiedown_cable_chosen": chosen_tiedown,
        "top_displacements": top_disp,
        "structural_connections": [],
    }

    built = {
        "points": coords,
        "points_initial": points_initial,
        "edges": edges,
        "triangles": triangles,
        "fixed_indices": fixed_indices,
        "q": q,
        "boundary_loop": boundary_loop,
        "anchors": anchors,
        "anchor_pos": anchor_pos,
        "seg_types": seg_types,
        "diagnostics": diagnostics,
        "warp_q": float(warp_q),
        "weft_q": float(weft_q),
        "edge_q": float(edge_q),
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

    anchor_count = int(st.session_state.get("ws_ss_anchor_count", 8))
    mesh_spacing = float(st.session_state.get("ws_ss_mesh_spacing", 0.5))
    transverse_count = int(st.session_state.get("ws_ss_transverse_count", 8))

    tiedown_pre = float(st.session_state.get("ws_ss_tiedown_pretension", 2.5))
    edge_cable_type = str(
        st.session_state.get("ws_ss_edge_cable_type", "6x19")
    )
    edge_cable_material = str(
        st.session_state.get("ws_ss_edge_cable_material", "stainless")
    )
    tiedown_cable_type = str(
        st.session_state.get("ws_ss_tiedown_cable_type", "6x19")
    )
    tiedown_cable_material = str(
        st.session_state.get("ws_ss_tiedown_cable_material", "galvanised")
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
        tiedown_pretension=tiedown_pre,
        edge_cable_type=edge_cable_type,
        edge_cable_material=edge_cable_material,
        tiedown_cable_type=tiedown_cable_type,
        tiedown_cable_material=tiedown_cable_material,
    )
    coords = built["points"]
    points_initial = built["points_initial"]
    edges = built["edges"]
    triangles = built["triangles"]
    fixed_indices = built["fixed_indices"]
    q = built["q"]
    boundary_loop = built["boundary_loop"]
    anchor_pos = built["anchor_pos"]
    diag = built["diagnostics"]
    warp_q = built["warp_q"]
    weft_q = built["weft_q"]
    edge_q = built["edge_q"]

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

    # ---- Anchor markers.
    anchor_x = anchor_pos[:, 0].tolist()
    anchor_y = anchor_pos[:, 1].tolist()
    anchor_z = anchor_pos[:, 2].tolist()

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
        # Edge cable: line between consecutive anchors, closed loop.
        # Split into two polylines: one per beam.
        n_a = len(anchor_pos)
        half = n_a // 2

        # Beam L edge cable: anchors 0..half-1
        beamL_anchors = anchor_pos[:half + 1]
        fig.add_trace(go.Scatter3d(
            x=beamL_anchors[:, 0].tolist(),
            y=beamL_anchors[:, 1].tolist(),
            z=beamL_anchors[:, 2].tolist(),
            mode="lines+markers",
            line=dict(color="#f1c40f", width=4),
            marker=dict(color="#f1c40f", size=4),
            name="Edge cable L",
            hoverinfo="skip",
        ))

        # Beam R edge cable: anchors half..end, plus closing to anchor 0.
        beamR_anchors = anchor_pos[half:]
        close = anchor_pos[:1]
        beamR_full = np.vstack([beamR_anchors, close])
        fig.add_trace(go.Scatter3d(
            x=beamR_full[:, 0].tolist(),
            y=beamR_full[:, 1].tolist(),
            z=beamR_full[:, 2].tolist(),
            mode="lines+markers",
            line=dict(color="#f1c40f", width=4),
            marker=dict(color="#f1c40f", size=4),
            name="Edge cable R",
            showlegend=False,
            hoverinfo="skip",
        ))
    else:
        # Kader track lines along both beams.
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
        st.markdown("**Shape inputs:**")
        c0, c0b, c0c = st.columns(3)
        c0.metric("Anchors/beam", diag["anchor_count"])
        c0b.metric("Mesh spacing", "%.2f" % diag["mesh_spacing"])
        c0c.metric("Loop anchors", diag["n_anchors"])

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

        if diag["attachment_type"] == "cable_supported":
            st.markdown("**Edge cable:**")
            ce = diag["edge_cable_chosen"]
            st.markdown(
                "- Type: " + diag["edge_cable_type"] +
                "  |  Material: " + diag["edge_cable_material"] +
                "  |  Prestress: " +
                ("%.1f kN" % diag["edge_cable_pretension_kN"])
            )
            st.markdown(
                "- Length: " +
                ("%.3f m" % diag["edge_cable_length_m"])
            )
            if ce is not None:
                st.markdown(
                    "- System-selected diameter: " +
                    ("%.1f mm" % ce["d"]) +
                    "  |  Area: " + ("%.1f mm2" % ce["A"]) +
                    "  |  Breaking: " + ("%.2f kN" % ce["breaking_kN"])
                )
                total_mass = ce["kg_m"] * diag["edge_cable_length_m"]
                st.markdown(
                    "- Total mass: " + ("%.3f kg" % total_mass)
                )

        st.markdown("**Tie-down cables:**")
        ct = diag["tiedown_cable_chosen"]
        st.markdown(
            "- Type: " + diag["tiedown_cable_type"] +
            "  |  Material: " + diag["tiedown_cable_material"] +
            "  |  Prestress: " +
            ("%.1f kN" % diag["tiedown_pretension_kN"])
        )
        if ct is not None:
            st.markdown(
                "- System-selected diameter: " +
                ("%.1f mm" % ct["d"]) +
                "  |  Area: " + ("%.1f mm2" % ct["A"]) +
                "  |  Breaking: " + ("%.2f kN" % ct["breaking_kN"])
            )

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
#
# This file is Step 2E of the migration. It uses the
# triangulated mesh engine (engine/mesh_triangulated.py).
# The boundary loop now carries proper anchors and proper
# segment types. The cable toggle releases the boundary
# points between anchors.
#
# Files untouched by this rewrite:
#   engine/form_finding.py
#   engine/mesh_triangulated.py
#   engine/mesh_triangulated_test.py
# =============================================================================
