# =============================================================================
# SDSe Engine - Tension-Field Extension for NFDM
# =============================================================================
# This module extends engine/nfdm.py with a tension-field projection
# step. It does NOT modify engine/nfdm.py. It reads the current
# configuration, computes the principal membrane stresses per
# triangle, and clamps compressive principal components to zero.
#
# Reference:
#   Pauletti, R. M. O. (2006). Natural Force Density Method.
#   Wagner, R. (1965). "Tension-field theory" (uniform shear
#   tension-field concept, applied here element-wise).
#
# Method:
#   For each triangle, from its current 3D coordinates:
#     1. Compute the local in-plane basis (t1, t2).
#     2. Compute the engineering (small-strain) or the
#        Green-Lagrange (finite-strain) strain. For the first
#        version we use the small-strain form, which is what
#        Pauletti's stress resultants are compatible with at
#        the near-equilibrium state after solve_nfdm converges.
#     3. Apply the plane-stress constitutive matrix to get the
#        in-plane stress components (s11, s22, s12).
#     4. Form the 2x2 stress tensor and eigendecompose it.
#     5. Clamp the principal stresses at zero, then rotate back.
#     6. Return the projected stress components AND a flag
#        indicating whether compression was detected.
#
# This module only projects. The re-equilibration loop lives in
# solve_nfdm_tension_field, which is added in the next chunk.
#
# Units: m, N/m^2 (stress resultant), m (thickness).
# =============================================================================

import numpy as np


EPS = 1e-12


# =============================================================================
# THE PROJECTION
# =============================================================================

def project_tension_field(sigma, tol=0.0):
    """
    Project a 2x2 in-plane stress tensor onto the tension-only
    (tension-field) admissible set.

    The projection is:
        sigma_TF = Q @ diag(max(s1, 0), max(s2, 0)) @ Q.T
    where (s1, s2) are the principal stresses of sigma and Q
    is the matrix of its principal directions.

    Parameters
    ----------
    sigma : (2, 2) array
        In-plane stress tensor [[s11, s12], [s12, s22]].
    tol : float
        Any principal stress greater than -tol and less than
        zero is treated as zero (numerical hygiene). Default 0.0.

    Returns
    -------
    sigma_tf : (2, 2) array
        The projected (tension-only) stress tensor.
    compression_found : bool
        True if at least one principal stress was negative
        before projection.
    s_principal : (2,) array
        The two principal stresses, sorted so that
        s_principal[0] <= s_principal[1].
    """
    sigma = np.asarray(sigma, dtype=float)
    if sigma.shape != (2, 2):
        raise ValueError(
            "project_tension_field: sigma must be (2, 2), got %s"
            % (sigma.shape,)
        )

    # Symmetric part only. A true in-plane stress tensor is
    # symmetric, but numerical assembly may leave a small
    # antisymmetric residue.
    sigma_sym = 0.5 * (sigma + sigma.T)

    # Eigen-decomposition of a symmetric 2x2 matrix.
    # np.linalg.eigh returns ascending eigenvalues.
    s_vals, Q = np.linalg.eigh(sigma_sym)

    compression_found = bool(np.any(s_vals < -tol))

    s_proj = np.maximum(s_vals, 0.0)

    sigma_tf = Q @ np.diag(s_proj) @ Q.T

    # Re-symmetrise (defensive; Q diag Q^T is symmetric in exact
    # arithmetic, but floating point may leave a 1e-17 residue).
    sigma_tf = 0.5 * (sigma_tf + sigma_tf.T)

    return sigma_tf, compression_found, s_vals


# =============================================================================
# THE HELPER: STRESS TENSOR TO (s11, s22, s12)
# =============================================================================

def tensor_to_components(sigma):
    """
    Convert a 2x2 stress tensor into the (s11, s22, s12)
    component triple used by engine/nfdm.py.

    Parameters
    ----------
    sigma : (2, 2) array

    Returns
    -------
    (s11, s22, s12) : tuple of float
    """
    sigma = np.asarray(sigma, dtype=float)
    return float(sigma[0, 0]), float(sigma[1, 1]), float(sigma[0, 1])


def components_to_tensor(s11, s22, s12):
    """
    Convert the (s11, s22, s12) component triple into a 2x2
    symmetric stress tensor.

    Parameters
    ----------
    s11, s22, s12 : float

    Returns
    -------
    sigma : (2, 2) array
    """
    return np.array([
        [s11, s12],
        [s12, s22],
    ], dtype=float)





