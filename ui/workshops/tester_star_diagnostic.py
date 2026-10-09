# =============================================================================
# SDSe - Star Diagnostic (Lab)
# =============================================================================
# Background test to see how a boundary node shared between the cable
# and the membrane moves when the edge cable pretension is changed.
#
# The question:
#   Is the shared boundary node free along the cable direction,
#   free in Z only, or free in all three directions?
#
# The method:
#   - Diamond in plan, 5 m long diagonal, 3 m short diagonal.
#   - Four corners pinned at alternating heights (+1, -1, +1, -1).
#   - Four sides, all cable, 12 subdivisions per side.
#   - Two FDM solves. Everything fixed except the edge cable
#     pretension.
#   - Read the boundary subdivision nodes from both runs.
#   - Report the displacement vector, the angle to the local cable
#     tangent, and the angle to the Z axis.
#
# The path:
#   The q computation, the mesh call, and the FDM call are taken
#   from _solve_fdm_path in viewers/figures/standard_saddle_mbs.py.
#   The boundary-edge q is passed as a DICT, not a scalar. That is
#   the path the working saddle viewer uses for form finding.
#   Pass a scalar and assign_anisotropic_q silently drops the value
#   in its Case 3 branch. Pass a dict and the value reaches the
#   boundary edges.
#
# This file is diagnostic only. Nothing here is called by the
# production code.
#
# History:
#   2026-10-09 - First version.
#   2026-10-09 - Rewritten to borrow the working q path.
#   2026-10-09 - Rewritten again to pass a DICT of boundary q
#                values, matching the working saddle viewer. The
#                scalar path in assign_anisotropic_q silently
#                applies warp_q to boundary edges.
# =============================================================================

import numpy as np
import streamlit as st

from engine.mesh_triangulated import build_mesh_triangulated
from engine.form_finding import (
    assign_anisotropic_q,
    auto_warp_dir,
    solve_fdm,
)


# =============================================================================
# GEOMETRY
# =============================================================================

def _build_diamond_boundary():
    """
    Diamond in plan: long diagonal 5 m along X, short diagonal 3 m
    along Y. Four corners at alternating heights (+1, -1, +1, -1).
    Subdivision nodes along each straight chord. All four sides are
    cable segments.
    """
    corners = np.array([
        (-2.5,  0.0, +1.0),
        ( 0.0, +1.5, -1.0),
        ( 2.5,  0.0, +1.0),
        ( 0.0, -1.5, -1.0),
    ], dtype=float)

    subdivisions_per_side = 12

    loop = []
    anchor_indices = []

    for k in range(4):
        a = corners[k]
        b = corners[(k + 1) % 4]
        anchor_indices.append(len(loop))
        for j in range(subdivisions_per_side):
            frac = float(j) / float(subdivisions_per_side)
            p = a + (b - a) * frac
            loop.append((float(p[0]), float(p[1]), float(p[2])))

    boundary_loop = np.asarray(loop, dtype=float)

    n_loop = boundary_loop.shape[0]
    segments = []
    n_a = len(anchor_indices)
    for k in range(n_a):
        aa = anchor_indices[k]
        bb = anchor_indices[(k + 1) % n_a]
        interior = []
        i = (aa + 1) % n_loop
        safety = 0
        while i != bb and safety < n_loop:
            interior.append(i)
            i = (i + 1) % n_loop
            safety += 1
        segments.append({
            "anchor_a": int(aa),
            "anchor_b": int(bb),
            "interior": interior,
        })

    segment_types = ["cable"] * n_a

    return boundary_loop, anchor_indices, segment_types, segments


# =============================================================================
# ONE SOLVE
# =============================================================================

