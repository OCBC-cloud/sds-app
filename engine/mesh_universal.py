# =============================================================================
# SDSe Engine - Universal Mesh Builder
# =============================================================================
# Builds a mesh from a boundary region. Three topologies.
# See engine/SPEC_mesh_topology.md.
#
# The engine knows three topologies, one mesher per topology:
#
#   "twosided" - two curves meeting at two shared tips.
#                Examples: Standard Saddle, Lens, Beam Saddle.
#                Mesh: bilinear blend between the two curves.
#                The two tips are SINGLE nodes, not columns.
#
#   "ring"     - one closed curve, no self-touching.
#                Examples: Crown, Dome.
#                Mesh: concentric rings collapsing to one centre.
#
#   "quad"     - four sides, each a curve or line.
#                Examples: coordinate-file boundaries, DXF quads.
#                Mesh: Coons patch with Boolean sum correction.
#
# The solver (solve_fdm) is universal. The model (anchors,
# segments, types, force densities) is universal. The mesh
# builder is topology-specific, as the industry does it.
#
# Vocabulary (fixed):
#   boundary curve  - one of the sides of the region.
#   tip / corner    - a point where two curves meet. Always held.
#   segment         - the gap between two anchors on a curve.
#   segment type    - beam, cable, or wall.
#   held            - a mesh node solve_fdm does not move.
#   released        - a mesh node solve_fdm moves to equilibrium.
#
# Hold rule (unchanged):
#   Anchor / tip / corner    -> always held.
#   Segment interior, beam   -> held.
#   Segment interior, wall   -> held.
#   Segment interior, cable  -> released.
#   Mesh interior            -> always released.
#
# Structural connections list (Part V doctrine):
#   Empty today. Populated in Stage 3.
#
# fixed_indices (returned by build_mesh_universal):
#   FLAT node indices, ready for solve_fdm.
#
# History:
#   2026-09-29 - First build. Three fills: tfi, polar, barycentric.
#   2026-09-30 - build_mesh_universal returns FLAT fixed_indices.
#   2026-09-30 - _fill_tfi gained tfi_split_index.
#   2026-09-30 - Full rewrite: three topologies replace three fills.
#                See engine/SPEC_mesh_topology.md.
# =============================================================================

import numpy as np


_VALID_TOPOLOGIES = ("twosided", "ring", "quad")
_VALID_TYPES = ("beam", "cable", "wall")


# =============================================================================
# VALIDATION
# =============================================================================

def _validate_topology(topology):
    """Raise ValueError if topology is not recognised."""
    if topology not in _VALID_TOPOLOGIES:
        raise ValueError(
            "topology must be one of %s (got %r)"
            % (list(_VALID_TOPOLOGIES), topology)
        )


