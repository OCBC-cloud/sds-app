# =============================================================================
# SDSe - Dome Multi-Cone Cone Picker
# =============================================================================
# Plan-view picker for the Dome Multi-Cone variant.
#
# The picker is a pure input device. It knows nothing about physics,
# nothing about the z of the frame, nothing about eave height.
# It knows the plan grid and lets the user pick crossings.
#
# The viewer owns all geometry. It reads the picks, computes z at
# each crossing, drops any pick whose z is not above eave height,
# and places the cones accordingly.
#
# Inputs the picker reads (from session state, prefix "ws_dm_"):
#     dome_diameter     float
#     meridians_x       int, N (frames spaced along X)
#     meridians_y       int, M (frames spaced along Y)
#
# What the picker writes (to session state):
#     ws_dm_picked_crossings   set of (i, j) integer pairs
#
# Layout:
#     N rows x M columns of small toggle buttons. The row index is
#     the Family A frame index i. The column index is the Family B
#     frame index j. A button appears only if the crossing at
#     plan (x_i, y_j) is inside the ground circle. Corners that
#     fall outside the circle are shown blank.
#
#     This is the closest layout Streamlit allows to "buttons on
#     the crossings". Streamlit widgets cannot be positioned inside
#     a Plotly chart, so the picker uses a widget grid instead.
#
# History:
#   2026-10-14 - First version. Plan-view picker, widget grid layout.
# =============================================================================

import numpy as np
import streamlit as st


# =============================================================================
# SESSION STATE HELPERS
# =============================================================================

def _get(key, default=None):
    return st.session_state.get("ws_dm_" + key, default)


def _set(key, value):
    st.session_state["ws_dm_" + key] = value


# =============================================================================
# PLAN GRID
# =============================================================================

def _offsets(n, ground_radius):
    """
    Evenly spaced offsets for n frames along one axis.
    Outer pair sits at +/- R * (n-1)/n, strictly inside the circle.
    Same rule as the viewer.
    """
    if n < 1:
        n = 1
    if n == 1:
        return [0.0]
    half_extent = ground_radius * (n - 1.0) / n
    return list(np.linspace(-half_extent, +half_extent, n))


# =============================================================================
# PUBLIC RENDER
# =============================================================================

def render_dome_cone_picker():
    """
    Render the plan-view cone picker for the Dome Multi-Cone variant.

    Reads dome_diameter, meridians_x, meridians_y from session state
    (prefix ws_dm_). Writes the picked crossings back to session state
    as ws_dm_picked_crossings, a set of (i, j) integer tuples.

    Reads no other inputs. Has no other dependencies.
    """
    # ---- Inputs -----------------------------------------------------------
    dome_diameter = float(_get("dome_diameter", 18.0))
    n_x = int(_get("meridians_x", 5))
    n_y = int(_get("meridians_y", 5))

    R = dome_diameter / 2.0
    offsets_x = _offsets(n_x, R)
    offsets_y = _offsets(n_y, R)

    # ---- Load current picked set ------------------------------------------
    picked = _get("picked_crossings", None)
    if picked is None:
        picked = set()
    else:
        picked = set(picked)

    # ---- Header -----------------------------------------------------------
    st.markdown(
        "<h4 style='color:#f39c12;margin-bottom:0.2rem;'>"
        "Cone position picker</h4>"
        "<p style='color:#a8b8c8;margin-top:0;font-size:0.9rem;'>"
        "Click a cell to place a cone at that crossing. Row = frame "
        "along Y (index i). Column = frame along X (index j). Cells "
        "outside the ground circle are blank.</p>",
        unsafe_allow_html=True,
    )

    # ---- Header row of column numbers -------------------------------------
    # Each column corresponds to a Family B frame at some y_j.
    # Row label column on the left shows i.
    col_labels = [""]
    for j in range(n_y):
        col_labels.append("j%d" % j)

    # ---- Grid of buttons --------------------------------------------------
    # N rows, M columns. Row index i (Family A). Column index j (Family B).
    # A cell shows a button only if x_i^2 + y_j^2 <= R^2.
    st.caption("Row i = Frames along X (running along Y). "
               "Column j = Frames along Y (running along X).")
    st.caption("Circle centre is at the middle of the grid. Cells "
               "outside the ground circle are blank.")

    # Add row header + column header
    header_cols = st.columns(n_y + 1)
    with header_cols[0]:
        st.markdown("&nbsp;")
    for j in range(n_y):
        with header_cols[j + 1]:
            st.markdown(
                "<div style='text-align:center;font-size:0.75rem;"
                "color:#a8b8c8;'>j%d</div>" % j,
                unsafe_allow_html=True,
            )

    for i in range(n_x):
        cols = st.columns(n_y + 1)
        with cols[0]:
            st.markdown(
                "<div style='text-align:right;font-size:0.75rem;"
                "color:#a8b8c8;line-height:2.2;'>i%d</div>" % i,
                unsafe_allow_html=True,
            )
        xi = offsets_x[i]
        for j in range(n_y):
            yj = offsets_y[j]
            inside = (xi * xi + yj * yj) <= R * R + 1e-9
            with cols[j + 1]:
                if not inside:
                    # Blank cell — outside the ground circle.
                    st.markdown(
                        "<div style='height:2.2rem;'></div>",
                        unsafe_allow_html=True,
                    )
                    # If this cell was previously picked, remove it.
                    if (i, j) in picked:
                        picked.discard((i, j))
                    continue

                key = "dm_pick_%d_%d" % (i, j)
                currently_on = (i, j) in picked

                # Streamlit toggle gives the on/off behaviour directly.
                new_state = st.toggle(
                    label="",
                    value=currently_on,
                    key=key,
                    help="i=%d, j=%d   plan=(%.2f, %.2f)"
                         % (i, j, xi, yj),
                )

                if new_state and (i, j) not in picked:
                    picked.add((i, j))
                elif (not new_state) and (i, j) in picked:
                    picked.discard((i, j))

    # ---- Write back to session state --------------------------------------
    _set("picked_crossings", picked)

    # ---- Summary ----------------------------------------------------------
    st.markdown(
        "<p style='color:#a8b8c8;margin-top:0.5rem;font-size:0.85rem;'>"
        "Picked crossings: <b>%d</b>. "
        "The viewer will build one cone per picked crossing whose "
        "height is above eave height. Picks below eave height are "
        "silently dropped."
        "</p>" % len(picked),
        unsafe_allow_html=True,
    )


# =============================================================================
# END OF ui/dome_cone_picker.py
# =============================================================================
