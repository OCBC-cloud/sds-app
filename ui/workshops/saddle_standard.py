# =============================================================================
# SDSe Fluid Design Studio - Standard Saddle Workshop
# =============================================================================
# Input page for the Standard Saddle variant of the Saddle Span family.
#
# Per engine/SPEC_saddle_span.md, this variant is:
#   Two curved edge beams converging to two ground support points.
#   Membrane stretched between. Classic hypar form.
#
# Design decisions (agreed 2026-09-14):
#   - 8 collapsible sections
#   - Shared CSS and helpers from ui/workshops/_shared.py
#   - Cable diameter is always automatic
#   - Foundation section with a small "Default" button above the inputs
#   - Pretension inputs define TARGET STRESS STATE for form-finding
#   - Tie-down cables: radio (4 cables / 8 cables)
#   - "Add. Pay Load" for user-supplied equipment loads
#   - Back to Registration at bottom
#   - "Intelligent Design Computing" advances to Results
#
# Tie-down positions (arc-length fraction per beam, from nearest support):
#   4 cables total -> 0.175, 0.825
#   8 cables total -> 0.175, 0.225, 0.775, 0.825
#
# Silent load rules (engine applies, Phase C):
#   Self weight       gamma_G = 1.2
#   Wind uplift       gamma_Q = -1.4
#   Wind downward     gamma_Q = +1.4
#   Add. Pay Load     gamma_Q = 1.5 (per country standard)
#
# Widget reset technique (2026-09-14):
#   Streamlit caches widget values under the widget key and refuses
#   to let us reset a widget in place. The workaround is to change
#   the widget KEY each time we want a fresh render. A counter in
#   session state drives this. The user sees only the values change.
#
# Updated 2026-09-19 (evening):
#   - _init_defaults() writes two viewer strings used by the Results
#     page under the 3D chart.
#   - The dimensions string is rebuilt live each render.
# =============================================================================

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
        # Section 1 - Geometry
        "ws_ss_span": 10.0,
        "ws_ss_apex": 15.0,
        "ws_ss_rise": 6.2,
        "ws_ss_curve_type": "parabolic",
        # Section 2 - Materials
        "ws_ss_steel_grade": "S355",
        "ws_ss_section_family": "CHS",
        "ws_ss_fabric_type": "PVDF",
        "ws_ss_fabric_grade": "Type III",
        # Section 3 - Members
        "ws_ss_member_construction": "single_beam",
        "ws_ss_section_preference": "auto",
        # Section 4 - Supports
        "ws_ss_support_type_start": "pinned",
        "ws_ss_support_type_end": "pinned",
        # Section 5 - Tie-down cables + pretension
        "ws_ss_tiedown_intervals": 4,
        "ws_ss_uplift_angle": 45,
        "ws_ss_spread_angle": 30,
        "ws_ss_cable_type": "6x19",
        "ws_ss_cable_material": "galvanised",
        "ws_ss_anchor_type": "pinned",
        "ws_ss_membrane_pretension": 2.0,
        "ws_ss_cable_pretension": 5.0,
        # Section 6 - Baseplate and Foundation
        "ws_ss_soil_bearing": 150.0,
        "ws_ss_soil_type": "sand",
        "ws_ss_water_table": 3.0,
        "ws_ss_foundation_type": "pad",
        # Widget key generation counter (bumped by the Default button)
        "ws_ss_found_widget_generation": 0,
        # Section 7 - Loads
        "ws_ss_add_payload": 0.0,
        "ws_ss_design_standard": "MY",
        # Section 8 - Attachment
        "ws_ss_attachment_type": "kader",
        # ---- Viewer strings for the Results page (below the 3D chart)
        "ws_ss_viewer_description": "Standard Saddle Span tensile membrane structure",
        "ws_ss_viewer_dimensions": "",
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
        warnings.append("Apex-to-Apex distance must be greater than 0.")
    if rise <= 0:
        warnings.append("Rise must be greater than 0.")
    if span > 0 and rise > 0:
        ratio = rise / span
        if ratio < 0.05:
            warnings.append("Rise / Span ratio is very low. Membrane may not drain.")
        elif ratio > 0.5:
            warnings.append("Rise / Span ratio is very high. Check anchor capacity.")
    return warnings


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_saddle_standard():
    """Render the Standard Saddle workshop."""
    st.markdown(WORKSHOP_CSS, unsafe_allow_html=True)
    _init_defaults()

    # Generation counter drives widget keys in Section 6.
    gen = int(st.session_state.get("ws_ss_found_widget_generation", 0))

    project_name = st.session_state.get("project_info", {}).get("name", "") or "Untitled Project"
    client_name = st.session_state.get("project_info", {}).get("client", "") or "Unknown Client"

    render_breadcrumb("Saddle Span", "Standard Saddle")
    render_project_header(project_name, client_name, "Standard Saddle Span")

    # =========================================================================
    # SECTION 1 - GEOMETRY
    # =========================================================================
    with st.expander("1. Geometry", expanded=True):
        section_header(
            "Geometry",
            "Overall dimensions of the saddle span. Span is the long dimension. "
            "Apex-to-Apex is the width. Rise is the vertical height of the beam apex."
        )

        col1, col2 = st.columns(2)
        with col1:
            span = st.number_input(
                "Span Distance (m) *",
                min_value=4.0, max_value=200.0,
                value=float(st.session_state["ws_ss_span"]),
                step=0.5,
                key="ws_ss_span_input",
            )
            st.session_state["ws_ss_span"] = span
        with col2:
            apex = st.number_input(
                "Apex-to-Apex Distance (m) *",
                min_value=4.0, max_value=200.0,
                value=float(st.session_state["ws_ss_apex"]),
                step=0.5,
                key="ws_ss_apex_input",
            )
            st.session_state["ws_ss_apex"] = apex

        col3, col4 = st.columns(2)
        with col3:
            rise = st.number_input(
                "Rise (m) *",
                min_value=0.5, max_value=50.0,
                value=float(st.session_state["ws_ss_rise"]),
                step=0.1,
                key="ws_ss_rise_input",
            )
            st.session_state["ws_ss_rise"] = rise
        with col4:
            curve_options = ["parabolic", "circular", "catenary"]
            curve_labels = ["Parabolic", "Circular", "Catenary"]
            curve_idx = curve_options.index(st.session_state["ws_ss_curve_type"])
            curve_choice = st.selectbox(
                "Beam Curve Type",
                curve_labels,
                index=curve_idx,
                key="ws_ss_curve_select",
            )
            st.session_state["ws_ss_curve_type"] = curve_options[curve_labels.index(curve_choice)]

        warns = _validate_geometry(span, apex, rise)
        for w in warns:
            warning_box(w)

    # =========================================================================
    # SECTION 2 - MATERIALS
    # =========================================================================
    with st.expander("2. Materials", expanded=False):
        section_header(
            "Materials",
            "Steel grade for beams and cables. Fabric type and grade for the membrane."
        )

        col1, col2 = st.columns(2)
        with col1:
            steel_grades = ["S235", "S275", "S355", "S420", "S460"]
            steel_idx = steel_grades.index(st.session_state["ws_ss_steel_grade"])
            steel = st.selectbox(
                "Steel Grade",
                steel_grades,
                index=steel_idx,
                key="ws_ss_steel_select",
            )
            st.session_state["ws_ss_steel_grade"] = steel
        with col2:
            section_families = ["CHS", "SHS", "RHS", "I-Beam"]
            fam_idx = section_families.index(st.session_state["ws_ss_section_family"])
            family = st.selectbox(
                "Section Family",
                section_families,
                index=fam_idx,
                key="ws_ss_family_select",
            )
            st.session_state["ws_ss_section_family"] = family

        col3, col4 = st.columns(2)
        with col3:
            fabric_types = list(FABRIC_PROPERTIES.keys())
            ft_idx = fabric_types.index(st.session_state["ws_ss_fabric_type"]) if st.session_state["ws_ss_fabric_type"] in fabric_types else 0
            fabric_type = st.selectbox(
                "Fabric Type",
                fabric_types,
                index=ft_idx,
                key="ws_ss_fabric_type_select",
            )
            st.session_state["ws_ss_fabric_type"] = fabric_type
        with col4:
            grades = [k for k in FABRIC_PROPERTIES.get(fabric_type, {}).keys() if k != "default"]
            if not grades:
                grades = ["Type III"]
            grade_idx = grades.index(st.session_state["ws_ss_fabric_grade"]) if st.session_state["ws_ss_fabric_grade"] in grades else 0
            grade = st.selectbox(
                "Fabric Grade",
                grades,
                index=grade_idx,
                key="ws_ss_fabric_grade_select",
            )
            st.session_state["ws_ss_fabric_grade"] = grade

    # =========================================================================
    # SECTION 3 - MEMBERS
    # =========================================================================
    with st.expander("3. Member Construction", expanded=False):
        section_header(
            "Member Construction",
            "Single beam is a solid CHS. Planar truss and space truss are triangulated assemblies."
        )

        member_options = ["single_beam", "planar_truss", "space_truss"]
        member_labels = ["Single Beam", "Planar Truss", "Space Truss"]
        m_idx = member_options.index(st.session_state["ws_ss_member_construction"])
        member = st.radio(
            "Construction Type",
            member_labels,
            index=m_idx,
            key="ws_ss_member_radio",
        )
        st.session_state["ws_ss_member_construction"] = member_options[member_labels.index(member)]

        if st.session_state["ws_ss_member_construction"] == "single_beam":
            preview_box(
                "Member will be a single CHS, SHS, RHS, or I-Beam section. "
                "Engine will auto-select the optimal size."
            )
        else:
            preview_box(
                "Member will be a triangulated truss. "
                "Engine will auto-select a unified section for chords and webs."
            )

    # =========================================================================
    # SECTION 4 - GROUND SUPPORTS
    # =========================================================================
    with st.expander("4. Ground Supports", expanded=False):
        section_header(
            "Ground Supports",
            "Support condition at each of the two ground points where the beams converge."
        )

        col1, col2 = st.columns(2)
        with col1:
            support_options = ["pinned", "rigid"]
            support_labels = ["Pinned", "Rigid"]
            s_idx = support_options.index(st.session_state["ws_ss_support_type_start"])
            s_choice = st.radio(
                "Support at Start End",
                support_labels,
                index=s_idx,
                key="ws_ss_support_start_radio",
            )
            st.session_state["ws_ss_support_type_start"] = support_options[support_labels.index(s_choice)]
        with col2:
            e_idx = support_options.index(st.session_state["ws_ss_support_type_end"])
            e_choice = st.radio(
                "Support at Far End",
                support_labels,
                index=e_idx,
                key="ws_ss_support_end_radio",
            )
            st.session_state["ws_ss_support_type_end"] = support_options[support_labels.index(e_choice)]

        if st.session_state["ws_ss_support_type_start"] == "rigid" or st.session_state["ws_ss_support_type_end"] == "rigid":
            warning_box(
                "Rigid supports introduce moment into the beams. "
                "The engine will apply the appropriate interaction check."
            )

    # =========================================================================
    # SECTION 5 - TIE-DOWN CABLES AND PRETENSION
    # =========================================================================
    with st.expander("5. Tie-down Cables and Pretension", expanded=False):
        section_header(
            "Tie-down Cables and Pretension",
            "Structural cables from each beam down to ground anchors. "
            "They resist wind uplift and stabilise the structure."
        )

        td_options = [4, 8]
        td_labels = ["4 cables", "8 cables"]
        current_td = int(st.session_state.get("ws_ss_tiedown_intervals", 4))
        td_idx = td_options.index(current_td) if current_td in td_options else 0
        td_choice = st.radio(
            "Number of Tie-down Cables *",
            td_labels,
            index=td_idx,
            key="ws_ss_tiedown_radio",
            help="Total tie-down cables for the structure. 4 = 2 per side, 8 = 4 per side.",
        )
        st.session_state["ws_ss_tiedown_intervals"] = td_options[td_labels.index(td_choice)]

        col1, col2 = st.columns(2)
        with col1:
            uplift = st.slider(
                "Anchor Uplift Angle (deg)",
                min_value=20, max_value=75,
                value=int(st.session_state["ws_ss_uplift_angle"]),
                step=1,
                key="ws_ss_uplift_angle_slider",
                help="Vertical angle of the cable from beam to ground anchor.",
            )
            st.session_state["ws_ss_uplift_angle"] = uplift
        with col2:
            spread = st.slider(
                "Anchor Spread Angle (deg)",
                min_value=0, max_value=60,
                value=int(st.session_state["ws_ss_spread_angle"]),
                step=1,
                key="ws_ss_spread_angle_slider",
                help="Horizontal spread of the anchor from the beam.",
            )
            st.session_state["ws_ss_spread_angle"] = spread

        col3, col4 = st.columns(2)
        with col3:
            cable_types = ["6x19", "Locked Coil", "Spiral"]
            ct_idx = cable_types.index(st.session_state["ws_ss_cable_type"])
            cable_type = st.selectbox(
                "Cable Type",
                cable_types,
                index=ct_idx,
                key="ws_ss_cable_type_select",
            )
            st.session_state["ws_ss_cable_type"] = cable_type
        with col4:
            cable_mats = ["galvanised", "stainless"]
            cm_labels = ["Galvanised", "Stainless"]
            cm_idx = cable_mats.index(st.session_state["ws_ss_cable_material"])
            cm_choice = st.selectbox(
                "Cable Material",
                cm_labels,
                index=cm_idx,
                key="ws_ss_cable_material_select",
            )
            st.session_state["ws_ss_cable_material"] = cable_mats[cm_labels.index(cm_choice)]

        anchor_options = ["pinned", "rigid"]
        anchor_labels = ["Pinned", "Rigid"]
        a_idx = anchor_options.index(st.session_state["ws_ss_anchor_type"])
        anchor_choice = st.radio(
            "Ground Anchor Type",
            anchor_labels,
            index=a_idx,
            key="ws_ss_anchor_radio",
        )
        st.session_state["ws_ss_anchor_type"] = anchor_options[anchor_labels.index(anchor_choice)]

        st.markdown(
            '<div class="ws-section-help" style="margin-top:1rem;">'
            '<strong>Pretension (Target Stress State)</strong> - '
            'These values define the target stress state for the form-finding '
            'engine. The engine will solve for the geometry that is in '
            'equilibrium with these target values.'
            '</div>',
            unsafe_allow_html=True,
        )

        col5, col6 = st.columns(2)
        with col5:
            mem_pre = st.slider(
                "Membrane Pretension (kN/m)",
                min_value=0.5, max_value=8.0,
                value=float(st.session_state["ws_ss_membrane_pretension"]),
                step=0.1,
                key="ws_ss_mem_pre_slider",
                help="Target membrane stress. Typical range: 1.0 to 4.0 kN/m.",
            )
            st.session_state["ws_ss_membrane_pretension"] = mem_pre
        with col6:
            cab_pre = st.slider(
                "Cable Pretension (kN)",
                min_value=0.5, max_value=50.0,
                value=float(st.session_state["ws_ss_cable_pretension"]),
                step=0.5,
                key="ws_ss_cab_pre_slider",
                help="Target cable tension. Typical range: 5 to 20 kN for 6x19 galvanised.",
            )
            st.session_state["ws_ss_cable_pretension"] = cab_pre

        preview_box(
            "Cable diameter is selected automatically by the engine "
            "based on the computed tension under the target stress state."
        )

    # =========================================================================
    # SECTION 6 - BASEPLATE AND PRELIMINARY FOUNDATION
    # =========================================================================
    with st.expander("6. Baseplate and Preliminary Foundation", expanded=False):
        section_header(
            "Baseplate and Preliminary Foundation",
            "The beam-to-ground supports transfer load to the ground. "
            "Preliminary foundation sizing depends on the soil at the site."
        )

        info_box(
            "<strong>Support Base and Anchors</strong><br>"
            "Support baseplate dimensions and anchor bolt size and count are "
            "auto-selected by the engine based on the support reaction "
            "(axial + shear + moment). No input required."
        )

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

        if st.button(
            "Default",
            key="ws_ss_found_default",
        ):
            st.session_state["ws_ss_soil_bearing"] = 150.0
            st.session_state["ws_ss_soil_type"] = "sand"
            st.session_state["ws_ss_water_table"] = 3.0
            st.session_state["ws_ss_foundation_type"] = "pad"
            st.session_state["ws_ss_found_widget_generation"] = gen + 1
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            bearing = st.number_input(
                "Assumed Soil Bearing Capacity (kN/m2)",
                min_value=50.0, max_value=1000.0,
                value=float(st.session_state["ws_ss_soil_bearing"]),
                step=10.0,
                key="ws_ss_soil_bearing_input_" + str(gen),
                help="From geotechnical investigation. Typical: sand 150, clay 100, rock 500.",
            )
            st.session_state["ws_ss_soil_bearing"] = bearing
        with col2:
            water = st.number_input(
                "Water Table Depth (m)",
                min_value=0.5, max_value=20.0,
                value=float(st.session_state["ws_ss_water_table"]),
                step=0.5,
                key="ws_ss_water_table_input_" + str(gen),
            )
            st.session_state["ws_ss_water_table"] = water

        soil_options = ["sand", "clay", "rock", "filled"]
        soil_labels = ["Sand", "Clay", "Rock", "Filled / Made Ground"]
        s_idx = soil_options.index(st.session_state["ws_ss_soil_type"])
        soil_choice = st.selectbox(
            "Soil Type",
            soil_labels,
            index=s_idx,
            key="ws_ss_soil_type_select_" + str(gen),
        )
        st.session_state["ws_ss_soil_type"] = soil_options[soil_labels.index(soil_choice)]

        found_options = ["pad", "pile", "raft"]
        found_labels = ["Pad Footing", "Pile Group", "Raft"]
        f_idx = found_options.index(st.session_state["ws_ss_foundation_type"])
        found_choice = st.selectbox(
            "Foundation Type",
            found_labels,
            index=f_idx,
            key="ws_ss_found_type_select_" + str(gen),
        )
        st.session_state["ws_ss_foundation_type"] = found_options[found_labels.index(found_choice)]

        warning_box(
            "<strong>Note:</strong> Preliminary foundation sizing only. "
            "Geotechnical verification required. Footing reinforcement and "
            "detailing are not provided by this app. Engage a geotechnical "
            "engineer to confirm."
        )

    # =========================================================================
    # SECTION 7 - LOADS AND STANDARD
    # =========================================================================
    with st.expander("7. Loads and Design Standard", expanded=False):
        section_header(
            "Loads and Design Standard",
            "User-added loads on the beam. Design code for safety factors."
        )

        payload = st.number_input(
            "Add. Pay Load (kg/m)",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state["ws_ss_add_payload"]),
            step=5.0,
            key="ws_ss_add_payload_input",
            help="Additional user load from equipment, stage rigging, sound, or lighting systems.",
        )
        st.session_state["ws_ss_add_payload"] = payload

        std_options = ["EU", "MY", "UK", "CN", "US"]
        std_idx = std_options.index(st.session_state["ws_ss_design_standard"])
        std = st.selectbox(
            "Design Standard",
            std_options,
            index=std_idx,
            key="ws_ss_standard_select",
        )
        st.session_state["ws_ss_design_standard"] = std

        preview_box(
            'Wind speed basis: <span class="num">'
            + str(WIND_SPEEDS.get(std, 30.0))
            + ' m/s</span>'
        )

    # =========================================================================
    # SECTION 8 - MEMBRANE-TO-BEAM ATTACHMENT
    # =========================================================================
    with st.expander("8. Membrane-to-Beam Attachment", expanded=False):
        section_header(
            "Membrane-to-Beam Attachment",
            "How the fabric edge is attached to the curved beams."
        )

        attach_options = ["kader", "segmented"]
        attach_labels = [
            "Kader Guider (continuous attachment)",
            "Segmented Edge (discrete attachment)",
        ]
        at_idx = attach_options.index(st.session_state["ws_ss_attachment_type"])
        at_choice = st.radio(
            "Attachment Method",
            attach_labels,
            index=at_idx,
            key="ws_ss_attachment_radio",
        )
        st.session_state["ws_ss_attachment_type"] = attach_options[attach_labels.index(at_choice)]

        if st.session_state["ws_ss_attachment_type"] == "kader":
            preview_box(
                "The fabric edge is continuously held in a track (keder) along the beam. "
                "Tension is distributed evenly along the beam length. "
                "No further inputs required."
            )
        else:
            info_box(
                "<strong>Segmented Edge Attachment</strong><br>"
                "Segment boundaries and edge cable geometry are determined by "
                "the form-finding engine, following the membrane natural edge. "
                "This matches industry practice (Easy, RFEM, RhinoMembrane). "
                "No fixed spacing input required."
            )

    # =========================================================================
    # VIEWER STRINGS (rebuilt live, read by the Results page)
    # =========================================================================
    # Total height = rise (apex of the beam above the ground supports).

    _total_h = float(st.session_state.get("ws_ss_rise", 6.2))

    st.session_state["ws_ss_viewer_description"] = (
        "Standard Saddle Span tensile membrane structure"
    )
    st.session_state["ws_ss_viewer_dimensions"] = (
        "Total height " + ("%.2f" % _total_h) + " m"
    )

    # =========================================================================
    # ACTIONS
    # =========================================================================
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Back to Registration", key="ws_ss_back", use_container_width=True):
            st.session_state.page = "registration"
            st.rerun()
    with col_b:
        if st.button(
            "Intelligent Design Computing",
            key="ws_ss_run",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.page = "results"
            st.rerun()
