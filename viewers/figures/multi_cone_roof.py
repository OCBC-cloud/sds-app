# =============================================================================
# SDSe - Multi-Cone Roof Viewer
# =============================================================================
# Builds the 3D figure for the Multi-Cone Cluster variant.
#
# Reads all inputs from session state under the "ws_mc_" prefix.
# Runs the same FDM pipeline that was proven in the Lab tester
# (ui/workshops/tester_multi_cone.py, v21):
#
#   1. Build eave perimeter from rib stations
#   2. Place cone rings along the primary beam by arc length
#   3. Build the fabric mesh with ring holes cut out
#   4. Laplace-lift the fabric to meet the eave and every ring
#   5. Delaunay triangulate the plan
#   6. Solve FDM with:
#        - only structural anchors held (8 eave corners + ring
#          polygon nodes + ring centres + beam tops)
#        - EVERY perimeter node fully free (real cable behaviour)
#        - anisotropic warp/weft blend on interior edges
#        - direct edge cable q from the slider
#
# Signature matches the FIGURE_REGISTRY contract:
#   - no arguments
#   - returns a plotly.graph_objects.Figure
#
# History:
#   2026-10-13 - First version. Migrated from the Lab tester v21.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm
from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
)


# =============================================================================
# COLOURS
# =============================================================================

RIB_SEGMENTS = 80
RING_NODES_MIN = 12
RING_NODES_MAX = 32

COL_MEMBRANE = "#4a7a9c"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"


# =============================================================================
# SESSION STATE HELPERS
# =============================================================================

def _get(key, default=None):
    """Read a Multi-Cone session-state value by short key."""
    return st.session_state.get("ws_mc_" + key, default)


# =============================================================================
# GEOMETRY HELPERS (from v21)
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


def _ring_node_count(r, target_len):
    n = int(round(2.0 * math.pi * r / max(target_len, 1e-6)))
    n = max(RING_NODES_MIN, min(RING_NODES_MAX, n))
    return n


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
# ANISOTROPIC WARP / WEFT BLEND
# =============================================================================

def _blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q):
    m = len(edges)
    q = np.zeros(m, dtype=float)
    warp_dir = np.asarray(warp_dir, dtype=float)
    wn = float(np.linalg.norm(warp_dir))
    if wn < 1e-12:
        warp_dir = np.array([1.0, 0.0])
    else:
        warp_dir = warp_dir / wn
    for k, (a, b) in enumerate(edges):
        pa = pts_2d[a]
        pb = pts_2d[b]
        d = pb - pa
        dn = float(np.linalg.norm(d))
        if dn < 1e-12:
            q[k] = float(warp_q)
            continue
        d = d / dn
        cos_t = float(np.dot(d, warp_dir))
        cos_t = max(-1.0, min(1.0, cos_t))
        c2 = cos_t * cos_t
        s2 = 1.0 - c2
        q[k] = float(warp_q) * c2 + float(weft_q) * s2
    return q


# =============================================================================
# LAPLACE LIFT
# =============================================================================

def _laplace_lift_fabric(all_pts, n_perimeter, boundary_z_map):
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    from scipy.spatial import cKDTree

    n_nodes = all_pts.shape[0]
    pts_2d = all_pts[:, :2]

    is_fixed = np.zeros(n_nodes, dtype=bool)
    for i in boundary_z_map:
        is_fixed[i] = True
    for i in range(n_perimeter):
        is_fixed[i] = True

    tree = cKDTree(pts_2d)
    k = min(8, n_nodes - 1)
    if k < 1:
        return all_pts[:, 2].copy()

    dists, idxs = tree.query(pts_2d, k=k + 1)

    rows, cols, data = [], [], []
    for i in range(n_nodes):
        nbrs = idxs[i, 1:]
        degree = len(nbrs)
        if degree == 0:
            continue
        rows.append(i); cols.append(i); data.append(float(degree))
        for j in nbrs:
            rows.append(i); cols.append(int(j)); data.append(-1.0)

    L = sp.csr_matrix((data, (rows, cols)), shape=(n_nodes, n_nodes))

    int_idx = np.where(~is_fixed)[0]
    bnd_idx = np.where(is_fixed)[0]

    if len(int_idx) == 0:
        return all_pts[:, 2].copy()

    L_ii = L[int_idx, :][:, int_idx]
    L_ib = L[int_idx, :][:, bnd_idx]

    z_b = np.zeros(len(bnd_idx), dtype=float)
    for a, i in enumerate(bnd_idx):
        if int(i) in boundary_z_map:
            z_b[a] = float(boundary_z_map[int(i)])
        else:
            z_b[a] = float(all_pts[i, 2])

    rhs = -L_ib @ z_b
    try:
        z_int = spla.spsolve(L_ii.tocsc(), rhs)
    except Exception:
        z_int = np.zeros(len(int_idx))

    z_all = all_pts[:, 2].copy()
    for a in range(len(int_idx)):
        z_all[int(int_idx[a])] = float(z_int[a])
    return z_all


# =============================================================================
# MESH BUILDER
# =============================================================================

