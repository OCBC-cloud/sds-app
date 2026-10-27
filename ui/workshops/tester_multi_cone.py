"""Multi-Cone Roof — Lab test page.

Two load cases (uplift, downforce) → membrane analysis + steel sizing.
Dead load is captured implicitly (frame self-weight is handled by the sizer).
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm
from engine.SDSe_mesh_builder import (
    SDSe_mesh_rings,
    SDSe_blend_q_per_edge,
)
from engine.nonlinear_equilibrium_newton_seed import (
    make_membrane_material,
    solve_nonlinear_equilibrium,
)
from engine.load_generator import generate_uls_loads
from engine.connection_design import (
    design_baseplate_and_foundation,
    design_corner_plate,
)
from engine.steel_frame_sizer import size_steel_frame
from data.materials import CABLE_PROPERTIES, STEEL_MATERIALS, FABRIC_PROPERTIES
from data.sections import SECTION_PROPERTIES
from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
)

RIB_SEGMENTS = 80
COL_MEMBRANE = "#4a7a9c"
COL_RING_EDGE = "#ffd166"
COL_PRIMARY = "#FF6B6B"
COL_RIB = "#e07b39"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"

GRAVITY = 9.81
MEMBRANE_DEAD_LOAD_KG_M2 = 1.102


def _select_edge_cable(actual_max_tension_N, safety_factor=2.0):
    design_load_N = actual_max_tension_N * safety_factor
    candidates = []
    for family_name, family in CABLE_PROPERTIES.items():
        if family_name == "default":
            continue
        for size, props in family.items():
            if size == "default":
                continue
            if not props.get("A") or not props.get("f_u"):
                continue
            breaking_N = props["A"] * props["f_u"]
            if breaking_N >= design_load_N:
                A_mm2 = props["A"]
                E_MPa = props.get("E", 160000)
                EA_N = A_mm2 * 1e-6 * E_MPa * 1e6
                d_mm = props.get("d", math.sqrt(4 * A_mm2 / math.pi))
                candidates.append((A_mm2, "%s %s" % (family_name, size), A_mm2, E_MPa, EA_N, d_mm))
    if candidates:
        candidates.sort(key=lambda c: c[0])
        _, name, A_mm2, E_MPa, EA_N, d_mm = candidates[0]
        return (name, A_mm2, E_MPa, EA_N, d_mm)
    return ("Fallback 10mm strand", 63.0, 160000, 10e9, 10.0)


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


def _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height, tip_x):
    plus, minus = [], []
    for i, xr in enumerate(rib_x):
        y_at = _rib_arch_y_at_eave(float(rib_peak_z[i]), float(rib_half_width[i]), eave_height)
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
        a = anchors[i]; b = anchors[(i + 1) % n_a]
        anchor_idx.append(len(loop))
        for k in range(subdivisions):
            f = k / float(subdivisions)
            loop.append(a + (b - a) * f)
    return np.asarray(loop, dtype=float), anchor_idx


def _cone_arc_positions(n_cones, spacing, total):
    if n_cones < 1:
        raise ValueError("Number of cones must be at least 1.")
    mid = total / 2.0
    if n_cones % 2 == 1:
        half = (n_cones - 1) // 2
        ks = [0]
        for i in range(1, half + 1):
            ks.append(+i); ks.append(-i)
    else:
        half = n_cones // 2
        ks = []
        for i in range(half):
            k = i + 0.5
            ks.append(+k); ks.append(-k)
    positions = [mid + k * spacing for k in ks]
    for p in positions:
        if p < 0.0 or p > total:
            raise ValueError("Ring position %.3f m falls outside the primary span of %.3f m." % (p, total))
    return sorted(positions)


def _build_member_schedule(built, coords, ring_x_positions, anchor_idx, edge_q_scalar, warp_q, weft_q, cable_name, cable_A_mm2, sections, eave_height, span, mid_width, ring_diameter):
    members = []
    ring_indices = built["ring_indices"]; centre_indices = built["centre_indices"]
    beam_top_indices = built["beam_top_indices"]; triangles = built["triangles"]; n_perimeter = built["n_perimeter"]
    members.append({"member_id": "Primary_Beam_Main", "member_type": "primary_beam", "length_m": float(span * 1.2), "section": sections.get("primary", "?"), "material": "S355", "role": "Main arched beam"})
    for i in range(3):
        members.append({"member_id": "Rib_Beam_%d" % (i+1), "member_type": "rib_beam", "length_m": float(mid_width * 1.5), "section": sections.get("rib", "?"), "material": "S355", "role": "Secondary arched beam"})
    for k in range(len(ring_indices)):
        idx_list = ring_indices[k]; n_poly = len(idx_list)
        ring_length = sum(float(np.linalg.norm(coords[int(idx_list[(i+1)%n_poly])] - coords[int(idx_list[i])])) for i in range(n_poly))
        members.append({"member_id": "Ring_%d_Ring_Beam" % (k+1), "member_type": "ring_beam", "length_m": float(ring_length), "section": sections.get("ring", "?"), "material": "S355", "role": "closed ring beam"})
        centre_i = int(centre_indices[k]); beam_i = int(beam_top_indices[k])
        L = float(np.linalg.norm(coords[beam_i] - coords[centre_i]))
        members.append({"member_id": "Ring_%d_Drop_Member" % (k+1), "member_type": "drop_member", "length_m": L, "section": sections.get("drop", "?"), "material": "S355", "role": "vertical drop"})
    total_cable_length = sum(float(np.linalg.norm(coords[(i+1)%n_perimeter] - coords[i])) for i in range(n_perimeter))
    members.append({"member_id": "Edge_Cable", "member_type": "cable", "length_m": total_cable_length, "section": cable_name, "material": "A=%.1f mm2" % cable_A_mm2, "role": "perimeter edge cable"})
    for idx, (a, b, c) in enumerate(triangles):
        pa, pb, pc = coords[a], coords[b], coords[c]
        mean_edge = (float(np.linalg.norm(pb - pa)) + float(np.linalg.norm(pc - pb)) + float(np.linalg.norm(pa - pc))) / 3.0
        members.append({"member_id": "Membrane_Panel_%04d" % (idx+1), "member_type": "membrane", "length_m": mean_edge, "section": "FABRIC", "material": "PVDF Type III", "role": "fabric panel"})
    return members


def _format_member_table(members):
    lines = []
    header = "%-26s  %-18s  %-9s  %-20s  %-20s  %s" % ("member_id", "member_type", "length_m", "section", "material", "role")
    lines.append(header); lines.append("-" * len(header))
    for m in members:
        lines.append("%-26s  %-18s  %-9.4f  %-20s  %-20s  %s" % (m["member_id"], m["member_type"], m["length_m"], str(m["section"])[:20], str(m["material"])[:20], m["role"]))
    return "\n".join(lines)


def _compute_fabric_utilization(dr_result, fabric_name, fabric_family):
    if not dr_result or "membrane_stress" not in dr_result:
        return None
    max_principal_N_m = 0.0
    for ms in dr_result["membrane_stress"]:
        sigma = ms.get("sigma", None)
        if sigma is None: continue
        s_xx = float(sigma[0, 0]); s_yy = float(sigma[1, 1]); s_xy = float(sigma[0, 1])
        mean = 0.5 * (s_xx + s_yy); diff = 0.5 * (s_xx - s_yy); radius = math.sqrt(diff**2 + s_xy**2)
        principal = mean + radius
        if principal > max_principal_N_m: max_principal_N_m = principal
    family = FABRIC_PROPERTIES.get(fabric_family, {}); fabric = family.get(fabric_name, {})
    f_u_warp = fabric.get("f_u_warp", None); f_u_weft = fabric.get("f_u_weft", None)
    if not f_u_warp or not f_u_weft: return None
    f_u_min_kN_m = min(float(f_u_warp), float(f_u_weft))
    util = (max_principal_N_m / 1000.0) / f_u_min_kN_m if f_u_min_kN_m > 0 else 999.0
    return {"fabric": fabric_name, "family": fabric_family, "f_u_min_kN_m": f_u_min_kN_m, "max_stress_kN_m": max_principal_N_m / 1000.0, "utilization": util}


def render_tester_multi_cone():
    bcol1, bcol2, bcol3 = st.columns([1, 1, 3])
    with bcol1:
        if st.button("← Back to Lab", key="mc_back_lab", use_container_width=True):
            st.session_state.page = "lab"; st.rerun()
    with bcol2:
        if st.button("← Back to Landing", key="mc_back_landing", use_container_width=True):
            st.session_state.page = "landing"; st.rerun()

    st.markdown("<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2><p style='color:#a8b8c8;margin-top:0;'>1. Find Form (FDM). 2. Two load cases → sized for worst.</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: span = st.number_input("Primary span (m)", 6.0, 60.0, 10.0, 0.5, key="mc_span")
    with c2: apex = st.number_input("Primary apex (m)", 1.0, 30.0, 6.0, 0.5, key="mc_apex")
    c1, c2 = st.columns(2)
    with c1: mid_width = st.number_input("Mid-span width (m)", 6.0, 60.0, 10.0, 0.5, key="mc_width")
    with c2: eave_height = st.number_input("Eave height (m)", 0.5, 10.0, 2.8, 0.1, key="mc_eave")
    c1, c2 = st.columns(2)
    with c1: ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 1.0, 0.1, key="mc_rd")
    with c2: curve_type = st.selectbox("Curve type", ["parabolic", "circular", "catenary"], index=0, key="mc_curve")
    c1, c2 = st.columns(2)
    with c1: secondary_count = int(st.number_input("Secondary count", 2, 20, 4, 1, key="mc_nribs"))
    with c2: optional_ends = st.toggle("Optional ends", value=False, key="mc_optends")
    subdivisions = int(st.number_input("Subdivisions per edge", 5, 25, 5, 1, key="mc_subdiv"))
    c1, c2 = st.columns(2)
    with c1: number_of_cones = int(st.number_input("Number of cones", 1, 20, 1, 1, key="mc_ncones"))
    with c2: ring_spacing = st.number_input("Distance between adjacent cones (m, along beam)", 0.5, 10.0, 5.0, 0.1, key="mc_spacing")
    ring_clearance = st.number_input("Ring clearance below beam (m)", 0.1, 5.0, 1.0, 0.1, key="mc_clr")

    st.markdown("### Fabric Selection")
    fabric_families = [k for k in FABRIC_PROPERTIES.keys() if k != "default"]
    c1, c2 = st.columns(2)
    with c1: fabric_family = st.selectbox("Fabric Family", fabric_families, index=fabric_families.index("PVDF") if "PVDF" in fabric_families else 0, key="mc_fabric_family")
    with c2:
        fabric_names = [k for k in FABRIC_PROPERTIES.get(fabric_family, {}).keys() if k != "default"]
        fabric_name = st.selectbox("Fabric Type", fabric_names, index=0, key="mc_fabric_name")

    st.markdown("### Form Finding Inputs (c-values)")
    c1, c2, c3 = st.columns(3)
    with c1: warp_c = st.number_input("Warp c", 0.1, 10.0, 2.0, 0.1, key="mc_warp_c")
    with c2: weft_c = st.number_input("Weft c", 0.1, 10.0, 2.0, 0.1, key="mc_weft_c")
    with c3: cable_c = st.number_input("Cable c", 0.1, 50.0, 10.0, 0.5, key="mc_cable_c")

    st.markdown("### Environmental Loads & Design Philosophy")
    c1, c2 = st.columns(2)
    with c1: code_choice = st.selectbox("Building Code", ["MS 1553", "ASCE 7", "EN 1991"], index=0, key="mc_code")
    with c2: design_philosophy = st.selectbox("Design Philosophy", ["Serviceability (Unfactored)", "Ultimate Limit State (Factored)"], index=1, key="mc_design_philosophy")
    c1, c2 = st.columns(2)
    with c1: wind_speed = st.number_input("Wind Speed (m/s)", 0.0, 80.0, 33.5, 1.0, key="mc_wind_speed")
    with c2: snow_depth = st.number_input("Snow Depth (m)", 0.0, 2.0, 0.0, 0.1, key="mc_snow_depth")
    payload_kg = st.number_input("Payload at apex (kg)", 0.0, 1000.0, 0.0, 10.0, key="mc_payload")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1: btn_fdm = st.button("1. Find Form (FDM)", use_container_width=True)
    with col_btn2: btn_analysis = st.button("2. Structural Analysis & Steel Sizing", use_container_width=True)

    if btn_fdm or "fdm_results" not in st.session_state:
        xp = np.linspace(-span / 2.0, span / 2.0, 200)
        zp = beam_curve(xp, span, apex, curve_type)
        s_p, total_p = arclength_parametrisation(xp, zp)
        rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
        rib_peak_z = np.interp(rib_x, xp, zp)
        rib_half_width = np.array([_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float)
        try:
            s_rings = _cone_arc_positions(number_of_cones, ring_spacing, total_p)
            ring_specs = []
            for s_val in s_rings:
                x_val = float(np.interp(s_val, s_p, xp)); bz_val = float(np.interp(s_val, s_p, zp))
                rz_val = bz_val - float(ring_clearance)
                ring_specs.append({"cx": x_val, "cy": 0.0, "cz": rz_val, "r": float(ring_diameter) / 2.0, "beam_z": bz_val})
        except ValueError as e:
            st.error("Placement refused: " + str(e)); return
        tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
        anchors = _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height, tip_x)
        perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
        bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
        L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
        target_len = max(L_avg, 1e-6)
        built = SDSe_mesh_rings(perimeter_loop=perimeter_loop, anchor_idx=anchor_idx, ring_specs=ring_specs, eave_height=eave_height, target_len=target_len)
        pts = built["points"]; edges = built["edges"]; boundary_edge_set = built["boundary_edges"]
        tris = built["triangles"]; fixed = built["fixed_indices"]
        warp_q = max(float(warp_c), 0.1) * 1000.0
        weft_q = max(float(weft_c), 0.1) * 1000.0
        edge_q_scalar = max(float(cable_c), 0.1) * 1000.0
        pts_2d = pts[:, :2]
        q_interior = SDSe_blend_q_per_edge(edges, pts_2d, np.array([1.0, 0.0]), warp_q, weft_q)
        q = np.empty(len(edges), dtype=float)
        for k, (i, j) in enumerate(edges):
            key = (i, j) if i < j else (j, i)
            q[k] = edge_q_scalar if key in boundary_edge_set else q_interior[k]
        try:
            fdm = solve_fdm(pts, edges, fixed, q)
            coords_fdm = fdm["coordinates"]; residual_fdm = float(fdm["residual_norm"]); solve_ok = True; solve_err = ""
        except Exception as e:
            coords_fdm = pts.copy(); residual_fdm = float("nan"); solve_ok = False; solve_err = str(e)
        max_edge_tension_N = edge_q_scalar * L_avg
        fdm["max_edge_tension_N"] = max_edge_tension_N
        st.session_state["fdm_results"] = {
            "built": built, "pts": pts, "edges": edges, "tris": tris, "fixed": fixed,
            "coords_fdm": coords_fdm, "fdm": fdm,
            "residual_fdm": residual_fdm, "solve_ok": solve_ok, "solve_err": solve_err,
            "warp_q": warp_q, "weft_q": weft_q, "edge_q_scalar": edge_q_scalar,
            "span": span, "mid_width": mid_width, "apex": apex, "L_avg": L_avg,
            "anchor_idx": anchor_idx, "x_rings": [np.interp(s, s_p, xp) for s in s_rings],
            "rib_x": rib_x, "rib_peak_z": rib_peak_z, "rib_half_width": rib_half_width,
            "xp": xp, "zp": zp, "eave_height": eave_height, "ring_diameter": ring_diameter,
            "warp_c": warp_c, "weft_c": weft_c, "cable_c": cable_c,
        }

    data = st.session_state.get("fdm_results")
    if not data: return
    coords_to_draw = data["coords_fdm"]

    if btn_analysis:
        with st.spinner("Running two load cases..."):
            cable_name, cable_A_mm2, cable_E_MPa, EA_cable, cable_d_mm = _select_edge_cable(
                data["fdm"]["max_edge_tension_N"], safety_factor=2.0)
            cables = []
            n_a = len(data["anchor_idx"]); pts = data["pts"]; coords_fdm = data["coords_fdm"]
            # --- FIXED CABLE L0: pretension-based, not slack-based ---
            for k in range(n_a):
                a_idx = data["anchor_idx"][k]; b_idx = data["anchor_idx"][(k + 1) % n_a]
                chain = [int(a_idx)]; i_cur = (a_idx + 1) % pts.shape[0]; b_int = int(b_idx); safety = 0
                while i_cur != b_int and safety < pts.shape[0]:
                    chain.append(int(i_cur)); i_cur = (i_cur + 1) % pts.shape[0]; safety += 1
                chain.append(int(b_int))
                for m in range(len(chain) - 1):
                    ia = chain[m]; ib = chain[m + 1]
                    L_ref = float(np.linalg.norm(coords_fdm[ib] - coords_fdm[ia]))
                    if L_ref < 1e-9:
                        continue
                    T_edge = data["edge_q_scalar"] * L_ref
                    if EA_cable > 0:
                        L0 = L_ref / (1.0 + T_edge / EA_cable)
                    else:
                        L0 = L_ref
                    cables.append({"a": ia, "b": ib, "L0": L0, "EA": EA_cable})
            apex_idx = data["built"]["beam_top_indices"][0] if len(data["built"]["beam_top_indices"]) > 0 else None
            load_output = generate_uls_loads(
                coords_fdm, data["tris"], code_choice, wind_speed, snow_depth, payload_kg, apex_idx,
                shape_type="multi_cone", h_over_d=apex / span if span > 0 else 0.0,
                cone_apexes=[(data["coords_fdm"][c][0], data["coords_fdm"][c][1], data["coords_fdm"][c][2]) for c in data["built"]["centre_indices"]],
                cone_radius_m=ring_diameter / 2.0)
            mat = make_membrane_material(
                E_warp_MPa=1400.0, E_weft_MPa=1400.0, thickness_mm=1.02, nu=0.34, G_MPa=50.0,
                warp_prestress_N_per_m=data["warp_q"], weft_prestress_N_per_m=data["weft_q"])
            results_by_case = {}
            converged_cases = {}
            for case_name in ("uplift", "downforce"):
                res = solve_nonlinear_equilibrium(
                    points=coords_fdm.copy(), triangles=data["tris"], fixed_indices=data["fixed"],
                    reference_points=coords_fdm.copy(), membrane_material=mat, cables=cables,
                    loads=load_output[case_name],
                    max_iter=300, max_outer=25, tol=0.01, tol_disp=1e-4,
                    max_total_steps=5000, max_wall_seconds=120.0,
                    seed_z_amplitude=0.001 * data["span"])
                results_by_case[case_name] = res
                if res.get("converged", False):
                    converged_cases[case_name] = {"dr_result": res}
                else:
                    st.warning(f"⚠ Case '{case_name}' did not converge. It will not be included in sizing.")

            view_case = "uplift" if "uplift" in converged_cases else ("downforce" if "downforce" in converged_cases else None)
            if view_case is None:
                st.error("Both wind load cases failed to converge. Cannot size steel. Check the geometry or loads.")
                return
            dr_result = results_by_case[view_case]
            coords_to_draw = dr_result["coordinates"]

            stage3_results = None
            if converged_cases:
                try:
                    data_for_sizer = dict(data)
                    data_for_sizer["ring_diameter"] = ring_diameter
                    data_for_sizer["mc_rd"] = ring_diameter
                    stage3_results = size_steel_frame(
                        data=data_for_sizer, newton_data_cases=converged_cases,
                        code_choice=code_choice, grade="S355", family="CHS")
                except Exception as e:
                    st.error(f"Stage 3 Frame Solver failed: {e}")

            st.session_state["newton_results"] = {
                "cases": results_by_case,
                "cable_name": cable_name, "cable_A_mm2": cable_A_mm2,
                "EA_cable": EA_cable, "cable_d_mm": cable_d_mm,
                "design_tension_N": max(data["fdm"]["max_edge_tension_N"],
                                        max((c["T_N"] for c in dr_result.get("cable_tension_list", [])), default=0)),
                "sections": {"primary": "Calculating", "rib": "Calculating", "ring": "Calculating", "drop": "Calculating"},
                "details": {}, "cables": cables, "material": mat,
                "fabric_family": fabric_family, "fabric_name": fabric_name,
            }
            if stage3_results:
                st.session_state["stage3_results"] = stage3_results
                if "sections" in stage3_results:
                    st.session_state["newton_results"]["sections"] = stage3_results["sections"]
                if "details" in stage3_results:
                    st.session_state["newton_results"]["details"] = stage3_results["details"]

    newton_data = st.session_state.get("newton_results")
    if newton_data and not btn_analysis and "cases" in newton_data:
        view_case = "uplift" if newton_data["cases"]["uplift"].get("converged", False) else "downforce"
        coords_to_draw = newton_data["cases"][view_case]["coordinates"]
        dr_result = newton_data["cases"][view_case]

    fig = go.Figure()
    if len(data["tris"]) > 0:
        tri = np.asarray(data["tris"], dtype=int)
        fig.add_trace(go.Mesh3d(x=coords_to_draw[:, 0], y=coords_to_draw[:, 1], z=coords_to_draw[:, 2],
                                i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
                                color=COL_MEMBRANE, opacity=0.55, flatshading=True,
                                showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=data["xp"], y=np.zeros_like(data["xp"]), z=data["zp"],
                               mode="lines", line=dict(color=COL_PRIMARY, width=7),
                               showlegend=False, hoverinfo="skip"))
    for i in range(len(data["rib_x"])):
        rp = _rib_polyline(float(data["rib_x"][i]), float(data["rib_half_width"][i]),
                           float(data["rib_peak_z"][i]), RIB_SEGMENTS)
        fig.add_trace(go.Scatter3d(x=rp[:, 0], y=rp[:, 1], z=rp[:, 2], mode="lines",
                                   line=dict(color=COL_RIB, width=5),
                                   showlegend=False, hoverinfo="skip"))
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        pp = coords_to_draw[idx_list]; closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(x=closed[:, 0], y=closed[:, 1], z=closed[:, 2], mode="lines",
                                   line=dict(color=COL_RING_EDGE, width=5),
                                   showlegend=False, hoverinfo="skip"))
        centre_i = data["built"]["centre_indices"][k]; beam_i = data["built"]["beam_top_indices"][k]
        cx, cy, cz = coords_to_draw[centre_i]
        for poly_i in idx_list:
            fig.add_trace(go.Scatter3d(x=[cx, coords_to_draw[poly_i, 0]],
                                       y=[cy, coords_to_draw[poly_i, 1]],
                                       z=[cz, coords_to_draw[poly_i, 2]],
                                       mode="lines", line=dict(color=COL_SPOKE, width=2),
                                       showlegend=False, hoverinfo="skip"))
        bx, by, bz = coords_to_draw[beam_i]
        fig.add_trace(go.Scatter3d(x=[cx, bx], y=[cy, by], z=[cz, bz], mode="lines",
                                   line=dict(color=COL_DROP, width=4),
                                   showlegend=False, hoverinfo="skip"))
    apply_common_layout(fig, data["apex"])
    geom_hash = f"{span}_{apex}_{mid_width}_{number_of_cones}_{ring_spacing}_{secondary_count}"
    st.plotly_chart(fig, use_container_width=True, key=f"mc_3d_{geom_hash}")

    with st.expander("Diagnostics", expanded=True):
        st.write("**Stage 1 — FDM:**")
        st.write("FDM Solve OK: %s" % data["solve_ok"])
        if not data["solve_ok"]:
            st.write("FDM error: %s" % data["solve_err"])
        else:
            st.write("FDM force imbalance (N): %.6e" % data["residual_fdm"])

        if newton_data and "cases" in newton_data:
            st.write("---")
            st.write("**Stage 2 — Two Load Cases:**")
            for case_name in ("uplift", "downforce"):
                res = newton_data["cases"][case_name]
                st.write(f"- {case_name}: converged={res['converged']} · iterations={res['iterations']} · time={res['elapsed_seconds']:.2f}s")

            st.write("---")
            st.write("**Fabric Utilization:**")
            fab_util = _compute_fabric_utilization(newton_data["cases"]["uplift"], newton_data.get("fabric_name"), newton_data.get("fabric_family"))
            if fab_util:
                st.write("Fabric: **%s** (%s)" % (fab_util["fabric"], fab_util["family"]))
                st.write("f_u (min): %.1f kN/m" % fab_util["f_u_min_kN_m"])
                st.write("Max membrane tension: %.2f kN/m" % fab_util["max_stress_kN_m"])
                util_pct = fab_util["utilization"] * 100
                if fab_util["utilization"] > 1.0:
                    st.error("Utilization: %.0f%% → **DANGER: fabric may rupture.**" % util_pct)
                elif fab_util["utilization"] > 0.5:
                    st.warning("Utilization: %.0f%% → **WARNING: approaching ULS.**" % util_pct)
                else:
                    st.success("Utilization: %.0f%% → **SAFE.**" % util_pct)

            st.write("---")
            st.write("**Stage 3 — 3D Frame (Worst of 2 Cases):**")
            stage3_data = st.session_state.get("stage3_results")
            if stage3_data:
                if "error" in stage3_data:
                    st.error(f"Stage 3 Error: {stage3_data['error']}")
                else:
                    st.success("Stage 3 Frame Solve Successful.")
                    s3_sections = stage3_data.get("sections", {})
                    s3_details = stage3_data.get("details", {})
                    st.write("Final Frame Sections (Auto-Sized):")
                    st.write(f"- Primary: **{s3_sections.get('primary')}**")
                    st.write(f"- Rib: **{s3_sections.get('rib')}**")
                    st.write(f"- Ring: **{s3_sections.get('ring')}**")
                    st.write(f"- Spoke: **{s3_sections.get('spoke')}**")
                    st.write(f"- Drop: **{s3_sections.get('drop')}**")
                    st.write("Frame Max Utilizations (governing case shown):")
                    for k, v in s3_details.items():
                        st.write(f"- {k.capitalize()}: {v['max_util']*100:.0f}% (Max N: {v['max_N']/1000.0:.1f} kN, Case: {v.get('governing_case', 'n/a')})")
            else:
                st.info("Stage 3 has not been run yet.")

            st.write("---")
            st.write("**Reaction Forces & Foundation Design (Uplift case):**")
            R = newton_data["cases"]["uplift"].get("reactions", None)
            if R is not None:
                anchor_idx = data["anchor_idx"]
                st.write("**Baseplate Table (All Anchor Nodes):**")
                st.code("%-6s  %-8s  %-8s  %-10s  %-10s  %-10s  %-12s  %-10s  %-10s  %-12s" %
                        ("Node", "X(m)", "Y(m)", "Fx(kN)", "Fy(kN)", "Fz(kN)", "Moment(kNm)", "Plate(mm)", "Bolts", "Pad(mm)"),
                        language="text")
                primary_sec = newton_data.get("sections", {}).get("primary", "CHS 100")
                for idx in anchor_idx:
                    r = R[idx]
                    design = design_baseplate_and_foundation(r, primary_sec, data["eave_height"])
                    st.code("%-6d  %-8.2f  %-8.2f  %-10.1f  %-10.1f  %-10.1f  %-12.1f  %-10s  %-10s  %-12s" % (
                        idx, data["coords_fdm"][idx, 0], data["coords_fdm"][idx, 1],
                        r[0]/1000.0, r[1]/1000.0, r[2]/1000.0, design["overturning_moment_kNm"],
                        "%dx%dx%d" % (design["plate_side_mm"], design["plate_side_mm"], design["plate_thickness_mm"]),
                        "%dxM%d" % (design["bolt_count"], design["bolt_diameter_mm"]),
                        "%dx%d" % (design["pad_side_mm"], design["pad_side_mm"])
                    ), language="text")

                st.write("---")
                st.write("**Corner Plate Table (All Anchor Nodes):**")
                st.code("%-6s  %-8s  %-8s  %-12s  %-14s  %-12s  %-10s  %-9s  %-9s" %
                        ("Node", "X(m)", "Y(m)", "T_cable(kN)", "Plate(mm)", "Weld(mm)", "Pin(mm)", "WeldUtil", "PinUtil"),
                        language="text")
                design_tension_N = float(newton_data.get("design_tension_N", 0.0))
                n_anchors = len(anchor_idx)
                for k in range(n_anchors):
                    idx = anchor_idx[k]
                    prev_idx = anchor_idx[(k - 1) % n_anchors]
                    next_idx = anchor_idx[(k + 1) % n_anchors]
                    v_prev = data["coords_fdm"][prev_idx] - data["coords_fdm"][idx]
                    v_next = data["coords_fdm"][next_idx] - data["coords_fdm"][idx]
                    L_prev = np.linalg.norm(v_prev); L_next = np.linalg.norm(v_next)
                    if L_prev > 1e-9 and L_next > 1e-9:
                        u_prev = v_prev / L_prev; u_next = v_next / L_next
                        F_resultant = design_tension_N * np.linalg.norm(u_prev + u_next)
                    else:
                        F_resultant = design_tension_N
                    cp = design_corner_plate(F_resultant, newton_data["cable_d_mm"], steel_fy_MPa=355)
                    st.code("%-6d  %-8.2f  %-8.2f  %-12.1f  %-14s  %-12s  %-10s  %-9s  %-9s" % (
                        idx, data["coords_fdm"][idx, 0], data["coords_fdm"][idx, 1],
                        F_resultant / 1000.0,
                        "%dx%dx%d" % (cp["plate_thickness_mm"], cp["plate_width_mm"], cp["plate_length_mm"]),
                        "%dx%d" % (cp["weld_size_mm"], cp["weld_length_mm"]),
                        "%d" % cp["pin_diameter_mm"],
                        "%.0f%%" % (cp["weld_utilization"] * 100),
                        "%.0f%%" % (cp["pin_utilization"] * 100),
                    ), language="text")

                st.write("---")
                st.write("**Cone Drop Table:**")
                st.code("%-8s  %-10s  %-10s  %-10s  %-10s" %
                        ("Cone", "X(m)", "Y(m)", "Fz(kN)", "Drop(mm)"), language="text")
                for k in range(len(data["built"]["centre_indices"])):
                    ci = data["built"]["centre_indices"][k]
                    bi = data["built"]["beam_top_indices"][k]
                    r_drop = R[bi]
                    st.code("%-8d  %-10.2f  %-10.2f  %-10.1f  %-10s" %
                            (k+1, data["coords_fdm"][ci, 0], data["coords_fdm"][ci, 1],
                             r_drop[2]/1000.0, newton_data["sections"].get("drop", "?")), language="text")

                st.write("---")
                st.write("**Deflection Check:**")
                max_deflection_mm = 0.0
                for i in range(len(data["coords_fdm"])):
                    d = np.linalg.norm(coords_to_draw[i] - data["coords_fdm"][i])
                    if d > max_deflection_mm:
                        max_deflection_mm = d * 1000.0
                limit_mm = (data["span"] * 1000.0) / 200.0
                status = "PASS" if max_deflection_mm <= limit_mm else "FAIL"
                st.code("Max Deflection: %.2f mm (Limit: %.1f mm) -> %s" %
                        (max_deflection_mm, limit_mm, status), language="text")

            members = _build_member_schedule(
                data["built"], coords_to_draw, data["x_rings"], data["anchor_idx"],
                data["edge_q_scalar"], data["warp_q"], data["weft_q"],
                newton_data["cable_name"], newton_data["cable_A_mm2"],
                newton_data["sections"], data["eave_height"],
                data["span"], data["mid_width"], ring_diameter)
            with st.expander("Member schedule (auto-sized)", expanded=True):
                st.code(_format_member_table(members), language="text")

            st.markdown("---")
            st.markdown("### 📄 SDSe Analysis Report")
            if st.button("📄 Open SDSe Analysis Report", key="SDSe_open_report_btn", use_container_width=True):
                st.session_state.page = "analysis_report"
                st.rerun()
