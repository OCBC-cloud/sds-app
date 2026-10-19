# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# The 60/40 Layout with the 2-Step ENTER Flow.
#
# Top 60%: Fixed board (Blank -> 2D Plan -> 3D Viewer).
# Bottom 40%: Gliding input deck.
# =============================================================================

import streamlit as st

from ui.workshops._renderer import render_workshop
from ui.components.dome_cone_picker import render_dome_cone_picker
from ui.components.SDSe_multi_board import render_multi_board
from viewers.figures.dome_multi_cone import build_dome_multi_cone
from data.recipes.dome_multi_cone import DOME_MULTI_CONE_RECIPE


# =============================================================================
# RENDERERS
# =============================================================================

def _render_plan_board():
    """The 2D cone picker."""
    dome_diameter = float(st.session_state.get("ws_dm_dome_diameter", 18.0))
    n_x = int(st.session_state.get("ws_dm_meridians_x", 5))
    n_y = int(st.session_state.get("ws_dm_meridians_y", 5))

    picked_raw = st.session_state.get("ws_dm_picked_crossings", None)
    if picked_raw is None:
        picked = set()
    else:
        try:
            picked = set((int(i), int(j)) for (i, j) in picked_raw)
        except (TypeError, ValueError):
            picked = set()

    st.markdown(
        "<p style='color:#a8b8c8;margin-top:0;'>"
        "Click a crossing to place or remove a cone."
        "</p>",
        unsafe_allow_html=True,
    )

    new_picked = render_dome_cone_picker(
        dome_diameter=dome_diameter,
        n_x=n_x,
        n_y=n_y,
        picked=picked,
        key="dome_cone_picker_main",
    )
    st.session_state["ws_dm_picked_crossings"] = set(new_picked)


def _render_profile_board_stub():
    st.info("The Profile board is temporarily unavailable.")


def _render_3d_board():
    """The solved 3D figure."""
    build_dome_multi_cone()


# =============================================================================
# STATE HELPERS
# =============================================================================

def _get_phase():
    """Reads the phase directly from session state."""
    return st.session_state.get("ws_dm_phase", "blank")

def _set_phase(phase):
    st.session_state["ws_dm_phase"] = phase

def _clear_all():
    """Wipes all dome session state keys and goes back to blank."""
    keys_to_delete = [k for k in st.session_state.keys() if k.startswith("ws_dm_")]
    for k in keys_to_delete:
        del st.session_state[k]
    _set_phase("blank")
    st.rerun()


# =============================================================================
# THE FIXED TOP BOARD (FRAGMENT)
# =============================================================================

@st.fragment
def _render_top_board():
    """
    Renders the top 60% board. Wrapped in a fragment so it stays fixed
    and doesn't cause the whole page to scroll when inputs change.
    """
    phase = _get_phase()
    
    # We use a fixed height container. 
    with st.container(height=500, border=False):
        if phase == "blank":
            st.markdown(
                "<div style='height:480px; display:flex; align-items:center; "
                "justify-content:center; background-color:#0e1117; "
                "border-radius:8px; border:1px solid #333;'>"
                "<p style='color:#555; font-family:sans-serif;'>Awaiting Geometry...</p>"
                "</div>",
                unsafe_allow_html=True
            )
        
        elif phase in ("picking", "inputs"):
            # Stay on 2D Plan for both picking and finalizing inputs
            render_multi_board(
                key="dome",
                plan_renderer=_render_plan_board,
                view_3d_renderer=_render_3d_board,
                profile_renderer=_render_profile_board_stub,
                forced_board="plan"
            )
            
        elif phase == "solved":
            # Switch to 3D Viewer
            render_multi_board(
                key="dome",
                plan_renderer=_render_plan_board,
                view_3d_renderer=_render_3d_board,
                profile_renderer=_render_profile_board_stub,
                forced_board="view_3d"
            )


# =============================================================================
# PAGE ENTRY POINT
# =============================================================================

def render_dome_multi_cone():
    """
    Render the Dome Multi-Cone workshop.
    """
    phase = _get_phase()

    # 1. Render the Fixed Top Board
    _render_top_board()

    st.markdown("---")

    # 2. Render the Gliding Bottom Input Deck
    if phase == "blank":
        st.markdown("### Step 1: Define Geometry")
        st.caption("Set your base dimensions, then click below to start picking cones.")
        
        # We use an expander so the user can open/close the recipe
        with st.expander("Base Geometry", expanded=True):
            render_workshop(DOME_MULTI_CONE_RECIPE)
            
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🎯 Define Cone Positions", type="primary", use_container_width=True):
                _set_phase("picking")
                st.rerun()
        with col2:
            if st.button("🗑️ CLEAR ALL", use_container_width=True):
                _clear_all()

    elif phase == "picking":
        st.markdown("### Step 2: Pick Cones")
        st.caption("Tap the crossings on the Plan board above, then press ENTER.")
        
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("⚡ ENTER: Lock Cone Data", type="primary", use_container_width=True):
                if not st.session_state.get("ws_dm_picked_crossings"):
                    st.warning("Please pick at least one cone crossing on the Plan board.")
                else:
                    _set_phase("inputs")
                    st.rerun()
        with col2:
            if st.button("🗑️ CLEAR ALL", use_container_width=True):
                _clear_all()

    elif phase == "inputs":
        st.markdown("### Step 3: Finalize Inputs")
        st.caption("Your cone picks are locked. Adjust the remaining inputs, then press ENTER to solve.")
        
        with st.expander("Finalize Parameters", expanded=True):
            render_workshop(DOME_MULTI_CONE_RECIPE)
            
        curve_type = str(st.session_state.get("ws_dm_curve_type", "parabolic")).lower()
        if curve_type == "custom":
            st.warning("Custom (Draw Profile) falls back to parabolic until the picker is ready.")

        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🚀 ENTER: Generate 3D Model", type="primary", use_container_width=True):
                _set_phase("solved")
                st.rerun()
        with col2:
            if st.button("🗑️ CLEAR ALL", use_container_width=True):
                _clear_all()
                
        if st.button("⬅️ Go Back to Re-pick Cones", use_container_width=True):
            _set_phase("picking")
            st.rerun()

    elif phase == "solved":
        st.success("✅ 3D Model Solved.")
        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Edit Inputs", use_container_width=True):
                _set_phase("inputs")
                st.rerun()
        with col2:
            if st.button("🗑️ CLEAR ALL", use_container_width=True):
                _clear_all()


# =============================================================================
# END OF ui/workshops/dome_multi_cone.py
# =============================================================================
