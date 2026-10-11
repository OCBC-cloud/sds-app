"""Multi-Cone Roof — Stage 3 Lab test page.

Version v19.

The v18 builder had two different walks over the same boundary
polyline: an arc-length walk for the ray outer points, and an
index-based walk for the fabric-to-boundary attach.  They did not
agree, so outer ray nodes were attached to synthetic positions
that had no node id.  The wall columns were built but no fan
actually attached to them.  The middle strip was tiled correctly
by accident (its wall columns happened to line up), but the left
and right cones had free outer nodes that the solver pulled
inward.  Hence the fractured outer fans.

v19 carries node ids through the boundary walk.  Every boundary
sample is a real node id.  If the arc-length sample falls between
two existing boundary nodes, a new node is inserted at that exact
position, and its id is recorded.  The ray outer node and the
boundary attach node are then the SAME id.

No tolerance snapping.  No nearest-node heuristics.  Shared ids.

Everything else is carried over from v18 unchanged.
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
RAYS_PER_RING = 48
RADIAL_NODES = 6

COL_MEMBRANE = "#4a7a9c"
COL_PERIMETER = "#f1c40f"
COL_ANCHOR = "#f39c12"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"
COL_VALLEY = "#7fb3d5"
COL_WALL = "#66d9ef"


# =============================================================================
# GEOMETRY HELPERS
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

    anchor_local_indices = []
    for i in range(len(rib_x)):
        anchor_local_indices.append(i)
    anchor_local_indices.append(len(plus))
    for i in range(len(rib_x)):
        anchor_local_indices.append(len(plus) + 1 + i)
    anchor_local_indices.append(len(pts) - 1)

    return np.asarray(pts, dtype=float), sorted(set(anchor_local_indices))


def _subdivide_polygon_with_anchors(anchors, subdivisions):
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
# CELL WALLS
# =============================================================================

def _cell_walls_x(x_rings):
    mids = []
    for i in range(len(x_rings) - 1):
        mids.append(0.5 * (x_rings[i] + x_rings[i + 1]))
    walls = []
    for i in range(len(x_rings)):
        left = mids[i - 1] if i > 0 else None
        right = mids[i] if i < len(x_rings) - 1 else None
        walls.append((left, right))
    return walls, mids


# =============================================================================
# BOUNDARY WALK WITH NODE IDS
# =============================================================================

def _walk_boundary_with_ids(points_list, boundary_ids, sample_count):
    """
    Walk a closed boundary polyline given as an ordered list of node ids.
    Sample it at `sample_count` evenly-spaced arc-length positions,
    carrying the node id for each sample.

    If a sample falls on an existing node, reuse that id.  If it falls
    between two nodes, insert a NEW node at the exact sample position
    and use the new id.  Either way, return a list of node ids, one per
    sample, plus a dict { node_id : (x, y, z) } for any newly inserted
    nodes.

    This guarantees that the samples are actual nodes: both the ray
    outer point and the fabric attach use the same id.
    """
    n = len(boundary_ids)
    if n < 2:
        return [], {}

    # Build positions along the closed polyline.
    positions = np.zeros((n, 2))
    for i, nid in enumerate(boundary_ids):
        positions[i, 0] = points_list[nid][0]
        positions[i, 1] = points_list[nid][1]

    # Segment lengths.
    seg = np.diff(np.vstack([positions, positions[:1]]), axis=0)
    seglen = np.linalg.norm(seg, axis=1)
    total_len = float(np.sum(seglen))
    if total_len < 1e-9:
        return [], {}
    cum = np.concatenate([[0.0], np.cumsum(seglen)])

    # Sample.
    new_nodes = {}
    sample_ids = []
    for s_idx in range(sample_count):
        s = total_len * s_idx / float(sample_count)
        # Find the segment containing s.
        j = int(np.searchsorted(cum, s, side="right") - 1)
        if j < 0:
            j = 0
        if j >= n:
            j = n - 1
        a = positions[j]
        b = positions[(j + 1) % n]
        seg_len = seglen[j]
        if seg_len < 1e-12:
            # Zero-length segment; reuse the start node.
            sample_ids.append(boundary_ids[j])
            continue
        t = (s - cum[j]) / seg_len
        if t < 1e-6:
            sample_ids.append(boundary_ids[j])
        elif t > 1.0 - 1e-6:
            sample_ids.append(boundary_ids[(j + 1) % n])
        else:
            # Insert a new node at this exact position.
            px = a[0] + t * (b[0] - a[0])
            py = a[1] + t * (b[1] - a[1])
            nid_new = len(points_list)
            # Wall nodes should keep the wall x exactly.
            z_new = points_list[boundary_ids[j]][2]
            points_list.append((px, py, z_new))
            new_nodes[nid_new] = (px, py, z_new)
            sample_ids.append(nid_new)

    return sample_ids, new_nodes


# =============================================================================
# MESH BUILDING
# =============================================================================

def _build_radial_mesh(perimeter_loop, perimeter_anchor_idx,
                       ring_specs, eave_height):
    n_perim = perimeter_loop.shape[0]
    perim_xy = perimeter_loop[:, :2]

    x_rings = [float(s["cx"]) for s in ring_specs]
    walls, mids = _cell_walls_x(x_rings)
    wall_x_values = sorted(w for (wl, wr) in walls for w in (wl, wr)
                           if w is not None)

    # --- Perimeter nodes --------------------------------------
    points_list = [tuple(p) for p in perimeter_loop]
    perimeter_start = 0
    perimeter_end = n_perim
    perimeter_ids = list(range(n_perim))

    # --- Wall node columns ------------------------------------
    ys = perimeter_loop[:, 1]
    y_min = float(np.min(ys))
    y_max = float(np.max(ys))

    wall_columns = {}
    wall_node_set = set()
    n_wall = RAYS_PER_RING
    for wx in wall_x_values:
        col = []
        for k in range(n_wall):
            f = k / float(n_wall - 1) if n_wall > 1 else 0.5
            y = y_min + f * (y_max - y_min)
            z = eave_height
            nid = len(points_list)
            points_list.append((float(wx), float(y), float(z)))
            col.append(nid)
            wall_node_set.add(nid)
        wall_columns[wx] = col

    # --- Ring circles and ring centres ------------------------
    ring_indices = []
    centre_indices = []
    beam_top_indices = []
    ring_node_counts = []
    ring_xy = []

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

        ring_xy.append((cx, cy, r))

    # --- For each ring, build a strip boundary as an ordered id
    #     list, then sample it at RAYS_PER_RING positions.
    #     Generate radial nodes between the ring circle and the
    #     sampled boundary node for each ray.
    fan_notes = []
    ring_radial_rows = []  # list of rows; each row is a list of node ids
    ring_boundary_sample_ids = []  # for later triangle attach

    for k, spec in enumerate(ring_specs):
        cx = float(spec["cx"])
        cy = float(spec["cy"])
        cz = float(spec["cz"])
        r = float(spec["r"])
        eave_z = eave_height

        left_wall = walls[k][0]
        right_wall = walls[k][1]

        # 1. Boundary as an ordered list of existing node ids.
        #    Walk the perimeter in loop order, keeping only perimeter
        #    nodes whose x lies within [left_wall, right_wall].
        #    Then prepend/append the wall columns as appropriate.
        perim_in_strip = []
        for pid in perimeter_ids:
            px = float(perim_xy[pid, 0])
            if left_wall is not None and px < left_wall - 1e-9:
                continue
            if right_wall is not None and px > right_wall + 1e-9:
                continue
            perim_in_strip.append(pid)

        if not perim_in_strip:
            ring_radial_rows.append([])
            ring_boundary_sample_ids.append([])
            fan_notes.append("ring %d : no perimeter nodes in strip"
                             % (k + 1))
            continue

        # Walk the perimeter loop once, starting at the first in-strip
        # node and collecting contiguous in-strip nodes.
        in_strip_set = set(perim_in_strip)
        start_idx = perim_in_strip[0]
        ordered_perim = []
        i = start_idx
        # Guard against infinite loop
        for _ in range(n_perim + 1):
            if i in in_strip_set:
                ordered_perim.append(i)
            i = (i + 1) % n_perim
            if i == start_idx:
                break

        # Split into +y and -y halves.
        perim_plus = [pid for pid in ordered_perim
                      if float(perim_xy[pid, 1]) >= 0.0]
        perim_minus = [pid for pid in ordered_perim
                       if float(perim_xy[pid, 1]) < 0.0]
        # Sort by x for a deterministic walk: top arc from left to right
        # (+x direction); bottom arc from right to left (-x direction).
        perim_top = sorted(perim_plus, key=lambda pid: float(perim_xy[pid, 0]))
        perim_bot = sorted(perim_minus, key=lambda pid: -float(perim_xy[pid, 0]))

        # Build the closed boundary id list:
        #   right wall (top -> bottom),  bottom arc,  left wall (bottom -> top),  top arc
        boundary_ids = []
        if right_wall is not None:
            for nid in reversed(wall_columns[right_wall]):
                boundary_ids.append(nid)
        for pid in perim_bot:
            boundary_ids.append(pid)
        if left_wall is not None:
            for nid in wall_columns[left_wall]:
                boundary_ids.append(nid)
        for pid in perim_top:
            boundary_ids.append(pid)

        # 2. Sample the boundary at RAYS_PER_RING arc-length positions,
        #    carrying node ids (inserting new nodes as needed).
        sample_ids, _new_nodes = _walk_boundary_with_ids(
            points_list, boundary_ids, RAYS_PER_RING
        )
        if not sample_ids:
            ring_radial_rows.append([])
            ring_boundary_sample_ids.append([])
            fan_notes.append("ring %d : empty boundary samples" % (k + 1))
            continue

        # 3. Build radial rows.  For each sample, cast inward to the
        #    ring circle along the direction from the ring centre.
        rows = []
        for j, outer_id in enumerate(sample_ids):
            bx = float(points_list[outer_id][0])
            by = float(points_list[outer_id][1])
            vx = bx - cx
            vy = by - cy
            vlen = math.hypot(vx, vy)
            if vlen < 1e-9:
                ix, iy = cx, cy
            else:
                ix = cx + r * vx / vlen
                iy = cy + r * vy / vlen
            row = []
            for mm in range(RADIAL_NODES):
                f = (mm + 1) / float(RADIAL_NODES + 1)
                px = ix + f * (bx - ix)
                py = iy + f * (by - iy)
                pz = cz + f * (eave_z - cz)
                nid = len(points_list)
                points_list.append((px, py, pz))
                row.append(nid)
            rows.append(row)
        ring_radial_rows.append(rows)
        ring_boundary_sample_ids.append(sample_ids)
        fan_notes.append(
            "ring %d : %d boundary samples, %d radial rows"
            % (k + 1, len(sample_ids), len(rows))
        )

    points = np.asarray(points_list, dtype=float)
    n_total = points.shape[0]

    # --- Triangles --------------------------------------------
    triangles = []

    # (a) Radial quad strips per ring.
    for k in range(len(ring_specs)):
        rows = ring_radial_rows[k]
        if not rows:
            continue
        n_rows = len(rows)
        for j in range(n_rows):
            row_a = rows[j]
            row_b = rows[(j + 1) % n_rows]
            for mm in range(RADIAL_NODES - 1):
                a0 = row_a[mm]
                a1 = row_a[mm + 1]
                b0 = row_b[mm]
                b1 = row_b[mm + 1]
                triangles.append((a0, b0, b1))
                triangles.append((a0, b1, a1))

    # (b) Ring-to-fabric attach.
    for k in range(len(ring_specs)):
        rows = ring_radial_rows[k]
        idx_list = ring_indices[k]
        if not rows:
            continue
        n_poly = len(idx_list)
        cx = float(ring_specs[k]["cx"])
        cy = float(ring_specs[k]["cy"])
        for row in rows:
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

    # (c) Fabric-to-boundary attach.  The boundary sample ids and the
    #     outer ids of the radial rows are the SAME node ids, so this
    #     is a simple join: for each row j, connect the row's outer
    #     node (== boundary sample j) to the boundary samples j and
    #     j+1.  The boundary samples are on shared wall/perimeter
    #     nodes, so adjacent rings automatically meet on the same
    #     ids.
    for k in range(len(ring_specs)):
        rows = ring_radial_rows[k]
        boundary_ids = ring_boundary_sample_ids[k]
        if not rows or not boundary_ids:
            continue
        n_b = len(boundary_ids)
        for j in range(min(n_b, len(rows))):
            outer_id = rows[j][-1]
            b_j = boundary_ids[j]
            b_jp1 = boundary_ids[(j + 1) % n_b]
            if outer_id == b_j:
                # already the same node; skip the degenerate triangle
                pass
            else:
                triangles.append((outer_id, b_j, b_jp1))
            # Also connect to previous boundary sample for closedness.
            b_jm1 = boundary_ids[(j - 1) % n_b]
            if outer_id == b_j:
                triangles.append((outer_id, b_jm1, b_j))

    triangles = [t for t in triangles if t[0] != t[1]
                 and t[1] != t[2] and t[0] != t[2]]

    # --- Edges from triangles ---------------------------------
    edge_set = set()
    for (a, b, c) in triangles:
        for (i, j) in ((a, b), (b, c), (c, a)):
            key = (i, j) if i < j else (j, i)
            edge_set.add(key)

    # --- Ring beam, spoke, drop member edges ------------------
    for k in range(len(ring_specs)):
        idx_list = ring_indices[k]
        centre_i = int(centre_indices[k])
        beam_i = int(beam_top_indices[k])
        n_poly = len(idx_list)
        for i in range(n_poly):
            a = idx_list[i]
            b = idx_list[(i + 1) % n_poly]
            key = (a, b) if a < b else (b, a)
            edge_set.add(key)
        for i in idx_list:
            key = (centre_i, i) if centre_i < i else (i, centre_i)
            edge_set.add(key)
        key = (centre_i, beam_i) if centre_i < beam_i else (beam_i, centre_i)
        edge_set.add(key)

    # --- Perimeter edge set ----------------------------------
    perimeter_edge_set = set()
    for i in range(n_perim):
        j = (i + 1) % n_perim
        key = (i, j) if i < j else (j, i)
        perimeter_edge_set.add(key)

    edges = sorted(edge_set)

    # --- Held nodes ------------------------------------------
    fixed_set = set()
    anchor_node_indices = []
    for i in perimeter_anchor_idx:
        fixed_set.add(int(i))
        anchor_node_indices.append(int(i))
    for idx_list in ring_indices:
        for i in idx_list:
            fixed_set.add(int(i))
    for ci in centre_indices:
        fixed_set.add(int(ci))
    for bi in beam_top_indices:
        fixed_set.add(int(bi))

    anchor_set = set(int(i) for i in perimeter_anchor_idx)
    cable_interior_indices = []
    dir_only_indices = []
    for i in range(n_perim):
        if i in anchor_set:
            continue
        prev_i = (i - 1) % n_perim
        next_i = (i + 1) % n_perim
        tangent = perimeter_loop[next_i] - perimeter_loop[prev_i]
        mag = float(np.linalg.norm(tangent))
        if mag < 1e-12:
            continue
        tangent = tangent / mag
        cable_interior_indices.append(i)
        dir_only_indices.append(
            (int(i), (float(tangent[0]), float(tangent[1]),
                       float(tangent[2]))))

    return {
        "points": points,
        "edges": edges,
        "triangles": triangles,
        "fixed_indices": sorted(fixed_set),
        "dir_only_indices": dir_only_indices,
        "perimeter_start": perimeter_start,
        "perimeter_end": perimeter_end,
        "n_perimeter": n_perim,
        "anchor_node_indices": anchor_node_indices,
        "cable_interior_indices": cable_interior_indices,
        "ring_indices": ring_indices,
        "centre_indices": centre_indices,
        "beam_top_indices": beam_top_indices,
        "ring_node_counts": ring_node_counts,
        "perimeter_edge_set": perimeter_edge_set,
        "fan_notes": fan_notes,
        "ring_xy": ring_xy,
        "cell_walls": walls,
        "cell_mids": mids,
        "ring_radial_rows": ring_radial_rows,
        "wall_x_values": wall_x_values,
        "wall_columns": wall_columns,
        "ring_boundary_sample_ids": ring_boundary_sample_ids,
    }


# =============================================================================
# MEMBER SCHEDULE
# =============================================================================

def _build_member_schedule(built, coords):
    members = []
    ring_indices = built["ring_indices"]
    centre_indices = built["centre_indices"]
    beam_top_indices = built["beam_top_indices"]
    anchor_node_indices = built["anchor_node_indices"]
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

    for i, node_i in enumerate(anchor_node_indices):
        members.append({
            "member_id": f"Anchor_{i+1:02d}_Ground",
            "member_type": "ground_anchor",
            "ring_index": 0,
            "node_a": int(node_i),
            "node_b": int(node_i),
            "length_m": 0.0,
            "section": "TBD",
            "material": "TBD",
            "role": "rigid ground anchor",
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
        "section": "TBD",
        "material": "TBD",
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
            "node_a": int(a),
            "node_b": int(b),
            "length_m": L,
            "section": "TBD",
            "material": "TBD",
            "role": "perimeter edge cable segment",
        })

    return members


def _format_member_table(members):
    lines = []
    header = (
        "%-28s  %-20s  %-5s  %-6s  %-6s  %-9s  %-7s  %-8s  %s"
        % ("member_id", "member_type", "ring", "node_a", "node_b",
           "length_m", "section", "material", "role")
    )
    lines.append(header)
    lines.append("-" * len(header))
    for m in members:
        lines.append(
            "%-28s  %-20s  %-5d  %-6d  %-6d  %-9.4f  %-7s  %-8s  %s"
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


def _status_line(i, status, points_initial, points_settled):
    xi, yi, zi = points_initial[i]
    xs, ys, zs = points_settled[i]
    d = float(np.linalg.norm(np.array([xs - xi, ys - yi, zs - zi])))
    return (
        "%6d  %10.5f  %10.5f  %10.5f  %10.5f  %10.5f  %10.5f  %9.4e  %s"
        % (i, xi, yi, zi, xs, ys, zs, d, status)
    )


def _format_all_nodes(points_initial, points_settled, built):
    n = points_initial.shape[0]
    status_of = ["free"] * n
    for i in built["anchor_node_indices"]:
        status_of[int(i)] = "held_ground_anchor"
    for i in built["cable_interior_indices"]:
        status_of[int(i)] = "cable_interior_dir_only"
    for idx_list in built["ring_indices"]:
        for i in idx_list:
            status_of[int(i)] = "held_ring_polygon"
    for i in built["centre_indices"]:
        status_of[int(i)] = "held_ring_centre"
    for i in built["beam_top_indices"]:
        status_of[int(i)] = "held_beam_top"
    for col in built.get("wall_columns", {}).values():
        for i in col:
            status_of[int(i)] = "shared_wall_node"

    lines = [_HEADER, "-" * len(_HEADER)]
    for i in range(n):
        lines.append(_status_line(i, status_of[i],
                                   points_initial, points_settled))
    return "\n".join(lines)


# =============================================================================
# PAGE
# =============================================================================

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>"
        "Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — shared-wall "
        "partition, ids carried through boundary walk."
        "</p>",
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
    anchors, anchor_local = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, tip_x
    )
    perimeter_loop, perimeter_anchor_idx = \
        _subdivide_polygon_with_anchors(anchors, subdivisions)

    built = _build_radial_mesh(
        perimeter_loop, perimeter_anchor_idx, ring_specs, eave_height
    )

    pts_init = built["points"]
    edges = built["edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]
    dir_only = built["dir_only_indices"]

    warp_q = max(float(warp_q_input), 0.1) * 1000.0
    weft_q = max(float(weft_q_input), 0.1) * 1000.0
    if edge_q_input > 0.0:
        edge_q_scalar = float(edge_q_input) * 1000.0
    else:
        edge_q_scalar = max(warp_q, weft_q) * 5.0
    edge_q_scalar = max(edge_q_scalar, 1.0)

    perim_edge_set = built["perimeter_edge_set"]
    q = np.empty(len(edges), dtype=float)
    for k, (i, j) in enumerate(edges):
        key = (i, j) if i < j else (j, i)
        if key in perim_edge_set:
            q[k] = edge_q_scalar
        else:
            q[k] = warp_q

    try:
        fdm = solve_fdm(pts_init, edges, fixed, q,
                         dir_only_indices=dir_only)
        coords = fdm["coordinates"]
        residual_norm = float(fdm["residual_norm"])
        solve_ok = True
        solve_err = ""
    except Exception as e:
        coords = pts_init.copy()
        residual_norm = float("nan")
        solve_ok = False
        solve_err = str(e)

    anchor_move_max = 0.0
    for i in built["anchor_node_indices"]:
        d = float(np.linalg.norm(coords[i] - pts_init[i]))
        if d > anchor_move_max:
            anchor_move_max = d

    cable_bow_max = 0.0
    for i in built["cable_interior_indices"]:
        p0 = pts_init[(i - 1) % built["n_perimeter"]]
        p1 = pts_init[i]
        p2 = pts_init[(i + 1) % built["n_perimeter"]]
        seg = p2 - p0
        seg_len = float(np.linalg.norm(seg))
        if seg_len < 1e-9:
            continue
        seg_unit = seg / seg_len
        rel = coords[i] - p0
        along = float(np.dot(rel, seg_unit))
        perp = rel - along * seg_unit
        perp_dist = float(np.linalg.norm(perp))
        if perp_dist > cable_bow_max:
            cable_bow_max = perp_dist

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

    anchor_ids = built["anchor_node_indices"]
    if anchor_ids:
        apts = coords[anchor_ids]
        fig.add_trace(go.Scatter3d(
            x=apts[:, 0], y=apts[:, 1], z=apts[:, 2],
            mode="markers",
            marker=dict(color=COL_ANCHOR, size=8, symbol="diamond"),
            name="ground anchor", showlegend=False, hoverinfo="skip",
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

    # --- Plan view ----------------------------------------------
    figp = go.Figure()
    perim_xy = pts_init[ps:pe, :2]
    perim_closed_xy = np.vstack([perim_xy, perim_xy[:1]])
    figp.add_trace(go.Scatter(
        x=perim_closed_xy[:, 0], y=perim_closed_xy[:, 1],
        mode="lines", line=dict(color=COL_PERIMETER, width=3),
        name="perimeter", showlegend=False, hoverinfo="skip",
    ))
    for k, idx_list in enumerate(built["ring_indices"]):
        pp = pts_init[idx_list]
        closed = np.vstack([pp, pp[:1]])
        figp.add_trace(go.Scatter(
            x=closed[:, 0], y=closed[:, 1],
            mode="lines", line=dict(color=COL_RING_EDGE, width=2),
            name=f"ring {k+1}", showlegend=False, hoverinfo="skip",
        ))
    for (wl, wr) in built["cell_walls"]:
        for wx in (wl, wr):
            if wx is not None:
                figp.add_trace(go.Scatter(
                    x=[wx, wx], y=[-10.0, +10.0],
                    mode="lines",
                    line=dict(color=COL_VALLEY, width=2, dash="dash"),
                    name="wall", showlegend=False, hoverinfo="skip",
                ))
    for wx, col in built["wall_columns"].items():
        wx_pts = pts_init[col]
        figp.add_trace(go.Scatter(
            x=wx_pts[:, 0], y=wx_pts[:, 1],
            mode="markers",
            marker=dict(color=COL_WALL, size=6, symbol="square"),
            name=f"wall x={wx:+.2f}", showlegend=False, hoverinfo="skip",
        ))
    ring_node_id_set = set()
    for idx_list in built["ring_indices"]:
        ring_node_id_set.update(int(i) for i in idx_list)
    for i in built["centre_indices"]:
        ring_node_id_set.add(int(i))
    for i in built["beam_top_indices"]:
        ring_node_id_set.add(int(i))
    wall_node_id_set = set()
    for col in built["wall_columns"].values():
        wall_node_id_set.update(int(i) for i in col)
    start_radial = built["n_perimeter"]
    radial_ids = [i for i in range(start_radial, pts_init.shape[0])
                  if i not in ring_node_id_set
                  and i not in wall_node_id_set]
    if radial_ids:
        rp2 = pts_init[radial_ids]
        figp.add_trace(go.Scatter(
            x=rp2[:, 0], y=rp2[:, 1],
            mode="markers",
            marker=dict(color=COL_MEMBRANE, size=3),
            name="radial nodes", showlegend=False, hoverinfo="skip",
        ))
    if anchor_ids:
        ap = pts_init[anchor_ids]
        figp.add_trace(go.Scatter(
            x=ap[:, 0], y=ap[:, 1],
            mode="markers",
            marker=dict(color=COL_ANCHOR, size=10, symbol="diamond"),
            name="anchor", showlegend=False, hoverinfo="skip",
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
        title=dict(text="Fan coverage (plan view, initial mesh)",
                   font=dict(color="#f39c12", size=14)),
    )
    st.plotly_chart(figp, use_container_width=True, key="mc_plan")

    members = _build_member_schedule(built, coords)

    with st.expander("Steel and cable member schedule (BQ and analysis)",
                      expanded=False):
        st.write(f"Total members recorded: {len(members)}")
        st.write(
            "Counts: %d ring beam (consolidated), %d ring beam segments, "
            "%d spokes, %d drop members, %d edge cable (consolidated), "
            "%d edge cable segments, %d ground anchors."
            % (
                sum(1 for m in members if m["member_type"] == "ring_beam"),
                sum(1 for m in members
                    if m["member_type"] == "ring_beam_segment"),
                sum(1 for m in members if m["member_type"] == "spoke"),
                sum(1 for m in members if m["member_type"] == "drop_member"),
                sum(1 for m in members if m["member_type"] == "edge_cable"),
                sum(1 for m in members
                    if m["member_type"] == "edge_cable_segment"),
                sum(1 for m in members
                    if m["member_type"] == "ground_anchor"),
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
        st.write("Ring x positions (m): " +
                 ", ".join(f"{v:+.3f}" for v in x_rings))
        st.write("Cell walls (x, m): " +
                 ", ".join(
                     f"{('%+.3f' % wl) if wl is not None else '-inf'}/"
                     f"{('%+.3f' % wr) if wr is not None else '+inf'}"
                     for (wl, wr) in built["cell_walls"]))
        st.write(f"Wall x values: " +
                 ", ".join(f"{v:+.3f}" for v in built["wall_x_values"]))
        st.write(f"Wall columns: "
                 f"{len(built['wall_columns'])} at "
                 f"{[(round(k,3), len(v)) for k, v in built['wall_columns'].items()]}")
        st.write(f"Outer anchor corners: {anchors.shape[0]}")
        st.write(f"Perimeter nodes: {built['n_perimeter']}")
        st.write(f"Ground anchors: {len(built['anchor_node_indices'])}")
        st.write(f"Cable-interior (dir-only) nodes: "
                 f"{len(built['cable_interior_indices'])}")
        st.write(f"Total mesh nodes: {pts_init.shape[0]}")
        st.write(f"Mesh edges: {len(edges)}")
        st.write(f"Mesh triangles: {len(tris)}")
        st.write(f"Held nodes: {len(fixed)}")
        st.write(f"Dir-only nodes: {len(dir_only)}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Solve error: {solve_err}")
        else:
            st.write(f"Residual norm: {residual_norm:.6e}")
        st.write(f"Max anchor movement (m): {anchor_move_max:.3e} "
                 "(should be 0)")
        st.write(f"Max cable bow off-tangent (m): {cable_bow_max:.3f} "
                 "(small is correct)")
        st.write("Ring node counts: " +
                 ", ".join(str(c) for c in built["ring_node_counts"]))
        st.write("Fan notes:")
        for note in built["fan_notes"]:
            st.write("  " + note)

    with st.expander("All nodes (full digitisation)", expanded=False):
        st.code(
            _format_all_nodes(pts_init, coords, built),
            language="text",
        )
