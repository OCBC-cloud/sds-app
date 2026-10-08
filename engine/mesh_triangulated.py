# =============================================================================
# SDSe Engine - Triangulated Mesh Builder
# =============================================================================
# Builds a triangulated mesh from a closed boundary loop.
# One method. Every shape. See engine/SPEC_mesh_triangulation.md.
#
# The method:
#   1. Project the boundary onto a plan plane.
#   2. Constrained Delaunay triangulation of the polygon,
#      with interior points generated on a grid.
#   3. Lift the interior nodes to 3D with a Laplace solve
#      on the triangulation (not mean-z).
#   4. Assemble points, edges, triangles, fixed, q.
#
# The solver (solve_fdm) is unchanged. It takes points,
# edges, fixed_indices, and q. The triangulation engine
# produces all four.
#
# Vocabulary (fixed):
#   boundary loop   - a closed sequence of 3D points.
#   anchor          - a point where two segments meet.
#                     Always held.
#   segment         - the gap between two anchors.
#   segment type    - beam, cable, or wall.
#
# Hold rule:
#   Anchor                  -> always held.
#   Segment interior, beam  -> held.
#   Segment interior, wall  -> held.
#   Segment interior, cable -> released.
#   Interior mesh nodes     -> always released.
#
# The cable interior nodes are held because a taut cable in
# a form-finding context has negligible sag. Its nodes are
# pinned between the anchors. Without this, the FDM solve
# pulls the boundary interior nodes inward and the shape
# collapses into a star. The cable does not "hold" its own
# nodes in the beam sense - it is held by its own tension.
# This matches the standard practice of FDM form-finding
# tools, which treat a taut cable as a polygon of anchors.
#
# Force densities:
#   Boundary edge on beam or wall segment: warp_q.
#   Boundary edge on cable segment:        edge_q.
#   Interior edge:                         weft_q.
#
# Updated 2026-10-05:
#   - edge_q may be a scalar (uniform) or a dict keyed by
#     (i, j) mesh node pairs (per-edge). When a dict is
#     provided, it is passed to assign_anisotropic_q as
#     boundary_edge_q.
#
# Updated 2026-10-08:
#   - Cable segment interior nodes are now held. A taut
#     cable has negligible sag; its nodes are pinned between
#     anchors. This prevents the FDM from pulling the
#     boundary into a star.
#
# Dependencies:
#   scipy.spatial.Delaunay and scipy.sparse.
#   scipy is on Streamlit Cloud.
#
# History:
#   2026-09-30 - First build.
#   2026-10-01 - Interior points and Laplace lift.
#   2026-10-05 - Per-edge edge_q support.
#   2026-10-08 - Cable segment interior nodes held.
# =============================================================================

import numpy as np


_VALID_TYPES = ("beam", "cable", "wall")


# =============================================================================
# VALIDATION
# =============================================================================

def _validate_boundary(boundary_loop):
    arr = np.asarray(boundary_loop, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError(
            "boundary_loop must be (n, 3) array (got shape %s)"
            % str(arr.shape)
        )
    if arr.shape[0] < 3:
        raise ValueError(
            "boundary_loop must have at least 3 points (got %d)"
            % arr.shape[0]
        )
    return arr


def _validate_anchors(anchor_indices, n_boundary):
    if anchor_indices is None:
        return list(range(n_boundary))
    anchors = sorted(set(int(i) for i in anchor_indices))
    for i in anchors:
        if i < 0 or i >= n_boundary:
            raise ValueError(
                "anchor index %d out of range [0, %d)"
                % (i, n_boundary)
            )
    return anchors


def _validate_segment_types(segment_types, n_segments):
    if segment_types is None:
        return ["cable"] * n_segments
    segment_types = list(segment_types)
    if len(segment_types) != n_segments:
        raise ValueError(
            "segment_types length %d does not match %d segments"
            % (len(segment_types), n_segments)
        )
    for k, t in enumerate(segment_types):
        if t not in _VALID_TYPES:
            raise ValueError(
                "segment_types[%d] must be one of %s (got %r)"
                % (k, list(_VALID_TYPES), t)
            )
    return segment_types


def _validate_target_edge_length(length, boundary_loop):
    if length is None:
        n = boundary_loop.shape[0]
        total = 0.0
        for k in range(n):
            p0 = boundary_loop[k]
            p1 = boundary_loop[(k + 1) % n]
            total += float(np.linalg.norm(p1 - p0))
        length = total / float(n)
    length = float(length)
    if length <= 0:
        raise ValueError(
            "target_edge_length must be > 0 (got %g)" % length
        )
    return length


# =============================================================================
# PLAN PROJECTION
# =============================================================================

def _project_to_plane(boundary_loop, plan_plane):
    pts_3d = np.asarray(boundary_loop, dtype=float)

    if plan_plane is None:
        normal = np.array([0.0, 0.0, 1.0])
        origin = pts_3d.mean(axis=0)
    else:
        normal = np.asarray(plan_plane[0], dtype=float)
        origin = np.asarray(plan_plane[1], dtype=float)
        n = np.linalg.norm(normal)
        if n < 1e-12:
            raise ValueError("plan_plane normal has zero length")
        normal = normal / n

    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, normal))) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    u = ref - np.dot(ref, normal) * normal
    u = u / (np.linalg.norm(u) + 1e-30)
    v = np.cross(normal, u)
    v = v / (np.linalg.norm(v) + 1e-30)

    centred = pts_3d - origin
    pts_2d = np.zeros((pts_3d.shape[0], 2))
    for i in range(pts_3d.shape[0]):
        pts_2d[i, 0] = float(np.dot(centred[i], u))
        pts_2d[i, 1] = float(np.dot(centred[i], v))

    return pts_2d, pts_3d, normal, origin


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


