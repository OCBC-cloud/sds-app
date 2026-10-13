# =============================================================================
# SDSe Fluid Design Studio - Multi-Cone Roof Workshop
# =============================================================================
# Thin wrapper. Calls the universal workshop renderer with the
# Multi-Cone Roof recipe. The renderer draws the page. The recipe
# owns all inputs.
#
# Same pattern as ui/workshops/saddle_standard.py.
#
# History:
#   2026-10-13 - First version. Multi-Cone Cluster variant.
# =============================================================================

from ui.workshops._renderer import render_workshop
from data.recipes.multi_cone_roof import MULTI_CONE_ROOF_RECIPE


def render_multi_cone_roof():
    """Render the Multi-Cone Roof workshop from its recipe."""
    render_workshop(MULTI_CONE_ROOF_RECIPE)
