# =============================================================================
# SDSe Engine - Membrane Boundary Schema (MBS)
# =============================================================================
# A universal engine for building the mesh of a membrane from its boundary.
#
# The schema:
#   1. A closed boundary. An ordered list of 3D points forming a loop.
#   2. Anchors. Discrete points on the boundary where the membrane is held.
#   3. Edges between anchors. Each edge is either:
#        - "beam" : the boundary follows the shape and contour of a
#                   structural member. The points along that edge are
#                   FIXED. They do not move in FDM.
#        - "cable": the boundary is a cable between two anchors. The
#                   points along that edge are FREE. They bow inward
#                   under tension, and move in FDM.
#   4. The interior. A grid that fills the boundary. Solved by FDM.
#
# The schema is shape-agnostic and member-agnostic:
#   - It does not know whether the boundary is a lens, a rectangle, a
#     triangle, a polygon, or a circle.
#   - It does not know whether the "beam" is a parabola, an arc, a
#     straight line, or an irregular curve.
#   - It receives only points.
#
# The engine is called by every viewer:
#   - viewers/figures/standard_saddle.py   (Saddle Span)
#   - viewers/figures/beam_supported.py    (Beam Supported Saddle)
#   - viewers/figures/cantilever_hypar.py  (Cantilever Hypar)
#   - viewers/figures/cantilever_leaf.py   (Cantilever Leaf)
#   - every future membrane viewer.
#
# The engine calls:
#   - engine/form_finding.py   (solve_fdm)
#   - viewers/figures/_shared.py (arclength_parametrisation)
#
# Reference for the fill method: Transfinite Interpolation (TFI).
# The boundary is expressed as four sides. A rectangular grid (u, v)
# is blended into the interior. Corners degenerate to points where
# the shape has no width at that side.
#
# Units: m. Force densities in N/m. Pretensions in kN/m.
#
# History:
#   2026-09-24 - First build. MBS engine. Universal. Replaces the
#                shape-specific mesh logic that was duplicated across
#                viewers.
# =============================================================================

import numpy as np

from engine.form_finding import solve_fdm


# ---- Public interface documentation ----------------------------------------
#
# build_mesh(
#     boundary,          # (M, 3) array, ordered list of points on the
#                        # closed boundary. First point != last point.
#     anchor_indices,    # list of int. Which boundary points are anchors.
#     edge_types,        # list of str, same length as anchor_indices.
#                        # edge_types[k] describes the segment from
#                        # anchor k to anchor k+1 (cyclic).
#                        # "beam" or "cable".
#     interior_points,   # (K, 3) array, initial interior points, optional.
#                        # If None, the engine generates a grid.
#     nx, ny,            # int. Mesh density of the interior grid.
#     membrane_q,        # float or (E,) array. Force density for the
#                        # interior edges.
#     cable_q,           # float. Force density for cable segments.
# )
#     -> dict with points, edges, fixed_indices, q, diagnostics
#
# build_and_solve(...) -> dict with coordinates, diagnostics
#
# =============================================================================





# =============================================================================
# BOUNDARY HELPERS
# =============================================================================

def _boundary_edge_list(boundary, anchor_indices):
    """
    Given an ordered boundary and a list of anchor indices, return
    the list of segments between consecutive anchors (cyclic).

    Returns
    -------
    segments : list of dicts
        Each dict has: "anchor_a" (int), "anchor_b" (int),
        "points" (list of int - the boundary indices between them,
        inclusive of both anchors).
    """
    n = len(anchor_indices)
    segments = []
    for k in range(n):
        a = anchor_indices[k]
        b = anchor_indices[(k + 1) % n]

        # Walk the boundary from a to b, following the ordering.
        # The boundary is a closed loop with no repeated points.
        m = len(boundary)
        pts = []
        i = a
        while True:
            pts.append(i)
            if i == b:
                break
            i = (i + 1) % m
            if len(pts) > m:
                raise ValueError(
                    "Boundary walk did not reach anchor_b. "
                    "Check that anchor_indices are in order and the "
                    "boundary is a closed loop."
                )
        segments.append({
            "anchor_a": a,
            "anchor_b": b,
            "points": pts,
        })
    return segments


