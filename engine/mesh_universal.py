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
#   "tfi"         - bilinear, for quad-shaped loops. Rectangular grid.
#   "polar"       - concentric rings, for circle-shaped loops.
#                   The innermost "ring" collapses to a single
#                   centre node. Total nodes = n_i * (M - 1) + 1.
#   "barycentric" - area-weighted, for triangle-shaped loops.
#
# Structural connections list (Part V doctrine):
#   Empty today. Populated in Stage 3.
#
# History:
#   2026-09-29 - First build.
#   2026-09-29 - Polar fill: collapse innermost ring to one centre
#                node. Removes zero-area triangles at the centre.
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
    """Return K mesh nodes on the segment from anchor p0 toward anchor p1.
    Includes p0. Excludes p1 (belongs to the next segment)."""
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    pts = np.zeros((K, 3))
    for k in range(K):
        t = k / float(K)
        pts[k] = p0 * (1.0 - t) + p1 * t
    return pts


def _build_boundary_row(boundary_loop, segment_types, K):
    """Build the boundary row (j = 0) of the mesh. Walks the loop."""
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
    """TFI fill for a quad-shaped loop. Returns (n_i, M, 3)."""
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

    Returns a grid of shape (n_i, M - 1, 3) for the rings, plus
    a single centre node. The caller assembles the flat node list
    as: [ring nodes for j = 0 .. M - 2] + [centre node].

    Ring j = 0 is the boundary itself.
    Ring j = M - 2 is the innermost ring, nearest the centre.
    The centre node is at the mean of the boundary row.

    No ring of coincident nodes at the centre. Only one node
    at the centre. Zero-area triangles are avoided.
    """
    cx = float(np.mean(boundary_row[:, 0]))
    cy = float(np.mean(boundary_row[:, 1]))
    cz = float(np.mean(boundary_row[:, 2]))
    centre = np.array([cx, cy, cz])

    rings = np.zeros((n_i, M - 1, 3))
    for i in range(n_i):
        p_b = boundary_row[i]
        for j in range(M - 1):
            v = j / float(M - 1)
            rings[i, j] = p_b * (1.0 - v) + centre * v

    return rings, centre


def _fill_barycentric(boundary_row, n_i, M):
    """Barycentric fill for a triangle-shaped loop. Returns (n_i, M, 3)."""
    n = n_i
    third = n // 3
    c_a = boundary_row[0]
    c_b = boundary_row[third]
    c_c = boundary_row[2 * third]
    centroid = (c_a + c_b + c_c) / 3.0

    grid = np.zeros((n, M, 3))
    for i in range(n):
        p_b = boundary_row[i]
        for j in range(M):
            v = j / float(M - 1)
            grid[i, j] = p_b * (1.0 - v) + centroid * v
    return grid






# =============================================================================
# FIXED INDICES
# =============================================================================

def _build_fixed_indices(n_i, K, segment_types):
    """
    Decide which nodes on the boundary row solve_fdm holds.

    Nodes on the boundary row are indexed 0 .. n_i - 1.
    Index = i in the boundary row. Independent of M.

    Rule:
        - Anchor (i multiple of K): held.
        - Segment interior, beam or wall: held.
        - Segment interior, cable: released.

    Returns:
        sorted list of int.
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

    return sorted(fixed)


# =============================================================================
# INDEX HELPERS
# =============================================================================
# Two topologies:
#
#   TFI / barycentric: rectangular (n_i, M) grid.
#       Node index = i * M + j.
#       Total nodes = n_i * M.
#       Centre node: none.
#
#   Polar: rings of (n_i, M - 1) plus one centre node.
#       Ring node index = i * (M - 1) + j, for j = 0 .. M - 2.
#       Centre node index = n_i * (M - 1).
#       Total nodes = n_i * (M - 1) + 1.

def _index_ring(i, j, n_i, M):
    """Index of a ring node in the polar layout."""
    return i * (M - 1) + j


def _index_centre(n_i, M):
    """Index of the centre node in the polar layout."""
    return n_i * (M - 1)


# =============================================================================
# EDGES — TFI and barycentric
# =============================================================================

def _build_edges_rect(n_i, M):
    """Edges for a rectangular (n_i, M) grid. Closed in the i direction."""
    edges = []
    for i in range(n_i):
        i_next = (i + 1) % n_i
        for j in range(M):
            k = i * M + j
            edges.append((k, i_next * M + j))
            if j + 1 < M:
                edges.append((k, i * M + (j + 1)))
    return edges


# =============================================================================
# EDGES — polar
# =============================================================================

