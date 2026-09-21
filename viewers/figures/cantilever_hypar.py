# =============================================================================
# SDSe - Cantilever Hypar Figure Builder
# =============================================================================
# Builds the 3D figure for the Cantilever Hypar variant.
# Called by viewers/results_viewer.py dispatcher.
#
# Geometry (from SPEC_cantilever_hypar.md):
#   - Straight vertical column at one end of the structure.
#   - Arc arm anchored to the column at a set fraction of column
#     height, arcing UPWARD in the middle. Both ends of the arm
#     sit at the same height.
#   - Diagonal strut from column top to the arm. Crossing point
#     is the structural anchor.
#   - Two perpendicular bent ribs at the arm's midpoint. Each rib
#     arcs UPWARD. Rib tips higher than the rib anchor.
#   - Saddle membrane spanning the four corners:
#       arm anchor end (lower), arm tip end (lower),
#       left rib tip (higher), right rib tip (higher).
#   - Edge cables concave inward (per PRINCIPLES_membrane.md).
#
# Arrangement is handled by engine/leaf_arrangement.py — the same
# shape-agnostic engine used by Cantilever Leaf. No new arrangement
# logic is written here.
#
# Placeholder inputs (see engine/PLACEHOLDERS.md):
#   - Column radius: draws the column thickness.
#   - Arm arc radius: draws the arm curve.
#   - Membrane edge sag (10-15%): draws the saddle surface.
#   These are removed when the structural calc engine and FDM
#   engine land. Do not treat them as design values.
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

# Arrangement constants (identical to Cantilever Leaf).
TIER_SCALE = 0.75
TIER_ROTATION_DEG = 45.0
TIER_RISE_FACTOR = 0.85

# Placeholder value: fraction of edge length to sag inward.
# PLACEHOLDER VALUE - replace with FDM result.
# See engine/PLACEHOLDERS.md.
EDGE_SAG_FRACTION = 0.12


# =============================================================================
# PARAMETER READERS
# =============================================================================

def _read_params():
    """Read all Hypar parameters from session state into one dict."""
    p = {
        # Real user inputs
        "column_height": float(st.session_state.get("ws_ch_column_height", 10.0)),
        "arm_reach": float(st.session_state.get("ws_ch_arm_reach", 6.0)),
        "anchor_fraction": float(st.session_state.get("ws_ch_anchor_fraction", 0.65)),
        "rib_reach": float(st.session_state.get("ws_ch_rib_reach", 3.0)),
        "rib_bend_deg": float(st.session_state.get("ws_ch_rib_bend_deg", 15.0)),
        # Placeholder inputs (remove when structural engine lands)
        "column_radius": float(st.session_state.get("ws_ch_column_radius", 0.15)),
        "arm_arc_radius": float(st.session_state.get("ws_ch_arm_arc_radius", 4.0)),
    }
    return p





# =============================================================================
# MOTHER OBJECT GEOMETRY
# =============================================================================

