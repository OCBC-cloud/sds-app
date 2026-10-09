# =============================================================================
# SDSe Engine - Triangulated Mesh Builder
# =============================================================================
# Builds a triangulated mesh from a closed boundary loop.
# One method. Every shape. See engine/SPEC_mesh_triangulation.md.
#
# The method:
#   1. Project the boundary onto a plan plane.
#   2. Triangulate the boundary and interior candidates (Delaunay).
#   3. Lift the interior nodes to 3D with a Laplace solve.
#   4. Assemble points, edges, triangles.
#   5. Solve FDM on the initial mesh.
#   6. Rebuild the triangulation from the SETTLED coordinates.
#   7. Return the settled points and the fresh triangles.
#
# The key architectural point (added 2026-10-09):
#   The triangulation returned to the caller is the triangulation of
#   the SETTLED shape, not of the initial shape. The FDM solve runs
#   on the initial mesh exactly as before, and the physics, the
#   forces, the reactions, and the q values are unchanged. What is
#   changed is only which triangles the caller receives.
#
#   This is what stops the star and the jagged edges. When the
#   triangulation the user sees is rebuilt from the settled shape,
#   there is no feedback from the triangulation back into the solve.
#   Every call rebuilds from scratch. Every edit by the user wipes
#   the previous triangulation.
#
# Vocabulary (fixed):
#   boundary loop   - a closed sequence of 3D points.
#   anchor          - a point where two segments meet. Always held.
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
# Directional constraint (kept as an active capability):
#   A caller may pass use_dir_constraint=True to build_mesh_triangulated.
#   When True, cable interior nodes are passed to solve_fdm with their
#   local cable tangent as a directional constraint. The node is free
#   along the tangent and fixed in the two axes perpendicular to it.
#   Used today only when a caller explicitly asks for it. Available in
#   the future for a fixed node along a wall, a mast base, or any
#   other partially constrained support.
#
# Force densities:
#   Boundary edge on beam or wall segment: warp_q.
#   Boundary edge on cable segment:        edge_q.
#   Interior edge:                         weft_q.
#
# Dependencies:
#   scipy.spatial.Delaunay and scipy.sparse.
#   scipy is on Streamlit Cloud.
#
# History:
#   2026-09-30 - First build.
#   2026-10-01 - Interior points and Laplace lift.
#   2026-10-05 - Per-edge edge_q support.
#   2026-10-08 - Header comment drift corrected.
#   2026-10-09 - Triangulation rebuilt from the settled shape.
#                Fixed the settled retriangulation to call Delaunay
#                directly, not through the interior grid generator.
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

def _plan_basis(plan_plane, pts_3d):
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
    return normal, origin, u, v


def _project_points(pts_3d, origin, u, v):
    centred = pts_3d - origin
    pts_2d = np.zeros((pts_3d.shape[0], 2))
    for i in range(pts_3d.shape[0]):
        pts_2d[i, 0] = float(np.dot(centred[i], u))
        pts_2d[i, 1] = float(np.dot(centred[i], v))
    return pts_2d


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
    """
    Triangulate the polygon defined by pts_2d (the boundary), with
    interior grid candidates added. Returns (interior_pts_2d,
    triangles) where triangles reference indices into
    np.vstack([pts_2d, interior_pts_2d]).
    """
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


def _triangulate_settled(settled_points, n_boundary, origin, u, v):
    """
    Rebuild the triangulation from the SETTLED coordinates.

    Projects the settled shape onto the same plan plane, runs
    Delaunay on the settled plan positions directly (no new
    interior candidates are added, because the settled points
    already include the interior nodes placed by the initial
    triangulation), filters to the settled boundary polygon, and
    returns the triangles.
    """
    from scipy.spatial import Delaunay

    settled_2d = _project_points(settled_points, origin, u, v)
    settled_boundary_2d = settled_2d[:n_boundary]

    tri = Delaunay(settled_2d)
    triangles_inside = []
    for simplex in tri.simplices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        cx = (settled_2d[a][0] + settled_2d[b][0] + settled_2d[c][0]) / 3.0
        cy = (settled_2d[a][1] + settled_2d[b][1] + settled_2d[c][1]) / 3.0
        if _point_in_polygon(cx, cy, settled_boundary_2d):
            triangles_inside.append((a, b, c))
    return triangles_inside


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
# SEGMENTS AND FIXED INDICES
# =============================================================================

def _compute_seg_of_node(boundary_loop, anchor_indices):
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
    return seg_of_node


def _compute_fixed_indices(boundary_loop, anchor_indices, segment_types):
    n = boundary_loop.shape[0]
    seg_of_node = _compute_seg_of_node(boundary_loop, anchor_indices)
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