def _solve_once(boundary_loop, anchors, segment_types,
                 edge_pretension_kN,
                 warp_pre_kN_per_m, weft_pre_kN_per_m,
                 mesh_spacing_m):
    """
    FDM solve on the diamond boundary. The q computation, the mesh
    call, and the FDM call are taken from _solve_fdm_path in the
    working saddle viewer. The boundary-edge q is passed as a DICT.
    """
    n = boundary_loop.shape[0]
    total_len = 0.0
    for i in range(n):
        p0 = boundary_loop[i]
        p1 = boundary_loop[(i + 1) % n]
        total_len += float(np.linalg.norm(p1 - p0))
    L_avg = total_len / float(n) if n > 0 else 1.0
    if L_avg < 1e-9:
        L_avg = 1.0

    edge_pre_used = float(edge_pretension_kN)
    edge_pre_source = "user"
    if edge_pre_used <= 0.0:
        edge_pre_used = 0.05
        edge_pre_source = "fallback"

    baseline_kN_per_m = 2.0
    ratio_limit = 4.0
    warp_input = max(0.1, float(warp_pre_kN_per_m))
    weft_input = max(0.1, float(weft_pre_kN_per_m))
    mean_input = 0.5 * (warp_input + weft_input)
    if mean_input < 1e-9:
        mean_input = 1.0
    warp_rel = warp_input / mean_input
    weft_rel = weft_input / mean_input
    if warp_rel / weft_rel > ratio_limit:
        warp_rel = ratio_limit * weft_rel
    if weft_rel / warp_rel > ratio_limit:
        weft_rel = ratio_limit * warp_rel
    warp_q = baseline_kN_per_m * warp_rel * 1000.0 / L_avg
    weft_q = baseline_kN_per_m * weft_rel * 1000.0 / L_avg
    edge_q_scalar = edge_pre_used * 1000.0 / L_avg

    target_len = float(mesh_spacing_m) if mesh_spacing_m and mesh_spacing_m > 0 else None

    mesh_result = build_mesh_triangulated(
        boundary_loop=boundary_loop,
        anchor_indices=anchors,
        segment_types=segment_types,
        target_edge_length=target_len,
        plan_plane=None,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q_scalar,
    )

    points_initial = mesh_result["points_initial"]
    edges = mesh_result["edges"]
    fixed_indices = mesh_result["fixed_indices"]
    n_boundary_pts = boundary_loop.shape[0]

    pts_2d = points_initial[:, :2]
    warp_dir = auto_warp_dir(pts_2d)

    # ---- Boundary-edge q, as a DICT keyed by node-pair ----
    # One entry per boundary edge in the boundary loop. The mesh
    # preserves boundary indices 0..n_boundary-1 in order, so the
    # boundary edges are the consecutive pairs (i, i+1) and the
    # closing pair (n_boundary-1, 0).
    q_dict = {}
    for i in range(n_boundary_pts):
        j = (i + 1) % n_boundary_pts
        key = (i, j) if i < j else (j, i)
        q_dict[key] = float(edge_q_scalar)

    q_aniso = assign_anisotropic_q(
        edges,
        pts_2d,
        warp_dir,
        warp_q,
        weft_q,
        n_boundary=n_boundary_pts,
        boundary_edge_q=q_dict,
    )

    # ---- Counters: how many edges actually got the edge_q value ----
    n_boundary_edges_in_mesh = 0
    n_boundary_edges_applied = 0
    for k, (a, b) in enumerate(edges):
        if a < n_boundary_pts and b < n_boundary_pts:
            d = abs(a - b)
            if d == 1 or d == n_boundary_pts - 1:
                n_boundary_edges_in_mesh += 1
                if abs(float(q_aniso[k]) - float(edge_q_scalar)) < 1e-6:
                    n_boundary_edges_applied += 1

    fdm_result = solve_fdm(
        points_initial.copy(),
        edges,
        fixed_indices,
        q_aniso,
    )

    return {
        "coords": fdm_result["coordinates"],
        "points_initial": points_initial,
        "edges": edges,
        "fixed_indices": fixed_indices,
        "n_boundary": n_boundary_pts,
        "L_avg": L_avg,
        "warp_q": warp_q,
        "weft_q": weft_q,
        "edge_q_scalar": edge_q_scalar,
        "edge_pre_used_kN": edge_pre_used,
        "edge_pre_source": edge_pre_source,
        "n_boundary_edges_in_mesh": n_boundary_edges_in_mesh,
        "n_boundary_edges_applied": n_boundary_edges_applied,
    }


# =============================================================================
# DISPLACEMENT ANALYSIS
# =============================================================================

def _cable_tangent_at(coords, boundary_index, n_boundary):
    prev_idx = (boundary_index - 1) % n_boundary
    next_idx = (boundary_index + 1) % n_boundary
    prev_pt = coords[prev_idx]
    next_pt = coords[next_idx]
    t = next_pt - prev_pt
    mag = float(np.linalg.norm(t))
    if mag < 1e-12:
        return np.array([1.0, 0.0, 0.0])
    return t / mag


