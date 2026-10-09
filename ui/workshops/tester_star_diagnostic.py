# =============================================================================
# SDSe - Star Diagnostic (Lab)
# =============================================================================
# Self-contained test file. Nothing here imports from engine/ or
# viewers/. The FDM solver, the q builder, and the mesh builder
# are copied locally. The engine and the viewer are untouched.
#
# Purpose:
#   Show that when the triangulated mesh is rebuilt fresh from the
#   settled coordinates after each form-finding, the resulting
#   triangulation is clean. No jagged edges, no slivers, no star.
#
# The one change from the production path:
#   The current engine triangulates the boundary BEFORE the FDM
#   solve. The triangles are the mesh on which the solve runs. When
#   the boundary bows, those triangles deform, and at extremes they
#   produce slivers and star-shaped boundary collapse.
#
#   In this file, the FDM solve runs as it does now, but the
#   triangles that are returned to the viewer are rebuilt fresh
#   from the SETTLED coordinates. The triangulation the user sees
#   is the triangulation of the settled shape, not of the initial
#   shape. Every slider move wipes everything and rebuilds.
#
# The shape:
#   The Standard Saddle, at the viewer's default geometry.
#
# The input:
#   One slider. Edge cable pretension, in kN.
#
# History:
#   2026-10-09 - First version.
#   2026-10-09 - Rewritten to borrow the working q path.
#   2026-10-09 - Rewritten to pass a DICT of boundary q values.
#   2026-10-09 - Added the three-run chord-distance test.
#   2026-10-09 - Rewritten as a self-contained test with the
#                settled-shape retriangulation.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st


# =============================================================================
# LOCAL COPY OF engine/form_finding.py
# =============================================================================

def _orthonormal_basis(direction):
    d = np.asarray(direction, dtype=float)
    n = float(np.linalg.norm(d))
    if n < 1e-12:
        raise ValueError("direction vector has zero length")
    d = d / n
    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, d))) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    p = ref - float(np.dot(ref, d)) * d
    p = p / (float(np.linalg.norm(p)) + 1e-30)
    q = np.cross(d, p)
    q = q / (float(np.linalg.norm(q)) + 1e-30)
    return d, p, q


