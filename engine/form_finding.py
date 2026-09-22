# =============================================================================
# SDSe Engine - Form Finding
# =============================================================================
# Link 1 of the engine chain. See engine/SPEC_engine_chain.md.
#
# Purpose: find the equilibrium shape of a membrane or cable mesh.
#
# Method: Force Density Method (FDM).
#   Each edge (i, j) has a force density q = T / L, where T is the
#   tension in the edge and L is its length. At every free node,
#   the sum of forces from the edges connected to it must equal the
#   external load on that node. This gives a linear system in the
#   free-node coordinates:
#
#       K * x = p
#
#   where K is assembled from the force densities, x is the
#   unknown coordinates, and p is the load. Solve once. That is
#   the equilibrium shape.
#
# Reference:
#   Schek, H.-J. (1974). The force density method for form-finding
#   and computation of general networks.
#
# This is the classical FDM. NFDM (Natural Force Density Method)
# will be added later as an upgrade, using the same file.
#
# Units:
#   Length: m
#   Force: N
#   Force density: N/m
#
# =============================================================================

import math

import numpy as np


# =============================================================================
# FDM SOLVER
# =============================================================================

def solve_fdm(points, edges, fixed_indices, force_densities, loads=None):
    """
    Solve the Force Density Method equilibrium.

    Parameters
    ----------
    points : list of (x, y, z) or (n, 3) array
        Initial node coordinates. Used to determine which nodes are
        fixed and as a starting point for free nodes.
    edges : list of (i, j)
        Each edge connects node i to node j.
    fixed_indices : list of int
        Node indices that are fixed (boundary). Cannot move.
    force_densities : float or list of float
        Scalar applies the same force density to every edge.
        Otherwise, one value per edge in order.
    loads : (n, 3) array or None
        External load at each node in N. Zero for form-finding
        under self-weight only.
        Default: no load.

    Returns
    -------
    result : dict
        {
          "coordinates": (n, 3) array of new node coordinates,
          "residual_norm": float, residual after solution,
          "n_free": int, number of free nodes solved,
          "n_fixed": int, number of fixed nodes,
        }
    """
    points = np.asarray(points, dtype=float)
    edges = list(edges)
    fixed_indices = list(fixed_indices)
    n = points.shape[0]
    m = len(edges)

    if n == 0:
        raise ValueError("No nodes supplied.")
    if m == 0:
        raise ValueError("No edges supplied.")

    # Force densities
    if np.isscalar(force_densities):
        q = np.full(m, float(force_densities))
    else:
        q = np.asarray(force_densities, dtype=float)
        if q.shape[0] != m:
            raise ValueError(
                "force_densities length %d does not match edges %d"
                % (q.shape[0], m)
            )

    # Load vector
    if loads is None:
        loads = np.zeros((n, 3), dtype=float)
    else:
        loads = np.asarray(loads, dtype=float)
        if loads.shape != (n, 3):
            raise ValueError("loads must have shape (n, 3)")

    # Fixed mask
    fixed_mask = np.zeros(n, dtype=bool)
    for i in fixed_indices:
        if i < 0 or i >= n:
            raise ValueError("fixed index %d out of range" % i)
        fixed_mask[i] = True

    free_idx = np.where(~fixed_mask)[0]
    n_free = len(free_idx)

    if n_free == 0:
        # Everything is fixed. Nothing to solve.
        return {
            "coordinates": points.copy(),
            "residual_norm": 0.0,
            "n_free": 0,
            "n_fixed": n,
        }

    # Assemble the K matrix over all nodes.
    K = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(edges):
        qk = q[k]
        K[i, i] += qk
        K[j, j] += qk
        K[i, j] -= qk
        K[j, i] -= qk

    # Partition into free (F) and fixed (X) blocks.
    K_ff = K[np.ix_(free_idx, free_idx)]
    K_fx = K[np.ix_(free_idx, fixed_indices)]

    X = points.copy()

    for d in range(3):
        rhs = loads[free_idx, d].copy()
        rhs -= K_fx @ points[fixed_indices, d]
        X[free_idx, d] = np.linalg.solve(K_ff, rhs)

    residual = K @ X - loads
    residual_norm = float(np.linalg.norm(residual[free_idx]))

    return {
        "coordinates": X,
        "residual_norm": residual_norm,
        "n_free": n_free,
        "n_fixed": n - n_free,
    }