def _analyse_run_pair(run_A, run_B):
    coords_A = run_A["coords"]
    coords_B = run_B["coords"]
    n_boundary = run_A["n_boundary"]
    fixed = set(int(i) for i in run_A["fixed_indices"])

    rows = []
    for i in range(n_boundary):
        if i in fixed:
            continue
        pA = coords_A[i]
        pB = coords_B[i]
        d = pB - pA
        mag = float(np.linalg.norm(d))
        tangent = _cable_tangent_at(coords_A, i, n_boundary)
        if mag < 1e-12:
            angle_cable = 0.0
            angle_z = 0.0
        else:
            u = d / mag
            cos_cable = float(np.dot(u, tangent))
            cos_cable = max(-1.0, min(1.0, cos_cable))
            angle_cable = float(np.degrees(np.arccos(abs(cos_cable))))
            cos_z = float(abs(u[2]))
            cos_z = max(0.0, min(1.0, cos_z))
            angle_z = float(np.degrees(np.arccos(cos_z)))
        rows.append({
            "index": int(i),
            "x_init": float(run_A["points_initial"][i, 0]),
            "y_init": float(run_A["points_initial"][i, 1]),
            "z_init": float(run_A["points_initial"][i, 2]),
            "xA": float(pA[0]), "yA": float(pA[1]), "zA": float(pA[2]),
            "xB": float(pB[0]), "yB": float(pB[1]), "zB": float(pB[2]),
            "dx": float(d[0]), "dy": float(d[1]), "dz": float(d[2]),
            "mag": mag,
            "angle_to_cable_deg": angle_cable,
            "angle_to_Z_deg": angle_z,
        })
    return rows


# =============================================================================
# REPORT
# =============================================================================

def _format_table(rows):
    header = (
        "%5s  %8s  %8s  %8s  %8s  %8s  %8s  %8s  %8s  %8s  %9s  %9s  %9s"
        % ("idx", "x_init", "y_init", "z_init",
           "xA", "yA", "zA", "xB", "yB", "zB",
           "|d|_mm", "ang_cab", "ang_Z")
    )
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            "%5d  %8.3f  %8.3f  %8.3f  %8.3f  %8.3f  %8.3f  %8.3f  %8.3f  %8.3f  %9.3f  %9.2f  %9.2f"
            % (r["index"],
               r["x_init"], r["y_init"], r["z_init"],
               r["xA"], r["yA"], r["zA"],
               r["xB"], r["yB"], r["zB"],
               r["mag"] * 1000.0,
               r["angle_to_cable_deg"],
               r["angle_to_Z_deg"])
        )
    return "\n".join(lines)


