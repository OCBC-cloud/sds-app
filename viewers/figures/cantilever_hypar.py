# =============================================================================
# SDSe - Cantilever Hypar Figure Builder
# =============================================================================
# Builds the 3D figure for the Cantilever Hypar variant.
# Called by viewers/results_viewer.py dispatcher.
#
# MEMBRANE-FIRST PRINCIPLE (per engine/PRINCIPLES_membrane.md):
#   1. Four corners A, B, C, D are defined first. Everything else
#      is measured from them.
#   2. Cables run STRAIGHT between the corners: A -> B -> C -> D -> A.
#   3. The fabric edge BOWS INWARD from each straight cable toward
#      the membrane centre. The membrane touches the cables only at
#      the four corners.
#   4. The surface between the four bowed edges is a saddle.
#   5. Steel members (arm, ribs, strut) are placed to suit the four
#      corners. They do not push the membrane anywhere.
#
# Plan view:
#   A = arm anchor end (near column)
#   C = arm tip end
#   B = rib tip, right side
#   D = rib tip, left side
#
# Heights:
#   A and C at anchor_z             (LOW)
#   B and D at anchor_z + rise      (HIGH)
#
# Placeholder inputs (see engine/PLACEHOLDERS.md):
#   - Column radius
#   - Arm arc radius
#   - Membrane edge sag fraction
#
# History:
#   2026-09-21 - First build.
#   2026-09-21 - Edge cable winding corrected.
#   2026-09-21 - Membrane rebuilt as a saddle with concave edges.
#   2026-09-21 - Rebuilt around four named corners A, B, C, D.
#                Cables drawn straight; fabric concave inward.
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
EDGE_SAG_FRACTION = 0.12

# How far the arm arcs above its endpoints (as a fraction of arm reach).
ARM_RISE_FRACTION = 0.20

# How far the rib tips rise above the rib anchor at the arm
# (as a fraction of rib reach).
RIB_RISE_FRACTION = 0.25


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
        "rib_bend_deg": float(st.session_state.get("ws_ch_rib_bend_deg", 15.0)),
        "column_radius": float(st.session_state.get("ws_ch_column_radius", 0.15)),
        "arm_arc_radius": float(st.session_state.get("ws_ch_arm_arc_radius", 4.0)),
    }


# =============================================================================
# GEOMETRY
# =============================================================================

def _compute_hypar_geometry(p):
    """
    Return a dict of arrays and points describing one Hypar mother object.

    Coordinate system:
      - Origin (0, 0, 0) at base of column.
      - Column runs vertically up Z.
      - Arm runs from A (0, 0, anchor_z) outward in +Y to C.
      - Ribs run left and right in ±X from the arm's midpoint.
    """
    col_h = p["column_height"]
    reach = p["arm_reach"]
    anchor_frac = p["anchor_fraction"]
    rib_reach = p["rib_reach"]
    rib_bend_deg = p["rib_bend_deg"]
    arc_r = p["arm_arc_radius"]

    anchor_z = col_h * anchor_frac

    # ---- Arm arc: from A (0, 0, anchor_z) to C (0, reach, anchor_z),
    #      arcing upward in the middle.
    n_arm = 80
    t_arm = np.linspace(0.0, 1.0, n_arm)
    arm_y = reach * t_arm
    arm_x = np.zeros_like(t_arm)

    arm_rise = reach * ARM_RISE_FRACTION
    arm_z = anchor_z + 4.0 * arm_rise * t_arm * (1.0 - t_arm)

    # Arm midpoint (arc apex)
    mid_idx = n_arm // 2
    mid_x = float(arm_x[mid_idx])
    mid_y = float(arm_y[mid_idx])
    mid_z = float(arm_z[mid_idx])

    # ---- Ribs: from the arm's midpoint outward in ±X.
    #      Each rib arcs upward so its tip sits higher than the mid_z.
    n_rib = 40
    t_rib = np.linspace(0.0, 1.0, n_rib)
    rib_rise = rib_reach * RIB_RISE_FRACTION

    right_rib_x = rib_reach * t_rib
    right_rib_y = np.full(n_rib, mid_y)
    right_rib_z = mid_z + 4.0 * rib_rise * t_rib * (1.0 - t_rib)

    left_rib_x = -rib_reach * t_rib
    left_rib_y = np.full(n_rib, mid_y)
    left_rib_z = mid_z + 4.0 * rib_rise * t_rib * (1.0 - t_rib)

    # ---- Four membrane corners
    corner_A = np.array([0.0, 0.0, anchor_z])                    # LOW
    corner_C = np.array([0.0, reach, anchor_z])                   # LOW
    corner_B = np.array([rib_reach, mid_y, mid_z + rib_rise])     # HIGH
    corner_D = np.array([-rib_reach, mid_y, mid_z + rib_rise])    # HIGH

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
        "left_rib_x": left_rib_x,
        "left_rib_y": left_rib_y,
        "left_rib_z": left_rib_z,
        "right_rib_x": right_rib_x,
        "right_rib_y": right_rib_y,
        "right_rib_z": right_rib_z,
        "strut_start": strut_start,
        "strut_end": strut_end,
        "corner_A": corner_A,
        "corner_B": corner_B,
        "corner_C": corner_C,
        "corner_D": corner_D,
    }