def _validate_curve(curve, name):
    """Raise ValueError if a curve is malformed."""
    arr = np.asarray(curve, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError(
            "%s must be (n, 3) array (got shape %s)"
            % (name, str(arr.shape))
        )
    if arr.shape[0] < 2:
        raise ValueError(
            "%s must have at least 2 points (got %d)"
            % (name, arr.shape[0])
        )
    return arr


def _validate_segment_types(segment_types, n_segments):
    """Raise ValueError if segment types are malformed."""
    if len(segment_types) != n_segments:
        raise ValueError(
            "segment_types must have length %d (got %d)"
            % (n_segments, len(segment_types))
        )
    for k, t in enumerate(segment_types):
        if t not in _VALID_TYPES:
            raise ValueError(
                "segment_types[%d] must be one of %s (got %r)"
                % (k, list(_VALID_TYPES), t)
            )


def _validate_density(K, M):
    """Raise ValueError if density parameters are malformed."""
    if K < 1:
        raise ValueError(
            "subdivisions_per_segment must be >= 1 (got %d)" % K
        )
    if M < 2:
        raise ValueError(
            "transverse_count must be >= 2 (got %d)" % M
        )


# =============================================================================
# CURVE HELPERS
# =============================================================================

def _resample_segment(p0, p1, K):
    """Return K mesh nodes on the segment from p0 toward p1.
    Includes p0. Excludes p1."""
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    pts = np.zeros((K, 3))
    for k in range(K):
        t = k / float(K)
        pts[k] = p0 * (1.0 - t) + p1 * t
    return pts





def _resample_curve(curve, K):
    """
    Resample a polyline curve into K nodes per segment.

    The curve is a sequence of anchors. Each segment between two
    consecutive anchors is resampled into K nodes: the anchor
    itself, then K-1 intermediate nodes. The final anchor of the
    curve is NOT included (it belongs to the next curve or is a
    tip handled separately).

    Parameters
    ----------
    curve : (n, 3) array of anchors
    K : int, subdivisions per segment

    Returns
    -------
    (n_pts, 3) array where n_pts = (len(curve) - 1) * K
    """
    curve = np.asarray(curve, dtype=float)
    n_anchors = curve.shape[0]
    rows = []
    for i in range(n_anchors - 1):
        p0 = curve[i]
        p1 = curve[i + 1]
        seg_nodes = _resample_segment(p0, p1, K)
        for p in seg_nodes:
            rows.append(p)
    if len(rows) == 0:
        return np.zeros((0, 3))
    return np.asarray(rows, dtype=float)


# =============================================================================
# MESHER: RING  (one closed curve, no self-touching)
# =============================================================================

def _mesh_ring(curve_loop, K, M):
    """
    Build a ring mesh from a closed curve.

    Concentric rings from the boundary inward, collapsing to a
    single centre node.

    Returns
    -------
    points    : (n_nodes, 3) array
    n_i       : number of boundary-row nodes
    n_nodes   : total node count
    has_centre: True
    centre_idx: index of the single centre node
    topo_info : dict with ring layout metadata
    """
    curve_loop = np.asarray(curve_loop, dtype=float)
    n_anchors = curve_loop.shape[0]

    # Build the boundary row: resample each segment of the loop.
    # The loop closes, so the last segment goes from the last
    # anchor back to the first.
    rows = []
    for i in range(n_anchors):
        p0 = curve_loop[i]
        p1 = curve_loop[(i + 1) % n_anchors]
        seg_nodes = _resample_segment(p0, p1, K)
        for p in seg_nodes:
            rows.append(p)
    boundary_row = np.asarray(rows, dtype=float)
    n_i = boundary_row.shape[0]

    # Centre node at the mean of the boundary row.
    cx = float(np.mean(boundary_row[:, 0]))
    cy = float(np.mean(boundary_row[:, 1]))
    cz = float(np.mean(boundary_row[:, 2]))
    centre = np.array([cx, cy, cz])

    # Rings: (n_i, M - 1) plus the single centre node.
    n_ring_nodes = n_i * (M - 1)
    n_nodes = n_ring_nodes + 1
    points = np.zeros((n_nodes, 3))
    for i in range(n_i):
        p_b = boundary_row[i]
        for j in range(M - 1):
            v = j / float(M - 1)
            k = i * (M - 1) + j
            points[k] = p_b * (1.0 - v) + centre * v
    centre_idx = n_ring_nodes
    points[centre_idx] = centre

    topo_info = {
        "n_i": n_i,
        "M": M,
        "has_centre": True,
        "centre_idx": centre_idx,
    }
    return points, n_i, n_nodes, True, centre_idx, topo_info


# =============================================================================
# MESHER: QUAD  (four sides, Coons patch with Boolean sum)
# =============================================================================

def _mesh_quad(side_A, side_B, side_C, side_D, K, M):
    """
    Build a quad mesh using a proper Coons patch.

    Side A is the bottom, side C is the top. Side D is the left,
    side B is the right. The four corners are the endpoints:
      P00 = A[0]  = D[0]
      P10 = A[-1] = B[0]
      P11 = C[-1] = B[-1]
      P01 = C[0]  = D[-1]

    The patch uses the Boolean sum correction:
        S(u, v) = (1-v)*A(u) + v*C(u) + (1-u)*D(v) + u*B(v)
                - [ (1-u)(1-v)*P00 + u(1-v)*P10
                    + (1-u)v*P01   + uv*P11 ]

    Returns
    -------
    points    : (n_nodes, 3) array
    n_i       : boundary row size (side A length)
    n_nodes   : total
    has_centre: False
    centre_idx: None
    topo_info : dict
    """
    side_A = np.asarray(side_A, dtype=float)
    side_B = np.asarray(side_B, dtype=float)
    side_C = np.asarray(side_C, dtype=float)
    side_D = np.asarray(side_D, dtype=float)

    # Resample each side into K * (n_anchors - 1) nodes.
    # We resample such that all four sides have the SAME number
    # of interior columns. The target is the number of nodes
    # along side A, taken as the reference.
    A_row = _resample_curve(side_A, K)
    C_row = _resample_curve(side_C, K)

    n_A = A_row.shape[0]
    n_C = C_row.shape[0]
    n_i = min(n_A, n_C)  # interior columns; both sides reduced

    # Trim to n_i nodes. (In practice A and C should be resampled
    # to the same length by the caller. We trim defensively.)
    A_use = A_row[:n_i]
    C_use = C_row[:n_i]

    # Corners.
    P00 = side_A[0]
    P10 = side_A[-1]
    P11 = side_C[-1]
    P01 = side_C[0]

    # Left and right sides must be sampled at M values of v.
    # We interpolate D and B at M v-values. Use linear
    # interpolation along their arc length.
    def _interp_side(side, M):
        side = np.asarray(side, dtype=float)
        n = side.shape[0]
        # Arc length parametrisation.
        seglens = np.zeros(n)
        for i in range(1, n):
            seglens[i] = seglens[i - 1] + float(
                np.linalg.norm(side[i] - side[i - 1])
            )
        total = seglens[-1] if seglens[-1] > 1e-12 else 1.0
        fracs = np.linspace(0.0, 1.0, M)
        out = np.zeros((M, 3))
        for k, f in enumerate(fracs):
            target = f * total
            # Find segment containing target.
            idx = 0
            for i in range(1, n):
                if seglens[i] >= target:
                    idx = i - 1
                    break
            else:
                idx = n - 2
            L = seglens[idx + 1] - seglens[idx]
            t = 0.0 if L < 1e-12 else (target - seglens[idx]) / L
            out[k] = side[idx] * (1.0 - t) + side[idx + 1] * t
        return out

    D_vals = _interp_side(side_D, M)
    B_vals = _interp_side(side_B, M)

    # Grid: (n_i, M, 3).
    grid = np.zeros((n_i, M, 3))
    for i in range(n_i):
        u = i / float(n_i - 1) if n_i > 1 else 0.0
        A_u = A_use[i]
        C_u = C_use[i]
        for j in range(M):
            v = j / float(M - 1)
            S = ((1.0 - v) * A_u + v * C_u
                 + (1.0 - u) * D_vals[j] + u * B_vals[j]
                 - ((1.0 - u) * (1.0 - v) * P00
                    + u * (1.0 - v) * P10
                    + (1.0 - u) * v * P01
                    + u * v * P11))
            grid[i, j] = S

    # Flatten.
    n_nodes = n_i * M
    points = grid.reshape((n_nodes, 3))

    topo_info = {
        "n_i": n_i,
        "M": M,
        "has_centre": False,
        "centre_idx": None,
    }
    return points, n_i, n_nodes, False, None, topo_info


# =============================================================================
# MESHER: TWOSIDED  (two curves, two shared tips)
# =============================================================================

def _mesh_twosided(curve_A, curve_B, tip_P0, tip_P1, K, M):
    """
    Build a two-sided mesh: two curves meeting at two shared tips.

    The two tips P0 and P1 are SINGLE nodes. The interior of
    the region is filled with a bilinear blend between the two
    curves:
        S(u, v) = (1 - v) * A(u) + v * B(u)

    Node layout:
        - Node 0:        P0 (single, shared by both curves)
        - Nodes 1..(M-1) * n_interior - 1:
                         interior columns, M nodes each
        - Node n_nodes-1: P1 (single, shared by both curves)

    Total nodes:
        interior_cols * M + 2
    where interior_cols = (n_anchors_A - 1) * K, and the two
    tip columns are collapsed to single nodes.

    Parameters
    ----------
    curve_A : anchors for curve A, ordered P0 -> P1
    curve_B : anchors for curve B, ordered P1 -> P0
    tip_P0  : 3D point of tip 0
    tip_P1  : 3D point of tip 1
    K       : subdivisions per segment
    M       : transverse rows

    Returns
    -------
    points, n_i, n_nodes, has_centre, centre_idx, topo_info
    """
    A_row = _resample_curve(curve_A, K)
    B_row = _resample_curve(curve_B, K)

    # Both curves must have the same number of interior nodes.
    n_interior = min(A_row.shape[0], B_row.shape[0])
    A_use = A_row[:n_interior]
    B_use = B_row[:n_interior]

    # Node 0 is P0. Then interior nodes. Then last node is P1.
    n_interior_nodes = n_interior * M
    n_nodes = n_interior_nodes + 2  # +2 for the two tips
    points = np.zeros((n_nodes, 3))
    points[0] = np.asarray(tip_P0, dtype=float)
    points[n_nodes - 1] = np.asarray(tip_P1, dtype=float)

    for i in range(n_interior):
        p_a = A_use[i]
        p_b = B_use[i]
        for j in range(M):
            v = j / float(M - 1)
            k = 1 + i * M + j
            points[k] = p_a * (1.0 - v) + p_b * v

    # n_i is the number of nodes along a "curve row" when the
    # tips are included. For edge/index bookkeeping, we set it
    # to n_interior + 2 (P0, interiors, P1).
    n_i = n_interior + 2

    topo_info = {
        "n_i": n_i,
        "M": M,
        "has_centre": False,
        "centre_idx": None,
        "n_interior": n_interior,
        "tip_P0_idx": 0,
        "tip_P1_idx": n_nodes - 1,
    }
    return points, n_i, n_nodes, False, None, topo_info





# =============================================================================
# EDGES
# =============================================================================

def _edges_ring(n_i, M, centre_idx):
    """Edges for a ring mesh. Ring edges (closed) + radial to centre."""
    edges = []
    for i in range(n_i):
        i_next = (i + 1) % n_i
        for j in range(M - 1):
            k = i * (M - 1) + j
            # Ring edge.
            edges.append((k, i_next * (M - 1) + j))
            # Radial edge.
            if j + 1 < M - 1:
                edges.append((k, i * (M - 1) + (j + 1)))
            else:
                edges.append((k, centre_idx))
    return edges


def _edges_quad(n_i, M):
    """Edges for a quad mesh. Closed in u-direction, open in v."""
    edges = []
    for i in range(n_i):
        i_next = (i + 1) % n_i
        for j in range(M):
            k = i * M + j
            edges.append((k, i_next * M + j))
            if j + 1 < M:
                edges.append((k, i * M + (j + 1)))
    return edges


def _edges_twosided(n_i, M, n_nodes):
    """
    Edges for a twosided mesh.

    Layout:
        Node 0           = P0
        Nodes 1..n_i*M   = interior grid
        Node n_nodes-1   = P1

    Interior grid: index = 1 + i * M + j, for i in [0, n_interior),
    j in [0, M). Column i=0 connects to P0. Column i=n_interior-1
    connects to P1.
    """
    # n_interior = number of interior columns
    # n_i = n_interior + 2
    n_interior = n_i - 2
    p0_idx = 0
    p1_idx = n_nodes - 1

    edges = []
    for i in range(n_interior):
        i_next = i + 1
        for j in range(M):
            k = 1 + i * M + j
            # Along the curve direction (i -> i+1).
            if i_next < n_interior:
                edges.append((k, 1 + i_next * M + j))
            else:
                # Last interior column connects to P1.
                edges.append((k, p1_idx))
            # Across the transverse direction (j -> j+1).
            if j + 1 < M:
                edges.append((k, 1 + i * M + (j + 1)))
            # First interior column connects to P0.
            if i == 0:
                edges.append((k, p0_idx))
    return edges


# =============================================================================
# FIXED INDICES
# =============================================================================

def _fixed_indices_ring(n_i, K, segment_types, M, centre_idx):
    """
    Fixed indices for a ring mesh.

    Boundary row is at j = 0 for each i. Boundary node i's
    flat index = i * (M - 1) + 0 = i * (M - 1).
    """
    boundary_fixed = _boundary_fixed_set(n_i, K, segment_types)
    return [i * (M - 1) for i in boundary_fixed]


def _fixed_indices_quad(n_i, K, segment_types, M):
    """
    Fixed indices for a quad mesh.

    Boundary row concept: not all four sides are in a single
    row. For simplicity, treat the four corner nodes and any
    node on a beam-classified side as fixed. This is the
    approximation used before; the full per-side fixed logic
    is deferred.
    """
    # For the quad case, fix the four corners plus boundary nodes
    # on the top (j=M-1) and bottom (j=0) rows.
    fixed = set()
    for i in range(n_i):
        fixed.add(i * M + 0)          # bottom row
        fixed.add(i * M + (M - 1))    # top row
    # Left and right sides:
    for j in range(M):
        fixed.add(0 * M + j)
        fixed.add((n_i - 1) * M + j)
    return sorted(fixed)


def _fixed_indices_twosided(n_i, K, segment_types, M, topo_info):
    """
    Fixed indices for a twosided mesh.

    Fixed nodes:
        - P0 and P1 (always).
        - All nodes in the interior grid that lie on a beam or
          wall segment along either curve.

    In the twosided layout, the "curve A" boundary is at
    j = 0 in the interior grid; the "curve B" boundary is at
    j = M-1. Both boundaries are held if the corresponding
    segment is beam or wall.
    """
    n_interior = topo_info["n_interior"]
    p0_idx = topo_info["tip_P0_idx"]
    p1_idx = topo_info["tip_P1_idx"]

    fixed = {p0_idx, p1_idx}

    # For each interior column i, decide whether the node on
    # curve A (j=0) and on curve B (j=M-1) is held.
    for i in range(n_interior):
        # Segment index along curve A: i // K
        seg_A = i // K
        if seg_A >= len(segment_types):
            seg_A = len(segment_types) - 1
        # Curve B is traversed in the opposite direction, so
        # segment index counts from the other end.
        seg_B = (n_interior - 1 - i) // K
        if seg_B >= len(segment_types):
            seg_B = len(segment_types) - 1

        # Curve A node (j=0).
        if segment_types[seg_A] in ("beam", "wall"):
            fixed.add(1 + i * M + 0)
        # Curve B node (j=M-1).
        if segment_types[seg_B] in ("beam", "wall"):
            fixed.add(1 + i * M + (M - 1))

    return sorted(fixed)


def _boundary_fixed_set(n_i, K, segment_types):
    """Helper: boundary-row indices that are held. Used by ring."""
    fixed = set()
    n_anchors = len(segment_types)
    for i in range(n_i):
        seg_index = i // K
        if seg_index >= n_anchors:
            seg_index = n_anchors - 1
        is_anchor = (i % K == 0)
        seg_type = segment_types[seg_index]
        if is_anchor:
            fixed.add(i)
        else:
            if seg_type in ("beam", "wall"):
                fixed.add(i)
    return sorted(fixed)


# =============================================================================
# Q ASSIGNMENT
# =============================================================================

def _q_ring(edges, n_i, M, K, segment_types,
            warp_q, weft_q, edge_q, centre_idx):
    """Q for a ring mesh."""
    n_anchors = len(segment_types)
    q = np.zeros(len(edges))
    for k, (a, b) in enumerate(edges):
        if a == centre_idx or b == centre_idx:
            q[k] = float(weft_q)
            continue
        ia = a // (M - 1)
        ja = a % (M - 1)
        jb = b % (M - 1)
        if ja == jb:
            seg_index = ia // K
            if seg_index >= n_anchors:
                seg_index = n_anchors - 1
            seg_type = segment_types[seg_index]
            q[k] = float(edge_q) if seg_type == "cable" else float(warp_q)
        else:
            q[k] = float(weft_q)
    return q


def _q_quad(edges, n_i, M, K, segment_types,
            warp_q, weft_q, edge_q):
    """Q for a quad mesh."""
    n_anchors = len(segment_types)
    q = np.zeros(len(edges))
    for k, (a, b) in enumerate(edges):
        ia = a // M
        ja = a % M
        jb = b % M
        if ja == jb:
            seg_index = ia // K
            if seg_index >= n_anchors:
                seg_index = n_anchors - 1
            seg_type = segment_types[seg_index]
            q[k] = float(edge_q) if seg_type == "cable" else float(warp_q)
        else:
            q[k] = float(weft_q)
    return q


def _q_twosided(edges, n_i, M, K, segment_types,
                warp_q, weft_q, edge_q, topo_info):
    """Q for a twosided mesh."""
    n_interior = topo_info["n_interior"]
    p0_idx = topo_info["tip_P0_idx"]
    p1_idx = topo_info["tip_P1_idx"]
    n_anchors = len(segment_types)

    q = np.zeros(len(edges))
    for k, (a, b) in enumerate(edges):
        # Edges touching P0 or P1: weft (they run from tip to
        # the first interior column).
        if a == p0_idx or b == p0_idx or a == p1_idx or b == p1_idx:
            q[k] = float(weft_q)
            continue

        # Interior edges. If a and b are on the same column (i),
        # this is a transverse (weft) edge. If they are on the
        # same row (j), this is a curve-direction (warp or edge)
        # edge.
        ia = (a - 1) // M
        ib = (b - 1) // M
        ja = (a - 1) % M
        jb = (b - 1) % M

        if ia == ib:
            # Transverse edge (weft).
            q[k] = float(weft_q)
        else:
            # Curve-direction edge. On j = 0 it is curve A; on
            # j = M-1 it is curve B.
            if ja == 0:
                seg_index = ia // K
                if seg_index >= n_anchors:
                    seg_index = n_anchors - 1
                seg_type = segment_types[seg_index]
                q[k] = float(edge_q) if seg_type == "cable" else float(warp_q)
            elif ja == M - 1:
                seg_index = (n_interior - 1 - ia) // K
                if seg_index >= n_anchors:
                    seg_index = n_anchors - 1
                seg_type = segment_types[seg_index]
                q[k] = float(edge_q) if seg_type == "cable" else float(warp_q)
            else:
                # Interior j. Warp.
                q[k] = float(warp_q)
    return q





# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def build_mesh_universal(topology,
                         curves=None,
                         corner_points=None,
                         segment_types=None,
                         subdivisions_per_segment=5,
                         transverse_count=8,
                         warp_q=2.0,
                         weft_q=2.0,
                         edge_q=5.0):
    """
    Build a mesh from a boundary region using one of three
    topologies. See engine/SPEC_mesh_topology.md.

    Parameters
    ----------
    topology : str
        "twosided" | "ring" | "quad"

    curves : list of curve point arrays
        twosided: [curve_A (P0 -> P1), curve_B (P1 -> P0)]
        ring:     [curve_loop]
        quad:     [side_A, side_B, side_C, side_D]

    corner_points : list of 3D point tuples
        twosided: [tip_P0, tip_P1]
        ring:     []
        quad:     [P00, P10, P11, P01]

    segment_types : list of str
        One per segment. Values: "beam", "cable", "wall".
        For twosided: the segments along curve A, then curve B.
        For ring: the segments around the loop.
        For quad: the segments along side A, then B, C, D.

    subdivisions_per_segment : int, K
        Nodes per segment along a boundary curve.

    transverse_count : int, M
        Nodes across the region from curve A to curve B (or
        boundary to centre for ring).

    warp_q, weft_q, edge_q : float
        Force densities (N/m). Assigned per edge by the mesher.

    Returns
    -------
    dict with keys:
        points         : (n_nodes, 3) array
        edges          : list of (i, j) tuples
        fixed_indices  : list of FLAT node indices for solve_fdm
        q              : (n_edges,) array of force densities
        diagnostics    : dict
    """
    _validate_topology(topology)
    K = int(subdivisions_per_segment)
    M = int(transverse_count)
    _validate_density(K, M)

    if curves is None:
        curves = []
    if corner_points is None:
        corner_points = []
    if segment_types is None:
        segment_types = []

    # ------------------------------------------------------------------
    # Dispatch on topology.
    # ------------------------------------------------------------------
    if topology == "twosided":
        if len(curves) != 2:
            raise ValueError(
                "twosided requires 2 curves (got %d)" % len(curves)
            )
        if len(corner_points) != 2:
            raise ValueError(
                "twosided requires 2 corner_points (got %d)"
                % len(corner_points)
            )
        curve_A = _validate_curve(curves[0], "curve_A")
        curve_B = _validate_curve(curves[1], "curve_B")
        tip_P0 = np.asarray(corner_points[0], dtype=float)
        tip_P1 = np.asarray(corner_points[1], dtype=float)

        n_segments = (curve_A.shape[0] - 1) + (curve_B.shape[0] - 1)
        _validate_segment_types(segment_types, n_segments)

        points, n_i, n_nodes, has_centre, centre_idx, topo_info = \
            _mesh_twosided(curve_A, curve_B, tip_P0, tip_P1, K, M)

        edges = _edges_twosided(n_i, M, n_nodes)
        fixed_indices = _fixed_indices_twosided(
            n_i, K, segment_types, M, topo_info
        )
        q = _q_twosided(edges, n_i, M, K, segment_types,
                        warp_q, weft_q, edge_q, topo_info)

    elif topology == "ring":
        if len(curves) != 1:
            raise ValueError(
                "ring requires 1 curve (got %d)" % len(curves)
            )
        curve_loop = _validate_curve(curves[0], "curve_loop")
        n_segments = curve_loop.shape[0]
        _validate_segment_types(segment_types, n_segments)

        points, n_i, n_nodes, has_centre, centre_idx, topo_info = \
            _mesh_ring(curve_loop, K, M)

        edges = _edges_ring(n_i, M, centre_idx)
        fixed_indices = _fixed_indices_ring(
            n_i, K, segment_types, M, centre_idx
        )
        q = _q_ring(edges, n_i, M, K, segment_types,
                    warp_q, weft_q, edge_q, centre_idx)





