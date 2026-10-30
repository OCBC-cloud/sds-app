# =============================================================================
# SDSe Engine - Nonlinear Membrane + Cable Equilibrium (v5.5 - Integrated)
# =============================================================================

import math
import time

import numpy as np

try:
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    _HAS_SCIPY_SPARSE = True
except Exception:
    _HAS_SCIPY_SPARSE = False


MEMBRANE_NU_DEFAULT = 0.34
MEMBRANE_G_MPa_DEFAULT = 50.0

DEFAULT_MAX_ITER = 300
DEFAULT_MAX_OUTER = 25
DEFAULT_TOL = 1.0e-6
DEFAULT_TOL_DISP = 1.0e-8
DEFAULT_LINE_SEARCH_STEPS = 24
DEFAULT_MAX_TOTAL_STEPS = 5000
DEFAULT_MAX_WALL_SECONDS = 120.0
ARMIJO_C1 = 1.0e-4

EPS = 1e-12


def plane_stress_matrix(E1, E2, nu12, G12):
    nu21 = nu12 * E2 / E1
    denom = 1.0 - nu12 * nu21
    if abs(denom) < EPS:
        raise ValueError("Orthotropic matrix is singular")
    return np.array([
        [E1 / denom, nu12 * E2 / denom, 0.0],
        [nu12 * E2 / denom, E2 / denom, 0.0],
        [0.0, 0.0, G12],
    ], dtype=float)


def make_membrane_material(E_warp_MPa, E_weft_MPa, thickness_mm,
                           nu=0.34, G_MPa=50.0,
                           warp_prestress_N_per_m=0.0,
                           weft_prestress_N_per_m=0.0):
    E1 = float(E_warp_MPa) * 1e6
    E2 = float(E_weft_MPa) * 1e6
    G12 = float(G_MPa) * 1e6
    t = float(thickness_mm) / 1000.0
    C = plane_stress_matrix(E1, E2, float(nu), G12)
    N_warp = float(warp_prestress_N_per_m)
    N_weft = float(weft_prestress_N_per_m)
    N_vec = np.array([N_warp, N_weft, 0.0], dtype=float)
    try:
        eps_ref_vec = np.linalg.solve(C, N_vec) / t
    except np.linalg.LinAlgError:
        eps_ref_vec = np.zeros(3)
    E_ref_2x2 = np.array([
        [eps_ref_vec[0], 0.5 * eps_ref_vec[2]],
        [0.5 * eps_ref_vec[2], eps_ref_vec[1]],
    ], dtype=float)
    return {
        "E_warp_Pa": E1, "E_weft_Pa": E2, "G_Pa": G12,
        "nu": float(nu), "thickness_m": t, "C_plane": C,
        "warp_prestress_N_per_m": N_warp, "weft_prestress_N_per_m": N_weft,
        "E_ref_2x2": E_ref_2x2,
    }


def make_cable_material(A_mm2, E_MPa, prestress_kN):
    A = float(A_mm2) * 1e-6
    E = float(E_MPa) * 1e6
    return {"A_m2": A, "E_Pa": E, "EA_N": A * E, "T_pretension_N": float(prestress_kN) * 1000.0}


def _triangle_basis(p0, p1, p2):
    e1 = p1 - p0
    e2 = p2 - p0
    n = np.cross(e1, e2)
    nn = float(np.linalg.norm(n))
    if nn < EPS:
        raise ValueError("Degenerate triangle")
    normal = n / nn
    t1 = e1
    n1 = float(np.linalg.norm(t1))
    if n1 < EPS:
        t1 = e2
        n1 = float(np.linalg.norm(t1))
        if n1 < EPS:
            raise ValueError("Degenerate triangle")
    t1 = t1 / n1
    t2 = np.cross(normal, t1)
    t2 = t2 / (np.linalg.norm(t2) + EPS)
    return t1, t2, normal


