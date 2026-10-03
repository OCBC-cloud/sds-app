# =============================================================================
# SDSe - Test runner
# =============================================================================
# Runs the engine tests. Called by GitHub Actions on every push.
# Add new test functions here as we build more engine modules.
#
# Updated 2026-10-03:
#   - Fixed the __main__ guard. It was indented inside main(),
#     so running this file as a script defined main() and then
#     exited without calling it. The CI was green because the
#     tests were never actually running.
#   - Removed test_mesh_universal(). It is dead code.
#
# Updated 2026-09-30:
#   - Switched to the triangulated mesh engine test.
#     The universal (structured) engine test remains in
#     the file, unused, until the old engine is deleted.
#   - Added the universal mesh engine test.
#
# Updated 2026-09-27:
#   - Added the standalone hypar benchmark. This is NOT wired into
#     the app. It runs here so that GitHub Actions produces a
#     reproducible log of the comparison between our linear FDM
#     solver and the SDS-CONST Benchmark 001 reference.
#
# Updated 2026-09-25:
#   - Removed the MBS engine test. It runs for minutes, and
#     GitHub Actions cancels the job before completion. The
#     test will be re-added once the MBS engine is proven in
#     the app, with a smaller mesh that runs in seconds.
# =============================================================================

import sys

from engine.membrane import _verify_mesh_handling
from engine.form_finding import _verify_form_finding


def test_membrane_mesh():
    """Run the membrane mesh handling test. Returns True if pass."""
    print("=" * 60)
    print("TEST: engine/membrane.py - mesh handling")
    print("=" * 60)
    res = _verify_mesh_handling()
    for key, val in res.items():
        print("  " + str(key) + ": " + str(val))
    print("-" * 60)
    if res["pass"]:
        print("RESULT: PASS")
        return True
    else:
        print("RESULT: FAIL")
        return False


def test_form_finding():
    """Run the FDM form-finding test. Returns True if pass."""
    print("=" * 60)
    print("TEST: engine/form_finding.py - FDM kernel")
    print("=" * 60)
    res = _verify_form_finding()
    for key, val in res.items():
        print("  " + str(key) + ": " + str(val))
    print("-" * 60)
    if res["pass"]:
        print("RESULT: PASS")
        return True
    else:
        print("RESULT: FAIL")
        return False


def test_hypar_benchmark():
    """
    Run the standalone hypar benchmark.

    This is NOT wired into the app. It runs here so that GitHub
    Actions produces a reproducible log of the comparison between
    our linear FDM solver and the SDS-CONST Benchmark 001 reference.
    """
    print("=" * 60)
    print("BENCHMARK: hypar (SDS-CONST Benchmark 001 reconstruction)")
    print("=" * 60)
    try:
        import benchmark_hypar
        benchmark_hypar.run()
        print("RESULT: COMPLETED (comparison output above)")
        print("-" * 60)
        return True
    except Exception as e:
        print("RESULT: FAIL")
        print("  " + str(e))
        print("-" * 60)
        return False
        

def test_mesh_triangulated():
    """Run the triangulated mesh engine test. Returns True if pass."""
    print("=" * 60)
    print("TEST: engine/mesh_triangulated.py - triangulated mesh engine")
    print("=" * 60)
    try:
        from engine.mesh_triangulated_test import run
        ok = run()
        print("-" * 60)
        if ok:
            print("RESULT: PASS")
            return True
        else:
            print("RESULT: FAIL")
            return False
    except Exception as e:
        print("RESULT: FAIL")
        print("  " + str(e))
        print("-" * 60)
        return False


def test_nfdm_tension_field():
    """Run the NFDM tension-field projection test. Returns True if pass."""
    print("=" * 60)
    print("TEST: engine/nfdm_tension_field.py - tension-field projection")
    print("=" * 60)
    try:
        from engine.nfdm_tension_field_test import _run_all
        ok = _run_all()
        print("-" * 60)
        if ok:
            print("RESULT: PASS")
            return True
        else:
            print("RESULT: FAIL")
            return False
    except Exception as e:
        print("RESULT: FAIL")
        print("  " + str(e))
        print("-" * 60)
        return False


def main():
    all_pass = True

    # Add new test calls here as we build more modules
    if not test_membrane_mesh():
        all_pass = False
    if not test_form_finding():
        all_pass = False
    if not test_hypar_benchmark():
        all_pass = False
    if not test_mesh_triangulated():
        all_pass = False
    if not test_nfdm_tension_field():
        all_pass = False

    print()
    print("=" * 60)
    if all_pass:
        print("ALL TESTS PASS")
        sys.exit(0)
    else:
        print("ONE OR MORE TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()


# =============================================================================
# END OF run_tests.py
# =============================================================================
