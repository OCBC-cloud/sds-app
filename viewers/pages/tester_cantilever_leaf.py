import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from viewers.figures.cantilever_leaf_lab import compute_lab_leaf_geometry, build_cantilever_leaf_lab_figure
from engine.cantilever_leaf_test_mesh import build_leaf_test_mesh
from engine.form_finding_test import solve_fdm
from engine.cantilever_frame_builder import build_cantilever_frame
from engine.frame_analysis import analyze_and_size_frame
from viewers.figures._shared import apply_common_layout

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
    st.markdown('<div class="ctl-header">Cantilever Leaf — Visual Bowing Test</div>', unsafe_allow_html=True)
    
    # Number Inputs
    st.markdown("### Leaf Geometry Inputs")
    col1, col2, col3 = st.columns(3)
    with col1:
        col_h = st.number_input("Column Height (m)", value=6.0, step=0.5, format="%.2f")
        outreach = st.number_input("Outreach (m)", value=5.0, step=0.5, format="%.2f")
        half_w = st.number_input("Middle Half-Width (m)", value=2.0, step=0.5, format="%.2f")
    with col2:
        tilt = st.number_input("Rib Tilt (deg)", value=0.0, step=1.0, format="%.1f")
        arc_r = st.number_input("Arc Radius (m)", value=1.0, step=0.1, format="%.2f")
    with col3:
        strut_j = st.number_input("Strut Joint (m)", value=3.0, step=0.5, format="%.2f")
        strut_a = st.number_input("Strut Angle (deg)", value=42.0, step=1.0, format="%.1f")
        n_ribs = st.number_input("Rib Pairs", value=3, step=1)

    st.markdown("### Pretension Forces (kN)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        mem_tension = st.number_input("Membrane Pretension (kN)", value=2.0, step=0.5, format="%.2f")
    with col_t2:
        cable_tension = st.number_input("Cable Pretension (kN)", value=5.0, step=0.5, format="%.2f")
        
    attached_to_spine = st.toggle("Attach Membrane to Main Spine", value=True)

    geom = compute_lab_leaf_geometry(col_h, outreach, half_w, tilt, arc_r, strut_j, strut_a, n_ribs)
    
    col_l, col_r = st.columns([2, 1])
    
    plot_placeholder = col_l.empty()

    with plot_placeholder:
        st.plotly_chart(build_cantilever_leaf_lab_figure(geom), use_container_width=True, config={"displayModeBar": False})

    with col_r:
        st.markdown("### Structural Auto-Sizing")
        if st.button("Run Real FDM & Size Steel", type="primary", use_container_width=True):
            with st.spinner("1. Building Test Mesh..."):
                mesh_data = build_leaf_test_mesh(
                    geom, 
                    membrane_tension=mem_tension * 1000.0, 
                    cable_tension=cable_tension * 1000.0,
                    attached_to_spine=attached_to_spine
                )
                
            with st.spinner("2. Running FDM Solver..."):
                fdm_res = solve_fdm(
                    points=mesh_data["points_3d"], 
                    edges=mesh_data["edges"], 
                    fixed_indices=mesh_data["fixed_indices"], 
                    force_densities=mesh_data["q"]
                )
                coords = fdm_res["coordinates"]
                reactions_N = fdm_res["reactions"] * 1000.0

            # --- UPDATE THE 3D VISUAL TO SHOW THE BOW ---
            with plot_placeholder:
                fig = go.Figure()
                
                # 1. Draw the settled membrane surface
                # We only take the original 24x24 grid nodes for the surface
                X = geom["membrane"]["X"]
                n_u, n_v = X.shape
                n_grid = n_u * n_v
                
                X_settled = coords[:n_grid, 0].reshape((n_u, n_v))
                Y_settled = coords[:n_grid, 1].reshape((n_u, n_v))
                Z_settled = coords[:n_grid, 2].reshape((n_u, n_v))
                
                fig.add_trace(go.Surface(
                    x=X_settled, y=Y_settled, z=Z_settled,
                    colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
                    opacity=0.5, showscale=False, hoverinfo="skip"
                ))

                # 2. Draw the settled perimeter cables (Left and Right edges)
                fig.add_trace(go.Scatter3d(
                    x=X_settled[:, 0], y=Y_settled[:, 0], z=Z_settled[:, 0],
                    mode="lines", line=dict(color="#00ffff", width=6), name="Bowed Cable (L)"
                ))
                fig.add_trace(go.Scatter3d(
                    x=X_settled[:, -1], y=Y_settled[:, -1], z=Z_settled[:, -1],
                    mode="lines", line=dict(color="#00ffff", width=6), name="Bowed Cable (R)"
                ))

                # 3. Draw the rigid steel frame
                b = geom["beam"]
                fig.add_trace(go.Scatter3d(x=b["x"], y=b["y"], z=b["z"], mode="lines", line=dict(color="#FF6B6B", width=8), name="Main beam"))
                fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[0,col_h], mode="lines", line=dict(color="#2ecc71", width=10), name="Column"))
                
                for rib in geom["ribs"]:
                    ax, ay, az = rib["attach"]
                    lx, ly, lz = rib["left_tip"]
                    rx, ry, rz = rib["right_tip"]
                    fig.add_trace(go.Scatter3d(x=[lx, ax, rx], y=[ly, ay, ry], z=[lz, az, rz], mode="lines", line=dict(color="#3498db", width=3), showlegend=False))
                
                sa = geom["strut"]["attach"]
                sb = geom["strut"]["base"]
                fig.add_trace(go.Scatter3d(x=[sa[0], sb[0]], y=[sa[1], sb[1]], z=[sa[2], sb[2]], mode="lines", line=dict(color="#e67e22", width=4), name="Strut"))

                st.plotly_chart(apply_common_layout(fig, col_h), use_container_width=True, config={"displayModeBar": False})

            # --- DIGITISED REPORT ---
            st.markdown("### 📊 Digitised Nodes Report")
            boundary_ids = []
            for i in range(n_u):
                boundary_ids.append(i * n_v + 0)
                boundary_ids.append(i * n_v + (n_v - 1))
            sample_ids = boundary_ids[::4] 
            
            report_data = []
            for idx in sample_ids:
                orig = mesh_data["points_3d"][idx]
                settled = coords[idx]
                report_data.append({
                    "Node": idx,
                    "Orig Y": round(orig[1], 3), "Settled Y": round(settled[1], 3), "Δ Y": round(settled[1] - orig[1], 3),
                    "Orig Z": round(orig[2], 3), "Settled Z": round(settled[2], 3), "Δ Z": round(settled[2] - orig[2], 3),
                })
            st.dataframe(pd.DataFrame(report_data), use_container_width=True, hide_index=True)

            with st.spinner("3. Auto-Sizing..."):
                frame_data = build_cantilever_frame(col_h, outreach, half_w, tilt, arc_r, strut_j, strut_a, n_ribs)
                applied_loads = {}
                steel_nodes = frame_data["nodes"]
                for i in range(len(coords)):
                    if i in mesh_data["fixed_indices"]:
                        mem_pos = coords[i]
                        dists = np.linalg.norm(steel_nodes - mem_pos, axis=1)
                        s_idx = np.argmin(dists)
                        force = -reactions_N[i]
                        if s_idx not in applied_loads:
                            applied_loads[s_idx] = np.zeros(3)
                        applied_loads[s_idx] += force

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
