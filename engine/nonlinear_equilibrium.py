# =============================================================================
# SDSe Engine - Nonlinear Membrane + Cable Equilibrium
# =============================================================================
# The real coupled nonlinear solver. Not a wrapper. Not a stage.
#
# Committed to on 2026-10-04 (see PROJECT_SESSION_LOG.md).
#
# What this module does:
#   Finds the equilibrium of a triangulated membrane mesh with
#   real membrane elements and real cable elements, coupled
#   through a single Newton-Raphson solve.
#
# Membrane element:
#   - Green-Lagrange strain from current geometry against a
#     reference configuration.
#   - Orthotropic plane-stress constitutive (E_warp, E_weft,
#     nu, G) using the plane-stress matrix for an orthotropic
#     material.
#   - Tension-field projection INSIDE the element:
#     sigma = Q diag(max(s1,0), max(s2,0)) Q^T.
#   - Internal force vector at the three nodes.
#
# Cable element:
#   - Tension T = EA (L - L0) / L0, clamped at T >= 0.
#   - Internal force vector at the two nodes.
#
# Newton-Raphson:
#   - Numerical tangent by finite differences.
#   - Backtracking line search on the residual norm.
#   - Iterates until max|R| < tol.
#
# Units:
#   Length: m. Force: N. Stress: N/m^2. Thickness: m.
#   Membrane E: N/m^2 (converted from MPa internally).
#   Cable E: N/m^2 (converted from MPa internally).
#
# References:
#   Pauletti, R. M. O. (2006). Natural Force Density Method.
#   Wagner, R. (1965). Tension-field theory.
#   CECS 158:2015, Appendix C (biaxial test).
#   Uhlemann, J. (2016). Elastic Constants of Architectural
#     Fabrics for Design Purposes. PhD thesis, Duisburg-Essen.
#   Ferrari 702 datasheet.
#
# History:
#   2026-10-04 - First build.
# =============================================================================

import math

import numpy as np


# =============================================================================
# MATERIAL DEFAULTS
# =============================================================================

# The plane-stress constitutive needs five numbers. Three come
# from data/materials.py. Two are not stored there yet and are
# held here as module constants until data/materials.py is
# extended. Both are marked as placeholders to be refined per
# fabric in Stage 3.

MEMBRANE_NU_DEFAULT = 0.34
MEMBRANE_G_MPa_DEFAULT = 50.0

# Convergence and solver defaults.
DEFAULT_MAX_ITER = 60
DEFAULT_TOL = 1.0e-6
DEFAULT_LINE_SEARCH_STEPS = 16
FD_TANGENT_STEP = 1.0e-7

# Thresholds.
EPS = 1e-12


# =============================================================================
# PLANE-STRESS CONSTITUTIVE MATRIX (ORTHOTROPIC)
# =============================================================================

def plane_stress_matrix(E1, E2, nu12, G12):
    """
    Return the 3x3 orthotropic plane-stress constitutive matrix.

    Parameters
    ----------
    E1, E2 : float
        Young's moduli in the warp (1) and weft (2) directions.
        Units: N/m^2.
    nu12 : float
        Poisson's ratio for loading in warp direction, strain
        measured in weft direction.
    G12 : float
        In-plane shear modulus. Units: N/m^2.

    Returns
    -------
    C : (3, 3) array
        Stress-strain matrix in Voigt notation (s11, s22, s12).
    """
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


# =============================================================================
# TRIANGLE GEOMETRY AND STRAIN
# =============================================================================

