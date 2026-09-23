# =============================================================================
# SDSe Engine - Form Finding
# =============================================================================
# Link 1 of the engine chain. See engine/SPEC_engine_chain.md.
#
# Purpose: find the equilibrium shape of a membrane or cable mesh.
#
# Method: Force Density Method (FDM).
#   Each edge (i, j) has a force density q = T / L. At every free
#   node, the sum of forces from the edges connected to it must
#   equal the external load on that node. This gives a linear
#   system in the free-node coordinates: K * x = p.
#
# Node constraints:
#   - fixed_indices: node cannot move at all (x, y, z fixed).
#   - z_only_indices: node can move in z only. Its x and y stay at
#     their initial values. Use this for nodes on a rigid beam edge,
#     where the beam does not move in plan but the fabric can pull
#     the edge up or down.
#   - All other nodes: free in all three directions.
#
# Reference:
#   Schek, H.-J. (1974). The force density method for form-finding
#   and computation of general networks.
#
# Units: m, N, N/m.
#
# History:
#   2026-09-22 - First build with flat and saddle self-tests.
#   2026-09-22 - mesh_size_for_span() added.
#   2026-09-23 - z_only_indices argument added.
#   2026-09-23 - mesh_size_for_shape() added. Mesh divisibility rule.
#                mesh_size_for_span() kept as a rectangle wrapper.
# =============================================================================

import math

import numpy as np


# =============================================================================
# MESH SIZE RULE
# =============================================================================
# The mesh must divide the shape's sides evenly, after the corners
# are removed.
#
#   n = N * k + C
#
#   N = number of sides
#   C = number of corners
#   k = any positive integer
#
# Examples:
#   Rectangle, square, rhombus (N=4, C=4): 8, 12, 16, 20, 24, 28, ...
#   Triangle (N=3, C=3):                   6, 9, 12, 15, 18, 21, 24, ...
#   Hexagon (N=6, C=6):                    12, 18, 24, 30, ...
#
# The mesh size must be one of these values. It must be at least 21
# nodes along the span, and at most 101.

MESH_MIN = 21
MESH_MAX = 101


