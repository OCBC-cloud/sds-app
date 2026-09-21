# =============================================================================
# SDSe - Cantilever Hypar Figure Builder
# =============================================================================
# Builds the 3D figure for the Cantilever Hypar variant.
# Called by viewers/results_viewer.py dispatcher.
#
# MEMBRANE-FIRST PRINCIPLE (per engine/PRINCIPLES_membrane.md):
#   The membrane is the hero. The steel follows.
#
#   1. The four membrane corners are defined first. Everything else
#      is measured from them.
#   2. The membrane is form-found as a saddle between those corners.
#      Each of the four edges is a concave arc bowing inward toward
#      the membrane centre. The interior is a smooth saddle surface.
#   3. The membrane touches the arm and ribs ONLY at the four
#      corners. It does not drape over any structural member.
#   4. Edge cables follow the same concave arcs as the membrane edges.
#
# Corners (in plan, X is arm direction, Y is rib direction):
#   corner_anchor : (0,         0,       anchor_z)   LOW
#   corner_tip    : (reach,     0,       anchor_z)   LOW
#   corner_left   : (mid_x,  -rib_reach, mid_z+rise) HIGH
#   corner_right  : (mid_x,  +rib_reach, mid_z+rise) HIGH
#
# Placeholder inputs (see engine/PLACEHOLDERS.md):
#   - Column radius: draws the column thickness.
#   - Arm arc radius: draws the arm curve.
#   - Membrane edge sag (10-15%): placeholder for the FDM result.
#
# History:
#   2026-09-21 - First build.
#   2026-09-21 - Edge cable winding order corrected.
#   2026-09-21 - Membrane rebuilt as a saddle with concave edges.
#                Flat bilinear patch replaced.
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

# PLACEHOLDER VALUE - replace with FDM result.
# See engine/PLACEHOLDERS.md.
EDGE_SAG_FRACTION = 0.10


# =============================================================================
# PARAMETER READERS
# =============================================================================

def _read_params():
    """Read all Hypar parameters from session state into one dict."""
    p = {
        "column_height": float(st.session_state.get("ws_ch_column_height", 10.0)),
        "arm_reach": float(st.session_state.get("ws_ch_arm_reach", 6.0)),
        "anchor_fraction": float(st.session_state.get("ws_ch_anchor_fraction", 0.65)),
        "rib_reach": float(st.session_state.get("ws_ch_rib_reach", 3.0)),
        "rib_bend_deg": float(st.session_state.get("ws_ch_rib_bend_deg", 15.0)),
        "column_radius": float(st.session_state.get("ws_ch_column_radius", 0.15)),
        "arm_arc_radius": float(st.session_state.get("ws_ch_arm_arc_radius", 4.0)),
    }
    return p


# =============================================================================
# GEOMETRY
# =============================================================================

def _compute_hypar_geometry(p):
    """Return a dict describing one Hypar mother object."""
    col_h = p["column_height"]
    reach = p["arm_reach"]
    anchor_frac = p["anchor_fraction"]
    rib_reach = p["rib_reach"]
    rib_bend_deg = p["rib_bend_deg"]
    arc_r = p["arm_arc_radius"]

    anchor_z = col_h * anchor_frac

    # ---- Arm arc
    n_arm = 80
    t_arm = np.linspace(0.0, 1.0, n_arm)
    arm_x = reach * t_arm
    rise = arc_r * 0.5
    arm_z = anchor_z + 4.0 * rise * t_arm * (1.0 - t_arm)
    arm_y = np.zeros_like(t_arm)

    mid_idx = n_arm // 2
    mid_x = arm_x[mid_idx]
    mid_y = arm_y[mid_idx]
    mid_z = arm_z[mid_idx]

    # ---- Ribs
    n_rib = 40
    t_rib = np.linspace(0.0, 1.0, n_rib)
    rib_rise = rib_reach * math.tan(math.radians(rib_bend_deg))

    left_rib_x = np.full(n_rib, mid_x)
    left_rib_y = -rib_reach * t_rib
    left_rib_z = mid_z + 4.0 * rib_rise * t_rib * (1.0 - t_rib)

    right_rib_x = np.full(n_rib, mid_x)
    right_rib_y = rib_reach * t_rib
    right_rib_z = mid_z + 4.0 * rib_rise * t_rib * (1.0 - t_rib)

    left_tip = (mid_x, -rib_reach, mid_z + rib_rise)
    right_tip = (mid_x, rib_reach, mid_z + rib_rise)

    # ---- Structural anchor (strut crossing)
    anchor_x = reach * 0.15
    t_anchor = anchor_x / reach
    anchor_z_on_arm = anchor_z + 4.0 * rise * t_anchor * (1.0 - t_anchor)

    strut_start = (0.0, 0.0, col_h)
    strut_end = (anchor_x, 0.0, anchor_z_on_arm)

    # ---- Membrane four corners (the membrane's supports)
    corner_anchor = np.array([0.0, 0.0, anchor_z])           # LOW
    corner_tip = np.array([reach, 0.0, anchor_z])            # LOW
    corner_left = np.array(left_tip)                          # HIGH
    corner_right = np.array(right_tip)                        # HIGH

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
# MEMBRANE SURFACE (saddle with concave edges)
# =============================================================================

