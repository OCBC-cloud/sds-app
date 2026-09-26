# =============================================================================
# SDSe Fluid Design Studio - MBS Tester Workshop
# =============================================================================
# Temporary research page. Tests the Membrane Boundary Schema engine
# across multiple shapes using the same nine-step pipeline.
#
# Doctrine (2026-09-26):
#   - The user supplies corners only. The engine derives everything
#     else: edge nodes, interior grid, mesh, solve.
#   - Segments N is the user's number of segments. Not converted.
#   - Mesh density is Mode A (fixed K) or Mode B (target ds metres).
#   - Focal point = centroid of boundary nodes in x-y, solved z.
#   - Every boundary node is held rigid (Stage 1 doctrine).
#   - Same parameters on every shape. Only the boundary changes.
#
# Shapes implemented in this file:
#   Lens      - two beam curves meeting at two tips (existing recipe).
#   Triangle  - three corners, three edges, user-editable corner xyz.
#
# Shapes deferred to later passes:
#   Square, Circle.
#
# Status: EXPERIMENTAL.
# =============================================================================

import numpy as np
import streamlit as st


# ---- Defaults -------------------------------------------------------------
DEFAULT_SEGMENTS = 7
DEFAULT_K = 5
DEFAULT_DS = 0.5
DEFAULT_WARP_Q = 2.0
DEFAULT_WEFT_Q = 2.0

# ---- Lens recipe constants (unchanged from prior version) ----------------
LENS_SPAN = 3.0
LENS_APEX_WIDTH = 4.0
LENS_RISE = 1.5
LENS_SAG_FRACTION = 0.10

# ---- Triangle defaults ----------------------------------------------------
TRI_A_DEFAULT = (-1.5, -1.5, 0.0)
TRI_B_DEFAULT = ( 1.5, -1.5, 0.0)
TRI_C_DEFAULT = ( 0.0,  1.5, 1.5)


# =============================================================================
# MESH DENSITY HELPERS
# =============================================================================

def _nodes_per_edge(n_segments, edge_length, mode, K, ds):
    """
    Return the total node count along one edge, given the user's
    segment count N and the mesh density mode.

    The edge is divided into N equal segments. Each segment is then
    subdivided further according to the mode:

      Mode A (fixed K): each segment has K interior nodes, so K+1
        sub-intervals per segment.
      Mode B (target ds): each segment has
        K_i = max(1, round(segment_length / ds) - 1)
        interior nodes, derived from the segment length.

    Returns
    -------
    n_nodes_total : int
        Total nodes along the edge, including both endpoints.
    node_positions : (n_nodes_total,) array
        Fractions in [0, 1] along the edge where nodes sit.
    """
    if n_segments < 1:
        n_segments = 1
    seg_len = float(edge_length) / float(n_segments)

    fractions = [0.0]
    for s in range(n_segments):
        if mode == "A":
            K_seg = max(1, int(K))
        else:
            K_seg = max(1, int(round(seg_len / float(ds))) - 1)

        # K_seg interior nodes -> K_seg + 1 sub-intervals in the segment.
        n_sub = K_seg + 1
        seg_start = s / float(n_segments)
        for k in range(1, n_sub + 1):
            fractions.append(seg_start + k * (1.0 / n_segments) / n_sub)

    fractions = np.array(fractions, dtype=float)
    # Clean up tiny float noise at the endpoint.
    fractions[-1] = 1.0
    return len(fractions), fractions


# =============================================================================
# SHAPE RECIPES
# =============================================================================
# Every recipe returns the same tuple:
#
#   (grid, boundary, anchor_indices, edge_types)
#
#   grid          : (nx, ny, 3) initial surface, or None to let TFI run
#   boundary      : (M, 3) closed loop of 3D points (or strip)
#   anchor_indices: list of ints, indices into boundary
#   edge_types    : list of "beam" or "cable", one per anchor
#
# The engine treats all shapes identically. Only the recipe differs.

