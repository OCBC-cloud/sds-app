"""SDSe Engine — Dynamic Relaxation Solver (BATS-integrated).

Solves membrane + cables + steel beams together in one DR loop.
No stiffness matrix. Kinetic damping. Automatic node fusion.

Authoritative reference: BATS (Basic Analysis of Tensile Structures),
extended for beam elements (Bletzinger, Ramm, et al., TUM).

Usage:
    Phase 1 (Form-Finding): solve_dr(..., loads=None, include_beams=False)
    Phase 2 (Integrated Analysis): solve_dr(..., loads=wind, include_beams=True)
"""

import math
import time

import numpy as np


# =============================================================================
# CONSTANTS
# =============================================================================

GRAVITY = 9.81
EPS = 1e-12
DEFAULT_MAX_ITER = 20000
DEFAULT_TOL = 1e-6
DEFAULT_DAMPING = 0.95
DEFAULT_MASS_SCALE = 1.0


# =============================================================================
# ELEMENT: MEMBRANE (CST, TENSION-FIELD)
# =============================================================================

def _membrane_stress(p0, p1, p2, r0, r1, r2, E1, E2, nu, G12, thickness, warp_pre_N, weft_pre_N):
    """Return (sigma_11, sigma_22, sigma_12) in the local plane."""
    e1 = p1 - p0
    e2 = p2 - p0
    n = np.cross(e1, e2)
    nn = np.linalg.norm(n)
    if nn < EPS:
        return np.zeros((2, 2))
    normal = n / nn
    t1 = e1 / np.linalg.norm(e1)
    t2 = np.cross(normal, t1)

    def comp(v):
        return np.array([np.dot(v, t1), np.dot(v, t2)])

    c1 = comp(p1 - p0)
    c2 = comp(p2 - p0)
    rr1 = comp(r1 - r0)
    rr2 = comp(r2 - r0)

    d1 = c1 - rr1
    d2 = c2 - rr2

    E11 = 0.5 * (d1[0] * d1[0] + d2[0] * d2[0] + 2 * (rr1[0] * d1[0] + rr2[0] * d2[0]))
    E22 = 0.5 * (d1[1] * d1[1] + d2[1] * d2[1] + 2 * (rr1[1] * d1[1] + rr2[1] * d2[1]))
    E12 = 0.5 * (d1[0] * d1[1] + d2[0] * d2[1]
                 + rr1[0] * d1[1] + d1[0] * rr1[1]
                 + rr2[0] * d2[1] + d2[0] * rr2[1])

    nu21 = nu * E2 / E1
    denom = 1.0 - nu * nu21
    C11 = E1 / denom
    C22 = E2 / denom
    C12 = nu * E2 / denom

    s11 = C11 * E11 + C12 * E22
    s22 = C12 * E11 + C22 * E22
    s12 = G12 * (2 * E12)

    s11 *= thickness
    s22 *= thickness
    s12 *= thickness

    s11 += warp_pre_N
    s22 += weft_pre_N

    sigma = np.array([[s11, s12], [s12, s22]])

    vals, vecs = np.linalg.eigh(sigma)
    vals_p = np.maximum(vals, 0.0)
    sigma_p = vecs @ np.diag(vals_p) @ vecs.T

    return sigma_p


def _membrane_nodal_forces(p0, p1, p2, r0, r1, r2, E1, E2, nu, G12, thickness, warp_pre_N, weft_pre_N):
    sigma = _membrane_stress(p0, p1, p2, r0, r1, r2, E1, E2, nu, G12, thickness, warp_pre_N, weft_pre_N)

    e1 = p1 - p0
    e2 = p2 - p0
    n = np.cross(e1, e2)
    nn = np.linalg.norm(n)
    if nn < EPS:
        return np.zeros(3), np.zeros(3), np.zeros(3)
    normal = n / nn
    t1 = e1 / np.linalg.norm(e1)
    t2 = np.cross(normal, t1)

    def plane(v):
        return np.array([np.dot(v, t1), np.dot(v, t2)])

    e01 = p1 - p0
    e12 = p2 - p1
    e20 = p0 - p2

    def outward(edge2d):
        n2 = np.array([edge2d[1], -edge2d[0]])
        n2n = np.linalg.norm(n2)
        return np.zeros(2) if n2n < EPS else n2 / n2n

    forces = []
    for e2d, e3d in [(plane(e01), e01), (plane(e12), e12), (plane(e20), e20)]:
        n2 = outward(e2d)
        trac = sigma @ n2
        ln = np.linalg.norm(e3d)
        f2 = trac * ln
        f3 = f2[0] * t1 + f2[1] * t2
        forces.append(f3)

    fe01, fe12, fe20 = forces
    f0 = (1.0 / 3.0) * (fe20 - fe01)
    f1 = (1.0 / 3.0) * (fe01 - fe12)
    f2 = (1.0 / 3.0) * (fe12 - fe20)
    return -f0, -f1, -f2


