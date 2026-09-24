# =============================================================================
# SDSe Fluid Design Studio - Standard Saddle Workshop
# =============================================================================
# Input page for the Standard Saddle variant of the Saddle Span family.
#
# Updated 2026-09-24:
#   - Section 5 pretension inputs replaced. The workshop now collects
#     three separate pretensions: WARP (along the span), WEFT (across
#     the membrane), and EDGE CABLE (along the free ends).
#     Convention: warp runs along the beam (i-direction); weft runs
#     between the two beams (j-direction). This is fixed and is
#     stated in the help text.
#   - Section 8: the "Edge cables on the free ends" toggle has been
#     REMOVED. The free-end cable is a mandatory part of the Cable
#     Supported Saddle geometry. It is not a user option. Its
#     pretension is set in Section 5.
# Updated 2026-09-22:
#   - Section 8 shows "Cable Attachment Points per Beam" when
#     Segmented is selected.
# Updated 2026-09-20:
#   - Viewer-strings block reads widget keys FIRST.
# Updated 2026-09-19:
#   - _init_defaults() writes two viewer strings.
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


def _init_defaults():
    defaults = {
        "ws_ss_span": 10.0,
        "ws_ss_apex": 15.0,
        "ws_ss_rise": 6.2,
        "ws_ss_curve_type": "parabolic",
        "ws_ss_steel_grade": "S355",
        "ws_ss_section_family": "CHS",
        "ws_ss_fabric_type": "PVDF",
        "ws_ss_fabric_grade": "Type III",
        "ws_ss_member_construction": "single_beam",
        "ws_ss_section_preference": "auto",
        "ws_ss_support_type_start": "pinned",
        "ws_ss_support_type_end": "pinned",
        "ws_ss_tiedown_intervals": 4,
        "ws_ss_uplift_angle": 45,
        "ws_ss_spread_angle": 30,
        "ws_ss_cable_type": "6x19",
        "ws_ss_cable_material": "galvanised",
        "ws_ss_anchor_type": "pinned",
        "ws_ss_warp_pretension": 2.0,
        "ws_ss_weft_pretension": 2.0,
        "ws_ss_edge_cable_pretension": 5.0,
        "ws_ss_soil_bearing": 150.0,
        "ws_ss_soil_type": "sand",
        "ws_ss_water_table": 3.0,
        "ws_ss_foundation_type": "pad",
        "ws_ss_found_widget_generation": 0,
        "ws_ss_add_payload": 0.0,
        "ws_ss_design_standard": "MY",
        "ws_ss_attachment_type": "kader",
        "ws_ss_cable_attachment_count": 6,
        "ws_ss_viewer_description": "Standard Saddle Span tensile membrane structure",
        "ws_ss_viewer_dimensions": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _validate_geometry(span, apex, rise):
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


def render_saddle_standard():
    """Render the Standard Saddle workshop."""
    st.markdown(WORKSHOP_CSS, unsafe_allow_html=True)
    _init_defaults()

    gen = int(st.session_state.get("ws_ss_found_widget_generation", 0))

    project_name = st.session_state.get("project_info", {}).get("name", "") or "Untitled Project"
    client_name = st.session_state.get("project_info", {}).get("client", "") or "Unknown Client"

    render_breadcrumb("Saddle Span", "Standard Saddle")
    render_project_header(project_name, client_name, "Standard Saddle Span")

    # SECTION 1 - GEOMETRY
    with st.expander("1. Geometry", expanded=True):
        section_header("Geometry", "Overall dimensions of the saddle span.")

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

    # SECTION 2 - MATERIALS
    with st.expander("2. Materials", expanded=False):
        section_header("Materials", "Steel grade, section family, and fabric.")

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

    # SECTION 3 - MEMBERS
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

    # SECTION 4 - GROUND SUPPORTS
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

    # SECTION 5 - TIE-DOWN CABLES AND PRETENSION
    with st.expander("5. Tie-down Cables and Pretension", expanded=False):
        section_header(
            "Tie-down Cables and Pretension",
            "Structural cables from each beam down to ground anchors, "
            "and the target pretension for the membrane and cables."
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
            )
            st.session_state["ws_ss_uplift_angle"] = uplift
        with col2:
            spread = st.slider(
                "Anchor Spread Angle (deg)",
                min_value=0, max_value=60,
                value=int(st.session_state["ws_ss_spread_angle"]),
                step=1,
                key="ws_ss_spread_angle_slider",
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
            '<strong>Pretension (Target Stress State)</strong><br>'
            'Warp runs along the span (the long direction, following the '
            'beams). Weft runs across the membrane (between the two beams). '
            'The edge cable runs along the two free ends. These values drive '
            'the form-finding engine. The shape is a consequence of the '
            'target stress state, not a control.'
            '</div>',
            unsafe_allow_html=True,
        )

        col5, col6 = st.columns(2)
        with col5:
            warp_pre = st.slider(
                "Warp Pretension (kN/m)",
                min_value=0.5, max_value=8.0,
                value=float(st.session_state["ws_ss_warp_pretension"]),
                step=0.1,
                key="ws_ss_warp_pre_slider",
            )
            st.session_state["ws_ss_warp_pretension"] = warp_pre
        with col6:
            weft_pre = st.slider(
                "Weft Pretension (kN/m)",
                min_value=0.5, max_value=8.0,
                value=float(st.session_state["ws_ss_weft_pretension"]),
                step=0.1,
                key="ws_ss_weft_pre_slider",
            )
            st.session_state["ws_ss_weft_pretension"] = weft_pre

        col7 = st.columns(1)[0]
        with col7:
            edge_pre = st.slider(
                "Edge Cable Pretension (kN)",
                min_value=0.5, max_value=50.0,
                value=float(st.session_state["ws_ss_edge_cable_pretension"]),
                step=0.5,
                key="ws_ss_edge_pre_slider",
            )
            st.session_state["ws_ss_edge_cable_pretension"] = edge_pre





# SECTION 6 - BASEPLATE AND PRELIMINARY FOUNDATION
    with st.expander("6. Baseplate and Preliminary Foundation", expanded=False):
        section_header(
            "Baseplate and Preliminary Foundation",
            "Sizing depends on soil at the site."
        )

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
            "Preliminary sizing only. Geotechnical verification required."
        )

    # SECTION 7 - LOADS AND STANDARD
    with st.expander("7. Loads and Design Standard", expanded=False):
        section_header(
            "Loads and Design Standard",
            "User-added loads. Design code for safety factors."
        )

        payload = st.number_input(
            "Add. Pay Load (kg/m)",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state["ws_ss_add_payload"]),
            step=5.0,
            key="ws_ss_add_payload_input",
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

    # SECTION 8 - MEMBRANE-TO-BEAM ATTACHMENT
    with st.expander("8. Membrane-to-Beam Attachment", expanded=False):
        section_header(
            "Membrane-to-Beam Attachment",
            "How the fabric meets the beams. The free-end cable is part "
            "of the structure, not an option."
        )

        attach_options = ["kader", "segmented"]
        attach_labels = [
            "Kader Guider (continuous attachment)",
            "Segmented Edge (discrete cable supports)",
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
                "The fabric edge is continuously held in a track (keder) along "
                "the beam. No discrete attachment points. No side cables."
            )
        else:
            info_box(
                "<strong>Segmented Edge Attachment</strong><br>"
                "The fabric edge is supported at discrete points along the "
                "beam. Between any two adjacent points, the fabric edge is "
                "a short cable segment that bows inward under the edge "
                "cable pretension (Section 5)."
            )

        if st.session_state["ws_ss_attachment_type"] == "segmented":
            n_attach = st.number_input(
                "Cable Attachment Points per Beam",
                min_value=2, max_value=30,
                value=int(st.session_state["ws_ss_cable_attachment_count"]),
                step=1,
                key="ws_ss_cable_attach_input",
                help="How many discrete cable support points hold the fabric "
                     "edge along each beam. More points means shorter cable "
                     "segments between them, and a stiffer edge.",
            )
            st.session_state["ws_ss_cable_attachment_count"] = n_attach

            _span_v = float(st.session_state.get("ws_ss_span", 10.0))
            _approx_seg = _span_v / max(1, n_attach)

            preview_box(
                'Attachment points per beam: <span class="num">'
                + str(n_attach)
                + '</span><br>'
                + 'Approximate spacing between attachments: <span class="num">'
                + ("%.2f m" % _approx_seg)
                + '</span><br>'
                + 'Cable bow between attachments is controlled by the '
                + 'edge cable pretension in Section 5.'
            )

        info_box(
            "<strong>Free-End Cable</strong><br>"
            "The two free ends of the membrane are supported by a cable "
            "that runs from one beam tip to the other, bowing inward under "
            "the membrane tension. This cable is a mandatory part of the "
            "Cable Supported Saddle geometry, not a user option. Its "
            "pretension is set in Section 5."
        )

    # VIEWER STRINGS
    _total_h = float(st.session_state.get(
        "ws_ss_rise_input",
        st.session_state.get("ws_ss_rise", 6.2),
    ))

    st.session_state["ws_ss_viewer_description"] = (
        "Standard Saddle Span tensile membrane structure"
    )
    st.session_state["ws_ss_viewer_dimensions"] = (
        "Total height " + ("%.2f" % _total_h) + " m"
    )

    # ACTIONS
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





