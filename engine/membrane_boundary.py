# =============================================================================
# SDSe Engine - Membrane Boundary Schema (MBS)
# =============================================================================
# A universal engine for building the mesh of a membrane from its
# boundary.
#
# The schema:
#   1. A closed boundary. An ordered list of 3D points forming a loop.
#   2. Anchors. Discrete points on the boundary where the membrane is
#      held.
#   3. Edges between anchors. Each edge is either:
#        - "beam" : the boundary follows the shape and contour of a
#                   structural member. Points along that edge are FIXED.
#        - "cable": the boundary is a cable between two anchors. Points
#                   along that edge are FREE.
#   4. The interior. A grid that fills the boundary.
#
# Two ways to fill the interior:
#   - If initial_points is provided, use them directly. This is the
#     preferred route: the caller draws a surface with engine/
#     membrane_surface.py and hands the coordinates in.
#   - If initial_points is None, use Transfinite Interpolation (TFI)
#     to warp a rectangular grid onto the boundary.
#
# History:
#   2026-09-24 - First build.
#   2026-09-24 - Fix: fix grid corners, not boundary indices.
#   2026-09-25 - Add initial_points argument. If provided, use them
#                as the grid. If not, use TFI as before.
# =============================================================================

import numpy as np

from engine.form_finding import solve_fdm


def _boundary_edge_list(boundary, anchor_indices):
    """Given an ordered boundary and a list of anchor indices,
    return the list of segments between consecutive anchors."""
    n = len(anchor_indices)
    segments = []
    for k in range(n):
        a = anchor_indices[k]
        b = anchor_indices[(k + 1) % n]
        m = len(boundary)
        pts = []
        i = a
        while True:
            pts.append(i)
            if i == b:
                break
            i = (i + 1) % m
            if len(pts) > m:
                raise ValueError("Boundary walk did not reach anchor_b.")
        segments.append({"anchor_a": a, "anchor_b": b, "points": pts})
    return segments


