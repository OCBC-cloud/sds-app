# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# History:
#   2026-10-20 - Moved action buttons to the bottom. Tells the renderer
#                not to draw its built-in buttons.
# =============================================================================

import streamlit as st

from ui.workshops._renderer import render_workshop
from ui.components.dome_cone_picker import render_dome_cone_picker
from ui.components.SDSe_multi_board import render_multi_board
from viewers.figures.dome_multi_cone import build_dome_multi_cone
from data.recipes.dome_multi_cone import DOME_MULTI_CONE_RECIPE


def _render_plan_board():
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
    st.info(
        "The Profile board is temporarily unavailable. The custom "
        "elevation picker is under construction. Use the recipe's "
        "Parabolic / Circular / Catenary options for the beam curve."
    )


def _render_3d_board():
    build_dome_multi_cone()


def render_dome_multi_cone():
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
    render_workshop(DOME_MULTI_CONE_RECIPE, show_actions=False)

    curve_type = str(
        st.session_state.get("ws_dm_curve_type", "parabolic")
    ).lower()
    if curve_type == "custom":
        st.info(
            "You have selected **Custom (Draw Profile)**. The custom "
            "elevation picker is not yet available. The 3D view will "
            "fall back to the default parabolic curve until the picker "
            "is rebuilt. Choose Parabolic, Circular, or Catenary to "
            "shape the dome today."
        )

    st.markdown("---")
    render_multi_board(
        key="dome",
        plan_label="Plan",
        profile_label="Profile",
        view_3d_label="3D View",
        plan_renderer=_render_plan_board,
        profile_renderer=_render_profile_board_stub,
        view_3d_renderer=_render_3d_board,
    )

    # ---- Draw the action buttons at the very bottom ----
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            "Back to Registration",
            key="dome_back_bottom",
            use_container_width=True,
        ):
            st.session_state.page = "registration"
            st.rerun()
            
    with col2:
        if st.button(
            "Intelligent Design Computing",
            key="dome_forward_bottom",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.page = "results"
            st.rerun()


# =============================================================================
# END OF ui/workshops/dome_multi_cone.py
# =============================================================================
