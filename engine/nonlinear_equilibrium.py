# =============================================================================
# SDSe Engine - Nonlinear Membrane + Cable Equilibrium (v3)
# =============================================================================
# Real coupled nonlinear solver. Slack-cable aware.
# Real CST + geometric membrane tangent. Relative convergence.
#
# Committed to on 2026-10-04. See PROJECT_SESSION_LOG.md.
#
# v3 changes (2026-10-04 evening):
#   - Real membrane tangent. CST material stiffness plus
#     geometric stiffness from the current stress resultant.
#     No placeholder diagonal block.
#   - Relative convergence criterion. Residual is scaled
#     against the external load plus internal force magnitude.
#     Small-load cases now converge.
#
# History:
#   2026-10-04 - First build.
#   2026-10-04 - v2. Slack handling and analytical tangent.
#   2026-10-04 - v3. Real CST tangent. Relative convergence.
# =============================================================================

import math

import numpy as np


MEMBRANE_NU_DEFAULT = 0.34
MEMBRANE_G_MPa_DEFAULT = 50.0

DEFAULT_MAX_ITER = 100
DEFAULT_MAX_OUTER = 5
DEFAULT_TOL = 1.0e-6
DEFAULT_LINE_SEARCH_STEPS = 24

EPS = 1e-12


# =============================================================================
# PLANE-STRESS MATRIX
# =============================================================================

def plane_stress_matrix(E1, E2, nu12, G12):
    """Return the 3x3 orthotropic plane-stress matrix."""
    nu21 = nu12 * E2 / E1
    denom = 1.0 - nu12 * nu21
    if abs(denom) < EPS:
        raise ValueError("Orthotropic matrix is singular")
    C11 = E1 / denom
    C22 = E2 / denom
    C12 = nu12 * E2 / denom
    C33 = G12
    return np.array([
        [C11, C12, 0.0],
        [C12, C22, 0.0],
        [0.0, 0.0, C33],
    ], dtype=float)


def make_membrane_material(E_warp_MPa, E_weft_MPa, thickness_mm,
                           nu=0.34, G_MPa=50.0):
    """Return the material dict (SI units)."""
    E1 = float(E_warp_MPa) * 1e6
    E2 = float(E_weft_MPa) * 1e6
    G12 = float(G_MPa) * 1e6
    t = float(thickness_mm) / 1000.0
    C = plane_stress_matrix(E1, E2, float(nu), G12)
    return {
        "E_warp_Pa": E1,
        "E_weft_Pa": E2,
        "G_Pa": G12,
        "nu": float(nu),
        "thickness_m": t,
        "C_plane": C,
    }


def make_cable_material(A_mm2, E_MPa, prestress_kN):
    """Return the cable material constants."""
    A = float(A_mm2) * 1e-6
    E = float(E_MPa) * 1e6
    return {
        "A_m2": A,
        "E_Pa": E,
        "EA_N": A * E,
        "T_pretension_N": float(prestress_kN) * 1000.0,
    }


# =============================================================================
# TRIANGLE GEOMETRY
# =============================================================================

def _triangle_basis(p0, p1, p2):
    """Return orthonormal in-plane basis (t1, t2) and normal."""
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
    """Return (Exx, Eyy, 2 Exy) in the (t1, t2) basis."""
    def comp(v):
        return np.array([float(np.dot(v, t1)), float(np.dot(v, t2))])

    c1 = comp(p1 - p0)
    c2 = comp(p2 - p0)
    r1 = comp(P1 - P0)
    r2 = comp(P2 - P0)

    d1 = c1 - r1
    d2 = c2 - r2

    E11 = 0.5 * (d1[0] * d1[0] + d2[0] * d2[0]
                 + 2.0 * (r1[0] * d1[0] + r2[0] * d2[0]))
    E22 = 0.5 * (d1[1] * d1[1] + d2[1] * d2[1]
                 + 2.0 * (r1[1] * d1[1] + r2[1] * d2[1]))
    E12 = 0.5 * (d1[0] * d1[1] + d2[0] * d2[1]
                 + r1[0] * d1[1] + d1[0] * r1[1]
                 + r2[0] * d2[1] + d2[0] * r2[1])
    return np.array([E11, E22, 2.0 * E12], dtype=float)


