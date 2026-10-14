# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# Renders the Dome Multi-Cone workshop page.
#
# Two things are rendered, in order:
#   1. The recipe-driven input groups (via the universal renderer).
#   2. The 2D cone picker, below the recipe.
#
# The picker is a pure input device. It reads dome_diameter,
# meridians_x, and meridians_y from session state, shows a grid of
# toggle buttons at every plan crossing inside the ground circle,
# and writes the picked set to session state.
#
# The viewer owns all geometry. It reads the picked set and builds
# the cones. Picks whose frame z is not above eave height are
# silently dropped by the viewer.
#
# Same pattern as ui/workshops/multi_cone_roof.py for the recipe
# part, plus the picker call.
#
# History:
#   2026-10-13 - First version. Recipe wrapper only.
#   2026-10-14 - Add the 2D cone picker below the recipe.
# =============================================================================

from ui.workshops._renderer import render_workshop
from ui.dome_cone_picker import render_dome_cone_picker
from data.recipes.dome_multi_cone import DOME_MULTI_CONE_RECIPE


def render_dome_multi_cone():
    """
    Render the Dome Multi-Cone workshop from its recipe, then the
    cone picker below it.
    """
    render_workshop(DOME_MULTI_CONE_RECIPE)
    render_dome_cone_picker()
