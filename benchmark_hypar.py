# =============================================================================
# SDSe - Benchmark Hypar (standalone)
# =============================================================================
# Standalone test. NOT wired into the app. NOT imported by any viewer,
# any workshop, or any Tester. Runs on its own.
#
# Purpose: reproduce, as closely as possible, the SDS-CONST Benchmark 001
# hypar test. Compare our linear FDM solver (engine/form_finding.solve_fdm)
# against the reference numbers in the verification record.
#
# Reference (from SDS-CONST Benchmark 001 Verification Record):
#   Plan form ................ 3.0 m x 3.0 m diamond
#   Surface .................. true hyperbolic paraboloid
#                              z = (H/2)*(x^2 - y^2)/a^2,
#                              H = 1.0 m, a = 1.5 m
#   Domain ................... |x| + |y| <= 1.5 m
#   Corner elevations ........ +0.5 / -0.5 alternating
#   Nodes .................... 41
#   Triangles ................ 56
#   Free DOFs ................ 111
#   E ........................ 200 MPa
#   t ........................ 1 mm
#   Poisson .................. 0.30
#   Prestress N0 ............. 1.0 kN/m
#   Fixed .................... four corner supports
#   Reported residual ........ 0.000394 N
#   Reported max movement .... 18.02 mm
#   Reported max force ....... 1.240 kN/m
#
# Our solver is LINEAR FDM (one solve). The reference solver is a
# NONLINEAR equilibrium solver. So the numbers may differ. That is
# expected. Comparison, not equality, is the goal.
# =============================================================================

import numpy as np

from engine.form_finding import solve_fdm


# =============================================================================
# 1. DIAMOND TOPOLOGY
# =============================================================================

def build_diamond_topology(n_rings=4):
    """
    Build a diamond topology: |x| + |y| <= a with a = 1.5.
    Nodes are placed on concentric diamond rings.

    For n_rings = 4, this gives 1 + 4 + 8 + 12 + 16 = 41 nodes.
    Triangles: 4 * (n_rings-1) + ... -> 56 total.

    Returns:
      coords_xy : (n, 2) array of (x, y)
      triangles : (m, 3) list of node indices
      edges     : (e, 2) list of unique edges from the triangles
    """
    a = 1.5
    nodes_xy = [(0.0, 0.0)]  # centre

    # Concentric rings of the diamond |x| + |y| = r * a / n_rings
    # Each ring k has 4*k nodes.
    for k in range(1, n_rings + 1):
        r = k / float(n_rings)
        # Corner points: (a*r, 0), (0, a*r), (-a*r, 0), (0, -a*r)
        # The ring has 4*k nodes: k on each side.
        # Side 1: from (a*r, 0) to (0, a*r)
        # We place k nodes evenly on each side, excluding one endpoint
        # to avoid duplicates.
        pts = []
        # Side 1 (x from a*r to 0, y from 0 to a*r):
        for m in range(k):
            t = m / float(k)
            x = a * r * (1.0 - t)
            y = a * r * t
            pts.append((x, y))
        # Side 2 (from (0, a*r) to (-a*r, 0)):
        for m in range(k):
            t = m / float(k)
            x = -a * r * t
            y = a * r * (1.0 - t)
            pts.append((x, y))
        # Side 3 (from (-a*r, 0) to (0, -a*r)):
        for m in range(k):
            t = m / float(k)
            x = -a * r * (1.0 - t)
            y = -a * r * t
            pts.append((x, y))
        # Side 4 (from (0, -a*r) to (a*r, 0)):
        for m in range(k):
            t = m / float(k)
            x = a * r * t
            y = -a * r * (1.0 - t)
            pts.append((x, y))
        nodes_xy.extend(pts)

    coords_xy = np.array(nodes_xy, dtype=float)
    n = coords_xy.shape[0]

    # ---- Build triangles between consecutive rings.
    # Ring 0 = centre (1 node). Ring k has 4*k nodes.
    # Ring k-1 has 4*(k-1) nodes.
    triangles = []
    ring_start = [0]
    for k in range(1, n_rings + 1):
        ring_start.append(ring_start[-1] + 4 * k)

    # First ring (k=1): 4 nodes, connect to centre.
    # The 4 nodes are: (a/4, 0), (0, a/4), (-a/4, 0), (0, -a/4)
    # with a/4 = r ratio 1/4. Wait, a = 1.5, ring 1 has r = 1/4 = 0.25,
    # so node at (0.375, 0). Yes.
    # Triangles: (centre, k=0-1, ring1[0]), (centre, ring1[1], ring1[0]), etc.
    # Simpler: for each pair (ring1[i], ring1[i+1]) make a triangle with centre.
    r0 = 0
    r1_start = ring_start[1]
    for i in range(4):
        a_idx = r0
        b_idx = r1_start + i
        c_idx = r1_start + (i + 1) % 4
        triangles.append((a_idx, b_idx, c_idx))

    # Between ring k-1 and ring k (for k >= 2): each ring k-1 node
    # connects to two adjacent ring k nodes and vice versa.
    # Ring k-1 has 4*(k-1) nodes; ring k has 4*k nodes.
    # Each ring k-1 node (at position p) is aligned with ring k node at
    # position 2*p (approximately) since densities differ by factor.
    # We match by angular position.
    for k in range(2, n_rings + 1):
        n_prev = 4 * (k - 1)
        n_curr = 4 * k
        start_prev = ring_start[k - 1]
        start_curr = ring_start[k]

        # For each ring k-1 node, connect to two ring k nodes.
        # Positions along the ring: ring k-1 at index p, angle ~ 2*pi*p/n_prev.
        # Ring k at index q, angle ~ 2*pi*q/n_curr.
        # We walk both rings and make quads -> two triangles.
        for p in range(n_prev):
            q_a = int(round(p * n_curr / float(n_prev))) % n_curr
            q_b = (q_a + 1) % n_curr
            a_idx = start_prev + p
            b_idx = start_prev + (p + 1) % n_prev
            c_idx = start_curr + q_a
            d_idx = start_curr + q_b
            # Two triangles: (a_idx, b_idx, c_idx) and (b_idx, d_idx, c_idx)
            triangles.append((a_idx, b_idx, c_idx))
            triangles.append((b_idx, d_idx, c_idx))

    # ---- Unique edges from triangles.
    edge_set = set()
    for (a, b, c) in triangles:
        for e in ((a, b), (b, c), (c, a)):
            if e[0] > e[1]:
                e = (e[1], e[0])
            edge_set.add(e)
    edges = sorted(edge_set)

    return coords_xy, triangles, edges


