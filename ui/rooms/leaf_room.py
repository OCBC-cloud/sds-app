# =============================================================================
# SDSe Fluid Design Studio - Leaf Rib Length Room
# =============================================================================
# Dedicated canvas for adjusting rib lengths of a Cantilever Leaf object.
# Accessed from the workshop.
#
# Reads base rib lengths from ws_sl_rib_base_lengths (computed by the workshop).
# Writes user overrides to ws_sl_rib_lengths_override.
# Sets ws_sl_rib_override_active = True only on Apply.
# =============================================================================

import streamlit as st


# =============================================================================
# CONSTANTS
# =============================================================================

MAX_RIB_PAIRS = 7


# =============================================================================
# HELPERS
# =============================================================================

def _ensure_rib_state():
    """
    Ensure session state has the rib override structures.
    Reads base lengths from ws_sl_rib_base_lengths (set by workshop).
    Falls back to a safe default if the workshop has not run yet.
    Does NOT auto-initialise the override. The override stays inactive
    until the user explicitly presses Apply.
    """
    if "ws_sl_rib_base_lengths" not in st.session_state:
        st.session_state["ws_sl_rib_base_lengths"] = [5.0] * MAX_RIB_PAIRS

    if "ws_sl_rib_symmetric" not in st.session_state:
        st.session_state["ws_sl_rib_symmetric"] = True

    if "ws_sl_rib_override_active" not in st.session_state:
        st.session_state["ws_sl_rib_override_active"] = False

    if "ws_sl_rib_lengths_override" not in st.session_state:
        st.session_state["ws_sl_rib_lengths_override"] = []


def _rib_position_label(i, n):
    """Return a position word for rib index i of n."""
    if n <= 1:
        return "centre"
    if i == 0:
        return "near column"
    if i == n - 1:
        return "near tip"
    mid = (n - 1) / 2.0
    if abs(i - mid) < 0.5:
        return "centre"
    if i < mid:
        return "inner"
    return "outer"


def _header():
    st.markdown(
        '<div style="font-size: 0.85rem; color: #a8b8c8; '
        'margin-bottom: 1.2rem;">'
        'SDSe Fluid Design Studio / '
        '<span style="color: #f39c12; font-weight: 600;">Cantilever</span>'
        ' / '
        '<span style="color: #f39c12; font-weight: 600;">Leaf</span>'
        ' / '
        '<span style="color: #f39c12; font-weight: 600;">Rib Length Room</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="color: #ffffff; font-size: 1.4rem; font-weight: 700; '
        'margin-bottom: 0.5rem;">Rib Length Adjustment</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="color: #a8b8c8; font-size: 0.9rem; '
        'margin-bottom: 1.5rem; line-height: 1.5;">'
        'Adjust the length of each rib pair to shape the leaf. '
        'The system recomputes rib tip coordinates, membrane, and '
        'perimeter cable from these lengths.'
        '</div>',
        unsafe_allow_html=True,
    )


def _section_header(text):
    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.2rem 0 0.6rem 0; font-size: 1.0rem;">'
        + text + '</div>',
        unsafe_allow_html=True,
    )


def _info_box(text):
    st.markdown(
        '<div style="background: #1a2a3a; border-left: 3px solid #4a7a9c; '
        'padding: 0.7rem 0.9rem; border-radius: 4px; margin-top: 0.5rem; '
        'font-size: 0.85rem; color: #c8d4e0; line-height: 1.5;">'
        + text + '</div>',
        unsafe_allow_html=True,
    )