def mesh_size_for_shape(span_m, n_sides, n_corners):
    """
    Return the recommended mesh size along the span, in nodes.

    The result belongs to the series n = n_sides * k + n_corners,
    bounded between MESH_MIN and MESH_MAX.

    Parameters
    ----------
    span_m : float
        The span along which the mesh size is being computed.
        If None or <= 0, the smallest valid value is returned.
    n_sides : int
        Number of sides of the shape (4 for rectangle, 3 for
        triangle, 6 for hexagon).
    n_corners : int
        Number of corners of the shape (usually equal to n_sides
        for a simple polygon).
    """
    if n_sides is None or n_corners is None:
        raise ValueError("n_sides and n_corners must be provided.")
    if n_sides <= 0 or n_corners < 0:
        raise ValueError("n_sides must be positive; n_corners >= 0.")

    # Nominal target: one node per metre, clamped to [MESH_MIN, MESH_MAX].
    if span_m is None or span_m <= 0:
        nominal = MESH_MIN
    else:
        nominal = int(round(span_m))
        if nominal < MESH_MIN:
            nominal = MESH_MIN
        if nominal > MESH_MAX:
            nominal = MESH_MAX

    # Find the valid value in the series nearest to the nominal target.
    # Series: n = n_sides * k + n_corners, for k = 0, 1, 2, ...
    # Since n_corners is usually equal to n_sides, the series starts
    # at n_sides * 1 + n_corners in practice, but we allow k = 0 for
    # degenerate shapes. We restrict candidates to [MESH_MIN, MESH_MAX].
    best = None
    best_dist = None
    k = 0
    # Cap k at a reasonable ceiling so we do not loop forever.
    k_max = (MESH_MAX // n_sides) + 2
    while k <= k_max:
        candidate = n_sides * k + n_corners
        if MESH_MIN <= candidate <= MESH_MAX:
            dist = abs(candidate - nominal)
            if best is None or dist < best_dist:
                best = candidate
                best_dist = dist
        k += 1

    if best is None:
        # No valid value in range. Fall back to the smallest valid
        # value in the series, even if it is below MESH_MIN.
        # This should not happen for the shapes SDSe supports.
        best = n_sides * 1 + n_corners

    return best


def mesh_size_for_span(span_m):
    """
    Backward-compatible wrapper. Rectangular shapes only (N=4, C=4).
    New code should call mesh_size_for_shape directly.
    """
    return mesh_size_for_shape(span_m, 4, 4)


# =============================================================================
# FDM SOLVER
# =============================================================================

def solve_fdm(points, edges, fixed_indices, force_densities,
              loads=None, z_only_indices=None):
    """
    Solve the Force Density Method equilibrium.

    Parameters
    ----------
    points : (n, 3) array of node coordinates
    edges : list of (i, j) edge pairs
    fixed_indices : list of int
        Nodes fixed in x, y, z.
    force_densities : float or (m,) array
        Scalar applies the same q to all edges.
    loads : (n, 3) array or None
        External load at each node in N. Default: no load.
    z_only_indices : list of int or None
        Nodes that can move only in z. Their x and y are fixed
        at the values in points. Default: None.

    Returns
    -------
    result : dict
        coordinates, residual_norm, n_free, n_fixed
    """
    points = np.asarray(points, dtype=float)
    edges = list(edges)
    fixed_indices = list(fixed_indices)
    if z_only_indices is None:
        z_only_indices = []
    else:
        z_only_indices = list(z_only_indices)

    n = points.shape[0]
    m = len(edges)

    if n == 0:
        raise ValueError("No nodes supplied.")
    if m == 0:
        raise ValueError("No edges supplied.")

    if np.isscalar(force_densities):
        q = np.full(m, float(force_densities))
    else:
        q = np.asarray(force_densities, dtype=float)
        if q.shape[0] != m:
            raise ValueError(
                "force_densities length %d does not match edges %d"
                % (q.shape[0], m)
            )

    if loads is None:
        loads = np.zeros((n, 3), dtype=float)
    else:
        loads = np.asarray(loads, dtype=float)
        if loads.shape != (n, 3):
            raise ValueError("loads must have shape (n, 3)")

    # ---- Build masks
    fixed_mask = np.zeros(n, dtype=bool)
    for i in fixed_indices:
        if i < 0 or i >= n:
            raise ValueError("fixed index %d out of range" % i)
        fixed_mask[i] = True

    z_only_mask = np.zeros(n, dtype=bool)
    for i in z_only_indices:
        if i < 0 or i >= n:
            raise ValueError("z_only index %d out of range" % i)
        if fixed_mask[i]:
            # A fixed node is not z_only. Fixed wins.
            continue
        z_only_mask[i] = True

    # ---- Assemble the global K matrix
    K = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(edges):
        qk = q[k]
        K[i, i] += qk
        K[j, j] += qk
        K[i, j] -= qk
        K[j, i] -= qk

    X = points.copy()

    # ---- Solve for free DOFs, one axis at a time.
    # For x and y axes:
    #   free nodes (not fixed, not z_only) participate.
    #   z_only nodes are FIXED in this axis.
    # For z axis:
    #   free nodes and z_only nodes participate.
    #   Only truly fixed nodes are fixed in this axis.

    def _solve_axis(axis, mask_free):
        idx = np.where(mask_free)[0]
        idx_fixed = np.where(~mask_free)[0]
        if len(idx) == 0:
            return
        K_ff = K[np.ix_(idx, idx)]
        K_fx = K[np.ix_(idx, idx_fixed)]
        rhs = loads[idx, axis].copy()
        rhs -= K_fx @ points[idx_fixed, axis]
        X[idx, axis] = np.linalg.solve(K_ff, rhs)

    # ---- x and y axes: only truly free nodes participate
    free_xy = (~fixed_mask) & (~z_only_mask)
    _solve_axis(0, free_xy)
    _solve_axis(1, free_xy)

    # ---- z axis: free + z_only participate
    free_z = (~fixed_mask)
    _solve_axis(2, free_z)

    residual = K @ X - loads
    free_all = ~fixed_mask
    residual_norm = float(np.linalg.norm(residual[free_all]))

    return {
        "coordinates": X,
        "residual_norm": residual_norm,
        "n_free": int(free_all.sum()),
        "n_fixed": int(fixed_mask.sum()),
    }




# =============================================================================
# SELF-TESTS
# =============================================================================

def _test_flat_mesh():
    """Verify FDM keeps a flat mesh flat."""
    nx = 4
    ny = 4
    points = []
    for j in range(ny):
        for i in range(nx):
            x = i / (nx - 1.0)
            y = j / (ny - 1.0)
            points.append((x, y, 0.0))

    edges = []
    for j in range(ny):
        for i in range(nx - 1):
            a = j * nx + i
            b = j * nx + (i + 1)
            edges.append((a, b))
    for j in range(ny - 1):
        for i in range(nx):
            a = j * nx + i
            b = (j + 1) * nx + i
            edges.append((a, b))

    fixed = []
    for j in range(ny):
        for i in range(nx):
            idx = j * nx + i
            if i == 0 or i == nx - 1 or j == 0 or j == ny - 1:
                fixed.append(idx)

    res = solve_fdm(points, edges, fixed, 1.0)

    coords = res["coordinates"]
    z_max = float(np.max(np.abs(coords[:, 2])))
    xy_shift = float(np.max(np.abs(coords[:, :2] - np.asarray(points)[:, :2])))

    return {
        "converged": res["residual_norm"] < 1e-9,
        "z_max_deviation": z_max,
        "xy_max_deviation": xy_shift,
        "flat_ok": z_max < 1e-9 and xy_shift < 1e-9,
    }


def _test_hypar_saddle():
    """Verify FDM forms a saddle from a non-planar boundary."""
    nx = 7
    ny = 7
    side = 2.0
    corner_amp = 0.5

    points = []
    for j in range(ny):
        for i in range(nx):
            x = side * i / (nx - 1.0)
            y = side * j / (ny - 1.0)
            z = 0.0
            on_boundary = (
                i == 0 or i == nx - 1 or j == 0 or j == ny - 1
            )
            if on_boundary:
                xi = i / (nx - 1.0)
                yj = j / (ny - 1.0)
                z = corner_amp * math.cos(math.pi * xi) * math.cos(math.pi * yj)
            points.append((x, y, z))

    edges = []
    for j in range(ny):
        for i in range(nx - 1):
            a = j * nx + i
            b = j * nx + (i + 1)
            edges.append((a, b))
    for j in range(ny - 1):
        for i in range(nx):
            a = j * nx + i
            b = (j + 1) * nx + i
            edges.append((a, b))

    fixed = []
    for j in range(ny):
        for i in range(nx):
            idx = j * nx + i
            if i == 0 or i == nx - 1 or j == 0 or j == ny - 1:
                fixed.append(idx)

    res = solve_fdm(points, edges, fixed, 1.0)
    coords = res["coordinates"]

    interior_zs = []
    for j in range(1, ny - 1):
        for i in range(1, nx - 1):
            idx = j * nx + i
            interior_zs.append(coords[idx, 2])

    z_min = float(np.min(interior_zs))
    z_max = float(np.max(interior_zs))

    has_positive = z_max > 1e-3
    has_negative = z_min < -1e-3
    range_ok = (z_max - z_min) > 1e-2

    return {
        "converged": res["residual_norm"] < 1e-9,
        "interior_z_min": z_min,
        "interior_z_max": z_max,
        "saddle_ok": has_positive and has_negative and range_ok,
    }


def _test_z_only_constraint():
    """Verify that a z_only node moves only in z."""
    # 3 nodes in a row along x, with the two ends fixed.
    points = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
    ]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    # Middle node: z-only.
    z_only = [1]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 1000.0, 1000.0],   # pull node 1 in y and z
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0,
                    loads=loads, z_only_indices=z_only)
    coords = res["coordinates"]

    # x should not have moved.
    x_moved = abs(coords[1, 0] - 1.0)
    # y should not have moved (z_only in y too).
    y_moved = abs(coords[1, 1] - 0.0)
    # z should have moved.
    z_moved = abs(coords[1, 2] - 0.0)

    return {
        "converged": res["residual_norm"] < 1e-6,
        "x_moved": x_moved,
        "y_moved": y_moved,
        "z_moved": z_moved,
        "z_only_ok": x_moved < 1e-9 and y_moved < 1e-9 and z_moved > 1e-3,
    }


