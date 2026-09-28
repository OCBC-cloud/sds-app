# =============================================================================
# SDSe - Standard Saddle Recipe
# =============================================================================
# The workshop recipe for the Cable Supported Saddle variant.
#
# Read by ui/workshops/_renderer.py. Draws the input page.
#
# Groups follow the substructure scheme (SUBSTRUCTURES.md):
#   Shape, Membrane, Frame, Cables, Foundation, Loads
#
# Session-state keys are the existing ws_ss_* keys. No viewer
# changes needed.
#
# History:
#   2026-09-29 - First build. Step 2B of UI_ARCHITECTURE.md Part 9.
# =============================================================================

from data.materials import FABRIC_PROPERTIES
from data.constants import WIND_SPEEDS


# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULTS = {
    "span": 10.0,
    "apex": 15.0,
    "rise": 6.2,
    "curve_type": "parabolic",
    "steel_grade": "S355",
    "section_family": "CHS",
    "fabric_type": "PVDF",
    "fabric_grade": "Type III",
    "member_construction": "single_beam",
    "section_preference": "auto",
    "support_type_start": "pinned",
    "support_type_end": "pinned",
    "tiedown_intervals": 4,
    "uplift_angle": 45,
    "spread_angle": 30,
    "cable_type": "6x19",
    "cable_material": "galvanised",
    "anchor_type": "pinned",
    "warp_pretension": 2.0,
    "weft_pretension": 2.0,
    "edge_cable_pretension": 5.0,
    "soil_bearing": 150.0,
    "soil_type": "sand",
    "water_table": 3.0,
    "foundation_type": "pad",
    "found_widget_generation": 0,
    "add_payload": 0.0,
    "design_standard": "MY",
    "attachment_type": "kader",
    "cable_attachment_count": 6,
    "viewer_description": "Standard Saddle Span tensile membrane structure",
    "viewer_dimensions": "",
}


# =============================================================================
# PREVIEW / WARNING HELPERS
# =============================================================================

def _warn_shape(state, prefix):
    """Warn if the rise/span ratio is out of the useful range."""
    span = state.get(prefix + "_span", 10.0)
    rise = state.get(prefix + "_rise", 6.2)
    msgs = []
    if span <= 0:
        msgs.append("Span must be greater than 0.")
    if rise <= 0:
        msgs.append("Rise must be greater than 0.")
    if span > 0 and rise > 0:
        ratio = rise / span
        if ratio < 0.05:
            msgs.append("Rise / Span ratio is very low. Membrane may not drain.")
        elif ratio > 0.5:
            msgs.append("Rise / Span ratio is very high. Check anchor capacity.")
    return "<br>".join(msgs) if msgs else None


def _preview_pretension(state, prefix):
    """Show the current pretension triad."""
    warp = state.get(prefix + "_warp_pretension", 2.0)
    weft = state.get(prefix + "_weft_pretension", 2.0)
    edge = state.get(prefix + "_edge_cable_pretension", 5.0)
    return (
        'Warp: <span class="num">' + ("%.1f" % warp) + ' kN/m</span>  |  '
        'Weft: <span class="num">' + ("%.1f" % weft) + ' kN/m</span>  |  '
        'Edge cable: <span class="num">' + ("%.1f" % edge) + ' kN</span>'
    )


def _preview_segmented_spacing(state, prefix):
    """Show the approximate spacing between cable attachments."""
    span = state.get(prefix + "_span", 10.0)
    n_attach = state.get(prefix + "_cable_attachment_count", 6)
    if n_attach < 1:
        return None
    approx_seg = span / n_attach
    return (
        'Attachment points per beam: <span class="num">'
        + str(n_attach) + '</span><br>'
        'Approximate spacing between attachments: <span class="num">'
        + ("%.2f m" % approx_seg) + '</span><br>'
        'Cable bow between attachments is controlled by the '
        'edge cable pretension.'
    )


def _preview_wind(state, prefix):
    """Show the design wind speed for the chosen standard."""
    std = state.get(prefix + "_design_standard", "MY")
    wind = WIND_SPEEDS.get(std, 30.0)
    return 'Wind speed basis: <span class="num">' + str(wind) + ' m/s</span>'


def _show_segmented_count(state, prefix):
    """Show the attachment count only when segmented is chosen."""
    return state.get(prefix + "_attachment_type", "kader") == "segmented"


def _write_viewer_strings(state, prefix):
    """Write the two viewer strings read by the Results page."""
    rise = state.get(prefix + "_rise", 6.2)
    state[prefix + "_viewer_description"] = (
        "Standard Saddle Span tensile membrane structure"
    )
    state[prefix + "_viewer_dimensions"] = (
        "Total height " + ("%.2f" % rise) + " m"
    )






# =============================================================================
# THE RECIPE
# =============================================================================

