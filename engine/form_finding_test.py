# =============================================================================
# SDSe Engine - Form Finding Test (self-contained)
# =============================================================================
# Carries BOTH the reduced-basis FDM solver AND the tests that prove it.
# Imports nothing from engine/form_finding.py. The original file is untouched.
# Entry point: run() -> bool.
# =============================================================================

import math
import numpy as np


# =============================================================================
# MESH SIZE RULE
# =============================================================================

MESH_MIN = 21
MESH_MAX = 101


def mesh_size_for_shape(span_m, n_sides, n_corners):
    if n_sides is None or n_corners is None:
        raise ValueError("n_sides and n_corners must be provided.")
    if n_sides <= 0 or n_corners < 0:
        raise ValueError("n_sides must be positive; n_corners >= 0.")
    if span_m is None or span_m <= 0:
        nominal = MESH_MIN
    else:
        nominal = int(round(span_m))
        if nominal < MESH_MIN:
            nominal = MESH_MIN
        if nominal > MESH_MAX:
            nominal = MESH_MAX
    best = None
    best_dist = None
    k = 0
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
        best = n_sides * 1 + n_corners
    return best


def mesh_size_for_span(span_m):
    return mesh_size_for_shape(span_m, 4, 4)


def _unit_direction(direction):
    d = np.asarray(direction, dtype=float)
    n = float(np.linalg.norm(d))
    if n < 1e-12:
        raise ValueError("direction vector has zero length")
    return d / n


# =============================================================================
# FDM SOLVER - PASS 1
# =============================================================================