def _build_lens_recipe(n_segments, mode, K, ds):
    """
    Build the lens surface and boundary.
    Uses engine/membrane_surface.py to produce the grid.
    Uses the arc-length subdivision for the boundary.
    """
    from viewers.figures._shared import beam_curve
    from engine.membrane_surface import build_surface

    # Use n_anchors = n_segments + 1 (anchors at segment ends).
    n_anchors = int(n_segments) + 1
    subdivisions = int(K) if mode == "A" else 5  # lens uses uniform subdiv
    n_v = 8  # across the width

    x_dense = np.linspace(-LENS_SPAN / 2.0, LENS_SPAN / 2.0, 400)
    z_dense = beam_curve(x_dense, LENS_SPAN, LENS_RISE, "parabolic")

    base_width = LENS_APEX_WIDTH * 0.5
    y_L_dense = -base_width * (1.0 - (2.0 * x_dense / LENS_SPAN) ** 2)
    y_R_dense = base_width * (1.0 - (2.0 * x_dense / LENS_SPAN) ** 2)
    y_L_dense[0] = 0.0
    y_L_dense[-1] = 0.0
    y_R_dense[0] = 0.0
    y_R_dense[-1] = 0.0

    beam_L = np.column_stack((x_dense, y_L_dense, z_dense))
    beam_R = np.column_stack((x_dense, y_R_dense, z_dense))

    grid = build_surface(
        beam_L_points=beam_L,
        beam_R_points=beam_R,
        n_anchors=n_anchors,
        subdivisions_per_segment=subdivisions,
        n_v=n_v,
        sag_fraction=LENS_SAG_FRACTION,
        taper_ends=True,
    )

    nx = grid.shape[0]
    boundary_list = [grid[0, 0]]
    for i in range(1, nx - 1):
        boundary_list.append(grid[i, 0])
    boundary_list.append(grid[nx - 1, 0])
    for i in range(nx - 2, 0, -1):
        boundary_list.append(grid[i, n_v - 1])

    boundary = np.array(boundary_list, dtype=float)
    anchors = list(range(len(boundary)))
    edge_types = ["beam"] * len(boundary)
    return grid, boundary, anchors, edge_types


def _build_triangle_recipe(corner_A, corner_B, corner_C,
                            n_segments, mode, K, ds):
    """
    Build a triangle boundary and a barycentric interior grid.

    corner_A, corner_B, corner_C : (3,) tuples (x, y, z), user-editable.
    n_segments : int, segments per edge.
    mode       : "A" or "B"
    K, ds      : mesh density parameters.
    """
    corners = [np.asarray(corner_A, dtype=float),
               np.asarray(corner_B, dtype=float),
               np.asarray(corner_C, dtype=float)]

    # ---- Build the boundary loop: A -> B -> C -> (back to A).
    boundary_pts = []
    anchor_idx_per_corner = []

    for e in range(3):
        p0 = corners[e]
        p1 = corners[(e + 1) % 3]
        edge_length = float(np.linalg.norm(p1 - p0))

        n_nodes, fractions = _nodes_per_edge(
            n_segments, edge_length, mode, K, ds
        )

        # Record the corner where this edge starts.
        anchor_idx_per_corner.append(len(boundary_pts))

        for f in fractions[:-1]:  # exclude the last (start of next edge)
            boundary_pts.append(p0 * (1.0 - f) + p1 * f)

    boundary = np.array(boundary_pts, dtype=float)

    # Every boundary node is held (Stage 1 doctrine: full rigid perimeter).
    anchors = list(range(len(boundary)))
    edge_types = ["beam"] * len(boundary)

    # ---- Interior grid: barycentric fill.
    # Resolution matches the boundary roughly.
    n_boundary = len(boundary)
    n_grid = max(21, n_boundary)
    nx = n_grid
    ny = n_grid

    # Find the mean of the corners as the interior collapse point.
    centroid = (corners[0] + corners[1] + corners[2]) / 3.0

    # Bilinear grid: for grid index (i, j) in [0, 1] x [0, 1],
    # place a point between centroid and boundary via a radial mapping.
    grid = np.zeros((nx, ny, 3))
    for i in range(nx):
        u = i / (nx - 1.0)
        for j in range(ny):
            v = j / (ny - 1.0)

            # Weights that map (u, v) to a point inside the triangle.
            # Use a simple scheme: barycentric coordinates from (u, v).
            # Points (u,v): (0,0) -> corner A; (1,0) -> corner B;
            # (0,1) -> corner C. Any other (u,v) inside unit square
            # clamps to a barycentric interior point.
            wA = max(0.0, 1.0 - u - v)
            wB = max(0.0, u)
            wC = max(0.0, v)
            total = wA + wB + wC
            if total < 1e-9:
                wA, wB, wC = 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0
            else:
                wA /= total
                wB /= total
                wC /= total

            pt = wA * corners[0] + wB * corners[1] + wC * corners[2]
            grid[i, j] = pt

    return grid, boundary, anchors, edge_types


# ---- Registry -------------------------------------------------------------
# The Tester reads this dict. Add new shapes here.

SHAPE_RECIPES = {
    "Lens": _build_lens_recipe,
    "Triangle": _build_triangle_recipe,
}


# =============================================================================
# END OF PART 1
# =============================================================================





