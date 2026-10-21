# =============================================================================
# SDSe Engine - Dynamic Relaxation Solver (v2)
# =============================================================================
# A robust nonlinear solver based on Dynamic Relaxation.
# Includes velocity clamping to prevent numerical explosion.
# =============================================================================

import time
import numpy as np

from engine.nonlinear_equilibrium import (
    _assemble_residual,
    make_membrane_material,
)


def solve_dynamic_relaxation(
    points, triangles, fixed_indices, reference_points,
    membrane_material, cables=None, loads=None,
    max_iter=20000, tol=1e-4, max_wall_seconds=25.0,
    damping=0.90, dt=0.001, max_velocity=1.0
):
    """
    Solve nonlinear equilibrium using Dynamic Relaxation.
    max_velocity is the maximum distance (in metres) a node can move
    per step. This prevents the solver from exploding on stiff cables.
    """
    t_start = time.time()
    points = np.asarray(points, dtype=float).copy()
    reference_points = np.asarray(reference_points, dtype=float).copy()
    triangles = list(triangles)
    n_nodes = points.shape[0]

    if loads is None:
        loads = np.zeros((n_nodes, 3), dtype=float)
    else:
        loads = np.asarray(loads, dtype=float)

    fixed_mask = np.zeros(n_nodes, dtype=bool)
    for i in fixed_indices:
        fixed_mask[i] = True
    free_mask = ~fixed_mask

    mass = np.ones(n_nodes, dtype=float)
    velocity = np.zeros((n_nodes, 3), dtype=float)

    cables = list(cables or [])
    taut_flags = [False] * len(cables)

    # Initial residual
    R = _assemble_residual(
        points, triangles, cables, reference_points,
        membrane_material, loads, free_mask, n_nodes, taut_flags
    )
    r_norm = float(np.linalg.norm(R[free_mask]))

    converged = False
    reason = "max_iter"
    iterations = 0
    total_steps = 0

    for it in range(max_iter):
        iterations = it + 1
        total_steps += 1

        if time.time() - t_start > max_wall_seconds:
            reason = "wall_clock_exceeded"
            break

        if r_norm < tol:
            converged = True
            reason = "converged"
            break

        for k, cb in enumerate(cables):
            a = int(cb["a"])
            b = int(cb["b"])
            L0 = float(cb["L0"])
            L = float(np.linalg.norm(points[b] - points[a]))
            taut_flags[k] = L > L0

        R = _assemble_residual(
            points, triangles, cables, reference_points,
            membrane_material, loads, free_mask, n_nodes, taut_flags
        )
        r_norm = float(np.linalg.norm(R[free_mask]))

        acc = R / mass[:, np.newaxis]
        velocity += acc * dt
        velocity *= damping

        # Velocity clamp
        v_norm = np.linalg.norm(velocity, axis=1)
        too_fast = v_norm > max_velocity
        if np.any(too_fast):
            velocity[too_fast] *= (max_velocity / v_norm[too_fast])[:, np.newaxis]

        points[free_mask] += velocity[free_mask] * dt

    # Compute final stress/tension
    from engine.nonlinear_equilibrium import membrane_stress, cable_state
    membrane_stress_list = []
    for (a, b, c) in triangles:
        try:
            sigma, comp, _sp = membrane_stress(
                points[a], points[b], points[c],
                reference_points[a], reference_points[b], reference_points[c],
                membrane_material
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

    elapsed = time.time() - t_start

    return {
        "coordinates": points,
        "converged": bool(converged),
        "iterations": int(iterations),
        "total_steps": int(total_steps),
        "elapsed_seconds": float(elapsed),
        "residual_norm": float(r_norm),
        "max_residual": float(r_norm),
        "membrane_stress": membrane_stress_list,
        "cable_tension": cable_tension_list,
        "reason": reason,
    }
