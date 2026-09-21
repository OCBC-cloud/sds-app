# =============================================================================
# SDSe Fluid Design Studio - Cantilever Hypar Workshop
# =============================================================================
# Input page for the Cantilever Hypar variant.
#
# Sibling of Cantilever Leaf. Same column. Same five arrangement
# modes. Different mother object: an asymmetric four-cornered
# saddle canopy cantilevered out sideways from the column.
#
# Geometry (from SPEC_cantilever_hypar.md):
#   - Straight vertical column.
#   - Arc arm anchored at anchor_fraction of column height, arcing
#     upward in the middle. Both ends at the same height.
#   - Diagonal strut from column top to the arm.
#   - Two perpendicular bent ribs at the arm's midpoint, arcing
#     upward. Rib tips higher than the rib anchor.
#   - Saddle membrane spanning four corners.
#   - Edge cables concave inward (per PRINCIPLES_membrane.md).
#
# Arrangement logic reuses engine/leaf_arrangement.py exactly.
#
# Placeholder inputs (see engine/PLACEHOLDERS.md):
#   ws_ch_column_radius
#   ws_ch_arm_arc_radius
#   Membrane edge sag (in the viewer, not a UI input)
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
# FABRIC CLASSIFICATION INFO
# =============================================================================

FABRIC_INFO = {
    "Type I": "700-800 g/m2. Light tensile structures, tents, shade sails.",
    "Type II": "900-1000 g/m2. Medium tensile structures.",
    "Type III": "1050-1200 g/m2. Mid-to-large tensile structures.",
    "Type IV": "1300-1400 g/m2. Large-span structures, stadiums.",
    "Type V": "1450-2000 g/m2. Max span, air-supported roofs.",
}


# =============================================================================
# DEFAULTS
# =============================================================================

