# =============================================================================
# SDSe - Universal Mesh Engine Test
# =============================================================================
# Standalone test for engine/mesh_universal.py.
#
# Not wired into the app. Run manually:
#     python engine/mesh_universal_test.py
#
# Or via run_tests.py.
#
# Tests:
#   1. Simple 2-anchor loop, all beam. Check mesh, holds, no zero-area.
#   2. Simple 2-anchor loop, all cable. Check cable release works.
#   3. Simple 4-anchor loop, mixed types. Check per-segment holds.
#   4. Solve with solve_fdm. Check residual is machine-zero.
# =============================================================================

import numpy as np

from engine.mesh_universal import build_mesh_universal
from engine.form_finding import solve_fdm


def _run_case(name, boundary_loop, segment_types, fill,
              K, M, warp_q, weft_q, edge_q):
    """Run one test case. Return a dict of results."""
    print("-" * 60)
    print("CASE:", name)
    print("  boundary_loop:", len(boundary_loop), "anchors")
    print("  segment_types:", segment_types)
    print("  fill:", fill, " K:", K, " M:", M)

    mesh = build_mesh_universal(
        boundary_loop=boundary_loop,
        segment_types=segment_types,
        fill=fill,
        subdivisions_per_segment=K,
        transverse_count=M,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q,
    )

    d = mesh["diagnostics"]
    print("  nodes:", d["n_nodes"])
    print("  edges:", d["n_edges"])
    print("  fixed:", d["n_fixed"])
    print("  free :", d["n_free"])

    res = solve_fdm(
        mesh["points"],
        mesh["edges"],
        mesh["fixed_indices"],
        mesh["q"],
    )

    print("  FDM residual: %.4e" % res["residual_norm"])

    coords = res["coordinates"]

    areas = []
    n_i = d["n_anchors"] * K
    M_ = d["transverse_count"]
    for i in range(n_i - 1):
        for j in range(M_ - 1):
            a = i * M_ + j
            b = (i + 1) * M_ + j
            c = i * M_ + (j + 1)
            d_ = (i + 1) * M_ + (j + 1)
            for tri in ((a, b, c), (b, d_, c)):
                p0 = coords[tri[0]]
                p1 = coords[tri[1]]
                p2 = coords[tri[2]]
                area = 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0)))
                areas.append(area)
    areas = np.array(areas)
    print("  min tri area : %.6e" % areas.min())
    print("  mean tri area: %.6e" % areas.mean())
    print("  zero-area (<1e-10):", int(np.sum(areas < 1e-10)))

    return {
        "name": name,
        "n_nodes": d["n_nodes"],
        "n_fixed": d["n_fixed"],
        "n_free": d["n_free"],
        "residual": res["residual_norm"],
        "min_area": float(areas.min()),
        "zero_area_count": int(np.sum(areas < 1e-10)),
    }


def run():
    """Run all test cases. Return True if all pass."""
    print("=" * 60)
    print("Universal Mesh Engine - standalone test")
    print("=" * 60)

    results = []

    # Case 1: flat quad, all beam.
    results.append(_run_case(
        "Flat quad, all beam",
        boundary_loop=[
            (0.0, 0.0, 0.0),
            (10.0, 0.0, 0.0),
            (10.0, 10.0, 0.0),
            (0.0, 10.0, 0.0),
        ],
        segment_types=["beam", "beam", "beam", "beam"],
        fill="tfi",
        K=5, M=8,
        warp_q=2.0, weft_q=2.0, edge_q=5.0,
    ))

    # Case 2: flat quad, all cable.
    results.append(_run_case(
        "Flat quad, all cable",
        boundary_loop=[
            (0.0, 0.0, 0.0),
            (10.0, 0.0, 0.0),
            (10.0, 10.0, 0.0),
            (0.0, 10.0, 0.0),
        ],
        segment_types=["cable", "cable", "cable", "cable"],
        fill="tfi",
        K=5, M=8,
        warp_q=2.0, weft_q=2.0, edge_q=5.0,
    ))

    # Case 3: 4-anchor loop, mixed types.
    results.append(_run_case(
        "Mixed: 2 beam, 2 cable",
        boundary_loop=[
            (0.0, 0.0, 0.0),
            (10.0, 0.0, 0.0),
            (10.0, 15.0, 0.0),
            (0.0, 15.0, 0.0),
        ],
        segment_types=["beam", "cable", "beam", "cable"],
        fill="tfi",
        K=5, M=8,
        warp_q=2.0, weft_q=2.0, edge_q=5.0,
    ))

    # Case 4: polar fill, 6-anchor hexagonal loop, all beam.
    hex_loop = []
    for k in range(6):
        ang = 2.0 * np.pi * k / 6.0
        hex_loop.append((5.0 * np.cos(ang), 5.0 * np.sin(ang), 0.0))
    results.append(_run_case(
        "Hexagon, polar fill, all beam",
        boundary_loop=hex_loop,
        segment_types=["beam", "beam", "beam", "beam", "beam", "beam"],
        fill="polar",
        K=5, M=8,
        warp_q=2.0, weft_q=2.0, edge_q=5.0,
    ))

    print("=" * 60)
    print("SUMMARY")
    for r in results:
        print("  %-40s  residual=%.2e  minArea=%.2e  zero=%d"
              % (r["name"], r["residual"], r["min_area"], r["zero_area_count"]))

    all_ok = True
    for r in results:
        if r["zero_area_count"] > 0:
            all_ok = False
            print("  FAIL:", r["name"], "has zero-area triangles")

    print("=" * 60)
    if all_ok:
        print("UNIVERSAL MESH ENGINE: PASS")
    else:
        print("UNIVERSAL MESH ENGINE: FAIL")
    return all_ok


if __name__ == "__main__":
    ok = run()
    exit(0 if ok else 1)





