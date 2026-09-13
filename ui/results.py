# Results page - simplified for 3D view testing
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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Workshop", key="rb", use_container_width=True):
            st.session_state.page = "workshop"
            st.rerun()
    with col2:
        if st.button("Home", key="hm", use_container_width=True, type="primary"):
            st.session_state.page = "studio"
            st.rerun()
