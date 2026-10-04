# =============================================================================
# SDSe - Standard Saddle Recipe
# =============================================================================
# The workshop recipe for the Cable Supported Saddle variant.
#
# Read by ui/workshops/_renderer.py. Draws the input page.
#
# Groups follow the substructure scheme (SUBSTRUCTURES.md):
#   Shape, Membrane, Frame, Cables (Tie-down), Cables (Edge),
#   Foundation, Loads
#
# Session-state keys are the existing ws_ss_* keys.
#
# History:
#   2026-09-29 - First build. Step 2B of UI_ARCHITECTURE.md Part 9.
#   2026-10-04 - Step 2E. Three Shape inputs added:
#                anchor_count, mesh_spacing, transverse_count.
#                Cable group split into Tie-down and Edge.
#                Three inputs per cable group:
#                type, material, pretension.
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
    "anchor_count": 8,
    "mesh_spacing": 0.5,
    "transverse_count": 8,
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
    "tiedown_cable_type": "6x19",
    "tiedown_cable_material": "galvanised",
    "tiedown_pretension": 2.5,
    "anchor_type": "pinned",
    "edge_cable_type": "6x19",
    "edge_cable_material": "stainless",
    "edge_cable_pretension": 5.0,
    "warp_pretension": 1.0,
    "weft_pretension": 1.0,
    "soil_bearing": 150.0,
    "soil_type": "sand",
    "water_table": 3.0,
    "foundation_type": "pad",
    "found_widget_generation": 0,
    "add_payload": 0.0,
    "design_standard": "MY",
    "attachment_type": "kader",
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
    warp = state.get(prefix + "_warp_pretension", 1.0)
    weft = state.get(prefix + "_weft_pretension", 1.0)
    return (
        'Warp: <span class="num">' + ("%.1f" % warp) + ' kN/m</span>  |  '
        'Weft: <span class="num">' + ("%.1f" % weft) + ' kN/m</span>'
    )


def _preview_shape_mesh(state, prefix):
    """Show the mesh spacing implied by the Shape inputs."""
    span = state.get(prefix + "_span", 10.0)
    anchor_count = state.get(prefix + "_anchor_count", 8)
    mesh_spacing = state.get(prefix + "_mesh_spacing", 0.5)
    if anchor_count < 3:
        anchor_count = 3
    if mesh_spacing <= 0:
        mesh_spacing = 0.5
    beam_len = span * 1.10
    seg_len = beam_len / (anchor_count - 1)
    sub = max(1, int(round(seg_len / mesh_spacing)))
    interior_points_per_beam = (anchor_count - 2) * sub
    total_loop = 2 * (anchor_count + interior_points_per_beam)
    return (
        'Anchors per beam: <span class="num">'
        + str(anchor_count) + '</span><br>'
        'Approx segment length: <span class="num">'
        + ("%.2f m" % seg_len) + '</span><br>'
        'Subdivision per segment: <span class="num">'
        + str(sub) + '</span>'
    )


def _preview_edge_cable(state, prefix):
    """Show the current edge cable settings."""
    ctype = state.get(prefix + "_edge_cable_type", "6x19")
    cmat = state.get(prefix + "_edge_cable_material", "stainless")
    cpre = state.get(prefix + "_edge_cable_pretension", 5.0)
    return (
        'Type: <span class="num">' + str(ctype) + '</span>  |  '
        'Material: <span class="num">' + str(cmat) + '</span>  |  '
        'Prestress: <span class="num">' + ("%.1f" % cpre) + ' kN</span>'
    )


def _preview_tiedown_cable(state, prefix):
    """Show the current tie-down cable settings."""
    ctype = state.get(prefix + "_tiedown_cable_type", "6x19")
    cmat = state.get(prefix + "_tiedown_cable_material", "galvanised")
    cpre = state.get(prefix + "_tiedown_pretension", 2.5)
    n = state.get(prefix + "_tiedown_intervals", 4)
    return (
        'Cables: <span class="num">' + str(n) + '</span>  |  '
        'Type: <span class="num">' + str(ctype) + '</span>  |  '
        'Material: <span class="num">' + str(cmat) + '</span>  |  '
        'Prestress: <span class="num">' + ("%.1f" % cpre) + ' kN</span>'
    )


def _preview_wind(state, prefix):
    """Show the design wind speed for the chosen standard."""
    std = state.get(prefix + "_design_standard", "MY")
    wind = WIND_SPEEDS.get(std, 30.0)
    return 'Wind speed basis: <span class="num">' + str(wind) + ' m/s</span>'


