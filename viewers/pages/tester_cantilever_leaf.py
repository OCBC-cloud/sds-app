# =============================================================================
# SDSe Fluid Design Studio - Cantilever Leaf LAB TESTER (Standalone Sandbox)
# =============================================================================

import math
import streamlit as st
import numpy as np

from data.materials import STEEL_MATERIALS, FABRIC_PROPERTIES
from data.constants import WIND_SPEEDS
from viewers.figures.cantilever_leaf import build_cantilever_leaf

# Our engine imports for the structural test
from engine.form_finding import solve_fdm
from engine.cantilever_leaf_test_mesh import build_leaf_test_mesh
from engine.cantilever_frame_builder import build_cantilever_frame
from engine.frame_analysis import analyze_and_size_frame

WORKSHOP_CSS = """
    <style>
    .ws-breadcrumb { font-size: 0.85rem; color: #a8b8c8; margin-bottom: 1.2rem; letter-spacing: 0.3px; }
    .ws-breadcrumb .crumb { color: #f39c12; font-weight: 600; }
    .ws-section { background-color: #121e2e; border: 1px solid #1e2a3a; border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.9rem; }
    .ws-section-title { color: #f39c12; font-size: 1.05rem; font-weight: 700; margin: 0 0 0.2rem 0; letter-spacing: 0.3px; }
    .ws-section-help { color: #a8b8c8; font-size: 0.82rem; margin: 0 0 0.8rem 0; line-height: 1.35; }
    .ws-preview-box { background-color: #0d1620; border-left: 3px solid #3498db; padding: 0.6rem 0.8rem; border-radius: 4px; margin-top: 0.5rem; font-size: 0.85rem; color: #c8d4e0; line-height: 1.5; }
    .ws-preview-box .num { color: #ffffff; font-weight: 600; }
    .ws-warning-box { background-color: #4a3a1a; border-left: 3px solid #f39c12; padding: 0.6rem 0.8rem; border-radius: 4px; margin-top: 0.5rem; font-size: 0.85rem; color: #f0f4fa; }
    .ws-info-box { background-color: #1a2a3a; border-left: 3px solid #4a7a9c; padding: 0.7rem 0.9rem; border-radius: 4px; margin-top: 0.5rem; font-size: 0.85rem; color: #c8d4e0; line-height: 1.5; }
    </style>
"""

FABRIC_INFO = {
    "Type I": "700-800 g/m2. Light tensile structures, tents, shade sails.",
    "Type II": "900-1000 g/m2. Medium tensile structures.",
    "Type III": "1050-1200 g/m2. Mid-to-large tensile structures.",
    "Type IV": "1300-1400 g/m2. Large-span structures, stadiums.",
    "Type V": "1450-2000 g/m2. Max span, air-supported roofs.",
}

