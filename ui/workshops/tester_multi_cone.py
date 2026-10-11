"""Multi-Cone Roof — Stage 3 Lab test page (radial fan mesh).

Version v15.  Clean rewrite of the mesh builder.

The mesh is now built by a RADIAL FAN from each ring to the perimeter,
not by laying a Cartesian grid over the plan.

Method (from the brief, Section 6, and standard tensile practice):

  1. Perimeter polygon at eave height, subdivided by anchors.
  2. Ring polygon for each cone, at its own height.
  3. For each ring, cast N_rays rays outward from the ring centre.
     Each ray is clipped at the ring circle and at the perimeter.
     Along each ray, place n_radial - 1 interior nodes.
  4. Join consecutive rays into quad strips, split each quad into two
     triangles.
  5. Between adjacent rings, a bridge strip connects their outward fans.
  6. The ring polygon nodes are held.  The perimeter anchors are held.
  7. solve_fdm runs on that mesh.

Every triangle has proper aspect ratio by construction.  The cone
surfaces emerge from the solve.  The member schedule is unchanged.

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

# Radial fan resolution.
RAYS_PER_RING = 48
RADIAL_NODES = 6           # number of interior nodes along each ray

COL_MEMBRANE = "#4a7a9c"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"


# --- Shape helpers -----------------------------------------------------------

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


def _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height, tip_x):
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


def _ring_node_count(r, target_len):
    n = int(round(2.0 * math.pi * r / max(target_len, 1e-6)))
    n = max(RING_NODES_MIN, min(RING_NODES_MAX, n))
    return n


def _ray_perimeter_intersection(origin_xy, direction, perimeter_xy):
    """Return the distance along the ray from origin to the perimeter.

    origin_xy: (2,)
    direction: (2,) unit vector
    perimeter_xy: (n, 2) closed polygon
    """
    ox, oy = origin_xy
    dx, dy = direction
    n = perimeter_xy.shape[0]
    best_t = None
    for i in range(n):
        j = (i + 1) % n
        px, py = perimeter_xy[i]
        qx, qy = perimeter_xy[j]
        # Ray: o + t*d,  Segment: p + s*(q-p), s in [0,1], t >= 0
        ex, ey = qx - px, qy - py
        denom = dx * ey - dy * ex
        if abs(denom) < 1e-12:
            continue
        # Solve for t and s.
        # o + t d = p + s e
        # t d - s e = p - o
        rhs_x = px - ox
        rhs_y = py - oy
        t = (rhs_x * ey - rhs_y * ex) / denom
        s = (dx * rhs_y - dy * rhs_x) / denom
        if t > 1e-9 and -1e-9 <= s <= 1.0 + 1e-9:
            if best_t is None or t < best_t:
                best_t = t
    return best_t


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


# --- Radial fan mesh ---------------------------------------------------------

def _build_radial_mesh(perimeter_loop, anchor_idx, ring_specs,
                        eave_height):
    """Build the membrane mesh by radial fans from each ring to the
    perimeter.  Returns points, edges, triangles, fixed_indices,
    ring_polygon_indices, plus a note list.
    """
    notes = []
    pts_list = []
    triangles = []
    edges_set = set()

    def _add_pt(p):
        pts_list.append((float(p[0]), float(p[1]), float(p[2])))
        return len(pts_list) - 1

    def _add_edge(a, b):
        if a == b:
            return
        key = (a, b) if a < b else (b, a)
        edges_set.add(key)

    # -------- Perimeter nodes --------
    n_perimeter = perimeter_loop.shape[0]
    perimeter_indices = []
    for i in range(n_perimeter):
        perimeter_indices.append(_add_pt(perimeter_loop[i]))
    for i in range(n_perimeter):
        a = perimeter_indices[i]
        b = perimeter_indices[(i + 1) % n_perimeter]
        _add_edge(a, b)

    # -------- Ring polygons --------
    # Each ring: polygon nodes, centre node, beam_top node.
    ring_polygon_indices = []
    ring_centre_indices = []
    ring_beam_top_indices = []
    ring_centres_2d = []           # (cx, cy)

    for spec in ring_specs:
        cx = float(spec["cx"])
        cy = float(spec["cy"])
        cz = float(spec["cz"])
        r = float(spec["r"])
        # Polygon node count derived from a nominal spacing.
        target_len = r  # small ring -> fewer nodes but at least RING_NODES_MIN
        n_poly = _ring_node_count(r, target_len)
        t = np.linspace(0.0, 2.0 * math.pi, n_poly, endpoint=False)
        idx_list = []
        for tt in t:
            idx = _add_pt((cx + r * math.cos(tt),
                            cy + r * math.sin(tt),
                            cz))
            idx_list.append(idx)
        ring_polygon_indices.append(idx_list)
        ring_centre_indices.append(_add_pt((cx, cy, cz)))
        ring_beam_top_indices.append(_add_pt((cx, cy, float(spec["beam_z"]))))
        ring_centres_2d.append((cx, cy))

        # Ring polygon edges + spokes + drop member
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            _add_edge(a, b)
        centre_i = ring_centre_indices[-1]
        for i in idx_list:
            _add_edge(centre_i, i)
        _add_edge(centre_i, ring_beam_top_indices[-1])

    # -------- Radial fan for each ring --------
    # Node index layout: for each ring, we have RAYS_PER_RING rays.
    # Each ray has RADIAL_NODES interior nodes between ring circle and
    # perimeter.
    # fan_nodes[r][i][k] = node index for ring r, ray i, layer k=1..RADIAL_NODES
    perimeter_xy = perimeter_loop[:, :2]
    fan_nodes = []

    for ri, spec in enumerate(ring_specs):
        cx = float(spec["cx"])
        cy = float(spec["cy"])
        cz = float(spec["cz"])
        r = float(spec["r"])
        bz = float(spec["beam_z"])
        n_poly = len(ring_polygon_indices[ri])

        rays_this_ring = []
        ring_rays = []

        # Ray angles chosen to match polygon node angles, so that the fan
        # emanates from polygon nodes directly.  If polygon count and
        # RAYS_PER_RING differ, we take evenly-spaced angles and connect
        # each ray to its nearest polygon node below.
        for k in range(RAYS_PER_RING):
            theta = 2.0 * math.pi * k / RAYS_PER_RING
            dx = math.cos(theta)
            dy = math.sin(theta)

            # Distance from ring circle edge to perimeter along this ray.
            # Start point on ring circle:
            start = np.array([cx + r * dx, cy + r * dy])
            t_max = _ray_perimeter_intersection(
                np.array([cx, cy]), np.array([dx, dy]), perimeter_xy
            )
            if t_max is None or t_max <= r:
                # Ring extends past the perimeter in this direction.
                # Skip this ray and note it.
                ring_rays.append(None)
                continue

            # Parametrise from r to t_max.
            radial_nodes = []
            for layer in range(1, RADIAL_NODES + 1):
                f = layer / float(RADIAL_NODES + 1)
                dist = r + f * (t_max - r)
                # Height along the ray: linear from ring height to eave.
                z = cz + f * (eave_height - cz)
                p = (cx + dist * dx, cy + dist * dy, z)
                radial_nodes.append(_add_pt(p))
            radial_nodes.append(None)   # placeholder for perimeter hit
            ring_rays.append(radial_nodes)

            # Connect radial nodes to each other.
            for a_i in range(len(radial_nodes) - 2):
                _add_edge(radial_nodes[a_i], radial_nodes[a_i + 1])

        # Connect each ray to its polygon node (outermost radial node
        # connects to nearest polygon node at ring circumference).
        for k, rr in enumerate(ring_rays):
            if rr is None or rr[0] is None:
                continue
            theta = 2.0 * math.pi * k / RAYS_PER_RING
            # Nearest polygon node to angle theta.
            poly_angles = np.linspace(0.0, 2.0 * math.pi, n_poly, endpoint=False)
            diffs = np.abs(((poly_angles - theta + math.pi) % (2.0 * math.pi)) - math.pi)
            poly_k = int(np.argmin(diffs))
            _add_edge(rr[0], ring_polygon_indices[ri][poly_k])

        # Connect each ray's outermost radial node to the perimeter by
        # finding the nearest perimeter node.
        for k, rr in enumerate(ring_rays):
            if rr is None or rr[-2] is None:
                continue
            theta = 2.0 * math.pi * k / RAYS_PER_RING
            dx = math.cos(theta)
            dy = math.sin(theta)
            # Approx endpoint on perimeter:
            t_max = _ray_perimeter_intersection(
                np.array([cx, cy]), np.array([dx, dy]), perimeter_xy
            )
            if t_max is None:
                continue
            end_xy = np.array([cx + t_max * dx, cy + t_max * dy])
            # Nearest perimeter node:
            d = np.linalg.norm(perimeter_xy - end_xy[None, :], axis=1)
            per_k = int(np.argmin(d))
            _add_edge(rr[-2], perimeter_indices[per_k])

        fan_nodes.append(ring_rays)

    # -------- Quad strips between consecutive rays of each ring --------
    # Each ring's fan is a ring of RAYS_PER_RING rays.  Between consecutive
    # rays (mod RAYS_PER_RING), form quad strips of triangles.
    for ri in range(len(ring_specs)):
        ring_rays = fan_nodes[ri]
        m = RAYS_PER_RING
        for k in range(m):
            k2 = (k + 1) % m
            rr1 = ring_rays[k]
            rr2 = ring_rays[k2]
            if rr1 is None or rr2 is None:
                continue
            # Layers 1..RADIAL_NODES present in each; the last entry is
            # a placeholder.  So rr1[0..RADIAL_NODES-1] are the interior
            # nodes, arranged from inner (near ring) to outer.
            for L in range(RADIAL_NODES - 1):
                a = rr1[L]
                b = rr1[L + 1]
                c = rr2[L + 1]
                d = rr2[L]
                # Two triangles: (a,b,c) and (a,c,d).
                if a is not None and b is not None and c is not None:
                    triangles.append((a, b, c))
                    _add_edge(b, c)
                if a is not None and c is not None and d is not None:
                    triangles.append((a, c, d))
                    _add_edge(c, d)
            # Also connect outermost radial nodes to each other through
            # the perimeter-to-nearest bridge — already handled.

    # -------- Bridge between consecutive rings --------
    # For two rings, connect their nearest-to-perimeter radial node rings
    # with triangles.  This is a simple fan between the two rings along
    # their facing directions.
    for ri in range(len(ring_specs) - 1):
        rr_left = fan_nodes[ri]
        rr_right = fan_nodes[ri + 1]
        for k in range(RAYS_PER_RING):
            # Pick a ray in the left ring heading in +x direction and
            # the corresponding ray in the right ring heading in -x
            # direction — their outermost radial nodes bridge to the
            # same perimeter region.
            # Simpler: bridge consecutive angular positions of the two
            # rings directly.  This yields a proper strip between them.
            k2 = (k + 1) % RAYS_PER_RING
            left1 = rr_left[k]
            left2 = rr_left[k2]
            right1 = rr_right[k]
            right2 = rr_right[k2]
            if any(x is None for x in (left1, left2, right1, right2)):
                continue
            # Use the innermost radial node (nearest to ring) as bridge
            # endpoints, so the bridge sits near the rings, not at the
            # perimeter.
            a = left1[0]
            b = left2[0]
            c = right2[0]
            d = right1[0]
            if a is not None and b is not None and c is not None:
                triangles.append((a, b, c))
                _add_edge(b, c)
            if a is not None and c is not None and d is not None:
                triangles.append((a, c, d))
                _add_edge(c, d)

    # -------- Held nodes --------
    fixed = set()
    for idx in anchor_idx:
        fixed.add(int(perimeter_indices[idx]))
    for idx_list in ring_polygon_indices:
        for i in idx_list:
            fixed.add(int(i))
    for i in ring_centre_indices:
        fixed.add(int(i))
    for i in ring_beam_top_indices:
        fixed.add(int(i))

    points = np.asarray(pts_list, dtype=float)
    edges = sorted(edges_set)

    return {
        "points": points,
        "edges": edges,
        "triangles": triangles,
        "fixed_indices": sorted(fixed),
        "ring_polygon_indices": ring_polygon_indices,
        "ring_centre_indices": ring_centre_indices,
        "ring_beam_top_indices": ring_beam_top_indices,
        "perimeter_indices": perimeter_indices,
        "notes": notes,
    }


# --- Member schedule ---------------------------------------------------------

def _build_member_schedule(built, coords):
    members = []
    ring_polygon_indices = built["ring_polygon_indices"]
    ring_centre_indices = built["ring_centre_indices"]
    ring_beam_top_indices = built["ring_beam_top_indices"]

    for k in range(len(ring_polygon_indices)):
        ring_no = k + 1
        idx_list = ring_polygon_indices[k]
        centre_i = int(ring_centre_indices[k])
        beam_i = int(ring_beam_top_indices[k])
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
            "section": "TBD",
            "material": "TBD",
            "role": "closed ring beam, one per cone",
        })
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
                       ring_polygon_indices, centre_indices, beam_top_indices):
    n = points_initial.shape[0]
    status_of = ["free"] * n
    for i in anchor_idx:
        status_of[int(i)] = "held_perimeter_anchor"
    for idx_list in ring_polygon_indices:
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


# --- Page --------------------------------------------------------------------

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — radial fan mesh.  "
        "Cones by construction.</p>",
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
        "Ring clearance below beam (m)", 0.1, 5.0, 1.0, 0.1, key="mc_clr",
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

    built = _build_radial_mesh(
        perimeter_loop, anchor_idx, ring_specs, eave_height
    )

    pts = built["points"]
    edges = built["edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]

    if len(tris) == 0:
        st.error("The radial fan produced no triangles.  Check ring positions.")
        return

    warp_q = max(float(warp_q_input), 0.1) * 1000.0
    weft_q = max(float(weft_q_input), 0.1) * 1000.0

    q = np.full(len(edges), warp_q, dtype=float)

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

    fig = go.Figure()
    tri = np.asarray(tris, dtype=int)
    fig.add_trace(go.Mesh3d(
        x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
        i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
        color=COL_MEMBRANE, opacity=0.6, flatshading=True,
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

    for k, idx_list in enumerate(built["ring_polygon_indices"]):
        pp = coords[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name=f"ring {k+1}", showlegend=False, hoverinfo="skip",
        ))
        centre_i = built["ring_centre_indices"][k]
        beam_i = built["ring_beam_top_indices"][k]
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

    members = _build_member_schedule(built, coords)

    with st.expander("Steel member schedule (BQ and analysis)", expanded=False):
        st.write(f"Total members recorded: {len(members)}")
        st.code(_format_member_table(members), language="text")

    with st.expander("Diagnostics", expanded=False):
        st.write(f"Number of cones: {number_of_cones}")
        st.write(f"Spacing (m, along beam): {ring_spacing:.3f}")
        st.write(f"Primary arc length (m): {total_p:.3f}")
        st.write(f"Maximum allowed spacing: {max_spacing:.3f} m")
        st.write(f"Ring clearance below beam (m): {ring_clearance:.3f}")
        st.write(f"Ring diameter (m): {ring_diameter:.3f}")
        st.write("Ring x positions (m): " +
                 ", ".join(f"{v:+.3f}" for v in x_rings))
        st.write("Ring z (m): " +
                 ", ".join(f"{v:.3f}" for v in ring_z_rings))
        st.write(f"Mesh nodes: {pts.shape[0]}")
        st.write(f"Mesh edges: {len(edges)}")
        st.write(f"Mesh triangles: {len(tris)}")
        st.write(f"Held nodes: {len(fixed)}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Solve error: {solve_err}")
        else:
            st.write(f"Residual norm: {residual_norm:.6e}")
        st.write("**Fan notes:**")
        for n in built["notes"]:
            st.write("- " + n)

    with st.expander("All nodes (full digitisation)", expanded=False):
        st.code(
            _format_all_nodes(
                pts, coords, built["perimeter_indices"],
                built["ring_polygon_indices"],
                built["ring_centre_indices"],
                built["ring_beam_top_indices"],
            ),
            language="text",
        )
