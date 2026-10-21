# =============================================================================
# SDSe - Universal Pickerboard Wrapper
# =============================================================================
# Python side of the universal 2D plan-view picker.
# Serves Leaf, Hypar, and future shapes.
# =============================================================================

import os
import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.dirname(__file__)

# Points to the 'pickerboard' folder we just created
_SDSe_pickerboard_component = components.declare_component(
    "SDSe_pickerboard",
    path=os.path.join(_COMPONENT_DIR, "pickerboard"),
)


def render_pickerboard(shape, reach, width, rib_reach, rib_lengths, key):
    """
    Render the universal 2D plan-view picker.
    """
    result = _SDSe_pickerboard_component(
        shape=str(shape),
        reach=float(reach),
        width=float(width),
        rib_reach=float(rib_reach),
        rib_lengths=list(rib_lengths),
        key=key,
        default={"rib_lengths": list(rib_lengths)},
    )

    if not result or "rib_lengths" not in result:
        return list(rib_lengths)

    try:
        return [float(v) for v in result["rib_lengths"]]
    except (TypeError, ValueError):
        return list(rib_lengths)


# =============================================================================
# END OF ui/components/SDSe_pickerboard.py
# =============================================================================