def _init_defaults():
    defaults = {
        "ws_sl_object_shape": "leaf", "ws_sl_column_height": 10.0, "ws_sl_outreach": 10.0,
        "ws_sl_ribs_per_side": 7, "ws_sl_rib_tilt": 20, "ws_sl_rib_spacing": 45, "ws_sl_arc_radius": 5.0,
        "ws_sl_curve_type": "parabolic", "ws_sl_steel_grade": "S355", "ws_sl_section_family": "CHS",
        "ws_sl_fabric_type": "PVDF", "ws_sl_fabric_grade": "Type III", "ws_sl_column_type": "unipole",
        "ws_sl_column_preference": "auto", "ws_sl_rib_section_family": "CHS", "ws_sl_rib_preference": "auto",
        "ws_sl_rib_connection": "bolted", "ws_sl_attachment_type": "kader", "ws_sl_perimeter_cable_type": "6x19",
        "ws_sl_perimeter_cable_material": "stainless", "ws_sl_membrane_pretension": 2.0, "ws_sl_soil_bearing": 150.0,
        "ws_sl_soil_type": "sand", "ws_sl_water_table": 3.0, "ws_sl_foundation_type": "pad",
        "ws_sl_found_widget_generation": 0, "ws_sl_add_payload": 0.0, "ws_sl_design_standard": "MY",
        "ws_sl_arrangement": "single", "ws_sl_arrangement_count": 4, "ws_sl_arrangement_tiers": 1,
        "ws_sl_first_leaf_height": 3.0, "ws_sl_leaf_zone_height": 7.0, "ws_sl_num_leaves": 8,
        "ws_sl_column_radius": 0.15, "ws_sl_leaf_angular_width": 60.0, "ws_sl_taper_mode": "taper_up",
        "ws_sl_taper_ratio": 0.88, "ws_sl_rib_override_active": False, "ws_sl_rib_lengths_override": [],
        "ws_sl_strut_angle_deg": 42, "ws_sl_last_geometry": None, "ws_sl_viewer_description": "Cantilever Leaf tensile membrane structure",
        "ws_sl_viewer_dimensions": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _compute_rib_lengths(outreach, tilt_deg, n_ribs):
    lengths = []
    if n_ribs < 1: return lengths
    ts = [0.5] if n_ribs == 1 else [0.08 + (0.92 - 0.08) * i / (n_ribs - 1) for i in range(n_ribs)]
    for t in ts:
        half_w = outreach * 0.42 * (math.sin(math.pi * t) ** 0.7)
        tilt_local = tilt_deg * (math.sin(math.pi * t) ** 0.7)
        z_rise = half_w * math.tan(math.radians(tilt_local))
        length = math.sqrt(half_w * half_w + z_rise * z_rise)
        lengths.append(round(length, 2))
    return lengths

def _rib_position_label(i, n):
    if n <= 1: return "centre"
    if i == 0: return "near column"
    if i == n - 1: return "near tip"
    mid = (n - 1) / 2.0
    if abs(i - mid) < 0.5: return "centre"
    return "inner" if i < mid else "outer"

def _validate_leaf_geometry(col_h, outreach, ribs, tilt):
    warnings = []
    if col_h <= 0: warnings.append("Column height must be greater than 0.")
    if outreach <= 0: warnings.append("Leaf outreach must be greater than 0.")
    if ribs < 5: warnings.append("Minimum 5 ribs per side for a proper leaf shape.")
    if ribs > 7: warnings.append("Maximum 7 ribs per side for Leaf.")
    if tilt < 10: warnings.append("Rib tilt below 10 degrees may not drain properly.")
    if tilt > 40: warnings.append("Rib tilt above 40 degrees loses the leaf silhouette.")
    if outreach > 12 and col_h < outreach: warnings.append("Tall outreach relative to column height.")
    return warnings

def _section_header(title, help_text=""):
    html = '<div class="ws-section-title">' + title + '</div>'
    if help_text: html += '<div class="ws-section-help">' + help_text + '</div>'
    st.markdown(html, unsafe_allow_html=True)

def _info_box(text): st.markdown('<div class="ws-info-box">' + text + '</div>', unsafe_allow_html=True)
def _preview_box(text): st.markdown('<div class="ws-preview-box">' + text + '</div>', unsafe_allow_html=True)
def _warning_box(text): st.markdown('<div class="ws-warning-box">' + text + '</div>', unsafe_allow_html=True)


def render_tester_cantilever_leaf():
    st.components.v1.html("""<script>window.parent.scrollTo(0, 0);</script>""", height=0, width=0)
    st.markdown(WORKSHOP_CSS, unsafe_allow_html=True)
    _init_defaults()
    gen = int(st.session_state.get("ws_sl_found_widget_generation", 0))
    project_name = st.session_state.get("project_info", {}).get("name", "") or "Lab Test Project"
    client_name = st.session_state.get("project_info", {}).get("client", "") or "Lab Test Client"

    st.markdown('<div class="ws-breadcrumb">SDSe Fluid Design Studio / <span class="crumb">LAB TEST</span> / <span class="crumb">Cantilever Leaf</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="ws-section"><div class="ws-section-title">' + project_name + '</div><div class="ws-section-help">Client: ' + client_name + '  |  Structure: Cantilever Leaf</div></div>', unsafe_allow_html=True)

    with st.expander("1. Object Shape", expanded=True):
        _section_header("Object Shape", "Choose the base object. Leaf is active now.")
        st.session_state["ws_sl_object_shape"] = "leaf"
        _preview_box("Base Object: <strong>Leaf</strong>")

    with st.expander("2. Geometry", expanded=False):
        _section_header("Geometry", "Overall layout of the leaf.")
        col1, col2 = st.columns(2)
        with col1:
            col_h = st.number_input("Column Height (m) *", min_value=2.0, max_value=30.0, value=float(st.session_state["ws_sl_column_height"]), step=0.5, key="ws_sl_column_height_input")
            st.session_state["ws_sl_column_height"] = col_h
        with col2:
            outreach = st.number_input("Leaf Outreach (m) *", min_value=2.0, max_value=12.0, value=float(st.session_state["ws_sl_outreach"]), step=0.5, key="ws_sl_outreach_input")
            st.session_state["ws_sl_outreach"] = outreach
        col3, col4 = st.columns(2)
        with col3:
            ribs = st.number_input("Ribs per Side (min 5, max 7) *", min_value=5, max_value=7, value=int(st.session_state["ws_sl_ribs_per_side"]), step=1, key="ws_sl_ribs_input")
            st.session_state["ws_sl_ribs_per_side"] = ribs
        with col4:
            tilt = st.slider("Rib Tilt Angle (deg)", min_value=5, max_value=40, value=int(st.session_state["ws_sl_rib_tilt"]), step=1, key="ws_sl_tilt_slider")
            st.session_state["ws_sl_rib_tilt"] = tilt
        col5, col6 = st.columns(2)
        with col5:
            spacing = st.slider("Rib Plan Spacing (deg)", min_value=15, max_value=90, value=int(st.session_state["ws_sl_rib_spacing"]), step=5, key="ws_sl_spacing_slider")
            st.session_state["ws_sl_rib_spacing"] = spacing
        with col6:
            arc_r = st.number_input("Main Beam Arc Radius (m) *", min_value=1.0, max_value=20.0, value=float(st.session_state["ws_sl_arc_radius"]), step=0.5, key="ws_sl_arc_input")
            st.session_state["ws_sl_arc_radius"] = arc_r

        computed_lengths = _compute_rib_lengths(outreach, tilt, ribs)
        st.session_state["ws_sl_rib_base_lengths"] = computed_lengths
        length_strs = ["Rib " + str(i + 1) + " (" + _rib_position_label(i, len(computed_lengths)) + "): <strong>" + ("%.2f" % L) + " m</strong>" for i, L in enumerate(computed_lengths)]
        _preview_box("<strong>Computed rib lengths</strong><br>" + "<br>".join(length_strs))
        for w in _validate_leaf_geometry(col_h, outreach, ribs, tilt): _warning_box(w)

    with st.expander("3. Materials", expanded=False):
        _section_header("Materials", "Steel grade, section family, and fabric.")
        col1, col2 = st.columns(2)
        with col1:
            steel_grades = ["S235", "S275", "S355", "S420", "S460"]
            s_idx = steel_grades.index(st.session_state["ws_sl_steel_grade"])
            steel = st.selectbox("Steel Grade", steel_grades, index=s_idx, key="ws_sl_steel_select")
            st.session_state["ws_sl_steel_grade"] = steel
        with col2:
            section_families = ["CHS", "SHS", "RHS", "I-Beam"]
            f_idx = section_families.index(st.session_state["ws_sl_section_family"])
            family = st.selectbox("Section Family", section_families, index=f_idx, key="ws_sl_family_select")
            st.session_state["ws_sl_section_family"] = family

    with st.expander("4. Column and Spine", expanded=False):
        _section_header("Column and Spine", "The uni-pole column and the curved spine.")
        col_types = ["unipole", "truss"]
        col_labels = ["Uni-Pole Column", "Truss Column"]
        ct_idx = col_types.index(st.session_state["ws_sl_column_type"])
        ct_choice = st.radio("Column Type", col_labels, index=ct_idx, key="ws_sl_column_type_radio")
        st.session_state["ws_sl_column_type"] = col_types[col_labels.index(ct_choice)]

        col_h_val = float(st.session_state.get("ws_sl_column_height", 10.0))
        strut_joint = round(col_h_val * 0.60, 2)
        st.session_state["ws_sl_strut_joint_height"] = strut_joint
        strut_angle = st.number_input("Strut Angle (deg) - from horizontal", min_value=25.0, max_value=65.0, value=float(st.session_state.get("ws_sl_strut_angle_deg", 42.0)), step=1.0, key="ws_sl_strut_angle_input")
        st.session_state["ws_sl_strut_angle_deg"] = strut_angle

    with st.expander("5. Ribs", expanded=False):
        _section_header("Ribs", "Radial ribs extending outward from the spine.")
        col1, col2 = st.columns(2)
        with col1:
            rib_families = ["CHS", "SHS", "RHS"]
            rf_idx = rib_families.index(st.session_state["ws_sl_rib_section_family"])
            rib_fam = st.selectbox("Rib Section Family", rib_families, index=rf_idx, key="ws_sl_rib_family_select")
            st.session_state["ws_sl_rib_section_family"] = rib_fam

    with st.expander("6. Membrane Attachment and Perimeter Cable", expanded=False):
        _section_header("Membrane Attachment and Perimeter Cable", "How the fabric is attached, and how the perimeter cable runs.")
        mem_pre = st.slider("Membrane Pretension (kN/m)", min_value=0.5, max_value=8.0, value=float(st.session_state["ws_sl_membrane_pretension"]), step=0.1, key="ws_sl_mem_pre_slider")
        st.session_state["ws_sl_membrane_pretension"] = mem_pre

    with st.expander("7. Baseplate and Preliminary Foundation", expanded=False):
        _section_header("Baseplate and Preliminary Foundation", "Sizing depends on soil at the site.")
        col1, col2 = st.columns(2)
        with col1:
            bearing = st.number_input("Soil Bearing Capacity (kN/m2)", min_value=50.0, max_value=1000.0, value=float(st.session_state["ws_sl_soil_bearing"]), step=10.0, key="ws_sl_soil_bearing_input")
            st.session_state["ws_sl_soil_bearing"] = bearing
        with col2:
            water = st.number_input("Water Table Depth (m)", min_value=0.5, max_value=20.0, value=float(st.session_state["ws_sl_water_table"]), step=0.5, key="ws_sl_water_table_input")
            st.session_state["ws_sl_water_table"] = water
        _warning_box("Preliminary sizing only. Geotechnical verification required.")

    with st.expander("8. Loads and Design Standard", expanded=False):
        _section_header("Loads and Design Standard", "User-added loads. Design code for safety factors.")
        payload = st.number_input("Add. Pay Load (kg/m)", min_value=0.0, max_value=500.0, value=float(st.session_state["ws_sl_add_payload"]), step=5.0, key="ws_sl_add_payload_input")
        st.session_state["ws_sl_add_payload"] = payload
        std_options = ["EU", "MY", "UK", "CN", "US"]
        std_idx = std_options.index(st.session_state["ws_sl_design_standard"])
        std = st.selectbox("Design Standard", std_options, index=std_idx, key="ws_sl_standard_select")
        st.session_state["ws_sl_design_standard"] = std

    with st.expander("9. Arrangement", expanded=False):
        _section_header("Arrangement", "How the mother object is arranged around the column.")
        arrangement_options = ["single", "double", "multiple", "tree_stack", "tiered_helix"]
        arrangement_labels = ["Single", "Double (mirror)", "Multiple (radial)", "Tree (stacked tiers)", "Tiered Helix (engine)"]
        arr_idx = arrangement_options.index(st.session_state["ws_sl_arrangement"])
        arr_choice = st.radio("Arrangement", arrangement_labels, index=arr_idx, key="ws_sl_arrangement_radio")
        st.session_state["ws_sl_arrangement"] = arrangement_options[arrangement_labels.index(arr_choice)]

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # The 3D Visual
    build_cantilever_leaf()

    # ---- NEW: Structural Analysis Section ----
    st.markdown("---")
    st.markdown("### Structural Auto-Sizing (Lab Test)")
    
    if st.button("Run Universal Analysis", type="primary", use_container_width=True):
        with st.spinner("Running Structural Pipeline..."):
            # 1. Build the dynamic geometry 
            # We pull the exact values the user set in the Workshop expanders
            col_h_test = float(st.session_state.get("ws_sl_column_height", 10.0))
            outreach_test = float(st.session_state.get("ws_sl_outreach", 10.0))
            tilt_test = float(st.session_state.get("ws_sl_rib_tilt", 20.0))
            arc_r_test = float(st.session_state.get("ws_sl_arc_radius", 5.0))
            n_ribs_test = int(st.session_state.get("ws_sl_ribs_per_side", 7))
            strut_j_test = float(st.session_state.get("ws_sl_strut_joint_height", 6.0))
            strut_a_test = float(st.session_state.get("ws_sl_strut_angle_deg", 42.0))
            
            # We need to pass a "half_width" based on the leaf width law for the steel builder
            # Using the same law as the visual: 0.42 * outreach
            half_w_test = outreach_test * 0.42

            # 2. Build the test mesh for the FDM solver
            from engine.cantilever_leaf_test_mesh import build_leaf_test_mesh
            # Note: we are creating a temporary geometry dict just for the mesh builder
            from viewers.figures.cantilever_leaf_lab import compute_lab_leaf_geometry
            geom_test = compute_lab_leaf_geometry(
                col_h=col_h_test, outreach=outreach_test, half_width_mid=half_w_test,
                rib_tilt_deg=tilt_test, arc_r=arc_r_test, strut_joint=strut_j_test,
                strut_angle=strut_a_test, ribs_per_side=n_ribs_test
            )
            
            mesh_data = build_leaf_test_mesh(
                geom_test, 
                membrane_tension=2000.0, 
                cable_tension=5000.0,
                attached_to_spine=True
            )
            
            # 3. Run FDM Solver
            fdm_res = solve_fdm(
                points=mesh_data["points_3d"], 
                edges=mesh_data["edges"], 
                fixed_indices=mesh_data["fixed_indices"], 
                force_densities=mesh_data["q"]
            )
            coords = fdm_res["coordinates"]
            reactions_N = fdm_res["reactions"] * 1000.0

            # 4. Build the steel frame
            frame_data = build_cantilever_frame(
                col_h_test, outreach_test, half_w_test, 
                tilt_test, arc_r_test, strut_j_test, strut_a_test, n_ribs_test
            )
            
            # 5. Map Loads
            applied_loads = {}
            steel_nodes = frame_data["nodes"]
            for i in range(len(coords)):
                if i in mesh_data["fixed_indices"]:
                    mem_pos = coords[i]
                    dists = np.linalg.norm(steel_nodes - mem_pos, axis=1)
                    s_idx = np.argmin(dists)
                    
                    force = -reactions_N[i]
                    if s_idx not in applied_loads:
                        applied_loads[s_idx] = np.zeros(3)
                    applied_loads[s_idx] += force

            # 6. Auto-Size
            result = analyze_and_size_frame(frame_data, applied_loads, grade="S355", family="CHS")
            
            if "error" in result:
                st.error(f"Sizing Failed: {result['error']}")
            else:
                st.success(f"Sizing Converged in {result.get('iterations', '?')} iterations!")
                st.markdown("#### Selected Sections:")
                for kind, sec in result["sections"].items():
                    st.write(f"- **{kind.capitalize()}**: `{sec}`")
                st.markdown("#### Utilization:")
                for kind, util in result["details"].items():
                    color = "#ff4b4b" if util > 0.85 else "#00cc66"
                    st.markdown(f"- **{kind.capitalize()}**: <span style='color:{color}'>{util*100:.1f}%</span>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Back to Lab", key="lab_leaf_back_bottom", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()
