# =============================================================================
# SDSe - Dome Multi-Cone Viewer
# =============================================================================
# Builds the 3D figure for the Dome Multi-Cone variant.
#
# Reads all inputs from session state under the "ws_dm_" prefix.
#
# The dome geometry generator (new piece):
#   1. Master meridian beam - one parabolic/circular/catenary curve
#      from ground to crown to ground, along the X axis.
#   2. Two families of meridians - the master beam copied, scaled,
#      and rotated 90 degrees about the vertical.
#   3. Eave crossings - where each meridian meets z = eave_height.
#      These become the eave anchor polygon.
#   4. Grid crossings - where family A and family B meet in plan,
#      inside the eave polygon. Held nodes.
#   5. Cone placement - automatic (grid-driven) or user-defined
#      (symmetric around crown, snapped to nearest crossing).
#
# Everything downstream reuses the multi-cone cluster code:
#   _build_cone_mesh, _laplace_lift_fabric, _blend_q_per_edge,
#   solve_fdm.
#
# History:
#   2026-10-13 - First version. Dome geometry generator.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm
from viewers.figures._shared import apply_common_layout


# =============================================================================
# COLOURS AND CONSTANTS
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
# SESSION STATE HELPER
# =============================================================================

def _get(key, default=None):
    """Read a Dome session-state value by short key."""
    return st.session_state.get("ws_dm_" + key, default)


# =============================================================================
# BEAM CURVE (dome profile)
# =============================================================================

def _dome_profile(t, height, curve_type):
    """
    Return z as a function of normalised radius t in [0, 1].
    t = 0 at crown, t = 1 at ground.
    """
    t = np.clip(t, 0.0, 1.0)
    if curve_type == "circular":
        return height * np.sqrt(np.maximum(0.0, 1.0 - t * t))
    if curve_type == "catenary":
        a = 2.5
        num = np.cosh(a * (1.0 - t)) - np.cosh(a)
        den = 1.0 - np.cosh(a)
        return height * num / den
    return height * (1.0 - t * t)


def _master_meridian(height, radius_at_ground, curve_type, n_samples=200):
    """
    Master meridian curve along the X axis.
    Returns (x, y, z) arrays, from crown -> ground.
    """
    t = np.linspace(0.0, 1.0, n_samples)
    z = _dome_profile(t, height, curve_type)
    ease = np.sin(0.5 * np.pi * t)
    r = radius_at_ground * ease
    x = r
    y = np.zeros_like(x)
    return x, y, z


# =============================================================================
# MERIDIAN FAMILIES
# =============================================================================

def _scale_meridian(master_x, master_y, master_z, scale):
    return master_x * scale, master_y * scale, master_z


def _rotate_about_z(x, y, angle_rad):
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    xr = x * c - y * s
    yr = x * s + y * c
    return xr, yr


def _build_meridian_family(master_x, master_y, master_z,
                            n_meridians, family_axis,
                            base_half_width):
    """
    Build one family of meridians.
    family_axis = "x" -> curves along X axis (offset across Y).
    family_axis = "y" -> same, rotated 90 degrees.
    """
    meridians = []

    if n_meridians < 2:
        n_meridians = 2

    scale_max = 1.0
    scale_min = 0.12
    scales = np.linspace(scale_min, scale_max, n_meridians)

    angle = 0.0 if family_axis == "x" else (math.pi / 2.0)

    for k, scale in enumerate(scales):
        sx, sy, sz = _scale_meridian(master_x, master_y, master_z, scale)

        offset = (k - (n_meridians - 1) / 2.0)
        perp_offset = offset * (base_half_width / max(n_meridians - 1, 1))
        sy = sy + perp_offset

        rx, ry = _rotate_about_z(sx, sy, angle)
        meridians.append((rx, ry, sz))

    return meridians


# =============================================================================
# EAVE ANCHOR POLYGON
# =============================================================================

