# =============================================================================
# SDSe - Benchmark Hypar (standalone)
# =============================================================================
# Standalone test. NOT wired into the app.
#
# Reproduces, as closely as possible, the SDS-CONST Benchmark 001 hypar.
# Reference: 41 nodes, 56 triangles, N0 = 1.0 kN/m, four corners fixed.
#
# Our solver is LINEAR FDM. The reference solver is NONLINEAR.
# Discrepancies are expected. Comparison is the point.
# =============================================================================

import numpy as np

from engine.form_finding import solve_fdm


def _build_hypar_mesh():
    """
    Build a 9x9 grid of (x, y) integer coordinates from -4 to +4.
    Keep only nodes with |x| + |y| <= 4 (the diamond).
    Scale by 0.375 so the diamond's extreme points sit at 1.5 m.

    Node count: 41.

    Cell triangulation:
      - A cell whose 4 corners are all inside the diamond
        becomes 2 triangles.
      - A cell with exactly 3 corners inside becomes 1 triangle.
      - A cell with 2 or fewer corners inside is skipped.

    Returns:
        coords_xy : (N, 2) array of scaled (x, y)
        tris      : list of (a, b, c) triangle index triples
        edges     : list of (a, b) unique edge pairs
    """
    a = 1.5
    scale = a / 4.0

    # ---- Step 1: collect nodes in the diamond, in a fixed order.
    node_map = {}
    coords_xy = []
    for gy in range(-4, 5):
        for gx in range(-4, 5):
            if abs(gx) + abs(gy) <= 4:
                node_map[(gx, gy)] = len(coords_xy)
                coords_xy.append((gx * scale, gy * scale))

    coords_xy = np.array(coords_xy, dtype=float)

    # ---- Step 2: build triangles from cells.
    tris = []
    for gy in range(-4, 4):
        for gx in range(-4, 4):
            corners = [
                (gx,     gy),
                (gx + 1, gy),
                (gx,     gy + 1),
                (gx + 1, gy + 1),
            ]
            inside = [c for c in corners if c in node_map]
            if len(inside) == 4:
                n00 = node_map[(gx,     gy)]
                n10 = node_map[(gx + 1, gy)]
                n01 = node_map[(gx,     gy + 1)]
                n11 = node_map[(gx + 1, gy + 1)]
                tris.append((n00, n10, n01))
                tris.append((n10, n11, n01))
            elif len(inside) == 3:
                idx = [node_map[c] for c in inside]
                tris.append((idx[0], idx[1], idx[2]))

    # ---- Step 3: unique edges from triangles.
    edge_set = set()
    for (a_i, b_i, c_i) in tris:
        for e in ((a_i, b_i), (b_i, c_i), (c_i, a_i)):
            if e[0] > e[1]:
                e = (e[1], e[0])
            edge_set.add(e)
    edges = sorted(edge_set)

    return coords_xy, tris, edges


def build_diamond_topology():
    """
    Thin wrapper. Returns (coords_xy, tris, edges) for the diamond.
    """
    return _build_hypar_mesh()


def hypar_z(x, y, H=1.0, a=1.5):
    return (H / 2.0) * (x * x - y * y) / (a * a)


def build_points_3d(coords_xy):
    pts = np.zeros((coords_xy.shape[0], 3))
    for i, (x, y) in enumerate(coords_xy):
        pts[i, 0] = x
        pts[i, 1] = y
        pts[i, 2] = hypar_z(x, y)
    return pts


def find_corner_indices(coords_xy, a=1.5, tol=1e-6):
    corners = []
    for i, (x, y) in enumerate(coords_xy):
        if (abs(abs(x) - a) < tol and abs(y) < tol) or \
           (abs(abs(y) - a) < tol and abs(x) < tol):
            corners.append(i)
    return sorted(corners)


def q_from_prestress(points, edges, N0):
    q = np.zeros(len(edges))
    for k, (i, j) in enumerate(edges):
        L = float(np.linalg.norm(points[j] - points[i]))
        if L < 1e-12:
            q[k] = 0.0
        else:
            q[k] = N0 / L
    return q


def run():
    print("=" * 68)
    print("SDSe - Benchmark Hypar (SDS-CONST Benchmark 001 reconstruction)")
    print("=" * 68)
    print()

    coords_xy, triangles, edges = build_diamond_topology()
    points_initial = build_points_3d(coords_xy)

    n_nodes = points_initial.shape[0]
    n_edges = len(edges)
    n_tris = len(triangles)

    print("Topology:")
    print("  Nodes:     ", n_nodes)
    print("  Edges:     ", n_edges)
    print("  Triangles: ", n_tris)
    print("  (Reference: 41 nodes / 56 triangles / 111 free DOFs)")
    print()

    corners = find_corner_indices(coords_xy)
    print("Fixed corner indices:", corners)
    print("  (Reference: four corner supports)")
    print()

    N0 = 1000.0
    q = q_from_prestress(points_initial, edges, N0)
    mean_q = float(np.mean(q))
    min_q = float(np.min(q))
    max_q = float(np.max(q))
    print("Prestress N0: %.1f N/m" % N0)
    print("  Mean q: %.6f" % mean_q)
    print("  Min q : %.6f" % min_q)
    print("  Max q : %.6f" % max_q)
    print()

    result = solve_fdm(points_initial, edges, corners, q)
    coords_final = result["coordinates"]

    disp = np.linalg.norm(coords_final - points_initial, axis=1)
    max_disp = float(np.max(disp))
    mean_disp = float(np.mean(disp))

    print("Our linear FDM result:")
    print("  residual_norm  : %.6e" % result["residual_norm"])
    print("  n_free         :", result["n_free"])
    print("  n_fixed        :", result["n_fixed"])
    print("  max_disp (m)   : %.6f" % max_disp)
    print("  mean_disp (m)  : %.6f" % mean_disp)
    print()

    tensions = np.zeros(n_edges)
    for k, (i, j) in enumerate(edges):
        L = float(np.linalg.norm(coords_final[j] - coords_final[i]))
        tensions[k] = q[k] * L
    min_t = float(np.min(tensions))
    max_t = float(np.max(tensions))
    mean_t = float(np.mean(tensions))
    print("Member tension (T = q * L):")
    print("  min : %.6f N" % min_t)
    print("  max : %.6f N" % max_t)
    print("  mean: %.6f N" % mean_t)
    print()

    print("=" * 68)
    print("Comparison with reference (SDS-CONST Benchmark 001):")
    print("=" * 68)
    print("  Nodes      : 41  (ours: %d)" % n_nodes)
    print("  Triangles  : 56  (ours: %d)" % n_tris)
    print("  Free DOFs  : 111 (ours: %d)" % (3 * result["n_free"]))
    print("  Reported residual : 0.000394 N")
    print("  Our residual      : %.6e N" % result["residual_norm"])
    print("  Reported max move : 18.02 mm")
    print("  Our max move      : %.4f mm" % (max_disp * 1000.0))
    print("  Reported max force: 1.240 kN/m")
    print("  Our max force     : %.6f N/m" % max_t)
    print()
    print("NOTE: reference solver is NONLINEAR. Ours is LINEAR FDM.")
    print("      Discrepancies are expected. Comparison is the point.")
    print()


if __name__ == "__main__":
    run()


# =============================================================================
# END OF benchmark_hypar.py
# =============================================================================
