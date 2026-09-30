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
# fixed_indices (returned by build_mesh_universal):
#   FLAT node indices, ready for solve_fdm. The public function
#   translates the internal boundary-row indices to flat node
#   indices. Callers do not need to know the layout.
#
# History:
#   2026-09-29 - First build.
#   2026-09-29 - Polar fill: collapse innermost ring to one centre
#                node. Removes zero-area triangles at the centre.
#   2026-09-30 - build_mesh_universal returns FLAT fixed_indices.
#                Translation done inside the public function.
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