def _build_edges_polar(n_i, M):
    """
    Edges for a polar mesh.

    Ring layout: (n_i, M - 1) ring nodes.
    Centre node: one node at index n_i * (M - 1).
    """
    edges = []
    centre_idx = _index_centre(n_i, M)

    # Ring edges (i-direction, closed) and radial edges (j-direction).
    for i in range(n_i):
        i_next = (i + 1) % n_i
        for j in range(M - 1):
            k = _index_ring(i, j, n_i, M)
            # Along the ring.
            edges.append((k, _index_ring(i_next, j, n_i, M)))
            # Radial, to the next ring inward.
            if j + 1 < M - 1:
                edges.append((k, _index_ring(i, j + 1, n_i, M)))
            else:
                # Innermost ring connects to the single centre node.
                edges.append((k, centre_idx))

    return edges


# =============================================================================
# Q ASSIGNMENT — TFI and barycentric
# =============================================================================

def _build_q_rect(edges, n_i, M, K, segment_types,
                  warp_q, weft_q, edge_q):
    """Q for a rectangular (n_i, M) grid."""
    n_anchors = len(segment_types)
    q = np.zeros(len(edges))

    for k, (a, b) in enumerate(edges):
        ia = a // M
        ja = a % M
        jb = b % M

        if ja == jb:
            seg_index = ia // K
            if seg_index >= n_anchors:
                seg_index = n_anchors - 1
            seg_type = segment_types[seg_index]
            q[k] = float(edge_q) if seg_type == "cable" else float(warp_q)
        else:
            q[k] = float(weft_q)

    return q


# =============================================================================
# Q ASSIGNMENT — polar
# =============================================================================

def _build_q_polar(edges, n_i, M, K, segment_types,
                   warp_q, weft_q, edge_q):
    """Q for a polar mesh."""
    n_anchors = len(segment_types)
    centre_idx = _index_centre(n_i, M)
    q = np.zeros(len(edges))

    for k, (a, b) in enumerate(edges):
        # Centre edges: always weft.
        if a == centre_idx or b == centre_idx:
            q[k] = float(weft_q)
            continue

        ia = a // (M - 1)
        ja = a % (M - 1)
        jb = b % (M - 1)

        if ja == jb:
            seg_index = ia // K
            if seg_index >= n_anchors:
                seg_index = n_anchors - 1
            seg_type = segment_types[seg_index]
            q[k] = float(edge_q) if seg_type == "cable" else float(warp_q)
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

    Returns dict with keys: points, edges, fixed_indices, q, diagnostics.
    """
    boundary_loop = [tuple(float(v) for v in p) for p in boundary_loop]
    segment_types = list(segment_types)

    _validate_inputs(boundary_loop, segment_types, fill,
                     subdivisions_per_segment, transverse_count)

    K = int(subdivisions_per_segment)
    M = int(transverse_count)

    boundary_row, n_i = _build_boundary_row(
        boundary_loop, segment_types, K
    )

    # ------------------------------------------------------------------
    # Build the flat node list and the edges.
    # Two topologies: rectangular (TFI, barycentric) and polar.
    # ------------------------------------------------------------------
    if fill == "polar":
        rings, centre = _fill_polar(boundary_row, n_i, M)
        n_nodes = n_i * (M - 1) + 1
        points = np.zeros((n_nodes, 3))
        for i in range(n_i):
            for j in range(M - 1):
                k = _index_ring(i, j, n_i, M)
                points[k] = rings[i, j]
        points[_index_centre(n_i, M)] = centre

        edges = _build_edges_polar(n_i, M)
        fixed_indices = _build_fixed_indices(n_i, K, segment_types)
        q = _build_q_polar(edges, n_i, M, K, segment_types,
                           warp_q, weft_q, edge_q)
        n_rows = M - 1
        has_centre = True
    else:
        if fill == "tfi":
            grid = _fill_tfi(boundary_row, n_i, M)
        else:
            grid = _fill_barycentric(boundary_row, n_i, M)

        n_nodes = n_i * M
        points = np.zeros((n_nodes, 3))
        for i in range(n_i):
            for j in range(M):
                points[i * M + j] = grid[i, j]

        edges = _build_edges_rect(n_i, M)
        fixed_indices = _build_fixed_indices(n_i, K, segment_types)
        q = _build_q_rect(edges, n_i, M, K, segment_types,
                          warp_q, weft_q, edge_q)
        n_rows = M
        has_centre = False

    diagnostics = {
        "n_nodes": n_nodes,
        "n_edges": len(edges),
        "n_fixed": len(fixed_indices),
        "n_free": n_nodes - len(fixed_indices),
        "fill_used": fill,
        "segment_types": list(segment_types),
        "n_anchors": len(boundary_loop),
        "n_segments": len(segment_types),
        "n_i": n_i,
        "n_rows": n_rows,
        "has_centre": has_centre,
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
# Two topologies:
#   TFI / barycentric: rectangular (n_i, M) grid.
#   Polar: rings (n_i, M-1) plus a single centre node.
#          No ring of coincident nodes at the centre.
#          Zero-area triangles at the centre are avoided.
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
# =============================================================================





