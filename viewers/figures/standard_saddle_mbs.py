# =============================================================================
# SDSe - Standard Saddle Figure Builder (MBS version)
# =============================================================================
# Builds the 3D figure for the Standard Saddle variant.
#
# Three zones, three audiences.
#
#   Zone 1 - Chart and controls. Visible to every user.
#            - The 3D chart.
#            - Display checkboxes (beams, membrane, anchors,
#              edge cable, tie-downs, supports).
#            - Solver mode selector (FDM / NFDM), shown to
#              Owner, Studio, Beta only.
#
#   Zone 2 - Customer deliverables. Owner, Studio, Beta only.
#            - Structural Analysis Report.
#            - Bill of Quantities.
#            - Member Schedule.
#
#   Zone 3 - Engineering bench. Owner only. Never visible to
#            any customer, at any price.
#            - Solver diagnostics: path, access mode, mesh
#              counts, convergence, residual, iterations.
#            - Edge cable pretension source and value.
#            - Pull-back summary.
#            - q values summary and per-edge table.
#            - Digitised node data: boundary, top 20, all nodes.
#
# The Owner role is the engineer's seat. It is not the top of
# the commercial ladder. It is the bench where the App is
# built. Nobody else ever sees Zone 3.
#
# History:
#   2026-09-29 - Step 2C. First MBS version.
#   2026-09-30 - Step 5. Rewritten to use the triangulated engine.
#   2026-10-04 - Step 2E. Anchors and subdivision.
#   2026-10-04 - Two-path solver. NFDM for high tiers.
#   2026-10-05 - Pull-back initial guess. Single-build FDM.
#                Cache. Loading message. Checkbox toggles.
#   2026-10-06 - FDM path fallback. Digitised node data.
#                q array print. Mode selector. Threshold fix.
#                Auto-scaled edge cable pretension.
#   2026-10-07 - Three zones. Owner gate on Zone 3.
#                Zone 2 placeholder for the report and BQ.
#   2026-10-07 - Zone 2 Structural Analysis Report. Nine sections.
#                Derived quantities only, no raw q in Zone 2.
#                Report gated on FDM path. NFDM shows reminder.
#                Drainage check: 15 deg rain / 28 deg snow.
#   2026-10-07 - Report wired to engine/member_sizing.py.
#                Sections 3, 4, 6 now carry real design forces.
#                Base condition read from ws_ss_base_condition.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go

import streamlit as st

from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
    find_index_at_arclength_fraction,
)
from engine.mesh_triangulated import build_mesh_triangulated
from engine.nonlinear_equilibrium import (
    solve_nonlinear_equilibrium,
    make_membrane_material,
    pullback_cable_initial_tensions,
)
from engine.form_finding import solve_fdm, assign_anisotropic_q, auto_warp_dir
from engine.member_sizing import design_forces_from_built
from data.materials import CABLE_PROPERTIES, FABRIC_PROPERTIES
from data.structures import get_member_schema, expand_beam_rows


# =============================================================================
# ACCESS MODE
# =============================================================================

HIGH_TIERS = ("owner", "studio", "beta")
OWNER_TIER = "owner"


def _access_mode():
    return str(st.session_state.get("access_mode", "owner")).lower()


def _is_high_tier():
    """Owner, Studio, Beta. Can select FDM/NFDM and see customer deliverables."""
    return _access_mode() in HIGH_TIERS


def _is_owner():
    """Owner only. The engineering bench. Never visible to any customer."""
    return _access_mode() == OWNER_TIER


# =============================================================================
# MATERIAL HELPERS
# =============================================================================

def _read_fabric_constants(fabric_type, fabric_grade):
    try:
        rec = FABRIC_PROPERTIES[fabric_type][fabric_grade]
        E1 = float(rec.get("E_warp", 1400.0))
        E2 = float(rec.get("E_weft", 1400.0))
        t = float(rec.get("t_mm", 1.02))
    except Exception:
        E1, E2, t = 1400.0, 1400.0, 1.02
    return E1, E2, t


def _pretension_to_N_per_m(value, recipe_units):
    v = max(0.0, float(value))
    if recipe_units == "daN/5cm":
        return v * 200.0
    return v * 1000.0


def _pick_cable_diameter(cable_type, material, pretension_kN,
                          safety_factor=5.0):
    family = None
    if cable_type == "6x19":
        family = CABLE_PROPERTIES.get("Strand", {})
    elif cable_type == "Locked Coil":
        family = CABLE_PROPERTIES.get("Locked Coil", {})
    elif cable_type == "Spiral":
        family = CABLE_PROPERTIES.get("Spiral", {})
    if not family:
        return None
    required_kN = float(pretension_kN) * float(safety_factor)
    entries = []
    for name, props in family.items():
        if name == "default":
            continue
        try:
            A_mm2 = float(props.get("A", 0.0))
            f_u = float(props.get("f_u", 0.0))
        except Exception:
            continue
        if A_mm2 <= 0 or f_u <= 0:
            continue
        breaking_kN = A_mm2 * f_u / 1000.0
        entries.append({
            "name": name,
            "d": float(props.get("d", 0.0)),
            "A": A_mm2,
            "f_u": f_u,
            "E": float(props.get("E", 0.0)),
            "kg_m": float(props.get("kg_m", 0.0)),
            "breaking_kN": breaking_kN,
        })
    entries.sort(key=lambda e: e["A"])
    for e in entries:
        if e["breaking_kN"] >= required_kN:
            return e
    return entries[-1] if entries else None


# =============================================================================
# NODE TABLE FORMATTER
# =============================================================================

def _format_node_table(points_initial, points_solved, indices=None):
    if indices is None:
        indices = range(points_initial.shape[0])
    lines = []
    header = (
        "%6s  %11s  %11s  %11s  %11s  %11s  %11s  %11s"
        % ("idx", "x_init", "y_init", "z_init",
           "x_solved", "y_solved", "z_solved", "disp")
    )
    lines.append(header)
    lines.append("-" * len(header))
    for k in indices:
        xi, yi, zi = points_initial[k]
        xs, ys, zs = points_solved[k]
        d = float(np.linalg.norm(
            np.array([xs - xi, ys - yi, zs - zi])
        ))
        lines.append(
            "%6d  %11.6f  %11.6f  %11.6f  %11.6f  %11.6f  %11.6f  %11.6e"
            % (k, xi, yi, zi, xs, ys, zs, d)
        )
    return "\n".join(lines)


def _top_displaced_indices(points_initial, points_solved, n_top=20):
    d = np.linalg.norm(points_solved - points_initial, axis=1)
    order = np.argsort(d)[::-1]
    return [int(k) for k in order[:n_top]]


def _format_q_table(edges, q_values, n_boundary, n_show=40):
    lines = []
    header = "%6s  %14s  %12s  %14s" % (
        "edge", "endpoints", "is_boundary", "q_value")
    lines.append(header)
    lines.append("-" * len(header))
    m = len(edges)
    for k in range(min(n_show, m)):
        a, b = edges[k]
        is_b = (
            n_boundary > 0
            and a < n_boundary
            and b < n_boundary
            and (abs(a - b) == 1 or abs(a - b) == n_boundary - 1)
        )
        lines.append(
            "%6d  %6d,%6d  %12s  %14.6e"
            % (k, int(a), int(b), str(is_b), float(q_values[k]))
        )
    return "\n".join(lines)


def _summarise_q(edges, q_values, n_boundary):
    m = len(edges)
    boundary_qs = []
    interior_qs = []
    for k in range(m):
        a, b = edges[k]
        is_b = (
            n_boundary > 0
            and a < n_boundary
            and b < n_boundary
            and (abs(a - b) == 1 or abs(a - b) == n_boundary - 1)
        )
        if is_b:
            boundary_qs.append(float(q_values[k]))
        else:
            interior_qs.append(float(q_values[k]))
    out = {}
    if boundary_qs:
        out["boundary_n"] = len(boundary_qs)
        out["boundary_min"] = float(np.min(boundary_qs))
        out["boundary_max"] = float(np.max(boundary_qs))
        out["boundary_mean"] = float(np.mean(boundary_qs))
    if interior_qs:
        out["interior_n"] = len(interior_qs)
        out["interior_min"] = float(np.min(interior_qs))
        out["interior_max"] = float(np.max(interior_qs))
        out["interior_mean"] = float(np.mean(interior_qs))
    if boundary_qs and interior_qs:
        out["ratio_mean_boundary_over_interior"] = (
            float(np.mean(boundary_qs)) / max(float(np.mean(interior_qs)), 1e-30)
        )
    return out


