# =============================================================================
# SDSe - Multi-Cone Roof Viewer
# =============================================================================
# Builds the 3D figure for the Multi-Cone Cluster variant.
#
# Reads all inputs from session state under the "ws_mc_" prefix.
# The mesh is built by engine/SDSe_mesh_builder.py.
#
#   Inputs          read from session state
#   Geometry        eave perimeter from rib stations, cone rings along
#                   the primary beam by arc length
#   Mesh            SDSe_mesh_rings (perimeter + ring holes)
#   Solve           solve_fdm, with:
#                     - only structural anchors held (eave corners
#                       + ring polygon nodes + ring centres + beam tops)
#                     - every intermediate perimeter node fully free
#                       (real cable behaviour)
#                     - anisotropic warp/weft blend on interior edges
#                     - direct edge cable q from the slider
#
# Signature matches the FIGURE_REGISTRY contract:
#   - no arguments
#   - returns a plotly.graph_objects.Figure
#
# History:
#   First SDSe-only version. Mesh build delegated to
#   engine/SDSe_mesh_builder.py.
#   Renamed SDSe_mesh_rings_spine to SDSe_mesh_rings.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm
from engine.SDSe_mesh_builder import (
    SDSe_mesh_rings,
    SDSe_blend_q_per_edge,
)
from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
)


# =============================================================================
# COLOURS
# =============================================================================

RIB_SEGMENTS = 80

COL_MEMBRANE = "#4a7a9c"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"


# =============================================================================
# SESSION STATE HELPER
# =============================================================================

def _get(key, default=None):
    """Read a Multi-Cone session-state value by short key."""
    return st.session_state.get("ws_mc_" + key, default)


# =============================================================================
# GEOMETRY HELPERS
# =============================================================================

def _ellipse_y(x, span, mid_width):
    a = span / 2.0
    b = mid_width / 2.0
    t = max(0.0, 1.0 - (x / a) ** 2)
    return b * math.sqrt(t)


def _rib_stations(n, optional_ends, span, x, s, total):
    if (not optional_ends) or n < 3:
        fracs = np.array([k / (n + 1.0) for k in range(1, n + 1)], dtype=float)
        return np.interp(fracs * total, s, x)
    xt = span / 2.0 - 3.0
    return np.linspace(-xt, +xt, n)


def _rib_arch_y_at_eave(peak_z, half_width, eave_height):
    if peak_z <= eave_height:
        return None
    u2 = 1.0 - eave_height / peak_z
    if u2 < 0.0:
        return None
    return half_width * math.sqrt(u2)


def _rib_polyline(rib_x, half_width, peak_z, n):
    y = np.linspace(-half_width, +half_width, n)
    u = y / half_width
    z = peak_z * (1.0 - u ** 2)
    x = np.full_like(y, rib_x)
    return np.column_stack([x, y, z])


def _tip_x_at_eave(span, apex, eave_height, curve_type):
    if apex <= eave_height:
        return span / 2.0
    x_fine = np.linspace(0.0, span / 2.0, 2000)
    z_fine = beam_curve(x_fine, span, apex, curve_type)
    idx = np.where(z_fine >= eave_height)[0]
    if len(idx) == 0:
        return span / 2.0
    return float(x_fine[idx[-1]])


def _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height, tip_x):
    plus, minus = [], []
    for i, xr in enumerate(rib_x):
        y_at = _rib_arch_y_at_eave(
            float(rib_peak_z[i]), float(rib_half_width[i]), eave_height
        )
        if y_at is None:
            continue
        plus.append((float(xr), +y_at, eave_height))
        minus.append((float(xr), -y_at, eave_height))
    pts = list(plus)
    pts.append((+tip_x, 0.0, eave_height))
    for p in reversed(minus):
        pts.append(p)
    pts.append((-tip_x, 0.0, eave_height))
    return np.asarray(pts, dtype=float)


def _subdivide_polygon(anchors, subdivisions):
    n_a = anchors.shape[0]
    loop = []
    anchor_idx = []
    for i in range(n_a):
        a = anchors[i]
        b = anchors[(i + 1) % n_a]
        anchor_idx.append(len(loop))
        for k in range(subdivisions):
            f = k / float(subdivisions)
            loop.append(a + (b - a) * f)
    return np.asarray(loop, dtype=float), anchor_idx


def _cone_arc_positions(n_cones, spacing, total):
    if n_cones < 1:
        raise ValueError("Number of cones must be at least 1.")
    mid = total / 2.0
    if n_cones % 2 == 1:
        half = (n_cones - 1) // 2
        ks = [0]
        for i in range(1, half + 1):
            ks.append(+i)
            ks.append(-i)
    else:
        half = n_cones // 2
        ks = []
        for i in range(half):
            k = i + 0.5
            ks.append(+k)
            ks.append(-k)
    positions = [mid + k * spacing for k in ks]
    for p in positions:
        if p < 0.0 or p > total:
            raise ValueError(
                "Ring position %.3f m falls outside the primary span "
                "of %.3f m. Reduce spacing or cone count." % (p, total)
            )
    return sorted(positions)


# =============================================================================
# PUBLIC FIGURE BUILDER
# =============================================================================

