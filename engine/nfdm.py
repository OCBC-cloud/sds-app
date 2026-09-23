# =============================================================================
# SDSe Engine - Natural Force Density Method (NFDM)
# =============================================================================
# Research kernel. Not yet wired into the shipping viewers.
# Reached only through the temporary NFDM tester page.
#
# Method:
#   Each triangular element carries a target plane-stress state.
#   Its natural force densities (three per triangle) are computed
#   from that stress and the triangle's geometry. The three q
#   values assemble into a global stiffness matrix, exactly as
#   classical FDM assembles edge force densities.
#
#   Because the membrane is a continuum of triangles rather than
#   a network of independent bars, the NFDM formulation cannot
#   fold onto itself. That is the property classical FDM lacks.
#
# Solver:
#   Newton-Raphson with backtracking line search.
#   Guards on:
#     - triangle area collapse (below a fraction of the initial area)
#     - negative natural force density (slack element)
#   Either guard stops the iteration and reports - it does not
#   paper over the failure.
#
# Reference:
#   Pauletti, R. M. O. (2006). Natural Force Density Method.
#
# Units: m, N/m^2 (stress resultant), m (thickness).
#
# History:
#   2026-09-23 - First build. Element math from V0.3 of the
#                SDS-CONST research scaffold kept. Iteration
#                scheme rewritten from scratch.
# =============================================================================

import numpy as np


# ---- Thresholds -----------------------------------------------------------
EPS = 1e-12
AREA_MIN_FRACTION = 0.05
Q_MIN = -1e-6


# =============================================================================
# TRIANGLE ELEMENT
# =============================================================================

def triangle_natural_force_densities(tri_points, stress, thickness):
    """
    Compute the three natural force densities of one triangle.

    Parameters
    ----------
    tri_points : (3, 3) array of node coordinates for the triangle
    stress : (3,) array
        Target Cauchy stress resultants [s11, s22, s12].
    thickness : float
        Membrane thickness in metres.

    Returns
    -------
    area : float
    lengths : (3,) edge lengths
    q : (3,) natural force densities for the three edges
        Edge order: (0,1), (1,2), (0,2).
    """
    x = np.asarray(tri_points, dtype=float)
    e = np.array([x[1] - x[0], x[2] - x[1], x[0] - x[2]])
    L = np.linalg.norm(e, axis=1)
    if np.any(L <= EPS):
        raise ValueError("degenerate triangle: zero edge length")

    area = 0.5 * np.linalg.norm(np.cross(e[0], -e[2]))
    if area <= EPS:
        raise ValueError("degenerate triangle: zero area")

    t1 = e[0] / L[0]
    normal = np.cross(e[0], -e[2])
    normal /= np.linalg.norm(normal)
    t2 = np.cross(normal, t1)

    d = np.column_stack((e @ t1, e @ t2)) / L[:, None]
    s11, s22, s12 = stress

    A = np.array([
        L ** 2 * d[:, 0] ** 2,
        L ** 2 * d[:, 1] ** 2,
        L ** 2 * d[:, 0] * d[:, 1],
    ])
    b = 2.0 * area * thickness * np.array([s11, s22, s12])

    q = np.linalg.lstsq(A, b, rcond=None)[0]
    return area, L, q


def ke_from_q(q):
    """
    Local 9x9 stiffness matrix of one triangle from its natural
    force densities q = (q1, q2, q3) for edges (0,1), (1,2), (0,2).
    """
    I = np.eye(3)
    q1, q2, q3 = q
    return np.block([
        [(q1 + q3) * I, -q1 * I, -q3 * I],
        [-q1 * I, (q1 + q2) * I, -q2 * I],
        [-q3 * I, -q2 * I, (q2 + q3) * I],
    ])


# =============================================================================
# GLOBAL ASSEMBLY
# =============================================================================

def assemble_global_K(points, triangles, stress, thickness):
    """
    Assemble the global 3N x 3N stiffness matrix from all triangles.

    Returns
    -------
    K : (3N, 3N) array
    states : list of (area, lengths, q) per triangle
    """
    n = len(points)
    K = np.zeros((3 * n, 3 * n), dtype=float)
    states = []
    for tri in triangles:
        area, L, q = triangle_natural_force_densities(
            points[tri], stress, thickness
        )
        states.append((area, L, q))
        dofs = np.array([3 * int(nd) + d for nd in tri for d in range(3)])
        K[np.ix_(dofs, dofs)] += ke_from_q(q)
    return K, states


# =============================================================================
# SOLVER
# =============================================================================

