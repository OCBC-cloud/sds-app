# =============================================================================
# SDSe - Star Diagnostic (Lab)
# =============================================================================
# Test 1 - Does the shared boundary node move along the cable, or off it?
#   Two FDM solves at two edge pretensions. For each boundary
#   subdivision node, compute the displacement vector and the angle
#   to the local cable tangent.
#
# Test 2 - Can a stronger cable hold the node on the cable line?
#   Three FDM solves at three edge pretensions (low, medium, high).
#   For each of the four sides, take the mid-side boundary node and
#   measure its perpendicular distance from the straight chord
#   between its two anchors. If the distance falls to near zero at
#   high edge pretension, the cable can win when strong enough. If
#   the distance stays large, the cable cannot win at any strength,
#   and the fix must be a directional constraint.
#
# The path:
#   The q computation, the mesh call, and the FDM call are taken
#   from _solve_fdm_path in viewers/figures/standard_saddle_mbs.py.
#   The boundary-edge q is passed as a DICT, matching the working
#   saddle viewer's form-finding path.
#
# Diagnostic only. Nothing here is called by the production code.
#
# History:
#   2026-10-09 - First version.
#   2026-10-09 - Rewritten to borrow the working q path.
#   2026-10-09 - Rewritten to pass a DICT of boundary q values.
#   2026-10-09 - Added the three-run chord-distance test.
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
    if edge_pre_used <= 0.0:
        edge_pre_used = 0.05

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
    }


# =============================================================================
# TEST 1 - Angle of motion to the local cable tangent
# =============================================================================

def _cable_tangent_at(coords, boundary_index, n_boundary):
    prev_idx = (boundary_index - 1) % n_boundary
    next_idx = (boundary_index + 1) % n_boundary
    t = coords[next_idx] - coords[prev_idx]
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
            "mag": mag,
            "angle_to_cable_deg": angle_cable,
            "angle_to_Z_deg": angle_z,
        })
    return rows


def _format_angle_table(rows):
    header = (
        "%5s  %8s  %8s  %8s  %8s  %8s  %8s  %9s  %9s  %9s"
        % ("idx", "x_init", "y_init", "z_init",
           "xA", "yA", "zA",
           "|d|_mm", "ang_cab", "ang_Z")
    )
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            "%5d  %8.3f  %8.3f  %8.3f  %8.3f  %8.3f  %8.3f  %9.3f  %9.2f  %9.2f"
            % (r["index"],
               r["x_init"], r["y_init"], r["z_init"],
               r["xA"], r["yA"], r["zA"],
               r["mag"] * 1000.0,
               r["angle_to_cable_deg"],
               r["angle_to_Z_deg"])
        )
    return "\n".join(lines)


def _angle_verdict(rows):
    if not rows:
        return "No boundary subdivision nodes found."
    mags = [r["mag"] for r in rows]
    total_mm = sum(mags) * 1000.0
    if total_mm < 0.1:
        return "No measurable motion."
    wc = 0.0
    wz = 0.0
    ws = 0.0
    for r in rows:
        w = r["mag"]
        wc += r["angle_to_cable_deg"] * w
        wz += r["angle_to_Z_deg"] * w
        ws += w
    mean_cable = wc / ws if ws > 1e-12 else 0.0
    mean_Z = wz / ws if ws > 1e-12 else 0.0
    verdict = (
        "Max motion: %.3f mm.  Mean angle to cable: %.1f deg.  "
        "Mean angle to Z: %.1f deg."
        % (max(mags) * 1000.0, mean_cable, mean_Z)
    )
    if mean_cable < 30.0:
        verdict += "  Motion along cable."
    elif mean_Z < 30.0:
        verdict += "  Motion in Z."
    else:
        verdict += "  Motion inward in plan plane."
    return verdict


# =============================================================================
# TEST 2 - Mid-side node distance from the anchor chord
# =============================================================================

