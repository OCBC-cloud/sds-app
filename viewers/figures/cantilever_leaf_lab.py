# =============================================================================
# SDSe - Cantilever Leaf LAB Figure Builder
# =============================================================================
# Structural-analysis test case. Fixed spec:
#   column height    = 6.0 m
#   outreach         = 5.0 m
#   ribs per side    = 3  (=> 3 pairs)
#   middle rib       = 2.0 m left + 2.0 m right (half-width = 2.0 at t=0.5)
#   half-width law   = 2.0 * sin(pi*t)^0.7   (Option A)
#   rib tilt         = 0 deg  (flat ribs -> pure transverse)
#   arc radius       = 1.0 m  (gentle crown, sagitta = 0.5 m)
#   strut joint      = 3.0 m  (long backstay)
#   strut angle      = 42 deg
#
# Exposes the geometry as raw arrays (not just a figure) so the structural
# solver can consume the same mesh that is drawn.
# =============================================================================

import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from viewers.figures._shared import apply_common_layout


# =============================================================================
# FIXED LAB SPEC
# =============================================================================

LAB_COL_H         = 6.0
LAB_OUTREACH      = 5.0
LAB_RIBS_PER_SIDE = 3
LAB_HALF_WIDTH_MID = 2.0   # ensures half_w(0.5) = 2.0 exactly
LAB_RIB_TILT_DEG  = 0.0
LAB_ARC_R         = 1.0     # sagitta = 0.5 m
LAB_STRUT_JOINT   = 3.0
LAB_STRUT_ANGLE   = 42.0

N_BEAM = 80


# =============================================================================
# GEOMETRY (returns raw arrays)
# =============================================================================

