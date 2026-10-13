"""Multi-Cone Roof — Stage 3 Lab test page.

Version v20.

What is new in v20:
  - Back buttons at the top: "Back to Lab" and "Back to Landing".
    This stops the page from idling and prevents the Streamlit
    sleep problem.
  - The edge cable is recorded as a member in the schedule:
      "Edge_Cable" (consolidated, total arclength)
      "Edge_Cable_Seg_<k>" (per segment between anchors)
  - The membrane is recorded as panels in the schedule:
      "Membrane_Panel_<n>" (one per fabric triangle)
    Each panel carries its warp and weft prestress.
  - A Q summary in Diagnostics: membrane area, cable length,
    cable/membrane q ratio.

Carried over from v19:
  - Fabric attaches directly to ring polygon nodes.

Carried over from v18:
  - Laplace lift with ring polygon nodes as boundary conditions.
  - Anisotropic warp/weft blend on interior edges.
  - Direct edge cable q from the slider.

Carried over from v14:
  - Cone placement by a single spacing input.
  - Refuse rule if any ring falls outside the span.

No other engine files are modified.
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm
from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
)


RIB_SEGMENTS = 80
RING_NODES_MIN = 12
RING_NODES_MAX = 32

COL_MEMBRANE = "#4a7a9c"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"


# =============================================================================
# Geometry helpers
# =============================================================================

def _ellipse_y(x, span, mid_width):
    a = span / 2.0
    b = mid_width / 2.0
    t = max(0.0, 1.0 - (x / a) ** 2)
    return b * math.sqrt(t)


def _rib_stations(n, optional_ends, span, x, s, total):
    if (not optional_ends) or n < 3:
        fracs = np.array([k / (n + 1.0) for k in range(1, n + 1)], dtype=float)
        return np.interp(fracs * total, s, x)
    xt = span / 2.0 - 3.0
    return np.linspace(-xt, +xt, n)


def _rib_arch_y_at_eave(peak_z, half_width, eave_height):
    if peak_z <= eave_height:
        return None
    u2 = 1.0 - eave_height / peak_z
    if u2 < 0.0:
        return None
    return half_width * math.sqrt(u2)


def _rib_polyline(rib_x, half_width, peak_z, n):
    y = np.linspace(-half_width, +half_width, n)
    u = y / half_width
    z = peak_z * (1.0 - u ** 2)
    x = np.full_like(y, rib_x)
    return np.column_stack([x, y, z])


def _tip_x_at_eave(span, apex, eave_height, curve_type):
    if apex <= eave_height:
        return span / 2.0
    x_fine = np.linspace(0.0, span / 2.0, 2000)
    z_fine = beam_curve(x_fine, span, apex, curve_type)
    idx = np.where(z_fine >= eave_height)[0]
    if len(idx) == 0:
        return span / 2.0
    return float(x_fine[idx[-1]])


def _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height,
                         tip_x):
    plus, minus = [], []
    for i, xr in enumerate(rib_x):
        y_at = _rib_arch_y_at_eave(
            float(rib_peak_z[i]), float(rib_half_width[i]), eave_height
        )
        if y_at is None:
            continue
        plus.append((float(xr), +y_at, eave_height))
        minus.append((float(xr), -y_at, eave_height))
    pts = list(plus)
    pts.append((+tip_x, 0.0, eave_height))
    for p in reversed(minus):
        pts.append(p)
    pts.append((-tip_x, 0.0, eave_height))
    return np.asarray(pts, dtype=float)


def _subdivide_polygon(anchors, subdivisions):
    n_a = anchors.shape[0]
    loop = []
    anchor_idx = []
    for i in range(n_a):
        a = anchors[i]
        b = anchors[(i + 1) % n_a]
        anchor_idx.append(len(loop))
        for k in range(subdivisions):
            f = k / float(subdivisions)
            loop.append(a + (b - a) * f)
    return np.asarray(loop, dtype=float), anchor_idx


def _eave_tangents(loop):
    n = loop.shape[0]
    tangents = np.zeros((n, 3), dtype=float)
    for i in range(n):
        a = loop[(i - 1) % n]
        b = loop[(i + 1) % n]
        t = b - a
        tn = float(np.linalg.norm(t))
        if tn < 1e-12:
            tangents[i] = np.array([1.0, 0.0, 0.0])
        else:
            tangents[i] = t / tn
    return tangents


def _point_in_polygon(x, y, poly):
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


def _ring_node_count(r, target_len):
    n = int(round(2.0 * math.pi * r / max(target_len, 1e-6)))
    n = max(RING_NODES_MIN, min(RING_NODES_MAX, n))
    return n


def _cone_arc_positions(n_cones, spacing, total):
    if n_cones < 1:
        raise ValueError("Number of cones must be at least 1.")
    mid = total / 2.0
    if n_cones % 2 == 1:
        half = (n_cones - 1) // 2
        ks = [0]
        for i in range(1, half + 1):
            ks.append(+i)
            ks.append(-i)
    else:
        half = n_cones // 2
        ks = []
        for i in range(half):
            k = i + 0.5
            ks.append(+k)
            ks.append(-k)
    positions = [mid + k * spacing for k in ks]
    for p in positions:
        if p < 0.0 or p > total:
            raise ValueError(
                "Ring position %.3f m falls outside the primary span "
                "of %.3f m.  Reduce spacing or cone count." % (p, total)
            )
    return sorted(positions)


def _max_spacing_for(n_cones, total):
    if n_cones <= 1:
        return float("inf")
    mid = total / 2.0
    if n_cones % 2 == 1:
        k_max = (n_cones - 1) // 2
    else:
        k_max = (n_cones - 1) / 2.0
    if k_max <= 0:
        return float("inf")
    return mid / k_max


# =============================================================================
# ANISOTROPIC WARP / WEFT BLEND
# =============================================================================

def _blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q):
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
# LAPLACE LIFT
# =============================================================================

def _laplace_lift_fabric(all_pts, n_perimeter, boundary_z_map):
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
# MESH BUILDER (v20 — same as v19)
# =============================================================================

def _build_cone_mesh(perimeter_loop, anchor_idx, ring_specs,
                      eave_height, target_len):
    from scipy.spatial import Delaunay

    poly_xy = perimeter_loop[:, :2]
    ring_centres_radii = [(float(s["cx"]), float(s["cy"]), float(s["r"]))
                          for s in ring_specs]

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
            if not _point_in_polygon(x, y, poly_xy):
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
        n_poly = _ring_node_count(r, target_len)
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

    z_all = _laplace_lift_fabric(all_pts, n_perimeter, boundary_z_map)
    all_pts[:, 2] = z_all

    pts_2d = all_pts[:, :2]
    tri = Delaunay(pts_2d[:fabric_end])

    triangles = []
    for simplex in tri.simplices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        cen = (pts_2d[a] + pts_2d[b] + pts_2d[c]) / 3.0
        if not _point_in_polygon(cen[0], cen[1], poly_xy):
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
# Member schedule (v20 — includes edge cable and membrane panels)
# =============================================================================

def _build_member_schedule(built, coords, ring_x_positions,
                            anchor_idx, edge_q_scalar,
                            warp_q, weft_q):
    members = []
    ring_indices = built["ring_indices"]
    centre_indices = built["centre_indices"]
    beam_top_indices = built["beam_top_indices"]
    triangles = built["triangles"]
    n_perimeter = built["n_perimeter"]
    boundary_edges = built["boundary_edges"]

    # ---- Ring steel members ----
    for k in range(len(ring_indices)):
        ring_no = k + 1
        idx_list = ring_indices[k]
        centre_i = int(centre_indices[k])
        beam_i = int(beam_top_indices[k])
        n_poly = len(idx_list)

        ring_length = 0.0
        for i in range(n_poly):
            a = int(idx_list[i])
            b = int(idx_list[(i + 1) % n_poly])
            ring_length += float(np.linalg.norm(coords[b] - coords[a]))
        members.append({
            "member_id": f"Ring_{ring_no}_Ring_Beam",
            "member_type": "ring_beam",
            "ring_index": ring_no,
            "node_a": int(idx_list[0]),
            "node_b": int(idx_list[0]),
            "length_m": float(ring_length),
            "section": "TBD", "material": "TBD",
            "role": "closed ring beam, one per cone",
        })
        for i in range(n_poly):
            a = int(idx_list[i]); b = int(idx_list[(i + 1) % n_poly])
            L = float(np.linalg.norm(coords[b] - coords[a]))
            members.append({
                "member_id": f"Ring_{ring_no}_Beam_Seg_{i+1:02d}",
                "member_type": "ring_beam_segment",
                "ring_index": ring_no,
                "node_a": a, "node_b": b, "length_m": L,
                "section": "TBD", "material": "TBD",
                "role": "ring beam segment between adjacent nodes",
            })
        for i, node_i in enumerate(idx_list):
            node_i = int(node_i)
            L = float(np.linalg.norm(coords[node_i] - coords[centre_i]))
            members.append({
                "member_id": f"Ring_{ring_no}_Spoke_{i+1:02d}",
                "member_type": "spoke",
                "ring_index": ring_no,
                "node_a": centre_i, "node_b": node_i, "length_m": L,
                "section": "TBD", "material": "TBD",
                "role": "radial spoke from ring centre to ring circle",
            })
        L = float(np.linalg.norm(coords[beam_i] - coords[centre_i]))
        members.append({
            "member_id": f"Ring_{ring_no}_Drop_Member",
            "member_type": "drop_member",
            "ring_index": ring_no,
            "node_a": beam_i, "node_b": centre_i, "length_m": L,
            "section": "TBD", "material": "TBD",
            "role": "vertical drop member from primary beam to ring centre",
        })

    # ---- Edge cable member (consolidated) ----
    total_cable_length = 0.0
    for i in range(n_perimeter):
        j = (i + 1) % n_perimeter
        total_cable_length += float(np.linalg.norm(coords[j] - coords[i]))
    members.append({
        "member_id": "Edge_Cable",
        "member_type": "cable",
        "ring_index": 0,
        "node_a": 0,
        "node_b": n_perimeter - 1,
        "length_m": total_cable_length,
        "section": "CABLE",
        "material": "Steel strand",
        "role": "perimeter edge cable, consolidated arclength",
        "prestress": edge_q_scalar,
    })

    # Per-segment edge cable (one per anchor-to-anchor arc).
    # Anchors are the corners held fully; they are the vertices of
    # the input anchor loop. We record one segment between each
    # pair of consecutive anchors, following the perimeter.
    anchor_positions = [int(i) for i in anchor_idx]
    n_anchors = len(anchor_positions)
    for k in range(n_anchors):
        start = anchor_positions[k]
        end = anchor_positions[(k + 1) % n_anchors]
        seg_length = 0.0
        i = start
        while True:
            j = (i + 1) % n_perimeter
            seg_length += float(np.linalg.norm(coords[j] - coords[i]))
            if j == end:
                break
            i = j
            if i == start:
                break
        members.append({
            "member_id": f"Edge_Cable_Seg_{k+1:02d}",
            "member_type": "cable_segment",
            "ring_index": 0,
            "node_a": start,
            "node_b": end,
            "length_m": seg_length,
            "section": "CABLE",
            "material": "Steel strand",
            "role": "edge cable segment between anchors",
            "prestress": edge_q_scalar,
        })

    # ---- Membrane panels (one per fabric triangle) ----
    panel_no = 1
    for (a, b, c) in triangles:
        pa = coords[a]
        pb = coords[b]
        pc = coords[c]
        mean_edge = (
            float(np.linalg.norm(pb - pa))
            + float(np.linalg.norm(pc - pb))
            + float(np.linalg.norm(pa - pc))
        ) / 3.0
        members.append({
            "member_id": f"Membrane_Panel_{panel_no:04d}",
            "member_type": "membrane",
            "ring_index": 0,
            "node_a": int(a),
            "node_b": int(b),
            "node_c": int(c),
            "length_m": mean_edge,
            "section": "FABRIC",
            "material": "PVDF Type III",
            "role": "fabric panel between ridge and eave",
            "prestress_warp": warp_q,
            "prestress_weft": weft_q,
        })
        panel_no += 1

    return members


def _format_member_table(members):
    lines = []
    header = (
        "%-26s  %-18s  %-6s  %-6s  %-6s  %-9s  %-8s  %-14s  %s"
        % ("member_id", "member_type", "ring", "node_a", "node_b",
           "length_m", "section", "material", "role")
    )
    lines.append(header)
    lines.append("-" * len(header))
    for m in members:
        lines.append(
            "%-26s  %-18s  %-6d  %-6d  %-6d  %-9.4f  %-8s  %-14s  %s"
            % (m["member_id"], m["member_type"], m.get("ring_index", 0),
               m["node_a"], m["node_b"], m["length_m"],
               m["section"], m["material"], m["role"])
        )
    return "\n".join(lines)


_HEADER = (
    "%6s  %10s  %10s  %10s  %10s  %10s  %10s  %9s  %s"
    % ("idx", "x_init", "y_init", "z_init",
       "x_set", "y_set", "z_set", "disp", "status")
)


def _status_line(i, status, points_initial, points_settled):
    xi, yi, zi = points_initial[i]
    xs, ys, zs = points_settled[i]
    d = float(np.linalg.norm(np.array([xs - xi, ys - yi, zs - zi])))
    return (
        "%6d  %10.5f  %10.5f  %10.5f  %10.5f  %10.5f  %10.5f  %9.4e  %s"
        % (i, xi, yi, zi, xs, ys, zs, d, status)
    )


def _format_all_nodes(points_initial, points_settled, anchor_idx,
                       ring_indices, centre_indices, beam_top_indices,
                       intermediate_perimeter_set):
    n = points_initial.shape[0]
    status_of = ["free"] * n
    for i in anchor_idx:
        status_of[int(i)] = "held_outer_eave_corner"
    for i in intermediate_perimeter_set:
        status_of[int(i)] = "eave_cable_dir_only"
    for idx_list in ring_indices:
        for i in idx_list:
            status_of[int(i)] = "held_ring_polygon"
    for i in centre_indices:
        status_of[int(i)] = "held_ring_centre"
    for i in beam_top_indices:
        status_of[int(i)] = "held_beam_top"
    lines = [_HEADER, "-" * len(_HEADER)]
    for i in range(n):
        lines.append(_status_line(i, status_of[i],
                                   points_initial, points_settled))
    return "\n".join(lines)


# =============================================================================
# Page
# =============================================================================

def render_tester_multi_cone():
    # ---- Back buttons (v20) ----
    bcol1, bcol2, bcol3 = st.columns([1, 1, 3])
    with bcol1:
        if st.button("← Back to Lab", key="mc_back_lab",
                     use_container_width=True):
            st.session_state.page = "lab"
            st.rerun()
    with bcol2:
        if st.button("← Back to Landing", key="mc_back_landing",
                     use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()

    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>v20 — edge cable and "
        "membrane recorded as members.</p>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        span = st.number_input("Primary span (m)", 6.0, 60.0, 25.0, 0.5,
                                key="mc_span")
    with c2:
        apex = st.number_input("Primary apex (m)", 1.0, 30.0, 9.0, 0.5,
                                key="mc_apex")

    c1, c2 = st.columns(2)
    with c1:
        mid_width = st.number_input("Mid-span width (m)", 6.0, 60.0, 18.0, 0.5,
                                     key="mc_width")
    with c2:
        eave_height = st.number_input("Eave height (m)", 0.5, 10.0, 2.8, 0.1,
                                       key="mc_eave")

    c1, c2 = st.columns(2)
    with c1:
        ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 1.0, 0.1,
                                         key="mc_rd")
    with c2:
        curve_type = st.selectbox(
            "Curve type", ["parabolic", "circular", "catenary"],
            index=0, key="mc_curve",
        )

    c1, c2 = st.columns(2)
    with c1:
        secondary_count = int(st.number_input("Secondary count", 2, 20, 3, 1,
                                                key="mc_nribs"))
    with c2:
        optional_ends = st.toggle("Optional ends", value=False,
                                    key="mc_optends")

    subdivisions = int(st.number_input(
        "Subdivisions per edge", 5, 25, 17, 1, key="mc_subdiv"
    ))

    c1, c2 = st.columns(2)
    with c1:
        number_of_cones = int(st.number_input(
            "Number of cones", 1, 20, 3, 1, key="mc_ncones"
        ))
    with c2:
        ring_spacing = st.number_input(
            "Distance between adjacent cones (m, along beam)",
            0.5, 10.0, 5.0, 0.1, key="mc_spacing"
        )

    ring_clearance = st.number_input(
        "Ring clearance below beam (m)", 0.1, 5.0, 1.0, 0.1,
        key="mc_clr",
    )

    c1, c2 = st.columns(2)
    with c1:
        warp_q_input = st.number_input(
            "Warp pretension (kN/m)", 0.1, 100.0, 20.0, 0.1, key="mc_warp",
        )
    with c2:
        weft_q_input = st.number_input(
            "Weft pretension (kN/m)", 0.1, 100.0, 20.0, 0.1, key="mc_weft",
        )

    edge_q_input = st.number_input(
        "Edge cable pretension (kN/m)",
        0.1, 500.0, 0.1, 0.1,
        key="mc_edgeq",
    )

    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array(
        [_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float
    )

    placement_error = ""
    ring_specs = []
    s_rings = []
    x_rings = []
    ring_z_rings = []

    max_spacing = _max_spacing_for(number_of_cones, total_p)
    try:
        s_rings = _cone_arc_positions(number_of_cones, ring_spacing, total_p)
        for s_val in s_rings:
            x_val = float(np.interp(s_val, s_p, xp))
            bz_val = float(np.interp(s_val, s_p, zp))
            rz_val = bz_val - float(ring_clearance)
            x_rings.append(x_val)
            ring_z_rings.append(rz_val)
            ring_specs.append({
                "cx": x_val, "cy": 0.0, "cz": rz_val,
                "r": float(ring_diameter) / 2.0,
                "beam_z": bz_val,
            })
    except ValueError as e:
        placement_error = str(e)

    if placement_error:
        st.error("Placement refused: " + placement_error)
        return

    tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
    anchors = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, tip_x
    )
    perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
    bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
    L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
    target_len = max(L_avg, 1e-6)

    built = _build_cone_mesh(
        perimeter_loop, anchor_idx, ring_specs,
        eave_height, target_len,
    )

    pts = built["points"]
    edges = built["edges"]
    boundary_edge_set = built["boundary_edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]

    n_perimeter = built["n_perimeter"]
    anchor_set = set(int(i) for i in anchor_idx)
    intermediate_perimeter = [
        i for i in range(n_perimeter) if i not in anchor_set
    ]
    tangents = _eave_tangents(perimeter_loop)
    dir_only_list = []
    for i in intermediate_perimeter:
        t = tangents[i]
        dir_only_list.append((i, (float(t[0]), float(t[1]), float(t[2]))))
    fixed = [i for i in fixed if i not in set(intermediate_perimeter)]

    warp_q = max(float(warp_q_input), 0.1) * 1000.0
    weft_q = max(float(weft_q_input), 0.1) * 1000.0
    edge_q_scalar = max(float(edge_q_input), 0.1) * 1000.0

    pts_2d = pts[:, :2]
    warp_dir = np.array([1.0, 0.0])
    q_interior = _blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q)

    q = np.empty(len(edges), dtype=float)
    for k, (i, j) in enumerate(edges):
        key = (i, j) if i < j else (j, i)
        if key in boundary_edge_set:
            q[k] = edge_q_scalar
        else:
            q[k] = q_interior[k]

    try:
        fdm = solve_fdm(pts, edges, fixed, q,
                        dir_only_indices=dir_only_list)
        coords = fdm["coordinates"]
        residual_norm = float(fdm["residual_norm"])
        solve_ok = True
        solve_err = ""
        dof_count = int(fdm.get("dof_count", 0))
    except Exception as e:
        coords = pts.copy()
        residual_norm = float("nan")
        solve_ok = False
        solve_err = str(e)
        dof_count = 0

    fig = go.Figure()

    if len(tris) > 0:
        tri = np.asarray(tris, dtype=int)
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            name="membrane", showlegend=False, hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter3d(
        x=xp, y=np.zeros_like(xp), z=zp,
        mode="lines", line=dict(color=COL_PRIMARY, width=7),
        name="primary beam", showlegend=False, hoverinfo="skip",
    ))

    for i in range(len(rib_x)):
        rp = _rib_polyline(
            float(rib_x[i]), float(rib_half_width[i]),
            float(rib_peak_z[i]), RIB_SEGMENTS,
        )
        fig.add_trace(go.Scatter3d(
            x=rp[:, 0], y=rp[:, 1], z=rp[:, 2],
            mode="lines", line=dict(color=COL_RIB, width=5),
            name="rib", showlegend=False, hoverinfo="skip",
        ))

    for k, idx_list in enumerate(built["ring_indices"]):
        pp = coords[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name="ring", showlegend=False, hoverinfo="skip",
        ))
        centre_i = built["centre_indices"][k]
        beam_i = built["beam_top_indices"][k]
        cx, cy, cz = coords[centre_i]
        for poly_i in idx_list:
            fig.add_trace(go.Scatter3d(
                x=[cx, coords[poly_i, 0]],
                y=[cy, coords[poly_i, 1]],
                z=[cz, coords[poly_i, 2]],
                mode="lines", line=dict(color=COL_SPOKE, width=2),
                name="spoke", showlegend=False, hoverinfo="skip",
            ))
        bx, by, bz = coords[beam_i]
        fig.add_trace(go.Scatter3d(
            x=[cx, bx], y=[cy, by], z=[cz, bz],
            mode="lines", line=dict(color=COL_DROP, width=4),
            name="drop", showlegend=False, hoverinfo="skip",
        ))

    apply_common_layout(fig, apex)
    st.plotly_chart(fig, use_container_width=True, key="mc_3d")

    members = _build_member_schedule(
        built, coords, x_rings,
        anchor_idx, edge_q_scalar, warp_q, weft_q,
    )

    # ---- Member schedule summary ----
    with st.expander("Member schedule (BQ and analysis)", expanded=False):
        n_ring = sum(1 for m in members if m["member_type"] == "ring_beam")
        n_ring_seg = sum(1 for m in members
                         if m["member_type"] == "ring_beam_segment")
        n_spokes = sum(1 for m in members if m["member_type"] == "spoke")
        n_drops = sum(1 for m in members if m["member_type"] == "drop_member")
        n_cables = sum(1 for m in members
                       if m["member_type"] in ("cable", "cable_segment"))
        n_panels = sum(1 for m in members if m["member_type"] == "membrane")

        st.write(f"Total members recorded: {len(members)}")
        st.write(
            f"Counts: {n_ring} ring beam (consolidated), "
            f"{n_ring_seg} ring beam segments, "
            f"{n_spokes} spokes, "
            f"{n_drops} drop members, "
            f"{n_cables} edge cable members "
            f"(1 consolidated + segments), "
            f"{n_panels} membrane panels."
        )
        st.code(_format_member_table(members), language="text")

    with st.expander("Diagnostics", expanded=True):
        st.write(f"Version: v20 (edge cable + membrane as members)")
        st.write(f"Number of cones: {number_of_cones}")
        st.write(f"Ring x positions (m): " +
                 ", ".join(f"{v:+.3f}" for v in x_rings))
        st.write(f"Ring z positions (m): " +
                 ", ".join(f"{v:.3f}" for v in ring_z_rings))
        st.write(f"Outer eave corners held: {anchors.shape[0]}")
        st.write(f"Perimeter nodes: {perimeter_loop.shape[0]}")
        st.write(f"Eave cable dir_only nodes (free): {len(intermediate_perimeter)}")
        st.write(f"Total mesh nodes: {pts.shape[0]}")
        st.write(f"Mesh edges: {len(edges)}")
        st.write(f"Mesh triangles: {len(tris)}")
        st.write(f"Held nodes (total): {len(fixed)}")
        st.write(f"DOF count: {dof_count}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Solve error: {solve_err}")
        else:
            st.write(f"Raw force imbalance (N): {residual_norm:.6e}")
            st.write("(This number includes constraint reactions at "
                     "held and dir_only nodes. It is not a convergence "
                     "failure.)")
        st.write(f"Warp q (N/m): {warp_q:.1f}")
        st.write(f"Weft q (N/m): {weft_q:.1f}")
        st.write(f"Edge cable q (N/m): {edge_q_scalar:.1f}")
        st.write(f"Cable / membrane q ratio: "
                 f"{edge_q_scalar / max(warp_q, 1.0):.4f}")
        st.write(f"Target edge length: {target_len:.4f}")
        st.write("Ring node counts: " +
                 ", ".join(str(c) for c in built["ring_node_counts"]))

    with st.expander("All nodes (full digitisation)", expanded=False):
        st.code(
            _format_all_nodes(
                pts, coords, anchor_idx,
                built["ring_indices"],
                built["centre_indices"],
                built["beam_top_indices"],
                intermediate_perimeter,
            ),
            language="text",
        )


# =============================================================================
# END OF ui/workshops/tester_multi_cone.py
# =============================================================================
