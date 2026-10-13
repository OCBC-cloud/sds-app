# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# Thin wrapper. Calls the universal workshop renderer with the
# Dome Multi-Cone recipe. The renderer draws the page. The recipe
# owns all inputs.
#
# Same pattern as ui/workshops/saddle_standard.py and
# ui/workshops/multi_cone_roof.py.
#
# History:
#   2026-10-13 - First version. Dome Multi-Cone variant.
# =============================================================================

from ui.workshops._renderer import render_workshop
from data.recipes.dome_multi_cone import DOME_MULTI_CONE_RECIPE


def render_dome_multi_cone():
    """Render the Dome Multi-Cone workshop from its recipe."""
    render_workshop(DOME_MULTI_CONE_RECIPE)
