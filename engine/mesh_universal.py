# =============================================================================
# SDSe Engine - Universal Mesh Builder
# =============================================================================
# Builds a mesh from a closed boundary loop divided into segments.
# Each segment is classified as "beam", "cable", or "wall".
#
# The engine knows no shapes. It knows boundaries, segments,
# and types. It is universal.
#
# Vocabulary (fixed):
#   boundary loop   - a closed sequence of 3D points.
#   anchor          - a point on the boundary loop where two
#                     segments meet. Always held.
#   segment         - the gap between two consecutive anchors.
#   segment type    - beam, cable, or wall.
#   held            - a mesh node solve_fdm does not move.
#   released        - a mesh node solve_fdm moves to equilibrium.
#
# Hold rule:
#   Anchor                  -> always held.
#   Segment interior, beam  -> held.
#   Segment interior, wall  -> held.
#   Segment interior, cable -> released.
#   Mesh interior           -> always released.
#
# Fill strategies:
#   "tfi"         - bilinear, for quad-shaped loops.
#   "polar"       - concentric rings, for circle-shaped loops.
#   "barycentric" - area-weighted, for triangle-shaped loops.
#
# Structural connections list (Part V doctrine):
#   Empty today. Populated in Stage 3.
#
# History:
#   2026-09-29 - First build.
# =============================================================================

import numpy as np


_VALID_FILLS = ("tfi", "polar", "barycentric")
_VALID_TYPES = ("beam", "cable", "wall")


def _validate_inputs(boundary_loop, segment_types, fill,
                     subdivisions_per_segment, transverse_count):
    """Raise ValueError if inputs are malformed."""
    if fill not in _VALID_FILLS:
        raise ValueError(
            "fill must be one of %s (got %r)"
            % (list(_VALID_FILLS), fill)
        )

    if len(boundary_loop) < 3:
        raise ValueError(
            "boundary_loop must have at least 3 points (got %d)"
            % len(boundary_loop)
        )

    n_anchors = len(boundary_loop)
    if len(segment_types) != n_anchors:
        raise ValueError(
            "segment_types must have length %d (got %d)"
            % (n_anchors, len(segment_types))
        )

    for k, t in enumerate(segment_types):
        if t not in _VALID_TYPES:
            raise ValueError(
                "segment_types[%d] must be one of %s (got %r)"
                % (k, list(_VALID_TYPES), t)
            )

    if subdivisions_per_segment < 1:
        raise ValueError(
            "subdivisions_per_segment must be >= 1 (got %d)"
            % subdivisions_per_segment
        )

    if transverse_count < 2:
        raise ValueError(
            "transverse_count must be >= 2 (got %d)"
            % transverse_count
        )


def _resample_segment(p0, p1, K):
    """
    Return the mesh nodes on the segment from anchor p0 to anchor p1.

    Includes p0 at the start. Excludes p1 at the end (it belongs
    to the next segment).

    Total nodes returned: K.
    """
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    pts = np.zeros((K, 3))
    for k in range(K):
        t = k / float(K)
        pts[k] = p0 * (1.0 - t) + p1 * t
    return pts


def _build_boundary_row(boundary_loop, segment_types, K):
    """
    Build the boundary row (j = 0) of the mesh.

    Walks the loop. For each segment, places K mesh nodes,
    starting at the anchor and going toward the next anchor.
    The next anchor is the start of the next segment, so it
    is not duplicated.

    Returns:
        row  - (n_i, 3) array of mesh nodes on the boundary.
        n_i  - number of nodes in the row.
    """
    n_anchors = len(boundary_loop)
    row = []
    for k in range(n_anchors):
        p0 = boundary_loop[k]
        p1 = boundary_loop[(k + 1) % n_anchors]
        seg_nodes = _resample_segment(p0, p1, K)
        for p in seg_nodes:
            row.append(p)
    row = np.asarray(row, dtype=float)
    return row, row.shape[0]






def _fill_tfi(boundary_row, n_i, M):
    """
    TFI fill for a quad-shaped loop.

    The boundary row is divided into two halves: the first half
    is the "top", the second half is the "bottom". The interior
    is a bilinear blend.

    For a quad loop with 4 segments, this is a natural split.
    For a loop with more anchors, the split happens at the middle
    index.

    Returns:
        grid  - (n_i, M, 3) array.
    """
    half = n_i // 2

    top = np.zeros((n_i, 3))
    bottom = np.zeros((n_i, 3))
    for i in range(n_i):
        j_top = (half + i) % n_i
        top[i] = boundary_row[j_top]
        bottom[i] = boundary_row[i]

    grid = np.zeros((n_i, M, 3))
    for i in range(n_i):
        p_a = bottom[i]
        p_b = top[i]
        for j in range(M):
            v = j / float(M - 1)
            grid[i, j] = p_a * (1.0 - v) + p_b * v
    return grid