def _compute_hypar_geometry(p):
    """
    Return a dict of arrays describing one Hypar mother object.

    Coordinate system:
      - Origin (0, 0, 0) at base of column.
      - Column runs vertically up Z.
      - Arm extends in +X direction.
      - Ribs extend in ±Y direction.
    """
    col_h = p["column_height"]
    reach = p["arm_reach"]
    anchor_frac = p["anchor_fraction"]
    rib_reach = p["rib_reach"]
    rib_bend_deg = p["rib_bend_deg"]
    arc_r = p["arm_arc_radius"]

    anchor_z = col_h * anchor_frac

    # ---- Arm arc: from column surface at anchor_z, arcs upward in
    # the middle, comes back to anchor_z at the free tip.
    # We model it as a symmetric parabola between two endpoints:
    #   start: (0, 0, anchor_z)
    #   end:   (reach, 0, anchor_z)
    #   apex:  midway, at anchor_z + rise
    # The rise is derived from the arc radius placeholder.
    n_arm = 80
    t_arm = np.linspace(0.0, 1.0, n_arm)
    arm_x = reach * t_arm
    # Parabolic rise with peak at t = 0.5
    # rise = arc_r * 0.5 controls apex height above anchor.
    rise = arc_r * 0.5
    arm_z = anchor_z + 4.0 * rise * t_arm * (1.0 - t_arm)
    arm_y = np.zeros_like(t_arm)

    # ---- Arm midpoint index (apex of the arc)
    mid_idx = n_arm // 2
    mid_x = arm_x[mid_idx]
    mid_y = arm_y[mid_idx]
    mid_z = arm_z[mid_idx]

    # ---- Ribs: two arcs attaching at the arm's midpoint,
    # extending in ±Y direction. Each rib arcs upward, so the tip
    # is HIGHER than the rib anchor.
    n_rib = 40
    t_rib = np.linspace(0.0, 1.0, n_rib)
    rib_rise = rib_reach * math.tan(math.radians(rib_bend_deg))

    # Left rib (negative Y)
    left_rib_x = np.full(n_rib, mid_x)
    left_rib_y = -rib_reach * t_rib
    left_rib_z = mid_z + 4.0 * rib_rise * t_rib * (1.0 - t_rib)

    # Right rib (positive Y)
    right_rib_x = np.full(n_rib, mid_x)
    right_rib_y = rib_reach * t_rib
    right_rib_z = mid_z + 4.0 * rib_rise * t_rib * (1.0 - t_rib)

    left_tip = (mid_x, -rib_reach, mid_z + rib_rise)
    right_tip = (mid_x, rib_reach, mid_z + rib_rise)

    # ---- Structural anchor: intersection of strut with arm.
    # Strut runs from column top (0, 0, col_h) toward the arm.
    # We define the strut's direction toward the arm's apex and
    # find where it crosses the arm's arc. Simplified approach:
    # find the point on the arm where a straight line from the
    # column top points at the arm's anchor.
    # Since the arm starts at (0, 0, anchor_z), the strut from
    # column top to that point is nearly vertical. For a proper
    # structural anchor we place it on the arm at a small
    # horizontal offset:
    anchor_x = reach * 0.15
    # Solve arm_z at this x
    t_anchor = anchor_x / reach
    anchor_z_on_arm = anchor_z + 4.0 * rise * t_anchor * (1.0 - t_anchor)

    strut_start = (0.0, 0.0, col_h)
    strut_end = (anchor_x, 0.0, anchor_z_on_arm)

    # ---- Membrane four corners
    corner_anchor = (0.0, 0.0, anchor_z)               # arm start
    corner_tip = (reach, 0.0, anchor_z)                # arm tip
    corner_left = left_tip
    corner_right = right_tip

    return {
        "col_h": col_h,
        "col_r": p["column_radius"],
        "anchor_z": anchor_z,
        "arm_x": arm_x, "arm_y": arm_y, "arm_z": arm_z,
        "mid": (mid_x, mid_y, mid_z),
        "left_rib_x": left_rib_x,
        "left_rib_y": left_rib_y,
        "left_rib_z": left_rib_z,
        "right_rib_x": right_rib_x,
        "right_rib_y": right_rib_y,
        "right_rib_z": right_rib_z,
        "left_tip": left_tip,
        "right_tip": right_tip,
        "strut_start": strut_start,
        "strut_end": strut_end,
        "corner_anchor": corner_anchor,
        "corner_tip": corner_tip,
        "corner_left": corner_left,
        "corner_right": corner_right,
    }


# =============================================================================
# MEMBRANE SURFACE
# =============================================================================
# Four-corner bilinear saddle. The membrane touches the structure
# only at the four corners (per PRINCIPLES_membrane.md). Edges are
# concave inward by a placeholder fraction. The interior is a
# bilinear interpolation with a small sag toward the centre.

def _build_membrane(geom, n_u=24, n_v=24):
    """Return X, Y, Z arrays for the membrane surface."""
    c_a = np.array(geom["corner_anchor"])
    c_t = np.array(geom["corner_tip"])
    c_l = np.array(geom["corner_left"])
    c_r = np.array(geom["corner_right"])

    # Bilinear interpolation. Let u sweep from anchor side to tip side,
    # and v sweep from left edge to right edge.
    X = np.zeros((n_u, n_v))
    Y = np.zeros((n_u, n_v))
    Z = np.zeros((n_u, n_v))

    centre = (c_a + c_t + c_l + c_r) * 0.25

    for i, u in enumerate(np.linspace(0.0, 1.0, n_u)):
        for j, v in enumerate(np.linspace(0.0, 1.0, n_v)):
            # Corner interpolation
            left_pt = c_a * (1.0 - u) + c_l * u
            right_pt = c_t * (1.0 - u) + c_r * u
            pt = left_pt * (1.0 - v) + right_pt * v

            # Apply a sag toward the centre, strongest away from
            # all four edges.
            edge_w_u = min(u, 1.0 - u) * 2.0
            edge_w_v = min(v, 1.0 - v) * 2.0
            weight = edge_w_u * edge_w_v
            sagged = pt * (1.0 - EDGE_SAG_FRACTION * weight) + centre * (EDGE_SAG_FRACTION * weight)

            X[i, j] = sagged[0]
            Y[i, j] = sagged[1]
            Z[i, j] = sagged[2]

    return X, Y, Z





# =============================================================================
# MOTHER OBJECT DRAWING
# =============================================================================

