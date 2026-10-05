# =============================================================================
# SDSe - Standard Saddle Figure Builder (MBS version)
# =============================================================================
# Builds the 3D figure for the Standard Saddle variant.
#
# Two solver paths:
#   FDM (Stage 1)   - the shape only. Fast. All tiers.
#   NFDM (Stage 2)  - real membrane + cable coupled equilibrium.
#                     Owner, Studio, Beta only.
#
# The rule:
#   NONLINEAR_TIERS = ("owner", "studio", "beta")
#   If Cable Supported AND access_mode in NONLINEAR_TIERS:
#       run solve_nonlinear_equilibrium.
#   Else:
#       run build_mesh_triangulated (FDM).
#
# The access gate is not built yet (see TIERS.md). Until then,
# access_mode defaults to "owner" so the Chief sees the real
# engine. When the gate lands, the default becomes "free" and
# the gate sets the true mode.
#
# History:
#   2026-09-29 - Step 2C. First MBS version.
#   2026-09-30 - Step 5. Rewritten to use the triangulated engine.
#   2026-10-04 - Step 2E. Anchors and subdivision.
#   2026-10-04 - Two-path solver. NFDM for high tiers.
#   2026-10-05 - Pull-back initial guess. Spinner. Legend toggles.
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
from data.materials import CABLE_PROPERTIES, FABRIC_PROPERTIES


# =============================================================================
# TIER RULE
# =============================================================================

NONLINEAR_TIERS = ("owner", "studio", "beta")


def _access_mode():
    """Return the current access mode. Default 'owner' until the gate is built."""
    return str(st.session_state.get("access_mode", "owner")).lower()


def _has_nonlinear():
    """Return True if the current access mode has the nonlinear engine."""
    return _access_mode() in NONLINEAR_TIERS


# =============================================================================
# MATERIAL HELPERS
# =============================================================================

def _read_fabric_constants(fabric_type, fabric_grade):
    """Return (E_warp_MPa, E_weft_MPa, thickness_mm) from FABRIC_PROPERTIES."""
    try:
        rec = FABRIC_PROPERTIES[fabric_type][fabric_grade]
        E1 = float(rec.get("E_warp", 1400.0))
        E2 = float(rec.get("E_weft", 1400.0))
        t = float(rec.get("t_mm", 1.02))
    except Exception:
        E1, E2, t = 1400.0, 1400.0, 1.02
    return E1, E2, t


def _pretension_to_N_per_m(value, recipe_units):
    """Convert the session value to N/m."""
    v = max(0.0, float(value))
    if recipe_units == "daN/5cm":
        return v * 200.0
    return v * 1000.0


def _pick_cable_diameter(cable_type, material, pretension_kN,
                          safety_factor=5.0):
    """Return the smallest cable whose breaking load exceeds
    pretension * safety_factor. Returns a dict or None."""
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


def _pullback_to_edge_q_dict(tensions, points):
    """
    Convert a pull-back tension dict (keyed by (i, j) mesh
    node pairs, values in N) into a per-edge q dict for the
    boundary. q = T / L.

    Returns dict keyed by (i, j) sorted pairs with q values
    in N/m.
    """
    q_dict = {}
    for key, T in tensions.items():
        i, j = int(key[0]), int(key[1])
        try:
            L = float(np.linalg.norm(points[j] - points[i]))
        except Exception:
            continue
        if L < 1e-9:
            continue
        q_dict[(i, j) if i < j else (j, i)] = float(T) / L
    return q_dict


# =============================================================================
# BOUNDARY LOOP
# =============================================================================