# =============================================================================
# TRIANGULATION
# =============================================================================

def _triangulate_polygon(pts_2d, target_edge_length):
    from scipy.spatial import Delaunay

    pts_2d = np.asarray(pts_2d, dtype=float)
    n_boundary = pts_2d.shape[0]

    interior_candidates = _grid_interior_points(
        pts_2d, target_edge_length
    )

    if interior_candidates.shape[0] > 0:
        all_pts = np.vstack([pts_2d, interior_candidates])
    else:
        all_pts = pts_2d.copy()

    tri = Delaunay(all_pts)

    tri_indices = tri.simplices
    triangles_inside = []
    for simplex in tri_indices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        cx = (all_pts[a][0] + all_pts[b][0] + all_pts[c][0]) / 3.0
        cy = (all_pts[a][1] + all_pts[b][1] + all_pts[c][1]) / 3.0
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
            interior_pts[new_idx] = all_pts[old_idx]
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


# =============================================================================
# EDGES
# =============================================================================

def _edges_from_triangles(triangles, n_points):
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


# =============================================================================
# FIXED INDICES
# =============================================================================

def _compute_fixed_indices(boundary_loop, anchor_indices, segment_types):
    n = boundary_loop.shape[0]
    n_anchors = len(anchor_indices)

    seg_of_node = [-1] * n
    for k in range(n_anchors):
        start = anchor_indices[k]
        end = anchor_indices[(k + 1) % n_anchors]
        i = start
        while True:
            seg_of_node[i] = k
            if i == end:
                break
            i = (i + 1) % n
            if i == start:
                break

    anchor_set = set(anchor_indices)

    fixed = []
    for i in range(n):
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


# =============================================================================
# FORCE DENSITIES
# =============================================================================

def _compute_q(edges, n_boundary, boundary_loop, anchor_indices,
               segment_types, warp_q, weft_q, edge_q):
    n_anchors = len(anchor_indices)
    n = n_boundary

    seg_of_node = [-1] * n
    for k in range(n_anchors):
        start = anchor_indices[k]
        end = anchor_indices[(k + 1) % n_anchors]
        i = start
        while True:
            seg_of_node[i] = k
            if i == end:
                break
            i = (i + 1) % n
            if i == start:
                break

    boundary_pair_set = set()
    for i in range(n):
        j = (i + 1) % n
        key = (i, j) if i < j else (j, i)
        boundary_pair_set.add(key)

    q = np.zeros(len(edges))
    for k, (a, b) in enumerate(edges):
        key = (a, b) if a < b else (b, a)
        if key in boundary_pair_set:
            seg_a = seg_of_node[a] if a < n else -1
            seg_b = seg_of_node[b] if b < n else -1
            seg_idx = seg_a if seg_a >= 0 else seg_b
            if seg_idx < 0:
                q[k] = float(weft_q)
                continue
            seg_type = segment_types[seg_idx]
            if seg_type == "cable":
                q[k] = float(edge_q)
            else:
                q[k] = float(warp_q)
        else:
            q[k] = float(weft_q)
    return q


# =============================================================================
# LAPLACE LIFT (2D -> 3D)
# =============================================================================

