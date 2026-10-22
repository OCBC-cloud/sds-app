"""Multi-Cone Roof — Lab test page.

Two-stage workflow:
    Stage 1: FDM finds the shape. User visually approves.
    Stage 2: Cable auto-sized, Newton solves with real prestress + loads.

History:
    First SDSe-only version.
    2026-10-22 - Added two-stage workflow (FDM then DR).
    2026-10-22 - Replaced DR with Newton-Raphson.
    2026-10-22 - Implemented two-step workflow.
    2026-10-22 - Fixed Reaction Forces.
    2026-10-22 - Added multi-code load generator.
    2026-10-22 - Added connection design (baseplate, J-bolts, fin plates).
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
from engine.load_generator import (
    generate_wind_load,
    generate_snow_load,
    generate_payload_load,
    CODE_PARAMS,
)
from engine.connection_design import (
    design_baseplate_and_foundation,
    design_fin_plate,
)
from data.materials import CABLE_PROPERTIES, STEEL_MATERIALS
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


# =============================================================================
# AUTO-SIZING HELPERS
# =============================================================================

def _select_edge_cable(fdm_result, safety_factor=2.0):
    """Pick the smallest cable (by area) across all families."""
    T_max_N = float(fdm_result.get("max_edge_tension_N", 0.0))
    if T_max_N <= 0:
        T_max_N = float(fdm_result.get("edge_q_scalar", 10000.0))

    design_load_N = T_max_N * safety_factor

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
                candidates.append((
                    A_mm2,
                    "%s %s" % (family_name, size),
                    A_mm2,
                    E_MPa,
                    EA_N,
                ))

    if candidates:
        candidates.sort(key=lambda c: c[0])
        _, name, A_mm2, E_MPa, EA_N = candidates[0]
        return (name, A_mm2, E_MPa, EA_N, T_max_N)

    return ("Fallback 10mm strand", 63.0, 160000, 10e9, T_max_N)


def _select_steel_section(max_axial_kN, max_moment_kNm,
                          family="CHS", grade="S355"):
    """Pick the smallest section in the family."""
    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("fy", 355)
    best = None
    for name, props in SECTION_PROPERTIES.items():
        if props.get("type") != family:
            continue
        A_mm2 = props.get("A", 1.0)
        W_el_mm3 = props.get("W_el", 1.0)
        N_Ed = max_axial_kN * 1000.0
        M_Ed = max_moment_kNm * 1e6
        N_cap = A_mm2 * fy_MPa
        M_cap = W_el_mm3 * fy_MPa
        util = (N_Ed / N_cap) + (M_Ed / M_cap)
        if util <= 0.9 and best is None:
            best = name
    return best if best else "Oversize required"


# =============================================================================
# Geometry helpers
# =============================================================================

def _ellipse_y(x, span, mid_width):
    a = span / 2.0
    b = mid_width / 2.0
    t = max(0.0, 1.0 - (x / a) ** 2)
    return b * math.sqrt(t)


def _rib_stations(n, optional_ends, span, x, s, total):
    if (not optional_ends) or n < 3:
        fracs = np.array(
            [k / (n + 1.0) for k in range(1, n + 1)], dtype=float
        )
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


def _build_eave_anchors(rib_x, rib_half_width, rib_peak_z,
                         eave_height, tip_x):
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


def _cone_arc_positions(n_cones, spacing, total):
    if n_cones < 1:
        raise ValueError("Number of cones must be at least 1.")
    mid = total / 2.0
    if n_cones % 2 == 1:
        half = (n_cones - 1) // 2
        ks = [0]
        for i in range(1, half + 1):
            ks.append(+i)
            ks.append(-i)
    else:
        half = n_cones // 2
        ks = []
        for i in range(half):
            k = i + 0.5
            ks.append(+k)
            ks.append(-k)
    positions = [mid + k * spacing for k in ks]
    for p in positions:
        if p < 0.0 or p > total:
            raise ValueError(
                "Ring position %.3f m falls outside the primary span "
                "of %.3f m. Reduce spacing or cone count." % (p, total)
            )
    return sorted(positions)


# =============================================================================
# Member schedule
# =============================================================================

def _build_member_schedule(built, coords, ring_x_positions,
                            anchor_idx, edge_q_scalar,
                            warp_q, weft_q,
                            cable_name, cable_A_mm2,
                            steel_section):
    members = []
    ring_indices = built["ring_indices"]
    centre_indices = built["centre_indices"]
    beam_top_indices = built["beam_top_indices"]
    triangles = built["triangles"]
    n_perimeter = built["n_perimeter"]

    for k in range(len(ring_indices)):
        ring_no = k + 1
        idx_list = ring_indices[k]
        centre_i = int(centre_indices[k])
        beam_i = int(beam_top_indices[k])
        n_poly = len(idx_list)

        ring_length = 0.0
        for i in range(n_poly):
            a = int(idx_list[i])
            b = int(idx_list[(i + 1) % n_poly])
            ring_length += float(np.linalg.norm(coords[b] - coords[a]))

        members.append({
            "member_id": "Ring_%d_Ring_Beam" % ring_no,
            "member_type": "ring_beam",
            "length_m": float(ring_length),
            "section": steel_section,
            "material": "S355",
            "role": "closed ring beam, one per cone",
        })

        L = float(np.linalg.norm(coords[beam_i] - coords[centre_i]))
        members.append({
            "member_id": "Ring_%d_Drop_Member" % ring_no,
            "member_type": "drop_member",
            "length_m": L,
            "section": steel_section,
            "material": "S355",
            "role": "vertical drop from primary beam to ring centre",
        })

    total_cable_length = 0.0
    for i in range(n_perimeter):
        j = (i + 1) % n_perimeter
        total_cable_length += float(np.linalg.norm(coords[j] - coords[i]))

    members.append({
        "member_id": "Edge_Cable",
        "member_type": "cable",
        "length_m": total_cable_length,
        "section": cable_name,
        "material": "A=%.1f mm2" % cable_A_mm2,
        "role": "perimeter edge cable (auto-sized)",
    })

    panel_no = 1
    for (a, b, c) in triangles:
        pa = coords[a]
        pb = coords[b]
        pc = coords[c]
        mean_edge = (
            float(np.linalg.norm(pb - pa)) +
            float(np.linalg.norm(pc - pb)) +
            float(np.linalg.norm(pa - pc))
        ) / 3.0
        members.append({
            "member_id": "Membrane_Panel_%04d" % panel_no,
            "member_type": "membrane",
            "length_m": mean_edge,
            "section": "FABRIC",
            "material": "PVDF Type III",
            "role": "fabric panel between ridge and eave",
        })
        panel_no += 1

    return members


def _format_member_table(members):
    lines = []
    header = (
        "%-26s  %-18s  %-9s  %-20s  %-20s  %s"
        % ("member_id", "member_type", "length_m",
           "section", "material", "role")
    )
    lines.append(header)
    lines.append("-" * len(header))
    for m in members:
        lines.append(
            "%-26s  %-18s  %-9.4f  %-20s  %-20s  %s"
            % (m["member_id"], m["member_type"], m["length_m"],
               str(m["section"])[:20], str(m["material"])[:20],
               m["role"])
        )
    return "\n".join(lines)


# =============================================================================
# Page
# =============================================================================

def render_tester_multi_cone():
    bcol1, bcol2, bcol3 = st.columns([1, 1, 3])
    with bcol1:
        if st.button("← Back to Lab", key="mc_back_lab",
                     use_container_width=True):
            st.session_state.page = "lab"
            st.rerun()
    with bcol2:
        if st.button("← Back to Landing", key="mc_back_landing",
                     use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()

    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>"
        "Multi-Cone Roof — Tester</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>"
        "Step 1: Find Form (FDM). Step 2: Structural Calculation (Newton).</p>",
        unsafe_allow_html=True,
    )

    # --- Inputs ---
    c1, c2 = st.columns(2)
    with c1:
        span = st.number_input("Primary span (m)", 6.0, 60.0, 10.0, 0.5,
                                key="mc_span")
    with c2:
        apex = st.number_input("Primary apex (m)", 1.0, 30.0, 5.0, 0.5,
                                key="mc_apex")

    c1, c2 = st.columns(2)
    with c1:
        mid_width = st.number_input("Mid-span width (m)", 6.0, 60.0, 10.0, 0.5,
                                     key="mc_width")
    with c2:
        eave_height = st.number_input("Eave height (m)", 0.5, 10.0, 2.8, 0.1,
                                       key="mc_eave")

    c1, c2 = st.columns(2)
    with c1:
        ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 1.0, 0.1,
                                         key="mc_rd")
    with c2:
        curve_type = st.selectbox(
            "Curve type", ["parabolic", "circular", "catenary"],
            index=0, key="mc_curve",
        )

    c1, c2 = st.columns(2)
    with c1:
        secondary_count = int(st.number_input(
            "Secondary count", 2, 20, 3, 1, key="mc_nribs"
        ))
    with c2:
        optional_ends = st.toggle("Optional ends", value=False,
                                    key="mc_optends")

    subdivisions = int(st.number_input(
        "Subdivisions per edge", 5, 25, 5, 1, key="mc_subdiv"
    ))

    c1, c2 = st.columns(2)
    with c1:
        number_of_cones = int(st.number_input(
            "Number of cones", 1, 20, 1, 1, key="mc_ncones"
        ))
    with c2:
        ring_spacing = st.number_input(
            "Distance between adjacent cones (m, along beam)",
            0.5, 10.0, 5.0, 0.1, key="mc_spacing"
        )

    ring_clearance = st.number_input(
        "Ring clearance below beam (m)", 0.1, 5.0, 1.0, 0.1,
        key="mc_clr",
    )

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
        "Edge cable pretension (kN/m)",
        0.1, 500.0, 1.0, 0.1,
        key="mc_edgeq",
    )

    st.markdown("### Environmental Loads")
    
    code_choice = st.selectbox(
        "Building Code", 
        list(CODE_PARAMS.keys()),
        index=0,
        key="mc_code"
    )

    c1, c2 = st.columns(2)
    with c1:
        wind_speed = st.number_input(
            "Wind Speed (m/s)", 0.0, 80.0, 30.0, 1.0, key="mc_wind_speed"
        )
    with c2:
        snow_depth = st.number_input(
            "Snow Depth (m)", 0.0, 2.0, 0.0, 0.1, key="mc_snow_depth"
        )
    
    payload_kg = st.number_input(
        "Payload at apex (kg)", 0.0, 1000.0, 0.0, 10.0, key="mc_payload"
    )

    # --- THE TWO BUTTONS ---
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        btn_fdm = st.button("1. Find Form (FDM)", use_container_width=True)
    with col_btn2:
        btn_newton = st.button("2. Structural Calculation", use_container_width=True)

    if btn_fdm or "fdm_results" not in st.session_state:
        # --- Run FDM ---
        xp = np.linspace(-span / 2.0, span / 2.0, 200)
        zp = beam_curve(xp, span, apex, curve_type)
        s_p, total_p = arclength_parametrisation(xp, zp)

        rib_x = _rib_stations(secondary_count, optional_ends, span,
                              xp, s_p, total_p)
        rib_peak_z = np.interp(rib_x, xp, zp)
        rib_half_width = np.array(
            [_ellipse_y(float(xr), span, mid_width) for xr in rib_x],
            dtype=float,
        )

        try:
            s_rings = _cone_arc_positions(number_of_cones, ring_spacing, total_p)
            ring_specs = []
            for s_val in s_rings:
                x_val = float(np.interp(s_val, s_p, xp))
                bz_val = float(np.interp(s_val, s_p, zp))
                rz_val = bz_val - float(ring_clearance)
                ring_specs.append({
                    "cx": x_val, "cy": 0.0, "cz": rz_val,
                    "r": float(ring_diameter) / 2.0,
                    "beam_z": bz_val,
                })
        except ValueError as e:
            st.error("Placement refused: " + str(e))
            return

        tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
        anchors = _build_eave_anchors(
            rib_x, rib_half_width, rib_peak_z, eave_height, tip_x
        )
        perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
        bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
        L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
        target_len = max(L_avg, 1e-6)

        built = SDSe_mesh_rings(
            perimeter_loop=perimeter_loop,
            anchor_idx=anchor_idx,
            ring_specs=ring_specs,
            eave_height=eave_height,
            target_len=target_len,
        )

        pts = built["points"]
        edges = built["edges"]
        boundary_edge_set = built["boundary_edges"]
        tris = built["triangles"]
        fixed = built["fixed_indices"]

        warp_q = max(float(warp_q_input), 0.1) * 1000.0
        weft_q = max(float(weft_q_input), 0.1) * 1000.0
        edge_q_scalar = max(float(edge_q_input), 0.1) * 1000.0

        pts_2d = pts[:, :2]
        warp_dir = np.array([1.0, 0.0])
        q_interior = SDSe_blend_q_per_edge(
            edges, pts_2d, warp_dir, warp_q, weft_q
        )

        q = np.empty(len(edges), dtype=float)
        for k, (i, j) in enumerate(edges):
            key = (i, j) if i < j else (j, i)
            if key in boundary_edge_set:
                q[k] = edge_q_scalar
            else:
                q[k] = q_interior[k]

        try:
            fdm = solve_fdm(pts, edges, fixed, q)
            coords_fdm = fdm["coordinates"]
            residual_fdm = float(fdm["residual_norm"])
            solve_ok = True
            solve_err = ""
        except Exception as e:
            coords_fdm = pts.copy()
            residual_fdm = float("nan")
            solve_ok = False
            solve_err = str(e)

        max_edge_tension_N = edge_q_scalar * L_avg
        fdm["max_edge_tension_N"] = max_edge_tension_N
        fdm["edge_q_scalar"] = edge_q_scalar

        # Save to session state so Step 2 can use it
        st.session_state["fdm_results"] = {
            "built": built,
            "pts": pts,
            "edges": edges,
            "tris": tris,
            "fixed": fixed,
            "coords_fdm": coords_fdm,
            "fdm": fdm,
            "residual_fdm": residual_fdm,
            "solve_ok": solve_ok,
            "solve_err": solve_err,
            "warp_q": warp_q,
            "weft_q": weft_q,
            "edge_q_scalar": edge_q_scalar,
            "span": span,
            "apex": apex,
            "L_avg": L_avg,
            "anchor_idx": anchor_idx,
            "x_rings": [np.interp(s, s_p, xp) for s in s_rings],
            "rib_x": rib_x,
            "rib_peak_z": rib_peak_z,
            "rib_half_width": rib_half_width,
            "xp": xp,
            "zp": zp,
        }

    data = st.session_state.get("fdm_results")
    if not data:
        return

    # --- SHOW FDM SHAPE ---
    coords_to_draw = data["coords_fdm"]
    dr_result = None

    if btn_newton:
        with st.spinner("Running Structural Calculation (Newton)..."):
            # Rebuild cables and materials from saved state
            cable_name, cable_A_mm2, cable_E_MPa, EA_cable, cable_T_fdm = \
                _select_edge_cable(data["fdm"], safety_factor=2.0)

            beam_axial_kN = data["fdm"]["max_edge_tension_N"] / 1000.0
            beam_moment_kNm = (beam_axial_kN * data["span"]) / 8.0
            steel_section = _select_steel_section(
                beam_axial_kN, beam_moment_kNm,
                family="CHS", grade="S355",
            )

            cables = []
            n_a = len(data["anchor_idx"])
            pts = data["pts"]
            coords_fdm = data["coords_fdm"]

            for k in range(n_a):
                a_idx = data["anchor_idx"][k]
                b_idx = data["anchor_idx"][(k + 1) % n_a]
                chain = [int(a_idx)]
                i_cur = (a_idx + 1) % pts.shape[0]
                b_int = int(b_idx)
                safety = 0
                while i_cur != b_int and safety < pts.shape[0]:
                    chain.append(int(i_cur))
                    i_cur = (i_cur + 1) % pts.shape[0]
                    safety += 1
                chain.append(int(b_int))
                for m in range(len(chain) - 1):
                    ia = chain[m]
                    ib = chain[m + 1]
                    L_ref = float(np.linalg.norm(coords_fdm[ib] - coords_fdm[ia]))
                    if L_ref < 1e-9:
                        continue
                    # Slack initial cable
                    L0 = L_ref * 1.001
                    cables.append({
                        "a": ia, "b": ib, "L0": L0, "EA": EA_cable,
                    })

            material = make_membrane_material(
                E_warp_MPa=1400.0, E_weft_MPa=1400.0, thickness_mm=1.02,
                nu=0.34, G_MPa=50.0,
                warp_prestress_N_per_m=data["warp_q"],
                weft_prestress_N_per_m=data["weft_q"],
            )

            # --- APPLY LOADS ---
            loads = np.zeros((pts.shape[0], 3), dtype=float)
            
            # 1. Snow Load
            if snow_depth > 0:
                loads += generate_snow_load(coords_fdm, data["tris"], snow_depth, code_choice)
                
            # 2. Wind Load (Uplift)
            if wind_speed > 0:
                loads += generate_wind_load(coords_fdm, data["tris"], wind_speed, code_choice)

            # 3. Payload
            if payload_kg > 0 and len(data["built"]["beam_top_indices"]) > 0:
                apex_idx = data["built"]["beam_top_indices"][0]
                loads += generate_payload_load(coords_fdm, apex_idx, payload_kg)

            dr_result = solve_nonlinear_equilibrium(
                points=coords_fdm.copy(),
                triangles=data["tris"],
                fixed_indices=data["fixed"],
                reference_points=coords_fdm.copy(),
                membrane_material=material,
                cables=cables,
                loads=loads,
                max_iter=100,
                max_outer=25,
                tol=1.5,
                tol_disp=1e-5,
                max_total_steps=200,
                max_wall_seconds=50.0,
                seed_z_amplitude=0.001 * data["span"],
            )
            
            coords_to_draw = dr_result["coordinates"]

            # Save the results so they don't vanish on next rerun
            st.session_state["newton_results"] = {
                "dr_result": dr_result,
                "cable_name": cable_name,
                "cable_A_mm2": cable_A_mm2,
                "EA_cable": EA_cable,
                "steel_section": steel_section,
                "beam_axial_kN": beam_axial_kN,
                "beam_moment_kNm": beam_moment_kNm,
                "cables": cables,
                "material": material,
            }

    # Load newton results if they exist
    newton_data = st.session_state.get("newton_results")
    if newton_data and not btn_newton:
        coords_to_draw = newton_data["dr_result"]["coordinates"]
        dr_result = newton_data["dr_result"]

    # --- DRAW ---
    fig = go.Figure()

    if len(data["tris"]) > 0:
        tri = np.asarray(data["tris"], dtype=int)
        fig.add_trace(go.Mesh3d(
            x=coords_to_draw[:, 0], y=coords_to_draw[:, 1], z=coords_to_draw[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            name="membrane", showlegend=False, hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter3d(
        x=data["xp"], y=np.zeros_like(data["xp"]), z=data["zp"],
        mode="lines", line=dict(color=COL_PRIMARY, width=7),
        name="primary beam", showlegend=False, hoverinfo="skip",
    ))

    for i in range(len(data["rib_x"])):
        rp = _rib_polyline(
            float(data["rib_x"][i]), float(data["rib_half_width"][i]),
            float(data["rib_peak_z"][i]), RIB_SEGMENTS,
        )
        fig.add_trace(go.Scatter3d(
            x=rp[:, 0], y=rp[:, 1], z=rp[:, 2],
            mode="lines", line=dict(color=COL_RIB, width=5),
            name="rib", showlegend=False, hoverinfo="skip",
        ))

    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        pp = coords_to_draw[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(
            x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5),
            name="ring", showlegend=False, hoverinfo="skip",
        ))
        centre_i = data["built"]["centre_indices"][k]
        beam_i = data["built"]["beam_top_indices"][k]
        cx, cy, cz = coords_to_draw[centre_i]
        for poly_i in idx_list:
            fig.add_trace(go.Scatter3d(
                x=[cx, coords_to_draw[poly_i, 0]],
                y=[cy, coords_to_draw[poly_i, 1]],
                z=[cz, coords_to_draw[poly_i, 2]],
                mode="lines", line=dict(color=COL_SPOKE, width=2),
                name="spoke", showlegend=False, hoverinfo="skip",
            ))
        bx, by, bz = coords_to_draw[beam_i]
        fig.add_trace(go.Scatter3d(
            x=[cx, bx], y=[cy, by], z=[cz, bz],
            mode="lines", line=dict(color=COL_DROP, width=4),
            name="drop", showlegend=False, hoverinfo="skip",
        ))

    apply_common_layout(fig, data["apex"])
    st.plotly_chart(fig, use_container_width=True, key="mc_3d")

    # --- DIAGNOSTICS ---
    with st.expander("Diagnostics", expanded=True):
        st.write("Number of cones: %d" % number_of_cones)
        st.write("Total mesh nodes: %d" % data["pts"].shape[0])
        st.write("Mesh edges: %d" % len(data["edges"]))
        st.write("Mesh triangles: %d" % len(data["tris"]))
        st.write("Held nodes (total): %d" % len(data["fixed"]))

        st.write("---")
        st.write("**Stage 1 — FDM:**")
        st.write("FDM Solve OK: %s" % data["solve_ok"])
        if not data["solve_ok"]:
            st.write("FDM error: %s" % data["solve_err"])
        else:
            st.write("FDM force imbalance (N): %.6e" % data["residual_fdm"])
            st.write("FDM estimated edge tension (N): %.1f"
                     % data["fdm"]["max_edge_tension_N"])

        if newton_data:
            nd = newton_data["dr_result"]
            st.write("---")
            st.write("**Stage 2 — Newton:**")
            st.write("Newton converged: %s" % nd["converged"])
            st.write("Newton iterations: %d" % nd["iterations"])
            st.write("Newton total steps: %d" % nd.get("total_steps", 0))
            st.write("Newton residual (N): %.6e" % nd["residual_norm"])
            st.write("Newton max residual (N): %.6e"
                     % nd.get("max_residual", nd["residual_norm"]))
            st.write("Newton time (s): %.2f" % nd["elapsed_seconds"])
            st.write("Newton reason: %s" % nd.get("reason", ""))
            st.write("Seed applied (m): %.6f" % nd.get("seed_applied_m", 0.0))

            # --- REACTION FORCES & CONNECTION DESIGN ---
            st.write("---")
            st.write("**Reaction Forces & Foundation Design:**")
            R = nd.get("reactions", None)
            if R is not None:
                fixed_indices = data["fixed"]
                if len(fixed_indices) > 0:
                    Rx_total = float(np.sum(R[fixed_indices, 0]))
                    Ry_total = float(np.sum(R[fixed_indices, 1]))
                    Rz_total = float(np.sum(R[fixed_indices, 2]))
                    st.write("Total Rx (N): %.2f" % Rx_total)
                    st.write("Total Ry (N): %.2f" % Ry_total)
                    st.write("Total Rz (N): %.2f" % Rz_total)
                    
                    # Find the worst-case node (largest magnitude reaction)
                    mags = np.linalg.norm(R[fixed_indices], axis=1)
                    worst_idx = np.argmax(mags)
                    nd_idx = fixed_indices[worst_idx]
                    worst_R = R[nd_idx]
                    
                    st.write("---")
                    st.write("**Worst-Case Baseplate & Foundation (Node %d):**" % nd_idx)
                    st.write("Reaction: Fx=%.1f, Fy=%.1f, Fz=%.1f (N)" % (worst_R[0], worst_R[1], worst_R[2]))
                    
                    design = design_baseplate_and_foundation(worst_R)
                    st.code(
                        "Baseplate: %d x %d x %d mm\n"
                        "Anchor Bolts: %d x M%d J-Bolts (Embed: %d mm)\n"
                        "Concrete Stump: %d x %d mm\n"
                        "Concrete Grade: %s"
                        % (
                            design["plate_side_mm"], design["plate_side_mm"], design["plate_thickness_mm"],
                            design["bolt_count"], design["bolt_diameter_mm"], design["bolt_embedment_mm"],
                            design["stump_side_mm"], design["stump_side_mm"],
                            design["concrete_grade"]
                        ),
                        language="text"
                    )
                    
                    # --- FIN PLATE DESIGN ---
                    st.write("---")
                    st.write("**Corner / Fin Plate Design (Edge Cable):**")
                    max_cable_T = 5000.0  # Fallback
                    if "cable_tension_list" in nd and len(nd["cable_tension_list"]) > 0:
                        max_cable_T = max(c["T_N"] for c in nd["cable_tension_list"])
                    
                    st.write("Max Cable Tension: %.1f N" % max_cable_T)
                    fin = design_fin_plate(max_cable_T, newton_data["cable_A_mm2"]**0.5)
                    st.code(
                        "Fin Plate Thickness: %d mm\n"
                        "Weld Size: %d mm fillet\n"
                        "Cable Diameter: %d mm"
                        % (
                            fin["fin_plate_thickness_mm"],
                            fin["weld_size_mm"],
                            fin["cable_diameter_mm"]
                        ),
                        language="text"
                    )
            else:
                st.write("Reactions not available in solver output.")

            hist = nd.get("history", [])
            if hist:
                st.write("Newton history (last 5 steps):")
                for row in hist[-5:]:
                    st.write("  outer=%s  inner=%s  ||R||=%.4e  max|R|=%.4e"
                             % (row[0], row[1], row[2], row[3]))

            # Member Schedule
            members = _build_member_schedule(
                data["built"], coords_to_draw, data["x_rings"],
                data["anchor_idx"], data["edge_q_scalar"], data["warp_q"], data["weft_q"],
                newton_data["cable_name"], newton_data["cable_A_mm2"], newton_data["steel_section"],
            )

            with st.expander("Member schedule (auto-sized)", expanded=True):
                st.write("Edge cable: **%s** (A=%.1f mm2)"
                         % (newton_data["cable_name"], newton_data["cable_A_mm2"]))
                st.write("Steel section: **%s**" % newton_data["steel_section"])
                st.write("Total members recorded: %d" % len(members))
                st.code(_format_member_table(members), language="text")

# =============================================================================
# END OF ui/workshops/tester_multi_cone.py
# =============================================================================