def _strain_vector_from_ref(p0, p1, p2, P0, P1, P2, t1, t2):
    def comp(v):
        return np.array([float(np.dot(v, t1)), float(np.dot(v, t2))])
    c1 = comp(p1 - p0); c2 = comp(p2 - p0)
    r1 = comp(P1 - P0); r2 = comp(P2 - P0)
    d1 = c1 - r1; d2 = c2 - r2
    E11 = 0.5 * (d1[0] * d1[0] + d2[0] * d2[0] + 2.0 * (r1[0] * d1[0] + r2[0] * d2[0]))
    E22 = 0.5 * (d1[1] * d1[1] + d2[1] * d2[1] + 2.0 * (r1[1] * d1[1] + r2[1] * d2[1]))
    E12 = 0.5 * (d1[0] * d1[1] + d2[0] * d2[1]
                 + r1[0] * d1[1] + d1[0] * r1[1]
                 + r2[0] * d2[1] + d2[0] * r2[1])
    return np.array([E11, E22, 2.0 * E12], dtype=float)


def _principal_project(s11, s22, s12):
    sigma = np.array([[s11, s12], [s12, s22]], dtype=float)
    vals, vecs = np.linalg.eigh(0.5 * (sigma + sigma.T))
    comp = bool(np.any(vals < -1e-9))
    proj = np.maximum(vals, 0.0)
    sigma_p = vecs @ np.diag(proj) @ vecs.T
    sigma_p = 0.5 * (sigma_p + sigma_p.T)
    return float(sigma_p[0, 0]), float(sigma_p[1, 1]), float(sigma_p[0, 1]), comp


def membrane_stress(p0, p1, p2, P0, P1, P2, material):
    C_plane = material["C_plane"]
    thickness = material["thickness_m"]
    N_warp = float(material.get("warp_prestress_N_per_m", 0.0))
    N_weft = float(material.get("weft_prestress_N_per_m", 0.0))
    t1, t2, _ = _triangle_basis(p0, p1, p2)
    eps_vec = _strain_vector_from_ref(p0, p1, p2, P0, P1, P2, t1, t2)
    stress = C_plane @ eps_vec
    s11 = float(stress[0]) * thickness + N_warp
    s22 = float(stress[1]) * thickness + N_weft
    s12 = float(stress[2]) * thickness
    s11p, s22p, s12p, comp = _principal_project(s11, s22, s12)
    sigma_p = np.array([[s11p, s12p], [s12p, s22p]], dtype=float)
    vals_p, _ = np.linalg.eigh(sigma_p)
    return sigma_p, comp, vals_p


def _membrane_internal_force(p0, p1, p2, P0, P1, P2, material):
    sigma, _c, _s = membrane_stress(p0, p1, p2, P0, P1, P2, material)
    t1, t2, _n = _triangle_basis(p0, p1, p2)
    def plane(v):
        return np.array([float(np.dot(v, t1)), float(np.dot(v, t2))])
    e01 = p1 - p0; e12 = p2 - p1; e20 = p0 - p2
    def outward(edge2d):
        n = np.array([edge2d[1], -edge2d[0]], dtype=float)
        nn = float(np.linalg.norm(n))
        return np.zeros(2) if nn < EPS else n / nn
    forces = []
    for e2d, e3d in ((plane(e01), e01), (plane(e12), e12), (plane(e20), e20)):
        n2d = outward(e2d)
        trac = sigma @ n2d
        ln = float(np.linalg.norm(e3d))
        f2 = trac * ln
        f3 = f2[0] * t1 + f2[1] * t2
        forces.append(f3)
    fe01, fe12, fe20 = forces
    f0 = (1.0 / 3.0) * (fe20 - fe01)
    f1 = (1.0 / 3.0) * (fe01 - fe12)
    f2 = (1.0 / 3.0) * (fe12 - fe20)
    return -f0, -f1, -f2


