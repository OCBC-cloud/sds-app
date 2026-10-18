# =============================================================================
# SDSe - Universal Multi-Board Component
# =============================================================================
# A universal 3-in-1 board component for mobile-first UI.
#
# Renders a single board container with a segmented toggle at the top:
#   [ Plan ] [ Profile ] [ 3D View ]
#
# Only the active board is rendered. The others are skipped. This is
# critical for performance on mobile: the 3D mesh is not rebuilt when
# the user is on the Plan board.
#
# The component is universal. Any workshop calls it by passing three
# renderer functions. The component does not know what a "dome" or a
# "saddle" is. It knows how to render a toggle and dispatch to the
# correct renderer.
#
# Usage:
#
#   from ui.components.SDSe_multi_board import render_multi_board
#
#   render_multi_board(
#       key="dome",
#       plan_label="Plan",
#       profile_label="Profile",
#       view_3d_label="3D View",
#       plan_renderer=lambda: render_cone_picker(...),
#       profile_renderer=lambda: render_profile_picker(...),
#       view_3d_renderer=lambda: build_dome_multi_cone(),
#   )
#
# The component owns its toggle state in session state under the key
#   ws_<key>_active_board
# where <key> is the caller-supplied key ("dome", "saddle", etc.).
#
# History:
#   2026-10-18 - First version. Universal 3-in-1 board.
# =============================================================================

import streamlit as st


_VALID_BOARDS = ("plan", "profile", "view_3d")

_DEFAULT_LABELS = {
    "plan": "Plan",
    "profile": "Profile",
    "view_3d": "3D View",
}


def _get_board_state(key):
    state_key = f"ws_{key}_active_board"
    active = st.session_state.get(state_key, "view_3d")
    if active not in _VALID_BOARDS:
        active = "view_3d"
    return state_key, active


def _render_toggle(key, active, labels):
    """
    Renders the segmented toggle at the top of the board.
    Uses st.radio with horizontal layout to get a segmented control.
    """
    state_key = f"ws_{key}_active_board"

    # Build display labels for the radio buttons
    options = [
        labels["plan"],
        labels["profile"],
        labels["view_3d"],
    ]
    mapping = {
        labels["plan"]: "plan",
        labels["profile"]: "profile",
        labels["view_3d"]: "view_3d",
    }

    # Reverse lookup: which label is currently active?
    current_label = None
    for lbl, val in mapping.items():
        if val == active:
            current_label = lbl
            break
    if current_label is None:
        current_label = labels["view_3d"]

    # Render as a horizontal radio
    chosen_label = st.radio(
        "View",
        options=options,
        index=options.index(current_label),
        horizontal=True,
        key=f"{state_key}_selector",
        label_visibility="collapsed",
    )

    chosen_board = mapping.get(chosen_label, "view_3d")
    if chosen_board != active:
        st.session_state[state_key] = chosen_board
        # Force a rerun so the correct renderer fires immediately.
        st.rerun()

    return chosen_board


def render_multi_board(
    key,
    plan_renderer,
    profile_renderer,
    view_3d_renderer,
    plan_label=None,
    profile_label=None,
    view_3d_label=None,
):
    """
    Renders the universal 3-in-1 board.

    Arguments:
        key                 A short string that scopes this board's state
                            in session_state. Use "dome", "saddle", etc.
        plan_renderer       Callable. Renders the Plan board.
        profile_renderer    Callable. Renders the Profile board.
        view_3d_renderer    Callable. Renders the 3D View.
        plan_label          Optional label override. Default "Plan".
        profile_label       Optional label override. Default "Profile".
        view_3d_label       Optional label override. Default "3D View".

    The label overrides allow a workshop to rename a board without
    changing this component. For example, a Saddle workshop might
    call its Plan board "Footprint" and its Profile board "Beam
    Curve". The component does not care.
    """
    labels = dict(_DEFAULT_LABELS)
    if plan_label is not None:
        labels["plan"] = plan_label
    if profile_label is not None:
        labels["profile"] = profile_label
    if view_3d_label is not None:
        labels["view_3d"] = view_3d_label

    state_key, active = _get_board_state(key)

    # --- The toggle ---
    st.markdown(
        "<div style='margin-bottom: 8px;'></div>",
        unsafe_allow_html=True,
    )
    active = _render_toggle(key, active, labels)

    # --- The active board content ---
    if active == "plan":
        plan_renderer()
    elif active == "profile":
        profile_renderer()
    elif active == "view_3d":
        view_3d_renderer()


# =============================================================================
# END OF ui/components/SDSe_multi_board.py
# =============================================================================
