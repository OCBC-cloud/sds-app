"""Multi-Cone Roof — Stage 1 Lab test page (mesh only).

Scope of this file (per handover Section 3.9):
  1. Read widgets.
  2. Build primary beam curve (parabolic / circular / catenary).
  3. Arc-length parametrise the primary beam.
  4. Rib stations along arc length (Section 3.4).
  5. Rib widths (Section 3.5).
  6. Perimeter polyline (Section 3.8).
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

RING_HEIGHT_OFFSET = 1.5      # m, provisional drop below the primary beam
RING_SEGMENTS = 64            # circle resolution for the ring markers
TARGET_EDGE_DIVISOR = 40.0    # perimeter_length / this -> target_edge_length

COL_MEMBRANE = "#4a7a9c"
COL_PERIMETER = "#f1c40f"
COL_ANCHOR = "#f39c12"
COL_RING = "#b0c4de"
COL_PRIMARY = "#FF6B6B"


# --- Geometry helpers --------------------------------------------------------

def _rib_stations_arc_fractions(n, optional_ends, span, x, s, total):
    """Return rib stations as arc-length fractions (length n, ascending).

    Rule 3.4:
      - Optional-ends OFF: N ribs at fractions k/(N+1), k = 1..N.
      - Optional-ends ON (and N >= 3): the two outermost ribs sit at the
        arc-length fractions where x = +/-(span/2 - 3).  The remaining
        N-2 ribs spread evenly by arc length between them.
      - Optional-ends ON with N = 1 or 2 behaves as OFF.
    """
    if (not optional_ends) or n < 3:
        return np.array([k / (n + 1.0) for k in range(1, n + 1)], dtype=float)

    # Locate the arc-length fractions of the two blunting x positions.
    x_target = span / 2.0 - 3.0
    # np.interp wants ascending x; x from beam_curve is already ascending
    # (-span/2 -> +span/2).  s is cumulative arc length along that same x.
    frac_right = float(np.interp(x_target, x, s) / total)
    frac_left = float(np.interp(-x_target, x, s) / total)

    frac_left = max(0.0, min(1.0, frac_left))
    frac_right = max(0.0, min(1.0, frac_right))
    if frac_right <= frac_left:
        # Degenerate span; fall back to the OFF rule.
        return np.array([k / (n + 1.0) for k in range(1, n + 1)], dtype=float)

    interior = np.linspace(frac_left, frac_right, n)
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


def _perimeter_from_ribs(rib_x, rib_widths, eave_height):
    """Build the closed perimeter loop, rule 3.8.

    Walk:
      +y side  left -> right   (every rib's +y end)
      close across right end   (from rightmost +y to rightmost -y)
      -y side  right -> left   (every rib's -y end)
      close across left end    (from leftmost -y back to leftmost +y)

    For a sharp lens (optional-ends OFF) the leftmost and rightmost ribs are
    the extreme-x ribs, and their two endpoints are the tips.  For a rugby
    ball (optional-ends ON) the leftmost and rightmost ribs are the blunting
    ribs, and the closures are straight cross segments of their width.
    """
    n = len(rib_x)
    pts = []
    # +y side, left -> right
    for i in range(n):
        pts.append((rib_x[i], +rib_widths[i] / 2.0, eave_height))
    # close right end: rightmost +y -> rightmost -y (already have +y)
    pts.append((rib_x[-1], -rib_widths[-1] / 2.0, eave_height))
    # -y side, right -> left (skip rightmost, already added)
    for i in range(n - 2, -1, -1):
        pts.append((rib_x[i], -rib_widths[i] / 2.0, eave_height))
    # close left end: leftmost -y -> leftmost +y (start point)
    # (the start point is already index 0; the loop is closed implicitly)
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
        "Perimeter + membrane + ring markers.</p>",
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
    fracs = _rib_stations_arc_fractions(
        secondary_count, optional_ends, span, x, s, total
    )
    rib_x = np.interp(fracs * total, s, x)
    rib_z = np.interp(fracs * total, s, z)   # primary z at each rib
    rib_widths = _rib_widths(secondary_count, mid_width)

    # --- Perimeter -----------------------------------------------------------
    perimeter = _perimeter_from_ribs(rib_x, rib_widths, eave_height)

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

    # Perimeter (yellow line).
    fig.add_trace(
        go.Scatter3d(
            x=perimeter[:, 0], y=perimeter[:, 1], z=perimeter[:, 2],
            mode="lines",
            line=dict(color=COL_PERIMETER, width=6),
            name="perimeter",
            showlegend=False,
            hoverinfo="skip",
        )
    )
    # Close the perimeter visually.
    fig.add_trace(
        go.Scatter3d(
            x=[perimeter[-1, 0], perimeter[0, 0]],
            y=[perimeter[-1, 1], perimeter[0, 1]],
            z=[perimeter[-1, 2], perimeter[0, 2]],
            mode="lines",
            line=dict(color=COL_PERIMETER, width=6),
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

    # Ring markers (drawing only, Section 3.7).
    ring_fracs = (1.0 / 3.0, 2.0 / 3.0)
    for frac in ring_fracs:
        rx = np.interp(frac * total, s, x)
        rz = np.interp(frac * total, s, z)
        _draw_ring_marker(fig, float(rx), float(rz - RING_HEIGHT_OFFSET), float(ring_diameter))

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
        st.write(f"Perimeter length (m): {perimeter_length:.3f}")
        st.write(f"Target edge length (m): {target_edge_length:.3f}")
