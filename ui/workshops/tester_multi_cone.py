"""Multi-Cone Roof — Stage 1 Lab test page (mesh only).

Scope of this file (per handover Section 3.9):
  1. Read widgets.
  2. Build primary beam curve (parabolic / circular / catenary).
  3. Arc-length parametrise the primary beam.
  4. Rib stations along arc length (Section 3.4).
  5. Rib widths (Section 3.5).
  6. Perimeter polyline (Section 3.8), including the two tip points.
  7. target_edge_length = perimeter_length / 40.
  8. build_mesh_triangulated(..., segment_types=["beam"]*n_segments, ...).
  9. solve_fdm(points_initial, edges, fixed_indices, q).
 10. solve_fdm_settled(...) for reactions.
 11. Plotly draw: perimeter, membrane, anchors, two ring markers.
 12. Diagnostics expander.
 13. st.plotly_chart.

Open-question resolutions (handover Section 7):
  A — Primary beam ends sit at z = 0 (ground).  Only the perimeter z (eave
      height) enters the mesh; this choice affects the drawn primary curve
      and will drive Stage 2 beam drawing.
  B — The optional-ends toggle repositions the outermost two ribs to
      x = +/-(span/2 - 3) when ON.  It does NOT change the rib count N.

Perimeter tip rule (revised):
  With optional-ends OFF the perimeter reaches the full primary span at
  both ends.  Two tip points are inserted, one at (+span/2, 0) and one
  at (-span/2, 0), both at eave_height.  The three ribs sit inside this
  envelope.  This produces the pointed-lens (American football) outline
  described in handover Section 3.2.

  With optional-ends ON, the tips are the two blunting ribs at
  x = +/-(span/2 - 3).  There are no tip points beyond those ribs; the
  closures are straight segments across the rib width (rugby ball).

Stage 1 fix history:
  2026-10-10 — corrected the -y walk in _perimeter_from_ribs so all N
               ribs are included when optional-ends is OFF (the previous
               version skipped one rib, giving 7 perimeter points instead
               of 8).  Optional-ends ON still skips the rightmost rib's
               -y end because that point is the blunt closure.  Also
               corrected the optional-ends ON rib placement to land the
               outermost two ribs on exactly x = +/-(span/2 - 3) by
               interpolating directly in x rather than round-tripping
               through arc length.

Ring height:
  Ring height is FIXED at 7.0 m for this stage.  Not solver-decided, not
  provisional, not a widget.  The rings are drawn as markers at z = 7.0 m
  on the spine.  Stage 3 will mesh the rings at this fixed height.
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

RING_HEIGHT = 7.0             # m, FIXED for this stage (client decision)
RING_SEGMENTS = 64            # circle resolution for the ring markers
TARGET_EDGE_DIVISOR = 40.0    # perimeter_length / this -> target_edge_length

COL_MEMBRANE = "#4a7a9c"
COL_PERIMETER = "#f1c40f"
COL_ANCHOR = "#f39c12"
COL_RING = "#b0c4de"
COL_PRIMARY = "#FF6B6B"


# --- Geometry helpers --------------------------------------------------------

def _rib_stations(n, optional_ends, span, x, s, total):
    """Return rib station x positions (length n, ascending).

    Rule 3.4 (corrected):
      - Optional-ends OFF: N ribs at the N interior equal-arc-length
        divisions of the primary.  For a symmetric parabola these land
        at x = span/2 * cos(k*pi/(N+1)) analog, achieved here by
        interpolating the arc-length fractions k/(N+1) back to x.
      - Optional-ends ON (and N >= 3): the two outermost ribs sit at
        exactly x = +/-(span/2 - 3).  The remaining N-2 ribs spread
        evenly by arc length between them.  Placement is by direct x
        interpolation, so the outermost pair lands on the exact target.
      - Optional-ends ON with N = 1 or 2 behaves as OFF.

    Returns rib_x only.  The arc-length fraction is recomputed for the
    diagnostics by the caller.
    """
    if (not optional_ends) or n < 3:
        # OFF rule: equal arc-length fractions k/(N+1).
        fracs = np.array([k / (n + 1.0) for k in range(1, n + 1)], dtype=float)
        return np.interp(fracs * total, s, x)

    # ON rule.  Place the two outermost ribs exactly, then spread the
    # interior ribs by direct x interpolation between them.
    x_target = span / 2.0 - 3.0
    x_left = -x_target
    x_right = +x_target
    interior = np.linspace(x_left, x_right, n)
    return interior


def _rib_widths(n, mid_width):
    """Rule 3.5: middle rib is mid_width; each pair outward loses 1 m.

    Odd N:  one middle at mid-width, pairs outward subtract 1 m.
    Even N: two middles at mid-width, pairs outward subtract 1 m.
    Clamp: never below 1 m.
    """
    widths = np.empty(n, dtype=float)
    if n % 2 == 1:
        centre = n // 2
        for i in range(n):
            widths[i] = mid_width - abs(i - centre)
    else:
        centre_hi = n // 2
        centre_lo = centre_hi - 1
        for i in range(n):
            d = min(abs(i - centre_lo), abs(i - centre_hi))
            widths[i] = mid_width - d
    return np.maximum(widths, 1.0)


def _perimeter_from_ribs(rib_x, rib_widths, eave_height, span, optional_ends):
    """Build the closed perimeter loop, rule 3.8 (revised).

    Optional-ends OFF (sharp lens / football):
      +y side: every rib's +y end, left -> right (N points)
      right tip: (+span/2, 0)                        (1 point)
      -y side: every rib's -y end, right -> left     (N points)
      left tip: (-span/2, 0)                         (1 point)
      total: 2N + 2 points

    Optional-ends ON (rugby ball):
      +y side: every rib's +y end, left -> right (N points)
      right closure: rightmost rib's -y end       (1 point)
      -y side: ribs n-2 .. 0, right -> left       (N-1 points)
      left closure: leftmost rib's +y end (the start) is implicit.
      total: 2N points

    All points at z = eave_height.
    """
    n = len(rib_x)
    pts = []

    # +y side, left -> right (all ribs).
    for i in range(n):
        pts.append((rib_x[i], +rib_widths[i] / 2.0, eave_height))

    if not optional_ends:
        # Right tip at the full primary span.
        pts.append((+span / 2.0, 0.0, eave_height))
        # -y side, right -> left (ALL ribs).
        for i in range(n - 1, -1, -1):
            pts.append((rib_x[i], -rib_widths[i] / 2.0, eave_height))
        # Left tip at the full primary span.
        pts.append((-span / 2.0, 0.0, eave_height))
    else:
        # Blunt closure across the rightmost rib.
        pts.append((rib_x[-1], -rib_widths[-1] / 2.0, eave_height))
        # -y side, right -> left (skip rightmost, already placed).
        for i in range(n - 2, -1, -1):
            pts.append((rib_x[i], -rib_widths[i] / 2.0, eave_height))
        # Blunt closure across the leftmost rib (back to start).
        pts.append((rib_x[0], +rib_widths[0] / 2.0, eave_height))

    return np.array(pts, dtype=float)


def _draw_ring_marker(fig, cx, cz, diameter):
    """Append a flat circle marker at (cx, 0, cz) of given diameter."""
    r = diameter / 2.0
    t = np.linspace(0.0, 2.0 * math.pi, RING_SEGMENTS)
    xs = cx + r * np.cos(t)
    ys = 0.0 * np.ones_like(t)
    zs = cz + r * np.sin(t)
    fig.add_trace(
        go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode="lines",
            line=dict(color=COL_RING, width=3),
            name=f"ring x={cx:+.2f}",
            showlegend=False,
            hoverinfo="skip",
        )
    )


# --- Page --------------------------------------------------------------------

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 1 — mesh only. "
        "Perimeter + membrane + ring markers at fixed height.</p>",
        unsafe_allow_html=True,
    )

    # --- Widgets (Section 3.3) ----------------------------------------------
    with st.container():
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
            ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 3.0, 0.1)
        with c2:
            curve_type = st.selectbox(
                "Curve type", ["parabolic", "circular", "catenary"], index=0
            )

        c1, c2 = st.columns(2)
        with c1:
            secondary_count = int(
                st.number_input("Secondary count", 2, 20, 3, 1)
            )
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
            "Edge cable pretension (kN/m, 0 = auto)",
            0.0, 500.0, 0.0, 1.0,
        )

    # --- Primary beam curve --------------------------------------------------
    x = np.linspace(-span / 2.0, span / 2.0, 200)
    z = beam_curve(x, span, apex, curve_type)
    s, total = arclength_parametrisation(x, z)

    # --- Rib stations --------------------------------------------------------
    rib_x = _rib_stations(secondary_count, optional_ends, span, x, s, total)
    rib_z = np.interp(rib_x, x, z)          # primary z at each rib
    rib_widths = _rib_widths(secondary_count, mid_width)

    # --- Perimeter -----------------------------------------------------------
    perimeter = _perimeter_from_ribs(
        rib_x, rib_widths, eave_height, span, optional_ends
    )

    # Perimeter length (closed loop).
    deltas = np.diff(np.vstack([perimeter, perimeter[:1]]), axis=0)
    perimeter_length = float(np.sum(np.linalg.norm(deltas, axis=1)))
    target_edge_length = perimeter_length / TARGET_EDGE_DIVISOR

    # --- Mesh ----------------------------------------------------------------
    warp_q = float(warp_q_input) * 1000.0
    weft_q = float(weft_q_input) * 1000.0
    edge_q = 5000.0 if edge_q_input <= 0.0 else float(edge_q_input) * 1000.0

    n_segments = perimeter.shape[0]
    mesh = build_mesh_triangulated(
        boundary_loop=perimeter,
        anchor_indices=None,
        segment_types=["beam"] * n_segments,
        target_edge_length=target_edge_length,
        plan_plane=None,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q,
    )

    points_initial = mesh["points_initial"]
    edges = mesh["edges"]
    fixed_indices = mesh["fixed_indices"]
    q = mesh["q"]
    triangles = mesh["triangles"]

    # --- Solve ---------------------------------------------------------------
    fdm = solve_fdm(points_initial, edges, fixed_indices, q)
    settled = solve_fdm_settled(fdm["coordinates"], edges, fixed_indices, q)

    coords = fdm["coordinates"]
    residual_norm = float(fdm["residual_norm"])

    # --- Figure --------------------------------------------------------------
    fig = go.Figure()

    # Membrane (settled shape, engine triangles).
    if len(triangles) > 0:
        tri = np.asarray(triangles, dtype=int)
        fig.add_trace(
            go.Mesh3d(
                x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
                i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
                color=COL_MEMBRANE,
                opacity=0.55,
                flatshading=True,
                name="membrane",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Perimeter (yellow line, closed).
    perim_closed = np.vstack([perimeter, perimeter[:1]])
    fig.add_trace(
        go.Scatter3d(
            x=perim_closed[:, 0], y=perim_closed[:, 1], z=perim_closed[:, 2],
            mode="lines",
            line=dict(color=COL_PERIMETER, width=6),
            name="perimeter",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Anchors (amber markers).
    if len(fixed_indices) > 0:
        fi = np.asarray(fixed_indices, dtype=int)
        fig.add_trace(
            go.Scatter3d(
                x=coords[fi, 0], y=coords[fi, 1], z=coords[fi, 2],
                mode="markers",
                marker=dict(color=COL_ANCHOR, size=4),
                name="anchors",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Ring markers at the FIXED height of 7.0 m (Stage 1 decision).
    ring_x_positions = (-span / 6.0, +span / 6.0)   # one-third and two-thirds
    for rx in ring_x_positions:
        _draw_ring_marker(fig, float(rx), RING_HEIGHT, float(ring_diameter))

    apply_common_layout(fig, apex)
    st.plotly_chart(fig, use_container_width=True)

    # --- Diagnostics ---------------------------------------------------------
    with st.expander("Diagnostics", expanded=False):
        st.write(f"Nodes: {mesh['diagnostics']['n_nodes']}")
        st.write(f"Edges: {mesh['diagnostics']['n_edges']}")
        st.write(f"Triangles: {mesh['diagnostics']['n_triangles']}")
        st.write(f"Fixed: {mesh['diagnostics']['n_fixed']}")
        st.write(f"Residual norm: {residual_norm:.6e}")
        st.write("Rib stations x (m): " + ", ".join(f"{v:+.3f}" for v in rib_x))
        st.write("Rib widths (m): " + ", ".join(f"{v:.3f}" for v in rib_widths))
        st.write("Primary z at rib stations (m): " + ", ".join(f"{v:.3f}" for v in rib_z))
        st.write("Perimeter points: " + str(perimeter.shape[0]))
        st.write("Perimeter length (m): " + f"{perimeter_length:.3f}")
        st.write("Target edge length (m): " + f"{target_edge_length:.3f}")
        st.write(f"Ring height (m, fixed): {RING_HEIGHT:.2f}")
        st.write("Ring stations x (m): " + ", ".join(f"{v:+.3f}" for v in ring_x_positions))