def build_multi_cone_roof():
    """
    Build the 3D figure for the Multi-Cone Cluster variant.

    Reads all inputs from session state (prefix "ws_mc_").
    Returns a plotly Figure. No arguments.
    """
    # ---- Read inputs ------------------------------------------------------
    span = float(_get("span", 25.0))
    apex = float(_get("apex", 9.0))
    mid_width = float(_get("mid_width", 18.0))
    eave_height = float(_get("eave_height", 2.8))
    curve_type = str(_get("curve_type", "parabolic"))
    secondary_count = int(_get("secondary_count", 3))
    optional_ends = bool(_get("optional_ends", False))
    subdivisions = int(_get("subdivisions_per_edge", 17))

    number_of_cones = int(_get("number_of_cones", 3))
    cone_spacing = float(_get("cone_spacing", 5.0))
    ring_diameter = float(_get("ring_diameter", 1.0))
    ring_clearance = float(_get("ring_clearance", 1.0))

    warp_q = max(float(_get("warp_pretension", 1.0)), 0.1) * 1000.0
    weft_q = max(float(_get("weft_pretension", 1.0)), 0.1) * 1000.0
    edge_q_scalar = max(float(_get("edge_cable_pretension", 25.0)), 0.1) * 1000.0

    # ---- Primary beam curve ----------------------------------------------
    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array(
        [_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float
    )

    # ---- Cone ring placement ---------------------------------------------
    s_rings = _cone_arc_positions(number_of_cones, cone_spacing, total_p)
    ring_specs = []
    for s_val in s_rings:
        x_val = float(np.interp(s_val, s_p, xp))
        bz_val = float(np.interp(s_val, s_p, zp))
        rz_val = bz_val - float(ring_clearance)
        ring_specs.append({
            "cx": x_val, "cy": 0.0, "cz": rz_val,
            "r": float(ring_diameter) / 2.0,
            "beam_z": bz_val,
        })

    # ---- Eave perimeter ---------------------------------------------------
    tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
    anchors = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, tip_x
    )
    perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
    bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
    L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
    target_len = max(L_avg, 1e-6)

    # ---- Mesh build via the shared SDSe engine ---------------------------
    built = SDSe_mesh_rings(
        perimeter_loop=perimeter_loop,
        anchor_idx=anchor_idx,
        ring_specs=ring_specs,
        eave_height=eave_height,
        target_len=target_len,
    )

    pts = built["points"]
    edges = built["edges"]
    boundary_edge_set = built["boundary_edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]

    pts_2d = pts[:, :2]
    warp_dir = np.array([1.0, 0.0])
    q_interior = SDSe_blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q)

    q = np.empty(len(edges), dtype=float)
    for k, (i, j) in enumerate(edges):
        key = (i, j) if i < j else (j, i)
        if key in boundary_edge_set:
            q[k] = edge_q_scalar
        else:
            q[k] = q_interior[k]

    try:
        fdm = solve_fdm(pts, edges, fixed, q)
        coords = fdm["coordinates"]
    except Exception as e:
        coords = pts.copy()
        st.warning("Multi-Cone solver failed: " + str(e))

    # ---- Build figure -----------------------------------------------------
    fig = go.Figure()

    if len(tris) > 0:
        tri = np.asarray(tris, dtype=int)
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            name="membrane", showlegend=False, hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter3d(
        x=xp, y=np.zeros_like(xp), z=zp,
        mode="lines", line=dict(color=COL_PRIMARY, width=7),
        name="primary beam", showlegend=False, hoverinfo="skip",
    ))

    for i in range(len(rib_x)):
        rp = _rib_polyline(
            float(rib_x[i]), float(rib_half_width[i]),
            float(rib_peak_z[i]), RIB_SEGMENTS,
        )
        fig.add_trace(go.Scatter3d(
            x=rp[:, 0], y=rp[:, 1], z=rp[:, 2],
            mode="lines", line=dict(color=COL_RIB, width=5),
            name="rib", showlegend=False, hoverinfo="skip",
        ))

    for k, idx_list in enumerate(built["ring_indices"]):
        pp = coords[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name="ring", showlegend=False, hoverinfo="skip",
        ))
        centre_i = built["centre_indices"][k]
        beam_i = built["beam_top_indices"][k]
        cx, cy, cz = coords[centre_i]
        for poly_i in idx_list:
            fig.add_trace(go.Scatter3d(
                x=[cx, coords[poly_i, 0]],
                y=[cy, coords[poly_i, 1]],
                z=[cz, coords[poly_i, 2]],
                mode="lines", line=dict(color=COL_SPOKE, width=2),
                name="spoke", showlegend=False, hoverinfo="skip",
            ))
        bx, by, bz = coords[beam_i]
        fig.add_trace(go.Scatter3d(
            x=[cx, bx], y=[cy, by], z=[cz, bz],
            mode="lines", line=dict(color=COL_DROP, width=4),
            name="drop", showlegend=False, hoverinfo="skip",
        ))

    return apply_common_layout(fig, apex)


# =============================================================================
# END OF viewers/figures/multi_cone_roof.py
# =============================================================================
