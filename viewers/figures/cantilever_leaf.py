# =============================================================================
# SDSe - Cantilever Leaf Figure Builder
# =============================================================================
# Builds the 3D figure for the Cantilever Leaf variant.
# Called by viewers/results_viewer.py dispatcher.
#
# Strut joint height fixed at 75% of column height (agreed 2026-09-14).
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go

import streamlit as st

from viewers.figures._shared import apply_common_layout


def build_cantilever_leaf():
    """Cantilever Leaf: column, spine, ribs, perimeter cables, membrane, strut."""
    col_h = float(st.session_state.get("ws_sl_column_height", 10.0))
    outreach = float(st.session_state.get("ws_sl_outreach", 10.0))
    ribs_per_side = int(st.session_state.get("ws_sl_ribs_per_side", 7))
    tilt_deg = float(st.session_state.get("ws_sl_rib_tilt", 20))
    arc_r = float(st.session_state.get("ws_sl_arc_radius", 5.0))
    strut_joint = float(st.session_state.get("ws_sl_strut_joint_height", col_h * 0.75))

    if col_h <= 0 or outreach <= 0:
        fig = go.Figure()
        fig.add_annotation(text="Invalid geometry - check inputs",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#f39c12", size=16))
        return apply_common_layout(fig, 10.0)

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[0, col_h],
        mode="lines",
        line=dict(color="#2ecc71", width=10),
        name="Column",
    ))
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode="markers",
        marker=dict(color="#2ecc71", size=10, symbol="square"),
        name="Baseplate",
    ))

    n_beam = 80
    t_beam = np.linspace(0, 1, n_beam)
    beam_x = outreach * t_beam
    beam_z = col_h + arc_r * np.sin(t_beam * np.pi * 0.6) * 0.7
    beam_y = np.zeros_like(t_beam)

    fig.add_trace(go.Scatter3d(
        x=beam_x, y=beam_y, z=beam_z,
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        name="Main beam",
    ))

    def leaf_half_width(t):
        return outreach * 0.42 * (np.sin(np.pi * t) ** 0.7)

    def rib_tilt_at(t):
        return math.radians(tilt_deg) * (math.sin(math.pi * t) ** 0.7)

    rib_ts = np.linspace(0.08, 0.92, ribs_per_side)
    rib_tip_left = []
    rib_tip_right = []

    for t in rib_ts:
        idx = int(t * (n_beam - 1))
        a_x = beam_x[idx]
        a_z = beam_z[idx]
        half_w = leaf_half_width(t)
        tilt = rib_tilt_at(t)
        tip_z = a_z + half_w * math.tan(tilt)

        fig.add_trace(go.Scatter3d(
            x=[a_x, a_x], y=[0, -half_w], z=[a_z, tip_z],
            mode="lines",
            line=dict(color="#3498db", width=4),
            showlegend=False,
            hoverinfo="skip",
        ))
        rib_tip_left.append((a_x, -half_w, tip_z))

        fig.add_trace(go.Scatter3d(
            x=[a_x, a_x], y=[0, +half_w], z=[a_z, tip_z],
            mode="lines",
            line=dict(color="#3498db", width=4),
            showlegend=False,
            hoverinfo="skip",
        ))
        rib_tip_right.append((a_x, +half_w, tip_z))

    if len(rib_tip_left) > 1:
        fig.add_trace(go.Scatter3d(
            x=[p[0] for p in rib_tip_left],
            y=[p[1] for p in rib_tip_left],
            z=[p[2] for p in rib_tip_left],
            mode="lines",
            line=dict(color="#FFD93D", width=3, dash="dash"),
            name="Perimeter L",
        ))
        fig.add_trace(go.Scatter3d(
            x=[p[0] for p in rib_tip_right],
            y=[p[1] for p in rib_tip_right],
            z=[p[2] for p in rib_tip_right],
            mode="lines",
            line=dict(color="#FFD93D", width=3, dash="dash"),
            name="Perimeter R",
        ))

    n_u = 30
    n_v = 30
    X_surf = np.zeros((n_u, n_v))
    Y_surf = np.zeros((n_u, n_v))
    Z_surf = np.zeros((n_u, n_v))

    for i, t in enumerate(np.linspace(0.02, 0.98, n_u)):
        idx = int(t * (n_beam - 1))
        b_x = beam_x[idx]
        b_z = beam_z[idx]
        half_w = leaf_half_width(t)
        tilt = rib_tilt_at(t)
        tip_z_at_t = b_z + half_w * math.tan(tilt)

        for j, v in enumerate(np.linspace(-1, 1, n_v)):
            X_surf[i, j] = b_x
            Y_surf[i, j] = v * half_w
            z_edge = b_z * (1 - abs(v)) + tip_z_at_t * abs(v)
            sag_amount = 0.15 * half_w * (1 - (2 * abs(v) - 1) ** 2)
            Z_surf[i, j] = z_edge - sag_amount

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.55,
        showscale=False,
        name="Membrane",
    ))

    idx_third = int(0.33 * (n_beam - 1))
    px = beam_x[idx_third]
    pz = beam_z[idx_third]

    t_s = np.linspace(0, 1, 25)
    sx = px * (1 - t_s)
    sz_base = pz + (strut_joint - pz) * t_s
    sz = sz_base + 0.1 * np.sin(np.pi * t_s) * (pz - strut_joint) * 0.5

    fig.add_trace(go.Scatter3d(
        x=sx, y=np.zeros_like(sx), z=sz,
        mode="lines",
        line=dict(color="#e67e22", width=4),
        name="Curved strut",
    ))

    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[strut_joint],
        mode="markers",
        marker=dict(color="#e67e22", size=6, symbol="diamond"),
        name="Strut joint",
    ))

    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[col_h],
        mode="markers",
        marker=dict(color="#FFD93D", size=8, symbol="diamond"),
        name="Column node",
    ))
    fig.add_trace(go.Scatter3d(
        x=[outreach], y=[0], z=[beam_z[-1]],
        mode="markers",
        marker=dict(color="#FFD93D", size=8, symbol="diamond"),
        name="Leaf tip",
    ))

    return apply_common_layout(fig, col_h + arc_r)







