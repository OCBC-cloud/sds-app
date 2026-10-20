# =============================================================================
# SDSe - Universal Multi-Board Component
# =============================================================================
# A universal board component for mobile-first UI.
# Supports forced_board to hide the radio toggle and lock a view.
# =============================================================================

import streamlit as st


_VALID_BOARDS_3 = ("plan", "profile", "view_3d")
_VALID_BOARDS_2 = ("plan", "view_3d")

_DEFAULT_LABELS = {
    "plan": "Plan",
    "profile": "Profile",
    "view_3d": "3D View",
}


def _get_board_state(key, valid):
    state_key = f"ws_{key}_active_board"
    active = st.session_state.get(state_key, "view_3d")
    if active not in valid:
        active = "view_3d"
    return state_key, active


def _render_toggle(key, active, labels, show_profile):
    state_key = f"ws_{key}_active_board"

    if show_profile:
        options = [labels["plan"], labels["profile"], labels["view_3d"]]
        mapping = {
            labels["plan"]: "plan",
            labels["profile"]: "profile",
            labels["view_3d"]: "view_3d",
        }
    else:
        options = [labels["plan"], labels["view_3d"]]
        mapping = {
            labels["plan"]: "plan",
            labels["view_3d"]: "view_3d",
        }

    current_label = None
    for lbl, val in mapping.items():
        if val == active:
            current_label = lbl
            break
    if current_label is None:
        current_label = labels["view_3d"]

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
        st.rerun()

    return chosen_board


def render_multi_board(
    key,
    plan_renderer,
    view_3d_renderer,
    profile_renderer=None,
    plan_label=None,
    profile_label=None,
    view_3d_label=None,
    forced_board=None,
):
    """
    Renders the universal multi-board.
    If forced_board is provided ("plan", "profile", or "view_3d"),
    the toggle is hidden and the board is locked to that view.
    """
    labels = dict(_DEFAULT_LABELS)
    if plan_label is not None:
        labels["plan"] = plan_label
    if profile_label is not None:
        labels["profile"] = profile_label
    if view_3d_label is not None:
        labels["view_3d"] = view_3d_label

    show_profile = profile_renderer is not None
    valid = _VALID_BOARDS_3 if show_profile else _VALID_BOARDS_2

    # --- State Machine Override ---
    if forced_board is not None:
        active = forced_board
    else:
        state_key, active = _get_board_state(key, valid)
        st.markdown(
            "<div style='margin-bottom: 8px;'></div>",
            unsafe_allow_html=True,
        )
        active = _render_toggle(key, active, labels, show_profile)

    # --- Render the active board ---
    if active == "plan":
        plan_renderer()
    elif active == "profile" and show_profile:
        profile_renderer()
    elif active == "view_3d":
        view_3d_renderer()


# =============================================================================
# END OF ui/components/SDSe_multi_board.py
# =============================================================================