def solve_fdm(points, edges, fixed_indices, force_densities,
              loads=None, dir_only_indices=None):
    points = np.asarray(points, dtype=float)
    edges = list(edges)
    fixed_indices = list(fixed_indices)
    if dir_only_indices is None:
        dir_only_indices = []
    else:
        dir_only_indices = list(dir_only_indices)

    n = points.shape[0]
    m = len(edges)
    if n == 0:
        raise ValueError("No nodes supplied.")
    if m == 0:
        raise ValueError("No edges supplied.")

    if np.isscalar(force_densities):
        q = np.full(m, float(force_densities))
    else:
        q = np.asarray(force_densities, dtype=float)
        if q.shape[0] != m:
            raise ValueError("force_densities length mismatch")

    q_min = float(np.min(q))
    if q_min <= 0.0:
        raise ValueError("force_densities must be > 0 (min %g)" % q_min)

    if loads is None:
        loads = np.zeros((n, 3), dtype=float)
    else:
        loads = np.asarray(loads, dtype=float)

    fixed_mask = np.zeros(n, dtype=bool)
    for i in fixed_indices:
        if i < 0 or i >= n:
            raise ValueError("fixed index out of range")
        fixed_mask[i] = True

    dir_map = {}
    for entry in dir_only_indices:
        node_i, direction = entry
        node_i = int(node_i)
        if node_i < 0 or node_i >= n:
            raise ValueError("dir_only index out of range")
        if fixed_mask[node_i]:
            continue
        d, p, qv = _orthonormal_basis(direction)
        dir_map[node_i] = (d, p, qv)

    K = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(edges):
        qk = q[k]
        K[i, i] += qk
        K[j, j] += qk
        K[i, j] -= qk
        K[j, i] -= qk

    X = points.copy()
    dir_only_set = set(dir_map.keys())

    def _solve_axis(axis, mask_free):
        idx = np.where(mask_free)[0]
        idx_fixed = np.where(~mask_free)[0]
        if len(idx) == 0:
            return
        K_ff = K[np.ix_(idx, idx)]
        K_fx = K[np.ix_(idx, idx_fixed)]
        rhs = loads[idx, axis].copy()
        rhs -= K_fx @ points[idx_fixed, axis]
        X[idx, axis] = np.linalg.solve(K_ff, rhs)

    dir_arr = np.array(list(dir_only_set), dtype=int) if dir_only_set else np.array([], dtype=int)
    in_dir = np.zeros(n, dtype=bool)
    if len(dir_arr) > 0:
        in_dir[dir_arr] = True

    free_xy = (~fixed_mask) & (~in_dir)
    free_z = (~fixed_mask) & (~in_dir)

    _solve_axis(0, free_xy)
    _solve_axis(1, free_xy)
    _solve_axis(2, free_z)

    for node_i, (d, p, qv) in dir_map.items():
        K_ii = K[node_i, node_i] * np.eye(3)
        neigh_sum = np.zeros(3)
        for k, (a, b) in enumerate(edges):
            if a == node_i:
                neigh_sum -= q[k] * X[b]
            elif b == node_i:
                neigh_sum -= q[k] * X[a]
        residual_d = float(d @ (K_ii @ X[node_i] + neigh_sum - loads[node_i]))
        k_along = float(d @ (K_ii @ d))
        if abs(k_along) < 1e-12:
            continue
        alpha = -residual_d / k_along
        X[node_i] = X[node_i] + alpha * d

    residual = K @ X - loads
    free_all = ~fixed_mask
    residual_norm = float(np.linalg.norm(residual[free_all]))

    reactions = np.zeros((n, 3), dtype=float)
    for i in fixed_indices:
        reactions[i, :] = -residual[i, :] / 1000.0

    return {
        "coordinates": X,
        "residual_norm": residual_norm,
        "n_free": int(free_all.sum()) - len(dir_map) * 2,
        "n_fixed": int(fixed_mask.sum()),
        "reactions": reactions,
    }


def _edge_key(a, b):
    return (a, b) if a < b else (b, a)


def assign_anisotropic_q(edges, points_2d, warp_dir, warp_q, weft_q,
                         n_boundary=None, boundary_edge_q=None):
    edges = list(edges)
    points_2d = np.asarray(points_2d, dtype=float)
    m = len(edges)
    q = np.zeros(m, dtype=float)

    warp_dir = np.asarray(warp_dir, dtype=float)
    wn = float(np.linalg.norm(warp_dir))
    if wn < 1e-12:
        raise ValueError("warp_dir has zero length")
    warp_dir = warp_dir / wn

    if n_boundary is None:
        n_boundary = 0

    if isinstance(boundary_edge_q, dict):
        for k, (a, b) in enumerate(edges):
            is_b = (
                n_boundary > 0
                and a < n_boundary
                and b < n_boundary
                and (abs(a - b) == 1 or abs(a - b) == n_boundary - 1)
            )
            if is_b:
                key = _edge_key(int(a), int(b))
                val = boundary_edge_q.get(key, None)
                if val is None:
                    val = boundary_edge_q.get((key[1], key[0]), None)
                if val is not None:
                    q[k] = float(val)
                    continue
                q[k] = float(warp_q)
                continue
            pa = points_2d[a]
            pb = points_2d[b]
            d = pb - pa
            dn = float(np.linalg.norm(d))
            if dn < 1e-12:
                q[k] = float(warp_q)
                continue
            d = d / dn
            cos_t = float(np.dot(d, warp_dir))
            cos_t = max(-1.0, min(1.0, cos_t))
            cos2 = cos_t * cos_t
            sin2 = 1.0 - cos2
            q[k] = float(warp_q) * cos2 + float(weft_q) * sin2
        return q

    boundary_edge_q_scalar = float(warp_q) if boundary_edge_q is None else float(boundary_edge_q)

    for k, (a, b) in enumerate(edges):
        is_b = (
            n_boundary > 0
            and a < n_boundary
            and b < n_boundary
            and (abs(a - b) == 1 or abs(a - b) == n_boundary - 1)
        )
        if is_b:
            q[k] = boundary_edge_q_scalar
            continue
        pa = points_2d[a]
        pb = points_2d[b]
        d = pb - pa
        dn = float(np.linalg.norm(d))
        if dn < 1e-12:
            q[k] = float(warp_q)
            continue
        d = d / dn
        cos_t = float(np.dot(d, warp_dir))
        cos_t = max(-1.0, min(1.0, cos_t))
        cos2 = cos_t * cos_t
        sin2 = 1.0 - cos2
        q[k] = float(warp_q) * cos2 + float(weft_q) * sin2

    return q


