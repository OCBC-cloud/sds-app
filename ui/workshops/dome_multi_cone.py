# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# 60/40 Split Layout with locked top board.
# =============================================================================

import streamlit as st

from ui.workshops._renderer import render_workshop
from ui.components.dome_cone_picker import render_dome_cone_picker
from ui.components.SDSe_multi_board import render_multi_board
from viewers.figures.dome_multi_cone import build_dome_multi_cone
from data.recipes.dome_multi_cone import DOME_MULTI_CONE_RECIPE


# =============================================================================
# CSS FOR LOCKED 60/40 LAYOUT
# =============================================================================

def _apply_layout_css():
    st.markdown(
        """
        <style>
        /* Hide the default Streamlit header to save space */
        header {visibility: hidden;}
        
        /* Make the main block scrollable if needed */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            max-height: 100vh;
        }
        
        /* Fixed-height container for the top board */
        .fixed-board-container {
            height: 55vh;
            min-height: 400px;
            background-color: #0e1117;
            border: 1px solid #333;
            border-radius: 8px;
            margin-bottom: 1rem;
            overflow: hidden;
        }
        
        /* Scrollable container for the bottom inputs */
        .scrollable-inputs {
            height: 40vh;
            overflow-y: auto;
            padding-right: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


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
    """Render the Dome Multi-Cone workshop."""
    
    _apply_layout_css()
    phase = _get_phase()

    # =========================================================================
    # TOP 55VH: THE FIXED BOARD
    # =========================================================================
    with st.container():
        st.markdown('<div class="fixed-board-container">', unsafe_allow_html=True)
        
        if phase == "blank":
            st.markdown(
                "<div style='height:100%; display:flex; align-items:center; "
                "justify-content:center; color:#555; font-family:sans-serif;'>"
                "<h3>Awaiting Geometry...</h3>"
                "</div>",
                unsafe_allow_html=True
            )
        elif phase in ("picking", "inputs"):
            render_multi_board(
                key="dome",
                plan_renderer=_render_plan_board,
                view_3d_renderer=_render_3d_board,
                profile_renderer=_render_profile_board_stub,
                forced_board="plan"
            )
        elif phase == "solved":
            render_multi_board(
                key="dome",
                plan_renderer=_render_plan_board,
                view_3d_renderer=_render_3d_board,
                profile_renderer=_render_profile_board_stub,
                forced_board="view_3d"
            )
            
        st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================================
    # BOTTOM 40VH: THE SCROLLABLE INPUT DECK
    # =========================================================================
    with st.container():
        st.markdown('<div class="scrollable-inputs">', unsafe_allow_html=True)
        
        if phase == "blank":
            st.markdown("### Step 1: Activate 2D Picker")
            st.caption("Click the button below to open the Plan board and begin picking cone positions.")
            
            if st.button("🎯 Activate 2D Picker", type="primary", use_container_width=True):
                _set_phase("picking")
                st.rerun()
                
            st.markdown("---")
            render_workshop(DOME_MULTI_CONE_RECIPE)

        elif phase == "picking":
            st.markdown("### Step 2: Pick Cones")
            st.caption("Tap the crossings on the Plan board above, then press ENTER.")
            
            if st.button("⚡ ENTER: Lock Cone Data", type="primary", use_container_width=True):
                if not st.session_state.get("ws_dm_picked_crossings"):
                    st.warning("Please pick at least one cone crossing on the Plan board.")
                else:
                    _set_phase("inputs")
                    st.rerun()
                    
            if st.button("🗑️ CLEAR ALL", use_container_width=True):
                _clear_all()

        elif phase == "inputs":
            st.markdown("### Step 3: Finalize Inputs")
            st.caption("Cone picks locked. Adjust the remaining inputs, then press ENTER to solve.")
            
            render_workshop(DOME_MULTI_CONE_RECIPE)
            
            if st.button("🚀 ENTER: Generate 3D Model", type="primary", use_container_width=True):
                _set_phase("solved")
                st.rerun()
                
            if st.button("⬅️ Go Back to Re-pick Cones", use_container_width=True):
                _set_phase("picking")
                st.rerun()
                
            if st.button("🗑️ CLEAR ALL", use_container_width=True):
                _clear_all()

        elif phase == "solved":
            st.success("✅ 3D Model Solved.")
            
            if st.button("⬅️ Edit Inputs", use_container_width=True):
                _set_phase("inputs")
                st.rerun()
                
            if st.button("🗑️ CLEAR ALL", use_container_width=True):
                _clear_all()

        st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# END OF ui/workshops/dome_multi_cone.py
# =============================================================================
