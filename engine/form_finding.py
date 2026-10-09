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
# Two-pass workflow:
#   Pass 1 - solve_fdm. The user's chosen pretensions are used as
#            force densities. The shape falls out. These pretensions
#            are a design lever: they manipulate the bow depth and
#            the membrane area. They are NOT the physical prestress
#            of the settled structure.
#   Pass 2 - solve_fdm_settled. The shape is now accepted. The
#            form-finding pretensions are discarded. The settled
#            force densities of the structure are used to compute
#            the real reactions.
#
# Updated 2026-10-05:
#   - assign_anisotropic_q accepts a per-edge boundary_edge_q.
#
# Updated 2026-10-07:
#   - Support reactions exposed from solve_fdm.
#   - solve_fdm_settled added.
#
# Updated 2026-10-09:
#   - solve_fdm gains a dir_only_indices argument: a list of
#     (node_index, direction_vector) pairs. For each such node,
#     motion is restricted to the given direction. The two axes
#     perpendicular to the direction are held. This is the general
#     form of the existing z_only_indices constraint, which is a
#     special case with direction = (0, 0, 1).
#   - z_only_indices is retained and works as before, for backward
#     compatibility. When both are supplied, they are merged.
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
# DIRECTIONAL CONSTRAINT HELPERS
# =============================================================================

def _orthonormal_basis(direction):
    """
    Given a unit vector d, return two unit vectors perpendicular to d
    and to each other, forming a right-handed orthonormal frame
    (d, p, q). Used to build the reduced 1-DOF basis for a node
    constrained to move along d.
    """
    d = np.asarray(direction, dtype=float)
    n = float(np.linalg.norm(d))
    if n < 1e-12:
        raise ValueError("direction vector has zero length")
    d = d / n

    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, d))) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    p = ref - float(np.dot(ref, d)) * d
    p = p / (float(np.linalg.norm(p)) + 1e-30)
    q = np.cross(d, p)
    q = q / (float(np.linalg.norm(q)) + 1e-30)
    return d, p, q


# =============================================================================
# FDM SOLVER - PASS 1 (FORM FINDING)
# =============================================================================

