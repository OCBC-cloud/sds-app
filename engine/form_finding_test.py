# =============================================================================
# SDSe Engine - Form Finding Test
# =============================================================================
# Standalone test for engine/form_finding.py.
#
# This file is self-contained. It imports the solver from
# engine.form_finding and runs every check inside itself. It does
# NOT call the self-test inside form_finding.py, because that
# self-test measures the wrong residual at dir_only nodes (raw
# 3-vector residual, not the per-DOF residual).
#
# What this file adds over form_finding.py's own self-test:
#
#   1. Per-DOF residual. At a dir_only node, the two axes
#      perpendicular to the free direction carry constraint
#      reactions. Those reactions are SUPPOSED to be non-zero.
#      The correct equilibrium check is the residual projected
#      onto each free DOF, not the raw 3-vector residual.
#
#   2. Coupled dir_only. Two dir_only nodes connected to each
#      other. The old post-correction implementation could not
#      solve this. The reduced-basis solve must give machine-
#      precision residual on every free DOF.
#
#   3. Smooth cable bow. A taut cable held at the ends, with a
#      transverse load, and dir_only at every interior node.
#      The bow must be smooth, symmetric, and centred.
#
# Entry point: run() -> bool.
#
# Updated 2026-10-12. First version.
# =============================================================================

import math

import numpy as np

from engine.form_finding import solve_fdm, solve_fdm_settled


# =============================================================================
# PER-DOF RESIDUAL
# =============================================================================

def _dof_residual_norm(points, edges, fixed_indices, q,
                       loads, dir_only_map):
    """
    Compute the equilibrium residual projected onto each free DOF.

    Parameters
    ----------
    points : (n, 3) array of final coordinates
    edges : list of (i, j)
    fixed_indices : list of fixed node indices
    q : (m,) array of force densities
    loads : (n, 3) array of external loads
    dir_only_map : dict node_index -> unit direction (3-vector).
        Nodes not in this map and not fixed are fully free.

    Returns
    -------
    float : norm of the residual vector in the reduced DOF basis.
        A value near machine precision means the solve is in
        equilibrium along every free DOF.
    """
    points = np.asarray(points, dtype=float)
    edges = list(edges)
    q = np.asarray(q, dtype=float)
    loads = np.asarray(loads, dtype=float)

    n = points.shape[0]
    fixed_mask = np.zeros(n, dtype=bool)
    for i in fixed_indices:
        fixed_mask[i] = True

    # Raw residual: R = K X - loads.
    K = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(edges):
        qk = float(q[k])
        K[i, i] += qk
        K[j, j] += qk
        K[i, j] -= qk
        K[j, i] -= qk
    R = K @ points - loads

    # Project onto each free DOF.
    residual_components = []
    for i in range(n):
        if fixed_mask[i]:
            continue
        if i in dir_only_map:
            d = np.asarray(dir_only_map[i], dtype=float)
            dn = float(np.linalg.norm(d))
            if dn < 1e-12:
                continue
            d = d / dn
            residual_components.append(float(d @ R[i]))
        else:
            residual_components.append(float(R[i, 0]))
            residual_components.append(float(R[i, 1]))
            residual_components.append(float(R[i, 2]))

    if not residual_components:
        return 0.0
    return float(np.linalg.norm(np.asarray(residual_components)))


# =============================================================================
# TEST 1 - FLAT MESH STAYS FLAT
# =============================================================================

def _test_flat_mesh():
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
            edges.append((j * nx + i, j * nx + (i + 1)))
    for j in range(ny - 1):
        for i in range(nx):
            edges.append((j * nx + i, (j + 1) * nx + i))

    fixed = []
    for j in range(ny):
        for i in range(nx):
            idx = j * nx + i
            if i == 0 or i == nx - 1 or j == 0 or j == ny - 1:
                fixed.append(idx)

    res = solve_fdm(points, edges, fixed, 1.0)
    coords = res["coordinates"]
    z_max = float(np.max(np.abs(coords[:, 2])))
    xy_shift = float(np.max(np.abs(
        coords[:, :2] - np.asarray(points)[:, :2]
    )))

    return {
        "residual_norm": res["residual_norm"],
        "z_max_deviation": z_max,
        "xy_max_deviation": xy_shift,
        "ok": (
            res["residual_norm"] < 1e-9
            and z_max < 1e-9
            and xy_shift < 1e-9
        ),
    }


