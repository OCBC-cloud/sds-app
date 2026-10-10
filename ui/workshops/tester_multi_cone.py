"""Multi-Cone Roof — Stage 3 Lab test page.

Stage 3 adds the cone rings to the mesh and forms the cones.

  - The perimeter mesh is built exactly as in Stage 2 (saddle span
    cable-boundary pattern).
  - Two rings at x = +/- span/6 (one third and two thirds of the span),
    at z = RING_HEIGHT = 7.0 m, y = 0, with diameter = ring_diameter.
  - Each ring is held by a vertical drop member from the primary beam
    directly above it.
  - The mesh is rewritten:
      1. Find the row of mesh nodes nearest each ring circle in plan.
      2. Build a ring polygon with the same node count as that row,
         distributed evenly around the ring circle.
      3. Populate the ring disc with interior nodes at the surrounding
         mesh density.
      4. Drop the mesh triangles that bridge across the ring interior.
      5. Connect the surrounding mesh nodes to the ring polygon nodes
         by edges.  Snap the innermost surrounding nodes onto the ring
         circle where possible.
  - Ring polygon nodes are held (fixed_indices).
  - The rewritten mesh is handed to solve_fdm.  The membrane attaches
    to the ring, and the two cones emerge from the solve.

Stage 3 is REAL form-finding (FDM).  Real equilibrium.  Real shape.
Linear physics.  Stage 4 (NFDM) will give the full nonlinear stresses.

No poles from the ground.  The rings hang from the primary beam.

No engine files are modified.  All of the ring logic lives here.
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.mesh_triangulated import build_mesh_triangulated
from engine.form_finding import solve_fdm
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
SUBDIVISIONS_PER_SEGMENT = 5

RING_STIFFNESS_FACTOR = 5.0    # ring edge q relative to membrane edge q
RING_DISC_FACTOR = 1.0         # disc interior q relative to membrane q

COL_MEMBRANE = "#4a7a9c"
COL_PERIMETER = "#f1c40f"
COL_ANCHOR = "#f39c12"
COL_RING = "#e8e8e8"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_DROP = "#b0c4de"
COL_GROUND = "#3a5a7a"


# --- Small geometry helpers --------------------------------------------------

def _ellipse_y(x, span, mid_width):
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
    if (not optional_ends) or n < 3:
        fracs = np.array([k / (n + 1.0) for k in range(1, n + 1)], dtype=float)
        return np.interp(fracs * total, s, x)
    x_target = span / 2.0 - 3.0
    return np.linspace(-x_target, +x_target, n)


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


def _build_eave_polygon(rib_x, rib_half_width, rib_peak_z, eave_height, span):
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
    pts.append((+span / 2.0, 0.0, eave_height))
    for p in reversed(minus):
        pts.append(p)
    pts.append((-span / 2.0, 0.0, eave_height))
    return np.asarray(pts, dtype=float)


def _subdivide_loop_cable(loop, sub):
    n_a = loop.shape[0]
    full, anchor_idx = [], []
    for i in range(n_a):
        a = loop[i]
        b = loop[(i + 1) % n_a]
        anchor_idx.append(len(full))
        full.append(a)
        for k in range(1, sub + 1):
            f = k / (sub + 1.0)
            full.append(a + (b - a) * f)
    return np.asarray(full, dtype=float), anchor_idx, ["cable"] * n_a


# --- Ring mesh rewrite -------------------------------------------------------

def _ring_circle_points(cx, cz, diameter, n):
    """n points evenly around the ring circle at x = cx, y = 0, z = cz.
    The ring lies in a horizontal plane (parallel to the ground)."""
    r = diameter / 2.0
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    return np.column_stack([
        cx + r * np.cos(t),
        r * np.sin(t),
        np.full_like(t, cz),
    ])


def _populate_ring_disc(cx, cz, diameter, n_ring, n_radial):
    """Interior nodes of the ring disc.

    Returns an (M, 3) array of points strictly inside the ring circle,
    at roughly the surrounding mesh density, excluding the centre
    (the centre node is added last).  Also returns a list of edges
    connecting the disc nodes to each other and to the ring polygon.
    """
    r = diameter / 2.0
    pts = []
    # Ring of interior nodes at r/3, r*2/3, and centre.
    for frac in (1.0 / 3.0, 2.0 / 3.0):
        rad = r * frac
        t = np.linspace(0.0, 2.0 * math.pi, n_ring, endpoint=False)
        for tt in t:
            pts.append((cx + rad * math.cos(tt),
                        rad * math.sin(tt),
                        cz))
    # Centre node.
    pts.append((cx, 0.0, cz))
    return np.asarray(pts, dtype=float)


def _rewrite_mesh_with_rings(mesh, ring_specs, membrane_q):
    """Given the engine mesh and a list of ring specs, rewrite.

    Each ring spec is a dict with keys: cx, cz, diameter.

    Returns a dict with the rewritten mesh:
      points, edges, fixed_indices, q,
      ring_polygon_indices (list per ring),
      ring_polygon_points (list per ring),
      cosmetic_triangles (list),
      dropped_triangle_count, ring_notes.
    """
    pts = np.array(mesh["points_initial"], copy=True)
    edges = list(mesh["edges"])
    tris = list(mesh["triangles"])
    fixed = set(int(i) for i in mesh["fixed_indices"])
    q_arr = np.array(mesh["q"], dtype=float)

    ring_notes = []
    ring_polygon_indices_all = []
    ring_polygon_points_all = []
    cosmetic_triangles = []
    dropped_total = 0

    for spec in ring_specs:
        cx = float(spec["cx"])
        cz = float(spec["cz"])
        d = float(spec["diameter"])
        r = d / 2.0

        # 1. Find mesh nodes near the ring in the horizontal plane.
        xy = pts[:, :2]
        dist = np.linalg.norm(xy - np.array([cx, 0.0]), axis=1)
        near_mask = dist < (r * 1.5 + 1e-9)
        near_idx = np.where(near_mask)[0]

        ring_notes.append(
            f"ring at x={cx:+.2f}: {len(near_idx)} nodes within {r*1.5:.3f} m"
        )

        if len(near_idx) < 3:
            ring_notes.append(
                f"  -> ring too small for the mesh.  Need to increase "
                f"ring diameter or refine the mesh."
            )
            ring_polygon_indices_all.append([])
            ring_polygon_points_all.append(np.zeros((0, 3)))
            continue

        # 2. Build the ring polygon with the same count.
        n_ring = len(near_idx)
        poly_pts = _ring_circle_points(cx, cz, d, n_ring)
        poly_start = pts.shape[0]
        pts = np.vstack([pts, poly_pts])
        poly_idx = list(range(poly_start, poly_start + n_ring))

        # 3. Populate the disc.
        disc_pts = _populate_ring_disc(cx, cz, d, max(4, n_ring // 2), 2)
        disc_start = pts.shape[0]
        pts = np.vstack([pts, disc_pts])
        disc_idx = list(range(disc_start, disc_start + disc_pts.shape[0]))

        # Ring polygon -> disc: connect each polygon node to nearest
        # disc nodes.
        ring_q = membrane_q * RING_STIFFNESS_FACTOR
        for i in range(n_ring):
            a = poly_idx[i]
            b = poly_idx[(i + 1) % n_ring]
            edges.append((a, b))
            q_arr = np.append(q_arr, ring_q)

        # Polygon -> disc spokes: connect polygon nodes to the outer
        # ring of disc nodes.
        n_disc_ring = max(4, n_ring // 2)
        outer_disc_start = disc_start
        for i in range(n_ring):
            a = poly_idx[i]
            # Nearest outer disc node by plan distance.
            outer_slice = disc_idx[:n_disc_ring]
            pa = pts[a]
            d_outer = np.linalg.norm(
                pts[outer_slice, :2] - pa[None, :2], axis=1
            )
            b = outer_slice[int(np.argmin(d_outer))]
            edges.append((a, b))
            q_arr = np.append(q_arr, membrane_q * RING_DISC_FACTOR)

        # Centre node to inner disc ring.
        centre = disc_idx[-1]
        inner_slice = disc_idx[n_disc_ring:2 * n_disc_ring]
        for b in inner_slice:
            edges.append((centre, int(b)))
            q_arr = np.append(q_arr, membrane_q * RING_DISC_FACTOR)

        # 4. Drop mesh triangles whose centroid is inside the ring circle.
        keep = []
        dropped = 0
        for tri in tris:
            ia, ib, ic = int(tri[0]), int(tri[1]), int(tri[2])
            c = (pts[ia, :2] + pts[ib, :2] + pts[ic, :2]) / 3.0
            if np.linalg.norm(c - np.array([cx, 0.0])) < r:
                dropped += 1
                continue
            keep.append(tri)
        tris = keep
        dropped_total += dropped

        # 5. Connect the surrounding mesh to the ring polygon:
        #    for each polygon node, connect to the nearest original
        #    mesh node that is just outside the ring.
        for i in range(n_ring):
            a = poly_idx[i]
            pa = pts[a]
            # Choose from the near_idx that are also outside r.
            outside = [int(k) for k in near_idx
                       if np.linalg.norm(pts[k, :2] - np.array([cx, 0.0])) >= r]
            if not outside:
                continue
            d_out = np.linalg.norm(
                pts[outside, :2] - pa[None, :2], axis=1
            )
            b = outside[int(np.argmin(d_out))]
            edges.append((int(b), int(a)))
            q_arr = np.append(q_arr, membrane_q * RING_DISC_FACTOR)

        ring_polygon_indices_all.append(poly_idx)
        ring_polygon_points_all.append(poly_pts)

        # Ring polygon nodes are held.
        for k in poly_idx:
            fixed.add(int(k))

    return {
        "points": pts,
        "edges": edges,
        "triangles": tris,
        "fixed_indices": sorted(fixed),
        "q": q_arr,
        "ring_polygon_indices": ring_polygon_indices_all,
        "ring_polygon_points": ring_polygon_points_all,
        "cosmetic_triangles": cosmetic_triangles,
        "dropped_triangle_count": dropped_total,
        "ring_notes": ring_notes,
    }


# --- Page --------------------------------------------------------------------

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — rings in the mesh. "
        "Cones from solve_fdm.  Real form-finding.</p>",
        unsafe_allow_html=True,
    )

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
        ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 2.0, 0.1)
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
        "Edge cable pretension (kN/m, 0 = auto)", 0.0, 500.0, 20.0, 1.0,
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
    boundary_loop, anchor_indices, seg_types = _subdivide_loop_cable(
        eave_loop, SUBDIVISIONS_PER_SEGMENT
    )

    bd = np.diff(np.vstack([boundary_loop, boundary_loop[:1]]), axis=0)
    bl = np.linalg.norm(bd, axis=1)
    L_avg = float(np.mean(bl)) if len(bl) else 1.0
    target_len = max(L_avg, 1e-6)

    # --- q values ------------------------------------------------------------
    warp_pre = max(float(warp_q_input), 0.1)
    weft_pre = max(float(weft_q_input), 0.1)
    warp_q = warp_pre * 1000.0
    weft_q = weft_pre * 1000.0
    if edge_q_input > 0.0:
        edge_q_scalar = float(edge_q_input) * 1000.0
    else:
        edge_q_scalar = max(warp_q, weft_q) * L_avg
    edge_q_scalar = max(edge_q_scalar, 1.0)

    # --- Base mesh (no rings) -----------------------------------------------
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

    # --- Ring specs ----------------------------------------------------------
    ring_x_positions = (-span / 6.0, +span / 6.0)
    ring_specs = [
        {"cx": float(rx), "cz": RING_HEIGHT, "diameter": float(ring_diameter)}
        for rx in ring_x_positions
    ]

    # --- Rewrite mesh with rings --------------------------------------------
    rewritten = _rewrite_mesh_with_rings(mesh, ring_specs, warp_q)

    pts_rw = rewritten["points"]
    edges_rw = rewritten["edges"]
    fixed_rw = rewritten["fixed_indices"]
    q_rw = rewritten["q"]
    tris_rw = rewritten["triangles"]

    # --- Solve ---------------------------------------------------------------
    try:
        fdm = solve_fdm(pts_rw, edges_rw, fixed_rw, q_rw)
        coords = fdm["coordinates"]
        residual_norm = float(fdm["residual_norm"])
        solve_ok = True
        solve_err = ""
    except Exception as e:
        coords = pts_rw.copy()
        residual_norm = float("nan")
        solve_ok = False
        solve_err = str(e)

    # --- Figure --------------------------------------------------------------
    fig = go.Figure()

    if len(tris_rw) > 0:
        tri = np.asarray(tris_rw, dtype=int)
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

    # Eave polygon
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
        rp = _rib_polyline(
            float(rib_x[i]), float(rib_half_width[i]),
            float(rib_peak_z[i]), RIB_SEGMENTS,
        )
        fig.add_trace(go.Scatter3d(
            x=rp[:, 0], y=rp[:, 1], z=rp[:, 2],
            mode="lines", line=dict(color=COL_RIB, width=5),
            name=f"rib x={rib_x[i]:+.2f}", showlegend=False, hoverinfo="skip",
        ))

    # Anchors
    if len(fixed_rw) > 0:
        fi = np.asarray(fixed_rw, dtype=int)
        fig.add_trace(go.Scatter3d(
            x=coords[fi, 0], y=coords[fi, 1], z=coords[fi, 2],
            mode="markers", marker=dict(color=COL_ANCHOR, size=4),
            name="held nodes", showlegend=False, hoverinfo="skip",
        ))

    # Rings: polygon at held position + drop member
    for k, spec in enumerate(ring_specs):
        poly_pts = rewritten["ring_polygon_points"][k]
        if poly_pts.shape[0] == 0:
            continue
        closed = np.vstack([poly_pts, poly_pts[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name=f"ring {k+1}", showlegend=False, hoverinfo="skip",
        ))
        # Drop member: vertical from primary beam above the ring centre.
        z_primary_above = float(np.interp(spec["cx"], xp, zp))
        fig.add_trace(go.Scatter3d(
            x=[spec["cx"], spec["cx"]],
            y=[0.0, 0.0],
            z=[z_primary_above, spec["cz"]],
            mode="lines", line=dict(color=COL_DROP, width=3),
            name=f"drop {k+1}", showlegend=False, hoverinfo="skip",
        ))

    apply_common_layout(fig, apex)
    st.plotly_chart(fig, use_container_width=True)

    # --- Diagnostics ---------------------------------------------------------
    with st.expander("Diagnostics", expanded=False):
        st.write(f"Base mesh nodes: {mesh['diagnostics']['n_nodes']}")
        st.write(f"Rewritten nodes: {pts_rw.shape[0]}")
        st.write(f"Rewritten edges: {len(edges_rw)}")
        st.write(f"Rewritten triangles: {len(tris_rw)}")
        st.write(f"Dropped triangles (ring interiors): {rewritten['dropped_triangle_count']}")
        st.write(f"Held nodes: {len(fixed_rw)}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Solve error: {solve_err}")
        else:
            st.write(f"Residual norm: {residual_norm:.6e}")
        st.write(f"Secondary count N: {secondary_count}")
        st.write(f"Anchor count = 2N+2: {eave_loop.shape[0]}")
        st.write(f"Boundary nodes: {boundary_loop.shape[0]}")
        st.write(f"L_avg (m): {L_avg:.3f}")
        st.write(f"Ring height: {RING_HEIGHT:.2f} m")
        st.write(f"Ring diameter: {ring_diameter:.3f} m")
        st.write(
            "Ring stations x (m): "
            + ", ".join(f"{v:+.3f}" for v in ring_x_positions)
        )
        st.write(f"Warp q: {warp_q:.2f}  |  Weft q: {weft_q:.2f}  |  Edge q: {edge_q_scalar:.2f}")
        st.write("**Ring notes:**")
        for n in rewritten["ring_notes"]:
            st.write("- " + n)