def _show_edge_cable(state, prefix):
    """Show the Edge Cable group only when attachment is cable_supported."""
    return state.get(prefix + "_attachment_type", "kader") == "cable_supported"


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
            "help": "Overall dimensions and mesh density.",
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
                {
                    "key": "anchor_count",
                    "label": "Anchors per Beam",
                    "type": "integer",
                    "default": 8,
                    "min": 3,
                    "max": 40,
                    "step": 1,
                    "help": "Number of discrete fabric attachment points along "
                            "each beam. Used when Cable Supported is active.",
                },
                {
                    "key": "mesh_spacing",
                    "label": "Mesh Spacing (m)",
                    "type": "number",
                    "default": 0.5,
                    "min": 0.1,
                    "max": 5.0,
                    "step": 0.1,
                    "help": "Interior mesh density between anchors.",
                },
                {
                    "key": "transverse_count",
                    "label": "Transverse Division",
                    "type": "integer",
                    "default": 8,
                    "min": 2,
                    "max": 20,
                    "step": 1,
                    "help": "Reserved for future use. Not applied yet.",
                },
            ],
            "warning": _warn_shape,
            "preview": _preview_shape_mesh,
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
                        ["cable_supported", "Cable Supported (discrete anchors)"],
                    ],
                    "default": "kader",
                },
            ],
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

        # ---- CABLES (TIE-DOWN) ----------------------------------------
        {
            "key": "cables_tiedown",
            "name": "Cables (Tie-down)",
            "help": "Ground tie-down cables. Carry uplift. Independent "
                    "of the attachment method.",
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
                    "key": "tiedown_cable_type",
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
                    "key": "tiedown_cable_material",
                    "label": "Cable Material",
                    "type": "dropdown",
                    "options": [
                        ["galvanised", "Galvanised"],
                        ["stainless", "Stainless"],
                    ],
                    "default": "galvanised",
                },
                {
                    "key": "tiedown_pretension",
                    "label": "Tie-down Pretension (kN)",
                    "type": "number",
                    "default": 2.5,
                    "min": 0.1,
                    "max": 500.0,
                    "step": 0.5,
                },
            ],
            "preview": _preview_tiedown_cable,
        },

        # ---- CABLES (EDGE) --------------------------------------------
        {
            "key": "cables_edge",
            "name": "Cables (Edge)",
            "help": "The roof edge cable. Runs between the anchors along "
                    "each beam. Active when Cable Supported is chosen.",
            "inputs": [
                {
                    "key": "edge_cable_type",
                    "label": "Cable Type",
                    "type": "dropdown",
                    "options": [
                        ["6x19", "6x19"],
                        ["Locked Coil", "Locked Coil"],
                        ["Spiral", "Spiral"],
                    ],
                    "default": "6x19",
                    "show_if": _show_edge_cable,
                },
                {
                    "key": "edge_cable_material",
                    "label": "Cable Material",
                    "type": "dropdown",
                    "options": [
                        ["stainless", "Stainless"],
                        ["galvanised", "Galvanised"],
                    ],
                    "default": "stainless",
                    "show_if": _show_edge_cable,
                },
                {
                    "key": "edge_cable_pretension",
                    "label": "Edge Cable Pretension (kN)",
                    "type": "number",
                    "default": 5.0,
                    "min": 0.1,
                    "max": 500.0,
                    "step": 0.5,
                    "show_if": _show_edge_cable,
                },
            ],
            "preview": _preview_edge_cable,
        },

        # ---- MEMBRANE PRETENSION --------------------------------------
        {
            "key": "pretension",
            "name": "Membrane Pretension",
            "help": "The membrane warp and weft prestress. Drives the "
                    "shape via FDM.",
            "inputs": [
                {
                    "key": "warp_pretension",
                    "label": "Warp Pretension (kN/m)",
                    "type": "number",
                    "default": 1.0,
                    "min": 0.1,
                    "max": 100.0,
                    "step": 0.1,
                    "help": "Along the span, following the beams.",
                },
                {
                    "key": "weft_pretension",
                    "label": "Weft Pretension (kN/m)",
                    "type": "number",
                    "default": 1.0,
                    "min": 0.1,
                    "max": 100.0,
                    "step": 0.1,
                    "help": "Across the membrane, between the two beams.",
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
