# =============================================================================
# SDSe - Standard Saddle Figure Builder
# =============================================================================
# Builds the 3D figure for the Standard Saddle variant.
# Called by viewers/results_viewer.py dispatcher.
#
# Tie-down geometry (updated 2026-09-14):
#   Attach points positioned by ARC-LENGTH fraction along each beam.
#     4 cables total -> positions 0.175, 0.825 on each beam
#     8 cables total -> positions 0.175, 0.225, 0.775, 0.825 on each beam
#
# Membrane (updated 2026-09-22):
#   The membrane surface is form-found using the FDM kernel
#   (engine/form_finding.py). The two long edges follow the beams.
#
# Attachment method (updated 2026-09-22):
#   ws_ss_attachment_type controls how the fabric meets the beams:
#     "kader"      - continuous track line along each beam
#     "segmented"  - discrete attachment dots at panel boundaries,
#                    plus seam lines across the membrane.
#   The number of segments is derived by the viewer from the beam
#   arc length and ws_ss_max_panel_length.
#
# Edge cables (updated 2026-09-22):
#   ws_ss_edge_cables is an independent toggle. When True, thick
#   yellow cables are drawn along the two short ends of the
#   membrane, following the FDM boundary. Corner dots mark where
#   the cables meet the beams.
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


# =============================================================================
# FDM MEMBRANE MESH
# =============================================================================

def _build_saddle_fdm(x, z_beam, y1, y2, span, apex,
                       membrane_pretension, cable_pretension,
                       nx=20, ny=20):
    """Build the FDM mesh and solve for the membrane shape."""
    n_pts = len(x)

    node_xyz = np.zeros((nx, ny, 3))
    for i in range(nx):
        xi = -span / 2.0 + span * i / (nx - 1.0)
        idx = int((xi + span / 2.0) / span * (n_pts - 1))
        idx = max(0, min(n_pts - 1, idx))
        bx = x[idx]
        bz = z_beam[idx]
        y_left = y1[idx]
        y_right = y2[idx]
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

    edges = []
    for i in range(nx):
        for j in range(ny):
            k = i * ny + j
            if i + 1 < nx:
                edges.append((k, (i + 1) * ny + j))
            if j + 1 < ny:
                edges.append((k, i * ny + (j + 1)))

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
        if (ia == 0 or ia == nx - 1) or (ib == 0 or ib == nx - 1):
            L_e = float(np.linalg.norm(points[b] - points[a]))
            if L_e < 1e-9:
                L_e = L_avg
            q[k] = T_cab * 1000.0 / L_e

    res = solve_fdm(points, edges, fixed_indices, q)
    coords = res["coordinates"]

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

    return X, Y, Z, edge_south, edge_north


# =============================================================================
# ATTACHMENT MODE VISUAL
# =============================================================================

def _add_kader_track(fig, x, z_beam, y_beam, show_legend=False):
    """Continuous track line along the beam."""
    fig.add_trace(go.Scatter3d(
        x=x, y=y_beam, z=z_beam,
        mode="lines",
        line=dict(color="#f39c12", width=2),
        showlegend=show_legend,
        name="Kader track" if show_legend else None,
        hoverinfo="skip",
    ))