# =============================================================================
# TEST 2 - HYPAR SADDLE FROM NON-PLANAR BOUNDARY
# =============================================================================

def _test_hypar_saddle():
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
            edges.append((j * nx + i, j * nx + (i + 1)))
    for j in range(ny - 1):
        for i in range(nx):
            edges.append((j * nx + i, (j + 1) * nx + i))

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
            interior_zs.append(coords[j * nx + i, 2])

    z_min = float(np.min(interior_zs))
    z_max = float(np.max(interior_zs))

    return {
        "residual_norm": res["residual_norm"],
        "interior_z_min": z_min,
        "interior_z_max": z_max,
        "ok": (
            res["residual_norm"] < 1e-9
            and z_min < -1e-3
            and z_max > 1e-3
            and (z_max - z_min) > 1e-2
        ),
    }


# =============================================================================
# TEST 3 - Z-ONLY CONSTRAINT
# =============================================================================

def _test_z_only_constraint():
    points = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
    ]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    z_only = [1]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 1000.0, 1000.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0,
                    loads=loads, z_only_indices=z_only)
    coords = res["coordinates"]

    x_moved = abs(coords[1, 0] - 1.0)
    y_moved = abs(coords[1, 1] - 0.0)
    z_moved = abs(coords[1, 2] - 0.0)

    return {
        "residual_norm": res["residual_norm"],
        "x_moved": x_moved,
        "y_moved": y_moved,
        "z_moved": z_moved,
        "ok": (
            x_moved < 1e-9
            and y_moved < 1e-9
            and z_moved > 1e-3
        ),
    }


# =============================================================================
# TEST 4 - DIR-ONLY, SINGLE NODE, Y AXIS
# =============================================================================

def _test_dir_only_basic():
    points = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
    ]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    dir_only = [(1, (0.0, 1.0, 0.0))]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 1000.0, 1000.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0,
                    loads=loads, dir_only_indices=dir_only)
    coords = res["coordinates"]

    x_moved = abs(coords[1, 0] - 1.0)
    y_moved = abs(coords[1, 1] - 0.0)
    z_moved = abs(coords[1, 2] - 0.0)

    return {
        "residual_norm": res["residual_norm"],
        "x_moved": x_moved,
        "y_moved": y_moved,
        "z_moved": z_moved,
        "ok": (
            x_moved < 1e-9
            and z_moved < 1e-9
            and y_moved > 1e-3
        ),
    }


# =============================================================================
# TEST 5 - DIR-ONLY, DIAGONAL
# =============================================================================

def _test_dir_only_diagonal():
    points = [
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (2.0, 2.0, 0.0),
    ]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    d = (1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0), 0.0)
    dir_only = [(1, d)]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [1000.0, 0.0, 1000.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0,
                    loads=loads, dir_only_indices=dir_only)
    coords = res["coordinates"]

    z_moved = abs(coords[1, 2] - 0.0)
    dx = coords[1, 0] - 1.0
    dy = coords[1, 1] - 1.0
    along_ok = abs(dx - dy) < 1e-6
    moved = abs(dx) > 1e-4

    return {
        "residual_norm": res["residual_norm"],
        "dx": dx,
        "dy": dy,
        "z_moved": z_moved,
        "ok": (z_moved < 1e-9) and along_ok and moved,
    }


# =============================================================================
# TEST 6 - COUPLED DIR-ONLY NODES
# =============================================================================
# Two dir_only nodes connected to each other. This is the case
# the old post-correction implementation could not solve. With
# the reduced-basis solve, the per-DOF residual must be at
# machine precision.

