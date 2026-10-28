import streamlit as st
import numpy as np
import math

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
    st.markdown('<div class="ctl-header">Cantilever Leaf — True Perimeter Cable</div>', unsafe_allow_html=True)
    
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
        if st.button("Run True Cable Analysis", type="primary", use_container_width=True):
            with st.spinner("1. Extracting Outer Boundary..."):
                
                # 1. Build the perimeter loop by following the outer edge of the fabric
                # We trace the RIGHT side from column to tip, then LEFT side from tip to column.
                m = geom["membrane"]
                X, Y, Z = m["X"], m["Y"], m["Z"]
                
                # Right boundary (max Y at each X station)
                right_boundary = []
                for i in range(X.shape[0]):
                    j_max = np.argmax(Y[i, :])
                    right_boundary.append((X[i, j_max], Y[i, j_max], Z[i, j_max]))
                
                # Left boundary (min Y at each X station)
                left_boundary = []
                for i in range(X.shape[0]):
                    j_min = np.argmin(Y[i, :])
                    left_boundary.append((X[i, j_min], Y[i, j_min], Z[i, j_min]))
                
                # Combine to make a continuous loop: Right (start to end) -> Left (end to start)
                perimeter_pts = right_boundary + list(reversed(left_boundary))
                perimeter_loop = np.array(perimeter_pts)
                
                # Subdivide for smooth cable bowing
                subdiv = []
                for i in range(len(perimeter_loop)):
                    a = perimeter_loop[i]
                    b = perimeter_loop[(i + 1) % len(perimeter_loop)]
                    for k in range(3): # 3 points per segment
                        subdiv.append(a + (b - a) * (k / 3.0))
                perimeter_loop = np.array(subdiv)
                
                # We fix ALL perimeter nodes because they represent the tensioned cable
                anchor_idx = list(range(len(perimeter_loop)))
                
                # Find the indices of the actual rib tips and beam tip to ensure they are anchored
                # (Optional: we could assign structural anchors to specific steel points)
                fixed = anchor_idx

            with st.spinner("2. Running FDM Solver on Cable..."):
                # 2. Build edges along the perimeter (a closed loop)
                n_p = len(perimeter_loop)
                edges = []
                for i in range(n_p):
                    edges.append((i, (i + 1) % n_p))
                
                # Cable tension (q) - very high for perimeter
                q = np.full(len(edges), 5000.0) # 5.0 kN
                
                # Run FDM (Notice we pass the points twice to give it a starting shape)
                fdm_res = solve_fdm(perimeter_loop, edges, fixed, q)
                coords = fdm_res["coordinates"]
                reactions_N = fdm_res["reactions"] * 1000.0

            with st.spinner("3. Transferring Cable Forces to Steel..."):
                frame_data = build_cantilever_frame(col_h, outreach, half_w, tilt, arc_r, strut_j, strut_a, n_ribs)
                
                applied_loads = {}
                steel_nodes = frame_data["nodes"]
                
                # Map the perimeter reactions directly to the steel frame
                for i in range(len(coords)):
                    if i in fixed:
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
