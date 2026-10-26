"""Multi-Cone Roof — Lab test page.

Three-stage workflow:
    Stage 1: FDM finds the shape.
    Stage 2: Simplified structural solve + auto-sizing.
    Stage 3: Rigorous 3D frame analysis (optional).
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm
from engine.SDSe_mesh_builder import SDSe_mesh_rings, SDSe_blend_q_per_edge
from engine.nonlinear_equilibrium_newton_seed import (
    make_membrane_material,
    solve_nonlinear_equilibrium,
)
from engine.load_generator import CODE_PARAMS, generate_uls_loads
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

PRETENSION_STEPS = [0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
UTILIZATION_WARN_THRESHOLD = 0.60
UTILIZATION_CAP = 0.70
MEMBRANE_DEAD_LOAD_KG_M2 = 1.102
GRAVITY = 9.81


# =============================================================================
# HELPERS
# =============================================================================

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


def _select_steel_section_simple(n_wind_kN, length_m, tributary_width_m, code_choice, family="CHS", grade="S355"):
    """Simplified sizing for Stage 2 (not the rigorous frame)."""
    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("fy", 355)
    E_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000)
    if code_choice == "MS 1553":
        gamma_DL, gamma_WL = 0.9, 1.5
    elif code_choice == "ASCE 7":
        gamma_DL, gamma_WL = 0.9, 1.0
    else:
        gamma_DL, gamma_WL = 1.0, 1.5
    L_eff_m = 0.7 * length_m
    membrane_DL_kN = MEMBRANE_DEAD_LOAD_KG_M2 * GRAVITY * tributary_width_m * length_m / 1000.0
    candidates = []
    for name, props in SECTION_PROPERTIES.items():
        if props.get("type") != family:
            continue
        if "I" not in props or "A" not in props:
            continue
        candidates.append((props.get("A", 1e9), name, props))
    candidates.sort(key=lambda c: c[0])
    candidates = candidates[:40]
    for A_mm2, name, props in candidates:
        W_el_mm3 = props.get("W_el", 1.0)
        weight_kg_m = props.get("weight", 0.0)
        steel_DL_kN = weight_kg_m * GRAVITY * length_m / 1000.0
        total_DL_kN = steel_DL_kN + membrane_DL_kN
        N_Ed_axial_kN = max(0.0, gamma_WL * n_wind_kN - gamma_DL * total_DL_kN)
        w_transverse_kN_m = total_DL_kN / length_m
        M_Ed_kNm = w_transverse_kN_m * length_m ** 2 / 8.0
        N_Ed = N_Ed_axial_kN * 1000.0
        M_Ed = M_Ed_kNm * 1e6
        N_cap = A_mm2 * fy_MPa
        M_cap = W_el_mm3 * fy_MPa
        util_stress = (N_Ed / N_cap) + (M_Ed / M_cap)
        I_mm4 = props["I"]
        L_mm = L_eff_m * 1000.0
        N_cr = (math.pi ** 2 * E_MPa * I_mm4) / (L_mm ** 2)
        buckling_util = N_Ed / N_cr if N_cr > 0 else 999.0
        combined_util = util_stress + buckling_util
        if combined_util <= UTILIZATION_CAP:
            return name, {
                "util": combined_util, "N_Ed_kN": N_Ed_axial_kN, "M_Ed_kNm": M_Ed_kNm,
                "total_DL_kN": total_DL_kN, "steel_DL_kN": steel_DL_kN,
                "membrane_DL_kN": membrane_DL_kN, "L_eff_m": L_eff_m,
            }
    A_mm2, name, props = candidates[-1]
    return name, {
        "util": 1.0, "N_Ed_kN": N_Ed_axial_kN, "M_Ed_kNm": M_Ed_kNm,
        "total_DL_kN": total_DL_kN, "steel_DL_kN": steel_DL_kN,
        "membrane_DL_kN": membrane_DL_kN, "L_eff_m": L_eff_m,
    }


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
        a = anchors[i]
        b = anchors[(i + 1) % n_a]
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
    ring_indices = built["ring_indices"]
    centre_indices = built["centre_indices"]
    beam_top_indices = built["beam_top_indices"]
    triangles = built["triangles"]
    n_perimeter = built["n_perimeter"]
    members.append({"member_id": "Primary_Beam_Main", "member_type": "primary_beam", "length_m": float(span * 1.2), "section": sections["primary"], "material": "S355", "role": "Main arched beam"})
    for i in range(3):
        members.append({"member_id": "Rib_Beam_%d" % (i+1), "member_type": "rib_beam", "length_m": float(mid_width * 1.5), "section": sections["rib"], "material": "S355", "role": "Secondary arched beam"})
    for k in range(len(ring_indices)):
        idx_list = ring_indices[k]
        ring_length = sum(float(np.linalg.norm(coords[int(idx_list[(i + 1) % len(idx_list)])] - coords[int(idx_list[i])])) for i in range(len(idx_list)))
        members.append({"member_id": "Ring_%d_Ring_Beam" % (k+1), "member_type": "ring_beam", "length_m": float(ring_length), "section": sections["ring"], "material": "S355", "role": "closed ring beam"})
        centre_i = int(centre_indices[k]); beam_i = int(beam_top_indices[k])
        L = float(np.linalg.norm(coords[beam_i] - coords[centre_i]))
        members.append({"member_id": "Ring_%d_Drop_Member" % (k+1), "member_type": "drop_member", "length_m": L, "section": sections["drop"], "material": "S355", "role": "vertical drop"})
    members.append({"member_id": "Edge_Cable", "member_type": "cable", "length_m": float(sum(float(np.linalg.norm(coords[(i+1) % n_perimeter] - coords[i])) for i in range(n_perimeter))), "section": cable_name, "material": "A=%.1f mm2" % cable_A_mm2, "role": "perimeter edge cable"})
    for (a, b, c) in triangles:
        pa, pb, pc = coords[a], coords[b], coords[c]
        mean_edge = (float(np.linalg.norm(pb - pa)) + float(np.linalg.norm(pc - pb)) + float(np.linalg.norm(pa - pc))) / 3.0
        members.append({"member_id": "Membrane_Panel_%04d" % (len(members) + 1), "member_type": "membrane", "length_m": mean_edge, "section": "FABRIC", "material": "PVDF Type III", "role": "fabric panel"})
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
        if sigma is None:
            continue
        s_xx, s_yy, s_xy = float(sigma[0, 0]), float(sigma[1, 1]), float(sigma[0, 1])
        mean = 0.5 * (s_xx + s_yy)
        radius = math.sqrt((0.5 * (s_xx - s_yy)) ** 2 + s_xy ** 2)
        principal = mean + radius
        if principal > max_principal_N_m:
            max_principal_N_m = principal
    family = FABRIC_PROPERTIES.get(fabric_family, {})
    fabric = family.get(fabric_name, {})
    f_u_warp = fabric.get("f_u_warp", None)
    f_u_weft = fabric.get("f_u_weft", None)
    if not f_u_warp or not f_u_weft:
        return None
    f_u_min = min(float(f_u_warp), float(f_u_weft))
    util = (max_principal_N_m / 1000.0) / f_u_min if f_u_min > 0 else 999.0
    return {
        "fabric": fabric_name, "family": fabric_family, "f_u_min_kN_m": f_u_min,
        "max_stress_kN_m": max_principal_N_m / 1000.0, "utilization": util,
    }


# =============================================================================
# PAGE
# =============================================================================

def render_tester_multi_cone():
    bcol1, bcol2, bcol3 = st.columns([1, 1, 3])
    with bcol1:
        if st.button("← Back to Lab", key="mc_back_lab", use_container_width=True):
            st.session_state.page = "lab"; st.rerun()
    with bcol2:
        if st.button("← Back to Landing", key="mc_back_landing", use_container_width=True):
            st.session_state.page = "landing"; st.rerun()

    st.markdown("<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2><p style='color:#a8b8c8;margin-top:0;'>Step 1: FDM. Step 2: Structural Solve. Step 3: Rigorous 3D Frame.</p>", unsafe_allow_html=True)

    # ===== INPUTS =====
    c1, c2 = st.columns(2)
    with c1: span = st.number_input("Primary span (m)", 6.0, 60.0, 10.0, 0.5, key="mc_span")
    with c2: apex = st.number_input("Primary apex (m)", 1.0, 30.0, 5.0, 0.5, key="mc_apex")
    c1, c2 = st.columns(2)
    with c1: mid_width = st.number_input("Mid-span width (m)", 6.0, 60.0, 10.0, 0.5, key="mc_width")
    with c2: eave_height = st.number_input("Eave height (m)", 0.5, 10.0, 2.8, 0.1, key="mc_eave")
    c1, c2 = st.columns(2)
    with c1: ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 1.0, 0.1, key="mc_rd")
    with c2: curve_type = st.selectbox("Curve type", ["parabolic", "circular", "catenary"], index=0, key="mc_curve")
    c1, c2 = st.columns(2)
    with c1: secondary_count = int(st.number_input("Secondary count", 2, 20, 3, 1, key="mc_nribs"))
    with c2: optional_ends = st.toggle("Optional ends", value=False, key="mc_optends")
    subdivisions = int(st.number_input("Subdivisions per edge", 5, 25, 5, 1, key="mc_subdiv"))
    c1, c2 = st.columns(2)
    with c1: number_of_cones = int(st.number_input("Number of cones", 1, 20, 1, 1, key="mc_ncones"))
    with c2: ring_spacing = st.number_input("Distance between adjacent cones (m)", 0.5, 10.0, 5.0, 0.1, key="mc_spacing")
    ring_clearance = st.number_input("Ring clearance below beam (m)", 0.1, 5.0, 1.0, 0.1, key="mc_clr")

    st.markdown("### Fabric Selection")
    fabric_families = [k for k in FABRIC_PROPERTIES.keys() if k != "default"]
    c1, c2 = st.columns(2)
    with c1:
        fabric_family = st.selectbox("Fabric Family", fabric_families, index=fabric_families.index("PVDF") if "PVDF" in fabric_families else 0, key="mc_fabric_family")
    with c2:
        fabric_names = [k for k in FABRIC_PROPERTIES.get(fabric_family, {}).keys() if k != "default"]
        fabric_name = st.selectbox("Fabric Type", fabric_names, index=0, key="mc_fabric_name")

    st.markdown("### Pretension & Loads")
    c1, c2 = st.columns(2)
    with c1: warp_q_input = st.number_input("Warp pretension (kN/m)", 0.1, 100.0, 1.0, 0.1, key="mc_warp")
    with c2: weft_q_input = st.number_input("Weft pretension (kN/m)", 0.1, 100.0, 1.0, 0.1, key="mc_weft")
    edge_q_input = st.number_input("Edge cable pretension (kN/m)", 0.1, 500.0, 5.0, 0.1, key="mc_edgeq")

    st.markdown("### Environmental Loads & Design Philosophy")
    c1, c2 = st.columns(2)
    with c1: code_choice = st.selectbox("Building Code", ["MS 1553", "ASCE 7", "EN 1991"], index=0, key="mc_code")
    with c2: design_philosophy = st.selectbox("Design Philosophy", ["Serviceability (Unfactored)", "Ultimate Limit State (Factored)"], index=0, key="mc_design_philosophy")
    c1, c2 = st.columns(2)
    with c1: wind_speed = st.number_input("Wind Speed (m/s)", 0.0, 80.0, 33.5, 1.0, key="mc_wind_speed")
    with c2: snow_depth = st.number_input("Snow Depth (m)", 0.0, 2.0, 0.0, 0.1, key="mc_snow_depth")
    payload_kg = st.number_input("Payload at apex (kg)", 0.0, 1000.0, 0.0, 10.0, key="mc_payload")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn1: btn_fdm = st.button("1. Find Form (FDM)", use_container_width=True)
    with col_btn2: btn_newton = st.button("2. Structural Calculation", use_container_width=True)
    with col_btn3: btn_frame = st.button("3. Rigorous 3D Frame", use_container_width=True)

    # ===== STAGE 1: FDM =====
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
                x_val = float(np.interp(s_val, s_p, xp))
                bz_val = float(np.interp(s_val, s_p, zp))
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
        warp_q = max(float(warp_q_input), 0.1) * 1000.0
        weft_q = max(float(weft_q_input), 0.1) * 1000.0
        edge_q_scalar = max(float(edge_q_input), 0.1) * 1000.0
        pts_2d = pts[:, :2]; warp_dir = np.array([1.0, 0.0])
        q_interior = SDSe_blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q)
        q = np.empty(len(edges), dtype=float)
        for k, (i, j) in enumerate(edges):
            key = (i, j) if i < j else (j, i)
            q[k] = edge_q_scalar if key in boundary_edge_set else q_interior[k]
        try:
            fdm = solve_fdm(pts, edges, fixed, q)
            coords_fdm = fdm["coordinates"]; residual_fdm = float(fdm["residual_norm"])
            solve_ok = True; solve_err = ""
        except Exception as e:
            coords_fdm = pts.copy(); residual_fdm = float("nan"); solve_ok = False; solve_err = str(e)
        max_edge_tension_N = edge_q_scalar * L_avg
        fdm["max_edge_tension_N"] = max_edge_tension_N
        fdm["edge_q_scalar"] = edge_q_scalar
        st.session_state["fdm_results"] = {
            "built": built, "pts": pts, "edges": edges, "tris": tris, "fixed": fixed, "coords_fdm": coords_fdm, "fdm": fdm,
            "residual_fdm": residual_fdm, "solve_ok": solve_ok, "solve_err": solve_err,
            "warp_q": warp_q, "weft_q": weft_q, "edge_q_scalar": edge_q_scalar, "span": span, "mid_width": mid_width, "apex": apex, "L_avg": L_avg,
            "anchor_idx": anchor_idx, "x_rings": [np.interp(s, s_p, xp) for s in s_rings], "rib_x": rib_x,
            "rib_peak_z": rib_peak_z, "rib_half_width": rib_half_width, "xp": xp, "zp": zp, "eave_height": eave_height,
        }

    data = st.session_state.get("fdm_results")
    if not data:
        return
    coords_to_draw = data["coords_fdm"]
    dr_result = None

    # ===== STAGE 2: Structural Solve =====
    if btn_newton:
        with st.spinner("Running Automated Structural Calculation..."):
            cable_name, cable_A_mm2, cable_E_MPa, EA_cable, cable_d_mm = _select_edge_cable(data["fdm"]["max_edge_tension_N"], safety_factor=2.0)
            cables = []
            n_a = len(data["anchor_idx"]); pts = data["pts"]; coords_fdm = data["coords_fdm"]
            for k in range(n_a):
                a_idx = data["anchor_idx"][k]; b_idx = data["anchor_idx"][(k + 1) % n_a]
                chain = [int(a_idx)]; i_cur = (a_idx + 1) % pts.shape[0]; b_int = int(b_idx); safety = 0
                while i_cur != b_int and safety < pts.shape[0]:
                    chain.append(int(i_cur)); i_cur = (i_cur + 1) % pts.shape[0]; safety += 1
                chain.append(int(b_int))
                for m in range(len(chain) - 1):
                    ia = chain[m]; ib = chain[m + 1]
                    L_ref = float(np.linalg.norm(coords_fdm[ib] - coords_fdm[ia]))
                    if L_ref < 1e-9: continue
                    cables.append({"a": ia, "b": ib, "L0": L_ref * 1.001, "EA": EA_cable})
            apex_idx = data["built"]["beam_top_indices"][0] if len(data["built"]["beam_top_indices"]) > 0 else None
            h_over_d = apex / span if span > 0 else 0.0
            cone_radius_m = ring_diameter / 2.0
            cone_apexes_3d = [np.array(data["coords_fdm"][bti]) for bti in data["built"]["beam_top_indices"]]
            fabric_props = FABRIC_PROPERTIES.get(fabric_family, {}).get(fabric_name, {})
            membrane_kg_m2 = float(fabric_props.get("kg_m2", 1.102) or 1.102)
            loads_dict = generate_uls_loads(
                coords_fdm, data["tris"], code_choice, wind_speed, snow_depth, payload_kg, apex_idx,
                shape_type="multi_cone", h_over_d=h_over_d, cone_apexes=cone_apexes_3d,
                cone_radius_m=cone_radius_m, membrane_kg_m2=membrane_kg_m2,
            )
            if design_philosophy == "Ultimate Limit State (Factored)":
                loads = loads_dict["uplift"]
                st.info("Running ULS Uplift Case with Cp map (multi-cone).")
            else:
                loads = loads_dict["service"]
            st.session_state["wind_diagnostics"] = loads_dict.get("wind_diagnostics", {})
            dr_result = None; final_pretension = None
            for p_factor in PRETENSION_STEPS:
                cur_warp = p_factor * 1000.0; cur_weft = p_factor * 1000.0
                mat = make_membrane_material(
                    E_warp_MPa=1400.0, E_weft_MPa=1400.0, thickness_mm=1.02, nu=0.34, G_MPa=50.0,
                    warp_prestress_N_per_m=cur_warp, weft_prestress_N_per_m=cur_weft,
                )
                res = solve_nonlinear_equilibrium(
                    points=coords_fdm.copy(), triangles=data["tris"], fixed_indices=data["fixed"], reference_points=coords_fdm.copy(),
                    membrane_material=mat, cables=cables, loads=loads,
                    max_iter=100, max_outer=25, tol=0.01, tol_disp=1e-4, max_total_steps=50, max_wall_seconds=10.0,
                    seed_z_amplitude=0.001 * data["span"],
                )
                if res["converged"]:
                    dr_result = res; final_pretension = p_factor; break
            if dr_result is None:
                st.error("This geometry requires a membrane pretension above %.1f kN/m to hold its shape under %.1f m/s wind." % (PRETENSION_STEPS[-1], wind_speed))
                return
            if final_pretension > 0.1:
                st.warning("Converged at increased pretension: %.1f kN/m membrane, %.1f kN/m cable." % (final_pretension, final_pretension * 5.0))
            max_actual_T = max([c["T_N"] for c in dr_result["cable_tension_list"]]) if "cable_tension_list" in dr_result and len(dr_result["cable_tension_list"]) > 0 else data["fdm"]["max_edge_tension_N"]
            design_tension_N = max(max_actual_T, data["fdm"]["max_edge_tension_N"])
            cable_name, cable_A_mm2, cable_E_MPa, EA_cable, cable_d_mm = _select_edge_cable(design_tension_N, safety_factor=2.0)
            max_reaction_kN = max([math.sqrt(r[0]**2 + r[1]**2 + r[2]**2) / 1000.0 for r in dr_result["reactions"]]) if "reactions" in dr_result and len(dr_result["reactions"]) > 0 else data["fdm"]["max_edge_tension_N"] / 1000.0
            sec_primary, det_primary = _select_steel_section_simple(max_reaction_kN, data["span"], data["mid_width"], code_choice)
            sec_rib, det_rib = _select_steel_section_simple(max_reaction_kN * 0.5, data["mid_width"], data["mid_width"] / (secondary_count + 1.0), code_choice)
            sec_ring, det_ring = _select_steel_section_simple(max_reaction_kN * 0.25, ring_diameter, ring_diameter, code_choice)
            sec_drop, det_drop = _select_steel_section_simple(max_reaction_kN * 0.25, ring_clearance, 1.0, code_choice)
            if "Oversize required" in [sec_primary, sec_rib, sec_ring, sec_drop]:
                st.error("One or more steel sections exceed the catalogue."); return
            if det_primary is not None and det_primary["util"] > UTILIZATION_WARN_THRESHOLD:
                st.warning("Primary Beam utilization: %.0f%%." % (det_primary["util"] * 100))
            coords_to_draw = dr_result["coordinates"]
            st.session_state["newton_results"] = {
                "dr_result": dr_result, "cable_name": cable_name, "cable_A_mm2": cable_A_mm2, "EA_cable": EA_cable,
                "cable_d_mm": cable_d_mm,
                "sections": {"primary": sec_primary, "rib": sec_rib, "ring": sec_ring, "drop": sec_drop},
                "details": {"primary": det_primary, "rib": det_rib, "ring": det_ring, "drop": det_drop},
                "beam_axial_kN": max_reaction_kN,
                "cables": cables, "material": mat, "final_pretension": final_pretension,
                "fabric_family": fabric_family, "fabric_name": fabric_name,
                "frame_sections": None, "frame_details": None, "frame_iteration_log": None, "frame_error": None,
            }

    # ===== STAGE 3: Rigorous 3D Frame =====
    if btn_frame:
        if "newton_results" not in st.session_state:
            st.warning("Run Stage 2 first before Stage 3.")
        else:
            with st.spinner("Running 3D Frame Analysis (may take 30-60 seconds)..."):
                try:
                    frame_result = size_steel_frame(
                        data=data, newton_data=st.session_state["newton_results"], code_choice=code_choice,
                    )
                    st.session_state["newton_results"]["frame_sections"] = frame_result.get("sections", {})
                    st.session_state["newton_results"]["frame_details"] = frame_result.get("details", {})
                    st.session_state["newton_results"]["frame_iteration_log"] = frame_result.get("iteration_log", [])
                    st.session_state["newton_results"]["frame_result"] = frame_result.get("frame_result")
                    st.session_state["newton_results"]["frame_error"] = frame_result.get("error")
                    st.success("3D Frame analysis complete.")
                except Exception as e:
                    st.session_state["newton_results"]["frame_error"] = str(e)
                    st.error("3D Frame analysis failed: %s" % str(e))

    newton_data = st.session_state.get("newton_results")
    if newton_data and not btn_newton and not btn_frame:
        coords_to_draw = newton_data["dr_result"]["coordinates"]
        dr_result = newton_data["dr_result"]

    # ===== 3D VIEWER =====
    fig = go.Figure()
    if len(data["tris"]) > 0:
        tri = np.asarray(data["tris"], dtype=int)
        fig.add_trace(go.Mesh3d(x=coords_to_draw[:, 0], y=coords_to_draw[:, 1], z=coords_to_draw[:, 2], i=tri[:, 0], j=tri[:, 1], k=tri[:, 2], color=COL_MEMBRANE, opacity=0.55, flatshading=True, showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=data["xp"], y=np.zeros_like(data["xp"]), z=data["zp"], mode="lines", line=dict(color=COL_PRIMARY, width=7), showlegend=False, hoverinfo="skip"))
    for i in range(len(data["rib_x"])):
        rp = _rib_polyline(float(data["rib_x"][i]), float(data["rib_half_width"][i]), float(data["rib_peak_z"][i]), RIB_SEGMENTS)
        fig.add_trace(go.Scatter3d(x=rp[:, 0], y=rp[:, 1], z=rp[:, 2], mode="lines", line=dict(color=COL_RIB, width=5), showlegend=False, hoverinfo="skip"))
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        pp = coords_to_draw[idx_list]; closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(x=closed[:, 0], y=closed[:, 1], z=closed[:, 2], mode="lines", line=dict(color=COL_RING_EDGE, width=5), showlegend=False, hoverinfo="skip"))
        centre_i, beam_i = data["built"]["centre_indices"][k], data["built"]["beam_top_indices"][k]
        cx, cy, cz = coords_to_draw[centre_i]
        for poly_i in idx_list:
            fig.add_trace(go.Scatter3d(x=[cx, coords_to_draw[poly_i, 0]], y=[cy, coords_to_draw[poly_i, 1]], z=[cz, coords_to_draw[poly_i, 2]], mode="lines", line=dict(color=COL_SPOKE, width=2), showlegend=False, hoverinfo="skip"))
        bx, by, bz = coords_to_draw[beam_i]
        fig.add_trace(go.Scatter3d(x=[cx, bx], y=[cy, by], z=[cz, bz], mode="lines", line=dict(color=COL_DROP, width=4), showlegend=False, hoverinfo="skip"))
    apply_common_layout(fig, data["apex"])
    geom_hash = f"{span}_{apex}_{mid_width}_{number_of_cones}_{ring_spacing}_{secondary_count}"
    st.plotly_chart(fig, use_container_width=True, key=f"mc_3d_{geom_hash}")

    # ===== DIAGNOSTICS =====
    with st.expander("Diagnostics", expanded=True):
        st.write("Cones: %d | Nodes: %d | Triangles: %d | Held: %d" % (number_of_cones, data["pts"].shape[0], len(data["tris"]), len(data["fixed"])))
        st.write("**Stage 1 — FDM:** OK=%s, Residual=%.4e" % (data["solve_ok"], data["residual_fdm"]))

        if newton_data:
            nd = newton_data["dr_result"]
            st.write("---")
            st.write("**Stage 2 — Newton:** converged=%s (%s), pretension=%.1f kN/m, time=%.2f s, last step=%.4f mm" % (
                nd["converged"], nd["reason"], newton_data.get("final_pretension", 1.0), nd["elapsed_seconds"], nd.get("last_step_m", 0.0) * 1000.0))

            wind_diag = st.session_state.get("wind_diagnostics", {})
            if wind_diag:
                st.write("**Wind Cp Diagnostic:** q=%.1f Pa, Uplift=%.1f kN, Max suction=%.2f kPa, Cp range [%.2f, %.2f]" % (
                    wind_diag.get("q_Pa", 0.0), wind_diag.get("total_uplift_kN", 0.0), wind_diag.get("max_pressure_kPa", 0.0),
                    wind_diag.get("min_cp", 0.0), wind_diag.get("max_cp", 0.0)))

            fab_util = _compute_fabric_utilization(nd, newton_data.get("fabric_name", fabric_name), newton_data.get("fabric_family", fabric_family))
            if fab_util:
                st.write("**Membrane:** %s, f_u=%.1f kN/m, max tension=%.2f kN/m, util=%.0f%%" % (
                    fab_util["fabric"], fab_util["f_u_min_kN_m"], fab_util["max_stress_kN_m"], fab_util["utilization"] * 100))

            det = newton_data.get("details", {}); sec = newton_data.get("sections", {})
            st.write("---")
            st.write("**Simplified Sizing (Stage 2):**")
            for key, label in [("primary", "Primary"), ("rib", "Rib"), ("ring", "Ring"), ("drop", "Drop")]:
                if key in det and det[key] is not None:
                    d = det[key]
                    st.write("%s: %s | L_eff=%.2fm | N_Ed=%.1f kN | Util=%.0f%%" % (label, sec[key], d["L_eff_m"], d["N_Ed_kN"], d["util"] * 100))

            frame_sections = newton_data.get("frame_sections")
            frame_details = newton_data.get("frame_details")
            frame_iter_log = newton_data.get("frame_iteration_log")
            frame_error = newton_data.get("frame_error")
            if frame_sections:
                st.write("---")
                st.write("**Rigorous 3D Frame (Stage 3):**")
                if frame_error:
                    st.error("Frame: %s" % frame_error)
                else:
                    st.success("Frame converged.")
                for key in ["primary", "rib", "ring", "drop", "spoke"]:
                    if key in frame_sections:
                        util = frame_details.get(key, {}).get("max_util", 0.0) if frame_details else 0.0
                        st.write("%s: %s | Max Util=%.0f%%" % (key.capitalize(), frame_sections[key], util * 100))
                if frame_iter_log:
                    st.write("Iteration log:")
                    for log in frame_iter_log:
                        st.write("  Iter %d: %s" % (log["iteration"], log["sections"]))

            R = nd.get("reactions", None)
            if R is not None:
                anchor_idx = data["anchor_idx"]
                primary_sec = newton_data["sections"]["primary"]
                st.write("---")
                st.write("**Baseplate Table:**")
                st.code("%-6s  %-8s  %-8s  %-10s  %-10s  %-10s  %-10s  %-10s" % ("Node", "X", "Y", "Fx(kN)", "Fy(kN)", "Fz(kN)", "Plate", "Pad"), language="text")
                for idx in anchor_idx:
                    r = R[idx]
                    design = design_baseplate_and_foundation(r, primary_sec, 0.0)
                    st.code("%-6d  %-8.2f  %-8.2f  %-10.1f  %-10.1f  %-10.1f  %-10s  %-10s" % (idx, data["coords_fdm"][idx, 0], data["coords_fdm"][idx, 1], r[0]/1000.0, r[1]/1000.0, r[2]/1000.0, "%dx%d" % (design["plate_side_mm"], design["plate_side_mm"]), "%dx%d" % (design["pad_side_mm"], design["pad_side_mm"])), language="text")

                st.write("---")
                st.write("**Corner Plate Table:**")
                st.code("%-6s  %-10s  %-14s  %-12s  %-10s  %-9s  %-9s" % ("Node", "T(kN)", "Plate", "Weld", "Pin", "Weld%", "Pin%"), language="text")
                n_anchors = len(anchor_idx)
                for k in range(n_anchors):
                    idx = anchor_idx[k]
                    prev_idx = anchor_idx[(k - 1) % n_anchors]; next_idx = anchor_idx[(k + 1) % n_anchors]
                    v_prev = data["coords_fdm"][prev_idx] - data["coords_fdm"][idx]
                    v_next = data["coords_fdm"][next_idx] - data["coords_fdm"][idx]
                    L_prev = np.linalg.norm(v_prev); L_next = np.linalg.norm(v_next)
                    if L_prev > 1e-9 and L_next > 1e-9:
                        F_res = design_tension_N * np.linalg.norm(v_prev / L_prev + v_next / L_next)
                    else:
                        F_res = design_tension_N
                    cp = design_corner_plate(F_res, newton_data["cable_d_mm"], steel_fy_MPa=355)
                    st.code("%-6d  %-10.1f  %-14s  %-12s  %-10d  %-9.0f%%  %-9.0f%%" % (idx, F_res/1000.0, "%dx%dx%d" % (cp["plate_thickness_mm"], cp["plate_width_mm"], cp["plate_length_mm"]), "%dx%d" % (cp["weld_size_mm"], cp["weld_length_mm"]), cp["pin_diameter_mm"], cp["weld_utilization"]*100, cp["pin_utilization"]*100), language="text")

                st.write("---")
                st.write("**Deflection:**")
                max_defl = 0.0; max_idx = -1
                for i in range(len(data["coords_fdm"])):
                    d = np.linalg.norm(coords_to_draw[i] - data["coords_fdm"][i])
                    if d > max_defl: max_defl = d * 1000.0; max_idx = i
                limit = (data["span"] * 1000.0) / 200.0
                st.code("Max: %.2f mm at Node %d (Limit %.1f mm) → %s" % (max_defl, max_idx, limit, "PASS" if max_defl <= limit else "FAIL"), language="text")

            members = _build_member_schedule(data["built"], coords_to_draw, data["x_rings"], data["anchor_idx"], data["edge_q_scalar"], data["warp_q"], data["weft_q"], newton_data["cable_name"], newton_data["cable_A_mm2"], newton_data["sections"], data["eave_height"], data["span"], data["mid_width"], ring_diameter)
            with st.expander("Member schedule (simplified)", expanded=False):
                st.code(_format_member_table(members), language="text")

            st.markdown("---")
            st.markdown("### 📄 SDSe Analysis Report")
            if st.button("📄 Open SDSe Analysis Report", key="SDSe_open_report_btn", use_container_width=True):
                st.session_state.page = "analysis_report"; st.rerun()
