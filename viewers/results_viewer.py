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
#
# Updated 2026-09-19 (evening, third pass):
#   After the figure is built, two amber annotations are added
#   inside the plot area (bottom-centre, above the legend):
#     - viewer description line
#     - viewer dimensions line
#   These strings are written to session state by the active
#   workshop under a per-variant prefix. They are read here and
#   drawn into the figure so a screenshot of the chart captures
#   the structure name and dimensions for the external renderer.
# =============================================================================

import plotly.graph_objects as go

import streamlit as st

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
# WORKSHOP PREFIX MAP
# =============================================================================
# The active workshop writes two strings under its own prefix:
#   ws_<prefix>_viewer_description
#   ws_<prefix>_viewer_dimensions
# They are drawn onto the figure so a screenshot of the chart
# captures them.

VARIANT_PREFIX = {
    "cantilever_leaf": "ws_sl_",
    "standard_saddle": "ws_ss_",
    "frame_supported_saddle": "ws_bs_",
}

AMBER = "#f39c12"


# =============================================================================
# VIEWER-STRING ANNOTATIONS
# =============================================================================

def _add_viewer_strings(fig, variant_key):
    """
    Draw the workshop's description and dimensions strings inside the
    plot area, bottom-centre, amber, just above the legend.

    Uses paper coordinates (xref='paper', yref='paper') so the text
    stays anchored to the chart frame regardless of the data range.
    """
    prefix = VARIANT_PREFIX.get(variant_key)
    if not prefix:
        return

    desc = st.session_state.get(prefix + "viewer_description", "") or ""
    dims = st.session_state.get(prefix + "viewer_dimensions", "") or ""

    if not desc and not dims:
        return

    # Y positions in paper coords. Legend sits at the very bottom of
    # the plot area. We stack the two lines just above the legend.
    y_desc = 0.055
    y_dims = 0.010

    if desc:
        fig.add_annotation(
            text=desc,
            xref="paper", yref="paper",
            x=0.5, y=y_desc,
            showarrow=False,
            font=dict(color=AMBER, size=13, family="sans-serif"),
            align="center",
            xanchor="center",
            yanchor="bottom",
        )

    if dims:
        fig.add_annotation(
            text=dims,
            xref="paper", yref="paper",
            x=0.5, y=y_dims,
            showarrow=False,
            font=dict(color=AMBER, size=13, family="sans-serif"),
            align="center",
            xanchor="center",
            yanchor="bottom",
        )


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def generate_results_figure(structure_key, variant_key):
    """
    Dispatch to the correct figure builder, then add the workshop's
    viewer strings as in-plot annotations.

    Falls back to a 'coming soon' placeholder if the variant has no builder.
    """
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
