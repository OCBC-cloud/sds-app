"""Multi-Cone Roof — Stage 2 Lab test page.

Stage 2 builds the ribcage and the correct eave boundary polygon, then
solves the membrane with the saddle-span boundary pattern (anchors held,
subdivision nodes free, cable segments between anchors).

Geometry (client decisions, 2026-10-10):

  - Primary beam: parabolic arch, ends at ground, apex at mid-span.
  - Ground ellipse at z = 0, semi-axes span/2 (x) and mid_width/2 (y).
    The rib ground supports sit on this ellipse.
  - Ribs: parabolic arches, each through three points — the two ground
    supports (on the ground ellipse) and the peak at the primary beam
    crossing. Rib count = user's "Secondary count".
  - Rib positions along arc length, rule from the earlier session:
      toggle OFF: N ribs at equal arc-length fractions k/(N+1)
      toggle ON  (N >= 3): outer ribs at x = +/- (span/2 - 3),
                  interior ribs spread between them by x
      toggle ON  (N < 3):  behaves as OFF
  - Eave boundary: a polygon at z = eave_height through the points where
    each rib crosses that plane (one on +y, one on -y per rib), plus the
    two tips at x = +/- span/2, y = 0.  Closed loop.
  - Anchors: every vertex of the eave boundary polygon.
    anchor_count = 2 * N + 2  (derived, not a widget).
  - Every boundary segment is a cable segment.  Subdivision nodes
    between anchors lie on the straight chord (cable rule from the
    saddle span pattern).  The bow comes from the solve.

Solve (saddle span pattern, copied):

  - build_mesh_triangulated(
        boundary_loop, anchor_indices, segment_types=["cable"]*n,
        target_edge_length=L_avg, plan_plane=None,
        warp_q, weft_q, edge_q)
  - solve_fdm on points_initial.
  - solve_fdm_settled for reactions.

Ring height is FIXED at 7.0 m.  Ring diameter default 0.5 m.  Rings are
drawn as markers only — not yet meshed — Stage 3 meshes them.
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.mesh_triangulated import build_mesh_triangulated
from engine.form_finding import solve_fdm, solve_fdm_settled
from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
)


# --- Constants ---------------------------------------------------------------

RING_HEIGHT = 7.0
RING_SEGMENTS = 64
ELLIPSE_SEGMENTS = 200
RIB_SEGMENTS = 80
SUBDIVISIONS_PER_SEGMENT = 5     # anchors-to-anchor interpolation, saddle pattern

COL_MEMBRANE = "#4a7a9c"
COL_PERIMETER = "#f1c40f"
COL_ANCHOR = "#f39c12"
COL_RING = "#b0c4de"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_POLE = "#7a8a9a"
COL_GROUND = "#3a5a7a"


# --- Geometry helpers --------------------------------------------------------

def _ellipse_y(x, span, mid_width):
    """+y on the ground ellipse at station x.  Clamped to 0 outside."""
    a = span / 2.0
    b = mid_width / 2.0
    t = max(0.0, 1.0 - (x / a) ** 2)
    return b * math.sqrt(t)


def _ground_ellipse(span, mid_width, n):
    a = span / 2.0
    b = mid_width / 2.0
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    return np.column_stack([a * np.cos(t), b * np.sin(t),
                            np.zeros(n, dtype=float)])


def _rib_stations(n, optional_ends, span, x, s, total):
    """Rib station x positions (length n, ascending)."""
    if (not optional_ends) or n < 3:
        fracs = np.array([k / (n + 1.0) for k in range(1, n + 1)], dtype=float)
        return np.interp(fracs * total, s, x)
    x_target = span / 2.0 - 3.0
    return np.linspace(-x_target, +x_target, n)


def _rib_arch(rib_x, half_width, peak_z, eave_height, n):
    """Sample the rib parabola at z = eave_height.

    The rib is z(y) = peak_z * (1 - (y/half_width)^2).
    Return the y-value at which z = eave_height, or None if the rib
    never reaches that height (peak_z <= eave_height).
    """
    if peak_z <= eave_height:
        return None
    u2 = 1.0 - eave_height / peak_z
    if u2 < 0.0:
        return None
    return half_width * math.sqrt(u2)


def _rib_polyline(rib_x, half_width, peak_z, n):
    """Full rib polyline from ground support to ground support."""
    y = np.linspace(-half_width, +half_width, n)
    u = y / half_width
    z = peak_z * (1.0 - u ** 2)
    x = np.full_like(y, rib_x)
    return np.column_stack([x, y, z])


def _build_eave_polygon(rib_x, rib_half_width, rib_peak_z, eave_height,
                        span):
    """Closed polygon at z = eave_height.

    Walk:
      +y crossings, left -> right
      right tip at (+span/2, 0)
      -y crossings, right -> left
      left tip at (-span/2, 0)

    If a rib's peak_z <= eave_height, that rib does not cross the eave
    plane and contributes no anchors (its ground supports sit below).
    """
    plus = []      # (+y crossing, one per rib that reaches eave)
    minus = []     # (-y crossing)
    for i, xr in enumerate(rib_x):
        y_at = _rib_arch(float(xr), float(rib_half_width[i]),
                         float(rib_peak_z[i]), eave_height, 1)
        if y_at is None:
            continue
        plus.append((float(xr), +y_at, eave_height))
        minus.append((float(xr), -y_at, eave_height))

    pts = []
    for p in plus:
        pts.append(p)
    pts.append((+span / 2.0, 0.0, eave_height))
    for p in reversed(minus):
        pts.append(p)
    pts.append((-span / 2.0, 0.0, eave_height))

    return np.asarray(pts, dtype=float)


def _subdivide_loop_cable(loop, subdivisions_per_segment):
    """Build the boundary loop with subdivision nodes on the chord.

    Between every pair of adjacent anchors, insert
    subdivisions_per_segment nodes evenly spaced along the straight
    chord.  Returns:
      full_loop  - (M, 3) new loop with anchors and subdivisions
      anchor_idx - list of indices into full_loop that are anchors
      seg_types  - list of "cable" strings, one per anchor-to-anchor segment
    """
    n_a = loop.shape[0]
    full_loop = []
    anchor_idx = []
    for i in range(n_a):
        a = loop[i]
        b = loop[(i + 1) % n_a]
        anchor_idx.append(len(full_loop))
        full_loop.append(a)
        for k in range(1, subdivisions_per_segment + 1):
            f = k / (subdivisions_per_segment + 1.0)
            full_loop.append(a + (b - a) * f)
    full_loop = np.asarray(full_loop, dtype=float)
    seg_types = ["cable"] * n_a
    return full_loop, anchor_idx, seg_types


def _draw_ring_marker(fig, cx, cz, diameter):
    r = diameter / 2.0
    t = np.linspace(0.0, 2.0 * math.pi, RING_SEGMENTS)
    xs = cx + r * np.cos(t)
    ys = np.zeros_like(t)
    zs = cz + r * np.sin(t)
    fig.add_trace(go.Scatter3d(
        x=xs, y=ys, z=zs, mode="lines",
        line=dict(color=COL_RING, width=4),
        name=f"ring x={cx:+.2f}", showlegend=False, hoverinfo="skip",
    ))


# --- Page --------------------------------------------------------------------

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 2 — ribcage, ground ellipse, "
        "eave polygon, cable boundary. Rings still markers only.</p>",
        unsafe_allow_html=True,
    )

    # --- Widgets ------------------------------------------------------------
    c1, c2 = st.columns(2)
    with c1:
        span = st.number_input("Primary span (m)", 6.0, 60.0, 18.0, 0.5)
    with c2:
        apex = st.number_input("Primary apex (m)", 1.0, 30.0, 9.0, 0.5)

    c1, c2 = st.columns(2)
    with c1:
        mid_width = st.number_input("Mid-span width (m)", 6.0, 60.0, 18.0, 0.5)
    with c2:
        eave_height = st.number_input("Eave height (m)", 0.5, 10.0, 2.8, 0.1)

    c1, c2 = st.columns(2)
    with c1:
        ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 0.5, 0.1)
    with c2:
        curve_type = st.selectbox(
            "Curve type", ["parabolic", "circular", "catenary"], index=0
        )

    c1, c2 = st.columns(2)
    with c1:
        secondary_count = int(st.number_input("Secondary count", 2, 20, 3, 1))
    with c2:
        optional_ends = st.toggle("Optional ends", value=False)

    c1, c2 = st.columns(2)
    with c1:
        warp_q_input = st.number_input(
            "Warp pretension (kN/m)", 0.1, 100.0, 2.0, 0.1
        )
    with c2:
        weft_q_input = st.number_input(
            "Weft pretension (kN/m)", 0.1, 100.0, 2.0, 0.1
        )

    edge_q_input = st.number_input(
        "Edge cable pretension (kN/m, 0 = auto)", 0.0, 500.0, 0.0, 1.0,
    )

    # --- Primary beam curve --------------------------------------------------
    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    # --- Rib stations, widths, peaks ----------------------------------------
    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array(
        [_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float
    )

    # --- Eave boundary polygon ----------------------------------------------
    eave_loop = _build_eave_polygon(
        rib_x, rib_half_width, rib_peak_z, eave_height, span
    )
    n_anchors = eave_loop.shape[0]

    # --- Subdivision on cable chords ----------------------------------------
    boundary_loop, anchor_indices, seg_types = _subdivide_loop_cable(
        eave_loop, SUBDIVISIONS_PER_SEGMENT
    )

    # target_edge_length = mean boundary edge length (saddle span rule)
    bd = np.diff(np.vstack([boundary_loop, boundary_loop[:1]]), axis=0)
    bl = np.linalg.norm(bd, axis=1)
    L_avg = float(np.mean(bl)) if len(bl) else 1.0
    if L_avg < 1e-9:
        L_avg = 1.0
    target_len = L_avg

    # --- q values ------------------------------------------------------------
    warp_pre = float(warp_q_input)
    weft_pre = float(weft_q_input)
    warp_q = max(warp_pre, 0.1) * 1000.0
    weft_q = max(weft_pre, 0.1) * 1000.0

    if edge_q_input > 0.0:
        edge_q_scalar = float(edge_q_input) * 1000.0
    else:
        # Auto: membrane prestress times mean chord length.
        N_membrane = max(warp_q, weft_q)
        edge_q_scalar = N_membrane * L_avg
    edge_q_scalar = max(edge_q_scalar, 1.0)

    # --- Mesh ----------------------------------------------------------------
    mesh = build_mesh_triangulated(
        boundary_loop=boundary_loop,
        anchor_indices=anchor_indices,
        segment_types=seg_types,
        target_edge_length=target_len,
        plan_plane=None,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q_scalar,
    )

    points_initial = mesh["points_initial"]
    edges = mesh["edges"]
    fixed_indices = mesh["fixed_indices"]
    q = mesh["q"]
    triangles = mesh["triangles"]

    # --- Solve ---------------------------------------------------------------
    fdm = solve_fdm(points_initial.copy(), edges, fixed_indices, q)
    coords = fdm["coordinates"]
    residual_norm = float(fdm["residual_norm"])

    # --- Figure --------------------------------------------------------------
    fig = go.Figure()

    if len(triangles) > 0:
        tri = np.asarray(triangles, dtype=int)
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            name="membrane", showlegend=False, hoverinfo="skip",
        ))

    # Ground ellipse
    ge = _ground_ellipse(span, mid_width, ELLIPSE_SEGMENTS)
    ge_c = np.vstack([ge, ge[:1]])
    fig.add_trace(go.Scatter3d(
        x=ge_c[:, 0], y=ge_c[:, 1], z=ge_c[:, 2],
        mode="lines", line=dict(color=COL_GROUND, width=4),
        name="ground ellipse", showlegend=False, hoverinfo="skip",
    ))

    # Eave boundary polygon (closed)
    ec = np.vstack([eave_loop, eave_loop[:1]])
    fig.add_trace(go.Scatter3d(
        x=ec[:, 0], y=ec[:, 1], z=ec[:, 2],
        mode="lines", line=dict(color=COL_PERIMETER, width=6),
        name="eave polygon", showlegend=False, hoverinfo="skip",
    ))

    # Primary beam
    fig.add_trace(go.Scatter3d(
        x=xp, y=np.zeros_like(xp), z=zp,
        mode="lines", line=dict(color=COL_PRIMARY, width=7),
        name="primary beam", showlegend=False, hoverinfo="skip",
    ))

    # Ribs
    for i in range(len(rib_x)):
        pts = _rib_polyline(
            float(rib_x[i]), float(rib_half_width[i]),
            float(rib_peak_z[i]), RIB_SEGMENTS,
        )
        fig.add_trace(go.Scatter3d(
            x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
            mode="lines", line=dict(color=COL_RIB, width=5),
            name=f"rib x={rib_x[i]:+.2f}", showlegend=False, hoverinfo="skip",
        ))

    # Anchors
    if len(fixed_indices) > 0:
        fi = np.asarray(fixed_indices, dtype=int)
        fig.add_trace(go.Scatter3d(
            x=coords[fi, 0], y=coords[fi, 1], z=coords[fi, 2],
            mode="markers", marker=dict(color=COL_ANCHOR, size=4),
            name="anchors", showlegend=False, hoverinfo="skip",
        ))

    # Rings and poles at fixed height
    ring_x_positions = (-span / 6.0, +span / 6.0)
    for rx in ring_x_positions:
        _draw_ring_marker(fig, float(rx), RING_HEIGHT, float(ring_diameter))
        fig.add_trace(go.Scatter3d(
            x=[float(rx), float(rx)], y=[0.0, 0.0], z=[0.0, RING_HEIGHT],
            mode="lines", line=dict(color=COL_POLE, width=3),
            name=f"pole x={rx:+.2f}", showlegend=False, hoverinfo="skip",
        ))

    apply_common_layout(fig, apex)
    st.plotly_chart(fig, use_container_width=True)

    # --- Diagnostics ---------------------------------------------------------
    with st.expander("Diagnostics", expanded=False):
        st.write(f"Nodes: {mesh['diagnostics']['n_nodes']}")
        st.write(f"Edges: {mesh['diagnostics']['n_edges']}")
        st.write(f"Triangles: {mesh['diagnostics']['n_triangles']}")
        st.write(f"Fixed (anchors): {len(fixed_indices)}")
        st.write(f"Residual norm: {residual_norm:.6e}")
        st.write(f"Secondary count N: {secondary_count}")
        st.write(f"Anchor count = 2N+2: {n_anchors}")
        st.write(f"Subdivisions per segment: {SUBDIVISIONS_PER_SEGMENT}")
        st.write(f"Boundary nodes: {boundary_loop.shape[0]}")
        st.write(f"Mean boundary edge L_avg (m): {L_avg:.3f}")
        st.write("Rib stations x (m): " + ", ".join(f"{v:+.3f}" for v in rib_x))
        st.write("Rib half widths (m): " + ", ".join(f"{v:.3f}" for v in rib_half_width))
        st.write("Rib peak z (m): " + ", ".join(f"{v:.3f}" for v in rib_peak_z))
        st.write(
            "Eave crossing y (+/-) (m): "
            + ", ".join(
                f"{_rib_arch(float(rib_x[i]), float(rib_half_width[i]), float(rib_peak_z[i]), eave_height, 1):.3f}"
                for i in range(len(rib_x))
            )
        )
        st.write("Eave polygon vertices: " + str(eave_loop.shape[0]))
        st.write(f"Ring height (m, fixed): {RING_HEIGHT:.2f}")
        st.write(
            "Ring stations x (m): "
            + ", ".join(f"{v:+.3f}" for v in ring_x_positions)
        )
        st.write(f"Warp q: {warp_q:.2f}  |  Weft q: {weft_q:.2f}  |  Edge q: {edge_q_scalar:.2f}")
