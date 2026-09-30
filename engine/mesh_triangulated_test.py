# =============================================================================
# SDSe Engine - Triangulated Mesh Test
# =============================================================================
# Standalone test for engine/mesh_triangulated.py.
#
# Five boundary inputs. Same engine call for each.
# If any of the five fails, the method fails.
#
# Boundary inputs:
#   1. saddle:          two parabolic curves, two tips.
#   2. hexagon:         six vertices.
#   3. pointed_rounded: one tip, one parabolic curve.
#   4. irregular:       ten-vertex arbitrary polygon.
#   5. curved_quad:     four parabolic sides.
#
# For each: build the mesh, check no zero-area triangles,
# check the fixed_indices are valid, solve FDM, check
# the residual is machine-zero.
#
# History:
#   2026-09-30 - First build.
# =============================================================================

import numpy as np

from engine.mesh_triangulated import build_mesh_triangulated
from engine.form_finding import solve_fdm


# =============================================================================
# BOUNDARY BUILDERS
# =============================================================================

def _boundary_saddle():
    """
    Two parabolic curves meeting at two tips.
    Curve A (Beam L) and Curve B (Beam R). Closed loop.
    """
    span = 10.0
    rise = 3.0
    width = 4.0
    n = 15  # points per curve

    # Curve A: from far tip, along Beam L, to near tip.
    t = np.linspace(0.0, 1.0, n)
    xs = -span / 2.0 + span * t
    zs = rise * (1.0 - (2.0 * xs / span) ** 2)
    ys_A = -width * (1.0 - (2.0 * xs / span) ** 2)
    curve_A = np.column_stack([xs, ys_A, zs])

    # Curve B: from near tip, back along Beam R, to far tip.
    ys_B = width * (1.0 - (2.0 * xs / span) ** 2)
    curve_B = np.column_stack([xs[::-1], ys_B[::-1], zs[::-1]])

    # Loop: curve A forward, then curve B with first/last removed
    # (the tips are shared). So:
    #   loop = [A[0], A[1], ..., A[-1], B[1], ..., B[-2]]
    loop = np.vstack([curve_A, curve_B[1:-1]])
    return loop


def _boundary_hexagon():
    """Six vertices around a circle."""
    n = 6
    radius = 5.0
    angles = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    pts = np.column_stack([
        radius * np.cos(angles),
        radius * np.sin(angles),
        np.zeros(n),
    ])
    return pts


def _boundary_pointed_rounded():
    """
    One pointed face, one rounded face.
    Like a triangle but with one side bulging.

    Tip at (0, -5, 0). Rounded face from (-5, +3) to (+5, +3)
    bulging upward.
    """
    tip = np.array([[0.0, -5.0, 0.0]])
    n_arc = 14
    t = np.linspace(0.0, 1.0, n_arc)
    # Rounded face: parabolic bulge.
    xa = -5.0 + 10.0 * t
    ya = 3.0 + 1.5 * np.sin(np.pi * t)
    za = np.zeros(n_arc)
    arc = np.column_stack([xa, ya, za])
    # Loop: tip, then arc (not closing back to tip with the last arc
    # point; the loop wraps naturally).
    loop = np.vstack([tip, arc])
    return loop


def _boundary_irregular():
    """An arbitrary 10-vertex polygon."""
    pts = np.array([
        [0.0, 0.0, 0.0],
        [3.0, -0.5, 0.0],
        [5.0, 1.5, 0.0],
        [4.5, 4.0, 0.0],
        [2.0, 5.5, 0.0],
        [-0.5, 5.0, 0.0],
        [-2.5, 3.5, 0.0],
        [-3.0, 1.5, 0.0],
        [-2.0, -0.5, 0.0],
        [-1.0, -1.5, 0.0],
    ])
    return pts


def _boundary_curved_quad():
    """Four parabolic sides."""
    n = 10
    t = np.linspace(0.0, 1.0, n)

    # Side A: bottom, (-1, -1) to (1, -1), bulging down.
    side_A = np.column_stack([
        -1.0 + 2.0 * t,
        -1.0 - 0.3 * np.sin(np.pi * t),
        np.zeros(n),
    ])
    # Side B: right, (1, -1) to (1, 1), bulging right.
    side_B = np.column_stack([
        1.0 + 0.3 * np.sin(np.pi * t),
        -1.0 + 2.0 * t,
        np.zeros(n),
    ])
    # Side C: top, (1, 1) to (-1, 1), bulging up.
    side_C = np.column_stack([
        1.0 - 2.0 * t,
        1.0 + 0.3 * np.sin(np.pi * t),
        np.zeros(n),
    ])
    # Side D: left, (-1, 1) to (-1, -1), bulging left.
    side_D = np.column_stack([
        -1.0 - 0.3 * np.sin(np.pi * t),
        1.0 - 2.0 * t,
        np.zeros(n),
    ])

    # Loop: A forward, B minus first, C minus first, D minus first.
    loop = np.vstack([side_A, side_B[1:], side_C[1:], side_D[1:]])
    return loop


