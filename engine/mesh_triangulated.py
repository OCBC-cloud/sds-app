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





