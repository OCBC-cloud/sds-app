"""Multi-Cone Roof — Stage 3 Lab test page.

Stage 3 builds the double-cone mesh, following the client's build order:

  1. Outer perimeter boundary polygon.
       Anchor points at rib crossings plus two tips.
       anchor_count = 2 * N + 2   (8 for the default N = 3)
  2. Subdivide each edge between adjacent anchors into `subdivisions`
       equal segments.  subdivisions is a widget (5 to 25, default 11).
  3. Rings placed flat at z = eave_height (2.8 m), same plane as the
       outer boundary.
  4. Mesh the annular region between the outer boundary and the two
       ring polygons.
  5. Lift only the ring polygon vertices to RING_HEIGHT = 7.0 m.
  6. Solve with solve_fdm.

Rings are holes in the fabric.  No fabric inside a ring polygon.

No engine files are modified.  The outer flat mesh comes from
build_mesh_triangulated.  The ring rewrite is done here.

Iteration history:
  2026-10-10 v1: first build.  Engine rejected segment_types
                 (one per node instead of one per anchor).
  2026-10-10 v2: segment_types now one per anchor.  This file.
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


def _build_mesh_with_rings(perimeter_loop, anchor_idx, ring_specs,
                            target_edge_length):
    """Call the engine on the perimeter, then rewrite to add ring holes."""
    # v2 fix: one segment_types entry per ANCHOR, not per loop node.
    base = build_mesh_triangulated(
        boundary_loop=perimeter_loop,
        anchor_indices=anchor_idx,
        segment_types=["cable"] * len(anchor_idx),
        target_edge_length=target_edge_length,
        plan_plane=None,
        warp_q=2000.0,
        weft_q=2000.0,
        edge_q=5000.0,
    )
    pts = np.array(base["points_initial"], copy=True)
    tris = [tuple(int(k) for k in t) for t in base["triangles"]]

    z_level = float(perimeter_loop[0, 2])
    ring_circles = [(float(s["cx"]), float(s["cy"]),
                     float(s["diameter"]) / 2.0) for s in ring_specs]

    ring_polys = []
    ring_notes = []
    for spec, (cx, cy, r) in zip(ring_specs, ring_circles):
        dist = np.linalg.norm(pts[:, :2] - np.array([cx, cy]), axis=1)
        n_used = int(np.sum(dist <= r * 2.0))
        note = f"ring at ({cx:+.2f}, {cy:+.2f}): {n_used} nodes within {r*2:.3f} m"
        if n_used < 6:
            n_used = 6
            note += "  -> raised to minimum 6"
        if n_used > 48:
            n_used = 48
            note += "  -> capped at 48"
        t = np.linspace(0.0, 2.0 * math.pi, n_used, endpoint=False)
        poly = np.column_stack([
            cx + r * np.cos(t),
            cy + r * np.sin(t),
            np.full(n_used, z_level, dtype=float),
        ])
        ring_polys.append(poly)
        ring_notes.append(note)

    ring_indices = []
    for poly in ring_polys:
        start = pts.shape[0]
        pts = np.vstack([pts, poly])
        ring_indices.append(list(range(start, start + poly.shape[0])))

    # Drop triangles whose centroid or any vertex is inside a ring.
    def _inside_any(xy):
        for (cx, cy, r) in ring_circles:
            if (xy[0] - cx) ** 2 + (xy[1] - cy) ** 2 < r * r:
                return True
        return False

    kept = []
    dropped = 0
    for tri in tris:
        a, b, c = tri
        cen = (pts[a, :2] + pts[b, :2] + pts[c, :2]) / 3.0
        if _inside_any(cen) or _inside_any(pts[a, :2]) \
                or _inside_any(pts[b, :2]) or _inside_any(pts[c, :2]):
            dropped += 1
            continue
        kept.append(tri)

    # Bridge: for each ring polygon edge, connect to the nearest
    # kept-triangle vertex within 3 * target_edge_length.
    all_kept_verts = sorted({v for t in kept for v in t})
    arr = np.array(all_kept_verts, dtype=int) if all_kept_verts else np.array([], dtype=int)

    new_tris = []
    for idx_list in ring_indices:
        n_poly = len(idx_list)
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            if arr.size == 0:
                continue
            pa = pts[a]
            d = np.linalg.norm(pts[arr, :2] - pa[None, :2], axis=1)
            k_near = int(np.argmin(d))
            c_idx = int(arr[k_near])
            if d[k_near] < 3.0 * target_edge_length:
                new_tris.append((int(a), int(b), c_idx))

    tris = kept + new_tris

    edge_set = set()
    for t in tris:
        a, b, c = t
        for (p, q) in ((a, b), (b, c), (c, a)):
            key = (p, q) if p < q else (q, p)
            edge_set.add(key)
    for idx_list in ring_indices:
        n_poly = len(idx_list)
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            key = (a, b) if a < b else (b, a)
            edge_set.add(key)
    edges = sorted(edge_set)

    q = np.full(len(edges), 2000.0, dtype=float)

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


def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — double-cone mesh.  "
        "Rings lifted to 7 m, then solved.</p>",
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

    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array(
        [_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float
    )

    anchors = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, span
    )
    perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)

    bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
    L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
    target_len = max(L_avg, 1e-6)

    ring_x_positions = (-span / 6.0, +span / 6.0)
    ring_specs = [
        {"cx": float(rx), "cy": 0.0,
         "cz": float(eave_height), "diameter": float(ring_diameter)}
        for rx in ring_x_positions
    ]

    built = _build_mesh_with_rings(
        perimeter_loop, anchor_idx, ring_specs, target_len
    )

    pts = built["points"]
    edges = built["edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]
    ring_indices = built["ring_indices"]

    # Lift ring polygon vertices to RING_HEIGHT.
    pts_lifted = pts.copy()
    for idx_list in ring_indices:
        for i in idx_list:
            pts_lifted[i, 2] = RING_HEIGHT

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

    for k, idx_list in enumerate(ring_indices):
        pp = coords[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name=f"ring {k+1}", showlegend=False, hoverinfo="skip",
        ))
        cx = ring_specs[k]["cx"]
        z_up = float(np.interp(cx, xp, zp))
        fig.add_trace(go.Scatter3d(
            x=[cx, cx], y=[0.0, 0.0], z=[z_up, RING_HEIGHT],
            mode="lines", line=dict(color=COL_DROP, width=3),
            name=f"drop {k+1}", showlegend=False, hoverinfo="skip",
        ))

    apply_common_layout(fig, apex)
    st.plotly_chart(fig, use_container_width=True)

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