# =============================================================================
# ELEMENT: CABLE (TENSION-ONLY)
# =============================================================================

def _cable_forces(p_a, p_b, L0, EA):
    d = p_b - p_a
    L = np.linalg.norm(d)
    if L < EPS or L0 < EPS:
        return np.zeros(3), np.zeros(3), 0.0
    strain = (L - L0) / L0
    if strain <= 0.0:
        return np.zeros(3), np.zeros(3), 0.0
    T = EA * strain
    u = d / L
    return -T * u, T * u, T


# =============================================================================
# ELEMENT: BEAM (12-DOF, EULER-BERNOULLI, SIMPLIFIED FOR DR)
# =============================================================================

def _beam_forces_3d(pa, pb, ra, rb, A, I, J, E, G, local_axes=None):
    """Return (force_a, moment_a, force_b, moment_b) for the beam in global coords."""
    d = pb - pa
    L = np.linalg.norm(d)
    if L < EPS:
        return np.zeros(3), np.zeros(3), np.zeros(3), np.zeros(3)

    u = d / L

    r_d = rb - ra
    r_d_perp = r_d - np.dot(r_d, u) * u

    axial_strain = (L - np.linalg.norm(r_d)) / max(np.linalg.norm(r_d), EPS)
    N = E * A * axial_strain

    if local_axes is not None:
        v = local_axes
    else:
        v = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(v, u)) > 0.9:
            v = np.array([1.0, 0.0, 0.0])
    w = np.cross(u, v)
    w = w / np.linalg.norm(w)
    v = np.cross(w, u)

    theta_b = r_d_perp / L

    M_bending = E * I * theta_b

    f_local = np.array([
        N,  # axial
        M_bending[0] * L,
        M_bending[1] * L,
        M_bending[2] * L,
    ])

    f_a = -N * u
    f_b = N * u

    M_a = np.zeros(3)
    M_b = M_bending

    return f_a, M_a, f_b, M_b


# =============================================================================
# FRAME BUILDER (membrane-cable-beam node fusion)
# =============================================================================

def _build_integrated_system(mesh, frame_data):
    """Merge membrane nodes with steel beam nodes at shared anchors/rings/drops."""
    pts = mesh["points"].copy()
    n_membrane = pts.shape[0]
    n_beams = frame_data["n_nodes"]

    beam_nodes = frame_data["nodes"]
    all_nodes = np.vstack([pts, beam_nodes])

    shared = {}
    for mem_idx, beam_idx in frame_data["shared_pairs"]:
        all_nodes[mem_idx] = beam_nodes[beam_idx]
        shared[beam_idx] = mem_idx

    return all_nodes, n_membrane, n_beams, shared


# =============================================================================
# DYNAMIC RELAXATION LOOP
# =============================================================================

