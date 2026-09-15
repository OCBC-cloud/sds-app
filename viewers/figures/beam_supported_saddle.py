# =============================================================================
# SDSe - Beam Supported Saddle Figure Builder
# =============================================================================
# Builds the 3D figure for the Beam Supported Saddle variant.
# Called by viewers/results_viewer.py dispatcher.
#
# Difference from Cable Supported Saddle:
#   - Tie-down cables replaced by solid secondary beams (same geometry)
#   - Purlins added as horizontal cross-members at 2.5 m intervals
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


def _compute_purlin_offsets(span):
    """Purlins every 2.5 m from centre, symmetric."""
    interval = 2.5
    half_span = span / 2.0
    offsets = [0.0]
    k = 1
    while True:
        o = k * interval
        if o > half_span - interval:
            break
        offsets.append(o)
        offsets.append(-o)
        k += 1
    return sorted(offsets)


def _compute_secondary_positions(per_beam_count):
    """Arc-length fractions for secondary beam positions."""
    if per_beam_count < 2:
        return [0.5]
    if per_beam_count == 2:
        return [0.175, 0.825]

    n_middle = per_beam_count - 2
    m_start = 0.175
    m_end = 0.825
    m_span = m_end - m_start
    step = m_span / (n_middle + 1)

    fractions = [m_start]
    for i in range(1, n_middle + 1):
        fractions.append(m_start + i * step)
    fractions.append(m_end)
    return fractions


def build_beam_supported_saddle():
    """Beam Supported Saddle: beams, membrane, purlins, secondary beams."""
    span = float(st.session_state.get("ws_bs_span", 10.0))
    apex = float(st.session_state.get("ws_bs_apex", 15.0))
    rise = float(st.session_state.get("ws_bs_rise", 6.2))
    curve_type = st.session_state.get("ws_bs_curve_type", "parabolic")
    per_beam = int(st.session_state.get("ws_bs_secondary_count", 2))
    uplift = float(st.session_state.get("ws_bs_uplift_angle", 45))
    spread = float(st.session_state.get("ws_bs_spread_angle", 30))

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

    # ---- Beams (red)
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

    # ---- Membrane surface (blue gradient)
    n_u = 30
    n_v = 30
    X_surf = np.zeros((n_u, n_v))
    Y_surf = np.zeros((n_u, n_v))
    Z_surf = np.zeros((n_u, n_v))

    for i, xi in enumerate(np.linspace(-span / 2.0, span / 2.0, n_u)):
        idx = int((xi + span / 2.0) / span * (n_pts - 1))
        idx = max(0, min(n_pts - 1, idx))
        bx = x[idx]
        bz = z_beam[idx]
        y_left = y1[idx]
        y_right = y2[idx]

        for j, v in enumerate(np.linspace(0.0, 1.0, n_v)):
            y_pos = y_left * (1 - v) + y_right * v
            sag = 0.15 * (1 - (2 * v - 1) ** 2) * base_width
            z_pos = bz - sag
            X_surf[i, j] = bx
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.55,
        showscale=False,
        name="Membrane",
    ))










    # ---- Purlins (orange horizontal cross-members)
    purlin_offsets = _compute_purlin_offsets(span)
    for offset in purlin_offsets:
        x_p = offset
        idx = int((x_p + span / 2.0) / span * (n_pts - 1))
        idx = max(0, min(n_pts - 1, idx))
        fig.add_trace(go.Scatter3d(
            x=[x_p, x_p],
            y=[y1[idx], y2[idx]],
            z=[z_beam[idx], z_beam[idx]],
            mode="lines",
            line=dict(color="#e67e22", width=5),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Legend dummy for purlins
    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="lines",
        line=dict(color="#e67e22", width=5),
        name="Purlins",
    ))

    # ---- Secondary beams (steel, solid) at cable positions
    per_beam_fractions = _compute_secondary_positions(per_beam)

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
                line=dict(color="#95a5a6", width=6),
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

    # Legend dummy for secondary beams
    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="lines",
        line=dict(color="#95a5a6", width=6),
        name="Secondary beams",
    ))

    # ---- Ground supports
    fig.add_trace(go.Scatter3d(
        x=[-span / 2.0, span / 2.0],
        y=[0, 0],
        z=[0, 0],
        mode="markers",
        marker=dict(color="#2ecc71", size=10, symbol="diamond"),
        name="Ground supports",
    ))

    return apply_common_layout(fig, rise)







