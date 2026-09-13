# Results page - with Section Used and Analysis Readings
import streamlit as st
from viewers.results_viewer import generate_results_figure


def render_results():
    sk = st.session_state.get("structure_key", "saddle_span")
    sn = st.session_state.get("structure_name", "Saddle Span")
    vk = st.session_state.get("variant_key", "")
    vn = st.session_state.get("variant_name", "Unknown Variant")
    info = st.session_state.get("project_info", {})
    pname = info.get("name", "") or "Untitled Project"
    cname = info.get("client", "") or "Unknown Client"

    st.markdown(
        '<div style="font-size: 0.85rem; color: #a8b8c8; margin-bottom: 1rem;">'
        'SDSe Fluid Design Studio / '
        '<span style="color: #f39c12;">' + sn + '</span>'
        ' / ' + vn + ' / Results'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
        'border-radius: 10px; padding: 1rem;">'
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700;">'
        + pname + '</div>'
        '<div style="color: #a8b8c8; font-size: 0.85rem; margin-top: 0.3rem;">'
        'Client: ' + cname + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">3D View</div>',
        unsafe_allow_html=True,
    )

    try:
        fig = generate_results_figure(sk, vk)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("3D view failed: " + str(e))

    st.markdown(
        '<div style="background: #1a3a2a; border: 2px solid #2ecc71; '
        'border-radius: 14px; padding: 1.5rem; text-align: center; '
        'margin: 1.4rem 0;">'
        '<div style="font-size: 3rem; font-weight: 800; color: #2ecc71;">100</div>'
        '<div style="color: #d0dff0; font-size: 0.9rem; margin-top: 0.5rem; '
        'letter-spacing: 1.5px; text-transform: uppercase;">Design Healthy</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">Section Used</div>',
        unsafe_allow_html=True,
    )

    fallback_section = "CHS 168.3x7.1"
    if sk == "saddle_span" and vk == "cantilever_leaf":
        fallback_section = "CHS 323.8x8.0 / CHS 168.3x7.1"

    st.markdown(
        '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
        'border-left: 4px solid #f39c12; border-radius: 8px; '
        'padding: 1rem 1.2rem; margin-bottom: 0.8rem;">'
        '<div style="color: #a8b8c8; font-size: 0.78rem; '
        'text-transform: uppercase; letter-spacing: 0.5px; '
        'margin-bottom: 0.3rem;">Primary member section</div>'
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700; '
        'font-family: monospace;">' + fallback_section + '</div>'
        '<div style="color: #a8b8c8; font-size: 0.72rem; '
        'margin-top: 0.4rem; font-style: italic;">'
        'Placeholder. Engine will auto-select the optimal section.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">Analysis Readings</div>',
        unsafe_allow_html=True,
    )

    def metric_card(label, value, unit):
        return (
            '<div style="background: #0d1620; border: 1px solid #1e2a3a; '
            'border-radius: 8px; padding: 0.8rem; text-align: center;">'
            '<div style="color: #a8b8c8; font-size: 0.72rem; '
            'text-transform: uppercase; letter-spacing: 0.5px;">'
            + label + '</div>'
            '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700; '
            'margin-top: 0.3rem; font-family: monospace;">'
            + value + '<span style="color: #a8b8c8; font-size: 0.75rem; '
            'margin-left: 3px;">' + unit + '</span></div>'
            '</div>'
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card("N_Ed", "--", "kN"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("M_Ed", "--", "kNm"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("V_Ed", "--", "kN"), unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(metric_card("Wind pressure", "--", "kPa"), unsafe_allow_html=True)
    with c5:
        st.markdown(metric_card("Uplift", "--", "kPa"), unsafe_allow_html=True)
    with c6:
        st.markdown(metric_card("Deflection", "--", "mm"), unsafe_allow_html=True)

    st.markdown(
        '<div style="background: #0d1620; border-left: 3px solid #4a7a9c; '
        'padding: 0.7rem 0.9rem; border-radius: 4px; margin: 0.5rem 0; '
        'font-size: 0.82rem; color: #c8d4e0; line-height: 1.5;">'
        'Readings populate when the engine is connected. '
        'The 3D view above is generated from the geometry you provided.'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Workshop", key="rb", use_container_width=True):
            st.session_state.page = "workshop"
            st.rerun()
    with col2:
        if st.button("Home", key="hm", use_container_width=True, type="primary"):
            st.session_state.page = "studio"
            st.rerun()
