"""Multi-Cone Roof — Lab test page."""

import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm
from engine.SDSe_mesh_builder import SDSe_mesh_rings, SDSe_blend_q_per_edge
from engine.nonlinear_equilibrium_newton_seed import make_membrane_material, solve_nonlinear_equilibrium
from engine.load_generator import CODE_PARAMS, generate_uls_loads
from engine.connection_design import design_baseplate_and_foundation, design_corner_plate
from engine.steel_frame_solver import solve_frame
from data.materials import CABLE_PROPERTIES, STEEL_MATERIALS
from data.sections import SECTION_PROPERTIES
from viewers.figures._shared import apply_common_layout, beam_curve, arclength_parametrisation

COL_MEMBRANE = "#4a7a9c"; COL_RING_EDGE = "#ffd166"; COL_PRIMARY = "#FF6B6B"; COL_RIB = "#e07b39"; COL_SPOKE = "#c0c0c0"; COL_DROP = "#a0a0a0"
PRETENSION_STEPS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0]
UTILIZATION_WARN_THRESHOLD = 0.60

def _select_edge_cable(actual_max_tension_N, safety_factor=2.0):
    design_load_N = actual_max_tension_N * safety_factor
    candidates = []
    for family_name, family in CABLE_PROPERTIES.items():
        if family_name == "default": continue
        for size, props in family.items():
            if size == "default" or not props.get("A") or not props.get("f_u"): continue
            breaking_N = props["A"] * props["f_u"]
            if breaking_N >= design_load_N:
                candidates.append((props["A"], "%s %s" % (family_name, size), props["A"], props.get("E", 160000), props["A"] * 1e-6 * props.get("E", 160000) * 1e6))
    if candidates:
        candidates.sort(key=lambda c: c[0])
        return (candidates[0][1], candidates[0][2], candidates[0][3], candidates[0][4])
    return ("Fallback", 63.0, 160000, 10e9)

def _select_steel_section(max_axial_kN, max_moment_kNm, member_length_m, family="CHS", grade="S355"):
    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("fy", 355)
    chs_sections = [(k, v) for k, v in SECTION_PROPERTIES.items() if v.get("type") == family]
    chs_sections.sort(key=lambda x: x[1].get("A", 0.0))
    for name, props in chs_sections:
        A_mm2, W_el_mm3 = props.get("A", 1.0), props.get("W_el", 1.0)
        N_cap, M_cap = A_mm2 * fy_MPa, W_el_mm3 * fy_MPa
        util = (abs(max_axial_kN) * 1000.0 / N_cap) + (abs(max_moment_kNm) * 1e6 / M_cap)
        r_mm = math.sqrt(props.get("I", 1.0) / A_mm2) if props.get("I") else 0.35 * props.get("d", 100)
        L_eff_mm = float(member_length_m) * 1000.0
        N_cr_kN = (math.pi ** 2) * 210000 * A_mm2 * (r_mm ** 2) / (L_eff_mm ** 2) / 1000.0 if L_eff_mm > 0 else 1e9
        buckling_util = (abs(max_axial_kN)) / N_cr_kN if max_axial_kN > 0 else 0.0
        if util <= 0.9 and buckling_util <= 1.0: return name
    return "Oversize required"

def _ellipse_y(x, span, mid_width): return (mid_width / 2.0) * math.sqrt(max(0.0, 1.0 - (x / (span / 2.0)) ** 2))
def _rib_stations(n, optional_ends, span, x, s, total):
    if (not optional_ends) or n < 3: return np.interp(np.array([k / (n + 1.0) for k in range(1, n + 1)]) * total, s, x)
    return np.linspace(-(span / 2.0 - 3.0), +(span / 2.0 - 3.0), n)
def _rib_arch_y_at_eave(peak_z, half_width, eave_height):
    if peak_z <= eave_height: return None
    u2 = 1.0 - eave_height / peak_z
    return half_width * math.sqrt(u2) if u2 >= 0.0 else None
