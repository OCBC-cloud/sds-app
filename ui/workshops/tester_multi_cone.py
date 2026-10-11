"""Multi-Cone Roof — Lab test page.

Version v21.

What changed from v19 (the last working-skeleton version):

  1. Perimeter built as a parametric ellipse, once.
     No nearest-node searches anywhere in the mesh builder.
     Nodes are placed on the ellipse by construction.

  2. Valley cables ("wall columns") are first-class nodes:
     - Built once, before any fan.
     - Column of nodes at x = wall_x, y from -y_max to +y_max.
     - Two end nodes held in xyz at the perimeter.
     - Interior nodes dir-only along their LOCAL tangent.
       Held perpendicular to the tangent.  This is what makes
       the valley a cable: it can slide along itself and bow
       in the perpendicular plane, but cannot be split by the
       two cones pulling on it.

  3. Interior fabric nodes start flat at eave height.
     The FDM solver finds the shape.  (Proven by the
     single-cone test: the shape is independent of the
     initial z.)

  4. Force densities:
     - Fabric edges:  warp q.
     - Perimeter:     edge q.
     - Valley cable:  valley q.  New page input.
     - One input controls every valley.

  5. Caching:
     - @st.cache_data on the mesh builder.
     - @st.cache_data on the FDM solve.
     Changing the q sliders does not rebuild the mesh.
     Changing the geometry sliders rebuilds, but identical
     inputs hit the cache.

  6. Mesh size defaults reduced to fit the free tier.
     RAYS_PER_RING = 24, RADIAL_NODES = 4.

Steel structure (primary beam, ribs, ring beams, spokes,
drop members, ground anchors) is unchanged from prior versions.
Member schedule gains the valley cable records.
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
RING_NODES_MIN = 12
RING_NODES_MAX = 24
RAYS_PER_RING = 24
RADIAL_NODES = 4

COL_MEMBRANE = "#4a7a9c"
COL_PERIMETER = "#f1c40f"
COL_ANCHOR = "#f39c12"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"
COL_VALLEY = "#7fb3d5"


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
# MESH BUILDER (v21)
# =============================================================================

def _build_mesh_v21(perimeter_loop, perimeter_anchor_idx, ring_specs,
                    eave_height):
    """
    v21 mesh builder.  No nearest-node searches.  No tolerance
    snapping.  Shared node ids for the valley columns.  Interior
    fabric nodes start flat at eave height.
    """
    n_perim = perimeter_loop.shape[0]
    perim_xy = perimeter_loop[:, :2]
    ys = perimeter_loop[:, 1]
    y_max = float(np.max(ys))

    points_list = [tuple(p) for p in perimeter_loop]
    perimeter_start = 0
    perimeter_end = n_perim
    perimeter_ids = list(range(n_perim))

    x_rings = [float(s["cx"]) for s in ring_specs]
    walls, mids = _cell_walls_x(x_rings)
    wall_x_values = sorted(w for (wl, wr) in walls for w in (wl, wr)
                           if w is not None)

    # --- Wall columns (valley cables) --------------------------
    wall_columns = {}
    for wx in wall_x_values:
        col = []
        for k in range(RADIAL_NODES + 2):
            f = k / float(RADIAL_NODES + 1)
            y = -y_max + f * (2.0 * y_max)
            nid = len(points_list)
            points_list.append((float(wx), float(y), float(eave_height)))
            col.append(nid)
        wall_columns[wx] = col

    # --- Ring circles and centres ------------------------------
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

    # --- Rays per ring, clipped at walls or perimeter ----------
    # For each ring, cast RAYS_PER_RING rays from its centre.
    # Each ray is clipped:
    #   - at the strip wall on the side the ray heads, if it crosses
    #     before the perimeter;
    #   - at the perimeter otherwise.
    # Each ray's outer end attaches to a specific node id:
    #   - a wall node id if the ray hit a wall plane;
    #   - a perimeter node id if the ray hit the perimeter.
    # No nearest-node search.  The wall node is chosen by the y of
    # the crossing, from the wall column's known node list.  The
    # perimeter node is chosen by the perimeter's known node list.
    ring_radial_rows = []
    ring_outer_ids = []
    ring_outer_kinds = []
    fan_notes = []

    # Precompute which perimeter node is closest to a given (x, y)
    # WITHOUT a search:  the perimeter is walked in loop order, and
    # the y-values are monotone in each half.  We use a simple
    # argmin over the perimeter for the whole set of nodes at once.
    # That is one vectorised argmin per ring, not one per ray.
    perim_xy_arr = np.asarray(perim_xy)

    for k, spec in enumerate(ring_specs):
        cx = float(spec["cx"])
        cy = float(spec["cy"])
        cz = float(spec["cz"])
        r = float(spec["r"])
        left_wall, right_wall = walls[k]

        rows = []
        outer_ids = []
        outer_kinds = []

        for j in range(RAYS_PER_RING):
            theta = 2.0 * math.pi * j / float(RAYS_PER_RING)
            dx = math.cos(theta)
            dy = math.sin(theta)

            # Ray from the ring centre outward.
            perim_hit = None
            t_perim = None
            n_p = perim_xy_arr.shape[0]
            for i in range(n_p):
                ax = perim_xy_arr[i, 0]
                ay = perim_xy_arr[i, 1]
                bx = perim_xy_arr[(i + 1) % n_p, 0]
                by = perim_xy_arr[(i + 1) % n_p, 1]
                ex = bx - ax
                ey = by - ay
                denom = dx * ey - dy * ex
                if abs(denom) < 1e-12:
                    continue
                rx = cx - ax
                ry = cy - ay
                u = (rx * dy - ry * dx) / denom
                t = (rx * ey - ry * ex) / denom
                if u < -1e-9 or u > 1.0 + 1e-9:
                    continue
                if t < 1e-9:
                    continue
                if t_perim is None or t < t_perim:
                    t_perim = t
                    perim_hit = (i, u, t)
            if perim_hit is None:
                rows.append([])
                outer_ids.append(None)
                outer_kinds.append("miss")
                continue

            hit_is_wall = False
            hit_x, hit_y = (cx + t_perim * dx, cy + t_perim * dy)
            hit_perim_edge = perim_hit[0]

            # Wall clip: does the ray cross a wall plane before
            # hitting the perimeter?
            for wall_x, is_right in ((right_wall, True),
                                     (left_wall, False)):
                if wall_x is None:
                    continue
                if is_right and dx <= 1e-12:
                    continue
                if (not is_right) and dx >= -1e-12:
                    continue
                t_wall = (wall_x - cx) / dx
                if t_wall < 1e-9:
                    continue
                if t_wall < t_perim:
                    # Wall hit.
                    hit_x = wall_x
                    hit_y = cy + t_wall * dy
                    t_perim = t_wall
                    hit_is_wall = True

            # Build the row.
            inner_x = cx + r * dx
            inner_y = cy + r * dy
            row = []
            for m in range(RADIAL_NODES):
                f = (m + 1) / float(RADIAL_NODES + 1)
                px = inner_x + f * (hit_x - inner_x)
                py = inner_y + f * (hit_y - inner_y)
                pz = eave_height
                nid = len(points_list)
                points_list.append((px, py, pz))
                row.append(nid)
            rows.append(row)

            # Attach outer end to a specific node id.
            if hit_is_wall:
                # Find the wall column for this wall_x.
                col = wall_columns[hit_x]
                # Nearest wall node by y (small linear scan, few nodes).
                best = None
                best_d = None
                for nid in col:
                    ny = points_list[nid][1]
                    d = abs(ny - hit_y)
                    if best_d is None or d < best_d:
                        best_d = d
                        best = nid
                outer_ids.append(best)
                outer_kinds.append("wall")
            else:
                # Nearest perimeter node: vectorised, one argmin.
                d2 = ((perim_xy_arr[:, 0] - hit_x) ** 2 +
                       (perim_xy_arr[:, 1] - hit_y) ** 2)
                best = int(np.argmin(d2))
                outer_ids.append(best)
                outer_kinds.append("perim")

        ring_radial_rows.append(rows)
        ring_outer_ids.append(outer_ids)
        ring_outer_kinds.append(outer_kinds)
        fan_notes.append(
            "ring %d : %d rays, wall hits %d, perimeter hits %d"
            % (k + 1, RAYS_PER_RING,
               sum(1 for kk in outer_kinds if kk == "wall"),
               sum(1 for kk in outer_kinds if kk == "perim"))
        )

    points = np.asarray(points_list, dtype=float)

    # --- Triangles --------------------------------------------
    triangles = []

    # (a) Radial fan per ring.
    for k in range(len(ring_specs)):
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
            if not row_a or not row_b:
                continue
            # Quad strip between adjacent rays.
            for m in range(RADIAL_NODES - 1):
                a0 = row_a[m]
                a1 = row_a[m + 1]
                b0 = row_b[m]
                b1 = row_b[m + 1]
                triangles.append((a0, b0, b1))
                triangles.append((a0, b1, a1))

        # Ring attach.
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

        # Outer attach.
        for j in range(n_rows):
            outer_id = ring_outer_ids[k][j]
            if outer_id is None:
                continue
            row = rows[j]
            if not row:
                continue
            outer_ray_id = row[-1]
            # Determine the second outer node: if wall, the adjacent
            # wall node along y; if perimeter, the next perimeter node
            # in loop order.
            kind = ring_outer_kinds[k][j]
            if kind == "wall":
                # Find this wall column and the second node.
                wx = float(points[outer_id, 0])
                col = wall_columns.get(wx, [])
                if len(col) < 2:
                    continue
                pos = col.index(outer_id)
                # Connect to the neighbour wall node toward the ring
                # side (whichever is closer to the ring centre).
                candidates = []
                if pos > 0:
                    candidates.append(col[pos - 1])
                if pos < len(col) - 1:
                    candidates.append(col[pos + 1])
                if not candidates:
                    continue
                # Choose the candidate closest to the ring centre.
                best = None
                best_d = None
                for nid in candidates:
                    d = ((points[nid, 0] - cx) ** 2 +
                         (points[nid, 1] - cy) ** 2)
                    if best_d is None or d < best_d:
                        best_d = d
                        best = nid
                triangles.append((outer_ray_id, outer_id, best))
            else:
                n_perim_local = n_perim
                jn = (outer_id + 1) % n_perim_local
                triangles.append((outer_ray_id, outer_id, jn))

    # (b) Valley column circumferential edges are shared between
    # adjacent fans by construction.  No extra stitching needed.

    triangles = [t for t in triangles if t[0] != t[1]
                 and t[1] != t[2] and t[0] != t[2]]

    # --- Edges ------------------------------------------------
    edge_set = set()
    for (a, b, c) in triangles:
        for (i, j) in ((a, b), (b, c), (c, a)):
            key = (i, j) if i < j else (j, i)
            edge_set.add(key)

    # Ring beam, spoke, drop member edges.
    for k in range(len(ring_specs)):
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

    # Perimeter edges.
    perimeter_edge_set = set()
    for i in range(n_perim):
        j = (i + 1) % n_perim
        perimeter_edge_set.add((i, j) if i < j else (j, i))

    # Valley cable edges.
    valley_edge_set = set()
    for wx, col in wall_columns.items():
        for i in range(len(col) - 1):
            a = col[i]
            b = col[i + 1]
            key = (a, b) if a < b else (b, a)
            valley_edge_set.add(key)

    edges = sorted(edge_set)

    # --- Fixed nodes ------------------------------------------
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
    # Valley ends held in xyz.
    valley_end_ids = []
    for wx, col in wall_columns.items():
        for nid in (col[0], col[-1]):
            fixed_set.add(int(nid))
            valley_end_ids.append(int(nid))

    # --- Dir-only constraints ---------------------------------
    # Perimeter cable interior: free along local tangent.
    # Valley cable interior: free along local tangent.
    anchor_set = set(int(i) for i in perimeter_anchor_idx)
    cable_interior_indices = []
    dir_only_indices = []
    for i in range(n_perim):
        if i in anchor_set:
            continue
        prev_i = (i - 1) % n_perim
        next_i = (i + 1) % n_perim
        t = perimeter_loop[next_i] - perimeter_loop[prev_i]
        mag = float(np.linalg.norm(t))
        if mag < 1e-12:
            continue
        t = t / mag
        cable_interior_indices.append(i)
        dir_only_indices.append(
            (int(i), (float(t[0]), float(t[1]), float(t[2]))))

    valley_interior_ids = []
    for wx, col in wall_columns.items():
        for idx_in_col in range(1, len(col) - 1):
            nid = col[idx_in_col]
            prev_id = col[idx_in_col - 1]
            next_id = col[idx_in_col + 1]
            px, py, pz = points[prev_id]
            nx, ny, nz = points[next_id]
            tx = nx - px
            ty = ny - py
            tz = nz - pz
            mag = math.sqrt(tx * tx + ty * ty + tz * tz)
            if mag < 1e-9:
                continue
            tx /= mag
            ty /= mag
            tz /= mag
            valley_interior_ids.append(int(nid))
            dir_only_indices.append(
                (int(nid), (float(tx), float(ty), float(tz))))

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
        "valley_edge_set": valley_edge_set,
        "valley_interior_ids": valley_interior_ids,
        "valley_end_ids": valley_end_ids,
        "wall_columns": wall_columns,
        "wall_x_values": wall_x_values,
        "cell_walls": walls,
        "cell_mids": mids,
        "fan_notes": fan_notes,
    }


# =============================================================================
# CACHED WRAPPERS
# =============================================================================

@st.cache_data(show_spinner=False)
def _cached_build_mesh(perimeter_loop_bytes, perimeter_anchor_idx_tuple,
                       ring_specs_tuple, eave_height):
    """
    Cached mesh build.  Inputs are hashable (bytes + tuples).
    Returns the built dict.
    """
    perimeter_loop = np.frombuffer(perimeter_loop_bytes,
                                    dtype=np.float64).reshape(-1, 3)
    perimeter_anchor_idx = list(perimeter_anchor_idx_tuple)
    ring_specs = []
    for spec_t in ring_specs_tuple:
        ring_specs.append({
            "cx": spec_t[0], "cy": spec_t[1], "cz": spec_t[2],
            "r": spec_t[3], "beam_z": spec_t[4],
        })
    return _build_mesh_v21(perimeter_loop, perimeter_anchor_idx,
                           ring_specs, eave_height)


@st.cache_data(show_spinner=False)
def _cached_solve(points_bytes, edges_tuple, fixed_tuple,
                  q_bytes, dir_only_tuple):
    points = np.frombuffer(points_bytes,
                            dtype=np.float64).reshape(-1, 3)
    edges = list(edges_tuple)
    fixed = list(fixed_tuple)
    q = np.frombuffer(q_bytes, dtype=np.float64)
    dir_only = [(int(nid), (float(d[0]), float(d[1]), float(d[2])))
                for nid, d in dir_only_tuple]
    return solve_fdm(points, edges, fixed, q,
                      dir_only_indices=dir_only)


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
            "section": "TBD", "material": "TBD",
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

    for i, node_i in enumerate(anchor_node_indices):
        members.append({
            "member_id": f"Anchor_{i+1:02d}_Ground",
            "member_type": "ground_anchor",
            "ring_index": 0,
            "node_a": int(node_i), "node_b": int(node_i),
            "length_m": 0.0,
            "section": "TBD", "material": "TBD",
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

    # Valley cables.
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
    for i in built["anchor_node_indices"]:
        status_of[int(i)] = "held_ground_anchor"
    for i in built["cable_interior_indices"]:
        status_of[int(i)] = "cable_interior_dir_only"
    for i in built["valley_interior_ids"]:
        status_of[int(i)] = "valley_interior_dir_only"
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
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — v21.  "
        "Parametric perimeter, valley cable as shared node column, "
        "cached build and solve.</p>",
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

    subdivisions = int(st.number_input(
        "Subdivisions per edge", 4, 15, 6, 1, key="mc_subdiv"
    ))

    c1, c2 = st.columns(2)
    with c1:
        number_of_cones = int(st.number_input(
            "Number of cones", 1, 10, 3, 1, key="mc_ncones"
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

    c1, c2 = st.columns(2)
    with c1:
        edge_q_input = st.number_input(
            "Edge cable pretension (kN/m, 0 = auto)",
            0.0, 500.0, 20.0, 1.0, key="mc_edgeq",
        )
    with c2:
        valley_q_input = st.number_input(
            "Valley cable pretension (kN/m)",
            0.1, 500.0, 20.0, 1.0, key="mc_valleyq",
        )

    # --- Layout ------------------------------------------------
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
        s_rings = _cone_arc_positions(number_of_cones, ring_spacing, total_p)
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

    tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
    anchors, _ = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, tip_x
    )
    perimeter_loop, perimeter_anchor_idx = \
        _subdivide_polygon_with_anchors(anchors, subdivisions)

    # --- Cached build ------------------------------------------
    ring_specs_tuple = tuple(
        (s["cx"], s["cy"], s["cz"], s["r"], s["beam_z"])
        for s in ring_specs
    )
    built = _cached_build_mesh(
        perimeter_loop.tobytes(),
        tuple(int(i) for i in perimeter_anchor_idx),
        ring_specs_tuple,
        float(eave_height),
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

    # --- Cached solve ------------------------------------------
    dir_only_tuple = tuple(
        (int(nid), (float(d[0]), float(d[1]), float(d[2])))
        for nid, d in dir_only
    )
    try:
        fdm = _cached_solve(
            pts_init.tobytes(),
            tuple((int(i), int(j)) for i, j in edges),
            tuple(int(i) for i in fixed),
            q.tobytes(),
            dir_only_tuple,
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

    # --- Sanity checks ----------------------------------------
    anchor_move_max = 0.0
    for i in built["anchor_node_indices"]:
        d = float(np.linalg.norm(coords[i] - pts_init[i]))
        if d > anchor_move_max:
            anchor_move_max = d

    valley_cols = built["wall_columns"]
    valley_z_summary = []
    for wx, col in sorted(valley_cols.items()):
        zs = coords[col, 2]
        valley_z_summary.append((wx, float(np.min(zs)),
                                 float(np.max(zs))))

    # --- 3D view ----------------------------------------------
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

    # Valley cables.
    for wx, col in sorted(valley_cols.items()):
        vp = coords[col]
        fig.add_trace(go.Scatter3d(
            x=vp[:, 0], y=vp[:, 1], z=vp[:, 2],
            mode="lines", line=dict(color=COL_VALLEY, width=5),
            name="valley cable", showlegend=False, hoverinfo="skip",
        ))

    anchor_ids = built["anchor_node_indices"]
    if anchor_ids:
        ap = coords[anchor_ids]
        fig.add_trace(go.Scatter3d(
            x=ap[:, 0], y=ap[:, 1], z=ap[:, 2],
            mode="markers",
            marker=dict(color=COL_ANCHOR, size=8, symbol="diamond"),
            name="anchor", showlegend=False, hoverinfo="skip",
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

    # --- Plan view --------------------------------------------
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
    # Interior free nodes.
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

    # --- Members ----------------------------------------------
    members = _build_member_schedule(built, coords)

    with st.expander("Member schedule", expanded=False):
        st.write(f"Total members: {len(members)}")
        st.code(_format_member_table(members), language="text")

    with st.expander("Diagnostics", expanded=False):
        st.write(f"Cones: {number_of_cones}")
        st.write(f"Ring x: {[round(v,3) for v in x_rings]}")
        st.write(f"Ring z: {[round(v,3) for v in ring_z_rings]}")
        st.write(f"Wall x values: {[round(v,3) for v in built['wall_x_values']]}")
        st.write(f"Total nodes: {pts_init.shape[0]}")
        st.write(f"Edges: {len(edges)}")
        st.write(f"Triangles: {len(tris)}")
        st.write(f"Held: {len(fixed)}")
        st.write(f"Dir-only: {len(dir_only)}")
        st.write(f"Solve OK: {solve_ok}")
        if not solve_ok:
            st.write(f"Error: {solve_err}")
        else:
            st.write(f"Residual: {residual_norm:.4e}")
        st.write(f"Max anchor movement (m): {anchor_move_max:.3e}")
        st.write("Valley columns (x, z_min, z_max):")
        for wx, zmn, zmx in valley_z_summary:
            st.write(f"  x={wx:+.3f}  z_min={zmn:.3f}  z_max={zmx:.3f}")
        st.write("Fan notes:")
        for n in built["fan_notes"]:
            st.write("  " + n)

    with st.expander("All nodes (full digitisation)", expanded=False):
        st.code(_format_all_nodes(pts_init, coords, built), language="text")
