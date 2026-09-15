# =============================================================================
# SDSe Fluid Design Studio - Cantilever Leaf Workshop
# =============================================================================
# Input page for the Cantilever Leaf variant.
#
# Design decisions (agreed 2026-09-15):
#   - Object Shape selector at top
#   - "Adjust Rib Lengths" opens ui/rooms/leaf_room.py
#   - Rib lengths computed from geometry
#   - Strut joint height FIXED at 75% of column height
#   - Arrangement section: Single / Double / Multiple / Tree Stack / Tree Spiral
#   - Tree Stack: 1-3 tiers, scale factor 0.75 fixed
#   - 9 collapsible sections total
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
    "Type V": "1450-2000 g/m2. Maximum span, air-supported roofs.",
}


# =============================================================================
# DEFAULTS
# =============================================================================

def _init_defaults():
    defaults = {
        "ws_sl_object_shape": "leaf",
        "ws_sl_column_height": 10.0,
        "ws_sl_outreach": 10.0,
        "ws_sl_ribs_per_side": 7,
        "ws_sl_rib_tilt": 20,
        "ws_sl_rib_spacing": 45,
        "ws_sl_arc_radius": 5.0,
        "ws_sl_curve_type": "parabolic",
        "ws_sl_steel_grade": "S355",
        "ws_sl_section_family": "CHS",
        "ws_sl_fabric_type": "PVDF",
        "ws_sl_fabric_grade": "Type III",
        "ws_sl_column_type": "unipole",
        "ws_sl_column_preference": "auto",
        "ws_sl_rib_section_family": "CHS",
        "ws_sl_rib_preference": "auto",
        "ws_sl_rib_connection": "bolted",
        "ws_sl_attachment_type": "kader",
        "ws_sl_perimeter_cable_type": "6x19",
        "ws_sl_perimeter_cable_material": "stainless",
        "ws_sl_membrane_pretension": 2.0,
        "ws_sl_soil_bearing": 150.0,
        "ws_sl_soil_type": "sand",
        "ws_sl_water_table": 3.0,
        "ws_sl_foundation_type": "pad",
        "ws_sl_found_widget_generation": 0,
        "ws_sl_add_payload": 0.0,
        "ws_sl_design_standard": "MY",
        "ws_sl_arrangement": "single",
        "ws_sl_arrangement_count": 4,
        "ws_sl_arrangement_tiers": 1,
        "ws_sl_arrangement_spiral_count": 8,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =============================================================================
# HELPERS
# =============================================================================

def _compute_rib_lengths(outreach, tilt_deg, n_ribs):
    """Return a list of computed rib lengths (in metres)."""
    lengths = []
    if n_ribs < 1:
        return lengths
    if n_ribs == 1:
        ts = [0.5]
    else:
        ts = []
        for i in range(n_ribs):
            t = 0.08 + (0.92 - 0.08) * i / (n_ribs - 1)
            ts.append(t)
    for t in ts:
        half_w = outreach * 0.42 * (math.sin(math.pi * t) ** 0.7)
        tilt_local = tilt_deg * (math.sin(math.pi * t) ** 0.7)
        z_rise = half_w * math.tan(math.radians(tilt_local))
        length = math.sqrt(half_w * half_w + z_rise * z_rise)
        lengths.append(round(length, 2))
    return lengths


def _rib_position_label(i, n):
    """Return a position word for rib index i of n."""
    if n <= 1:
        return "centre"
    if i == 0:
        return "near column"
    if i == n - 1:
        return "near tip"
    mid = (n - 1) / 2.0
    if abs(i - mid) < 0.5:
        return "centre"
    if i < mid:
        return "inner"
    return "outer"


def _validate_leaf_geometry(col_h, outreach, ribs, tilt):
    warnings = []
    if col_h <= 0:
        warnings.append("Column height must be greater than 0.")
    if outreach <= 0:
        warnings.append("Leaf outreach must be greater than 0.")
    if ribs < 5:
        warnings.append("Minimum 5 ribs per side for a proper leaf shape.")
    if ribs > 7:
        warnings.append("Maximum 7 ribs per side for Leaf.")
    if tilt < 10:
        warnings.append("Rib tilt below 10 degrees may not drain properly.")
    if tilt > 40:
        warnings.append("Rib tilt above 40 degrees loses the leaf silhouette.")
    if outreach > 12 and col_h < outreach:
        warnings.append("Tall outreach relative to column height.")
    return warnings


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










# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_saddle_leaf():
    """Render the Cantilever Leaf workshop."""
    st.markdown(WORKSHOP_CSS, unsafe_allow_html=True)
    _init_defaults()

    gen = int(st.session_state.get("ws_sl_found_widget_generation", 0))

    project_name = st.session_state.get("project_info", {}).get("name", "") or "Untitled Project"
    client_name = st.session_state.get("project_info", {}).get("client", "") or "Unknown Client"

    st.markdown(
        '<div class="ws-breadcrumb">'
        'SDSe Fluid Design Studio / '
        '<span class="crumb">Cantilever</span>'
        ' / '
        '<span class="crumb">Cantilever Leaf</span>'
        '</div>',
        unsafe_allow_html=True,
    )

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
    # SECTION 1 - OBJECT SHAPE
    # =========================================================================
    with st.expander("1. Object Shape", expanded=True):
        _section_header(
            "Object Shape",
            "Choose the base object. Leaf is active now."
        )

        shape_options = ["leaf", "flower", "bell", "hypar"]
        shape_labels = [
            "Leaf",
            "Flower (coming soon)",
            "Bell (coming soon)",
            "Hypar (coming soon)",
        ]
        shape_idx = shape_options.index(st.session_state["ws_sl_object_shape"])
        shape_choice = st.radio(
            "Base Object",
            shape_labels,
            index=shape_idx,
            key="ws_sl_shape_radio",
        )
        st.session_state["ws_sl_object_shape"] = "leaf"

        n_ribs = int(st.session_state.get("ws_sl_ribs_per_side", 7))
        rib_override = st.session_state.get("ws_sl_rib_lengths_override", [])
        rib_base = st.session_state.get("ws_sl_rib_base_lengths", [])
        is_sym = st.session_state.get("ws_sl_rib_symmetric", True)

        if rib_override:
            min_l = min(rib_override)
            max_l = max(rib_override)
            rib_summary = (
                "Ribs: <strong>" + str(n_ribs) + "</strong> pairs, "
                "<strong>" + ("Symmetric" if is_sym else "Individual") + "</strong><br>"
                "User-adjusted lengths: <strong>" + ("%.2f" % min_l)
                + " m</strong> to <strong>" + ("%.2f" % max_l) + " m</strong>"
            )
        elif rib_base:
            min_l = min(rib_base)
            max_l = max(rib_base)
            rib_summary = (
                "Ribs: <strong>" + str(n_ribs) + "</strong> pairs, "
                "<strong>System computed</strong><br>"
                "Lengths: <strong>" + ("%.2f" % min_l)
                + " m</strong> to <strong>" + ("%.2f" % max_l) + " m</strong>"
            )
        else:
            rib_summary = (
                "Ribs: <strong>" + str(n_ribs) + "</strong> pairs<br>"
                "Lengths will appear once geometry is set."
            )

        _preview_box(rib_summary)

        if st.button(
            "Adjust Rib Lengths",
            key="ws_sl_open_rib_room",
            use_container_width=True,
        ):
            st.session_state.page = "leaf_room"
            st.rerun()

        _info_box("Opens a dedicated room for individual rib adjustment.")

    # =========================================================================
    # SECTION 2 - GEOMETRY
    # =========================================================================
    with st.expander("2. Geometry", expanded=False):
        _section_header(
            "Geometry",
            "Overall layout of the leaf."
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
                min_value=2.0, max_value=12.0,
                value=float(st.session_state["ws_sl_outreach"]),
                step=0.5,
                key="ws_sl_outreach_input",
            )
            st.session_state["ws_sl_outreach"] = outreach

        col3, col4 = st.columns(2)
        with col3:
            ribs = st.number_input(
                "Ribs per Side (min 5, max 7) *",
                min_value=5, max_value=7,
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

        computed_lengths = _compute_rib_lengths(outreach, tilt, ribs)
        st.session_state["ws_sl_rib_base_lengths"] = computed_lengths

        length_strs = []
        for i, L in enumerate(computed_lengths):
            pos = _rib_position_label(i, len(computed_lengths))
            length_strs.append(
                "Rib " + str(i + 1) + " (" + pos + "): "
                "<strong>" + ("%.2f" % L) + " m</strong>"
            )
        preview_html = "<br>".join(length_strs)
        _preview_box(
            "<strong>Computed rib lengths</strong><br>" + preview_html
        )

        warns = _validate_leaf_geometry(col_h, outreach, ribs, tilt)
        for w in warns:
            _warning_box(w)










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

        info_text = FABRIC_INFO.get(
            st.session_state["ws_sl_fabric_grade"],
            "Refer to manufacturer datasheet.",
        )
        _info_box(
            "<strong>" + st.session_state["ws_sl_fabric_grade"]
            + " Fabric</strong><br>" + info_text
        )

    # =========================================================================
    # SECTION 4 - COLUMN AND SPINE
    # =========================================================================
    with st.expander("4. Column and Spine", expanded=False):
        _section_header(
            "Column and Spine",
            "The uni-pole column and the curved spine."
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

        col_h_val = float(st.session_state.get("ws_sl_column_height", 10.0))
        strut_joint = round(col_h_val * 0.75, 2)
        st.session_state["ws_sl_strut_joint_height"] = strut_joint

        _preview_box(
            'Strut joint height: <span class="num">'
            + ("%.2f m" % strut_joint)
            + '</span> (75% of column height)<br>'
            'Fixed by the engine.'
        )

        _preview_box(
            "Column base is a rigid baseplate. "
            "Torsion and moment are resisted by the baseplate."
        )

    # =========================================================================
    # SECTION 5 - RIBS
    # =========================================================================
    with st.expander("5. Ribs", expanded=False):
        _section_header(
            "Ribs",
            "Radial ribs extending outward from the spine."
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
        at_idx = attach_options.index(st.session_state["ws_sl_attachment_type"])
        at_choice = st.radio(
            "Fabric Attachment Method",
            attach_labels,
            index=at_idx,
            key="ws_sl_attach_radio",
        )
        st.session_state["ws_sl_attachment_type"] = attach_options[attach_labels.index(at_choice)]

        _info_box(
            "<strong>Perimeter Cable Path</strong><br>"
            "Follows the membrane natural edge. Ends attach to the "
            "outermost rib tips. Curve is a result of form-finding."
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

        _preview_box(
            "Perimeter cable diameter is selected automatically by the engine."
        )

        mem_pre = st.slider(
            "Membrane Pretension (kN/m)",
            min_value=0.5, max_value=8.0,
            value=float(st.session_state["ws_sl_membrane_pretension"]),
            step=0.1,
            key="ws_sl_mem_pre_slider",
        )
        st.session_state["ws_sl_membrane_pretension"] = mem_pre

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
            key="ws_sl_found_default",
        ):
            st.session_state["ws_sl_soil_bearing"] = 150.0
            st.session_state["ws_sl_soil_type"] = "sand"
            st.session_state["ws_sl_water_table"] = 3.0
            st.session_state["ws_sl_foundation_type"] = "pad"
            st.session_state["ws_sl_found_widget_generation"] = gen + 1
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            bearing = st.number_input(
                "Soil Bearing Capacity (kN/m2)",
                min_value=50.0, max_value=1000.0,
                value=float(st.session_state["ws_sl_soil_bearing"]),
                step=10.0,
                key="ws_sl_soil_bearing_input_" + str(gen),
            )
            st.session_state["ws_sl_soil_bearing"] = bearing
        with col2:
            water = st.number_input(
                "Water Table Depth (m)",
                min_value=0.5, max_value=20.0,
                value=float(st.session_state["ws_sl_water_table"]),
                step=0.5,
                key="ws_sl_water_table_input_" + str(gen),
            )
            st.session_state["ws_sl_water_table"] = water

        soil_options = ["sand", "clay", "rock", "filled"]
        soil_labels = ["Sand", "Clay", "Rock", "Filled"]
        s_idx = soil_options.index(st.session_state["ws_sl_soil_type"])
        soil_choice = st.selectbox(
            "Soil Type",
            soil_labels,
            index=s_idx,
            key="ws_sl_soil_type_select_" + str(gen),
        )
        st.session_state["ws_sl_soil_type"] = soil_options[soil_labels.index(soil_choice)]

        found_options = ["pad", "pile", "raft"]
        found_labels = ["Pad Footing", "Pile Group", "Raft"]
        f_idx = found_options.index(st.session_state["ws_sl_foundation_type"])
        found_choice = st.selectbox(
            "Foundation Type",
            found_labels,
            index=f_idx,
            key="ws_sl_found_type_select_" + str(gen),
        )
        st.session_state["ws_sl_foundation_type"] = found_options[found_labels.index(found_choice)]

        _warning_box(
            "Preliminary sizing only. Geotechnical verification required."
        )

    # =========================================================================
    # SECTION 8 - LOADS AND STANDARD
    # =========================================================================
    with st.expander("8. Loads and Design Standard", expanded=False):
        _section_header(
            "Loads and Design Standard",
            "User-added loads. Design code for safety factors."
        )

        payload = st.number_input(
            "Add. Pay Load (kg/m)",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state["ws_sl_add_payload"]),
            step=5.0,
            key="ws_sl_add_payload_input",
        )
        st.session_state["ws_sl_add_payload"] = payload

        std_options = ["EU", "MY", "UK", "CN", "US"]
        std_idx = std_options.index(st.session_state["ws_sl_design_standard"])
        std = st.selectbox(
            "Design Standard",
            std_options,
            index=std_idx,
            key="ws_sl_standard_select",
        )
        st.session_state["ws_sl_design_standard"] = std

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
            "How the mother object is arranged around the column."
        )

        arrangement_options = [
            "single", "double", "multiple", "tree_stack", "tree_spiral"
        ]
        arrangement_labels = [
            "Single",
            "Double (mirror)",
            "Multiple (radial)",
            "Tree (stacked tiers)",
            "Tree (spiral)",
        ]
        arr_idx = arrangement_options.index(st.session_state["ws_sl_arrangement"])
        arr_choice = st.radio(
            "Arrangement",
            arrangement_labels,
            index=arr_idx,
            key="ws_sl_arrangement_radio",
        )
        st.session_state["ws_sl_arrangement"] = arrangement_options[arrangement_labels.index(arr_choice)]

        if st.session_state["ws_sl_arrangement"] == "multiple":
            n_leaves = st.slider(
                "Number of objects around column",
                min_value=2, max_value=8,
                value=int(st.session_state["ws_sl_arrangement_count"]),
                step=1,
                key="ws_sl_arr_n_slider",
            )
            st.session_state["ws_sl_arrangement_count"] = n_leaves

        elif st.session_state["ws_sl_arrangement"] == "tree_stack":
            n_tiers = st.slider(
                "Number of tiers",
                min_value=1, max_value=3,
                value=int(st.session_state["ws_sl_arrangement_tiers"]),
                step=1,
                key="ws_sl_arr_tiers_slider",
            )
            st.session_state["ws_sl_arrangement_tiers"] = n_tiers

            _preview_box(
                "Tier scale factor 0.75. Rotation fixed by engine. "
                "User only designs the mother object."
            )

        elif st.session_state["ws_sl_arrangement"] == "tree_spiral":
            n_spiral = st.slider(
                "Number of leaves in spiral",
                min_value=3, max_value=15,
                value=int(st.session_state["ws_sl_arrangement_spiral_count"]),
                step=1,
                key="ws_sl_arr_spiral_slider",
            )
            st.session_state["ws_sl_arrangement_spiral_count"] = n_spiral

            _preview_box(
                "Spiral rise, rotation, and scale are fixed by the engine. "
                "User only designs the mother object."
            )

        _info_box(
            "Arrangement multiplies the mother object around the "
            "column. Mother geometry is not changed by arrangement."
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
