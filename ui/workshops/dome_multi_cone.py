# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# Renders the Dome Multi-Cone workshop page.
#
# The workshop is now a single universal multi-board. One toggle at
# the top switches between three views:
#
#   [ Plan ]    -> the 2D cone picker (existing).
#   [ Profile ] -> the 5-slider elevation drawer (new).
#   [ 3D View ] -> the solved 3D figure (existing viewer).
#
# Only the active board is rendered. The heavy 3D solver does not fire
# when the user is on the Plan or Profile board.
#
# The recipe-driven inputs still render above the multi-board so the
# user can shape the dome before entering the drawing phase.
#
# History:
#   2026-10-13 - First version. Recipe wrapper only.
#   2026-10-14 - Add the 2D cone picker below the recipe.
#   2026-10-14 - Switch picker to the real SVG component in
#                ui/components/dome_cone_picker.py.
#   2026-10-18 - Wrap recipe + picker + profile + viewer into the
#                universal SDSe_multi_board component.
# =============================================================================

import streamlit as st

from ui.workshops._renderer import render_workshop
from ui.components.dome_cone_picker import render_dome_cone_picker
from ui.components.dome_profile_picker import render_dome_profile_picker
from ui.components.SDSe_multi_board import render_multi_board
from viewers.figures.dome_multi_cone import build_dome_multi_cone
from data.recipes.dome_multi_cone import DOME_MULTI_CONE_RECIPE


# =============================================================================
# RENDERERS (one per board)
# =============================================================================

def _render_plan_board():
    """
    Render the Plan board: the 2D cone picker.
    Reads dome_diameter, meridians_x, meridians_y, and picked_crossings
    from session state. Writes back to ws_dm_picked_crossings.
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
        "Click a crossing to place or remove a cone. "
        "Switch to the Profile board to shape the beam curve."
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


def _render_profile_board():
    """
    Render the Profile board: the 5-slider elevation drawer.
    Only meaningful when curve_type == "custom". Otherwise it shows
    a note telling the user how to activate it.
    """
    curve_type = str(
        st.session_state.get("ws_dm_curve_type", "parabolic")
    ).lower()

    if curve_type != "custom":
        st.info(
            "The Profile board is available when the beam curve is set "
            "to **Custom (Draw Profile)** in the recipe above. "
            "Select it to unlock the 5-slider elevation drawer."
        )
        # Still render the picker so the user can preview the shape
        # before committing to custom mode. The sliders write to session
        # state and will be picked up the moment the user switches to custom.
        st.markdown(
            "<p style='color:#a8b8c8;'>"
            "Preview mode below. Moving a slider will not affect the "
            "3D shape until the beam curve is set to Custom."
            "</p>",
            unsafe_allow_html=True,
        )
        render_dome_profile_picker()
        return

    # Custom mode active. Render the picker.
    render_dome_profile_picker()


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
    # ---- Recipe-driven input groups ---------------------------------------
    render_workshop(DOME_MULTI_CONE_RECIPE)

    # ---- Universal multi-board (Plan / Profile / 3D View) -----------------
    st.markdown("---")
    render_multi_board(
        key="dome",
        plan_label="Plan",
        profile_label="Profile",
        view_3d_label="3D View",
        plan_renderer=_render_plan_board,
        profile_renderer=_render_profile_board,
        view_3d_renderer=_render_3d_board,
    )


# =============================================================================
# END OF ui/workshops/dome_multi_cone.py
# =============================================================================
