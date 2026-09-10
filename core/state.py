# =============================================================================
# SDSe - Session State Helpers
# =============================================================================
# Initialises session state and provides reset helpers.
#
# Contents:
#   init_session_state()             - set defaults on first run
#   clear_previous_project_data()    - reset project-specific state
#
# Usage:
#   from core.state import init_session_state, clear_previous_project_data
# =============================================================================

import streamlit as st


# =============================================================================
# INITIALISE SESSION STATE
# =============================================================================

def init_session_state():
    """Set default session state on first run. Safe to call every rerun."""
    defaults = {
        "page": "dashboard",
        "project_registered": False,
        "project_info": {},
        "typology": None,
        "params": {},
        "locked": False,
        "comments": "",
        "saved_projects": [],
        "design_results": {},
        "bq": {},
        "structure_inputs": {},
        "rotation_angle": 0,
        "materials": {
            "standard": "EU",
            "material_type": "Steel",
            "section_type": "CHS",
            "fabric_type": "PVC-coated Polyester",
            "cable_type": "6x19 Galvanized",
            "tie_down_vertical_angle": 45,
            "tie_down_horizontal_spread": 30,
            "shape_type": "parabolic",
            "member_type": "single_beam",
            "truss_type": "warren",
            "num_bays": 2,
            "prestress_level": "medium",
            "joint_type": "bolted",
            "country": "Malaysia",
            "dome_frequency": 6,
            "dome_radius": 20,
            "dome_height": 20,
            "curve_type": "parabolic",
            "tie_down_system": "cable",
            "truss_depth_mode": "auto",
            "truss_depth_manual": 1.0,
            "fabric_sag": 30,
        },
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# CLEAR PROJECT DATA
# =============================================================================

def clear_previous_project_data():
    """Reset project-specific state without wiping saved projects."""
    st.session_state.design_results = {}
    st.session_state.bq = {}
    st.session_state.params = {}
    st.session_state.comments = ""
    st.session_state.locked = False
    st.session_state.typology = None
    st.session_state.structure_inputs = {}
    st.session_state.rotation_angle = 0

    # Preserve user's choice of standard and country from current session
    current_standard = st.session_state.materials.get("standard", "EU")
    current_country = st.session_state.materials.get("country", "Malaysia")

    st.session_state.materials = {
        "standard": current_standard,
        "material_type": "Steel",
        "section_type": "CHS",
        "fabric_type": "PVC-coated Polyester",
        "cable_type": "6x19 Galvanized",
        "tie_down_vertical_angle": 45,
        "tie_down_horizontal_spread": 30,
        "shape_type": "parabolic",
        "member_type": "single_beam",
        "truss_type": "warren",
        "num_bays": 2,
        "prestress_level": "medium",
        "joint_type": "bolted",
        "country": current_country,
        "dome_frequency": 6,
        "dome_radius": 20,
        "dome_height": 20,
        "curve_type": "parabolic",
        "tie_down_system": "cable",
        "truss_depth_mode": "auto",
        "truss_depth_manual": 1.0,
        "fabric_sag": 30,
    }
