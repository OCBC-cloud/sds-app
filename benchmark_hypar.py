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
#
# Our solver is LINEAR FDM (one solve). The reference solver is a
# NONLINEAR equilibrium solver. So the numbers may differ.
#
# Topology construction:
#   Concentric diamond rings.
#   Ring 0 (outer) : 16 nodes (4 per side).
#   Ring 1         : 12 nodes (3 per side).
#   Ring 2         :  8 nodes (2 per side).
#   Ring 3         :  4 nodes (1 per side).
#   Centre         :  1 node.
#   Total          : 41 nodes.
#
# =============================================================================

import numpy as np

from engine.form_finding import solve_fdm


# =============================================================================
# 1. DIAMOND TOPOLOGY
# =============================================================================

def _ring_positions(k, a):
    """
    Return the coordinates of the 4*k nodes on diamond ring number k,
    where k = 1 gives the outermost ring with 4 nodes per side,
    k = 2 gives the next ring with 3 nodes per side, etc.

    The rings are nested: the outer ring is at |x| + |y| = a,
    the next at |x| + |y| = a * (k-1) / k, etc.

    A ring with 4*m nodes has m nodes on each of the four sides.
    We place the nodes at positions (m-1) on one side, and one at
    each corner is shared with the next side. To avoid duplication,
    we place m-1 nodes per side (not m), so total per ring is 4*(m-1).
    But we want the corner nodes to belong to the ring, so we use
    m nodes per side and skip the duplicated corner at the end of
    the last side.
    """
    # We will pass in the number of nodes per side directly.
    return None  # placeholder, unused