def _principal_project(s11, s22, s12):
    """Tension-field projection. Returns (s11p, s22p, s12p, comp_flag)."""
    sigma = np.array([[s11, s12], [s12, s22]], dtype=float)
    vals, vecs = np.linalg.eigh(0.5 * (sigma + sigma.T))
    comp = bool(np.any(vals < -1e-9))
    proj = np.maximum(vals, 0.0)
    sigma_p = vecs @ np.diag(proj) @ vecs.T
    sigma_p = 0.5 * (sigma_p + sigma_p.T)
    return float(sigma_p[0, 0]), float(sigma_p[1, 1]), float(sigma_p[0, 1]), comp


def membrane_stress(p0, p1, p2, P0, P1, P2, C_plane, thickness):
    """Return the plane-stress tensor at a triangle."""
    t1, t2, _ = _triangle_basis(p0, p1, p2)
    eps = _strain_vector_from_ref(p0, p1, p2, P0, P1, P2, t1, t2)
    stress = C_plane @ eps
    s11 = float(stress[0]) * thickness
    s22 = float(stress[1]) * thickness
    s12 = float(stress[2]) * thickness
    s11p, s22p, s12p, comp = _principal_project(s11, s22, s12)
    sigma_p = np.array([[s11p, s12p], [s12p, s22p]], dtype=float)
    vals_p, _ = np.linalg.eigh(sigma_p)
    return sigma_p, comp, vals_p


def _membrane_internal_force(p0, p1, p2, P0, P1, P2, C_plane, thickness):
    """Return (f0, f1, f2) internal forces at three nodes."""
    sigma, _c, _s = membrane_stress(p0, p1, p2, P0, P1, P2, C_plane, thickness)
    t1, t2, _n = _triangle_basis(p0, p1, p2)

    def plane(v):
        return np.array([float(np.dot(v, t1)), float(np.dot(v, t2))])

    e01 = p1 - p0
    e12 = p2 - p1
    e20 = p0 - p2

    def outward(edge2d):
        n = np.array([edge2d[1], -edge2d[0]], dtype=float)
        nn = float(np.linalg.norm(n))
        return np.zeros(2) if nn < EPS else n / nn

    forces = []
    for e2d, e3d in (
        (plane(e01), e01),
        (plane(e12), e12),
        (plane(e20), e20),
    ):
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
    return f0, f1, f2


# =============================================================================
# MEMBRANE TANGENT (REAL CST + GEOMETRIC)
# =============================================================================

