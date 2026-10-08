# =============================================================================
# SDSe - Star Diagnostic (Lab)
# =============================================================================
# A background test, in the Lab, to find out how a boundary node
# that is shared between the cable and the membrane actually moves
# when the edge cable pretension is changed.
#
# The question:
#   Is the shared boundary node free along the cable direction,
#   free in Z only, or free in all three directions?
#
# The method:
#   - Build a diamond saddle, 5 m x 3 m plan, four corners pinned,
#     alternating corner heights (+1, -1, +1, -1).
#   - Four sides, all cable segments.
#   - Run the FDM solve twice, holding everything fixed except the
#     edge cable pretension.
#   - Read the boundary subdivision nodes (which are the shared
#     cable-membrane nodes) from both runs.
#   - Compute the displacement vector at each node.
#   - Report the angle of that displacement to the local cable
#     tangent, and to the Z axis.
#
# The interpretation:
#   If the motion is along the cable, the node is free along the
#   cable only. Directional constraint is the fix.
#   If the motion is in Z, the node is free in Z only. z_only is
#   the fix.
#   If the motion is inward in the plan plane, the node is fully
#   free. The star is a force-balance problem, not a constraint
#   problem, and the fix is in the force densities.
#
# This file is diagnostic only. It does not modify the engine,
# the viewer, or the working App. Nothing here is called by the
# production code.
#
# History:
#   2026-10-09 - First version, on the Chief's instruction.
# =============================================================================

