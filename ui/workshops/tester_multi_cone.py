"""Multi-Cone Roof — Stage 3 Lab test page.

Version v13.

New in this version:
  - Number of cones widget (1 to 20, default 2).
  - Plan-view figure above the widget: roof seen from above,
    with one coloured dot per cone, updated live.
  - Per-cone collapsible expanders ("Cone 1", "Cone 2", ...),
    collapsed by default so the page stays usable on a phone.
  - Inside each cone expander:
      * Position along roof (front -> back): slider 0..1
      * Left / Right / Both: radio
      * Along the rib (0 = left support, 0.5 = peak,
        1 = right support): slider 0..1
      * Clearance below beam (m): number input 0.1..5.0
  - Reset all to defaults button.
  - Solve button.  Sliders update the plan view live; the 3D
    solve runs only when Solve is pressed.
  - Each ring has a centre node, held.
  - Radial spokes: one edge from centre to each ring polygon
    node.  Rigid steel members.  Held.  Recorded.
  - One drop member per ring: from centre up to a new held node
    on the primary (or rib) directly above.

Carried over:
  - Ring polygon node count from circumference, floor 12, cap 32.
  - z interpolation weight w = d_ring / (d_ring + d_perim).
  - Ring attachment test 3D distance to the ring circle, 1 x
    target_len, fabric nodes snapped to ring z and held.
  - Full node digitisation.

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
COL_PLAN_OUTLINE = "#f1c40f"
COL_PLAN_PRIMARY = "#FF6B6B"
COL_PLAN_RIB = "#e07b39"

CONE_COLORS = [
    "#f39c12", "#e74c3c", "#3498db", "#2ecc71",
    "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
    "#c0392b", "#16a085", "#8e44ad", "#d35400",
    "#27ae60", "#2980b9", "#f1c40f", "#7f8c8d",
    "#c0392b", "#16a085", "#8e44ad", "#d35400",
]


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


def _rib_point_at_fraction(rib_x, rib_half_width, rib_peak_z, frac):
    """Point on the rib at parametrisation frac in [0, 1].

    frac = 0 -> left ground support
    frac = 0.5 -> peak (at y = 0, z = peak)
    frac = 1 -> right ground support

    Uses a linear y and a parabolic z, so the rib reaches
    z = rib_peak_z at frac = 0.5.
    """
    y = -rib_half_width + 2.0 * rib_half_width * frac
    u = 2.0 * frac - 1.0              # in [-1, +1]
    z = rib_peak_z * (1.0 - u ** 2)
    return float(rib_x), float(y), float(z)


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


# --- Cone placement from user input ------------------------------------------

def _cone_position_from_inputs(frac_along_primary, side, frac_along_rib,
                                rib_x, rib_half_width, rib_peak_z,
                                xp, zp, span):
    """Return (cx, cy, beam_z) for one cone, using user inputs.

    Strategy:
      1.  The primary beam's plan position at frac_along_primary is
          found (x_primary).
      2.  The rib whose station x is closest to x_primary is chosen.
      3.  The cone centre sits on that rib at frac_along_rib.
          side = "left"  -> frac_along_rib directly
          side = "right" -> 1 - frac_along_rib
          side = "both"  -> ignored; caller places two cones.
      4.  beam_z is the rib's z at that point.

    If there are no ribs, the cone sits on the primary itself.
    """
    s_total = 1.0
    x_primary = float(np.interp(frac_along_primary, np.linspace(0, 1, 200), xp))

    if len(rib_x) == 0:
        y = 0.0
        z = float(np.interp(x_primary, xp, zp))
        return x_primary, y, z

    # Nearest rib by x.
    k = int(np.argmin(np.abs(np.asarray(rib_x) - x_primary)))
    rx = float(rib_x[k])
    rhw = float(rib_half_width[k])
    rpz = float(rib_peak_z[k])

    f = frac_along_rib
    if side == "right":
        f = 1.0 - f
    # For side == "both", the caller passes f for the first cone
    # and (1 - f) for the second.

    _, y, z = _rib_point_at_fraction(rx, rhw, rpz, f)
    return rx, y, z


# --- Mesh build --------------------------------------------------------------

def _build_cone_mesh(perimeter_loop, anchor_idx, ring_specs,
                      eave_height, target_len):
    """
    ring_specs: list of dicts with keys cx, cy, cz, r, beam_z.
    """
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
    ring_polygon_points = []

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
        ring_polygon_points.append(poly)

        # Centre node.
        centre_indices.append(len(all_pts_list))
        all_pts_list.append((cx, cy, cz))

        # Beam top node: directly above the ring centre at the
        # beam's (or rib's) z at that plan position.
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

    structural_connections = []
    for k, spec in enumerate(ring_specs):
        cx = float(spec["cx"]); cy = float(spec["cy"])
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
        structural_connections.append({
            "ring_index": k,
            "centre_node": int(centre_i),
            "beam_top_node": int(beam_i),
            "polygon_nodes": [int(i) for i in idx_list],
            "n_spokes": int(n_poly),
            "member_types": ["ring_beam", "spoke", "drop_member"],
        })

    # Ring attachment: for each polygon node, connect to the two
    # nearest fabric nodes outside the ring circle.  Snap attached
    # fabric nodes to the ring z.
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

    # Snap attached fabric nodes to the closest ring z.
    for i in attached_node_indices:
        fx, fy = all_pts[i, 0], all_pts[i, 1]
        best_d = float("inf")
        best_z = all_pts[i, 2]
        for spec in ring_specs:
            cx = float(spec["cx"]); cy = float(spec["cy"])
            r = float(spec["r"]); cz = float(spec["cz"])
            d = math.sqrt((fx - cx) ** 2 + (fy - cy) ** 2) - r
            if d < best_d:
                best_d = d; best_z = cz
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
        "ring_polygon_points": ring_polygon_points,
        "attached_node_indices": sorted(attached_node_indices),
        "ring_attach_counts": ring_attach_counts,
        "ring_attach_edges_added": ring_attach_edges_added,
        "structural_connections": structural_connections,
        "n_perimeter": n_perimeter,
        "n_interior": len(interior_xy),
        "fabric_start": fabric_start,
        "fabric_end": fabric_end,
    }


# --- Plan-view figure --------------------------------------------------------

def _plan_view_figure(span, mid_width, xp, zp, rib_x, rib_half_width,
                       cone_xy_list):
    fig = go.Figure()
    a = span / 2.0
    b = mid_width / 2.0
    t = np.linspace(0.0, 2.0 * math.pi, 200)
    fig.add_trace(go.Scatter(
        x=a * np.cos(t), y=b * np.sin(t),
        mode="lines",
        line=dict(color=COL_PLAN_OUTLINE, width=2),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=xp, y=np.zeros_like(xp),
        mode="lines",
        line=dict(color=COL_PLAN_PRIMARY, width=4),
        showlegend=False, hoverinfo="skip",
    ))
    for i, xr in enumerate(rib_x):
        hw = float(rib_half_width[i])
        fig.add_trace(go.Scatter(
            x=[float(xr), float(xr)], y=[-hw, +hw],
            mode="lines",
            line=dict(color=COL_PLAN_RIB, width=2),
            showlegend=False, hoverinfo="skip",
        ))
    for j, (cx, cy) in enumerate(cone_xy_list):
        col = CONE_COLORS[j % len(CONE_COLORS)]
        fig.add_trace(go.Scatter(
            x=[cx], y=[cy],
            mode="markers+text",
            marker=dict(color=col, size=16, symbol="circle",
                        line=dict(color="#ffffff", width=2)),
            text=[str(j + 1)], textposition="middle center",
            textfont=dict(color="#000000", size=10),
            showlegend=False, hoverinfo="skip",
        ))
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="#0e1621",
        plot_bgcolor="#0e1621",
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
    )
    return fig


# --- Node status formatting --------------------------------------------------

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


# --- Session state helpers ---------------------------------------------------

def _default_cone_dict(n):
    """Sensible defaults: cone i at evenly spaced positions."""
    out = []
    for i in range(n):
        frac = (i + 1) / (n + 1)
        out.append({
            "position": float(frac),
            "side": "both",
            "along_rib": 0.50,
            "clearance": 1.00,
        })
    return out


def _ensure_cone_state(n, prev_list):
    """Grow or shrink the cone list to length n, keeping existing values."""
    if prev_list is None:
        return _default_cone_dict(n)
    if len(prev_list) == n:
        return prev_list
    if len(prev_list) < n:
        # Keep the existing ones; for the new ones use evenly
        # spaced positions on the FULL set of n cones.
        full = _default_cone_dict(n)
        out = list(prev_list)
        for i in range(len(prev_list), n):
            out.append(full[i])
        return out
    else:
        return prev_list[:n]


# --- Page --------------------------------------------------------------------

def render_tester_multi_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>Stage 3 — multi-cone, "
        "collapsible per-cone controls.</p>",
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
        warp_q_input = st.number_input(
            "Warp pretension (kN/m)", 0.1, 100.0, 1.0, 0.1,
            key="mc_warp",
        )
    with c2:
        weft_q_input = st.number_input(
            "Weft pretension (kN/m)", 0.1, 100.0, 1.0, 0.1,
            key="mc_weft",
        )

    edge_q_input = st.number_input(
        "Edge cable pretension (kN/m, 0 = auto)", 0.0, 500.0, 20.0, 1.0,
        key="mc_edgeq",
    )

    # --- Primary curve, ribs -----------------------------------------
    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array(
        [_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float
    )

    # --- Cone count widget -------------------------------------------
    number_of_cones = int(st.number_input(
        "Number of cones", 1, 20, 2, 1, key="mc_ncones"
    ))

    # Maintain session state list of cone dicts.
    prev = st.session_state.get("mc_cones", None)
    cones = _ensure_cone_state(number_of_cones, prev)
    st.session_state["mc_cones"] = cones

    # --- Plan view (live) --------------------------------------------
    # Compute the (x, y) positions of all cones for the plan view.
    cone_xy_list = []
    for c in cones:
        side = c["side"]
        f = c["along_rib"]
        if side == "both":
            for f_local in (f, 1.0 - f):
                cx, cy, _ = _cone_position_from_inputs(
                    c["position"], "left", f_local,
                    rib_x, rib_half_width, rib_peak_z, xp, zp, span,
                )
                cone_xy_list.append((cx, cy))
        else:
            cx, cy, _ = _cone_position_from_inputs(
                c["position"], side, f,
                rib_x, rib_half_width, rib_peak_z, xp, zp, span,
            )
            cone_xy_list.append((cx, cy))

    st.markdown(
        "<p style='color:#a8b8c8;margin-top:0.8rem;'>"
        "Plan view — where the cones are:</p>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        _plan_view_figure(span, mid_width, xp, zp, rib_x, rib_half_width,
                           cone_xy_list),
        use_container_width=True,
        key="mc_plan",
    )

    # --- Per-cone collapsible sections -------------------------------
    st.markdown(
        "<p style='color:#a8b8c8;margin-top:0.8rem;'>"
        "Cone positions (open one to edit):</p>",
        unsafe_allow_html=True,
    )

    for i in range(number_of_cones):
        c = cones[i]
        col = CONE_COLORS[i % len(CONE_COLORS)]
        label = f"Cone {i+1}"
        with st.expander(label, expanded=False):
            st.markdown(
                f"<div style='display:inline-block;width:12px;height:12px;"
                f"background:{col};border-radius:6px;margin-right:8px;"
                f"vertical-align:middle;'></div>"
                f"<span style='color:#ffffff;'>Cone {i+1}</span>",
                unsafe_allow_html=True,
            )
            pos = st.slider(
                "Position along roof (front → back)",
                0.0, 1.0, float(c["position"]), 0.01,
                key=f"mc_pos_{i}",
            )
            side = st.radio(
                "Side",
                ["left", "right", "both"],
                index=["left", "right", "both"].index(c["side"]),
                horizontal=True,
                key=f"mc_side_{i}",
            )
            along_rib = st.slider(
                "Along the rib (0 = left support, 0.5 = peak, 1 = right support)",
                0.0, 1.0, float(c["along_rib"]), 0.01,
                key=f"mc_along_{i}",
            )
            clearance = st.number_input(
                "Clearance below beam (m)",
                0.1, 5.0, float(c["clearance"]), 0.1,
                key=f"mc_clr_{i}",
            )
            cones[i] = {
                "position": float(pos),
                "side": str(side),
                "along_rib": float(along_rib),
                "clearance": float(clearance),
            }
    st.session_state["mc_cones"] = cones

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Reset all to defaults", use_container_width=True,
                     key="mc_reset"):
            st.session_state["mc_cones"] = _default_cone_dict(number_of_cones)
            st.rerun()
    with col_b:
        solve_now = st.button("Solve", use_container_width=True, key="mc_solve")

    if not solve_now:
        st.info("Press Solve to run the form-finding.  Sliders update the plan "
                "view live.")
        return

    # --- Build ring specs from cone dicts ----------------------------
    ring_specs = []
    for c in cones:
        side = c["side"]
        f = c["along_rib"]
        clr = float(c["clearance"])
        if side == "both":
            pairs = [(f, "left"), (1.0 - f, "left")]  # two cones, mirrored
        else:
            pairs = [(f, side)]
        for (f_local, side_local) in pairs:
            cx, cy, beam_z = _cone_position_from_inputs(
                c["position"], side_local, f_local,
                rib_x, rib_half_width, rib_peak_z, xp, zp, span,
            )
            ring_specs.append({
                "cx": float(cx),
                "cy": float(cy),
                "cz": float(beam_z - clr),
                "r": float(ring_diameter) / 2.0,
                "beam_z": float(beam_z),
            })

    # --- Eave boundary polygon ---------------------------------------
    tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
    anchors = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, tip_x
    )
    perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
    bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
    L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
    target_len = max(L_avg, 1e-6)

    # --- Build mesh --------------------------------------------------
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

    # --- Main 3D figure ----------------------------------------------
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

    for k in range(len(ring_specs)):
        idx_list = built["ring_indices"][k]
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

    with st.expander("Diagnostics", expanded=False):
        st.write(f"Number of cones requested: {number_of_cones}")
        st.write(f"Total rings placed: {len(ring_specs)}")
        st.write(f"Outer anchors: {anchors.shape[0]}")
        st.write(f"Perimeter tip x (m): +/-{tip_x:.4f}")
        st.write(f"Subdivisions per edge: {subdivisions}")
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
        st.write(f"Warp q: {warp_q:.2f}  |  Weft q: {weft_q:.2f}  "
                 f"|  Edge q: {edge_q_scalar:.2f}")
        st.write(f"Ring diameter: {ring_diameter:.3f} m")
        if len(ring_specs) > 0:
            st.write("Cone centres (x, y, z):")
            for i, spec in enumerate(ring_specs):
                st.write(f"  Ring {i+1}: "
                         f"({spec['cx']:+.3f}, {spec['cy']:+.3f}, "
                         f"{spec['cz']:.3f})  beam_z={spec['beam_z']:.3f}")
        st.write("Ring node counts (from circumference): " +
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