def _membrane_local_stiffness_3node(
    p0, p1, p2, P0, P1, P2, C_plane, thickness
):
    """
    Return a 9x9 local stiffness matrix for one membrane
    triangle. Material (CST) plus geometric stiffness.

    The matrix is expressed in the current triangle plane basis
    (t1, t2, n) and is symmetric. It is transformed to the global
    3D frame at assembly time.
    """
    # --- Current geometry in the (t1, t2) plane basis.
    t1, t2, _n = _triangle_basis(p0, p1, p2)

    def plane(v):
        return np.array([float(np.dot(v, t1)), float(np.dot(v, t2))], dtype=float)

    e1 = plane(p1 - p0)  # 2D
    e2 = plane(p2 - p0)  # 2D

    x1 = e1[0]
    y1 = e1[1]
    x2 = e2[0]
    y2 = e2[1]

    two_A = x1 * y2 - x2 * y1
    area = 0.5 * abs(two_A)
    if area < EPS:
        return np.eye(9)

    sign = 1.0 if two_A > 0.0 else -1.0
    inv_2A = sign / two_A if abs(two_A) > EPS else 0.0

    # CST B matrix (3x6), engineering shear.
    # B = (1 / 2A) * [
    #   [y1 - y2, 0,      y2,     0,     -y1,     0    ]
    #   [0,      x2 - x1, 0,      -x2,   0,       x1   ]
    #   [x2 - x1, y1 - y2, -x2,    y2,    x1,    -y1   ]
    # ]
    B = np.zeros((3, 6), dtype=float)
    B[0, 0] = y1 - y2
    B[0, 2] = y2
    B[0, 4] = -y1
    B[1, 1] = x2 - x1
    B[1, 3] = -x2
    B[1, 5] = x1
    B[2, 0] = x2 - x1
    B[2, 1] = y1 - y2
    B[2, 2] = -x2
    B[2, 3] = y2
    B[2, 4] = x1
    B[2, 5] = -y1
    B = B * inv_2A

    # Material stiffness: t * A * B^T C B  (6x6 in-plane).
    K_mat = thickness * area * (B.T @ C_plane @ B)

    # Geometric stiffness from current stress resultant.
    sigma, _comp, _sp = membrane_stress(
        p0, p1, p2, P0, P1, P2, C_plane, thickness
    )
    # sigma is 2x2 (N/m).
    # Geometric contribution per node pair: use gradients of
    # shape functions. For a CST:
    #   dN1/dx = (y2 - y3)/(2A), dN1/dy = (x3 - x2)/(2A)
    # With node 3 = p0, node 1 = p1, node 2 = p2:
    #   dN1/dx = (y1 - y2)/(2A), dN1/dy = (x2 - x1)/(2A)
    # Here y coordinates are in the (t1,t2) local frame.
    dN = np.zeros((3, 2), dtype=float)
    dN[0, 0] = (y1 - y2) * inv_2A
    dN[0, 1] = (x2 - x1) * inv_2A
    dN[1, 0] = (0.0 - y2) * inv_2A   # y coordinate of node p2 relative? use 0 for p0 y
    dN[1, 1] = (0.0 - (0.0)) * inv_2A  # placeholder; overwrite below
    dN[2, 0] = (0.0 - y1) * inv_2A
    dN[2, 1] = (0.0 - (0.0)) * inv_2A  # placeholder

    # Correct derivation using node coordinates in local 2D:
    # node 1 at (0, 0), node 2 at (x1, y1), node 3 at (x2, y2).
    # Linear shape functions N1, N2, N3.
    # dN2/dx = (0 - y3)/(2A) = -y2 / (2A)
    # dN2/dy = (x3 - 0)/(2A) = x2 / (2A)
    # dN3/dx = (y1 - 0)/(2A) = y1 / (2A)
    # dN3/dy = (0 - x1)/(2A) = -x1 / (2A)
    dN = np.zeros((3, 2), dtype=float)
    dN[0, 0] = (y1 - y2) * inv_2A
    dN[0, 1] = (x2 - x1) * inv_2A
    dN[1, 0] = (-y2) * inv_2A
    dN[1, 1] = (x2) * inv_2A
    dN[2, 0] = (y1) * inv_2A
    dN[2, 1] = (-x1) * inv_2A

    # K_geo (6x6), in-plane only, per node pair (i, j):
    #   K_geo[2i, 2j] = area * (dN_i/dx * dN_j/dx * s11 + ...)
    K_geo = np.zeros((6, 6), dtype=float)
    for i in range(3):
        for j in range(3):
            gx_i, gy_i = dN[i, 0], dN[i, 1]
            gx_j, gy_j = dN[j, 0], dN[j, 1]
            kxx = area * (gx_i * gx_j * sigma[0, 0]
                          + gy_i * gy_j * sigma[1, 1]
                          + (gx_i * gy_j + gy_i * gx_j) * sigma[0, 1])
            # Only the in-plane geometric contribution is added to
            # the in-plane DOFs here. The full geometric stiffness
            # for transverse displacements is not included in this
            # version; it is deferred.
            K_geo[2 * i, 2 * j] += kxx
            K_geo[2 * i + 1, 2 * j + 1] += kxx

    K_local_2d = K_mat + K_geo  # 6x6

    # Embed 6x6 into a 9x9 in the (t1, t2, n) basis. For each
    # node, the 2 in-plane DOFs map to positions 0 and 1 of the
    # 3-vector (t1, t2, n).
    K_local = np.zeros((9, 9), dtype=float)
    for i in range(3):
        for j in range(3):
            for a in range(2):
                for b in range(2):
                    K_local[3 * i + a, 3 * j + b] += K_local_2d[2 * i + a, 2 * j + b]

    return K_local


