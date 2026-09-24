# =============================================================================
# SDSe - Standard Saddle Figure Builder
# =============================================================================
# Builds the 3D figure for the Standard Saddle variant.
# Called by viewers/results_viewer.py dispatcher.
#
# Membrane (updated 2026-09-22):
#   The membrane surface is form-found using the FDM kernel
#   (engine/form_finding.py), then drawn as a TRIANGULATED mesh
#   (go.Mesh3d). This matches industry practice (RFEM, Easy,
#   ixCube).
#
# Mesh size rule: engine.mesh_size_for_span() — one node per metre,
#   min 21, max 101, always odd.
#
# Attachment method: ws_ss_attachment_type — "kader" or "segmented".
#   In segmented mode, only the cable attachment points are fixed.
#   The beam-edge nodes between them are free.
#
# Side-cable stiffness: SIDE_CABLE_STIFFNESS_FACTOR = 12.0
#
# Updated 2026-09-23 (late):
#   - DIAGNOSTICS added. Below the 3D view, the viewer now records
#     and prints:
#       a) initial triangle area statistics (min, max, and the
#          indices of the smallest 10 triangles)
#       b) per-node displacement from initial to solved, sorted,
#          with the top 20 largest displacements and their (i,j)
#       c) the residual norm and n_free / n_fixed from solve_fdm
#
# Updated 2026-09-24 (morning):
#   - FIX 1 of 3. Mesh node placement along the beam (nx
#     direction) is now UNIFORM IN ARC LENGTH, not uniform in x.
#     The y-direction placement (ny) remains uniform between the
#     two beams.
#     Reason: with uniform-x placement, the parabola's steepest
#     sections (the beam ends) packed nodes too densely along
#     the arc. Two triangles at the corners collapsed to zero
#     area BEFORE solve_fdm ran. FDM then dragged those collapsed
#     nodes 3 m upward, producing the fold.
#     With arc-length-uniform placement, the corner triangles
#     should no longer be degenerate.
#   - Fixes 2 and 3 (attachment placement by arc length, and
#     SIDE_CABLE_STIFFNESS_FACTOR back to 6.0) are NOT applied
#     yet. One variable at a time. Measure after each.
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
from engine.form_finding import solve_fdm, mesh_size_for_span


SIDE_CABLE_STIFFNESS_FACTOR = 12.0