def _test_mesh_size_for_shape():
    """Verify the mesh divisibility rule returns valid values."""
    # Rectangle: N=4, C=4 -> series 8, 12, 16, 20, 24, 28, ...
    r1 = mesh_size_for_shape(25.0, 4, 4)
    r2 = mesh_size_for_shape(28.0, 4, 4)
    r3 = mesh_size_for_shape(50.0, 4, 4)
    r4 = mesh_size_for_shape(None, 4, 4)

    # Triangle: N=3, C=3 -> series 6, 9, 12, 15, 18, 21, 24, ...
    t1 = mesh_size_for_shape(22.0, 3, 3)

    # Every result must be in the series and in range.
    def in_series(n, sides, corners):
        if n < corners:
            return False
        return (n - corners) % sides == 0

    rect_ok = all([
        in_series(r1, 4, 4),
        in_series(r2, 4, 4),
        in_series(r3, 4, 4),
        in_series(r4, 4, 4),
        MESH_MIN <= r1 <= MESH_MAX,
        MESH_MIN <= r2 <= MESH_MAX,
        MESH_MIN <= r3 <= MESH_MAX,
        MESH_MIN <= r4 <= MESH_MAX,
    ])
    tri_ok = all([
        in_series(t1, 3, 3),
        MESH_MIN <= t1 <= MESH_MAX,
    ])

    return {
        "rect_near_25": r1,
        "rect_near_28": r2,
        "rect_near_50": r3,
        "rect_none": r4,
        "tri_near_22": t1,
        "rect_series_ok": rect_ok,
        "tri_series_ok": tri_ok,
        "mesh_rule_ok": rect_ok and tri_ok,
    }


