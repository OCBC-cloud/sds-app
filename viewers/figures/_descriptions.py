# =============================================================================
# SDSe - Structure Summary Descriptions
# =============================================================================
# Small text block describing the current structure dimensions.
# Called by the Results page to show a summary below the 3D view.
# =============================================================================

import streamlit as st


def get_structure_summary(variant_key):
    """
    Return an HTML string describing the current structure.
    Reads from session state keys set by the workshop.
    Returns empty string if the variant is unknown.
    """
    if variant_key == "standard_saddle":
        return _summary_cable_supported()
    if variant_key == "frame_supported_saddle":
        return _summary_beam_supported()
    if variant_key == "cantilever_leaf":
        return _summary_cantilever_leaf()
    return ""


def _summary_cable_supported():
    """Summary for Cable Supported Saddle."""
    span = st.session_state.get("ws_ss_span", 0.0)
    apex = st.session_state.get("ws_ss_apex", 0.0)
    rise = st.session_state.get("ws_ss_rise", 0.0)
    count = int(st.session_state.get("ws_ss_tiedown_intervals", 4))

    line1 = "Span: <strong>" + ("%.1f" % span) + " m</strong>"
    line1 += "  |  Apex-to-Apex: <strong>" + ("%.1f" % apex) + " m</strong>"
    line1 += "  |  Rise: <strong>" + ("%.1f" % rise) + " m</strong>"

    line2 = "Tie-down cables: <strong>" + str(count) + "</strong> total"

    return _wrap_two_lines(line1, line2)


def _summary_beam_supported():
    """Summary for Beam Supported Saddle."""
    span = st.session_state.get("ws_bs_span", 0.0)
    apex = st.session_state.get("ws_bs_apex", 0.0)
    rise = st.session_state.get("ws_bs_rise", 0.0)
    sec = int(st.session_state.get("ws_bs_secondary_count", 2))

    # Count purlins using the same rule as the workshop
    purlin_count = _count_purlins(span)

    line1 = "Span: <strong>" + ("%.1f" % span) + " m</strong>"
    line1 += "  |  Apex-to-Apex: <strong>" + ("%.1f" % apex) + " m</strong>"
    line1 += "  |  Rise: <strong>" + ("%.1f" % rise) + " m</strong>"

    line2 = "Secondary beams per main beam: <strong>" + str(sec) + "</strong>"
    line2 += "  |  Purlins: <strong>" + str(purlin_count) + "</strong>"

    return _wrap_two_lines(line1, line2)


def _summary_cantilever_leaf():
    """Summary for Cantilever Leaf."""
    col_h = st.session_state.get("ws_sl_column_height", 0.0)
    outreach = st.session_state.get("ws_sl_outreach", 0.0)
    ribs = int(st.session_state.get("ws_sl_ribs_per_side", 0))

    line1 = "Column height: <strong>" + ("%.1f" % col_h) + " m</strong>"
    line1 += "  |  Outreach: <strong>" + ("%.1f" % outreach) + " m</strong>"

    line2 = "Ribs per side: <strong>" + str(ribs) + "</strong>"

    return _wrap_two_lines(line1, line2)


def _count_purlins(span):
    """Count purlins using the 2.5 m rule."""
    interval = 2.5
    half = span / 2.0
    count = 1  # centre purlin
    k = 1
    while True:
        offset = k * interval
        if offset > half - interval:
            break
        count += 2
        k += 1
    return count


def _wrap_two_lines(line1, line2):
    """Wrap two summary lines in the standard info box style."""
    html = (
        '<div style="background: #0d1620; border-left: 3px solid #4a7a9c; '
        'padding: 0.7rem 0.9rem; border-radius: 4px; margin: 0.5rem 0; '
        'font-size: 0.82rem; color: #c8d4e0; line-height: 1.6;">'
        '<div>' + line1 + '</div>'
        '<div style="margin-top: 0.3rem;">' + line2 + '</div>'
        '</div>'
    )
    return html