def _rib_polyline(rib_x, half_width, peak_z, n):
    y = np.linspace(-half_width, +half_width, n); u = y / half_width
    return np.column_stack([np.full_like(y, rib_x), y, peak_z * (1.0 - u ** 2)])
def _tip_x_at_eave(span, apex, eave_height, curve_type):
    if apex <= eave_height: return span / 2.0
    x_fine = np.linspace(0.0, span / 2.0, 2000); z_fine = beam_curve(x_fine, span, apex, curve_type)
    idx = np.where(z_fine >= eave_height)[0]
    return float(x_fine[idx[-1]]) if len(idx) else span / 2.0
def _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height, tip_x):
    plus, minus = [], []
    for i, xr in enumerate(rib_x):
        y_at = _rib_arch_y_at_eave(float(rib_peak_z[i]), float(rib_half_width[i]), eave_height)
        if y_at is None: continue
        plus.append((float(xr), +y_at, eave_height)); minus.append((float(xr), -y_at, eave_height))
    return np.asarray(list(plus) + [(+tip_x, 0.0, eave_height)] + list(reversed(minus)) + [(-tip_x, 0.0, eave_height)], dtype=float)
def _subdivide_polygon(anchors, subdivisions):
    loop, anchor_idx = [], []
    for i in range(anchors.shape[0]):
        a, b = anchors[i], anchors[(i + 1) % anchors.shape[0]]
        anchor_idx.append(len(loop))
        for k in range(subdivisions): loop.append(a + (b - a) * (k / float(subdivisions)))
    return np.asarray(loop, dtype=float), anchor_idx
def _cone_arc_positions(n_cones, spacing, total):
    mid = total / 2.0
    if n_cones % 2 == 1:
        half = (n_cones - 1) // 2
        ks = [0] + [k for i in range(1, half + 1) for k in (+i, -i)]
    else:
        half = n_cones // 2
        ks = [k for i in range(half) for k in (i + 0.5, -(i + 0.5))]
    return sorted([mid + k * spacing for k in ks])

