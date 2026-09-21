# =============================================================================
# SDSe - Cantilever Hypar Figure Builder
# =============================================================================
# Builds the 3D figure for the Cantilever Hypar variant.
# Called by viewers/results_viewer.py dispatcher.
#
# MEMBRANE-FIRST PRINCIPLE (per engine/PRINCIPLES_membrane.md):
#   1. Four corners A, B, C, D are the membrane's only supports.
#   2. The cable IS the membrane's edge. There is no separate
#      straight cable line. The cable follows the SAME concave
#      inward curve as the fabric edge.
#   3. The membrane touches the arm and ribs only at the four
#      corners.
#
# Plan view (X to the right, Y away from viewer):
#   A = arm anchor end at (0, 0, anchor_z)          LOW
#   C = arm tip end at (0, reach, anchor_z)          LOW
#   B = right rib tip                                HIGH
#   D = left rib tip                                 HIGH
#
# Rib geometry:
#   The rib is ONE continuous arc that passes through three points:
#     P_left  = left rib tip   (at -rib_reach in X)
#     P_mid   = arm's midpoint (the lowest point of the arc)
#     P_right = right rib tip  (at +rib_reach in X)
#   The user inputs BOTH the rib reach and the rib curve radius.
#
# Membrane edge sag:
#   The user inputs the sag as a percentage (0-30). The fabric
#   edges bow inward by that fraction of edge length. The cable
#   follows the same curve.
#
# History:
#   2026-09-21 - First build.
#   2026-09-21 - Edge cable winding corrected.
#   2026-09-21 - Membrane rebuilt as a saddle with concave edges.
#   2026-09-21 - Rib is now one arc through three points.
#   2026-09-21 - Membrane edge sag read from session state as a
#                percentage, driven by the workshop slider.
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

# Default sag fraction when session state has no value.
# PLACEHOLDER VALUE - replace with FDM result.
# See engine/PLACEHOLDERS.md.
DEFAULT_SAG_FRACTION = 0.15


def _edge_sag_fraction():
    """Read membrane edge sag from session state as a fraction."""
    pct = st.session_state.get("ws_ch_membrane_sag_pct", None)
    if pct is None:
        return DEFAULT_SAG_FRACTION
    try:
        return max(0.0, float(pct)) / 100.0
    except (TypeError, ValueError):
        return DEFAULT_SAG_FRACTION


# =============================================================================
# PARAMETER READERS
# =============================================================================

def _read_params():
    """Read all Hypar parameters from session state into one dict."""
    return {
        "column_height": float(st.session_state.get("ws_ch_column_height", 10.0)),
        "arm_reach": float(st.session_state.get("ws_ch_arm_reach", 6.0)),
        "anchor_fraction": float(st.session_state.get("ws_ch_anchor_fraction", 0.65)),
        "rib_reach": float(st.session_state.get("ws_ch_rib_reach", 3.0)),
        "rib_curve_radius": float(st.session_state.get("ws_ch_rib_curve_radius", 6.0)),
        "column_radius": float(st.session_state.get("ws_ch_column_radius", 0.15)),
        "arm_arc_radius": float(st.session_state.get("ws_ch_arm_arc_radius", 4.0)),
    }


# =============================================================================
# RIB ARC THROUGH THREE POINTS
# =============================================================================

