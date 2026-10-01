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
# Force densities:
#   Boundary edge on beam or wall segment: warp_q.
#   Boundary edge on cable segment:        edge_q.
#   Interior edge:                         weft_q.
#
# Dependencies:
#   scipy.spatial.Delaunay and scipy.sparse.
#   scipy is on Streamlit Cloud.
#   The `triangle` package is NOT used: it cannot be built
#   on Streamlit Cloud. See SPEC_mesh_triangulation.md
#   section 10.
#
# History:
#   2026-09-30 - First build. Replaces engine/mesh_universal.py
#                and engine/mesh_topology.py.
#   2026-10-01 - Interior points and Laplace lift. The earlier
#                version had no interior nodes and used mean-z;
#                the result was a flat membrane.
# =============================================================================

import numpy as np


_VALID_TYPES = ("beam", "cable", "wall")


# =============================================================================
# VALIDATION
# =============================================================================

def _validate_boundary(boundary_loop):
    """Raise ValueError if the boundary is malformed. Return (n, 3) array."""
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
    """Raise ValueError if anchors are malformed. Return sorted list."""
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
    """Raise ValueError if segment types are malformed. Return list."""
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
    """Return a positive float. Default = mean boundary edge length."""
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
#
# Project the 3D boundary onto a 2D plane.
#
# Default plane is the XY plane (normal = Z).
# A caller may supply a different plane as (normal, origin).

def _project_to_plane(boundary_loop, plan_plane):
    """
    Project 3D boundary points onto a 2D plane.

    Parameters
    ----------
    boundary_loop : (n, 3) array
    plan_plane : ((3,) normal, (3,) origin) or None

    Returns
    -------
    pts_2d : (n, 2) array, plan coordinates
    pts_3d : (n, 3) array, original boundary points
    normal : (3,) unit vector
    origin : (3,) point on the plane
    """
    pts_3d = np.asarray(boundary_loop, dtype=float)

    if plan_plane is None:
        # Default: XY plane.
        normal = np.array([0.0, 0.0, 1.0])
        origin = pts_3d.mean(axis=0)
    else:
        normal = np.asarray(plan_plane[0], dtype=float)
        origin = np.asarray(plan_plane[1], dtype=float)
        n = np.linalg.norm(normal)
        if n < 1e-12:
            raise ValueError("plan_plane normal has zero length")
        normal = normal / n

    # Build an orthonormal basis (u, v) in the plane.
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
    """
    Ray-casting test: is (x, y) inside the closed polygon?

    Polygon is (n, 2). Edges are (i, i+1) with wraparound.
    """
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
    """
    Generate candidate interior points on a grid, keeping
    only those inside the polygon.

    The grid spacing is target_edge_length. Points too close
    to the boundary (within 0.4 * spacing) are dropped to
    avoid sliver triangles.
    """
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
    Constrained Delaunay triangulation of a simple polygon.

    Interior points are generated on a grid with spacing
    approximately target_edge_length. The Delaunay
    triangulation is then built over the boundary and the
    interior points together. Triangles whose centroid is
    outside the polygon are discarded.

    Parameters
    ----------
    pts_2d : (n, 2) array of polygon vertices, closed loop
    target_edge_length : float

    Returns
    -------
    interior_pts : (k, 2) array of interior points
    triangles    : list of (a, b, c) tuples, indices into the
                   combined point list [boundary; interior]
    """
    from scipy.spatial import Delaunay

    pts_2d = np.asarray(pts_2d, dtype=float)
    n_boundary = pts_2d.shape[0]

    # ---- 1. Generate interior candidate points.
    interior_candidates = _grid_interior_points(
        pts_2d, target_edge_length
    )

    # ---- 2. Combine boundary and interior candidates.
    if interior_candidates.shape[0] > 0:
        all_pts = np.vstack([pts_2d, interior_candidates])
    else:
        all_pts = pts_2d.copy()

    # ---- 3. Delaunay over the combined point set.
    tri = Delaunay(all_pts)

    # ---- 4. Keep triangles whose centroid is inside the polygon.
    tri_indices = tri.simplices
    triangles_inside = []
    for simplex in tri_indices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        cx = (all_pts[a][0] + all_pts[b][0] + all_pts[c][0]) / 3.0
        cy = (all_pts[a][1] + all_pts[b][1] + all_pts[c][1]) / 3.0
        if _point_in_polygon(cx, cy, pts_2d):
            triangles_inside.append((a, b, c))

    # ---- 5. Which candidates are actually used?
    used = set()
    for (a, b, c) in triangles_inside:
        used.add(a)
        used.add(b)
        used.add(c)

    used_interior = sorted(i for i in used if i >= n_boundary)

    # ---- 6. Compact the interior list, remap indices.
    if len(       used_interior) ==  for new0:
        interior_pts = np.zeros((0, 2))
        remap = {}
    else:
        interior_pts = np.zeros((len(used_interior), 2))
        remap = {}
_idx, old_idx in enumerate(used_interior):
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
    """
    Build a unique edge list from a triangle list.
    Each edge (i, j) is stored with i < j.
    """
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

def _compute_fixed_indices(boundary_loop, anchor_indices,
                            segment_types):
    """
    Decide which boundary nodes are held in the FDM solve.

    Rule:
        - Anchor                        -> held.
        - Segment interior, beam        -> held.
        - Segment interior, wall        -> held.
        - Segment interior, cable       -> released.

    Returns a sorted list of boundary node indices.
    """
    n = boundary_loop.shape[0]
    n_anchors = len(anchor_indices)

    # For each boundary index i, which segment does it belong to?
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
    """
    Assign a force density to every edge.

    Boundary edges: by segment type at their midpoint.
    Interior edges: weft_q.
    """
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

    # Which edges are boundary edges?
    boundary_pair_set = set()
    for i in range(n):
        j = (i + 1) % n
        key = (i, j) if i < j else (j, i)
        boundary_pair_set.add(key)

    q = np.zeros(len(edges))
    for k, (a, b) in enumerate(edges):
        key = (a, b) if a < b else (b, a)
        if key in boundary_pair_set:
            # Boundary edge.
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