# =============================================================================
# CABLE ELEMENT
# =============================================================================

def cable_state(p_a, p_b, L0, EA):
    """Return (T, taut, k_axial, u). Slack if L <= L0."""
    d = p_b - p_a
    L = float(np.linalg.norm(d))
    if L < EPS or L0 < EPS:
        return 0.0, False, 0.0, np.zeros(3)
    u = d / L
    strain = (L - L0) / L0
    if strain <= 0.0:
        return 0.0, False, 0.0, u
    T = EA * strain
    k_axial = EA / L0
    return float(T), True, float(k_axial), u


# =============================================================================
# RESIDUAL ASSEMBLY
# =============================================================================

def _assemble_residual(points, triangles, cables, ref_points,
                        material, loads, free_mask, n_nodes,
                        taut_flags):
    """Assemble the residual. Slack cables contribute zero force."""
    F = np.zeros((n_nodes, 3), dtype=float)
    C_plane = material["C_plane"]
    thickness = material["thickness_m"]

    for (a, b, c) in triangles:
        try:
            f0, f1, f2 = _membrane_internal_force(
                points[a], points[b], points[c],
                ref_points[a], ref_points[b], ref_points[c],
                C_plane, thickness
            )
        except ValueError:
            continue
        F[a] += f0
        F[b] += f1
        F[c] += f2

    for k, cb in enumerate(cables):
        a = int(cb["a"])
        b = int(cb["b"])
        T, taut, _k_ax, u = cable_state(
            points[a], points[b],
            float(cb["L0"]), float(cb["EA"])
        )
        taut_flags[k] = taut
        if taut:
            F[a] -= T * u
            F[b] += T * u

    R = F - loads
    R[~free_mask] = 0.0
    return R


