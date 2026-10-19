# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# 60/40 Layout with the 2-Step ENTER Flow.
#
# Phase "blank":   Blank 60% board. Inputs visible below.
# Phase "picking": 2D Plan board. User picks cones and presses ENTER #1.
# Phase "inputs":  Plan remains visible (locked). Rest of inputs appear.
#                  User reviews and presses ENTER #2.
# Phase "solved":  3D Viewer board.
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
    keys_to_delete = [k for k in st.session_state.keys() if k.startswith("ws_dm_")]
    for k in keys_to_delete:
        del st.session_state[k]
    _set_phase("blank")
    st.rerun()


# =============================================================================
# PAGE ENTRY POINT
# =============================================================================

def render_dome_multi_cone():
    """
    Render the Dome Multi-Cone workshop.
    """
    phase = _get_phase()

    # =========================================================================
    # TOP 60%: THE FIXED BOARD
    # =========================================================================
    # We use a fixed-height container. Streamlit locks this area.
    with st.container(height=550, border=False):
        
        if phase == "blank":
            st.markdown(
                "<div style='height:500px; display:flex; align-items:center; "
                "justify-content:center; background-color:#0e1117; "
                "border-radius:8px; border:1px solid #333;'>"
                "<p style='color:#555; font-family:sans-serif;'>Awaiting Geometry...</p>"
                "</div>",
                unsafe_allow_html=True
            )
        
        elif phase == "picking" or phase == "inputs":
            # In picking and inputs, we stay on the Plan board
            render_multi_board(
                key="dome",
                plan_renderer=_render_plan_board,
                view_3d_renderer=_render_3d_board,
                profile_renderer=_render_profile_board_stub,
                forced_board="plan"
            )
            
        elif phase == "solved":
            # In solved, we switch to the 3D board
            render_multi_board(
                key="dome",
                plan_renderer=_render_plan_board,
                view_3d_renderer=_render_3d_board,
                profile_renderer=_render_profile_board_stub,
                forced_board="view_3d"
            )

    st.markdown("---")

    # =========================================================================
    # BOTTOM 40%: THE GLIDING INPUT DECK
    # =========================================================================
    
    if phase == "blank":
        st.markdown("### Step 1: Define Geometry")
        st.caption("Set the number of meridians to begin selecting cone positions.")
        
        # Show only the basic geometry first
        render_workshop(DOME_MULTI_CONE_RECIPE)
        
        # Automatically flip to picking when meridians exist
        n_x = int(st.session_state.get("ws_dm_meridians_x", 0))
        n_y = int(st.session_state.get("ws_dm_meridians_y", 0))
        if n_x > 0 and n_y > 0:
            _set_phase("picking")
            st.rerun()

    elif phase == "picking":
        st.markdown("### Step 1: Pick Cones")
        st.caption("Tap the crossings on the Plan board above, then press ENTER to collect the data.")
        
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("⚡ ENTER: Collect Cone Data", type="primary", use_container_width=True):
                if not st.session_state.get("ws_dm_picked_crossings"):
                    st.warning("Please pick at least one cone crossing on the Plan board.")
                else:
                    _set_phase("inputs")
                    st.rerun()
        with col2:
            if st.button("🗑️ CLEAR", use_container_width=True):
                _clear_all()

    elif phase == "inputs":
        st.markdown("### Step 2: Finalize Inputs")
        st.caption("Your cone picks are locked. Adjust the remaining inputs, then press ENTER to solve.")
        
        # Show the full recipe for final adjustments
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
            if st.button("🗑️ CLEAR", use_container_width=True):
                _clear_all()
                
        # Allow going back to re-pick
        if st.button("⬅️ Re-pick Cones", use_container_width=True):
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