def auto_warp_dir(points_2d):
    pts = np.asarray(points_2d, dtype=float)
    if pts.shape[0] < 2:
        return np.array([1.0, 0.0])
    dx = float(np.max(pts[:, 0]) - np.min(pts[:, 0]))
    dy = float(np.max(pts[:, 1]) - np.min(pts[:, 1]))
    if dx >= dy:
        return np.array([1.0, 0.0])
    return np.array([0.0, 1.0])


# =============================================================================
# LOCAL COPY OF engine/mesh_triangulated.py
# =============================================================================

def _point_in_polygon(x, y, polygon):
    n = polygon.shape[0]
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = float(polygon[i][0]), float(polygon[i][1])
        xj, yj = float(polygon[j][0]), float(polygon[j][1])
        if ((yi > y) != (yj > y)):
            x_intersect = (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi
            if x < x_intersect:
                inside = not inside
        j = i
    return inside


def _grid_interior_points(pts_2d, target_edge_length):
    pts_2d = np.asarray(pts_2d, dtype=float)
    h = float(target_edge_length)
    if h <= 0:
        return np.zeros((0, 2))
    xmin = float(np.min(pts_2d[:, 0]))
    xmax = float(np.max(pts_2d[:, 0]))
    ymin = float(np.min(pts_2d[:, 1]))
    ymax = float(np.max(pts_2d[:, 1]))
    xs = np.arange(xmin + 0.5 * h, xmax, h)
    ys = np.arange(ymin + 0.5 * h, ymax, h)
    candidates = []
    margin = 0.4 * h
    for x in xs:
        for y in ys:
            if not _point_in_polygon(x, y, pts_2d):
                continue
            too_close = False
            for k in range(pts_2d.shape[0]):
                d = np.hypot(x - pts_2d[k, 0], y - pts_2d[k, 1])
                if d < margin:
                    too_close = True
                    break
            if too_close:
                continue
            candidates.append((float(x), float(y)))
    if len(candidates) == 0:
        return np.zeros((0, 2))
    return np.asarray(candidates, dtype=float)


def _triangulate_all(all_pts_2d, n_boundary, pts_2d):
    from scipy.spatial import Delaunay
    tri = Delaunay(all_pts_2d)
    triangles_inside = []
    for simplex in tri.simplices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        cx = (all_pts_2d[a][0] + all_pts_2d[b][0] + all_pts_2d[c][0]) / 3.0
        cy = (all_pts_2d[a][1] + all_pts_2d[b][1] + all_pts_2d[c][1]) / 3.0
        if _point_in_polygon(cx, cy, pts_2d):
            triangles_inside.append((a, b, c))
    used = set()
    for (a, b, c) in triangles_inside:
        used.add(a)
        used.add(b)
        used.add(c)
    used_interior = sorted(i for i in used if i >= n_boundary)
    if len(used_interior) == 0:
        interior_pts = np.zeros((0, 2))
        remap = {}
    else:
        interior_pts = np.zeros((len(used_interior), 2))
        remap = {}
        for new_idx, old_idx in enumerate(used_interior):
            interior_pts[new_idx] = all_pts_2d[old_idx]
            remap[old_idx] = n_boundary + new_idx
    compacted = []
    for (a, b, c) in triangles_inside:
        na = a if a < n_boundary else remap.get(a, -1)
        nb = b if b < n_boundary else remap.get(b, -1)
        nc = c if c < n_boundary else remap.get(c, -1)
        if na < 0 or nb < 0 or nc < 0:
            continue
        compacted.append((na, nb, nc))
    return interior_pts, compacted


def _edges_from_triangles(triangles):
    seen = set()
    edges = []
    for (a, b, c) in triangles:
        for (i, j) in ((a, b), (b, c), (c, a)):
            if i == j:
                continue
            key = (i, j) if i < j else (j, i)
            if key not in seen:
                seen.add(key)
                edges.append(key)
    return edges


def _seg_of_node(n_boundary, anchor_indices):
    n_anchors = len(anchor_indices)
    seg = [-1] * n_boundary
    for k in range(n_anchors):
        start = anchor_indices[k]
        end = anchor_indices[(k + 1) % n_anchors]
        i = start
        while True:
            seg[i] = k
            if i == end:
                break
            i = (i + 1) % n_boundary
            if i == start:
                break
    return seg


def _compute_fixed_indices(n_boundary, anchor_indices, segment_types):
    seg_of_node = _seg_of_node(n_boundary, anchor_indices)
    anchor_set = set(anchor_indices)
    fixed = []
    for i in range(n_boundary):
        if i in anchor_set:
            fixed.append(i)
            continue
        seg_idx = seg_of_node[i]
        if seg_idx < 0:
            fixed.append(i)
            continue
        seg_type = segment_types[seg_idx]
        if seg_type in ("beam", "wall"):
            fixed.append(i)
    return sorted(set(fixed))


def _laplace_lift_2d(all_pts_2d, boundary_z, n_boundary):
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    from scipy.spatial import cKDTree
    n_nodes = all_pts_2d.shape[0]
    n_interior = n_nodes - n_boundary
    z_all = np.zeros(n_nodes)
    z_all[:n_boundary] = boundary_z
    if n_interior == 0:
        return z_all
    tree = cKDTree(all_pts_2d)
    k = min(8, n_nodes - 1)
    if k < 1:
        return z_all
    dists, idxs = tree.query(all_pts_2d, k=k + 1)
    rows, cols, data = [], [], []
    for i in range(n_nodes):
        nbrs = idxs[i, 1:]
        degree = len(nbrs)
        if degree == 0:
            continue
        rows.append(i)
        cols.append(i)
        data.append(float(degree))
        for j in nbrs:
            rows.append(i)
            cols.append(int(j))
            data.append(-1.0)
    L = sp.csr_matrix((data, (rows, cols)), shape=(n_nodes, n_nodes))
    int_idx = np.arange(n_boundary, n_nodes)
    bnd_idx = np.arange(0, n_boundary)
    L_ii = L[int_idx, :][:, int_idx]
    L_ib = L[int_idx, :][:, bnd_idx]
    rhs = -L_ib @ z_all[:n_boundary]
    z_interior = spla.spsolve(L_ii.tocsc(), rhs)
    z_all[int_idx] = z_interior
    return z_all


def _validate_boundary(boundary_loop):
    arr = np.asarray(boundary_loop, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("boundary_loop must be (n, 3)")
    if arr.shape[0] < 3:
        raise ValueError("boundary_loop must have >= 3 points")
    return arr


# =============================================================================
# THE TEST MESH BUILDER - rebuilds triangles after the FDM settle
# =============================================================================

def build_mesh_settled_triangulation(boundary_loop, anchor_indices,
                                      segment_types, target_edge_length,
                                      warp_q, weft_q, edge_q):
    """
    Same as build_mesh_triangulated, but the triangles returned are
    rebuilt fresh from the SETTLED coordinates. The FDM solve itself
    is unchanged. Every call rebuilds from scratch. No state carried
    between calls.
    """
    boundary = _validate_boundary(boundary_loop)
    n_boundary = boundary.shape[0]

    # ---- Plan projection ----
    pts_3d = boundary
    normal = np.array([0.0, 0.0, 1.0])
    origin = pts_3d.mean(axis=0)
    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, normal))) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    u = ref - np.dot(ref, normal) * normal
    u = u / (np.linalg.norm(u) + 1e-30)
    v = np.cross(normal, u)
    v = v / (np.linalg.norm(v) + 1e-30)
    centred = pts_3d - origin
    pts_2d = np.zeros((n_boundary, 2))
    for i in range(n_boundary):
        pts_2d[i, 0] = float(np.dot(centred[i], u))
        pts_2d[i, 1] = float(np.dot(centred[i], v))

    # ---- Interior candidates and initial triangulation ----
    interior_candidates = _grid_interior_points(pts_2d, target_edge_length)
    if interior_candidates.shape[0] > 0:
        all_pts_2d = np.vstack([pts_2d, interior_candidates])
    else:
        all_pts_2d = pts_2d.copy()

    interior_pts_2d, triangles_initial = _triangulate_all(
        all_pts_2d, n_boundary, pts_2d)

    n_interior = interior_pts_2d.shape[0]
    if n_interior > 0:
        all_pts_2d_full = np.vstack([pts_2d, interior_pts_2d])
    else:
        all_pts_2d_full = pts_2d.copy()

    # ---- Assemble 3D initial points ----
    all_points = np.zeros((all_pts_2d_full.shape[0], 3))
    for i in range(n_boundary):
        all_points[i] = pts_3d[i]

    if n_interior > 0:
        boundary_z = np.array([
            float(np.dot(p - origin, normal)) for p in pts_3d
        ])
        z_init = _laplace_lift_2d(all_pts_2d_full, boundary_z, n_boundary)
        for i in range(n_boundary, all_pts_2d_full.shape[0]):
            a = all_pts_2d_full[i, 0]
            b = all_pts_2d_full[i, 1]
            z = float(z_init[i])
            all_points[i] = origin + a * u + b * v + z * normal

    edges = _edges_from_triangles(triangles_initial)

    fixed_indices = _compute_fixed_indices(
        n_boundary, anchor_indices, segment_types)

    warp_dir = auto_warp_dir(pts_2d)

    q_dict = {}
    for i in range(n_boundary):
        j = (i + 1) % n_boundary
        key = (i, j) if i < j else (j, i)
        q_dict[key] = float(edge_q)

    q_aniso = assign_anisotropic_q(
        edges, all_pts_2d_full, warp_dir, warp_q, weft_q,
        n_boundary=n_boundary, boundary_edge_q=q_dict)

    # ---- FDM solve ----
    points_initial = all_points.copy()
    fdm_result = solve_fdm(
        all_points, edges, fixed_indices, q_aniso,
        dir_only_indices=None,
    )
    settled_points = fdm_result["coordinates"]

    # ---- REBUILD TRIANGLES FROM THE SETTLED SHAPE ----
    # Project the settled shape onto the same plan plane. Run Delaunay
    # on the settled plan positions. The result is the triangulation
    # of the settled shape, not of the initial shape.
    settled_centred = settled_points - origin
    settled_2d = np.zeros((settled_points.shape[0], 2))
    for i in range(settled_points.shape[0]):
        settled_2d[i, 0] = float(np.dot(settled_centred[i], u))
        settled_2d[i, 1] = float(np.dot(settled_centred[i], v))

    settled_interior_2d, triangles_settled = _triangulate_all(
        settled_2d, n_boundary, settled_2d[:n_boundary])

    # ---- Diagnostics for the triangulation ----
    tri_diag = _triangulation_diagnostics(
        settled_points, triangles_settled)

    return {
        "points": settled_points,
        "points_initial": points_initial,
        "edges": edges,
        "triangles": triangles_settled,
        "triangles_initial": triangles_initial,
        "fixed_indices": fixed_indices,
        "q": q_aniso,
        "n_boundary": n_boundary,
        "tri_diag": tri_diag,
        "residual_norm": fdm_result["residual_norm"],
    }


