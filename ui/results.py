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
        return None

    data = st.session_state.get("ws_dm_solved_data", None)
    if not data:
        return {"error": "No solved data in session state."}

    # Pass the summary to the builder
    newton_data_cases = {"1.0_DL_LL": {"dr_result": {
        "coordinates": data["fdm_coords"],
        "solve_summary": data["solve_summary"],
        "reactions": data["solve_summary"].get("nfdm", {}).get("reactions", None)
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
        return {"error": str(e)}


def _render_marketing_render(vk, sk):
    # (Kept simple for diagnostic testing - will restore full version later)
    st.info("Marketing Render section here.")


def _render_analysis_and_quantities():
    vk = st.session_state.get("variant_key", "")

    with st.expander("Analysis and Quantities", expanded=True):

        # =====================================================================
        # DIAGNOSTIC ZONE
        # =====================================================================
        solved_data = st.session_state.get("ws_dm_solved_data", None)
        
        if not solved_data:
            st.error("❌ CRITICAL: NO SOLVED DATA FOUND. The viewer didn't save the solver results.")
        else:
            st.success("✅ Solved data found in session state.")
            summary = solved_data.get("solve_summary", {})
            nfdm = summary.get("nfdm", {})
            
            st.write("### 🔍 Solver Diagnostics")
            st.write(f"**Converged:** `{nfdm.get('converged')}`")
            st.write(f"**Reason:** `{nfdm.get('reason')}`")
            st.write(f"**Iterations:** `{nfdm.get('iterations')}`")
            st.write(f"**Total Steps:** `{nfdm.get('total_steps')}`")
            st.write(f"**Elapsed (s):** `{nfdm.get('elapsed_seconds'):.2f}`" if nfdm.get('elapsed_seconds') else "N/A")
            st.write(f"**Max Residual:** `{nfdm.get('max_residual')}`")
            
            reactions = nfdm.get("reactions")
            if reactions is not None:
                try:
                    max_force = np.max(np.abs(np.asarray(reactions)))
                    st.write(f"**Reactions Shape:** `{np.asarray(reactions).shape}`")
                    st.write(f"**Max Reaction Force:** `{max_force:.2f} N`")
                except Exception as e:
                    st.error(f"Reactions exist but failed to read: {e}")
            else:
                st.error("❌ NO 'REACTIONS' ARRAY FOUND IN NFDM SUMMARY.")
        # =====================================================================

        cache_id = str(len(solved_data["built"]["points"])) if solved_data else "0"
        sizer_result = _run_structural_analysis(vk, cache_id)

        section_used = "--"
        n_ed, m_ed, v_ed = "--", "--", "--"
        
        if sizer_result and "error" not in sizer_result:
            sections = sizer_result.get("sections", {})
            if sections:
                section_used = sections.get("primary", "CHS")
            
            st.write(f"**Sizer Result Section:** `{section_used}`")

        elif sizer_result and "error" in sizer_result:
            st.error("Sizer/Builder failed: " + sizer_result["error"])

        st.markdown("---")
        
        with st.expander("Section used", expanded=True):
            st.markdown(f"**{section_used}**")

        with st.expander("Analysis readings", expanded=True):
            st.write(f"N_Ed: {n_ed} kN")
            st.write(f"M_Ed: {m_ed} kNm")
            st.write(f"V_Ed: {v_ed} kN")


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
        'SDSe Fluid Design Studio / <span style="color: #f39c12;">' + sn + '</span> / ' + vn + ' / Results</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
        'border-radius: 10px; padding: 1rem;">'
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700;">' + pname + '</div>'
        '<div style="color: #a8b8c8; font-size: 0.85rem; margin-top: 0.3rem;">Client: ' + cname + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="color: #f39c12; font-weight: 700; margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">3D View</div>', unsafe_allow_html=True)

    try:
        fig = generate_results_figure(sk, vk)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        import traceback
        st.error("3D view failed: " + str(e))
        st.code(traceback.format_exc())

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