def _concave_edge(p0, p1, centre, n_pts, sag_frac):
    """
    Return a list of n_pts points along the edge from p0 to p1, bowed
    inward toward the membrane centre by sag_frac of edge length.
    """
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    centre = np.asarray(centre, dtype=float)

    edge_vec = p1 - p0
    edge_len = float(np.linalg.norm(edge_vec))
    if edge_len < 1e-9:
        return [p0.copy() for _ in range(n_pts)]

    sag = sag_frac * edge_len

    # Direction from midpoint toward centre (inward bow).
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
        # Parabolic weight, zero at both ends, max at middle.
        w = 4.0 * t * (1.0 - t)
        pts.append(base + inward_dir * sag * w)
    return pts


def _build_membrane_saddle(geom, n_u=32, n_v=32):
    """
    Build a saddle membrane between the four corners.

    The membrane's boundary is four concave edges (each bows inward
    toward the centre). The interior is a Coons-style surface that
    matches those edges.
    """
    c_a = np.asarray(geom["corner_anchor"], dtype=float)   # LOW
    c_t = np.asarray(geom["corner_tip"], dtype=float)      # LOW
    c_l = np.asarray(geom["corner_left"], dtype=float)     # HIGH
    c_r = np.asarray(geom["corner_right"], dtype=float)    # HIGH

    centre = (c_a + c_t + c_l + c_r) * 0.25

    # Boundary edges, each concave inward
    n_edge = max(n_u, n_v)
    edge_at = _concave_edge(c_a, c_t, centre, n_edge, EDGE_SAG_FRACTION)  # u=0 edge
    edge_bt = _concave_edge(c_l, c_r, centre, n_edge, EDGE_SAG_FRACTION)  # u=1 edge
    edge_al = _concave_edge(c_a, c_l, centre, n_edge, EDGE_SAG_FRACTION)  # v=0 edge
    edge_tr = _concave_edge(c_t, c_r, centre, n_edge, EDGE_SAG_FRACTION)  # v=1 edge

    X = np.zeros((n_u, n_v))
    Y = np.zeros((n_u, n_v))
    Z = np.zeros((n_u, n_v))

    for i, u in enumerate(np.linspace(0.0, 1.0, n_u)):
        # Points along u-edges (the two "top" and "bottom" edges)
        eu = edge_al[i]   # point on edge a->l at u
        fu = edge_tr[i]   # point on edge t->r at u

        for j, v in enumerate(np.linspace(0.0, 1.0, n_v)):
            # Points along v-edges (the two "left" and "right" edges)
            gv = edge_at[j]   # point on edge a->t at v
            hv = edge_bt[j]   # point on edge l->r at v

            # Coons patch interpolation
            A = eu * (1.0 - v) + fu * v
            B = gv * (1.0 - u) + hv * u
            C = (c_a * (1.0 - u) * (1.0 - v)
                 + c_t * u * (1.0 - v)
                 + c_l * (1.0 - u) * v
                 + c_r * u * v)
            pt = A + B - C

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

    # ---- Arm
    ax, ay, az = [], [], []
    for i in range(len(geom["arm_x"])):
        xv = geom["arm_x"][i] * scale
        yv = geom["arm_y"][i] * scale
        zv = _scale_z(geom["arm_z"][i])
        xr, yr = _rot(xv, yv)
        ax.append(xr); ay.append(yr); az.append(zv)

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
        lx.append(xr); ly.append(yr); lz.append(zv)

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
        rx.append(xr); ry.append(yr); rz.append(zv)

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

    # ---- Membrane surface (saddle with concave edges)
    X_m, Y_m, Z_m = _build_membrane_saddle(geom)
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

    # ---- Edge cables along the membrane's four concave edges
    c_a = geom["corner_anchor"]
    c_t = geom["corner_tip"]
    c_l = geom["corner_left"]
    c_r = geom["corner_right"]
    centre = (
        np.asarray(c_a) + np.asarray(c_t)
        + np.asarray(c_l) + np.asarray(c_r)
    ) * 0.25

    boundary_edges = [
        (c_a, c_t, centre),
        (c_t, c_r, centre),
        (c_r, c_l, centre),
        (c_l, c_a, centre),
    ]

    ecx, ecy, ecz = [], [], []
    n_per_edge = 12
    for (p0, p1, ctr) in boundary_edges:
        pts = _concave_edge(p0, p1, ctr, n_per_edge, EDGE_SAG_FRACTION)
        for q in pts:
            xv = q[0] * scale
            yv = q[1] * scale
            zv = _scale_z(q[2])
            xr, yr = _rot(xv, yv)
            ecx.append(xr); ecy.append(yr); ecz.append(zv)

    fig.add_trace(go.Scatter3d(
        x=ecx, y=ecy, z=ecz,
        mode="lines",
        line=dict(color="#f1c40f", width=3, dash="dot"),
        showlegend=show_legend,
        name="Edge cables" if show_legend else None,
        hoverinfo="skip",
    ))

    # ---- Joint marker at the structural anchor
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