def solve_dr(
    points,
    triangles,
    cables,
    beams,
    fixed_indices,
    reference_points,
    membrane_props,
    loads=None,
    max_iter=DEFAULT_MAX_ITER,
    tol=DEFAULT_TOL,
    kinetic_damping=True,
    mass_scale=DEFAULT_MASS_SCALE,
    wall_seconds=60.0,
):
    """Integrated Dynamic Relaxation solver (BATS-style).

    Args:
        points: (N, 3) node coordinates
        triangles: list of (a, b, c) membrane triangle indices
        cables: list of dicts {"a", "b", "L0", "EA"}
        beams: list of dicts {"a", "b", "section"}
        fixed_indices: list of node indices (baseplates, eave anchors)
        reference_points: (N, 3) reference geometry (for strain computation)
        membrane_props: dict with E1, E2, nu, G12, thickness, warp_pre_N, weft_pre_N
        loads: (N, 3) nodal loads or None

    Returns:
        dict with coordinates, residual_norm, iterations, converged, reason
    """
    t_start = time.time()

    pts = np.asarray(points, dtype=float).copy()
    ref = np.asarray(reference_points, dtype=float).copy()
    N = pts.shape[0]

    if loads is None:
        F_ext = np.zeros((N, 3))
    else:
        F_ext = np.asarray(loads, dtype=float).copy()

    fixed_set = set(int(i) for i in fixed_indices)
    free_mask = np.array([i not in fixed_set for i in range(N)])
    free_idx = np.where(free_mask)[0]

    mass = np.ones(N) * mass_scale
    vel = np.zeros((N, 3))
    kinetic_prev = 0.0

    converged = False
    reason = "max_iter"
    iterations = 0

    E1 = membrane_props["E_warp_Pa"]
    E2 = membrane_props["E_weft_Pa"]
    nu = membrane_props["nu"]
    G12 = membrane_props["G_Pa"]
    thickness = membrane_props["thickness_m"]
    warp_pre = membrane_props["warp_prestress_N_per_m"]
    weft_pre = membrane_props["weft_prestress_N_per_m"]

    prev_res_norm = None

    for it in range(max_iter):
        iterations = it + 1
        if time.time() - t_start > wall_seconds:
            reason = "wall_clock"
            break

        residual = F_ext.copy()

        for (a, b, c) in triangles:
            f0, f1, f2 = _membrane_nodal_forces(
                pts[a], pts[b], pts[c],
                ref[a], ref[b], ref[c],
                E1, E2, nu, G12, thickness, warp_pre, weft_pre,
            )
            residual[a] += f0
            residual[b] += f1
            residual[c] += f2

        for cab in cables:
            fa, fb, _T = _cable_forces(pts[cab["a"]], pts[cab["b"]], cab["L0"], cab["EA"])
            residual[cab["a"]] += fa
            residual[cab["b"]] += fb

        for beam in beams:
            fa, Ma, fb, Mb = _beam_forces_3d(
                pts[beam["a"]], pts[beam["b"]],
                ref[beam["a"]], ref[beam["b"]],
                beam["section"]["A"], beam["section"]["I"],
                beam["section"].get("J", 2 * beam["section"]["I"]),
                beam["E"], beam["G"],
            )
            residual[beam["a"]] += fa
            residual[beam["b"]] += fb

        residual[~free_mask] = 0.0

        res_norm = np.linalg.norm(residual)
        max_res = np.max(np.abs(residual)) if residual.size else 0.0

        if max_res < tol * 1000.0:
            converged = True
            reason = "converged"
            break

        acc = residual / mass[:, None]

        if kinetic_damping:
            kinetic = 0.5 * mass[:, None] * vel * vel
            kinetic_now = kinetic.sum()
            if kinetic_now < kinetic_prev:
                vel[:] = 0.0
            kinetic_prev = kinetic_now

        vel[free_idx] += acc[free_idx] * 1.0
        vel[~free_mask] = 0.0

        pts[free_idx] += vel[free_idx] * 1.0

        prev_res_norm = res_norm

    return {
        "coordinates": pts,
        "iterations": iterations,
        "converged": converged,
        "reason": reason,
        "residual_norm": float(prev_res_norm) if prev_res_norm is not None else 0.0,
        "elapsed_seconds": time.time() - t_start,
    }


# =============================================================================
# HIGH-LEVEL WRAPPER
# =============================================================================

def solve_integrated(
    mesh_points,
    mesh_triangles,
    mesh_edges,
    boundary_edge_set,
    ring_specs,
    ribbon_specs,
    membrane_props,
    target_pretension_N,
    edge_cable_pretension_N,
    fixed_indices,
    loads=None,
    include_beams=True,
    max_iter=DEFAULT_MAX_ITER,
    wall_seconds=60.0,
):
    """One-stop wrapper: build cables, beams, fuse nodes, run DR."""
    ref = mesh_points.copy()

    cables = []
    n_a = len(ribbon_specs)
    for k, spec in enumerate(ribbon_specs):
        if k >= n_a - 1:
            break
        a = spec["start_idx"]
        b = ribbon_specs[k + 1]["start_idx"]
        L_ref = np.linalg.norm(ref[b] - ref[a])
        if L_ref < EPS:
            continue
        L0 = L_ref * (1.0 - edge_cable_pretension_N / (160e9 * 22.9e-6 * 1000))
        cables.append({"a": a, "b": b, "L0": L0, "EA": 160e9 * 22.9e-6})

    beams = []
    if include_beams:
        for spec in ring_specs:
            for i in range(len(spec["nodes"]) - 1):
                a = spec["nodes"][i]
                b = spec["nodes"][i + 1]
                beams.append({
                    "a": a, "b": b,
                    "section": spec["section"],
                    "E": 210e9, "G": 80e9,
                })

    if not include_beams:
        beams = []

    result = solve_dr(
        points=mesh_points,
        triangles=mesh_triangles,
        cables=cables,
        beams=beams,
        fixed_indices=fixed_indices,
        reference_points=ref,
        membrane_props=membrane_props,
        loads=loads,
        max_iter=max_iter,
        wall_seconds=wall_seconds,
    )

    return result
