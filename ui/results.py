# =============================================================================
# SDSe Fluid Design Studio - Results Page
# =============================================================================
# The final page in the app flow. Appears after the user taps
# "Intelligent Design Computing" on any workshop.
#
# Design decisions (agreed 2026-09-13):
#   - 3D viewer driven by the workshop inputs (real geometry)
#   - Health score: placeholder until engine is connected
#   - Section used: placeholder until engine is connected
#   - Analysis readings: placeholder with notes
#   - Member schedule: geometric data real; sections/utilisation shown
#     as "auto" once engine is connected
#   - Quantities: geometric values (fabric area, member lengths)
#   - Preliminary foundation panel for the leaf
#   - Anchor reactions panel for the standard saddle (placeholder)
#   - Export: DXF and JSON only (PDF later)
#   - Save design: disabled "coming soon"
#   - Back to Workshop (inputs preserved)
#   - Home (return to Studio)
# =============================================================================

import json
import math
from datetime import datetime

import streamlit as st

from viewers.results_viewer import generate_results_figure


# =============================================================================
# CSS
# =============================================================================

RESULTS_CSS = """
    <style>
    .res-breadcrumb {
        font-size: 0.85rem;
        color: #a8b8c8;
        margin-bottom: 1.2rem;
        letter-spacing: 0.3px;
    }
    .res-breadcrumb .crumb {
        color: #f39c12;
        font-weight: 600;
    }
    .res-header {
        background-color: #121e2e;
        border: 1px solid #1e2a3a;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 1.2rem;
    }
    .res-header .project {
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
    }
    .res-header .meta {
        color: #a8b8c8;
        font-size: 0.85rem;
        line-height: 1.4;
    }

    .res-section-title {
        color: #f39c12;
        font-size: 1.05rem;
        font-weight: 700;
        margin: 1.4rem 0 0.6rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #1e2a3a;
        letter-spacing: 0.3px;
    }

    .health-card {
        background-color: #1a3a2a;
        border: 2px solid #2ecc71;
        border-radius: 14px;
        padding: 1.5rem 1rem;
        text-align: center;
        margin: 1rem 0 1.4rem 0;
    }
    .health-card .big {
        font-size: 3rem;
        font-weight: 800;
        color: #2ecc71;
        line-height: 1;
    }
    .health-card .label {
        color: #d0dff0;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    .health-card .note {
        color: #a8b8c8;
        font-size: 0.75rem;
        margin-top: 0.6rem;
        font-style: italic;
    }

    .res-info-card {
        background-color: #121e2e;
        border: 1px solid #1e2a3a;
        border-left: 4px solid #f39c12;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .res-info-card .label {
        color: #a8b8c8;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
    }
    .res-info-card .value {
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 700;
        font-family: monospace;
    }
    .res-info-card .note {
        color: #a8b8c8;
        font-size: 0.72rem;
        margin-top: 0.4rem;
        font-style: italic;
    }

    .res-metric {
        background-color: #0d1620;
        border: 1px solid #1e2a3a;
        border-radius: 8px;
        padding: 0.8rem;
        text-align: center;
    }
    .res-metric .label {
        color: #a8b8c8;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .res-metric .value {
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: 0.3rem;
        font-family: monospace;
    }
    .res-metric .unit {
        color: #a8b8c8;
        font-size: 0.75rem;
        margin-left: 3px;
    }

    .res-placeholder {
        background-color: #0d1620;
        border-left: 3px solid #4a7a9c;
        padding: 0.7rem 0.9rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        font-size: 0.82rem;
        color: #c8d4e0;
        line-height: 1.5;
    }

    .res-coming-soon {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 600;
        background-color: #f39c1233;
        color: #f39c12;
        border: 1px solid #f39c12;
        margin-left: 6px;
    }
    </style>
"""


# =============================================================================
# HELPERS
# =============================================================================

def _beam_arc_length_approx(span, rise, curve_type):
    """Approximate arc length of one beam for quantity calc."""
    if span <= 0:
        return 0.0
    ratio = rise / span
    if curve_type == "parabolic":
        return span * (1.0 + (8.0 / 3.0) * ratio * ratio)
    elif curve_type == "circular":
        if rise <= 0:
            return span
        R = (span ** 2 + 4 * rise ** 2) / (8 * rise)
        if R <= span / 2:
            return span
        half_angle = math.asin(span / (2 * R))
        return 2 * R * half_angle
    elif curve_type == "catenary":
        return span * (1.0 + 2.5 * ratio * ratio)
    return span


