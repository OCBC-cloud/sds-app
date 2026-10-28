import streamlit as st
import numpy as np

from viewers.figures.cantilever_leaf_lab import compute_lab_leaf_geometry, build_cantilever_leaf_lab_figure
from engine.cantilever_leaf_test_mesh import build_leaf_test_mesh
from engine.form_finding_test import solve_fdm
from engine.cantilever_frame_builder import build_cantilever_frame
from engine.frame_analysis import analyze_and_size_frame

LAB_TESTER_CSS = """
    <style>
    .stApp > header { display: none !important; }
    .block-container { padding-top: 1.2rem !important; max-width: 1200px; }
    .ctl-topbar { display: flex; justify-content: space-between; align-items: center; padding: 0 0 0.6rem 0; border-bottom: 1px solid #1e2a3a; margin-bottom: 1.2rem; }
    .ctl-wordmark { font-size: 1.1rem; font-weight: 700; color: #f39c12; letter-spacing: 2px; }
    .ctl-header { font-size: 1.4rem; font-weight: 700; color: #ffffff; margin: 0.4rem 0 0.3rem 0; }
    .ctl-sub { font-size: 0.9rem; color: #a8b8c8; margin-bottom: 1.2rem; line-height: 1.4; }
    </style>
"""

def render_tester_cantilever_leaf():
    st.markdown(LAB_TESTER_CSS, unsafe_allow_html=True)
    st.markdown('<div class="ctl-topbar"><div class="ctl-wordmark">SDSe LAB</div><div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="ctl-header">Cantilever Leaf — Real Mesh & Cable</div>', unsafe_allow_html=True)
    
    # Sliders
    st.markdown("### Leaf Geometry Inputs")
    col1, col2, col3 = st.columns(3)
    with col1:
        col_h = st.slider("Column Height (m)", 3.0, 12.0, 6.0, 0.5)
        outreach = st.slider("Outreach (m)", 2.0, 15.0, 5.0, 0.5)
        half_w = st.slider("Middle Half-Width (m)", 0.5, 5.0, 2.0, 0.5)
    with col2:
        tilt = st.slider("Rib Tilt (deg)", -45.0, 45.0, 0.0, 1.0)
        arc_r = st.slider("Arc Radius (m)", 0.0, 5.0, 1.0, 0.1)
    with col3:
        strut_j = st.slider("Strut Joint (m)", 1.0, col_h, 3.0, 0.5)
        strut_a = st.slider("Strut Angle (deg)", 20.0, 80.0, 42.0, 1.0)
        n_ribs = st.slider("Rib Pairs", 1, 8, 3, 1)

    geom = compute_lab_leaf_geometry(col_h, outreach, half_w, tilt, arc_r, strut_j, strut_a, n_ribs)
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.plotly_chart(build_cantilever_leaf_lab_figure(geom), use_container_width=True, config={"displayModeBar": False})

    with col_r:
        st.markdown("### Structural Auto-Sizing")
        if st.button("Run Real FDM & Size Steel", type="primary", use_container_width=True):
            with st.spinner("1. Building Test Mesh & Cable Boundary..."):
                mesh_data = build_leaf_test_mesh(geom)
                
            with st.spinner("2. Running FDM Solver..."):
                fdm_res = solve_fdm(
                    points=mesh_data["points_3d"], 
                    edges=mesh_data["edges"], 
                    fixed_indices=mesh_data["fixed_indices"], 
                    force_densities=mesh_data["q"]
                )
                coords = fdm_res["coordinates"]
                reactions_N = fdm_res["reactions"] * 1000.0

            with st.spinner("3. Transferring Loads to Steel..."):
                frame_data = build_cantilever_frame(col_h, outreach, half_w, tilt, arc_r, strut_j, strut_a, n_ribs)
                
                applied_loads = {}
                steel_nodes = frame_data["nodes"]
                
                # Map membrane reactions to nearest steel nodes
                for i in range(len(coords)):
                    if i in mesh_data["fixed_indices"]:
                        mem_pos = coords[i]
                        dists = np.linalg.norm(steel_nodes - mem_pos, axis=1)
                        s_idx = np.argmin(dists)
                        
                        force = -reactions_N[i]
                        if s_idx not in applied_loads:
                            applied_loads[s_idx] = np.zeros(3)
                        applied_loads[s_idx] += force

            with st.spinner("4. Auto-Sizing..."):
                result = analyze_and_size_frame(frame_data, applied_loads, grade="S355", family="CHS")
                
                if "error" in result:
                    st.error(f"Sizing Failed: {result['error']}")
                else:
                    st.success(f"Sizing Converged in {result.get('iterations', '?')} iterations!")
                    st.markdown("#### Selected Sections:")
                    for kind, sec in result["sections"].items():
                        st.write(f"- **{kind.capitalize()}**: `{sec}`")
                    st.markdown("#### Utilization:")
                    for kind, util in result["details"].items():
                        color = "#ff4b4b" if util > 0.85 else "#00cc66"
                        st.markdown(f"- **{kind.capitalize()}**: <span style='color:{color}'>{util*100:.1f}%</span>", unsafe_allow_html=True)

    if st.button("Back to Lab", key="tcl_back", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()
