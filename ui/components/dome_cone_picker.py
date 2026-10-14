# =============================================================================
# SDSe - Dome Multi-Cone Cone Picker (Streamlit Component)
# =============================================================================
# Python side of the 2D plan-view cone picker.
#
# The visual is rendered in index.html (same folder). An SVG canvas
# with a ground circle, frame grid lines, and a clickable toggle at
# every crossing. JavaScript handles clicks and sends the picked
# set back to Python.
#
# This file:
#   - declares the Streamlit component
#   - exposes render_dome_cone_picker(...) for Python callers
#
# The picker is a pure input device. It knows nothing about physics.
# The viewer owns all geometry and reads the picked set.
#
# History:
#   2026-10-14 - First version. Real SVG picker.
# =============================================================================

import os
import streamlit.components.v1 as components


# =============================================================================
# COMPONENT DECLARATION
# =============================================================================

# Streamlit looks for index.html inside this directory.
_COMPONENT_DIR = os.path.dirname(__file__)

_dome_cone_picker_component = components.declare_component(
    "dome_cone_picker",
    path=_COMPONENT_DIR,
)


# =============================================================================
# PUBLIC RENDER FUNCTION
# =============================================================================

def render_dome_cone_picker(dome_diameter, n_x, n_y, picked, key):
    """
    Render the 2D plan-view cone picker.

    Parameters
    ----------
    dome_diameter : float
        Diameter of the ground circle, in metres.
    n_x : int
        Number of frames spaced along X. Family A. Rendered as
        vertical lines in plan.
    n_y : int
        Number of frames spaced along Y. Family B. Rendered as
        horizontal lines in plan.
    picked : set of (i, j)
        The current picked set from session state.
    key : str
        Unique key for this component instance.

    Returns
    -------
    set of (i, j)
        The picked set after the user's latest interaction. If the
        user has not yet clicked anything, returns the passed-in
        picked set unchanged.
    """
    picked_list = [[int(i), int(j)] for (i, j) in sorted(picked)]

    result = _dome_cone_picker_component(
        dome_diameter=float(dome_diameter),
        n_x=int(n_x),
        n_y=int(n_y),
        picked=picked_list,
        key=key,
        default={"picked": picked_list},
    )

    if not result or "picked" not in result:
        return set(picked)

    try:
        return set((int(i), int(j)) for (i, j) in result["picked"])
    except (TypeError, ValueError):
        return set(picked)


# =============================================================================
# END OF ui/components/dome_cone_picker.py
# =============================================================================