# =============================================================================
# BOUNDARY LOOP
# =============================================================================

def _build_boundary_loop(x, z_beam, y1, y2, span, anchor_count,
                          mesh_spacing, attachment_type):
    n_pts = len(x)
    s, total = arclength_parametrisation(x, z_beam)
    if total <= 0:
        s = np.linspace(0.0, 1.0, n_pts)
        total = 1.0

    arc_targets = np.linspace(0.0, total, anchor_count)

    if anchor_count > 1:
        seg_arc = total / float(anchor_count - 1)
    else:
        seg_arc = total
    if mesh_spacing is None or mesh_spacing <= 0:
        sub = 1
    else:
        sub = int(round(seg_arc / float(mesh_spacing)))
        if sub < 1:
            sub = 1
        if sub > 20:
            sub = 20

    def _beam_points(y_curve, reverse=False):
        pts = []
        anchors_local = []
        for k in range(anchor_count):
            target = arc_targets[k]
            bx = float(np.interp(target, s, x))
            bz = float(np.interp(target, s, z_beam))
            by = float(np.interp(target, s, y_curve))
            anchors_local.append(len(pts))
            pts.append((bx, by, bz))
            if k < anchor_count - 1 and sub > 0:
                a0 = arc_targets[k]
                a1 = arc_targets[k + 1]
                for j in range(1, sub + 1):
                    frac = float(j) / float(sub + 1)
                    tm = a0 + (a1 - a0) * frac
                    mx = float(np.interp(tm, s, x))
                    mz = float(np.interp(tm, s, z_beam))
                    my = float(np.interp(tm, s, y_curve))
                    pts.append((mx, my, mz))
        if reverse:
            n = len(pts)
            rev_pts = [pts[n - 1 - i] for i in range(n)]
            rev_anchors = [n - 1 - a for a in anchors_local]
            return rev_pts, rev_anchors
        return pts, anchors_local

    beam_L_pts, beam_L_anchors = _beam_points(y1, reverse=False)
    beam_R_pts, beam_R_anchors = _beam_points(y2, reverse=True)

    loop_pts = list(beam_L_pts)
    for i in range(1, len(beam_R_pts) - 1):
        loop_pts.append(beam_R_pts[i])

    boundary_loop = np.asarray(loop_pts, dtype=float)

    anchors = list(beam_L_anchors)
    offset = len(beam_L_pts)
    for a in beam_R_anchors:
        if a == 0:
            continue
        if a == len(beam_R_pts) - 1:
            continue
        anchors.append(offset + (a - 1))
    anchors = sorted(set(anchors))

    segments = []
    n_a = len(anchors)
    for k in range(n_a):
        a = anchors[k]
        b = anchors[(k + 1) % n_a]
        interior = []
        i = (a + 1) % boundary_loop.shape[0]
        safety = 0
        while i != b and safety < boundary_loop.shape[0]:
            interior.append(i)
            i = (i + 1) % boundary_loop.shape[0]
            safety += 1
        segments.append({
            "anchor_a": int(a),
            "anchor_b": int(b),
            "interior": interior,
        })

    if str(attachment_type).lower() == "cable_supported":
        seg_types = ["cable"] * n_a
    else:
        seg_types = ["beam"] * n_a

    anchor_pos = boundary_loop[anchors]

    return boundary_loop, anchors, seg_types, anchor_pos, segments


def _build_beam_curves(span, apex, rise, curve_type, n_pts=200):
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)
    s, total = arclength_parametrisation(x, z_beam)
    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)
    return x, y1, y2, z_beam, s, total


# =============================================================================
# AUTO-SCALED EDGE CABLE PRETENSION
# =============================================================================

def _auto_edge_pretension_kN(arc_total, anchor_count,
                              warp_pre, weft_pre):
    """
    Return the auto-scaled edge cable pretension in kN.

    The bow threshold scales with the anchor spacing, not the
    total span. The threshold is:

        T = N_membrane * L_anchor

    where:
        N_membrane  = the membrane prestress resultant (N/m),
                      taken as max(warp_pre, weft_pre).
        L_anchor    = the distance between two adjacent anchors
                      along the beam = arc_total / (anchor_count - 1).
    """
    if anchor_count < 2:
        return 0.0
    L_anchor = float(arc_total) / float(anchor_count - 1)
    N_membrane = max(
        float(warp_pre) * 1000.0,
        float(weft_pre) * 1000.0,
    )
    T_N = N_membrane * L_anchor
    return T_N / 1000.0


# =============================================================================
# FDM PATH
# =============================================================================

