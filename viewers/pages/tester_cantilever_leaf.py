# =============================================================================
# SDSe - Lab: Cantilever Leaf Tester (Universal Pipeline)
# =============================================================================
# 1. Geometry -> 2. Membrane Mesh -> 3. FDM Solver -> 4. Steel Frame ->
# 5. Universal Frame Analysis & Auto-Sizing.
# =============================================================================

import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
from scipy.spatial import Delaunay

from viewers.figures.cantilever_leaf_lab import (
    compute_lab_leaf_geometry,
    build_cantilever_leaf_lab_figure,
)
from viewers.figures._shared import apply_common_layout

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
    st.markdown('<div class="ctl-sub">Runs membrane form-finding, extracts forces, and auto-sizes the steel frame.</div>', unsafe_allow_html=True)

    # 1. Base Geometry
    geom = compute_lab_leaf_geometry()
    
    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.plotly_chart(build_cantilever_leaf_lab_figure(geom), use_container_width=True, config={"displayModeBar": False})

    with col_r:
        st.markdown("### Structural Auto-Sizing")
        st.write("Click below to solve membrane physics and size the steel.")
        
        if st.button("Run Structural Analysis", type="primary", use_container_width=True):
            with st.spinner("1. Meshing Membrane..."):
                # A. Build a simple membrane mesh from the rib tips to the spine
                b = geom["beam"]
                spine_pts = np.column_stack([b["x"], b["y"], b["z"]])
                mesh_pts = list(spine_pts)
                mesh_edges = []
                fixed_nodes = []
                
                # Add rib tips and connect them to the spine
                for rib in geom["ribs"]:
                    # Left rib
                    l_idx = len(mesh_pts)
                    mesh_pts.append(rib["left_tip"])
                    # Find nearest spine node
                    ax, ay, az = rib["attach"]
                    spine_idx = np.argmin(np.linalg.norm(spine_pts - np.array([ax, ay, az]), axis=1))
                    mesh_edges.append((spine_idx, l_idx))
                    fixed_nodes.append(spine_idx) # fix the spine
                    
                    # Right rib
                    r_idx = len(mesh_pts)
                    mesh_pts.append(rib["right_tip"])
                    mesh_edges.append((spine_idx, r_idx))
                
                # Add perimeter connecting left tips to right tips
                n_ribs = len(geom["ribs"])
                for i in range(n_ribs - 1):
                    l1 = len(spine_pts) + i*2
                    l2 = len(spine_pts) + (i+1)*2
                    r1 = l1 + 1
                    r2 = l2 + 1
                    mesh_edges.append((l1, l2))
                    mesh_edges.append((r1, r2))
                
                pts_array = np.array(mesh_pts)
                fixed_nodes = list(set(fixed_nodes))
                
            with st.spinner("2. Running FDM Membrane Physics..."):
                # B. Run FDM Solver
                # We use a uniform force density for the membrane edges
                q = np.full(len(mesh_edges), 5000.0) # 5kN/m tension
                fdm_res = solve_fdm(pts_array, mesh_edges, fixed_nodes, q)
                
                # The FDM returns reactions in kN. We need them in N for the steel solver.
                reactions_kN = fdm_res["reactions"]
                reactions_N = reactions_kN * 1000.0
                
            with st.spinner("3. Building Steel Frame & Applying Loads..."):
                # C. Build Steel Frame
                frame_data = build_cantilever_frame()
                
                # D. Map membrane reactions to the steel frame
                # For this simple test, we map the FDM fixed nodes (spine) to the frame nodes
                applied_loads = {}
                for i, f_node in enumerate(fixed_nodes):
                    # The FDM reaction is the force the fabric pulls on the spine
                    # (Note: FDM reactions are already negative of the applied load)
                    applied_loads[f_node] = -reactions_N[f_node]
                    
            with st.spinner("4. Running 3D Steel Solver & Auto-Sizing..."):
                # E. Analyze and Size
                result = analyze_and_size_frame(
                    frame_data=frame_data,
                    applied_loads=applied_loads,
                    grade="S355",
                    family="CHS"
                )
                
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

        st.markdown("---")
        st.markdown("### Geometry Dump")
        st.markdown(f"<div class='ctl-card ctl-mono'>Outreach: 5.0 m\nRibs: 3 pairs\nColumn: 6.0 m</div>", unsafe_allow_html=True)

    if st.button("Back to Lab", key="tcl_back", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()