def _triangulation_diagnostics(points, triangles):
    areas = []
    aspect = []
    max_angles = []
    for tri in triangles:
        ia, ib, ic = int(tri[0]), int(tri[1]), int(tri[2])
        pa = points[ia]
        pb = points[ib]
        pc = points[ic]
        e_ab = float(np.linalg.norm(pb - pa))
        e_bc = float(np.linalg.norm(pc - pb))
        e_ca = float(np.linalg.norm(pa - pc))
        if e_ab <= 1e-12 or e_bc <= 1e-12 or e_ca <= 1e-12:
            areas.append(0.0)
            aspect.append(0.0)
            max_angles.append(180.0)
            continue
        n_vec = np.cross(pb - pa, pc - pa)
        area = 0.5 * float(np.linalg.norm(n_vec))
        areas.append(area)
        perimeter = e_ab + e_bc + e_ca
        # aspect ratio = longest edge / (2 * inradius); using the
        # ratio (longest / shortest) as a simpler and clearly
        # interpretable measure.
        aspect.append(max(e_ab, e_bc, e_ca) / min(e_ab, e_bc, e_ca))
        # max corner angle using the law of cosines
        a2 = e_bc * e_bc
        b2 = e_ca * e_ca
        c2 = e_ab * e_ab
        cos_a = (b2 + c2 - a2) / (2.0 * math.sqrt(b2 * c2) + 1e-30)
        cos_b = (a2 + c2 - b2) / (2.0 * math.sqrt(a2 * c2) + 1e-30)
        cos_c = (a2 + b2 - c2) / (2.0 * math.sqrt(a2 * b2) + 1e-30)
        ang_a = math.degrees(math.acos(max(-1.0, min(1.0, cos_a))))
        ang_b = math.degrees(math.acos(max(-1.0, min(1.0, cos_b))))
        ang_c = math.degrees(math.acos(max(-1.0, min(1.0, cos_c))))
        max_angles.append(max(ang_a, ang_b, ang_c))

    n_slivers = sum(1 for a in max_angles if a > 170.0)
    n_zero_area = sum(1 for a in areas if a < 1e-9)

    return {
        "n_triangles": len(triangles),
        "min_area": float(np.min(areas)) if areas else 0.0,
        "max_area": float(np.max(areas)) if areas else 0.0,
        "mean_area": float(np.mean(areas)) if areas else 0.0,
        "min_aspect": float(np.min(aspect)) if aspect else 0.0,
        "max_aspect": float(np.max(aspect)) if aspect else 0.0,
        "mean_aspect": float(np.mean(aspect)) if aspect else 0.0,
        "n_slivers": int(n_slivers),
        "n_zero_area": int(n_zero_area),
        "max_corner_angle": float(np.max(max_angles)) if max_angles else 0.0,
    }


