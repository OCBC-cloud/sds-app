# =============================================================================
# SDSe Fluid Design Studio - Standard Saddle Workshop
# =============================================================================
# Step 2B of UI_ARCHITECTURE.md Part 9.
#
# History:
#   2026-10-20 - Restructured to match the Dome Multi-Cone standard:
#                - Recipe buttons hidden.
#                - Multi-board forced to Plan view.
#                - Action buttons moved to the bottom.
# =============================================================================

import streamlit as st

from ui.workshops._renderer import render_workshop
from ui.components.SDSe_multi_board import render_multi_board
from viewers.figures.standard_saddle import build_standard_saddle
from data.recipes.standard_saddle import STANDARD_SADDLE_RECIPE


def _render_plan_board():
    """
    Placeholder for the Standard Saddle 2D Plan board.
    """
    st.info("The 2D Plan picker for the Standard Saddle is coming in a future update.")


def _render_3d_board():
    """
    Render the 3D View board: the solved saddle figure.
    """
    build_standard_saddle()


def render_saddle_standard():
    """Render the Standard Saddle workshop from its recipe."""
    
    # ---- Force the page to start at the top ----
    st.components.v1.html(
        """
        <script>
            window.parent.scrollTo(0, 0);
        </script>
        """,
        height=0,
        width=0,
    )

    # ---- Render the recipe, but skip its built-in buttons ----
    render_workshop(STANDARD_SADDLE_RECIPE, show_actions=False)

    st.markdown("---")
    
    # ---- Render the board, forced to Plan view ----
    render_multi_board(
        key="saddle_std",
        plan_label="Plan",
        view_3d_label="3D View",
        plan_renderer=_render_plan_board,
        view_3d_renderer=_render_3d_board,
        forced_board="plan"
    )

    # ---- Draw the action buttons at the very bottom ----
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            "Back to Registration",
            key="saddle_std_back_bottom",
            use_container_width=True,
        ):
            st.session_state.page = "registration"
            st.rerun()
            
    with col2:
        if st.button(
            "Intelligent Design Computing",
            key="saddle_std_forward_bottom",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.page = "results"
            st.rerun()