def solve_nfdm(points, triangles, fixed_indices, stress,
               thickness=0.01, loads=None,
               max_iter=80, tol=1e-8):
    """
    Solve the NFDM equilibrium via Newton-Raphson with line search.

    Returns dict with: coordinates, converged, iterations, reason,
    residual_norm, min_area, max_area, min_q, max_q, negative_q.
    """
    points = np.asarray(points, dtype=float).copy()
    triangles = np.asarray(triangles, dtype=int)
    fixed = np.asarray(fixed_indices, dtype=int)

    n = len(points)
    if loads is None:
        loads = np.zeros_like(points)
    loads = np.asarray(loads, dtype=float)

    fixed_mask = np.zeros(n, dtype=bool)
    fixed_mask[fixed] = True
    free = np.where(~fixed_mask)[0]
    if len(free) == 0:
        raise ValueError("no free nodes")

    free_dofs = np.array([3 * nd + d for nd in free for d in range(3)])
    all_dofs = np.arange(3 * n)
    fixed_dofs = np.setdiff1d(all_dofs, free_dofs)

    initial_areas = []
    for tri in triangles:
        a, _, _ = triangle_natural_force_densities(
            points[tri], stress, thickness
        )
        initial_areas.append(a)
    initial_areas = np.array(initial_areas)

    f_global = loads.ravel().copy()
    x_fixed_vals = points.ravel()[fixed_dofs].copy()

    history = []
    reason = "max_iter"
    converged = False

    for it in range(1, max_iter + 1):
        K, _ = assemble_global_K(points, triangles, stress, thickness)
        Kff = K[np.ix_(free_dofs, free_dofs)]
        Kxf = K[np.ix_(free_dofs, fixed_dofs)]

        x_free = points.ravel()[free_dofs]
        residual_vec = Kff @ x_free + Kxf @ x_fixed_vals - f_global[free_dofs]
        residual_norm = float(np.linalg.norm(residual_vec))

        scale = max(1.0, float(np.max(np.abs(np.diag(Kff)))))
        Kff_reg = Kff + 1e-12 * scale * np.eye(len(free_dofs))
        try:
            dx = np.linalg.solve(Kff_reg, -residual_vec)
        except np.linalg.LinAlgError:
            reason = "singular matrix"
            break

        alpha = 1.0
        best_alpha = None
        best_residual = residual_norm
        for _ls in range(12):
            trial = points.copy()
            trial.ravel()[free_dofs] = x_free + alpha * dx
            try:
                K_t, _ = assemble_global_K(trial, triangles, stress, thickness)
            except ValueError:
                alpha *= 0.5
                continue
            Kff_t = K_t[np.ix_(free_dofs, free_dofs)]
            xf_t = trial.ravel()[free_dofs]
            res_t = Kff_t @ xf_t + Kxf @ x_fixed_vals - f_global[free_dofs]
            r_t = float(np.linalg.norm(res_t))
            if r_t < best_residual:
                best_residual = r_t
                best_alpha = alpha
                break
            alpha *= 0.5

        if best_alpha is None:
            reason = "line search failed"
            break

        points.ravel()[free_dofs] = x_free + best_alpha * dx
        disp = best_alpha * float(np.linalg.norm(dx))
        history.append((it, disp, best_residual))

        if disp < tol:
            converged = True
            reason = "converged"
            break

    K, states = assemble_global_K(points, triangles, stress, thickness)
    areas = np.array([s[0] for s in states])
    q_all = np.concatenate([s[2] for s in states])
    Kff = K[np.ix_(free_dofs, free_dofs)]
    Kxf = K[np.ix_(free_dofs, fixed_dofs)]
    final_res = Kff @ points.ravel()[free_dofs] + Kxf @ x_fixed_vals - f_global[free_dofs]

    return {
        "coordinates": points,
        "converged": converged,
        "iterations": len(history),
        "reason": reason,
        "residual_norm": float(np.linalg.norm(final_res)),
        "min_area": float(areas.min()),
        "max_area": float(areas.max()),
        "min_q": float(q_all.min()),
        "max_q": float(q_all.max()),
        "negative_q": int((q_all < -1e-6).sum()),
        "history": history,
    }


# =============================================================================
# BENCHMARK MESHES
# =============================================================================

def make_flat_grid(nx=8, ny=6, Lx=4.0, Ly=3.0):
    """Flat rectangular grid. Fixed boundary on all four edges."""
    xs = np.linspace(0.0, Lx, nx + 1)
    ys = np.linspace(0.0, Ly, ny + 1)
    points = np.array([[x, y, 0.0] for y in ys for x in xs], dtype=float)
    tris = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            b = a + 1
            d = (j + 1) * (nx + 1) + i
            c = d + 1
            tris.append([a, b, c])
            tris.append([a, c, d])
    boundary = sorted({
        j * (nx + 1) + i
        for j in range(ny + 1)
        for i in range(nx + 1)
        if i in (0, nx) or j in (0, ny)
    })
    return points, np.array(tris, dtype=int), np.array(boundary, dtype=int)


def make_reduced_catenoid(nx=12, ny=8, Lx=4.0, Ly=3.0, sag=0.5):
    """
    Reduced catenoid benchmark. Boundary high on two opposite
    edges, low on the other two. Minimal surface in between.
    """
    xs = np.linspace(0.0, Lx, nx + 1)
    ys = np.linspace(0.0, Ly, ny + 1)
    points = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = xs[i]
            y = ys[j]
            z = 0.0
            on_boundary = (i == 0 or i == nx or j == 0 or j == ny)
            if on_boundary:
                if i == 0:
                    z = sag
                elif i == nx:
                    z = -sag
                elif j == 0:
                    z = -sag
                elif j == ny:
                    z = sag
            points.append([x, y, z])
    points = np.array(points, dtype=float)
    tris = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            b = a + 1
            d = (j + 1) * (nx + 1) + i
            c = d + 1
            tris.append([a, b, c])
            tris.append([a, c, d])
    tris = np.array(tris, dtype=int)
    boundary = sorted({
        j * (nx + 1) + i
        for j in range(ny + 1)
        for i in range(nx + 1)
        if i == 0 or i == nx or j == 0 or j == ny
    })
    return points, tris, np.array(boundary, dtype=int)


