"""Two Cone — Isolated valley test page.

Purpose: prove that a valley between two cones behaves correctly
when treated as a cable:
  - Valley END nodes held in xyz (at the eave).
  - Valley INTERIOR nodes free along their LOCAL cable tangent,
    held perpendicular to it.  This is done with solve_fdm's
    dir_only_indices, using the actual local tangent from the
    mesh geometry, not a hard-coded axis.
  - Valley edges get their own force density input: valley_q.
  - Perimeter edges get their own force density input: edge_q.
  - Fabric edges get warp_q.

No primary beam.  No ribs.  No drop members.  No anchors beyond the
valley ends and the perimeter cable.  Two rings, one eave, one
valley.  Enough to prove the valley treatment, nothing else.
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding import solve_fdm
from viewers.figures._shared import apply_common_layout


COL_MEMBRANE = "#4a7a9c"
COL_RING = "#ffd166"
COL_EAVE = "#f1c40f"
COL_VALLEY = "#7fb3d5"
COL_VALLEY_END = "#f39c12"


# =============================================================================
# MESH
# =============================================================================

def _two_cone_mesh(cone_separation, ring_radius, eave_half_width,
                   ring_z, n_rays, n_radial, z_start,
                   n_perimeter=48):
    """
    Build a two-cone fan mesh with a valley between the cones.

    Layout, all in plan:
      Ring A at (x = -cone_separation/2, y = 0).
      Ring B at (x = +cone_separation/2, y = 0).
      Perimeter: an ellipse with semi-axes (span_x, eave_half_width),
      centred at (0, 0).  span_x is set so the ellipse comfortably
      encloses both rings; we take it as cone_separation + eave_half_width.

    The valley is the vertical line x = 0, y in [-y_max, +y_max]
    where y_max is the half-width of the valley at that x.

    The valley nodes:
      - Two end nodes on the perimeter at x = 0.
      - A column of interior nodes at x = 0, y spanning between them.
    Both cones' fans attach to the valley column.  The valley edges
    get valley_q.  The valley interior nodes are dir-only along the
    local valley tangent (which is close to the y axis but computed
    from the actual node positions).

    Returns dict with everything the page needs.
    """
    cx = 0.0
    cy = 0.0
    span_x = cone_separation + eave_half_width
    a_ell = span_x
    b_ell = eave_half_width

    points = []

    # --- Perimeter nodes ---------------------------------------
    perimeter_ids = []
    for i in range(n_perimeter):
        t = 2.0 * math.pi * i / float(n_perimeter)
        x = a_ell * math.cos(t)
        y = b_ell * math.sin(t)
        perimeter_ids.append(len(points))
        points.append((x, y, 0.0))

    # --- Ring A and Ring B -------------------------------------
    def make_ring(rx, ry, rz):
        ids = []
        for j in range(n_rays):
            t = 2.0 * math.pi * j / float(n_rays)
            x = rx + ring_radius * math.cos(t)
            y = ry + ring_radius * math.sin(t)
            ids.append(len(points))
            points.append((x, y, rz))
        return ids

    ring_a_x = -cone_separation / 2.0
    ring_b_x = +cone_separation / 2.0
    ring_a_ids = make_ring(ring_a_x, 0.0, ring_z)
    ring_b_ids = make_ring(ring_b_x, 0.0, ring_z)

    # --- Valley column ----------------------------------------
    # We need the valley to run from the perimeter at x=0, y > 0,
    # down to the perimeter at x=0, y < 0, with n_valley interior
    # nodes in between.
    #
    # Find the perimeter y values at x = 0.  The ellipse crosses
    # x = 0 at y = +/- b_ell.
    valley_y_top = +b_ell
    valley_y_bot = -b_ell

    n_valley_interior = 6
    valley_ids = []  # ordered from top (y > 0) to bottom (y < 0)
    valley_end_top = None
    valley_end_bot = None

    # Find nearest perimeter nodes to the top and bottom valley ends.
    best_top = None
    best_top_d = None
    best_bot = None
    best_bot_d = None
    for pid in perimeter_ids:
        x, y, _ = points[pid]
        d_top = (x - 0.0) ** 2 + (y - valley_y_top) ** 2
        d_bot = (x - 0.0) ** 2 + (y - valley_y_bot) ** 2
        if best_top_d is None or d_top < best_top_d:
            best_top_d = d_top
            best_top = pid
        if best_bot_d is None or d_bot < best_bot_d:
            best_bot_d = d_bot
            best_bot = pid
    valley_end_top = best_top
    valley_end_bot = best_bot

    # Interior valley nodes on the line x = 0 between the two ends.
    # Their initial z is at eave (0) — the solver will find their z.
    for m in range(n_valley_interior):
        f = (m + 1) / float(n_valley_interior + 1)
        y = valley_y_top + f * (valley_y_bot - valley_y_top)
        valley_ids.append(len(points))
        points.append((0.0, y, z_start))

    # Full ordered valley column, top end to bottom end.
    valley_column_ids = [valley_end_top] + valley_ids + [valley_end_bot]

    # --- Fan rows for each cone -------------------------------
    # For each ring, cast rays from the ring centre.  Each ray
    # stops either at the perimeter OR at the valley column
    # (whichever it hits first).
    #
    # To keep this simple and deterministic, we index each ring's
    # rays by angle, and for each ray we find the closest point on
    # the perimeter that is NOT inside the other cone's half-plane.
    # Concretely:
    #   - Ring A owns x < 0.
    #   - Ring B owns x > 0.
    # The valley is the vertical plane x = 0.
    #
    # For ring A, each ray is clipped at x = 0 if the ray crosses
    # x=0 at t > 0.  Otherwise it goes to the perimeter.

    def clip_ray(ox, oy, dx, dy, x_wall, perimeter_xy):
        # Wall clip: where does the ray hit x = x_wall?
        t_wall = None
        if abs(dx) > 1e-12:
            t_candidate = (x_wall - ox) / dx
            if t_candidate > 0.0:
                t_wall = t_candidate

        # Perimeter clip.
        t_perim = None
        n_perim_local = perimeter_xy.shape[0]
        for i in range(n_perim_local):
            ax, ay = perimeter_xy[i, 0], perimeter_xy[i, 1]
            bx, by = perimeter_xy[(i + 1) % n_perim_local, 0], \
                     perimeter_xy[(i + 1) % n_perim_local, 1]
            ex, ey = bx - ax, by - ay
            denom = dx * ey - dy * ex
            if abs(denom) < 1e-12:
                continue
            rx, ry = ox - ax, oy - ay
            u = (rx * dy - ry * dx) / denom
            t = (rx * ey - ry * ex) / denom
            if u < -1e-9 or u > 1.0 + 1e-9:
                continue
            if t < 1e-9:
                continue
            if t_perim is None or t < t_perim:
                t_perim = t

        t_use = None
        hit_wall = False
        if t_wall is not None and t_perim is not None:
            if t_wall < t_perim:
                t_use = t_wall
                hit_wall = True
            else:
                t_use = t_perim
        elif t_wall is not None:
            t_use = t_wall
            hit_wall = True
        elif t_perim is not None:
            t_use = t_perim

        if t_use is None:
            return None, False
        return (ox + t_use * dx, oy + t_use * dy), hit_wall

    perimeter_xy = np.array([[p[0], p[1]] for p in points[:n_perimeter]])

    def build_fan(ring_cx, ring_cy, ring_ids_local, x_wall):
        # For each ray, generate n_radial interior nodes plus the
        # boundary node (either perimeter or valley).
        rows = []
        outer_ids = []
        outer_kinds = []  # 'perim' or 'valley'
        for j in range(n_rays):
            t = 2.0 * math.pi * j / float(n_rays)
            dx = math.cos(t)
            dy = math.sin(t)
            hit, is_wall = clip_ray(ring_cx, ring_cy, dx, dy,
                                    x_wall, perimeter_xy)
            if hit is None:
                rows.append([])
                outer_ids.append(None)
                outer_kinds.append("miss")
                continue
            ix = ring_cx + ring_radius * dx
            iy = ring_cy + ring_radius * dy
            row = []
            for m in range(n_radial):
                f = (m + 1) / float(n_radial + 1)
                px = ix + f * (hit[0] - ix)
                py = iy + f * (hit[1] - iy)
                pz = ring_z + f * (z_start - ring_z)
                nid = len(points)
                points.append((px, py, pz))
                row.append(nid)
            rows.append(row)
            # Attach to boundary.
            if is_wall:
                # Nearest valley node to (hit[0], hit[1]).
                best = None
                best_d = None
                for vid in valley_column_ids:
                    vx, vy, _ = points[vid]
                    d = (vx - hit[0]) ** 2 + (vy - hit[1]) ** 2
                    if best_d is None or d < best_d:
                        best_d = d
                        best = vid
                outer_ids.append(best)
                outer_kinds.append("valley")
            else:
                # Nearest perimeter node.
                best = None
                best_d = None
                for pid in perimeter_ids:
                    px, py, _ = points[pid]
                    d = (px - hit[0]) ** 2 + (py - hit[1]) ** 2
                    if best_d is None or d < best_d:
                        best_d = d
                        best = pid
                outer_ids.append(best)
                outer_kinds.append("perim")
        return rows, outer_ids, outer_kinds

    rows_a, outer_a, kinds_a = build_fan(ring_a_x, 0.0, ring_a_ids, 0.0)
    rows_b, outer_b, kinds_b = build_fan(ring_b_x, 0.0, ring_b_ids, 0.0)

    # --- Edges -------------------------------------------------
    edge_set = set()

    def add_edge(a, b):
        if a is None or b is None:
            return
        key = (a, b) if a < b else (b, a)
        edge_set.add(key)

    # Ring polygons.
    for i in range(n_rays):
        j = (i + 1) % n_rays
        add_edge(ring_a_ids[i], ring_a_ids[j])
        add_edge(ring_b_ids[i], ring_b_ids[j])

    # Perimeter loop.
    for i in range(n_perimeter):
        j = (i + 1) % n_perimeter
        add_edge(perimeter_ids[i], perimeter_ids[j])

    # Valley column edges (consecutive nodes along the valley).
    for i in range(len(valley_column_ids) - 1):
        add_edge(valley_column_ids[i], valley_column_ids[i + 1])

    # Fan A strips.
    for j in range(n_rays):
        jn = (j + 1) % n_rays
        row_a0 = rows_a[j]
        row_a1 = rows_a[jn]
        if not row_a0 or not row_a1:
            continue
        # Ring -> first radial row.
        add_edge(ring_a_ids[j], row_a0[0])
        add_edge(ring_a_ids[jn], row_a1[0])
        # Between radial rows.
        for m in range(n_radial - 1):
            add_edge(row_a0[m], row_a0[m + 1])
            add_edge(row_a1[m], row_a1[m + 1])
            add_edge(row_a0[m], row_a1[m])
        # Last row -> boundary.
        add_edge(row_a0[-1], outer_a[j])
        add_edge(row_a1[-1], outer_a[jn])
        # Cross edges along the last row (circumferential).
        add_edge(row_a0[-1], row_a1[-1])
        # Circumferential edges between rows (skip ring polygon already added).
        for m in range(n_radial):
            add_edge(row_a0[m], row_a1[m])

    # Fan B strips.
    for j in range(n_rays):
        jn = (j + 1) % n_rays
        row_b0 = rows_b[j]
        row_b1 = rows_b[jn]
        if not row_b0 or not row_b1:
            continue
        add_edge(ring_b_ids[j], row_b0[0])
        add_edge(ring_b_ids[jn], row_b1[0])
        for m in range(n_radial - 1):
            add_edge(row_b0[m], row_b0[m + 1])
            add_edge(row_b1[m], row_b1[m + 1])
            add_edge(row_b0[m], row_b1[m])
        add_edge(row_b0[-1], outer_b[j])
        add_edge(row_b1[-1], outer_b[jn])
        add_edge(row_b0[-1], row_b1[-1])
        for m in range(n_radial):
            add_edge(row_b0[m], row_b1[m])

    edges = sorted(edge_set)

    # --- Fixed nodes ------------------------------------------
    fixed = set()
    # Ring A and Ring B: held fully.
    for nid in ring_a_ids + ring_b_ids:
        fixed.add(nid)
    # Valley ends: held fully.
    fixed.add(valley_end_top)
    fixed.add(valley_end_bot)

    # --- Valley interior nodes: dir-only along local tangent ---
    # The valley column is ordered top to bottom.  For each
    # interior node, compute the local tangent from the adjacent
    # nodes on the column.
    dir_only = []
    valley_interior_ids = list(valley_ids)  # copy
    for idx_in_col, nid in enumerate(valley_column_ids):
        if nid in (valley_end_top, valley_end_bot):
            continue
        prev_id = valley_column_ids[idx_in_col - 1]
        next_id = valley_column_ids[idx_in_col + 1]
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
        dir_only.append((nid, (tx, ty, tz)))

    # --- Force density classification -------------------------
    valley_edge_set = set()
    for i in range(len(valley_column_ids) - 1):
        a = valley_column_ids[i]
        b = valley_column_ids[i + 1]
        valley_edge_set.add((a, b) if a < b else (b, a))

    perimeter_edge_set = set()
    for i in range(n_perimeter):
        j = (i + 1) % n_perimeter
        perimeter_edge_set.add(
            (perimeter_ids[i], perimeter_ids[j])
            if perimeter_ids[i] < perimeter_ids[j]
            else (perimeter_ids[j], perimeter_ids[i])
        )

    return {
        "points": np.asarray(points, dtype=float),
        "edges": edges,
        "fixed": sorted(fixed),
        "dir_only": dir_only,
        "ring_a_ids": ring_a_ids,
        "ring_b_ids": ring_b_ids,
        "perimeter_ids": perimeter_ids,
        "valley_column_ids": valley_column_ids,
        "valley_interior_ids": valley_interior_ids,
        "valley_end_top": valley_end_top,
        "valley_end_bot": valley_end_bot,
        "valley_edge_set": valley_edge_set,
        "perimeter_edge_set": perimeter_edge_set,
        "rows_a": rows_a,
        "rows_b": rows_b,
        "outer_a": outer_a,
        "outer_b": outer_b,
    }


# =============================================================================
# PAGE
# =============================================================================

def render_tester_two_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>"
        "Two Cone — Isolated Valley Test</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Two rings, one eave, "
        "one valley. The valley interior nodes are free along the "
        "local valley tangent only.</p>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        cone_sep = st.number_input(
            "Cone separation (m)", 1.0, 30.0, 6.0, 0.5, key="tc_sep",
        )
    with c2:
        ring_radius = st.number_input(
            "Ring radius (m)", 0.1, 5.0, 1.0, 0.1, key="tc_ringr",
        )

    c1, c2 = st.columns(2)
    with c1:
        eave_half_width = st.number_input(
            "Eave half-width (m)", 1.0, 20.0, 6.0, 0.5, key="tc_eavehw",
        )
    with c2:
        ring_z = st.number_input(
            "Ring z (m)", 0.5, 30.0, 7.0, 0.5, key="tc_ringz",
        )

    c1, c2 = st.columns(2)
    with c1:
        n_rays = int(st.number_input(
            "Rays per cone", 8, 64, 24, 1, key="tc_rays",
        ))
    with c2:
        n_radial = int(st.number_input(
            "Radial nodes between ring and boundary", 2, 15, 5, 1,
            key="tc_nrad",
        ))

    c1, c2 = st.columns(2)
    with c1:
        z_start = st.number_input(
            "Interior nodes initial z (m)", -10.0, 30.0, 3.0, 0.5,
            key="tc_zstart",
        )
    with c2:
        n_perimeter = int(st.number_input(
            "Perimeter nodes", 12, 96, 48, 1, key="tc_nperim",
        ))

    c1, c2 = st.columns(2)
    with c1:
        warp_q_input = st.number_input(
            "Warp q (N/m)", 1.0, 100000.0, 2000.0, 100.0, key="tc_warpq",
        )
    with c2:
        edge_q_input = st.number_input(
            "Edge cable q (N/m)", 1.0, 100000.0, 2000.0, 100.0,
            key="tc_edgeq",
        )

    valley_q_input = st.number_input(
        "Valley cable q (N/m) — applied to ALL valleys",
        1.0, 100000.0, 8000.0, 100.0, key="tc_valleyq",
    )

    built = _two_cone_mesh(
        float(cone_sep), float(ring_radius), float(eave_half_width),
        float(ring_z), n_rays, n_radial, float(z_start), n_perimeter,
    )

    pts_init = built["points"]
    edges = built["edges"]
    fixed = built["fixed"]
    dir_only = built["dir_only"]
    valley_edge_set = built["valley_edge_set"]
    perimeter_edge_set = built["perimeter_edge_set"]

    warp_q = float(warp_q_input)
    edge_q = float(edge_q_input)
    valley_q = float(valley_q_input)

    q = np.empty(len(edges), dtype=float)
    for k, (i, j) in enumerate(edges):
        key = (i, j) if i < j else (j, i)
        if key in valley_edge_set:
            q[k] = valley_q
        elif key in perimeter_edge_set:
            q[k] = edge_q
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

    interior_ids = [i for i in range(pts_init.shape[0])
                    if i not in set(fixed)
                    and i not in [d[0] for d in dir_only]]
    z_int = coords[interior_ids, 2] if interior_ids else np.array([])
    moved = float(np.max(np.linalg.norm(coords - pts_init, axis=1))) \
        if pts_init.shape[0] else 0.0

    valley_col = built["valley_column_ids"]
    valley_z = coords[valley_col, 2]

    st.write(f"**Fixed nodes:** {len(fixed)}  "
             f"**Dir-only (valley interior):** {len(dir_only)}  "
             f"**Free interior:** {len(interior_ids)}")

    st.write(
        "**Ring A z after solve:** min=%.3f max=%.3f"
        % (float(np.min(coords[built['ring_a_ids'], 2])),
           float(np.max(coords[built['ring_a_ids'], 2])))
    )
    st.write(
        "**Ring B z after solve:** min=%.3f max=%.3f"
        % (float(np.min(coords[built['ring_b_ids'], 2])),
           float(np.max(coords[built['ring_b_ids'], 2])))
    )
    st.write(
        "**Valley column z after solve:** min=%.3f max=%.3f  "
        "(ends held at 0; interior should sag or lift under valley q)"
        % (float(np.min(valley_z)), float(np.max(valley_z)))
    )
    st.write(
        "**Free interior z after solve:** min=%.3f max=%.3f"
        % (float(np.min(z_int)), float(np.max(z_int)))
    )
    st.write("**Max free-node movement (m):** %.4f" % moved)
    st.write(f"**Solve OK:** {solve_ok}")
    if not solve_ok:
        st.write(f"**Solve error:** {solve_err}")
    else:
        st.write("**Residual norm:** %.6e" % residual_norm)

    # --- 3D view ----------------------------------------------
    fig = go.Figure()

    # Membrane as two fan meshes.
    def add_fan_trace(ring_ids_local, rows, outer_ids, n_rays_local):
        tris = []
        for j in range(n_rays_local):
            jn = (j + 1) % n_rays_local
            row0 = rows[j]
            row1 = rows[jn]
            if not row0 or not row1:
                continue
            # Ring fan: triangle (ring[j], ring[jn], row0[0]) and (ring[jn], row1[0], row0[0])
            tris.append((ring_ids_local[j], ring_ids_local[jn], row0[0]))
            tris.append((ring_ids_local[jn], row1[0], row0[0]))
            for m in range(n_radial - 1):
                a0 = row0[m]
                a1 = row1[m]
                b0 = row0[m + 1]
                b1 = row1[m + 1]
                tris.append((a0, a1, b1))
                tris.append((a0, b1, b0))
            a = row0[-1]
            b = row1[-1]
            c = outer_ids[j]
            d = outer_ids[jn]
            if c is not None and d is not None and c != d:
                tris.append((a, b, d))
                tris.append((a, d, c))
        return np.asarray(tris, dtype=int) if tris else None

    tris_a = add_fan_trace(built["ring_a_ids"], built["rows_a"],
                           built["outer_a"], n_rays)
    if tris_a is not None:
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tris_a[:, 0], j=tris_a[:, 1], k=tris_a[:, 2],
            color=COL_MEMBRANE, opacity=0.6, flatshading=True,
            name="cone A", showlegend=False, hoverinfo="skip",
        ))
    tris_b = add_fan_trace(built["ring_b_ids"], built["rows_b"],
                           built["outer_b"], n_rays)
    if tris_b is not None:
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tris_b[:, 0], j=tris_b[:, 1], k=tris_b[:, 2],
            color=COL_MEMBRANE, opacity=0.6, flatshading=True,
            name="cone B", showlegend=False, hoverinfo="skip",
        ))

    # Ring A, ring B.
    for label, ring_ids_local, col in [
        ("ring A", built["ring_a_ids"], COL_RING),
        ("ring B", built["ring_b_ids"], COL_RING),
    ]:
        pts = coords[ring_ids_local]
        closed = np.vstack([pts, pts[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=col, width=6),
            name=label, showlegend=False, hoverinfo="skip",
        ))

    # Perimeter.
    perim_pts = coords[built["perimeter_ids"]]
    perim_closed = np.vstack([perim_pts, perim_pts[:1]])
    fig.add_trace(go.Scatter3d(
        x=perim_closed[:, 0], y=perim_closed[:, 1], z=perim_closed[:, 2],
        mode="lines", line=dict(color=COL_EAVE, width=4),
        name="perimeter", showlegend=False, hoverinfo="skip",
    ))

    # Valley cable.
    vpts = coords[built["valley_column_ids"]]
    fig.add_trace(go.Scatter3d(
        x=vpts[:, 0], y=vpts[:, 1], z=vpts[:, 2],
        mode="lines", line=dict(color=COL_VALLEY, width=7),
        name="valley cable", showlegend=False, hoverinfo="skip",
    ))

    # Valley ends as markers.
    ends = coords[[built["valley_end_top"], built["valley_end_bot"]]]
    fig.add_trace(go.Scatter3d(
        x=ends[:, 0], y=ends[:, 1], z=ends[:, 2],
        mode="markers",
        marker=dict(color=COL_VALLEY_END, size=10, symbol="diamond"),
        name="valley ends", showlegend=False, hoverinfo="skip",
    ))

    apply_common_layout(fig, float(ring_z))
    st.plotly_chart(fig, use_container_width=True, key="tc_3d")

    # --- Plan view --------------------------------------------
    figp = go.Figure()
    figp.add_trace(go.Scatter(
        x=coords[built["perimeter_ids"], 0],
        y=coords[built["perimeter_ids"], 1],
        mode="lines", line=dict(color=COL_EAVE, width=2),
        name="perimeter", showlegend=False, hoverinfo="skip",
    ))
    for label, ring_ids_local in [
        ("ring A", built["ring_a_ids"]),
        ("ring B", built["ring_b_ids"]),
    ]:
        figp.add_trace(go.Scatter(
            x=coords[ring_ids_local, 0], y=coords[ring_ids_local, 1],
            mode="lines", line=dict(color=COL_RING, width=2),
            name=label, showlegend=False, hoverinfo="skip",
        ))
    figp.add_trace(go.Scatter(
        x=coords[built["valley_column_ids"], 0],
        y=coords[built["valley_column_ids"], 1],
        mode="lines+markers",
        line=dict(color=COL_VALLEY, width=3),
        marker=dict(color=COL_VALLEY, size=5),
        name="valley", showlegend=False, hoverinfo="skip",
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
        title=dict(text="Plan view (after solve)",
                   font=dict(color="#f39c12", size=14)),
    )
    st.plotly_chart(figp, use_container_width=True, key="tc_plan")