def _find_eave_crossings(meridians, eave_height):
    crossings = []
    for (x, y, z) in meridians:
        idx_above = np.where(z >= eave_height)[0]
        if len(idx_above) < 2:
            continue
        i_first = int(idx_above[0])
        i_last = int(idx_above[-1])
        if i_first > 0:
            z0, z1 = z[i_first - 1], z[i_first]
            if z1 - z0 > 1e-9:
                f = (eave_height - z0) / (z1 - z0)
                xx = x[i_first - 1] + f * (x[i_first] - x[i_first - 1])
                yy = y[i_first - 1] + f * (y[i_first] - y[i_first - 1])
                crossings.append((float(xx), float(yy), float(eave_height)))
        if i_last < len(z) - 1:
            z0, z1 = z[i_last], z[i_last + 1]
            if z1 - z0 < -1e-9:
                f = (eave_height - z0) / (z1 - z0)
                xx = x[i_last] + f * (x[i_last + 1] - x[i_last])
                yy = y[i_last] + f * (y[i_last + 1] - y[i_last])
                crossings.append((float(xx), float(yy), float(eave_height)))
    return crossings


def _order_around_centre(points):
    arr = np.asarray(points, dtype=float)
    if arr.shape[0] < 3:
        return arr
    cx = float(np.mean(arr[:, 0]))
    cy = float(np.mean(arr[:, 1]))
    angles = np.arctan2(arr[:, 1] - cy, arr[:, 0] - cx)
    order = np.argsort(angles)
    return arr[order]


def _dedupe_close(points, tol=0.05):
    if len(points) == 0:
        return np.zeros((0, 3), dtype=float)
    pts = np.asarray(points, dtype=float)
    keep = []
    for i in range(pts.shape[0]):
        too_close = False
        for j in keep:
            if np.linalg.norm(pts[i] - pts[j]) < tol:
                too_close = True
                break
        if not too_close:
            keep.append(i)
    return pts[keep]


def _build_eave_polygon(meridians, eave_height):
    crossings = _find_eave_crossings(meridians, eave_height)
    crossings = _dedupe_close(crossings, tol=0.05)
    polygon = _order_around_centre(crossings)
    return polygon


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


# =============================================================================
# GRID CROSSINGS
# =============================================================================

def _point_in_polygon_xy(x, y, poly):
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


def _find_grid_crossings(family_a, family_b, eave_polygon):
    crossings = []
    poly_xy = eave_polygon[:, :2]
    for (ax, ay, az) in family_a:
        for (bx, by, bz) in family_b:
            n = len(ax)
            best_i = 0
            best_j = 0
            best_d = float("inf")
            for i in range(n):
                dx = ax[i] - bx
                dy = ay[i] - by
                d2 = dx * dx + dy * dy
                j = int(np.argmin(d2))
                if float(d2[j]) < best_d:
                    best_d = float(d2[j])
                    best_i = i
                    best_j = j
            if best_d > 1.0:
                continue
            cx = 0.5 * (ax[best_i] + bx[best_j])
            cy = 0.5 * (ay[best_i] + by[best_j])
            cz = 0.5 * (az[best_i] + bz[best_j])
            if not _point_in_polygon_xy(cx, cy, poly_xy):
                continue
            crossings.append((float(cx), float(cy), float(cz)))
    return crossings


# =============================================================================
# CONE PLACEMENT
# =============================================================================

def _min_dist_to_polygon(x, y, poly_xy):
    n = poly_xy.shape[0]
    best = float("inf")
    for i in range(n):
        ax, ay = poly_xy[i]
        bx, by = poly_xy[(i + 1) % n]
        dx = bx - ax
        dy = by - ay
        L2 = dx * dx + dy * dy
        if L2 < 1e-12:
            d = math.hypot(x - ax, y - ay)
        else:
            t = ((x - ax) * dx + (y - ay) * dy) / L2
            t = max(0.0, min(1.0, t))
            px = ax + t * dx
            py = ay + t * dy
            d = math.hypot(x - px, y - py)
        if d < best:
            best = d
    return best