def _solve_fdm_path(span, apex, rise, curve_type,
                     anchor_count, mesh_spacing,
                     warp_pre, weft_pre, edge_pre,
                     attachment_type,
                     fabric_type, fabric_grade):
    x, y1, y2, z_beam, s, total = _build_beam_curves(
        span, apex, rise, curve_type
    )

    boundary_loop, anchors, seg_types, anchor_pos, segments = (
        _build_boundary_loop(
            x, z_beam, y1, y2, span, anchor_count, mesh_spacing,
            attachment_type,
        )
    )

    target_len = float(mesh_spacing) if mesh_spacing and mesh_spacing > 0 else None

    n = boundary_loop.shape[0]
    total_len = 0.0
    for i in range(n):
        p0 = boundary_loop[i]
        p1 = boundary_loop[(i + 1) % n]
        total_len += float(np.linalg.norm(p1 - p0))
    L_avg = total_len / float(n) if n > 0 else 1.0
    if L_avg < 1e-9:
        L_avg = 1.0

    edge_pre_used = float(edge_pre)
    edge_pre_source = "user"
    if edge_pre_used <= 0.0:
        edge_pre_used = _auto_edge_pretension_kN(
            total, anchor_count, warp_pre, weft_pre
        )
        edge_pre_source = "auto"
    if edge_pre_used <= 0.0:
        edge_pre_used = 0.05

    baseline_kN_per_m = 2.0
    ratio_limit = 4.0
    warp_input = max(0.1, float(warp_pre))
    weft_input = max(0.1, float(weft_pre))
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

    mesh_result = build_mesh_triangulated(
        boundary_loop=boundary_loop,
        anchor_indices=anchors,
        segment_types=seg_types,
        target_edge_length=target_len,
        plan_plane=None,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q_scalar,
    )

    points_initial = mesh_result["points_initial"]
    edges = mesh_result["edges"]
    triangles = mesh_result["triangles"]
    fixed_indices = mesh_result["fixed_indices"]

    E1, E2, t_mm = _read_fabric_constants(fabric_type, fabric_grade)
    warp_prest_N = _pretension_to_N_per_m(warp_pre, "kN/m")
    weft_prest_N = _pretension_to_N_per_m(weft_pre, "kN/m")
    mat = make_membrane_material(
        E_warp_MPa=E1, E_weft_MPa=E2, thickness_mm=t_mm,
        nu=0.34, G_MPa=50.0,
        warp_prestress_N_per_m=warp_prest_N,
        weft_prestress_N_per_m=weft_prest_N,
    )

    pullback_summary = None
    q_dict = None
    n_fallback_edges = 0
    if str(attachment_type).lower() == "cable_supported":
        try:
            tensions = pullback_cable_initial_tensions(
                points=points_initial,
                triangles=triangles,
                boundary_loop=boundary_loop,
                anchors=anchors,
                segments=segments,
                material=mat,
            )
            q_dict = {}
            for key, T in tensions.items():
                i, j = int(key[0]), int(key[1])
                L = float(np.linalg.norm(points_initial[j] - points_initial[i]))
                if L < 1e-9:
                    continue
                q_kk = (i, j) if i < j else (j, i)
                if T is not None and T > 1.0:
                    q_dict[q_kk] = float(T) / L
                else:
                    q_dict[q_kk] = float(edge_q_scalar)
                    n_fallback_edges += 1
            tvals = [v for v in tensions.values() if v > 1.0]
            if tvals:
                pullback_summary = {
                    "min_N": float(min(tvals)),
                    "max_N": float(max(tvals)),
                    "mean_N": float(sum(tvals) / len(tvals)),
                    "n_edges": len(tvals),
                    "n_fallback_edges": int(n_fallback_edges),
                }
            else:
                pullback_summary = {
                    "min_N": 0.0,
                    "max_N": 0.0,
                    "mean_N": 0.0,
                    "n_edges": 0,
                    "n_fallback_edges": int(n_fallback_edges),
                    "note": "pull-back returned zero or below 1 N on every boundary edge; fell back to edge_q_scalar",
                }
        except Exception as e:
            pullback_summary = {"error": str(e)}

    pts_2d = points_initial[:, :2]
    warp_dir = auto_warp_dir(pts_2d)

    n_boundary_pts = boundary_loop.shape[0]
    if q_dict is not None:
        q_aniso = assign_anisotropic_q(
            edges,
            pts_2d,
            warp_dir,
            warp_q,
            weft_q,
            n_boundary=n_boundary_pts,
            boundary_edge_q=q_dict,
        )
        q_path = "dict"
    else:
        q_aniso = assign_anisotropic_q(
            edges,
            pts_2d,
            warp_dir,
            warp_q,
            weft_q,
            n_boundary=n_boundary_pts,
            boundary_edge_q=edge_q_scalar,
        )
        q_path = "scalar"

    fdm_result = solve_fdm(
        points_initial.copy(),
        edges,
        fixed_indices,
        q_aniso,
    )
    coords = fdm_result["coordinates"]

    edge_cable_length_m = 0.0
    if str(attachment_type).lower() == "cable_supported":
        n_a = len(anchors)
        for k in range(n_a):
            a = anchor_pos[k]
            b = anchor_pos[(k + 1) % n_a]
            edge_cable_length_m += float(np.linalg.norm(b - a))

    diagnostics = {
        "solver": "FDM (Stage 1)",
        "residual_norm": float(fdm_result.get("residual_norm", 0.0)),
        "n_free": int(fdm_result.get("n_free", 0)),
        "n_fixed": int(len(fixed_indices)),
        "n_nodes": int(coords.shape[0]),
        "n_edges": len(edges),
        "n_triangles": len(triangles),
        "n_anchors": len(anchors),
        "n_segments": len(seg_types),
        "target_edge_length": float(target_len) if target_len else 0.0,
        "L_avg": float(L_avg),
        "attachment_type": str(attachment_type),
        "anchor_count": int(anchor_count),
        "mesh_spacing": float(mesh_spacing),
        "edge_cable_length_m": float(edge_cable_length_m),
        "pullback_summary": pullback_summary,
        "n_fallback_edges": int(n_fallback_edges),
        "q_path": q_path,
        "warp_q": float(warp_q),
        "weft_q": float(weft_q),
        "edge_q_scalar": float(edge_q_scalar),
        "edge_pretension_kN": float(edge_pre_used),
        "edge_pretension_source": str(edge_pre_source),
        "L_anchor_m": float(total) / max(1.0, float(anchor_count - 1)),
        "top_displacements": [],
        "structural_connections": [],
        "fixed_indices": [int(i) for i in fixed_indices],
        "reactions": fdm_result.get("reactions", None),
        "variant_key": "standard_saddle",
    }

    return {
        "points": coords,
        "points_initial": points_initial,
        "edges": edges,
        "triangles": triangles,
        "fixed_indices": fixed_indices,
        "q": q_aniso,
        "boundary_loop": boundary_loop,
        "anchors": anchors,
        "anchor_pos": anchor_pos,
        "segments": segments,
        "seg_types": seg_types,
        "diagnostics": diagnostics,
    }


# =============================================================================
# NFDM PATH
# =============================================================================

def _solve_nfdm_path(span, apex, rise, curve_type,
                      anchor_count, mesh_spacing,
                      warp_pre, weft_pre, edge_pre,
                      attachment_type,
                      edge_cable_type, edge_cable_material,
                      fabric_type, fabric_grade):
    x, y1, y2, z_beam, s, total = _build_beam_curves(
        span, apex, rise, curve_type
    )

    boundary_loop, anchors, seg_types, anchor_pos, segments = (
        _build_boundary_loop(
            x, z_beam, y1, y2, span, anchor_count, mesh_spacing,
            attachment_type,
        )
    )

    target_len = float(mesh_spacing) if mesh_spacing and mesh_spacing > 0 else None

    n = boundary_loop.shape[0]
    total_len = 0.0
    for i in range(n):
        p0 = boundary_loop[i]
        p1 = boundary_loop[(i + 1) % n]
        total_len += float(np.linalg.norm(p1 - p0))
    L_avg = total_len / float(n) if n > 0 else 1.0
    if L_avg < 1e-9:
        L_avg = 1.0

    edge_pre_used = float(edge_pre)
    edge_pre_source = "user"
    if edge_pre_used <= 0.0:
        edge_pre_used = _auto_edge_pretension_kN(
            total, anchor_count, warp_pre, weft_pre
        )
        edge_pre_source = "auto"
    if edge_pre_used <= 0.0:
        edge_pre_used = 0.05

    mesh_result = build_mesh_triangulated(
        boundary_loop=boundary_loop,
        anchor_indices=anchors,
        segment_types=seg_types,
        target_edge_length=target_len,
        plan_plane=None,
        warp_q=2000.0,
        weft_q=2000.0,
        edge_q=5000.0,
    )

    points_initial = mesh_result["points_initial"]
    edges = mesh_result["edges"]
    triangles = mesh_result["triangles"]
    fixed_indices = mesh_result["fixed_indices"]
    n_nodes = points_initial.shape[0]

    E1, E2, t_mm = _read_fabric_constants(fabric_type, fabric_grade)
    warp_prest_N = _pretension_to_N_per_m(warp_pre, "kN/m")
    weft_prest_N = _pretension_to_N_per_m(weft_pre, "kN/m")
    mat = make_membrane_material(
        E_warp_MPa=E1, E_weft_MPa=E2, thickness_mm=t_mm,
        nu=0.34, G_MPa=50.0,
        warp_prestress_N_per_m=warp_prest_N,
        weft_prestress_N_per_m=weft_prest_N,
    )

    chosen = _pick_cable_diameter(
        edge_cable_type, edge_cable_material, edge_pre_used,
    )
    if chosen is None:
        chosen = {"A": 162.9, "E": 160000.0}
    A_m2 = float(chosen["A"]) * 1e-6
    E_Pa = float(chosen["E"]) * 1e6
    EA_N = A_m2 * E_Pa
    T_pre_user_N = edge_pre_used * 1000.0

    pullback_tensions = {}
    pullback_summary = None
    if str(attachment_type).lower() == "cable_supported":
        try:
            pullback_tensions = pullback_cable_initial_tensions(
                points=points_initial,
                triangles=triangles,
                boundary_loop=boundary_loop,
                anchors=anchors,
                segments=segments,
                material=mat,
            )
            tvals = [v for v in pullback_tensions.values() if v > 1.0]
            if tvals:
                pullback_summary = {
                    "min_N": float(min(tvals)),
                    "max_N": float(max(tvals)),
                    "mean_N": float(sum(tvals) / len(tvals)),
                    "n_edges": len(tvals),
                }
        except Exception as e:
            pullback_summary = {"error": str(e)}

    cables = []
    if str(attachment_type).lower() == "cable_supported":
        for seg in segments:
            chain = [seg["anchor_a"]] + list(seg["interior"]) + [seg["anchor_b"]]
            for k in range(len(chain) - 1):
                a = int(chain[k])
                b = int(chain[k + 1])
                key = (a, b) if a < b else (b, a)
                T_pull = pullback_tensions.get(key, None)
                if T_pull is None:
                    T_pull = pullback_tensions.get((key[1], key[0]), None)
                if T_pull is None or T_pull <= 1.0:
                    T_cable = T_pre_user_N
                else:
                    T_cable = float(T_pull)
                cables.append({
                    "a": a,
                    "b": b,
                    "T_pretension_N": T_cable,
                    "EA": EA_N,
                })

    res = solve_nonlinear_equilibrium(
        points=points_initial.copy(),
        triangles=triangles,
        fixed_indices=fixed_indices,
        reference_points=points_initial.copy(),
        membrane_material=mat,
        cables=cables,
        loads=None,
        max_iter=80,
        tol=1e-4,
    )
    coords = res["coordinates"]

    edge_cable_length_m = 0.0
    for cb in cables:
        L = float(np.linalg.norm(
            coords[int(cb["b"])] - coords[int(cb["a"])]
        ))
        edge_cable_length_m += L

    max_res = float(res.get("max_residual", 0.0))
    diagnostics = {
        "solver": "NFDM (Stage 2)",
        "residual_norm": float(res.get("residual_norm", 0.0)),
        "max_residual": max_res,
        "converged": bool(res.get("converged", False)),
        "n_iterations": int(res.get("iterations", 0)),
        "reason": str(res.get("reason", "")),
        "n_free": int(n_nodes - len(fixed_indices)),
        "n_fixed": int(len(fixed_indices)),
        "n_nodes": int(n_nodes),
        "n_edges": len(edges),
        "n_triangles": len(triangles),
        "n_anchors": len(anchors),
        "n_segments": len(seg_types),
        "n_cables": len(cables),
        "target_edge_length": float(target_len) if target_len else 0.0,
        "L_avg": float(L_avg),
        "attachment_type": str(attachment_type),
        "anchor_count": int(anchor_count),
        "mesh_spacing": float(mesh_spacing),
        "edge_cable_length_m": float(edge_cable_length_m),
        "edge_cable_type": str(edge_cable_type),
        "edge_cable_material": str(edge_cable_material),
        "edge_cable_pretension_kN": float(edge_pre_used),
        "edge_pretension_source": str(edge_pre_source),
        "edge_cable_chosen": chosen,
        "warp_prestress_N_per_m": float(warp_prest_N),
        "weft_prestress_N_per_m": float(weft_prest_N),
        "pullback_summary": pullback_summary,
        "top_displacements": [],
        "structural_connections": [],
        "cable_tensions": res.get("cable_tension", []),
        "q_path": "n/a (nfdm)",
        "L_anchor_m": float(total) / max(1.0, float(anchor_count - 1)),
        "fixed_indices": [int(i) for i in fixed_indices],
        "reactions": res.get("reactions", None),
        "variant_key": "standard_saddle",
    }

    return {
        "points": coords,
        "points_initial": points_initial,
        "edges": edges,
        "triangles": triangles,
        "fixed_indices": fixed_indices,
        "q": mesh_result["q"],
        "boundary_loop": boundary_loop,
        "anchors": anchors,
        "anchor_pos": anchor_pos,
        "segments": segments,
        "seg_types": seg_types,
        "diagnostics": diagnostics,
        "cables": cables,
    }