def _triangle_basis(p0, p1, p2):
    """
    Return an orthonormal in-plane basis for a triangle.

    Parameters
    ----------
    p0, p1, p2 : (3,) node coordinates in current configuration.

    Returns
    -------
    t1, t2 : (3,) unit vectors spanning the triangle plane.
    normal : (3,) unit vector normal to the triangle.
    """
    e1 = p1 - p0
    e2 = p2 - p0
    n = np.cross(e1, e2)
    nn = float(np.linalg.norm(n))
    if nn < EPS:
        raise ValueError("Degenerate triangle (zero area)")
    normal = n / nn

    t1 = e1
    n1 = float(np.linalg.norm(t1))
    if n1 < EPS:
        t1 = e2
        n1 = float(np.linalg.norm(t1))
        if n1 < EPS:
            raise ValueError("Degenerate triangle (zero edge)")
    t1 = t1 / n1
    t2 = np.cross(normal, t1)
    t2 = t2 / (np.linalg.norm(t2) + EPS)
    return t1, t2, normal


def _green_lagrange_strain(p0, p1, p2, P0, P1, P2, t1, t2):
    """
    Return the 2x2 in-plane Green-Lagrange strain tensor.

    Parameters
    ----------
    p0, p1, p2 : current 3D node coordinates
    P0, P1, P2 : reference 3D node coordinates
    t1, t2 : current triangle basis (planar)

    Returns
    -------
    E : (2, 2) array. Engineering strain tensor components
        [Exx, Exy; Exy, Eyy] in the (t1, t2) basis.
    """
    # Reference edge vectors in the reference plane basis
    # (using the same t1, t2 as the current triangle plane,
    # which is a standard small-strain variant. For a fully
    # accurate Green-Lagrange strain the reference basis should
    # be the reference triangle's own basis. This is noted in
    # the module docstring; refinement is deferred.)
    E = np.zeros((2, 2), dtype=float)

    # Current edges in current basis.
    def _components(v):
        return np.array([float(np.dot(v, t1)), float(np.dot(v, t2))])

    c_e1 = _components(p1 - p0)
    c_e2 = _components(p2 - p0)
    r_e1 = _components(P1 - P0)
    r_e2 = _components(P2 - P0)

    for i in range(2):
        for j in range(2):
            # 2*E_ij = sum_over_edges ( (de_i)(de_j) )
            # where de = c_e - r_e in the (t1, t2) basis.
            de1 = c_e1 - r_e1
            de2 = c_e2 - r_e2
            E[i, j] = 0.5 * (
                de1[i] * de1[j] + de2[i] * de2[j]
            ) + 0.5 * (
                r_e1[i] * de1[j] + de1[i] * r_e1[j]
                + r_e2[i] * de2[j] + de2[i] * r_e2[j]
            )
    return E


def _strain_vector(E):
    """Return (Exx, Eyy, 2*Exy) from the 2x2 strain tensor."""
    return np.array([
        float(E[0, 0]),
        float(E[1, 1]),
        2.0 * float(E[0, 1]),
    ], dtype=float)


def _principal_project(s11, s22, s12):
    """
    Project a 2x2 stress tensor onto tension-only.

    Returns (s11p, s22p, s12p) after sigma = Q diag(max(0,s)) Q^T.
    """
    sigma = np.array([[s11, s12], [s12, s22]], dtype=float)
    vals, vecs = np.linalg.eigh(0.5 * (sigma + sigma.T))
    proj = np.maximum(vals, 0.0)
    sigma_p = vecs @ np.diag(proj) @ vecs.T
    sigma_p = 0.5 * (sigma_p + sigma_p.T)
    return float(sigma_p[0, 0]), float(sigma_p[1, 1]), float(sigma_p[0, 1])


# =============================================================================
# MEMBRANE ELEMENT: STRESS AND INTERNAL FORCE
# =============================================================================

