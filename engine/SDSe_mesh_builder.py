# =============================================================================
# SDSe_mesh_builder.py
# =============================================================================
# Permanent, unified membrane mesh builder for all SDSe shapes.
#
# This module is the single source of truth for membrane meshing.
# It replaces several overlapping mesh builders that previously lived
# scattered across viewer files. See:
#
#     engine/SDSe_mesh_builder_SPEC.md
#
# for the full doctrine, the takeover sequence, and the audit trail.
#
# -----------------------------------------------------------------------------
# DOCTRINE (summary — full text in the SPEC)
# -----------------------------------------------------------------------------
#   1. This builder is permanent. It will serve every shape in the system.
#   2. Old builders are superseded one at a time, never deleted.
#   3. A shape switches to this builder only after a Lab proof that it
#      draws identically to the old one on the same inputs.
#   4. Nothing user-facing changes until the engine is proven in the Lab.
#   5. One file at a time. Named explicitly. Shown. Signed off.
#
# -----------------------------------------------------------------------------
# CONTRACT
# -----------------------------------------------------------------------------
# The engine is a mesh builder. It does not know what shape is being
# meshed, what a picker is, what a cone is, or what a spine is. It
# takes a geometry description and returns a mesh.
#
# The caller (a viewer file) assembles the inputs:
#
#     perimeter_loop    closed boundary of the membrane
#     anchor_idx        which perimeter nodes are held
#     ring_specs        one dict per ring hole
#     eave_height       z of the boundary
#     target_len        mesh density
#
# The engine returns points, edges, triangles, fixed set, boundary
# edges. The caller then runs the FDM solve and draws.
#
# -----------------------------------------------------------------------------
# PHYSICS — FROZEN FROM v21
# -----------------------------------------------------------------------------
# The core physics is a verbatim port of ui/workshops/tester_multi_cone.py
# v21 (2026-10-13). No re-derivation. No invention. The functions lifted
# and renamed with the SDSe_ prefix:
#
#     v21 name                      SDSe name
#     ------------                  ------------------------
#     _laplace_lift_fabric          SDSe_laplace_lift
#     _blend_q_per_edge             SDSe_blend_q_per_edge
#     _ring_node_count              SDSe_ring_node_count
#     _point_in_polygon             SDSe_point_in_polygon
#     _build_cone_mesh              SDSe_mesh_rings
#
# v21 physics preserved verbatim:
#   - Only structural anchors are held on the boundary.
#   - Every intermediate perimeter node is fully free (3 DOF).
#   - The perimeter cable bows by FDM, not by constraint.
#
# -----------------------------------------------------------------------------
# DELIVERED
# -----------------------------------------------------------------------------
#     SDSe_build_mesh              -- dispatcher
#     SDSe_mesh_rings              -- mesh with rings and holes, any shape
#     (shared core)                -- SDSe_laplace_lift, SDSe_blend_q_per_edge,
#                                     SDSe_ring_node_count,
#                                     SDSe_point_in_polygon
#
# NOT YET IMPLEMENTED (deferred):
#     SDSe_mesh_flat
#     SDSe_mesh_kader
#     SDSe_mesh_cable
#     SDSe_mesh_rings_cable
#
# -----------------------------------------------------------------------------
# HISTORY
# -----------------------------------------------------------------------------
#   2026-10-14 - v1. First SDSe component. Faithful port of v21
#                _build_cone_mesh, renamed with SDSe_ prefix.
#   2026-10-14 - Renamed SDSe_mesh_rings_spine to SDSe_mesh_rings.
#                The function was never spine-specific — it takes a
#                perimeter and rings, and meshes. Any shape can call it.
#                Dispatcher key renamed from "rings_spine" to "rings".
# =============================================================================

import math

import numpy as np


# =============================================================================
# CONSTANTS
# =============================================================================
# These match the constants used by v21. If a caller needs different
# values, they should pass them in — these are defaults.

SDSe_RING_NODES_MIN = 12
SDSe_RING_NODES_MAX = 32


# =============================================================================
# SHARED CORE — geometry helpers
# =============================================================================

def SDSe_point_in_polygon(x, y, poly):
    """
    Ray-cast point-in-polygon test in plan (XY plane).

    poly is an (n, 2) or (n, 3) array; only columns 0 and 1 are used.
    Returns True if (x, y) is inside the polygon.

    Verbatim port of v21 _point_in_polygon.
    """
    n = poly.shape[0]
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i, 0], poly[i, 1]
        xj, yj = poly[j, 0], poly[j, 1]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi
            if x < xint:
                inside = not inside
        j = i
    return inside


