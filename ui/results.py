# =============================================================================
# SDSe Fluid Design Studio - Results Page (Geometry Documentation Only)
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np


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

    st.markdown("---")
    
    with st.expander("📐 Geometry Documentation (Raw Mesh Data)", expanded=True):
        
        solved_data = st.session_state.get("ws_dm_solved_data", None)
        
        if not solved_data:
            st.error("❌ No FDM solved data found in session state.")
            return
            
        fdm_coords = solved_data.get("fdm_coords", None)
        built = solved_data.get("built", None)
        
        if fdm_coords is None:
            st.error("❌ 'fdm_coords' is missing from session state.")
            return
            
        if built is None:
            st.error("❌ 'built' dictionary is missing from session state.")
            return
            
        triangles = built.get("triangles", [])
        
        # 1. Document the Surface Area
        st.write("### 🌐 True Curved Surface Area")
        st.write(f"**Mesh Nodes:** {len(fdm_coords)}")
        st.write(f"**Mesh Triangles:** {len(triangles)}")
        
        true_surface_area = 0.0
        if len(triangles) > 0:
            for tri in triangles:
                p0 = fdm_coords[int(tri[0])]
                p1 = fdm_coords[int(tri[1])]
                p2 = fdm_coords[int(tri[2])]
                cross_prod = np.cross(p1 - p0, p2 - p0)
                true_surface_area += 0.5 * np.linalg.norm(cross_prod)
                
            st.success(f"**Calculated True Surface Area:** {true_surface_area:.2f} m²")
        else:
            st.error("❌ No triangles found in mesh. Cannot calculate surface area.")

        # 2. Document the Digitised Node State
        st.write("### 🖥️ Digitised Node State (Raw Coordinates)")
        
        node_data = []
        for i in range(len(fdm_coords)):
            node_data.append({
                "Node ID": i,
                "X": f"{fdm_coords[i][0]:.4f}",
                "Y": f"{fdm_coords[i][1]:.4f}",
                "Z": f"{fdm_coords[i][2]:.4f}",
            })
            
        if node_data:
            st.dataframe(pd.DataFrame(node_data), use_container_width=True)
        else:
            st.warning("No node data found.")

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