def _build_true_frame(data, membrane_reactions):
    """Build the actual frame: primary beam, ribs, drop members."""
    nodes, elements = [], []
    span, apex, eave = data["span"], data["apex"], data["eave_height"]
    
    # 1. Ground nodes (Z=0) and anchor nodes (Z=eave)
    # We use the actual anchor coordinates from the mesh.
    anchor_coords = data["coords_fdm"][data["anchor_idx"]]
    n_anchors = len(anchor_coords)
    
    # Ground nodes
    for i in range(n_anchors):
        nodes.append([anchor_coords[i, 0], anchor_coords[i, 1], 0.0])
    
    # Anchor nodes
    for i in range(n_anchors):
        nodes.append([anchor_coords[i, 0], anchor_coords[i, 1], eave])
    
    # Apex node
    nodes.append([0.0, 0.0, apex])
    apex_idx = len(nodes) - 1
    
    # Crossing nodes (where ribs meet the primary beam at Y=0)
    rib_x = data.get("rib_x", [])
    crossing_indices = []
    for xr in rib_x:
        # Find Z at Y=0 (on the primary beam)
        z_at_x = float(np.interp(xr, data["xp"], data["zp"]))
        nodes.append([float(xr), 0.0, z_at_x])
        crossing_indices.append(len(nodes) - 1)
    
    # Cone connection nodes
    ring_x_positions = data.get("x_rings", [])
    cone_indices = []
    for x_ring in ring_x_positions:
        z_at_x = float(np.interp(x_ring, data["xp"], data["zp"]))
        nodes.append([float(x_ring), 0.0, z_at_x])
        cone_indices.append(len(nodes) - 1)
    
    nodes = np.asarray(nodes, dtype=float)
    
    # Use standard section properties for frame analysis
    chs = SECTION_PROPERTIES.get("CHS 168.3x7.1", {})
    sec = {"A": chs.get("A", 3550.0), "I": chs.get("I", 1.0e7), "Iy": chs.get("I", 1.0e7), "Iz": chs.get("I", 1.0e7), "J": chs.get("I", 2.0e7)}
    
    # Elements: primary beam (ground -> anchor -> crossing/cone -> apex -> ...)
    # For simplicity, we build a chain along Y=0 through all nodes with Y=0
    y_zero_node_ids = []
    for i in range(n_anchors):
        if abs(anchor_coords[i, 1]) < 1e-3: y_zero_node_ids.append(i) # ground
        if abs(anchor_coords[i, 1]) < 1e-3: y_zero_node_ids.append(n_anchors + i) # anchor
    # Add crossing and cone nodes
    y_zero_node_ids.extend(crossing_indices)
    y_zero_node_ids.extend(cone_indices)
    y_zero_node_ids.append(apex_idx)
    
    # Remove duplicates and sort by X
    y_zero_node_ids = sorted(set(y_zero_node_ids), key=lambda i: nodes[i, 0])
    for i in range(len(y_zero_node_ids) - 1):
        elements.append({"a": y_zero_node_ids[i], "b": y_zero_node_ids[i+1], "section": sec})
    
    # Ribs: for each rib, ground -> anchor -> crossing -> anchor -> ground
    for j, xr in enumerate(rib_x):
        # Find the closest crossing node
        crossing_id = crossing_indices[j]
        # Find the anchors on the rib (same X, different Y)
        rib_anchor_plus = None; rib_anchor_minus = None; ground_plus = None; ground_minus = None
        for i in range(n_anchors):
            if abs(anchor_coords[i, 0] - xr) < 1e-3:
                if anchor_coords[i, 1] > 0:
                    rib_anchor_plus = n_anchors + i; ground_plus = i
                else:
                    rib_anchor_minus = n_anchors + i; ground_minus = i
        if rib_anchor_plus is not None:
            elements.append({"a": ground_plus, "b": rib_anchor_plus, "section": sec})
            elements.append({"a": rib_anchor_plus, "b": crossing_id, "section": sec})
        if rib_anchor_minus is not None:
            elements.append({"a": ground_minus, "b": rib_anchor_minus, "section": sec})
            elements.append({"a": rib_anchor_minus, "b": crossing_id, "section": sec})
    
    # Loads: reactions at anchors
    loads = np.zeros((len(nodes), 6))
    for i in range(n_anchors):
        if membrane_reactions is not None and i < len(membrane_reactions):
            r = membrane_reactions[i]
            loads[n_anchors + i, 0] = r[0]; loads[n_anchors + i, 1] = r[1]; loads[n_anchors + i, 2] = r[2]
    
    # Fixed nodes: ground
    fixed_nodes = list(range(n_anchors))
    
    return nodes, elements, loads, fixed_nodes

