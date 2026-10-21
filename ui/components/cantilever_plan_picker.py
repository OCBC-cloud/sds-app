# =============================================================================
# SDSe - Cantilever Plan Picker (Streamlit Component)
# =============================================================================
# Python side of the 2D plan-view picker for Cantilever Leaf and Hypar.
# =============================================================================

import os
import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.dirname(__file__)

_cantilever_plan_picker_component = components.declare_component(
    "cantilever_plan_picker",
    path=_COMPONENT_DIR,
)


def render_cantilever_plan_picker(structure_type, reach, width, rib_reach, rib_lengths, key):
    """
    Render the 2D plan-view picker for the Cantilever structures.
    """
    result = _cantilever_plan_picker_component(
        structure_type=str(structure_type),
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
# END OF ui/components/cantilever_plan_picker.py
# =============================================================================