def solve_fdm(points, edges, fixed_indices, force_densities,
              loads=None, z_only_indices=None, dir_only_indices=None):
    points = np.asarray(points, dtype=float)
    edges = list(edges)
    fixed_indices = list(fixed_indices)
    if z_only_indices is None:
        z_only_indices = []
    else:
        z_only_indices = list(z_only_indices)
    if dir_only_indices is None:
        dir_only_indices = []
    else:
        dir_only_indices = list(dir_only_indices)

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
            raise ValueError("force_densities length mismatch")

    if float(np.min(q)) <= 0.0:
        raise ValueError("force_densities must be > 0")

    if loads is None:
        loads = np.zeros((n, 3), dtype=float)
    else:
        loads = np.asarray(loads, dtype=float)
        if loads.shape != (n, 3):
            raise ValueError("loads must have shape (n, 3)")

    fixed_mask = np.zeros(n, dtype=bool)
    for i in fixed_indices:
        if i < 0 or i >= n:
            raise ValueError("fixed index %d out of range" % i)
        fixed_mask[i] = True

    node_dir = [None] * n
    node_is_dir_only = np.zeros(n, dtype=bool)

    for entry in dir_only_indices:
        node_i, direction = entry
        node_i = int(node_i)
        if node_i < 0 or node_i >= n:
            raise ValueError("dir_only index out of range")
        if fixed_mask[node_i]:
            continue
        node_dir[node_i] = _unit_direction(direction)
        node_is_dir_only[node_i] = True

    for i in z_only_indices:
        if i < 0 or i >= n:
            raise ValueError("z_only index out of range")
        if fixed_mask[i]:
            continue
        if node_is_dir_only[i]:
            continue
        node_dir[i] = np.array([0.0, 0.0, 1.0])
        node_is_dir_only[i] = True

    K = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(edges):
        qk = q[k]
        K[i, i] += qk
        K[j, j] += qk
        K[i, j] -= qk
        K[j, i] -= qk

    dof_of_node = [None] * n
    dof_basis = []
    dof_node = []

    for i in range(n):
        if fixed_mask[i]:
            dof_of_node[i] = []
            continue
        if node_is_dir_only[i]:
            d = node_dir[i]
            dof_of_node[i] = [(len(dof_basis), d)]
            dof_basis.append(d)
            dof_node.append(i)
        else:
            ex = np.array([1.0, 0.0, 0.0])
            ey = np.array([0.0, 1.0, 0.0])
            ez = np.array([0.0, 0.0, 1.0])
            dof_of_node[i] = [
                (len(dof_basis), ex),
                (len(dof_basis) + 1, ey),
                (len(dof_basis) + 2, ez),
            ]
            dof_basis.extend([ex, ey, ez])
            dof_node.extend([i, i, i])

    n_dof = len(dof_basis)

    if n_dof == 0:
        X = points.copy()
        residual = K @ X - loads
        reactions = np.zeros((n, 3), dtype=float)
        for i in fixed_indices:
            reactions[i, :] = -residual[i, :] / 1000.0
        return {
            "coordinates": X,
            "residual_norm": 0.0,
            "n_free": 0,
            "n_fixed": int(fixed_mask.sum()),
            "dof_count": 0,
            "reactions": reactions,
        }

    K_red = np.zeros((n_dof, n_dof), dtype=float)
    rhs = np.zeros(n_dof, dtype=float)

    phi = np.zeros((n_dof, 3), dtype=float)
    for a in range(n_dof):
        phi[a, :] = dof_basis[a]

    node_basis = [None] * n
    node_dof_idx = [None] * n
    for i in range(n):
        if not dof_of_node[i]:
            node_basis[i] = np.zeros((0, 3), dtype=float)
            node_dof_idx[i] = np.zeros((0,), dtype=int)
        else:
            rows = [dof_basis[a] for (a, _) in dof_of_node[i]]
            idxs = [a for (a, _) in dof_of_node[i]]
            node_basis[i] = np.vstack(rows)
            node_dof_idx[i] = np.array(idxs, dtype=int)

    for k, (i, j) in enumerate(edges):
        qk = float(q[k])
        Bi = node_basis[i]
        Bj = node_basis[j]
        ki = Bi.shape[0]
        kj = Bj.shape[0]
        if ki == 0 and kj == 0:
            continue
        if ki > 0:
            K_red[np.ix_(node_dof_idx[i], node_dof_idx[i])] += qk * (Bi @ Bi.T)
        if kj > 0:
            K_red[np.ix_(node_dof_idx[j], node_dof_idx[j])] += qk * (Bj @ Bj.T)
        if ki > 0 and kj > 0:
            cross = qk * (Bi @ Bj.T)
            K_red[np.ix_(node_dof_idx[i], node_dof_idx[j])] -= cross
            K_red[np.ix_(node_dof_idx[j], node_dof_idx[i])] -= cross.T

    F = loads.copy()
    X0 = points
    for k, (i, j) in enumerate(edges):
        qk = float(q[k])
        diff = X0[i] - X0[j]
        F[i] -= qk * diff
        F[j] += qk * diff

    for a in range(n_dof):
        i = dof_node[a]
        rhs[a] = float(phi[a] @ F[i])

    try:
        u = np.linalg.solve(K_red, rhs)
    except np.linalg.LinAlgError:
        u, *_ = np.linalg.lstsq(K_red, rhs, rcond=None)

    X = X0.copy()
    for a in range(n_dof):
        i = dof_node[a]
        X[i] = X[i] + u[a] * dof_basis[a]

    residual = K @ X - loads
    free_all = ~fixed_mask
    residual_norm = float(np.linalg.norm(residual[free_all]))

    reactions = np.zeros((n, 3), dtype=float)
    for i in fixed_indices:
        reactions[i, :] = -residual[i, :] / 1000.0

    return {
        "coordinates": X,
        "residual_norm": residual_norm,
        "n_free": int(np.sum(free_all)),
        "n_fixed": int(fixed_mask.sum()),
        "dof_count": int(n_dof),
        "reactions": reactions,
    }


# =============================================================================
# FDM SOLVER - PASS 2
# =============================================================================

def solve_fdm_settled(settled_points, edges, fixed_indices, settled_q):
    points = np.asarray(settled_points, dtype=float)
    edges = list(edges)
    fixed_indices = list(fixed_indices)
    n = points.shape[0]
    m = len(edges)
    if n == 0:
        raise ValueError("No nodes supplied.")
    if m == 0:
        raise ValueError("No edges supplied.")
    q = np.asarray(settled_q, dtype=float)
    if q.shape[0] != m:
        raise ValueError("settled_q length mismatch")
    fixed_mask = np.zeros(n, dtype=bool)
    for i in fixed_indices:
        if i < 0 or i >= n:
            raise ValueError("fixed index %d out of range" % i)
        fixed_mask[i] = True
    K = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(edges):
        qk = float(q[k])
        K[i, i] += qk
        K[j, j] += qk
        K[i, j] -= qk
        K[j, i] -= qk
    loads = np.zeros((n, 3), dtype=float)
    residual = K @ points - loads
    reactions = np.zeros((n, 3), dtype=float)
    for i in fixed_indices:
        reactions[i, :] = -residual[i, :] / 1000.0
    free_all = ~fixed_mask
    residual_norm = float(np.linalg.norm(residual[free_all])) if free_all.any() else 0.0
    return {
        "coordinates": points.copy(),
        "reactions": reactions,
        "residual_norm": residual_norm,
        "n_free": 0,
        "n_fixed": int(fixed_mask.sum()),
    }