def render_tester_multi_cone():
    st.markdown("<h2 style='color:#f39c12;'>Multi-Cone Roof — Tester</h2>", unsafe_allow_html=True)
    
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
    c1, c2 = st.columns(2)
    with c1: warp_q_input = st.number_input("Warp pretension (kN/m)", 0.1, 100.0, 1.0, 0.1, key="mc_warp")
    with c2: weft_q_input = st.number_input("Weft pretension (kN/m)", 0.1, 100.0, 1.0, 0.1, key="mc_weft")
    edge_q_input = st.number_input("Edge cable pretension (kN/m)", 0.1, 500.0, 5.0, 0.1, key="mc_edgeq")
    st.markdown("### Environmental Loads")
    c1, c2 = st.columns(2)
    with c1: code_choice = st.selectbox("Building Code", list(CODE_PARAMS.keys()), index=0, key="mc_code")
    with c2: design_philosophy = st.selectbox("Design Philosophy", ["Serviceability (Unfactored)", "Ultimate Limit State (Factored)"], index=0, key="mc_design_philosophy")
    c1, c2 = st.columns(2)
    with c1: wind_speed = st.number_input("Wind Speed (m/s)", 0.0, 80.0, 33.5, 1.0, key="mc_wind_speed")
    with c2: snow_depth = st.number_input("Snow Depth (m)", 0.0, 2.0, 0.0, 0.1, key="mc_snow_depth")
    payload_kg = st.number_input("Payload at apex (kg)", 0.0, 1000.0, 0.0, 10.0, key="mc_payload")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1: btn_fdm = st.button("1. Find Form (FDM)", use_container_width=True)
    with col_btn2: btn_newton = st.button("2. Structural Calculation", use_container_width=True)
    
    if btn_fdm or "fdm_results" not in st.session_state:
        xp = np.linspace(-span / 2.0, span / 2.0, 200); zp = beam_curve(xp, span, apex, curve_type); s_p, total_p = arclength_parametrisation(xp, zp)
        rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
        rib_peak_z = np.interp(rib_x, xp, zp); rib_half_width = np.array([_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float)
        try:
            s_rings = _cone_arc_positions(number_of_cones, ring_spacing, total_p)
            ring_specs = [{"cx": float(np.interp(s_val, s_p, xp)), "cy": 0.0, "cz": float(np.interp(s_val, s_p, zp)) - float(ring_clearance), "r": float(ring_diameter) / 2.0, "beam_z": float(np.interp(s_val, s_p, zp))} for s_val in s_rings]
        except ValueError as e:
            st.error("Placement refused: " + str(e)); return
        tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
        anchors = _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height, tip_x)
        perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
        bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
        L_avg = float(np.mean(np.linalg.norm(bd, axis=1))); target_len = max(L_avg, 1e-6)
        built = SDSe_mesh_rings(perimeter_loop=perimeter_loop, anchor_idx=anchor_idx, ring_specs=ring_specs, eave_height=eave_height, target_len=target_len)
        pts, edges, boundary_edge_set, tris, fixed = built["points"], built["edges"], built["boundary_edges"], built["triangles"], built["fixed_indices"]
        warp_q = max(float(warp_q_input), 0.1) * 1000.0; weft_q = max(float(weft_q_input), 0.1) * 1000.0; edge_q_scalar = max(float(edge_q_input), 0.1) * 1000.0
        pts_2d = pts[:, :2]; warp_dir = np.array([1.0, 0.0]); q_interior = SDSe_blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q)
        q = np.empty(len(edges), dtype=float)
        for k, (i, j) in enumerate(edges): q[k] = edge_q_scalar if (i, j) in boundary_edge_set or (j, i) in boundary_edge_set else q_interior[k]
        try:
            fdm = solve_fdm(pts, edges, fixed, q); coords_fdm, residual_fdm, solve_ok, solve_err = fdm["coordinates"], float(fdm["residual_norm"]), True, ""
        except Exception as e:
            coords_fdm, residual_fdm, solve_ok, solve_err = pts.copy(), float("nan"), False, str(e)
        max_edge_tension_N = edge_q_scalar * L_avg; fdm["max_edge_tension_N"] = max_edge_tension_N
        st.session_state["fdm_results"] = {"built": built, "pts": pts, "edges": edges, "tris": tris, "fixed": fixed, "coords_fdm": coords_fdm, "fdm": fdm, "residual_fdm": residual_fdm, "solve_ok": solve_ok, "solve_err": solve_err, "warp_q": warp_q, "weft_q": weft_q, "edge_q_scalar": edge_q_scalar, "span": span, "mid_width": mid_width, "apex": apex, "L_avg": L_avg, "anchor_idx": anchor_idx, "x_rings": [np.interp(s, s_p, xp) for s in s_rings], "rib_x": rib_x, "rib_peak_z": rib_peak_z, "rib_half_width": rib_half_width, "xp": xp, "zp": zp, "eave_height": eave_height}
    
    data = st.session_state.get("fdm_results")
    if not data: return
    coords_to_draw = data["coords_fdm"]
    
    if btn_newton:
        with st.spinner("Running membrane solve..."):
            cable_name, cable_A_mm2, cable_E_MPa, EA_cable = _select_edge_cable(data["fdm"]["max_edge_tension_N"], safety_factor=2.0)
            cables = []
            for k in range(len(data["anchor_idx"])):
                a_idx = data["anchor_idx"][k]; b_idx = data["anchor_idx"][(k + 1) % len(data["anchor_idx"])]
                chain = [int(a_idx)]; i_cur = (a_idx + 1) % data["pts"].shape[0]; b_int = int(b_idx); safety = 0
                while i_cur != b_int and safety < data["pts"].shape[0]:
                    chain.append(int(i_cur)); i_cur = (i_cur + 1) % data["pts"].shape[0]; safety += 1
                chain.append(int(b_int))
                for m in range(len(chain) - 1):
                    ia, ib = chain[m], chain[m + 1]; L_ref = float(np.linalg.norm(data["coords_fdm"][ib] - data["coords_fdm"][ia]))
                    if L_ref >= 1e-9: cables.append({"a": ia, "b": ib, "L0": L_ref * 1.001, "EA": EA_cable})
            apex_idx = data["built"]["beam_top_indices"][0] if len(data["built"]["beam_top_indices"]) > 0 else None
            loads = generate_uls_loads(data["coords_fdm"], data["tris"], code_choice, wind_speed, snow_depth, payload_kg, apex_idx)["uplift" if design_philosophy == "Ultimate Limit State (Factored)" else "service"]
            dr_result, final_pretension = None, None
            for p_factor in PRETENSION_STEPS:
                cur_warp, cur_weft = p_factor * 1000.0, p_factor * 1000.0
                mat = make_membrane_material(E_warp_MPa=1400.0, E_weft_MPa=1400.0, thickness_mm=1.02, nu=0.34, G_MPa=50.0, warp_prestress_N_per_m=cur_warp, weft_prestress_N_per_m=cur_weft)
                res = solve_nonlinear_equilibrium(points=data["coords_fdm"].copy(), triangles=data["tris"], fixed_indices=data["fixed"], reference_points=data["coords_fdm"].copy(), membrane_material=mat, cables=cables, loads=loads, max_iter=100, max_outer=25, tol=0.01, tol_disp=1e-5, max_total_steps=200, max_wall_seconds=15.0, seed_z_amplitude=0.001 * data["span"])
                if res["converged"]: dr_result, final_pretension = res, p_factor; break
            if dr_result is None: st.error("Membrane solver did not converge."); return
            if final_pretension > 1.0: st.warning("Converged at increased pretension: %.1f kN/m." % final_pretension)

            with st.spinner("Running steel frame solve..."):
                R = dr_result.get("reactions", None)
                nodes_frame, elements_frame, loads_frame, fixed_nodes = _build_true_frame(data, R)
                frame_result = solve_frame(nodes_frame, elements_frame, loads_frame, fixed_nodes, STEEL_MATERIALS.get("Steel", {}).get("S355", {"E": 210000.0}))
                
                # Extract true moments
                max_M_primary = max([max(mf["My"], mf["Mz"]) for mf in frame_result["member_end_forces"]], default=0.0) / 1e6
                max_N_primary = max([abs(mf["N"]) for mf in frame_result["member_end_forces"]], default=0.0) / 1000.0
                
                # Sizing
                sec_primary = _select_steel_section(max_N_primary, max_M_primary, data["span"])
                sec_rib = _select_steel_section(max_N_primary/3.0, max_M_primary/3.0, data["mid_width"])
                sec_ring = _select_steel_section(10.0, 2.0, 1.0)
                
                # Foundation
                max_base_moment = max([abs(frame_result["reactions"][i, 3]) for i in fixed_nodes], default=0.0) / 1e6
                max_base_moment = max(max_base_moment, max([abs(frame_result["reactions"][i, 4]) for i in fixed_nodes], default=0.0) / 1e6)

            coords_to_draw = dr_result["coordinates"]
            st.session_state["newton_results"] = {"dr_result": dr_result, "cable_name": cable_name, "cable_A_mm2": cable_A_mm2, "EA_cable": EA_cable, "sec_primary": sec_primary, "sec_rib": sec_rib, "sec_ring": sec_ring, "max_M_primary": max_M_primary, "max_N_primary": max_N_primary, "max_base_moment": max_base_moment, "frame_result": frame_result}

    newton_data = st.session_state.get("newton_results")
    if newton_data and not btn_newton:
        coords_to_draw = newton_data["dr_result"]["coordinates"]
        dr_result = newton_data["dr_result"]

    fig = go.Figure()
    if len(data["tris"]) > 0:
        tri = np.asarray(data["tris"], dtype=int)
        fig.add_trace(go.Mesh3d(x=coords_to_draw[:, 0], y=coords_to_draw[:, 1], z=coords_to_draw[:, 2], i=tri[:, 0], j=tri[:, 1], k=tri[:, 2], color=COL_MEMBRANE, opacity=0.55, flatshading=True, name="membrane", showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=data["xp"], y=np.zeros_like(data["xp"]), z=data["zp"], mode="lines", line=dict(color=COL_PRIMARY, width=7), name="primary beam", showlegend=False, hoverinfo="skip"))
    for i in range(len(data["rib_x"])):
        rp = _rib_polyline(float(data["rib_x"][i]), float(data["rib_half_width"][i]), float(data["rib_peak_z"][i]), 80)
        fig.add_trace(go.Scatter3d(x=rp[:, 0], y=rp[:, 1], z=rp[:, 2], mode="lines", line=dict(color=COL_RIB, width=5), name="rib", showlegend=False, hoverinfo="skip"))
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        pp = coords_to_draw[idx_list]; closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(x=closed[:, 0], y=closed[:, 1], z=closed[:, 2], mode="lines", line=dict(color=COL_RING_EDGE, width=5), name="ring", showlegend=False, hoverinfo="skip"))
        centre_i, beam_i = data["built"]["centre_indices"][k], data["built"]["beam_top_indices"][k]
        cx, cy, cz = coords_to_draw[centre_i]
        for poly_i in idx_list: fig.add_trace(go.Scatter3d(x=[cx, coords_to_draw[poly_i, 0]], y=[cy, coords_to_draw[poly_i, 1]], z=[cz, coords_to_draw[poly_i, 2]], mode="lines", line=dict(color=COL_SPOKE, width=2), name="spoke", showlegend=False, hoverinfo="skip"))
        bx, by, bz = coords_to_draw[beam_i]
        fig.add_trace(go.Scatter3d(x=[cx, bx], y=[cy, by], z=[cz, bz], mode="lines", line=dict(color=COL_DROP, width=4), name="drop", showlegend=False, hoverinfo="skip"))
    apply_common_layout(fig, data["apex"])
    st.plotly_chart(fig, use_container_width=True, key="mc_3d")

    with st.expander("Diagnostics", expanded=True):
        st.write("Membrane converged: %s" % data["solve_ok"])
        if newton_data:
            nd = newton_data["dr_result"]
            st.write("Pretension factor: %.1f" % newton_data.get("final_pretension", 1.0))
            st.write("---")
            st.write("**Steel Frame Results:**")
            st.write("Max Primary Moment: %.1f kNm" % newton_data["max_M_primary"])
            st.write("Max Primary Axial: %.1f kN" % newton_data["max_N_primary"])
            st.write("Max Base Moment: %.1f kNm" % newton_data["max_base_moment"])
            st.write("---")
            st.write("**Sized Sections:**")
            st.write("Primary Beam: **%s**" % newton_data["sec_primary"])
            st.write("Ribs: **%s**" % newton_data["sec_rib"])
            st.write("Rings/Drops: **%s**" % newton_data["sec_ring"])
            
            st.write("---")
            st.write("**Baseplate Reactions (from frame):**")
            st.write("Fx_max: %.1f kN, Fy_max: %.1f kN" % (np.max(np.abs(newton_data["frame_result"]["reactions"][:, 0])) / 1000.0, np.max(np.abs(newton_data["frame_result"]["reactions"][:, 1])) / 1000.0))

# =============================================================================
# END OF ui/workshops/tester_multi_cone.py