def _arc_through_three_points(P_left, P_mid, P_right, radius, n_pts=40):
    """
    Return an array of n_pts points along an arc that passes through
    P_left, P_mid, P_right. P_mid is the lowest point of the arc;
    P_left and P_right are the two tips.
    """
    P_left = np.asarray(P_left, dtype=float)
    P_mid = np.asarray(P_mid, dtype=float)
    P_right = np.asarray(P_right, dtype=float)

    u_axis = P_right - P_left
    u_len = float(np.linalg.norm(u_axis))
    if u_len < 1e-9:
        return np.array([P_mid] * n_pts), True, 0.0
    u_axis = u_axis / u_len

    world_up = np.array([0.0, 0.0, 1.0])
    v_axis = world_up - np.dot(world_up, u_axis) * u_axis
    v_len = float(np.linalg.norm(v_axis))
    if v_len < 1e-9:
        v_axis = np.array([0.0, 1.0, 0.0])
        v_axis = v_axis - np.dot(v_axis, u_axis) * u_axis
        v_axis = v_axis / float(np.linalg.norm(v_axis))
    else:
        v_axis = v_axis / v_len

    origin = P_left
    x1, y1 = 0.0, float(np.dot(P_left - origin, v_axis))
    x2, y2 = float(np.dot(P_mid - origin, u_axis)), float(np.dot(P_mid - origin, v_axis))
    x3, y3 = u_len, float(np.dot(P_right - origin, v_axis))

    d = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        pts_2d = []
        for t in np.linspace(0.0, 1.0, n_pts):
            pts_2d.append(np.array([t * u_len, (1.0 - t) * y1 + t * y3]))
        pts_2d = np.array(pts_2d)
        adjusted = True
        actual_r = 0.0
    else:
        ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3)
              + (x2 ** 2 + y2 ** 2) * (y3 - y1)
              + (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
        uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2)
              + (x2 ** 2 + y2 ** 2) * (x1 - x3)
              + (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
        actual_r = math.sqrt((x1 - ux) ** 2 + (y1 - uy) ** 2)

        a_l = math.atan2(y1 - uy, x1 - ux)
        a_m = math.atan2(y2 - uy, x2 - ux)
        a_r = math.atan2(y3 - uy, x3 - ux)

        def _unwrap(a, ref):
            while a - ref > math.pi:
                a -= 2.0 * math.pi
            while a - ref < -math.pi:
                a += 2.0 * math.pi
            return a

        a_m = _unwrap(a_m, a_l)
        a_r = _unwrap(a_r, a_m)

        pts_2d = []
        for t in np.linspace(0.0, 1.0, n_pts):
            a = a_l + t * (a_r - a_l)
            pts_2d.append(np.array([ux + actual_r * math.cos(a),
                                     uy + actual_r * math.sin(a)]))
        pts_2d = np.array(pts_2d)
        adjusted = abs(actual_r - radius) > 1e-6

    pts_3d = np.zeros((n_pts, 3))
    for i in range(n_pts):
        pts_3d[i] = origin + pts_2d[i, 0] * u_axis + pts_2d[i, 1] * v_axis

    return pts_3d, adjusted, actual_r


# =============================================================================
# GEOMETRY
# =============================================================================

def _compute_hypar_geometry(p):
    """Return a dict of arrays and points describing one Hypar mother object."""
    col_h = p["column_height"]
    reach = p["arm_reach"]
    anchor_frac = p["anchor_fraction"]
    rib_reach = p["rib_reach"]
    rib_curve_r = p["rib_curve_radius"]
    arc_r = p["arm_arc_radius"]

    anchor_z = col_h * anchor_frac

    # ---- Arm arc
    n_arm = 80
    t_arm = np.linspace(0.0, 1.0, n_arm)
    arm_y = reach * t_arm
    arm_x = np.zeros_like(t_arm)
    arm_rise = arc_r * 0.5
    arm_z = anchor_z + 4.0 * arm_rise * t_arm * (1.0 - t_arm)

    mid_idx = n_arm // 2
    mid_x = float(arm_x[mid_idx])
    mid_y = float(arm_y[mid_idx])
    mid_z = float(arm_z[mid_idx])

    # ---- Rib arc through three points
    if rib_curve_r >= rib_reach:
        tip_rise = rib_curve_r - math.sqrt(rib_curve_r ** 2 - rib_reach ** 2)
        adjusted_radius = rib_curve_r
        radius_adjusted = False
    else:
        tip_rise = 0.0
        adjusted_radius = rib_reach
        radius_adjusted = True

    tip_z = mid_z + tip_rise

    P_left = np.array([-rib_reach, mid_y, tip_z])
    P_mid = np.array([mid_x, mid_y, mid_z])
    P_right = np.array([rib_reach, mid_y, tip_z])

    rib_pts, _adj, _r = _arc_through_three_points(
        P_left, P_mid, P_right, rib_curve_r, n_pts=60
    )

    # ---- Four membrane corners
    corner_A = np.array([0.0, 0.0, anchor_z])
    corner_C = np.array([0.0, reach, anchor_z])
    corner_B = np.array(P_right)
    corner_D = np.array(P_left)

    # ---- Strut from column top to a point on the arm
    strut_anchor_y = reach * 0.15
    t_strut = strut_anchor_y / reach
    strut_anchor_z = anchor_z + 4.0 * arm_rise * t_strut * (1.0 - t_strut)
    strut_start = (0.0, 0.0, col_h)
    strut_end = (0.0, strut_anchor_y, strut_anchor_z)

    return {
        "col_h": col_h,
        "col_r": p["column_radius"],
        "anchor_z": anchor_z,
        "arm_x": arm_x, "arm_y": arm_y, "arm_z": arm_z,
        "mid": (mid_x, mid_y, mid_z),
        "rib_pts": rib_pts,
        "left_tip": P_left,
        "right_tip": P_right,
        "strut_start": strut_start,
        "strut_end": strut_end,
        "corner_A": corner_A,
        "corner_B": corner_B,
        "corner_C": corner_C,
        "corner_D": corner_D,
        "rib_radius_adjusted": radius_adjusted,
        "rib_radius_used": adjusted_radius,
    }


# =============================================================================
# MEMBRANE EDGE AND SURFACE
# =============================================================================

def _concave_edge(p0, p1, centre, n_pts, sag_frac):
    """Return n_pts points along the fabric edge from p0 to p1,
    bowed inward toward the membrane centre by sag_frac of edge length."""
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    centre = np.asarray(centre, dtype=float)

    edge_vec = p1 - p0
    edge_len = float(np.linalg.norm(edge_vec))
    if edge_len < 1e-9:
        return [p0.copy() for _ in range(n_pts)]

    sag = sag_frac * edge_len
    mid = (p0 + p1) * 0.5
    inward = centre - mid
    inward_len = float(np.linalg.norm(inward))
    if inward_len < 1e-9:
        inward_dir = np.zeros(3)
    else:
        inward_dir = inward / inward_len

    pts = []
    for t in np.linspace(0.0, 1.0, n_pts):
        base = p0 * (1.0 - t) + p1 * t
        w = 4.0 * t * (1.0 - t)
        pts.append(base + inward_dir * sag * w)
    return pts


def _build_membrane_surface(geom, n_u=32, n_v=32):
    """Build the membrane as a Coons patch bounded by four concave edges."""
    sag_frac = _edge_sag_fraction()

    A = np.asarray(geom["corner_A"], dtype=float)
    B = np.asarray(geom["corner_B"], dtype=float)
    C = np.asarray(geom["corner_C"], dtype=float)
    D = np.asarray(geom["corner_D"], dtype=float)

    centre = (A + B + C + D) * 0.25

    n_edge = max(n_u, n_v)
    edge_AB = _concave_edge(A, B, centre, n_edge, sag_frac)
    edge_BC = _concave_edge(B, C, centre, n_edge, sag_frac)
    edge_CD = _concave_edge(C, D, centre, n_edge, sag_frac)
    edge_DA = _concave_edge(D, A, centre, n_edge, sag_frac)

    X = np.zeros((n_u, n_v))
    Y = np.zeros((n_u, n_v))
    Z = np.zeros((n_u, n_v))

    edge_DC_rev = edge_CD[::-1]
    edge_AD = edge_DA[::-1]

    for i, u in enumerate(np.linspace(0.0, 1.0, n_u)):
        P_left = edge_AB[i]
        P_right = edge_DC_rev[i]

        for j, v in enumerate(np.linspace(0.0, 1.0, n_v)):
            P_top = edge_AD[j]
            P_bottom = edge_BC[j]

            S = P_left * (1.0 - v) + P_right * v
            T = P_top * (1.0 - u) + P_bottom * u
            corner_term = (
                A * (1.0 - u) * (1.0 - v)
                + B * u * (1.0 - v)
                + D * (1.0 - u) * v
                + C * u * v
            )
            pt = S + T - corner_term

            X[i, j] = pt[0]
            Y[i, j] = pt[1]
            Z[i, j] = pt[2]

    return X, Y, Z


# =============================================================================
# MOTHER OBJECT DRAWING
# =============================================================================

def _add_hypar_mother(fig, geom, rot_deg=0.0, scale=1.0, z_offset=0.0,
                       col_h_ref=None, show_legend=False):
    """Add one Hypar mother object at the given rotation, scale, offset."""
    theta = math.radians(rot_deg)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    def _rot(x, y):
        return x * cos_t - y * sin_t, x * sin_t + y * cos_t

    def _scale_z(z):
        if col_h_ref is None or col_h_ref <= 0:
            return z * scale + z_offset
        return (z - col_h_ref) * scale + col_h_ref + z_offset

    def _transform(pt):
        xv = pt[0] * scale
        yv = pt[1] * scale
        zv = _scale_z(pt[2])
        xr, yr = _rot(xv, yv)
        return (xr, yr, zv)

    # ---- Arm
    ax, ay, az = [], [], []
    for i in range(len(geom["arm_x"])):
        xr, yr, zr = _transform(
            (geom["arm_x"][i], geom["arm_y"][i], geom["arm_z"][i])
        )
        ax.append(xr); ay.append(yr); az.append(zr)

    fig.add_trace(go.Scatter3d(
        x=ax, y=ay, z=az,
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        showlegend=show_legend,
        name="Arm" if show_legend else None,
        hoverinfo="skip",
    ))

    # ---- Rib arc
    rib = geom["rib_pts"]
    rbx, rby, rbz = [], [], []
    for i in range(rib.shape[0]):
        xr, yr, zr = _transform((rib[i, 0], rib[i, 1], rib[i, 2]))
        rbx.append(xr); rby.append(yr); rbz.append(zr)

    fig.add_trace(go.Scatter3d(
        x=rbx, y=rby, z=rbz,
        mode="lines",
        line=dict(color="#3498db", width=4),
        showlegend=show_legend,
        name="Ribs" if show_legend else None,
        hoverinfo="skip",
    ))

    # ---- Strut
    ssx, ssy, ssz = _transform(geom["strut_start"])
    sex, sey, sez = _transform(geom["strut_end"])
    fig.add_trace(go.Scatter3d(
        x=[ssx, sex], y=[ssy, sey], z=[ssz, sez],
        mode="lines",
        line=dict(color="#e67e22", width=3),
        showlegend=show_legend,
        name="Strut" if show_legend else None,
        hoverinfo="skip",
    ))

    # ---- Membrane surface
    X_m, Y_m, Z_m = _build_membrane_surface(geom)
    X_rot = np.zeros_like(X_m)
    Y_rot = np.zeros_like(Y_m)
    Z_rot = np.zeros_like(Z_m)
    for i in range(X_m.shape[0]):
        for j in range(X_m.shape[1]):
            xr, yr, zr = _transform((X_m[i, j], Y_m[i, j], Z_m[i, j]))
            X_rot[i, j] = xr
            Y_rot[i, j] = yr
            Z_rot[i, j] = zr

    fig.add_trace(go.Surface(
        x=X_rot, y=Y_rot, z=Z_rot,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.55,
        showscale=False,
        hoverinfo="skip",
    ))

    # ---- Edge cable: one trace, following the concave fabric edge
    sag_frac = _edge_sag_fraction()
    A = np.asarray(geom["corner_A"], dtype=float)
    B = np.asarray(geom["corner_B"], dtype=float)
    C = np.asarray(geom["corner_C"], dtype=float)
    D = np.asarray(geom["corner_D"], dtype=float)
    centre = (A + B + C + D) * 0.25

    cable_pts = []
    n_per_edge = 16
    for (p0, p1) in [(A, B), (B, C), (C, D), (D, A)]:
        pts = _concave_edge(p0, p1, centre, n_per_edge, sag_frac)
        cable_pts.extend(pts[:-1])
    cable_pts.append(A)

    cx, cy, cz = [], [], []
    for q in cable_pts:
        xr, yr, zr = _transform(q)
        cx.append(xr); cy.append(yr); cz.append(zr)

    fig.add_trace(go.Scatter3d(
        x=cx, y=cy, z=cz,
        mode="lines",
        line=dict(color="#f1c40f", width=3),
        showlegend=show_legend,
        name="Edge cables" if show_legend else None,
        hoverinfo="skip",
    ))

    # ---- Joint marker at the strut's anchor on the arm
    jx, jy, jz = _transform(geom["strut_end"])
    fig.add_trace(go.Scatter3d(
        x=[jx], y=[jy], z=[jz],
        mode="markers",
        marker=dict(color="#f1c40f", size=6, symbol="circle"),
        showlegend=False,
        hoverinfo="skip",
    ))


# =============================================================================
# TIERED HELIX ARRANGEMENT
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

    if geom.get("rib_radius_adjusted", False):
        st.session_state["ws_ch_rib_radius_adjusted"] = True
        st.session_state["ws_ch_rib_radius_used"] = geom.get("rib_radius_used", 0.0)
    else:
        st.session_state["ws_ch_rib_radius_adjusted"] = False

    fig = go.Figure()

    arrangement = st.session_state.get("ws_ch_arrangement", "single")

    col_top_z = col_h
    if arrangement == "tiered_helix":
        fl_h = float(st.session_state.get("ws_ch_first_leaf_height", col_h))
        lz_h = float(st.session_state.get("ws_ch_leaf_zone_height", 7.0))
        col_top_z = max(col_h, fl_h + lz_h)

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

    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="markers",
        marker=dict(color="#6ab0d4", size=8),
        name="Membrane",
    ))

    return apply_common_layout(fig, col_top_z)