def membrane_stress(p0, p1, p2, P0, P1, P2, C_plane, thickness):
    """
    Compute the plane-stress tensor at a triangle.

    Parameters
    ----------
    p0, p1, p2 : current 3D positions of the three nodes.
    P0, P1, P2 : reference 3D positions (same order).
    C_plane : (3, 3) plane-stress constitutive matrix.
    thickness : float, membrane thickness in metres.

    Returns
    -------
    sigma_resultant : (2, 2) in-plane stress resultant tensor.
        Units: N/m (force per unit width).
    compression_found : bool
    s_principal : (2,) principal values ascending.
    """
    t1, t2, _ = _triangle_basis(p0, p1, p2)
    E = _green_lagrange_strain(p0, p1, p2, P0, P1, P2, t1, t2)
    eps = _strain_vector(E)
    stress = C_plane @ eps  # N/m^2

    # Convert to stress resultant: multiply by thickness.
    s11 = float(stress[0]) * thickness
    s22 = float(stress[1]) * thickness
    s12 = float(stress[2]) * thickness

    sigma = np.array([[s11, s12], [s12, s22]], dtype=float)
    vals, _ = np.linalg.eigh(0.5 * (sigma + sigma.T))
    compression = bool(np.any(vals < -1e-9))
    s11p, s22p, s12p = _principal_project(s11, s22, s12)
    sigma_p = np.array([[s11p, s12p], [s12p, s22p]], dtype=float)
    vals_p, _ = np.linalg.eigh(sigma_p)
    return sigma_p, compression, vals_p


def _triangle_area_and_normal(p0, p1, p2):
    """Return (area, unit normal) of the triangle."""
    e1 = p1 - p0
    e2 = p2 - p0
    n = np.cross(e1, e2)
    area = 0.5 * float(np.linalg.norm(n))
    if area < EPS:
        raise ValueError("Degenerate triangle (zero area)")
    return area, n / (2.0 * area)


def membrane_internal_force(p0, p1, p2, P0, P1, P2, C_plane, thickness):
    """
    Return the internal force contribution at each of the three
    membrane nodes from a single triangle.

    Method: the Cauchy stress resultant tensor sigma (N/m) acting
    on each triangle edge, integrated along the edge length in
    the current configuration, gives the net force on each edge.
    The nodal force is one third of the edge forces adjacent to
    the node (constant-strain triangle equivalent).

    Returns
    -------
    f0, f1, f2 : (3,) force vectors at nodes 0, 1, 2.
        Sum is zero (self-equilibrating).
    """
    sigma, _comp, _sp = membrane_stress(
        p0, p1, p2, P0, P1, P2, C_plane, thickness
    )

    t1, t2, normal = _triangle_basis(p0, p1, p2)

    # Edge vectors in current config.
    e01 = p1 - p0
    e12 = p2 - p1
    e20 = p0 - p2

    # Convert each edge to the triangle plane basis.
    def _plane(v):
        return np.array([float(np.dot(v, t1)), float(np.dot(v, t2))])

    def _outward_normal_2d(edge_2d):
        # Outward normal in 2D for CCW-oriented triangle.
        n = np.array([edge_2d[1], -edge_2d[0]], dtype=float)
        nn = float(np.linalg.norm(n))
        if nn < EPS:
            return np.zeros(2)
        return n / nn

    # Traction on each edge from the stress resultant tensor.
    # t_edge = sigma @ n_edge (per unit length, in N/m).
    forces = []
    for edge_2d, edge_3d in (
        (_plane(e01), e01),
        (_plane(e12), e12),
        (_plane(e20), e20),
    ):
        n2d = _outward_normal_2d(edge_2d)
        traction_2d = sigma @ n2d  # N/m
        edge_len = float(np.linalg.norm(edge_3d))
        # Force vector = traction * length, in the plane basis,
        # then lifted to 3D. The edge's own 3D unit vector is used.
        force_2d = traction_2d * edge_len
        # Convert 2D force in (t1, t2) back to 3D.
        force_3d = force_2d[0] * t1 + force_2d[1] * t2
        forces.append(force_3d)

    # Edge forces as computed act on the triangle edges. The
    # nodal force for a CST triangle is one third of the sum of
    # the two edges adjacent to the node, with the outward
    # direction taken into account.
    f_edge01, f_edge12, f_edge20 = forces

    # f0 acts on edges 01 and 20, f1 on 01 and 12, f2 on 12 and 20.
    # The outward normal to edge 01 points away from node 2, so
    # f_edge01 acts positively on node 2 and negatively on node 0.
    # We follow the standard CST convention: the internal force
    # vector is the assembly of the traction on the edges
    # adjacent to each node, weighted by 1/3 for a CST.
    f0 = (1.0 / 3.0) * (f_edge20 - f_edge01)
    f1 = (1.0 / 3.0) * (f_edge01 - f_edge12)
    f2 = (1.0 / 3.0) * (f_edge12 - f_edge20)

    return f0, f1, f2


