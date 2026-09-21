# =============================================================================
# SDSe Fluid Design Studio - Results Viewer Dispatcher
# =============================================================================
# Looks up the correct figure builder for a given variant and calls it.
# Each variant has its own builder file under viewers/figures/.
#
# Dispatch rule:
#   Variant keys are globally unique. The dispatcher ignores
#   structure_key entirely and routes on variant_key alone.
#
# Variant keys (internal, never changed):
#   "standard_saddle"          -> Cable Supported Saddle
#   "frame_supported_saddle"   -> Beam Supported Saddle
#   "cantilever_leaf"          -> Cantilever Leaf
#   "cantilever_hypar"         -> Cantilever Hypar
#
# Updated 2026-09-21:
#   - Cantilever Hypar registered.
# Updated 2026-09-21:
#   - Annotation font size 13 -> 8, to match legend.
# =============================================================================

import plotly.graph_objects as go

import streamlit as st

from viewers.figures._shared import apply_common_layout
from viewers.figures.standard_saddle import build_standard_saddle
from viewers.figures.cantilever_leaf import build_cantilever_leaf
from viewers.figures.beam_supported_saddle import build_beam_supported_saddle
from viewers.figures.cantilever_hypar import build_cantilever_hypar


# =============================================================================
# FIGURE REGISTRY
# =============================================================================

FIGURE_REGISTRY = {
    "standard_saddle": build_standard_saddle,
    "cantilever_leaf": build_cantilever_leaf,
    "frame_supported_saddle": build_beam_supported_saddle,
    "cantilever_hypar": build_cantilever_hypar,
}


# =============================================================================
# WORKSHOP PREFIX MAP
# =============================================================================

VARIANT_PREFIX = {
    "cantilever_leaf": "ws_sl_",
    "standard_saddle": "ws_ss_",
    "frame_supported_saddle": "ws_bs_",
    "cantilever_hypar": "ws_ch_",
}

AMBER = "#f39c12"

ANNOTATION_FONT_SIZE = 8


# =============================================================================
# VIEWER-STRING ANNOTATIONS
# =============================================================================

def _add_viewer_strings(fig, variant_key):
    """Draw the workshop's description and dimensions strings inside the plot."""
    prefix = VARIANT_PREFIX.get(variant_key)
    if not prefix:
        return

    desc = st.session_state.get(prefix + "viewer_description", "") or ""
    dims = st.session_state.get(prefix + "viewer_dimensions", "") or ""

    if not desc and not dims:
        return

    y_desc = 0.055
    y_dims = 0.010

    if desc:
        fig.add_annotation(
            text=desc,
            xref="paper", yref="paper",
            x=0.5, y=y_desc,
            showarrow=False,
            font=dict(color=AMBER, size=ANNOTATION_FONT_SIZE, family="sans-serif"),
            align="center", xanchor="center", yanchor="bottom",
        )

    if dims:
        fig.add_annotation(
            text=dims,
            xref="paper", yref="paper",
            x=0.5, y=y_dims,
            showarrow=False,
            font=dict(color=AMBER, size=ANNOTATION_FONT_SIZE, family="sans-serif"),
            align="center", xanchor="center", yanchor="bottom",
        )


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def generate_results_figure(structure_key, variant_key):
    """Dispatch to the correct figure builder, then add viewer strings."""
    builder = FIGURE_REGISTRY.get(variant_key)

    if builder is not None:
        fig = builder()
        _add_viewer_strings(fig, variant_key)
        return fig

    fig = go.Figure()
    fig.add_annotation(
        text="3D view for this variant coming soon",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=AMBER, size=16),
    )
    return apply_common_layout(fig, 10.0)





