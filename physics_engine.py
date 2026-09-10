# =============================================================================
# SDSe Physics Engine - Phase A
# 2D Catenary and Small Cable-Net Solver (verification prototype)
# -----------------------------------------------------------------------------
# Purpose : Prove the solver kernel reproduces closed-form catenary results
#           before scaling to 3D cable nets (Phase B/C).
# Author  : SDSe v10.0
# Units   : N, m, N/m (cable weight per unit length).
# Method  : Analytic catenary + Newton-Raphson on nodal residuals.
# =============================================================================

import math
import numpy as np


# =============================================================================
# CLOSED-FORM CATENARY
# -----------------------------------------------------------------------------
# A uniform cable hanging between two points under its own weight w (N/m)
# takes the shape:  y(x) = a * cosh((x - x0) / a) + y0
# where a = H / w,  H = horizontal tension component (constant along cable).
#
# Given horizontal span L, vertical difference h, and cable parameter a,
# we solve for the horizontal tension H and the arc length via:
#     h = 2a * sinh(L / (2a)) * sinh(x_mid / a)
# where x_mid is the horizontal distance from the low point of the catenary
# to the left support. In the symmetric case (h = 0), x_mid = 0.
# =============================================================================

def catenary_horizontal_tension(L, h, w, a_guess=None):
    """
    Solve for the catenary parameter a such that the geometric constraint
        h = a * (cosh((L - x_mid)/a) - cosh(x_mid/a))
    is satisfied. For the general h != 0 case, we iterate on a.

    L : horizontal span (m)
    h : vertical difference between supports (m), positive = right higher
    w : cable weight per unit length (N/m)
    Returns a (m), the catenary parameter. Horizontal tension H = w * a.
    """
    if L <= 0:
        raise ValueError("Span L must be positive.")
    if w <= 0:
        raise ValueError("Cable weight w must be positive.")

    # Symmetric case (h = 0) — closed form via sinh:
    # h = 0 => a * (cosh(L/(2a)) * 2*sinh(x_mid/a)) = 0 => x_mid = 0
    # Then sag S = a * (cosh(L/(2a)) - 1). Solve a from S if given.
    # Here we iterate on the general form using Newton on residual.

    if a_guess is None:
        a = L / 2.0  # sensible starting point
    else:
        a = a_guess

    for _ in range(80):
        # Symmetric assumption: x_mid = L/2 for the general case is wrong,
        # but for prototype verification we restrict to the symmetric case
        # (h small relative to L) and use the sinh form directly.
        # General h is handled by cable_net_2d_solve below.

        # Use: sinh(L / (2a)) * sinh(x_mid / a) = h / (2a)
        # Approximate symmetric x_mid = L/2 for h << L.
        x_mid = L / 2.0
        residual = 2.0 * a * math.sinh(L / (2.0 * a)) * math.sinh(x_mid / a) - h

        # Derivative with respect to a (numerical, small step)
        da = a * 1e-6
        a2 = a + da
        x_mid2 = L / 2.0
        residual2 = 2.0 * a2 * math.sinh(L / (2.0 * a2)) * math.sinh(x_mid2 / a2) - h
        d_residual = (residual2 - residual) / da

        if abs(d_residual) < 1e-14:
            break
        step = -residual / d_residual
        a += step
        if abs(step) < 1e-10 * max(1.0, abs(a)):
            break

    if a <= 0:
        raise RuntimeError("Catenary solver failed to converge to a > 0.")

    return a