def _membrane_local_stiffness_3node(p0, p1, p2, P0, P1, P2, material):
    C_plane = material["C_plane"]
    thickness = material["thickness_m"]
    t1, t2, _n = _triangle_basis(p0, p1, p2)
    def plane(v):
        return np.array([float(np.dot(v, t1)), float(np.dot(v, t2))], dtype=float)
    e1 = plane(p1 - p0); e2 = plane(p2 - p0)
    x1, y1 = e1[0], e1[1]; x2, y2 = e2[0], e2[1]
    two_A = x1 * y2 - x2 * y1
    area = 0.5 * abs(two_A)
    if area < EPS:
        return np.eye(9)
    sign = 1.0 if two_A > 0.0 else -1.0
    inv_2A = sign / two_A if abs(two_A) > EPS else 0.0
    B = np.zeros((3, 6), dtype=float)
    B[0, 0] = y1 - y2; B[0, 2] = y2; B[0, 4] = -y1
    B[1, 1] = x2 - x1; B[1, 3] = -x2; B[1, 5] = x1
    B[2, 0] = x2 - x1; B[2, 1] = y1 - y2; B[2, 2] = -x2
    B[2, 3] = y2; B[2, 4] = x1; B[2, 5] = -y1
    B = B * inv_2A
    K_mat = thickness * area * (B.T @ C_plane @ B)
    sigma_total, _comp, _sp = membrane_stress(p0, p1, p2, P0, P1, P2, material)
    dN = np.zeros((3, 2), dtype=float)
    dN[0, 0] = (y1 - y2) * inv_2A; dN[0, 1] = (x2 - x1) * inv_2A
    dN[1, 0] = (-y2) * inv_2A; dN[1, 1] = (x2) * inv_2A
    dN[2, 0] = (y1) * inv_2A; dN[2, 1] = (-x1) * inv_2A
    K_geo = np.zeros((6, 6), dtype=float)
    for i in range(3):
        for j in range(3):
            gx_i, gy_i = dN[i, 0], dN[i, 1]
            gx_j, gy_j = dN[j, 0], dN[j, 1]
            kxx = area * (gx_i * gx_j * sigma_total[0, 0]
                          + gy_i * gy_j * sigma_total[1, 1]
                          + (gx_i * gy_j + gy_i * gx_j) * sigma_total[0, 1])
            K_geo[2 * i, 2 * j] += kxx
            K_geo[2 * i + 1, 2 * j + 1] += kxx
    K_2d = K_mat + K_geo
    K_local = np.zeros((9, 9), dtype=float)
    for i in range(3):
        for j in range(3):
            for a in range(2):
                for b in range(2):
                    K_local[3 * i + a, 3 * j + b] += K_2d[2 * i + a, 2 * j + b]
    return K_local


def cable_state(p_a, p_b, L0, EA):
    d = p_b - p_a
    L = float(np.linalg.norm(d))
    if L < EPS or L0 < EPS:
        return 0.0, False, 0.0, np.zeros(3)
    u = d / L
    strain = (L - L0) / L0
    if strain <= 0.0:
        return 0.0, False, 0.0, u
    T = EA * strain
    return float(T), True, float(EA / L0), u


def _cable_stiffness(p_a, p_b, L0, EA):
    d = p_b - p_a
    L = float(np.linalg.norm(d))
    if L < EPS or L0 < EPS:
        return np.zeros((3, 3)), False
    u = d / L
    strain = (L - L0) / L0
    if strain <= 0.0:
        return np.zeros((3, 3)), False
    T = EA * strain
    k_axial = EA / L0
    I3 = np.eye(3)
    uu = np.outer(u, u)
    return (-k_axial * uu - (T / L) * (I3 - uu)), True