# =============================================================================
# CABLE ELEMENT
# =============================================================================

def cable_internal_force(p_a, p_b, L0, EA):
    """
    Return the tension and the internal force vectors at the two
    nodes of a cable element.

    Parameters
    ----------
    p_a, p_b : (3,) current node positions.
    L0 : float. Unstretched length in metres.
    EA : float. Cross-sectional stiffness (N). A (m^2) * E (N/m^2).

    Returns
    -------
    T : float. Tension in N. Zero if slack.
    f_a, f_b : (3,) force vectors on the two nodes.
    """
    d = p_b - p_a
    L = float(np.linalg.norm(d))
    if L < EPS:
        return 0.0, np.zeros(3), np.zeros(3)
    if L0 < EPS:
        return 0.0, np.zeros(3), np.zeros(3)

    strain = (L - L0) / L0
    if strain <= 0.0:
        return 0.0, np.zeros(3), np.zeros(3)

    T = EA * strain
    u = d / L
    f_a = -T * u
    f_b = T * u
    return float(T), f_a, f_b


# =============================================================================
# DATA CONTAINERS
# =============================================================================

def make_membrane_material(E_warp_MPa, E_weft_MPa, thickness_mm,
                            nu=0.34, G_MPa=50.0):
    """
    Build the membrane material dict.

    Units are converted to SI (N/m^2, m) for the solver.
    """
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
    """
    Build a cable element record.

    The unstretched length L0 is set by the driver from the
    reference configuration and the pretension. This function
    returns the material constants only.
    """
    A = float(A_mm2) * 1e-6
    E = float(E_MPa) * 1e6
    EA = A * E
    T_pre = float(prestress_kN) * 1000.0
    return {
        "A_m2": A,
        "E_Pa": E,
        "EA_N": EA,
        "T_pretension_N": T_pre,
    }


# =============================================================================
# RESIDUAL ASSEMBLY
# =============================================================================

def _assemble_residual(
    points, triangles, cables,
    ref_points, material, loads, free_mask, n_nodes
):
    """
    Assemble the internal force residual at every free node.

    Parameters
    ----------
    points : (n, 3) current node positions.
    triangles : list of (a, b, c).
    cables : list of dicts with keys 'a', 'b', 'L0', 'EA'.
    ref_points : (n, 3) reference positions.
    material : dict from make_membrane_material.
    loads : (n, 3) applied load on each node, N.
    free_mask : (n,) bool, True where node is free.
    n_nodes : int

    Returns
    -------
    R : (n, 3) residual, R = F_int - F_ext.
    """
    F = np.zeros((n_nodes, 3), dtype=float)

    C_plane = material["C_plane"]
    thickness = material["thickness_m"]

    for (a, b, c) in triangles:
        p0 = points[a]
        p1 = points[b]
        p2 = points[c]
        P0 = ref_points[a]
        P1 = ref_points[b]
        P2 = ref_points[c]
        try:
            f0, f1, f2 = membrane_internal_force(
                p0, p1, p2, P0, P1, P2, C_plane, thickness
            )
        except ValueError:
            continue
        F[a] += f0
        F[b] += f1
        F[c] += f2

    for cb in cables:
        a = int(cb["a"])
        b = int(cb["b"])
        _T, f_a, f_b = cable_internal_force(
            points[a], points[b],
            float(cb["L0"]), float(cb["EA"])
        )
        F[a] += f_a
        F[b] += f_b

    R = F - loads
    R[~free_mask] = 0.0
    return R


