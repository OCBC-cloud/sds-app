# =============================================================================
# SDSe - Test runner
# =============================================================================
# Runs the engine tests. Called by GitHub Actions on every push.
# Add new test functions here as we build more engine modules.
# =============================================================================

import sys

import numpy as np

from engine.membrane import _verify_mesh_handling
from engine.form_finding import _verify_form_finding
from engine.membrane_boundary import build_mesh, build_and_solve


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


def test_mbs_engine():
    """
    Run the Membrane Boundary Schema engine test.

    Builds a simple square boundary with four anchors and
    all-cable edges. Calls the engine. Solves with FDM.
    Reports node count, triangle areas, residual.

    The test passes if the mesh has positive node and edge
    counts, no zero-area triangles, and a finite residual.
    """
    print("=" * 60)
    print("TEST: engine/membrane_boundary.py - MBS engine")
    print("=" * 60)

    # ---- Simple square boundary: 4 corners, all-cable edges.
    # Boundary is a closed loop, first point != last point.
    # Corners in order: SW, SE, NE, NW.
    corners = np.array([
        [ 2.0,  2.0, 2.0],   # 2: NE, high
        [-2.0,  2.0, 2.0],   # 3: NW, high
    ], dtype=float)

    # For a simple test we give the engine each corner as a
    # distinct boundary point. Anchors are all four corners.
    anchor_indices = [0, 1, 2, 3]
    edge_types = ["cable", "cable", "cable", "cable"]

    nx = 9
    ny = 9

    try:
        mesh = build_mesh(
            boundary=corners,
            anchor_indices=anchor_indices,
            edge_types=edge_types,
            nx=nx, ny=ny,
            membrane_q=1.0,
            cable_q=1.0,
        )
    except Exception as e:
        print("  build_mesh raised: " + str(e))
        print("-" * 60)
        print("RESULT: FAIL")
        return False

    n_nodes = mesh["diagnostics"]["n_nodes"]
    n_edges = mesh["diagnostics"]["n_edges"]
    n_fixed = mesh["diagnostics"]["n_fixed"]
    n_free = mesh["diagnostics"]["n_free"]

    print("  n_nodes        : " + str(n_nodes))
    print("  n_edges        : " + str(n_edges))
    print("  n_fixed        : " + str(n_fixed))
    print("  n_free         : " + str(n_free))

    # ---- Compute minimum triangle area of the initial mesh.
    # Split each quad into two triangles.
    points = mesh["points"]
    min_area = float("inf")
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            b = (i + 1) * ny + j
            c = i * ny + (j + 1)
            d = (i + 1) * ny + (j + 1)
            for tri in ((a, b, c), (b, d, c)):
                p0 = points[tri[0]]
                p1 = points[tri[1]]
                p2 = points[tri[2]]
                area = 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0)))
                if area < min_area:
                    min_area = area
    print("  min_tri_area   : " + ("%.6e" % min_area))

    # ---- Solve with FDM.
    try:
        result = build_and_solve(
            boundary=corners,
            anchor_indices=anchor_indices,
            edge_types=edge_types,
            nx=nx, ny=ny,
            membrane_q=1.0,
            cable_q=1.0,
        )
        residual = float(result["solve_result"]["residual_norm"])
        print("  residual_norm  : " + ("%.6e" % residual))
    except Exception as e:
        print("  build_and_solve raised: " + str(e))
        print("-" * 60)
        print("RESULT: FAIL")
        return False

    # ---- Pass criteria.
    pass_ok = (
        n_nodes > 0
        and n_edges > 0
        and n_fixed > 0
        and n_free > 0
        and min_area > 1e-9
        and np.isfinite(residual)
    )

    print("-" * 60)
    if pass_ok:
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
    if not test_form_finding():
        all_pass = False
    if not test_mbs_engine():
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





