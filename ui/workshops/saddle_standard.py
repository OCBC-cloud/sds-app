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
#   - Collapsible sections (8 sections)
#   - Mixed widgets: numbers, sliders, selectboxes, radios
#   - Custom-styled section headers (accent orange)
#   - Cable diameter is always automatic
#   - Foundation section standardised to match Cantilever Leaf
#   - Pretension inputs define TARGET STRESS STATE for form-finding
#   - No fixed segment spacing on edge cables - engine places them
#     where the membrane geometry demands (industry practice)
#   - Back to Registration at bottom
#   - "Intelligent Design Computing" advances to Results
#
# Form-finding note (per industry practice - Easy, RFEM, RhinoMembrane):
#   Geometry is NOT drawn by the user. It emerges from equilibrium.
#   The user sets target membrane stress and target cable tension.
#   The solver (Phase C engine) finds the shape that satisfies both.
# =============================================================================

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
    """Initialise workshop state on first entry."""
    defaults = {
        # Section 1 - Geometry
        "ws_ss_span": 20.0,
        "ws_ss_apex": 12.0,
        "ws_ss_rise": 2.5,
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
        "ws_ss_tiedown_intervals": 3,
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
        # Section 7 - Loads
        "ws_ss_live_load": 0.5,
        "ws_ss_design_standard": "MY",
        # Section 8 - Attachment
        "ws_ss_attachment_type": "kader",
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


def _section_header(title, help_text=""):
    """Render a section header with custom styling."""
    html = '<div class="ws-section-title">' + title + '</div>'
    if help_text:
        html += '<div class="ws-section-help">' + help_text + '</div>'
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_saddle_standard():
    """Render the Standard Saddle workshop."""
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
        '<span class="crumb">Standard Saddle</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Project header
    st.markdown(
        '<div class="ws-section">'
        '<div class="ws-section-title">' + project_name + '</div>'
        '<div class="ws-section-help">'
        'Client: ' + client_name + '  |  Structure: Standard Saddle Span'
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
            "Overall dimensions of the saddle span. "
            "Span is the long dimension. Apex-to-Apex is the width. Rise is the vertical height of the beam apex."
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
        _section_header(
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
            st.markdown(
                '<div class="ws-preview-box">'
                'Member will be a single CHS, SHS, RHS, or I-Beam section. '
                'Engine will auto-select the optimal size.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="ws-preview-box">'
                'Member will be a triangulated truss. '
                'Engine will auto-select a unified section for chords and webs.'
                '</div>',
                unsafe_allow_html=True,
            )

    # =========================================================================
    # SECTION 4 - GROUND SUPPORTS
    # =========================================================================
    with st.expander("4. Ground Supports", expanded=False):
        _section_header(
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
            st.markdown(
                '<div class="ws-warning-box">'
                'Rigid supports introduce moment into the beams. '
                'The engine will apply the appropriate interaction check.'
                '</div>',
                unsafe_allow_html=True,
            )

    # =========================================================================
    # SECTION 5 - TIE-DOWN CABLES AND PRETENSION
    # =========================================================================
    with st.expander("5. Tie-down Cables and Pretension", expanded=False):
        _section_header(
            "Tie-down Cables and Pretension",
            "Structural cables from each beam down to ground anchors. "
            "They resist wind uplift and stabilise the structure."
        )

        intervals = st.number_input(
            "Number of Tie-down Intervals *",
            min_value=1, max_value=20,
            value=int(st.session_state["ws_ss_tiedown_intervals"]),
            step=1,
            key="ws_ss_tiedown_intervals_input",
            help="How many tie-down points along each beam. One anchor per tie-down.",
        )
        st.session_state["ws_ss_tiedown_intervals"] = intervals

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

        # ---- Pretension
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

        st.markdown(
            '<div class="ws-preview-box">'
            'Cable diameter is selected automatically by the engine '
            'based on the computed tension under the target stress state.'
            '</div>',
            unsafe_allow_html=True,
        )

    # =========================================================================
    # SECTION 6 - BASEPLATE AND PRELIMINARY FOUNDATION
    # =========================================================================
    with st.expander("6. Baseplate and Preliminary Foundation", expanded=False):
        _section_header(
            "Baseplate and Preliminary Foundation",
            "The beam-to-ground supports transfer load to the ground. "
            "Preliminary foundation sizing depends on the soil at the site."
        )

        st.markdown(
            '<div class="ws-info-box">'
            '<strong>Support Base and Anchors</strong><br>'
            'Support baseplate dimensions and anchor bolt size and count are '
            'auto-selected by the engine based on the support reaction '
            '(axial + shear + moment). No input required.'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            bearing = st.number_input(
                "Assumed Soil Bearing Capacity (kN/m2)",
                min_value=50.0, max_value=1000.0,
                value=float(st.session_state["ws_ss_soil_bearing"]),
                step=10.0,
                key="ws_ss_soil_bearing_input",
                help="From geotechnical investigation. Typical: sand 150, clay 100, rock 500.",
            )
            st.session_state["ws_ss_soil_bearing"] = bearing
        with col2:
            water = st.number_input(
                "Water Table Depth (m)",
                min_value=0.5, max_value=20.0,
                value=float(st.session_state["ws_ss_water_table"]),
                step=0.5,
                key="ws_ss_water_table_input",
            )
            st.session_state["ws_ss_water_table"] = water

        soil_options = ["sand", "clay", "rock", "filled"]
        soil_labels = ["Sand", "Clay", "Rock", "Filled / Made Ground"]
        s_idx = soil_options.index(st.session_state["ws_ss_soil_type"])
        soil_choice = st.selectbox(
            "Soil Type",
            soil_labels,
            index=s_idx,
            key="ws_ss_soil_type_select",
        )
        st.session_state["ws_ss_soil_type"] = soil_options[soil_labels.index(soil_choice)]

        found_options = ["pad", "pile", "raft"]
        found_labels = ["Pad Footing", "Pile Group", "Raft"]
        f_idx = found_options.index(st.session_state["ws_ss_foundation_type"])
        found_choice = st.selectbox(
            "Foundation Type",
            found_labels,
            index=f_idx,
            key="ws_ss_found_type_select",
        )
        st.session_state["ws_ss_foundation_type"] = found_options[found_labels.index(found_choice)]

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
            "Live load on the beam. Design code for safety factors."
        )

        live = st.number_input(
            "Live Load on Beam (kg/m)",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state["ws_ss_live_load"]),
            step=5.0,
            key="ws_ss_live_load_input",
        )
        st.session_state["ws_ss_live_load"] = live

        std_options = ["EU", "MY", "UK", "CN", "US"]
        std_idx = std_options.index(st.session_state["ws_ss_design_standard"])
        std = st.selectbox(
            "Design Standard",
            std_options,
            index=std_idx,
            key="ws_ss_standard_select",
        )
        st.session_state["ws_ss_design_standard"] = std

        st.markdown(
            '<div class="ws-preview-box">'
            'Wind speed basis: <span class="num">'
            + str(WIND_SPEEDS.get(std, 30.0))
            + ' m/s</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    # =========================================================================
    # SECTION 8 - MEMBRANE-TO-BEAM ATTACHMENT
    # =========================================================================
    with st.expander("8. Membrane-to-Beam Attachment", expanded=False):
        _section_header(
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
            st.markdown(
                '<div class="ws-preview-box">'
                'The fabric edge is continuously held in a track (keder) along the beam. '
                'Tension is distributed evenly along the beam length. '
                'No further inputs required.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="ws-info-box">'
                '<strong>Segmented Edge Attachment</strong><br>'
                'Segment boundaries and edge cable geometry are determined by '
                'the form-finding engine, following the membrane natural edge. '
                'This matches industry practice (Easy, RFEM, RhinoMembrane). '
                'No fixed spacing input required.'
                '</div>',
                unsafe_allow_html=True,
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
