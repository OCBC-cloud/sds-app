# =============================================================================
# SDSe Fluid Design Studio - Results Viewer
# =============================================================================
# Production 3D viewer for the Results page.
#
# Takes inputs as parameters - no sidebar controls.
# Returns a Plotly figure ready for st.plotly_chart().
#
# Design decisions (agreed 2026-09-13):
#   - One viewer function per structure type
#   - Reads workshop inputs from session state
#   - Correct strut joint height for the leaf (60% of column)
#   - Standard saddle includes tie-down cables and anchors
#   - Leaf includes baseplate, anchors, and correct strut geometry
#   - Member colouring by utilisation added later (Phase C)
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go

import streamlit as st


# =============================================================================
# SHARED HELPERS
# =============================================================================

def _apply_common_layout(fig, rise_ref, extra_notes=None):
    """Apply shared Plotly layout to any figure."""
    z_max = max(10, rise_ref * 1.5)
    title_text = ""
    if extra_notes:
        title_text = extra_notes

    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            xaxis=dict(color="#b0c4de", gridcolor="#1a2a3a"),
            yaxis=dict(color="#b0c4de", gridcolor="#1a2a3a"),
            zaxis=dict(color="#b0c4de", gridcolor="#1a2a3a", range=[-2, z_max]),
            bgcolor="#0a0e17",
            aspectmode="data",
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
        ),
        paper_bgcolor="#0a0e17",
        margin=dict(l=0, r=0, b=0, t=0),
        height=600,
        legend=dict(
            font=dict(color="#ffffff", size=8),
            orientation="h",
            yanchor="bottom",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(10,14,23,0.7)",
            bordercolor="#2a3a4f",
            borderwidth=1,
        ),
    )
    return fig


def _beam_curve(x, span, rise, curve_type):
    """Return z values along the beam for the given curve type."""
    if span <= 0:
        return np.zeros_like(x)
    x_norm = 2.0 * x / span
    if curve_type == "parabolic":
        return rise * (1.0 - x_norm ** 2)
    elif curve_type == "circular":
        R = (span ** 2 + 4 * rise ** 2) / (8 * rise) if rise > 0 else span / 2
        if R > 0:
            return rise - (R - np.sqrt(np.maximum(0, R ** 2 - x ** 2)))
        return rise * (1.0 - x_norm ** 2)
    elif curve_type == "catenary":
        if rise <= 0:
            return rise * (1.0 - x_norm ** 2)
        try:
            a = span / (2.0 * math.asinh(rise / (span / 2.0))) if rise > 0 else 1.0
            if a > 0:
                return rise * (1.0 - (np.cosh(x / a) - 1.0) / (np.cosh(span / (2.0 * a)) - 1.0))
            return rise * (1.0 - x_norm ** 2)
        except Exception:
            return rise * (1.0 - x_norm ** 2)
    return rise * (1.0 - x_norm ** 2)


def _beam_arc_length(span, rise, curve_type):
    """Approximate arc length of one beam."""
    if span <= 0:
        return 0.0
    ratio = rise / span
    if curve_type == "parabolic":
        return span * (1.0 + (8.0 / 3.0) * ratio * ratio)
    elif curve_type == "circular":
        if rise <= 0:
            return span
        R = (span ** 2 + 4 * rise ** 2) / (8 * rise)
        if R <= span / 2:
            return span
        half_angle = math.asin(span / (2 * R))
        return 2 * R * half_angle
    elif curve_type == "catenary":
        return span * (1.0 + 2.5 * ratio * ratio)
    return span


# =============================================================================
# STANDARD SADDLE FIGURE
# =============================================================================

def generate_standard_saddle_figure():
    """
    Render the Standard Saddle for the Results page.
    Reads inputs from st.session_state (workshop inputs).
    Includes: two curved beams, membrane, tie-down cables, ground anchors.
    """
    span = float(st.session_state.get("ws_ss_span", 20.0))
    apex = float(st.session_state.get("ws_ss_apex", 12.0))
    rise = float(st.session_state.get("ws_ss_rise", 2.5))
    curve_type = st.session_state.get("ws_ss_curve_type", "parabolic")
    n_intervals = int(st.session_state.get("ws_ss_tiedown_intervals", 3))
    uplift = float(st.session_state.get("ws_ss_uplift_angle", 45))
    spread = float(st.session_state.get("ws_ss_spread_angle", 30))

    if span <= 0 or apex <= 0 or rise <= 0:
        fig = go.Figure()
        fig.add_annotation(text="Invalid geometry - check inputs",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#f39c12", size=16))
        return _apply_common_layout(fig, 10.0)

    n_pts = 60
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = _beam_curve(x, span, rise, curve_type)

    # Two beams separated by width, converging at ends
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

    # ---- Membrane surface (sags below the beams)
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

    # ---- Tie-down cables and anchors
    # One tie-down at each interval, on each beam
    for k in range(n_intervals):
        # Position along beam (interior spacing)
        t = (k + 1) / (n_intervals + 1)
        x_tie = -span / 2.0 + t * span
        idx = int(t * (n_pts - 1))
        idx = max(0, min(n_pts - 1, idx))

        beam_z = z_beam[idx]

        # Each tie-down anchors on both sides of the structure
        for side, y_beam in ((-1, y1[idx]), (+1, y2[idx])):
            # Anchor offset from beam based on angles
            drop = beam_z
            if drop <= 0:
                drop = 0.5
            horizontal = drop / math.tan(math.radians(uplift)) if uplift > 0 else drop
            lateral = horizontal * math.tan(math.radians(spread))

            anchor_y = y_beam + side * lateral
            anchor_x = x_tie

            # Cable from beam node to anchor
            fig.add_trace(go.Scatter3d(
                x=[x_tie, anchor_x],
                y=[y_beam, anchor_y],
                z=[beam_z, 0],
                mode="lines",
                line=dict(color="#f1c40f", width=2, dash="dot"),
                showlegend=False,
                hoverinfo="skip",
            ))

            # Anchor marker
            fig.add_trace(go.Scatter3d(
                x=[anchor_x], y=[anchor_y], z=[0],
                mode="markers",
                marker=dict(color="#f1c40f", size=5, symbol="square"),
                showlegend=False,
                hoverinfo="skip",
            ))

    # ---- Ground support points (beam ends)
    fig.add_trace(go.Scatter3d(
        x=[-span / 2.0, span / 2.0],
        y=[0, 0],
        z=[0, 0],
        mode="markers",
        marker=dict(color="#2ecc71", size=10, symbol="diamond"),
        name="Ground supports",
    ))

    # Legend dummy entries for tie-downs
    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="lines",
        line=dict(color="#f1c40f", width=2, dash="dot"),
        name="Tie-down cables",
    ))

    return _apply_common_layout(fig, rise)