def _assemble_residual(points, triangles, cables, ref_points,
                        material, loads, free_mask, n_nodes, taut_flags):
    F = np.zeros((n_nodes, 3), dtype=float)
    for (a, b, c) in triangles:
        try:
            f0, f1, f2 = _membrane_internal_force(
                points[a], points[b], points[c],
                ref_points[a], ref_points[b], ref_points[c], material)
        except ValueError:
            continue
        F[a] += f0; F[b] += f1; F[c] += f2
    for k, cb in enumerate(cables):
        a = int(cb["a"]); b = int(cb["b"])
        T, taut, _k_ax, u = cable_state(points[a], points[b], float(cb["L0"]), float(cb["EA"]))
        taut_flags[k] = taut
        if taut:
            F[a] += T * u
            F[b] -= T * u
    R = F + loads
    R[~free_mask] = 0.0
    return R


def _assemble_tangent_sparse(points, triangles, cables, ref_points,
                              material, free_mask, n_nodes, taut_flags):
    n_free = 3 * int(free_mask.sum())
    free_idx = np.where(free_mask)[0]
    dof_of_node = -np.ones(n_nodes, dtype=int)
    for pos, nd in enumerate(free_idx):
        dof_of_node[nd] = pos
    rows = []; cols = []; data = []
    for (a, b, c) in triangles:
        try:
            area = 0.5 * float(np.linalg.norm(np.cross(points[b] - points[a], points[c] - points[a])))
        except Exception:
            continue
        if area < EPS:
            continue
        Kloc = _membrane_local_stiffness_3node(
            points[a], points[b], points[c], ref_points[a], ref_points[b], ref_points[c], material)
        t1, t2, nrm = _triangle_basis(points[a], points[b], points[c])
        Kloc_global = np.zeros((9, 9), dtype=float)
        for node_i in range(3):
            for gi in range(3):
                for node_j in range(3):
                    for gj in range(3):
                        s = 0.0
                        for loc_i in range(3):
                            for loc_j in range(3):
                                basis_i = [t1, t2, nrm][loc_i]
                                basis_j = [t1, t2, nrm][loc_j]
                                s += (Kloc[3 * node_i + loc_i, 3 * node_j + loc_j]
                                      * basis_i[gi] * basis_j[gj])
                        Kloc_global[3 * node_i + gi, 3 * node_j + gj] = s
        nds = [a, b, c]; dofs = []
        for nd in nds:
            if free_mask[nd]:
                base = dof_of_node[nd] * 3
                dofs.extend([base, base + 1, base + 2])
            else:
                dofs.extend([-1, -1, -1])
        for i_loc in range(9):
            gi = dofs[i_loc]
            if gi < 0:
                continue
            for j_loc in range(9):
                gj = dofs[j_loc]
                if gj < 0:
                    continue
                v = Kloc_global[i_loc, j_loc]
                if v != 0.0:
                    rows.append(gi); cols.append(gj); data.append(v)
    for k, cb in enumerate(cables):
        if not taut_flags[k]:
            continue
        a = int(cb["a"]); b = int(cb["b"])
        Kblk, ok = _cable_stiffness(points[a], points[b], float(cb["L0"]), float(cb["EA"]))
        if not ok:
            continue
        da = dof_of_node[a] * 3 if free_mask[a] else -1
        db = dof_of_node[b] * 3 if free_mask[b] else -1
        if da < 0 and db < 0:
            continue
        for i_ax in range(3):
            for j_ax in range(3):
                v = Kblk[i_ax, j_ax]
                if v == 0.0:
                    continue
                for (gi_base, gj_base, sign) in [(da, da, 1), (db, db, 1), (da, db, -1), (db, da, -1)]:
                    gi = (gi_base + i_ax) if gi_base >= 0 else -1
                    gj = (gj_base + j_ax) if gj_base >= 0 else -1
                    if gi >= 0 and gj >= 0:
                        rows.append(gi); cols.append(gj); data.append(sign * v)
    if _HAS_SCIPY_SPARSE:
        K = sp.coo_matrix(
            (np.asarray(data, dtype=float),
             (np.asarray(rows, dtype=int), np.asarray(cols, dtype=int))),
            shape=(n_free, n_free)).tocsr()
        K.sum_duplicates()
        return K
    else:
        Kdense = np.zeros((n_free, n_free), dtype=float)
        for r, c, v in zip(rows, cols, data):
            Kdense[r, c] += v
        return Kdense