def _build_boundary_loop(x, z_beam, y1, y2, span, anchor_count,
                          mesh_spacing, attachment_type):
    """
    Build the closed boundary loop, the anchor indices, and
    the segment types for the triangulated engine.
    """
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
        interior_local = []
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
                seg_interior = []
                for j in range(1, sub + 1):
                    frac = float(j) / float(sub + 1)
                    tm = a0 + (a1 - a0) * frac
                    mx = float(np.interp(tm, s, x))
                    mz = float(np.interp(tm, s, z_beam))
                    my = float(np.interp(tm, s, y_curve))
                    seg_interior.append(len(pts))
                    pts.append((mx, my, mz))
                interior_local.append((k, seg_interior))
        if reverse:
            n = len(pts)
            rev_pts = [pts[n - 1 - i] for i in range(n)]
            rev_anchors = [n - 1 - a for a in anchors_local]
            rev_interior = []
            for k, lst in interior_local:
                rev_interior.append((k, [n - 1 - i for i in lst]))
            return rev_pts, rev_anchors, rev_interior
        return pts, anchors_local, interior_local

    beam_L_pts, beam_L_anchors, beam_L_interior = _beam_points(y1, reverse=False)
    beam_R_pts, beam_R_anchors, beam_R_interior = _beam_points(y2, reverse=True)

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


# =============================================================================
# FDM PATH (Stage 1)
# =============================================================================

def _build_saddle_fdm(span, apex, rise, curve_type,
                       anchor_count, mesh_spacing,
                       warp_pretension, weft_pretension,
                       edge_cable_pretension,
                       attachment_type,
                       warp_prest_N_per_m, weft_prest_N_per_m,
                       fabric_type, fabric_grade):
    """
    FDM path. Uses the triangulated engine's internal FDM.
    Computes the pull-back, converts to per-edge q values,
    and passes as a dict so the FDM mesh reflects the
    physical cable tensions.
    """
    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)
    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    boundary_loop, anchors, seg_types, anchor_pos, segments = (
        _build_boundary_loop(
            x, z_beam, y1, y2, span, anchor_count, mesh_spacing,
            attachment_type,
        )
    )

    target_len = float(mesh_spacing) if mesh_spacing and mesh_spacing > 0 else None

    # --- Force densities. Ratio-anchored.
    n = boundary_loop.shape[0]
    total_len = 0.0
    for i in range(n):
        p0 = boundary_loop[i]
        p1 = boundary_loop[(i + 1) % n]
        total_len += float(np.linalg.norm(p1 - p0))
    L_avg = total_len / float(n) if n > 0 else 1.0
    if L_avg < 1e-9:
        L_avg = 1.0

    baseline_kN_per_m = 2.0
    ratio_limit = 4.0
    warp_input = max(0.1, float(warp_pretension))
    weft_input = max(0.1, float(weft_pretension))
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
    edge_q_scalar = max(0.1, float(edge_cable_pretension)) * 1000.0 / L_avg

    # --- First mesh build: use the uniform edge_q. We get
    # points_initial and topology. Then we compute the
    # pull-back and rebuild the FDM q values per edge.
    mesh_pre = build_mesh_triangulated(
        boundary_loop=boundary_loop,
        anchor_indices=anchors,
        segment_types=seg_types,
        target_edge_length=target_len,
        plan_plane=None,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q_scalar,
    )

    points_initial = mesh_pre["points_initial"]
    triangles = mesh_pre["triangles"]
    edges = mesh_pre["edges"]
    fixed_indices = mesh_pre["fixed_indices"]

    # --- Membrane material for the pull-back computation.
    E1, E2, t_mm = _read_fabric_constants(fabric_type, fabric_grade)
    mat = make_membrane_material(
        E_warp_MPa=E1, E_weft_MPa=E2, thickness_mm=t_mm,
        nu=0.34, G_MPa=50.0,
        warp_prestress_N_per_m=warp_prest_N_per_m,
        weft_prestress_N_per_m=weft_prest_N_per_m,
    )

    # --- Compute pull-back. Only in Cable Supported mode.
    edge_q_for_engine = edge_q_scalar
    pullback_summary = None
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
            q_dict = _pullback_to_edge_q_dict(tensions, points_initial)
            if q_dict:
                edge_q_for_engine = q_dict
                # Summary for diagnostics.
                tvals = list(tensions.values())
                tvals = [v for v in tvals if v > 0.0]
                if tvals:
                    pullback_summary = {
                        "min_N": float(min(tvals)),
                        "max_N": float(max(tvals)),
                        "mean_N": float(sum(tvals) / len(tvals)),
                        "n_edges": len(tvals),
                    }
        except Exception as e:
            pullback_summary = {"error": str(e)}

    # --- Final mesh build with the per-edge q dict.
    result = build_mesh_triangulated(
        boundary_loop=boundary_loop,
        anchor_indices=anchors,
        segment_types=seg_types,
        target_edge_length=target_len,
        plan_plane=None,
        warp_q=warp_q,
        weft_q=weft_q,
        edge_q=edge_q_for_engine,
    )

    coords = result["points"]
    points_initial = result["points_initial"]
    edges = result["edges"]
    triangles = result["triangles"]
    fixed_indices = result["fixed_indices"]
    q = result["q"]
    diag = result["diagnostics"]

    edge_cable_length_m = 0.0
    if str(attachment_type).lower() == "cable_supported":
        n_a = len(anchors)
        for k in range(n_a):
            a = anchor_pos[k]
            b = anchor_pos[(k + 1) % n_a]
            edge_cable_length_m += float(np.linalg.norm(b - a))

    diagnostics = {
        "solver": "FDM (Stage 1)",
        "residual_norm": float(diag.get("residual_norm", 0.0)),
        "n_free": int(diag.get("n_free", 0)),
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
        "top_displacements": [],
        "structural_connections": [],
    }

    return {
        "points": coords,
        "points_initial": points_initial,
        "edges": edges,
        "triangles": triangles,
        "fixed_indices": fixed_indices,
        "q": q,
        "boundary_loop": boundary_loop,
        "anchors": anchors,
        "anchor_pos": anchor_pos,
        "segments": segments,
        "seg_types": seg_types,
        "diagnostics": diagnostics,
    }


