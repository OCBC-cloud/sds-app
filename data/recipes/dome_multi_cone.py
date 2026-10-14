# =============================================================================
# SDSe - Dome Multi-Cone Roof Recipe
# =============================================================================
# Recipe for the Dome Multi-Cone workshop.
# Read by ui/workshops/_renderer.py to build the input page.
#
# Schema follows data/recipes/standard_saddle.py exactly:
#   - Only the five allowed input types
#   - No custom widgets
#
# History:
#   2026-10-13 - First version. Dome geometry generator driven by
#                meridian beams on a globe grid.
#   2026-10-14 - Renamed the two meridian count inputs. They control
#                how many frames are SPACED along each axis, not the
#                direction each frame runs. Labels now say "Frames
#                along X" and "Frames along Y" and the help text
#                explains what each frame actually does.
# =============================================================================

DOME_MULTI_CONE_RECIPE = {
    "title": "Dome Multi-Cone Roof",
    "breadcrumb": ("Multi-Cone Roof", "Dome Multi-Cone"),
    "structure_label": "Dome Multi-Cone",
    "prefix": "ws_dm",

    "defaults": {
        # Group 1 - Dome shape
        "dome_diameter": 18.0,
        "crown_height": 9.0,
        "ground_outline": "circle",
        "base_width_x": 18.0,
        "base_width_y": 18.0,
        "meridians_x": 5,
        "meridians_y": 5,
        "eave_height": 3.2,
        "curve_type": "parabolic",

        # Group 2 - Cone placement
        "placement_mode": "automatic",
        "cone_count": 4,
        "cone_ring_radius": 0.6,
        "cone_start_angle": 0.0,
        "drop_length": 1.0,
        "ring_diameter": 2.0,
        "min_member_length": 3.6,
        "min_ring_gap": 1.8,
        "min_eave_clearance": 2.7,

        # Group 3 - Prestress
        "warp_pretension": 1.0,
        "weft_pretension": 1.0,
        "edge_cable_pretension": 25.0,
        "grid_pretension": 20.0,

        # Group 4 - Materials
        "fabric_type": "PVDF",
        "fabric_grade": "Type III",
        "meridian_material": "S355",
        "ring_material": "S355",

        # Group 5 - Foundation
        "base_condition": "pinned",

        # Group 6 - Load case
        "load_standard": "MY",
    },

    "groups": [

        # =====================================================================
        # GROUP 1 - DOME SHAPE
        # =====================================================================
        {
            "key": "dome_shape",
            "name": "1. Dome Shape",
            "expanded": True,
            "help": "Footprint, height, frame grid, eave, and beam curve.",
            "inputs": [
                {
                    "key": "dome_diameter",
                    "label": "Dome diameter (m)",
                    "type": "number",
                    "default": 18.0,
                    "min": 3.0,
                    "max": 200.0,
                    "step": 0.5,
                },
                {
                    "key": "crown_height",
                    "label": "Crown height above ground (m)",
                    "type": "number",
                    "default": 9.0,
                    "min": 1.0,
                    "max": 60.0,
                    "step": 0.5,
                },
                {
                    "key": "ground_outline",
                    "label": "Ground outline",
                    "type": "dropdown",
                    "options": [
                        ["circle", "Circle"],
                        ["ellipse", "Ellipse"],
                        ["oval", "Oval"],
                    ],
                    "default": "circle",
                },
                {
                    "key": "base_width_x",
                    "label": "Base width X (m)",
                    "type": "number",
                    "default": 18.0,
                    "min": 3.0,
                    "max": 200.0,
                    "step": 0.5,
                },
                {
                    "key": "base_width_y",
                    "label": "Base width Y (m)",
                    "type": "number",
                    "default": 18.0,
                    "min": 3.0,
                    "max": 200.0,
                    "step": 0.5,
                },
                {
                    "key": "meridians_x",
                    "label": "Frames along X",
                    "type": "integer",
                    "default": 5,
                    "min": 3,
                    "max": 40,
                    "step": 1,
                    "help": "Number of frames spaced along the X axis. "
                            "Each frame runs along Y (its curve lies in "
                            "the YZ plane).",
                },
                {
                    "key": "meridians_y",
                    "label": "Frames along Y",
                    "type": "integer",
                    "default": 5,
                    "min": 3,
                    "max": 40,
                    "step": 1,
                    "help": "Number of frames spaced along the Y axis. "
                            "Each frame runs along X (its curve lies in "
                            "the XZ plane).",
                },
                {
                    "key": "eave_height",
                    "label": "Eave height (m)",
                    "type": "number",
                    "default": 3.2,
                    "min": 0.5,
                    "max": 40.0,
                    "step": 0.1,
                    "help": "Where the membrane stops. Below this, no fabric.",
                },
                {
                    "key": "curve_type",
                    "label": "Beam curve",
                    "type": "dropdown",
                    "options": [
                        ["parabolic", "Parabolic"],
                        ["circular", "Circular"],
                        ["catenary", "Catenary"],
                    ],
                    "default": "parabolic",
                },
            ],
        },

        # =====================================================================
        # GROUP 2 - CONE PLACEMENT
        # =====================================================================
        {
            "key": "cone_placement",
            "name": "2. Cone Placement",
            "expanded": True,
            "help": "How many cones, where they hang, and the rules "
                    "for automatic placement.",
            "inputs": [
                {
                    "key": "placement_mode",
                    "label": "Placement mode",
                    "type": "radio",
                    "options": [
                        ["automatic", "Automatic (solver chooses count)"],
                        ["user_defined", "User-defined count"],
                    ],
                    "default": "automatic",
                },
                {
                    "key": "cone_count",
                    "label": "Number of cones (user-defined mode)",
                    "type": "integer",
                    "default": 4,
                    "min": 1,
                    "max": 40,
                    "step": 1,
                    "help": "Only used when placement mode is User-defined.",
                },
                {
                    "key": "cone_ring_radius",
                    "label": "Cone ring radius (fraction of dome radius)",
                    "type": "number",
                    "default": 0.6,
                    "min": 0.1,
                    "max": 0.95,
                    "step": 0.05,
                    "help": "Where cones sit relative to the crown. "
                            "0.6 means 60% out from centre.",
                },
                {
                    "key": "cone_start_angle",
                    "label": "Start angle (deg)",
                    "type": "number",
                    "default": 0.0,
                    "min": 0.0,
                    "max": 90.0,
                    "step": 5.0,
                    "help": "Rotation of the symmetric cone layout.",
                },
                {
                    "key": "drop_length",
                    "label": "Drop length below crossing (m)",
                    "type": "number",
                    "default": 1.0,
                    "min": 0.1,
                    "max": 10.0,
                    "step": 0.1,
                },
                {
                    "key": "ring_diameter",
                    "label": "Ring diameter (m)",
                    "type": "number",
                    "default": 2.0,
                    "min": 0.05,
                    "max": 10.0,
                    "step": 0.05,
                },
                {
                    "key": "min_member_length",
                    "label": "Min member length (m, 0 = no rule)",
                    "type": "number",
                    "default": 3.6,
                    "min": 0.0,
                    "max": 20.0,
                    "step": 0.1,
                    "help": "In automatic mode, cones closer than this are skipped.",
                },
                {
                    "key": "min_ring_gap",
                    "label": "Min ring gap (m, 0 = no rule)",
                    "type": "number",
                    "default": 1.8,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                },
                {
                    "key": "min_eave_clearance",
                    "label": "Min eave clearance (m, 0 = no rule)",
                    "type": "number",
                    "default": 2.7,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                },
            ],
        },

        # =====================================================================
        # GROUP 3 - PRESTRESS
        # =====================================================================
        {
            "key": "prestress",
            "name": "3. Prestress",
            "help": "Membrane warp and weft, edge cable, and grid members.",
            "inputs": [
                {
                    "key": "warp_pretension",
                    "label": "Warp pretension (kN/m)",
                    "type": "number",
                    "default": 1.0,
                    "min": 0.1,
                    "max": 100.0,
                    "step": 0.1,
                },
                {
                    "key": "weft_pretension",
                    "label": "Weft pretension (kN/m)",
                    "type": "number",
                    "default": 1.0,
                    "min": 0.1,
                    "max": 100.0,
                    "step": 0.1,
                },
                {
                    "key": "edge_cable_pretension",
                    "label": "Edge cable pretension (kN/m)",
                    "type": "number",
                    "default": 25.0,
                    "min": 0.1,
                    "max": 500.0,
                    "step": 0.5,
                },
                {
                    "key": "grid_pretension",
                    "label": "Grid member pretension (kN)",
                    "type": "number",
                    "default": 20.0,
                    "min": 0.1,
                    "max": 500.0,
                    "step": 0.5,
                    "help": "Pretension carried by the meridian steel grid.",
                },
            ],
        },

        # =====================================================================
        # GROUP 4 - MATERIALS
        # =====================================================================
        {
            "key": "materials",
            "name": "4. Materials",
            "help": "Fabric, meridian steel, ring steel.",
            "inputs": [
                {
                    "key": "fabric_type",
                    "label": "Fabric type",
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
                    "label": "Fabric grade",
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
                    "key": "meridian_material",
                    "label": "Meridian steel grade",
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
                    "key": "ring_material",
                    "label": "Ring steel grade",
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
            ],
        },

        # =====================================================================
        # GROUP 5 - FOUNDATION
        # =====================================================================
        {
            "key": "foundation",
            "name": "5. Foundation",
            "help": "Base support condition.",
            "inputs": [
                {
                    "key": "base_condition",
                    "label": "Base condition",
                    "type": "radio",
                    "options": [
                        ["pinned", "Pinned"],
                        ["fixed", "Fixed"],
                    ],
                    "default": "pinned",
                },
            ],
        },

        # =====================================================================
        # GROUP 6 - LOAD CASE
        # =====================================================================
        {
            "key": "load_case",
            "name": "6. Load case",
            "help": "Design standard used for partial factors.",
            "inputs": [
                {
                    "key": "load_standard",
                    "label": "Design standard",
                    "type": "dropdown",
                    "options": [
                        ["MY", "MY - Malaysia"],
                        ["SG", "SG - Singapore"],
                        ["ID", "ID - Indonesia"],
                        ["TH", "TH - Thailand"],
                        ["VN", "VN - Vietnam"],
                        ["CN", "CN - China"],
                        ["EU", "EU - Europe"],
                        ["UK", "UK - United Kingdom"],
                        ["US", "US - United States"],
                        ["AU", "AU - Australia"],
                    ],
                    "default": "MY",
                },
            ],
        },
    ],

    "actions": {
        "back_page": "registration",
        "primary_label": "Intelligent Design Computing",
        "primary_page": "results",
    },
}


# =============================================================================
# END OF data/recipes/dome_multi_cone.py
# =============================================================================