def _verdict(rows):
    if not rows:
        return "No boundary subdivision nodes found."
    mags = [r["mag"] for r in rows]
    total_motion_mm = sum(mags) * 1000.0
    max_motion_mm = max(mags) * 1000.0 if mags else 0.0
    if total_motion_mm < 0.1:
        return (
            "No measurable motion. Max motion %.4f mm. "
            "The edge pretension is not reaching the solve, or the "
            "node is effectively fixed in all three axes."
            % max_motion_mm
        )
    weighted_cable = 0.0
    weighted_Z = 0.0
    weight_sum = 0.0
    for r in rows:
        w = r["mag"]
        weighted_cable += r["angle_to_cable_deg"] * w
        weighted_Z += r["angle_to_Z_deg"] * w
        weight_sum += w
    if weight_sum < 1e-12:
        return "No weighted motion. Cannot compute a verdict."
    mean_cable = weighted_cable / weight_sum
    mean_Z = weighted_Z / weight_sum
    verdict = (
        "Max motion: %.3f mm.  Mean angle to cable tangent: %.1f deg.  "
        "Mean angle to Z: %.1f deg."
        % (max_motion_mm, mean_cable, mean_Z)
    )
    if mean_cable < 30.0:
        verdict += (
            "  VERDICT: motion is predominantly along the cable. "
            "The node is free along the cable only."
        )
    elif mean_Z < 30.0:
        verdict += (
            "  VERDICT: motion is predominantly in Z. "
            "The node is free in Z only."
        )
    else:
        verdict += (
            "  VERDICT: motion is neither along the cable nor in Z. "
            "The node is moving inward in the plan plane. "
            "The node is effectively free in all three directions."
        )
    return verdict


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_tester_star_diagnostic():
    st.markdown(
        "## Star Diagnostic  \n"
        "How does the shared boundary node move when only the edge "
        "cable pretension is changed?"
    )

    st.markdown(
        "**Shape.** Diamond in plan, 5 m long diagonal, 3 m short "
        "diagonal. Four corners pinned, alternating heights "
        "(+1, -1, +1, -1). Four sides, all cable. "
        "Mesh spacing 0.25 m, 12 subdivisions per side."
    )

    st.markdown(
        "**Path.** Boundary-edge q is passed as a DICT, matching the "
        "working saddle viewer's form-finding path."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        edge_A = st.number_input(
            "Edge cable A (kN)",
            value=0.5, min_value=0.01, max_value=100.0, step=0.1,
            key="diag_edge_A",
        )
    with c2:
        edge_B = st.number_input(
            "Edge cable B (kN)",
            value=5.0, min_value=0.01, max_value=100.0, step=0.1,
            key="diag_edge_B",
        )
    with c3:
        mesh_spacing = st.number_input(
            "Mesh spacing (m)",
            value=0.25, min_value=0.05, max_value=2.0, step=0.05,
            key="diag_mesh_spacing",
        )

    c4, c5 = st.columns(2)
    with c4:
        warp_pre = st.number_input(
            "Warp pretension (kN/m)",
            value=2.0, min_value=0.1, max_value=20.0, step=0.1,
            key="diag_warp",
        )
    with c5:
        weft_pre = st.number_input(
            "Weft pretension (kN/m)",
            value=2.0, min_value=0.1, max_value=20.0, step=0.1,
            key="diag_weft",
        )

    run = st.button(
        "Run Diagnostic",
        key="diag_run",
        use_container_width=True,
        type="primary",
    )

    if not run:
        return

    boundary_loop, anchors, segment_types, segments = _build_diamond_boundary()

    with st.spinner("Running solve A..."):
        run_A = _solve_once(
            boundary_loop, anchors, segment_types,
            edge_pretension_kN=float(edge_A),
            warp_pre_kN_per_m=float(warp_pre),
            weft_pre_kN_per_m=float(weft_pre),
            mesh_spacing_m=float(mesh_spacing),
        )
    with st.spinner("Running solve B..."):
        run_B = _solve_once(
            boundary_loop, anchors, segment_types,
            edge_pretension_kN=float(edge_B),
            warp_pre_kN_per_m=float(warp_pre),
            weft_pre_kN_per_m=float(weft_pre),
            mesh_spacing_m=float(mesh_spacing),
        )

    st.markdown("---")
    st.markdown("**Solve A summary**")
    st.markdown(
        "- Edge pretension: %.3f kN (%s)" % (
            run_A["edge_pre_used_kN"], run_A["edge_pre_source"]
        )
        + "  |  edge_q: %.4f" % run_A["edge_q_scalar"]
        + "  |  warp_q: %.4f" % run_A["warp_q"]
        + "  |  weft_q: %.4f" % run_A["weft_q"]
    )
    st.markdown(
        "- Boundary nodes: " + str(run_A["n_boundary"])
        + "  |  L_avg: %.4f m" % run_A["L_avg"]
        + "  |  fixed: " + str(len(run_A["fixed_indices"]))
    )
    st.markdown(
        "- Boundary edges in mesh: "
        + str(run_A["n_boundary_edges_in_mesh"])
        + "  |  applied edge_q: "
        + str(run_A["n_boundary_edges_applied"])
    )

    st.markdown("**Solve B summary**")
    st.markdown(
        "- Edge pretension: %.3f kN (%s)" % (
            run_B["edge_pre_used_kN"], run_B["edge_pre_source"]
        )
        + "  |  edge_q: %.4f" % run_B["edge_q_scalar"]
        + "  |  warp_q: %.4f" % run_B["warp_q"]
        + "  |  weft_q: %.4f" % run_B["weft_q"]
    )
    st.markdown(
        "- Boundary nodes: " + str(run_B["n_boundary"])
        + "  |  L_avg: %.4f m" % run_B["L_avg"]
        + "  |  fixed: " + str(len(run_B["fixed_indices"]))
    )
    st.markdown(
        "- Boundary edges in mesh: "
        + str(run_B["n_boundary_edges_in_mesh"])
        + "  |  applied edge_q: "
        + str(run_B["n_boundary_edges_applied"])
    )

    st.markdown("---")
    st.markdown("**Boundary node displacement table**")
    st.caption(
        "node index, initial x/y/z, settled A (xA,yA,zA), "
        "settled B (xB,yB,zB), displacement |d| in mm, "
        "angle to local cable tangent, angle to Z axis."
    )

    rows = _analyse_run_pair(run_A, run_B)
    st.code(_format_table(rows), language="text")

    st.markdown("---")
    st.markdown("**Verdict**")
    st.markdown(_verdict(rows))


# =============================================================================
# END OF ui/workshops/tester_star_diagnostic.py
# =============================================================================
