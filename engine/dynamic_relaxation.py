# =============================================================================
# SDSe Engine - Dynamic Relaxation Solver (Kinetic Damping)
# =============================================================================
# A robust nonlinear solver using Dynamic Relaxation with kinetic damping.
# Kinetic damping detects when the total kinetic energy peaks and resets
# velocity to zero at that moment. This kills the bounce and forces
# convergence without slowing down the solver.
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
    max_iter=5000, tol=1e-4, max_wall_seconds=25.0,
    dt=0.001, max_velocity=1.0, kinetic_damping=True
):
    """
    Solve nonlinear equilibrium using Dynamic Relaxation with
    kinetic damping (default) or viscous damping (kinetic_damping=False).
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

    R = _assemble_residual(
        points, triangles, cables, reference_points,
        membrane_material, loads, free_mask, n_nodes, taut_flags
    )
    r_norm = float(np.linalg.norm(R[free_mask]))

    converged = False
    reason = "max_iter"
    iterations = 0
    total_steps = 0

    # Kinetic damping tracking
    prev_kinetic = None
    kinetic_peaks = 0
    viscous_damping = 0.90

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

        # Update taut flags
        for k, cb in enumerate(cables):
            a = int(cb["a"])
            b = int(cb["b"])
            L0 = float(cb["L0"])
            L = float(np.linalg.norm(points[b] - points[a]))
            taut_flags[k] = L > L0

        # Compute residual
        R = _assemble_residual(
            points, triangles, cables, reference_points,
            membrane_material, loads, free_mask, n_nodes, taut_flags
        )
        r_norm = float(np.linalg.norm(R[free_mask]))

        # Accelerate
        acc = R / mass[:, np.newaxis]
        velocity += acc * dt

        # Damping strategy
        if kinetic_damping:
            # Kinetic energy per node
            kinetic = float(np.sum(0.5 * mass[free_mask] *
                                   np.sum(velocity[free_mask] ** 2, axis=1)))
            
            # Detect peak in kinetic energy
            if prev_kinetic is not None and kinetic < prev_kinetic:
                # The kinetic energy has peaked. Reset velocity.
                velocity[free_mask] = 0.0
                kinetic_peaks += 1
                prev_kinetic = None
            else:
                prev_kinetic = kinetic
        else:
            velocity *= viscous_damping

        # Velocity clamp
        v_norm = np.linalg.norm(velocity, axis=1)
        too_fast = v_norm > max_velocity
        if np.any(too_fast):
            velocity[too_fast] *= (max_velocity / v_norm[too_fast])[:, np.newaxis]

        # Move
        points[free_mask] += velocity[free_mask] * dt

    # Final stress/tension
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
        "kinetic_peaks": kinetic_peaks,
    }
