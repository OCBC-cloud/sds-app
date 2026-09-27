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


def _side_points(p0, p1, n_interior):
    pts = []
    for m in range(1, n_interior + 1):
        t = m / float(n_interior + 1)
        x = p0[0] * (1.0 - t) + p1[0] * t
        y = p0[1] * (1.0 - t) + p1[1] * t
        pts.append((x, y))
    return pts


def _diamond_ring(a, n_side):
    """
    Return the nodes of a diamond ring |x| + |y| = a.
    n_side = number of nodes on each side including both corners.
    Total nodes on the ring: 4 * (n_side - 1).
    """
    c1 = (a, 0.0)
    c2 = (0.0, a)
    c3 = (-a, 0.0)
    c4 = (0.0, -a)
    n_int = n_side - 2
    s1 = _side_points(c1, c2, n_int)
    s2 = _side_points(c2, c3, n_int)
    s3 = _side_points(c3, c4, n_int)
    s4 = _side_points(c4, c1, n_int)
    return [c1] + s1 + [c2] + s2 + [c3] + s3 + [c4] + s4


def build_diamond_topology():
    """
    Diamond domain |x| + |y| <= 1.5.
    Ring 0 (outer): 16 nodes  (n_side = 5).
    Ring 1:         12 nodes  (n_side = 4).
    Ring 2:          8 nodes  (n_side = 3).
    Ring 3:          4 nodes  (n_side = 2).
    Centre:          1 node.
    Total: 41 nodes.
    """
    a = 1.5
    ring0 = _diamond_ring(a * 1.0, 5)
    ring1 = _diamond_ring(a * 0.75, 4)
    ring2 = _diamond_ring(a * 0.50, 3)
    ring3 = _diamond_ring(a * 0.25, 2)
    all_nodes = ring0 + ring1 + ring2 + ring3 + [(0.0, 0.0)]
    coords_xy = np.array(all_nodes, dtype=float)

    n0 = len(ring0)
    n1 = len(ring1)
    n2 = len(ring2)
    n3 = len(ring3)

    i_r0 = 0
    i_r1 = i_r0 + n0
    i_r2 = i_r1 + n1
    i_r3 = i_r2 + n2
    i_c = i_r3 + n3

    tris = []

    # Between two rings: walk both, connect by fraction.
    def _pair(outer_start, outer_n, inner_start, inner_n):
        o_ps = outer_n // 4
        i_ps = inner_n // 4
        for s in range(4):
            for ii in range(i_ps):
                in_abs = inner_start + (s * i_ps + ii) % inner_n
                o_a_local = int(round((ii / float(i_ps)) * o_ps))
                o_b_local = int(round(((ii + 1) / float(i_ps)) * o_ps))
                if o_a_local >= o_ps:
                    o_a_local = o_ps - 1
                if o_b_local > o_ps:
                    o_b_local = o_ps
                o_a = outer_start + (s * o_ps + o_a_local) % outer_n
                if o_b_local < o_ps:
                    o_b = outer_start + (s * o_ps + o_b_local) % outer_n
                else:
                    o_b = outer_start + ((s + 1) * o_ps) % outer_n
                tris.append((in_abs, o_a, o_b))

    _pair(i_r0, n0, i_r1, n1)
    _pair(i_r1, n1, i_r2, n2)
    _pair(i_r2, n2, i_r3, n3)

    # Ring 3 to centre: 4 triangles.
    for k in range(4):
        a_i = i_r3 + k
        b_i = i_r3 + (k + 1) % 4
        tris.append((a_i, b_i, i_c))

    edge_set = set()
    for (a, b, c) in tris:
        for e in ((a, b), (b, c), (c, a)):
            if e[0] > e[1]:
                e = (e[1], e[0])
            edge_set.add(e)
    edges = sorted(edge_set)

    return coords_xy, tris, edges





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





