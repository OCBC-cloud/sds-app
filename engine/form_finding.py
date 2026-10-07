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
# Updated 2026-10-05:
#   - assign_anisotropic_q accepts a per-edge boundary_edge_q.
#     A dict keyed by (i, j) edge pairs (or a scalar). This
#     allows the pull-back function to feed per-edge force
#     densities on the boundary. The pull-back is computed
#     from the membrane stress at the form-found shape.
#
# Reference:
#   Schek, H.-J. (1974). The force density method for form-finding
#   and computation of general networks.
#
# Units: m, N, N/m.
# =============================================================================

import math

import numpy as np


# =============================================================================
# MESH SIZE RULE
# =============================================================================

MESH_MIN = 21
MESH_MAX = 101


def mesh_size_for_shape(span_m, n_sides, n_corners):
    """Return the recommended mesh size along the span, in nodes."""
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
    """Backward-compatible wrapper. Rectangular shapes only (N=4, C=4)."""
    return mesh_size_for_shape(span_m, 4, 4)


# =============================================================================
# FDM SOLVER
# =============================================================================

def solve_fdm(points, edges, fixed_indices, force_densities,
              loads=None, z_only_indices=None):
    """Solve the Force Density Method equilibrium."""
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

    q_min = float(np.min(q))
    if q_min <= 0.0:
        raise ValueError(
            "force_densities must be > 0 (min value %g)"
            % q_min
        )

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

    z_only_mask = np.zeros(n, dtype=bool)
    for i in z_only_indices:
        if i < 0 or i >= n:
            raise ValueError("z_only index %d out of range" % i)
        if fixed_mask[i]:
            continue
        z_only_mask[i] = True

    K = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(edges):
        qk = q[k]
        K[i, i] += qk
        K[j, j] += qk
        K[i, j] -= qk
        K[j, i] -= qk

    X = points.copy()

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

    free_xy = (~fixed_mask) & (~z_only_mask)
    _solve_axis(0, free_xy)
    _solve_axis(1, free_xy)

    free_z = (~fixed_mask)
    _solve_axis(2, free_z)

    residual = K @ X - loads
    free_all = ~fixed_mask
    residual_norm = float(np.linalg.norm(residual[free_all]))

    # -------------------------------------------------------------------------
    # Support reactions.
    # The residual at a fixed node is the net force the structure applies
    # to the support. The reaction is the force the support applies back,
    # so it is the negative of that residual.
    #
    # Units: the K matrix uses force density q in N/m and coordinates in
    # metres, so K @ X is in newtons. Divide by 1000 to return kilo-newtons,
    # matching the "_kN" field names every consumer uses.
    #
    # Sign convention: uplift is positive Z, downforce is negative Z.
    # -------------------------------------------------------------------------
    reactions = np.zeros((n, 3), dtype=float)
    for i in fixed_indices:
        reactions[i, :] = -residual[i, :] / 1000.0

    return {
        "coordinates": X,
        "residual_norm": residual_norm,
        "n_free": int(free_all.sum()),
        "n_fixed": int(fixed_mask.sum()),
        "reactions": reactions,
    }


# =============================================================================
# ANISOTROPIC FORCE DENSITIES
# =============================================================================

def _edge_key(a, b):
    """Return a canonical key for an undirected edge."""
    return (a, b) if a < b else (b, a)