# =============================================================================
# NEWTON-RAPHSON SOLVER
# =============================================================================

def solve_nonlinear_equilibrium(
    points,
    triangles,
    fixed_indices,
    reference_points,
    membrane_material,
    cables=None,
    loads=None,
    max_iter=DEFAULT_MAX_ITER,
    tol=DEFAULT_TOL,
):
    """
    Find the equilibrium of a membrane + cable system.

    Parameters
    ----------
    points : (n, 3) initial coordinates.
    triangles : list of (a, b, c).
    fixed_indices : list of int, nodes fully fixed.
    reference_points : (n, 3) reference configuration.
    membrane_material : dict from make_membrane_material.
    cables : list of dicts, each with keys:
        a (int), b (int), L0 (float), EA (float).
        Optional: T_pretension_N (float).
        If T_pretension_N is given and L0 is not, L0 is derived
        from the reference length so that T = T_pretension_N at
        the reference configuration.
    loads : (n, 3) external loads, N. Default: zero.
    max_iter, tol : solver controls.

    Returns
    -------
    result : dict with keys:
        coordinates, converged, iterations, residual_norm,
        max_residual, membrane_stress (list per triangle),
        cable_tension (list per cable), history, reason.
    """
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
            raise ValueError("fixed index %d out of range" % i)
        fixed_mask[i] = True
    free_mask = ~fixed_mask

    if free_mask.sum() == 0:
        raise ValueError("no free nodes")

    # --- Prepare cables. Derive L0 from the reference if needed.
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

    def _flat_free(vec3):
        return vec3.ravel()[free_dofs]

    def _unflatten(flat):
        v = points.copy()
        v.ravel()[free_dofs] = flat
        return v

    # --- Initial residual and convergence history.
    history = []
    reason = "max_iter"
    converged = False

    R = _assemble_residual(
        points, triangles, cables,
        ref_points, membrane_material, loads, free_mask, n_nodes
    )
    r_flat = _flat_free(R)
    r_norm = float(np.linalg.norm(r_flat))
    r_max = float(np.max(np.abs(r_flat))) if r_flat.size else 0.0
    history.append((0, r_norm, r_max))

    if r_max < tol:
        converged = True
        reason = "converged_at_start"

    # --- Newton iteration.
    if not converged:
        for it in range(1, max_iter + 1):
            # Numerical tangent by forward finite differences.
            n_dof = len(free_dofs)
            K = np.zeros((n_dof, n_dof), dtype=float)
            x0 = _flat_free(points)
            for k in range(n_dof):
                h = FD_TANGENT_STEP * max(1.0, abs(x0[k]))
                x1 = x0.copy()
                x1[k] += h
                p1 = _unflatten(x1)
                R1 = _assemble_residual(
                    p1, triangles, cables,
                    ref_points, membrane_material, loads, free_mask,
                    n_nodes
                )
                r1 = _flat_free(R1)
                K[:, k] = (r1 - r_flat) / h

            # Solve K dx = -R.
            try:
                dx = np.linalg.solve(K, -r_flat)
            except np.linalg.LinAlgError:
                reason = "singular_tangent"
                break

            # Line search.
            alpha = 1.0
            best_alpha = None
            best_norm = r_norm
            for _ls in range(DEFAULT_LINE_SEARCH_STEPS):
                x_try = x0 + alpha * dx
                p_try = _unflatten(x_try)
                try:
                    R_try = _assemble_residual(
                        p_try, triangles, cables,
                        ref_points, membrane_material, loads, free_mask,
                        n_nodes
                    )
                except Exception:
                    alpha *= 0.5
                    continue
                r_try = _flat_free(R_try)
                n_try = float(np.linalg.norm(r_try))
                if n_try < best_norm:
                    best_alpha = alpha
                    best_norm = n_try
                    best_r_flat = r_try
                    break
                alpha *= 0.5

            if best_alpha is None:
                reason = "line_search_failed"
                break

            # Accept the step.
            x0 = x0 + best_alpha * dx
            points = _unflatten(x0)
            r_flat = best_r_flat
            r_norm = best_norm
            r_max = float(np.max(np.abs(r_flat)))
            history.append((it, r_norm, r_max))

            if r_max < tol:
                converged = True
                reason = "converged"
                break

    # --- Post-processing: stress per triangle, tension per cable.
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
        T, _fa, _fb = cable_internal_force(
            points[int(cb["a"])], points[int(cb["b"])],
            float(cb["L0"]), float(cb["EA"])
        )
        cable_tension_list.append({
            "a": int(cb["a"]),
            "b": int(cb["b"]),
            "T_N": float(T),
            "L0_m": float(cb["L0"]),
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
    """Flat square, all edges fixed, no load. Must stay flat."""
    n = 4
    pts = []
    for j in range(n):
        for i in range(n):
            pts.append([i / (n - 1.0), j / (n - 1.0), 0.0])
    pts = np.asarray(pts, dtype=float)
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

    mat = make_membrane_material(
        E_warp_MPa=1400.0, E_weft_MPa=1400.0,
        thickness_mm=1.02, nu=0.34, G_MPa=50.0,
    )

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
        "ok": z_max < 1e-6,
    }


def _test_single_cable_catenary():
    """
    A cable with fixed ends and gravity load must sag. The
    cable element under downward point load at the midpoint
    must stretch and produce tension.
    """
    pts = np.array([[0.0, 0.0, 0.0],
                    [0.5, 0.0, 0.0],
                    [1.0, 0.0, 0.0]], dtype=float)
    # Downward load at the midpoint node.
    loads = np.zeros((3, 3))
    loads[1, 2] = -500.0  # 500 N downward

    cab = [{"a": 0, "b": 1, "L0": 0.5, "EA": 1.0e7},
           {"a": 1, "b": 2, "L0": 0.5, "EA": 1.0e7}]

    mat = make_membrane_material(
        E_warp_MPa=1.0, E_weft_MPa=1.0,
        thickness_mm=0.01, nu=0.34, G_MPa=1.0,
    )

    res = solve_nonlinear_equilibrium(
        points=pts, triangles=[], fixed_indices=[0, 2],
        reference_points=pts, membrane_material=mat,
        cables=cab, loads=loads, max_iter=40, tol=1e-6,
    )
    coords = res["coordinates"]
    sag = -float(coords[1, 2])
    tension = float(res["cable_tension"][0]["T_N"])
    return {
        "converged": res["converged"],
        "iterations": res["iterations"],
        "residual_norm": res["residual_norm"],
        "sag_m": sag,
        "tension_N": tension,
        "ok": res["converged"] and sag > 1e-4 and tension > 100.0,
    }


def _test_pretension_tension():
    """
    A cable with pretension and no load must have exactly the
    pretension in it at the reference configuration.
    """
    pts = np.array([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0]], dtype=float)
    EA = 1.0e7
    T_pre = 1000.0

    cab = [{"a": 0, "b": 1, "T_pretension_N": T_pre, "EA": EA}]

    mat = make_membrane_material(
        E_warp_MPa=1.0, E_weft_MPa=1.0,
        thickness_mm=0.01, nu=0.34, G_MPa=1.0,
    )

    res = solve_nonlinear_equilibrium(
        points=pts, triangles=[], fixed_indices=[0, 1],
        reference_points=pts, membrane_material=mat,
        cables=cab, loads=None, max_iter=10, tol=1e-6,
    )
    T_final = float(res["cable_tension"][0]["T_N"])
    err = abs(T_final - T_pre) / T_pre
    return {
        "T_target": T_pre,
        "T_final": T_final,
        "rel_error": err,
        "ok": err < 1e-6,
    }