def _preview_box(text):
    st.markdown(
        '<div style="background: #0d1620; border-left: 3px solid #3498db; '
        'padding: 0.6rem 0.8rem; border-radius: 4px; margin-top: 0.5rem; '
        'font-size: 0.85rem; color: #c8d4e0; line-height: 1.5;">'
        + text + '</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_leaf_room():
    """Render the Leaf Rib Length Room."""
    _ensure_rib_state()
    _header()

    # ---- Adjustment mode
    _section_header("Adjustment Mode")

    sym_val = st.session_state.get("ws_sl_rib_symmetric", True)
    mode_options = ["Symmetric", "Individual"]
    mode_idx = 0 if sym_val else 1
    mode_choice = st.radio(
        "Adjustment Mode",
        mode_options,
        index=mode_idx,
        key="ws_sl_rib_mode_radio",
        help="Symmetric: one set of lengths, mirrored. "
             "Individual: separate lengths for left and right.",
    )
    st.session_state["ws_sl_rib_symmetric"] = (mode_choice == "Symmetric")
    is_symmetric = st.session_state["ws_sl_rib_symmetric"]

    if is_symmetric:
        _info_box("Symmetric mode. Each rib length applies to both sides.")
    else:
        _info_box("Individual mode. Left and right rib lengths are independent.")

    # ---- Rib length inputs
    _section_header("Rib Lengths")

    base_lengths = list(st.session_state["ws_sl_rib_base_lengths"])
    override_active = bool(st.session_state.get("ws_sl_rib_override_active", False))
    current_overrides = list(st.session_state.get("ws_sl_rib_lengths_override", []))

    n_ribs = int(st.session_state.get("ws_sl_ribs_per_side", MAX_RIB_PAIRS))
    if n_ribs > MAX_RIB_PAIRS:
        n_ribs = MAX_RIB_PAIRS
    if n_ribs < 1:
        n_ribs = 1

    new_overrides = []

    if is_symmetric:
        for i in range(n_ribs):
            pos = _rib_position_label(i, n_ribs)
            base_val = base_lengths[i] if i < len(base_lengths) else 5.0
            if override_active and i < len(current_overrides):
                current_val = current_overrides[i]
            else:
                current_val = base_val
            new_val = st.number_input(
                "Rib " + str(i + 1) + " of " + str(n_ribs) + " - " + pos + " (m)",
                min_value=0.5,
                max_value=30.0,
                value=float(current_val),
                step=0.1,
                key="ws_sl_rib_input_sym_" + str(i),
                help="Base length (system computed): " + ("%.2f m" % base_val),
            )
            new_overrides.append(new_val)
    else:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(
                '<div style="color: #f39c12; font-weight: 600; '
                'font-size: 0.9rem; margin-bottom: 0.4rem;">Left side</div>',
                unsafe_allow_html=True,
            )
            left_vals = []
            for i in range(n_ribs):
                pos = _rib_position_label(i, n_ribs)
                base_val = base_lengths[i] if i < len(base_lengths) else 5.0
                if override_active and i < len(current_overrides):
                    current_val = current_overrides[i]
                else:
                    current_val = base_val
                new_val = st.number_input(
                    "Rib " + str(i + 1) + " L",
                    min_value=0.5,
                    max_value=30.0,
                    value=float(current_val),
                    step=0.1,
                    key="ws_sl_rib_input_L_" + str(i),
                    help="Rib " + str(i + 1) + " of " + str(n_ribs) + " - " + pos,
                )
                left_vals.append(new_val)
        with col_right:
            st.markdown(
                '<div style="color: #f39c12; font-weight: 600; '
                'font-size: 0.9rem; margin-bottom: 0.4rem;">Right side</div>',
                unsafe_allow_html=True,
            )
            right_vals = []
            for i in range(n_ribs):
                pos = _rib_position_label(i, n_ribs)
                base_val = base_lengths[i] if i < len(base_lengths) else 5.0
                if override_active and i < len(current_overrides):
                    current_val = current_overrides[i]
                else:
                    current_val = base_val
                new_val = st.number_input(
                    "Rib " + str(i + 1) + " R",
                    min_value=0.5,
                    max_value=30.0,
                    value=float(current_val),
                    step=0.1,
                    key="ws_sl_rib_input_R_" + str(i),
                    help="Rib " + str(i + 1) + " of " + str(n_ribs) + " - " + pos,
                )
                right_vals.append(new_val)

        for i in range(n_ribs):
            new_overrides.append(max(left_vals[i], right_vals[i]))

    # ---- Summary
    if new_overrides:
        min_l = min(new_overrides)
        max_l = max(new_overrides)
        avg_l = sum(new_overrides) / len(new_overrides)
        base_min = min(base_lengths[:len(new_overrides)]) if base_lengths else 0.0
        base_max = max(base_lengths[:len(new_overrides)]) if base_lengths else 0.0
        _preview_box(
            'Rib pairs: <strong>' + str(len(new_overrides)) + '</strong><br>'
            'Current range: <strong>' + ("%.2f" % min_l) + ' m</strong> to '
            '<strong>' + ("%.2f" % max_l) + ' m</strong> '
            '(avg <strong>' + ("%.2f" % avg_l) + ' m</strong>)<br>'
            'System base range: <strong>' + ("%.2f" % base_min) + ' m</strong> to '
            '<strong>' + ("%.2f" % base_max) + ' m</strong><br>'
            'Mode: <strong>' + ("Symmetric" if is_symmetric else "Individual")
            + '</strong>'
        )

    # ---- Actions
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Cancel", key="leaf_room_cancel", use_container_width=True):
            st.session_state.page = "workshop"
            st.rerun()
    with col_b:
        if st.button(
            "Apply and Return",
            key="leaf_room_apply",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["ws_sl_rib_lengths_override"] = new_overrides
            st.session_state["ws_sl_rib_override_active"] = True
            st.session_state.page = "workshop"
            st.rerun()