def solve_fdm(points, edges, fixed_indices, force_densities,
              loads=None, z_only_indices=None, dir_only_indices=None):
    """
    Solve the Force Density Method equilibrium.

    Parameters
    ----------
    points : (n, 3) array of initial coordinates
    edges : list of (i, j)
    fixed_indices : list of node indices that do not move
    force_densities : (m,) array or scalar
    loads : (n, 3) array or None
    z_only_indices : list of node indices free in Z only. X and Y
        are held. This is a special case of dir_only_indices with
        direction = (0, 0, 1).
    dir_only_indices : list of (node_index, direction_vector) pairs.
        For each such node, motion is restricted to the given
        direction. The two axes perpendicular to the direction are
        held. Used for cable interior nodes: a cable node is free
        to slide along the local cable tangent, and fixed in the
        two directions perpendicular to it. This prevents the
        membrane from pulling the boundary node inward in the plan
        plane, without preventing the node from bowing along the
        cable.

    Returns
    -------
    dict with keys: coordinates, residual_norm, n_free, n_fixed,
                    reactions
    """
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

    # ---- Directional constraints ----
    # For each (node, direction), we store the unit direction and
    # the two unit axes perpendicular to it. The node is free to
    # move along the direction and held along the two perpendicular
    # axes. A node already in z_only_mask is skipped, because the
    # two constraints are not meant to be combined on one node.
    dir_map = {}
    for entry in dir_only_indices:
        try:
            node_i, direction = entry
        except Exception:
            raise ValueError(
                "dir_only_indices entries must be (node_index, direction_vector)"
            )
        node_i = int(node_i)
        if node_i < 0 or node_i >= n:
            raise ValueError("dir_only index %d out of range" % node_i)
        if fixed_mask[node_i]:
            continue
        if z_only_mask[node_i]:
            continue
        d, p, qv = _orthonormal_basis(direction)
        dir_map[node_i] = (d, p, qv)

    K = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(edges):
        qk = q[k]
        K[i, i] += qk
        K[j, j] += qk
        K[i, j] -= qk
        K[j, i] -= qk

    X = points.copy()

    # ---- Nodes that are fully free in all three axes ----
    # A node is fully free only if it is not fixed, not z_only, and
    # not in dir_map.
    dir_only_set = set(dir_map.keys())

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

    free_xy = (~fixed_mask) & (~z_only_mask) & (~np.isin(np.arange(n), list(dir_only_set)))
    free_z = (~fixed_mask) & (~np.isin(np.arange(n), list(dir_only_set)))

    # Solve for the axis-free nodes in X, Y, Z as before.
    _solve_axis(0, free_xy)
    _solve_axis(1, free_xy)
    _solve_axis(2, free_z)

    # ---- Handle direction-only nodes ----
    # For each direction-only node, we solve a 1-DOF system along
    # the direction, then project the result back to the node's
    # coordinates. This is done after the axis solves, so the axis
    # solves use only the fully-free and z_only nodes. The
    # direction-only nodes are treated as if fixed in the axis
    # solves (because they were excluded from free_xy and free_z),
    # then resolved along their own direction.
    for node_i, (d, p, qv) in dir_map.items():
        # The node contributes one DOF along d. The equilibrium
        # equation for that DOF is:
        #     d^T K[i, i] d * alpha + d^T (sum_j K[i, j] X[j]) = d^T load[i]
        # where X[i] = alpha * d (the position is parametrised along
        # d from the origin; but the contribution from the node
        # itself must be from its own degree of freedom).
        #
        # In practice, the simplest and most robust implementation
        # is: temporarily solve the full 3-DOF system for this node
        # with the two perpendicular directions held, using the
        # current X as the fixed contribution from neighbours.

        # Build the 3x3 local block K_ii.
        K_ii = K[node_i, node_i] * np.eye(3)

        # Contribution from neighbours: for every edge (node_i, j),
        # the neighbour's current position contributes -q * X[j] to
        # the node's force balance.
        neigh_sum = np.zeros(3)
        for k, (a, b) in enumerate(edges):
            if a == node_i:
                neigh_sum -= q[k] * X[b]
            elif b == node_i:
                neigh_sum -= q[k] * X[a]

        rhs_full = loads[node_i] - neigh_sum

        # Project onto the direction d: only the component along d
        # is free.
        d_col = d.reshape(3, 1)
        # Effective scalar stiffness along d.
        k_along = float(d @ (K_ii @ d))
        if abs(k_along) < 1e-12:
            continue
        # Force along d.
        f_along = float(d @ rhs_full)
        # Displacement along d.
        alpha = f_along / k_along
        # The new position of the node: the old position plus the
        # displacement along d that satisfies equilibrium.
        #
        # But the equilibrium equation is a linear system in the
        # node's coordinates. We want the new coordinates X[i] such
        # that:
        #     K_ii @ X[i] + neigh_sum = loads[i]      (full 3-DOF)
        # restricted to the 1-DOF along d. This means:
        #     X[i] = X_old[i] + alpha * d
        # where alpha is determined by:
        #     d^T (K_ii @ (X_old[i] + alpha * d) + neigh_sum - loads[i]) = 0
        # Simplifying:
        #     d^T (K_ii @ X_old[i] + neigh_sum - loads[i]) + alpha * (d^T K_ii d) = 0
        # So:
        #     alpha = - d^T (K_ii @ X_old[i] + neigh_sum - loads[i]) / (d^T K_ii d)
        residual_d = float(d @ (K_ii @ X[node_i] + neigh_sum - loads[node_i]))
        k_along = float(d @ (K_ii @ d))
        if abs(k_along) < 1e-12:
            continue
        alpha = - residual_d / k_along
        X[node_i] = X[node_i] + alpha * d

    residual = K @ X - loads
    free_all = ~fixed_mask
    residual_norm = float(np.linalg.norm(residual[free_all]))

    reactions = np.zeros((n, 3), dtype=float)
    for i in fixed_indices:
        reactions[i, :] = -residual[i, :] / 1000.0

    n_free = int(np.sum(free_all)) - len(dir_map) * 2
    if n_free < 0:
        n_free = 0

    return {
        "coordinates": X,
        "residual_norm": residual_norm,
        "n_free": n_free,
        "n_fixed": int(fixed_mask.sum()),
        "reactions": reactions,
    }


# =============================================================================
# FDM SOLVER - PASS 2 (SETTLED STATE)
# =============================================================================