def _add_segmented_dots_and_seams(fig, x, z_beam, y_beam,
                                   s, total, n_seg,
                                   X_surf, Y_surf, Z_surf,
                                   is_left_beam,
                                   show_legend_dots=False,
                                   show_legend_seams=False):
    """
    Segmented mode visual for one beam:
      - attachment dots at n_seg + 1 evenly spaced positions
      - seam lines across the membrane at the interior positions
    """
    n_boundaries = n_seg + 1
    fractions = [i / (n_boundaries - 1.0) for i in range(n_boundaries)]

    # Attachment dots along the beam
    bx, by, bz = [], [], []
    for frac in fractions:
        idx = find_index_at_arclength_fraction(s, total, frac)
        bx.append(x[idx])
        by.append(y_beam[idx])
        bz.append(z_beam[idx])

    fig.add_trace(go.Scatter3d(
        x=bx, y=by, z=bz,
        mode="markers",
        marker=dict(color="#f39c12", size=5, symbol="circle"),
        showlegend=show_legend_dots,
        name="Segment attachment" if show_legend_dots else None,
        hoverinfo="skip",
    ))

    # Seam lines across the membrane (interior fractions only)
    n_u = X_surf.shape[0]
    n_v = X_surf.shape[1]
    for k in range(1, n_boundaries - 1):
        frac = fractions[k]
        idx_u = int(frac * (n_u - 1))
        idx_u = max(0, min(n_u - 1, idx_u))
        fig.add_trace(go.Scatter3d(
            x=X_surf[idx_u, :],
            y=Y_surf[idx_u, :],
            z=Z_surf[idx_u, :],
            mode="lines",
            line=dict(color="#f39c12", width=1, dash="dot"),
            showlegend=(show_legend_seams and k == 1),
            name="Seam" if (show_legend_seams and k == 1) else None,
            hoverinfo="skip",
        ))


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

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
    max_panel = float(st.session_state.get("ws_ss_max_panel_length", 2.5))

    if span <= 0 or apex <= 0 or rise <= 0:
        fig = go.Figure()
        fig.add_annotation(text="Invalid geometry - check inputs",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#f39c12", size=16))
        return apply_common_layout(fig, 10.0)

    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)

    s, total = arclength_parametrisation(x, z_beam)

    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    fig = go.Figure()

    # ---- Beams
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

    # ---- FDM membrane
    X_surf, Y_surf, Z_surf, edge_south, edge_north = _build_saddle_fdm(
        x, z_beam, y1, y2, span, apex,
        membrane_pre, cable_pre,
        nx=20, ny=20,
    )

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.55,
        showscale=False,
        name="Membrane",
    ))

    # ---- Attachment visual
    if attach_type == "segmented":
        arc_len = float(total) if total > 1e-9 else span
        n_seg = max(2, int(math.ceil(arc_len / max(0.5, max_panel))))
        _add_segmented_dots_and_seams(
            fig, x, z_beam, y1, s, total, n_seg,
            X_surf, Y_surf, Z_surf,
            is_left_beam=True,
            show_legend_dots=True,
            show_legend_seams=True,
        )
        _add_segmented_dots_and_seams(
            fig, x, z_beam, y2, s, total, n_seg,
            X_surf, Y_surf, Z_surf,
            is_left_beam=False,
            show_legend_dots=False,
            show_legend_seams=False,
        )
    else:
        _add_kader_track(fig, x, z_beam, y1, show_legend=True)
        _add_kader_track(fig, x, z_beam, y2, show_legend=False)

    # ---- Edge cables (short ends), optional
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

        corner_xs = [-span / 2.0, span / 2.0, -span / 2.0, span / 2.0]
        corner_ys = [
            -base_width * (1.0 - (2.0 * (-span / 2.0) / span) ** 2),
            base_width * (1.0 - (2.0 * (span / 2.0) / span) ** 2),
            base_width * (1.0 - (2.0 * (-span / 2.0) / span) ** 2),
            -base_width * (1.0 - (2.0 * (span / 2.0) / span) ** 2),
        ]
        bz_s = float(beam_curve(np.array([-span / 2.0]), span, rise, curve_type)[0])
        bz_n = float(beam_curve(np.array([span / 2.0]), span, rise, curve_type)[0])
        corner_zs = [bz_s, bz_n, bz_s, bz_n]

        fig.add_trace(go.Scatter3d(
            x=corner_xs, y=corner_ys, z=corner_zs,
            mode="markers",
            marker=dict(color="#f1c40f", size=6, symbol="circle"),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ---- Tie-down cables
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

    return apply_common_layout(fig, rise)