# =============================================================================
# CACHED WRAPPERS
# =============================================================================

def _r6(v):
    return round(float(v), 6)


@st.cache_data(show_spinner=False)
def _cached_fdm(span, apex, rise, curve_type,
                 anchor_count, mesh_spacing,
                 warp_pre, weft_pre, edge_pre,
                 attachment_type, fabric_type, fabric_grade):
    return _solve_fdm_path(
        span=span, apex=apex, rise=rise, curve_type=curve_type,
        anchor_count=anchor_count, mesh_spacing=mesh_spacing,
        warp_pre=warp_pre, weft_pre=weft_pre, edge_pre=edge_pre,
        attachment_type=attachment_type,
        fabric_type=fabric_type, fabric_grade=fabric_grade,
    )


@st.cache_data(show_spinner=False)
def _cached_nfdm(span, apex, rise, curve_type,
                  anchor_count, mesh_spacing,
                  warp_pre, weft_pre, edge_pre,
                  attachment_type,
                  edge_cable_type, edge_cable_material,
                  fabric_type, fabric_grade):
    return _solve_nfdm_path(
        span=span, apex=apex, rise=rise, curve_type=curve_type,
        anchor_count=anchor_count, mesh_spacing=mesh_spacing,
        warp_pre=warp_pre, weft_pre=weft_pre, edge_pre=edge_pre,
        attachment_type=attachment_type,
        edge_cable_type=edge_cable_type,
        edge_cable_material=edge_cable_material,
        fabric_type=fabric_type, fabric_grade=fabric_grade,
    )


# =============================================================================
# STRUCTURAL REPORT GENERATOR
# =============================================================================
#
# Consumes the built dict and the diagnostics dict, returns a report
# payload. The payload contains derived quantities only. The raw q
# array is read internally for Section 4's membrane edge forces and
# is never placed in the payload.
#
# Design forces are read from engine/member_sizing.py. Sections 3, 4,
# and 6 now carry real numbers. Utilisation and result columns remain
# "--" until the section selection layer is built.
#
# Drainage thresholds (Chief's working practice, subject to code
# override when data/codes.py is built):
#   Rain runoff:  minimum 15 degrees
#   Snow load:    minimum 28 degrees
# =============================================================================

_DRAINAGE_MIN_RAIN_DEG = 15.0
_DRAINAGE_MIN_SNOW_DEG = 28.0


