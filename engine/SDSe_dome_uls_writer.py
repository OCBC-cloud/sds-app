# =============================================================================
# SDSe Engine - Dome ULS Writer (Small Wrapper)
# =============================================================================

import streamlit as st
from engine.SDSe_uls_solver import run_uls_analysis

def write_dome_uls_to_session(built, fdm_coords, dome_diameter, crown_height, fabric_type, fabric_grade):
    """
    Calculates the ULS forces and saves them to session state for results.py.
    """
    if built is None or fdm_coords is None:
        return
        
    try:
        uls_results = run_uls_analysis(
            built=built,
            fdm_coords=fdm_coords,
            dome_diameter=dome_diameter,
            crown_height=crown_height,
            fabric_type=fabric_type,
            fabric_grade=fabric_grade
        )
        st.session_state["ws_dome_uls_results"] = uls_results
    except Exception as e:
        st.session_state["ws_dome_uls_results"] = {"error": str(e)}
