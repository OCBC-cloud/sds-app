# =============================================================================
# SDSe Engine - Tests for engine/nfdm_tension_field.py
# =============================================================================
# Six tests for the tension-field projection.
#
# Each test is a physical statement about the projection, not just
# a numerical check:
#
#   1. Pure tension       -> unchanged. Tension is admissible.
#   2. Pure compression   -> zero. Compression is not admissible.
#   3. Pure shear         -> rank-one tension field.
#   4. Biaxial tension    -> unchanged. Both principals positive.
#   5. Mixed              -> keeps the tensile principal only.
#   6. Helper round-trip  -> tensor -> components -> tensor.
#
# Written against engine/nfdm_tension_field.py as it actually is.
# It imports project_tension_field, tensor_to_components,
# components_to_tensor. Nothing else.
#
# History:
#   2026-10-02 - first written. Clobbered after commit.
#   2026-10-03 - rewritten from PROJECT_SESSION_LOG.md.
# =============================================================================

import numpy as np

from engine.nfdm_tension_field import (
    project_tension_field,
    tensor_to_components,
    components_to_tensor,
)


TOL = 1e-9


# =============================================================================
# TEST 1 - Pure tension, unchanged
# =============================================================================

def _test_pure_tension():
    """
    A pure uniaxial tension state has both principals >= 0.
    The projection is the identity. The compression flag is
    False.
    """
    sigma = np.array([[10.0, 0.0],
                      [0.0,  0.0]])
    sigma_tf, comp, s = project_tension_field(sigma)

    ok_tensor = np.allclose(sigma_tf, sigma, atol=TOL)
    ok_flag = (comp is False)
    ok_principal = (s[0] >= -TOL) and (s[1] >= -TOL)

    return ok_tensor and ok_flag and ok_principal


# =============================================================================
# TEST 2 - Pure compression, removed
# =============================================================================

def _test_pure_compression():
    """
    A pure compression state has both principals <= 0.
    The projection returns the zero tensor. The compression
    flag is True.
    """
    sigma = np.array([[-10.0, 0.0],
                      [  0.0, 0.0]])
    sigma_tf, comp, s = project_tension_field(sigma)

    ok_tensor = np.allclose(sigma_tf, np.zeros((2, 2)), atol=TOL)
    ok_flag = (comp is True)
    ok_principal = (s[0] < 0.0) and (abs(s[1]) < TOL)

    return ok_tensor and ok_flag and ok_principal


# =============================================================================
# TEST 3 - Pure shear, rank-one tension field
# =============================================================================

def _test_pure_shear():
    """
    A pure shear state has principals +tau and -tau. After the
    projection, only the tensile principal survives. The result
    is a rank-one tensor: det(sigma_tf) == 0, and the direction
    of the remaining principal is the 45-degree direction.
    """
    tau = 5.0
    sigma = np.array([[0.0, tau],
                      [tau, 0.0]])
    sigma_tf, comp, s = project_tension_field(sigma)

    # Determinant is zero: rank-one.
    det = float(np.linalg.det(sigma_tf))
    ok_rank = abs(det) < TOL

    # Principal stresses: one is +tau, the other is 0.
    ok_principal = (
        abs(s[0] + tau) < TOL and
        abs(s[1] - tau) < TOL
    )

    # Compression was found (the -tau principal).
    ok_flag = (comp is True)

    # Trace of the projected tensor equals tau (only the +tau
    # principal survives).
    ok_trace = abs(float(np.trace(sigma_tf)) - tau) < TOL

    return ok_rank and ok_principal and ok_flag and ok_trace







# =============================================================================
# TEST 4 - Biaxial tension, unchanged
# =============================================================================

def _test_biaxial_tension():
    """
    Both principals positive. The projection is the identity.
    """
    sigma = np.array([[8.0, 0.0],
                      [0.0, 3.0]])
    sigma_tf, comp, s = project_tension_field(sigma)

    ok_tensor = np.allclose(sigma_tf, sigma, atol=TOL)
    ok_flag = (comp is False)
    ok_principal = (s[0] >= -TOL) and (s[1] >= -TOL)

    return ok_tensor and ok_flag and ok_principal


# =============================================================================
# TEST 5 - Mixed tension and compression
# =============================================================================

def _test_mixed():
    """
    One principal positive, one negative. The projection keeps
    the tensile principal only. The result is rank-one, and its
    trace equals the tensile principal.
    """
    sigma = np.array([[ 6.0, 2.0],
                      [ 2.0, -1.0]])
    sigma_tf, comp, s = project_tension_field(sigma)

    # Compression was found.
    ok_flag = (comp is True)

    # The tensile principal is s[1] (ascending order).
    s_pos = s[1]
    ok_principal = (s_pos > 0.0) and (s[0] < 0.0)

    # Rank-one.
    det = float(np.linalg.det(sigma_tf))
    ok_rank = abs(det) < TOL

    # Trace of the projection equals the surviving principal.
    ok_trace = abs(float(np.trace(sigma_tf)) - s_pos) < TOL

    # The projected tensor is symmetric.
    ok_sym = np.allclose(sigma_tf, sigma_tf.T, atol=TOL)

    return ok_flag and ok_principal and ok_rank and ok_trace and ok_sym


# =============================================================================
# TEST 6 - Helper round-trip
# =============================================================================

def _test_helpers():
    """
    tensor -> components -> tensor must be the identity.
    Also: the components returned by tensor_to_components must
    be (s11, s22, s12), matching the order engine/nfdm.py uses.
    """
    s11, s22, s12 = 3.0, 7.0, 2.0
    sigma = components_to_tensor(s11, s22, s12)

    # Shape and symmetry.
    if sigma.shape != (2, 2):
        return False
    if not np.allclose(sigma, sigma.T, atol=TOL):
        return False

    # Round-trip.
    c11, c22, c12 = tensor_to_components(sigma)
    ok_values = (
        abs(c11 - s11) < TOL and
        abs(c22 - s22) < TOL and
        abs(c12 - s12) < TOL
    )

    # Order check: sigma[0,0] is s11, sigma[1,1] is s22,
    # sigma[0,1] is s12.
    ok_order = (
        abs(sigma[0, 0] - s11) < TOL and
        abs(sigma[1, 1] - s22) < TOL and
        abs(sigma[0, 1] - s12) < TOL
    )

    return ok_values and ok_order


# =============================================================================
# RUNNER
# =============================================================================

def _run_all():
    """
    Run all six tests. Print a short report. Return True if all
    pass, False otherwise.
    """
    tests = [
        ("1. Pure tension  -> unchanged",         _test_pure_tension),
        ("2. Pure compress -> zero",              _test_pure_compression),
        ("3. Pure shear    -> rank-one",          _test_pure_shear),
        ("4. Biaxial tens  -> unchanged",         _test_biaxial_tension),
        ("5. Mixed         -> keeps tensile part", _test_mixed),
        ("6. Helper round-trip",                  _test_helpers),
    ]

    all_pass = True
    for label, fn in tests:
        try:
            ok = bool(fn())
        except Exception as e:
            ok = False
            print("  " + label + ": EXCEPTION - " + str(e))
        else:
            print("  " + label + ": " + ("PASS" if ok else "FAIL"))
        if not ok:
            all_pass = False

    return all_pass