def compute_lab_leaf_geometry():
    """
    Return a dict describing the lab test-case geometry.
    All coordinates in metres, origin at column base.
    """
    col_h    = LAB_COL_H
    outreach = LAB_OUTREACH
    ribs_per_side = LAB_RIBS_PER_SIDE
    arc_r    = LAB_ARC_R
    strut_j  = LAB_STRUT_JOINT

    # ---- Main beam (parabolic crown)
    t_beam = np.linspace(0.0, 1.0, N_BEAM)
    beam_x = outreach * t_beam
    beam_y = np.zeros_like(t_beam)
    # z = col_h + 4*S*t*(1-t),  S = arc_r * 0.5
    S = arc_r * 0.5
    beam_z = col_h + 4.0 * S * t_beam * (1.0 - t_beam)

    # ---- Rib stations (3 per side -> 3 rib pairs)
    rib_ts = np.linspace(0.08, 0.92, ribs_per_side)

    def half_width(t):
        # Exactly 2.0 at t = 0.5
        return LAB_HALF_WIDTH_MID * (math.sin(math.pi * t) ** 0.7)

    def tilt_rad(t):
        return math.radians(LAB_RIB_TILT_DEG) * (math.sin(math.pi * t) ** 0.7)

    # ---- Rib lines
    ribs = []
    for i, t in enumerate(rib_ts):
        idx = int(round(t * (N_BEAM - 1)))
        a_x = float(beam_x[idx])
        a_z = float(beam_z[idx])
        hw  = half_width(t)
        tl  = tilt_rad(t)
        tip_z = a_z + hw * math.tan(tl)
        ribs.append({
            "index": i,
            "t": float(t),
            "attach": (a_x, 0.0, a_z),
            "left_tip":  (a_x, -hw, tip_z),
            "right_tip": (a_x, +hw, tip_z),
            "half_width": hw,
            "length": math.sqrt(hw*hw + (hw*math.tan(tl))**2),
        })

    # ---- Curved strut attach point (beam parabola ∩ ray from strut joint)
    tan_a = math.tan(math.radians(LAB_STRUT_ANGLE))
    A_q = 4.0 * S / (outreach * outreach)
    B_q = tan_a - (4.0 * S / outreach)
    C_q = strut_j - col_h
    disc = B_q * B_q - 4.0 * A_q * C_q

    strut_attach_local = None
    if disc >= 0.0 and A_q > 1e-9:
        sq = math.sqrt(disc)
        x1 = (-B_q + sq) / (2.0 * A_q)
        x2 = (-B_q - sq) / (2.0 * A_q)
        cand = [x for x in (x1, x2) if 0.0 < x < outreach]
        if cand:
            strut_attach_local = cand[0]
    if strut_attach_local is None:
        strut_attach_local = outreach * 0.33

    idx_a = int(round((strut_attach_local / outreach) * (N_BEAM - 1)))
    idx_a = max(0, min(N_BEAM - 1, idx_a))
    strut_attach = (float(beam_x[idx_a]), 0.0, float(beam_z[idx_a]))
    strut_base   = (0.0, 0.0, strut_j)

    # ---- Membrane grid (24 x 24)
    n_u, n_v = 24, 24
    u_vals = np.linspace(0.02, 0.98, n_u)
    v_vals = np.linspace(-1.0, 1.0, n_v)
    X = np.zeros((n_u, n_v))
    Y = np.zeros((n_u, n_v))
    Z = np.zeros((n_u, n_v))
    for i, t in enumerate(u_vals):
        idx = int(round(t * (N_BEAM - 1)))
        bx  = float(beam_x[idx])
        bz  = float(beam_z[idx])
        hw  = half_width(t)
        tl  = tilt_rad(t)
        tip_z = bz + hw * math.tan(tl)
        for j, v in enumerate(v_vals):
            y_loc = v * hw
            z_edge = bz * (1 - abs(v)) + tip_z * abs(v)
            sag = 0.15 * hw * (1 - (2 * abs(v) - 1) ** 2)
            z_loc = z_edge - sag
            X[i, j] = bx
            Y[i, j] = y_loc
            Z[i, j] = z_loc

    return {
        "spec": {
            "column_height":  col_h,
            "outreach":       outreach,
            "ribs_per_side":  ribs_per_side,
            "half_width_mid": LAB_HALF_WIDTH_MID,
            "rib_tilt_deg":   LAB_RIB_TILT_DEG,
            "arc_radius":     arc_r,
            "strut_joint":    strut_j,
            "strut_angle":    LAB_STRUT_ANGLE,
        },
        "beam": {"x": beam_x, "y": beam_y, "z": beam_z},
        "ribs": ribs,
        "strut": {"attach": strut_attach, "base": strut_base},
        "membrane": {"X": X, "Y": Y, "Z": Z, "u": u_vals, "v": v_vals},
        "column": {"base": (0.0, 0.0, 0.0), "top": (0.0, 0.0, col_h)},
    }


def build_cantilever_leaf_lab_figure(geom):
    """Draw the lab test case from a geometry dict."""
    fig = go.Figure()

    col_h = geom["spec"]["column_height"]

    # ---- Column
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

    # ---- Beam spine
    b = geom["beam"]
    fig.add_trace(go.Scatter3d(
        x=b["x"], y=b["y"], z=b["z"],
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        name="Main beam",
    ))

    # ---- Ribs
    for rib in geom["ribs"]:
        ax, ay, az = rib["attach"]
        lx, ly, lz = rib["left_tip"]
        rx, ry, rz = rib["right_tip"]
        fig.add_trace(go.Scatter3d(
            x=[lx, ax, rx], y=[ly, ay, ry], z=[lz, az, rz],
            mode="lines",
            line=dict(color="#3498db", width=3),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ---- Membrane
    m = geom["membrane"]
    fig.add_trace(go.Surface(
        x=m["X"], y=m["Y"], z=m["Z"],
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.55,
        showscale=False,
        hoverinfo="skip",
    ))

    # ---- Strut
    sa = geom["strut"]["attach"]
    sb = geom["strut"]["base"]
    fig.add_trace(go.Scatter3d(
        x=[sa[0], sb[0]], y=[sa[1], sb[1]], z=[sa[2], sb[2]],
        mode="lines",
        line=dict(color="#e67e22", width=4),
        name="Curved strut",
    ))

    return apply_common_layout(fig, col_h)