def SDSe_ring_node_count(r, target_len):
    """
    Adaptive node count for a ring of radius r, targeting
    edge length approximately equal to target_len.

    Verbatim port of v21 _ring_node_count.
    """
    n = int(round(2.0 * math.pi * r / max(target_len, 1e-6)))
    n = max(SDSe_RING_NODES_MIN, min(SDSe_RING_NODES_MAX, n))
    return n


# =============================================================================
# SHARED CORE — anisotropic warp / weft blend
# =============================================================================

def SDSe_blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q):
    """
    Anisotropic warp/weft force-density blend, per edge.

    For each edge, project its direction onto warp_dir. The q value is
    blended between warp_q and weft_q by cos^2 of the angle to warp_dir.
    Edges aligned with the warp direction get warp_q; edges perpendicular
    get weft_q; edges at an angle get a smooth blend.

    Verbatim port of v21 _blend_q_per_edge.
    """
    m = len(edges)
    q = np.zeros(m, dtype=float)
    warp_dir = np.asarray(warp_dir, dtype=float)
    wn = float(np.linalg.norm(warp_dir))
    if wn < 1e-12:
        warp_dir = np.array([1.0, 0.0])
    else:
        warp_dir = warp_dir / wn
    for k, (a, b) in enumerate(edges):
        pa = pts_2d[a]
        pb = pts_2d[b]
        d = pb - pa
        dn = float(np.linalg.norm(d))
        if dn < 1e-12:
            q[k] = float(warp_q)
            continue
        d = d / dn
        cos_t = float(np.dot(d, warp_dir))
        cos_t = max(-1.0, min(1.0, cos_t))
        c2 = cos_t * cos_t
        s2 = 1.0 - c2
        q[k] = float(warp_q) * c2 + float(weft_q) * s2
    return q


# =============================================================================
# SHARED CORE — Laplace lift
# =============================================================================

def SDSe_laplace_lift(all_pts, n_perimeter, boundary_z_map):
    """
    Laplace-lift the interior z coordinates so the membrane meets the
    boundary conditions (perimeter, ring polygon nodes, ring centres,
    beam tops) smoothly.

    all_pts           (n, 3) array. x, y used as mesh; z is the target.
    n_perimeter       first n_perimeter nodes are boundary nodes.
    boundary_z_map    dict {node_index: z_value} of fixed nodes.

    Returns a new z array of length n. Interior nodes are lifted to
    the Laplace solution; fixed nodes keep their prescribed z.

    Verbatim port of v21 _laplace_lift_fabric.
    """
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    from scipy.spatial import cKDTree

    n_nodes = all_pts.shape[0]
    pts_2d = all_pts[:, :2]

    is_fixed = np.zeros(n_nodes, dtype=bool)
    for i in boundary_z_map:
        is_fixed[i] = True
    for i in range(n_perimeter):
        is_fixed[i] = True

    tree = cKDTree(pts_2d)
    k = min(8, n_nodes - 1)
    if k < 1:
        return all_pts[:, 2].copy()

    dists, idxs = tree.query(pts_2d, k=k + 1)

    rows, cols, data = [], [], []
    for i in range(n_nodes):
        nbrs = idxs[i, 1:]
        degree = len(nbrs)
        if degree == 0:
            continue
        rows.append(i); cols.append(i); data.append(float(degree))
        for j in nbrs:
            rows.append(i); cols.append(int(j)); data.append(-1.0)

    L = sp.csr_matrix((data, (rows, cols)), shape=(n_nodes, n_nodes))

    int_idx = np.where(~is_fixed)[0]
    bnd_idx = np.where(is_fixed)[0]

    if len(int_idx) == 0:
        return all_pts[:, 2].copy()

    L_ii = L[int_idx, :][:, int_idx]
    L_ib = L[int_idx, :][:, bnd_idx]

    z_b = np.zeros(len(bnd_idx), dtype=float)
    for a, i in enumerate(bnd_idx):
        if int(i) in boundary_z_map:
            z_b[a] = float(boundary_z_map[int(i)])
        else:
            z_b[a] = float(all_pts[i, 2])

    rhs = -L_ib @ z_b
    try:
        z_int = spla.spsolve(L_ii.tocsc(), rhs)
    except Exception:
        z_int = np.zeros(len(int_idx))

    z_all = all_pts[:, 2].copy()
    for a in range(len(int_idx)):
        z_all[int(int_idx[a])] = float(z_int[a])
    return z_all