# =============================================================================
# CANTILEVER LEAF FIGURE
# =============================================================================

def generate_cantilever_leaf_figure():
    """
    Render the Cantilever Leaf for the Results page.
    Reads inputs from st.session_state (workshop inputs).
    Includes: column, main beam, radial ribs, perimeter cables,
    membrane, curved strut (at correct joint height), baseplate.
    """
    col_h = float(st.session_state.get("ws_sl_column_height", 10.0))
    outreach = float(st.session_state.get("ws_sl_outreach", 10.0))
    ribs_per_side = int(st.session_state.get("ws_sl_ribs_per_side", 7))
    tilt_deg = float(st.session_state.get("ws_sl_rib_tilt", 20))
    arc_r = float(st.session_state.get("ws_sl_arc_radius", 5.0))
    curve_type = st.session_state.get("ws_sl_curve_type", "parabolic")
    strut_joint = float(st.session_state.get("ws_sl_strut_joint_height", col_h * 0.6))

    if col_h <= 0 or outreach <= 0:
        fig = go.Figure()
        fig.add_annotation(text="Invalid geometry - check inputs",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#f39c12", size=16))
        return _apply_common_layout(fig, 10.0)

    fig = go.Figure()

    # ---- Column
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[0, col_h],
        mode="lines",
        line=dict(color="#2ecc71", width=10),
        name="Column",
    ))

    # ---- Baseplate
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode="markers",
        marker=dict(color="#2ecc71", size=10, symbol="square"),
        name="Baseplate",
    ))

    # ---- Main beam (curved spine from column top outward)
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

    # ---- Leaf envelope
    def leaf_half_width(t):
        return outreach * 0.42 * (np.sin(np.pi * t) ** 0.7)

    def rib_tilt_at(t):
        return math.radians(tilt_deg) * (math.sin(math.pi * t) ** 0.7)

    # ---- Ribs
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

        # Left rib
        fig.add_trace(go.Scatter3d(
            x=[a_x, a_x], y=[0, -half_w], z=[a_z, tip_z],
            mode="lines",
            line=dict(color="#3498db", width=4),
            showlegend=False,
            hoverinfo="skip",
        ))
        rib_tip_left.append((a_x, -half_w, tip_z))

        # Right rib
        fig.add_trace(go.Scatter3d(
            x=[a_x, a_x], y=[0, +half_w], z=[a_z, tip_z],
            mode="lines",
            line=dict(color="#3498db", width=4),
            showlegend=False,
            hoverinfo="skip",
        ))
        rib_tip_right.append((a_x, +half_w, tip_z))

    # ---- Perimeter cables (segments between rib tips)
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

    # ---- Membrane
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

    # ---- Curved strut (from 1/3 of main beam to column at strut_joint height)
    idx_third = int(0.33 * (n_beam - 1))
    px = beam_x[idx_third]
    pz = beam_z[idx_third]

    # Curve path from strut start to column joint
    t_s = np.linspace(0, 1, 25)
    sx = px * (1 - t_s)
    sz_base = pz + (strut_joint - pz) * t_s
    # Small arch to give it a curved appearance
    sz = sz_base + 0.1 * math.sin(math.pi * t_s) * (pz - strut_joint) * 0.5

    fig.add_trace(go.Scatter3d(
        x=sx, y=np.zeros_like(sx), z=sz,
        mode="lines",
        line=dict(color="#e67e22", width=4),
        name="Curved strut",
    ))

    # ---- Column joint node (where strut meets column)
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[strut_joint],
        mode="markers",
        marker=dict(color="#e67e22", size=6, symbol="diamond"),
        name="Strut joint",
    ))

    # ---- Column node and leaf tip markers
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

    return _apply_common_layout(fig, col_h + arc_r)


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def generate_results_figure(structure_key, variant_key):
    """
    Return the correct figure for the given structure + variant.
    Falls back to an empty figure with a note if not yet supported.
    """
    if structure_key == "saddle_span" and variant_key == "standard_saddle":
        return generate_standard_saddle_figure()
    elif structure_key == "saddle_span" and variant_key == "cantilever_leaf":
        return generate_cantilever_leaf_figure()
    else:
        fig = go.Figure()
        fig.add_annotation(
            text="3D view for this variant coming soon",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#f39c12", size=16),
        )
        return _apply_common_layout(fig, 10.0)