STANDARD_SADDLE_RECIPE = {
    "title": "Standard Saddle Span",
    "breadcrumb": ("Saddle Span", "Standard Saddle"),
    "structure_label": "Standard Saddle Span",
    "prefix": "ws_ss",
    "defaults": DEFAULTS,
    "groups": [

        # ---- SHAPE -----------------------------------------------------
        {
            "key": "shape",
            "name": "Shape",
            "help": "Overall dimensions of the saddle span.",
            "expanded": True,
            "inputs": [
                {
                    "key": "span",
                    "label": "Span Distance (m) *",
                    "type": "number",
                    "default": 10.0,
                    "min": 4.0,
                    "max": 200.0,
                    "step": 0.5,
                },
                {
                    "key": "apex",
                    "label": "Apex-to-Apex Distance (m) *",
                    "type": "number",
                    "default": 15.0,
                    "min": 4.0,
                    "max": 200.0,
                    "step": 0.5,
                },
                {
                    "key": "rise",
                    "label": "Rise (m) *",
                    "type": "number",
                    "default": 6.2,
                    "min": 0.5,
                    "max": 50.0,
                    "step": 0.1,
                },
                {
                    "key": "curve_type",
                    "label": "Beam Curve Type",
                    "type": "dropdown",
                    "options": [
                        ["parabolic", "Parabolic"],
                        ["circular", "Circular"],
                        ["catenary", "Catenary"],
                    ],
                    "default": "parabolic",
                },
            ],
            "warning": _warn_shape,
        },

        # ---- MEMBRANE --------------------------------------------------
        {
            "key": "membrane",
            "name": "Membrane",
            "help": "Fabric type, grade, and attachment method.",
            "inputs": [
                {
                    "key": "fabric_type",
                    "label": "Fabric Type",
                    "type": "dropdown",
                    "options": [
                        ["PVDF", "PVDF"],
                        ["PTFE", "PTFE"],
                        ["ETFE", "ETFE"],
                    ],
                    "default": "PVDF",
                },
                {
                    "key": "fabric_grade",
                    "label": "Fabric Grade",
                    "type": "dropdown",
                    "options": [
                        ["Type I", "Type I"],
                        ["Type II", "Type II"],
                        ["Type III", "Type III"],
                        ["Type IV", "Type IV"],
                    ],
                    "default": "Type III",
                },
                {
                    "key": "attachment_type",
                    "label": "Attachment Method",
                    "type": "radio",
                    "options": [
                        ["kader", "Kader Guider (continuous attachment)"],
                        ["segmented", "Segmented Edge (discrete cable supports)"],
                    ],
                    "default": "kader",
                },
                {
                    "key": "cable_attachment_count",
                    "label": "Cable Attachment Points per Beam",
                    "type": "integer",
                    "default": 6,
                    "min": 2,
                    "max": 30,
                    "step": 1,
                    "show_if": _show_segmented_count,
                    "help": "How many discrete cable support points hold the "
                            "fabric edge along each beam.",
                },
            ],
            "preview": _preview_segmented_spacing,
        },

        # ---- FRAME -----------------------------------------------------
        {
            "key": "frame",
            "name": "Frame",
            "help": "Steel grade, section family, member construction, and supports.",
            "inputs": [
                {
                    "key": "steel_grade",
                    "label": "Steel Grade",
                    "type": "dropdown",
                    "options": [
                        ["S235", "S235"],
                        ["S275", "S275"],
                        ["S355", "S355"],
                        ["S420", "S420"],
                        ["S460", "S460"],
                    ],
                    "default": "S355",
                },
                {
                    "key": "section_family",
                    "label": "Section Family",
                    "type": "dropdown",
                    "options": [
                        ["CHS", "CHS"],
                        ["SHS", "SHS"],
                        ["RHS", "RHS"],
                        ["I-Beam", "I-Beam"],
                    ],
                    "default": "CHS",
                },
                {
                    "key": "member_construction",
                    "label": "Member Construction",
                    "type": "radio",
                    "options": [
                        ["single_beam", "Single Beam"],
                        ["planar_truss", "Planar Truss"],
                        ["space_truss", "Space Truss"],
                    ],
                    "default": "single_beam",
                },
                {
                    "key": "support_type_start",
                    "label": "Support at Start End",
                    "type": "radio",
                    "options": [
                        ["pinned", "Pinned"],
                        ["rigid", "Rigid"],
                    ],
                    "default": "pinned",
                },
                {
                    "key": "support_type_end",
                    "label": "Support at Far End",
                    "type": "radio",
                    "options": [
                        ["pinned", "Pinned"],
                        ["rigid", "Rigid"],
                    ],
                    "default": "pinned",
                },
            ],
        },





        
        # ---- CABLES ----------------------------------------------------
        {
            "key": "cables",
            "name": "Cables",
            "help": "Tie-down cables and the pretension triad.",
            "inputs": [
                {
                    "key": "tiedown_intervals",
                    "label": "Number of Tie-down Cables",
                    "type": "radio",
                    "options": [
                        [4, "4 cables"],
                        [8, "8 cables"],
                    ],
                    "default": 4,
                },
                {
                    "key": "uplift_angle",
                    "label": "Anchor Uplift Angle (deg)",
                    "type": "integer",
                    "default": 45,
                    "min": 20,
                    "max": 75,
                    "step": 1,
                },
                {
                    "key": "spread_angle",
                    "label": "Anchor Spread Angle (deg)",
                    "type": "integer",
                    "default": 30,
                    "min": 0,
                    "max": 60,
                    "step": 1,
                },
                {
                    "key": "cable_type",
                    "label": "Cable Type",
                    "type": "dropdown",
                    "options": [
                        ["6x19", "6x19"],
                        ["Locked Coil", "Locked Coil"],
                        ["Spiral", "Spiral"],
                    ],
                    "default": "6x19",
                },
                {
                    "key": "cable_material",
                    "label": "Cable Material",
                    "type": "dropdown",
                    "options": [
                        ["galvanised", "Galvanised"],
                        ["stainless", "Stainless"],
                    ],
                    "default": "galvanised",
                },
                {
                    "key": "anchor_type",
                    "label": "Ground Anchor Type",
                    "type": "radio",
                    "options": [
                        ["pinned", "Pinned"],
                        ["rigid", "Rigid"],
                    ],
                    "default": "pinned",
                },
                {
                    "key": "warp_pretension",
                    "label": "Warp Pretension (kN/m)",
                    "type": "number",
                    "default": 2.0,
                    "min": 0.5,
                    "max": 8.0,
                    "step": 0.1,
                    "help": "Along the span, following the beams.",
                },
                {
                    "key": "weft_pretension",
                    "label": "Weft Pretension (kN/m)",
                    "type": "number",
                    "default": 2.0,
                    "min": 0.5,
                    "max": 8.0,
                    "step": 0.1,
                    "help": "Across the membrane, between the two beams.",
                },
                {
                    "key": "edge_cable_pretension",
                    "label": "Edge Cable Pretension (kN)",
                    "type": "number",
                    "default": 5.0,
                    "min": 0.5,
                    "max": 50.0,
                    "step": 0.5,
                    "help": "Along the two free ends.",
                },
            ],
            "preview": _preview_pretension,
        },

        # ---- FOUNDATION ------------------------------------------------
        {
            "key": "foundation",
            "name": "Foundation",
            "help": "Preliminary sizing. Geotechnical verification required.",
            "inputs": [
                {
                    "key": "soil_bearing",
                    "label": "Assumed Soil Bearing Capacity (kN/m2)",
                    "type": "number",
                    "default": 150.0,
                    "min": 50.0,
                    "max": 1000.0,
                    "step": 10.0,
                },
                {
                    "key": "water_table",
                    "label": "Water Table Depth (m)",
                    "type": "number",
                    "default": 3.0,
                    "min": 0.5,
                    "max": 20.0,
                    "step": 0.5,
                },
                {
                    "key": "soil_type",
                    "label": "Soil Type",
                    "type": "dropdown",
                    "options": [
                        ["sand", "Sand"],
                        ["clay", "Clay"],
                        ["rock", "Rock"],
                        ["filled", "Filled / Made Ground"],
                    ],
                    "default": "sand",
                },
                {
                    "key": "foundation_type",
                    "label": "Foundation Type",
                    "type": "dropdown",
                    "options": [
                        ["pad", "Pad Footing"],
                        ["pile", "Pile Group"],
                        ["raft", "Raft"],
                    ],
                    "default": "pad",
                },
            ],
            "defaults": {
                "soil_bearing": 150.0,
                "soil_type": "sand",
                "water_table": 3.0,
                "foundation_type": "pad",
            },
        },

        # ---- LOADS -----------------------------------------------------
        {
            "key": "loads",
            "name": "Loads",
            "help": "User-added loads and design code for safety factors.",
            "inputs": [
                {
                    "key": "add_payload",
                    "label": "Add. Pay Load (kg/m)",
                    "type": "number",
                    "default": 0.0,
                    "min": 0.0,
                    "max": 500.0,
                    "step": 5.0,
                },
                {
                    "key": "design_standard",
                    "label": "Design Standard",
                    "type": "dropdown",
                    "options": [
                        ["EU", "EU"],
                        ["MY", "MY"],
                        ["UK", "UK"],
                        ["CN", "CN"],
                        ["US", "US"],
                    ],
                    "default": "MY",
                },
            ],
            "preview": _preview_wind,
        },
    ],

    "viewer_strings": _write_viewer_strings,

    "actions": {
        "back_page": "registration",
        "primary_label": "Intelligent Design Computing",
        "primary_page": "results",
    },
}


# =============================================================================
# END OF data/recipes/standard_saddle.py
# =============================================================================