def _build_saddle_fdm(x, z_beam, y1, y2, span, apex,
                       membrane_pretension, cable_pretension,
                       attach_type, n_attach,
                       nx=21, ny=21):
    """
    Build the FDM mesh, solve for the membrane shape, and return
    both the solution and diagnostic information.

    Fix 1 (2026-09-24): mesh nodes along the beam (nx direction)
    are placed at equal arc-length intervals, not equal x
    intervals. The ny direction remains uniform between the
    two beams.
    """
    n_pts = len(x)

    # ---- Arc length of the beam curve
    s, total = arclength_parametrisation(x, z_beam)
    if total <= 0:
        # Fallback: uniform in x, as before
        s = np.linspace(0.0, 1.0, n_pts)
        total = 1.0

    # ---- Fix 1: nx nodes at uniform arc-length fractions
    # For each mesh index i, target arc length = (i/(nx-1)) * total
    # Interpolate to get bx and bz at that arc length.
    arc_targets = np.linspace(0.0, total, nx)
    bx_arr = np.interp(arc_targets, s, x)
    bz_arr = np.interp(arc_targets, s, z_beam)

    # For y1, y2, we also need the beam half-widths at those x points.
    # y1 and y2 are functions of x through the parabola:
    #   y = ±base_width * (1 - (2x/span)^2)
    base_width = apex * 0.5
    y1_arr = -base_width * (1.0 - (2.0 * bx_arr / span) ** 2)
    y2_arr = base_width * (1.0 - (2.0 * bx_arr / span) ** 2)

    # ---- Build the node grid
    node_xyz = np.zeros((nx, ny, 3))
    for i in range(nx):
        bx = float(bx_arr[i])
        bz = float(bz_arr[i])
        y_left = float(y1_arr[i])
        y_right = float(y2_arr[i])
        for j in range(ny):
            v = j / (ny - 1.0)
            y_pos = y_left * (1.0 - v) + y_right * v
            z_init = bz - 0.15 * (1.0 - (2.0 * v - 1.0) ** 2) * (apex * 0.5)
            node_xyz[i, j, 0] = bx
            node_xyz[i, j, 1] = y_pos
            node_xyz[i, j, 2] = z_init

    n_nodes = nx * ny
    points = np.zeros((n_nodes, 3))
    for i in range(nx):
        for j in range(ny):
            k = i * ny + j
            points[k] = node_xyz[i, j]

    points_initial = points.copy()

    edges = []
    for i in range(nx):
        for j in range(ny):
            k = i * ny + j
            if i + 1 < nx:
                edges.append((k, (i + 1) * ny + j))
            if j + 1 < ny:
                edges.append((k, i * ny + (j + 1)))

    if attach_type == "segmented":
        n_attach_int = max(2, int(n_attach))
        attach_i = []
        for k in range(n_attach_int):
            frac = k / (n_attach_int - 1.0)
            ii = int(round(frac * (nx - 1)))
            ii = max(0, min(nx - 1, ii))
            attach_i.append(ii)
        attach_i = sorted(set(attach_i))
        fixed_indices = []
        for i in attach_i:
            fixed_indices.append(i * ny + 0)
            fixed_indices.append(i * ny + (ny - 1))
    else:
        attach_i = []
        fixed_indices = []
        for i in range(nx):
            fixed_indices.append(i * ny + 0)
            fixed_indices.append(i * ny + (ny - 1))

    L_avg = 1.0
    if len(edges) > 0:
        total_len = 0.0
        for (a, b) in edges:
            total_len += float(np.linalg.norm(points[b] - points[a]))
        L_avg = total_len / max(1, len(edges))
    if L_avg < 1e-9:
        L_avg = 1.0

    T_mem = max(0.1, float(membrane_pretension))
    T_cab = max(0.1, float(cable_pretension))
    q_mem = T_mem * 1000.0 / L_avg

    q = np.full(len(edges), q_mem)
    for k, (a, b) in enumerate(edges):
        ia = a // ny
        ib = b // ny
        ja = a % ny
        jb = b % ny
        L_e = float(np.linalg.norm(points[b] - points[a]))
        if L_e < 1e-9:
            L_e = L_avg

        if (ia == 0 or ia == nx - 1) or (ib == 0 or ib == nx - 1):
            q[k] = T_cab * 1000.0 / L_e
        elif attach_type == "segmented":
            on_beam = (ja == 0 or ja == ny - 1) and (jb == 0 or jb == ny - 1)
            if on_beam:
                q[k] = SIDE_CABLE_STIFFNESS_FACTOR * T_cab * 1000.0 / L_e

    res = solve_fdm(points, edges, fixed_indices, q)
    coords = res["coordinates"]

    # ---- Diagnostics: initial triangle areas -------------------------------
    initial_areas = []
    initial_area_tri = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            b = (i + 1) * ny + j
            c = i * ny + (j + 1)
            d = (i + 1) * ny + (j + 1)
            for tri in ((a, b, c), (b, d, c)):
                p0 = points_initial[tri[0]]
                p1 = points_initial[tri[1]]
                p2 = points_initial[tri[2]]
                area = 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0)))
                initial_areas.append(area)
                initial_area_tri.append(tri)
    initial_areas = np.array(initial_areas)

    disp = np.linalg.norm(coords - points_initial, axis=1)

    order = np.argsort(disp)[::-1]
    top_n = 20
    top_disp = []
    for rank, k in enumerate(order[:top_n]):
        i_idx = int(k // ny)
        j_idx = int(k % ny)
        top_disp.append({
            "rank": rank + 1,
            "node": int(k),
            "i": i_idx,
            "j": j_idx,
            "disp": float(disp[k]),
            "z_initial": float(points_initial[k, 2]),
            "z_solved": float(coords[k, 2]),
        })

    order_a = np.argsort(initial_areas)
    top_small = []
    for rank, idx in enumerate(order_a[:10]):
        tri = initial_area_tri[idx]
        top_small.append({
            "rank": rank + 1,
            "nodes": (int(tri[0]), int(tri[1]), int(tri[2])),
            "area": float(initial_areas[idx]),
        })

    diagnostics = {
        "initial_area_min": float(initial_areas.min()),
        "initial_area_max": float(initial_areas.max()),
        "initial_area_mean": float(initial_areas.mean()),
        "residual_norm": float(res["residual_norm"]),
        "n_free": int(res["n_free"]),
        "n_fixed": int(res["n_fixed"]),
        "top_displacements": top_disp,
        "smallest_initial_triangles": top_small,
        "edge_count": len(edges),
        "node_count": n_nodes,
    }

    X = np.zeros((nx, ny))
    Y = np.zeros((nx, ny))
    Z = np.zeros((nx, ny))
    for i in range(nx):
        for j in range(ny):
            k = i * ny + j
            X[i, j] = coords[k, 0]
            Y[i, j] = coords[k, 1]
            Z[i, j] = coords[k, 2]

    edge_south = np.zeros((ny, 3))
    edge_north = np.zeros((ny, 3))
    for j in range(ny):
        edge_south[j] = coords[0 * ny + j]
        edge_north[j] = coords[(nx - 1) * ny + j]

    return X, Y, Z, edge_south, edge_north, attach_i, diagnostics


def _grid_to_triangles(X, Y, Z):
    """Convert a rectangular grid of nodes (nx x ny) into a triangulated mesh."""
    nx, ny = X.shape
    node_x = X.reshape(-1)
    node_y = Y.reshape(-1)
    node_z = Z.reshape(-1)

    tri_i = []
    tri_j = []
    tri_k = []

    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            b = (i + 1) * ny + j
            c = i * ny + (j + 1)
            d = (i + 1) * ny + (j + 1)

            tri_i.append(a)
            tri_j.append(b)
            tri_k.append(c)

            tri_i.append(b)
            tri_j.append(d)
            tri_k.append(c)

    return node_x, node_y, node_z, tri_i, tri_j, tri_k


def _add_kader_track(fig, x, z_beam, y_beam, show_legend=False):
    fig.add_trace(go.Scatter3d(
        x=x, y=y_beam, z=z_beam,
        mode="lines",
        line=dict(color="#f39c12", width=2),
        showlegend=show_legend,
        name="Kader track" if show_legend else None,
        hoverinfo="skip",
    ))


def build_standard_saddle():
    """Standard Saddle: two curved beams, membrane, tie-downs, anchors."""
    span = float(st.session_state.get("ws_ss_span", 10.0))
    apex = float(st.session_state.get("ws_ss_apex", 15.0))
    rise = float(st.session_state.get("ws_ss_rise", 6.2))
    curve_type = st.session_state.get("ws_ss_curve_type", "parabolic")
    n_intervals = int(st.session_state.get("ws_ss_tiedown_intervals", 2))
    uplift = float(st.session_state.get("ws_ss_uplift_angle", 45))
    spread = float(st.session_state.get("ws_ss_spread_angle", 30))
    membrane_pre = float(st.session_state.get("ws_ss_membrane_pretension", 2.0))
    cable_pre = float(st.session_state.get("ws_ss_cable_pretension", 5.0))
    attach_type = str(st.session_state.get("ws_ss_attachment_type", "kader"))
    edge_cables_on = bool(st.session_state.get("ws_ss_edge_cables", True))
    n_attach = int(st.session_state.get("ws_ss_cable_attachment_count", 6))

    if span <= 0 or apex <= 0 or rise <= 0:
        fig = go.Figure()
        fig.add_annotation(text="Invalid geometry - check inputs",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#f39c12", size=16))
        return apply_common_layout(fig, 10.0)

    n_mesh = mesh_size_for_span(span)
    nx = n_mesh
    ny = n_mesh

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

    X_surf, Y_surf, Z_surf, edge_south, edge_north, attach_i_list, diag = _build_saddle_fdm(
        x, z_beam, y1, y2, span, apex,
        membrane_pre, cable_pre,
        attach_type, n_attach,
        nx=nx, ny=ny,
    )

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

    if attach_type == "segmented" and len(attach_i_list) > 0:
        dots_lx = X_surf[attach_i_list, 0].tolist()
        dots_ly = Y_surf[attach_i_list, 0].tolist()
        dots_lz = Z_surf[attach_i_list, 0].tolist()
        fig.add_trace(go.Scatter3d(
            x=dots_lx, y=dots_ly, z=dots_lz,
            mode="markers",
            marker=dict(color="#f39c12", size=7, symbol="circle"),
            showlegend=True,
            name="Cable attach points",
            hoverinfo="skip",
        ))

        dots_rx = X_surf[attach_i_list, -1].tolist()
        dots_ry = Y_surf[attach_i_list, -1].tolist()
        dots_rz = Z_surf[attach_i_list, -1].tolist()
        fig.add_trace(go.Scatter3d(
            x=dots_rx, y=dots_ry, z=dots_rz,
            mode="markers",
            marker=dict(color="#f39c12", size=7, symbol="circle"),
            showlegend=False,
            hoverinfo="skip",
        ))

        fig.add_trace(go.Scatter3d(
            x=X_surf[:, 0], y=Y_surf[:, 0], z=Z_surf[:, 0],
            mode="lines",
            line=dict(color="#f1c40f", width=4),
            showlegend=True,
            name="Side cables",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=X_surf[:, -1], y=Y_surf[:, -1], z=Z_surf[:, -1],
            mode="lines",
            line=dict(color="#f1c40f", width=4),
            showlegend=False,
            hoverinfo="skip",
        ))
    else:
        _add_kader_track(fig, x, z_beam, y1, show_legend=True)
        _add_kader_track(fig, x, z_beam, y2, show_legend=False)

    if edge_cables_on:
        fig.add_trace(go.Scatter3d(
            x=edge_south[:, 0], y=edge_south[:, 1], z=edge_south[:, 2],
            mode="lines",
            line=dict(color="#f1c40f", width=5),
            showlegend=True,
            name="Edge cables",
        ))
        fig.add_trace(go.Scatter3d(
            x=edge_north[:, 0], y=edge_north[:, 1], z=edge_north[:, 2],
            mode="lines",
            line=dict(color="#f1c40f", width=5),
            showlegend=False,
        ))

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

            horizontal = drop / math.tan(math.radians(uplift)) if uplift > 0 else drop

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

    # ---- Diagnostics panel -------------------------------------------------
    with st.expander("FDM diagnostics (temporary)", expanded=True):
        st.markdown(
            "**Initial mesh triangle area** — before solve_fdm:"
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Min area", "%.6e" % diag["initial_area_min"])
        c2.metric("Mean area", "%.6e" % diag["initial_area_mean"])
        c3.metric("Max area", "%.6f" % diag["initial_area_max"])

        st.markdown(
            "**FDM solver residual** — after solve_fdm:"
        )
        d1, d2, d3 = st.columns(3)
        d1.metric("Residual", "%.4e" % diag["residual_norm"])
        d2.metric("Free nodes", diag["n_free"])
        d3.metric("Fixed nodes", diag["n_fixed"])

        st.markdown(
            "**Top 20 largest node displacements** (initial to solved):"
        )
        rows = []
        for entry in diag["top_displacements"]:
            rows.append(
                "rank " + str(entry["rank"]) +
                "  node " + str(entry["node"]) +
                "  (i=" + str(entry["i"]) + ", j=" + str(entry["j"]) + ")" +
                "  disp=" + ("%.4f" % entry["disp"]) +
                "  z_init=" + ("%.4f" % entry["z_initial"]) +
                "  z_solved=" + ("%.4f" % entry["z_solved"])
            )
        st.code("\n".join(rows), language="text")

        st.markdown(
            "**Smallest 10 initial triangles** (before solve):"
        )
        rows2 = []
        for entry in diag["smallest_initial_triangles"]:
            rows2.append(
                "rank " + str(entry["rank"]) +
                "  nodes " + str(entry["nodes"]) +
                "  area=" + ("%.6e" % entry["area"])
            )
        st.code("\n".join(rows2), language="text")

    return fig





