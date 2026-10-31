# =============================================================================
# SDSe Fluid Design Studio - Results Page
# =============================================================================

import streamlit as st
import streamlit.components.v1 as components
import numpy as np

from viewers.results_viewer import generate_results_figure
from engine.steel_frame_sizer import size_steel_frame


def _build_params(variant_key):
    get = st.session_state.get
    if variant_key == "cantilever_leaf":
        return {"arrangement": get("ws_sl_arrangement", "single")}
    if variant_key == "standard_saddle":
        return {"span": get("ws_ss_span", None)}
    if variant_key == "frame_supported_saddle":
        return {"span": get("ws_bs_span", None)}
    return {}


@st.cache_data(show_spinner=False)
def _run_structural_analysis(vk, solved_data_id):
    if vk != "dome_multi_cone":
        return {"error": "Variant not wired for steel sizing yet."}

    data = st.session_state.get("ws_dm_solved_data", None)
    if not data:
        return {"error": "No solved data in session state."}

    fdm_coords = data.get("fdm_coords")
    if fdm_coords is None:
         return {"error": "FDM solver did not produce coordinates."}

    newton_data_cases = {"1.0_DL_LL": {"dr_result": {
        "coordinates": fdm_coords,
        "reactions": None
    }}}
    
    data["built"] = data["built"]
    data["anchor_idx"] = data["anchor_idx"]
    data["eave_height"] = data["eave_height"]
    data["xp"] = data["xp"]
    data["zp"] = data["zp"]
    data["rib_x"] = data["rib_x"]
    data["rib_half_width"] = data["rib_half_width"]
    data["mc_rd"] = data["mc_rd"]

    try:
        sizer_result = size_steel_frame(
            data=data,
            newton_data_cases=newton_data_cases,
            grade="S355",
            family="CHS"
        )
        return sizer_result
    except Exception as e:
        return {"error": "Fatal: " + str(e)}


def _render_analysis_and_quantities():
    vk = st.session_state.get("variant_key", "")
    with st.expander("Analysis and Quantities", expanded=True):

        solved_data = st.session_state.get("ws_dm_solved_data", None)
        
        if not solved_data:
            st.error("❌ NO SOLVED DATA FOUND.")
        else:
            st.success("✅ Using FDM stable geometry for force extraction.")

        cache_id = str(len(solved_data["built"]["points"])) if solved_data else "0"
        sizer_result = _run_structural_analysis(vk, cache_id)

        section_used = "--"
        n_ed, m_ed, v_ed = "--", "--", "--"
        
        # =====================================================================
        # THE HONEST CHECK: Show the error, don't hide it.
        # =====================================================================
        if sizer_result is None:
            st.error("❌ Sizer returned nothing.")
        elif "error" in sizer_result:
            st.error("❌ ENGINE FAILED: " + sizer_result["error"])
        else:
            sections = sizer_result.get("sections", {})
            if sections:
                section_used = sections.get("primary", "CHS")
            else:
                st.warning("⚠️ Sizer returned no sections.")

            frame_res = sizer_result.get("frame_result")
            if frame_res and len(frame_res.get("member_end_forces", [])) > 0:
                for end_force in frame_res["member_end_forces"]:
                    n_val = abs(end_force.get('N', 0.0))
                    my = max(abs(end_force.get('My_a', 0.0)), abs(end_force.get('My_b', 0.0)))
                    mz = max(abs(end_force.get('Mz_a', 0.0)), abs(end_force.get('Mz_b', 0.0)))
                    if n_val > 1.0 or my > 1.0 or mz > 1.0:
                        n_ed = f"{n_val / 1000.0:.1f}"
                        m_ed = f"{max(my, mz) / 1000.0:.1f}"
                        break
        # =====================================================================

        st.markdown("---")
        
        with st.expander("Section used", expanded=True):
            st.markdown(f"**{section_used}**")

        with st.expander("Analysis readings", expanded=True):
            st.write(f"**N_Ed:** {n_ed} kN")
            st.write(f"**M_Ed:** {m_ed} kNm")
            st.write(f"**V_Ed:** {v_ed} kN")


def render_results():
    sk = st.session_state.get("structure_key", "saddle_span")
    sn = st.session_state.get("structure_name", "Saddle Span")
    vk = st.session_state.get("variant_key", "")
    vn = st.session_state.get("variant_name", "Unknown Variant")
    info = st.session_state.get("project_info", {})
    pname = info.get("name", "") or "Untitled Project"
    cname = info.get("client", "") or "Unknown Client"

    st.markdown(f'<div style="font-size: 0.85rem; color: #a8b8c8; margin-bottom: 1rem;">SDSe Fluid Design Studio / <span style="color: #f39c12;">{sn}</span> / {vn} / Results</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background: #121e2e; border: 1px solid #1e2a3a; border-radius: 10px; padding: 1rem;"><div style="color: #ffffff; font-size: 1.15rem; font-weight: 700;">{pname}</div><div style="color: #a8b8c8; font-size: 0.85rem; margin-top: 0.3rem;">Client: {cname}</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="color: #f39c12; font-weight: 700; margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">3D View</div>', unsafe_allow_html=True)

    try:
        fig = generate_results_figure(sk, vk)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("3D view failed: " + str(e))

    _render_analysis_and_quantities()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Workshop", key="rb", use_container_width=True):
            st.session_state.page = "workshop"
            st.rerun()
    with col2:
        if st.button("Home", key="hm", use_container_width=True, type="primary"):
            st.session_state.page = "studio"
            st.rerun()
