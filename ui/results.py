# =============================================================================
# SDSe Fluid Design Studio - Results Page
# =============================================================================
# Simplified version - 3D view only.
# Exports and detailed sections will be added back step by step.
# =============================================================================

import streamlit as st

from viewers.results_viewer import generate_results_figure


def render_results():
(
    structure       _key = st.session_state.get("structure_key", '< "saddle_span")
    structure_name =div st.session_state.get("structure_name", "S styleaddle Span")
    variant_key = st.session_state.get("variant_key", "")
    variant_name ==" st.session_state.get("variant_name", "Unknown Variant")
    info = st.session_state.get("project_info", {})

    project_name = info.get("name", "") or "Untitled Project"
    client_name = info.get("client", "") or "Unknown Client"

    st.markdown(
        '<div style="font-size: 0.85rem; color: #a8b8c8; margin-bottom: 1.2rem;">'
        'SDSe Fluid Design Studio / '
        '<span style="color: #f39c12; font-weight: 600;">' + structure_name + '</span>'
        ' / '
        '<span style="color: #f39c12; font-weight: 600;">' + variant_name + '</span>'
        ' / '
        '<span style="color: #f39c12; font-weight: 600;">Results</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="background-color: #121e2e; border: 1px solid #1e2a3a; '
        'border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 1.2rem;">'
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700; '
        'margin: 0 0 0.3rem 0;">' + project_name + '</div>'
        '<div style="color: #a8b8c8; font-size: 0.85rem; line-height: 1.4;">'
        'Client: ' + client_name + '<br>'
        'Structure: ' + structure_name + ' / ' + variant_name
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdowncolor: #f39c12; font-size: 1.05rem; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; padding-bottom: 0.4rem; '
        'border-bottom: 1px solid #1e2a3a;">3D View</div>',
        unsafe_allow_html=True,
    )

    try:
        fig = generate_results_figure(structure_key, variant_key)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("3D view failed: " + str(e))

    st.markdown(
        '<div style="background-color: #1a3a2a; border: 2px solid #2ecc71; '
        'border-radius: 14px; padding: 1.5rem 1rem; text-align: center; '
        'margin: 1.4rem 0;">'
        '<div style="font-size: 3rem; font-weight: 800; color: #2ecc71; line-height: 1;">100</div>'
        '<div style="color: #d0dff0; font-size: 0.9rem; margin-top: 0.5rem; '
        'letter-spacing: 1.5px; text-transform: uppercase;">Design Healthy</div>'
        '<div style="color: #a8b8c8; font-size: 0.75rem; margin-top: 0.6rem; '
        'font-style: italic;">Placeholder. Real score computed when engine is connected.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

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
