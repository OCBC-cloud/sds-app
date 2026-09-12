# =============================================================================
# SDSe Fluid Design Studio - Cantilever Leaf Workshop
# =============================================================================
# Input page for the Cantilever Leaf variant of the Saddle Span family.
#
# Per engine/SPEC_saddle_span.md, this variant is:
#   Uni-pole column with curved spine (main beam) and radial ribs.
#   Leaf-shaped membrane canopy. Cantilevered.
#   Baseplate anchor resists torsion - footing must be designed separately.
#
# Design decisions (agreed 2026-09-13):
#   - Collapsible sections
#   - Mixed widgets
#   - Custom-styled section headers
#   - No tie-down cables (this is a cantilever, not an uplift structure)
#   - Section 6 is Baseplate + Preliminary Foundation Sizing
#   - Preliminary foundation = reaction / soil bearing capacity
#   - Note for user: geotechnical verification and reinforcement not provided
#   - Section 5 covers fabric attachment AND perimeter cable
#   - Cable diameter and baseplate sizing are automatic
#   - Strut joint height auto-determined (60% of column) with user override
#   - Back to Registration at bottom
#   - "Intelligent Design Computing" advances to Results
# =============================================================================

import math

import streamlit as st

from data.materials import STEEL_MATERIALS, FABRIC_PROPERTIES
from data.constants import WIND_SPEEDS


# =============================================================================
# CSS
# =============================================================================

WORKSHOP_CSS = """
    <style>
    .ws-breadcrumb {
        font-size: 0.85rem;
        color: #a8b8c8;
        margin-bottom: 1.2rem;
        letter-spacing: 0.3px;
    }
    .ws-breadcrumb .crumb {
        color: #f39c12;
        font-weight: 600;
    }
    .ws-section {
        background-color: #121e2e;
        border: 1px solid #1e2a3a;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
    }
    .ws-section-title {
        color: #f39c12;
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0 0 0.2rem 0;
        letter-spacing: 0.3px;
    }
    .ws-section-help {
        color: #a8b8c8;
        font-size: 0.82rem;
        margin: 0 0 0.8rem 0;
        line-height: 1.35;
    }
    .ws-preview-box {
        background-color: #0d1620;
        border-left: 3px solid #3498db;
        padding: 0.6rem 0.8rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #c8d4e0;
        line-height: 1.5;
    }
    .ws-preview-box .num {
        color: #ffffff;
        font-weight: 600;
    }
    .ws-warning-box {
        background-color: #4a3a1a;
        border-left: 3px solid #f39c12;
        padding: 0.6rem 0.8rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #f0f4fa;
    }
    .ws-info-box {
        background-color: #1a2a3a;
        border-left: 3px solid #4a7a9c;
        padding: 0.7rem 0.9rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #c8d4e0;
        line-height: 1.5;
    }
    </style>
"""


# =============================================================================
# DEFAULTS
# =============================================================================