def _test_coupled_dir_only():
    points = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (3.0, 0.0, 0.0),
    ]
    edges = [(0, 1), (1, 2), (2, 3)]
    fixed = [0, 3]
    dir_only_list = [
        (1, (0.00, 1.0, 0.0)),
        (2, (00.0, 1.0, )),
    ]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 100.0, 50.0],
        [0.0, 100.0, -50.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0,
                    loads=loads, dir_only_indices=dir_only_list)
    coords = res["coordinates"]

    dir_only_map = {i: np.asarray(d) for (i, d) in dir_only_list}
    per_dof = _dof_residual_norm(
        coords, edges, fixed, np.full(len(edges), 1.0),
        loads, dir_only_map,
    )

    x1 = abs(coords[1, 0] - 1.0)
    z1 = abs(coords[1, 2] - 0.0)
    x2 = abs(coords[2, 0] - 2.0)
    z2 = abs(coords[2, 2] - 0.0)

    return {
        "raw_residual": res["residual_norm"],
        "per_dof_residual": per_dof,
        "x1_moved": x1,
        "z1_moved": z1,
        "x2_moved": x2,
        "z2_moved": z2,
        "ok": (
            per_dof < 1e-9
            and x1 < 1e-9 and z1 < 1e-9
            and x2 < 1e-9 and z2 < 1e-9
        ),
    }


# =============================================================================
# TEST 7 - DIR-ONLY CHAIN, PER-DOF MACHINE PRECISION
# =============================================================================
# A six-node chain with four interior dir_only nodes. Every free
# DOF must have machine-precision residual.

def _test_dir_only_chain():
    n = 6
    points = [(float(i), 0.0, 0.0) for i in range(n)]
    edges = [(i, i + 1) for i in range(n - 1)]
    fixed = [0, n - 1]
    dir_only_list = [(i, (0.0, 1.0, 0.0)) for i in range(1, n - 1)]

    loads = np.zeros((n, 3))
    for i in range(1, n - 1):
        loads[i, 1] = 100.0 * i
        loads[i, 2] = 50.0 * (i % 2)

    res = solve_fdm(points, edges, fixed, 1.0,
                    loads=loads, dir_only_indices=dir_only_list)
    coords = res["coordinates"]

    dir_only_map = {i: np.asarray(d) for (i, d) in dir_only_list}
    per_dof = _dof_residual_norm(
        coords, edges, fixed, np.full(len(edges), 1.0),
        loads, dir_only_map,
    )

    return {
        "raw_residual": res["residual_norm"],
        "per_dof_residual": per_dof,
        "dof_count": res["dof_count"],
        "ok": per_dof < 1e-9,
    }


# =============================================================================
# TEST 8 - SMOOTH CABLE BOW
# =============================================================================
# A taut cable held at both ends, transverse load, dir_only at
# every interior node along the X axis. The bow must be smooth,
# symmetric, and centred. No X drift, no Z drift. Per-DOF
# residual at machine precision.

def _test_smooth_cable_bow():
    n = 21
    points = [(float(i), 0.0, 0.0) for i in range(n)]
    edges = [(i, i + 1) for i in range(n - 1)]
    fixed = [0, n - 1]
    dir_only_list = [(i, (0.0, 1.0, 0.0)) for i in range(1, n - 1)]

    loads = np.zeros((n, 3))
    for i in range(1, n - 1):
        loads[i, 1] = 100.0

    res = solve_fdm(points, edges, fixed, 1.0,
                    loads=loads, dir_only_indices=dir_only_list)
    coords = res["coordinates"]

    xs = coords[:, 0]
    ys = coords[:, 1]
    zs = coords[:, 2]

    x_drift = float(np.max(np.abs(xs - np.arange(n, dtype=float))))
    z_drift = float(np.max(np.abs(zs)))

    mid = n // 2
    y_mid = float(ys[mid])

    # Symmetry: y[i] == y[n-1-i] within tolerance.
    sym_max = 0.0
    for i in range(1, n - 1):
        sym_max = max(sym_max, abs(ys[i] - ys[n - 1 - i]))

    # Peak at mid: y[mid] strictly greater than y[i] for all other
    # interior nodes.
    peak_ok = all(ys[mid] >= ys[i] - 1e-12 for i in range(1, n - 1))

    dir_only_map = {i: np.asarray(d) for (i, d) in dir_only_list}
    per_dof = _dof_residual_norm(
        coords, edges, fixed, np.full(len(edges), 1.0),
        loads, dir_only_map,
    )

    return {
        "raw_residual": res["residual_norm"],
        "per_dof_residual": per_dof,
        "x_drift": x_drift,
        "z_drift": z_drift,
        "y_mid": y_mid,
        "symmetry_max": sym_max,
        "peak_ok": peak_ok,
        "ok": (
            x_drift < 1e-9
            and z_drift < 1e-9
            and sym_max < 1e-9
            and peak_ok
            and per_dof < 1e-9
        ),
    }