# =============================================================================
# ANISOTROPIC Q
# =============================================================================

def _edge_key(a, b):
    return (a, b) if a < b else (b, a)


def assign_anisotropic_q(edges, points_2d, warp_dir, warp_q, weft_q,
                          n_boundary=None, boundary_edge_q=None,
                          boundary_edge_type=None):
    edges = list(edges)
    points_2d = np.asarray(points_2d, dtype=float)
    m = len(edges)
    q = np.zeros(m, dtype=float)
    warp_dir = np.asarray(warp_dir, dtype=float)
    wn = float(np.linalg.norm(warp_dir))
    if wn < 1e-12:
        raise ValueError("warp_dir has zero length")
    warp_dir = warp_dir / wn
    if n_boundary is None:
        n_boundary = 0

    def _is_boundary_edge(a, b):
        return (n_boundary > 0 and a < n_boundary and b < n_boundary
                and (abs(a - b) == 1 or abs(a - b) == n_boundary - 1))

    def _blend(pa, pb):
        d = pb - pa
        dn = float(np.linalg.norm(d))
        if dn < 1e-12:
            return float(warp_q)
        d = d / dn
        cos_t = float(np.dot(d, warp_dir))
        cos_t = max(-1.0, min(1.0, cos_t))
        cos2 = cos_t * cos_t
        sin2 = 1.0 - cos2
        return float(warp_q) * cos2 + float(weft_q) * sin2

    if isinstance(boundary_edge_q, dict):
        for k, (a, b) in enumerate(edges):
            if _is_boundary_edge(a, b):
                key = _edge_key(int(a), int(b))
                val = boundary_edge_q.get(key, None)
                if val is None:
                    val = boundary_edge_q.get((key[1], key[0]), None)
                q[k] = float(val) if val is not None else float(warp_q)
                continue
            q[k] = _blend(points_2d[a], points_2d[b])
        return q

    if isinstance(boundary_edge_q, np.ndarray):
        if boundary_edge_q.shape[0] != m:
            raise ValueError("boundary_edge_q array length mismatch")
        for k, (a, b) in enumerate(edges):
            if _is_boundary_edge(a, b):
                q[k] = float(boundary_edge_q[k])
                continue
            q[k] = _blend(points_2d[a], points_2d[b])
        return q

    if boundary_edge_q is None:
        boundary_edge_q_scalar = float(warp_q)
    else:
        boundary_edge_q_scalar = float(boundary_edge_q)

    for k, (a, b) in enumerate(edges):
        if _is_boundary_edge(a, b):
            if boundary_edge_type is not None and k < len(boundary_edge_type):
                if boundary_edge_type[k] == "cable":
                    q[k] = float(boundary_edge_q_scalar)
                else:
                    q[k] = float(warp_q)
            else:
                q[k] = float(warp_q)
            continue
        q[k] = _blend(points_2d[a], points_2d[b])
    return q


def auto_warp_dir(points_2d):
    pts = np.asarray(points_2d, dtype=float)
    if pts.shape[0] < 2:
        return np.array([1.0, 0.0])
    dx = float(np.max(pts[:, 0]) - np.min(pts[:, 0]))
    dy = float(np.max(pts[:, 1]) - np.min(pts[:, 1]))
    return np.array([1.0, 0.0]) if dx >= dy else np.array([0.0, 1.0])


def rotate_warp_dir(warp_dir, angle_rad):
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    w = np.asarray(warp_dir, dtype=float)
    return np.array([c * w[0] - s * w[1], s * w[0] + c * w[1]])


# =============================================================================
# PER-DOF RESIDUAL
# =============================================================================

def _dof_residual_norm(points, edges, fixed_indices, q, loads, dir_only_map):
    points = np.asarray(points, dtype=float)
    edges = list(edges)
    q = np.asarray(q, dtype=float)
    loads = np.asarray(loads, dtype=float)
    n = points.shape[0]
    fixed_mask = np.zeros(n, dtype=bool)
    for i in fixed_indices:
        fixed_mask[i] = True
    K = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(edges):
        qk = float(q[k])
        K[i, i] += qk
        K[j, j] += qk
        K[i, j] -= qk
        K[j, i] -= qk
    R = K @ points - loads
    components = []
    for i in range(n):
        if fixed_mask[i]:
            continue
        if i in dir_only_map:
            d = np.asarray(dir_only_map[i], dtype=float)
            dn = float(np.linalg.norm(d))
            if dn < 1e-12:
                continue
            d = d / dn
            components.append(float(d @ R[i]))
        else:
            components.append(float(R[i, 0]))
            components.append(float(R[i, 1]))
            components.append(float(R[i, 2]))
    if not components:
        return 0.0
    return float(np.linalg.norm(np.asarray(components)))


