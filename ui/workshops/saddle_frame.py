# =============================================================================
# SDSe Fluid Design Studio - Beam Supported Saddle Workshop
# =============================================================================
# Input page for the Beam Supported Saddle variant.
#
# Per engine/SPEC_saddle_span.md, this variant is:
#   Saddle form with a rigid frame underneath.
#   Purlins connect the frame to the curved beam at intervals.
#   Secondary beams (steel members) replace tie-down cables.
#
# Members: membrane + main beam + purlins + secondary beams
#
# Secondary beam rule (code-compliant, silent):
#   Baseline: 2 secondary beams per main beam (at 0.175 and 0.825 arc length).
#   Maximum unsupported main beam section: 15 m
#   (per CECS158:2004 and general membrane practice).
#   Middle section (0.650 x arc_length) is divided into equal sub-sections
#   each <= 15 m. Total = 2 baseline + additional.
#   Result is mirrored to the other beam.
#
# Purlin rule (silent, engine applies):
#   One purlin at apex line. Additional every 2.5 m outward.
#   Stops when next purlin would be within 2.5 m of a support,
#   or less than 2.5 m from previous purlin.
#
# Design decisions (agreed 2026-09-15):
#   - 9 collapsible sections
#   - Shared CSS and helpers from ui/workshops/_shared.py
#   - Foundation section with small "Default" button above inputs
#   - Membrane pretension is TARGET STRESS STATE for form-finding
#   - Secondary beam count is system-recommended, user can override
#   - Secondary beams: single / planar truss / 3D truss
#   - Add. Pay Load for user-supplied equipment loads
#   - Back to Registration at bottom
#   - "Intelligent Design Computing" advances to Results
#
# Silent load rules (engine applies, Phase C):
#   Self weight       gamma_G = 1.2
#   Wind uplift       gamma_Q = -1.4
#   Wind downward     gamma_Q = +1.4
#   Add. Pay Load     gamma_Q = 1.5 (per country standard)
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
        # Section 1 - Geometry
        "ws_bs_span": 10.0,
        "ws_bs_apex": 15.0,
        "ws_bs_rise": 6.2,
        "ws_bs_curve_type": "parabolic",
        # Section 2 - Materials
        "ws_bs_steel_grade": "S355",
        "ws_bs_section_family": "CHS",
        "ws_bs_fabric_type": "PVDF",
        "ws_bs_fabric_grade": "Type III",
        # Section 3 - Members
        "ws_bs_member_construction": "single_beam",
        "ws_bs_section_preference": "auto",
        # Section 4 - Frame supports and struts
        "ws_bs_support_type_start": "pinned",
        "ws_bs_support_type_end": "pinned",
        # Section 5 - Secondary beams
        "ws_bs_secondary_count": 4,
        "ws_bs_secondary_count_override": False,
        "ws_bs_secondary_construction": "single_beam",
        "ws_bs_secondary_section_family": "CHS",
        "ws_bs_secondary_base_connection": "pinned",
        "ws_bs_uplift_angle": 45,
        "ws_bs_spread_angle": 30,
        "ws_bs_membrane_pretension": 2.0,
        # Section 6 - Purlins
        "ws_bs_purlin_construction": "single_beam",
        "ws_bs_purlin_section_family": "CHS",
        # Section 7 - Baseplate and Foundation
        "ws_bs_soil_bearing": 150.0,
        "ws_bs_soil_type": "sand",
        "ws_bs_water_table": 3.0,
        "ws_bs_foundation_type": "pad",
        "ws_bs_found_widget_generation": 0,
        # Section 8 - Loads
        "ws_bs_add_payload": 0.0,
        "ws_bs_design_standard": "MY",
        # Section 9 - Attachment
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


def _arc_length_parabola(span, rise):
    """
    Approximate arc length of a parabolic beam over the given span
    and rise. Used for secondary beam and purlin positioning.
    """
    if span <= 0:
        return 0.0
    ratio = rise / span if span > 0 else 0.0
    return span * (1.0 + (8.0 / 3.0) * ratio * ratio)


def _compute_secondary_count(arc_length):
    """
    Code-compliant secondary beam count.
    Baseline 2 per beam. Middle section (0.650 x arc) divided into
    equal sub-sections each <= 15 m. Total returned as even number.
    """
    MAX_UNSUPPORTED = 15.0
    middle = 0.650 * arc_length
    if middle <= MAX_UNSUPPORTED:
        base = 2
    else:
        n_subsections = int(math.ceil(middle / MAX_UNSUPPORTED))
        base = 1 + n_subsections
    if base % 2 != 0:
        base = base + 1
    return max(2, base)


def _compute_purlin_positions(span):
    """
    Silent rule: purlins every 2.5 m from centre, symmetric.
    Stops when next purlin would be within 2.5 m of the ground support,
    or less than 2.5 m from previous purlin.
    Returns list of offsets from centre.
    """
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
    render_project_header(project_name, client_name, "Beam Supported Saddle Span")

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
            "Steel grade for beams, purlins, and secondary beams. "
            "Fabric type and grade for the membrane."
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







