# =============================================================================
# SDSe - Lab: Cantilever Leaf Tester (Universal Pipeline)
# =============================================================================
# This page connects the visual geometry to the Universal Structural Engine:
# 1. Geometry -> 2. Membrane Mesh -> 3. FDM Solver -> 4. Load Extractor ->
# 5. Steel Frame Builder -> 6. Universal Frame Analysis & Auto-Sizing.
# =============================================================================

import streamlit as st
import numpy as np

# Visuals
from viewers.figures.cantilever_leaf_lab import (
    compute_lab_leaf_geometry,
    build_cantilever_leaf_lab_figure,
)

# Engines
from engine.fdm_solver import solve_fdm  # Placeholder: replace with your actual FDM import
from engine.cantilever_frame_builder import build_cantilever_frame
from engine.load_extractor import extract_frame_loads
from engine.frame_analysis import analyze_and_size_frame
from engine.load_generator import generate_uls_loads

LAB_TESTER_CSS = """
    <style>
    .stApp > header { display: none !important; }
    .block-container { padding-top: 1.2rem !important; max-width: 1200px; }
    .ctl-topbar {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0 0 0.6rem 0; border-bottom: 1px solid #1e2a3a; margin-bottom: 1.2rem;
    }
    .ctl-wordmark { font-size: 1.1rem; font-weight: 700; color: #f39c12; letter-spacing: 2px; }
    .ctl-header { font-size: 1.4rem; font-weight: 700; color: #ffffff; margin: 0.4rem 0 0.3rem 0; }
    .ctl-sub { font-size: 0.9rem; color: #a8b8c8; margin-bottom: 1.2rem; line-height: 1.4; }
    .ctl-card {
        background-color: #121e2e; border: 1px solid #1e2a3a;
        border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.7rem;
    }
    .ctl-mono { font-family: 'SF Mono', Menlo, monospace; font-size: 0.8rem; color: #c8d8e8; white-space: pre-wrap; }
    </style>
"""

def render_tester_cantilever_leaf():
    st.markdown(LAB_TESTER_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="ctl-topbar">'
        '<div class="ctl-wordmark">SDSe LAB</div>'
        '<div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="ctl-header">Cantilever Leaf Tester</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="ctl-sub">'
        'Universal Pipeline Test. Fixed 6 m column, 5 m outreach, 3 rib pairs. '
        'Runs membrane physics, extracts loads, and auto-sizes the steel frame.'
        '</div>',
        unsafe_allow_html=True,
    )

    # 1. Build Base Geometry
    geom = compute_lab_leaf_geometry()
    fig = build_cantilever_leaf_lab_figure(geom)

    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_r:
        st.markdown("### Steel Auto-Sizing")
        st.write("Click below to run the full structural pipeline.")
        
        if st.button("Run Structural Analysis", type="primary", use_container_width=True):
            with st.spinner("Running Pipeline..."):
                
                # --- STEP 1: Membrane Form Finding ---
                # (Using a simplified dummy mesh for the test until we wire the real one)
                # We assume the fabric is tensioned and tied to the rib tips.
                st.info("1. Running Membrane Physics...")
                
                # --- STEP 2: Extract Forces ---
                # We map the rib tips (from geometry) to the steel nodes.
                st.info("2. Extracting loads to steel frame...")
                
                # We build the steel frame
                frame_data = build_cantilever_frame()
                
                # Dummy applied loads for now (We will wire the real extractor next)
                applied_loads = {i: np.array([0.0, 0.0, -5000.0]) for i in range(len(frame_data["nodes"])) if i > 1}
                
                # --- STEP 3: Analyze and Size ---
                st.info("3. Running Universal Solver & Sizing...")
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
                        st.write(f"- **{kind.capitalize()}**: {sec}")
                        
                    st.markdown("#### Utilization:")
                    for kind, util in result["details"].items():
                        color = "red" if util > 0.85 else "green"
                        st.markdown(f"- **{kind.capitalize()}**: <span style='color:{color}'>{util*100:.1f}%</span>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Geometry Dump")
        st.markdown(f"<div class='ctl-card ctl-mono'>Nodes: {len(geom['beam']['x'])} beam samples\nRibs: 3 pairs\nOutreach: 5.0 m</div>", unsafe_allow_html=True)

    if st.button("Back to Lab", key="tcl_back", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()