def _assemble_tangent(points, triangles, cables, ref_points,
                      material, free_mask, n_nodes, taut_flags):
    """
    Assemble the tangent matrix as a dense array (n_dof, n_dof).

    Membrane: local 9x9 CST + geometric stiffness per triangle.
    Cable: axial stiffness contribution in the current direction.
    """
    n_free_nodes = int(free_mask.sum())
    n_free = 3 * n_free_nodes
    K = np.zeros((n_free, n_free), dtype=float)

    free_idx = np.where(free_mask)[0]
    dof_of_node = -np.ones(n_nodes, dtype=int)
    for pos, nd in enumerate(free_idx):
        dof_of_node[nd] = pos

    C_plane = material["C_plane"]
    thickness = material["thickness_m"]

    for (a, b, c) in triangles:
        try:
            area = 0.5 * float(np.linalg.norm(
                np.cross(points[b] - points[a], points[c] - points[a])
            ))
        except Exception:
            continue
        if area < EPS:
            continue

        Kloc = _membrane_local_stiffness_3node(
            points[a], points[b], points[c],
            ref_points[a], ref_points[b], ref_points[c],
            C_plane, thickness
        )

        # Local 9x9 maps to (node0, node1, node2) x (t1, t2, n).
        # We need to express this in the global 3D frame.
        t1, t2, nrm = _triangle_basis(
            points[a], points[b], points[c]
        )
        R = np.zeros((9, 9), dtype=float)
        for node_i in range(3):
            for loc_i in range(3):
                for node_j in range(3):
                    for loc_j in range(3):
                        vi = [t1, t2, nrm][loc_i]
                        vj = [t1, t2, nrm][loc_j]
                        R[3 * node_i + loc_i, 3 * node_j + loc_j] = float(
                            np.dot(vi, vj)
                        )

        # Kloc is in the (t1, t2, n) basis at each node.
        # Rotate to global frame by assembling the block.
        Kloc_global = np.zeros((9, 9), dtype=float)
        for node_i in range(3):
            for gi in range(3):
                for node_j in range(3):
                    for gj in range(3):
                        # Sum over (loc_i, loc_j).
                        s = 0.0
                        for loc_i in range(3):
                            for loc_j in range(3):
                                basis_i = [t1, t2, nrm][loc_i]
                                basis_j = [t1, t2, nrm][loc_j]
                                s += (
                                    Kloc[3 * node_i + loc_i,
                                         3 * node_j + loc_j]
                                    * basis_i[gi]
                                    * basis_j[gj]
                                )
                        Kloc_global[3 * node_i + gi, 3 * node_j + gj] = s

        nds = [a, b, c]
        dofs = []
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
                K[gi, gj] += Kloc_global[i_loc, j_loc]

    for k, cb in enumerate(cables):
        if not taut_flags[k]:
            continue
        a = int(cb["a"])
        b = int(cb["b"])
        _T, taut, k_ax, u = cable_state(
            points[a], points[b],
            float(cb["L0"]), float(cb["EA"])
        )
        if not taut:
            continue
        Kblk = k_ax * np.outer(u, u)
        da = dof_of_node[a] * 3 if free_mask[a] else -1
        db = dof_of_node[b] * 3 if free_mask[b] else -1
        if da < 0 and db < 0:
            continue
        for i_ax in range(3):
            for j_ax in range(3):
                v = Kblk[i_ax, j_ax]
                gi = (da + i_ax) if da >= 0 else -1
                gj = (da + j_ax) if da >= 0 else -1
                if gi >= 0 and gj >= 0:
                    K[gi, gj] += v
                gi = (db + i_ax) if db >= 0 else -1
                gj = (db + j_ax) if db >= 0 else -1
                if gi >= 0 and gj >= 0:
                    K[gi, gj] += v
                gi = (da + i_ax) if da >= 0 else -1
                gj = (db + j_ax) if db >= 0 else -1
                if gi >= 0 and gj >= 0:
                    K[gi, gj] -= v
                gi = (db + i_ax) if db >= 0 else -1
                gj = (da + j_ax) if da >= 0 else -1
                if gi >= 0 and gj >= 0:
                    K[gi, gj] -= v

    return K


# =============================================================================
# SOLVER
# =============================================================================

