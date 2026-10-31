# =============================================================================
# SDSe Fluid Design Studio - Results Page (Global Statics)
# =============================================================================

import streamlit as st
import pandas as pd
from viewers.results_viewer import generate_results_figure
from engine.SDSe_orchestrator import run_structural_analysis


def render_results():
    sk = st.session_state.get("structure_key", "saddle_span")
    sn = st.session_state.get("structure_name", "Saddle Span")
    vk = st.session_state.get("variant_key", "")
    vn = st.session_state.get("variant_name", "Unknown Variant")
    info = st.session_state.get("project_info", {})
    pname = info.get("name", "") or "Untitled Project"
    cname = info.get("client", "") or "Unknown Client"

    # Header
    st.markdown(f'<div style="font-size: 0.85rem; color: #a8b8c8; margin-bottom: 1rem;">SDSe Fluid Design Studio / <span style="color: #f39c12;">{sn}</span> / {vn} / Results</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background: #121e2e; border: 1px solid #1e2a3a; border-radius: 10px; padding: 1rem;"><div style="color: #ffffff; font-size: 1.15rem; font-weight: 700;">{pname}</div><div style="color: #a8b8c8; font-size: 0.85rem; margin-top: 0.3rem;">Client: {cname}</div></div>', unsafe_allow_html=True)

    # --- 3D VIEWER ---
    st.markdown('<div style="color: #f39c12; font-weight: 700; margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">3D View</div>', unsafe_allow_html=True)
    try:
        fig = generate_results_figure(sk, vk)
        st.plotly_chart(fig, use_container_width=True, key="results_3d_view")
    except Exception as e:
        st.error("3D view failed: " + str(e))

    st.markdown("---")

    # --- ANALYSIS SECTION ---
    with st.expander("Analysis and Quantities", expanded=True):
        
        if st.button("🚀 Run Structural Analysis", type="primary", use_container_width=True):
            with st.spinner("Calculating Global Statics..."):
                solved_data = st.session_state.get("ws_dm_solved_data", None)
                
                if not solved_data:
                    st.error("❌ No FDM data found. Please run the form-finding again.")
                else:
                    # Prepare data for orchestrator
                    data = solved_data.copy()
                    data["fabric_type"] = st.session_state.get("ws_dm_fabric_type", "PVDF")
                    data["fabric_grade"] = st.session_state.get("ws_dm_fabric_grade", "Ferrari 702")
                    data["dome_diameter"] = st.session_state.get("ws_dm_dome_diameter", 18.0)
                    data["crown_height"] = st.session_state.get("ws_dm_crown_height", 9.0)

                    result = run_structural_analysis(data)
                    
                    if "error" in result:
                        st.error("❌ " + result["error"])
                    else:
                        st.session_state["global_statics_results"] = result
                        st.success("✅ Analysis Complete!")

        # Display results if they exist
        if "global_statics_results" in st.session_state:
            result = st.session_state["global_statics_results"]
            sections = result.get("sections", {})
            loads = result.get("loads", {})
            
            st.markdown("### 🌪️ Wind & Uplift Forces")
            st.write(f"**True Surface Area:** {loads.get('surface_area', 0.0):.1f} m²")
            st.write(f"**Total Wind Uplift:** {loads.get('total_wind_uplift_N', 0.0) / 1000:.1f} kN")
            st.write(f"**Total Wind Pressure:** {loads.get('total_wind_pressure_N', 0.0) / 1000:.1f} kN")

            st.markdown("### 🏗️ Steel Sections (S355)")
            for k, v in sections.items():
                st.write(f"**{k.capitalize()}:** {v}")
                
            st.markdown("### 📊 Utilization")
            for k, v in result.get("max_utilization", {}).items():
                st.write(f"**{k.capitalize()}:** {v:.1%}")
                
            if st.button("Clear Results"):
                del st.session_state["global_statics_results"]
                st.rerun()

    # Footer buttons
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
