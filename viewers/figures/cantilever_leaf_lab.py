# =============================================================================
# SDSe - Cantilever Leaf LAB Figure Builder (Dynamic)
# =============================================================================

import math
import numpy as np
import plotly.graph_objects as go
from viewers.figures._shared import apply_common_layout

N_BEAM = 80

def compute_lab_leaf_geometry(col_h=6.0, outreach=5.0, half_width_mid=2.0, 
                              rib_tilt_deg=0.0, arc_r=1.0, strut_joint=3.0, 
                              strut_angle=42.0, ribs_per_side=3):
    # ---- Main beam (parabolic crown)
    t_beam = np.linspace(0.0, 1.0, N_BEAM)
    beam_x = outreach * t_beam
    beam_y = np.zeros_like(t_beam)
    S = arc_r * 0.5
    beam_z = col_h + 4.0 * S * t_beam * (1.0 - t_beam)

    # ---- Rib stations
    rib_ts = np.linspace(0.08, 0.92, ribs_per_side)

    def half_width(t):
        return half_width_mid * (math.sin(math.pi * t) ** 0.7)

    def tilt_rad(t):
        return math.radians(rib_tilt_deg) * (math.sin(math.pi * t) ** 0.7)

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
            "index": i, "t": float(t),
            "attach": (a_x, 0.0, a_z),
            "left_tip":  (a_x, -hw, tip_z),
            "right_tip": (a_x, +hw, tip_z),
            "half_width": hw,
        })

    # ---- Strut attach point
    tan_a = math.tan(math.radians(strut_angle))
    A_q = 4.0 * S / (outreach * outreach)
    B_q = tan_a - (4.0 * S / outreach)
    C_q = strut_joint - col_h
    disc = B_q * B_q - 4.0 * A_q * C_q

    strut_attach_local = outreach * 0.33
    if disc >= 0.0 and A_q > 1e-9:
        sq = math.sqrt(disc)
        x1 = (-B_q + sq) / (2.0 * A_q)
        x2 = (-B_q - sq) / (2.0 * A_q)
        cand = [x for x in (x1, x2) if 0.0 < x < outreach]
        if cand:
            strut_attach_local = cand[0]

    idx_a = max(0, min(N_BEAM - 1, int(round((strut_attach_local / outreach) * (N_BEAM - 1)))))
    strut_attach = (float(beam_x[idx_a]), 0.0, float(beam_z[idx_a]))

    return {
        "spec": {
            "column_height": col_h, "outreach": outreach, "ribs_per_side": ribs_per_side,
            "half_width_mid": half_width_mid, "rib_tilt_deg": rib_tilt_deg,
            "arc_radius": arc_r, "strut_joint": strut_joint, "strut_angle": strut_angle,
        },
        "beam": {"x": beam_x, "y": beam_y, "z": beam_z},
        "ribs": ribs,
        "strut": {"attach": strut_attach, "base": (0.0, 0.0, strut_joint)},
        "column": {"base": (0.0, 0.0, 0.0), "top": (0.0, 0.0, col_h)},
    }

def build_cantilever_leaf_lab_figure(geom):
    fig = go.Figure()
    col_h = geom["spec"]["column_height"]
    
    # Column
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[0, col_h], mode="lines", line=dict(color="#2ecc71", width=10), name="Column"))
    # Beam
    b = geom["beam"]
    fig.add_trace(go.Scatter3d(x=b["x"], y=b["y"], z=b["z"], mode="lines", line=dict(color="#FF6B6B", width=8), name="Main beam"))
    # Ribs
    for rib in geom["ribs"]:
        ax, ay, az = rib["attach"]
        lx, ly, lz = rib["left_tip"]
        rx, ry, rz = rib["right_tip"]
        fig.add_trace(go.Scatter3d(x=[lx, ax, rx], y=[ly, ay, ry], z=[lz, az, rz], mode="lines", line=dict(color="#3498db", width=3), showlegend=False))
    # Strut
    sa = geom["strut"]["attach"]
    sb = geom["strut"]["base"]
    fig.add_trace(go.Scatter3d(x=[sa[0], sb[0]], y=[sa[1], sb[1]], z=[sa[2], sb[2]], mode="lines", line=dict(color="#e67e22", width=4), name="Strut"))
    
    return apply_common_layout(fig, col_h)