# =============================================================================
# 2. HYPERBOLIC PARABOLOID SURFACE
# =============================================================================

def hypar_z(x, y, H=1.0, a=1.5):
    """z = (H/2)*(x^2 - y^2)/a^2."""
    return (H / 2.0) * (x * x - y * y) / (a * a)


# =============================================================================
# 3. BUILD POINTS IN 3D
# =============================================================================

def build_points_3d(coords_xy):
    pts = np.zeros((coords_xy.shape[0], 3))
    for i, (x, y) in enumerate(coords_xy):
        pts[i, 0] = x
        pts[i, 1] = y
        pts[i, 2] = hypar_z(x, y)
    return pts


# =============================================================================
# 4. IDENTIFY THE FOUR CORNERS
# =============================================================================

def find_corner_indices(coords_xy, a=1.5, tol=1e-6):
    corners = []
    for i, (x, y) in enumerate(coords_xy):
        if (abs(abs(x) - a) < tol and abs(y) < tol) or \
           (abs(abs(y) - a) < tol and abs(x) < tol):
            corners.append(i)
    return sorted(corners)


# =============================================================================
# 5. FORCE DENSITY FROM PRESCRIBED PRESTRESS
# =============================================================================

def q_from_prestress(points, edges, N0):
    """
    q_edge = N0 / L_initial, where L_initial is the initial length
    of the edge. Gives T = q * L = N0 when the edge is at its
    initial length.
    """
    q = np.zeros(len(edges))
    for k, (i, j) in enumerate(edges):
        L = float(np.linalg.norm(points[j] - points[i]))
        if L < 1e-12:
            q[k] = 0.0
        else:
            q[k] = N0 / L
    return q


# =============================================================================
# 6. RUN AND REPORT
# =============================================================================

def run():
    print("=" * 68)
    print("SDSe - Benchmark Hypar (SDS-CONST Benchmark 001 reconstruction)")
    print("=" * 68)
    print()

    # ---- Geometry
    coords_xy, triangles, edges = build_diamond_topology(n_rings=4)
    points_initial = build_points_3d(coords_xy)

    n_nodes = points_initial.shape[0]
    n_edges = len(edges)
    n_tris = len(triangles)

    print("Topology:")
    print("  Nodes:     ", n_nodes)
    print("  Edges:     ", n_edges)
    print("  Triangles: ", n_tris)
    print("  (Reference: 41 / 56 triangles, 111 free DOFs)")
    print()

    # ---- Corners fixed
    corners = find_corner_indices(coords_xy)
    print("Fixed corner indices:", corners)
    print("  (Reference: four corner supports)")
    print()

    # ---- Prestress
    N0 = 1000.0  # N/m
    q = q_from_prestress(points_initial, edges, N0)
    print("Prestress N0: %.1f N/m" % N0)
    print("Mean q: %.6f   Min q: %.6f   Max q: %.6f"
          % (float(np.mean(q)), float(np.min(q)), float(np.max(q))))
    print()

    # ---- Solve with our linear FDM
    result = solve_fdm(points_initial, edges, corners, q)
    coords_final = result["coordinates"]

    # ---- Nodal movement
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

    # ---- Member tension from q * L_final
    tensions = np.zeros(n_edges)
    for k, (i, j) in enumerate(edges):
        L = float(np.linalg.norm(coords_final[j] - coords_final[i]))
        tensions[k] = q[k] * L
    print("Member tension (T = q * L):")
    print("  min: %.6f N" % float(np.min(tensions)))
    print("  max: %.6f N" % float(np.max(tensions)))
    print("  mean: %.6f N" % float(np.mean(tensions)))
    print()

    print("=" * 68)
    print("Comparison with reference (SDS-CONST Benchmark 001):")
    print("=" * 68)
    print("  Nodes:      41 (ours: %d)" % n_nodes)
    print("  Triangles:  56 (ours: %d)" % n_tris)
    print("  Free DOFs:  111 (ours: %d)" % (3 * result["n_free"]))
    print("  Reported residual  (ref): 0.000394 N")
    print("  Our residual             : %.6e N" % result["residual_norm"])
    print("  Reported max movement (ref): 18.02 mm")
    print("  Our max movement           : %.4f mm" % (max_disp * 1000.0))
    print("  Reported max force (ref): 1.240 kN/m")
    print("  Our max force           : %.6f N/m" % float(np.max(tensions)))
    print()
    print("NOTE: reference solver is NONLINEAR. Ours is LINEAR FDM.")
    print("      Discrepancies are expected. Comparison is the point.")
    print()


if __name__ == "__main__":
    run()


# =============================================================================
# END OF benchmark_hypar.py
# =============================================================================
