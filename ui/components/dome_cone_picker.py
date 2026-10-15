# =============================================================================
# SDSe - Dome Multi-Cone Cone Picker (Streamlit Component)
# =============================================================================
# Python side of the 2D plan-view cone picker.
#
# The visual is rendered in index.html (same folder). An SVG canvas
# with a ground circle, frame grid lines, and a clickable toggle at
# every pickable position. JavaScript handles clicks and sends the
# picked set back to Python.
#
# Three kinds of pickable positions:
#   Crossings    where Family A meets Family B. Toggled by name.
#   A-midpoints  on a Family A frame, between two adjacent crossings.
#   B-midpoints  on a Family B frame, between two adjacent crossings.
#
# The picker is a pure input device. It knows nothing about physics.
# The viewer owns all geometry and reads the picked set.
#
# Pick format, in session state under ws_dm_picked_crossings:
#   ("C",  i, j)   crossing at frame i (A) and frame j (B)
#   ("Am", i, j)   on frame i (A), between crossings j and j+1
#   ("Bm", i, j)   on frame j (B), between crossings i and i+1
#
# Backward compatibility: old flat (i, j) tuples in session state
# are treated as crossings by the caller. This module normalises
# them here so the component always sees the three-tuple format.
#
# History:
#   2026-10-14 - First version. Real SVG picker, crossings only.
#   2026-10-14 - Piece 4. Add midpoint positions.
# =============================================================================

import os
import streamlit.components.v1 as components


# =============================================================================
# COMPONENT DECLARATION
# =============================================================================

_COMPONENT_DIR = os.path.dirname(__file__)

_dome_cone_picker_component = components.declare_component(
    "dome_cone_picker",
    path=_COMPONENT_DIR,
)


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _normalise_picked(picked):
    """
    Accept the picked set in either format and return a list of
    [kind, i, j] triples, sorted.

    Old format: (i, j) tuple           -> ("C", i, j)
    New format: (kind, i, j) tuple     -> used as-is

    Anything else is skipped silently.
    """
    out = []
    for item in picked:
        try:
            if len(item) == 3:
                kind = str(item[0])
                if kind not in ("C", "Am", "Bm"):
                    continue
                out.append([kind, int(item[1]), int(item[2])])
            elif len(item) == 2:
                out.append(["C", int(item[0]), int(item[1])])
        except (TypeError, ValueError):
            continue
    out.sort()
    return out


def _denormalise_picked(triples):
    """
    Convert the list of [kind, i, j] triples returned by the
    component back into a set of tuples, using the new format.
    """
    out = set()
    for item in triples:
        try:
            if len(item) != 3:
                continue
            kind = str(item[0])
            if kind not in ("C", "Am", "Bm"):
                continue
            out.add((kind, int(item[1]), int(item[2])))
        except (TypeError, ValueError):
            continue
    return out


# =============================================================================
# PUBLIC RENDER FUNCTION
# =============================================================================

def render_dome_cone_picker(dome_diameter, n_x, n_y, picked, key):
    """
    Render the 2D plan-view cone picker.

    Parameters
    ----------
    dome_diameter : float
    n_x : int   number of frames spaced along X (Family A)
    n_y : int   number of frames spaced along Y (Family B)
    picked : set of tuples
        The current picked set. Accepts both old (i, j) format and
        new (kind, i, j) format.
    key : str

    Returns
    -------
    set of (kind, i, j) tuples
        The picked set after the user's latest interaction. In the
        new three-tuple format.
    """
    picked_normalised = _normalise_picked(picked)

    result = _dome_cone_picker_component(
        dome_diameter=float(dome_diameter),
        n_x=int(n_x),
        n_y=int(n_y),
        picked=picked_normalised,
        key=key,
        default={"picked": picked_normalised},
    )

    if not result or "picked" not in result:
        return _denormalise_picked(picked_normalised)

    try:
        return _denormalise_picked(result["picked"])
    except (TypeError, ValueError):
        return _denormalise_picked(picked_normalised)


# =============================================================================
# END OF ui/components/dome_cone_picker.py
# =============================================================================
