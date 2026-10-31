# =============================================================================
# SDSe Fluid Design Studio - Results Page (True Structural Analysis)
# =============================================================================

import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd

from viewers.results_viewer import generate_results_figure
from engine.SDSe_orchestrator import run_structural_analysis


def _run_analysis(vk, cache_id):
    if vk != "dome_multi_cone":
        return {"error": "Variant not wired for steel sizing yet."}

    data = st.session_state.get("ws_dm_solved_data", None)
    if not data:
        return {"error": "No solved data in session state."}
        
    # Assemble the data dictionary the orchestrator needs
    data["fdm_coords"] = data["fdm_coords"]
    data["built"] = data["built"]
    data["anchor_idx"] = data["anchor_idx"]
    data["eave_height"] = data["eave_height"]
    data["xp"] = data["xp"]
    data["zp"] = data["zp"]
    data["rib_x"] = data["rib_x"]
    data["rib_half_width"] = data["rib_half_width"]
    data["mc_rd"] = data["mc_rd"]
    
    # Pull material/wind inputs from session state
    data["fabric_type"] = st.session_state.get("ws_dm_fabric_type", "PVDF")
    data["fabric_grade"] = st.session_state.get("ws_dm_fabric_grade", "Type III")
    data["load_standard"] = st.session_state.get("ws_dm_load_standard", "MY")

    try:
        return run_structural_analysis(data)
    except Exception as e:
        return {"error": "Fatal: " + str(e)}


def _render_analysis():
    vk = st.session_state.get("variant_key", "")
    solved_data = st.session_state.get("ws_dm_solved_data", None)
    cache_id = str(len(solved_data["built"]["points"])) if solved_data else "0"
    
    result = _run_analysis(vk, cache_id)

    with st.expander("Analysis and Quantities", expanded=True):
        
        if "error" in result:
            st.error("❌ ENGINE FAILED: " + result["error"])
            return

        sections = result.get("sections", {})
        results = result.get("results", {})
        
        section_used = sections.get("primary", "--")
        
        # 1. Display the section
        with st.expander("Section used", expanded=True):
            st.markdown(f"**Primary:** {sections.get('primary', '--')}")
            st.markdown(f"**Ribs:** {sections.get('rib', '--')}")
            st.markdown(f"**Rings:** {sections.get('ring', '--')}")

        # 2. Display the worst-case forces
        member_forces = results.get("member_end_forces", [])
        n_ed, m_ed, v_ed = 0.0, 0.0, 0.0
        
        for elem in member_forces:
            n_ed = max(n_ed, abs(elem.get("N", 0.0)) / 1000.0)
            m_ed = max(m_ed, max(abs(elem.get("My_a", 0.0)), abs(elem.get("Mz_a", 0.0))) / 1e6)
            v_ed = max(v_ed, max(abs(elem.get("V_y", 0.0)), abs(elem.get("V_z", 0.0))) / 1000.0)

        with st.expander("Maximum Analysis Readings", expanded=True):
            st.write(f"**N_Ed (Max):** {n_ed:.1f} kN")
            st.write(f"**M_Ed (Max):** {m_ed:.1f} kNm")
            st.write(f"**V_Ed (Max):** {v_ed:.1f} kN")

        # 3. DIGITISED NODE STATE REPORTING
        with st.expander("🔍 Digitised Node State (Full Report)", expanded=False):
            st.write("### Reactions at Baseplates")
            reactions = results.get("reactions", [])
            
            if len(reactions) > 0:
                react_data = []
                for i, r in enumerate(reactions):
                    if np.any(r != 0):  # Only show fixed nodes
                        react_data.append({
                            "Node": i,
                            "Fx (kN)": f"{r[0]/1000:.2f}",
                            "Fy (kN)": f"{r[1]/1000:.2f}",
                            "Fz (kN)": f"{r[2]/1000:.2f}",
                            "Mx (kNm)": f"{r[3]/1000:.2f}",
                            "My (kNm)": f"{r[4]/1000:.2f}",
                            "Mz (kNm)": f"{r[5]/1000:.2f}"
                        })
                st.dataframe(pd.DataFrame(react_data), use_container_width=True)
            else:
                st.info("No reactions found.")

            st.write("### Member Forces (First 10)")
            if len(member_forces) > 0:
                elem_data = []
                for elem in member_forces[:10]:
                    elem_data.append({
                        "Member Type": elem.get("kind", "?"),
                        "Node A": elem.get("a"),
                        "Node B": elem.get("b"),
                        "Axial (kN)": f"{elem.get('N', 0.0)/1000:.1f}",
                        "Shear Y (kN)": f"{elem.get('V_y', 0.0)/1000:.1f}",
                        "Shear Z (kN)": f"{elem.get('V_z', 0.0)/1000:.1f}",
                        "Moment Y (kNm)": f"{max(abs(elem.get('My_a', 0.0)), abs(elem.get('My_b', 0.0)))/1e6:.1f}",
                        "Moment Z (kNm)": f"{max(abs(elem.get('Mz_a', 0.0)), abs(elem.get('Mz_b', 0.0)))/1e6:.1f}",
                        "Torsion (kNm)": f"{elem.get('T', 0.0)/1e6:.2f}"
                    })
                st.dataframe(pd.DataFrame(elem_data), use_container_width=True)


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

    _render_analysis()

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