def _build_cone_mesh(perimeter_loop, anchor_idx, ring_specs,
                      eave_height, target_len):
    from scipy.spatial import Delaunay

    poly_xy = perimeter_loop[:, :2]
    ring_centres_radii = [(float(s["cx"]), float(s["cy"]), float(s["r"]))
                          for s in ring_specs]

    xmin = float(np.min(perimeter_loop[:, 0]))
    xmax = float(np.max(perimeter_loop[:, 0]))
    ymin = float(np.min(perimeter_loop[:, 1]))
    ymax = float(np.max(perimeter_loop[:, 1]))

    h = float(target_len)
    xs = np.arange(xmin + 0.5 * h, xmax, h)
    ys = np.arange(ymin + 0.5 * h, ymax, h)

    clearance_band = 1.0 * target_len
    interior_xy = []
    for x in xs:
        for y in ys:
            if not _point_in_polygon(x, y, poly_xy):
                continue
            too_close = False
            for (cx, cy, r) in ring_centres_radii:
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if d < r + clearance_band:
                    too_close = True
                    break
            if too_close:
                continue
            interior_xy.append((float(x), float(y)))

    all_pts_list = [tuple(p) for p in perimeter_loop]
    n_perimeter = len(all_pts_list)

    ring_indices = []
    centre_indices = []
    beam_top_indices = []
    ring_node_counts = []

    for spec in ring_specs:
        cx = float(spec["cx"]); cy = float(spec["cy"])
        cz = float(spec["cz"]); r = float(spec["r"])
        n_poly = _ring_node_count(r, target_len)
        ring_node_counts.append(n_poly)
        t = np.linspace(0.0, 2.0 * math.pi, n_poly, endpoint=False)
        poly = np.column_stack([
            cx + r * np.cos(t),
            cy + r * np.sin(t),
            np.full(n_poly, cz, dtype=float),
        ])
        start = len(all_pts_list)
        for p in poly:
            all_pts_list.append(tuple(p))
        ring_indices.append(list(range(start, start + n_poly)))
        centre_indices.append(len(all_pts_list))
        all_pts_list.append((cx, cy, cz))
        beam_top_indices.append(len(all_pts_list))
        all_pts_list.append((cx, cy, float(spec["beam_z"])))

    fabric_start = len(all_pts_list)
    for (x, y) in interior_xy:
        all_pts_list.append((x, y, eave_height))
    fabric_end = len(all_pts_list)

    all_pts = np.asarray(all_pts_list, dtype=float)

    boundary_z_map = {}
    for i in range(n_perimeter):
        boundary_z_map[i] = float(eave_height)
    for k, spec in enumerate(ring_specs):
        cz = float(spec["cz"])
        for i in ring_indices[k]:
            boundary_z_map[int(i)] = cz
    for k, ci in enumerate(centre_indices):
        boundary_z_map[int(ci)] = float(ring_specs[k]["cz"])
    for k, bi in enumerate(beam_top_indices):
        boundary_z_map[int(bi)] = float(ring_specs[k]["beam_z"])

    z_all = _laplace_lift_fabric(all_pts, n_perimeter, boundary_z_map)
    all_pts[:, 2] = z_all

    pts_2d = all_pts[:, :2]
    tri = Delaunay(pts_2d[:fabric_end])

    triangles = []
    for simplex in tri.simplices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        cen = (pts_2d[a] + pts_2d[b] + pts_2d[c]) / 3.0
        if not _point_in_polygon(cen[0], cen[1], poly_xy):
            continue
        bad = False
        for (cx, cy, r) in ring_centres_radii:
            if ((cen[0] - cx) ** 2 + (cen[1] - cy) ** 2) < r * r:
                bad = True
                break
        if bad:
            continue
        triangles.append((a, b, c))

    boundary_edge_set = set()
    for i in range(n_perimeter):
        j = (i + 1) % n_perimeter
        key = (i, j) if i < j else (j, i)
        boundary_edge_set.add(key)

    all_edge_set = set()
    for (a, b, c) in triangles:
        for (p, q) in ((a, b), (b, c), (c, a)):
            key = (p, q) if p < q else (q, p)
            all_edge_set.add(key)
    for key in boundary_edge_set:
        all_edge_set.add(key)

    for k in range(len(ring_specs)):
        idx_list = ring_indices[k]
        centre_i = centre_indices[k]
        beam_i = beam_top_indices[k]
        n_poly = len(idx_list)
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            key = (a, b) if a < b else (b, a)
            all_edge_set.add(key)
            boundary_edge_set.add(key)
        for i in idx_list:
            key = (centre_i, i) if centre_i < i else (i, centre_i)
            all_edge_set.add(key)
        key = (centre_i, beam_i) if centre_i < beam_i else (beam_i, centre_i)
        all_edge_set.add(key)

    fixed = set(int(i) for i in anchor_idx)
    for idx_list in ring_indices:
        for i in idx_list:
            fixed.add(int(i))
    for ci in centre_indices:
        fixed.add(int(ci))
    for bi in beam_top_indices:
        fixed.add(int(bi))

    edges = sorted(all_edge_set)

    return {
        "points": all_pts,
        "edges": edges,
        "boundary_edges": boundary_edge_set,
        "triangles": triangles,
        "fixed_indices": sorted(fixed),
        "ring_indices": ring_indices,
        "centre_indices": centre_indices,
        "beam_top_indices": beam_top_indices,
        "ring_node_counts": ring_node_counts,
        "n_perimeter": n_perimeter,
        "n_interior": len(interior_xy),
    }


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

    # ---- Mesh + solve -----------------------------------------------------
    built = _build_cone_mesh(
        perimeter_loop, anchor_idx, ring_specs,
        eave_height, target_len,
    )

    pts = built["points"]
    edges = built["edges"]
    boundary_edge_set = built["boundary_edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]

    pts_2d = pts[:, :2]
    warp_dir = np.array([1.0, 0.0])
    q_interior = _blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q)

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
        # Draw the initial geometry with a warning if the solve fails.
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