# =============================================================================
# BUILDER — rings and holes, any shape
# =============================================================================

def SDSe_mesh_rings(perimeter_loop, anchor_idx, ring_specs,
                    eave_height, target_len):
    """
    Build a membrane mesh with rings and holes, given a closed
    perimeter and a list of ring specifications.

    The function is not shape-specific. It takes a boundary and rings.
    Any shape with a closed perimeter and cone rings can call it:
    a spine with cones hanging off it, a dome with cones hanging off
    a frame grid, or anything else.

    Inputs
    ------
    perimeter_loop    (n_p, 3) closed loop, in order around the boundary.
    anchor_idx        list of indices into perimeter_loop that are
                      STRUCTURAL anchors (held). Intermediate perimeter
                      nodes are FREE.
    ring_specs        list of dicts, each with:
                        cx, cy  -- ring centre in plan
                        cz      -- ring z (bottom of drop member)
                        r       -- ring radius
                        beam_z  -- z of the attachment point
    eave_height       z of the boundary (perimeter).
    target_len        target edge length for adaptive meshing.

    Outputs
    -------
    dict with:
        points              (n, 3) all mesh nodes
        edges               list of (i, j) unique undirected edges
        boundary_edges      set of (i, j) sorted-tuple edges on the
                            perimeter and on ring polygons
        triangles           list of (a, b, c) Delaunay triangles after
                            filtering by polygon-in and ring-out
        fixed_indices       sorted list of held node indices
        ring_indices        list of lists, node indices per ring polygon
        centre_indices      list of node indices, ring centres
        beam_top_indices    list of node indices, attachment points
        ring_node_counts    list of node counts per ring
        n_perimeter         number of perimeter nodes
        n_interior          number of interior fabric nodes
        fabric_start        index of first fabric node
        fabric_end          index after last fabric node

    Verbatim port of v21 _build_cone_mesh.
    """
    from scipy.spatial import Delaunay

    poly_xy = perimeter_loop[:, :2]
    ring_centres_radii = [
        (float(s["cx"]), float(s["cy"]), float(s["r"]))
        for s in ring_specs
    ]

    xmin = float(np.min(perimeter_loop[:, 0]))
    xmax = float(np.max(perimeter_loop[:, 0]))
    ymin = float(np.min(perimeter_loop[:, 1]))
    ymax = float(np.max(perimeter_loop[:, 1]))

    h = float(target_len)
    xs = np.arange(xmin + 0.5 * h, xmax, h)
    ys = np.arange(ymin + 0.5 * h, ymax, h)

    clearance_band = 1.0 * target_len
    interior_xy = []
    for x in xs:
        for y in ys:
            if not SDSe_point_in_polygon(x, y, poly_xy):
                continue
            too_close = False
            for (cx, cy, r) in ring_centres_radii:
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if d < r + clearance_band:
                    too_close = True
                    break
            if too_close:
                continue
            interior_xy.append((float(x), float(y)))

    all_pts_list = [tuple(p) for p in perimeter_loop]
    n_perimeter = len(all_pts_list)

    ring_indices = []
    centre_indices = []
    beam_top_indices = []
    ring_node_counts = []

    for spec in ring_specs:
        cx = float(spec["cx"]); cy = float(spec["cy"])
        cz = float(spec["cz"]); r = float(spec["r"])
        n_poly = SDSe_ring_node_count(r, target_len)
        ring_node_counts.append(n_poly)
        t = np.linspace(0.0, 2.0 * math.pi, n_poly, endpoint=False)
        poly = np.column_stack([
            cx + r * np.cos(t),
            cy + r * np.sin(t),
            np.full(n_poly, cz, dtype=float),
        ])
        start = len(all_pts_list)
        for p in poly:
            all_pts_list.append(tuple(p))
        ring_indices.append(list(range(start, start + n_poly)))

        centre_indices.append(len(all_pts_list))
        all_pts_list.append((cx, cy, cz))

        beam_top_indices.append(len(all_pts_list))
        all_pts_list.append((cx, cy, float(spec["beam_z"])))

    fabric_start = len(all_pts_list)
    for (x, y) in interior_xy:
        all_pts_list.append((x, y, eave_height))
    fabric_end = len(all_pts_list)

    all_pts = np.asarray(all_pts_list, dtype=float)

    boundary_z_map = {}
    for i in range(n_perimeter):
        boundary_z_map[i] = float(eave_height)
    for k, spec in enumerate(ring_specs):
        cz = float(spec["cz"])
        for i in ring_indices[k]:
            boundary_z_map[int(i)] = cz
    for k, ci in enumerate(centre_indices):
        boundary_z_map[int(ci)] = float(ring_specs[k]["cz"])
    for k, bi in enumerate(beam_top_indices):
        boundary_z_map[int(bi)] = float(ring_specs[k]["beam_z"])

    z_all = SDSe_laplace_lift(all_pts, n_perimeter, boundary_z_map)
    all_pts[:, 2] = z_all

    pts_2d = all_pts[:, :2]
    tri = Delaunay(pts_2d[:fabric_end])

    triangles = []
    for simplex in tri.simplices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        cen = (pts_2d[a] + pts_2d[b] + pts_2d[c]) / 3.0
        if not SDSe_point_in_polygon(cen[0], cen[1], poly_xy):
            continue
        bad = False
        for (cx, cy, r) in ring_centres_radii:
            if ((cen[0] - cx) ** 2 + (cen[1] - cy) ** 2) < r * r:
                bad = True
                break
        if bad:
            continue
        triangles.append((a, b, c))

    boundary_edge_set = set()
    for i in range(n_perimeter):
        j = (i + 1) % n_perimeter
        key = (i, j) if i < j else (j, i)
        boundary_edge_set.add(key)

    all_edge_set = set()
    for (a, b, c) in triangles:
        for (p, q) in ((a, b), (b, c), (c, a)):
            key = (p, q) if p < q else (q, p)
            all_edge_set.add(key)
    for key in boundary_edge_set:
        all_edge_set.add(key)

    for k in range(len(ring_specs)):
        idx_list = ring_indices[k]
        centre_i = centre_indices[k]
        beam_i = beam_top_indices[k]
        n_poly = len(idx_list)
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            key = (a, b) if a < b else (b, a)
            all_edge_set.add(key)
            boundary_edge_set.add(key)
        for i in idx_list:
            key = (centre_i, i) if centre_i < i else (i, centre_i)
            all_edge_set.add(key)
        key = (centre_i, beam_i) if centre_i < beam_i else (beam_i, centre_i)
        all_edge_set.add(key)

    fixed = set(int(i) for i in anchor_idx)
    for idx_list in ring_indices:
        for i in idx_list:
            fixed.add(int(i))
    for ci in centre_indices:
        fixed.add(int(ci))
    for bi in beam_top_indices:
        fixed.add(int(bi))

    edges = sorted(all_edge_set)

    return {
        "points": all_pts,
        "edges": edges,
        "boundary_edges": boundary_edge_set,
        "triangles": triangles,
        "fixed_indices": sorted(fixed),
        "ring_indices": ring_indices,
        "centre_indices": centre_indices,
        "beam_top_indices": beam_top_indices,
        "ring_node_counts": ring_node_counts,
        "n_perimeter": n_perimeter,
        "n_interior": len(interior_xy),
        "fabric_start": fabric_start,
        "fabric_end": fabric_end,
    }