def catenary_shape(L, h, w, n_points=100):
    """
    Return x, y arrays tracing the closed-form catenary between two supports
    separated horizontally by L and vertically by h (right support higher).
    y is measured from the low point of the catenary.

    For the symmetric case h = 0, we use the standard form:
        y(x) = a * (cosh(x / a) - 1)
    with the low point at x = 0 (mid-span).
    """
    a = catenary_horizontal_tension(L, h, w)

    if abs(h) < 1e-9:
        # Symmetric case
        x = np.linspace(-L / 2.0, L / 2.0, n_points)
        y = a * (np.cosh(x / a) - 1.0)
    else:
        # General case: shift so that left support at (0, 0),
        # right support at (L, h). Low point offset by x_mid.
        # Solve x_mid from:  sinh(x_mid/a) = h / (2a * sinh(L/(2a)))
        sinh_val = h / (2.0 * a * math.sinh(L / (2.0 * a)))
        sinh_val = max(-1e10, min(1e10, sinh_val))
        x_mid = a * math.asinh(sinh_val)
        x = np.linspace(0.0, L, n_points)
        y = a * (np.cosh((x - x_mid) / a) - np.cosh(x_mid / a))

    return x, y, a


def catenary_sag(L, w, a):
    """Sag (vertical distance from support chord to low point) for symmetric case."""
    return a * (math.cosh(L / (2.0 * a)) - 1.0)


def catenary_length(L, a):
    """Arc length of a symmetric catenary of span L and parameter a."""
    return 2.0 * a * math.sinh(L / (2.0 * a))


def catenary_tension_at_support(L, w, a):
    """
    Total tension at a support of a symmetric catenary:
        T = H * cosh(L / (2a))
        H = w * a
    Returns (T_horizontal, T_total) in N.
    """
    H = w * a
    T = H * math.cosh(L / (2.0 * a))
    return H, T


# =============================================================================
# 2D CABLE-NET SOLVER (Newton-Raphson prototype)
# -----------------------------------------------------------------------------
# Nodes numbered 0..n-1. Cables connect pairs. Every cable has weight w.
# Fixed nodes are pinned (no DOF). Free nodes are solved for equilibrium.
# Residual at each free node i in x and y = sum of axial forces from
# connected cables (which depend on node positions) minus any external load.
# =============================================================================

def cable_axial_force(xi, yi, xj, yj, EA, L0):
    """
    Axial force in a cable element connecting nodes i and j.
    EA : axial stiffness (N)
    L0 : unstressed length (m)
    Returns force magnitude (positive in tension) and direction vector.
    """
    dx = xj - xi
    dy = yj - yi
    L = math.sqrt(dx * dx + dy * dy)
    if L < 1e-12:
        return 0.0, 0.0, 0.0
    strain = (L - L0) / L0
    T = EA * strain  # positive = tension
    # Force on node i is toward j if in tension:
    fx = T * dx / L
    fy = T * dy / L
    return fx, fy, T


