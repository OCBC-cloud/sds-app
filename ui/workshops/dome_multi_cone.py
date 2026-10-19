# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# Renders the Dome Multi-Cone workshop page.
#
# The workshop is a universal multi-board. Currently two boards are
# enabled:
#
#   [ Plan ]    -> the 2D cone picker.
#   [ 3D View ] -> the solved 3D figure.
#
# History:
#   2026-10-13 - First version. Recipe wrapper only.
#   2026-10-14 - Add the 2D cone picker below the recipe.
#   2026-10-14 - Switch picker to the real SVG component in
#                ui/components/dome_cone_picker.py.
#   2026-10-18 - Wrap recipe + picker + viewer into the universal
#                SDSe_multi_board component.
#   2026-10-18 - Retire the Profile board. Canvas picker could not
#                commit values. Keep Plan and 3D View only.
#   2026-10-20 - Restored to stable version + added scroll-to-top fix.
# =============================================================================

import streamlit as st

from ui.workshops._renderer import render_workshop
from ui.components.dome_cone_picker import render_dome_cone_picker
from ui.components.SDSe_multi_board import render_multi_board
from viewers.figures.dome_multi_cone import build_dome_multi_cone
from data.recipes.dome_multi_cone import DOME_MULTI_CONE_RECIPE


# =============================================================================
# RENDERERS (one per board)
# =============================================================================

def _render_plan_board():
    """
    Render the Plan board: the 2D cone picker.
    """
    dome_diameter = float(
        st.session_state.get("ws_dm_dome_diameter", 18.0)
    )
    n_x = int(st.session_state.get("ws_dm_meridians_x", 5))
    n_y = int(st.session_state.get("ws_dm_meridians_y", 5))

    picked_raw = st.session_state.get("ws_dm_picked_crossings", None)
    if picked_raw is None:
        picked = set()
    else:
        try:
            picked = set(
                (int(i), int(j)) for (i, j) in picked_raw
            )
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
    """
    Stub renderer for the retired Profile board.
    """
    st.info(
        "The Profile board is temporarily unavailable. The custom "
        "elevation picker is under construction. Use the recipe's "
        "Parabolic / Circular / Catenary options for the beam curve."
    )


def _render_3d_board():
    """
    Render the 3D View board: the solved dome figure.
    """
    build_dome_multi_cone()


# =============================================================================
# PAGE
# =============================================================================

def render_dome_multi_cone():
    """
    Render the Dome Multi-Cone workshop from its recipe, then hand off to
    the universal multi-board for the drawing phase.
    """
    # ---- Force the page to start at the top when entering the workshop ----
    st.components.v1.html(
        """
        <script>
            window.parent.scrollTo(0, 0);
        </script>
        """,
        height=0,
        width=0,
    )

    # ---- Recipe-driven input groups ---------------------------------------
    render_workshop(DOME_MULTI_CONE_RECIPE)

    # ---- Explain the "custom" option if it is selected --------------------
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

    # ---- Universal multi-board (Plan / 3D View only) ----------------------
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


# =============================================================================
# END OF ui/workshops/dome_multi_cone.py
# =============================================================================
