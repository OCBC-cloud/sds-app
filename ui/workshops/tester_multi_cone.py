"""Multi-Cone Roof — Lab test page.

Stage 3 Lab test for the multi-cone roof. Reads user inputs, builds
the geometry, and calls engine/SDSe_mesh_builder for the membrane mesh.

The perimeter is a real cable. Every intermediate perimeter node is
fully free (3 DOF). Only the eave anchors are held. A node constrained
to slide only along the local tangent cannot respond to the membrane's
inward pull; with free nodes the cable bows the way a real cable does.

Everything downstream of the geometry uses the shared engine:
    - SDSe_mesh_rings
    - SDSe_blend_q_per_edge
    - solve_fdm

No mesh-builder code lives in this file.

History:
    First SDSe-only version.
    Renamed SDSe_mesh_rings_spine to SDSe_mesh_rings.
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm
from engine.SDSe_mesh_builder import (
    SDSe_mesh_rings,
    SDSe_blend_q_per_edge,
)
from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
)


RIB_SEGMENTS = 80

COL_MEMBRANE = "#4a7a9c"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"


# =============================================================================
# Geometry helpers (Lab-tester specific; not part of the shared engine)
# =============================================================================

def _ellipse_y(x, span, mid_width):
    a = span / 2.0
    b = mid_width / 2.0
    t = max(0.0, 1.0 - (x / a) ** 2)
    return b * math.sqrt(t)


def _rib_stations(n, optional_ends, span, x, s, total):
    if (not optional_ends) or n < 3:
        fracs = np.array([k / (n + 1.0) for k in range(1, n + 1)], dtype=float)
        return np.interp(fracs * total, s, x)
    xt = span / 2.0 - 3.0
    return np.linspace(-xt, +xt, n)


def _rib_arch_y_at_eave(peak_z, half_width, eave_height):
    if peak_z <= eave_height:
        return None
    u2 = 1.0 - eave_height / peak_z
    if u2 < 0.0:
        return None
    return half_width * math.sqrt(u2)


def _rib_polyline(rib_x, half_width, peak_z, n):
    y = np.linspace(-half_width, +half_width, n)
    u = y / half_width
    z = peak_z * (1.0 - u ** 2)
    x = np.full_like(y, rib_x)
    return np.column_stack([x, y, z])


def _tip_x_at_eave(span, apex, eave_height, curve_type):
    if apex <= eave_height:
        return span / 2.0
    x_fine = np.linspace(0.0, span / 2.0, 2000)
    z_fine = beam_curve(x_fine, span, apex, curve_type)
    idx = np.where(z_fine >= eave_height)[0]
    if len(idx) == 0:
        return span / 2.0
    return float(x_fine[idx[-1]])


def _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height,
                         tip_x):
    plus, minus = [], []
    for i, xr in enumerate(rib_x):
        y_at = _rib_arch_y_at_eave(
            float(rib_peak_z[i]), float(rib_half_width[i]), eave_height
        )
        if y_at is None:
            continue
        plus.append((float(xr), +y_at, eave_height))
        minus.append((float(xr), -y_at, eave_height))
    pts = list(plus)
    pts.append((+tip_x, 0.0, eave_height))
    for p in reversed(minus):
        pts.append(p)
    pts.append((-tip_x, 0.0, eave_height))
    return np.asarray(pts, dtype=float)


def _subdivide_polygon(anchors, subdivisions):
    n_a = anchors.shape[0]
    loop = []
    anchor_idx = []
    for i in range(n_a):
        a = anchors[i]
        b = anchors[(i + 1) % n_a]
        anchor_idx.append(len(loop))
        for k in range(subdivisions):
            f = k / float(subdivisions)
            loop.append(a + (b - a) * f)
    return np.asarray(loop, dtype=float), anchor_idx


def _cone_arc_positions(n_cones, spacing, total):
    if n_cones < 1:
        raise ValueError("Number of cones must be at least 1.")
    mid = total / 2.0
    if n_cones % 2 == 1:
        half = (n_cones - 1) // 2
        ks = [0]
        for i in range(1, half + 1):
            ks.append(+i)
            ks.append(-i)
    else:
        half = n_cones // 2
        ks = []
        for i in range(half):
            k = i + 0.5
            ks.append(+k)
            ks.append(-k)
    positions = [mid + k * spacing for k in ks]
    for p in positions:
        if p < 0.0 or p > total:
            raise ValueError(
                "Ring position %.3f m falls outside the primary span "
                "of %.3f m.  Reduce spacing or cone count." % (p, total)
            )
    return sorted(positions)


# =============================================================================
# Member schedule (Lab-tester specific; builds a full BOQ-style list)
# =============================================================================

def _build_member_schedule(built, coords, ring_x_positions,
                            anchor_idx, edge_q_scalar,
                            warp_q, weft_q):
    members = []
    ring_indices = built["ring_indices"]
    centre_indices = built["centre_indices"]
    beam_top_indices = built["beam_top_indices"]
    triangles = built["triangles"]
    n_perimeter = built["n_perimeter"]

    for k in range(len(ring_indices)):
        ring_no = k + 1
        idx_list = ring_indices[k]
        centre_i = int(centre_indices[k])
        beam_i = int(beam_top_indices[k])
        n_poly = len(idx_list)

        ring_length = 0.0
        for i in range(n_poly):
            a = int(idx_list[i])
            b = int(idx_list[(i + 1) % n_poly])
            ring_length += float(np.linalg.norm(coords[b] - coords[a]))
        members.append({
            "member_id": f"Ring_{ring_no}_Ring_Beam",
            "member_type": "ring_beam",
            "ring_index": ring_no,
            "node_a": int(idx_list[0]),
            "node_b": int(idx_list[0]),
            "length_m": float(ring_length),
            "section": "TBD", "material": "TBD",
            "role": "closed ring beam, one per cone",
        })
        for i in range(n_poly):
            a = int(idx_list[i]); b = int(idx_list[(i + 1) % n_poly])
            L = float(np.linalg.norm(coords[b] - coords[a]))
            members.append({
                "member_id": f"Ring_{ring_no}_Beam_Seg_{i+1:02d}",
                "member_type": "ring_beam_segment",
                "ring_index": ring_no,
                "node_a": a, "node_b": b, "length_m": L,
                "section": "TBD", "material": "TBD",
                "role": "ring beam segment between adjacent nodes",
            })
        for i, node_i in enumerate(idx_list):
            node_i = int(node_i)
            L = float(np.linalg.norm(coords[node_i] - coords[centre_i]))
            members.append({
                "member_id": f"Ring_{ring_no}_Spoke_{i+1:02d}",
                "member_type": "spoke",
                "ring_index": ring_no,
                "node_a": centre_i, "node_b": node_i, "length_m": L,
                "section": "TBD", "material": "TBD",
                "role": "radial spoke from ring centre to ring circle",
            })
        L = float(np.linalg.norm(coords[beam_i] - coords[centre_i]))
        members.append({
            "member_id": f"Ring_{ring_no}_Drop_Member",
            "member_type": "drop_member",
            "ring_index": ring_no,
            "node_a": beam_i, "node_b": centre_i, "length_m": L,
            "section": "TBD", "material": "TBD",
            "role": "vertical drop member from primary beam to ring centre",
        })

    total_cable_length = 0.0
    for i in range(n_perimeter):
        j = (i + 1) % n_perimeter
        total_cable_length += float(np.linalg.norm(coords[j] - coords[i]))
    members.append({
        "member_id": "Edge_Cable",
        "member_type": "cable",
        "ring_index": 0,
        "node_a": 0,
        "node_b": n_perimeter - 1,
        "length_m": total_cable_length,
        "section": "CABLE",
        "material": "Steel strand",
        "role": "perimeter edge cable, consolidated arclength",
        "prestress": edge_q_scalar,
    })

    anchor_positions = [int(i) for i in anchor_idx]
    n_anchors = len(anchor_positions)
    for k in range(n_anchors):
        start = anchor_positions[k]
        end = anchor_positions[(k + 1) % n_anchors]
        seg_length = 0.0
        i = start
        while True:
            j = (i + 1) % n_perimeter
            seg_length += float(np.linalg.norm(coords[j] - coords[i]))
            if j == end:
                break
            i = j
            if i == start:
                break
        members.append({
            "member_id": f"Edge_Cable_Seg_{k+1:02d}",
            "member_type": "cable_segment",
            "ring_index": 0,
            "node_a": start,
            "node_b": end,
            "length_m": seg_length,
            "section": "CABLE",
            "material": "Steel strand",
            "role": "edge cable segment between anchors",
            "prestress": edge_q_scalar,
        })

    panel_no = 1
    for (a, b, c) in triangles:
        pa = coords[a]
        pb = coords[b]
        pc = coords[c]
        mean_edge = (
            float(np.linalg.norm(pb - pa))
            + float(np.linalg.norm(pc - pb))
            + float(np.linalg.norm(pa - pc))
        ) / 3.0
        members.append({
            "member_id": f"Membrane_Panel_{panel_no:04d}",
            "member_type": "membrane",
            "ring_index": 0,
            "node_a": int(a),
            "node_b": int(b),
            "node_c": int(c),
            "length_m": mean_edge,
            "section": "FABRIC",
            "material": "PVDF Type III",
            "role": "fabric panel between ridge and eave",
            "prestress_warp": warp_q,
            "prestress_weft": weft_q,
        })
        panel_no += 1

    return members


def _format_member_table(members):
    lines = []
    header = (
        "%-26s  %-18s  %-6s  %-6s  %-6s  %-9s  %-8s  %-14s  %s"
        % ("member_id", "member_type", "ring", "node_a", "node_b",
           "length_m", "section", "material", "role")
    )
    lines.append(header)
    lines.append("-" * len(header))
    for m in members:
        lines.append(
            "%-26s  %-18s  %-6d  %-6d  %-6d  %-9.4f  %-8s  %-14s  %s"
            % (m["member_id"], m["member_type"], m.get("ring_index", 0),
               m["node_a"], m["node_b"], m["length_m"],
               m["section"], m["material"], m["role"])
        )
    return "\n".join(lines)


_HEADER = (
    "%6s  %10s  %10s  %10s  %10s  %10s  %10s  %9s  %s"
    % ("idx", "x_init", "y_init", "z_init",
       "x_set", "y_set", "z_set", "disp", "status")
)


def _status_line(i, status, points_initial, points_settled):
    xi, yi, zi = points_initial[i]
    xs, ys, zs = points_settled[i]
    d = float(np.linalg.norm(np.array([xs - xi, ys - yi, zs - zi])))
    return (
        "%6d  %10.5f  %10.5f  %10.5f  %10.5f  %10.5f  %10.5f  %9.4e  %s"
        % (i, xi, yi, zi, xs, ys, zs, d, status)
    )


def _format_all_nodes(points_initial, points_settled, anchor_idx,
                       ring_indices, centre_indices, beam_top_indices,
                       intermediate_perimeter_set):
    n = points_initial.shape[0]
    status_of = ["free"] * n
    for i in anchor_idx:
        status_of[int(i)] = "held_outer_eave_corner"
    for i in intermediate_perimeter_set:
        status_of[int(i)] = "perimeter_cable_free"
    for idx_list in ring_indices:
        for i in idx_list:
            status_of[int(i)] = "held_ring_polygon"
    for i in centre_indices:
        status_of[int(i)] = "held_ring_centre"
    for i in beam_top_indices:
        status_of[int(i)] = "held_beam_top"
    lines = [_HEADER, "-" * len(_HEADER)]
    for i in range(n):
        lines.append(_status_line(i, status_of[i],
                                   points_initial, points_settled))
    return "\n".join(lines)


# =============================================================================
# Page
# =============================================================================

def render_tester_multi_cone():
    bcol1, bcol2, bcol3 = st.columns([1, 1, 3])
    with bcol1:
        if st.button("← Back to Lab", key="mc_back_lab",
                     use_container_width=True):
            st.session_state.page = "lab"
            st.rerun()
    with bcol2:
        if st.button("← Back to Landing", key="mc_back_landing",
                     use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()

    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>"
        "Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>"
        "Perimeter is a real cable. Only the eave anchors are held.</p>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        span = st.number_input("Primary span (m)", 6.0, 60.0, 25.0, 0.5,
                                key="mc_span")
    with c2:
        apex = st.number_input("Primary apex (m)", 1.0, 30.0, 9.0, 0.5,
                                key="mc_apex")

    c1, c2 = st.columns(2)
    with c1:
        mid_width = st.number_input("Mid-span width (m)", 6.0, 60.0, 18.0, 0.5,
                                     key="mc_width")
    with c2:
        eave_height = st.number_input("Eave height (m)", 0.5, 10.0, 2.8, 0.1,
                                       key="mc_eave")

    c1, c2 = st.columns(2)
    with c1:
        ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 1.0, 0.1,
                                         key="mc_rd")
    with c2:
        curve_type = st.selectbox(
            "Curve type", ["parabolic", "circular", "catenary"],
            index=0, key="mc_curve",
        )

    c1, c2 = st.columns(2)
    with c1:
        secondary_count = int(st.number_input("Secondary count", 2, 20, 3, 1,
                                                key="mc_nribs"))
    with c2:
        optional_ends = st.toggle("Optional ends", value=False,
                                    key="mc_optends")

    subdivisions = int(st.number_input(
        "Subdivisions per edge", 5, 25, 17, 1, key="mc_subdiv"
    ))

    c1, c2 = st.columns(2)
    with c1:
        number_of_cones = int(st.number_input(
            "Number of cones", 1, 20, 3, 1, key="mc_ncones"
        ))
    with c2:
        ring_spacing = st.number_input(
            "Distance between adjacent cones (m, along beam)",
            0.5, 10.0, 5.0, 0.1, key="mc_spacing"
        )

    ring_clearance = st.number_input(
        "Ring clearance below beam (m)", 0.1, 5.0, 1.0, 0.1,
        key="mc_clr",
    )

    c1, c2 = st.columns(2)
    with c1:
        warp_q_input = st.number_input(
            "Warp pretension (kN/m)", 0.1, 100.0, 20.0, 0.1, key="mc_warp",
        )
    with c2:
        weft_q_input = st.number_input(
            "Weft pretension (kN/m)", 0.1, 100.0, 20.0, 0.1, key="mc_weft",
        )

    edge_q_input = st.number_input(
        "Edge cable pretension (kN/m)",
        0.1, 500.0, 20.0, 0.1,
        key="mc_edgeq",
    )

    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array(
        [_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float
    )

    placement_error = ""
    ring_specs = []
    x_rings = []
    ring_z_rings = []

    try:
        s_rings = _cone_arc_positions(number_of_cones, ring_spacing, total_p)
        for s_val in s_rings:
            x_val = float(np.interp(s_val, s_p, xp))
            bz_val = float(np.interp(s_val, s_p, zp))
            rz_val = bz_val - float(ring_clearance)
            x_rings.append(x_val)
            ring_z_rings.append(rz_val)
            ring_specs.append({
                "cx": x_val, "cy": 0.0, "cz": rz_val,
                "r": float(ring_diameter) / 2.0,
                "beam_z": bz_val,
            })
    except ValueError as e:
        placement_error = str(e)

    if placement_error:
        st.error("Placement refused: " + placement_error)
        return

    tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
    anchors = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, tip_x
    )
    perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
    bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
    L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
    target_len = max(L_avg, 1e-6)

    # ---- SDSe engine call ------------------------------------------------
    built = SDSe_mesh_rings(
        perimeter_loop=perimeter_loop,
        anchor_idx=anchor_idx,
        ring_specs=ring_specs,
        eave_height=eave_height,
        target_len=target_len,
    )

    pts = built["points"]
    edges = built["edges"]
    boundary_edge_set = built["boundary_edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]

    n_perimeter = built["n_perimeter"]
    anchor_set = set(int(i) for i in anchor_idx)
    intermediate_perimeter = [
        i for i in range(n_perimeter) if i not in anchor_set
    ]

    warp_q = max(float(warp_q_input), 0.1) * 1000.0
    weft_q = max(float(weft_q_input), 0.1) * 1000.0
    edge_q_scalar = max(float(edge_q_input), 0.1) * 1000.0

    pts_2d = pts[:, :2]
    warp_dir = np.array([1.0, 0.0])
    q_interior = SDSe_blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q)

    q = np.empty(len(edges), dtype=float)
    for k, (i, j) in enumerate(edges):
        key = (i, j) if i < j else (j, i)
        if key in boundary_edge_set:
            q[k] = edge_q_scalar
        else:
            q[k] = q_interior[k]

    try:
        fdm = solve_fdm(pts, edges, fixed, q)
        coords = fdm["coordinates"]
        residual_norm = float(fdm["residual_norm"])
        solve_ok = True
        solve_err = ""
        dof_count = int(fdm.get("dof_count", 0))
    except Exception as e:
        coords = pts.copy()
        residual_norm = float("nan")
        solve_ok = False
        solve_err = str(e)
        dof_count = 0

    fig = go.Figure()

    if len(tris) > 0:
        tri = np.asarray(tris, dtype=int)
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            name="membrane", showlegend=False, hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter3d(
        x=xp, y=np.zeros_like(xp), z=zp,
        mode="lines", line=dict(color=COL_PRIMARY, width=7),
        name="primary beam", showlegend=False, hoverinfo="skip",
    ))

    for i in range(len(rib_x)):
        rp = _rib_polyline(
            float(rib_x[i]), float(rib_half_width[i]),
            float(rib_peak_z[i]), RIB_SEGMENTS,
        )
        fig.add_trace(go.Scatter3d(
            x=rp[:, 0], y=rp[:, 1], z=rp[:, 2],
            mode="lines", line=dict(color=COL_RIB, width=5),
            name="rib", showlegend=False, hoverinfo="skip",
        ))

    for k, idx_list in enumerate(built["ring_indices"]):
        pp = coords[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name="ring", showlegend=False, hoverinfo="skip",
        ))
        centre_i = built["centre_indices"][k]
        beam_i = built["beam_top_indices"][k]
        cx, cy, cz = coords[centre_i]
        for poly_i in idx_list:
            fig.add_trace(go.Scatter3d(
                x=[cx, coords[poly_i, 0]],
                y=[cy, coords[poly_i, 1]],
                z=[cz, coords[poly_i, 2]],
                mode="lines", line=dict(color=COL_SPOKE, width=2),
                name="spoke", showlegend=False, hoverinfo="skip",
            ))
        bx, by, bz = coords[beam_i]
        fig.add_trace(go.Scatter3d(
            x=[cx, bx], y=[cy, by], z=[cz, bz],
            mode="lines", line=dict(color=COL_DROP, width=4),
            name="drop", showlegend=False, hoverinfo="skip",
        ))

    apply_common_layout(fig, apex)
    st.plotly_chart(fig, use_container_width=True, key="mc_3d")

    members = _build_member_schedule(
        built, coords, x_rings,
        anchor_idx, edge_q_scalar, warp_q, weft_q,
    )

    with st.expander("Member schedule (BQ and analysis)", expanded=False):
        n_ring = sum(1 for m in members if m["member_type"] == "ring_beam")
        n_ring_seg = sum(1 for m in members
                         if m["member_type"] == "ring_beam_segment")
        n_spokes = sum(1 for m in members if m["member_type"] == "spoke")
        n_drops = sum(1 for m in members if m["member_type"] == "drop_member")
        n_cables = sum(1 for m in members
                       if m["member_type"] in ("cable", "cable_segment"))
        n_panels = sum(1 for m in members if m["member_type"] == "membrane")

        st.write(f"Total members recorded: {len(members)}")
        st.write(
            f"Counts: {n_ring} ring beam (consolidated), "
            f"{n_ring_seg} ring beam segments, "
            f"{n_spokes} spokes, "
            f"{n_drops} drop members, "
            f"{n_cables} edge cable members "
            f"(1 consolidated + segments), "
            f"{n_panels} membrane panels."
        )
        st.code(_format_member_table(members), language="text")

    with st.expander("Diagnostics", expanded=True):
        st.write("Mesh builder: engine/SDSe_mesh_builder.py "
                 "(SDSe_mesh_rings)")
        st.write(f"Number of cones: {number_of_cones}")
        st.write(f"Ring x positions (m): " +
                 ", ".join(f"{v:+.3f}" for v in x_rings))
        st.write(f"Ring z positions (m): " +
                 ", ".join(f"{v:.3f}" for v in ring_z_rings))
        st.write(f"Outer eave corners held: {anchors.shape[0]}")
        st.write(f"Perimeter nodes: {perimeter_loop.shape[0]}")
        st.write(f"Perimeter cable nodes (free): {len(intermediate_perimeter)}")
        st.write(f"Total mesh nodes: {pts.shape[0]}")
        st.write(f"Mesh edges: {len(edges)}")
        st.write(f"Mesh triangles: {len(tris)}")
        st.write(f"Held nodes (total): {len(fixed)}")
        st.write(f"DOF count: {dof_count}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Solve error: {solve_err}")
        else:
            st.write(f"Raw force imbalance (N): {residual_norm:.6e}")
            st.write("(Includes constraint reactions at held nodes. "
                     "Not a convergence failure.)")
        st.write(f"Warp q (N/m): {warp_q:.1f}")
        st.write(f"Weft q (N/m): {weft_q:.1f}")
        st.write(f"Edge cable q (N/m): {edge_q_scalar:.1f}")
        st.write(f"Cable / membrane q ratio: "
                 f"{edge_q_scalar / max(warp_q, 1.0):.4f}")
        st.write(f"Target edge length: {target_len:.4f}")
        st.write("Ring node counts: " +
                 ", ".join(str(c) for c in built["ring_node_counts"]))

    with st.expander("All nodes (full digitisation)", expanded=False):
        st.code(
            _format_all_nodes(
                pts, coords, anchor_idx,
                built["ring_indices"],
                built["centre_indices"],
                built["beam_top_indices"],
                intermediate_perimeter,
            ),
            language="text",
        )


# =============================================================================
# END OF ui/workshops/tester_multi_cone.py
# =============================================================================