def _add_hypar_mother(fig, geom, rot_deg=0.0, scale=1.0, z_offset=0.0,
                       col_h_ref=None, show_legend=False):
    """
    Add one Hypar mother object at the given rotation, scale, and
    vertical offset. All coordinates are scaled relative to the
    base column height (col_h_ref) so that stacking works properly.
    """
    theta = math.radians(rot_deg)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    def _rot(x, y):
        return x * cos_t - y * sin_t, x * sin_t + y * cos_t

    def _scale_z(z):
        if col_h_ref is None or col_h_ref <= 0:
            return z * scale + z_offset
        return (z - col_h_ref) * scale + col_h_ref + z_offset

    # ---- Arm
    ax, ay, az = [], [], []
    for i in range(len(geom["arm_x"])):
        xv = geom["arm_x"][i] * scale
        yv = geom["arm_y"][i] * scale
        zv = _scale_z(geom["arm_z"][i])
        xr, yr = _rot(xv, yv)
        ax.append(xr)
        ay.append(yr)
        az.append(zv)

    fig.add_trace(go.Scatter3d(
        x=ax, y=ay, z=az,
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        showlegend=show_legend,
        name="Arm" if show_legend else None,
        hoverinfo="skip",
    ))

    # ---- Left rib
    lx, ly, lz = [], [], []
    for i in range(len(geom["left_rib_x"])):
        xv = geom["left_rib_x"][i] * scale
        yv = geom["left_rib_y"][i] * scale
        zv = _scale_z(geom["left_rib_z"][i])
        xr, yr = _rot(xv, yv)
        lx.append(xr)
        ly.append(yr)
        lz.append(zv)

    fig.add_trace(go.Scatter3d(
        x=lx, y=ly, z=lz,
        mode="lines",
        line=dict(color="#3498db", width=4),
        showlegend=show_legend,
        name="Ribs" if show_legend else None,
        hoverinfo="skip",
    ))

    # ---- Right rib
    rx, ry, rz = [], [], []
    for i in range(len(geom["right_rib_x"])):
        xv = geom["right_rib_x"][i] * scale
        yv = geom["right_rib_y"][i] * scale
        zv = _scale_z(geom["right_rib_z"][i])
        xr, yr = _rot(xv, yv)
        rx.append(xr)
        ry.append(yr)
        rz.append(zv)

    fig.add_trace(go.Scatter3d(
        x=rx, y=ry, z=rz,
        mode="lines",
        line=dict(color="#3498db", width=4),
        showlegend=False,
        hoverinfo="skip",
    ))

    # ---- Strut
    ss = geom["strut_start"]
    se = geom["strut_end"]
    ssx, ssy = _rot(ss[0] * scale, ss[1] * scale)
    sex, sey = _rot(se[0] * scale, se[1] * scale)
    fig.add_trace(go.Scatter3d(
        x=[ssx, sex],
        y=[ssy, sey],
        z=[_scale_z(ss[2]), _scale_z(se[2])],
        mode="lines",
        line=dict(color="#e67e22", width=3),
        showlegend=show_legend,
        name="Strut" if show_legend else None,
        hoverinfo="skip",
    ))

    # ---- Membrane surface (only when scale is 1 for clarity;
    # smaller stacked membranes are still drawn for continuity)
    X_m, Y_m, Z_m = _build_membrane(geom)
    X_rot = np.zeros_like(X_m)
    Y_rot = np.zeros_like(Y_m)
    Z_rot = np.zeros_like(Z_m)
    for i in range(X_m.shape[0]):
        for j in range(X_m.shape[1]):
            xv = X_m[i, j] * scale
            yv = Y_m[i, j] * scale
            zv = _scale_z(Z_m[i, j])
            xr, yr = _rot(xv, yv)
            X_rot[i, j] = xr
            Y_rot[i, j] = yr
            Z_rot[i, j] = zv

    fig.add_trace(go.Surface(
        x=X_rot, y=Y_rot, z=Z_rot,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.55,
        showscale=False,
        hoverinfo="skip",
    ))

    # ---- Edge cables (yellow dashed) around the four corners
    corners = [
        geom["corner_anchor"],
        geom["corner_left"],
        geom["corner_tip"],
        geom["corner_right"],
        geom["corner_anchor"],
    ]
    ecx, ecy, ecz = [], [], []
    for c in corners:
        xv = c[0] * scale
        yv = c[1] * scale
        zv = _scale_z(c[2])
        xr, yr = _rot(xv, yv)
        ecx.append(xr)
        ecy.append(yr)
        ecz.append(zv)

    fig.add_trace(go.Scatter3d(
        x=ecx, y=ecy, z=ecz,
        mode="lines",
        line=dict(color="#f1c40f", width=3, dash="dot"),
        showlegend=show_legend,
        name="Edge cables" if show_legend else None,
        hoverinfo="skip",
    ))

    # ---- Joint marker at the structural anchor on the arm
    jx = geom["strut_end"][0] * scale
    jy = geom["strut_end"][1] * scale
    jz = _scale_z(geom["strut_end"][2])
    jxr, jyr = _rot(jx, jy)
    fig.add_trace(go.Scatter3d(
        x=[jxr], y=[jyr], z=[jz],
        mode="markers",
        marker=dict(color="#f1c40f", size=6, symbol="circle"),
        showlegend=False,
        hoverinfo="skip",
    ))


