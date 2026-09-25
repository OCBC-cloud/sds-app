# =============================================================================
# SDSe Engine - Membrane Boundary Schema (MBS)
# =============================================================================
# Universal engine for building the mesh of a membrane from its
# boundary.
#
# The schema:
#   1. A closed boundary. An ordered loop of 3D points.
#   2. Anchors. Discrete points on the boundary where the
#      membrane is held.
#   3. Edges between anchors. Each edge is "beam" or "cable".
#   4. The interior. A grid that fills the boundary.
#
# Two ways to fill the interior:
#   - If initial_points is provided, use them directly.
#   - If initial_points is None, use Transfinite Interpolation.
#
# Force densities q:
#   - If per_edge_q is provided, use it verbatim (length must
#     equal the number of mesh edges).
#   - Otherwise, assign q from membrane_q and cable_q using the
#     beam/cable classification of the boundary.
#
# History:
#   2026-09-24 - First build.
#   2026-09-24 - Fix grid corners, not boundary indices.
#   2026-09-25 - Add initial_points argument.
#   2026-09-25 - Init corners = None before grid decision.
#   2026-09-26 - Add per_edge_q. Backward-compatible. Enables
#                anisotropic prestress (warp vs weft) without
#                changing existing callers.
# =============================================================================

import numpy as np

from engine.form_finding import solve_fdm


def _boundary_as_four_sides(boundary, anchor_indices, edge_types):
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
# END OF CHUNK A1
# =============================================================================





# =============================================================================
# PUBLIC FUNCTIONS
# =============================================================================

def build_mesh(boundary, anchor_indices, edge_types,
               nx=21, ny=21,
               membrane_q=1.0, cable_q=10.0,
               fixed_tip_indices=None,
               initial_points=None,
               per_edge_q=None):
    """
    Build a membrane mesh from a closed boundary.

    Parameters
    ----------
    boundary : (M, 3) array
        Closed loop of boundary points.
    anchor_indices : list of int
        Indices into boundary where the membrane is held.
    edge_types : list of str
        "beam" or "cable" for each anchor-to-anchor edge.
    nx, ny : int
        Mesh resolution along the two grid directions.
    membrane_q : float
        Default force density for membrane edges.
    cable_q : float
        Force density for free-end cable edges.
    fixed_tip_indices : list of int, optional
        Extra node indices to fix (tips).
    initial_points : (nx, ny, 3) or (nx*ny, 3) array, optional
        If provided, use these as the initial mesh coordinates
        and skip the TFI interior fill.
    per_edge_q : (n_edges,) array, optional
        If provided, use these force densities verbatim.
        The length must equal the number of mesh edges
        produced by this function. If None, q is assigned
        from membrane_q and cable_q as before.

    Returns
    -------
    dict with keys:
        points         : (n_nodes, 3)
        edges          : list of (a, b)
        fixed_indices  : sorted list of int
        q              : (n_edges,) array
        diagnostics    : dict
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
                    "initial_points shape does not match (nx, ny, 3)"
                )
            grid = pts_in.copy()
        elif pts_in.ndim == 2:
            if pts_in.shape != (nx * ny, 3):
                raise ValueError(
                    "initial_points shape does not match (nx*ny, 3)"
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

    node_corners = [
        0,
        ny - 1,
        (nx - 1) * ny,
        (nx - 1) * ny + (ny - 1),
    ]
    for nc in node_corners:
        fixed_set.add(int(nc))

    if fixed_tip_indices:
        for i in fixed_tip_indices:
            fixed_set.add(int(i))

    has_beam = "beam" in edge_types
    if has_beam:
        for i in range(nx):
            fixed_set.add(i * ny + 0)
            fixed_set.add(i * ny + (ny - 1))

    if initial_points is not None:
        for j in range(ny):
            fixed_set.add(0 * ny + j)
            fixed_set.add((nx - 1) * ny + j)

    # ---- q assignment.
    if per_edge_q is not None:
        q_arr = np.asarray(per_edge_q, dtype=float)
        if q_arr.shape != (len(edges),):
            raise ValueError(
                "per_edge_q must have length %d (got %d)"
                % (len(edges), int(q_arr.size))
            )
        q = q_arr.copy()
    else:
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

    corners_out = []
    if corners is not None:
        corners_out = [int(c) for c in corners]

    diagnostics = {
        "nx": nx,
        "ny": ny,
        "n_nodes": n_nodes,
        "n_edges": len(edges),
        "n_fixed": len(fixed_indices),
        "n_free": n_nodes - len(fixed_indices),
        "has_beam": has_beam,
        "has_cable": "cable" in edge_types,
        "corners": corners_out,
        "used_initial_points": initial_points is not None,
        "used_per_edge_q": per_edge_q is not None,
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
                    initial_points=None,
                    per_edge_q=None):
    """
    Build the mesh and solve it with FDM in one call.

    Parameters
    ----------
    per_edge_q : (n_edges,) array, optional
        If provided, used verbatim as the force densities.
        Length must equal the number of edges in the mesh built
        by build_mesh with the same arguments. If None, q is
        assigned from membrane_q and cable_q.

    Returns
    -------
    dict with keys:
        coordinates   : (n_nodes, 3) solved coordinates
        mesh          : the build_mesh output dict
        solve_result  : the solve_fdm output dict
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
        per_edge_q=per_edge_q,
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





