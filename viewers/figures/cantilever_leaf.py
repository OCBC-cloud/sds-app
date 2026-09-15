# =============================================================================
# SDSe - Cantilever Leaf Figure Builder
# =============================================================================
# Builds the 3D figure for the Cantilever Leaf variant.
# Called by viewers/results_viewer.py dispatcher.
#
# Reads arrangement from session state:
#   single      -> 1 leaf
#   double      -> 2 leaves mirrored
#   multiple    -> N leaves at equal rotation around column
#   tree_stack  -> 1-3 tiers, scale factor 0.75, rotation fixed
#   tree_spiral -> N leaves spiralling up at golden angle
#
# Column and baseplate drawn once. Leaf parts drawn per copy.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go

import streamlit as st

from viewers.figures._shared import apply_common_layout


# =============================================================================
# CONSTANTS
# =============================================================================

TIER_SCALE = 0.75
TIER_ROTATION_DEG = 45.0
TIER_RISE_FACTOR = 0.85
GOLDEN_ANGLE_DEG = 137.507764
SPIRAL_SCALE = 0.97
SPIRAL_RISE_FACTOR = 0.55


# =============================================================================
# LEAF GEOMETRY
# =============================================================================

def _compute_leaf_parts():
    """Return all base leaf geometry as dicts of arrays."""
    col_h = float(st.session_state.get("ws_sl_column_height", 10.0))
    outreach = float(st.session_state.get("ws_sl_outreach", 10.0))
    ribs_per_side = int(st.session_state.get("ws_sl_ribs_per_side", 7))
    tilt_deg = float(st.session_state.get("ws_sl_rib_tilt", 20))
    arc_r = float(st.session_state.get("ws_sl_arc_radius", 5.0))
    strut_joint = float(st.session_state.get("ws_sl_strut_joint_height", col_h * 0.75))
    rib_override = st.session_state.get("ws_sl_rib_lengths_override", [])

    n_beam = 80
    t_beam = np.linspace(0, 1, n_beam)
    beam_x = outreach * t_beam
    beam_z = col_h + arc_r * np.sin(t_beam * np.pi * 0.6) * 0.7
    beam_y = np.zeros_like(t_beam)

    rib_ts = np.linspace(0.08, 0.92, ribs_per_side)

    def leaf_half_width(t):
        return outreach * 0.42 * (np.sin(np.pi * t) ** 0.7)

    def rib_tilt_at(t):
        return math.radians(tilt_deg) * (math.sin(math.pi * t) ** 0.7)

    rib_lines = []
    for i, t in enumerate(rib_ts):
        idx = int(t * (n_beam - 1))
        a_x = beam_x[idx]
        a_z = beam_z[idx]
        half_w = leaf_half_width(t)
        tilt = rib_tilt_at(t)
        if rib_override and i < len(rib_override):
            base_half = leaf_half_width(t)
            ratio = float(rib_override[i]) / max(0.01, base_half)
            half_w = half_w * ratio
            tip_z = a_z + half_w * math.tan(tilt)
        else:
            tip_z = a_z + half_w * math.tan(tilt)
        rib_lines.append({
            "attach": (a_x, a_z),
            "left_tip": (a_x, -half_w, tip_z),
            "right_tip": (a_x, +half_w, tip_z),
        })

    return {
        "col_h": col_h,
        "outreach": outreach,
        "beam_x": beam_x,
        "beam_y": beam_y,
        "beam_z": beam_z,
        "ribs": rib_lines,
        "strut_joint": strut_joint,
        "arc_r": arc_r,
    }


# =============================================================================
# LEAF DRAWING (single copy, with rotation / scale / rise)
# =============================================================================

