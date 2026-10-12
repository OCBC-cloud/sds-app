"""Multi-Cone Roof — Lab test page.

Version v27.

Changes from v26:

  1. Perimeter is a real cable.  Every perimeter node between
     anchors is dir-only along its local ellipse tangent.  The
     perimeter is built from the actual ellipse, not a polygon
     between anchors.

  2. Valley ends land on perimeter nodes.  The valley column's
     first and last nodes ARE perimeter nodes (the ones nearest
     to the wall-ellipse intersections).  Both cables pass through
     the same node, so they bow together.

  3. Ring spacing widget.  0 = solver places rings evenly by
     arc length along the primary.  Positive = Chief overrides.

  4. Valley cable q default raised to 200 kN/m.

  5. Edge cable q default raised to 200 kN/m.

  6. Anchor diamond markers removed from all views.

  7. Ring centre circle markers removed.

  8. Ray density ~1.5 m target along each part of each cone's
     boundary loop.

  9. WALL_NODES = 12, RING_NODES_MIN = 20, RING_NODES_MAX = 36.
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


RIB_SEGMENTS = 60
RING_NODES_MIN = 20
RING_NODES_MAX = 36
WALL_NODES = 12
RADIAL_NODES = 6
RAYS_PER_RING = 48
TARGET_RAY_SPACING = 1.5
PERIMETER_SUBDIVISIONS = 20

COL_MEMBRANE = "#4a7a9c"
COL_PERIMETER = "#f1c40f"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"
COL_VALLEY = "#7fb3d5"


# =============================================================================
# GEOMETRY HELPERS
# =============================================================================

def _ellipse_xy(a, b, t):
    return a * math.cos(t), b * math.sin(t)


def _ellipse_y(x, span, mid_width):
    a = span / 2.0
    b = mid_width / 2.0
    t = max(0.0, 1.0 - (x / a) ** 2)
    return b * math.sqrt(t)


def _rib_stations(n, optional_ends, span, x, s, total):
    if (not optional_ends) or n < 3:
        fracs = np.array([k / (n + 1.0) for k in range(1, n + 1)],
                          dtype=float)
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


def _build_ellipse_perimeter(span, mid_width, eave_height, subdivisions):
    """
    Build a perimeter loop directly from the ellipse equation,
    sampled evenly by angle.  Every node is on the ellipse.
    Returns (loop_xy, loop_3d, anchor_angles).
    """
    a = span / 2.0
    b = mid_width / 2.0
    n = subdivisions
    ts = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    pts = np.column_stack([a * np.cos(ts), b * np.sin(ts),
                            np.full(n, eave_height, dtype=float)])
    return ts, pts


def _ring_node_count(r, target_len):
    n = int(round(2.0 * math.pi * r / max(target_len, 1e-6)))
    n = max(RING_NODES_MIN, min(RING_NODES_MAX, n))
    return n


def _cone_arc_positions(n_cones, spacing, total):
    if n_cones < 1:
        raise ValueError("Number of cones must be at least 1.")
    mid = total / 2.0
    if spacing > 0.0:
        # Chief override: place symmetric about the middle.
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
    else:
        # Solver even placement: N positions evenly along arc.
        if n_cones == 1:
            positions = [mid]
        else:
            positions = [total * (k + 1) / (n_cones + 1)
                         for k in range(n_cones)]
    for p in positions:
        if p < 0.0 or p > total:
            raise ValueError(
                "Ring position %.3f m falls outside the primary span "
                "of %.3f m." % (p, total)
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


def _wall_x_from_rings(x_rings, s_rings, xp, s_p):
    """Wall x positions: at the midpoint of arc length between
    adjacent rings."""
    walls_x = []
    for i in range(len(s_rings) - 1):
        s_mid = 0.5 * (s_rings[i] + s_rings[i + 1])
        walls_x.append(float(np.interp(s_mid, s_p, xp)))
    return walls_x


# =============================================================================
# MESH BUILDER (v27)
# =============================================================================

def _build_mesh_v27(perimeter_ts, perimeter_pts, span, mid_width,
                    ring_specs, eave_height):
    a_ell = span / 2.0
    b_ell = mid_width / 2.0

    points_list = [tuple(p) for p in perimeter_pts]
    n_perim = len(perimeter_pts)
    perimeter_ids = list(range(n_perim))

    n_cones = len(ring_specs)
    x_rings = [float(s["cx"]) for s in ring_specs]

    # Wall x positions.
    wall_xs = []
    for i in range(n_cones - 1):
        wall_xs.append(0.5 * (x_rings[i] + x_rings[i + 1]))

    # --- Wall columns, ends on perimeter nodes ---
    # For each wall x, find the two perimeter nodes nearest to
    # the intersection of the wall line with the ellipse.
    wall_columns = {}
    wall_ends = {}
    wall_end_node_ids = {}
    for wx in wall_xs:
        y_top = _ellipse_y(wx, span, mid_width)
        y_bot = -y_top
        # Nearest perimeter nodes to (wx, +y_top) and (wx, -y_top).
        perim_xy = np.array([[p[0], p[1]] for p in perimeter_pts])
        d_top = (perim_xy[:, 0] - wx) ** 2 + (perim_xy[:, 1] - y_top) ** 2
        d_bot = (perim_xy[:, 0] - wx) ** 2 + (perim_xy[:, 1] + y_top) ** 2
        top_id = int(np.argmin(d_top))
        bot_id = int(np.argmin(d_bot))

        # Interior wall nodes (WALL_NODES - 2 of them).
        n_interior = WALL_NODES - 2
        col = [bot_id]
        for k in range(1, n_interior + 1):
            f = k / float(n_interior + 1)
            y = y_bot + f * (y_top - y_bot)
            nid = len(points_list)
            points_list.append((float(wx), float(y), float(eave_height)))
            col.append(nid)
        col.append(top_id)

        wall_columns[wx] = col
        wall_ends[wx] = (top_id, bot_id)
        wall_end_node_ids[wx] = (top_id, bot_id)

    # --- Ring circles ---
    ring_indices = []
    centre_indices = []
    beam_top_indices = []
    ring_node_counts = []
    for spec in ring_specs:
        cx = float(spec["cx"])
        cy = float(spec["cy"])
        cz = float(spec["cz"])
        r = float(spec["r"])
        n_poly = _ring_node_count(r, r)
        ring_node_counts.append(n_poly)
        t = np.linspace(0.0, 2.0 * math.pi, n_poly, endpoint=False)
        poly = np.column_stack([
            cx + r * np.cos(t),
            cy + r * np.sin(t),
            np.full(n_poly, cz, dtype=float),
        ])
        start = len(points_list)
        for p in poly:
            points_list.append(tuple(p))
        ring_indices.append(list(range(start, start + n_poly)))

        centre_indices.append(len(points_list))
        points_list.append((cx, cy, cz))

        beam_top_indices.append(len(points_list))
        points_list.append((cx, cy, float(spec["beam_z"])))

    # --- Boundary loop per cone + fan ---
    fan_notes = []
    ring_radial_rows = []
    ring_loop_ids = []

    for k, spec in enumerate(ring_specs):
        cx = float(spec["cx"])
        cy = float(spec["cy"])
        cz = float(spec["cz"])
        r = float(spec["r"])

        left_wall = wall_xs[k - 1] if k > 0 else None
        right_wall = wall_xs[k] if k < n_cones - 1 else None

        loop_ids, wall_side_count = _build_cone_boundary_loop(
            k, n_cones, left_wall, right_wall,
            perimeter_ts, perimeter_pts, perimeter_ids,
            wall_columns, span, mid_width,
        )
        ring_loop_ids.append(loop_ids)
        n_loop = len(loop_ids)
        if n_loop < 4:
            ring_radial_rows.append([])
            fan_notes.append("cone %d : empty loop" % (k + 1))
            continue

        loop_xy = np.array([[points_list[nid][0], points_list[nid][1]]
                             for nid in loop_ids])

        # Rays split by part (wall part is [0, wall_side_count),
        # perimeter part is [wall_side_count, n_loop)).
        def sample_part(xy_part, spacing):
            if xy_part.shape[0] < 2:
                return []
            closed = np.vstack([xy_part, xy_part[:1]])
            seg = np.diff(closed, axis=0)
            seglen = np.linalg.norm(seg, axis=1)
            total = float(np.sum(seglen))
            if total < 1e-9:
                return []
            n_rays = max(2, int(round(total / spacing)))
            cum = np.concatenate([[0.0], np.cumsum(seglen)])
            targets = np.linspace(0.0, total, n_rays, endpoint=False)
            pts = []
            for s in targets:
                j = int(np.searchsorted(cum, s, side="right") - 1)
                if j < 0:
                    j = 0
                if j >= xy_part.shape[0]:
                    j = xy_part.shape[0] - 1
                t_seg = (s - cum[j]) / max(seglen[j], 1e-12)
                a_pt = closed[j]
                b_pt = closed[j + 1]
                pts.append(a_pt + t_seg * (b_pt - a_pt))
            return pts

        targets_xy = []
        targets_xy.extend(sample_part(loop_xy[:wall_side_count],
                                       TARGET_RAY_SPACING))
        targets_xy.extend(sample_part(loop_xy[wall_side_count:],
                                       TARGET_RAY_SPACING))

        if not targets_xy:
            ring_radial_rows.append([])
            fan_notes.append("cone %d : no targets" % (k + 1))
            continue

        rows = []
        for outer_xy in targets_xy:
            vx = outer_xy[0] - cx
            vy = outer_xy[1] - cy
            vlen = math.hypot(vx, vy)
            if vlen < 1e-9:
                ix, iy = cx, cy
            else:
                ix = cx + r * vx / vlen
                iy = cy + r * vy / vlen
            row = []
            for m in range(RADIAL_NODES):
                f = (m + 1) / float(RADIAL_NODES + 1)
                px = ix + f * (outer_xy[0] - ix)
                py = iy + f * (outer_xy[1] - iy)
                pz = cz + f * (eave_height - cz)
                nid = len(points_list)
                points_list.append((px, py, pz))
                row.append(nid)
            rows.append(row)
        ring_radial_rows.append(rows)
        fan_notes.append(
            "cone %d : %d loop samples, %d rays, walls L=%s R=%s"
            % (k + 1, n_loop, len(rows),
               "yes" if left_wall is not None else "no",
               "yes" if right_wall is not None else "no")
        )

    points = np.asarray(points_list, dtype=float)

    # --- Triangles ---
    triangles = []
    for k in range(n_cones):
        rows = ring_radial_rows[k]
        idx_list = ring_indices[k]
        if not rows:
            continue
        n_poly = len(idx_list)
        cx = float(ring_specs[k]["cx"])
        cy = float(ring_specs[k]["cy"])
        n_rows = len(rows)

        for j in range(n_rows):
            jn = (j + 1) % n_rows
            row_a = rows[j]
            row_b = rows[jn]
            for m in range(RADIAL_NODES - 1):
                a0 = row_a[m]
                a1 = row_a[m + 1]
                b0 = row_b[m]
                b1 = row_b[m + 1]
                triangles.append((a0, b0, b1))
                triangles.append((a0, b1, a1))

        for row in rows:
            if not row:
                continue
            inner_id = row[0]
            ix = float(points[inner_id, 0])
            iy = float(points[inner_id, 1])
            ang = math.atan2(iy - cy, ix - cx)
            if ang < 0.0:
                ang += 2.0 * math.pi
            kk = int(round(ang / (2.0 * math.pi / n_poly))) % n_poly
            poly_id = idx_list[kk]
            poly_next = idx_list[(kk + 1) % n_poly]
            triangles.append((poly_id, inner_id, row[1]))
            triangles.append((poly_id, row[1], poly_next))

        loop_ids = ring_loop_ids[k]
        n_loop = len(loop_ids)
        for j in range(n_rows):
            row = rows[j]
            if not row:
                continue
            outer_id = row[-1]
            px = float(points[outer_id, 0])
            py = float(points[outer_id, 1])
            best = None
            best_d = None
            for nid in loop_ids:
                nx = float(points[nid, 0])
                ny = float(points[nid, 1])
                d = (nx - px) ** 2 + (ny - py) ** 2
                if best_d is None or d < best_d:
                    best_d = d
                    best = nid
            if best is None:
                continue
            pos = loop_ids.index(best)
            loop_next = loop_ids[(pos + 1) % n_loop]
            loop_prev = loop_ids[(pos - 1) % n_loop]
            triangles.append((outer_id, best, loop_next))
            triangles.append((outer_id, loop_prev, best))

    triangles = [t for t in triangles if t[0] != t[1]
                 and t[1] != t[2] and t[0] != t[2]]

    edge_set = set()
    for (a, b, c) in triangles:
        for (i, j) in ((a, b), (b, c), (c, a)):
            key = (i, j) if i < j else (j, i)
            edge_set.add(key)

    for k in range(n_cones):
        idx_list = ring_indices[k]
        centre_i = int(centre_indices[k])
        beam_i = int(beam_top_indices[k])
        n_poly = len(idx_list)
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            edge_set.add((a, b) if a < b else (b, a))
        for i in idx_list:
            edge_set.add((centre_i, i) if centre_i < i else (i, centre_i))
        edge_set.add((centre_i, beam_i) if centre_i < beam_i
                     else (beam_i, centre_i))

    perimeter_edge_set = set()
    for i in range(n_perim):
        j = (i + 1) % n_perim
        perimeter_edge_set.add((i, j) if i < j else (j, i))

    valley_edge_set = set()
    for wx, col in wall_columns.items():
        for i in range(len(col) - 1):
            a = col[i]
            b = col[i + 1]
            valley_edge_set.add((a, b) if a < b else (b, a))

    edges = sorted(edge_set)

    fixed_set = set()
    anchor_node_indices = []   # kept for schedule, no markers
    for idx_list in ring_indices:
        for i in idx_list:
            fixed_set.add(int(i))
    for ci in centre_indices:
        fixed_set.add(int(ci))
    for bi in beam_top_indices:
        fixed_set.add(int(bi))

    # Valley ends held (they are perimeter nodes, but hold fully
    # to anchor the cable ends).
    valley_end_ids = []
    for wx, (top_id, bot_id) in wall_ends.items():
        fixed_set.add(int(top_id))
        fixed_set.add(int(bot_id))
        valley_end_ids.append(int(top_id))
        valley_end_ids.append(int(bot_id))

    # --- Boundary constraints ---
    # Every perimeter node is dir-only along its local ellipse
    # tangent, EXCEPT the valley end nodes (which are held) and
    # the rib-crossing anchors (which are held).  For simplicity
    # here we treat every perimeter node as dir-only along the
    # ellipse tangent, except valley ends.
    dir_only_indices = []
    valley_end_set = set(valley_end_ids)
    cable_interior_indices = []
    for i in range(n_perim):
        if i in valley_end_set:
            continue
        t = float(perimeter_ts[i])
        # Ellipse tangent direction: derivative of (a cos t, b sin t)
        # is (-a sin t, b cos t).
        tx = -a_ell * math.sin(t)
        ty = b_ell * math.cos(t)
        mag = math.hypot(tx, ty)
        if mag < 1e-9:
            continue
        tx /= mag
        ty /= mag
        cable_interior_indices.append(i)
        dir_only_indices.append((int(i), (tx, ty, 0.0)))

    valley_interior_ids = []
    z_only_indices = []
    for wx, col in wall_columns.items():
        for idx_in_col in range(1, len(col) - 1):
            nid = col[idx_in_col]
            valley_interior_ids.append(int(nid))
            z_only_indices.append(int(nid))

    return {
        "points": points,
        "edges": edges,
        "triangles": triangles,
        "fixed_indices": sorted(fixed_set),
        "dir_only_indices": dir_only_indices,
        "z_only_indices": z_only_indices,
        "perimeter_start": 0,
        "perimeter_end": n_perim,
        "n_perimeter": n_perim,
        "anchor_node_indices": anchor_node_indices,
        "cable_interior_indices": cable_interior_indices,
        "ring_indices": ring_indices,
        "centre_indices": centre_indices,
        "beam_top_indices": beam_top_indices,
        "ring_node_counts": ring_node_counts,
        "perimeter_edge_set": perimeter_edge_set,
        "valley_edge_set": valley_edge_set,
        "valley_interior_ids": valley_interior_ids,
        "valley_end_ids": valley_end_ids,
        "wall_columns": wall_columns,
        "wall_ends": wall_ends,
        "wall_xs": wall_xs,
        "ring_loop_ids": ring_loop_ids,
        "fan_notes": fan_notes,
    }


def _build_cone_boundary_loop(k, n_cones, left_wall, right_wall,
                              perimeter_ts, perimeter_pts, perimeter_ids,
                              wall_columns, span, mid_width):
    """
    For cone k, return (loop_ids, wall_side_count).

    Loop order:
      [wall_R interior/top through bottom] + [perimeter arc bottom]
      + [wall_L bottom through top] + [perimeter arc top]
    """
    n_perim = len(perimeter_ids)
    perim_xy = perimeter_pts[:, :2]

    x_right = right_wall if right_wall is not None else (span / 2.0 + 1.0)
    x_left = left_wall if left_wall is not None else (-span / 2.0 - 1.0)

    in_strip = []
    for pid in perimeter_ids:
        px = float(perim_xy[pid, 0])
        if x_left - 1e-9 <= px <= x_right + 1e-9:
            in_strip.append(pid)
    if not in_strip:
        return [], 0

    in_set = set(in_strip)
    start = in_strip[0]
    ordered = []
    i = start
    visited = set()
    while i not in visited:
        visited.add(i)
        if i in in_set:
            ordered.append(i)
        i = (i + 1) % n_perim
        if i == start:
            break

    perim_top = [pid for pid in ordered if float(perim_xy[pid, 1]) >= 0.0]
    perim_bot = [pid for pid in ordered if float(perim_xy[pid, 1]) < 0.0]
    perim_top = sorted(perim_top, key=lambda pid: float(perim_xy[pid, 0]))
    perim_bot = sorted(perim_bot, key=lambda pid: -float(perim_xy[pid, 0]))

    loop = []
    wall_side_count = 0
    if right_wall is not None:
        col = wall_columns[right_wall]
        for nid in reversed(col):
            loop.append(nid)
            wall_side_count += 1
    for pid in perim_bot:
        loop.append(pid)
    if left_wall is not None:
        col = wall_columns[left_wall]
        for nid in col:
            loop.append(nid)
            wall_side_count += 1
    for pid in perim_top:
        loop.append(pid)
    return loop, wall_side_count


# =============================================================================
# CACHED WRAPPERS
# =============================================================================

@st.cache_data(show_spinner=False)
def _cached_build_mesh(perimeter_ts_bytes, perimeter_pts_bytes,
                       span, mid_width, ring_specs_tuple, eave_height):
    perimeter_ts = np.frombuffer(perimeter_ts_bytes, dtype=np.float64)
    perimeter_pts = np.frombuffer(perimeter_pts_bytes,
                                    dtype=np.float64).reshape(-1, 3)
    ring_specs = []
    for spec_t in ring_specs_tuple:
        ring_specs.append({
            "cx": spec_t[0], "cy": spec_t[1], "cz": spec_t[2],
            "r": spec_t[3], "beam_z": spec_t[4],
        })
    return _build_mesh_v27(perimeter_ts, perimeter_pts, span, mid_width,
                            ring_specs, eave_height)


@st.cache_data(show_spinner=False)
def _cached_solve(points_bytes, edges_tuple, fixed_tuple,
                  q_bytes, dir_only_tuple, z_only_tuple):
    points = np.frombuffer(points_bytes,
                            dtype=np.float64).reshape(-1, 3)
    edges = list(edges_tuple)
    fixed = list(fixed_tuple)
    q = np.frombuffer(q_bytes, dtype=np.float64)
    dir_only = [(int(nid), (float(d[0]), float(d[1]), float(d[2])))
                for nid, d in dir_only_tuple]
    z_only = list(z_only_tuple)
    return solve_fdm(points, edges, fixed, q,
                      z_only_indices=z_only,
                      dir_only_indices=dir_only)


# =============================================================================
# MEMBER SCHEDULE
# =============================================================================

def _build_member_schedule(built, coords):
    members = []
    ring_indices = built["ring_indices"]
    centre_indices = built["centre_indices"]
    beam_top_indices = built["beam_top_indices"]
    n_perim = built["n_perimeter"]
    perimeter_start = built["perimeter_start"]

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
            "role": "closed ring beam",
        })
        for i in range(n_poly):
            a = int(idx_list[i])
            b = int(idx_list[(i + 1) % n_poly])
            L = float(np.linalg.norm(coords[b] - coords[a]))
            members.append({
                "member_id": f"Ring_{ring_no}_Beam_Seg_{i+1:02d}",
                "member_type": "ring_beam_segment",
                "ring_index": ring_no,
                "node_a": a, "node_b": b, "length_m": L,
                "section": "TBD", "material": "TBD",
                "role": "ring beam segment",
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
                "role": "radial spoke",
            })
        L = float(np.linalg.norm(coords[beam_i] - coords[centre_i]))
        members.append({
            "member_id": f"Ring_{ring_no}_Drop_Member",
            "member_type": "drop_member",
            "ring_index": ring_no,
            "node_a": beam_i, "node_b": centre_i, "length_m": L,
            "section": "TBD", "material": "TBD",
            "role": "vertical drop member",
        })

    perimeter_loop_ids = list(range(perimeter_start,
                                     perimeter_start + n_perim))
    total_length = 0.0
    for i in range(n_perim):
        a = perimeter_loop_ids[i]
        b = perimeter_loop_ids[(i + 1) % n_perim]
        total_length += float(np.linalg.norm(coords[b] - coords[a]))
    members.append({
        "member_id": "Edge_Cable",
        "member_type": "edge_cable",
        "ring_index": 0,
        "node_a": int(perimeter_loop_ids[0]),
        "node_b": int(perimeter_loop_ids[0]),
        "length_m": float(total_length),
        "section": "TBD", "material": "TBD",
        "role": "closed perimeter edge cable",
    })
    for i in range(n_perim):
        a = perimeter_loop_ids[i]
        b = perimeter_loop_ids[(i + 1) % n_perim]
        L = float(np.linalg.norm(coords[b] - coords[a]))
        members.append({
            "member_id": f"Edge_Cable_Seg_{i+1:03d}",
            "member_type": "edge_cable_segment",
            "ring_index": 0,
            "node_a": int(a), "node_b": int(b), "length_m": L,
            "section": "TBD", "material": "TBD",
            "role": "perimeter edge cable segment",
        })

    wall_columns = built["wall_columns"]
    for vi, (wx, col) in enumerate(sorted(wall_columns.items())):
        valley_no = vi + 1
        length = 0.0
        for i in range(len(col) - 1):
            a = int(col[i])
            b = int(col[i + 1])
            length += float(np.linalg.norm(coords[b] - coords[a]))
        members.append({
            "member_id": f"Valley_Cable_{valley_no}",
            "member_type": "valley_cable",
            "ring_index": 0,
            "node_a": int(col[0]), "node_b": int(col[-1]),
            "length_m": float(length),
            "section": "TBD", "material": "TBD",
            "role": "valley cable between two cones",
        })
        for i in range(len(col) - 1):
            a = int(col[i])
            b = int(col[i + 1])
            L = float(np.linalg.norm(coords[b] - coords[a]))
            members.append({
                "member_id": f"Valley_Cable_{valley_no}_Seg_{i+1:02d}",
                "member_type": "valley_cable_segment",
                "ring_index": 0,
                "node_a": a, "node_b": b, "length_m": L,
                "section": "TBD", "material": "TBD",
                "role": "valley cable segment",
            })

    return members


def _format_member_table(members):
    lines = []
    header = (
        "%-30s  %-22s  %-5s  %-6s  %-6s  %-9s  %-7s  %-8s  %s"
        % ("member_id", "member_type", "ring", "node_a", "node_b",
           "length_m", "section", "material", "role")
    )
    lines.append(header)
    lines.append("-" * len(header))
    for m in members:
        lines.append(
            "%-30s  %-22s  %-5d  %-6d  %-6d  %-9.4f  %-7s  %-8s  %s"
            % (m["member_id"], m["member_type"], m["ring_index"],
               m["node_a"], m["node_b"], m["length_m"],
               m["section"], m["material"], m["role"])
        )
    return "\n".join(lines)


# =============================================================================
# DIGITISATION
# =============================================================================

_HEADER = (
    "%6s  %10s  %10s  %10s  %10s  %10s  %10s  %9s  %s"
    % ("idx", "x_init", "y_init", "z_init",
       "x_set", "y_set", "z_set", "disp", "status")
)


def _format_all_nodes(points_initial, points_settled, built):
    n = points_initial.shape[0]
    status_of = ["free"] * n
    for i in built["cable_interior_indices"]:
        status_of[int(i)] = "cable_interior_dir_only"
    for i in built["valley_interior_ids"]:
        status_of[int(i)] = "valley_interior_z_only"
    for i in built["valley_end_ids"]:
        status_of[int(i)] = "held_valley_end"
    for idx_list in built["ring_indices"]:
        for i in idx_list:
            status_of[int(i)] = "held_ring_polygon"
    for i in built["centre_indices"]:
        status_of[int(i)] = "held_ring_centre"
    for i in built["beam_top_indices"]:
        status_of[int(i)] = "held_beam_top"
    lines = [_HEADER, "-" * len(_HEADER)]
    for i in range(n):
        xi, yi, zi = points_initial[i]
        xs, ys, zs = points_settled[i]
        d = float(np.linalg.norm(np.array([xs - xi, ys - yi, zs - zi])))
        lines.append(
            "%6d  %10.5f  %10.5f  %10.5f  %10.5f  %10.5f  %10.5f  %9.4e  %s"
            % (i, xi, yi, zi, xs, ys, zs, d, status_of[i])
        )
    return "\n".join(lines)


# =============================================================================
# PAGE
# =============================================================================

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>"
        "Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — v27.  "
        "Real ellipse perimeter cable, valley ends on perimeter, "
        "spacing override, stiffer cables, cleaner view.</p>",
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
        ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 0.5,
                                         0.1, key="mc_rd")
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

    c1, c2 = st.columns(2)
    with c1:
        number_of_cones = int(st.number_input(
            "Number of cones", 1, 10, 3, 1, key="mc_ncones"
        ))
    with c2:
        ring_spacing_input = st.number_input(
            "Spacing override (m, 0 = solver evenly places)",
            0.0, 10.0, 0.0, 0.1, key="mc_spacing"
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

    c1, c2 = st.columns(2)
    with c1:
        edge_q_input = st.number_input(
            "Edge cable pretension (kN/m, 0 = auto)",
            0.0, 5000.0, 200.0, 10.0, key="mc_edgeq",
        )
    with c2:
        valley_q_input = st.number_input(
            "Valley cable pretension (kN/m)",
            0.1, 5000.0, 200.0, 10.0, key="mc_valleyq",
        )

    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p,
                          total_p)
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
        s_rings = _cone_arc_positions(number_of_cones,
                                       float(ring_spacing_input), total_p)
        for s_val in s_rings:
            x_val = float(np.interp(s_val, s_p, xp))
            bz_val = float(np.interp(s_val, s_p, zp))
            rz_val = bz_val - float(ring_clearance)
            x_rings.append(x_val)
            beam_z_rings.append(bz_val)
            ring_z_rings.append(rz_val)
            ring_specs.append({
                "cx": x_val, "cy": 0.0, "cz": rz_val,
                "r": float(ring_diameter) / 2.0, "beam_z": bz_val,
            })
    except ValueError as e:
        placement_error = str(e)

    if placement_error:
        st.error("Placement refused: " + placement_error)
        return

    # Widget check: wall spacing at least 2x ring radius.
    if number_of_cones >= 2:
        min_wall_spacing = min(
            abs(x_rings[i + 1] - x_rings[i])
            for i in range(len(x_rings) - 1)
        )
        min_required = 2.0 * (float(ring_diameter) / 2.0)
        if min_wall_spacing < min_required:
            st.error(
                "Placement refused: cone spacing is too small.  "
                "Minimum spacing between ring centres is %.3f m." %
                min_required
            )
            return

    # --- Perimeter: pure ellipse, not polygon between anchors ---
    perimeter_ts, perimeter_pts = _build_ellipse_perimeter(
        span, mid_width, eave_height, PERIMETER_SUBDIVISIONS,
    )

    ring_specs_tuple = tuple(
        (s["cx"], s["cy"], s["cz"], s["r"], s["beam_z"])
        for s in ring_specs
    )
    built = _cached_build_mesh(
        perimeter_ts.tobytes(),
        perimeter_pts.tobytes(),
        float(span),
        float(mid_width),
        ring_specs_tuple,
        float(eave_height),
    )

    pts_init = built["points"]
    edges = built["edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]
    dir_only = built["dir_only_indices"]
    z_only = built["z_only_indices"]

    warp_q = max(float(warp_q_input), 0.1) * 1000.0
    weft_q = max(float(weft_q_input), 0.1) * 1000.0
    if edge_q_input > 0.0:
        edge_q_scalar = float(edge_q_input) * 1000.0
    else:
        edge_q_scalar = max(warp_q, weft_q) * 5.0
    edge_q_scalar = max(edge_q_scalar, 1.0)
    valley_q_scalar = max(float(valley_q_input), 0.1) * 1000.0

    perim_edge_set = built["perimeter_edge_set"]
    valley_edge_set = built["valley_edge_set"]
    q = np.empty(len(edges), dtype=float)
    for k, (i, j) in enumerate(edges):
        key = (i, j) if i < j else (j, i)
        if key in valley_edge_set:
            q[k] = valley_q_scalar
        elif key in perim_edge_set:
            q[k] = edge_q_scalar
        else:
            q[k] = warp_q

    dir_only_tuple = tuple(
        (int(nid), (float(d[0]), float(d[1]), float(d[2])))
        for nid, d in dir_only
    )
    z_only_tuple = tuple(int(i) for i in z_only)
    try:
        fdm = _cached_solve(
            pts_init.tobytes(),
            tuple((int(i), int(j)) for i, j in edges),
            tuple(int(i) for i in fixed),
            q.tobytes(),
            dir_only_tuple,
            z_only_tuple,
        )
        coords = fdm["coordinates"]
        residual_norm = float(fdm["residual_norm"])
        solve_ok = True
        solve_err = ""
    except Exception as e:
        coords = pts_init.copy()
        residual_norm = float("nan")
        solve_ok = False
        solve_err = str(e)

    valley_cols = built["wall_columns"]
    valley_z_summary = []
    for wx, col in sorted(valley_cols.items()):
        zs = coords[col, 2]
        valley_z_summary.append((wx, float(np.min(zs)),
                                 float(np.max(zs))))

    # --- 3D view ---
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
            mode="lines", line=dict(color=COL_RIB, width=4),
            name="rib", showlegend=False, hoverinfo="skip",
        ))

    ps = built["perimeter_start"]
    pe = built["perimeter_end"]
    perim_pts = coords[ps:pe]
    perim_closed = np.vstack([perim_pts, perim_pts[:1]])
    fig.add_trace(go.Scatter3d(
        x=perim_closed[:, 0], y=perim_closed[:, 1],
        z=perim_closed[:, 2],
        mode="lines", line=dict(color=COL_PERIMETER, width=5),
        name="edge cable", showlegend=False, hoverinfo="skip",
    ))

    for wx, col in sorted(valley_cols.items()):
        vp = coords[col]
        fig.add_trace(go.Scatter3d(
            x=vp[:, 0], y=vp[:, 1], z=vp[:, 2],
            mode="lines", line=dict(color=COL_VALLEY, width=5),
            name="valley cable", showlegend=False, hoverinfo="skip",
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

    # --- Plan view ---
    figp = go.Figure()
    perim_xy = pts_init[ps:pe, :2]
    perim_closed_xy = np.vstack([perim_xy, perim_xy[:1]])
    figp.add_trace(go.Scatter(
        x=perim_closed_xy[:, 0], y=perim_closed_xy[:, 1],
        mode="lines+markers",
        line=dict(color=COL_PERIMETER, width=3),
        marker=dict(color=COL_PERIMETER, size=2),
        name="perimeter", showlegend=False, hoverinfo="skip",
    ))
    for k, idx_list in enumerate(built["ring_indices"]):
        pp = pts_init[idx_list]
        closed = np.vstack([pp, pp[:1]])
        figp.add_trace(go.Scatter(
            x=closed[:, 0], y=closed[:, 1],
            mode="lines", line=dict(color=COL_RING_EDGE, width=2),
            name="ring", showlegend=False, hoverinfo="skip",
        ))
    for wx, col in sorted(valley_cols.items()):
        p = pts_init[col]
        figp.add_trace(go.Scatter(
            x=p[:, 0], y=p[:, 1],
            mode="lines+markers",
            line=dict(color=COL_VALLEY, width=3),
            marker=dict(color=COL_VALLEY, size=5),
            name="valley", showlegend=False, hoverinfo="skip",
        ))
    for k, loop_ids in enumerate(built["ring_loop_ids"]):
        if not loop_ids:
            continue
        lp = pts_init[loop_ids]
        lp_closed = np.vstack([lp, lp[:1]])
        figp.add_trace(go.Scatter(
            x=lp_closed[:, 0], y=lp_closed[:, 1],
            mode="lines",
            line=dict(color="#4a90e2", width=1, dash="dot"),
            name=f"loop {k+1}", showlegend=False, hoverinfo="skip",
        ))
    ring_node_set = set()
    for idx_list in built["ring_indices"]:
        ring_node_set.update(int(i) for i in idx_list)
    for i in built["centre_indices"]:
        ring_node_set.add(int(i))
    for i in built["beam_top_indices"]:
        ring_node_set.add(int(i))
    valley_node_set = set()
    for col in built["wall_columns"].values():
        valley_node_set.update(int(i) for i in col)
    radial_ids = [i for i in range(pts_init.shape[0])
                  if i not in ring_node_set
                  and i not in valley_node_set
                  and i >= built["n_perimeter"]]
    if radial_ids:
        rp2 = pts_init[radial_ids]
        figp.add_trace(go.Scatter(
            x=rp2[:, 0], y=rp2[:, 1],
            mode="markers",
            marker=dict(color=COL_MEMBRANE, size=3),
            name="radial", showlegend=False, hoverinfo="skip",
        ))
    figp.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="#0e1621",
        plot_bgcolor="#0e1621",
        font=dict(color="#a8b8c8"),
        xaxis=dict(title="X (m)", scaleanchor="y", scaleratio=1.0,
                   gridcolor="#1e2a3a", zerolinecolor="#1e2a3a"),
        yaxis=dict(title="Y (m)",
                   gridcolor="#1e2a3a", zerolinecolor="#1e2a3a"),
        title=dict(text="Plan view (initial mesh)",
                   font=dict(color="#f39c12", size=14)),
    )
    st.plotly_chart(figp, use_container_width=True, key="mc_plan")

    members = _build_member_schedule(built, coords)

    with st.expander("Member schedule", expanded=False):
        st.write(f"Total members: {len(members)}")
        st.code(_format_member_table(members), language="text")

    with st.expander("Diagnostics", expanded=False):
        st.write(f"Cones: {number_of_cones}")
        st.write(f"Spacing input (m): {ring_spacing_input:.3f}")
        st.write(f"Ring x (from solver or override): "
                 f"{[round(v,3) for v in x_rings]}")
        st.write(f"Ring z: {[round(v,3) for v in ring_z_rings]}")
        st.write(f"Wall x values: "
                 f"{[round(v,3) for v in built['wall_xs']]}")
        st.write(f"Perimeter nodes: {built['n_perimeter']}")
        st.write(f"Total nodes: {pts_init.shape[0]}")
        st.write(f"Edges: {len(edges)}")
        st.write(f"Triangles: {len(tris)}")
        st.write(f"Held: {len(fixed)}")
        st.write(f"Dir-only (perimeter cable): {len(dir_only)}")
        st.write(f"Z-only (valley cable): {len(z_only)}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Error: {solve_err}")
        else:
            st.write(f"Residual: {residual_norm:.4e}")
        st.write("Valley columns (x, z_min, z_max):")
        for wx, zmn, zmx in valley_z_summary:
            st.write(f"  x={wx:+.3f}  z_min={zmn:.3f}  z_max={zmx:.3f}")
        st.write("Fan notes:")
        for n in built["fan_notes"]:
            st.write("  " + n)

    with st.expander("All nodes (full digitisation)", expanded=False):
        st.code(_format_all_nodes(pts_init, coords, built), language="text")