def _mid_node_chord_distance(coords, boundary_loop, anchor_indices, n_boundary):
    """
    For each side (between two consecutive anchors), find the boundary
    subdivision node at the middle of that side, and compute the
    perpendicular distance from that node to the straight chord
    between the two anchors.
    Returns a list of dicts, one per side.
    """
    results = []
    n_a = len(anchor_indices)
    for k in range(n_a):
        aa = anchor_indices[k]
        bb = anchor_indices[(k + 1) % n_a]

        interior = []
        i = (aa + 1) % n_boundary
        safety = 0
        while i != bb and safety < n_boundary:
            interior.append(i)
            i = (i + 1) % n_boundary
            safety += 1

        if not interior:
            continue

        mid = interior[len(interior) // 2]

        pA = coords[aa]
        pB = coords[bb]
        pM = coords[mid]

        chord = pB - pA
        chord_len = float(np.linalg.norm(chord))
        if chord_len < 1e-12:
            d_perp = 0.0
        else:
            u = chord / chord_len
            w = pM - pA
            proj = float(np.dot(w, u))
            perp = w - proj * u
            d_perp = float(np.linalg.norm(perp))

        results.append({
            "side": k,
            "anchor_a": int(aa),
            "anchor_b": int(bb),
            "mid_node": int(mid),
            "chord_len_m": chord_len,
            "perp_dist_mm": d_perp * 1000.0,
        })
    return results


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_tester_star_diagnostic():
    st.markdown(
        "## Star Diagnostic  \n"
        "Two tests on the diamond.  \n"
        "Test 1: two runs, angle of node motion to the cable.  \n"
        "Test 2: three runs, mid-side node distance from the anchor chord."
    )

    st.markdown(
        "**Shape.** Diamond in plan, 5 m long diagonal, 3 m short "
        "diagonal. Four corners pinned, alternating heights "
        "(+1, -1, +1, -1). Four sides, all cable. "
        "Mesh spacing 0.25 m, 12 subdivisions per side."
    )

    # ---------------------------------------------------------------
    # TEST 1 INPUTS
    # ---------------------------------------------------------------
    st.markdown("### Test 1 - angle of motion")
    c1, c2, c3 = st.columns(3)
    with c1:
        edge_A = st.number_input(
            "Edge cable A (kN)",
            value=0.5, min_value=0.01, max_value=1000.0, step=0.1,
            key="diag_edge_A",
        )
    with c2:
        edge_B = st.number_input(
            "Edge cable B (kN)",
            value=5.0, min_value=0.01, max_value=1000.0, step=0.1,
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

    run1 = st.button(
        "Run Test 1",
        key="diag_run1",
        use_container_width=True,
        type="primary",
    )

    if run1:
        boundary_loop, anchors, segment_types, segments = _build_diamond_boundary()

        with st.spinner("Running A..."):
            run_A = _solve_once(
                boundary_loop, anchors, segment_types,
                edge_pretension_kN=float(edge_A),
                warp_pre_kN_per_m=float(warp_pre),
                weft_pre_kN_per_m=float(weft_pre),
                mesh_spacing_m=float(mesh_spacing),
            )
        with st.spinner("Running B..."):
            run_B = _solve_once(
                boundary_loop, anchors, segment_types,
                edge_pretension_kN=float(edge_B),
                warp_pre_kN_per_m=float(warp_pre),
                weft_pre_kN_per_m=float(weft_pre),
                mesh_spacing_m=float(mesh_spacing),
            )

        st.markdown(
            "**A:** edge %.3f kN  |  edge_q %.4f  |  warp_q %.4f  |  weft_q %.4f  |  L_avg %.4f m"
            % (run_A["edge_pre_used_kN"], run_A["edge_q_scalar"],
               run_A["warp_q"], run_A["weft_q"], run_A["L_avg"])
        )
        st.markdown(
            "**B:** edge %.3f kN  |  edge_q %.4f"
            % (run_B["edge_pre_used_kN"], run_B["edge_q_scalar"])
        )

        rows = _analyse_run_pair(run_A, run_B)
        st.code(_format_angle_table(rows), language="text")
        st.markdown("**Verdict:** " + _angle_verdict(rows))

    # ---------------------------------------------------------------
    # TEST 2 INPUTS
    # ---------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Test 2 - can the cable hold the mid-side node?")
    st.caption(
        "Three runs. For each side, the perpendicular distance of the "
        "mid-side node from the straight chord between its two anchors."
    )

    d1, d2, d3 = st.columns(3)
    with d1:
        edge_low = st.number_input(
            "Edge LOW (kN)",
            value=0.5, min_value=0.01, max_value=1000.0, step=0.1,
            key="diag_edge_low",
        )
    with d2:
        edge_mid = st.number_input(
            "Edge MID (kN)",
            value=20.0, min_value=0.01, max_value=5000.0, step=1.0,
            key="diag_edge_mid",
        )
    with d3:
        edge_high = st.number_input(
            "Edge HIGH (kN)",
            value=200.0, min_value=0.01, max_value=20000.0, step=10.0,
            key="diag_edge_high",
        )

    run2 = st.button(
        "Run Test 2",
        key="diag_run2",
        use_container_width=True,
        type="primary",
    )

    if run2:
        boundary_loop, anchors, segment_types, segments = _build_diamond_boundary()

        with st.spinner("Running LOW..."):
            rL = _solve_once(
                boundary_loop, anchors, segment_types,
                edge_pretension_kN=float(edge_low),
                warp_pre_kN_per_m=float(warp_pre),
                weft_pre_kN_per_m=float(weft_pre),
                mesh_spacing_m=float(mesh_spacing),
            )
        with st.spinner("Running MID..."):
            rM = _solve_once(
                boundary_loop, anchors, segment_types,
                edge_pretension_kN=float(edge_mid),
                warp_pre_kN_per_m=float(warp_pre),
                weft_pre_kN_per_m=float(weft_pre),
                mesh_spacing_m=float(mesh_spacing),
            )
        with st.spinner("Running HIGH..."):
            rH = _solve_once(
                boundary_loop, anchors, segment_types,
                edge_pretension_kN=float(edge_high),
                warp_pre_kN_per_m=float(warp_pre),
                weft_pre_kN_per_m=float(weft_pre),
                mesh_spacing_m=float(mesh_spacing),
            )

        n_boundary = rL["n_boundary"]

        dL = _mid_node_chord_distance(
            rL["coords"], boundary_loop, anchors, n_boundary)
        dM = _mid_node_chord_distance(
            rM["coords"], boundary_loop, anchors, n_boundary)
        dH = _mid_node_chord_distance(
            rH["coords"], boundary_loop, anchors, n_boundary)

        header = (
            "%5s  %9s  %9s  %9s  %9s  %9s  %9s"
            % ("side", "chord_m",
               "LOW_mm", "MID_mm", "HIGH_mm",
               "edge_q_L", "edge_q_H")
        )
        lines = [header, "-" * len(header)]
        for i in range(len(dL)):
            lines.append(
                "%5d  %9.4f  %9.3f  %9.3f  %9.3f  %9.2f  %9.2f"
                % (dL[i]["side"],
                   dL[i]["chord_len_m"],
                   dL[i]["perp_dist_mm"],
                   dM[i]["perp_dist_mm"],
                   dH[i]["perp_dist_mm"],
                   rL["edge_q_scalar"],
                   rH["edge_q_scalar"])
            )
        st.code("\n".join(lines), language="text")

        # Summary
        ratio_summary = []
        for i in range(len(dL)):
            if dL[i]["perp_dist_mm"] > 1e-6:
                ratio = dH[i]["perp_dist_mm"] / dL[i]["perp_dist_mm"]
            else:
                ratio = 0.0
            ratio_summary.append(ratio)

        avg_ratio = sum(ratio_summary) / len(ratio_summary) if ratio_summary else 0.0
        max_high = max(d["perp_dist_mm"] for d in dH) if dH else 0.0

        st.markdown(
            "**Average ratio HIGH/LOW of mid-side perpendicular distance: "
            "%.4f**" % avg_ratio
        )
        st.markdown(
            "**Max HIGH perpendicular distance: %.3f mm**" % max_high
        )

        if max_high < 5.0:
            st.markdown(
                "**VERDICT:** the cable wins at high pretension. "
                "Mid-side node sits on the anchor chord. "
                "The star is a strength problem, not a constraint problem."
            )
        else:
            st.markdown(
                "**VERDICT:** the cable cannot hold the node on the "
                "chord, even at high pretension. "
                "The node is free in all three directions. "
                "The fix must be a directional constraint."
            )


# =============================================================================
# END OF ui/workshops/tester_star_diagnostic.py
# =============================================================================
