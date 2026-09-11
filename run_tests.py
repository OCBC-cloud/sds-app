# =============================================================================
# SDSe - Test runner
# =============================================================================
# Runs the engine tests. Called by GitHub Actions on every push.
# Add new test functions here as we build more engine modules.
# =============================================================================

import sys

from engine.membrane import _verify_mesh_handling


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


def main():
    all_pass = True

    # Add new test calls here as we build more modules
    if not test_membrane_mesh():
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