def build_diamond_topology(n_side=4):
    """
    Build a diamond topology: |x| + |y| <= 1.5.
    n_side is the number of nodes on each side of the outer ring.

    With n_side = 4:
      Outer ring     : 4 sides * 4 nodes   - 4 shared corners = 12 nodes?
      Let us define instead:
        Outer ring with n_side nodes per side and 4 shared corners:
          total = 4 * (n_side - 1)
      n_side = 5 -> 16 nodes per outer ring.
      n_side = 4 -> 12 nodes per outer ring.
      n_side = 3 ->  8 nodes per outer ring.
      n_side = 2 ->  4 nodes per outer ring.
      n_side = 1 ->  1 node (centre).

    For 41 nodes with reference 56 triangles, we expect:
      Outer ring     = 16 nodes
      Ring 1         = 12 nodes
      Ring 2         =  8 nodes
      Ring 3         =  4 nodes
      Centre         =  1 node
      Total = 41.

    The outer ring of 16 nodes means 4 corners + 12 side nodes.
    Each side has 5 nodes (2 corners + 3 side nodes).
    """
    a = 1.5

    # Outer ring: 16 nodes on |x| + |y| = a.
    # Each side has 5 nodes: 2 corners + 3 interior.
    # We define ring 0 with corner points at:
    #   (a, 0), (0, a), (-a, 0), (0, -a)
    # and 3 interior nodes per side.

    def ring_nodes(scale):
        """
        Return 16 nodes on the diamond |x| + |y| = a * scale.
        Corners at 4 positions, 3 interior nodes per side.
        """
        r = a * scale
        # Corners
        c1 = (r, 0.0)
        c2 = (0.0, r)
        c3 = (-r, 0.0)
        c4 = (0.0, -r)
        # 3 interior nodes per side (excluding the corner endpoints,
        # which are shared with the adjacent side).
        def side(p0, p1):
            pts = []
            for m in range(1, 4):
                t = m / 4.0
                pts.append((p0[0] * (1.0 - t) + p1[0] * t,
                            p0[1] * (1.0 - t) + p1[1] * t))
            return pts
        s1 = side(c1, c2)
        s2 = side(c2, c3)
        s3 = side(c3, c4)
        s4 = side(c4, c1)
        # Order: corner, 3 side nodes, corner, 3 side nodes, ..., back to first corner.
        return [c1] + s1 + [c2] + s2 + [c3] + s3 + [c4] + s4

    def smaller_ring_nodes(scale, per_side):
        """
        Return a ring with `per_side` nodes per side. per_side includes
        the 2 corners. So per_side=4 -> 4 corners + 3 interior = 12 total.
        per_side=3 -> 4 corners + 2 interior = 8 total.
        per_side=2 -> 4 corners + 1 interior = 4 total.
        """
        r = a * scale
        c1 = (r, 0.0)
        c2 = (0.0, r)
        c3 = (-r, 0.0)
        c4 = (0.0, -r)
        n_interior = per_side - 2  # number of interior nodes per side
        def side(p0, p1):
            pts = []
            for m in range(1, n_interior + 1):
                t = m / float(n_interior + 1)
                pts.append((p0[0] * (1.0 - t) + p1[0] * t,
                            p0[1] * (1.0 - t) + p1[1] * t))
            return pts
        s1 = side(c1, c2)
        s2 = side(c2, c3)
        s3 = side(c3, c4)
        s4 = side(c4, c1)
        return [c1] + s1 + [c2] + s2 + [c3] + s3 + [c4] + s4

    # Ring 0 (outer): 16 nodes
    ring0 = ring_nodes(1.0)
    # Ring 1: 12 nodes, per_side = 4
    ring1 = smaller_ring_nodes(3.0 / 4.0, 4)
    # Ring 2: 8 nodes, per_side = 3
    ring2 = smaller_ring_nodes(2.0 / 4.0, 3)
    # Ring 3: 4 nodes, per_side = 2 (just corners)
    ring3 = smaller_ring_nodes(1.0 / 4.0, 2)
    # Centre
    centre = [(0.0, 0.0)]

    all_nodes = ring0 + ring1 + ring2 + ring3 + centre
    coords_xy = np.array(all_nodes, dtype=float)

    # Indexing helpers
    idx_r0 = 0
    idx_r1 = idx_r0 + len(ring0)
    idx_r2 = idx_r1 + len(ring1)
    idx_r3 = idx_r2 + len(ring2)
    idx_c = idx_r3 + len(ring3)

    # ---- Triangles between ring pairs.
    #
    # Between ring0 (16) and ring1 (12): 16 outer nodes, 12 inner.
    # The two rings are aligned at the four corners. Between two
    # consecutive corners, the outer ring has 4 nodes (2 corners + 2
    # interior), the inner ring has 3 nodes (2 corners + 1 interior).
    # Both rings share their corners. Each side of the outer ring
    # spans from corner_k to corner_{k+1}, with 2 interior nodes.
    # Each side of the inner ring spans from corner_k to corner_{k+1},
    # with 1 interior node.
    #
    # Per side: 2 outer interior nodes + 1 inner interior node. That
    # gives 2 quads -> 4 triangles per side, times 4 sides = 16 triangles.
    # Actually simpler: for each of the 16 outer nodes, one triangle.
    # But we must be careful with counts.

    def pair_triangles(outer_start, n_outer, inner_start, n_inner):
        """
        Triangulate between an outer ring of n_outer nodes and an
        inner ring of n_inner nodes. The outer ring corners align
        with the inner ring corners at 4 evenly spaced positions.

        Assumes n_outer and n_inner are both multiples of 4.
        """
        tris = []
        # Handle each of the 4 sides separately.
        o_per_side = n_outer // 4
        i_per_side = n_inner // 4
        for s in range(4):
            # Outer ring nodes for this side, indices s*o_per_side to s*o_per_side + o_per_side
            o_idx = [(outer_start + (s * o_per_side + k) % n_outer) for k in range(o_per_side + 1)]
            i_idx = [(inner_start + (s * i_per_side + k) % n_inner) for k in range(i_per_side + 1)]
            # o_idx has o_per_side+1 entries (first is corner, last is next corner)
            # i_idx has i_per_side+1 entries
            # Walk both, forming quads and triangles.
            # Since o_per_side > i_per_side in our case:
            #   o_per_side = 4, i_per_side = 3 for ring0-ring1.
            #   o_per_side = 3, i_per_side = 2 for ring1-ring2.
            #   o_per_side = 2, i_per_side = 1 for ring2-ring3.
            # Strategy: for each inner node, connect to two adjacent outer nodes.
            for ii in range(i_per_side):
                in_a = i_idx[ii]
                in_b = i_idx[ii + 1]
                # Match to outer nodes by fraction.
                # ii / i_per_side corresponds to position along side.
                o_frac_a = ii / float(i_per_side)
                o_frac_b = (ii + 1) / float(i_per_side)
                o_a = int(round(o_frac_a * o_per_side))
                o_b = int(round(o_frac_b * o_per_side))
                if o_a > o_per_side:
                    o_a = o_per_side
                if o_b > o_per_side:
                    o_b = o_per_side
                # Triangles from outer[o_a..o_b] to inner[in_a..in_b]
                # Simplest: fan from in_a to outer[o_a..o_b], then in_b.
                for oi in range(o_a, o_b):
                    on = o_idx[oi]
                    on_next = o_idx[oi + 1]
                    tris.append((on, on_next, in_a))
                # Final triangle to in_b:
                if o_a != o_b:
                    tris.append((o_idx[o_b], in_a, in_b))
        return tris

    # Simpler correct approach: use a robust triangulation.
    # For each pair of rings, walk both rings node by node.
    def ring_to_ring_triangles(outer_start, outer_n, inner_start, inner_n):
        """
        Walk both rings together and emit triangles.
        Assumes both rings are aligned at the 4 corners.
        """
        tris = []
        o_ps = outer_n // 4
        i_ps = inner_n // 4
        # For each of the 4 sides:
        for s in range(4):
            # Outer nodes for this side, including both corners: o_ps + 1 nodes
            # Index position (s * o_ps + k) mod outer_n
            o_idx = []
            for k in range(o_ps + 1):
                o_idx.append(outer_start + (s * o_ps + k) % outer_n)
            i_idx = []
            for k in range(i_ps + 1):
                i_idx.append(inner_start + (s * i_ps + k) % inner_n)
            # Walk outer nodes, matching to nearest inner node.
            # For each outer node pair, if there is an inner node between them,
            # emit 1 quad (2 triangles). Otherwise, emit 1 triangle.
            # Because o_ps >= i_ps, some outer nodes have no corresponding inner node.
            outer_i = 0
            inner_i = 0
            while outer_i < o_ps:
                on_a = o_idx[outer_i]
                on_b = o_idx[outer_i + 1]
                if inner_i < i_ps:
                    # check if inner node falls between outer_i and outer_i+1
                    # Use fraction: outer_i+1 fraction from start of side
                    # We emit triangle (on_a, on_b, in_i)
                    in_c = i_idx[inner_i]
                    tris.append((on_a, on_b, in_c))
                    outer_i += 1
                    # Advance inner if the next outer node is past the next inner
                    # Simple heuristic: advance inner every o_ps / i_ps outer steps.
                    if (outer_i * i_ps) >= ((inner_i + 1) * o_ps):
                        inner_i += 1
                else:
                    # No more inner nodes on this side, connect to corner
                    in_c = i_idx[i_ps]
                    tris.append((on_a, on_b, in_c))
                    outer_i += 1
        return tris

    # Hmm, the above is getting complicated. Let's use a cleaner method:
    # For each pair of rings, simply project each node of the smaller ring
    # onto the larger ring by angle, and form quads.
    def fan_triangles(outer_start, outer_n, inner_start, inner_n):
        """
        Robust: for each pair of adjacent inner nodes, find the two
        outer nodes that bracket them, and form 1 quad (2 triangles)
        plus any leftover triangles.
        """
        tris = []
        # Angle-based alignment. Compute angles for both rings.
        # Note: rings are diamond-shaped, so angle alone is not enough.
        # We use the ring index (position along ring) as a proxy.
        # The outer ring has 4 segments (sides), inner has 4 segments.
        # Each side has o_ps and i_ps nodes respectively.
        o_ps = outer_n // 4
        i_ps = inner_n // 4
        for s in range(4):
            # indices on this side (excluding the endpoint which is the next side's start)
            o_side = [(s * o_ps + k) % outer_n for k in range(o_ps)]
            i_side = [(s * i_ps + k) % inner_n for k in range(i_ps)]
            # For each inner node, connect to the closest outer node and the
            # next outer node.
            for ii, i_local in enumerate(i_side):
                in_abs = inner_start + i_local
                # Match fraction along side: ii / i_ps
                o_local_f = (ii / float(i_ps)) * o_ps
                o_local = int(round(o_local_f))
                if o_local >= o_ps:
                    o_local = o_ps - 1
                o_local_next = o_local + 1
                if o_local_next >= o_ps:
                    o_local_next = 0  # wrap to corner
                o_a = outer_start + o_side[o_local]
                o_b = outer_start + o_side[o_local_next] if o_local_next < o_ps else outer_start + ((s + 1) * o_ps) % outer_n
                # Triangle from in_abs to o_a, o_b
                tris.append((in_abs, o_a, o_b))
        return tris

    tris = []
    # Ring0 to Ring1
    tris += fan_triangles(idx_r0, len(ring0), idx_r1, len(ring1))
    # Ring1 to Ring2
    tris += fan_triangles(idx_r1, len(ring1), idx_r2, len(ring2))
    # Ring2 to Ring3
    tris += fan_triangles(idx_r2, len(ring2), idx_r3, len(ring3))
    # Ring3 to centre
    for k in range(len(ring3)):
        a a_i = idx_r3 + k
)):
        b_i = idx_r3            + (k + 1) % len if(ring3)
        tris.append((a_i, b_i, idx_c))

    # ---- Unique edges from triangles.
    edge_set = set()
    for (a, b, c) in tris:
        for e in ((a, b), (b, c), (c, e[0] > e[1]:
                e = (e[1], e[0])
            edge_set.add(e)
    edges = sorted(edge_set)

    return coords_xy, tris, edges


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

    coords_xy, triangles, edges = build_diamond_topology(n_side=4)
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
    print("Prestress N0: %.1f N/m" % N0)
    print("Mean q: %.6f   Min q: %.6f   Max q: %.6f"
          % (float(np.mean(q)), float(np.min(q)), float(np.max(q))))
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
    print("  Reported residual (ref)  : 0.000394 N")
    print("  Our residual             : %.6e N" % result["residual_norm"])
    print("  Reported max movement    : 18.02 mm")
    print("  Our max movement         : %.4f mm" % (max_disp * 1000.0))
    print("  Reported max force       : 1.240 kN/m")
    print("  Our max force            : %.6f N/m" % float(np.max(tensions)))
    print()
    print("NOTE: reference solver is NONLINEAR. Ours is LINEAR FDM.")
    print("      Discrepancies are expected. Comparison is the point.")
    print()


if __name__ == "__main__":
    run()


# =============================================================================
# END OF benchmark_hypar.py
# =============================================================================