def _compute_cable_dir_indices(boundary_loop, anchor_indices, segment_types):
    """
    Optional: for each cable-segment interior boundary node, return
    its local cable tangent. Dormant capability. Passed to solve_fdm
    only when the caller asks for it (use_dir_constraint=True).
    """
    n = boundary_loop.shape[0]
    seg_of_node = _compute_seg_of_node(boundary_loop, anchor_indices)
    anchor_set = set(anchor_indices)

    result = []
    for i in range(n):
        if i in anchor_set:
            continue
        seg_idx = seg_of_node[i]
        if seg_idx < 0:
            continue
        if segment_types[seg_idx] != "cable":
            continue
        prev_idx = (i - 1) % n
        next_idx = (i + 1) % n
        tangent = boundary_loop[next_idx] - boundary_loop[prev_idx]
        mag = float(np.linalg.norm(tangent))
        if mag < 1e-12:
            continue
        tangent = tangent / mag
        result.append((int(i), (float(tangent[0]),
                                 float(tangent[1]),
                                 float(tangent[2]))))
    return result


# =============================================================================
# LAPLACE LIFT (2D -> 3D)
# =============================================================================

def _laplace_lift(all_pts_2d, boundary_z, n_boundary):
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

    L = sp.csr_matrix((data, (rows, cols)), shape=(n_nodes, n_nodes))

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
    use_dir_constraint=False,
):
    """
    Build a triangulated mesh from a closed boundary loop.

    The FDM solve runs on the initial mesh, exactly as before. The
    triangles returned to the caller are rebuilt fresh from the
    SETTLED coordinates.

    Parameters
    ----------
    edge_q : float or dict
        Scalar: uniform force density on cable boundary edges.
        Dict: per-edge values, keyed by (i, j) mesh node pairs
        (sorted).
    use_dir_constraint : bool
        If True, cable interior nodes are passed to solve_fdm with
        their local cable tangent as a directional constraint. This
        is optional and off by default. The current form-finding
        path relies on the settled-shape rebuild, not on this
        constraint, to keep the boundary clean. The capability is
        available for callers that need a node held to a line.

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

    normal, origin, u, v = _plan_basis(plan_plane, boundary)
    pts_2d = _project_points(boundary, origin, u, v)

    interior_pts_2d, triangles_initial = _triangulate_polygon(
        pts_2d, target_len
    )
    n_interior = interior_pts_2d.shape[0]

    if n_interior > 0:
        all_pts_2d = np.vstack([pts_2d, interior_pts_2d])
    else:
        all_pts_2d = pts_2d.copy()

    all_points = np.zeros((all_pts_2d.shape[0], 3))
    for i in range(n_boundary):
        all_points[i] = boundary[i]

    if n_interior > 0:
        boundary_z = np.array([
            float(np.dot(p - origin, normal)) for p in boundary
        ])
        z_init = _laplace_lift(all_pts_2d, boundary_z, n_boundary)
        for i in range(n_boundary, all_pts_2d.shape[0]):
            a = all_pts_2d[i, 0]
            b = all_pts_2d[i, 1]
            z = float(z_init[i])
            all_points[i] = origin + a * u + b * v + z * normal

    edges = _edges_from_triangles(triangles_initial, all_points.shape[0])

    fixed_indices = _compute_fixed_indices(
        boundary, anchors, seg_types
    )

    dir_only_indices = []
    if use_dir_constraint:
        dir_only_indices = _compute_cable_dir_indices(
            boundary, anchors, seg_types
        )

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
            dir_only_indices=dir_only_indices if use_dir_constraint else None,
        )
        settled_points = fdm_result["coordinates"]
    else:
        settled_points = all_points

    triangles_settled = _triangulate_settled(
        settled_points, n_boundary, origin, u, v
    )

    diagnostics = {
        "n_nodes": int(settled_points.shape[0]),
        "n_edges": len(edges),
        "n_triangles": len(triangles_settled),
        "n_triangles_initial": len(triangles_initial),
        "n_fixed": len(fixed_indices),
        "n_dir_only": len(dir_only_indices),
        "n_free": int(settled_points.shape[0]) - len(fixed_indices),
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
        "lift_used": "fdm_anisotropic_settled_triangulation",
        "structural_connections": [],
    }

    return {
        "points": settled_points,
        "points_initial": points_initial,
        "edges": edges,
        "triangles": triangles_settled,
        "triangles_initial": triangles_initial,
        "fixed_indices": fixed_indices,
        "dir_only_indices": dir_only_indices,
        "q": q_aniso,
        "diagnostics": diagnostics,
    }


# =============================================================================
# END OF engine/mesh_triangulated.py
# =============================================================================
