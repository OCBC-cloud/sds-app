import streamlit as st
import numpy as np

from viewers.figures.cantilever_leaf_lab import compute_lab_leaf_geometry, build_cantilever_leaf_lab_figure
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
    .ctl-card { background-color: #121e2e; border: 1px solid #1e2a3a; border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.7rem; }
    .ctl-mono { font-family: 'SF Mono', Menlo, monospace; font-size: 0.8rem; color: #c8d8e8; white-space: pre-wrap; }
    </style>
"""

def render_tester_cantilever_leaf():
    st.markdown(LAB_TESTER_CSS, unsafe_allow_html=True)
    st.markdown('<div class="ctl-topbar"><div class="ctl-wordmark">SDSe LAB</div><div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="ctl-header">Cantilever Leaf — Universal Structural Test</div>', unsafe_allow_html=True)
    
    # Sliders moved to the main page layout!
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
    
    st.markdown("---")
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.plotly_chart(build_cantilever_leaf_lab_figure(geom), use_container_width=True, config={"displayModeBar": False})

    with col_r:
        st.markdown("### Structural Auto-Sizing")
        if st.button("Run Structural Analysis", type="primary", use_container_width=True):
            with st.spinner("Running Pipeline..."):
                # 1. FDM (Simplified)
                b = geom["beam"]
                spine_pts = np.column_stack([b["x"], b["y"], b["z"]])
                mesh_pts = list(spine_pts)
                mesh_edges = []
                fixed_nodes = []
                
                for rib in geom["ribs"]:
                    l_idx = len(mesh_pts)
                    mesh_pts.append(rib["left_tip"])
                    ax, ay, az = rib["attach"]
                    spine_idx = np.argmin(np.linalg.norm(spine_pts - np.array([ax, ay, az]), axis=1))
                    mesh_edges.append((spine_idx, l_idx))
                    fixed_nodes.append(spine_idx)
                    
                    r_idx = len(mesh_pts)
                    mesh_pts.append(rib["right_tip"])
                    mesh_edges.append((spine_idx, r_idx))
                
                for i in range(len(geom["ribs"]) - 1):
                    l1 = len(spine_pts) + i*2
                    l2 = len(spine_pts) + (i+1)*2
                    mesh_edges.extend([(l1, l2), (l1+1, l2+1)])
                
                q = np.full(len(mesh_edges), 5000.0)
                fdm_res = solve_fdm(np.array(mesh_pts), mesh_edges, list(set(fixed_nodes)), q)
                reactions_N = fdm_res["reactions"] * 1000.0
                
                # 2. Build Frame
                frame_data = build_cantilever_frame(col_h, outreach, half_w, tilt, arc_r, strut_j, strut_a, n_ribs)
                
                # 3. Apply Loads
                applied_loads = {}
                for i, f_node in enumerate(list(set(fixed_nodes))):
                    applied_loads[f_node] = -reactions_N[f_node]
                
                # Add Wind Load to Rib Tips (1.0 kN downward for testing)
                for elem in frame_data["elements"]:
                    if elem["kind"] == "rib":
                        tip_node = elem["b"]
                        applied_loads[tip_node] = np.array([0.0, 0.0, -1000.0])
                
                # 4. Size
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