# =============================================================================
# MEMBRANE EDGE AND SURFACE
# =============================================================================

def _concave_edge(p0, p1, centre, n_pts, sag_frac):
    """
    Return n_pts points along the fabric edge from p0 to p1,
    bowed inward toward the membrane centre by sag_frac of edge length.

    The cables run straight from p0 to p1. The fabric edge bows inward
    from that straight line. The two match only at p0 and p1.
    """
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
    """
    Build the membrane as a Coons patch bounded by four concave edges.

    Corners are A, B, C, D. Cables run straight A->B->C->D->A.
    Fabric edges bow inward from those cables.
    """
    A = np.asarray(geom["corner_A"], dtype=float)
    B = np.asarray(geom["corner_B"], dtype=float)
    C = np.asarray(geom["corner_C"], dtype=float)
    D = np.asarray(geom["corner_D"], dtype=float)

    centre = (A + B + C + D) * 0.25

    n_edge = max(n_u, n_v)
    # Four fabric edges, each concave inward
    edge_AB = _concave_edge(A, B, centre, n_edge, EDGE_SAG_FRACTION)
    edge_BC = _concave_edge(B, C, centre, n_edge, EDGE_SAG_FRACTION)
    edge_CD = _concave_edge(C, D, centre, n_edge, EDGE_SAG_FRACTION)
    edge_DA = _concave_edge(D, A, centre, n_edge, EDGE_SAG_FRACTION)

    X = np.zeros((n_u, n_v))
    Y = np.zeros((n_u, n_v))
    Z = np.zeros((n_u, n_v))

    # Coons patch. Parameterise u along the AB-CD direction (from the
    # A/B side to the D/C side) and v along the DA-BC direction.
    # Actually use: u from A-side to C-side (AB edge to CD edge),
    # v from A-side to C-side along the other pair.
    # Simpler approach: u along the AB edge (A->B), v from the AB edge
    # to the DC edge (crossing the saddle diagonally).
    #
    # Better: bilinear Coons patch.
    #   u -> A..B and D..C
    #   v -> A..D and B..C
    # Left pair edges: AB (v=0), DC reversed (v=1)
    # Cross pair edges: AD (u=0), BC (u=1)
    edge_AD = edge_DA[::-1]  # from A to D
    edge_DC_rev = edge_CD[::-1]  # from D to C

    for i, u in enumerate(np.linspace(0.0, 1.0, n_u)):
        P_left = edge_AB[i]        # point on AB at u
        P_right = edge_DC_rev[i]   # point on DC at u (D->C)

        for j, v in enumerate(np.linspace(0.0, 1.0, n_v)):
            P_top = edge_AD[j]     # point on AD at v (A->D)
            P_bottom = edge_BC[j]  # point on BC at v (B->C)

            # Coons blending
            S = (P_left * (1.0 - v) + P_right * v)
            T = (P_top * (1.0 - u) + P_bottom * u)
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

    # ---- Left rib
    lx, ly, lz = [], [], []
    for i in range(len(geom["left_rib_x"])):
        xr, yr, zr = _transform(
            (geom["left_rib_x"][i], geom["left_rib_y"][i], geom["left_rib_z"][i])
        )
        lx.append(xr); ly.append(yr); lz.append(zr)

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
        xr, yr, zr = _transform(
            (geom["right_rib_x"][i], geom["right_rib_y"][i], geom["right_rib_z"][i])
        )
        rx.append(xr); ry.append(yr); rz.append(zr)

    fig.add_trace(go.Scatter3d(
        x=rx, y=ry, z=rz,
        mode="lines",
        line=dict(color="#3498db", width=4),
        showlegend=False,
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

    # ---- Edge cables (straight between corners) + fabric edge (concave)
    A = geom["corner_A"]
    B = geom["corner_B"]
    C = geom["corner_C"]
    D = geom["corner_D"]
    centre = (np.asarray(A) + np.asarray(B)
              + np.asarray(C) + np.asarray(D)) * 0.25

    # Straight cables A->B->C->D->A
    cable_pts = [A, B, C, D, A]
    cx, cy, cz = [], [], []
    for q in cable_pts:
        xr, yr, zr = _transform(q)
        cx.append(xr); cy.append(yr); cz.append(zr)

    fig.add_trace(go.Scatter3d(
        x=cx, y=cy, z=cz,
        mode="lines",
        line=dict(color="#f1c40f", width=2),
        showlegend=show_legend,
        name="Edge cables" if show_legend else None,
        hoverinfo="skip",
    ))

    # Concave fabric edges (thin dotted) to show the fabric boundary
    fabric_pts = []
    for (p0, p1) in [(A, B), (B, C), (C, D), (D, A)]:
        fabric_pts.extend(_concave_edge(p0, p1, centre, 10, EDGE_SAG_FRACTION))

    fx, fy, fz = [], [], []
    for q in fabric_pts:
        xr, yr, zr = _transform(q)
        fx.append(xr); fy.append(yr); fz.append(zr)

    fig.add_trace(go.Scatter3d(
        x=fx, y=fy, z=fz,
        mode="lines",
        line=dict(color="#f1c40f", width=1, dash="dot"),
        showlegend=False,
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

    fig = go.Figure()

    arrangement = st.session_state.get("ws_ch_arrangement", "single")

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