def _solve_linear_system(K, r_flat, n_dof):
    rhs = -r_flat
    if _HAS_SCIPY_SPARSE and sp.issparse(K):
        try:
            dx = spla.spsolve(K.tocsc(), rhs)
            if np.all(np.isfinite(dx)):
                return dx
        except Exception:
            pass
        scale = max(1.0, float(np.max(np.abs(K.data))) if K.nnz > 0 else 1.0)
        K_reg = K + 1e-9 * scale * sp.identity(n_dof, format="csr")
        try:
            dx = spla.spsolve(K_reg.tocsc(), rhs)
            if np.all(np.isfinite(dx)):
                return dx
        except Exception:
            pass
        return np.zeros(n_dof)
    else:
        try:
            return np.linalg.solve(K, rhs)
        except np.linalg.LinAlgError:
            scale = max(1.0, float(np.max(np.abs(np.diag(K)))) if n_dof > 0 else 1.0)
            K_reg = K + 1e-9 * scale * np.eye(n_dof)
            try:
                return np.linalg.solve(K_reg, rhs)
            except np.linalg.LinAlgError:
                return np.zeros(n_dof)


def _apply_z_seed(points, amplitude, fixed_mask):
    if amplitude <= 0.0 or points.shape[0] == 0:
        return points, 0.0
    free = ~fixed_mask
    if not np.any(free):
        return points, 0.0
    xs = points[free, 0]; ys = points[free, 1]
    x_min, x_max = float(np.min(xs)), float(np.max(xs))
    y_min, y_max = float(np.min(ys)), float(np.max(ys))
    x_span = max(x_max - x_min, EPS); y_span = max(y_max - y_min, EPS)
    u = (points[free, 0] - x_min) / x_span
    v = (points[free, 1] - y_min) / y_span
    bump = np.sin(np.pi * u) * np.sin(np.pi * v)
    pts = points.copy()
    pts[free, 2] += float(amplitude) * bump
    return pts, float(amplitude)


