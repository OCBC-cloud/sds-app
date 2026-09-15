# =============================================================================
# SDSe Fluid Design Studio - Leaf Rib Length Room
# =============================================================================
# Dedicated canvas for adjusting rib lengths of a Cantilever Leaf object.
# This is a "pull-away" room accessed from the workshop.
#
# The user:
#   - Chooses symmetric or individual mode
#   - Adjusts rib lengths (7 values, or 14 in individual mode)
#   - Taps Apply to commit changes and return to the workshop
#
# Reads the base rib lengths from session state (computed by the workshop).
# Writes override values back to session state for the viewer to use.
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
    Ensure the session state has the rib override structures.
    Base rib lengths are read from ws_sl_rib_base_lengths if set,
    otherwise a default 5.0 m placeholder is used.
    """
    if "ws_sl_rib_base_lengths" not in st.session_state:
        base = [5.0] * MAX_RIB_PAIRS
        st.session_state["ws_sl_rib_base_lengths"] = base

    if "ws_sl_rib_symmetric" not in st.session_state:
        st.session_state["ws_sl_rib_symmetric"] = True

    if "ws_sl_rib_lengths_override" not in st.session_state:
        st.session_state["ws_sl_rib_lengths_override"] = list(
            st.session_state["ws_sl_rib_base_lengths"]
        )


def _header():
    """Render the room header and breadcrumb."""
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

    # ---- Symmetric vs Individual mode
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
        _info_box(
            "Symmetric mode. Each rib length applies to both "
            "left and right sides."
        )
    else:
        _info_box(
            "Individual mode. Left and right rib lengths are "
            "independent."
        )

    # ---- Rib length inputs
    _section_header("Rib Lengths")

    base_lengths = st.session_state["ws_sl_rib_base_lengths"]
    current_overrides = list(st.session_state["ws_sl_rib_lengths_override"])

    n_ribs = st.session_state.get("ws_sl_ribs_per_side", MAX_RIB_PAIRS)
    if n_ribs > MAX_RIB_PAIRS:
        n_ribs = MAX_RIB_PAIRS
    if n_ribs < 1:
        n_ribs = 1

    new_overrides = []

    if is_symmetric:
        for i in range(n_ribs):
            base_val = base_lengths[i] if i < len(base_lengths) else 5.0
            current_val = current_overrides[i] if i < len(current_overrides) else base_val
            new_val = st.number_input(
                "Rib " + str(i + 1) + " length (m)",
                min_value=0.5,
                max_value=30.0,
                value=float(current_val),
                step=0.1,
                key="ws_sl_rib_input_sym_" + str(i),
                help="Base length: " + ("%.2f m" % base_val),
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
                base_val = base_lengths[i] if i < len(base_lengths) else 5.0
                current_val = current_overrides[i] if i < len(current_overrides) else base_val
                new_val = st.number_input(
                    "Rib " + str(i + 1) + " (L) m",
                    min_value=0.5,
                    max_value=30.0,
                    value=float(current_val),
                    step=0.1,
                    key="ws_sl_rib_input_L_" + str(i),
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
                base_val = base_lengths[i] if i < len(base_lengths) else 5.0
                current_val = current_overrides[i] if i < len(current_overrides) else base_val
                new_val = st.number_input(
                    "Rib " + str(i + 1) + " (R) m",
                    min_value=0.5,
                    max_value=30.0,
                    value=float(current_val),
                    step=0.1,
                    key="ws_sl_rib_input_R_" + str(i),
                )
                right_vals.append(new_val)

        # Store the larger of L / R for the "primary" list
        # Individual mode stores a single list as base for now
        for i in range(n_ribs):
            new_overrides.append(max(left_vals[i], right_vals[i]))

    # ---- Summary box
    n_pairs = len(new_overrides)
    min_len = min(new_overrides) if new_overrides else 0.0
    max_len = max(new_overrides) if new_overrides else 0.0

    _preview_box(
        'Rib pairs: <strong>' + str(n_pairs) + '</strong><br>'
        'Length range: <strong>' + ("%.2f m" % min_len)
        + '</strong> to <strong>' + ("%.2f m" % max_len) + '</strong><br>'
        'Mode: <strong>' + ("Symmetric" if is_symmetric else "Individual")
        + '</strong>'
    )

    # ---- Action buttons
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
            st.session_state.page = "workshop"
            st.rerun()