def solve_fdm_settled(settled_points, edges, fixed_indices,
                      settled_q):
    """
    Solve the settled state of an already form-found shape.

    The two-pass workflow:

        Pass 1 - solve_fdm. The user's chosen pretensions are used
                 as force densities. The shape falls out.
        Pass 2 - solve_fdm_settled. The shape is accepted. The
                 settled force densities are used to compute the
                 real reactions of the settled structure.

    The shape does not move. The function computes the force
    balance at every node; at fixed nodes that balance is the
    reaction.

    Parameters
    ----------
    settled_points : (n, 3) array of settled coordinates
    edges : list of (i, j)
    fixed_indices : list of fixed node indices
    settled_q : (m,) array of settled force densities, N/m

    Returns
    -------
    dict with keys: coordinates, reactions, residual_norm,
                    n_free, n_fixed
    """
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
        raise ValueError(
            "settled_q length %d does not match edges %d"
            % (q.shape[0], m)
        )

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
    residual_norm = float(np.linalg.norm(residual[free_all])) \
        if free_all.any() else 0.0

    return {
        "coordinates": points.copy(),
        "reactions": reactions,
        "residual_norm": residual_norm,
        "n_free": 0,
        "n_fixed": int(fixed_mask.sum()),
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
                    val = boundary_edge_q.get((key[1], key[0]), None)
                if val is not None:
                    q[k] = float(val)
                    continue
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

    # --- Case 3: scalar boundary_edge_q.
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


def _test_dir_only_constraint():
    """
    A middle node constrained to move along the Y axis only.
    Loaded along Y and Z. It should move in Y, not in X, not in Z.
    """
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

    constraint_ok = (
        x_moved < 1e-9
        and z_moved < 1e-9
        and y_moved > 1e-3
    )

    return {
        "residual_norm": res["residual_norm"],
        "x_moved": x_moved,
        "y_moved": y_moved,
        "z_moved": z_moved,
        "dir_only_ok": constraint_ok,
    }


def _test_dir_only_diagonal():
    """
    A middle node constrained to move along the X-Y diagonal.
    Loaded along X and Z. It should move in X (and Y), not in Z.
    """
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
    # The X-Y displacement should lie along the diagonal direction.
    dx = coords[1, 0] - 1.0
    dy = coords[1, 1] - 1.0
    along_ok = abs(dx - dy) < 1e-6
    moved = abs(dx) > 1e-4

    constraint_ok = (z_moved < 1e-9) and along_ok and moved

    return {
        "residual_norm": res["residual_norm"],
        "dx": dx,
        "dy": dy,
        "z_moved": z_moved,
        "dir_diagonal_ok": constraint_ok,
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


def _test_settled_matches_pass1_when_q_unchanged():
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
    ok = diff < 1e-9

    return {"ok": ok, "diff": diff}


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

    t3b = _test_dir_only_constraint()
    results["dir_only_residual"] = t3b["residual_norm"]
    results["dir_only_x_moved"] = t3b["x_moved"]
    results["dir_only_y_moved"] = t3b["y_moved"]
    results["dir_only_z_moved"] = t3b["z_moved"]
    results["dir_only_ok"] = t3b["dir_only_ok"]

    t3c = _test_dir_only_diagonal()
    results["dir_diag_residual"] = t3c["residual_norm"]
    results["dir_diag_dx"] = t3c["dx"]
    results["dir_diag_dy"] = t3c["dy"]
    results["dir_diag_z_moved"] = t3c["z_moved"]
    results["dir_diag_ok"] = t3c["dir_diagonal_ok"]

    t4 = _test_mesh_size_for_shape()
    results["mesh_rect_near_25"] = t4["rect_near_25"]
    results["mesh_rect_near_28"] = t4["rect_near_28"]
    results["mesh_rect_near_50"] = t4["rect_near_50"]
    results["mesh_rect_none"] = t4["rect_none"]
    results["mesh_tri_near_22"] = t4["tri_near_22"]
    results["mesh_rule_ok"] = t4["mesh_rule_ok"]

    t5 = _test_settled_matches_pass1_when_q_unchanged()
    results["settled_match_ok"] = t5["ok"]
    results["settled_match_diff"] = t5["diff"]

    results["pass"] = all([
        results["flat_converged"],
        results["flat_ok"],
        results["saddle_converged"],
        results["saddle_ok"],
        results["z_only_ok"],
        results["dir_only_ok"],
        results["dir_diag_ok"],
        results["mesh_rule_ok"],
        results["settled_match_ok"],
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
    print("Test 3b - dir_only constraint (Y axis)")
    print("  residual_norm    : %.6e" % res["dir_only_residual"])
    print("  x moved          : %.6e" % res["dir_only_x_moved"])
    print("  y moved          : %.6f" % res["dir_only_y_moved"])
    print("  z moved          : %.6e" % res["dir_only_z_moved"])
    print("  dir_only_ok      :", res["dir_only_ok"])
    print()
    print("Test 3c - dir_only constraint (X-Y diagonal)")
    print("  residual_norm    : %.6e" % res["dir_diag_residual"])
    print("  dx               : %.6f" % res["dir_diag_dx"])
    print("  dy               : %.6f" % res["dir_diag_dy"])
    print("  z moved          : %.6e" % res["dir_diag_z_moved"])
    print("  dir_diag_ok      :", res["dir_diag_ok"])
    print()
    print("Test 4 - Mesh divisibility rule")
    print("  rect near 25 m   :", res["mesh_rect_near_25"])
    print("  rect near 28 m   :", res["mesh_rect_near_28"])
    print("  rect near 50 m   :", res["mesh_rect_near_50"])
    print("  rect span None   :", res["mesh_rect_none"])
    print("  tri  near 22 m   :", res["mesh_tri_near_22"])
    print("  mesh_rule_ok     :", res["mesh_rule_ok"])
    print()
    print("Test 5 - Settled solve matches pass 1 when q unchanged")
    print("  settled_match_ok :", res["settled_match_ok"])
    print("  max reaction diff: %.6e" % res["settled_match_diff"])
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")


# =============================================================================
# END OF engine/form_finding.py
# =============================================================================