def _arc_lengths_along_segment(boundary, seg_points):
    """
    Given a segment (list of boundary indices), compute the
    cumulative arc length along that segment.

    Returns
    -------
    s : (len(seg_points),) array
    total : float
    """
    pts = np.asarray([boundary[i] for i in seg_points], dtype=float)
    diff = np.diff(pts, axis=0)
    seg_len = np.linalg.norm(diff, axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg_len)))
    total = float(s[-1]) if len(s) > 0 else 0.0
    return s, total


# =============================================================================
# INTERIOR GRID
# =============================================================================

def _boundary_as_four_sides(boundary, anchor_indices, edge_types):
    """
    Express the boundary as four sides for TFI blending.

    The boundary is a closed loop. For TFI, we need four continuous
    curves joining four corner points. The corners are chosen as the
    anchors where the edge_type changes from "beam" to "cable" (or
    the endpoints of the longest beam run).

    Simplest rule: choose the first and last anchors of the longest
    "beam" run as the top corners, and the first and last anchors of
    the longest "cable" run as the bottom corners.

    If only one type exists (all beam, or all cable), we take the two
    anchors that are furthest apart (in 3D) as corners, and split the
    boundary at their midpoint.

    Returns
    -------
    sides : list of 4 lists of boundary indices, in order, forming
            the four sides of the TFI quad. Corner points are the
            first point of each side.
    corners : list of 4 boundary indices.
    """
    n_anchors = len(anchor_indices)
    if n_anchors < 4:
        # Fewer than 4 anchors. Fall back: use all boundary points
        # directly, split into four equal-ish arcs.
        m = len(boundary)
        quarter = max(1, m // 4)
        c0 = 0
        c1 = quarter % m
        c2 = (2 * quarter) % m
        c3 = (3 * quarter) % m
        corners = [c0, c1, c2, c3]
        sides = []
        for k in range(4):
            a = corners[k]
            b = corners[(k + 1) % 4]
            pts = []
            i = a
            while True:
                pts.append(i)
                if i == b:
                    break
                i = (i + 1) % m
            sides.append(pts)
        return sides, corners

    # Find contiguous runs of the same edge_type.
    runs = []
    start = 0
    for k in range(1, n_anchors):
        if edge_types[k] != edge_types[start]:
            runs.append((start, k - 1, edge_types[start]))
            start = k
    runs.append((start, n_anchors - 1, edge_types[start]))
    # Handle cyclic wrap: if first and last run are same type, merge.
    if len(runs) > 1 and runs[0][2] == runs[-1][2]:
        runs[0] = (runs[-1][0], runs[0][1], runs[0][2])
        runs = runs[:-1]

    # Longest run of each type.
    beam_runs = [r for r in runs if r[2] == "beam"]
    cable_runs = [r for r in runs if r[2] == "cable"]

    def _longest(rs):
        if not rs:
            return None
        best = rs[0]
        for r in rs[1:]:
            if (r[1] - r[0]) > (best[1] - best[0]):
                best = r
        return best

    beam_run = _longest(beam_runs)
    cable_run = _longest(cable_runs)

    if beam_run is None and cable_run is not None:
        # All cable. Take two most distant anchors as top corners.
        corners_idx = _two_furthest_anchors(boundary, anchor_indices)
        c0 = anchor_indices[corners_idx[0]]
        c2 = anchor_indices[corners_idx[1]]
        c1 = anchor_indices[(corners_idx[0] + n_anchors // 2) % n_anchors]
        c3 = anchor_indices[(corners_idx[1] + n_anchors // 2) % n_anchors]
        corners = [c0, c1, c2, c3]
    elif cable_run is None and beam_run is not None:
        # All beam. Take two most distant anchors as top corners.
        corners_idx = _two_furthest_anchors(boundary, anchor_indices)
        c0 = anchor_indices[corners_idx[0]]
        c2 = anchor_indices[corners_idx[1]]
        c1 = anchor_indices[(corners_idx[0] + n_anchors // 2) % n_anchors]
        c3 = anchor_indices[(corners_idx[1] + n_anchors // 2) % n_anchors]
        corners = [c0, c1, c2, c3]
    else:
        # Mixed. Beam corners and cable corners.
        c0 = anchor_indices[beam_run[0]]
        c2 = anchor_indices[beam_run[1]]
        c1 = anchor_indices[cable_run[0]]
        c3 = anchor_indices[cable_run[1]]
        corners = [c0, c1, c2, c3]

    # Build the four sides by walking the boundary between corners.
    m = len(boundary)
    sides = []
    for k in range(4):
        a = corners[k]
        b = corners[(k + 1) % 4]
        pts = []
        i = a
        while True:
            pts.append(i)
            if i == b:
                break
            i = (i + 1) % m
        sides.append(pts)
    return sides, corners


def _two_furthest_anchors(boundary, anchor_indices):
    """Return indices (into anchor_indices list) of the two anchors
    furthest apart in 3D."""
    best = (0, 1)
    best_d = -1.0
    for i in range(len(anchor_indices)):
        for j in range(i + 1, len(anchor_indices)):
            a = boundary[anchor_indices[i]]
            b = boundary[anchor_indices[j]]
            d = float(np.linalg.norm(np.asarray(a) - np.asarray(b)))
            if d > best_d:
                best_d = d
                best = (i, j)
    return best


def _resample_side(boundary, side_points, target_n):
    """
    Resample a boundary side (list of boundary indices) into
    target_n equally-spaced (in arc length) points.

    Returns
    -------
    pts : (target_n, 3) array
    """
    pts = np.asarray([boundary[i] for i in side_points], dtype=float)
    if len(pts) == 1:
        return np.tile(pts, (target_n, 1))
    diff = np.diff(pts, axis=0)
    seg_len = np.linalg.norm(diff, axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg_len)))
    total = float(s[-1])
    if total < 1e-9:
        return np.tile(pts[0], (target_n, 1))

    out = np.zeros((target_n, 3))
    for k in range(target_n):
        target = (k / (target_n - 1.0)) * total
        idx = int(np.searchsorted(s, target, side="right") - 1)
        idx = max(0, min(idx, len(pts) - 2))
        seg_start = s[idx]
        seg_end = s[idx + 1]
        if seg_end - seg_start < 1e-12:
            out[k] = pts[idx]
        else:
            t = (target - seg_start) / (seg_end - seg_start)
            out[k] = pts[idx] * (1.0 - t) + pts[idx + 1] * t
    return out


def _tfi_grid(side_0, side_1, side_2, side_3, nx, ny):
    """
    Transfinite interpolation of a quad grid.

    side_0 : bottom edge, from corner 0 to corner 1
    side_1 : right edge,  from corner 1 to corner 2
    side_2 : top edge,    from corner 2 to corner 3
    side_3 : left edge,   from corner 3 to corner 0

    Each side is a (N, 3) array of points, ordered along the side.

    Corners must be consistent:
        side_0[0]  == side_3[-1]   (corner 0)
        side_0[-1] == side_1[0]    (corner 1)
        side_1[-1] == side_2[0]    (corner 2)
        side_2[-1] == side_3[0]    (corner 3)

    Returns
    -------
    grid : (nx, ny, 3) array
    """
    # Resample all four sides to (nx, ) for u-direction, (ny, ) for v.
    bottom = _resample_side_arr(side_0, nx)
    top = _resample_side_arr(side_2, nx)
    left = _resample_side_arr(side_3, ny)
    right = _resample_side_arr(side_1, ny)

    c0 = bottom[0]
    c1 = bottom[-1]
    c2 = top[-1]
    c3 = top[0]

    grid = np.zeros((nx, ny, 3))
    for i in range(nx):
        u = i / (nx - 1.0)
        for j in range(ny):
            v = j / (ny - 1.0)

            # Linear blending of the four sides.
            bottom_pt = bottom[i]
            top_pt = top[i]
            left_pt = left[j]
            right_pt = right[j]

            S = bottom_pt * (1.0 - v) + top_pt * v
            T = left_pt * (1.0 - u) + right_pt * u

            corner_term = (
                c0 * (1.0 - u) * (1.0 - v)
                + c1 * u * (1.0 - v)
                + c2 * u * v
                + c3 * (1.0 - u) * v
            )

            grid[i, j] = S + T - corner_term
    return grid


def _resample_side_arr(side_pts, target_n):
    """Resample a pre-computed side (N, 3) array into target_n points."""
    if len(side_pts) == 1:
        return np.tile(side_pts[0], (target_n, 1))
    diff = np.diff(side_pts, axis=0)
    seg_len = np.linalg.norm(diff, axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg_len)))
    total = float(s[-1])
    if total < 1e-9:
        return np.tile(side_pts[0], (target_n, 1))

    out = np.zeros((target_n, 3))
    for k in range(target_n):
        target = (k / (target_n - 1.0)) * total
        idx = int(np.searchsorted(s, target, side="right") - 1)
        idx = max(0, min(idx, len(side_pts) - 2))
        seg_start = s[idx]
        seg_end = s[idx + 1]
        if seg_end - seg_start < 1e-12:
            out[k] = side_pts[idx]
        else:
            t = (target - seg_start) / (seg_end - seg_start)
            out[k] = side_pts[idx] * (1.0 - t) + side_pts[idx + 1] * t
    return out





# =============================================================================
# PUBLIC FUNCTIONS
# =============================================================================

def build_mesh(boundary, anchor_indices, edge_types,
               nx=21, ny=21,
               membrane_q=1.0, cable_q=10.0,
               fixed_tip_indices=None):
    """
    Build a membrane mesh from a closed boundary, following the
    Membrane Boundary Schema.

    Parameters
    ----------
    boundary : (M, 3) array
        Ordered list of points on the closed boundary. First point
        must not equal last point.
    anchor_indices : list of int
        Which boundary points are anchors. Must be in order along
        the boundary, starting at any point.
    edge_types : list of str, same length as anchor_indices
        edge_types[k] describes the segment from anchor k to
        anchor k+1 (cyclic). "beam" or "cable".
    nx, ny : int
        Interior grid density.
    membrane_q : float
        Force density for interior edges.
    cable_q : float
        Force density for cable segments on the boundary.
    fixed_tip_indices : list of int or None
        Extra boundary points to fix. Use this to pin tips where
        the boundary is degenerate.

    Returns
    -------
    dict with:
        points        : (N, 3) array
        edges         : list of (i, j)
        fixed_indices : list of int
        q             : (E,) array
        diagnostics   : dict
    """
    boundary = np.asarray(boundary, dtype=float)
    if boundary.ndim != 2 or boundary.shape[1] != 3:
        raise ValueError("boundary must be (M, 3)")

    anchor_indices = list(anchor_indices)
    edge_types = list(edge_types)
    if len(anchor_indices) != len(edge_types):
        raise ValueError(
            "anchor_indices and edge_types must have the same length"
        )

    # ---- Express boundary as four sides for TFI
    sides, corners = _boundary_as_four_sides(
        boundary, anchor_indices, edge_types
    )

    # ---- Resample the four sides to nx (bottom/top) and ny (left/right)
    side_0_pts = np.asarray([boundary[i] for i in sides[0]], dtype=float)
    side_1_pts = np.asarray([boundary[i] for i in sides[1]], dtype=float)
    side_2_pts = np.asarray([boundary[i] for i in sides[2]], dtype=float)
    side_3_pts = np.asarray([boundary[i] for i in sides[3]], dtype=float)

    # ---- Build the interior grid by TFI
    grid = _tfi_grid(side_0_pts, side_1_pts, side_2_pts, side_3_pts,
                     nx=nx, ny=ny)

    # ---- Flatten grid into points array
    n_nodes = nx * ny
    points = np.zeros((n_nodes, 3))
    for i in range(nx):
        for j in range(ny):
            k = i * ny + j
            points[k] = grid[i, j]

    # ---- Build edges: each grid cell is split into two triangles
    edges = []
    for i in range(nx):
        for j in range(ny):
            k = i * ny + j
            if i + 1 < nx:
                edges.append((k, (i + 1) * ny + j))
            if j + 1 < ny:
                edges.append((k, i * ny + (j + 1)))

    # ---- Fixed indices: beam segments on the boundary, plus tips
    fixed_set = set()

    # Tip points (corners of the four sides)
    for c in corners:
        fixed_set.add(int(c))

    # Extra fixed tips (caller-provided)
    if fixed_tip_indices:
        for i in fixed_tip_indices:
            fixed_set.add(int(i))

    # Beam segments: all points along a "beam" side are fixed.
    # We approximate the "beam" side as the two sides that came
    # from the beam runs. Simplest rule: the corners tell us which
    # two sides are beam sides. For now, if either corner of a
    # side sits on a beam segment, we fix that side's points.
    # This is conservative; refine later if needed.
    #
    # For the current build, we fix the top and bottom rows of the
    # grid (i.e., side 0 and side 2 resampled) if there are any
    # beam edges. Otherwise we fix only the tips.

    has_beam = "beam" in edge_types
    if has_beam:
        for i in range(nx):
            fixed_set.add(i * ny + 0)
            fixed_set.add(i * ny + (ny - 1))

    # ---- q assignment
    q = np.full(len(edges), float(membrane_q))
    for k, (a, b) in enumerate(edges):
        ia = a // ny
        ib = b // ny
        ja = a % ny
        jb = b % ny

        on_beam_edge = has_beam and (
            (ja == 0 and jb == 0) or (ja == ny - 1 and jb == ny - 1)
        )
        on_free_end = (ia == 0 and ib == 0) or (ia == nx - 1 and ib == nx - 1)

        if on_free_end and "cable" in edge_types:
            # Cable runs at the tips: strong q
            q[k] = float(cable_q)
        elif on_beam_edge:
            # Beam edge: membrane q (the beam holds it)
            q[k] = float(membrane_q)
        else:
            q[k] = float(membrane_q)

    fixed_indices = sorted(fixed_set)

    diagnostics = {
        "nx": nx,
        "ny": ny,
        "n_nodes": n_nodes,
        "n_edges": len(edges),
        "n_fixed": len(fixed_indices),
        "n_free": n_nodes - len(fixed_indices),
        "has_beam": has_beam,
        "has_cable": "cable" in edge_types,
        "corners": [int(c) for c in corners],
    }

    return {
        "points": points,
        "edges": edges,
        "fixed_indices": fixed_indices,
        "q": q,
        "diagnostics": diagnostics,
    }


def build_and_solve(boundary, anchor_indices, edge_types,
                    nx=21, ny=21,
                    membrane_q=1.0, cable_q=10.0,
                    loads=None,
                    fixed_tip_indices=None):
    """
    Build the mesh and solve it with FDM in one call.

    Returns
    -------
    dict with:
        coordinates  : (N, 3) array - the equilibrium shape
        mesh         : the mesh dict from build_mesh
        solve_result : the dict from solve_fdm
    """
    mesh = build_mesh(
        boundary=boundary,
        anchor_indices=anchor_indices,
        edge_types=edge_types,
        nx=nx, ny=ny,
        membrane_q=membrane_q,
        cable_q=cable_q,
        fixed_tip_indices=fixed_tip_indices,
    )

    res = solve_fdm(
        mesh["points"],
        mesh["edges"],
        mesh["fixed_indices"],
        mesh["q"],
        loads=loads,
    )

    return {
        "coordinates": res["coordinates"],
        "mesh": mesh,
        "solve_result": res,
    }


# =============================================================================
# END OF engine/membrane_boundary.py
# =============================================================================