import math

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
    Return (boundary_loop, anchor_indices, segment_types).

    A diamond plan: long diagonal 5 m along X, short diagonal 3 m
    along Y. Four corners, alternating heights (+1, -1, +1, -1).
    Between corners, subdivision points are laid along the straight
    chord. All four sides are cable segments.
    """
    corners = np.array([
        (-2.5,  0.0, +1.0),
        ( 0.0, +1.5, -1.0),
        ( 2.5,  0.0, +1.0),
        ( 0.0, -1.5, -1.0),
    ], dtype=float)

    subdivisions_per_side = 12

    loop = []
    anchors = []

    for k in range(4):
        a = corners[k]
        b = corners[(k + 1) % 4]
        anchors.append(len(loop))
        for j in range(subdivisions_per_side):
            frac = float(j) / float(subdivisions_per_side)
            p = a + (b - a) * frac
            loop.append((float(p[0]), float(p[1]), float(p[2])))

    boundary_loop = np.asarray(loop, dtype=float)
    anchor_indices = list(anchors)
    segment_types = ["cable"] * 4

    return boundary_loop, anchor_indices, segment_types


# =============================================================================
# ONE SOLVE
# =============================================================================

def _solve_once(boundary_loop, anchor_indices, segment_types,
                 edge_pretension_kN,
                 warp_pre_kN_per_m, weft_pre_kN_per_m,
                 mesh_spacing_m):
    """
    Run the FDM solve on the given boundary with the given edge
    cable pretension. Return the built dict.
    """
    n = boundary_loop.shape[0]
    total_len = 0.0
    for i in range(n):
        p0 = boundary_loop[i]
        p1 = boundary_loop[(i + 1) % n]
        total_len += float(np.linalg.norm(p1 - p0))
    L_avg = total_len / float(n)
    if L_avg < 1e-9:
        L_avg = 1.0

    warp_q = float(warp_pre_kN_per_m) * 1000.0 / L_avg
    weft_q = float(weft_pre_kN_per_m) * 1000.0 / L_avg
    edge_q_scalar = float(edge_pretension_kN) * 1000.0 / L_avg

    mesh_result = build_mesh_triangulated(
        boundary_loop=boundary_loop,
        anchor_indices=anchor_indices,
        segment_types=segment_types,
        target_edge_length=float(mesh_spacing_m),
        plan_plane=None,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q_scalar,
    )

    points_initial = mesh_result["points_initial"]
    edges = mesh_result["edges"]
    fixed_indices = mesh_result["fixed_indices"]

    pts_2d = points_initial[:, :2]
    warp_dir = auto_warp_dir(pts_2d)

    n_boundary_pts = boundary_loop.shape[0]
    q_aniso = assign_anisotropic_q(
        edges,
        pts_2d,
        warp_dir,
        warp_q,
        weft_q,
        n_boundary=n_boundary_pts,
        boundary_edge_q=edge_q_scalar,
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
    }


# =============================================================================
# DISPLACEMENT ANALYSIS
# =============================================================================

def _cable_tangent_at(coords, boundary_index, n_boundary):
    """
    Return the unit tangent of the boundary loop at the given
    boundary index, taken from the settled coordinates. Uses the
    two neighbours along the loop.
    """
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
    """
    Compare the boundary nodes between the two runs. Return a list
    of dicts, one per boundary subdivision node (anchors excluded).
    """
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
    if total_motion_mm < 0.1:
        return (
            "No measurable motion. The two pretensions produced "
            "identical settled coordinates. The node is effectively "
            "fixed in all three axes, or the pretension change had "
            "no effect on the solve."
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
        "Mean angle to cable tangent: %.1f deg. "
        "Mean angle to Z: %.1f deg."
        % (mean_cable, mean_Z)
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
        "A background test to see how the shared boundary node "
        "moves when only the edge cable pretension is changed."
    )

    st.markdown(
        "**Shape.** Diamond in plan, 5 m long diagonal, 3 m short "
        "diagonal. Four corners pinned, alternating heights "
        "(+1, -1, +1, -1). Four sides, all cable. "
        "Mesh spacing 0.25 m, 12 subdivisions per side."
    )

    st.markdown(
        "**Method.** Two FDM solves. Same geometry, same warp and "
        "weft. Only the edge cable pretension differs."
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

    boundary_loop, anchor_indices, segment_types = _build_diamond_boundary()

    with st.spinner("Running solve A..."):
        run_A = _solve_once(
            boundary_loop, anchor_indices, segment_types,
            edge_pretension_kN=float(edge_A),
            warp_pre_kN_per_m=float(warp_pre),
            weft_pre_kN_per_m=float(weft_pre),
            mesh_spacing_m=float(mesh_spacing),
        )
    with st.spinner("Running solve B..."):
        run_B = _solve_once(
            boundary_loop, anchor_indices, segment_types,
            edge_pretension_kN=float(edge_B),
            warp_pre_kN_per_m=float(warp_pre),
            weft_pre_kN_per_m=float(weft_pre),
            mesh_spacing_m=float(mesh_spacing),
        )

    st.markdown("---")
    st.markdown("**Solve A summary**")
    st.markdown(
        "- Edge pretension: %.3f kN" % float(edge_A)
        + "  |  edge_q: %.4f" % run_A["edge_q_scalar"]
        + "  |  warp_q: %.4f" % run_A["warp_q"]
        + "  |  weft_q: %.4f" % run_A["weft_q"]
    )
    st.markdown(
        "- Boundary nodes: " + str(run_A["n_boundary"])
        + "  |  L_avg: %.4f m" % run_A["L_avg"]
        + "  |  fixed: " + str(len(run_A["fixed_indices"]))
    )

    st.markdown("**Solve B summary**")
    st.markdown(
        "- Edge pretension: %.3f kN" % float(edge_B)
        + "  |  edge_q: %.4f" % run_B["edge_q_scalar"]
        + "  |  warp_q: %.4f" % run_B["warp_q"]
        + "  |  weft_q: %.4f" % run_B["weft_q"]
    )
    st.markdown(
        "- Boundary nodes: " + str(run_B["n_boundary"])
        + "  |  L_avg: %.4f m" % run_B["L_avg"]
        + "  |  fixed: " + str(len(run_B["fixed_indices"]))
    )

    st.markdown("---")
    st.markdown("**Boundary node displacement table**")
    st.caption(
        "Columns: node index, initial x, y, z, settled coordinates "
        "in run A (xA, yA, zA), settled coordinates in run B "
        "(xB, yB, zB), displacement magnitude in mm, angle of the "
        "displacement to the local cable tangent in degrees, angle "
        "of the displacement to the Z axis in degrees."
    )

    rows = _analyse_run_pair(run_A, run_B)
    st.code(_format_table(rows), language="text")

    st.markdown("---")
    st.markdown("**Verdict**")
    verdict = _verdict(rows)
    st.markdown(verdict)


# =============================================================================
# END OF ui/workshops/tester_star_diagnostic.py
# =============================================================================
