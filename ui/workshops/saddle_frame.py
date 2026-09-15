# =============================================================================
# SDSe Fluid Design Studio - Beam Supported Saddle Workshop
# =============================================================================
# Input page for the Beam Supported Saddle variant.
# Members: membrane + main beam + purlins + secondary beams.
#
# Secondary beam rule (silent):
#   Baseline 2 per beam. Max unsupported 15 m.
# Purlin rule (silent):
#   One at apex, then every 2.5 m outward.
# =============================================================================

import math

import streamlit as st

from data.materials import FABRIC_PROPERTIES
from data.constants import WIND_SPEEDS

from ui.workshops._shared import (
    WORKSHOP_CSS,
    section_header,
    render_breadcrumb,
    render_project_header,
    info_box,
    preview_box,
    warning_box,
)


# =============================================================================
# DEFAULTS
# =============================================================================

def _init_defaults():
    """Initialise workshop state on first entry."""
    defaults = {
        "ws_bs_span": 10.0,
        "ws_bs_apex": 15.0,
        "ws_bs_rise": 6.2,
        "ws_bs_curve_type": "parabolic",
        "ws_bs_steel_grade": "S355",
        "ws_bs_section_family": "CHS",
        "ws_bs_fabric_type": "PVDF",
        "ws_bs_fabric_grade": "Type III",
        "ws_bs_member_construction": "single_beam",
        "ws_bs_section_preference": "auto",
        "ws_bs_support_type_start": "pinned",
        "ws_bs_support_type_end": "pinned",
        "ws_bs_secondary_count": 2,
        "ws_bs_secondary_count_override": False,
        "ws_bs_secondary_construction": "single_beam",
        "ws_bs_secondary_section_family": "CHS",
        "ws_bs_secondary_base_connection": "pinned",
        "ws_bs_uplift_angle": 45,
        "ws_bs_spread_angle": 30,
        "ws_bs_membrane_pretension": 2.0,
        "ws_bs_purlin_construction": "single_beam",
        "ws_bs_purlin_section_family": "CHS",
        "ws_bs_soil_bearing": 150.0,
        "ws_bs_soil_type": "sand",
        "ws_bs_water_table": 3.0,
        "ws_bs_foundation_type": "pad",
        "ws_bs_found_widget_generation": 0,
        "ws_bs_add_payload": 0.0,
        "ws_bs_design_standard": "MY",
        "ws_bs_attachment_type": "kader",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =============================================================================
# HELPERS
# =============================================================================

def _validate_geometry(span, apex, rise):
    """Return list of warning messages for geometry issues."""
    warnings = []
    if span <= 0:
        warnings.append("Span must be greater than 0.")
    if apex <= 0:
        warnings.append("Apex-to-Apex must be greater than 0.")
    if rise <= 0:
        warnings.append("Rise must be greater than 0.")
    if span > 0 and rise > 0:
        ratio = rise / span
        if ratio < 0.05:
            warnings.append("Rise / Span ratio is very low.")
        elif ratio > 0.5:
            warnings.append("Rise / Span ratio is very high.")
    return warnings


def _arc_length_parabola(span, rise):
    """Arc length of parabolic beam by numerical integration."""
    if span <= 0:
        return 0.0
    n_seg = 100
    x_start = -span / 2.0
    x_end = span / 2.0
    dx = (x_end - x_start) / n_seg
    total = 0.0
    for i in range(n_seg):
        x0 = x_start + i * dx
        x1 = x0 + dx
        z0 = rise * (1.0 - (2.0 * x0 / span) ** 2)
        z1 = rise * (1.0 - (2.0 * x1 / span) ** 2)
        dz = z1 - z0
        total += math.sqrt(dx * dx + dz * dz)
    return total


def _compute_secondary_count(arc_length):
    """
    Return secondary beams PER BEAM.
    Baseline 2. Middle section (0.65 x arc) divided into
    equal sub-sections each <= 15 m.
    """
    MAX_UNSUPPORTED = 15.0
    middle = 0.650 * arc_length
    if middle <= MAX_UNSUPPORTED:
        base = 2
    else:
        n_subsections = int(math.ceil(middle / MAX_UNSUPPORTED))
        base = 1 + n_subsections
    if base < 2:
        base = 2
    return base


def _compute_secondary_positions(per_beam_count):
    """Arc-length fractions for secondary beam positions."""
    if per_beam_count < 2:
        return [0.5]
    if per_beam_count == 2:
        return [0.175, 0.825]

    n_middle = per_beam_count - 2
    m_start = 0.175
    m_end = 0.825
    m_span = m_end - m_start
    step = m_span / (n_middle + 1)

    fractions = [m_start]
    for i in range(1, n_middle + 1):
        fractions.append(m_start + i * step)
    fractions.append(m_end)
    return fractions


def _compute_purlin_positions(span):
    """Purlins every 2.5 m from centre, symmetric."""
    interval = 2.5
    half_span = span / 2.0
    positions = [0.0]
    k = 1
    while True:
        offset = k * interval
        if offset > half_span - interval:
            break
        positions.append(offset)
        positions.append(-offset)
        k += 1
    return sorted(positions)










# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_saddle_frame():
    """Render the Beam Supported Saddle workshop."""
    st.markdown(WORKSHOP_CSS, unsafe_allow_html=True)
    _init_defaults()

    gen = int(st.session_state.get("ws_bs_found_widget_generation", 0))

    project_name = st.session_state.get("project_info", {}).get("name", "") or "Untitled Project"
    client_name = st.session_state.get("project_info", {}).get("client", "") or "Unknown Client"

    render_breadcrumb("Saddle Span", "Beam Supported Saddle")
    render_project_header(project_name, client_name, "Beam Supported Saddle")

    # =========================================================================
    # SECTION 1 - GEOMETRY
    # =========================================================================
    with st.expander("1. Geometry", expanded=True):
        section_header(
            "Geometry",
            "Overall dimensions of the saddle span."
        )

        col1, col2 = st.columns(2)
        with col1:
            span = st.number_input(
                "Span Distance (m) *",
                min_value=4.0, max_value=200.0,
                value=float(st.session_state["ws_bs_span"]),
                step=0.5,
                key="ws_bs_span_input",
            )
            st.session_state["ws_bs_span"] = span
        with col2:
            apex = st.number_input(
                "Apex-to-Apex Distance (m) *",
                min_value=4.0, max_value=200.0,
                value=float(st.session_state["ws_bs_apex"]),
                step=0.5,
                key="ws_bs_apex_input",
            )
            st.session_state["ws_bs_apex"] = apex

        col3, col4 = st.columns(2)
        with col3:
            rise = st.number_input(
                "Rise (m) *",
                min_value=0.5, max_value=50.0,
                value=float(st.session_state["ws_bs_rise"]),
                step=0.1,
                key="ws_bs_rise_input",
            )
            st.session_state["ws_bs_rise"] = rise
        with col4:
            curve_options = ["parabolic", "circular", "catenary"]
            curve_labels = ["Parabolic", "Circular", "Catenary"]
            curve_idx = curve_options.index(st.session_state["ws_bs_curve_type"])
            curve_choice = st.selectbox(
                "Beam Curve Type",
                curve_labels,
                index=curve_idx,
                key="ws_bs_curve_select",
            )
            st.session_state["ws_bs_curve_type"] = curve_options[curve_labels.index(curve_choice)]

        warns = _validate_geometry(span, apex, rise)
        for w in warns:
            warning_box(w)

    # =========================================================================
    # SECTION 2 - MATERIALS
    # =========================================================================
    with st.expander("2. Materials", expanded=False):
        section_header(
            "Materials",
            "Steel grade, section family, and fabric."
        )

        col1, col2 = st.columns(2)
        with col1:
            steel_grades = ["S235", "S275", "S355", "S420", "S460"]
            steel_idx = steel_grades.index(st.session_state["ws_bs_steel_grade"])
            steel = st.selectbox(
                "Steel Grade",
                steel_grades,
                index=steel_idx,
                key="ws_bs_steel_select",
            )
            st.session_state["ws_bs_steel_grade"] = steel
        with col2:
            section_families = ["CHS", "SHS", "RHS", "I-Beam"]
            fam_idx = section_families.index(st.session_state["ws_bs_section_family"])
            family = st.selectbox(
                "Section Family",
                section_families,
                index=fam_idx,
                key="ws_bs_family_select",
            )
            st.session_state["ws_bs_section_family"] = family

        col3, col4 = st.columns(2)
        with col3:
            fabric_types = list(FABRIC_PROPERTIES.keys())
            ft_idx = fabric_types.index(st.session_state["ws_bs_fabric_type"]) if st.session_state["ws_bs_fabric_type"] in fabric_types else 0
            fabric_type = st.selectbox(
                "Fabric Type",
                fabric_types,
                index=ft_idx,
                key="ws_bs_fabric_type_select",
            )
            st.session_state["ws_bs_fabric_type"] = fabric_type
        with col4:
            grades = [k for k in FABRIC_PROPERTIES.get(fabric_type, {}).keys() if k != "default"]
            if not grades:
                grades = ["Type III"]
            grade_idx = grades.index(st.session_state["ws_bs_fabric_grade"]) if st.session_state["ws_bs_fabric_grade"] in grades else 0
            grade = st.selectbox(
                "Fabric Grade",
                grades,
                index=grade_idx,
                key="ws_bs_fabric_grade_select",
            )
            st.session_state["ws_bs_fabric_grade"] = grade










    # =========================================================================
    # SECTION 3 - BEAM CONSTRUCTION
    # =========================================================================
    with st.expander("3. Beam Construction", expanded=False):
        section_header(
            "Beam Construction",
            "Main curved beam. Solid section or truss."
        )

        member_options = ["single_beam", "planar_truss", "space_truss"]
        member_labels = ["Single Beam", "Planar Truss", "Space Truss"]
        m_idx = member_options.index(st.session_state["ws_bs_member_construction"])
        member = st.radio(
            "Beam Type",
            member_labels,
            index=m_idx,
            key="ws_bs_member_radio",
        )
        st.session_state["ws_bs_member_construction"] = member_options[member_labels.index(member)]

        preview_box("Engine will auto-select the optimal section size.")

    # =========================================================================
    # SECTION 4 - FRAME SUPPORTS
    # =========================================================================
    with st.expander("4. Frame Supports", expanded=False):
        section_header(
            "Frame Supports",
            "Support at each ground point."
        )

        col1, col2 = st.columns(2)
        with col1:
            support_options = ["pinned", "rigid"]
            support_labels = ["Pinned", "Rigid"]
            s_idx = support_options.index(st.session_state["ws_bs_support_type_start"])
            s_choice = st.radio(
                "Support at Start",
                support_labels,
                index=s_idx,
                key="ws_bs_support_start_radio",
            )
            st.session_state["ws_bs_support_type_start"] = support_options[support_labels.index(s_choice)]
        with col2:
            e_idx = support_options.index(st.session_state["ws_bs_support_type_end"])
            e_choice = st.radio(
                "Support at End",
                support_labels,
                index=e_idx,
                key="ws_bs_support_end_radio",
            )
            st.session_state["ws_bs_support_type_end"] = support_options[support_labels.index(e_choice)]

        if st.session_state["ws_bs_support_type_start"] == "rigid" or st.session_state["ws_bs_support_type_end"] == "rigid":
            warning_box("Rigid supports introduce moment into the frame.")

    # =========================================================================
    # SECTION 5 - SECONDARY BEAMS AND PRETENSION
    # =========================================================================
    with st.expander("5. Secondary Beams and Pretension", expanded=False):
        section_header(
            "Secondary Beams",
            "Steel members from main beam to frame."
        )

        span_val = float(st.session_state.get("ws_bs_span", 10.0))
        rise_val = float(st.session_state.get("ws_bs_rise", 6.2))
        arc = _arc_length_parabola(span_val, rise_val)
        recommended = _compute_secondary_count(arc)

        info_box(
            "<strong>System Recommendation</strong><br>"
            "15 m max unsupported section:<br>"
            "Recommended: <strong>" + str(recommended) + "</strong> per beam"
        )

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

        accept_default = st.radio(
            "Use system recommendation?",
            ["Yes - accept", "No - override"],
            index=0 if not st.session_state.get("ws_bs_secondary_count_override", False) else 1,
            key="ws_bs_secondary_accept_radio",
        )
        st.session_state["ws_bs_secondary_count_override"] = (accept_default == "No - override")

        if st.session_state["ws_bs_secondary_count_override"]:
            per_beam_options = [2, 3, 4, 5, 6, 8, 10, 12]
            per_beam_options = [n for n in per_beam_options if n >= recommended]
            if not per_beam_options:
                per_beam_options = [recommended]
            current_val = int(st.session_state.get("ws_bs_secondary_count", recommended))
            if current_val not in per_beam_options:
                current_val = per_beam_options[0]
            choice = st.selectbox(
                "Number of secondary beams per main beam",
                per_beam_options,
                index=per_beam_options.index(current_val),
                key="ws_bs_secondary_count_select",
            )
            st.session_state["ws_bs_secondary_count"] = choice
        else:
            st.session_state["ws_bs_secondary_count"] = recommended

        per_beam = int(st.session_state["ws_bs_secondary_count"])
        positions_list = _compute_secondary_positions(per_beam)
        positions_text = ", ".join(["%.3f" % f for f in positions_list])
        preview_box(
            'Secondary beams per main beam: <span class="num">' + str(per_beam) + '</span><br>'
            'Attach positions (arc-length fraction): <span class="num">' + positions_text + '</span>'
        )

        st.markdown(
            '<div class="ws-section-help" style="margin-top:1rem;">'
            '<strong>Toggle Angles</strong>'
            '</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            uplift = st.slider(
                "Uplift Angle (deg)",
                min_value=20, max_value=75,
                value=int(st.session_state["ws_bs_uplift_angle"]),
                step=1,
                key="ws_bs_uplift_angle_slider",
            )
            st.session_state["ws_bs_uplift_angle"] = uplift
        with col2:
            spread = st.slider(
                "Spread Angle (deg)",
                min_value=0, max_value=60,
                value=int(st.session_state["ws_bs_spread_angle"]),
                step=1,
                key="ws_bs_spread_angle_slider",
            )
            st.session_state["ws_bs_spread_angle"] = spread

        st.markdown(
            '<div style="color: #a8b8c8; font-size: 0.78rem; '
            'font-style: italic; margin-top: 0.3rem;">'
            'System recommendation. Adjust if needed.'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="ws-section-help" style="margin-top:1rem;">'
            '<strong>Secondary Beam Construction</strong>'
            '</div>',
            unsafe_allow_html=True,
        )

        sc_options = ["single_beam", "planar_truss", "space_truss"]
        sc_labels = ["Single Beam", "Planar Truss", "Space Truss"]
        sc_idx = sc_options.index(st.session_state["ws_bs_secondary_construction"])
        sc_choice = st.radio(
            "Construction Type",
            sc_labels,
            index=sc_idx,
            key="ws_bs_secondary_construction_radio",
        )
        st.session_state["ws_bs_secondary_construction"] = sc_options[sc_labels.index(sc_choice)]

        col3, col4 = st.columns(2)
        with col3:
            sc_families = ["CHS", "SHS", "RHS", "I-Beam"]
            sc_f_idx = sc_families.index(st.session_state["ws_bs_secondary_section_family"])
            sc_family = st.selectbox(
                "Section Family",
                sc_families,
                index=sc_f_idx,
                key="ws_bs_secondary_family_select",
            )
            st.session_state["ws_bs_secondary_section_family"] = sc_family
        with col4:
            base_options = ["pinned", "rigid"]
            base_labels = ["Pinned", "Rigid"]
            base_idx = base_options.index(st.session_state["ws_bs_secondary_base_connection"])
            base_choice = st.radio(
                "Base Connection",
                base_labels,
                index=base_idx,
                key="ws_bs_secondary_base_radio",
            )
            st.session_state["ws_bs_secondary_base_connection"] = base_options[base_labels.index(base_choice)]

        mem_pre = st.slider(
            "Membrane Pretension (kN/m)",
            min_value=0.5, max_value=8.0,
            value=float(st.session_state["ws_bs_membrane_pretension"]),
            step=0.1,
            key="ws_bs_mem_pre_slider",
        )
        st.session_state["ws_bs_membrane_pretension"] = mem_pre










    # =========================================================================
    # SECTION 6 - PURLINS
    # =========================================================================
    with st.expander("6. Purlins", expanded=False):
        section_header(
            "Purlins",
            "Spacing set by engine to prevent ponding."
        )

        span_val = float(st.session_state.get("ws_bs_span", 10.0))
        purlin_positions = _compute_purlin_positions(span_val)
        purlin_count = len(purlin_positions)

        info_box(
            "<strong>Auto-Arranged by Engine</strong><br>"
            "Purlins at 2.5 m intervals from centre."
        )

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

        positions_text = ", ".join(["%.1f" % p for p in purlin_positions])
        preview_box(
            'Total purlins: <span class="num">' + str(purlin_count) + '</span><br>'
            'Positions: <span class="num">' + positions_text + '</span>'
        )

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

        purlin_construction_options = ["single_beam", "planar_truss", "space_truss"]
        purlin_construction_labels = ["Single Beam", "Planar Truss", "Space Truss"]
        pc_idx = purlin_construction_options.index(st.session_state["ws_bs_purlin_construction"])
        purlin_construction = st.radio(
            "Purlin Construction Type",
            purlin_construction_labels,
            index=pc_idx,
            key="ws_bs_purlin_construction_radio",
        )
        st.session_state["ws_bs_purlin_construction"] = purlin_construction_options[purlin_construction_labels.index(purlin_construction)]

        purlin_families = ["CHS", "SHS", "RHS", "I-Beam"]
        pf_idx = purlin_families.index(st.session_state["ws_bs_purlin_section_family"])
        purlin_fam = st.selectbox(
            "Purlin Section Family",
            purlin_families,
            index=pf_idx,
            key="ws_bs_purlin_family_select",
        )
        st.session_state["ws_bs_purlin_section_family"] = purlin_fam

    # =========================================================================
    # SECTION 7 - BASEPLATE AND PRELIMINARY FOUNDATION
    # =========================================================================
    with st.expander("7. Baseplate and Preliminary Foundation", expanded=False):
        section_header(
            "Baseplate and Preliminary Foundation",
            "Sizing depends on soil at the site."
        )

        if st.button(
            "Default",
            key="ws_bs_found_default",
        ):
            st.session_state["ws_bs_soil_bearing"] = 150.0
            st.session_state["ws_bs_soil_type"] = "sand"
            st.session_state["ws_bs_water_table"] = 3.0
            st.session_state["ws_bs_foundation_type"] = "pad"
            st.session_state["ws_bs_found_widget_generation"] = gen + 1
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            bearing = st.number_input(
                "Soil Bearing Capacity (kN/m2)",
                min_value=50.0, max_value=1000.0,
                value=float(st.session_state["ws_bs_soil_bearing"]),
                step=10.0,
                key="ws_bs_soil_bearing_input_" + str(gen),
            )
            st.session_state["ws_bs_soil_bearing"] = bearing
        with col2:
            water = st.number_input(
                "Water Table Depth (m)",
                min_value=0.5, max_value=20.0,
                value=float(st.session_state["ws_bs_water_table"]),
                step=0.5,
                key="ws_bs_water_table_input_" + str(gen),
            )
            st.session_state["ws_bs_water_table"] = water

        soil_options = ["sand", "clay", "rock", "filled"]
        soil_labels = ["Sand", "Clay", "Rock", "Filled"]
        s_idx = soil_options.index(st.session_state["ws_bs_soil_type"])
        soil_choice = st.selectbox(
            "Soil Type",
            soil_labels,
            index=s_idx,
            key="ws_bs_soil_type_select_" + str(gen),
        )
        st.session_state["ws_bs_soil_type"] = soil_options[soil_labels.index(soil_choice)]

        found_options = ["pad", "pile", "raft"]
        found_labels = ["Pad Footing", "Pile Group", "Raft"]
        f_idx = found_options.index(st.session_state["ws_bs_foundation_type"])
        found_choice = st.selectbox(
            "Foundation Type",
            found_labels,
            index=f_idx,
            key="ws_bs_found_type_select_" + str(gen),
        )
        st.session_state["ws_bs_foundation_type"] = found_options[found_labels.index(found_choice)]

        warning_box("Preliminary sizing only. Geotechnical verification required.")

    # =========================================================================
    # SECTION 8 - LOADS AND STANDARD
    # =========================================================================
    with st.expander("8. Loads and Design Standard", expanded=False):
        section_header(
            "Loads and Design Standard",
            "User-added loads. Design code for safety factors."
        )

        payload = st.number_input(
            "Add. Pay Load (kg/m)",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state["ws_bs_add_payload"]),
            step=5.0,
            key="ws_bs_add_payload_input",
        )
        st.session_state["ws_bs_add_payload"] = payload

        std_options = ["EU", "MY", "UK", "CN", "US"]
        std_idx = std_options.index(st.session_state["ws_bs_design_standard"])
        std = st.selectbox(
            "Design Standard",
            std_options,
            index=std_idx,
            key="ws_bs_standard_select",
        )
        st.session_state["ws_bs_design_standard"] = std

        preview_box(
            'Wind speed basis: <span class="num">'
            + str(WIND_SPEEDS.get(std, 30.0))
            + ' m/s</span>'
        )

    # =========================================================================
    # SECTION 9 - MEMBRANE-TO-BEAM ATTACHMENT
    # =========================================================================
    with st.expander("9. Membrane-to-Beam Attachment", expanded=False):
        section_header(
            "Membrane-to-Beam Attachment",
            "How fabric edge attaches to the curved beams."
        )

        attach_options = ["kader", "segmented"]
        attach_labels = [
            "Kader Guider (continuous)",
            "Segmented Edge (discrete)",
        ]
        at_idx = attach_options.index(st.session_state["ws_bs_attachment_type"])
        at_choice = st.radio(
            "Attachment Method",
            attach_labels,
            index=at_idx,
            key="ws_bs_attachment_radio",
        )
        st.session_state["ws_bs_attachment_type"] = attach_options[attach_labels.index(at_choice)]

        if st.session_state["ws_bs_attachment_type"] == "kader":
            preview_box("Fabric edge held in a track along the beam.")
        else:
            info_box("Segment boundaries set by the form-finding engine.")

    # =========================================================================
    # ACTIONS
    # =========================================================================
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Back to Registration", key="ws_bs_back", use_container_width=True):
            st.session_state.page = "registration"
            st.rerun()
    with col_b:
        if st.button(
            "Intelligent Design Computing",
            key="ws_bs_run",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.page = "results"
            st.rerun()