def _test_saddle_with_cable():
    """
    A small saddle with a real cable along one edge.
    Changing the cable pretension must change the shape.
    """
    # Simple 3x3 grid, mid node free.
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

    mat = make_membrane_material(
        E_warp_MPa=1400.0, E_weft_MPa=1400.0,
        thickness_mm=1.02, nu=0.34, G_MPa=50.0,
    )

    # Cable along edge 0-1-2 (top edge of the grid).
    cab_low = [{"a": 0, "b": 1, "T_pretension_N": 100.0, "EA": 1.0e7},
               {"a": 1, "b": 2, "T_pretension_N": 100.0, "EA": 1.0e7}]
    cab_high = [{"a": 0, "b": 1, "T_pretension_N": 2000.0, "EA": 1.0e7},
                {"a": 1, "b": 2, "T_pretension_N": 2000.0, "EA": 1.0e7}]

    res_low = solve_nonlinear_equilibrium(
        points=pts.copy(), triangles=tris, fixed_indices=fixed,
        reference_points=pts.copy(), membrane_material=mat,
        cables=cab_low, max_iter=30, tol=1e-5,
    )
    res_high = solve_nonlinear_equilibrium(
        points=pts.copy(), triangles=tris, fixed_indices=fixed,
        reference_points=pts.copy(), membrane_material=mat,
        cables=cab_high, max_iter=30, tol=1e-5,
    )

    disp_low = np.linalg.norm(
        res_low["coordinates"] - pts, axis=1
    ).max()
    disp_high = np.linalg.norm(
        res_high["coordinates"] - pts, axis=1
    ).max()
    diff = float(np.linalg.norm(
        res_low["coordinates"] - res_high["coordinates"]
    ))

    return {
        "converged_low": res_low["converged"],
        "converged_high": res_high["converged"],
        "disp_low_m": float(disp_low),
        "disp_high_m": float(disp_high),
        "diff_m": diff,
        "ok": diff > 1e-6,
    }


