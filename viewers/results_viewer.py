# =============================================================================
# SDSe Fluid Design Studio - Results Viewer Dispatcher
# =============================================================================
# Looks up the correct figure builder for a given variant and calls it.
# Each variant has its own builder file under viewers/figures/.
#
# Architecture (updated 2026-09-15):
#   - This file is a small dispatcher only.
#   - Every variant's figure lives in viewers/figures/<variant>.py
#   - Shared helpers live in viewers/figures/_shared.py
#   - Adding a new variant = add a file + add a registry entry
#
# Dispatch rule:
#   Variant keys are globally unique. The dispatcher ignores
#   structure_key entirely and routes on variant_key alone.
#
# Variant keys (internal, never changed):
#   "standard_saddle"          -> Cable Supported Saddle
#   "frame_supported_saddle"   -> Beam Supported Saddle
#   "cantilever_leaf"          -> Cantilever Leaf
# =============================================================================

import plotly.graph_objects as go

from viewers.figures._shared import apply_common_layout
from viewers.figures.standard_saddle import build_standard_saddle
from viewers.figures.cantilever_leaf import build_cantilever_leaf
from viewers.figures.beam_supported_saddle import build_beam_supported_saddle


# =============================================================================
# FIGURE REGISTRY
# =============================================================================
# Maps variant_key to the builder function that draws it.
# Add a new entry here when a new variant gets its own figure file.

FIGURE_REGISTRY = {
    "standard_saddle": build_standard_saddle,
    "cantilever_leaf": build_cantilever_leaf,
    "frame_supported_saddle": build_beam_supported_saddle,
    # Future:
    # "cantilever_cone": build_cantilever_cone,
    # "cantilever_pyramid": build_cantilever_pyramid,
    # and so on for every variant.
}


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def generate_results_figure(structure_key, variant_key):
    """
    Dispatch to the correct figure builder.
    Falls back to a 'coming soon' placeholder if the variant has no builder.
    """
    builder = FIGURE_REGISTRY.get(variant_key)

    if builder is not None:
        return builder()

    fig = go.Figure()
    fig.add_annotation(
        text="3D view for this variant coming soon",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color="#f39c12", size=16),
    )
    return apply_common_layout(fig, 10.0)