def _place_cones_user_defined(crossings, n_cones, ring_radius_frac,
                                start_angle_deg, dome_diameter,
                                min_eave_clearance, eave_polygon):
    refusals = []
    if not crossings or n_cones < 1:
        return [], ["No grid crossings available."]

    crossings_arr = np.asarray(crossings, dtype=float)
    dome_r = dome_diameter / 2.0
    ring_r = ring_radius_frac * dome_r
    start = math.radians(start_angle_deg)

    chosen = []
    poly_xy = eave_polygon[:, :2]

    for k in range(n_cones):
        angle = start + (2.0 * math.pi * k / n_cones)
        ix = ring_r * math.cos(angle)
        iy = ring_r * math.sin(angle)

        dx = crossings_arr[:, 0] - ix
        dy = crossings_arr[:, 1] - iy
        d = np.sqrt(dx * dx + dy * dy)
        order = np.argsort(d)

        picked = None
        for idx in order:
            cx, cy, cz = crossings_arr[idx]
            if min_eave_clearance > 0.0:
                edist = _min_dist_to_polygon(cx, cy, poly_xy)
                if edist < min_eave_clearance:
                    continue
            ok = True
            for (px, py, pz) in chosen:
                if math.hypot(cx - px, cy - py) < 1e-6:
                    ok = False
                    break
            if ok:
                picked = (cx, cy, cz)
                break

        if picked is None:
            refusals.append(
                "Cone %d could not be placed. Nearest crossing too far "
                "or too close to the eave." % (k + 1)
            )
            continue

        chosen.append(picked)

    return chosen, refusals


def _place_cones_automatic(crossings, dome_radius, ring_diameter,
                            min_member_length, min_ring_gap,
                            min_eave_clearance, eave_polygon):
    if not crossings:
        return [], []

    crossings_arr = np.asarray(crossings, dtype=float)
    r = np.sqrt(crossings_arr[:, 0] ** 2 + crossings_arr[:, 1] ** 2)
    ang = np.arctan2(crossings_arr[:, 1], crossings_arr[:, 0])
    order = np.lexsort((ang, r))
    sorted_crossings = crossings_arr[order]

    placed = []
    poly_xy = eave_polygon[:, :2]

    for (cx, cy, cz) in sorted_crossings:
        if min_eave_clearance > 0.0:
            edist = _min_dist_to_polygon(cx, cy, poly_xy)
            if edist < min_eave_clearance:
                continue

        ok = True
        for (px, py, pz) in placed:
            d = math.hypot(cx - px, cy - py)
            if d < ring_diameter:
                ok = False
                break
            if min_ring_gap > 0.0 and d < ring_diameter + min_ring_gap:
                ok = False
                break
            if min_member_length > 0.0 and d < min_member_length:
                ok = False
                break
        if ok:
            placed.append((float(cx), float(cy), float(cz)))

    return placed, []


# =============================================================================
# RING SPECS
# =============================================================================

def _ring_node_count(r, target_len):
    n = int(round(2.0 * math.pi * r / max(target_len, 1e-6)))
    n = max(RING_NODES_MIN, min(RING_NODES_MAX, n))
    return n


def _build_ring_specs(cone_positions, drop_length, ring_diameter, target_len):
    specs = []
    for (cx, cy, cz) in cone_positions:
        specs.append({
            "cx": float(cx),
            "cy": float(cy),
            "cz": float(cz - drop_length),
            "r": float(ring_diameter) / 2.0,
            "beam_z": float(cz),
        })
    return specs


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


def _build_dome_mesh(perimeter_loop, anchor_idx, ring_specs,
                     grid_crossings_xy, eave_height, target_len):
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

    crossing_indices = []
    for (gx, gy) in grid_crossings_xy:
        crossing_indices.append(len(all_pts_list))
        all_pts_list.append((float(gx), float(gy), eave_height))

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
    for ci in crossing_indices:
        fixed.add(int(ci))

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
        "crossing_indices": crossing_indices,
        "n_perimeter": n_perimeter,
        "n_interior": len(interior_xy),
    }


# =============================================================================
# ANISOTROPIC BLEND
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
# PUBLIC FIGURE BUILDER
# =============================================================================

