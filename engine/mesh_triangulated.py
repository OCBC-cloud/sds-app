# =============================================================================
# SDSe Engine - Triangulated Mesh Builder
# =============================================================================
# Builds a triangulated mesh from a closed boundary loop.
# One method. Every shape. See engine/SPEC_mesh_triangulation.md.
#
# The method:
#   1. Project the boundary onto a plan plane.
#   2. Constrained Delaunay triangulation of the polygon.
#   3. Lift the interior nodes to 3D (Coons or mean-z).
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
#   scipy.spatial.Delaunay (scipy is on Streamlit Cloud).
#   The `triangle` package is NOT used: it cannot be built
#   on Streamlit Cloud. See SPEC_mesh_triangulation.md
#   section 10.
#
# History:
#   2026-09-30 - First build. Replaces engine/mesh_universal.py
#                and engine/mesh_topology.py.
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

def _best_fit_plane(boundary_loop):
    """
    Find the plane that best fits the boundary points.

    Returns (normal, origin):
        normal : (3,) unit vector
        origin : (3,) point on the plane
    """
    pts = np.asarray(boundary_loop, dtype=float)
    origin = pts.mean(axis=0)
    centred = pts - origin

    # Covariance and its smallest eigenvector.
    cov = centred.T @ centred
    vals, vecs = np.linalg.eigh(cov)
    normal = vecs[:, 0]  # smallest eigenvalue
    normal = normal / (np.linalg.norm(normal) + 1e-30)
    return normal, origin


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
    # Pick a reference vector not parallel to normal.
    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, normal))) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    u = ref - np.dot(ref, normal) * normal
    u = u / (np.linalg.norm(u) + 1e-30)
    v = np.cross(normal, u)
    v = v / (np.linalg.norm(v) + 1e-30)

    # Project.
    centred = pts_3d - origin
    pts_2d = np.zeros((pts_3d.shape[0], 2))
    for i in range(pts_3d.shape[0]):
        pts_2d[i, 0] = float(np.dot(centred[i], u))
        pts_2d[i, 1] = float(np.dot(centred[i], v))

    return pts_2d, pts_3d, normal, origin


def _lift_to_3d(pts_2d, normal, origin, z_values):
    """
    Lift 2D plan points back to 3D, using supplied z values.

    Parameters
    ----------
    pts_2d : (n, 2) array
    normal : (3,) unit vector
    origin : (3,) point on the plane
    z_values : (n,) array of heights along the plane normal

    Returns
    -------
    (n, 3) array
    """
    pts_2d = np.asarray(pts_2d, dtype=float)
    z_values = np.asarray(z_values, dtype=float)

    # Rebuild the (u, v) basis as in _project_to_plane.
    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, normal))) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    u = ref - np.dot(ref, normal) * normal
    u = u / (np.linalg.norm(u) + 1e-30)
    v = np.cross(normal, u)
    v = v / (np.linalg.norm(v) + 1e-30)

    out = np.zeros((pts_2d.shape[0], 3))
    for i in range(pts_2d.shape[0]):
        a = pts_2d[i, 0]
        b = pts_2d[i, 1]
        z = z_values[i]
        out[i] = origin + a * u + b * v + z * normal
    return out


# =============================================================================
# TRIANGULATION
# =============================================================================

def _triangulate_polygon(pts_2d, target_edge_length):
    """
    Constrained Delaunay triangulation of a simple polygon.

    Uses scipy.spatial.Delaunay, then filters triangles whose
    centroids fall outside the polygon.

    Parameters
    ----------
    pts_2d : (n, 2) array of polygon vertices, closed loop
    target_edge_length : float

    Returns
    -------
    interior_pts : (k, 2) array of interior points (may be empty)
    triangles    : list of (a, b, c) tuples, indices into the
                   combined point list [boundary; interior]
    """
    from scipy.spatial import Delaunay

    pts_2d = np.asarray(pts_2d, dtype=float)
    n = pts_2d.shape[0]

    # Build a Delaunay triangulation of the boundary alone.
    # scipy.spatial.Delaunay takes the vertices and produces
    # the convex hull triangulation.
    tri = Delaunay(pts_2d)

    # Keep triangles whose centroid is inside the polygon.
    tri_indices = tri.simplices
    triangles_inside = []
    for simplex in tri_indices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        # Centroid.
        ca = 0.5 * (pts_2d[a] + pts_2d[b] + pts_2d[c]) / 3.0
        cx = 0.5 * (pts_2d[a][0] + pts_2d[b][0] + pts_2d[c][0]) / 3.0
        cy = 0.5 * (pts_2d[a][1] + pts_2d[b][1] + pts_2d[c][1]) / 3.0
        if _point_in_polygon(cx, cy, pts_2d):
            triangles_inside.append((a, b, c))

    # For the first implementation, no interior points.
    # The mesh is a triangulation of the boundary alone.
    # A refinement in a later version will insert interior
    # points to meet the target_edge_length.
    interior_pts = np.zeros((0, 2))

    return interior_pts, triangles_inside


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