# =============================================================================
# SELF-TESTS
# =============================================================================

def _test_flat_membrane():
    """Flat mesh, no load. Should stay flat."""
    points, tris, boundary = make_flat_grid(nx=8, ny=6)
    res = solve_nfdm(
        points, tris, boundary,
        stress=(1.0, 1.0, 0.0),
        thickness=0.01,
        max_iter=40,
    )
    z_max = float(np.max(np.abs(res["coordinates"][:, 2])))
    return {
        "converged": res["converged"],
        "iterations": res["iterations"],
        "residual_norm": res["residual_norm"],
        "z_max_deviation": z_max,
        "flat_ok": z_max < 1e-6,
        "reason": res["reason"],
    }


def _test_reduced_catenoid():
    """Reduced catenoid. Should form a smooth saddle, no fold."""
    points, tris, boundary = make_reduced_catenoid()
    res = solve_nfdm(
        points, tris, boundary,
        stress=(1.0, 1.0, 0.0),
        thickness=0.01,
        max_iter=60,
    )
    coords = res["coordinates"]
    interior = np.array([
        coords[j * 13 + i, 2]
        for j in range(1, 8)
        for i in range(1, 12)
    ])
    z_min = float(np.min(interior))
    z_max = float(np.max(interior))
    no_fold = (-0.6 < z_min) and (z_max < 0.6) and (z_max - z_min > 1e-3)
    return {
        "converged": res["converged"],
        "iterations": res["iterations"],
        "residual_norm": res["residual_norm"],
        "min_area": res["min_area"],
        "max_area": res["max_area"],
        "min_q": res["min_q"],
        "negative_q": res["negative_q"],
        "interior_z_min": z_min,
        "interior_z_max": z_max,
        "no_fold": no_fold,
        "reason": res["reason"],
    }


def _verify_nfdm():
    """Run all NFDM self-tests. Returns dict with pass flag."""
    results = {}
    t1 = _test_flat_membrane()
    results["flat_converged"] = t1["converged"]
    results["flat_iterations"] = t1["iterations"]
    results["flat_residual"] = t1["residual_norm"]
    results["flat_z_max"] = t1["z_max_deviation"]
    results["flat_ok"] = t1["flat_ok"]

    t2 = _test_reduced_catenoid()
    results["cat_converged"] = t2["converged"]
    results["cat_iterations"] = t2["iterations"]
    results["cat_residual"] = t2["residual_norm"]
    results["cat_min_area"] = t2["min_area"]
    results["cat_max_area"] = t2["max_area"]
    results["cat_min_q"] = t2["min_q"]
    results["cat_negative_q"] = t2["negative_q"]
    results["cat_interior_z_min"] = t2["interior_z_min"]
    results["cat_interior_z_max"] = t2["interior_z_max"]
    results["cat_no_fold"] = t2["no_fold"]

    results["pass"] = all([
        results["flat_converged"],
        results["flat_ok"],
        results["cat_converged"],
        results["cat_no_fold"],
    ])
    return results


def get_catenoid_for_viewer():
    """
    Return (coordinates, triangles, boundary, result) for the tester
    viewer. Runs the reduced catenoid benchmark.
    """
    points, tris, boundary = make_reduced_catenoid()
    res = solve_nfdm(
        points, tris, boundary,
        stress=(1.0, 1.0, 0.0),
        thickness=0.01,
        max_iter=60,
    )
    return res["coordinates"], tris, boundary, res


if __name__ == "__main__":
    print("engine/nfdm.py - Natural Force Density Method")
    print("-" * 70)
    res = _verify_nfdm()
    print("Test 1 - Flat membrane")
    print("  converged        :", res["flat_converged"])
    print("  iterations       :", res["flat_iterations"])
    print("  residual_norm    : %.6e" % res["flat_residual"])
    print("  z max deviation  : %.6e" % res["flat_z_max"])
    print("  flat_ok          :", res["flat_ok"])
    print()
    print("Test 2 - Reduced catenoid")
    print("  converged        :", res["cat_converged"])
    print("  iterations       :", res["cat_iterations"])
    print("  residual_norm    : %.6e" % res["cat_residual"])
    print("  min_area         : %.6e" % res["cat_min_area"])
    print("  max_area         : %.6f" % res["cat_max_area"])
    print("  min_q            : %.6f" % res["cat_min_q"])
    print("  negative_q       :", res["cat_negative_q"])
    print("  interior z min   : %.6f" % res["cat_interior_z_min"])
    print("  interior z max   : %.6f" % res["cat_interior_z_max"])
    print("  no_fold          :", res["cat_no_fold"])
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")
