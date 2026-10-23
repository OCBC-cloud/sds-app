"""Multi-Cone Roof — Lab test page.

Two-stage workflow:
    Stage 1: FDM finds the shape.
    Stage 2: Automated pretension search + Newton solve.
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
    CODE_PARAMS,
    generate_uls_loads,
)
from engine.connection_design import (
    design_baseplate_and_foundation,
    design_corner_plate,
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

# Max pretension limited to 10.0 kN/m for PVDF fabric safety
PRETENSION_STEPS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]
UTILIZATION_WARN_THRESHOLD = 0.60


# =============================================================================
# AUTO-SIZING HELPERS
# =============================================================================

def _select_edge_cable(actual_max_tension_N, safety_factor=2.0):
    """Pick the smallest cable (by area) across all families."""
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
                candidates.append((A_mm2, "%s %s" % (family_name, size), A_mm2, E_MPa, EA_N))

    if candidates:
        candidates.sort(key=lambda c: c[0])
        _, name, A_mm2, E_MPa, EA_N = candidates[0]
        return (name, A_mm2, E_MPa, EA_N)

    return ("Fallback 10mm strand", 63.0, 160000, 10e9)


def _section_radius_of_gyration(section_name):
    """Return radius of gyration (mm). Tries r, then sqrt(I/A), then 0.35*d for CHS."""
    props = SECTION_PROPERTIES.get(section_name, {})
    if "r" in props and props["r"]:
        return float(props["r"])
    if "I" in props and props.get("I") and props.get("A"):
        try:
            return math.sqrt(float(props["I"]) / float(props["A"]))
        except Exception:
            pass
    if "d" in props and props["d"]:
        # Conservative approximation for a CHS: r ~ 0.35 * d
        return 0.35 * float(props["d"])
    return None


def _steel_capacity_ratios(section_name, max_axial_kN, max_moment_kNm,
                           member_length_m, E_MPa=210000, grade="S355"):
    """Single source of truth for steel utilization.

    Returns (interaction_util, buckling_util).
    """
    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("fy", 355)
    props = SECTION_PROPERTIES.get(section_name, {})
    A_mm2 = props.get("A", 1.0)
    W_el_mm3 = props.get("W_el", 1.0)

    N_Ed = max_axial_kN * 1000.0
    M_Ed = max_moment_kNm * 1e6

    N_cap = A_mm2 * fy_MPa
    M_cap = W_el_mm3 * fy_MPa
    interaction_util = (N_Ed / N_cap) + (M_Ed / M_cap)

    # --- Euler buckling, L_eff = L ---
    r_mm = _section_radius_of_gyration(section_name)
    if r_mm is None or r_mm <= 0.0 or A_mm2 <= 0.0:
        buckling_util = 1.0e9
    else:
        L_eff_mm = float(member_length_m) * 1000.0
        I_mm4 = A_mm2 * (r_mm ** 2)
        N_cr_N = (math.pi ** 2) * E_MPa * I_mm4 / (L_eff_mm ** 2)
        if N_Ed <= 0.0:
            buckling_util = 0.0
        else:
            buckling_util = N_Ed / N_cr_N if N_cr_N > 0.0 else 1.0e9

    return interaction_util, buckling_util


def _select_steel_section(max_axial_kN, max_moment_kNm, member_length_m,
                          family="CHS", grade="S355"):
    """Pick the smallest section in the family that satisfies
    yield interaction (<=1.0) and Euler buckling (<=1.0), with L_eff = L.
    """
    best = None
    for name, props in SECTION_PROPERTIES.items():
        if props.get("type") != family:
            continue
        interaction_util, buckling_util = _steel_capacity_ratios(
            name, max_axial_kN, max_moment_kNm, member_length_m, grade=grade
        )
        if interaction_util <= 1.0 and buckling_util <= 1.0 and best is None:
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
            raise ValueError("Ring position %.3f m falls outside the primary span of %.3f m." % (p, total))
    return sorted(positions)


# =============================================================================
# Member schedule
# =============================================================================

def _build_member_schedule(built, coords, ring_x_positions, anchor_idx, edge_q_scalar,
                           warp_q, weft_q, cable_name, cable_A_mm2, steel_section,
                           eave_height, span, mid_width):
    members = []
    ring_indices = built["ring_indices"]
    centre_indices = built["centre_indices"]
    beam_top_indices = built["beam_top_indices"]
    triangles = built["triangles"]
    n_perimeter = built["n_perimeter"]

    primary_beam_length = span * 1.2
    members.append({"member_id": "Primary_Beam_Main", "member_type": "primary_beam", "length_m": float(primary_beam_length), "section": steel_section, "material": "S355", "role": "Main arched beam from ground to ground"})

    rib_length = mid_width * 1.5
    for i in range(3):
        members.append({"member_id": "Rib_Beam_%d" % (i+1), "member_type": "rib_beam", "length_m": float(rib_length), "section": steel_section, "material": "S355", "role": "Secondary arched beam from primary beam to ground"})

    stub_length = eave_height
    for i in range(len(anchor_idx)):
        members.append({"member_id": "Stub_Col_%d" % (i+1), "member_type": "stub_column", "length_m": float(stub_length), "section": steel_section, "material": "S355", "role": "Vertical stub from eave to baseplate"})

    for k in range(len(ring_indices)):
        ring_no = k + 1
        idx_list = ring_indices[k]
        n_poly = len(idx_list)
        ring_length = 0.0
        for i in range(n_poly):
            a = int(idx_list[i])
            b = int(idx_list[(i + 1) % n_poly])
            ring_length += float(np.linalg.norm(coords[b] - coords[a]))
        members.append({"member_id": "Ring_%d_Ring_Beam" % ring_no, "member_type": "ring_beam", "length_m": float(ring_length), "section": steel_section, "material": "S355", "role": "closed ring beam, one per cone"})

        centre_i = int(centre_indices[k])
        beam_i = int(beam_top_indices[k])
        L = float(np.linalg.norm(coords[beam_i] - coords[centre_i]))
        members.append({"member_id": "Ring_%d_Drop_Member" % ring_no, "member_type": "drop_member", "length_m": L, "section": steel_section, "material": "S355", "role": "vertical drop from primary beam to ring centre"})

    total_cable_length = 0.0
    for i in range(n_perimeter):
        j = (i + 1) % n_perimeter
        total_cable_length += float(np.linalg.norm(coords[j] - coords[i]))
    members.append({"member_id": "Edge_Cable", "member_type": "cable", "length_m": total_cable_length, "section": cable_name, "material": "A=%.1f mm2" % cable_A_mm2, "role": "perimeter edge cable (auto-sized)"})

    panel_no = 1
    for (a, b, c) in triangles:
        pa, pb, pc = coords[a], coords[b], coords[c]
        mean_edge = (float(np.linalg.norm(pb - pa)) + float(np.linalg.norm(pc - pb)) + float(np.linalg.norm(pa - pc))) / 3.0
        members.append({"member_id": "Membrane_Panel_%04d" % panel_no, "member_type": "membrane", "length_m": mean_edge, "section": "FABRIC", "material": "PVDF Type III", "role": "fabric panel between ridge and eave"})
        panel_no += 1

    return members


def _format_member_table(members):
    lines = []
    header = "%-26s  %-18s  %-9s  %-20s  %-20s  %s" % ("member_id", "member_type", "length_m", "section", "material", "role")
    lines.append(header)
    lines.append("-" * len(header))
    for m in members:
        lines.append("%-26s  %-18s  %-9.4f  %-20s  %-20s  %s" % (m["member_id"], m["member_type"], m["length_m"], str(m["section"])[:20], str(m["material"])[:20], m["role"]))
    return "\n".join(lines)


# =============================================================================
# Page
# =============================================================================

def render_tester_multi_cone():
    bcol1, bcol2, bcol3 = st.columns([1, 1, 3])
    with bcol1:
        if st.button("← Back to Lab", key="mc_back_lab", use_container_width=True):
            st.session_state.page = "lab"
            st.rerun()
    with bcol2:
        if st.button("← Back to Landing", key="mc_back_landing", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()

    st.markdown("<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Multi-Cone Roof — Tester</h2><p style='color:#a8b8c8;margin-top:0;'>Step 1: Find Form (FDM). Step 2: Automated Structural Solve.</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        span = st.number_input("Primary span (m)", 6.0, 60.0, 10.0, 0.5, key="mc_span")
    with c2:
        apex = st.number_input("Primary apex (m)", 1.0, 30.0, 5.0, 0.5, key="mc_apex")

    c1, c2 = st.columns(2)
    with c1:
        mid_width = st.number_input("Mid-span width (m)", 6.0, 60.0, 10.0, 0.5, key="mc_width")
    with c2:
        eave_height = st.number_input("Eave height (m)", 0.5, 10.0, 2.8, 0.1, key="mc_eave")

    c1, c2 = st.columns(2)
    with c1:
        ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 1.0, 0.1, key="mc_rd")
    with c2:
        curve_type = st.selectbox("Curve type", ["parabolic", "circular", "catenary"], index=0, key="mc_curve")

    c1, c2 = st.columns(2)
    with c1:
        secondary_count = int(st.number_input("Secondary count", 2, 20, 3, 1, key="mc_nribs"))
    with c2:
        optional_ends = st.toggle("Optional ends", value=False, key="mc_optends")

    subdivisions = int(st.number_input("Subdivisions per edge", 5, 25, 5, 1, key="mc_subdiv"))

    c1, c2 = st.columns(2)
    with c1:
        number_of_cones = int(st.number_input("Number of cones", 1, 20, 1, 1, key="mc_ncones"))
    with c2:
        ring_spacing = st.number_input("Distance between adjacent cones (m, along beam)", 0.5, 10.0, 5.0, 0.1, key="mc_spacing")

    ring_clearance = st.number_input("Ring clearance below beam (m)", 0.1, 5.0, 1.0, 0.1, key="mc_clr")

    c1, c2 = st.columns(2)
    with c1:
        warp_q_input = st.number_input("Warp pretension (kN/m)", 0.1, 100.0, 1.0, 0.1, key="mc_warp")
    with c2:
        weft_q_input = st.number_input("Weft pretension (kN/m)", 0.1, 100.0, 1.0, 0.1, key="mc_weft")

    edge_q_input = st.number_input("Edge cable pretension (kN/m)", 0.1, 500.0, 5.0, 0.1, key="mc_edgeq")

    st.markdown("### Environmental Loads & Design Philosophy")

    c1, c2 = st.columns(2)
    with c1:
        code_choice = st.selectbox("Building Code", list(CODE_PARAMS.keys()), index=0, key="mc_code")
    with c2:
        design_philosophy = st.selectbox("Design Philosophy", ["Serviceability (Unfactored)", "Ultimate Limit State (Factored)"], index=0, key="mc_design_philosophy")

    c1, c2 = st.columns(2)
    with c1:
        wind_speed = st.number_input("Wind Speed (m/s)", 0.0, 80.0, 33.5, 1.0, key="mc_wind_speed")
    with c2:
        snow_depth = st.number_input("Snow Depth (m)", 0.0, 2.0, 0.0, 0.1, key="mc_snow_depth")

    payload_kg = st.number_input("Payload at apex (kg)", 0.0, 1000.0, 0.0, 10.0, key="mc_payload")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        btn_fdm = st.button("1. Find Form (FDM)", use_container_width=True)
    with col_btn2:
        btn_newton = st.button("2. Structural Calculation", use_container_width=True)

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
            st.error("Placement refused: " + str(e))
            return

        tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
        anchors = _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height, tip_x)
        perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
        bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
        L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
        target_len = max(L_avg, 1e-6)

        built = SDSe_mesh_rings(perimeter_loop=perimeter_loop, anchor_idx=anchor_idx, ring_specs=ring_specs, eave_height=eave_height, target_len=target_len)

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
        q_interior = SDSe_blend_q_per_edge(edges, pts_2d, warp_dir, warp_q, weft_q)

        q = np.empty(len(edges), dtype=float)
        for k, (i, j) in enumerate(edges):
            key = (i, j) if i < j else (j, i)
            q[k] = edge_q_scalar if key in boundary_edge_set else q_interior[k]

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

    if btn_newton:
        with st.spinner("Running Automated Structural Calculation..."):
            cable_name, cable_A_mm2, cable_E_MPa, EA_cable = _select_edge_cable(data["fdm"]["max_edge_tension_N"], safety_factor=2.0)

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
                    cables.append({"a": ia, "b": ib, "L0": L_ref * 1.001, "EA": EA_cable})

            apex_idx = data["built"]["beam_top_indices"][0] if len(data["built"]["beam_top_indices"]) > 0 else None

            if design_philosophy == "Ultimate Limit State (Factored)":
                loads = generate_uls_loads(coords_fdm, data["tris"], code_choice, wind_speed, snow_depth, payload_kg, apex_idx)["uplift"]
                st.info("Running ULS Uplift Case. Check Diagnostics for Foundation Uplift design.")
            else:
                loads = generate_uls_loads(coords_fdm, data["tris"], code_choice, wind_speed, snow_depth, payload_kg, apex_idx)["service"]

            dr_result = None
            final_pretension = None

            for p_factor in PRETENSION_STEPS:
                cur_warp = p_factor * 1000.0
                cur_weft = p_factor * 1000.0
                cur_cable = p_factor * 5.0 * 1000.0

                mat = make_membrane_material(
                    E_warp_MPa=1400.0, E_weft_MPa=1400.0, thickness_mm=1.02, nu=0.34, G_MPa=50.0,
                    warp_prestress_N_per_m=cur_warp, weft_prestress_N_per_m=cur_weft,
                )

                res = solve_nonlinear_equilibrium(
                    points=coords_fdm.copy(), triangles=data["tris"], fixed_indices=data["fixed"], reference_points=coords_fdm.copy(),
                    membrane_material=mat, cables=cables, loads=loads,
                    max_iter=100, max_outer=25, tol=0.01, tol_disp=1e-5, max_total_steps=200, max_wall_seconds=15.0, seed_z_amplitude=0.001 * data["span"],
                )

                if res["converged"]:
                    dr_result = res
                    final_pretension = p_factor
                    break

            if dr_result is None:
                st.error("This geometry requires a membrane pretension above %.1f kN/m to hold its shape under %.1f m/s wind. This exceeds the maximum safe limit for PVDF fabric. You MUST add more ribs (increase secondary count) or add more cones to reduce the unsupported span." % (PRETENSION_STEPS[-1], wind_speed))
                return

            if final_pretension > 1.0:
                st.warning("Converged at increased pretension: %.1f kN/m membrane, %.1f kN/m cable." % (final_pretension, final_pretension * 5.0))

            if final_pretension > 6.0:
                st.warning("High Pretension Warning: The solver needed %.1f kN/m to converge. PVDF fabric typically operates at 1-3 kN/m. At this level, you must verify the fabric's tear strength. Consider adding more ribs or increasing the apex." % final_pretension)

            if "cable_tension_list" in dr_result and len(dr_result["cable_tension_list"]) > 0:
                max_actual_T = max([c["T_N"] for c in dr_result["cable_tension_list"]])
            else:
                max_actual_T = data["fdm"]["max_edge_tension_N"]

            max_actual_T = max(max_actual_T, data["fdm"]["max_edge_tension_N"])

            if len(data["anchor_idx"]) > 0:
                total_perimeter = 0.0
                n_anchors = len(data["anchor_idx"])
                for k in range(n_anchors):
                    a_idx = data["anchor_idx"][k]
                    b_idx = data["anchor_idx"][(k + 1) % n_anchors]
                    L_segment = float(np.linalg.norm(data["coords_fdm"][b_idx] - data["coords_fdm"][a_idx]))
                    total_perimeter += L_segment
            else:
                total_perimeter = data["span"] * 4.0

            baseline_tension_N = data["edge_q_scalar"] * total_perimeter
            design_tension_N = max(max_actual_T, baseline_tension_N)

            cable_name, cable_A_mm2, cable_E_MPa, EA_cable = _select_edge_cable(design_tension_N, safety_factor=2.0)

            if "reactions" in dr_result and len(dr_result["reactions"]) > 0:
                max_reaction_kN = max([math.sqrt(r[0]**2 + r[1]**2 + r[2]**2)/1000.0 for r in dr_result["reactions"]])
            else:
                max_reaction_kN = data["fdm"]["max_edge_tension_N"] / 1000.0

            governing_member_length_m = data["span"] * 1.2
            steel_section = _select_steel_section(
                max_reaction_kN,
                (max_reaction_kN * data["span"]) / 8.0,
                governing_member_length_m,
                family="CHS", grade="S355",
            )

            interaction_util, buckling_util = _steel_capacity_ratios(
                steel_section, max_reaction_kN, (max_reaction_kN * data["span"]) / 8.0,
                governing_member_length_m,
            )
            util = max(interaction_util, buckling_util)

            if util > UTILIZATION_WARN_THRESHOLD:
                st.warning(
                    "Warning: Steel section utilization is at %.0f%% "
                    "(interaction %.0f%%, buckling %.0f%%). "
                    "Consider adding more ribs to reduce the unsupported membrane surface, "
                    "or adding more cones to provide more pull holding supports." % (
                        util * 100.0, interaction_util * 100.0, buckling_util * 100.0
                    )
                )

            # --- SMART AUTO-SIZE BUTTON ---
            st.markdown("---")
            st.write("### Member Sizing Recommendation")
            if util > UTILIZATION_WARN_THRESHOLD:
                st.write("The current section **%s** is at **%.0f%%** utilization." % (steel_section, util * 100.0))
                if st.checkbox("Auto-recommend a larger steel section", key="auto_size_check"):
                    keys = [k for k, v in SECTION_PROPERTIES.items() if v.get("type") == "CHS"]
                    keys.sort(key=lambda k: SECTION_PROPERTIES[k].get("A", 0.0))
                    try:
                        current_idx = keys.index(steel_section)
                        next_section = keys[current_idx + 1] if current_idx + 1 < len(keys) else steel_section
                    except ValueError:
                        next_section = steel_section
                        
                    st.success("Recommendation: Oversize to **%s**" % next_section)
                    steel_section = next_section
                    
                    st.write("---")
                    st.write("### Membrane Support Recommendation")
                    if final_pretension > 3.0:
                        st.write("The membrane required **%.1f kN/m** pretension to hold its shape. This is high for PVDF." % final_pretension)
                        st.info("💡 **Engineering Tip:** Consider increasing the 'Secondary count' (ribs) in the main inputs from **%d** to **%d** to reduce the unsupported span and lower the required pretension." % (secondary_count, secondary_count + 2))

            coords_to_draw = dr_result["coordinates"]
            st.session_state["newton_results"] = {
                "dr_result": dr_result, "cable_name": cable_name, "cable_A_mm2": cable_A_mm2, "EA_cable": EA_cable,
                "steel_section": steel_section, "beam_axial_kN": max_reaction_kN, "beam_moment_kNm": (max_reaction_kN * data["span"]) / 8.0,
                "cables": cables, "material": mat, "final_pretension": final_pretension,
                "interaction_util": interaction_util, "buckling_util": buckling_util,
            }

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
        rp = _rib_polyline(float(data["rib_x"][i]), float(data["rib_half_width"][i]), float(data["rib_peak_z"][i]), RIB_SEGMENTS)
        fig.add_trace(go.Scatter3d(x=rp[:, 0], y=rp[:, 1], z=rp[:, 2], mode="lines", line=dict(color=COL_RIB, width=5), name="rib", showlegend=False, hoverinfo="skip"))

    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        pp = coords_to_draw[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(x=closed[:, 0], y=closed[:, 1], z=closed[:, 2], mode="lines", line=dict(color=COL_RING_EDGE, width=5), name="ring", showlegend=False, hoverinfo="skip"))
        centre_i, beam_i = data["built"]["centre_indices"][k], data["built"]["beam_top_indices"][k]
        cx, cy, cz = coords_to_draw[centre_i]
        for poly_i in idx_list:
            fig.add_trace(go.Scatter3d(x=[cx, coords_to_draw[poly_i, 0]], y=[cy, coords_to_draw[poly_i, 1]], z=[cz, coords_to_draw[poly_i, 2]], mode="lines", line=dict(color=COL_SPOKE, width=2), name="spoke", showlegend=False, hoverinfo="skip"))
        bx, by, bz = coords_to_draw[beam_i]
        fig.add_trace(go.Scatter3d(x=[cx, bx], y=[cy, by], z=[cz, bz], mode="lines", line=dict(color=COL_DROP, width=4), name="drop", showlegend=False, hoverinfo="skip"))

    apply_common_layout(fig, data["apex"])
    st.plotly_chart(fig, use_container_width=True, key="mc_3d")

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
            st.write("FDM estimated edge tension (N): %.1f" % data["fdm"]["max_edge_tension_N"])

        if newton_data:
            nd = newton_data["dr_result"]
            st.write("---")
            st.write("**Stage 2 — Newton:**")
            st.write("Newton converged: %s" % nd["converged"])
            st.write("Pretension factor used: %.1f (Warp/Weft %.1f kN/m, Cable %.1f kN/m)" % (newton_data.get("final_pretension", 1.0), newton_data.get("final_pretension", 1.0)*1.0, newton_data.get("final_pretension", 1.0)*5.0))
            st.write("Newton iterations: %d" % nd["iterations"])
            st.write("Newton total steps: %d" % nd.get("total_steps", 0))
            st.write("Newton residual (N): %.6e" % nd["residual_norm"])
            st.write("Newton max residual (N): %.6e" % nd.get("max_residual", nd["residual_norm"]))
            st.write("Newton time (s): %.2f" % nd["elapsed_seconds"])
            st.write("Newton reason: %s" % nd.get("reason", ""))

            st.write("---")
            st.write("**Steel section check (L_eff = L, conservative):**")
            st.write("Section: **%s**" % newton_data["steel_section"])
            st.write("Interaction utilization: %.1f%%" % (newton_data.get("interaction_util", 0.0) * 100.0))
            st.write("Buckling utilization (Euler): %.1f%%" % (newton_data.get("buckling_util", 0.0) * 100.0))

            st.write("---")
            st.write("**Reaction Forces & Foundation Design:**")
            R = nd.get("reactions", None)
            if R is not None:
                fixed_indices = data["fixed"]
                if len(fixed_indices) > 0:
                    anchor_idx = data["anchor_idx"]

                    # --- Match cable tensions to anchors for corner plate design ---
                    anchor_cable_tension_N = {}
                    cable_tensions = nd.get("cable_tension_list", [])
                    if cable_tensions:
                        per_anchor = [[] for _ in range(len(anchor_idx))]
                        n_a = len(anchor_idx)
                        pts_all = data["pts"]
                        cable_i = 0
                        for k in range(n_a):
                            a_idx = anchor_idx[k]
                            b_idx = anchor_idx[(k + 1) % n_a]
                            chain = [int(a_idx)]
                            i_cur = (a_idx + 1) % pts_all.shape[0]
                            b_int = int(b_idx)
                            safety = 0
                            while i_cur != b_int and safety < pts_all.shape[0]:
                                chain.append(int(i_cur))
                                i_cur = (i_cur + 1) % pts_all.shape[0]
                                safety += 1
                            chain.append(int(b_int))
                            n_segments = len(chain) - 1
                            for m in range(n_segments):
                                if cable_i < len(cable_tensions):
                                    per_anchor[k].append(cable_tensions[cable_i]["T_N"])
                                cable_i += 1
                        for k in range(n_a):
                            if per_anchor[k]:
                                anchor_cable_tension_N[anchor_idx[k]] = max(per_anchor[k])
                            else:
                                anchor_cable_tension_N[anchor_idx[k]] = 0.0
                    else:
                        for idx in anchor_idx:
                            anchor_cable_tension_N[idx] = 0.0

                    # --- Baseplate Table ---
                    st.write("**Baseplate Table (All Anchor Nodes):**")
                    st.code(
                        "%-6s  %-8s  %-8s  %-10s  %-10s  %-10s  %-12s  %-10s  %-10s  %-12s"
                        % ("Node", "X(m)", "Y(m)", "Fx(kN)", "Fy(kN)", "Fz(kN)", "Moment(kNm)", "Plate(mm)", "Bolts", "Pad(mm)"),
                        language="text"
                    )
                    for idx in anchor_idx:
                        r = R[idx]
                        design = design_baseplate_and_foundation(r, newton_data["steel_section"], data["eave_height"])
                        st.code(
                            "%-6d  %-8.2f  %-8.2f  %-10.1f  %-10.1f  %-10.1f  %-12.1f  %-10s  %-10s  %-12s"
                            % (
                                idx, data["coords_fdm"][idx, 0], data["coords_fdm"][idx, 1],
                                r[0]/1000.0, r[1]/1000.0, r[2]/1000.0, design["overturning_moment_kNm"],
                                "%dx%d" % (design["plate_side_mm"], design["plate_side_mm"]),
                                "%dxM%d" % (design["bolt_count"], design["bolt_diameter_mm"]),
                                "%dx%d" % (design["pad_side_mm"], design["pad_side_mm"])
                            ),
                            language="text"
                        )

                    # --- Corner Plate Table ---
                    st.write("---")
                    st.write("**Corner Plate Table (Cable-to-Ring Connections):**")
                    st.code(
                        "%-6s  %-12s  %-12s  %-10s  %-10s  %-10s  %-12s  %-10s  %-10s"
                        % ("Node", "Cable T(kN)", "Cable d(mm)", "Plate(mm)", "Width(mm)", "Weld(mm)", "Pin(mm)", "Weld util", "Pin util"),
                        language="text"
                    )
                    any_corner_warn = False
                    for idx in anchor_idx:
                        # Use the maximum of the baseline or the solver's reported max tension.
                        max_solver_T = max([c["T_N"] for c in cable_tensions]) if cable_tensions else 0.0
                        T_N = max(anchor_cable_tension_N.get(idx, 0.0), max_solver_T, data["fdm"]["max_edge_tension_N"])
                        
                        # Cable diameter estimate from selected cable area
                        A_mm2 = newton_data["cable_A_mm2"]
                        cable_d_mm = max(6.0, math.sqrt(4.0 * A_mm2 / math.pi))
                        corner = design_corner_plate(T_N, cable_d_mm)
                        weld_util = corner["weld_utilization"]
                        pin_util = corner["pin_utilization"]
                        if weld_util > 1.0 or pin_util > 1.0:
                            any_corner_warn = True
                        st.code(
                            "%-6d  %-12.1f  %-12.1f  %-10d  %-10d  %-10d  %-12d  %-10.2f  %-10.2f"
                            % (
                                idx, T_N / 1000.0, cable_d_mm,
                                corner["plate_thickness_mm"], corner["plate_width_mm"],
                                corner["weld_size_mm"], corner["pin_diameter_mm"],
                                weld_util, pin_util,
                            ),
                            language="text"
                        )
                    if any_corner_warn:
                        st.warning(
                            "One or more corner plates exceed 100% utilization. "
                            "Increase plate thickness, weld size, or pin diameter, or reduce cable tension."
                        )

                    # --- Cone Drop Table ---
                    st.write("---")
                    st.write("**Cone Drop Table:**")
                    st.code(
                        "%-8s  %-10s  %-10s  %-10s" % ("Cone", "X(m)", "Y(m)", "Fz(kN)"),
                        language="text"
                    )
                    for k in range(len(data["built"]["centre_indices"])):
                        ci = data["built"]["centre_indices"][k]
                        bi = data["built"]["beam_top_indices"][k]
                        r_drop = R[bi]
                        st.code(
                            "%-8d  %-10.2f  %-10.2f  %-10.1f"
                            % (k+1, data["coords_fdm"][ci, 0], data["coords_fdm"][ci, 1], r_drop[2]/1000.0),
                            language="text"
                        )

                    # --- Deflection Check ---
                    st.write("---")
                    st.write("**Deflection Check:**")
                    max_deflection_mm = 0.0
                    max_def_idx = -1
                    for i in range(len(data["coords_fdm"])):
                        d = np.linalg.norm(coords_to_draw[i] - data["coords_fdm"][i])
                        if d > max_deflection_mm:
                            max_deflection_mm = d * 1000.0
                            max_def_idx = i
                    limit_mm = (data["span"] * 1000.0) / 200.0
                    status = "PASS" if max_deflection_mm <= limit_mm else "FAIL"
                    st.code(
                        "Max Deflection: %.2f mm at Node %d (Limit: %.1f mm) -> %s" % (max_deflection_mm, max_def_idx, limit_mm, status),
                        language="text"
                    )
            else:
                st.write("Reactions not available in solver output.")

            hist = nd.get("history", [])
            if hist:
                st.write("Newton history (last 5 steps):")
                for row in hist[-5:]:
                    st.write("  outer=%s  inner=%s  ||R||=%.4e  max|R|=%.4e" % (row[0], row[1], row[2], row[3]))

            members = _build_member_schedule(data["built"], coords_to_draw, data["x_rings"], data["anchor_idx"], data["edge_q_scalar"], data["warp_q"], data["weft_q"], newton_data["cable_name"], newton_data["cable_A_mm2"], newton_data["steel_section"], data["eave_height"], data["span"], data["mid_width"])
            with st.expander("Member schedule (auto-sized)", expanded=True):
                st.write("Edge cable: **%s** (A=%.1f mm2)" % (newton_data["cable_name"], newton_data["cable_A_mm2"]))
                st.write("Steel section: **%s**" % newton_data["steel_section"])
                st.write("Total members recorded: %d" % len(members))
                st.code(_format_member_table(members), language="text")

# =============================================================================
# END OF ui/workshops/tester_multi_cone.py
