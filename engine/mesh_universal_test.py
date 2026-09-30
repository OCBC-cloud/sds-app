# =============================================================================
# SDSe Engine - Universal Mesh Builder Test
# =============================================================================
# Standalone test for engine/mesh_universal.py.
#
# Three topologies tested:
#   - twosided: a saddle boundary (two parabolic curves, two tips).
#   - ring:     a hexagon loop.
#   - quad:     a curved-boundary quad.
#
# Each test confirms:
#   - zero zero-area triangles,
#   - machine-zero FDM residual after solve_fdm,
#   - the tips / centre are single nodes where applicable.
#
# History:
#   2026-09-29 - First build. Three fills: tfi, polar, barycentric.
#   2026-09-30 - Rewritten for the topology API. Three topologies.
# =============================================================================

import numpy as np

from engine.mesh_universal import build_mesh_universal
from engine.form_finding import solve_fdm


# =============================================================================
# HELPERS
# =============================================================================

def _triangles_from_grid(grid, n_i, M):
    """Build a triangle list from an (n_i, M) grid of points."""
    tris = []
    for i in range(n_i - 1):
        for j in range(M - 1):
            a = i * M + j
            b = (i + 1) * M + j
            c = i * M + (j + 1)
            d = (i + 1) * M + (j + 1)
            tris.append((a, b, c))
            tris.append((b, d, c))
    return tris


def _tri_areas(points, tris):
    """Compute the area of each triangle. Returns an array."""
    areas = np.zeros(len(tris))
    for k, (a, b, c) in enumerate(tris):
        p0 = points[a]
        p1 = points[b]
        p2 = points[c]
        areas[k] = 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0)))
    return areas


def _solve_and_report(result, label):
    """Solve FDM on a built mesh and print diagnostics."""
    points = result["points"]
    edges = result["edges"]
    fixed = result["fixed_indices"]
    q = result["q"]
    diag = result["diagnostics"]

    print("  topology: %s" % diag["topology_used"])
    print("  n_i: %d  M: %d" % (diag["n_i"], diag["transverse_count"]))
    print("  nodes: %d" % diag["n_nodes"])
    print("  edges: %d" % diag["n_edges"])
    print("  fixed: %d" % diag["n_fixed"])
    print("  free : %d" % diag["n_free"])

    # Verify fixed indices are in range.
    n_nodes = points.shape[0]
    for fi in fixed:
        if fi < 0 or fi >= n_nodes:
            print("  FIXED INDEX OUT OF RANGE: %d" % fi)
            return {"ok": False, "reason": "fixed index out of range"}

    res = solve_fdm(points, edges, fixed, q)
    print("  FDM residual: %.4e" % res["residual_norm"])

    return res


# =============================================================================
# TEST 1: TWOSIDED (saddle)
# =============================================================================