def assign_anisotropic_q(
    edges,
    points_2d,
    warp_dir,
    warp_q,
    weft_q,
    n_boundary=None,
    boundary_edge_q=None,
    boundary_edge_type=None,
):
    """
    Build a per-edge force density array.

    Interior edges use the anisotropic fabric blend.
    Boundary edges use either a uniform value, or a
    per-edge dict of values.

    Parameters
    ----------
    edges : list of (i, j)
    points_2d : (n, 2) array
    warp_dir : (2,) unit vector
    warp_q, weft_q : float
    n_boundary : int or None
    boundary_edge_q : float or dict
        If scalar, all boundary edges use this value.
        If dict, keyed by (i, j) in sorted order.
        Missing keys fall back to warp_q.
        Can be a numpy array of length len(edges).
    boundary_edge_type : list of str or None
        One per edge, giving "beam", "cable", "wall".
        Used only if boundary_edge_q is scalar.

    Returns
    -------
    q : (m,) array
    """
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

    # --- Case 1: boundary_edge_q is a dict keyed by edge pairs.
    if isinstance(boundary_edge_q, dict):
        for k, (a, b) in enumerate(edges):
            is_boundary_edge = (
                n_boundary > 0
                and a < n_boundary
                and b < n_boundary
                and (abs(a - b) == 1 or abs(a - b) == n_boundary - 1)
            )
            if is_boundary_edge:
                key = _edge_key(int(a), int(b))
                val = boundary_edge_q.get(key, None)
                if val is None:
                    # Try reversed key (defensive)
                    val = boundary_edge_q.get((key[1], key[0]), None)
                if val is not None:
                    q[k] = float(val)
                    continue
                q[k] = float(warp_q)
                continue
            # Interior edge: anisotropic blend.
            pa = points_2d[a]
            pb = points_2d[b]
            d = pb - pa
            dn = float(np.linalg.norm(d))
            if dn < 1e-12:
                q[k] = float(warp_q)
                continue
            d = d / dn
            cos_t = float(np.dot(d, warp_dir))
            if cos_t > 1.0:
                cos_t = 1.0
            elif cos_t < -1.0:
                cos_t = -1.0
            cos2 = cos_t * cos_t
            sin2 = 1.0 - cos2
            q[k] = float(warp_q) * cos2 + float(weft_q) * sin2
        return q

    # --- Case 2: boundary_edge_q is an array.
    if isinstance(boundary_edge_q, np.ndarray):
        if boundary_edge_q.shape[0] != m:
            raise ValueError(
                "boundary_edge_q array length %d does not match edges %d"
                % (boundary_edge_q.shape[0], m)
            )
        for k, (a, b) in enumerate(edges):
            is_boundary_edge = (
                n_boundary > 0
                and a < n_boundary
                and b < n_boundary
                and (abs(a - b) == 1 or abs(a - b) == n_boundary - 1)
            )
            if is_boundary_edge:
                q[k] = float(boundary_edge_q[k])
                continue
            pa = points_2d[a]
            pb = points_2d[b]
            d = pb - pa
            dn = float(np.linalg.norm(d))
            if dn < 1e-12:
                q[k] = float(warp_q)
                continue
            d = d / dn
            cos_t = float(np.dot(d, warp_dir))
            if cos_t > 1.0:
                cos_t = 1.0
            elif cos_t < -1.0:
                cos_t = -1.0
            cos2 = cos_t * cos_t
            sin2 = 1.0 - cos2
            q[k] = float(warp_q) * cos2 + float(weft_q) * sin2
        return q

    # --- Case 3: scalar boundary_edge_q. Original behaviour.
    if boundary_edge_q is None:
        boundary_edge_q_scalar = float(warp_q)
    else:
        boundary_edge_q_scalar = float(boundary_edge_q)

    for k, (a, b) in enumerate(edges):
        is_boundary_edge = (
            n_boundary > 0
            and a < n_boundary
            and b < n_boundary
            and (abs(a - b) == 1 or abs(a - b) == n_boundary - 1)
        )
        if is_boundary_edge:
            if boundary_edge_type is not None and k < len(boundary_edge_type):
                seg_type = boundary_edge_type[k]
                if seg_type == "cable":
                    q[k] = float(boundary_edge_q_scalar)
                else:
                    q[k] = float(warp_q)
            else:
                q[k] = float(warp_q)
            continue
        pa = points_2d[a]
        pb = points_2d[b]
        d = pb - pa
        dn = float(np.linalg.norm(d))
        if dn < 1e-12:
            q[k] = float(warp_q)
            continue
        d = d / dn
        cos_t = float(np.dot(d, warp_dir))
        if cos_t > 1.0:
            cos_t = 1.0
        elif cos_t < -1.0:
            cos_t = -1.0
        cos2 = cos_t * cos_t
        sin2 = 1.0 - cos2
        q[k] = float(warp_q) * cos2 + float(weft_q) * sin2

    return q


def auto_warp_dir(points_2d):
    """Return the long axis of the plan bounding box."""
    pts = np.asarray(points_2d, dtype=float)
    if pts.shape[0] < 2:
        return np.array([1.0, 0.0])
    xmin = float(np.min(pts[:, 0]))
    xmax = float(np.max(pts[:, 0]))
    ymin = float(np.min(pts[:, 1]))
    ymax = float(np.max(pts[:, 1]))
    dx = xmax - xmin
    dy = ymax - ymin
    if dx >= dy:
        return np.array([1.0, 0.0])
    return np.array([0.0, 1.0])


def rotate_warp_dir(warp_dir, angle_rad):
    """Return a rotated unit vector."""
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    w = np.asarray(warp_dir, dtype=float)
    return np.array([c * w[0] - s * w[1], s * w[0] + c * w[1]])


# =============================================================================
# SELF-TESTS
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

    constraint_ok = (
        x_moved < 1e-9
        and y_moved < 1e-9
        and z_moved > 1e-3
    )

    return {
        "residual_norm": res["residual_norm"],
        "x_moved": x_moved,
        "y_moved": y_moved,
        "z_moved": z_moved,
        "z_only_ok": constraint_ok,
    }


def _test_mesh_size_for_shape():
    r1 = mesh_size_for_shape(25.0, 4, 4)
    r2 = mesh_size_for_shape(28.0, 4, 4)
    r3 = mesh_size_for_shape(50.0, 4, 4)
    r4 = mesh_size_for_shape(None, 4, 4)
    t1 = mesh_size_for_shape(22.0, 3, 3)

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
    results["z_only_residual"] = t3["residual_norm"]
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
    print("  residual_norm    : %.6e  (info only)" % res["z_only_residual"])
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