def _format_number(v, digits=2):
    try:
        return ("%." + str(digits) + "f") % float(v)
    except (TypeError, ValueError):
        return str(v)


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_results():
    """Render the Results page."""
    st.markdown(RESULTS_CSS, unsafe_allow_html=True)

    structure_key = st.session_state.get("structure_key", "saddle_span")
    structure_name = st.session_state.get("structure_name", "Saddle Span")
    variant_key = st.session_state.get("variant_key", "")
    variant_name = st.session_state.get("variant_name", "Unknown Variant")
    info = st.session_state.get("project_info", {})

    project_name = info.get("name", "") or "Untitled Project"
    client_name = info.get("client", "") or "Unknown Client"
    reference = info.get("reference", "") or "-"

    # ---- Breadcrumb
    st.markdown(
        '<div class="res-breadcrumb">'
        'SDSe Fluid Design Studio / '
        '<span class="crumb">' + structure_name + '</span>'
        ' / '
        '<span class="crumb">' + variant_name + '</span>'
        ' / '
        '<span class="crumb">Results</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Project header
    st.markdown(
        '<div class="res-header">'
        '<div class="project">' + project_name + '</div>'
        '<div class="meta">'
        'Client: ' + client_name + '<br>'
        'Reference: ' + reference + '<br>'
        'Structure: ' + structure_name + ' / ' + variant_name
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- 3D Viewer
    st.markdown('<div class="res-section-title">3D View</div>', unsafe_allow_html=True)

    try:
        fig = generate_results_figure(structure_key, variant_key)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    except Exception as e:
        st.error("3D view failed: " + str(e))

    # ---- Health Indicator (placeholder)
    st.markdown('<div class="res-section-title">Health Score</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="health-card">'
        '<div class="big">100</div>'
        '<div class="label">Design Healthy</div>'
        '<div class="note">'
        'Placeholder value. Real health score computed when engine is connected.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Section Used (placeholder)
    st.markdown('<div class="res-section-title">Section Used</div>', unsafe_allow_html=True)

    fallback_section = "CHS 168.3x7.1"
    if structure_key == "saddle_span" and variant_key == "cantilever_leaf":
        fallback_section = "CHS 323.8x8.0 (column) / CHS 168.3x7.1 (spine)"

    st.markdown(
        '<div class="res-info-card">'
        '<div class="label">Primary member section</div>'
        '<div class="value">' + fallback_section + '</div>'
        '<div class="note">'
        'Placeholder. Engine will auto-select the optimal section from the catalogue.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Analysis Readings (placeholder)
    st.markdown('<div class="res-section-title">Analysis Readings</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="res-metric">'
            '<div class="label">N_Ed</div>'
            '<div class="value">--<span class="unit">kN</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="res-metric">'
            '<div class="label">M_Ed</div>'
            '<div class="value">--<span class="unit">kNm</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="res-metric">'
            '<div class="label">V_Ed</div>'
            '<div class="value">--<span class="unit">kN</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(
            '<div class="res-metric">'
            '<div class="label">Wind pressure</div>'
            '<div class="value">--<span class="unit">kPa</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            '<div class="res-metric">'
            '<div class="label">Uplift</div>'
            '<div class="value">--<span class="unit">kPa</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            '<div class="res-metric">'
            '<div class="label">Deflection</div>'
            '<div class="value">--<span class="unit">mm</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="res-placeholder">'
        'Analysis readings will populate when the engine is connected. '
        'The 3D view above is generated from the input geometry you provided.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Member Schedule
    st.markdown('<div class="res-section-title">Member Schedule</div>', unsafe_allow_html=True)

    members = _build_member_schedule(structure_key, variant_key)
    if members:
        header = "| # | Role | Section | Length (m) | Weight (kg) | Utilisation |"
        sep = "|---|---|---|---|---|---|"
        rows = [header, sep]
        for i, m in enumerate(members, 1):
            rows.append(
                "| " + str(i)
                + " | " + str(m.get("role", ""))
                + " | " + str(m.get("section", "auto"))
                + " | " + _format_number(m.get("length", 0))
                + " | " + _format_number(m.get("weight", 0), 1)
                + " | " + str(m.get("utilisation", "--"))
                + " |"
            )
        st.markdown("\n".join(rows))
    else:
        st.info("Member schedule will appear once the workshop inputs are complete.")

    # ---- Quantities
    st.markdown('<div class="res-section-title">Quantities</div>', unsafe_allow_html=True)

    qty = _build_quantities(structure_key, variant_key)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="res-metric">'
            '<div class="label">Steel weight</div>'
            '<div class="value">' + _format_number(qty["steel_kg"], 1) + '<span class="unit">kg</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="res-metric">'
            '<div class="label">Cable length</div>'
            '<div class="value">' + _format_number(qty["cable_m"], 1) + '<span class="unit">m</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="res-metric">'
            '<div class="label">Fabric area</div>'
            '<div class="value">' + _format_number(qty["fabric_m2"], 1) + '<span class="unit">m2</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="res-placeholder">'
        'Quantities shown are derived from the input geometry. '
        'Full BQ (with weights and finish details) computed when engine is connected.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Preliminary Foundation (leaf) or Anchor Reactions (standard saddle)
    if structure_key == "saddle_span" and variant_key == "cantilever_leaf":
        st.markdown('<div class="res-section-title">Preliminary Foundation</div>', unsafe_allow_html=True)
        bearing = float(st.session_state.get("ws_sl_soil_bearing", 150.0))
        st.markdown(
            '<div class="res-info-card">'
            '<div class="label">Assumed bearing capacity</div>'
            '<div class="value">' + _format_number(bearing, 0) + ' kN/m2</div>'
            '<div class="note">'
            'Baseplate dimensions and anchor bolts will be auto-sized when engine is connected. '
            'Preliminary footing size will be computed from the column reaction. '
            'Geotechnical verification required.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    elif structure_key == "saddle_span" and variant_key == "standard_saddle":
        st.markdown('<div class="res-section-title">Anchor Reactions</div>', unsafe_allow_html=True)
        intervals = int(st.session_state.get("ws_ss_tiedown_intervals", 3))
        st.markdown(
            '<div class="res-info-card">'
            '<div class="label">Tie-down intervals</div>'
            '<div class="value">' + str(intervals) + ' per beam</div>'
            '<div class="note">'
            'Cable tensions and anchor uplift reactions will be computed when the engine is connected.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ---- Export
    st.markdown('<div class="res-section-title">Export</div>', unsafe_allow_html=True)

    col_dxf, col_json = st.columns(2)

    with col_dxf:
        if st.button("Export DXF", key="res_export_dxf", use_container_width=True):
            st.info("DXF export will be wired in the next phase.")

    with col_json:
        if st.button("Export JSON", key="res_export_json", use_container_width=True):
            data = {
                "project": info,
                "structure_key": structure_key,
                "variant_key": variant_key,
                "inputs": _collect_inputs(structure_key, variant_key),
                "exported_at": datetime.now().isoformat(),
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(data, indent=2, default=str),
                file_name="sdse_design_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json",
                mime="application/json",
                key="res_json_download",
            )

    # ---- Save design (coming soon)
    st.markdown('<div style="height: 0.6rem;"></div>', unsafe_allow_html=True)
    st.button(
        "Save Design (coming soon)",
        key="res_save_design",
        use_container_width=True,
        disabled=True,
    )

    # ---- Navigation
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
    col_back, col_home = st.columns(2)
    with col_back:
        if st.button("Back to Workshop", key="res_back_ws", use_container_width=True):
            st.session_state.page = "workshop"
            st.rerun()
    with col_home:
        if st.button("Home", key="res_home", use_container_width=True, type="primary"):
            st.session_state.page = "studio"
            st.rerun()


# =============================================================================
# HELPERS - SCHEDULE, QUANTITIES, INPUT COLLECTION
# =============================================================================

def _build_member_schedule(structure_key, variant_key):
    """Build a member list from inputs. Lengths real; sections auto."""
    members = []

    if structure_key == "saddle_span" and variant_key == "standard_saddle":
        span = float(st.session_state.get("ws_ss_span", 20.0))
        rise = float(st.session_state.get("ws_ss_rise", 2.5))
        curve = st.session_state.get("ws_ss_curve_type", "parabolic")
        arc = _beam_arc_length_approx(span, rise, curve)
        intervals = int(st.session_state.get("ws_ss_tiedown_intervals", 3))
        apex = float(st.session_state.get("ws_ss_apex", 12.0))

        members.append({"role": "Edge beam L", "section": "auto", "length": arc, "weight": arc * 20.0, "utilisation": "--"})
        members.append({"role": "Edge beam R", "section": "auto", "length": arc, "weight": arc * 20.0, "utilisation": "--"})
        members.append({"role": "Membrane", "section": "fabric", "length": apex, "weight": span * apex * 0.9 / 1000.0, "utilisation": "--"})

        n_ties = intervals * 2  # both sides
        tie_len = 0.0
        if arc > 0:
            tie_len = intervals and (span / (intervals + 1))
        members.append({"role": "Tie-down cables", "section": "auto", "length": float(n_ties) * 2.5, "weight": 0.0, "utilisation": "--"})

    elif structure_key == "saddle_span" and variant_key == "cantilever_leaf":
        col_h = float(st.session_state.get("ws_sl_column_height", 10.0))
        outreach = float(st.session_state.get("ws_sl_outreach", 10.0))
        ribs = int(st.session_state.get("ws_sl_ribs_per_side", 7))
        strut_j = float(st.session_state.get("ws_sl_strut_joint_height", col_h * 0.6))

        members.append({"role": "Column", "section": "auto", "length": col_h, "weight": col_h * 64.9, "utilisation": "--"})
        members.append({"role": "Main beam (spine)", "section": "auto", "length": outreach * 1.05, "weight": outreach * 1.05 * 28.3, "utilisation": "--"})
        members.append({"role": "Ribs (" + str(ribs) + " per side)", "section": "auto", "length": outreach * 0.6 * 2 * ribs, "weight": outreach * 0.6 * 2 * ribs * 15.0, "utilisation": "--"})
        members.append({"role": "Curved strut", "section": "auto", "length": math.sqrt((outreach * 0.33) ** 2 + (col_h - strut_j) ** 2), "weight": 0.0, "utilisation": "--"})

    return members


def _build_quantities(structure_key, variant_key):
    """Compute geometric quantities from inputs."""
    qty = {"steel_kg": 0.0, "cable_m": 0.0, "fabric_m2": 0.0}

    if structure_key == "saddle_span" and variant_key == "standard_saddle":
        span = float(st.session_state.get("ws_ss_span", 20.0))
        apex = float(st.session_state.get("ws_ss_apex", 12.0))
        rise = float(st.session_state.get("ws_ss_rise", 2.5))
        curve = st.session_state.get("ws_ss_curve_type", "parabolic")
        arc = _beam_arc_length_approx(span, rise, curve)
        intervals = int(st.session_state.get("ws_ss_tiedown_intervals", 3))

        qty["steel_kg"] = arc * 2 * 20.0
        qty["fabric_m2"] = span * apex * 1.1
        qty["cable_m"] = intervals * 2 * 2.5

    elif structure_key == "saddle_span" and variant_key == "cantilever_leaf":
        outreach = float(st.session_state.get("ws_sl_outreach", 10.0))
        ribs = int(st.session_state.get("ws_sl_ribs_per_side", 7))
        col_h = float(st.session_state.get("ws_sl_column_height", 10.0))

        qty["steel_kg"] = col_h * 64.9 + outreach * 28.3 + ribs * 2 * outreach * 0.6 * 15.0
        qty["fabric_m2"] = outreach * outreach * 0.5 * 0.8
        qty["cable_m"] = outreach * 2 * 0.9  # perimeter cables approx

    return qty


def _collect_inputs(structure_key, variant_key):
    """Collect workshop inputs from session state for JSON export."""
    keys_prefix = ""
    if structure_key == "saddle_span" and variant_key == "standard_saddle":
        keys_prefix = "ws_ss_"
    elif structure_key == "saddle_span" and variant_key == "cantilever_leaf":
        keys_prefix = "ws_sl_"

    inputs = {}
    for k, v in st.session_state.items():
        if isinstance(k, str) and k.startswith(keys_prefix):
            inputs[k] = v
    return inputs