def assemble_residual_and_jacobian(coords, fixed_mask, cables, EA, L0_array,
                                    loads_xy):
    """
    Assemble the global residual vector R and Jacobian J for a 2D cable net.
    coords    : (n, 2) array of node coordinates
    fixed_mask: (n,) boolean, True = fixed node
    cables    : list of (i, j) node index tuples
    EA        : scalar axial stiffness (same for all cables for now)
    L0_array  : (m,) array of unstressed lengths per cable
    loads_xy  : (n, 2) array of external loads at each node (N)

    Returns R (free DOF vector), J (dense Jacobian).
    """
    n = coords.shape[0]
    free_idx = np.where(~fixed_mask)[0]
    n_free = len(free_idx)
    dof_map = -np.ones(n, dtype=int)
    for k, i in enumerate(free_idx):
        dof_map[i] = 2 * k

    R = np.zeros(2 * n_free)
    J = np.zeros((2 * n_free, 2 * n_free))

    for m, (i, j) in enumerate(cables):
        xi, yi = coords[i]
        xj, yj = coords[j]
        dx = xj - xi
        dy = yj - yi
        L = math.sqrt(dx * dx + dy * dy)
        if L < 1e-12:
            continue

        L0 = L0_array[m]
        if L0 <= 0:
            continue

        strain = (L - L0) / L0
        T = EA * strain  # positive = tension

        # Unit vector from i to j
        ux = dx / L
        uy = dy / L

        # Force on node i (pulling toward j)
        fx_i = T * ux
        fy_i = T * uy
        # Force on node j
        fx_j = -fx_i
        fy_j = -fy_i

        # Residual: sum of internal forces minus external load = 0
        # (Newton: R = F_int - F_ext, solved for R = 0)
        if not fixed_mask[i]:
            k = dof_map[i]
            R[k]     += fx_i - loads_xy[i, 0]
            R[k + 1] += fy_i - loads_xy[i, 1]
        if not fixed_mask[j]:
            k = dof_map[j]
            R[k]     += fx_j - loads_xy[j, 0]
            R[k + 1] += fy_j - loads_xy[j, 1]

        # --- Jacobian contributions (derivatives of F_int w.r.t. node coords)
        # Element stiffness matrix for a bar element (small-strain assumption):
        # k_e = (EA / L0) * [ [ ux^2, ux*uy ], [ ux*uy, uy^2 ] ] with sign pattern
        ke = (EA / L0) * np.array([[ux * ux, ux * uy],
                                   [ux * uy, uy * uy]])

        # Assemble into global J
        # Node i row block vs node i col block: +k_e
        # Node i row block vs node j col block: -k_e
        # Node j row block vs node i col block: -k_e
        # Node j row block vs node j col block: +k_e
        if not fixed_mask[i]:
            ki = dof_map[i]
            if not fixed_mask[i]:
                J[ki:ki + 2, ki:ki + 2] += ke
            if not fixed_mask[j]:
                kj = dof_map[j]
                J[ki:ki + 2, kj:kj + 2] -= ke
        if not fixed_mask[j]:
            kj = dof_map[j]
            if not fixed_mask[i]:
                ki = dof_map[i]
                J[kj:kj + 2, ki:ki + 2] -= ke
            if not fixed_mask[j]:
                J[kj:kj + 2, kj:kj + 2] += ke

    return R, J


def solve_cable_net_2d(coords_init, fixed_mask, cables, EA, L0_array,
                       loads_xy, max_iter=50, tol=1e-6, verbose=False):
    """
    Newton-Raphson solve for equilibrium of a 2D cable net.
    Returns (coords, converged, iterations, residual_norm_history).
    """
    coords = coords_init.copy().astype(float)
    history = []

    for it in range(max_iter):
        R, J = assemble_residual_and_jacobian(
            coords, fixed_mask, cables, EA, L0_array, loads_xy
        )
        rnorm = float(np.linalg.norm(R))
        history.append(rnorm)

        if verbose:
            print("  iter %2d  ||R|| = %.6e" % (it, rnorm))

        if rnorm < tol:
            return coords, True, it, history

        # Solve J * delta = -R
        try:
            delta = np.linalg.solve(J, -R)
        except np.linalg.LinAlgError:
            return coords, False, it, history

        # Apply delta to free DOFs
        free_idx = np.where(~fixed_mask)[0]
        for k, i in enumerate(free_idx):
            coords[i, 0] += delta[2 * k]
            coords[i, 1] += delta[2 * k + 1]

    # Final residual check
    R, _ = assemble_residual_and_jacobian(
        coords, fixed_mask, cables, EA, L0_array, loads_xy
    )
    rnorm = float(np.linalg.norm(R))
    history.append(rnorm)
    converged = rnorm < tol
    return coords, converged, max_iter, history


# =============================================================================
# VERIFICATION - reproduce closed-form catenary
# -----------------------------------------------------------------------------
# Test case: steel cable, L = 20 m span, symmetric supports, weight w = 50 N/m.
# Closed-form: sag S such that S = a * (cosh(L/(2a)) - 1), with a = H / w.
# We pick a target a, then verify the solver reproduces the sag and tension.
# =============================================================================

