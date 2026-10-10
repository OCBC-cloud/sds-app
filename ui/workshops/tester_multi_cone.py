"""Multi-Cone Roof — Stage 3 Lab test page.

Build order (client direction):

  1. Outer perimeter polygon.  Anchors at rib crossings plus two tips.
     anchor_count = 2 * N + 2  (8 for N = 3).
     The two tips are where the primary beam crosses eave height, not
     the extremes of the ground ellipse.
  2. Subdivide every anchor-to-anchor edge into `subdivisions` equal
     parts.  Widget, 5 to 25, default 11.
  3. Ring polygons.  Node count = the number of mesh nodes within one
     ring radius of the ring circle.  No widget.  Placed at
     z = RING_HEIGHT = 7.0 m.
  4. Build the mesh between the perimeter (at eave height) and the ring
     polygons (at 7.0 m).  Interior nodes on a plan grid.  z by
     distance-weight rule.  scipy Delaunay.  Holes dropped.
  5. Ring polygon nodes and perimeter anchors are held.
  6. Every boundary edge (perimeter anchor-to-anchor including
     subdivisions, and ring polygon edges) uses edge_q_scalar.
     Every interior edge uses warp_q.
  7. solve_fdm on the shaped mesh.

Fixes in this version (2026-10-10):
  - Ring polygon node count from the mesh, not a widget.
  - Perimeter tips at the primary-beam-crosses-eave point.
  - Edge cable as a real member: boundary q = edge_q_scalar.
  - Diagnostics report the count used, the tip x positions, and the
    boundary q / interior q split.

No engine files are modified.  The engine build_mesh_triangulated is
NOT used for the cone mesh — it takes one closed boundary and cannot
take holes.  The cone mesh is built here with scipy.spatial.Delaunay.
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding import solve_fdm
from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
)


RING_HEIGHT = 7.0
ELLIPSE_SEGMENTS = 200
RIB_SEGMENTS = 80

COL_MEMBRANE = "#4a7a9c"
COL_PERIMETER = "#f1c40f"
COL_ANCHOR = "#f39c12"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_DROP = "#b0c4de"
COL_GROUND = "#3a5a7a"


# --- Basic helpers -----------------------------------------------------------

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
    """x where the primary beam crosses eave height.

    For a parabolic beam the primary beam has z = apex * (1 - (2x/span)^2).
    Setting z = eave gives |x| = (span/2) * sqrt(1 - eave/apex).
    For other curve types, look up on a fine sampling.
    """
    if apex <= eave_height:
        return span / 2.0
    x_fine = np.linspace(0.0, span / 2.0, 2000)
    z_fine = beam_curve(x_fine, span, apex, curve_type)
    # Find the largest x where z >= eave (approaching from the top).
    idx = np.where(z_fine >= eave_height)[0]
    if len(idx) == 0:
        return span / 2.0
    return float(x_fine[idx[-1]])


def _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height,
                         tip_x):
    """Anchors at rib crossings plus two tips at +/- tip_x."""
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


# --- Mesh build --------------------------------------------------------------

def _point_in_polygon(x, y, poly):
    n = poly.shape[0]
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i, 0], poly[i, 1]
        xj, yj = poly[j, 0], poly[j, 1]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi
            if x < xint:
                inside = not inside
        j = i
    return inside


def _inside_any_ring(xy, rings):
    for (cx, cy, r) in rings:
        if (xy[0] - cx) ** 2 + (xy[1] - cy) ** 2 < r * r:
            return True
    return False


def _build_cone_mesh(perimeter_loop, anchor_idx, ring_centres_radii,
                      eave_height, target_len):
    """
    Build the mesh between the perimeter (at eave) and the ring polygons
    (at RING_HEIGHT).

    1. Plan-grid interior nodes for the fabric.
    2. z by distance-weight rule.
    3. Delaunay triangulation on plan positions.
    4. Holes dropped where centroid or any vertex lies inside a ring.
    5. Ring polygon nodes determined by the mesh: for each ring, count
       the fabric nodes within 2 * ring radius of the ring centre.
       That count drives the polygon vertex count.
    """
    from scipy.spatial import Delaunay

    poly_xy = perimeter_loop[:, :2]

    # --- Interior grid in plan ------------------------------------------
    xmin = float(np.min(perimeter_loop[:, 0]))
    xmax = float(np.max(perimeter_loop[:, 0]))
    ymin = float(np.min(perimeter_loop[:, 1]))
    ymax = float(np.max(perimeter_loop[:, 1]))

    h = float(target_len)
    xs = np.arange(xmin + 0.5 * h, xmax, h)
    ys = np.arange(ymin + 0.5 * h, ymax, h)

    interior_xy = []
    for x in xs:
        for y in ys:
            if not _point_in_polygon(x, y, poly_xy):
                continue
            if _inside_any_ring((x, y), ring_centres_radii):
                continue
            interior_xy.append((float(x), float(y)))

    # --- z for interior nodes -------------------------------------------
    def _z_at(x, y):
        d_ring = float("inf")
        for (cx, cy, r) in ring_centres_radii:
            d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) - r
            if d < d_ring:
                d_ring = d
        d_ring = max(d_ring, 0.0)
        d_perim = float(np.min(np.linalg.norm(
            poly_xy - np.array([x, y]), axis=1
        )))
        denom = d_ring + d_perim
        if denom < 1e-9:
            return float(RING_HEIGHT)
        w = d_perim / denom
        return float(RING_HEIGHT + (eave_height - RING_HEIGHT) * w)

    # --- Determine ring polygon node count from the fabric mesh ---------
    # Count fabric grid nodes within one ring diameter of each ring centre.
    ring_node_counts = []
    for (cx, cy, r) in ring_centres_radii:
        cnt = 0
        for (x, y) in interior_xy:
            d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if d <= 2.0 * r:
                cnt += 1
        cnt = max(cnt, 6)
        cnt = min(cnt, 32)
        ring_node_counts.append(cnt)

    # --- Build ring polygons with the derived counts --------------------
    ring_polys = []
    ring_indices = []
    all_pts_list = [tuple(p) for p in perimeter_loop]
    n_perimeter = len(all_pts_list)

    for k, (cx, cy, r) in enumerate(ring_centres_radii):
        n_poly = ring_node_counts[k]
        t = np.linspace(0.0, 2.0 * math.pi, n_poly, endpoint=False)
        poly = np.column_stack([
            cx + r * np.cos(t),
            cy + r * np.sin(t),
            np.full(n_poly, RING_HEIGHT, dtype=float),
        ])
        start = len(all_pts_list)
        for p in poly:
            all_pts_list.append(tuple(p))
        ring_indices.append(list(range(start, start + n_poly)))
        ring_polys.append(poly)

    # --- Interior fabric nodes ------------------------------------------
    for (x, y) in interior_xy:
        all_pts_list.append((x, y, _z_at(x, y)))

    all_pts = np.asarray(all_pts_list, dtype=float)
    pts_2d = all_pts[:, :2]

    # --- Delaunay, drop holes -------------------------------------------
    tri = Delaunay(pts_2d)
    triangles = []
    for simplex in tri.simplices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        cen = (pts_2d[a] + pts_2d[b] + pts_2d[c]) / 3.0
        if not _point_in_polygon(cen[0], cen[1], poly_xy):
            continue
        if _inside_any_ring(cen, ring_centres_radii):
            continue
        if (_inside_any_ring(pts_2d[a], ring_centres_radii)
                or _inside_any_ring(pts_2d[b], ring_centres_radii)
                or _inside_any_ring(pts_2d[c], ring_centres_radii)):
            continue
        triangles.append((a, b, c))

    # --- Edges with boundary / interior classification ------------------
    boundary_edge_set = set()
    for idx_list in ring_indices:
        n_poly = len(idx_list)
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            key = (a, b) if a < b else (b, a)
            boundary_edge_set.add(key)

    # Perimeter boundary edges: consecutive nodes in the perimeter loop,
    # plus the closing edge.
    for i in range(n_perimeter):
        j = (i + 1) % n_perimeter
        key = (i, j) if i < j else (j, i)
        boundary_edge_set.add(key)

    all_edge_set = set()
    for (a, b, c) in triangles:
        for (p, q) in ((a, b), (b, c), (c, a)):
            key = (p, q) if p < q else (q, p)
            all_edge_set.add(key)
    # ring polygon edges may not appear in triangles (they are the hole),
    # add them explicitly so they exist as members
    for key in boundary_edge_set:
        all_edge_set.add(key)
    edges = sorted(all_edge_set)

    # --- Fixed: perimeter anchors + every ring polygon vertex ----------
    fixed = set(int(i) for i in anchor_idx)
    for idx_list in ring_indices:
        for i in idx_list:
            fixed.add(int(i))

    return {
        "points": all_pts,
        "edges": edges,
        "boundary_edges": boundary_edge_set,
        "triangles": triangles,
        "fixed_indices": sorted(fixed),
        "ring_indices": ring_indices,
        "ring_node_counts": ring_node_counts,
        "n_perimeter": n_perimeter,
        "n_interior": len(interior_xy),
    }


# --- Page --------------------------------------------------------------------

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — double-cone mesh, "
        "edge cable member, ring polygons from the mesh.</p>",
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

    subdivisions = int(st.number_input(
        "Subdivisions per edge", 5, 25, 11, 1
    ))

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

    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array(
        [_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float
    )

    tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)

    anchors = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, tip_x
    )
    perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)

    bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
    L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
    target_len = max(L_avg, 1e-6)

    ring_x_positions = (-span / 6.0, +span / 6.0)
    r_ring = float(ring_diameter) / 2.0
    ring_centres_radii = [(float(rx), 0.0, r_ring) for rx in ring_x_positions]

    built = _build_cone_mesh(
        perimeter_loop, anchor_idx, ring_centres_radii,
        eave_height, target_len,
    )

    pts = built["points"]
    edges = built["edges"]
    boundary_edge_set = built["boundary_edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]

    warp_q = max(float(warp_q_input), 0.1) * 1000.0
    weft_q = max(float(weft_q_input), 0.1) * 1000.0
    if edge_q_input > 0.0:
        edge_q_scalar = float(edge_q_input) * 1000.0
    else:
        edge_q_scalar = max(warp_q, weft_q) * target_len
    edge_q_scalar = max(edge_q_scalar, 1.0)

    # --- q per edge: boundary edges use edge_q, interior use warp_q -----
    q = np.empty(len(edges), dtype=float)
    for k, (i, j) in enumerate(edges):
        key = (i, j) if i < j else (j, i)
        if key in boundary_edge_set:
            q[k] = edge_q_scalar
        else:
            q[k] = warp_q

    # --- Solve ----------------------------------------------------------
    try:
        fdm = solve_fdm(pts, edges, fixed, q)
        coords = fdm["coordinates"]
        residual_norm = float(fdm["residual_norm"])
        solve_ok = True
        solve_err = ""
    except Exception as e:
        coords = pts.copy()
        residual_norm = float("nan")
        solve_ok = False
        solve_err = str(e)

    # --- Figure ---------------------------------------------------------
    fig = go.Figure()

    if len(tris) > 0:
        tri = np.asarray(tris, dtype=int)
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            name="membrane", showlegend=False, hoverinfo="skip",
        ))

    ge = _ground_ellipse(span, mid_width, ELLIPSE_SEGMENTS)
    ge_c = np.vstack([ge, ge[:1]])
    fig.add_trace(go.Scatter3d(
        x=ge_c[:, 0], y=ge_c[:, 1], z=ge_c[:, 2],
        mode="lines", line=dict(color=COL_GROUND, width=4),
        name="ground ellipse", showlegend=False, hoverinfo="skip",
    ))

    pc = np.vstack([perimeter_loop, perimeter_loop[:1]])
    fig.add_trace(go.Scatter3d(
        x=pc[:, 0], y=pc[:, 1], z=pc[:, 2],
        mode="lines", line=dict(color=COL_PERIMETER, width=5),
        name="perimeter", showlegend=False, hoverinfo="skip",
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
            name=f"rib x={rib_x[i]:+.2f}", showlegend=False, hoverinfo="skip",
        ))

    if len(fixed) > 0:
        fi = np.asarray(fixed, dtype=int)
        fig.add_trace(go.Scatter3d(
            x=coords[fi, 0], y=coords[fi, 1], z=coords[fi, 2],
            mode="markers", marker=dict(color=COL_ANCHOR, size=4),
            name="held nodes", showlegend=False, hoverinfo="skip",
        ))

    for k, idx_list in enumerate(built["ring_indices"]):
        pp = coords[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name=f"ring {k+1}", showlegend=False, hoverinfo="skip",
        ))
        cx = ring_x_positions[k]
        z_up = float(np.interp(cx, xp, zp))
        fig.add_trace(go.Scatter3d(
            x=[cx, cx], y=[0.0, 0.0], z=[z_up, RING_HEIGHT],
            mode="lines", line=dict(color=COL_DROP, width=3),
            name=f"drop {k+1}", showlegend=False, hoverinfo="skip",
        ))

    apply_common_layout(fig, apex)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Diagnostics", expanded=False):
        st.write(f"Outer anchors: {anchors.shape[0]}")
        st.write(f"Perimeter tip x (m): +/-{tip_x:.4f}")
        st.write(f"Subdivisions per edge: {subdivisions}")
        st.write(f"Perimeter nodes: {perimeter_loop.shape[0]}")
        st.write(f"Total mesh nodes: {pts.shape[0]}")
        st.write(f"Mesh edges: {len(edges)}")
        st.write(f"Boundary edges: {len(boundary_edge_set)}")
        st.write(f"Mesh triangles: {len(tris)}")
        st.write(f"Held nodes: {len(fixed)}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Solve error: {solve_err}")
        else:
            st.write(f"Residual norm: {residual_norm:.6e}")
        st.write(f"Target edge length: {target_len:.4f}")
        st.write(f"Warp q: {warp_q:.2f}")
        st.write(f"Weft q: {weft_q:.2f}")
        st.write(f"Edge q (boundary): {edge_q_scalar:.2f}")
        st.write(f"Ring height: {RING_HEIGHT:.2f} m")
        st.write(f"Ring diameter: {ring_diameter:.3f} m")
        st.write(f"Ring stations x: " +
                 ", ".join(f"{v:+.3f}" for v in ring_x_positions))
        st.write("Ring node counts (from mesh): " +
                 ", ".join(str(c) for c in built["ring_node_counts"]))