def _fill_polar(boundary_row, n_i, M):
    """
    Polar fill for a ring-shaped loop.

    A centre point is placed at the mean of the boundary row
    in xy, at the mean z. The interior is a radial blend
    between the boundary and the centre.

    Returns:
        grid  - (n_i, M, 3) array.
    """
    cx = float(np.mean(boundary_row[:, 0]))
    cy = float(np.mean(boundary_row[:, 1]))
    cz = float(np.mean(boundary_row[:, 2]))
    centre = np.array([cx, cy, cz])

    grid = np.zeros((n_i, M, 3))
    for i in range(n_i):
        p_b = boundary_row[i]
        for j in range(M):
            v = j / float(M - 1)
            grid[i, j] = p_b * (1.0 - v) + centre * v
    return grid


def _fill_barycentric(boundary_row, n_i, M):
    """
    Barycentric fill for a triangle-shaped loop.

    The boundary row must have three anchors roughly equal
    distance apart. The boundary row is divided into three
    sides. Each interior node is an area-weighted blend of
    the three corners.

    For v1, we approximate: treat the boundary row as a
    triangle with three representative corners. The interior
    is filled by barycentric coordinates.

    Returns:
        grid  - (n_i, M, 3) array.
    """
    n = n_i
    third = n // 3
    c_a = boundary_row[0]
    c_b = boundary_row[third]
    c_c = boundary_row[2 * third]

    grid = np.zeros((n, M, 3))
    for i in range(n):
        p_b = boundary_row[i]
        for j in range(M):
            v = j / float(M - 1)
            grid[i, j] = p_b * (1.0 - v) + (c_a + c_b + c_c) / 3.0 * v
    return grid


def _fill_grid(boundary_row, fill, n_i, M):
    """Dispatch to the correct fill strategy."""
    if fill == "tfi":
        return _fill_tfi(boundary_row, n_i, M)
    if fill == "polar":
        return _fill_polar(boundary_row, n_i, M)
    if fill == "barycentric":
        return _fill_barycentric(boundary_row, n_i, M)
    raise ValueError("unknown fill: " + fill)






# =============================================================================
# FIXED INDICES
# =============================================================================

def _build_fixed_indices(n_i, M, K, segment_types):
    """
    Decide which mesh nodes solve_fdm holds.

    Boundary nodes (j = 0) are indexed 0 .. n_i - 1.
    Interior nodes are indexed n_i .. n_i * M - 1.

    Walk the boundary row. For each mesh node on the boundary:
        - If it is an anchor (index multiple of K): held.
        - If it is a segment interior:
            - Segment type "beam" or "wall": held.
            - Segment type "cable": released.

    Interior nodes (j >= 1): always released.

    Returns:
        fixed_indices  - sorted list of int.
    """
    fixed = set()
    n_anchors = len(segment_types)

    for i in range(n_i):
        seg_index = i // K
        if seg_index >= n_anchors:
            seg_index = n_anchors - 1
        is_anchor = (i % K == 0)
        seg_type = segment_types[seg_index]

        if is_anchor:
            fixed.add(i)
        else:
            if seg_type in ("beam", "wall"):
                fixed.add(i)
            else:
                pass

    return sorted(fixed)


# =============================================================================
# EDGES
# =============================================================================

def _build_edges(n_i, M):
    """
    Build the edge list for a structured (n_i, M) grid.

    Node index = i * M + j.

    Edges along i-direction (same j):
        (i * M + j, (i + 1) * M + j) for i = 0 .. n_i - 2.
    Plus the wrap-around edge (i = n_i - 1 to i = 0) if the
    grid is treated as closed in i. For v1, we do NOT close the
    i-direction. The boundary row is a loop, but the mesh grid
    is open in i to avoid double-counting the wrap segment.

    Actually: the boundary row IS closed (the last anchor connects
    to the first). But the grid is built from the boundary row as
    a linear array of n_i nodes. Closing the i-loop means adding
    an edge from node (n_i - 1, j) to (0, j). For v1, we add it.

    Edges along j-direction (same i):
        (i * M + j, i * M + j + 1) for j = 0 .. M - 2.

    Returns:
        edges  - list of (i, j).
    """
    edges = []

    for i in range(n_i):
        for j in range(M):
            k = i * M + j

            i_next = (i + 1) % n_i
            if i_next != 0 or i == 0:
                edges.append((k, i_next * M + j))
            else:
                edges.append((k, 0 * M + j))

            if j + 1 < M:
                edges.append((k, i * M + (j + 1)))

    return edges