# =============================================================================
# DISPATCHER
# =============================================================================

def SDSe_build_mesh(shape, **kwargs):
    """
    Unified dispatcher for SDSe membrane meshing.

    Callers specify the shape by name and pass the kwargs the
    corresponding builder needs. The dispatcher routes to the correct
    builder. Unknown shapes raise NotImplementedError with a pointer
    to the SPEC.

    Recognised shapes
    -----------------
    "rings"    -> SDSe_mesh_rings
                  kwargs: perimeter_loop, anchor_idx, ring_specs,
                          eave_height, target_len

    Not yet implemented:
        "flat"           -- SDSe_mesh_flat
        "kader"          -- SDSe_mesh_kader
        "cable"          -> SDSe_mesh_cable
        "rings_cable"    -> SDSe_mesh_rings_cable
    """
    s = str(shape).strip().lower()

    if s == "rings":
        return SDSe_mesh_rings(
            perimeter_loop=kwargs["perimeter_loop"],
            anchor_idx=kwargs["anchor_idx"],
            ring_specs=kwargs["ring_specs"],
            eave_height=kwargs["eave_height"],
            target_len=kwargs["target_len"],
        )

    raise NotImplementedError(
        "SDSe_build_mesh: shape %r is not implemented. "
        "See engine/SDSe_mesh_builder_SPEC.md for the delivered "
        "builders." % (shape,)
    )


# =============================================================================
# END OF engine/SDSe_mesh_builder.py
# =============================================================================