def _test_twosided():
    """
    A two-sided saddle: two parabolic curves meeting at two tips.

    Curve A is the "bottom" (negative y side).
    Curve B is the "top" (positive y side).
    Tips are at the ends of the span.

    Confirm:
      - the two tips are single nodes (node 0 and node last),
      - zero zero-area triangles,
      - machine-zero residual.
    """
    span = 10.0
    rise = 3.0
    width = 4.0

    # Anchor positions along the span.
    n_anchors = 7
    xs = np.linspace(-span / 2.0, span / 2.0, n_anchors)

    # Parabolic rise.
    zs = rise * (1.0 - (2.0 * xs / span) ** 2)

    # Curve A: negative y. Curve B: positive y.
    # y width tapers to zero at the tips (the parabola in plan).
    ys_shape = width * (1.0 - (2.0 * xs / span) ** 2)
    curve_A = np.column_stack([xs, -ys_shape, zs])
    curve_B = np.column_stack([xs[::-1], ys_shape[::-1], zs[::-1]])

    # Tips.
    tip_P0 = curve_A[0]     # far tip
    tip_P1 = curve_A[-1]    # near tip

    # Segment types: all beam. Two curves of (n_anchors - 1) each.
    n_segments = (n_anchors - 1) * 2
    segment_types = ["beam"] * n_segments

    result = build_mesh_universal(
        topology="twosided",
        curves=[curve_A, curve_B],
        corner_points=[tip_P0, tip_P1],
        segment_types=segment_types,
        subdivisions_per_segment=5,
        transverse_count=8,
        warp_q=2000.0,
        weft_q=2000.0,
        edge_q=5000.0,
    )

    diag = result["diagnostics"]
    print("  n_interior: %d" % diag["topo_n_interior"])
    print("  tip_P0_idx: %d" % diag["topo_tip_P0_idx"])
    print("  tip_P1_idx: %d" % diag["topo_tip_P1_idx"])

    # Check: the tips are single nodes at the right indices.
    n_nodes = result["points"].shape[0]
    p0_ok = (diag["topo_tip_P0_idx"] == 0)
    p1_ok = (diag["topo_tip_P1_idx"] == n_nodes - 1)

    # Solve.
    res = _solve_and_report(result, "twosided")

    # Count zero-area triangles.
    n_i = diag["n_i"] - 2   # interior columns
    M = diag["transverse_count"]
    # Reconstruct a grid for triangle counting: nodes 1..1+n_i*M-1.
    # The tips are separate. Build triangles among the interior grid.
    interior = result["points"][1:n_nodes - 1]
    tris = []
    for i in range(n_i - 1):
        for j in range(M - 1):
            a = i * M + j
            b = (i + 1) * M + j
            c = i * M + (j + 1)
            d = (i + 1) * M + (j + 1)
            tris.append((a, b, c))
            tris.append((b, d, c))
    areas = _tri_areas(interior, tris)
    min_area = float(areas.min()) if len(areas) else 0.0
    zero_count = int(np.sum(areas < 1e-10))
    print("  interior triangles: %d" % len(tris))
    print("  min tri area: %.4e" % min_area)
    print("  zero-area (<1e-10): %d" % zero_count)

    ok = (
        p0_ok and p1_ok
        and zero_count == 0
        and res["residual_norm"] < 1e-9
    )
    return {"ok": ok, "label": "twosided"}





# =============================================================================
# TEST 2: RING (hexagon)
# =============================================================================

def _test_ring():
    """
    A hexagon loop. Six anchors around a circle.

    Confirm:
      - the centre is a single node,
      - zero zero-area triangles,
      - machine-zero residual.
    """
    n_anchors = 6
    radius = 5.0

    angles = np.linspace(0.0, 2.0 * np.pi, n_anchors, endpoint=False)
    curve_loop = np.column_stack([
        radius * np.cos(angles),
        radius * np.sin(angles),
        np.zeros(n_anchors),
    ])

    segment_types = ["beam"] * n_anchors

    result = build_mesh_universal(
        topology="ring",
        curves=[curve_loop],
        segment_types=segment_types,
        subdivisions_per_segment=5,
        transverse_count=8,
        warp_q=2000.0,
        weft_q=2000.0,
        edge_q=5000.0,
    )

    diag = result["diagnostics"]
    print("  has_centre: %s" % diag["has_centre"])
    print("  centre_idx: %d" % diag["centre_idx"])

    n_nodes = result["points"].shape[0]
    centre_ok = (diag["centre_idx"] == n_nodes - 1)

    res = _solve_and_report(result, "ring")

    # Zero-area triangles: reconstruct ring triangles.
    n_i = diag["n_i"]
    M = diag["transverse_count"]
    centre_idx = diag["centre_idx"]
    points = result["points"]
    tris = []
    for i in range(n_i):
        i_next = (i + 1) % n_i
        for j in range(M - 1):
            a = i * (M - 1) + j
            b = i_next * (M - 1) + j
            if j + 1 < M - 1:
                c = i * (M - 1) + (j + 1)
                d = i_next * (M - 1) + (j + 1)
                tris.append((a, b, c))
                tris.append((b, d, c))
            else:
                # Innermost ring to centre.
                tris.append((a, b, centre_idx))
    areas = _tri_areas(points, tris)
    min_area = float(areas.min()) if len(areas) else 0.0
    zero_count = int(np.sum(areas < 1e-10))
    print("  ring triangles: %d" % len(tris))
    print("  min tri area: %.4e" % min_area)
    print("  zero-area (<1e-10): %d" % zero_count)

    ok = (
        centre_ok
        and zero_count == 0
        and res["residual_norm"] < 1e-9
    )
    return {"ok": ok, "label": "ring"}