# =============================================================================
# TEST 9 - SETTLED MATCHES PASS 1 WHEN Q UNCHANGED
# =============================================================================

def _test_settled_match():
    points = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
    ]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    q = np.array([1000.0, 1000.0])

    res1 = solve_fdm(points, edges, fixed, q)
    res2 = solve_fdm_settled(
        res1["coordinates"], edges, fixed, q,
    )

    diff = float(np.max(np.abs(res1["reactions"] - res2["reactions"])))
    return {
        "reaction_diff": diff,
        "ok": diff < 1e-9,
    }


# =============================================================================
# TEST 10 - REACTIONS AT A DIR-ONLY NODE ARE ZERO ALONG ITS FREE AXIS
# =============================================================================
# A dir_only node is held in the two perpendicular axes. The
# constraint reactions should be nonzero in those axes, and zero
# along the free axis. This is a physics check on the solver, not
# just a numerical one.

def _test_dir_only_reactions():
    points = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
    ]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    dir_only_list = [(1, (0.0, 1.0, 0.0))]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 1000.0, 1000.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0,
                    loads=loads, dir_only_indices=dir_only_list)
    coords = res["coordinates"]

    # Recompute the raw residual at the dir_only node.
    K = np.zeros((3, 3), dtype=float)
    for (i, j) in edges:
        K[i, i] += 1.0
        K[j, j] += 1.0
        K[i, j] -= 1.0
        K[j, i] -= 1.0
    R = K @ coords - loads

    # Along the free direction (Y), the residual should be zero.
    r_along = abs(float(R[1, 1]))
    # Perpendicular axes (X and Z) may carry reaction forces.
    r_x = abs(float(R[1, 0]))
    r_z = abs(float(R[1, 2]))

    return {
        "residual_along_free_axis": r_along,
        "residual_perp_x": r_x,
        "residual_perp_z": r_z,
        "ok": r_along < 1e-9,
    }


# =============================================================================
# RUN ALL
# =============================================================================

def run():
    """
    Run all form-finding tests. Return True if every test passes.
    Print a compact report.
    """
    print("=" * 60)
    print("TEST: engine/form_finding.py - FDM solver (standalone)")
    print("=" * 60)

    results = {}
    overall = True

    tests = [
        ("flat_mesh_stays_flat", _test_flat_mesh),
        ("hypar_saddle_from_boundary", _test_hypar_saddle),
        ("z_only_constraint", _test_z_only_constraint),
        ("dir_only_basic_y_axis", _test_dir_only_basic),
        ("dir_only_diagonal", _test_dir_only_diagonal),
        ("coupled_dir_only", _test_coupled_dir_only),
        ("dir_only_chain", _test_dir_only_chain),
        ("smooth_cable_bow", _test_smooth_cable_bow),
        ("settled_matches_pass1", _test_settled_match),
        ("dir_only_reactions", _test_dir_only_reactions),
    ]

    for name, fn in tests:
        try:
            r = fn()
            ok = bool(r.get("ok", False))
            results[name] = (ok, r)
            status = "PASS" if ok else "FAIL"
            if not ok:
                overall = False
            print("  %-30s %s" % (name, status))
            for k, v in r.items():
                if k == "ok":
                    continue
                if isinstance(v, float):
                    print("      %-26s %.6e" % (k, v))
                else:
                    print("      %-26s %s" % (k, v))
        except Exception as e:
            results[name] = (False, {"exception": str(e)})
            overall = False
            print("  %-30s FAIL" % name)
            print("      exception: %s" % str(e))

    print("-" * 60)
    print("RESULT:", "PASS" if overall else "FAIL")
    return overall


# =============================================================================
# STANDALONE ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    ok = run()
    raise SystemExit(0 if ok else 1)


# =============================================================================
# END OF engine/form_finding_test.py
# =============================================================================
