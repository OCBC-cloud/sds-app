# =============================================================================
# SDSe - Dome Multi-Cone Cone Picker
# =============================================================================
# 2D plan-view picker for the Dome Multi-Cone variant.
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
# The picker has no other dependencies.
#
# History:
#   2026-10-14 - First version. Plan-view picker.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st


# =============================================================================
# COLOURS
# =============================================================================

COL_GROUND = "#2ecc71"
COL_FRAME_A_PLAN = "#FF6B6B"
COL_FRAME_B_PLAN = "#e07b39"
COL_BUTTON_OFF = "#3a4a5a"   # dull, inactive
COL_BUTTON_ON = "#f1c40f"    # bright, active


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


def _plan_crossings(dome_diameter, n_x, n_y):
    """
    Plan crossings between the two families of frames.
    A crossing exists at (x_i, y_j) iff x_i^2 + y_j^2 <= R^2.

    Returns list of dicts:
        {"i": i, "j": j, "x": x_i, "y": y_j}
    """
    R = dome_diameter / 2.0
    offsets_x = _offsets(n_x, R)
    offsets_y = _offsets(n_y, R)

    crossings = []
    for i, xi in enumerate(offsets_x):
        for j, yj in enumerate(offsets_y):
            if xi * xi + yj * yj <= R * R + 1e-9:
                crossings.append({
                    "i": i, "j": j,
                    "x": float(xi),
                    "y": float(yj),
                })
    return crossings