# =============================================================================
# NFDM PATH (Stage 2)
# =============================================================================

def _build_saddle_nfdm(span, apex, rise, curve_type,
                       anchor_count, mesh_spacing,
                       attachment_type,
                       warp_prest_N_per_m, weft_prest_N_per_m,
                       edge_cable_type, edge_cable_material,
                       edge_cable_pretension_kN,
                       fabric_type, fabric_grade):
    """
    Nonlinear path. Real membrane. Real cables. Coupled solve.
    Uses the pull-back tensions as the per-cable initial
    pretension. Newton converges faster.
    """
    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)
    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    boundary_loop, anchors, seg_types, anchor_pos, segments = (
        _build_boundary_loop(
            x, z_beam, y1, y2, span, anchor_count, mesh_spacing,
            attachment_type,
        )
    )

    target_len = float(mesh_spacing) if mesh_spacing and mesh_spacing > 0 else None

    # --- Topology from FDM.
    n = boundary_loop.shape[0]
    total_len = 0.0
    for i in range(n):
        p0 = boundary_loop[i]
        p1 = boundary_loop[(i + 1) % n]
        total_len += float(np.linalg.norm(p1 - p0))
    L_avg = total_len / float(n) if n > 0 else 1.0
    if L_avg < 1e-9:
        L_avg = 1.0

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

    # --- Membrane material.
    E1, E2, t_mm = _read_fabric_constants(fabric_type, fabric_grade)
    mat = make_membrane_material(
        E_warp_MPa=E1, E_weft_MPa=E2, thickness_mm=t_mm,
        nu=0.34, G_MPa=50.0,
        warp_prestress_N_per_m=warp_prest_N_per_m,
        weft_prestress_N_per_m=weft_prest_N_per_m,
    )

    # --- Cable properties.
    chosen = _pick_cable_diameter(
        edge_cable_type, edge_cable_material,
        float(edge_cable_pretension_kN),
    )
    if chosen is None:
        chosen = {"A": 162.9, "E": 160000.0}
    A_m2 = float(chosen["A"]) * 1e-6
    E_Pa = float(chosen["E"]) * 1e6
    EA_N = A_m2 * E_Pa
    T_pre_user_N = float(edge_cable_pretension_kN) * 1000.0

    # --- Pull-back to get initial per-cable tensions.
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
            tvals = [v for v in pullback_tensions.values() if v > 0.0]
            if tvals:
                pullback_summary = {
                    "min_N": float(min(tvals)),
                    "max_N": float(max(tvals)),
                    "mean_N": float(sum(tvals) / len(tvals)),
                    "n_edges": len(tvals),
                }
        except Exception as e:
            pullback_summary = {"error": str(e)}

    # --- Build cables. Use pull-back per edge, or user's
    # pretension as a fallback.
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
                if T_pull is None or T_pull <= 0.0:
                    T_cable = T_pre_user_N
                else:
                    T_cable = float(T_pull)
                cables.append({
                    "a": a,
                    "b": b,
                    "T_pretension_N": T_cable,
                    "EA": EA_N,
                })

    # --- Nonlinear solve with pull-back pretensions.
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
        "edge_cable_pretension_kN": float(edge_cable_pretension_kN),
        "edge_cable_chosen": chosen,
        "warp_prestress_N_per_m": float(warp_prest_N_per_m),
        "weft_prestress_N_per_m": float(weft_prest_N_per_m),
        "pullback_summary": pullback_summary,
        "top_displacements": [],
        "structural_connections": [],
        "cable_tensions": res.get("cable_tension", []),
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
# PUBLIC FUNCTION
# =============================================================================