def _init_defaults():
    defaults = {
        # Section 1 - Geometry
        "ws_sl_column_height": 10.0,
        "ws_sl_outreach": 10.0,
        "ws_sl_ribs_per_side": 7,
        "ws_sl_rib_tilt": 20,
        "ws_sl_rib_spacing": 45,
        "ws_sl_arc_radius": 5.0,
        "ws_sl_curve_type": "parabolic",
        # Section 2 - Materials
        "ws_sl_steel_grade": "S355",
        "ws_sl_section_family": "CHS",
        "ws_sl_fabric_type": "PVDF",
        "ws_sl_fabric_grade": "Type III",
        # Section 3 - Column and Spine
        "ws_sl_column_type": "unipole",
        "ws_sl_column_preference": "auto",
        "ws_sl_strut_joint_height": 6.0,
        # Section 4 - Ribs
        "ws_sl_rib_section_family": "CHS",
        "ws_sl_rib_preference": "auto",
        "ws_sl_rib_connection": "bolted",
        # Section 5 - Attachment + Perimeter Cable
        "ws_sl_attachment_type": "kader",
        "ws_sl_segment_spacing": 2.5,
        "ws_sl_perimeter_cable_type": "6x19",
        "ws_sl_perimeter_cable_material": "stainless",
        # Section 6 - Baseplate and Foundation
        "ws_sl_soil_bearing": 150.0,
        "ws_sl_soil_type": "sand",
        "ws_sl_water_table": 3.0,
        "ws_sl_foundation_type": "pad",
        # Section 7 - Loads
        "ws_sl_live_load": 0.5,
        "ws_sl_design_standard": "MY",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =============================================================================
# HELPERS
# =============================================================================

def _validate_leaf_geometry(col_h, outreach, ribs, tilt):
    warnings = []
    if col_h <= 0:
        warnings.append("Column height must be greater than 0.")
    if outreach <= 0:
        warnings.append("Leaf outreach must be greater than 0.")
    if ribs < 5:
        warnings.append("Minimum 5 ribs per side for a proper leaf shape.")
    if ribs > 15:
        warnings.append("More than 15 ribs per side is architecturally excessive.")
    if tilt < 10:
        warnings.append("Rib tilt below 10 degrees may not drain properly.")
    if tilt > 40:
        warnings.append("Rib tilt above 40 degrees loses the leaf silhouette.")
    if outreach > 12 and col_h < outreach:
        warnings.append("Tall outreach relative to column height. Torsion will govern.")
    return warnings


def _section_header(title, help_text=""):
    html = '<div class="ws-section-title">' + title + '</div>'
    if help_text:
        html += '<div class="ws-section-help">' + help_text + '</div>'
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_saddle_leaf():
    """Render the Cantilever Leaf workshop."""
    st.markdown(WORKSHOP_CSS, unsafe_allow_html=True)
    _init_defaults()

    project_name = st.session_state.get("project_info", {}).get("name", "") or "Untitled Project"
    client_name = st.session_state.get("project_info", {}).get("client", "") or "Unknown Client"

    # ---- Breadcrumb
    st.markdown(
        '<div class="ws-breadcrumb">'
        'SDSe Fluid Design Studio / '
        '<span class="crumb">Saddle Span</span>'
        ' / '
        '<span class="crumb">Cantilever Leaf</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Project header
    st.markdown(
        '<div class="ws-section">'
        '<div class="ws-section-title">' + project_name + '</div>'
        '<div class="ws-section-help">'
        'Client: ' + client_name + '  |  Structure: Cantilever Leaf'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # =========================================================================
    # SECTION 1 - GEOMETRY
    # =========================================================================
    with st.expander("1. Geometry", expanded=True):
        _section_header(
            "Geometry",
            "Overall layout of the leaf. Column rises from ground. Leaf extends outward with radial ribs."
        )

        col1, col2 = st.columns(2)
        with col1:
            col_h = st.number_input(
                "Column Height (m) *",
                min_value=2.0, max_value=30.0,
                value=float(st.session_state["ws_sl_column_height"]),
                step=0.5,
                key="ws_sl_column_height_input",
            )
            st.session_state["ws_sl_column_height"] = col_h
        with col2:
            outreach = st.number_input(
                "Leaf Outreach (m) *",
                min_value=2.0, max_value=30.0,
                value=float(st.session_state["ws_sl_outreach"]),
                step=0.5,
                key="ws_sl_outreach_input",
            )
            st.session_state["ws_sl_outreach"] = outreach

        col3, col4 = st.columns(2)
        with col3:
            ribs = st.number_input(
                "Ribs per Side (min 5) *",
                min_value=5, max_value=15,
                value=int(st.session_state["ws_sl_ribs_per_side"]),
                step=1,
                key="ws_sl_ribs_input",
            )
            st.session_state["ws_sl_ribs_per_side"] = ribs
        with col4:
            tilt = st.slider(
                "Rib Tilt Angle (deg)",
                min_value=5, max_value=40,
                value=int(st.session_state["ws_sl_rib_tilt"]),
                step=1,
                key="ws_sl_tilt_slider",
            )
            st.session_state["ws_sl_rib_tilt"] = tilt

        col5, col6 = st.columns(2)
        with col5:
            spacing = st.slider(
                "Rib Plan Spacing (deg)",
                min_value=15, max_value=90,
                value=int(st.session_state["ws_sl_rib_spacing"]),
                step=5,
                key="ws_sl_spacing_slider",
            )
            st.session_state["ws_sl_rib_spacing"] = spacing
        with col6:
            arc_r = st.number_input(
                "Main Beam Arc Radius (m) *",
                min_value=1.0, max_value=20.0,
                value=float(st.session_state["ws_sl_arc_radius"]),
                step=0.5,
                key="ws_sl_arc_input",
            )
            st.session_state["ws_sl_arc_radius"] = arc_r

        curve_options = ["parabolic", "circular", "catenary"]
        curve_labels = ["Parabolic", "Circular", "Catenary"]
        c_idx = curve_options.index(st.session_state["ws_sl_curve_type"])
        curve_choice = st.selectbox(
            "Spine Curve Type",
            curve_labels,
            index=c_idx,
            key="ws_sl_curve_select",
        )
        st.session_state["ws_sl_curve_type"] = curve_options[curve_labels.index(curve_choice)]

        warns = _validate_leaf_geometry(col_h, outreach, ribs, tilt)
        for w in warns:
            st.markdown(
                '<div class="ws-warning-box">' + w + '</div>',
                unsafe_allow_html=True,
            )

    # =========================================================================
    # SECTION 2 - MATERIALS
    # =========================================================================
    with st.expander("2. Materials", expanded=False):
        _section_header(
            "Materials",
            "Steel grade for the structure. Fabric type and grade for the membrane."
        )

        col1, col2 = st.columns(2)
        with col1:
            steel_grades = ["S235", "S275", "S355", "S420", "S460"]
            s_idx = steel_grades.index(st.session_state["ws_sl_steel_grade"])
            steel = st.selectbox(
                "Steel Grade",
                steel_grades,
                index=s_idx,
                key="ws_sl_steel_select",
            )
            st.session_state["ws_sl_steel_grade"] = steel
        with col2:
            section_families = ["CHS", "SHS", "RHS", "I-Beam"]
            f_idx = section_families.index(st.session_state["ws_sl_section_family"])
            family = st.selectbox(
                "Section Family",
                section_families,
                index=f_idx,
                key="ws_sl_family_select",
            )
            st.session_state["ws_sl_section_family"] = family

        col3, col4 = st.columns(2)
        with col3:
            fabric_types = list(FABRIC_PROPERTIES.keys())
            ft_idx = fabric_types.index(st.session_state["ws_sl_fabric_type"]) if st.session_state["ws_sl_fabric_type"] in fabric_types else 0
            fabric_type = st.selectbox(
                "Fabric Type",
                fabric_types,
                index=ft_idx,
                key="ws_sl_fabric_type_select",
            )
            st.session_state["ws_sl_fabric_type"] = fabric_type
        with col4:
            grades = [k for k in FABRIC_PROPERTIES.get(fabric_type, {}).keys() if k != "default"]
            if not grades:
                grades = ["Type III"]
            g_idx = grades.index(st.session_state["ws_sl_fabric_grade"]) if st.session_state["ws_sl_fabric_grade"] in grades else 0
            grade = st.selectbox(
                "Fabric Grade",
                grades,
                index=g_idx,
                key="ws_sl_fabric_grade_select",
            )
            st.session_state["ws_sl_fabric_grade"] = grade

    # =========================================================================
    # SECTION 3 - COLUMN AND SPINE
    # =========================================================================
    with st.expander("3. Column and Spine", expanded=False):
        _section_header(
            "Column and Spine",
            "The uni-pole column and the curved spine (main beam) at the top."
        )

        col_types = ["unipole", "truss"]
        col_labels = ["Uni-Pole Column", "Truss Column"]
        ct_idx = col_types.index(st.session_state["ws_sl_column_type"])
        ct_choice = st.radio(
            "Column Type",
            col_labels,
            index=ct_idx,
            key="ws_sl_column_type_radio",
        )
        st.session_state["ws_sl_column_type"] = col_types[col_labels.index(ct_choice)]

        col_pref = st.radio(
            "Column Section Preference",
            ["Auto-select", "User-specified"],
            index=0,
            key="ws_sl_col_pref_radio",
        )
        st.session_state["ws_sl_column_preference"] = "auto" if col_pref == "Auto-select" else "manual"

        # ---- Strut Joint Height (auto-determined with override)
        col_h_val = float(st.session_state.get("ws_sl_column_height", 10.0))
        auto_joint = round(col_h_val * 0.6, 2)
        min_joint = round(col_h_val * 0.40, 2)
        max_joint = round(col_h_val * 0.75, 2)

        if "ws_sl_strut_joint_height" not in st.session_state:
            st.session_state["ws_sl_strut_joint_height"] = auto_joint

        strut_joint = st.number_input(
            "Strut Joint Height on Column (m)",
            min_value=min_joint,
            max_value=max_joint,
            value=float(st.session_state["ws_sl_strut_joint_height"]),
            step=0.1,
            key="ws_sl_strut_joint_input",
            help="Height where the curved strut meets the column. Higher = smaller moment into the base.",
        )
        st.session_state["ws_sl_strut_joint_height"] = strut_joint

        st.markdown(
            '<div class="ws-preview-box">'
            'Auto-determined: <span class="num">'
            + ("%.2f m" % auto_joint)
            + '</span> (60% of column height)<br>'
            'Valid range: ' + ("%.2f m" % min_joint) + ' to ' + ("%.2f m" % max_joint) + '<br>'
            'Higher joint reduces moment transfer to the baseplate.'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="ws-preview-box">'
            'Column base is a rigid baseplate. Torsion and moment '
            'are resisted by the baseplate and its anchors.'
            '</div>',
            unsafe_allow_html=True,
        )

    # =========================================================================
    # SECTION 4 - RIBS
    # =========================================================================
    with st.expander("4. Ribs", expanded=False):
        _section_header(
            "Ribs",
            "Radial ribs extending outward and upward from the spine."
        )

        col1, col2 = st.columns(2)
        with col1:
            rib_families = ["CHS", "SHS", "RHS"]
            rf_idx = rib_families.index(st.session_state["ws_sl_rib_section_family"])
            rib_fam = st.selectbox(
                "Rib Section Family",
                rib_families,
                index=rf_idx,
                key="ws_sl_rib_family_select",
            )
            st.session_state["ws_sl_rib_section_family"] = rib_fam
        with col2:
            rib_pref = st.radio(
                "Rib Section Preference",
                ["Auto-select", "User-specified"],
                index=0,
                key="ws_sl_rib_pref_radio",
            )
            st.session_state["ws_sl_rib_preference"] = "auto" if rib_pref == "Auto-select" else "manual"

        conn_options = ["bolted", "welded"]
        conn_labels = ["Bolted Cleat / Gusset", "Welded"]
        c_idx = conn_options.index(st.session_state["ws_sl_rib_connection"])
        conn_choice = st.radio(
            "Rib-to-Spine Connection",
            conn_labels,
            index=c_idx,
            key="ws_sl_rib_conn_radio",
        )
        st.session_state["ws_sl_rib_connection"] = conn_options[conn_labels.index(conn_choice)]

    # =========================================================================
    # SECTION 5 - MEMBRANE-TO-RIB ATTACHMENT AND PERIMETER CABLE
    # =========================================================================
    with st.expander("5. Membrane Attachment and Perimeter Cable", expanded=False):
        _section_header(
            "Membrane Attachment and Perimeter Cable",
            "How the fabric is attached to the ribs, and how the perimeter cable runs between rib tips."
        )

        attach_options = ["kader", "segmented"]
        attach_labels = [
            "Kader Guider (continuous attachment)",
            "Segmented Edge Cables (discrete attachment)",
        ]
        at_idx = attach_options.index(st.session_state["ws_sl_attachment_type"])
        at_choice = st.radio(
            "Fabric Attachment Method",
            attach_labels,
            index=at_idx,
            key="ws_sl_attach_radio",
        )
        st.session_state["ws_sl_attachment_type"] = attach_options[attach_labels.index(at_choice)]

        if st.session_state["ws_sl_attachment_type"] == "segmented":
            desired = st.number_input(
                "Desired Segment Spacing (m)",
                min_value=0.5, max_value=10.0,
                value=float(st.session_state["ws_sl_segment_spacing"]),
                step=0.1,
                key="ws_sl_seg_spacing_input",
            )
            st.session_state["ws_sl_segment_spacing"] = desired

        # Perimeter cable (auto diameter, user picks type and material)
        st.markdown(
            '<div class="ws-section-help" style="margin-top:1rem;">'
            '<strong>Perimeter Cable</strong> — runs between the tips of the ribs to form the leaf outline.'
            '</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            pc_types = ["6x19", "Locked Coil", "Spiral"]
            pc_idx = pc_types.index(st.session_state["ws_sl_perimeter_cable_type"])
            pc_type = st.selectbox(
                "Perimeter Cable Type",
                pc_types,
                index=pc_idx,
                key="ws_sl_pc_type_select",
            )
            st.session_state["ws_sl_perimeter_cable_type"] = pc_type
        with col2:
            pc_mats = ["stainless", "galvanised"]
            pc_mat_labels = ["Stainless Steel", "Galvanised Steel"]
            pc_idx2 = pc_mats.index(st.session_state["ws_sl_perimeter_cable_material"])
            pc_mat = st.selectbox(
                "Perimeter Cable Material",
                pc_mat_labels,
                index=pc_idx2,
                key="ws_sl_pc_mat_select",
            )
            st.session_state["ws_sl_perimeter_cable_material"] = pc_mats[pc_mat_labels.index(pc_mat)]

        st.markdown(
            '<div class="ws-preview-box">'
            'Perimeter cable diameter is selected automatically by the engine '
            'based on the computed tension.'
            '</div>',
            unsafe_allow_html=True,
        )

    # =========================================================================
    # SECTION 6 - BASEPLATE AND FOUNDATION
    # =========================================================================
    with st.expander("6. Baseplate and Preliminary Foundation", expanded=False):
        _section_header(
            "Baseplate and Preliminary Foundation",
            "The column baseplate anchors the leaf to the ground. "
            "Preliminary foundation sizing depends on the soil at the site."
        )

        st.markdown(
            '<div class="ws-info-box">'
            '<strong>Baseplate and Anchors</strong><br>'
            'Baseplate dimensions and anchor bolt size and count are '
            'auto-selected by the engine based on the column reaction '
            '(axial + moment + torsion). No input required.'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            bearing = st.number_input(
                "Assumed Soil Bearing Capacity (kN/m2)",
                min_value=50.0, max_value=1000.0,
                value=float(st.session_state["ws_sl_soil_bearing"]),
                step=10.0,
                key="ws_sl_soil_bearing_input",
                help="From geotechnical investigation. Typical: sand 150, clay 100, rock 500.",
            )
            st.session_state["ws_sl_soil_bearing"] = bearing
        with col2:
            water = st.number_input(
                "Water Table Depth (m)",
                min_value=0.5, max_value=20.0,
                value=float(st.session_state["ws_sl_water_table"]),
                step=0.5,
                key="ws_sl_water_table_input",
            )
            st.session_state["ws_sl_water_table"] = water

        soil_options = ["sand", "clay", "rock", "filled"]
        soil_labels = ["Sand", "Clay", "Rock", "Filled / Made Ground"]
        s_idx = soil_options.index(st.session_state["ws_sl_soil_type"])
        soil_choice = st.selectbox(
            "Soil Type",
            soil_labels,
            index=s_idx,
            key="ws_sl_soil_type_select",
        )
        st.session_state["ws_sl_soil_type"] = soil_options[soil_labels.index(soil_choice)]

        found_options = ["pad", "pile", "raft"]
        found_labels = ["Pad Footing", "Pile Group", "Raft"]
        f_idx = found_options.index(st.session_state["ws_sl_foundation_type"])
        found_choice = st.selectbox(
            "Foundation Type",
            found_labels,
            index=f_idx,
            key="ws_sl_found_type_select",
        )
        st.session_state["ws_sl_foundation_type"] = found_options[found_labels.index(found_choice)]

        st.markdown(
            '<div class="ws-warning-box">'
            '<strong>Note:</strong> Preliminary foundation sizing only. '
            'Geotechnical verification required. Footing reinforcement and '
            'detailing are not provided by this app. Engage a geotechnical '
            'engineer to confirm.'
            '</div>',
            unsafe_allow_html=True,
        )

    # =========================================================================
    # SECTION 7 - LOADS AND STANDARD
    # =========================================================================
    with st.expander("7. Loads and Design Standard", expanded=False):
        _section_header(
            "Loads and Design Standard",
            "Live load on the ribs and the design code for safety factors."
        )

        live = st.number_input(
            "Live Load on Ribs (kg/m)",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state["ws_sl_live_load"]),
            step=5.0,
            key="ws_sl_live_input",
        )
        st.session_state["ws_sl_live_load"] = live

        std_options = ["EU", "MY", "UK", "CN", "US"]
        std_idx = std_options.index(st.session_state["ws_sl_design_standard"])
        std = st.selectbox(
            "Design Standard",
            std_options,
            index=std_idx,
            key="ws_sl_standard_select",
        )
        st.session_state["ws_sl_design_standard"] = std

        st.markdown(
            '<div class="ws-preview-box">'
            'Wind speed basis: <span class="num">'
            + str(WIND_SPEEDS.get(std, 30.0))
            + ' m/s</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    # =========================================================================
    # ACTIONS
    # =========================================================================
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Back to Registration", key="ws_sl_back", use_container_width=True):
            st.session_state.page = "registration"
            st.rerun()
    with col_b:
        if st.button(
            "Intelligent Design Computing",
            key="ws_sl_run",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.page = "results"
            st.rerun()