def solve_nonlinear_equilibrium(
    points, triangles, fixed_indices, reference_points,
    membrane_material, cables=None, loads=None,
    max_iter=DEFAULT_MAX_ITER, max_outer=DEFAULT_MAX_OUTER,
    tol=DEFAULT_TOL, tol_disp=DEFAULT_TOL_DISP,
    max_total_steps=DEFAULT_MAX_TOTAL_STEPS,
    max_wall_seconds=DEFAULT_MAX_WALL_SECONDS,
    seed_z_amplitude=0.0,
):
    t_start = time.time()
    points = np.asarray(points, dtype=float).copy()
    ref_points = np.asarray(reference_points, dtype=float).copy()
    triangles = list(triangles)
    n_nodes = points.shape[0]

    if loads is None:
        loads = np.zeros((n_nodes, 3), dtype=float)
    else:
        loads = np.asarray(loads, dtype=float)
        if loads.shape != (n_nodes, 3):
            raise ValueError("loads must have shape (n, 3)")

    fixed_mask = np.zeros(n_nodes, dtype=bool)
    for i in fixed_indices:
        if i < 0 or i >= n_nodes:
            raise ValueError("fixed index out of range")
        fixed_mask[i] = True

    connected = np.zeros(n_nodes, dtype=bool)
    for (a, b, c) in triangles:
        connected[a] = True; connected[b] = True; connected[c] = True
    isolated = ~connected & ~fixed_mask
    if np.sum(isolated) > 0:
        fixed_mask[isolated] = True

    free_mask = ~fixed_mask
    if free_mask.sum() == 0:
        raise ValueError("no free nodes")

    seed_applied = 0.0
    if seed_z_amplitude and float(seed_z_amplitude) > 0.0:
        points, seed_applied = _apply_z_seed(points, float(seed_z_amplitude), fixed_mask)

    cables = list(cables or [])
    for cb in cables:
        if "L0" not in cb and "T_pretension_N" in cb:
            ref_len = float(np.linalg.norm(ref_points[int(cb["b"])] - ref_points[int(cb["a"])]))
            T_pre = float(cb["T_pretension_N"]); EA = float(cb["EA"])
            cb["L0"] = ref_len if EA <= 0 else ref_len / (1.0 + T_pre / EA)

    free_idx = np.where(free_mask)[0]
    free_dofs = np.array([3 * int(i) + d for i in free_idx for d in range(3)], dtype=int)
    n_dof = len(free_dofs)

    def flat(vec3):
        return vec3.ravel()[free_dofs]

    def unflat(v):
        p = points.copy()
        p.ravel()[free_dofs] = v
        return p

    load_scale = float(np.max(np.abs(loads))) if loads.size else 0.0
    cable_pre_scale = max([abs(float(cb.get("T_pretension_N", 0.0))) for cb in cables] + [0.0])
    membrane_N_per_m = max(
        abs(float(membrane_material.get("warp_prestress_N_per_m", 0.0))),
        abs(float(membrane_material.get("weft_prestress_N_per_m", 0.0))),
        1.0)
    edge_lengths = []
    for (a, b, c) in triangles:
        edge_lengths.append(float(np.linalg.norm(points[b] - points[a])))
        edge_lengths.append(float(np.linalg.norm(points[c] - points[b])))
        edge_lengths.append(float(np.linalg.norm(points[a] - points[c])))
    char_len = float(np.median(edge_lengths)) if edge_lengths else 1.0
    membrane_scale_N = membrane_N_per_m * char_len
    force_scale = max(1.0, load_scale, cable_pre_scale, membrane_scale_N)
    tol_abs = float(tol) * force_scale

    bbox = np.max(points, axis=0) - np.min(points, axis=0)
    scale_len = max(float(np.linalg.norm(bbox)), 1e-3)
    tol_disp_abs = float(tol_disp) * scale_len

    taut_flags = [False] * len(cables)
    history = []
    reason = "max_iter"
    converged = False
    inner_failed = False
    prev_residual = None
    stall_count = 0
    total_steps = 0
    last_step_size = 0.0

    for outer in range(max_outer + 1):
        if time.time() - t_start > max_wall_seconds:
            reason = "wall_clock_exceeded"; break
        if total_steps >= max_total_steps:
            reason = "step_budget_exhausted"; break
        for k, cb in enumerate(cables):
            _T, taut, _k, _u = cable_state(points[int(cb["a"])], points[int(cb["b"])], float(cb["L0"]), float(cb["EA"]))
            taut_flags[k] = taut
        R = _assemble_residual(points, triangles, cables, ref_points, membrane_material, loads, free_mask, n_nodes, taut_flags)
        r_flat = flat(R)
        r_norm = float(np.linalg.norm(r_flat))
        r_max = float(np.max(np.abs(r_flat))) if r_flat.size else 0.0
        history.append((outer, 0, r_norm, r_max))

        if r_max < tol_abs:
            converged = True; reason = "converged"; break

        inner_failed = False
        for it in range(1, max_iter + 1):
            if time.time() - t_start > max_wall_seconds:
                reason = "wall_clock_exceeded"; inner_failed = True; break
            if total_steps >= max_total_steps:
                reason = "step_budget_exhausted"; inner_failed = True; break
            total_steps += 1
            K = _assemble_tangent_sparse(points, triangles, cables, ref_points, membrane_material, free_mask, n_nodes, taut_flags)
            dx = _solve_linear_system(K, r_flat, n_dof)
            dx_norm = float(np.linalg.norm(dx))
            max_step = 0.01 * scale_len
            if dx_norm > max_step and dx_norm > 0.0:
                dx = dx * (max_step / dx_norm)
                dx_norm = max_step
            alpha = 1.0
            best_alpha = None; best_r = None; best_norm = r_norm
            x0 = flat(points); best_flags = list(taut_flags)
            for ls_step in range(DEFAULT_LINE_SEARCH_STEPS):
                x_try = x0 + alpha * dx
                p_try = unflat(x_try)
                trial_flags = [False] * len(cables)
                for kk, cbt in enumerate(cables):
                    _Tt, taut_t, _k_t, _u_t = cable_state(p_try[int(cbt["a"])], p_try[int(cbt["b"])], float(cbt["L0"]), float(cbt["EA"]))
                    trial_flags[kk] = taut_t
                try:
                    R_try = _assemble_residual(p_try, triangles, cables, ref_points, membrane_material, loads, free_mask, n_nodes, trial_flags)
                except Exception:
                    alpha *= 0.5; continue
                r_try = flat(R_try)
                n_try = float(np.linalg.norm(r_try))
                if n_try < best_norm:
                    best_alpha = alpha; best_norm = n_try; best_r = r_try; best_flags = trial_flags; break
                alpha *= 0.5
            if best_alpha is None:
                reason = "line_search_failed"; inner_failed = True; break
            points = unflat(x0 + best_alpha * dx)
            r_flat = best_r; r_norm = best_norm
            r_max = float(np.max(np.abs(r_flat))) if r_flat.size else 0.0
            taut_flags = best_flags
            history.append((outer, it, r_norm, r_max))
            last_step_size = best_alpha * dx_norm

            if r_max < tol_abs:
                converged = True; reason = "converged"; break

            if last_step_size < tol_disp_abs:
                if r_max < tol_abs * 10.0:
                    converged = True; reason = "converged_disp_but_residual_ok"; break
                else:
                    reason = "stalled_step_small_residual_large"
                    inner_failed = True
                    break

        if converged: break
        if inner_failed: break

        new_flags = [False] * len(cables)
        for k, cb in enumerate(cables):
            _T, taut, _k, _u = cable_state(points[int(cb["a"])], points[int(cb["b"])], float(cb["L0"]), float(cb["EA"]))
            new_flags[k] = taut
        if new_flags == taut_flags:
            if prev_residual is not None:
                improvement = prev_residual - r_max
                rel_improvement = improvement / max(abs(prev_residual), 1.0)
                if rel_improvement < 1.0e-3:
                    stall_count += 1
                else:
                    stall_count = 0
            prev_residual = r_max
            if stall_count >= 3:
                reason = "active_set_stable_no_convergence"; break
        else:
            stall_count = 0; prev_residual = r_max
        taut_flags = new_flags

    membrane_stress_list = []
    for (a, b, c) in triangles:
        try:
            sigma, comp, _sp = membrane_stress(points[a], points[b], points[c], ref_points[a], ref_points[b], ref_points[c], membrane_material)
            membrane_stress_list.append({"triangle": (int(a), int(b), int(c)), "sigma": sigma, "compression_found": bool(comp)})
        except ValueError:
            membrane_stress_list.append({"triangle": (int(a), int(b), int(c)), "sigma": np.zeros((2, 2)), "compression_found": False})

    cable_tension_list = []
    for cb in cables:
        T, taut, _k, _u = cable_state(points[int(cb["a"])], points[int(cb["b"])], float(cb["L0"]), float(cb["EA"]))
        cable_tension_list.append({"a": int(cb["a"]), "b": int(cb["b"]), "T_N": float(T), "L0_m": float(cb["L0"]), "taut": bool(taut)})

    all_true = np.ones(n_nodes, dtype=bool)
    R_final = _assemble_residual(points, triangles, cables, ref_points, membrane_material, loads, all_true, n_nodes, taut_flags)
    R_final[fixed_mask] = -R_final[fixed_mask]
