# =============================================================================
# SDSe - Cantilever Leaf Figure Builder
# =============================================================================
# Builds the 3D figure for the Cantilever Leaf variant.
# Called by viewers/results_viewer.py dispatcher.
#
# Reads arrangement from session state:
#   single       -> 1 leaf
#   double       -> 2 leaves mirrored
#   multiple     -> N leaves at equal rotation around column
#   tree_stack   -> 1-3 tiers, scale factor 0.75, rotation fixed
#   tiered_helix -> N leaves placed by engine/leaf_arrangement (helix)
#
# Rib override support:
#   If ws_sl_rib_override_active is True and ws_sl_rib_lengths_override
#   contains values, the membrane and perimeter cable follow the new
#   rib tips. The whole leaf reshapes coherently.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go

import streamlit as st

from viewers.figures._shared import apply_common_layout
from engine.leaf_arrangement import place_leaves


# =============================================================================
# CONSTANTS
# =============================================================================

TIER_SCALE = 0.75
TIER_ROTATION_DEG = 45.0
TIER_RISE_FACTOR = 0.85


# =============================================================================
# COLUMN TOP RESOLVER
# =============================================================================

def _resolve_column_top_z(col_h, arrangement):
    """Return the correct top of the column for this arrangement."""
    if arrangement == "tiered_helix":
        fl_h = float(st.session_state.get("ws_sl_first_leaf_height", 3.0))
        lz_h = float(st.session_state.get("ws_sl_leaf_zone_height", 7.0))
        return max(col_h, fl_h + lz_h)
    return col_h


# =============================================================================
# RIB OVERRIDE HELPERS
# =============================================================================

def _get_rib_override(n_ribs, base_lengths):
    """
    Return a normalised ratio list for rib overrides.

    Returns None if no override is active. Otherwise returns a list
    of length n_ribs where each entry is override[i] / base[i].
    Ratios are clamped to a sane range to avoid extreme geometry.
    """
    override_active = bool(st.session_state.get("ws_sl_rib_override_active", False))
    if not override_active:
        return None

    override = st.session_state.get("ws_sl_rib_lengths_override", [])
    if not override:
        return None

    ratios = []
    for i in range(n_ribs):
        base = base_lengths[i] if i < len(base_lengths) else 1.0
        ovr = override[i] if i < len(override) else base
        if base <= 0.01:
            base = 0.01
        r = float(ovr) / base
        # Clamp to keep geometry sane
        if r < 0.25:
            r = 0.25
        if r > 4.0:
            r = 4.0
        ratios.append(r)
    return ratios


def _rib_ratio_at(t, ratios):
    """
    Return the interpolated override ratio at parameter t in [0, 1].

    t maps to rib index positions consistent with _compute_leaf_parts:
    ribs sit at ts = linspace(0.08, 0.92, n_ribs).
    """
    if not ratios:
        return 1.0

    n = len(ratios)
    if n == 1:
        return ratios[0]

    # Rib positions
    ts = [0.08 + (0.92 - 0.08) * i / (n - 1) for i in range(n)]

    # Before first rib
    if t <= ts[0]:
        return ratios[0]

    # After last rib
    if t >= ts[-1]:
        return ratios[-1]

    # Between ribs: linear interpolation
    for i in range(n - 1):
        if ts[i] <= t <= ts[i + 1]:
            span = ts[i + 1] - ts[i]
            if span < 1e-9:
                return ratios[i]
            w = (t - ts[i]) / span
            return ratios[i] * (1.0 - w) + ratios[i + 1] * w

    return 1.0


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

    n_beam = 80
    t_beam = np.linspace(0, 1, n_beam)
    beam_x = outreach * t_beam
    beam_z = col_h + (arc_r * 0.5) * 4.0 * t_beam * (1.0 - t_beam)
    beam_y = np.zeros_like(t_beam)

    rib_ts = np.linspace(0.08, 0.92, ribs_per_side)

    def leaf_half_width(t):
        return outreach * 0.42 * (np.sin(np.pi * t) ** 0.7)

    def rib_tilt_at(t):
        return math.radians(tilt_deg) * (math.sin(np.pi * t) ** 0.7)

    # ---- Build base rib lengths (for override ratio computation)
    base_lengths = []
    for t in rib_ts:
        half_w = leaf_half_width(t)
        tilt_local = tilt_deg * (math.sin(np.pi * t) ** 0.7)
        z_rise = half_w * math.tan(math.radians(tilt_local))
        length = math.sqrt(half_w * half_w + z_rise * z_rise)
        base_lengths.append(round(length, 2))

    # ---- Build override ratio map
    ratios = _get_rib_override(ribs_per_side, base_lengths)

    # ---- Build rib lines (with override applied)
    rib_lines = []
    for i, t in enumerate(rib_ts):
        idx = int(t * (n_beam - 1))
        a_x = beam_x[idx]
        a_z = beam_z[idx]
        half_w = leaf_half_width(t)
        tilt = rib_tilt_at(t)

        if ratios:
            half_w = half_w * ratios[i]

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
        "rib_ratios": ratios,
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
    ratios = parts.get("rib_ratios", None)

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

    # ---- Membrane (follows rib override ratios)
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

        # Apply override ratio at this parameter position
        if ratios:
            hw = hw * _rib_ratio_at(t, ratios)

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
# TIERED HELIX ARRANGEMENT (engine-driven)
# =============================================================================

