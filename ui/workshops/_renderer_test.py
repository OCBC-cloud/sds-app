# =============================================================================
# SDSe Fluid Design Studio - Renderer Test Recipe
# =============================================================================
# Step 2A of UI_ARCHITECTURE.md Part 9.
#
# Purpose: prove the universal workshop renderer
# (ui/workshops/_renderer.py) draws a page correctly.
#
# This file is TEMPORARY. It is deleted after the renderer is
# proven and the first real workshop is migrated.
#
# It defines one small recipe with:
#   - Two groups (Shape, Membrane).
#   - Four inputs: number, integer, dropdown, radio.
#   - One show_if on a conditional input.
#   - One preview callable.
#   - One warning callable.
#   - Viewer strings that write two session keys.
#
# Nothing here touches any real workshop. Nothing here feeds the
# engine. It is a drawing test.
#
# History:
#   2026-09-28 - First build. Step 2A.
# =============================================================================

import streamlit as st

from ui.workshops._renderer import render_workshop


def _preview_shape(state, prefix):
    """Show the current span and rise as a preview string."""
    span = state.get(prefix + "_span", 10.0)
    rise = state.get(prefix + "_rise", 3.0)
    ratio = 0.0
    if span and span > 0:
        ratio = rise / span
    return (
        'Span: <span class="num">' + ("%.2f" % span) + ' m</span>  |  '
        'Rise: <span class="num">' + ("%.2f" % rise) + ' m</span>  |  '
        'Rise/Span: <span class="num">' + ("%.3f" % ratio) + '</span>'
    )


def _warn_shape(state, prefix):
    """Warn if the rise/span ratio is out of the useful range."""
    span = state.get(prefix + "_span", 10.0)
    rise = state.get(prefix + "_rise", 3.0)
    if not span or span <= 0:
        return "Span must be greater than 0."
    ratio = rise / span
    if ratio < 0.05:
        return "Rise / Span ratio is very low. Membrane may not drain."
    if ratio > 0.5:
        return "Rise / Span ratio is very high. Check anchor capacity."
    return None


def _show_segmented_count(state, prefix):
    """Only show the attachment count when method is 'segmented'."""
    method = state.get(prefix + "_attach_method", "kader")
    return method == "segmented"


def _write_viewer_strings(state, prefix):
    """Write the two viewer strings the Results page reads."""
    span = state.get(prefix + "_span", 10.0)
    state[prefix + "_viewer_description"] = "Renderer test structure"
    state[prefix + "_viewer_dimensions"] = (
        "Span " + ("%.2f" % span) + " m"
    )







TEST_RECIPE = {
    "title": "Renderer Test",
    "breadcrumb": ("Test", "Renderer Test"),
    "structure_label": "Renderer Test Page",
    "prefix": "ws_rt",
    "defaults": {
        "span": 10.0,
        "rise": 3.0,
        "ribs": 5,
        "curve_type": "parabolic",
        "attach_method": "kader",
        "attach_count": 6,
    },
    "groups": [
        {
            "key": "shape",
            "name": "Shape",
            "help": "Overall dimensions of the test object.",
            "expanded": True,
            "inputs": [
                {
                    "key": "span",
                    "label": "Span (m)",
                    "type": "number",
                    "default": 10.0,
                    "min": 1.0,
                    "max": 200.0,
                    "step": 0.5,
                },
                {
                    "key": "rise",
                    "label": "Rise (m)",
                    "type": "number",
                    "default": 3.0,
                    "min": 0.5,
                    "max": 50.0,
                    "step": 0.1,
                },
                {
                    "key": "ribs",
                    "label": "Ribs per side",
                    "type": "integer",
                    "default": 5,
                    "min": 3,
                    "max": 12,
                    "step": 1,
                },
                {
                    "key": "curve_type",
                    "label": "Curve type",
                    "type": "dropdown",
                    "options": [
                        ["parabolic", "Parabolic"],
                        ["circular", "Circular"],
                        ["catenary", "Catenary"],
                    ],
                    "default": "parabolic",
                },
            ],
            "preview": _preview_shape,
            "warning": _warn_shape,
        },
        {
            "key": "membrane",
            "name": "Membrane",
            "help": "Attachment method. Conditional input test.",
            "inputs": [
                {
                    "key": "attach_method",
                    "label": "Attachment method",
                    "type": "radio",
                    "options": [
                        ["kader", "Kader (continuous)"],
                        ["segmented", "Segmented (discrete)"],
                    ],
                    "default": "kader",
                },
                {
                    "key": "attach_count",
                    "label": "Attachment points per side",
                    "type": "integer",
                    "default": 6,
                    "min": 2,
                    "max": 30,
                    "step": 1,
                    "show_if": _show_segmented_count,
                },
            ],
        },
    ],
    "viewer_strings": _write_viewer_strings,
    "actions": {
        "back_page": "studio",
        "primary_label": "Test Complete",
        "primary_page": "studio",
    },
}


def render_renderer_test():
    """Render the test page. Called by the navigation router."""
    render_workshop(TEST_RECIPE)