# =============================================================================
# TEST 3: QUAD (curved sides)
# =============================================================================

def _test_quad():
    """
    A curved quad: four parabolic sides forming a domed region.

    The four corners are at (+-1, +-1). Each side is a parabola
    bulging outward.

    Confirm:
      - zero zero-area triangles,
      - machine-zero residual,
      - the Coons patch fills correctly.
    """
    n_side = 5   # anchors per side

    # Side A: bottom, from (-1, -1) to (1, -1), bulging down.
    t = np.linspace(0.0, 1.0, n_side)
    side_A = np.column_stack([
        -1.0 + 2.0 * t,
        -1.0 - 0.3 * np.sin(np.pi * t),
        np.zeros(n_side),
    ])
    # Side C: top, from (1, 1) to (-1, 1), bulging up.
    side_C = np.column_stack([
        1.0 - 2.0 * t,
        1.0 + 0.3 * np.sin(np.pi * t),
        np.zeros(n_side),
    ])
    # Side D: left, from (-1, 1) to (-1, -1), bulging left.
    side_D = np.column_stack([
        -1.0 - 0.3 * np.sin(np.pi * t),
        1.0 - 2.0 * t,
        np.zeros(n_side),
    ])
    # Side B: right, from (1, -1) to (1, 1), bulging right.
    side_B = np.column_stack([
        1.0 + 0.3 * np.sin(np.pi * t),
        -1.0 + 2.0 * t,
        np.zeros(n_side),
    ])

    # Corners: P00 = A[0], P10 = A[-1], P11 = C[-1], P01 = C[0]
    P00 = side_A[0]
    P10 = side_A[-1]
    P11 = side_C[-1]
    P01 = side_C[0]

    n_segments = (n_side - 1) * 4
    segment_types = ["beam"] * n_segments

    result = build_mesh_universal(
        topology="quad",
        curves=[side_A, side_B, side_C, side_D],
        corner_points=[P00, P10, P11, P01],
        segment_types=segment_types,
        subdivisions_per_segment=5,
        transverse_count=8,
        warp_q=2000.0,
        weft_q=2000.0,
        edge_q=5000.0,
    )

    diag = result["diagnostics"]
    res = _solve_and_report(result, "quad")

    n_i = diag["n_i"]
    M = diag["transverse_count"]
    points = result["points"]
    tris = _triangles_from_grid(points.reshape((n_i, M, 3)), n_i, M)
    areas = _tri_areas(points, tris)
    min_area = float(areas.min()) if len(areas) else 0.0
    zero_count = int(np.sum(areas < 1e-10))
    print("  quad triangles: %d" % len(tris))
    print("  min tri area: %.4e" % min_area)
    print("  zero-area (<1e-10): %d" % zero_count)

    ok = (
        zero_count == 0
        and res["residual_norm"] < 1e-9
    )
    return {"ok": ok, "label": "quad"}


# =============================================================================
# RUNNER
# =============================================================================

def run_all():
    """Run all three topology tests. Returns True if all pass."""
    print("=" * 60)
    print("Universal Mesh Engine - standalone test")
    print("=" * 60)

    results = []
    for test in (_test_twosided, _test_ring, _test_quad):
        print("-" * 60)
        print("CASE: %s" % test.__name__)
        try:
            r = test()
        except Exception as e:
            print("  EXCEPTION: %s" % str(e))
            r = {"ok": False, "label": test.__name__}
        print("  result: %s" % ("OK" if r["ok"] else "FAIL"))
        results.append(r)

    print("=" * 60)
    print("SUMMARY")
    for r in results:
        print("  %-20s  %s" % (r["label"], "OK" if r["ok"] else "FAIL"))
    print("=" * 60)

    all_ok = all(r["ok"] for r in results)
    print("UNIVERSAL MESH ENGINE: %s" % ("PASS" if all_ok else "FAIL"))
    print("-" * 60)
    return all_ok


if __name__ == "__main__":
    run_all()
run = run_all