# =============================================================================
# SELF-TEST 1 - Flat mesh stays flat
# =============================================================================
# A flat square mesh, uniform force density, no loads, corners fixed.
# Expected: the mesh stays flat. If the free nodes move out of plane,
# the kernel is wrong.

def _test_flat_mesh():
    """Verify FDM keeps a flat mesh flat."""
    # 4x4 grid over 1 m x 1 m
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

    # Fix all boundary nodes
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


# =============================================================================
# SELF-TEST 2 - Hypar saddle from four raised corners
# =============================================================================
# A flat square mesh, corners at alternating heights.
# Expected: the surface forms a saddle, with two opposite corners
# high and two opposite corners low. The interior must not be flat.

def _test_hypar_saddle():
    """Verify FDM produces a saddle when opposite corners are raised."""
    nx = 5
    ny = 5
    side = 2.0

    points = []
    for j in range(ny):
        for i in range(nx):
            x = side * i / (nx - 1.0)
            y = side * j / (ny - 1.0)
            # Corners raised as hypar: opposite corners high
            z = 0.0
            if (i == 0 or i == nx - 1) and (j == 0 or j == ny - 1):
                if (i == 0 and j == 0) or (i == nx - 1 and j == ny - 1):
                    z = 0.5
                else:
                    z = -0.5
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

    # Fix all boundary nodes (they define the saddle)
    fixed = []
    for j in range(ny):
        for i in range(nx):
            idx = j * nx + i
            if i == 0 or i == nx - 1 or j == 0 or j == ny - 1:
                fixed.append(idx)

    res = solve_fdm(points, edges, fixed, 1.0)
    coords = res["coordinates"]

    # Check that the interior nodes are between the high and low
    # corner z-values (saddle-like), and not flat.
    interior_z = []
    for j in range(1, ny - 1):
        for i in range(1, nx - 1):
            idx = j * nx + i
            interior_z.append(coords[idx, 2])

    z_min = float(np.min(interior_z))
    z_max = float(np.max(interior_z))

    return {
        "converged": res["residual_norm"] < 1e-9,
        "interior_z_min": z_min,
        "interior_z_max": z_max,
        "saddle_ok": (
            z_min < -1e-4 and z_max > 1e-4 and z_max - z_min > 1e-3
        ),
    }





# =============================================================================
# SELF-TEST GATE
# =============================================================================
# Runs both tests. Returns a dict with results and a single "pass"
# boolean that the test runner can read.

def _verify_form_finding():
    """
    Run all form-finding self-tests. Returns a dict with results.
    """
    results = {}

    # Test 1: flat mesh
    t1 = _test_flat_mesh()
    results["flat_converged"] = t1["converged"]
    results["flat_z_max_dev"] = t1["z_max_deviation"]
    results["flat_xy_max_dev"] = t1["xy_max_deviation"]
    results["flat_ok"] = t1["flat_ok"]

    # Test 2: hypar saddle
    t2 = _test_hypar_saddle()
    results["saddle_converged"] = t2["converged"]
    results["saddle_z_min"] = t2["interior_z_min"]
    results["saddle_z_max"] = t2["interior_z_max"]
    results["saddle_ok"] = t2["saddle_ok"]

    results["pass"] = all([
        results["flat_converged"],
        results["flat_ok"],
        results["saddle_converged"],
        results["saddle_ok"],
    ])

    return results


# =============================================================================
# ENTRY POINT
# =============================================================================

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
    print("Test 2 - Hypar saddle")
    print("  converged        :", res["saddle_converged"])
    print("  interior z min   : %.6f" % res["saddle_z_min"])
    print("  interior z max   : %.6f" % res["saddle_z_max"])
    print("  saddle_ok        :", res["saddle_ok"])
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")