# =============================================================================
# SADDLE BOUNDARY BUILDER
# =============================================================================

def _build_saddle_boundary(span, apex, rise, anchor_count, mesh_spacing):
    """
    The Standard Saddle boundary, same geometry as the viewer.
    Two parabolic beam curves, two tips. Eight anchors per beam by
    default. Boundary loop closed through both beams.
    """
    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = rise * (1.0 - (2.0 * x / span) ** 2)

    s = np.zeros(n_pts)
    for i in range(1, n_pts):
        s[i] = s[i - 1] + float(np.hypot(x[i] - x[i - 1],
                                          z_beam[i] - z_beam[i - 1]))
    total = s[-1] if s[-1] > 1e-12 else 1.0

    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    arc_targets = np.linspace(0.0, total, anchor_count)
    seg_arc = total / float(anchor_count - 1) if anchor_count > 1 else total
    sub = max(1, min(20, int(round(seg_arc / float(mesh_spacing)))))

    def _beam_points(y_curve, reverse=False):
        pts = []
        anchors_local = []
        for k in range(anchor_count):
            target = arc_targets[k]
            bx = float(np.interp(target, s, x))
            bz = float(np.interp(target, s, z_beam))
            by = float(np.interp(target, s, y_curve))
            anchors_local.append(len(pts))
            pts.append((bx, by, bz))
            if k < anchor_count - 1:
                a0 = arc_targets[k]
                a1 = arc_targets[k + 1]
                for j in range(1, sub + 1):
                    frac = float(j) / float(sub + 1)
                    tm = a0 + (a1 - a0) * frac
                    mx = float(np.interp(tm, s, x))
                    mz = float(np.interp(tm, s, z_beam))
                    my = float(np.interp(tm, s, y_curve))
                    pts.append((mx, my, mz))
        if reverse:
            n = len(pts)
            rev_pts = [pts[n - 1 - i] for i in range(n)]
            rev_anchors = [n - 1 - a for a in anchors_local]
            return rev_pts, rev_anchors
        return pts, anchors_local

    beam_L_pts, beam_L_anchors = _beam_points(y1, reverse=False)
    beam_R_pts, beam_R_anchors = _beam_points(y2, reverse=True)

    loop = list(beam_L_pts)
    for i in range(1, len(beam_R_pts) - 1):
        loop.append(beam_R_pts[i])

    boundary_loop = np.asarray(loop, dtype=float)

    anchors = list(beam_L_anchors)
    offset = len(beam_L_pts)
    for a in beam_R_anchors:
        if a == 0:
            continue
        if a == len(beam_R_pts) - 1:
            continue
        anchors.append(offset + (a - 1))
    anchors = sorted(set(anchors))

    n_loop = boundary_loop.shape[0]
    n_a = len(anchors)
    segments = []
    for k in range(n_a):
        aa = anchors[k]
        bb = anchors[(k + 1) % n_a]
        interior = []
        i = (aa + 1) % n_loop
        safety = 0
        while i != bb and safety < n_loop:
            interior.append(i)
            i = (i + 1) % n_loop
            safety += 1
        segments.append({"anchor_a": int(aa), "anchor_b": int(bb),
                         "interior": interior})

    segment_types = ["cable"] * n_a
    return boundary_loop, anchors, segment_types


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_tester_star_diagnostic():
    st.markdown("## Star Diagnostic")
    st.markdown(
        "One slider. Edge cable pretension. Everything else fixed at "
        "the Standard Saddle defaults. On Run, the FDM solve is "
        "performed as usual, and the triangulation displayed is "
        "rebuilt fresh from the settled shape."
    )

    # ---- Fixed geometry (viewer defaults) ----
    span = 10.0
    apex = 10.0
    rise = 6.2
    anchor_count = 8
    mesh_spacing = 0.5
    warp_pre = 2.0   # kN/m
    weft_pre = 2.0   # kN/m

    st.markdown(
        "**Shape.** Span %.1f m, apex %.1f m, rise %.1f m, "
        "anchors/beam %d, mesh spacing %.2f m, warp %.2f, weft %.2f"
        % (span, apex, rise, anchor_count, mesh_spacing,
           warp_pre, weft_pre)
    )

    edge_pre = st.slider(
        "Edge cable pretension (kN)",
        min_value=0.1, max_value=100.0, value=10.0, step=0.1,
        key="star_diag_edge",
    )

    run = st.button("Run", key="star_diag_run",
                    use_container_width=True, type="primary")

    if not run:
        return

    boundary_loop, anchors, segment_types = _build_saddle_boundary(
        span, apex, rise, anchor_count, mesh_spacing)

    n = boundary_loop.shape[0]
    total_len = 0.0
    for i in range(n):
        p0 = boundary_loop[i]
        p1 = boundary_loop[(i + 1) % n]
        total_len += float(np.linalg.norm(p1 - p0))
    L_avg = total_len / float(n) if n > 0 else 1.0
    if L_avg < 1e-9:
        L_avg = 1.0

    baseline_kN_per_m = 2.0
    ratio_limit = 4.0
    warp_input = max(0.1, float(warp_pre))
    weft_input = max(0.1, float(weft_pre))
    mean_input = 0.5 * (warp_input + weft_input)
    if mean_input < 1e-9:
        mean_input = 1.0
    warp_rel = warp_input / mean_input
    weft_rel = weft_input / mean_input
    if warp_rel / weft_rel > ratio_limit:
        warp_rel = ratio_limit * weft_rel
    if weft_rel / warp_rel > ratio_limit:
        weft_rel = ratio_limit * warp_rel    warp_q = baseline_kN_per_m * warp_rel * 1000.0 / L_avg
    weft_q = baseline_kN_per_m * weft_rel * 1000.0 / L_avg
    edge_q = float(edge_pre) * 1000.0 / L_avg

    with st.spinner("Running form-finding and rebuilding triangulation..."):
        built = build_mesh_settled_triangulation(
            boundary_loop=boundary_loop,
            anchor_indices=anchors,
            segment_types=segment_types,
            target_edge_length=mesh_spacing,
            warp_q=warp_q,
            weft_q=weft_q,
            edge_q=edge_q,
        )

    points = built["points"]
    triangles = built["triangles"]
    n_boundary = built["n_boundary"]
    tri_diag = built["tri_diag"]

    # ---- 3D view of the settled shape ----
    node_x = points[:, 0].tolist()
    node_y = points[:, 1].tolist()
    node_z = points[:, 2].tolist()
    tri_i = [int(t[0]) for t in triangles]
    tri_j = [int(t[1]) for t in triangles]
    tri_k = [int(t[2]) for t in triangles]

    fig = go.Figure()
    fig.add_trace(go.Mesh3d(
        x=node_x, y=node_y, z=node_z,
        i=tri_i, j=tri_j, k=tri_k,
        color="#4a7a9c", opacity=0.55, flatshading=True,
        name="Membrane", showlegend=False, hoverinfo="skip",
    ))
    # Boundary loop
    bx = [float(points[i][0]) for i in range(n_boundary)]
    by = [float(points[i][1]) for i in range(n_boundary)]
    bz = [float(points[i][2]) for i in range(n_boundary)]
    bx.append(bx[0]); by.append(by[0]); bz.append(bz[0])
    fig.add_trace(go.Scatter3d(
        x=bx, y=by, z=bz, mode="lines+markers",
        line=dict(color="#f1c40f", width=4),
        marker=dict(color="#f1c40f", size=3),
        name="Boundary", showlegend=False, hoverinfo="skip",
    ))
    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)", yaxis_title="Y (m)", zaxis_title="Z (m)",
            bgcolor="#0a0e17",
            xaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            yaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            zaxis=dict(gridcolor="#2a3441", color="#e6edf3"),
            aspectmode="data",
        ),
        paper_bgcolor="#0a0e17",
        font=dict(color="#e6edf3"),
        margin=dict(l=0, r=0, t=20, b=0),
        height=460,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---- Summary ----
    st.markdown("**Triangulation of the settled shape**")
    st.markdown(
        "- Triangles: " + str(tri_diag["n_triangles"])
        + "  |  Slivers (>170 deg): " + str(tri_diag["n_slivers"])
        + "  |  Zero-area: " + str(tri_diag["n_zero_area"])
    )
    st.markdown(
        "- Area min: %.6e  |  mean: %.6e  |  max: %.6e"
        % (tri_diag["min_area"], tri_diag["mean_area"],
           tri_diag["max_area"])
    )
    st.markdown(
        "- Aspect min: %.3f  |  mean: %.3f  |  max: %.3f"
        % (tri_diag["min_aspect"], tri_diag["mean_aspect"],
           tri_diag["max_aspect"])
    )
    st.markdown(
        "- Max corner angle: %.2f deg" % tri_diag["max_corner_angle"]
    )
    st.markdown(
        "- FDM residual: %.4e  |  Edge cable pretension: %.3f kN"
        % (built["residual_norm"], float(edge_pre))
    )

    if tri_diag["n_slivers"] == 0 and tri_diag["n_zero_area"] == 0:
        st.markdown(
            "**VERDICT: clean triangulation of the settled shape. "
            "No slivers, no zero-area triangles.**"
        )
    else:
        st.markdown(
            "**VERDICT: triangulation has artifacts.** "
            "See sliver and zero-area counts above."
        )


# =============================================================================
# END OF ui/workshops/tester_star_diagnostic.py
# =============================================================================