def _boundary_as_four_sides(boundary, anchor_indices, edge_types):
    """Express the boundary as four sides for TFI blending."""
    n_anchors = len(anchor_indices)
    if n_anchors < 4:
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

    runs = []
    start = 0
    for k in range(1, n_anchors):
        if edge_types[k] != edge_types[start]:
            runs.append((start, k - 1, edge_types[start]))
            start = k
    runs.append((start, n_anchors - 1, edge_types[start]))
    if len(runs) > 1 and runs[0][2] == runs[-1][2]:
        runs[0] = (runs[-1][0], runs[0][1], runs[0][2])
        runs = runs[:-1]

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
        if n_anchors == 4:
            corners = [anchor_indices[0], anchor_indices[1],
                       anchor_indices[2], anchor_indices[3]]
        else:
            corners_idx = _two_furthest_anchors(boundary, anchor_indices)
            c0 = anchor_indices[corners_idx[0]]
            c2 = anchor_indices[corners_idx[1]]
            c1 = anchor_indices[(corners_idx[0] + n_anchors // 2) % n_anchors]
            c3 = anchor_indices[(corners_idx[1] + n_anchors // 2) % n_anchors]
            corners = [c0, c1, c2, c3]
    elif cable_run is None and beam_run is not None:
        if n_anchors == 4:
            corners = [anchor_indices[0], anchor_indices[1],
                       anchor_indices[2], anchor_indices[3]]
        else:
            corners_idx = _two_furthest_anchors(boundary, anchor_indices)
            c0 = anchor_indices[corners_idx[0]]
            c2 = anchor_indices[corners_idx[1]]
            c1 = anchor_indices[(corners_idx[0] + n_anchors // 2) % n_anchors]
            c3 = anchor_indices[(corners_idx[1] + n_anchors // 2) % n_anchors]
            corners = [c0, c1, c2, c3]
    else:
        c0 = anchor_indices[beam_run[0]]
        c2 = anchor_indices[beam_run[1]]
        c1 = anchor_indices[cable_run[0]]
        c3 = anchor_indices[cable_run[1]]
        corners = [c0, c1, c2, c3]

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


def _tfi_grid(side_0, side_1, side_2, side_3, nx, ny):
    """Transfinite interpolation of a quad grid."""
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


# =============================================================================
# PUBLIC FUNCTIONS
# =============================================================================

def build_mesh(boundary, anchor_indices, edge_types,
               nx=21, ny=21,
               membrane_q=1.0, cable_q=10.0,
               fixed_tip_indices=None,
               initial_points=None):
    """
    Build a membrane mesh from a closed boundary, following the
    Membrane Boundary Schema.

    Parameters
    ----------
    boundary : (M, 3) array
    anchor_indices : list of int
    edge_types : list of str
    nx, ny : int
        Grid density. If initial_points is provided, nx and ny must
        match the shape of initial_points when reshaped.
    membrane_q : float
    cable_q : float
    fixed_tip_indices : list of int or None
        Boundary indices to fix. Note: these are BOUNDARY indices,
        not mesh node indices.
    initial_points : (nx * ny, 3) array or (nx, ny, 3) array or None
        If provided, use these coordinates as the initial mesh grid.
        If None, build the grid via Transfinite Interpolation.
        This is the preferred route — hand in the coordinates
        produced by engine/membrane_surface.py.

    Returns
    -------
    dict with points, edges, fixed_indices, q, diagnostics.
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
corners = None
    # ---- Decide the grid.
    if initial_points is not None:
        pts_in = np.asarray(initial_points, dtype=float)
        if pts_in.ndim == 3:
            if pts_in.shape != (nx, ny, 3):
                raise ValueError(
                    "initial_points shape %s does not match (nx, ny, 3)"
                    % str(pts_in.shape)
                )
            grid = pts_in.copy()
        elif pts_in.ndim == 2:
            if pts_in.shape != (nx * ny, 3):
                raise ValueError(
                    "initial_points shape %s does not match (nx*ny, 3)"
                    % str(pts_in.shape)
                )
            grid = pts_in.reshape((nx, ny, 3))
        else:
            raise ValueError("initial_points must be 2D or 3D array")
    else:
        sides, corners = _boundary_as_four_sides(
            boundary, anchor_indices, edge_types
        )
        side_0_pts = np.asarray([boundary[i] for i in sides[0]], dtype=float)
        side_1_pts = np.asarray([boundary[i] for i in sides[1]], dtype=float)
        side_2_pts = np.asarray([boundary[i] for i in sides[2]], dtype=float)
        side_3_pts = np.asarray([boundary[i] for i in sides[3]], dtype=float)
        grid = _tfi_grid(side_0_pts, side_1_pts, side_2_pts, side_3_pts,
                         nx=nx, ny=ny)
        corners = None

    # ---- Flatten into points.
    n_nodes = nx * ny
    points = np.zeros((n_nodes, 3))
    for i in range(nx):
        for j in range(ny):
            k = i * ny + j
            points[k] = grid[i, j]

    # ---- Edges.
    edges = []
    for i in range(nx):
        for j in range(ny):
            k = i * ny + j
            if i + 1 < nx:
                edges.append((k, (i + 1) * ny + j))
            if j + 1 < ny:
                edges.append((k, i * ny + (j + 1)))

    # ---- Fixed indices.
    fixed_set = set()

    # The four GRID corners, as node indices.
    node_corners = [
        0,
        ny - 1,
        (nx - 1) * ny,
        (nx - 1) * ny + (ny - 1),
    ]
    for nc in node_corners:
        fixed_set.add(int(nc))

    # Extra fixed tips (caller-provided boundary indices).
    if fixed_tip_indices:
        for i in fixed_tip_indices:
            fixed_set.add(int(i))

    # If any edge type is "beam", fix the top and bottom rows of the
    # grid (the beam edges).
    has_beam = "beam" in edge_types
    if has_beam:
        for i in range(nx):
            fixed_set.add(i * ny + 0)
            fixed_set.add(i * ny + (ny - 1))

    # If initial_points came with taper_ends=True, all v-nodes at
    # u=0 and u=n_u-1 collapse to a single point. Fix them all.
    if initial_points is not None:
        for j in range(ny):
            fixed_set.add(0 * ny + j)
            fixed_set.add((nx - 1) * ny + j)

    # ---- q assignment.
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
            q[k] = float(cable_q)
        elif on_beam_edge:
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
        "corners": [int(c) for c in corners] if corners else [],
        "used_initial_points": initial_points is not None,
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
                    fixed_tip_indices=None,
                    initial_points=None):
    """
    Build the mesh and solve it with FDM in one call.
    """
    mesh = build_mesh(
        boundary=boundary,
        anchor_indices=anchor_indices,
        edge_types=edge_types,
        nx=nx, ny=ny,
        membrane_q=membrane_q,
        cable_q=cable_q,
        fixed_tip_indices=fixed_tip_indices,
        initial_points=initial_points,
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
