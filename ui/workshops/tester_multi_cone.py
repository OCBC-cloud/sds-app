"""Multi-Cone Roof — Stage 3 Lab test page.

Version v15.

What is new in this version (v15), versus v14:

  The boundary conditions are now physically correct for a real
  tensile membrane roof.

  v14 fixed every perimeter node.  A real tensile roof does not
  have a rigid perimeter wall.  It has an edge cable, anchored
  at discrete ground anchors, free to sag and to bow in the plan
  plane between anchors.  v15 implements exactly that:

    - fixed_indices = the 8 ground anchors only
      (2 tips + 6 rib crossings), plus every ring polygon node,
      ring centre, and beam-top node.
    - dir_only_indices = every perimeter node between anchors,
      each with its local cable tangent.  The node is free to
      slide along the cable, held off it.  This is the engine's
      dir_only capability, used for the first time here.
    - Perimeter cable edges get edge_q.
    - Fabric edges get warp_q.

  New named members recorded:
    Edge_Cable                    one consolidated
    Edge_Cable_Seg_<k>            one per perimeter segment
    Anchor_<i>_Ground             one per ground anchor

  Viewer additions:
    - Edge cable drawn as a distinct closed line.
    - Ground anchors drawn as markers.

  Diagnostics additions:
    - Anchor count vs cable-interior count.
    - Anchor movement check (should be zero).
    - Cable-interior bow check (small is correct).

Carried over from v14 unchanged:
  - Fan mesh topology (rays from ring centres to perimeter).
  - Cone placement by a single spacing input.
  - Ring z follows the beam: z_ring = beam_z(s_ring) - clearance.
  - Refuse rule if any ring falls outside the span.
  - Member schedule for Ring_Beam, Beam_Seg, Spoke, Drop_Member.
  - All-nodes digitisation.

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

# Radial fan resolution.  Increase for a finer mesh.
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
    """Return the eave anchor loop and the indices of the true
    ground anchors (2 tips + 2 per rib crossing)."""
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

    # Ground anchors: first point is first rib plus-side, last is
    # last rib minus-side?  No.  Anchors are: every rib crossing
    # (both sides) and both tips.
    anchor_local_indices = []
    for i in range(len(rib_x)):
        anchor_local_indices.append(i)                       # plus side
    anchor_local_indices.append(len(plus))                   # +tip
    for i in range(len(rib_x)):
        anchor_local_indices.append(len(plus) + 1 + i)       # minus side
    anchor_local_indices.append(len(pts) - 1)                # -tip

    return np.asarray(pts, dtype=float), sorted(set(anchor_local_indices))


def _subdivide_polygon_with_anchors(anchors, subdivisions):
    """Subdivide each anchor-to-anchor edge into subdivisions
    segments.  Return the full loop and the indices of the true
    anchors within the loop."""
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
# RADIAL FAN MESH
# =============================================================================

def _ray_perimeter_intersection(origin_xy, dir_xy, perimeter_xy):
    """
    Find the intersection of the ray (origin + t*dir, t >= 0) with
    the closed polyline perimeter.  Return the intersection point
    (x, y) with the largest t that is >= 0, or None if the ray
    misses the perimeter.
    """
    n = perimeter_xy.shape[0]
    ox, oy = float(origin_xy[0]), float(origin_xy[1])
    dx, dy = float(dir_xy[0]), float(dir_xy[1])
    best_t = None
    best_pt = None
    for i in range(n):
        ax, ay = float(perimeter_xy[i, 0]), float(perimeter_xy[i, 1])
        bx, by = float(perimeter_xy[(i + 1) % n, 0]), \
                 float(perimeter_xy[(i + 1) % n, 1])
        # Segment P = a + u*(b-a), u in [0,1]
        ex, ey = bx - ax, by - ay
        denom = dx * ey - dy * ex
        if abs(denom) < 1e-12:
            continue
        # Solve: a + u*e = o + t*d
        # u*e - t*d = o - a
        rx, ry = ox - ax, oy - ay
        u = (rx * dy - ry * dx) / denom
        t = (rx * ey - ry * ex) / denom
        if u < -1e-9 or u > 1.0 + 1e-9:
            continue
        if t < 1e-9:
            continue
        if best_t is None or t > best_t:
            best_t = t
            best_pt = (ox + t * dx, oy + t * dy)
    return best_pt


def _build_radial_mesh(perimeter_loop, perimeter_anchor_idx,
                       ring_specs, eave_height):
    """
    Build the radial fan mesh.

    Returns dict with:
      points, edges, triangles,
      fixed_indices, dir_only_indices,
      perimeter_start, perimeter_end,
      anchor_node_indices, cable_interior_indices,
      ring_indices, centre_indices, beam_top_indices,
      perimeter_edge_set, edge_cable_edge_set,
      fan_notes
    """
    n_perim = perimeter_loop.shape[0]
    perim_xy = perimeter_loop[:, :2]

    # --- Point list, in order -------------------------------------
    points_list = [tuple(p) for p in perimeter_loop]
    perimeter_start = 0
    perimeter_end = n_perim

    n_ring_poly_total = 0
    ring_indices = []
    centre_indices = []
    beam_top_indices = []
    ring_node_counts = []
    ring_xy = []  # (cx, cy, r)

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
        n_ring_poly_total += n_poly

        centre_indices.append(len(points_list))
        points_list.append((cx, cy, cz))

        beam_top_indices.append(len(points_list))
        points_list.append((cx, cy, float(spec["beam_z"])))

        ring_xy.append((cx, cy, r))

    # --- Radial nodes ---------------------------------------------
    radial_node_rows = []  # for each ring, a list of lists of node ids
    fan_notes = []

    for k, spec in enumerate(ring_specs):
        cx = float(spec["cx"])
        cy = float(spec["cy"])
        cz = float(spec["cz"])
        r = float(spec["r"])
        beam_z = float(spec["beam_z"])

        ring_radial_rows = []
        n_hit = 0
        n_miss = 0
        for j in range(RAYS_PER_RING):
            theta = 2.0 * math.pi * j / float(RAYS_PER_RING)
            dx = math.cos(theta)
            dy = math.sin(theta)

            hit = _ray_perimeter_intersection((cx, cy), (dx, dy),
                                                perim_xy)
            if hit is None:
                n_miss += 1
                ring_radial_rows.append([])
                continue
            n_hit += 1

            # Ray starts at ring circle, ends at perimeter.
            inner_xy = (cx + r * dx, cy + r * dy)
            outer_xy = hit

            row = []
            for m in range(RADIAL_NODES):
                f = (m + 1) / float(RADIAL_NODES + 1)
                px = inner_xy[0] + f * (outer_xy[0] - inner_xy[0])
                py = inner_xy[1] + f * (outer_xy[1] - inner_xy[1])
                # Height: linear from ring z to eave height along
                # the ray.  The FDM solver will find the real shape.
                pz = cz + f * (eave_height - cz)
                node_id = len(points_list)
                points_list.append((px, py, pz))
                row.append(node_id)
            ring_radial_rows.append(row)
        radial_node_rows.append(ring_radial_rows)
        fan_notes.append(
            "ring %d: %d rays hit perimeter, %d missed"
            % (k + 1, n_hit, n_miss)
        )

    points = np.asarray(points_list, dtype=float)
    n_total = points.shape[0]

    # --- Triangles: fan per ring, quad strips split --------------
    triangles = []
    for k in range(len(ring_specs)):
        rows = radial_node_rows[k]
        idx_list = ring_indices[k]
        n_poly = len(idx_list)
        for j in range(RAYS_PER_RING):
            row_a = rows[j]
            row_b = rows[(j + 1) % RAYS_PER_RING]
            if len(row_a) == 0 or len(row_b) == 0:
                continue
            for m in range(RADIAL_NODES - 1):
                a0 = row_a[m]
                a1 = row_a[m + 1]
                b0 = row_b[m]
                b1 = row_b[m + 1]
                # Quad (a0, b0, b1, a1).  Two triangles.
                triangles.append((a0, b0, b1))
                triangles.append((a0, b1, a1))

        # --- Attach innermost radial nodes to the ring polygon --
        # Each ray's innermost node (row[m=0]) is attached to the
        # nearest ring polygon node.
        for j in range(RAYS_PER_RING):
            row = rows[j]
            if len(row) == 0:
                continue
            inner_id = row[0]
            theta = 2.0 * math.pi * j / float(RAYS_PER_RING)
            # Nearest ring polygon node by angle.
            # ring polygon node k is at angle 2*pi*k/n_poly.
            kk = int(round(theta / (2.0 * math.pi / n_poly))) % n_poly
            poly_id = idx_list[kk]
            triangles.append((poly_id, inner_id, row[1] if len(row) > 1
                              else inner_id))

        # --- Attach outermost radial nodes to perimeter ----------
        for j in range(RAYS_PER_RING):
            row = rows[j]
            if len(row) == 0:
                continue
            outer_id = row[-1]
            px = float(points[outer_id, 0])
            py = float(points[outer_id, 1])
            # Nearest perimeter node.
            best = None
            best_d2 = None
            for i in range(n_perim):
                qx = float(perim_xy[i, 0])
                qy = float(perim_xy[i, 1])
                d2 = (qx - px) ** 2 + (qy - py) ** 2
                if best_d2 is None or d2 < best_d2:
                    best_d2 = d2
                    best = i
            if best is None:
                continue
            triangles.append((outer_id, best,
                              (best + 1) % n_perim))

    # --- Bridge between adjacent rings (saddle) -----------------
    for k in range(len(ring_specs) - 1):
        rows_a = radial_node_rows[k]
        rows_b = radial_node_rows[k + 1]
        for j in range(RAYS_PER_RING):
            row_a = rows_a[j]
            row_b = rows_b[j]
            if len(row_a) == 0 or len(row_b) == 0:
                continue
            # Connect the outermost node of ring k row to the
            # innermost node of ring k+1 row when they are on the
            # same ray direction.  Simpler and safer: connect the
            # last node of ring k to the first node of ring k+1
            # if they lie between the two rings.
            # Use the last node of ring k and the first node of
            # ring k+1 as a 4-node quad with the same on the next
            # ray.
            jn = (j + 1) % RAYS_PER_RING
            row_a2 = rows_a[jn]
            row_b2 = rows_b[jn]
            if len(row_a2) == 0 or len(row_b2) == 0:
                continue
            a_last = row_a[-1]
            a2_last = row_a2[-1]
            b_first = row_b[0]
            b2_first = row_b2[0]
            triangles.append((a_last, a2_last, b2_first))
            triangles.append((a_last, b2_first, b_first))

    triangles = [t for t in triangles if t[0] != t[1]
                 and t[1] != t[2] and t[0] != t[2]]

    # --- Edges from triangles ------------------------------------
    edge_set = set()
    for (a, b, c) in triangles:
        for (i, j) in ((a, b), (b, c), (c, a)):
            key = (i, j) if i < j else (j, i)
            edge_set.add(key)

    # --- Ring beam, spoke, drop member edges --------------------
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

    # --- Perimeter edge set (for edge cable q) ------------------
    perimeter_edge_set = set()
    for i in range(n_perim):
        j = (i + 1) % n_perim
        key = (i, j) if i < j else (j, i)
        perimeter_edge_set.add(key)

    edges = sorted(edge_set)

    # --- Held nodes ----------------------------------------------
    fixed_set = set()
    # Ground anchors.
    anchor_node_indices = []
    for i in perimeter_anchor_idx:
        fixed_set.add(int(i))
        anchor_node_indices.append(int(i))
    # Ring polygon nodes.
    for idx_list in ring_indices:
        for i in idx_list:
            fixed_set.add(int(i))
    # Ring centres.
    for ci in centre_indices:
        fixed_set.add(int(ci))
    # Beam-tops.
    for bi in beam_top_indices:
        fixed_set.add(int(bi))

    # --- Cable-interior nodes with dir-only tangent -------------
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

    # --- Ring beam, segments, spokes, drop members --------------
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

    # --- Ground anchors -----------------------------------------
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

    # --- Edge cable, consolidated + segments --------------------
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
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — radial fan mesh, "
        "real tensile boundary conditions (edge cable, discrete anchors)."
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

    # --- Geometry inputs ----------------------------------------
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

    # --- Build radial mesh --------------------------------------
    built = _build_radial_mesh(
        perimeter_loop, perimeter_anchor_idx, ring_specs, eave_height
    )

    pts_init = built["points"]
    edges = built["edges"]
    tris = built["triangles"]
    fixed = built["fixed_indices"]
    dir_only = built["dir_only_indices"]

    # --- Force densities ----------------------------------------
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

    # --- Solve --------------------------------------------------
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

    # --- Anchor / cable sanity checks ---------------------------
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

    # --- Figure --------------------------------------------------
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

    # --- Edge cable as one closed line --------------------------
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

    # --- Ground anchor markers ----------------------------------
    anchor_ids = built["anchor_node_indices"]
    if anchor_ids:
        apts = coords[anchor_ids]
        fig.add_trace(go.Scatter3d(
            x=apts[:, 0], y=apts[:, 1], z=apts[:, 2],
            mode="markers",
            marker=dict(color=COL_ANCHOR, size=8, symbol="diamond"),
            name="ground anchor", showlegend=False, hoverinfo="skip",
        ))

    # --- Ring assembly ------------------------------------------
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

    # --- Member schedule ----------------------------------------
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
        st.write("Ring arc-length positions (m): " +
                 ", ".join(f"{v:.3f}" for v in s_rings))
        st.write("Ring x positions (m): " +
                 ", ".join(f"{v:+.3f}" for v in x_rings))
        st.write("Beam z at ring stations (m): " +
                 ", ".join(f"{v:.3f}" for v in beam_z_rings))
        st.write("Ring z at ring stations (m): " +
                 ", ".join(f"{v:.3f}" for v in ring_z_rings))
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