def _build_structural_report(
    built,
    diag,
    span,
    apex,
    rise,
    curve_type,
    anchor_count,
    mesh_spacing,
    warp_pre,
    weft_pre,
    edge_pre,
    fabric_type,
    fabric_grade,
    attachment_type,
    snow_in_brief,
    base_condition,
    code,
):
    """
    Build the structural report payload from the FDM (Stage 1) result.
    All quantities are derived. No raw q values appear in the payload.
    """
    report = {}

    design_forces = design_forces_from_built(
        built, code=code, base_condition=base_condition,
    )

    # -------------------------------------------------------------------------
    # Section 1 - Design basis
    # -------------------------------------------------------------------------
    report["design_basis"] = {
        "structure": "Cable Supported Saddle",
        "geometry": {
            "span_m": float(span),
            "apex_m": float(apex),
            "rise_m": float(rise),
            "curve_type": str(curve_type),
            "anchor_count_per_beam": int(anchor_count),
            "mesh_spacing_m": float(mesh_spacing),
        },
        "materials": {
            "fabric_type": str(fabric_type),
            "fabric_grade": str(fabric_grade),
            "edge_cable_type": str(diag.get("edge_cable_type", "6x19")),
            "edge_cable_material": str(diag.get("edge_cable_material", "stainless")),
        },
        "prestress": {
            "warp_kN_per_m": float(warp_pre),
            "weft_kN_per_m": float(weft_pre),
            "edge_cable_pretension_kN": float(diag.get("edge_pretension_kN", 0.0)),
            "edge_cable_pretension_source": str(diag.get("edge_pretension_source", "?")),
        },
        "base_condition": str(base_condition),
        "code": str(code) if code else "MY (default)",
        "load_cases": (
            "Prestress only. Wind, snow, imposed, and seismic load "
            "cases are not included in this draft."
        ),
        "code_checks": (
            "Design forces are computed with partial factors applied "
            "(gamma_G from data/constants.py). Section selection and "
            "code checks are not performed in this draft."
        ),
    }

    # -------------------------------------------------------------------------
    # Section 2 - Form-found geometry
    # -------------------------------------------------------------------------
    coords = built["points"]
    boundary_loop = built["boundary_loop"]
    anchor_pos = built["anchor_pos"]

    anchor_rows = []
    for k in range(anchor_pos.shape[0]):
        px, py, pz = anchor_pos[k]
        anchor_rows.append({
            "index": int(k),
            "x_m": float(px),
            "y_m": float(py),
            "z_m": float(pz),
        })

    report["form_found_geometry"] = {
        "n_nodes": int(coords.shape[0]),
        "n_anchor_loops": int(anchor_pos.shape[0]),
        "anchor_rows": anchor_rows,
        "note": (
            "Boundary coordinates are the form-found anchor positions. "
            "The membrane pulls the beams inward; the anchors do not move."
        ),
    }

    # -------------------------------------------------------------------------
    # Section 3 - Reactions (now from the solver)
    # -------------------------------------------------------------------------
    reactions = diag.get("reactions", None)
    fixed_indices = diag.get("fixed_indices", None)
    reaction_rows = []
    if reactions is not None and fixed_indices is not None:
        reactions = np.asarray(reactions, dtype=float)
        for idx in fixed_indices:
            idx = int(idx)
            if idx < 0 or idx >= reactions.shape[0]:
                continue
            r = reactions[idx]
            reaction_rows.append({
                "node_index": idx,
                "x_kN": float(r[0]),
                "y_kN": float(r[1]),
                "z_kN": float(r[2]),
                "mag_kN": float(np.linalg.norm(r)),
            })

    report["reactions"] = {
        "status": "ok" if reaction_rows else "pending",
        "rows": reaction_rows,
        "model": (
            "Support reactions from the FDM solver residual at the "
            "fixed nodes. Uplift positive Z, downforce negative Z."
        ),
        "note": (
            "" if reaction_rows else
            "Support reactions are not yet available. This section will "
            "fill in when the solver returns reaction data."
        ),
    }

    # -------------------------------------------------------------------------
    # Section 4 - Member forces (from engine/member_sizing.py)
    # -------------------------------------------------------------------------
    membrane = design_forces["membrane"]
    edge_cable = design_forces["edge_cable"]
    beam = design_forces["beam"]
    tiedown = design_forces["tiedown"]

    report["member_forces"] = {
        "membrane": membrane,
        "edge_cable": edge_cable,
        "beam": beam,
        "tiedown": tiedown,
        "partial_factors": design_forces["partial_factors"],
        "note": (
            "Design forces with partial factors applied. Membrane is "
            "q x L per edge. Edge cable is the resultant along each "
            "segment. Beam is a continuous beam over all supports. "
            "Tie-down is the reaction resolved along the cable axis."
        ),
    }

    # -------------------------------------------------------------------------
    # Section 5 - Membrane stresses (pending)
    # -------------------------------------------------------------------------
    report["membrane_stresses"] = {
        "status": "pending",
        "note": (
            "Membrane stresses require the nonlinear (NFDM) solver. "
            "The FDM path does not compute stresses. This will be "
            "available when the NFDM path converges at App scale."
        ),
    }

    # -------------------------------------------------------------------------
    # Section 6 - Member schedule (from data/structures.py schema)
    # -------------------------------------------------------------------------
    schema = get_member_schema("saddle_span", "standard_saddle")
    member_rows = []

    # Design force per member group, for display.
    membrane_max_kN = float(membrane.get("max_kN", 0.0))
    edge_cable_max_kN = float(edge_cable.get("max_kN", 0.0))
    beam_max_kN_m = float(beam.get("max_moment_kN_m", 0.0))
    tiedown_max_kN = float(tiedown.get("max_kN", 0.0))

    if schema is None:
        member_rows = []
        schema_note = (
            "No member schema has been defined for this variant yet."
        )
    else:
        if schema.get("membrane_first"):
            member_rows.append({
                "label": "Membrane",
                "section": "--",
                "design_force": "%.1f kN" % membrane_max_kN,
                "utilisation": "--",
                "result": "--",
                "note": "Peak in-plane force per edge, factored.",
            })
        for row in schema.get("cables_before_beams", []):
            member_rows.append({
                "label": row["label"],
                "section": row["section"],
                "design_force": "%.1f kN" % edge_cable_max_kN,
                "utilisation": "--",
                "result": "--",
                "note": row.get("note", ""),
            })
        if schema.get("beam_expandable"):
            beam_rows = expand_beam_rows("simple")
            if len(beam_rows) == 1:
                member_rows.append({
                    "label": schema.get("beam_label_single", "Main Beam"),
                    "section": beam_rows[0]["section"],
                    "design_force": "%.1f kNm" % beam_max_kN_m,
                    "utilisation": "--",
                    "result": "--",
                    "note": "Max moment, continuous beam.",
                })
            else:
                for br in beam_rows:
                    member_rows.append({
                        "label": br["label"],
                        "section": br["section"],
                        "design_force": "--",
                        "utilisation": "--",
                        "result": "--",
                        "note": br.get("note", ""),
                    })
        for row in schema.get("extra_rows_before_cables", []):
            member_rows.append({
                "label": row["label"],
                "section": row["section"],
                "design_force": "--",
                "utilisation": "--",
                "result": "--",
                "note": row.get("note", ""),
            })
        for row in schema.get("cables_last", []):
            member_rows.append({
                "label": row["label"],
                "section": row["section"],
                "design_force": "%.1f kN" % tiedown_max_kN,
                "utilisation": "--",
                "result": "--",
                "note": row.get("note", ""),
            })
        schema_note = (
            "Design force column shows factored peak forces. Section "
            "selection and code checks require data/sections.py and a "
            "chosen design code. Neither is wired yet."
        )

    report["member_sizing"] = {
        "rows": member_rows,
        "note": schema_note,
    }

    # -------------------------------------------------------------------------
    # Section 7 - Cable sag check (pending)
    # -------------------------------------------------------------------------
    report["cable_sag"] = {
        "status": "pending",
        "note": (
            "Cable sag requires a catenary or parabolic solve of the "
            "cable under its own weight. The FDM path treats cables as "
            "force-density edges, not as sagging catenaries."
        ),
    }

    # -------------------------------------------------------------------------
    # Section 8 - Drainage check
    # -------------------------------------------------------------------------
    triangles = built["triangles"]
    slopes_deg = []
    for tri in triangles:
        ia, ib, ic = int(tri[0]), int(tri[1]), int(tri[2])
        pa = coords[ia]
        pb = coords[ib]
        pc = coords[ic]
        n_vec = np.cross(pb - pa, pc - pa)
        mag = float(np.linalg.norm(n_vec))
        if mag < 1e-12:
            continue
        nz = abs(float(n_vec[2])) / mag
        nz_clamped = max(0.0, min(1.0, nz))
        slope_rad = float(np.arcsin(nz_clamped))
        slope_deg = float(np.degrees(slope_rad))
        slopes_deg.append(slope_deg)

    threshold_deg = _DRAINAGE_MIN_SNOW_DEG if snow_in_brief else _DRAINAGE_MIN_RAIN_DEG
    n_below = sum(1 for s in slopes_deg if s < threshold_deg)

    report["membrane_gradient"] = {
        "threshold_deg": float(threshold_deg),
        "threshold_source": (
            "snow load brief (working practice: 28 deg minimum)"
            if snow_in_brief else
            "rain runoff (working practice: 15 deg minimum)"
        ),
        "n_triangles": len(slopes_deg),
        "n_below_threshold": int(n_below),
        "min_slope_deg": float(np.min(slopes_deg)) if slopes_deg else 0.0,
        "max_slope_deg": float(np.max(slopes_deg)) if slopes_deg else 0.0,
        "mean_slope_deg": float(np.mean(slopes_deg)) if slopes_deg else 0.0,
        "note": (
            "Slope is the angle of each triangle plane from horizontal. "
            "The threshold is the Chief's working practice for rain (15 deg) "
            "and snow (28 deg), subject to code override when data/codes.py "
            "is built."
        ),
    }

    # -------------------------------------------------------------------------
    # Section 9 - Bill of quantities (pending)
    # -------------------------------------------------------------------------
    report["bq"] = {
        "status": "pending",
        "edge_cable_length_m": float(diag.get("edge_cable_length_m", 0.0)),
        "note": (
            "The bill of quantities requires member lengths and weights, "
            "which require the section selection layer. The single "
            "quantity available today is the edge cable length."
        ),
    }

    return report


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def build_standard_saddle():
    span = _r6(st.session_state.get("ws_ss_span", 10.0))
    apex = _r6(st.session_state.get("ws_ss_apex", 15.0))
    rise = _r6(st.session_state.get("ws_ss_rise", 6.2))
    curve_type = str(st.session_state.get("ws_ss_curve_type", "parabolic"))
    n_intervals = int(st.session_state.get("ws_ss_tiedown_intervals", 2))
    uplift = float(st.session_state.get("ws_ss_uplift_angle", 45))
    spread = float(st.session_state.get("ws_ss_spread_angle", 30))
    warp_pre = _r6(st.session_state.get("ws_ss_warp_pretension", 2.0))
    weft_pre = _r6(st.session_state.get("ws_ss_weft_pretension", 2.0))
    edge_pre = _r6(st.session_state.get("ws_ss_edge_cable_pretension", 0.0))
    attach_type = str(st.session_state.get("ws_ss_attachment_type", "kader"))

    anchor_count = int(st.session_state.get("ws_ss_anchor_count", 8))
    mesh_spacing = _r6(st.session_state.get("ws_ss_mesh_spacing", 0.5))

    edge_cable_type = str(st.session_state.get("ws_ss_edge_cable_type", "6x19"))
    edge_cable_material = str(st.session_state.get("ws_ss_edge_cable_material", "stainless"))
    fabric_type = str(st.session_state.get("ws_ss_fabric_type", "PVDF"))
    fabric_grade = str(st.session_state.get("ws_ss_fabric_grade", "Type III"))

    if span <= 0 or apex <= 0 or rise <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Invalid geometry - check inputs",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#f39c12", size=16),
        )
        return apply_common_layout(fig, 10.0)

    # -------------------------------------------------------------------------
    # ZONE 1 - CHART AND CONTROLS
    # -------------------------------------------------------------------------

    # Solver mode selector: Owner, Studio, Beta only.
    if _is_high_tier():
        st.markdown("**Solver mode:**")
        mode_choice = st.radio(
            "Solver mode",
            options=["NFDM (Stage 2, coupled nonlinear)",
                     "FDM (Stage 1, form-found shape)"],
            index=1,
            key="ss_solver_mode",
            label_visibility="collapsed",
        )
        use_nfdm_selected = mode_choice.startswith("NFDM")
    else:
        st.info(
            "Stage 1 form-finding is active. "
            "Coupled nonlinear refinement (Stage 2) "
            "is available in higher access tiers."
        )
        use_nfdm_selected = False

    use_nfdm = (
        use_nfdm_selected
        and _is_high_tier()
        and attach_type == "cable_supported"
    )

    # Display checkboxes in a single expander.
    with st.expander("Display", expanded=False):
        cb1, cb2, cb3 = st.columns(3)
        with cb1:
            show_beams = st.checkbox("Beams", value=True, key="ss_show_beams")
        with cb2:
            show_membrane = st.checkbox("Membrane", value=True, key="ss_show_membrane")
        with cb3:
            show_anchors = st.checkbox("Anchors", value=True, key="ss_show_anchors")
        cb4, cb5, cb6 = st.columns(3)
        with cb4:
            if attach_type == "cable_supported":
                show_edge = st.checkbox("Edge cable", value=True, key="ss_show_edge")
            else:
                show_edge = st.checkbox("Kader", value=True, key="ss_show_kader")
        with cb5:
            show_tiedown = st.checkbox("Tie-downs", value=True, key="ss_show_tiedown")
        with cb6:
            show_ground = st.checkbox("Supports", value=True, key="ss_show_ground")

    # Run the solver.
    msg = st.empty()
    msg.info("Preparing design...Do not refresh or leave the page")
    try:
        if use_nfdm:
            built = _cached_nfdm(
                span, apex, rise, curve_type,
                anchor_count, mesh_spacing,
                warp_pre, weft_pre, edge_pre,
                attach_type,
                edge_cable_type, edge_cable_material,
                fabric_type, fabric_grade,
            )
        else:
            built = _cached_fdm(
                span, apex, rise, curve_type,
                anchor_count, mesh_spacing,
                warp_pre, weft_pre, edge_pre,
                attach_type, fabric_type, fabric_grade,
            )
    finally:
        msg.empty()

    coords = built["points"]
    points_initial = built["points_initial"]
    triangles = built["triangles"]
    boundary_loop = built["boundary_loop"]
    anchor_pos = built["anchor_pos"]
    diag = built["diagnostics"]

    x, y1, y2, z_beam, s, total = _build_beam_curves(
        span, apex, rise, curve_type
    )

    fig = go.Figure()

    if show_beams:
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_beam,
            mode="lines",
            line=dict(color="#FF6B6B", width=8),
            name="Beam L",
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_beam,
            mode="lines",
            line=dict(color="#FF6B6B", width=8),
            name="Beam R",
        ))

    if show_membrane:
        node_x = coords[:, 0].tolist()
        node_y = coords[:, 1].tolist()
        node_z = coords[:, 2].tolist()
        tri_i = [int(t[0]) for t in triangles]
        tri_j = [int(t[1]) for t in triangles]
        tri_k = [int(t[2]) for t in triangles]
        fig.add_trace(go.Mesh3d(
            x=node_x, y=node_y, z=node_z,
            i=tri_i, j=tri_j, k=tri_k,
            color="#4a7a9c",
            opacity=0.55,
            flatshading=True,
            name="Membrane",
            showlegend=False,
            hoverinfo="skip",
        ))

    if show_anchors:
        anchor_x = anchor_pos[:, 0].tolist()
        anchor_y = anchor_pos[:, 1].tolist()
        anchor_z = anchor_pos[:, 2].tolist()
        fig.add_trace(go.Scatter3d(
            x=anchor_x, y=anchor_y, z=anchor_z,
            mode="markers",
            marker=dict(color="#f39c12", size=5, symbol="circle"),
            name="Anchors",
            showlegend=False,
            hoverinfo="skip",
        ))

    if attach_type == "cable_supported" and show_edge:
        segments = built["segments"]
        first = True
        for seg in segments:
            chain = [seg["anchor_a"]] + list(seg["interior"]) + [seg["anchor_b"]]
            cx = [float(coords[i][0]) for i in chain]
            cy = [float(coords[i][1]) for i in chain]
            cz = [float(coords[i][2]) for i in chain]
            fig.add_trace(go.Scatter3d(
                x=cx, y=cy, z=cz,
                mode="lines+markers",
                line=dict(color="#f1c40f", width=4),
                marker=dict(color="#f1c40f", size=3),
                name="Edge cable" if first else " ",
                showlegend=first,
                hoverinfo="skip",
            ))
            first = False

    elif attach_type != "cable_supported" and show_edge:
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_beam,
            mode="lines",
            line=dict(color="#f39c12", width=2),
            showlegend=False,
            name="Kader L",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_beam,
            mode="lines",
            line=dict(color="#f39c12", width=2),
            showlegend=False,
            name="Kader R",
            hoverinfo="skip",
        ))

    if show_tiedown:
        if n_intervals == 4:
            per_beam_fractions = [0.175, 0.825]
        elif n_intervals == 8:
            per_beam_fractions = [0.175, 0.225, 0.775, 0.825]
        else:
            per_beam_fractions = [0.175, 0.825]

        for frac in per_beam_fractions:
            idx = find_index_at_arclength_fraction(s, total, frac)
            x_tie = x[idx]
            beam_z = z_beam[idx]
            for side, y_beam in ((-1, y1[idx]), (+1, y2[idx])):
                drop = beam_z if beam_z > 0 else 0.5
                horizontal = drop / math.tan(math.radians(uplift)) if uplift > 0 else drop
                x_offset = horizontal * 0.5
                y_offset = horizontal * 0.5 * math.tan(math.radians(spread))
                if x_tie < 0:
                    anchor_x_t = x_tie - x_offset
                elif x_tie > 0:
                    anchor_x_t = x_tie + x_offset
                else:
                    anchor_x_t = x_tie + x_offset
                anchor_y_t = y_beam + side * y_offset
                fig.add_trace(go.Scatter3d(
                    x=[x_tie, anchor_x_t], y=[y_beam, anchor_y_t], z=[beam_z, 0],
                    mode="lines",
                    line=dict(color="#f1c40f", width=2, dash="dot"),
                    showlegend=False, hoverinfo="skip",
                    name="Tie-down",
                ))
                fig.add_trace(go.Scatter3d(
                    x=[anchor_x_t], y=[anchor_y_t], z=[0],
                    mode="markers",
                    marker=dict(color="#f1c40f", size=5, symbol="square"),
                    showlegend=False, hoverinfo="skip",
                    name="Tie-down anchor",
                ))

    if show_ground:
        fig.add_trace(go.Scatter3d(
            x=[-span / 2.0, span / 2.0], y=[0, 0], z=[0, 0],
            mode="markers",
            marker=dict(color="#2ecc71", size=10, symbol="diamond"),
            name="Ground supports",
            showlegend=False,
        ))

    fig = apply_common_layout(fig, rise)

    # -------------------------------------------------------------------------
    # ZONE 2 - CUSTOMER DELIVERABLES (Owner, Studio, Beta only)
    # -------------------------------------------------------------------------
    #
    # The Structural Analysis Report. Derived quantities only.
    # The raw q array is read by the report generator and is not
    # placed in the payload.
    #
    # Design forces come from engine/member_sizing.py. Sections 3, 4,
    # and 6 now carry real numbers.
    #
    if _is_high_tier():
        snow_in_brief = bool(
            st.session_state.get("ws_ss_snow_in_brief", False)
        )
        base_condition = str(
            st.session_state.get("ws_ss_base_condition", "pinned")
        ).lower()

        if diag["solver"].startswith("NFDM"):
            with st.expander("Structural Analysis Report", expanded=False):
                st.info(
                    "The structural report is generated from the FDM "
                    "(Stage 1) path. Switch solver mode to FDM to view "
                    "the report."
                )
        else:
            report = _build_structural_report(
                built=built,
                diag=diag,
                span=span,
                apex=apex,
                rise=rise,
                curve_type=curve_type,
                anchor_count=anchor_count,
                mesh_spacing=mesh_spacing,
                warp_pre=warp_pre,
                weft_pre=weft_pre,
                edge_pre=edge_pre,
                fabric_type=fabric_type,
                fabric_grade=fabric_grade,
                attachment_type=attach_type,
                snow_in_brief=snow_in_brief,
                base_condition=base_condition,
                code="MY",
            )

            with st.expander("Structural Analysis Report", expanded=False):

                # Section 1 - Design basis
                st.markdown("### 1. Design basis")
                db = report["design_basis"]
                st.markdown("**Structure:** " + db["structure"])
                g = db["geometry"]
                st.markdown(
                    "- Span: %.2f m" % g["span_m"]
                    + "  |  Apex: %.2f m" % g["apex_m"]
                    + "  |  Rise: %.2f m" % g["rise_m"]
                )
                st.markdown(
                    "- Curve: " + g["curve_type"]
                    + "  |  Anchors per beam: " + str(g["anchor_count_per_beam"])
                    + "  |  Mesh spacing: %.2f m" % g["mesh_spacing_m"]
                )
                m = db["materials"]
                st.markdown(
                    "- Fabric: " + m["fabric_type"] + " / " + m["fabric_grade"]
                    + "  |  Edge cable: " + m["edge_cable_type"]
                    + " / " + m["edge_cable_material"]
                )
                p = db["prestress"]
                st.markdown(
                    "- Prestress: warp %.2f kN/m" % p["warp_kN_per_m"]
                    + "  |  weft %.2f kN/m" % p["weft_kN_per_m"]
                    + "  |  edge cable %.3f kN" % p["edge_cable_pretension_kN"]
                    + " (" + p["edge_cable_pretension_source"] + ")"
                )
                st.markdown(
                    "- Base condition: **" + db["base_condition"] + "**"
                    + "  |  Code: " + db["code"]
                )
                st.caption("**Load cases:** " + db["load_cases"])
                st.caption("**Code checks:** " + db["code_checks"])

                # Section 2 - Form-found geometry
                st.markdown("### 2. Form-found geometry")
                fg = report["form_found_geometry"]
                st.markdown(
                    "- Nodes: " + str(fg["n_nodes"])
                    + "  |  Anchor loops: " + str(fg["n_anchor_loops"])
                )
                st.caption(fg["note"])
                anchor_table = "  idx      x (m)      y (m)      z (m)\n"
                anchor_table += "-" * 44 + "\n"
                for row in fg["anchor_rows"]:
                    anchor_table += (
                        "%5d  %9.4f  %9.4f  %9.4f\n"
                        % (row["index"], row["x_m"], row["y_m"], row["z_m"])
                    )
                st.code(anchor_table, language="text")

                # Section 3 - Reactions
                st.markdown("### 3. Reactions")
                r = report["reactions"]
                if r["status"] == "ok":
                    st.caption(r["model"])
                    react_table = "  node      Fx (kN)    Fy (kN)    Fz (kN)    |F| (kN)\n"
                    react_table += "-" * 62 + "\n"
                    for row in r["rows"]:
                        react_table += (
                            "%6d  %10.3f  %10.3f  %10.3f  %10.3f\n"
                            % (row["node_index"], row["x_kN"],
                               row["y_kN"], row["z_kN"], row["mag_kN"])
                        )
                    st.code(react_table, language="text")
                else:
                    st.caption("Status: " + r["status"])
                    st.caption(r["note"])

                # Section 4 - Member forces
                st.markdown("### 4. Member forces")
                mf = report["member_forces"]
                mem = mf["membrane"]
                ec = mf["edge_cable"]
                bm = mf["beam"]
                td = mf["tiedown"]

                st.markdown("**Membrane** — " + mem["model"])
                st.markdown(
                    "- n=" + str(mem["n"])
                    + "  |  min %.1f kN" % mem["min_kN"]
                    + "  |  mean %.1f kN" % mem["mean_kN"]
                    + "  |  **max %.1f kN**" % mem["max_kN"]
                )
                st.markdown("**Edge cable** — " + ec["model"])
                st.markdown(
                    "- segments=" + str(ec["n_segments"])
                    + "  |  min %.1f kN" % ec["min_kN"]
                    + "  |  mean %.1f kN" % ec["mean_kN"]
                    + "  |  **max %.1f kN**" % ec["max_kN"]
                )
                st.markdown("**Beam** — " + bm.get("model", ""))
                if bm.get("status") == "ok":
                    st.markdown(
                        "- spans=" + str(bm.get("n_spans", 0))
                        + "  |  **max moment %.1f kNm**" % bm["max_moment_kN_m"]
                        + "  |  **max shear %.1f kN**" % bm["max_shear_kN"]
                    )
                else:
                    st.caption("Beam: " + str(bm.get("status", "")))
                st.markdown("**Tie-down** — " + td.get("model", ""))
                if td.get("status") == "ok":
                    st.markdown(
                        "- n=" + str(td.get("n", 0))
                        + "  |  min %.1f kN" % td["min_kN"]
                        + "  |  mean %.1f kN" % td["mean_kN"]
                        + "  |  **max %.1f kN**" % td["max_kN"]
                    )
                else:
                    st.caption("Tie-down: " + str(td.get("status", "")))
                pf = mf["partial_factors"]
                st.caption(
                    "Partial factors: gamma_G = %.2f, gamma_Q_wind = %.2f, "
                    "gamma_Q_snow = %.2f, gamma_M0 = %.2f, gamma_M1 = %.2f, "
                    "gamma_M2 = %.2f  (%s)"
                    % (pf["gamma_G"], pf["gamma_Q_wind"], pf["gamma_Q_snow"],
                       pf["gamma_M0"], pf["gamma_M1"], pf["gamma_M2"],
                       pf.get("code", ""))
                )
                st.caption(mf["note"])

                # Section 5 - Membrane stresses
                st.markdown("### 5. Membrane stresses")
                st.caption("Status: " + report["membrane_stresses"]["status"])
                st.caption(report["membrane_stresses"]["note"])

                # Section 6 - Member schedule
                st.markdown("### 6. Member schedule")
                ms = report["member_sizing"]
                sched_table = "  member                     section       force      util   result\n"
                sched_table += "-" * 82 + "\n"
                for row in ms["rows"]:
                    sched_table += (
                        "  %-26s %-13s %-10s %-6s %-7s\n"
                        % (row["label"], row["section"],
                           row["design_force"], row["utilisation"], row["result"])
                    )
                st.code(sched_table, language="text")
                st.caption(ms["note"])

                # Section 7 - Cable sag check
                st.markdown("### 7. Cable sag check")
                st.caption("Status: " + report["cable_sag"]["status"])
                st.caption(report["cable_sag"]["note"])

                # Section 8 - Membrane gradient check
                st.markdown("### 8. Membrane gradient check")
                mg = report["membrane_gradient"]
                st.markdown(
                    "- Threshold: %.1f deg (%s)"
                    % (mg["threshold_deg"], mg["threshold_source"])
                )
                st.markdown(
                    "- Triangles: " + str(mg["n_triangles"])
                    + "  |  below threshold: " + str(mg["n_below_threshold"])
                )
                st.markdown(
                    "- Slope min %.2f deg" % mg["min_slope_deg"]
                    + "  |  mean %.2f deg" % mg["mean_slope_deg"]
                    + "  |  max %.2f deg" % mg["max_slope_deg"]
                )
                st.caption(mg["note"])

                # Section 9 - Bill of quantities
                st.markdown("### 9. Bill of quantities")
                bq = report["bq"]
                st.caption("Status: " + bq["status"])
                st.markdown(
                    "- Edge cable length: %.3f m" % bq["edge_cable_length_m"]
                )
                st.caption(bq["note"])

    # -------------------------------------------------------------------------
    # ZONE 3 - ENGINEERING BENCH (Owner only)
    # -------------------------------------------------------------------------
    #
    # Never visible to any customer, at any price.
    # This is the microscope. The q values, the internal forces,
    # the digitised node data, the convergence reason.
    if _is_owner():
        with st.expander("Solver diagnostics", expanded=False):
            st.markdown("**Solver path:** " + str(diag["solver"]))
            st.markdown("**Access mode:** " + str(_access_mode()))

            c0, c0b, c0c = st.columns(3)
            c0.metric("Anchors/beam", diag["anchor_count"])
            c0b.metric("Mesh spacing", "%.2f" % diag["mesh_spacing"])
            c0c.metric("Loop anchors", diag["n_anchors"])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Nodes", diag["n_nodes"])
            c2.metric("Edges", diag["n_edges"])
            c3.metric("Triangles", diag["n_triangles"])
            c4.metric("Fixed", diag["n_fixed"])

            st.markdown(
                "**Edge cable pretension:** "
                + ("%.3f kN" % diag.get("edge_pretension_kN", 0.0))
                + " (" + str(diag.get("edge_pretension_source", "?")) + ")"
            )
            st.markdown(
                "**Anchor spacing L_anchor:** "
                + ("%.3f m" % diag.get("L_anchor_m", 0.0))
            )

            if diag["solver"].startswith("NFDM"):
                st.markdown("**Convergence:** " +
                            ("PASS" if diag.get("converged") else "no") +
                            " (" + str(diag.get("reason", "")) + ")")
                d1, d2, d3 = st.columns(3)
                d1.metric("Iterations", diag.get("n_iterations", 0))
                d2.metric("Residual", "%.4e" % diag.get("max_residual", 0.0))
                d3.metric("Cables", diag.get("n_cables", 0))
                st.markdown(
                    "**Membrane prestress:** warp " +
                    ("%.1f N/m" % diag.get("warp_prestress_N_per_m", 0.0)) +
                    "  |  weft " +
                    ("%.1f N/m" % diag.get("weft_prestress_N_per_m", 0.0))
                )
            else:
                d1, d2, d3 = st.columns(3)
                d1.metric("Residual", "%.4e" % diag["residual_norm"])
                d2.metric("Min tri area", "%.6e" % 0.0)
                d3.metric("Mean tri area", "%.6e" % 0.0)

            if diag["solver"].startswith("FDM"):
                st.markdown("---")
                st.markdown("**q values**")
                st.markdown(
                    "- q path: " + str(diag.get("q_path", "n/a")) +
                    "   |   warp_q: " + ("%.4f" % diag.get("warp_q", 0.0)) +
                    "   |   weft_q: " + ("%.4f" % diag.get("weft_q", 0.0)) +
                    "   |   edge_q_scalar: " + ("%.4f" % diag.get("edge_q_scalar", 0.0))
                )
                q_vals = built.get("q", None)
                edges_local = built.get("edges", None)
                if q_vals is not None and edges_local is not None:
                    n_boundary_local = int(boundary_loop.shape[0])
                    summary = _summarise_q(
                        edges_local, q_vals, n_boundary_local
                    )
                    st.markdown(
                        "- boundary: n=" + str(summary.get("boundary_n", 0)) +
                        "   min=" + ("%.4f" % summary.get("boundary_min", 0.0)) +
                        "   max=" + ("%.4f" % summary.get("boundary_max", 0.0)) +
                        "   mean=" + ("%.4f" % summary.get("boundary_mean", 0.0))
                    )
                    st.markdown(
                        "- interior: n=" + str(summary.get("interior_n", 0)) +
                        "   min=" + ("%.4f" % summary.get("interior_min", 0.0)) +
                        "   max=" + ("%.4f" % summary.get("interior_max", 0.0)) +
                        "   mean=" + ("%.4f" % summary.get("interior_mean", 0.0))
                    )
                    ratio = summary.get(
                        "ratio_mean_boundary_over_interior", None
                    )
                    if ratio is not None:
                        st.markdown(
                            "- **ratio boundary_mean / interior_mean = "
                            + ("%.4f" % ratio) + "**"
                        )

            ps = diag.get("pullback_summary", None)
            if ps is not None:
                st.markdown("**Pull-back (membrane edge force):**")
                if "error" in ps:
                    st.markdown("- error: " + ps["error"])
                else:
                    st.markdown(
                        "- Min: " + ("%.2f N" % ps["min_N"]) +
                        "  |  Max: " + ("%.2f N" % ps["max_N"]) +
                        "  |  Mean: " + ("%.2f N" % ps["mean_N"])
                    )
                    st.markdown("- Edges: " + str(ps["n_edges"]))
                    if "n_fallback_edges" in ps:
                        st.markdown("- Fallback edges: " + str(ps["n_fallback_edges"]))
                    if "note" in ps:
                        st.markdown("- note: " + ps["note"])

            if diag["attachment_type"] == "cable_supported":
                st.markdown("**Edge cable:**")
                st.markdown("- Length: " + ("%.3f m" % diag["edge_cable_length_m"]))
                if "edge_cable_chosen" in diag and diag["edge_cable_chosen"] is not None:
                    ce = diag["edge_cable_chosen"]
                    st.markdown(
                        "- System-selected diameter: " +
                        ("%.1f mm" % ce["d"]) +
                        "  |  Area: " + ("%.1f mm2" % ce["A"]) +
                        "  |  Breaking: " + ("%.2f kN" % ce["breaking_kN"])
                    )

        with st.expander("Advanced — digitised data", expanded=False):
            st.markdown("**Digitised node data**")

            q_vals = built.get("q", None)
            edges_local = built.get("edges", None)
            if q_vals is not None and edges_local is not None:
                n_boundary_local = int(boundary_loop.shape[0])
                st.markdown("**First 40 edges** (index, endpoints, is_boundary, q_value):")
                st.code(
                    _format_q_table(
                        edges_local, q_vals, n_boundary_local, n_show=40
                    ),
                    language="text",
                )

            n_boundary_local = int(boundary_loop.shape[0])
            boundary_idx = list(range(min(n_boundary_local, coords.shape[0])))

            st.markdown(
                "**Boundary nodes** — "
                + str(len(boundary_idx))
                + " rows. Columns: idx, x_init, y_init, z_init, "
                + "x_solved, y_solved, z_solved, disp"
            )
            st.code(
                _format_node_table(
                    points_initial, coords, indices=boundary_idx
                ),
                language="text",
            )

            top_idx = _top_displaced_indices(
                points_initial, coords, n_top=20
            )
            st.markdown(
                "**Top 20 displaced nodes** — sorted by displacement, "
                + "largest first"
            )
            st.code(
                _format_node_table(
                    points_initial, coords, indices=top_idx
                ),
                language="text",
            )

            st.markdown(
                "**All nodes** — "
                + str(coords.shape[0])
                + " rows. Same columns."
            )
            st.code(
                _format_node_table(
                    points_initial, coords, indices=None
                ),
                language="text",
            )

    return fig


# =============================================================================
# END OF viewers/figures/standard_saddle_mbs.py
# =============================================================================
