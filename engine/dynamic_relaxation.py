# =============================================================================
# SDSe Engine - Dynamic Relaxation Solver
# =============================================================================
# A robust nonlinear solver based on Dynamic Relaxation (DR).
# Replaces Newton-Raphson for membrane form-finding under load.
# =============================================================================

import numpy as np
import time


def solve_dynamic_relaxation(
    points, triangles, fixed_indices, reference_points,
    membrane_material, cables=None, loads=None,
    max_iter=5000, tol=1e-4, max_wall_seconds=25.0,
    damping=0.95, dt=0.001
):
    """
    Solves nonlinear equilibrium using Dynamic Relaxation.
    """
    t_start = time.time()
    points = np.asarray(points, dtype=float).copy()
    n_nodes = points.shape[0]

    if loads is None:
        loads = np.zeros((n_nodes, 3), dtype=float)
    else:
        loads = np.asarray(loads, dtype=float)

    fixed_mask = np.zeros(n_nodes, dtype=bool)
    for i in fixed_indices:
        fixed_mask[i] = True
    free_mask = ~fixed_mask

    # 1. Assign fictitious mass (based on connectivity)
    # We use a simple uniform mass for stability
    mass = np.ones(n_nodes, dtype=float)
    
    # 2. Pre-calculate element stiffnesses (simplified for DR)
    # For DR, we use the current geometry to calculate forces.
    
    # 3. Initialize velocity
    velocity = np.zeros((n_nodes, 3), dtype=float)
    
    # We need the tangent stiffness for the DR stability check
    # For now, we use a simplified version

    def _assemble_forces(pts):
        """Assemble the out-of-balance forces."""
        F = np.zeros((n_nodes, 3), dtype=float)
        
        # Membrane forces
        for (a, b, c) in triangles:
            # Use the existing membrane internal force logic
            # (We'll import or inline a simplified version here)
            pass
            
        # Cable forces
        if cables:
            for cb in cables:
                a = int(cb["a"])
                b = int(cb["b"])
                L0 = float(cb["L0"])
                EA = float(cb["EA"])
                
                d = pts[b] - pts[a]
                L = float(np.linalg.norm(d))
                
                if L > 1e-9 and L > L0:
                    T = EA * (L - L0) / L0
                    u = d / L
                    F[a] += T * u
                    F[b] -= T * u
        
        # External loads
        F += loads
        
        # Zero out fixed nodes
        F[fixed_mask] = 0.0
        return F

    # We need a proper force assembly. Let's use the existing solver's
    # _assemble_residual logic, but we'll re-write it here for clarity.
    
    from engine.nonlinear_equilibrium import _assemble_residual, _membrane_internal_force, cable_state, make_membrane_material

    taut_flags = [False] * len(cables) if cables else []
    
    # 4. The Dynamic Relaxation Loop
    for it in range(max_iter):
        if time.time() - t_start > max_wall_seconds:
            return {
                "coordinates": points,
                "converged": False,
                "reason": "wall_clock_exceeded",
                "iterations": it,
                "residual_norm": np.inf,
            }
        
        # Calculate residual
        R = _assemble_residual(
            points, triangles, cables, reference_points,
            membrane_material, loads, free_mask, n_nodes, taut_flags
        )
        
        r_norm = float(np.linalg.norm(R[free_mask]))
        
        if r_norm < tol:
            return {
                "coordinates": points,
                "converged": True,
                "reason": "converged",
                "iterations": it,
                "residual_norm": r_norm,
            }
        
        # Update velocities and positions
        # a = F / m
        acc = R / mass[:, np.newaxis]
        
        # v = v + a * dt
        velocity += acc * dt
        
        # Apply damping
        velocity *= damping
        
        # x = x + v * dt
        points[free_mask] += velocity[free_mask] * dt
        
        # Update cable tautness
        if cables:
            for k, cb in enumerate(cables):
                a = int(cb["a"])
                b = int(cb["b"])
                L0 = float(cb["L0"])
                L = float(np.linalg.norm(points[b] - points[a]))
                taut_flags[k] = L > L0

    return {
        "coordinates": points,
        "converged": False,
        "reason": "max_iter",
        "iterations": max_iter,
        "residual_norm": r_norm,
    }