# =============================================================================
# TIERED HELIX ARRANGEMENT (reuses leaf_arrangement engine)
# =============================================================================

def _add_tiered_helix(fig, geom, col_h_ref):
    """Place Hypar units along a helix using engine/leaf_arrangement."""
    first_leaf_height = float(st.session_state.get("ws_ch_first_leaf_height", col_h_ref))
    leaf_zone_height = float(st.session_state.get("ws_ch_leaf_zone_height", 7.0))
    num_leaves = int(st.session_state.get("ws_ch_num_leaves", 8))
    column_radius = float(st.session_state.get("ws_ch_column_radius", 0.15))
    leaf_angular_width = float(st.session_state.get("ws_ch_leaf_angular_width", 60.0))
    taper_mode = str(st.session_state.get("ws_ch_taper_mode", "taper_up"))
    taper_ratio = float(st.session_state.get("ws_ch_taper_ratio", 0.88))

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

    # ---- Bud stubs (yellow reference lines)
    for bud in buds:
        ax, ay, az = bud["axis_attach"]
        tx, ty, tz = bud["bud_tip"]
        fig.add_trace(go.Scatter3d(
            x=[ax, tx], y=[ay, ty], z=[az, tz],
            mode="lines",
            line=dict(color="#f1c40f", width=3),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ---- Each mother object at its bud
    for bud in buds:
        _add_hypar_mother(
            fig, geom,
            rot_deg=bud["yaw_deg"],
            scale=bud["scale"],
            z_offset=bud["z_attach"] - col_h_ref,
            col_h_ref=col_h_ref,
            show_legend=False,
        )

    return result["meta"]


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def build_cantilever_hypar():
    """Cantilever Hypar: column, arm, ribs, strut, membrane, arrangement."""
    p = _read_params()

    col_h = p["column_height"]
    reach = p["arm_reach"]

    if col_h <= 0 or reach <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Invalid geometry - check inputs",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#f39c12", size=16),
        )
        return apply_common_layout(fig, 10.0)

    geom = _compute_hypar_geometry(p)

    fig = go.Figure()

    arrangement = st.session_state.get("ws_ch_arrangement", "single")

    # ---- Column height for display: extend through helix zone
    col_top_z = col_h
    if arrangement == "tiered_helix":
        fl_h = float(st.session_state.get("ws_ch_first_leaf_height", col_h))
        lz_h = float(st.session_state.get("ws_ch_leaf_zone_height", 7.0))
        col_top_z = max(col_h, fl_h + lz_h)

    # ---- Column (straight, green)
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

    # ---- Arrangement routing
    if arrangement == "single":
        _add_hypar_mother(fig, geom, 0.0, 1.0, 0.0,
                          col_h_ref=col_h, show_legend=True)

    elif arrangement == "double":
        _add_hypar_mother(fig, geom, 0.0, 1.0, 0.0,
                          col_h_ref=col_h, show_legend=True)
        _add_hypar_mother(fig, geom, 180.0, 1.0, 0.0,
                          col_h_ref=col_h, show_legend=False)

    elif arrangement == "multiple":
        n = int(st.session_state.get("ws_ch_arrangement_count", 4))
        if n < 2:
            n = 2
        step = 360.0 / n
        for k in range(n):
            _add_hypar_mother(
                fig, geom, k * step, 1.0, 0.0,
                col_h_ref=col_h, show_legend=(k == 0),
            )

    elif arrangement == "tree_stack":
        n_tiers = int(st.session_state.get("ws_ch_arrangement_tiers", 1))
        if n_tiers < 1:
            n_tiers = 1
        rise = reach * TIER_RISE_FACTOR
        for k in range(n_tiers):
            scale_k = TIER_SCALE ** k
            z_off = rise * k
            rot = k * TIER_ROTATION_DEG
            _add_hypar_mother(
                fig, geom, rot, scale_k, z_off,
                col_h_ref=col_h, show_legend=(k == 0),
            )

    elif arrangement == "tiered_helix":
        _add_tiered_helix(fig, geom, col_h)

    else:
        _add_hypar_mother(fig, geom, 0.0, 1.0, 0.0,
                          col_h_ref=col_h, show_legend=True)

    # ---- Legend dummy for the membrane
    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="markers",
        marker=dict(color="#6ab0d4", size=8),
        name="Membrane",
    ))

    return apply_common_layout(fig, col_top_z)