# =============================================================================
# Q ASSIGNMENT
# =============================================================================

def _build_q(edges, n_i, M, K, segment_types,
             warp_q, weft_q, edge_q):
    """
    Assign a force density to each edge.

    Rules:
        Edge along the i-direction (same j, i to i+1):
            If the segment at i is "cable": q = edge_q.
            Otherwise: q = warp_q.
        Edge along the j-direction (same i, j to j+1):
            q = weft_q.

    Returns:
        q  - (n_edges,) array.
    """
    n_anchors = len(segment_types)
    q = np.zeros(len(edges))

    for k, (a, b) in enumerate(edges):
        ia = a // M
        ib = b // M
        ja = a % M
        jb = b % M

        if ja == jb:
            seg_index = ia // K
            if seg_index >= n_anchors:
                seg_index = n_anchors - 1
            seg_type = segment_types[seg_index]
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

def build_mesh_universal(boundary_loop, segment_types, fill,
                         subdivisions_per_segment,
                         transverse_count,
                         warp_q, weft_q, edge_q):
    """
    Build a mesh from a closed boundary loop divided into segments.

    Parameters
    ----------
    boundary_loop : list of (x, y, z)
        At least 3 points. Ordered. The last connects back
        to the first.
    segment_types : list of str
        One per gap. "beam", "cable", or "wall".
    fill : str
        "tfi" | "polar" | "barycentric".
    subdivisions_per_segment : int
        K. Extra mesh nodes per segment. Default 5.
    transverse_count : int
        M. Rows from boundary to interior. Default 8.
    warp_q, weft_q, edge_q : float
        Force densities in N/m.

    Returns
    -------
    dict with keys:
        points, edges, fixed_indices, q, diagnostics.
    """
    boundary_loop = [tuple(float(v) for v in p)
                     for p in boundary_loop]
    segment_types = list(segment_types)

    _validate_inputs(boundary_loop, segment_types, fill,
                     subdivisions_per_segment, transverse_count)

    K = int(subdivisions_per_segment)
    M = int(transverse_count)

    boundary_row, n_i = _build_boundary_row(
        boundary_loop, segment_types, K
    )

    grid = _fill_grid(boundary_row, fill, n_i, M)

    n_nodes = n_i * M
    points = np.zeros((n_nodes, 3))
    for i in range(n_i):
        for j in range(M):
            k = i * M + j
            points[k] = grid[i, j]

    edges = _build_edges(n_i, M)
    fixed_indices = _build_fixed_indices(
        n_i, M, K, segment_types
    )
    q = _build_q(edges, n_i, M, K, segment_types,
                 warp_q, weft_q, edge_q)

    diagnostics = {
        "n_nodes": n_nodes,
        "n_edges": len(edges),
        "n_fixed": len(fixed_indices),
        "n_free": n_nodes - len(fixed_indices),
        "fill_used": fill,
        "segment_types": list(segment_types),
        "n_anchors": len(boundary_loop),
        "n_segments": len(segment_types),
        "subdivisions_per_segment": K,
        "transverse_count": M,
        "structural_connections": [],
    }

    return {
        "points": points,
        "edges": edges,
        "fixed_indices": fixed_indices,
        "q": q,
        "diagnostics": diagnostics,
    }


# =============================================================================
# END OF engine/mesh_universal.py
# =============================================================================
#
# This file is the universal mesh engine. It replaces the
# four-sided TFI path of engine/membrane_boundary.py for all
# shapes with a clear boundary loop.
#
# It does NOT replace:
#   - engine/membrane_boundary.py (used by the Tester shapes)
#   - engine/membrane_surface.py  (used by the Tester Lens)
#   - the Crown-3Lobe recipe      (bespoke, merged lobes)
#
# The new engine is called by:
#   - the Standard Saddle viewer (Step 2C, next)
#   - the DXF custom_boundary workshop (later)
#   - the coordinate-file custom_boundary workshop (later)
#   - the Crown, Triangle, Lens (later, if migrated)
#
# Files untouched by this addition:
#   engine/form_finding.py
#   engine/membrane_boundary.py
#   engine/membrane_surface.py
#   every existing viewer
#   every existing workshop
#
# The new engine sits in isolation until the first viewer
# calls it.
# =============================================================================