def _boundary_edges(n_boundary):
    """
    The boundary loop edges. Node i connects to node (i+1)%n.
    """
    edges = []
    for i in range(n_boundary):
        j = (i + 1) % n_boundary
        key = (i, j) if i < j else (j, i)
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

    The segment index of boundary node i is the segment
    between anchor k and anchor k+1 that contains i.
    """
    n = boundary_loop.shape[0]
    n_anchors = len(anchor_indices)

    # Build a mapping: for each boundary index i, which segment
    # (0 .. n_anchors-1) does it belong to?
    seg_of_node = [-1] * n
    for k in range(n_anchors):
        start = anchor_indices[k]
        end = anchor_indices[(k + 1) % n_anchors]
        # Walk from start to end (wraparound).
        i = start
        while True:
            seg_of_node[i] = k
            if i == end:
                break
            i = (i + 1) % n
            if i == start:
                break

    # Anchors: always held.
    anchor_set = set(anchor_indices)

    fixed = []
    for i in range(n):
        if i in anchor_set:
            fixed.append(i)
            continue
        seg_idx = seg_of_node[i]
        if seg_idx < 0:
            # Should not happen; treat as held.
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

    # seg_of_node as in _compute_fixed_indices.
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

    # Which edges are boundary edges? Lookup by node pair.
    boundary_pair_set = set()
    for i in range(n):
        j = (i + 1) % n
        key = (i, j) if i < j else (j, i)
        boundary_pair_set.add(key)

    q = np.zeros(len(edges))
    for k, (a, b) in enumerate(edges):
        key = (a, b) if a < b else (b, a)
        if key in boundary_pair_set:
            # Boundary edge. Segment by either endpoint.
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

    See engine/SPEC_mesh_triangulation.md for the full design.

    Parameters
    ----------
    boundary_loop : (n, 3) array
        Ordered boundary points forming a closed loop.
        The loop is closed by convention. Do not duplicate
        the first point at the end.

    anchor_indices : list of int, or None
        Indices into boundary_loop where two segments meet.
        If None, every boundary point is treated as an
        anchor (so every boundary node is held).

    segment_types : list of str, or None
        One per segment between consecutive anchors.
        Values: "beam", "cable", "wall".
        If None, all segments are "cable".

    target_edge_length : float, or None
        Reserved for a refinement pass. Not used in the
        first implementation. Recorded in diagnostics.

    plan_plane : ((3,) normal, (3,) origin) or None
        Plane for 2D triangulation. Default: XY plane.

    warp_q, weft_q, edge_q : float
        Force densities (N/m) for the three segment
        categories and the interior.

    Returns
    -------
    dict:
        points          (n_nodes, 3) array
        edges           list of (i, j) tuples
        triangles       list of (a, b, c) tuples
        fixed_indices   list of int, FLAT node indices
        q               (n_edges,) array
        diagnostics     dict
    """
    # ---- 1. Validate inputs.
    boundary = _validate_boundary(boundary_loop)
    n_boundary = boundary.shape[0]

    anchors = _validate_anchors(anchor_indices, n_boundary)
    n_segments = len(anchors)
    seg_types = _validate_segment_types(segment_types, n_segments)
    target_len = _validate_target_edge_length(
        target_edge_length, boundary
    )

    # ---- 2. Plan projection.
    pts_2d, pts_3d, normal, origin = _project_to_plane(
        boundary, plan_plane
    )

    # ---- 3. Triangulate the polygon.
    interior_pts_2d, triangles = _triangulate_polygon(
        pts_2d, target_len
    )
    n_interior = interior_pts_2d.shape[0]

    # ---- 4. Lift interior points to 3D.
    #        First implementation: mean-z of boundary.
    if n_interior > 0:
        mean_z = float(np.mean(
            [float(np.dot(p - origin, normal)) for p in pts_3d]
        ))
        interior_pts_3d = _lift_to_3d(
            interior_pts_2d, normal, origin,
            np.full(n_interior, mean_z)
        )
        all_points = np.vstack([pts_3d, interior_pts_3d])
    else:
        all_points = pts_3d.copy()

    # ---- 5. Edges.
    edges = _edges_from_triangles(triangles, all_points.shape[0])

    # ---- 6. Fixed indices.
    fixed_boundary = _compute_fixed_indices(
        boundary, anchors, seg_types
    )
    # The interior points are never fixed. So the fixed
    # indices are just the boundary indices, which are
    # already the first n_boundary nodes in all_points.
    fixed_indices = list(fixed_boundary)

    # ---- 7. Force densities.
    q = _compute_q(edges, n_boundary, boundary, anchors,
                   seg_types, warp_q, weft_q, edge_q)

    # ---- 8. Diagnostics.
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
        "plan_normal": [float(v) for v in normal],
        "plan_origin": [float(v) for v in origin],
        "structural_connections": [],
    }

    return {
        "points": all_points,
        "edges": edges,
        "triangles": triangles,
        "fixed_indices": fixed_indices,
        "q": q,
        "diagnostics": diagnostics,
    }


# =============================================================================
# END OF engine/mesh_triangulated.py
# =============================================================================
#
# This file is the universal mesh engine. One method. Every
# shape. See engine/SPEC_mesh_triangulation.md.
#
# It replaces engine/mesh_universal.py (the earlier structured
# engine with three topologies). The structured engine is kept
# as a working fallback until the new engine passes its tests,
# then deleted.
#
# The solver (solve_fdm) is unchanged. The viewer draws
# triangles from result["triangles"].
#
# Files that will be updated in the migration:
#   engine/mesh_triangulated_test.py     (new test, Step 3)
#   viewers/figures/standard_saddle_mbs.py  (Step 4)
#   run_tests.py                          (Step 3)
#
# Files that will be deleted after the migration:
#   engine/mesh_universal.py
#   engine/mesh_universal_test.py
# =============================================================================