def _laplace_lift(points_2d, normal, origin, boundary_z, n_boundary):
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    from scipy.spatial import cKDTree

    n_nodes = points_2d.shape[0]
    n_interior = n_nodes - n_boundary

    z_all = np.zeros(n_nodes)
    z_all[:n_boundary] = boundary_z

    if n_interior == 0:
        return z_all

    tree = cKDTree(points_2d)
    k = min(8, n_nodes - 1)
    if k < 1:
        return z_all
    dists, idxs = tree.query(points_2d, k=k + 1)

    rows = []
    cols = []
    data = []

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

    L = sp.csr_matrix(
        (data, (rows, cols)),
        shape=(n_nodes, n_nodes)
    )

    int_idx = np.arange(n_boundary, n_nodes)
    bnd_idx = np.arange(0, n_boundary)

    L_ii = L[int_idx, :][:, int_idx]
    L_ib = L[int_idx, :][:, bnd_idx]

    rhs = -L_ib @ z_all[:n_boundary]

    z_interior = spla.spsolve(L_ii.tocsc(), rhs)

    z_all[int_idx] = z_interior
    return z_all


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def build_mesh_triangulated(
    boundary_loop,
    anchor_indices=None,
    segment_types=None,
    target_edge_length=None,
    plan_plane=None,
    warp_q=2000.0,
    weft_q=2000.0,
    edge_q=5000.0,
):
    """
    Build a triangulated mesh from a closed boundary loop.

    Parameters
    ----------
    edge_q : float or dict
        Scalar: uniform force density on cable boundary edges.
        Dict: per-edge values, keyed by (i, j) mesh node pairs
        (sorted). Missing keys fall back to the pull-back value
        computed from the membrane equilibrium if pull-back is
        available, else warp_q. See assign_anisotropic_q.

    See engine/SPEC_mesh_triangulation.md for the full design.
    """
    boundary = _validate_boundary(boundary_loop)
    n_boundary = boundary.shape[0]

    anchors = _validate_anchors(anchor_indices, n_boundary)
    n_segments = len(anchors)
    seg_types = _validate_segment_types(segment_types, n_segments)
    target_len = _validate_target_edge_length(
        target_edge_length, boundary
    )

    pts_2d, pts_3d, normal, origin = _project_to_plane(
        boundary, plan_plane
    )

    interior_pts_2d, triangles = _triangulate_polygon(
        pts_2d, target_len
    )
    n_interior = interior_pts_2d.shape[0]

    if n_interior > 0:
        all_pts_2d = np.vstack([pts_2d, interior_pts_2d])
    else:
        all_pts_2d = pts_2d.copy()

    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, normal))) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    u = ref - np.dot(ref, normal) * normal
    u = u / (np.linalg.norm(u) + 1e-30)
    v = np.cross(normal, u)
    v = v / (np.linalg.norm(v) + 1e-30)

    all_points = np.zeros((all_pts_2d.shape[0], 3))
    for i in range(pts_3d.shape[0]):
        all_points[i] = pts_3d[i]

    if n_interior > 0:
        boundary_z = np.array([
            float(np.dot(p - origin, normal)) for p in pts_3d
        ])
        z_init = _laplace_lift(
            all_pts_2d, normal, origin, boundary_z, n_boundary
        )
        for i in range(pts_3d.shape[0], all_pts_2d.shape[0]):
            a = all_pts_2d[i, 0]
            b = all_pts_2d[i, 1]
            z = float(z_init[i])
            all_points[i] = origin + a * u + b * v + z * normal
    else:
        for i in range(pts_3d.shape[0], all_pts_2d.shape[0]):
            a = all_pts_2d[i, 0]
            b = all_pts_2d[i, 1]
            all_points[i] = origin + a * u + b * v

    edges = _edges_from_triangles(triangles, all_points.shape[0])

    fixed_boundary = _compute_fixed_indices(
        boundary, anchors, seg_types
    )
    fixed_indices = list(fixed_boundary)

    from engine.form_finding import (
        assign_anisotropic_q,
        auto_warp_dir,
        solve_fdm,
    )

    warp_dir = auto_warp_dir(pts_2d)

    q_aniso = assign_anisotropic_q(
        edges,
        all_pts_2d,
        warp_dir,
        warp_q,
        weft_q,
        n_boundary=n_boundary,
        boundary_edge_q=edge_q,
    )

    points_initial = all_points.copy()

    fdm_result = None
    if len(fixed_indices) > 0:
        fdm_result = solve_fdm(
            all_points,
            edges,
            fixed_indices,
            q_aniso,
        )
        all_points = fdm_result["coordinates"]

    diagnostics = {
        "n_nodes": int(all_points.shape[0]),
        "n_edges": len(edges),
        "n_triangles": len(triangles),
        "n_fixed": len(fixed_indices),
        "n_free": int(all_points.shape[0]) - len(fixed_indices),
        "n_boundary": int(n_boundary),
        "n_interior": int(n_interior),
        "n_anchors": len(anchors),
        "n_segments": n_segments,
        "target_edge_length": float(target_len),
        "anchor_indices": list(anchors),
        "segment_types": list(seg_types),
        "plan_normal": [float(vv) for vv in normal],
        "plan_origin": [float(vv) for vv in origin],
        "warp_dir": [float(vv) for vv in warp_dir],
        "lift_used": "fdm_anisotropic",
        "structural_connections": [],
    }

    return {
        "points": all_points,
        "points_initial": points_initial,
        "edges": edges,
        "triangles": triangles,
        "fixed_indices": fixed_indices,
        "q": q_aniso,
        "diagnostics": diagnostics,
    }


# =============================================================================
# END OF engine/mesh_triangulated.py
# =============================================================================