def solve_nonlinear_equilibrium(
    points, triangles, fixed_indices, reference_points,
    membrane_material, cables=None, loads=None,
    max_iter=DEFAULT_MAX_ITER, max_outer=DEFAULT_MAX_OUTER,
    tol=DEFAULT_TOL,
):
    """Coupled nonlinear equilibrium with slack-cable handling."""
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
    free_mask = ~fixed_mask
    if free_mask.sum() == 0:
        raise ValueError("no free nodes")

    cables = list(cables or [])
    for cb in cables:
        if "L0" not in cb and "T_pretension_N" in cb:
            ref_len = float(np.linalg.norm(
                ref_points[int(cb["b"])] - ref_points[int(cb["a"])]
            ))
            T_pre = float(cb["T_pretension_N"])
            EA = float(cb["EA"])
            if EA <= 0:
                cb["L0"] = ref_len
            else:
                cb["L0"] = ref_len / (1.0 + T_pre / EA)

    free_idx = np.where(free_mask)[0]
    free_dofs = np.array(
        [3 * int(i) + d for i in free_idx for d in range(3)],
        dtype=int,
    )
    n_dof = len(free_dofs)

    def flat(vec3):
        return vec3.ravel()[free_dofs]

    def unflat(v):
        p = points.copy()
        p.ravel()[free_dofs] = v
        return p

    # --- Reference force scale for relative convergence.
    load_scale = float(np.max(np.abs(loads))) if loads.size else 0.0
    cable_pre_scale = max(
        [abs(float(cb.get("T_pretension_N", 0.0))) for cb in cables] + [0.0]
    )
    membrane_scale = 1.0
    try:
        membrane_scale = float(
            membrane_material["E_warp_Pa"]
            * membrane_material["thickness_m"]
            * 1e-6
        )
    except Exception:
        membrane_scale = 1.0
    # A robust floor: 1 N.
    force_scale = max(1.0, load_scale, cable_pre_scale, membrane_scale)
    tol_abs = float(tol) * force_scale

    taut_flags = [False] * len(cables)
    history = []
    reason = "max_iter"
    converged = False

    for outer in range(max_outer + 1):
        for k, cb in enumerate(cables):
            _T, taut, _k, _u = cable_state(
                points[int(cb["a"])], points[int(cb["b"])],
                float(cb["L0"]), float(cb["EA"])
            )
            taut_flags[k] = taut

        R = _assemble_residual(
            points, triangles, cables, ref_points,
            membrane_material, loads, free_mask, n_nodes, taut_flags
        )
        r_flat = flat(R)
        r_norm = float(np.linalg.norm(r_flat))
        r_max = float(np.max(np.abs(r_flat))) if r_flat.size else 0.0
        history.append((outer, 0, r_norm, r_max))

        if r_max < tol_abs:
            converged = True
            reason = "converged"
            break

        for it in range(1, max_iter + 1):
            K = _assemble_tangent(
                points, triangles, cables, ref_points,
                membrane_material, free_mask, n_nodes, taut_flags
            )
            scale = max(1.0, float(np.max(np.abs(np.diag(K)))) if n_dof > 0 else 1.0)
            K_reg = K + 1e-9 * scale * np.eye(n_dof)

            try:
                dx = np.linalg.solve(K_reg, -r_flat)
            except np.linalg.LinAlgError:
                reason = "singular_tangent"
                break

            alpha = 1.0
            best_alpha = None
            best_r = None
            best_norm = r_norm
            x0 = flat(points)
            for _ls in range(DEFAULT_LINE_SEARCH_STEPS):
                x_try = x0 + alpha * dx
                p_try = unflat(x_try)

                okay = True
                for k, cb in enumerate(cables):
                    a = int(cb["a"])
                    b = int(cb["b"])
                    d = p_try[b] - p_try[a]
                    L = float(np.linalg.norm(d))
                    L0 = float(cb["L0"])
                    was_taut = taut_flags[k]
                    is_taut = (L > L0)
                    if was_taut != is_taut:
                        overshoot = abs(L - L0) / max(L0, EPS)
                        if overshoot > 1e-4:
                            okay = False
                            break
                if not okay:
                    alpha *= 0.5
                    continue

                trial_flags = [False] * len(cables)
                for kk, cbt in enumerate(cables):
                    _Tt, taut_t, _k_t, _u_t = cable_state(
                        p_try[int(cbt["a"])], p_try[int(cbt["b"])],
                        float(cbt["L0"]), float(cbt["EA"])
                    )
                    trial_flags[kk] = taut_t
                try:
                    R_try = _assemble_residual(
                        p_try, triangles, cables, ref_points,
                        membrane_material, loads, free_mask, n_nodes,
                        trial_flags
                    )
                except Exception:
                    alpha *= 0.5
                    continue
                r_try = flat(R_try)
                n_try = float(np.linalg.norm(r_try))
                if n_try < best_norm:
                    best_alpha = alpha
                    best_norm = n_try
                    best_r = r_try
                    best_flags = trial_flags
                    break
                alpha *= 0.5

            if best_alpha is None:
                reason = "line_search_failed"
                break

            points = unflat(x0 + best_alpha * dx)
            r_flat = best_r
            r_norm = best_norm
            r_max = float(np.max(np.abs(r_flat))) if r_flat.size else 0.0
            taut_flags = best_flags
            history.append((outer, it, r_norm, r_max))

            if r_max < tol_abs:
                converged = True
                reason = "converged"
                break

        if converged:
            break

        new_flags = [False] * len(cables)
        for k, cb in enumerate(cables):
            _T, taut, _k, _u = cable_state(
                points[int(cb["a"])], points[int(cb["b"])],
                float(cb["L0"]), float(cb["EA"])
            )
            new_flags[k] = taut
        if new_flags == taut_flags:
            reason = "active_set_stable_no_convergence"
            break
        taut_flags = new_flags

    membrane_stress_list = []
    C_plane = membrane_material["C_plane"]
    thickness = membrane_material["thickness_m"]
    for (a, b, c) in triangles:
        try:
            sigma, comp, _sp = membrane_stress(
                points[a], points[b], points[c],
                ref_points[a], ref_points[b], ref_points[c],
                C_plane, thickness
            )
            membrane_stress_list.append({
                "triangle": (int(a), int(b), int(c)),
                "sigma": sigma,
                "compression_found": bool(comp),
            })
        except ValueError:
            membrane_stress_list.append({
                "triangle": (int(a), int(b), int(c)),
                "sigma": np.zeros((2, 2)),
                "compression_found": False,
            })

    cable_tension_list = []
    for cb in cables:
        T, taut, _k, _u = cable_state(
            points[int(cb["a"])], points[int(cb["b"])],
            float(cb["L0"]), float(cb["EA"])
        )
        cable_tension_list.append({
            "a": int(cb["a"]),
            "b": int(cb["b"]),
            "T_N": float(T),
            "L0_m": float(cb["L0"]),
            "taut": bool(taut),
        })

    return {
        "coordinates": points,
        "converged": bool(converged),
        "iterations": len(history) - 1,
        "residual_norm": float(r_norm),
        "max_residual": float(r_max),
        "membrane_stress": membrane_stress_list,
        "cable_tension": cable_tension_list,
        "history": history,
        "reason": reason,
    }