# =============================================================================
# TRIANGLE AREA CHECK
# =============================================================================

def _check_no_zero_area_triangles(points, triangles, label):
    """
    Compute the area of every triangle. Return (ok, min_area, count).
    """
    if len(triangles) == 0:
        print("  NO TRIANGLES PRODUCED")
        return False, 0.0, 0

    areas = np.zeros(len(triangles))
    for k, (a, b, c) in enumerate(triangles):
        p0 = points[a]
        p1 = points[b]
        p2 = points[c]
        areas[k] = 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0)))

    min_area = float(areas.min())
    zero_count = int(np.sum(areas < 1e-10))
    print("  triangles: %d" % len(triangles))
    print("  min tri area: %.4e" % min_area)
    print("  zero-area (<1e-10): %d" % zero_count)
    return (zero_count == 0), min_area, zero_count


# =============================================================================
# RUN ONE CASE
# =============================================================================

def _run_case(label, boundary):
    """
    Build the mesh, check it, solve it. Print a summary.
    """
    print("-" * 60)
    print("CASE: %s" % label)
    print("  boundary points: %d" % boundary.shape[0])

    try:
        result = build_mesh_triangulated(
            boundary_loop=boundary,
            warp_q=2000.0,
            weft_q=2000.0,
            edge_q=5000.0,
        )
    except Exception as e:
        print("  BUILD FAILED: %s" % str(e))
        return {"label": label, "ok": False, "reason": "build failed"}

    diag = result["diagnostics"]
    points = result["points"]
    edges = result["edges"]
    triangles = result["triangles"]
    fixed = result["fixed_indices"]
    q = result["q"]

    print("  nodes: %d" % diag["n_nodes"])
    print("  edges: %d" % diag["n_edges"])
    print("  triangles: %d" % diag["n_triangles"])
    print("  fixed: %d" % diag["n_fixed"])
    print("  free : %d" % diag["n_free"])

    # Fixed index range check.
    n_nodes = points.shape[0]
    for fi in fixed:
        if fi < 0 or fi >= n_nodes:
            print("  FIXED INDEX OUT OF RANGE: %d" % fi)
            return {"label": label, "ok": False,
                    "reason": "fixed index out of range"}

    # Zero-area check.
    area_ok, min_area, zero_count = _check_no_zero_area_triangles(
        points, triangles, label
    )

    # FDM solve.
    try:
        res = solve_fdm(points, edges, fixed, q)
    except Exception as e:
        print("  SOLVE FAILED: %s" % str(e))
        return {"label": label, "ok": False, "reason": "solve failed"}

    print("  FDM residual: %.4e" % res["residual_norm"])

    ok = area_ok and (res["residual_norm"] < 1e-9)
    return {
        "label": label,
        "ok": ok,
        "min_area": min_area,
        "zero_count": zero_count,
        "residual": res["residual_norm"],
    }





# =============================================================================
# RUNNER
# =============================================================================

def run_all():
    """Run all five boundary cases. Returns True if all pass."""
    print("=" * 60)
    print("Triangulated Mesh Engine - standalone test")
    print("=" * 60)

    cases = [
        ("saddle", _boundary_saddle()),
        ("hexagon", _boundary_hexagon()),
        ("pointed_rounded", _boundary_pointed_rounded()),
        ("irregular", _boundary_irregular()),
        ("curved_quad", _boundary_curved_quad()),
    ]

    results = []
    for label, boundary in cases:
        r = _run_case(label, boundary)
        results.append(r)

    print("=" * 60)
    print("SUMMARY")
    for r in results:
        line = "  %-20s  %s" % (
            r["label"], "OK" if r.get("ok") else "FAIL"
        )
        if "min_area" in r:
            line += "  min_area=%.4e" % r["min_area"]
        if "residual" in r:
            line += "  residual=%.4e" % r["residual"]
        if "reason" in r:
            line += "  (%s)" % r["reason"]
        print(line)
    print("=" * 60)

    all_ok = all(r.get("ok", False) for r in results)
    print("TRIANGULATED MESH ENGINE: %s"
          % ("PASS" if all_ok else "FAIL"))
    print("-" * 60)
    return all_ok


# Alias for run_tests.py compatibility.
run = run_all


if __name__ == "__main__":
    run_all()