def build_standard_saddle():
    """Standard Saddle viewer entry point."""
    span = float(st.session_state.get("ws_ss_span", 10.0))
    apex = float(st.session_state.get("ws_ss_apex", 15.0))
    rise = float(st.session_state.get("ws_ss_rise", 6.2))
    curve_type = st.session_state.get("ws_ss_curve_type", "parabolic")
    n_intervals = int(st.session_state.get("ws_ss_tiedown_intervals", 2))
    uplift = float(st.session_state.get("ws_ss_uplift_angle", 45))
    spread = float(st.session_state.get("ws_ss_spread_angle", 30))
    warp_pre = float(st.session_state.get("ws_ss_warp_pretension", 2.0))
    weft_pre = float(st.session_state.get("ws_ss_weft_pretension", 2.0))
    edge_pre = float(st.session_state.get("ws_ss_edge_cable_pretension", 5.0))
    attach_type = str(st.session_state.get("ws_ss_attachment_type", "kader"))

    anchor_count = int(st.session_state.get("ws_ss_anchor_count", 8))
    mesh_spacing = float(st.session_state.get("ws_ss_mesh_spacing", 0.5))

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

    use_nfdm = (_has_nonlinear() and attach_type == "cable_supported")

    with st.spinner("Preparing your design..."):
        if use_nfdm:
            warp_prest_N = _pretension_to_N_per_m(warp_pre, "kN/m")
            weft_prest_N = _pretension_to_N_per_m(weft_pre, "kN/m")
            built = _build_saddle_nfdm(
                span=span, apex=apex, rise=rise, curve_type=curve_type,
                anchor_count=anchor_count, mesh_spacing=mesh_spacing,
                attachment_type=attach_type,
                warp_prest_N_per_m=warp_prest_N,
                weft_prest_N_per_m=weft_prest_N,
                edge_cable_type=edge_cable_type,
                edge_cable_material=edge_cable_material,
                edge_cable_pretension_kN=edge_pre,
                fabric_type=fabric_type, fabric_grade=fabric_grade,
            )
        else:
            warp_prest_N = _pretension_to_N_per_m(warp_pre, "kN/m")
            weft_prest_N = _pretension_to_N_per_m(weft_pre, "kN/m")
            built = _build_saddle_fdm(
                span=span, apex=apex, rise=rise, curve_type=curve_type,
                anchor_count=anchor_count, mesh_spacing=mesh_spacing,
                warp_pretension=warp_pre, weft_pretension=weft_pre,
                edge_cable_pretension=edge_pre,
                attachment_type=attach_type,
                warp_prest_N_per_m=warp_prest_N,
                weft_prest_N_per_m=weft_prest_N,
                fabric_type=fabric_type, fabric_grade=fabric_grade,
            )

    coords = built["points"]
    points_initial = built["points_initial"]
    triangles = built["triangles"]
    boundary_loop = built["boundary_loop"]
    anchor_pos = built["anchor_pos"]
    diag = built["diagnostics"]

    # --- Beam curves for drawing.
    n_pts = 200
    x = np.linspace(-span / 2.0, span / 2.0, n_pts)
    z_beam = beam_curve(x, span, rise, curve_type)
    s, total = arclength_parametrisation(x, z_beam)
    base_width = apex * 0.5
    y1 = -base_width * (1.0 - (2.0 * x / span) ** 2)
    y2 = base_width * (1.0 - (2.0 * x / span) ** 2)

    fig = go.Figure()

    # --- Beams. Legend entry "Beams".
    fig.add_trace(go.Scatter3d(
        x=x, y=y1, z=z_beam,
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        name="Beams",
        showlegend=True,
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=y2, z=z_beam,
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        name="Beam R",
        showlegend=False,
    ))

    # --- Membrane. Toggleable.
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
        showlegend=True,
        hoverinfo="skip",
    ))

    # --- Anchors. Toggleable.
    anchor_x = anchor_pos[:, 0].tolist()
    anchor_y = anchor_pos[:, 1].tolist()
    anchor_z = anchor_pos[:, 2].tolist()

    fig.add_trace(go.Scatter3d(
        x=anchor_x, y=anchor_y, z=anchor_z,
        mode="markers",
        marker=dict(color="#f39c12", size=5, symbol="circle"),
        name="Anchors",
        showlegend=True,
        hoverinfo="skip",
    ))

    # --- Edge cable or Kader track. Toggleable.
    if attach_type == "cable_supported":
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
                name="Edge cable" if first else "Edge cable ",
                showlegend=first,
                hoverinfo="skip",
            ))
            first = False
    else:
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_beam,
            mode="lines",
            line=dict(color="#f39c12", width=2),
            showlegend=True,
            name="Kader track",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_beam,
            mode="lines",
            line=dict(color="#f39c12", width=2),
            showlegend=False,
            name="Kader track R",
            hoverinfo="skip",
        ))

    # --- Tie-downs. One legend entry, grouped.
    if n_intervals == 4:
        per_beam_fractions = [0.175, 0.825]
    elif n_intervals == 8:
        per_beam_fractions = [0.175, 0.225, 0.775, 0.825]
    else:
        per_beam_fractions = [0.175, 0.825]

    td_first = True
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
                name="Tie-down cables" if td_first else "Tie-down cables ",
                showlegend=td_first,
                hoverinfo="skip",
            ))
            td_first = False
            fig.add_trace(go.Scatter3d(
                x=[anchor_x_t], y=[anchor_y_t], z=[0],
                mode="markers",
                marker=dict(color="#f1c40f", size=5, symbol="square"),
                showlegend=False,
                name="Tie-down anchors",
                hoverinfo="skip",
            ))

    # --- Ground supports. Toggleable.
    fig.add_trace(go.Scatter3d(
        x=[-span / 2.0, span / 2.0], y=[0, 0], z=[0, 0],
        mode="markers",
        marker=dict(color="#2ecc71", size=10, symbol="diamond"),
        name="Ground supports",
        showlegend=True,
    ))

    fig = apply_common_layout(fig, rise)

    # --- Diagnostics expander.
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

        # --- Pull-back summary.
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

    return fig


# =============================================================================
# END OF viewers/figures/standard_saddle_mbs.py
#
# This file has two solver paths:
#   FDM  (Stage 1) - all tiers
#   NFDM (Stage 2) - owner, studio, beta
#
# The rule lives in NONLINEAR_TIERS at the top of the file.
#
# Files untouched by this rewrite:
#   engine/form_finding.py
#   engine/mesh_triangulated.py
#   engine/mesh_triangulated_test.py
#   engine/nonlinear_equilibrium.py
# =============================================================================
