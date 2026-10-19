# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# The new state-machine driven UI.
#
# Top 60%: A static board that switches views based on the "phase":
#   "blank"   -> Shows a waiting message.
#   "picking" -> Shows the Plan view (cone picker).
#   "solved"  -> Shows the 3D View (the solver).
#
# Bottom 40%: Gliding input deck.
#   The recipe inputs remain persistent here. The user can tweak values
#   and hit ENTER again without losing their cone picks.
#
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
    
    # If the picks changed, we update the state, but we DON'T force a rerun.
    # The user will hit the ENTER button to solve.
    st.session_state["ws_dm_picked_crossings"] = set(new_picked)


def _render_profile_board_stub():
    st.info("The Profile board is temporarily unavailable.")


def _render_3d_board():
    """The solved 3D figure."""
    build_dome_multi_cone()


# =============================================================================
# UI STATE HELPERS
# =============================================================================

def _get_phase():
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
# PAGE ENTRY POINT
# =============================================================================

def render_dome_multi_cone():
    """
    Render the Dome Multi-Cone workshop.
    """
    phase = _get_phase()

    # =========================================================================
    # TOP 60%: THE STATIC BOARD
    # =========================================================================
    # We wrap this in a container to visually separate it.
    with st.container():
        if phase == "blank":
            st.info("👋 Welcome. Adjust the inputs below and start picking cones to see the 3D model.")
        
        elif phase == "picking":
            # Lock to Plan view
            render_multi_board(
                key="dome",
                plan_label="Plan",
                profile_label="Profile",
                view_3d_label="3D View",
                plan_renderer=_render_plan_board,
                profile_renderer=_render_profile_board_stub,
                view_3d_renderer=_render_3d_board,
                forced_board="plan"
            )
            
        elif phase == "solved":
            # Lock to 3D view
            render_multi_board(
                key="dome",
                plan_label="Plan",
                profile_label="Profile",
                view_3d_label="3D View",
                plan_renderer=_render_plan_board,
                profile_renderer=_render_profile_board_stub,
                view_3d_renderer=_render_3d_board,
                forced_board="view_3d"
            )

    st.markdown("---")

    # =========================================================================
    # BOTTOM 40%: THE INPUT DECK
    # =========================================================================
    
    # 1. The Recipe
    render_workshop(DOME_MULTI_CONE_RECIPE)

    curve_type = str(st.session_state.get("ws_dm_curve_type", "parabolic")).lower()
    if curve_type == "custom":
        st.warning(
            "You have selected **Custom (Draw Profile)**. The custom "
            "elevation picker is not yet available. The 3D view will "
            "fall back to the default parabolic curve."
        )

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # 2. The State Machine Controls
    if phase == "blank" or phase == "picking":
        st.markdown("### 🎯 Pick Cones & Solve")
        st.caption("Click the crossings on the Plan board above, then press Generate.")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("⚡ ENTER: Generate 3D Model", type="primary", use_container_width=True):
                # If no picks were made, default to picking phase
                if not st.session_state.get("ws_dm_picked_crossings"):
                    st.warning("Please pick at least one cone crossing on the Plan board.")
                else:
                    _set_phase("solved")
                    st.rerun()
        with col2:
            if st.button("🗑️ CLEAR ALL", use_container_width=True):
                _clear_all()

    elif phase == "solved":
        st.success("✅ 3D Model Solved.")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Edit Inputs & Cones", use_container_width=True):
                _set_phase("picking")
                st.rerun()
        with col2:
            if st.button("🗑️ CLEAR ALL", use_container_width=True):
                _clear_all()

    # 3. Auto-advance to picking if the user changes the grid size
    # (This is a gentle nudge, not a forceful reset)
    if phase == "blank":
        n_x = int(st.session_state.get("ws_dm_meridians_x", 5))
        n_y = int(st.session_state.get("ws_dm_meridians_y", 5))
        if n_x > 0 and n_y > 0:
             # We wait for the user to click "ENTER" or interact, but we don't force it.
             pass


# =============================================================================
# END OF ui/workshops/dome_multi_cone.py
# =============================================================================