# =============================================================================
# TESTS
# =============================================================================

def _test_flat_mesh():
    nx = 4
    ny = 4
    points = []
    for j in range(ny):
        for i in range(nx):
            points.append((i / (nx - 1.0), j / (ny - 1.0), 0.0))
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
    xy_shift = float(np.max(np.abs(coords[:, :2] - np.asarray(points)[:, :2])))
    return {
        "residual_norm": res["residual_norm"],
        "z_max_deviation": z_max,
        "xy_max_deviation": xy_shift,
        "ok": res["residual_norm"] < 1e-9 and z_max < 1e-9 and xy_shift < 1e-9,
    }


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
            on_boundary = (i == 0 or i == nx - 1 or j == 0 or j == ny - 1)
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
        "ok": (res["residual_norm"] < 1e-9 and z_min < -1e-3
               and z_max > 1e-3 and (z_max - z_min) > 1e-2),
    }


def _test_z_only_constraint():
    points = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 1000.0, 1000.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0, loads=loads, z_only_indices=[1])
    coords = res["coordinates"]
    x_moved = abs(coords[1, 0] - 1.0)
    y_moved = abs(coords[1, 1] - 0.0)
    z_moved = abs(coords[1, 2] - 0.0)
    return {
        "residual_norm": res["residual_norm"],
        "x_moved": x_moved, "y_moved": y_moved, "z_moved": z_moved,
        "ok": x_moved < 1e-9 and y_moved < 1e-9 and z_moved > 1e-3,
    }


def _test_dir_only_basic():
    points = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 1000.0, 1000.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0, loads=loads,
                    dir_only_indices=[(1, (0.0, 1.0, 0.0))])
    coords = res["coordinates"]
    x_moved = abs(coords[1, 0] - 1.0)
    y_moved = abs(coords[1, 1] - 0.0)
    z_moved = abs(coords[1, 2] - 0.0)
    return {
        "residual_norm": res["residual_norm"],
        "x_moved": x_moved, "y_moved": y_moved, "z_moved": z_moved,
        "ok": x_moved < 1e-9 and z_moved < 1e-9 and y_moved > 1e-3,
    }


def _test_dir_only_diagonal():
    points = [(0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (2.0, 2.0, 0.0)]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    d = (1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0), 0.0)
    loads = np.array([
        [0.0, 0.0, 0.0],
        [1000.0, 0.0, 1000.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0, loads=loads,
                    dir_only_indices=[(1, d)])
    coords = res["coordinates"]
    z_moved = abs(coords[1, 2] - 0.0)
    dx = coords[1, 0] - 1.0
    dy = coords[1, 1] - 1.0
    return {
        "residual_norm": res["residual_norm"],
        "dx": dx, "dy": dy, "z_moved": z_moved,
        "ok": (z_moved < 1e-9) and abs(dx - dy) < 1e-6 and abs(dx) > 1e-4,
    }


def _test_coupled_dir_only():
    points = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (3.0, 0.0, 0.0)]
    edges = [(0, 1), (1, 2), (2, 3)]
    fixed = [0, 3]
    dir_only_list = [(1, (0.0, 1.0, 0.0)), (2, (0.0, 1.0, 0.0))]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 100.0, 50.0],
        [0.0, 100.0, -50.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0, loads=loads,
                    dir_only_indices=dir_only_list)
    coords = res["coordinates"]
    dir_only_map = {i: np.asarray(d) for (i, d) in dir_only_list}
    per_dof = _dof_residual_norm(coords, edges, fixed,
                                 np.full(len(edges), 1.0), loads, dir_only_map)
    x1 = abs(coords[1, 0] - 1.0)
    z1 = abs(coords[1, 2] - 0.0)
    x2 = abs(coords[2, 0] - 2.0)
    z2 = abs(coords[2, 2] - 0.0)
    return {
        "raw_residual": res["residual_norm"],
        "per_dof_residual": per_dof,
        "x1_moved": x1, "z1_moved": z1,
        "x2_moved": x2, "z2_moved": z2,
        "ok": (per_dof < 1e-9 and x1 < 1e-9 and z1 < 1e-9
               and x2 < 1e-9 and z2 < 1e-9),
    }


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
    res = solve_fdm(points, edges, fixed, 1.0, loads=loads,
                    dir_only_indices=dir_only_list)
    coords = res["coordinates"]
    dir_only_map = {i: np.asarray(d) for (i, d) in dir_only_list}
    per_dof = _dof_residual_norm(coords, edges, fixed,
                                 np.full(len(edges), 1.0), loads, dir_only_map)
    return {
        "raw_residual": res["residual_norm"],
        "per_dof_residual": per_dof,
        "dof_count": res["dof_count"],
        "ok": per_dof < 1e-9,
    }


