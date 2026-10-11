"""Multi-Cone Roof — Stage 3 Lab test page.

Version v14.

What is new in this version:
  - Spokes and drop members are drawn back in the viewer.
  - Every steel member (spoke, drop member, ring beam segment,
    ring beam consolidated) is recorded by name for BQ and analysis.

Members recorded per ring:
  - Ring beam:  one consolidated member per ring, plus N
                segment members between adjacent polygon nodes.
                Name:  Ring_<i>_Ring_Beam  and  Ring_<i>_Beam_Seg_<k>
  - Spokes:     one per ring polygon node.
                Name:  Ring_<i>_Spoke_<k>
  - Drop member: one per ring.
                Name:  Ring_<i>_Drop_Member

Member fields:
  member_id, member_type, ring_index, node_a, node_b,
  length_m, section, material, role

section and material are placeholders ("TBD") until the sizing
engine assigns them.

Carried over from v13:
  - Cone placement by a single spacing input.
  - Ring z follows the beam: z_ring = beam_z(s_ring) - clearance.
  - Refuse rule if any ring falls outside the span.
  - Per-cone widgets removed.  Three numbers control layout:
      number of cones, spacing, clearance.

No engine files are modified.
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding import solve_fdm
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


def _inside_any_ring(xy, rings):
    for (cx, cy, r) in rings:
        if (xy[0] - cx) ** 2 + (xy[1] - cy) ** 2 < r * r:
            return True
    return False


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

    interior_xy = []
    for x in xs:
        for y in ys:
            if not _point_in_polygon(x, y, poly_xy):
                continue
            if _inside_any_ring((x, y), ring_centres_radii):
                continue
            interior_xy.append((float(x), float(y)))

    def _nearest_ring(x, y):
        best_d = float("inf")
        best_z = eave_height
        for spec in ring_specs:
            cx = float(spec["cx"]); cy = float(spec["cy"])
            r = float(spec["r"]); cz = float(spec["cz"])
            d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) - r
            if d < best_d:
                best_d = d
                best_z = cz
        return max(best_d, 0.0), best_z

    def _z_at(x, y):
        d_ring, rz = _nearest_ring(x, y)
        d_perim = float(np.min(np.linalg.norm(
            poly_xy - np.array([x, y]), axis=1
        )))
        denom = d_ring + d_perim
        if denom < 1e-9:
            return float(rz)
        w = d_ring / denom
        return float(rz + (eave_height - rz) * w)

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
        all_pts_list.append((x, y, _z_at(x, y)))
    fabric_end = len(all_pts_list)

    all_pts = np.asarray(all_pts_list, dtype=float)
    pts_2d = all_pts[:, :2]

    tri = Delaunay(pts_2d[:fabric_end])
    triangles = []
    for simplex in tri.simplices:
        a, b, c = int(simplex[0]), int(simplex[1]), int(simplex[2])
        cen = (pts_2d[a] + pts_2d[b] + pts_2d[c]) / 3.0
        if not _point_in_polygon(cen[0], cen[1], poly_xy):
            continue
        if _inside_any_ring(cen, ring_centres_radii):
            continue
        if (_inside_any_ring(pts_2d[a], ring_centres_radii)
                or _inside_any_ring(pts_2d[b], ring_centres_radii)
                or _inside_any_ring(pts_2d[c], ring_centres_radii)):
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

    # --- Ring assembly edges -----------------------------------------
    for k in range(len(ring_specs)):
        idx_list = ring_indices[k]
        centre_i = centre_indices[k]
        beam_i = beam_top_indices[k]
        n_poly = len(idx_list)
        # Ring beam segments
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            key = (a, b) if a < b else (b, a)
            all_edge_set.add(key)
            boundary_edge_set.add(key)
        # Spokes
        for i in idx_list:
            key = (centre_i, i) if centre_i < i else (i, centre_i)
            all_edge_set.add(key)
        # Drop member
        key = (centre_i, beam_i) if centre_i < beam_i else (beam_i, centre_i)
        all_edge_set.add(key)

    # --- Fabric attachment -------------------------------------------
    attached_node_indices = set()
    ring_attach_counts = []
    ring_attach_edges_added = []
    fabric_indices = list(range(fabric_start, fabric_end))

    for k, spec in enumerate(ring_specs):
        cx = float(spec["cx"]); cy = float(spec["cy"])
        r = float(spec["r"]); cz = float(spec["cz"])
        idx_list = ring_indices[k]
        attached_here = set()
        edges_added_here = 0
        for poly_node in idx_list:
            px, py, pz = all_pts[poly_node]
            best = []
            for fi in fabric_indices:
                fx, fy, fz = all_pts[fi]
                d_plan = math.sqrt((fx - cx) ** 2 + (fy - cy) ** 2)
                if d_plan <= r:
                    continue
                d3 = math.sqrt((fx - px) ** 2 + (fy - py) ** 2
                                + (fz - pz) ** 2)
                best.append((d3, fi))
            best.sort()
            for (d3, fi) in best[:2]:
                key = (poly_node, fi) if poly_node < fi else (fi, poly_node)
                if key not in all_edge_set:
                    all_edge_set.add(key)
                    edges_added_here += 1
                attached_here.add(fi)
        ring_attach_counts.append(len(attached_here))
        ring_attach_edges_added.append(edges_added_here)
        attached_node_indices.update(attached_here)

    for i in attached_node_indices:
        fx, fy = all_pts[i, 0], all_pts[i, 1]
        best_d = float("inf")
        best_z = all_pts[i, 2]
        for spec in ring_specs:
            cx = float(spec["cx"]); cy = float(spec["cy"])
            r = float(spec["r"]); cz = float(spec["cz"])
            d = math.sqrt((fx - cx) ** 2 + (fy - cy) ** 2) - r
            if d < best_d:
                best_d = d
                best_z = cz
        all_pts[i, 2] = best_z

    edges = sorted(all_edge_set)

    fixed = set(int(i) for i in anchor_idx)
    for idx_list in ring_indices:
        for i in idx_list:
            fixed.add(int(i))
    for ci in centre_indices:
        fixed.add(int(ci))
    for bi in beam_top_indices:
        fixed.add(int(bi))
    for i in attached_node_indices:
        fixed.add(int(i))

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
        "attached_node_indices": sorted(attached_node_indices),
        "ring_attach_counts": ring_attach_counts,
        "ring_attach_edges_added": ring_attach_edges_added,
        "n_perimeter": n_perimeter,
        "n_interior": len(interior_xy),
        "fabric_start": fabric_start,
        "fabric_end": fabric_end,
    }


# --- Member schedule ---------------------------------------------------------

def _build_member_schedule(built, coords, ring_x_positions):
    """Return a list of named member records for BQ and analysis.

    Fields: member_id, member_type, ring_index, node_a, node_b,
            length_m, section, material, role
    """
    members = []
    ring_indices = built["ring_indices"]
    centre_indices = built["centre_indices"]
    beam_top_indices = built["beam_top_indices"]

    for k in range(len(ring_indices)):
        ring_no = k + 1
        idx_list = ring_indices[k]
        centre_i = int(centre_indices[k])
        beam_i = int(beam_top_indices[k])
        n_poly = len(idx_list)

        # Ring beam consolidated (one member for BQ).
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
            "section": "TBD",
            "material": "TBD",
            "role": "closed ring beam, one per cone",
        })

        # Ring beam segments (one per polygon node).
        for i in range(n_poly):
            a = int(idx_list[i])
            b = int(idx_list[(i + 1) % n_poly])
            L = float(np.linalg.norm(coords[b] - coords[a]))
            members.append({
                "member_id": f"Ring_{ring_no}_Beam_Seg_{i+1:02d}",
                "member_type": "ring_beam_segment",
                "ring_index": ring_no,
                "node_a": a,
                "node_b": b,
                "length_m": L,
                "section": "TBD",
                "material": "TBD",
                "role": "ring beam segment between adjacent nodes",
            })

        # Spokes: one per polygon node.
        for i, node_i in enumerate(idx_list):
            node_i = int(node_i)
            L = float(np.linalg.norm(coords[node_i] - coords[centre_i]))
            members.append({
                "member_id": f"Ring_{ring_no}_Spoke_{i+1:02d}",
                "member_type": "spoke",
                "ring_index": ring_no,
                "node_a": centre_i,
                "node_b": node_i,
                "length_m": L,
                "section": "TBD",
                "material": "TBD",
                "role": "radial spoke from ring centre to ring circle",
            })

        # Drop member: one per ring.
        L = float(np.linalg.norm(coords[beam_i] - coords[centre_i]))
        members.append({
            "member_id": f"Ring_{ring_no}_Drop_Member",
            "member_type": "drop_member",
            "ring_index": ring_no,
            "node_a": beam_i,
            "node_b": centre_i,
            "length_m": L,
            "section": "TBD",
            "material": "TBD",
            "role": "vertical drop member from primary beam to ring centre",
        })

    return members


def _format_member_table(members):
    lines = []
    header = (
        "%-28s  %-18s  %-5s  %-6s  %-6s  %-9s  %-7s  %-8s  %s"
        % ("member_id", "member_type", "ring", "node_a", "node_b",
           "length_m", "section", "material", "role")
    )
    lines.append(header)
    lines.append("-" * len(header))
    for m in members:
        lines.append(
            "%-28s  %-18s  %-5d  %-6d  %-6d  %-9.4f  %-7s  %-8s  %s"
            % (m["member_id"], m["member_type"], m["ring_index"],
               m["node_a"], m["node_b"], m["length_m"],
               m["section"], m["material"], m["role"])
        )
    return "\n".join(lines)


# --- Node digitisation -------------------------------------------------------

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
                       attached_set):
    n = points_initial.shape[0]
    status_of = ["free"] * n
    for i in anchor_idx:
        status_of[int(i)] = "held_perimeter_anchor"
    for idx_list in ring_indices:
        for i in idx_list:
            status_of[int(i)] = "held_ring_polygon"
    for i in centre_indices:
        status_of[int(i)] = "held_ring_centre"
    for i in beam_top_indices:
        status_of[int(i)] = "held_beam_top"
    for i in attached_set:
        status_of[int(i)] = "held_ring_attached"
    lines = [_HEADER, "-" * len(_HEADER)]
    for i in range(n):
        lines.append(_status_line(i, status_of[i],
                                   points_initial, points_settled))
    return "\n".join(lines)


# --- Page --------------------------------------------------------------------

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — multi-cone, steel "
        "member schedule.</p>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        span = st.number_input("Primary span (m)", 6.0, 60.0, 18.0, 0.5,
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
        ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 0.5, 0.1,
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
        "Subdivisions per edge", 5, 25, 11, 1, key="mc_subdiv"
    ))

    c1, c2 = st.columns(2)
    with c1:
        number_of_cones = int(st.number_input(
            "Number of cones", 1, 20, 3, 1, key="mc_ncones"
        ))
    with c2:
        ring_spacing = st.number_input(
            "Distance between adjacent cones (m, along beam)",
            0.5, 10.0, 3.0, 0.1, key="mc_spacing"
        )

    ring_clearance = st.number_input(
        "Ring clearance below beam (m)", 0.1, 5.0, 1.0, 0.1,
        key="mc_clr",
    )

    c1, c2 = st.columns(2)
    with c1:
        warp_q_input = st.number_input(
            "Warp pretension (kN/m)", 0.1, 100.0, 1.0, 0.1, key="mc_warp",
        )
    with c2:
        weft_q_input = st.number_input(
            "Weft pretension (kN/m)", 0.1, 100.0, 1.0, 0.1, key="mc_weft",
        )

    edge_q_input = st.number_input(
        "Edge cable pretension (kN/m, 0 = auto)", 0.0, 500.0, 20.0, 1.0,
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
    beam_z_rings = []
    ring_z_rings = []

    max_spacing = _max_spacing_for(number_of_cones, total_p)
    try:
        s_rings = _cone_arc_positions(number_of_cones, ring_spacing, total_p)
        for s_val in s_rings:
            x_val = float(np.interp(s_val, s_p, xp))
            bz_val = float(np.interp(s_val, s_p, zp))
            rz_val = bz_val - float(ring_clearance)
            x_rings.append(x_val)
            beam_z_rings.append(bz_val)
            ring_z_rings.append(rz_val)
            ring_specs.append({
                "cx": x_val,
                "cy": 0.0,
                "cz": rz_val,
                "r": float(ring_diameter) / 2.0,
                "beam_z": bz_val,
            })
    except ValueError as e:
        placement_error = str(e)

    if placement_error:
        st.error(
            "Placement refused: " + placement_error + "\n\n"
            "For %d cones on a primary of arc length %.3f m the maximum "
            "allowed spacing is %.3f m."
            % (number_of_cones, total_p, max_spacing)
        )
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

    warp_q = max(float(warp_q_input), 0.1) * 1000.0
    weft_q = max(float(weft_q_input), 0.1) * 1000.0
    if edge_q_input > 0.0:
        edge_q_scalar = float(edge_q_input) * 1000.0
    else:
        edge_q_scalar = max(warp_q, weft_q) * target_len
    edge_q_scalar = max(edge_q_scalar, 1.0)

    q = np.empty(len(edges), dtype=float)
    for k, (i, j) in enumerate(edges):
        key = (i, j) if i < j else (j, i)
        if key in boundary_edge_set:
            q[k] = edge_q_scalar
        else:
            q[k] = warp_q

    try:
        fdm = solve_fdm(pts, edges, fixed, q)
        coords = fdm["coordinates"]
        residual_norm = float(fdm["residual_norm"])
        solve_ok = True
        solve_err = ""
    except Exception as e:
        coords = pts.copy()
        residual_norm = float("nan")
        solve_ok = False
        solve_err = str(e)

    # --- Figure ------------------------------------------------------
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
            name=f"rib x={rib_x[i]:+.2f}", showlegend=False, hoverinfo="skip",
        ))

    for k, idx_list in enumerate(built["ring_indices"]):
        pp = coords[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name=f"ring {k+1}", showlegend=False, hoverinfo="skip",
        ))
        centre_i = built["centre_indices"][k]
        beam_i = built["beam_top_indices"][k]
        cx, cy, cz = coords[centre_i]
        # Spokes drawn
        for poly_i in idx_list:
            fig.add_trace(go.Scatter3d(
                x=[cx, coords[poly_i, 0]],
                y=[cy, coords[poly_i, 1]],
                z=[cz, coords[poly_i, 2]],
                mode="lines", line=dict(color=COL_SPOKE, width=2),
                name="spoke", showlegend=False, hoverinfo="skip",
            ))
        # Drop member drawn
        bx, by, bz = coords[beam_i]
        fig.add_trace(go.Scatter3d(
            x=[cx, bx], y=[cy, by], z=[cz, bz],
            mode="lines", line=dict(color=COL_DROP, width=4),
            name="drop", showlegend=False, hoverinfo="skip",
        ))

    apply_common_layout(fig, apex)
    st.plotly_chart(fig, use_container_width=True, key="mc_3d")

    # --- Member schedule --------------------------------------------
    members = _build_member_schedule(built, coords, x_rings)

    with st.expander("Steel member schedule (BQ and analysis)", expanded=False):
        st.write(f"Total members recorded: {len(members)}")
        st.write(
            "Counts: %d ring beam (consolidated), %d ring beam segments, "
            "%d spokes, %d drop members."
            % (
                sum(1 for m in members if m["member_type"] == "ring_beam"),
                sum(1 for m in members if m["member_type"] == "ring_beam_segment"),
                sum(1 for m in members if m["member_type"] == "spoke"),
                sum(1 for m in members if m["member_type"] == "drop_member"),
            )
        )
        st.code(_format_member_table(members), language="text")

    with st.expander("Diagnostics", expanded=False):
        st.write(f"Number of cones: {number_of_cones}")
        st.write(f"Spacing (m, along beam): {ring_spacing:.3f}")
        st.write(f"Primary arc length (m): {total_p:.3f}")
        st.write(f"Maximum allowed spacing: {max_spacing:.3f} m")
        st.write(f"Ring clearance below beam (m): {ring_clearance:.3f}")
        st.write(f"Ring diameter (m): {ring_diameter:.3f}")
        st.write("Ring arc-length positions (m): " +
                 ", ".join(f"{v:.3f}" for v in s_rings))
        st.write("Ring x positions (m): " +
                 ", ".join(f"{v:+.3f}" for v in x_rings))
        st.write("Beam z at ring stations (m): " +
                 ", ".join(f"{v:.3f}" for v in beam_z_rings))
        st.write("Ring z at ring stations (m): " +
                 ", ".join(f"{v:.3f}" for v in ring_z_rings))
        st.write(f"Outer anchors: {anchors.shape[0]}")
        st.write(f"Perimeter nodes: {perimeter_loop.shape[0]}")
        st.write(f"Total mesh nodes: {pts.shape[0]}")
        st.write(f"Mesh edges: {len(edges)}")
        st.write(f"Mesh triangles: {len(tris)}")
        st.write(f"Held nodes: {len(fixed)}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Solve error: {solve_err}")
        else:
            st.write(f"Residual norm: {residual_norm:.6e}")
        st.write(f"Target edge length: {target_len:.4f}")
        st.write("Ring node counts: " +
                 ", ".join(str(c) for c in built["ring_node_counts"]))
        st.write("Ring fabric nodes attached: " +
                 ", ".join(str(c) for c in built["ring_attach_counts"]))
        st.write("Ring attachment edges added: " +
                 ", ".join(str(c) for c in built["ring_attach_edges_added"]))

    with st.expander("All nodes (full digitisation)", expanded=False):
        st.code(
            _format_all_nodes(
                pts, coords, anchor_idx,
                built["ring_indices"],
                built["centre_indices"],
                built["beam_top_indices"],
                built["attached_node_indices"],
            ),
            language="text",
        )