def _add_leaf(fig, parts, rot_deg=0.0, scale=1.0, z_offset=0.0):
    """Add one copy of the leaf at the given rotation and offset."""
    theta = math.radians(rot_deg)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    def _rot(x, y):
        xr = x * cos_t - y * sin_t
        yr = x * sin_t + y * cos_t
        return xr, yr

    col_h = parts["col_h"]

    # ---- Main beam (curved spine)
    bxs, bys, bzs = [], [], []
    for i in range(len(parts["beam_x"])):
        xv = parts["beam_x"][i] * scale
        yv = parts["beam_y"][i] * scale
        zv = (parts["beam_z"][i] - col_h) * scale + col_h + z_offset
        xr, yr = _rot(xv, yv)
        bxs.append(xr)
        bys.append(yr)
        bzs.append(zv)

    fig.add_trace(go.Scatter3d(
        x=bxs, y=bys, z=bzs,
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        showlegend=False,
        hoverinfo="skip",
    ))

    # ---- Ribs
    for rib in parts["ribs"]:
        ax = rib["attach"][0] * scale
        az = (rib["attach"][1] - col_h) * scale + col_h + z_offset
        lx = rib["left_tip"][0] * scale
        ly = rib["left_tip"][1] * scale
        lz = (rib["left_tip"][2] - col_h) * scale + col_h + z_offset
        rx = rib["right_tip"][0] * scale
        ry = rib["right_tip"][1] * scale
        rz = (rib["right_tip"][2] - col_h) * scale + col_h + z_offset

        axr, ayr = _rot(ax, 0.0)
        lxr, lyr = _rot(lx, ly)
        rxr, ryr = _rot(rx, ry)

        fig.add_trace(go.Scatter3d(
            x=[axr, lxr], y=[ayr, lyr], z=[az, lz],
            mode="lines",
            line=dict(color="#3498db", width=3),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=[axr, rxr], y=[ayr, ryr], z=[az, rz],
            mode="lines",
            line=dict(color="#3498db", width=3),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ---- Membrane
    n_u = 24
    n_v = 24
    X_s = np.zeros((n_u, n_v))
    Y_s = np.zeros((n_u, n_v))
    Z_s = np.zeros((n_u, n_v))
    n_beam = len(parts["beam_x"])

    def _half_width(t):
        return parts["outreach"] * 0.42 * (np.sin(np.pi * t) ** 0.7)

    def _tilt(t):
        return math.radians(st.session_state.get("ws_sl_rib_tilt", 20)) * (math.sin(np.pi * t) ** 0.7)

    for i, t in enumerate(np.linspace(0.02, 0.98, n_u)):
        idx = int(t * (n_beam - 1))
        bx = parts["beam_x"][idx]
        bz = parts["beam_z"][idx]
        hw = _half_width(t)
        tilt = _tilt(t)
        tip_z = bz + hw * math.tan(tilt)

        for j, v in enumerate(np.linspace(-1, 1, n_v)):
            x_loc = bx * scale
            y_loc = v * hw * scale
            z_edge = bz * (1 - abs(v)) + tip_z * abs(v)
            sag = 0.15 * hw * (1 - (2 * abs(v) - 1) ** 2)
            z_loc = (z_edge - sag - col_h) * scale + col_h + z_offset
            xr, yr = _rot(x_loc, y_loc)
            X_s[i, j] = xr
            Y_s[i, j] = yr
            Z_s[i, j] = z_loc

    fig.add_trace(go.Surface(
        x=X_s, y=Y_s, z=Z_s,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.55,
        showscale=False,
        hoverinfo="skip",
    ))

    # ---- Curved strut
    idx_third = int(0.33 * (n_beam - 1))
    px = parts["beam_x"][idx_third] * scale
    pz = (parts["beam_z"][idx_third] - col_h) * scale + col_h + z_offset
    t_s = np.linspace(0, 1, 20)
    sx_loc = px * (1 - t_s)
    sz_loc = pz + (parts["strut_joint"] * scale + z_offset - pz) * t_s
    sxr = sx_loc * cos_t
    syr = sx_loc * sin_t

    fig.add_trace(go.Scatter3d(
        x=sxr, y=syr, z=sz_loc,
        mode="lines",
        line=dict(color="#e67e22", width=3),
        showlegend=False,
        hoverinfo="skip",
    ))










# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def build_cantilever_leaf():
    """Cantilever Leaf: column, spine, ribs, membrane, strut, and arrangement."""
    col_h = float(st.session_state.get("ws_sl_column_height", 10.0))
    outreach = float(st.session_state.get("ws_sl_outreach", 10.0))

    if col_h <= 0 or outreach <= 0:
        fig = go.Figure()
        fig.add_annotation(text="Invalid geometry - check inputs",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#f39c12", size=16))
        return apply_common_layout(fig, 10.0)

    parts = _compute_leaf_parts()

    fig = go.Figure()

    # ---- Column (drawn once)
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

    # ---- Read arrangement
    arrangement = st.session_state.get("ws_sl_arrangement", "single")

    if arrangement == "single":
        _add_leaf(fig, parts, 0.0, 1.0, 0.0)

    elif arrangement == "double":
        _add_leaf(fig, parts, 0.0, 1.0, 0.0)
        _add_leaf(fig, parts, 180.0, 1.0, 0.0)

    elif arrangement == "multiple":
        n = int(st.session_state.get("ws_sl_arrangement_count", 4))
        if n < 2:
            n = 2
        step = 360.0 / n
        for k in range(n):
            _add_leaf(fig, parts, k * step, 1.0, 0.0)

    elif arrangement == "tree_stack":
        n_tiers = int(st.session_state.get("ws_sl_arrangement_tiers", 1))
        if n_tiers < 1:
            n_tiers = 1
        rise = outreach * TIER_RISE_FACTOR
        for k in range(n_tiers):
            scale = TIER_SCALE ** k
            z_off = rise * k
            rot = k * TIER_ROTATION_DEG
            _add_leaf(fig, parts, rot, scale, z_off)

    elif arrangement == "tree_spiral":
        n_leaves = int(st.session_state.get("ws_sl_arrangement_spiral_count", 8))
        if n_leaves < 3:
            n_leaves = 3
        rise = outreach * SPIRAL_RISE_FACTOR
        for k in range(n_leaves):
            scale = SPIRAL_SCALE ** k
            z_off = rise * k
            rot = k * GOLDEN_ANGLE_DEG
            _add_leaf(fig, parts, rot, scale, z_off)

    else:
        _add_leaf(fig, parts, 0.0, 1.0, 0.0)

    # ---- Legend dummies (drawn once)
    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        name="Main beam",
    ))
    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="lines",
        line=dict(color="#e67e22", width=3),
        name="Curved strut",
    ))

    return apply_common_layout(fig, col_h)