def _verify_form_finding():
    """Run all form-finding self-tests. Returns a dict with results."""
    results = {}

    t1 = _test_flat_mesh()
    results["flat_converged"] = t1["converged"]
    results["flat_z_max_dev"] = t1["z_max_deviation"]
    results["flat_xy_max_dev"] = t1["xy_max_deviation"]
    results["flat_ok"] = t1["flat_ok"]

    t2 = _test_hypar_saddle()
    results["saddle_converged"] = t2["converged"]
    results["saddle_z_min"] = t2["interior_z_min"]
    results["saddle_z_max"] = t2["interior_z_max"]
    results["saddle_ok"] = t2["saddle_ok"]

    t3 = _test_z_only_constraint()
    results["z_only_converged"] = t3["converged"]
    results["z_only_x_moved"] = t3["x_moved"]
    results["z_only_y_moved"] = t3["y_moved"]
    results["z_only_z_moved"] = t3["z_moved"]
    results["z_only_ok"] = t3["z_only_ok"]

    t4 = _test_mesh_size_for_shape()
    results["mesh_rect_near_25"] = t4["rect_near_25"]
    results["mesh_rect_near_28"] = t4["rect_near_28"]
    results["mesh_rect_near_50"] = t4["rect_near_50"]
    results["mesh_rect_none"] = t4["rect_none"]
    results["mesh_tri_near_22"] = t4["tri_near_22"]
    results["mesh_rule_ok"] = t4["mesh_rule_ok"]

    results["pass"] = all([
        results["flat_converged"],
        results["flat_ok"],
        results["saddle_converged"],
        results["saddle_ok"],
        results["z_only_converged"],
        results["z_only_ok"],
        results["mesh_rule_ok"],
    ])

    return results


if __name__ == "__main__":
    print("engine/form_finding.py - Force Density Method")
    print("-" * 70)

    res = _verify_form_finding()

    print("Test 1 - Flat mesh")
    print("  converged        :", res["flat_converged"])
    print("  z max deviation  : %.6e" % res["flat_z_max_dev"])
    print("  xy max deviation : %.6e" % res["flat_xy_max_dev"])
    print("  flat_ok          :", res["flat_ok"])
    print()
    print("Test 2 - Saddle from non-planar boundary")
    print("  converged        :", res["saddle_converged"])
    print("  interior z min   : %.6f" % res["saddle_z_min"])
    print("  interior z max   : %.6f" % res["saddle_z_max"])
    print("  saddle_ok        :", res["saddle_ok"])
    print()
    print("Test 3 - z_only constraint")
    print("  converged        :", res["z_only_converged"])
    print("  x moved          : %.6e" % res["z_only_x_moved"])
    print("  y moved          : %.6e" % res["z_only_y_moved"])
    print("  z moved          : %.6f" % res["z_only_z_moved"])
    print("  z_only_ok        :", res["z_only_ok"])
    print()
    print("Test 4 - Mesh divisibility rule")
    print("  rect near 25 m   :", res["mesh_rect_near_25"])
    print("  rect near 28 m   :", res["mesh_rect_near_28"])
    print("  rect near 50 m   :", res["mesh_rect_near_50"])
    print("  rect span None   :", res["mesh_rect_none"])
    print("  tri  near 22 m   :", res["mesh_tri_near_22"])
    print("  mesh_rule_ok     :", res["mesh_rule_ok"])
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")