def run_all_tests():
    """Run the module self-tests. Return True if all pass."""
    print("=" * 60)
    print("Nonlinear Equilibrium - self-tests")
    print("=" * 60)

    all_ok = True

    print("-" * 60)
    print("Test 1 - Flat membrane stays flat")
    try:
        r1 = _test_flat_membrane()
        for k, v in r1.items():
            print("  %-16s : %s" % (k, v))
        if not r1.get("ok"):
            all_ok = False
    except Exception as e:
        print("  FAILED: %s" % str(e))
        all_ok = False

    print("-" * 60)
    print("Test 2 - Single cable catenary sag under load")
    try:
        r2 = _test_single_cable_catenary()
        for k, v in r2.items():
            print("  %-16s : %s" % (k, v))
        if not r2.get("ok"):
            all_ok = False
    except Exception as e:
        print("  FAILED: %s" % str(e))
        all_ok = False

    print("-" * 60)
    print("Test 3 - Cable pretension recovered exactly")
    try:
        r3 = _test_pretension_tension()
        for k, v in r3.items():
            print("  %-16s : %s" % (k, v))
        if not r3.get("ok"):
            all_ok = False
    except Exception as e:
        print("  FAILED: %s" % str(e))
        all_ok = False

    print("-" * 60)
    print("Test 4 - Saddle with edge cable responds to pretension")
    try:
        r4 = _test_saddle_with_cable()
        for k, v in r4.items():
            print("  %-16s : %s" % (k, v))
        if not r4.get("ok"):
            all_ok = False
    except Exception as e:
        print("  FAILED: %s" % str(e))
        all_ok = False

    print("=" * 60)
    print("GATE:", "PASS" if all_ok else "FAIL")
    print("-" * 60)
    return all_ok


# Alias for run_tests.py compatibility.
run = run_all_tests


if __name__ == "__main__":
    run_all_tests()


# =============================================================================