def build_dome_multi_cone():
    dome_diameter = float(_get("dome_diameter", 18.0))
    crown_height = float(_get("crown_height", 9.0))
    ground_outline = str(_get("ground_outline", "circle"))
    base_x = float(_get("base_width_x", 18.0))
    base_y = float(_get("base_width_y", 18.0))
    mer_x = int(_get("meridians_x", 8))
    mer_y = int(_get("meridians_y", 8))
    eave_height = float(_get("eave_height", 3.2))
    curve_type = str(_get("curve_type", "parabolic"))

    placement_mode = str(_get("placement_mode", "automatic"))
    cone_count = int(_get("cone_count", 4))
    cone_ring_radius = float(_get("cone_ring_radius", 0.6))
    cone_start_angle = float(_get("cone_start_angle", 0.0))
    drop_length = float(_get("drop_length", 1.0))
    ring_diameter = float(_get("ring_diameter", 2.0))
    min_member_length = float(_get("min_member_length", 3.6))
    min_ring_gap = float(_get("min_ring_gap", 1.8))
    min_eave_clearance = float(_get("min_eave_clearance", 2.7))

    warp_q = max(float(_get("warp_pretension", 1.0)), 0.1) * 1000.0
    weft_q = max(float(_get("weft_pretension", 1.0)), 0.1) * 1000.0
    edge_q_scalar = max(float(_get("edge_cable_pretension", 25.0)), 0.1) * 1000.0

    if ground_outline == "circle":
        half_x = half_y = dome_diameter / 2.0
    else:
        half_x = base_x / 2.0
        half_y = base_y / 2.0

    master_x, master_y, master_z = _master_meridian(
        crown_height, half_x, curve_type, n_samples=200
    )

    family_a = _build_meridian_family(
        master_x, master_y, master_z, mer_x, "x", half_y
    )
    family_b = _build_meridian_family(
        master_x, master_y, master_z, mer_y, "y", half_x
    )

    all_meridians = family_a + family_b
    eave_anchors = _build_eave_polygon(all_meridians, eave_height)
    if eave_anchors.shape[0] < 3:
        t = np.linspace(0, 2 * math.pi, 32, endpoint=False)
        eave_anchors = np.column_stack([
            half_x * np.cos(t),
            half_y * np.sin(t),
            np.full_like(t, eave_height),
        ])
    subdivisions = max(3, int(24 / max(len(eave_anchors), 1)))
    perimeter_loop, anchor_idx = _subdivide_polygon(eave_anchors, subdivisions)

    grid_crossings = _find_grid_crossings(family_a, family_b, eave_anchors)

    if placement_mode == "user_defined":
        cones, refusals = _place_cones_user_defined(
            grid_crossings, cone_count, cone_ring_radius,
            cone_start_angle, dome_diameter,
            min_eave_clearance, eave_anchors,
        )
        for msg in refusals:
            st.warning(msg)
    else:
        cones, _ = _place_cones_automatic(
            grid_crossings, dome_diameter / 2.0, ring_diameter,
            min_member_length, min_ring_gap,
            min_eave_clearance, eave_anchors,
        )

    ring_specs = _build_ring_specs(cones, drop_length, ring_diameter, 0.5)

    bbox_w = float(np.max(perimeter_loop[:, 0]) - np.min(perimeter_loop[:, 0]))
    target_len = max(bbox_w / 40.0, 0.4)

    built = _build_dome_mesh(
        perimeter_loop, anchor_idx, ring_specs,
        [(c[0], c[1]) for c in grid_crossings],
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
        coords = pts.copy()
        st.warning("Dome solver failed: " + str(e))

    fig = go.Figure()

    if len(tris) > 0:
        tri = np.asarray(tris, dtype=int)
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            name="membrane", showlegend=False, hoverinfo="skip",
        ))

    for (x, y, z) in family_a:
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode="lines", line=dict(color=COL_RIB, width=4),
            name="meridian", showlegend=False, hoverinfo="skip",
        ))
    for (x, y, z) in family_b:
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode="lines", line=dict(color=COL_RIB, width=4),
            name="meridian", showlegend=False, hoverinfo="skip",
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

    return apply_common_layout(fig, crown_height)


# =============================================================================
# END OF viewers/figures/dome_multi_cone.py
# =============================================================================