def _add_tiered_helix(fig, parts):
    """Place leaves along a helix using engine/leaf_arrangement.place_leaves()."""
    first_leaf_height = float(st.session_state.get("ws_sl_first_leaf_height", 3.0))
    leaf_zone_height = float(st.session_state.get("ws_sl_leaf_zone_height", 7.0))
    num_leaves = int(st.session_state.get("ws_sl_num_leaves", 8))
    column_radius = float(st.session_state.get("ws_sl_column_radius", 0.15))
    leaf_angular_width = float(st.session_state.get("ws_sl_leaf_angular_width", 60.0))
    taper_mode = str(st.session_state.get("ws_sl_taper_mode", "taper_up"))
    taper_ratio = float(st.session_state.get("ws_sl_taper_ratio", 0.88))

    result = place_leaves(
        first_leaf_height=first_leaf_height,
        leaf_zone_height=leaf_zone_height,
        num_leaves=num_leaves,
        column_radius=column_radius,
        leaf_angular_width=leaf_angular_width,
        scale_mode=taper_mode,
        taper_ratio=taper_ratio,
    )

    buds = result["buds"]

    # ---- Bud stubs
    for bud in buds:
        ax, ay, az = bud["axis_attach"]
        tx, ty, tz = bud["bud_tip"]
        fig.add_trace(go.Scatter3d(
            x=[ax, tx], y=[ay, ty], z=[az, tz],
            mode="lines",
            line=dict(color="#f1c40f", width=4),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ---- Bud anchor nodes
    anchor_x = [b["axis_attach"][0] for b in buds]
    anchor_y = [b["axis_attach"][1] for b in buds]
    anchor_z = [b["axis_attach"][2] for b in buds]
    fig.add_trace(go.Scatter3d(
        x=anchor_x, y=anchor_y, z=anchor_z,
        mode="markers",
        marker=dict(color="#f1c40f", size=5, symbol="circle"),
        showlegend=False,
        hoverinfo="skip",
    ))

    # ---- Each leaf at its bud
    for bud in buds:
        _add_leaf(
            fig,
            parts,
            rot_deg=bud["yaw_deg"],
            scale=bud["scale"],
            z_offset=bud["z_attach"] - parts["col_h"],
        )

    # ---- Virtual helix reference curve
    if len(buds) >= 2:
        hx = [b["bud_tip"][0] for b in buds]
        hy = [b["bud_tip"][1] for b in buds]
        hz = [b["bud_tip"][2] for b in buds]
        fig.add_trace(go.Scatter3d(
            x=hx, y=hy, z=hz,
            mode="lines",
            line=dict(color="#9b59b6", width=2, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        ))

    return result["meta"]


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

    # ---- Read arrangement (needed for column top resolution)
    arrangement = st.session_state.get("ws_sl_arrangement", "single")

    # ---- Column (extends through the leaf zone when tiered_helix)
    col_top_z = _resolve_column_top_z(col_h, arrangement)

    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[0, col_top_z],
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

    elif arrangement == "tiered_helix":
        _add_tiered_helix(fig, parts)

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

    return apply_common_layout(fig, col_top_z)