def _test_smooth_cable_bow():
    n = 21
    points = [(float(i), 0.0, 0.0) for i in range(n)]
    edges = [(i, i + 1) for i in range(n - 1)]
    fixed = [0, n - 1]
    dir_only_list = [(i, (0.0, 1.0, 0.0)) for i in range(1, n - 1)]
    loads = np.zeros((n, 3))
    for i in range(1, n - 1):
        loads[i, 1] = 100.0
    res = solve_fdm(points, edges, fixed, 1.0, loads=loads,
                    dir_only_indices=dir_only_list)
    coords = res["coordinates"]
    xs = coords[:, 0]
    ys = coords[:, 1]
    zs = coords[:, 2]
    x_drift = float(np.max(np.abs(xs - np.arange(n, dtype=float))))
    z_drift = float(np.max(np.abs(zs)))
    mid = n // 2
    y_mid = float(ys[mid])
    sym_max = 0.0
    for i in range(1, n - 1):
        sym_max = max(sym_max, abs(ys[i] - ys[n - 1 - i]))
    peak_ok = all(ys[mid] >= ys[i] - 1e-12 for i in range(1, n - 1))
    dir_only_map = {i: np.asarray(d) for (i, d) in dir_only_list}
    per_dof = _dof_residual_norm(coords, edges, fixed,
                                 np.full(len(edges), 1.0), loads, dir_only_map)
    return {
        "raw_residual": res["residual_norm"],
        "per_dof_residual": per_dof,
        "x_drift": x_drift, "z_drift": z_drift,
        "y_mid": y_mid, "symmetry_max": sym_max, "peak_ok": peak_ok,
        "ok": (x_drift < 1e-9 and z_drift < 1e-9 and sym_max < 1e-9
               and peak_ok and per_dof < 1e-9),
    }


def _test_settled_match():
    points = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    q = np.array([1000.0, 1000.0])
    res1 = solve_fdm(points, edges, fixed, q)
    res2 = solve_fdm_settled(res1["coordinates"], edges, fixed, q)
    diff = float(np.max(np.abs(res1["reactions"] - res2["reactions"])))
    return {"reaction_diff": diff, "ok": diff < 1e-9}


def _test_dir_only_reactions():
    points = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
    edges = [(0, 1), (1, 2)]
    fixed = [0, 2]
    loads = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 1000.0, 1000.0],
        [0.0, 0.0, 0.0],
    ])
    res = solve_fdm(points, edges, fixed, 1.0, loads=loads,
                    dir_only_indices=[(1, (0.0, 1.0, 0.0))])
    coords = res["coordinates"]
    K = np.zeros((3, 3), dtype=float)
    for (i, j) in edges:
        K[i, i] += 1.0
        K[j, j] += 1.0
        K[i, j] -= 1.0
        K[j, i] -= 1.0
    R = K @ coords - loads
    r_along = abs(float(R[1, 1]))
    r_x = abs(float(R[1, 0]))
    r_z = abs(float(R[1, 2]))
    return {
        "residual_along_free_axis": r_along,
        "residual_perp_x": r_x,
        "residual_perp_z": r_z,
        "ok": r_along < 1e-9,
    }


# =============================================================================
# RUN
# =============================================================================

def run():
    print("=" * 60)
    print("TEST: engine/form_finding_test.py - FDM solver (self-contained)")
    print("=" * 60)

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

    overall = True

    for name, fn in tests:
        try:
            r = fn()
            ok = bool(r.get("ok", False))
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
            overall = False
            print("  %-30s FAIL" % name)
            print("      exception: %s" % str(e))

    print("-" * 60)
    print("RESULT:", "PASS" if overall else "FAIL")
    return overall


if __name__ == "__main__":
    ok = run()
    raise SystemExit(0 if ok else 1)