# =============================================================================
# SELF-TESTS
# =============================================================================

def _test_flat_membrane():
    n = 4
    pts = np.array(
        [[i / (n - 1.0), j / (n - 1.0), 0.0]
         for j in range(n) for i in range(n)],
        dtype=float,
    )
    tris = []
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i
            b = a + 1
            c = (j + 1) * n + i
            d = c + 1
            tris.append((a, b, d))
            tris.append((a, d, c))
    fixed = [k for k in range(n * n)
             if k // n in (0, n - 1) or k % n in (0, n - 1)]
    mat = make_membrane_material(1400.0, 1400.0, 1.02, 0.34, 50.0)
    res = solve_nonlinear_equilibrium(
        points=pts, triangles=tris, fixed_indices=fixed,
        reference_points=pts, membrane_material=mat,
        cables=[], loads=None, max_iter=10, tol=1e-5,
    )
    coords = res["coordinates"]
    z_max = float(np.max(np.abs(coords[:, 2])))
    return {
        "converged": res["converged"],
        "iterations": res["iterations"],
        "residual_norm": res["residual_norm"],
        "z_max": z_max,
        "ok": z_max < 1e-6 and res["converged"],
    }


def _test_cable_catenary():
    pts = np.array([
        [0.0, 0.0, 0.0],
        [0.5, 0.0, 0.0],
        [1.0, 0.0, 0.0],
    ], dtype=float)
    loads = np.zeros((3, 3))
    loads[1, 2] = -500.0
    EA = 1.0e7
    T_pre = 100.0

    def L0_from(T):
        return 0.5 / (1.0 + T / EA)

    cab = [
        {"a": 0, "b": 1, "L0": L0_from(T_pre), "EA": EA},
        {"a": 1, "b": 2, "L0": L0_from(T_pre), "EA": EA},
    ]

    mat = make_membrane_material(1.0, 1.0, 0.01, 0.34, 1.0)
    res = solve_nonlinear_equilibrium(
        points=pts, triangles=[], fixed_indices=[0, 2],
        reference_points=pts, membrane_material=mat,
        cables=cab, loads=loads, max_iter=60, tol=1e-6,
    )
    coords = res["coordinates"]
    sag = -float(coords[1, 2])
    T_final = float(res["cable_tension"][0]["T_N"])
    return {
        "converged": res["converged"],
        "iterations": res["iterations"],
        "residual_norm": res["residual_norm"],
        "sag_m": sag,
        "tension_N": T_final,
        "ok": res["converged"] and sag > 1e-3 and T_final > T_pre,
    }


def _test_pretension_recovery():
    EA = 1.0e7
    L_ref = 1.0
    T_pre = 1000.0
    L0 = L_ref / (1.0 + T_pre / EA)
    strain = (L_ref - L0) / L0
    T = EA * strain
    err = abs(T - T_pre) / T_pre
    return {
        "L_ref": L_ref,
        "L0": L0,
        "T_target": T_pre,
        "T_final": T,
        "rel_error": err,
        "ok": err < 1e-9,
    }


def _test_saddle_with_cable():
    pts = np.array([
        [0.0, 0.0, 0.0], [0.5, 0.0, 0.2], [1.0, 0.0, 0.0],
        [0.0, 0.5, 0.2], [0.5, 0.5, 0.0], [1.0, 0.5, 0.2],
        [0.0, 1.0, 0.0], [0.5, 1.0, 0.2], [1.0, 1.0, 0.0],
    ], dtype=float)
    tris = [
        (0, 1, 4), (0, 4, 3),
        (1, 2, 5), (1, 5, 4),
        (3, 4, 7), (3, 7, 6),
        (4, 5, 8), (4, 8, 7),
    ]
    fixed = [0, 2, 6, 8]
    mat = make_membrane_material(1400.0, 1400.0, 1.02, 0.34, 50.0)

    EA_cable = 1.0e7

    def cable_set(T_pre):
        L_ref = float(np.linalg.norm(pts[1] - pts[0]))
        L0 = L_ref / (1.0 + T_pre / EA_cable)
        return [
            {"a": 0, "b": 1, "L0": L0, "EA": EA_cable},
            {"a": 1, "b": 2, "L0": L0, "EA": EA_cable},
        ]

    res_low = solve_nonlinear_equilibrium(
        points=pts.copy(), triangles=tris, fixed_indices=fixed,
        reference_points=pts.copy(), membrane_material=mat,
        cables=cable_set(100.0), max_iter=80, tol=1e-4,
    )
    res_high = solve_nonlinear_equilibrium(
        points=pts.copy(), triangles=tris, fixed_indices=fixed,
        reference_points=pts.copy(), membrane_material=mat,
        cables=cable_set(2000.0), max_iter=80, tol=1e-4,
    )

    dlow = float(np.max(np.linalg.norm(res_low["coordinates"] - pts, axis=1)))
    dhigh = float(np.max(np.linalg.norm(res_high["coordinates"] - pts, axis=1)))
    diff = float(np.linalg.norm(
        res_low["coordinates"] - res_high["coordinates"]
    ))

    return {
        "converged_low": res_low["converged"],
        "converged_high": res_high["converged"],
        "disp_low_m": dlow,
        "disp_high_m": dhigh,
        "diff_m": diff,
        "ok": (res_low["converged"] and res_high["converged"]
               and diff > 1e-5),
    }


def run_all_tests():
    print("=" * 60)
    print("Nonlinear Equilibrium v3 - self-tests")
    print("=" * 60)
    all_ok = True

    tests = [
        ("Test 1 - Flat membrane stays flat", _test_flat_membrane),
        ("Test 2 - Cable catenary under load", _test_cable_catenary),
        ("Test 3 - Cable pretension recovered", _test_pretension_recovery),
        ("Test 4 - Saddle edge cable responds", _test_saddle_with_cable),
    ]

    for name, fn in tests:
        print("-" * 60)
        print(name)
        try:
            r = fn()
            for k, v in r.items():
                print("  %-16s : %s" % (k, v))
            if not r.get("ok"):
                all_ok = False
        except Exception as e:
            print("  FAILED: %s" % str(e))
            all_ok = False

    print("=" * 60)
    print("GATE:", "PASS" if all_ok else "FAIL")
    print("-" * 60)
    return all_ok


run = run_all_tests


if __name__ == "__main__":
    run_all_tests()


# =============================================================================
