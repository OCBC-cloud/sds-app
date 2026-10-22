# =============================================================================
# SDSe Engine - Dynamic Relaxation Solver (Kinetic Damping)
# =============================================================================
# A robust nonlinear solver using Dynamic Relaxation with kinetic damping.
# Kinetic damping detects when the total kinetic energy peaks and resets
# velocity to zero at that moment. This kills the bounce and forces
# convergence without slowing down the solver.
#
# History:
#   2026-10-22 - Removed duplicate residual assembly at top of loop (2x speed).
#                Stopping criterion is now RELATIVE to the initial residual
#                (tol_rel), because a raw Newton force norm of 1e-4 N is
#                unreachable on a kN-scale structure. Old absolute 'tol' is
#                still accepted for backward compatibility.
#                Kinetic energy is now smoothed with a 3-point moving average
#                before peak detection, so damping does not fire every 3
#                iterations on noise. Default max_velocity raised 1.0 -> 10.0.
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
    max_iter=5000, tol_rel=1e-3, tol=None, max_wall_seconds=25.0,
    dt=0.001, max_velocity=10.0, kinetic_damping=True
):
    """
    Solve nonlinear equilibrium using Dynamic Relaxation with
    kinetic damping (default) or viscous damping (kinetic_damping=False).

    Stopping criterion:
        converged when ||R_free|| <= tol_rel * ||R_free,initial||
    If the caller passes the legacy absolute 'tol' (Newtons), it is used
    directly instead of the relative criterion. This keeps old call sites
    working without silently changing their meaning.

    'tol_rel' is dimensionless. Recommended values:
        1e-2   - loose, quick look
        1e-3   - default, good engineering convergence
        1e-4   - tight, may not be reachable inside a wall clock budget
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

    # Initial residual: computed ONCE, used for the relative tolerance and
    # as the loop's starting residual. No duplicate assembly at the top of
    # each iteration.
    R = _assemble_residual(
        points, triangles, cables, reference_points,
        membrane_material, loads, free_mask, n_nodes, taut_flags
    )
    r_norm = float(np.linalg.norm(R[free_mask]))
    r_norm_initial = max(r_norm, 1e-30)

    if tol is not None:
        # Legacy absolute tolerance (Newtons). Honor it exactly.
        r_target = float(tol)
        stop_mode = "absolute"
    else:
        r_target = float(tol_rel) * r_norm_initial
        stop_mode = "relative"

    converged = False
    reason = "max_iter"
    iterations = 0
    total_steps = 0

    # Kinetic damping tracking. kinetic_history is a 3-point ring buffer
    # used to smooth the energy before peak detection, so false peaks on
    # stiffness noise do not fire every few iterations.
    kinetic_history = []
    kinetic_peaks = 0
    viscous_damping = 0.90

    for it in range(max_iter):
        iterations = it + 1
        total_steps += 1

        if time.time() - t_start > max_wall_seconds:
            reason = "wall_clock_exceeded"
            break

        if r_norm < r_target:
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

        # Accelerate
        acc = R / mass[:, np.newaxis]
        velocity += acc * dt

        # Damping strategy
        if kinetic_damping:
            kinetic = float(np.sum(0.5 * mass[free_mask] *
                                   np.sum(velocity[free_mask] ** 2, axis=1)))

            # 3-point moving average of kinetic energy. Peak detection
            # operates on the smoothed series, not the raw one.
            kinetic_history.append(kinetic)
            if len(kinetic_history) > 3:
                kinetic_history.pop(0)
            if len(kinetic_history) < 3:
                smoothed = kinetic
                prev_smoothed = None
            else:
                smoothed = sum(kinetic_history) / 3.0
                prev_smoothed = getattr(solve_dynamic_relaxation,
                                        "_prev_smoothed", None)
                solve_dynamic_relaxation._prev_smoothed = smoothed

            if (prev_smoothed is not None) and (smoothed < prev_smoothed):
                # Smoothed kinetic energy has peaked. Reset velocity.
                velocity[free_mask] = 0.0
                kinetic_peaks += 1
                solve_dynamic_relaxation._prev_smoothed = None
                kinetic_history.clear()
        else:
            velocity *= viscous_damping

        # Velocity clamp
        v_norm = np.linalg.norm(velocity, axis=1)
        too_fast = v_norm > max_velocity
        if np.any(too_fast):
            velocity[too_fast] *= (max_velocity / v_norm[too_fast])[:, np.newaxis]

        # Move
        points[free_mask] += velocity[free_mask] * dt

        # Recompute residual AFTER moving. This is the only residual
        # assembly inside the loop. The value is used by the top-of-loop
        # convergence check on the next pass, and by the final report if
        # the loop exits.
        R = _assemble_residual(
            points, triangles, cables, reference_points,
            membrane_material, loads, free_mask, n_nodes, taut_flags
        )
        r_norm = float(np.linalg.norm(R[free_mask]))

    # If the loop exited by max_iter or wall clock without the top-of-loop
    # check catching the final residual, evaluate convergence one last time
    # so the reported flag matches the reported residual.
    if (not converged) and (r_norm < r_target):
        converged = True
        reason = "converged"

    # Clear the class-level scratch used by the smoothing detector, so the
    # next run of the solver starts clean.
    if hasattr(solve_dynamic_relaxation, "_prev_smoothed"):
        del solve_dynamic_relaxation._prev_smoothed

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
        "residual_initial": float(r_norm_initial),
        "residual_target": float(r_target),
        "stop_mode": stop_mode,
        "max_residual": float(r_norm),
        "membrane_stress": membrane_stress_list,
        "cable_tension": cable_tension_list,
        "reason": reason,
        "kinetic_peaks": kinetic_peaks,
    }