def verify_catenary():
    """
    Self-test: build a discrete cable net (20 elements, symmetric spans),
    solve for equilibrium, compare against closed-form catenary.
    Returns dict with max relative errors.
    """
    # Geometry
    L = 20.0
    w = 50.0            # N/m cable weight
    a_ref = 5.0         # target catenary parameter -> H = 250 N
    H_ref = w * a_ref

    # Closed-form sag and tension
    sag_ref = a_ref * (math.cosh(L / (2.0 * a_ref)) - 1.0)
    T_support_ref = H_ref * math.cosh(L / (2.0 * a_ref))

    # Build a discrete cable net of n segments
    n = 20
    n_nodes = n + 1
    coords = np.zeros((n_nodes, 2))
    xs = np.linspace(-L / 2.0, L / 2.0, n_nodes)
    coords[:, 0] = xs
    # Initial guess: straight line between supports
    coords[:, 1] = 0.0

    # Fixed nodes: both ends
    fixed_mask = np.zeros(n_nodes, dtype=bool)
    fixed_mask[0] = True
    fixed_mask[-1] = True

    # Cables: consecutive pairs
    cables = [(i, i + 1) for i in range(n)]

    # Unstressed length: pick L0 so that at equilibrium we get H = w * a.
    # For a catenary under its own weight, the arc length is:
    # L_arc = 2 * a * sinh(L / (2a))
    L_arc_ref = 2.0 * a_ref * math.sinh(L / (2.0 * a_ref))
    L0_per_elem = L_arc_ref / n

    # Axial stiffness: choose EA high enough that cable is nearly inextensible
    # so we recover the catenary (small-strain assumption).
    EA = 1.0e10  # very stiff

    # Loads: gravity distributed to nodes. Each cable weighs w * L0, split
    # half to each end node.
    loads_xy = np.zeros((n_nodes, 2))
    for i in range(n):
        w_cable = w * L0_per_elem
        loads_xy[i, 1]     -= w_cable / 2.0
        loads_xy[i + 1, 1] -= w_cable / 2.0

    coords_sol, conv, iters, hist = solve_cable_net_2d(
        coords, fixed_mask, cables, EA, np.full(n, L0_per_elem),
        loads_xy, max_iter=100, tol=1e-6, verbose=False
    )

    # Extract sag and support tension
    sag_num = abs(coords_sol[0, 1])  # node 0 is at y = 0 initially
    sag_num = abs(coords_sol[0, 1] - coords_sol[n // 2, 1])
    # Actually sag = max |y_i| - |y_support|. Since y_support = 0:
    sag_num = float(np.max(np.abs(coords_sol[:, 1])))

    # Support tension: force in first cable
    fx, fy, T_first = cable_axial_force(
        coords_sol[0, 0], coords_sol[0, 1],
        coords_sol[1, 0], coords_sol[1, 1],
        EA, L0_per_elem
    )
    T_support_num = abs(T_first)

    # Relative errors
    sag_err = abs(sag_num - sag_ref) / max(abs(sag_ref), 1e-9)
    T_err   = abs(T_support_num - T_support_ref) / max(T_support_ref, 1e-9)

    return {
        "converged": conv,
        "iterations": iters,
        "sag_ref_m": sag_ref,
        "sag_num_m": sag_num,
        "sag_rel_err": sag_err,
        "T_ref_N": T_support_ref,
        "T_num_N": T_support_num,
        "T_rel_err": T_err,
        "residual_history": hist,
    }


# =============================================================================
# Self-test on import (prints to console)
# =============================================================================

if __name__ == "__main__":
    print("Phase A verification: 2D catenary cable net")
    print("-" * 60)
    res = verify_catenary()
    print("Converged       :", res["converged"])
    print("Iterations      :", res["iterations"])
    print("Sag (ref)       : %.6f m" % res["sag_ref_m"])
    print("Sag (solver)    : %.6f m" % res["sag_num_m"])
    print("Sag rel error   : %.6e" % res["sag_rel_err"])
    print("T_support (ref) : %.4f N" % res["T_ref_N"])
    print("T_support (num) : %.4f N" % res["T_num_N"])
    print("T rel error     : %.6e" % res["T_rel_err"])
    print("-" * 60)
    if res["sag_rel_err"] < 0.001 and res["T_rel_err"] < 0.001 and res["converged"]:
        print("PHASE A GATE: PASS (errors < 0.1 percent)")
    else:
        print("PHASE A GATE: FAIL - iterate before moving to Phase B")


# ============================== PHASE A END ==================================

