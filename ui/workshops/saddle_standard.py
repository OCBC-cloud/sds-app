# =============================================================================
# SDSe Fluid Design Studio - Standard Saddle Workshop
# =============================================================================
# Step 2B of UI_ARCHITECTURE.md Part 9.
#
# This file is now a thin wrapper. It calls the universal workshop
# renderer with the Standard Saddle recipe. The renderer draws the
# page. The recipe owns all inputs.
#
# Before 2026-09-29, this file was ~450 lines of hand-written
# Streamlit code. Now it is 12 lines. The recipe is the interface.
#
# History:
#   2026-09-29 - Migrated to the universal renderer (Step 2B).
#                See data/recipes/standard_saddle.py.
# =============================================================================

from ui.workshops._renderer import render_workshop
from data.recipes.standard_saddle import STANDARD_SADDLE_RECIPE


def render_saddle_standard():
    """Render the Standard Saddle workshop from its recipe."""
    render_workshop(STANDARD_SADDLE_RECIPE)





