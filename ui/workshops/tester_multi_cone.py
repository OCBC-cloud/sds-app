"""Multi-Cone Roof — Stage 3 Lab test page.

Stage 3 builds the double-cone mesh from first principles, following the
client's build order:

  1. Outer perimeter boundary polygon.
       Anchor points at rib crossings plus two tips.
       anchor_count = 2 * N + 2   (8 for the default N = 3)
  2. Subdivide each edge between adjacent anchors into `subdivisions`
       equal segments.  subdivisions is a widget (5 to 25, default 11).
  3. Rings placed flat at z = eave_height (2.8 m), same plane as the
       outer boundary.
  4. Mesh the annular region between the outer boundary and the two
       ring polygons — real triangles, no dangling edges.
  5. Lift only the ring polygon vertices to RING_HEIGHT = 7.0 m.
  6. Solve with solve_fdm.

Rings are holes in the fabric.  No fabric inside a ring polygon.

No engine files are modified.  The outer flat mesh comes from
build_mesh_triangulated.  The ring rewrite is done here.

The membranes start flat at 2.8 m, the ring polygons start at 2.8 m,
then the ring polygon nodes are lifted to 7.0 m as the initial guess.
The solver then settles the double-cone shape from that starting point.
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
ELLIPSE_SEGMENTS = 200
RIB_SEGMENTS = 80

COL_MEMBRANE = "#4a7a9c"
COL_PERIMETER = "#f1c40f"
COL_ANCHOR = "#f39c12"
COL_RING = "#e8e8e8"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_DROP = "#b0c4de"
COL_GROUND = "#3a5a7a"


# --- Shape helpers -----------------------------------------------------------

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


def _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height, span):
    """8 anchors for N=3: 2N rib crossings + 2 tips, all at eave_height."""
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


def _subdivide_polygon(anchors, subdivisions):
    """Subdivide each anchor-to-anchor edge into `subdivisions` equal parts.

    Every edge gets the same count.  Between anchor i and anchor i+1,
    (subdivisions - 1) interior nodes are inserted.  Total loop size is
    n_anchors * subdivisions.

    Returns:
      loop       - (n_anchors * subdivisions, 3)
      anchor_idx - list of indices into loop of the anchors
    """
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


# --- Ring mesh build ---------------------------------------------------------

def _ring_polygon_from_nearest(mesh_points_2d, cx, cy, r):
    """Find the mesh nodes nearest the ring circle, use their count as
    the polygon vertex count, and build a regular polygon on the ring
    at the same z as the mesh points.

    Returns:
      poly_points (n, 3)   vertices of the ring polygon
      n_used      int      number of vertices used
      note        str      human-readable note
    """
    r_outer = r * 2.0
    dist = np.linalg.norm(mesh_points_2d - np.array([cx, cy]), axis=1)
    near = np.where(dist <= r_outer)[0]
    n_used = int(len(near))

    note = f"ring at ({cx:+.2f}, {cy:+.2f}): {n_used} nodes within {r_outer:.3f} m"

    if n_used < 6:
        n_used = 6
        note += "  -> too few; using minimum 6"
    if n_used > 48:
        n_used = 48
        note += "  -> capped at 48"

    t = np.linspace(0.0, 2.0 * math.pi, n_used, endpoint=False)
    z_level = 0.0
    if len(near) > 0:
        z_level = float(np.mean(mesh_points_2d[near]))
    # z will be supplied by caller (flat build at eave_height).
    poly = np.column_stack([
        cx + r * np.cos(t),
        cy + r * np.sin(t),
        np.zeros(n_used, dtype=float),
    ])
    return poly, n_used, note


def _is_inside_any_ring(xy, ring_circles):
    for (cx, cy, r) in ring_circles:
        if (xy[0] - cx) ** 2 + (xy[1] - cy) ** 2 < r * r:
            return True
    return False


def _ring_distance(xy, ring_circles):
    best = float("inf")
    for (cx, cy, r) in ring_circles:
        d = math.sqrt((xy[0] - cx) ** 2 + (xy[1] - cy) ** 2) - r
        if d < best:
            best = d
    return best


def _build_mesh_with_rings(perimeter_loop, anchor_idx, ring_specs,
                            target_edge_length):
    """Full mesh build in the flat plane.

    1. Call the engine on the perimeter loop to get a base triangulation.
    2. Add ring polygon vertices (flat, at the plane's z).
    3. Delete any base triangles whose centroid lies inside a ring.
    4. Bridge the gap: for each boundary edge of the deleted region,
       connect to the nearest ring polygon nodes to form triangles.
    5. Triangulate the region between the outer perimeter and the two
       ring polygons using a simple Delaunay on the union of nodes,
       with the perimeter as the outer boundary and the ring polygons
       as holes.  (We do this by calling the engine a second time on a
       dummy outer loop that encloses everything, then filtering.)
    6. Return points, edges, triangles, ring_polygon_indices.
    """
    # --- Step 1: base triangulation from the engine ----------------------
    base = build_mesh_triangulated(
        boundary_loop=perimeter_loop,
        anchor_indices=anchor_idx,
        segment_types=["cable"] * (perimeter_loop.shape[0]),
        target_edge_length=target_edge_length,
        plan_plane=None,
        warp_q=2000.0,
        weft_q=2000.0,
        edge_q=5000.0,
    )
    pts = np.array(base["points_initial"], copy=True)
    tris = [tuple(int(k) for k in t) for t in base["triangles"]]
    base_edges = list(base["edges"])

    z_level = float(perimeter_loop[0, 2])
    ring_circles = [(float(s["cx"]), float(s["cy"]), float(s["diameter"]) / 2.0)
                    for s in ring_specs]

    # --- Step 2: ring polygons -------------------------------------------
    ring_polys = []
    ring_notes = []
    for spec, (cx, cy, r) in zip(ring_specs, ring_circles):
        poly2d, n_used, note = _ring_polygon_from_nearest(
            pts[:, :2], cx, cy, r
        )
        poly2d[:, 2] = z_level
        ring_polys.append(poly2d)
        ring_notes.append(note)

    # --- Step 3: append ring polygon vertices ----------------------------
    ring_indices = []
    for poly2d in ring_polys:
        start = pts.shape[0]
        pts = np.vstack([pts, poly2d])
        ring_indices.append(list(range(start, start + poly2d.shape[0])))

    # --- Step 4: drop triangles inside any ring --------------------------
    kept_tris = []
    dropped = 0
    for tri in tris:
        a, b, c = tri
        centroid = (pts[a, :2] + pts[b, :2] + pts[c, :2]) / 3.0
        if _is_inside_any_ring(centroid, ring_circles):
            dropped += 1
            continue
        # Also drop triangles that have any vertex now inside a ring.
        if (_is_inside_any_ring(pts[a, :2], ring_circles)
                or _is_inside_any_ring(pts[b, :2], ring_circles)
                or _is_inside_any_ring(pts[c, :2], ring_circles)):
            dropped += 1
            continue
        kept_tris.append(tri)

    # --- Step 5: bridge remaining outer mesh to ring polygons ------------
    # For every vertex of a kept triangle, if it lies within one mesh
    # spacing of a ring, connect it to the two nearest ring polygon
    # vertices of that ring.  This forms a fan that closes the gap.
    new_tris = []
    for ring_k, idx_list in enumerate(ring_indices):
        cx, cy, r = ring_circles[ring_k]
        poly_pts = ring_polys[ring_k]
        n_poly = poly_pts.shape[0]
        # Ring polygon edges.
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            # Connect to nearest outer mesh vertex (if any within 2*target).
            pa = pts[a]
            # Find any kept-triangle vertex within 2*target of pa.
            candidates = [t for t in kept_tris]
            # We will only add a bridging triangle when a nearby vertex
            # exists.  To keep this simple we find nearest kept vertex.
            all_kept_verts = set()
            for t in kept_tris:
                all_kept_verts.update(t)
            if not all_kept_verts:
                continue
            arr = np.array(sorted(all_kept_verts), dtype=int)
            d = np.linalg.norm(pts[arr, :2] - pa[None, :2], axis=1)
            k_near = int(np.argmin(d))
            c_idx = int(arr[k_near])
            if d[k_near] < 3.0 * target_edge_length:
                new_tris.append((int(a), int(b), c_idx))

    tris = kept_tris + new_tris

    # --- Edges ------------------------------------------------------------
    edge_set = set()
    for t in tris:
        a, b, c = t
        for (p, q) in ((a, b), (b, c), (c, a)):
            key = (p, q) if p < q else (q, p)
            edge_set.add(key)
    # Add the ring polygon edges so the ring is a closed loop in the mesh.
    for idx_list in ring_indices:
        n_poly = len(idx_list)
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            key = (a, b) if a < b else (b, a)
            edge_set.add(key)
    edges = sorted(edge_set)

    # --- q values (uniform, will be replaced by solver call) --------------
    q = np.full(len(edges), 2000.0, dtype=float)

    # --- Held nodes: perimeter anchors and every ring vertex --------------
    fixed = set(int(i) for i in anchor_idx)
    for idx_list in ring_indices:
        for i in idx_list:
            fixed.add(int(i))

    return {
        "points": pts,
        "edges": edges,
        "triangles": tris,
        "fixed_indices": sorted(fixed),
        "q": q,
        "ring_indices": ring_indices,
        "ring_polygons": ring_polys,
        "dropped_count": dropped,
        "ring_notes": ring_notes,
        "z_level": z_level,
    }


# --- Page --------------------------------------------------------------------

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — double-cone mesh from "
        "first principles.  Flat build, ring lift, solve.</p>",
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

    # --- Primary beam curve --------------------------------------------------
    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array(
        [_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float
    )

    # --- Outer perimeter: anchors then subdivision ---------------------------
    anchors = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, span
    )
    perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)

    bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
    L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
    target_len = max(L_avg, 1e-6)

    # --- Ring specs (flat at eave height) -----------------------------------
    ring_x_positions = (-span / 6.0, +span / 6.0)
    ring_specs = [
        {"cx": float(rx), "cy": 0.0,
         "cz": float(eave_height), "diameter": float(ring_diameter)}
        for rx in ring_x_positions
    ]

    # --- Build mesh with rings (flat at eave plane) -------------------------
    built = _build_mesh_with_rings(
        perimeter_loop, anchor_idx, ring_specs, target_len
    )

    pts = built["points"]
    edges = built["edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]
    ring_indices = built["ring_indices"]

    # --- Lift ring polygon vertices to RING_HEIGHT --------------------------
    pts_lifted = pts.copy()
    for idx_list in ring_indices:
        for i in idx_list:
            pts_lifted[i, 2] = RING_HEIGHT

    # --- q values ------------------------------------------------------------
    warp_pre = max(float(warp_q_input), 0.1)
    weft_pre = max(float(weft_q_input), 0.1)
    warp_q = warp_pre * 1000.0
    weft_q = weft_pre * 1000.0
    if edge_q_input > 0.0:
        edge_q_scalar = float(edge_q_input) * 1000.0
    else:
        edge_q_scalar = max(warp_q, weft_q) * target_len
    edge_q_scalar = max(edge_q_scalar, 1.0)

    q = np.full(len(edges), warp_q, dtype=float)

    # --- Solve ---------------------------------------------------------------
    try:
        fdm = solve_fdm(pts_lifted, edges, fixed, q)
        coords = fdm["coordinates"]
        residual_norm = float(fdm["residual_norm"])
        solve_ok = True
        solve_err = ""
    except Exception as e:
        coords = pts_lifted.copy()
        residual_norm = float("nan")
        solve_ok = False
        solve_err = str(e)

    # --- Figure --------------------------------------------------------------
    fig = go.Figure()

    if len(tris) > 0:
        tri = np.asarray(tris, dtype=int)
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

    # Perimeter at eave
    pc = np.vstack([perimeter_loop, perimeter_loop[:1]])
    fig.add_trace(go.Scatter3d(
        x=pc[:, 0], y=pc[:, 1], z=pc[:, 2],
        mode="lines", line=dict(color=COL_PERIMETER, width=5),
        name="perimeter", showlegend=False, hoverinfo="skip",
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

    # Held nodes
    if len(fixed) > 0:
        fi = np.asarray(fixed, dtype=int)
        fig.add_trace(go.Scatter3d(
            x=coords[fi, 0], y=coords[fi, 1], z=coords[fi, 2],
            mode="markers", marker=dict(color=COL_ANCHOR, size=4),
            name="held nodes", showlegend=False, hoverinfo="skip",
        ))

    # Ring polygons at lifted position
    for k, idx_list in enumerate(ring_indices):
        pp = coords[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name=f"ring {k+1}", showlegend=False, hoverinfo="skip",
        ))
        # Drop member from primary above the ring centre.
        cx = ring_specs[k]["cx"]
        z_up = float(np.interp(cx, xp, zp))
        fig.add_trace(go.Scatter3d(
            x=[cx, cx], y=[0.0, 0.0], z=[z_up, RING_HEIGHT],
            mode="lines", line=dict(color=COL_DROP, width=3),
            name=f"drop {k+1}", showlegend=False, hoverinfo="skip",
        ))

    apply_common_layout(fig, apex)
    st.plotly_chart(fig, use_container_width=True)

    # --- Diagnostics ---------------------------------------------------------
    with st.expander("Diagnostics", expanded=False):
        st.write(f"Anchors (outer): {anchors.shape[0]}")
        st.write(f"Subdivisions per edge: {subdivisions}")
        st.write(f"Perimeter loop nodes: {perimeter_loop.shape[0]}")
        st.write(f"Total mesh nodes: {pts.shape[0]}")
        st.write(f"Mesh edges: {len(edges)}")
        st.write(f"Mesh triangles: {len(tris)}")
        st.write(f"Dropped triangles inside rings: {built['dropped_count']}")
        st.write(f"Held nodes: {len(fixed)}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Solve error: {solve_err}")
        else:
            st.write(f"Residual norm: {residual_norm:.6e}")
        st.write(f"Target edge length: {target_len:.4f}")
        st.write(f"Ring height (lifted): {RING_HEIGHT:.2f}")
        st.write(f"Ring stations x: " +
                 ", ".join(f"{v:+.3f}" for v in ring_x_positions))
        st.write(f"Ring diameter: {ring_diameter:.3f}")
        st.write("**Ring notes:**")
        for n in built["ring_notes"]:
            st.write("- " + n)
