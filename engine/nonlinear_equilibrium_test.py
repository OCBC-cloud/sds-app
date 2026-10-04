# =============================================================================
# SDSe Engine - Nonlinear Equilibrium Test Wrapper
# =============================================================================
# Standalone test runner for engine/nonlinear_equilibrium.py.
#
# The heavy lifting is in nonlinear_equilibrium.run_all_tests().
# This file exists so run_tests.py has a stable import path and
# so the module can be exercised on its own from the command line.
#
# History:
#   2026-10-04 - First build.
# =============================================================================

from engine.nonlinear_equilibrium import run_all_tests


def run_all():
    """Entry point used by run_tests.py. Returns True if all pass."""
    print("=" * 60)
    print("TEST: engine/nonlinear_equilibrium.py")
    print("=" * 60)
    ok = run_all_tests()
    print("-" * 60)
    if ok:
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")
    return ok


# Alias for run_tests.py compatibility.
run = run_all


if __name__ == "__main__":
    run_all()