def _init_defaults():
    defaults = {
        "ws_ch_object_shape": "hypar",

        # Geometry (real user inputs)
        "ws_ch_column_height": 10.0,
        "ws_ch_arm_reach": 6.0,
        "ws_ch_anchor_fraction": 0.65,
        "ws_ch_rib_reach": 3.0,
        "ws_ch_rib_bend_deg": 15.0,

        # Placeholder inputs (see engine/PLACEHOLDERS.md)
        "ws_ch_column_radius": 0.15,
        "ws_ch_arm_arc_radius": 4.0,

        # Materials
        "ws_ch_steel_grade": "S355",
        "ws_ch_section_family": "CHS",
        "ws_ch_fabric_type": "PVDF",
        "ws_ch_fabric_grade": "Type III",

        # Column and strut
        "ws_ch_column_type": "unipole",
        "ws_ch_column_preference": "auto",
        "ws_ch_strut_angle_deg": 42,

        # Ribs
        "ws_ch_rib_section_family": "CHS",
        "ws_ch_rib_preference": "auto",
        "ws_ch_rib_connection": "bolted",

        # Membrane attachment
        "ws_ch_attachment_type": "kader",
        "ws_ch_perimeter_cable_type": "6x19",
        "ws_ch_perimeter_cable_material": "stainless",
        "ws_ch_membrane_pretension": 2.0,

        # Foundation
        "ws_ch_soil_bearing": 150.0,
        "ws_ch_soil_type": "sand",
        "ws_ch_water_table": 3.0,
        "ws_ch_foundation_type": "pad",
        "ws_ch_found_widget_generation": 0,

        # Loads
        "ws_ch_add_payload": 0.0,
        "ws_ch_design_standard": "MY",

        # Arrangement
        "ws_ch_arrangement": "single",
        "ws_ch_arrangement_count": 4,
        "ws_ch_arrangement_tiers": 1,
        "ws_ch_first_leaf_height": 10.0,
        "ws_ch_leaf_zone_height": 7.0,
        "ws_ch_num_leaves": 8,
        "ws_ch_leaf_angular_width": 60.0,
        "ws_ch_taper_mode": "taper_up",
        "ws_ch_taper_ratio": 0.88,
        "ws_ch_last_geometry": None,

        # Viewer strings
        "ws_ch_viewer_description": "Cantilever Hypar tensile membrane structure",
        "ws_ch_viewer_dimensions": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v





# =============================================================================
# HELPERS
# =============================================================================

def _section_header(title, help_text=""):
    html = '<div class="ws-section-title">' + title + '</div>'
    if help_text:
        html += '<div class="ws-section-help">' + help_text + '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _info_box(text):
    st.markdown(
        '<div class="ws-info-box">' + text + '</div>',
        unsafe_allow_html=True,
    )


def _preview_box(text):
    st.markdown(
        '<div class="ws-preview-box">' + text + '</div>',
        unsafe_allow_html=True,
    )


def _warning_box(text):
    st.markdown(
        '<div class="ws-warning-box">' + text + '</div>',
        unsafe_allow_html=True,
    )


def _validate_hypar_geometry(col_h, reach, anchor_frac, rib_reach, rib_bend):
    warnings = []
    if col_h <= 0:
        warnings.append("Column height must be greater than 0.")
    if reach <= 0:
        warnings.append("Arm reach must be greater than 0.")
    if anchor_frac < 0.55 or anchor_frac > 0.80:
        warnings.append("Anchor fraction outside recommended range 0.55 to 0.80.")
    if rib_reach <= 0:
        warnings.append("Rib reach must be greater than 0.")
    if rib_bend < 5 or rib_bend > 40:
        warnings.append("Rib bend angle outside recommended range 5 to 40 deg.")
    if reach > col_h * 0.9:
        warnings.append("Arm reach close to column height. Cantilever arm may be unstable.")
    if rib_reach > reach * 0.8:
        warnings.append("Rib reach close to arm reach. Check membrane proportions.")
    return warnings


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_saddle_hypar():
    """Render the Cantilever Hypar workshop."""
    st.markdown(WORKSHOP_CSS, unsafe_allow_html=True)
    _init_defaults()

    gen = int(st.session_state.get("ws_ch_found_widget_generation", 0))

    project_name = st.session_state.get("project_info", {}).get("name", "") or "Untitled Project"
    client_name = st.session_state.get("project_info", {}).get("client", "") or "Unknown Client"

    st.markdown(
        '<div class="ws-breadcrumb">'
        'SDSe Fluid Design Studio / '
        '<span class="crumb">Cantilever</span>'
        ' / '
        '<span class="crumb">Cantilever Hypar</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="ws-section">'
        '<div class="ws-section-title">' + project_name + '</div>'
        '<div class="ws-section-help">'
        'Client: ' + client_name + '  |  Structure: Cantilever Hypar'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # =========================================================================
    # SECTION 1 - OBJECT SHAPE
    # =========================================================================
    with st.expander("1. Object Shape", expanded=True):
        _section_header(
            "Object Shape",
            "Choose the base object. Hypar is active now."
        )

        shape_options = ["leaf", "flower", "bell", "hypar"]
        shape_labels = [
            "Leaf (coming soon)",
            "Flower (coming soon)",
            "Bell (coming soon)",
            "Hypar",
        ]
        shape_choice = st.radio(
            "Base Object",
            shape_labels,
            index=3,
            key="ws_ch_shape_radio",
        )
        st.session_state["ws_ch_object_shape"] = "hypar"

        _info_box(
            "The Cantilever Hypar is a saddle-shaped membrane canopy "
            "cantilevered out sideways from a column. Its arrangement "
            "modes are the same as Cantilever Leaf."
        )

    # =========================================================================
    # SECTION 2 - GEOMETRY
    # =========================================================================
    with st.expander("2. Geometry", expanded=False):
        _section_header(
            "Geometry",
            "Overall layout of one Hypar canopy."
        )

        col1, col2 = st.columns(2)
        with col1:
            col_h = st.number_input(
                "Column Height (m) *",
                min_value=2.0, max_value=30.0,
                value=float(st.session_state["ws_ch_column_height"]),
                step=0.5,
                key="ws_ch_column_height_input",
            )
            st.session_state["ws_ch_column_height"] = col_h
        with col2:
            reach = st.number_input(
                "Arm Reach (m) *",
                min_value=1.0, max_value=20.0,
                value=float(st.session_state["ws_ch_arm_reach"]),
                step=0.5,
                key="ws_ch_arm_reach_input",
            )
            st.session_state["ws_ch_arm_reach"] = reach

        col3, col4 = st.columns(2)
        with col3:
            anchor_frac = st.slider(
                "Anchor Height Fraction",
                min_value=0.55, max_value=0.80,
                value=float(st.session_state["ws_ch_anchor_fraction"]),
                step=0.01,
                key="ws_ch_anchor_frac_slider",
                help="Height on the column where the arm anchors, as "
                     "a fraction of column height.",
            )
            st.session_state["ws_ch_anchor_fraction"] = anchor_frac
        with col4:
            rib_reach = st.number_input(
                "Rib Reach (m) *",
                min_value=0.5, max_value=15.0,
                value=float(st.session_state["ws_ch_rib_reach"]),
                step=0.5,
                key="ws_ch_rib_reach_input",
            )
            st.session_state["ws_ch_rib_reach"] = rib_reach

        rib_bend = st.slider(
            "Rib Bend Angle (deg)",
            min_value=5.0, max_value=40.0,
            value=float(st.session_state["ws_ch_rib_bend_deg"]),
            step=1.0,
            key="ws_ch_rib_bend_slider",
            help="How much the ribs arc upward from the arm.",
        )
        st.session_state["ws_ch_rib_bend_deg"] = rib_bend

        _preview_box(
            'Arm anchor height: <span class="num">'
            + ("%.2f m" % (col_h * anchor_frac))
            + '</span> ('
            + ("%.0f%%" % (anchor_frac * 100))
            + ' of column)<br>'
            'Rib rise above arm: <span class="num">'
            + ("%.2f m" % (rib_reach * math.tan(math.radians(rib_bend))))
            + '</span>'
        )

        warns = _validate_hypar_geometry(col_h, reach, anchor_frac, rib_reach, rib_bend)
        for w in warns:
            _warning_box(w)

        _info_box(
            "The membrane surface is not a user input. Its shape is "
            "determined by the equilibrium of membrane pretension and "
            "edge cable tension. The viewer approximates the surface "
            "until the FDM engine lands. See "
            "engine/PRINCIPLES_membrane.md."
        )

    # =========================================================================
    # SECTION 3 - MATERIALS
    # =========================================================================
    with st.expander("3. Materials", expanded=False):
        _section_header(
            "Materials",
            "Steel grade, section family, and fabric."
        )

        col1, col2 = st.columns(2)
        with col1:
            steel_grades = ["S235", "S275", "S355", "S420", "S460"]
            s_idx = steel_grades.index(st.session_state["ws_ch_steel_grade"])
            steel = st.selectbox(
                "Steel Grade",
                steel_grades,
                index=s_idx,
                key="ws_ch_steel_select",
            )
            st.session_state["ws_ch_steel_grade"] = steel
        with col2:
            section_families = ["CHS", "SHS", "RHS", "I-Beam"]
            f_idx = section_families.index(st.session_state["ws_ch_section_family"])
            family = st.selectbox(
                "Section Family",
                section_families,
                index=f_idx,
                key="ws_ch_family_select",
            )
            st.session_state["ws_ch_section_family"] = family

        col3, col4 = st.columns(2)
        with col3:
            fabric_types = list(FABRIC_PROPERTIES.keys())
            ft_idx = fabric_types.index(st.session_state["ws_ch_fabric_type"]) if st.session_state["ws_ch_fabric_type"] in fabric_types else 0
            fabric_type = st.selectbox(
                "Fabric Type",
                fabric_types,
                index=ft_idx,
                key="ws_ch_fabric_type_select",
            )
            st.session_state["ws_ch_fabric_type"] = fabric_type
        with col4:
            grades = [k for k in FABRIC_PROPERTIES.get(fabric_type, {}).keys() if k != "default"]
            if not grades:
                grades = ["Type III"]
            g_idx = grades.index(st.session_state["ws_ch_fabric_grade"]) if st.session_state["ws_ch_fabric_grade"] in grades else 0
            grade = st.selectbox(
                "Fabric Grade",
                grades,
                index=g_idx,
                key="ws_ch_fabric_grade_select",
            )
            st.session_state["ws_ch_fabric_grade"] = grade

        info_text = FABRIC_INFO.get(
            st.session_state["ws_ch_fabric_grade"],
            "Refer to manufacturer datasheet.",
        )
        _info_box(
            "<strong>" + st.session_state["ws_ch_fabric_grade"]
            + " Fabric</strong><br>" + info_text
        )

    # =========================================================================
    # SECTION 4 - COLUMN AND STRUT
    # =========================================================================
    with st.expander("4. Column and Strut", expanded=False):
        _section_header(
            "Column and Strut",
            "The vertical column and the diagonal strut that triangulates "
            "the arm into the column."
        )

        col_types = ["unipole", "truss"]
        col_labels = ["Uni-Pole Column", "Truss Column"]
        ct_idx = col_types.index(st.session_state["ws_ch_column_type"])
        ct_choice = st.radio(
            "Column Type",
            col_labels,
            index=ct_idx,
            key="ws_ch_column_type_radio",
        )
        st.session_state["ws_ch_column_type"] = col_types[col_labels.index(ct_choice)]

        col_pref = st.radio(
            "Column Section Preference",
            ["Auto-select", "User-specified"],
            index=0,
            key="ws_ch_col_pref_radio",
        )
        st.session_state["ws_ch_column_preference"] = "auto" if col_pref == "Auto-select" else "manual"

        _preview_box(
            "The diagonal strut runs from the column top down to a "
            "computed anchor point on the arm. The intersection point "
            "is calculated by the engine (geometry intersection for "
            "now, mechanics optimum when the structural engine lands)."
        )

        _info_box(
            "Column base is a rigid baseplate. Torsion and moment are "
            "resisted by the baseplate."
        )





# =========================================================================
    # SECTION 5 - RIBS
    # =========================================================================
    with st.expander("5. Ribs", expanded=False):
        _section_header(
            "Ribs",
            "The two perpendicular bent ribs at the arm's midpoint."
        )

        col1, col2 = st.columns(2)
        with col1:
            rib_families = ["CHS", "SHS", "RHS"]
            rf_idx = rib_families.index(st.session_state["ws_ch_rib_section_family"])
            rib_fam = st.selectbox(
                "Rib Section Family",
                rib_families,
                index=rf_idx,
                key="ws_ch_rib_family_select",
            )
            st.session_state["ws_ch_rib_section_family"] = rib_fam
        with col2:
            rib_pref = st.radio(
                "Rib Section Preference",
                ["Auto-select", "User-specified"],
                index=0,
                key="ws_ch_rib_pref_radio",
            )
            st.session_state["ws_ch_rib_preference"] = "auto" if rib_pref == "Auto-select" else "manual"

        conn_options = ["bolted", "welded"]
        conn_labels = ["Bolted Cleat / Gusset", "Welded"]
        c_idx = conn_options.index(st.session_state["ws_ch_rib_connection"])
        conn_choice = st.radio(
            "Rib-to-Arm Connection",
            conn_labels,
            index=c_idx,
            key="ws_ch_rib_conn_radio",
        )
        st.session_state["ws_ch_rib_connection"] = conn_options[conn_labels.index(conn_choice)]

        _info_box(
            "Both ribs attach at the exact midpoint of the arm. They "
            "arc upward, so their tips sit higher than the rib anchor "
            "on the arm. This curvature pairs with the arm's downward "
            "run to form the saddle membrane."
        )

    # =========================================================================
    # SECTION 6 - MEMBRANE ATTACHMENT AND PERIMETER CABLE
    # =========================================================================
    with st.expander("6. Membrane Attachment and Perimeter Cable", expanded=False):
        _section_header(
            "Membrane Attachment and Perimeter Cable",
            "How the fabric is attached, and how the perimeter cable runs."
        )

        attach_options = ["kader", "segmented"]
        attach_labels = [
            "Kader Guider (continuous)",
            "Segmented Edge (discrete)",
        ]
        at_idx = attach_options.index(st.session_state["ws_ch_attachment_type"])
        at_choice = st.radio(
            "Fabric Attachment Method",
            attach_labels,
            index=at_idx,
            key="ws_ch_attach_radio",
        )
        st.session_state["ws_ch_attachment_type"] = attach_options[attach_labels.index(at_choice)]

        _info_box(
            "<strong>Membrane Boundary</strong><br>"
            "The membrane spans four corners: the arm anchor, the arm "
            "tip, and the two rib tips. Its four edges are cable-"
            "supported and curve inward under equilibrium. This is "
            "the SDSe form-finding principle (engine/PRINCIPLES_membrane.md)."
        )

        col1, col2 = st.columns(2)
        with col1:
            pc_types = ["6x19", "Locked Coil", "Spiral"]
            pc_idx = pc_types.index(st.session_state["ws_ch_perimeter_cable_type"])
            pc_type = st.selectbox(
                "Perimeter Cable Type",
                pc_types,
                index=pc_idx,
                key="ws_ch_pc_type_select",
            )
            st.session_state["ws_ch_perimeter_cable_type"] = pc_type
        with col2:
            pc_mats = ["stainless", "galvanised"]
            pc_mat_labels = ["Stainless Steel", "Galvanised Steel"]
            pc_idx2 = pc_mats.index(st.session_state["ws_ch_perimeter_cable_material"])
            pc_mat = st.selectbox(
                "Perimeter Cable Material",
                pc_mat_labels,
                index=pc_idx2,
                key="ws_ch_pc_mat_select",
            )
            st.session_state["ws_ch_perimeter_cable_material"] = pc_mats[pc_mat_labels.index(pc_mat)]

        _preview_box(
            "Perimeter cable diameter is selected automatically by the engine."
        )

        mem_pre = st.slider(
            "Membrane Pretension (kN/m)",
            min_value=0.5, max_value=8.0,
            value=float(st.session_state["ws_ch_membrane_pretension"]),
            step=0.1,
            key="ws_ch_mem_pre_slider",
        )
        st.session_state["ws_ch_membrane_pretension"] = mem_pre





# =========================================================================
    # SECTION 7 - BASEPLATE AND PRELIMINARY FOUNDATION
    # =========================================================================
    with st.expander("7. Baseplate and Preliminary Foundation", expanded=False):
        _section_header(
            "Baseplate and Preliminary Foundation",
            "Sizing depends on soil at the site."
        )

        if st.button(
            "Default",
            key="ws_ch_found_default",
        ):
            st.session_state["ws_ch_soil_bearing"] = 150.0
            st.session_state["ws_ch_soil_type"] = "sand"
            st.session_state["ws_ch_water_table"] = 3.0
            st.session_state["ws_ch_foundation_type"] = "pad"
            st.session_state["ws_ch_found_widget_generation"] = gen + 1
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            bearing = st.number_input(
                "Soil Bearing Capacity (kN/m2)",
                min_value=50.0, max_value=1000.0,
                value=float(st.session_state["ws_ch_soil_bearing"]),
                step=10.0,
                key="ws_ch_soil_bearing_input_" + str(gen),
            )
            st.session_state["ws_ch_soil_bearing"] = bearing
        with col2:
            water = st.number_input(
                "Water Table Depth (m)",
                min_value=0.5, max_value=20.0,
                value=float(st.session_state["ws_ch_water_table"]),
                step=0.5,
                key="ws_ch_water_table_input_" + str(gen),
            )
            st.session_state["ws_ch_water_table"] = water

        soil_options = ["sand", "clay", "rock", "filled"]
        soil_labels = ["Sand", "Clay", "Rock", "Filled"]
        s_idx = soil_options.index(st.session_state["ws_ch_soil_type"])
        soil_choice = st.selectbox(
            "Soil Type",
            soil_labels,
            index=s_idx,
            key="ws_ch_soil_type_select_" + str(gen),
        )
        st.session_state["ws_ch_soil_type"] = soil_options[soil_labels.index(soil_choice)]

        found_options = ["pad", "pile", "raft"]
        found_labels = ["Pad Footing", "Pile Group", "Raft"]
        f_idx = found_options.index(st.session_state["ws_ch_foundation_type"])
        found_choice = st.selectbox(
            "Foundation Type",
            found_labels,
            index=f_idx,
            key="ws_ch_found_type_select_" + str(gen),
        )
        st.session_state["ws_ch_foundation_type"] = found_options[found_labels.index(found_choice)]

        _warning_box(
            "Preliminary sizing only. Geotechnical verification required."
        )

    # =========================================================================
    # SECTION 8 - LOADS AND DESIGN STANDARD
    # =========================================================================
    with st.expander("8. Loads and Design Standard", expanded=False):
        _section_header(
            "Loads and Design Standard",
            "User-added loads. Design code for safety factors."
        )

        payload = st.number_input(
            "Add. Pay Load (kg/m)",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state["ws_ch_add_payload"]),
            step=5.0,
            key="ws_ch_add_payload_input",
        )
        st.session_state["ws_ch_add_payload"] = payload

        std_options = ["EU", "MY", "UK", "CN", "US"]
        std_idx = std_options.index(st.session_state["ws_ch_design_standard"])
        std = st.selectbox(
            "Design Standard",
            std_options,
            index=std_idx,
            key="ws_ch_standard_select",
        )
        st.session_state["ws_ch_design_standard"] = std

        _preview_box(
            'Wind speed basis: <span class="num">'
            + str(WIND_SPEEDS.get(std, 30.0))
            + ' m/s</span>'
        )

    # =========================================================================
    # SECTION 9 - ARRANGEMENT
    # =========================================================================
    with st.expander("9. Arrangement", expanded=False):
        _section_header(
            "Arrangement",
            "How the mother object is arranged around the column. "
            "Identical to Cantilever Leaf."
        )

        arrangement_options = [
            "single", "double", "multiple", "tree_stack", "tiered_helix"
        ]
        arrangement_labels = [
            "Single",
            "Double (mirror)",
            "Multiple (radial)",
            "Tree (stacked tiers)",
            "Tiered Helix (engine)",
        ]
        arr_idx = arrangement_options.index(st.session_state["ws_ch_arrangement"])
        arr_choice = st.radio(
            "Arrangement",
            arrangement_labels,
            index=arr_idx,
            key="ws_ch_arrangement_radio",
        )
        st.session_state["ws_ch_arrangement"] = arrangement_options[arrangement_labels.index(arr_choice)]

        if st.session_state["ws_ch_arrangement"] == "multiple":
            n_units = st.number_input(
                "Number of objects around column",
                min_value=2, max_value=8,
                value=int(st.session_state["ws_ch_arrangement_count"]),
                step=1,
                key="ws_ch_arr_n_input",
            )
            st.session_state["ws_ch_arrangement_count"] = n_units

        elif st.session_state["ws_ch_arrangement"] == "tree_stack":
            n_tiers = st.number_input(
                "Number of tiers",
                min_value=1, max_value=3,
                value=int(st.session_state["ws_ch_arrangement_tiers"]),
                step=1,
                key="ws_ch_arr_tiers_input",
            )
            st.session_state["ws_ch_arrangement_tiers"] = n_tiers

            _preview_box(
                "Tier scale factor 0.75. Rotation fixed by engine. "
                "User only designs the mother object."
            )

        elif st.session_state["ws_ch_arrangement"] == "tiered_helix":
            st.session_state["ws_ch_first_leaf_height"] = float(
                st.session_state.get("ws_ch_column_height", 10.0)
            )

            lz_h = st.number_input(
                "Leaf Zone Height (m)",
                min_value=0.5, max_value=30.0,
                value=float(st.session_state["ws_ch_leaf_zone_height"]),
                step=0.5,
                key="ws_ch_lzh_input",
            )
            st.session_state["ws_ch_leaf_zone_height"] = lz_h

            n_lv = st.number_input(
                "Number of Leaves",
                min_value=1, max_value=30,
                value=int(st.session_state["ws_ch_num_leaves"]),
                step=1,
                key="ws_ch_num_leaves_input",
            )
            st.session_state["ws_ch_num_leaves"] = n_lv

            col_r = st.number_input(
                "Column Radius (m)",
                min_value=0.05, max_value=1.00,
                value=float(st.session_state["ws_ch_column_radius"]),
                step=0.01,
                key="ws_ch_col_r_input",
            )
            st.session_state["ws_ch_column_radius"] = col_r

            law = st.number_input(
                "Leaf Angular Width (deg)",
                min_value=10, max_value=180,
                value=int(st.session_state["ws_ch_leaf_angular_width"]),
                step=5,
                key="ws_ch_law_input",
            )
            st.session_state["ws_ch_leaf_angular_width"] = float(law)

            taper_opts = ["full_scale", "taper_up", "taper_down"]
            taper_labels = ["Full Scale", "Taper Up (smaller at top)", "Taper Down (smaller at bottom)"]
            t_idx = taper_opts.index(st.session_state["ws_ch_taper_mode"])
            taper_choice = st.radio(
                "Scale Mode",
                taper_labels,
                index=t_idx,
                key="ws_ch_taper_mode_radio",
            )
            st.session_state["ws_ch_taper_mode"] = taper_opts[taper_labels.index(taper_choice)]

            if st.session_state["ws_ch_taper_mode"] != "full_scale":
                tr = st.number_input(
                    "Taper Ratio (per leaf)",
                    min_value=0.50, max_value=0.99,
                    value=float(st.session_state["ws_ch_taper_ratio"]),
                    step=0.01,
                    key="ws_ch_taper_ratio_input",
                )
                st.session_state["ws_ch_taper_ratio"] = tr

            _preview_box(
                "Bud length = column radius + 0.45 m. "
                "Helix turns computed by the engine."
            )

        _info_box(
            "Arrangement multiplies the mother object around the "
            "column. Mother geometry is not changed by arrangement."
        )

    # =========================================================================
    # VIEWER STRINGS (rebuilt live, read by the Results page)
    # =========================================================================
    # Total height = column height for all arrangements.
    # For tiered_helix, extend to first_leaf_height + leaf_zone_height.

    _arr = st.session_state.get("ws_ch_arrangement", "single")

    _col_h = float(st.session_state.get(
        "ws_ch_column_height_input",
        st.session_state.get("ws_ch_column_height", 10.0),
    ))

    if _arr == "tiered_helix":
        _lz_h = float(st.session_state.get(
            "ws_ch_lzh_input",
            st.session_state.get("ws_ch_leaf_zone_height", 7.0),
        ))
        _total_h = _col_h + _lz_h
    else:
        _total_h = _col_h

    st.session_state["ws_ch_viewer_description"] = (
        "Cantilever Hypar tensile membrane structure"
    )
    st.session_state["ws_ch_viewer_dimensions"] = (
        "Total height " + ("%.2f" % _total_h) + " m"
    )

    # =========================================================================
    # ACTIONS
    # =========================================================================
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Back to Registration", key="ws_ch_back", use_container_width=True):
            st.session_state.page = "registration"
            st.rerun()
    with col_b:
        if st.button(
            "Intelligent Design Computing",
            key="ws_ch_run",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.page = "results"
            st.rerun()





