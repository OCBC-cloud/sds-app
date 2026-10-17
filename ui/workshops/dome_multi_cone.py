# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# Renders the Dome Multi-Cone workshop page.
#
# Two things are rendered, in order:
#   1. The recipe-driven input groups (via the universal renderer).
#   2. The 2D cone picker (a real Streamlit component, SVG canvas).
#
# The picker is a pure input device. It reads dome_diameter,
# meridians_x, and meridians_y from session state, shows an SVG plan
# view with a toggle at every crossing inside the ground circle, and
# writes the picked set back to session state under
# ws_dm_picked_crossings.
#
# The viewer owns all geometry. It reads the picked set and builds
# the cones. Picks whose frame z is not above eave height are
# silently dropped by the viewer.
#
# History:
#   2026-10-13 - First version. Recipe wrapper only.
#   2026-10-14 - Add the 2D cone picker below the recipe.
#   2026-10-14 - Switch picker to the real SVG component in
#                ui/components/dome_cone_picker.py.
# =============================================================================

import streamlit as st

from ui.workshops._renderer import render_workshop
from ui.components.dome_cone_picker import render_dome_cone_picker
from data.recipes.dome_multi_cone import DOME_MULTI_CONE_RECIPE


def render_dome_multi_cone():
    """
    Render the Dome Multi-Cone workshop from its recipe, then the
    real SVG cone picker below it.
    """
    # ---- Recipe-driven input groups ---------------------------------------
    render_workshop(DOME_MULTI_CONE_RECIPE)

    # ---- 2D cone picker (SVG component) -----------------------------------
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
    st.markdown("---")
    st.markdown("### Select Cone Positions")
    st.markdown("Click a crossing point to place or remove a cone.")
    new_picked = render_dome_cone_picker(
        dome_diameter=dome_diameter,
        n_x=n_x,
        n_y=n_y,
        picked=picked,
        key="dome_cone_picker_main",
    )

    st.session_state["ws_dm_picked_crossings"] = set(new_picked)


# =============================================================================
# END OF ui/workshops/dome_multi_cone.py
# =============================================================================
