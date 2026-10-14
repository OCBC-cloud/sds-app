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
# Cone placement is handled by ui/dome_cone_picker.py, which the
# workshop wrapper renders below the recipe. The picker is a pure
# input device: it collects the user's picked crossings and writes
# them to session state under ws_dm_picked_crossings. The viewer
# owns all geometry and reads the picked set.
#
# History:
#   2026-10-13 - First version. Dome geometry generator driven by
#                frame beams on a globe grid.
#   2026-10-14 - Renamed the two frame count inputs. They control
#                how many frames are SPACED along each axis.
#   2026-10-14 - Removed Group 2 (Cone Placement). Cone positions
#                are now picked in the 2D picker below the recipe.
#                Renumbered remaining groups sequentially.
#                Reduced frame-count max to 15 for picker responsiveness.
#   2026-10-14 - Renamed the frame steel input. Key changed from
#                "meridian_material" to "frame_material". The word
#                "meridian" is no longer used anywhere in this recipe.
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

        # Group 2 - Prestress
        "warp_pretension": 1.0,
        "weft_pretension": 1.0,
        "edge_cable_pretension": 25.0,
        "grid_pretension": 20.0,

        # Group 3 - Materials
        "fabric_type": "PVDF",
        "fabric_grade": "Type III",
        "frame_material": "S355",
        "ring_material": "S355",

        # Group 4 - Foundation
        "base_condition": "pinned",

        # Group 5 - Load case
        "load_standard": "MY",

        # Cone geometry (fixed for now, not user input).
        # Values the viewer reads. The picker does not read these.
        "drop_length": 1.0,
        "ring_diameter": 2.0,
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
                    "max": 15,
                    "step": 1,
                    "help": "Number of frames spaced along the X axis. "
                            "Each frame runs along Y (its curve lies in "
                            "the YZ plane). Max 15 for picker "
                            "responsiveness.",
                },
                {
                    "key": "meridians_y",
                    "label": "Frames along Y",
                    "type": "integer",
                    "default": 5,
                    "min": 3,
                    "max": 15,
                    "step": 1,
                    "help": "Number of frames spaced along the Y axis. "
                            "Each frame runs along X (its curve lies in "
                            "the XZ plane). Max 15 for picker "
                            "responsiveness.",
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
        # GROUP 2 - PRESTRESS
        # =====================================================================
        {
            "key": "prestress",
            "name": "2. Prestress",
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
                    "help": "Pretension carried by the frame steel grid.",
                },
            ],
        },

        # =====================================================================
        # GROUP 3 - MATERIALS
        # =====================================================================
        {
            "key": "materials",
            "name": "3. Materials",
            "help": "Fabric, frame steel, ring steel.",
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
                    "key": "frame_material",
                    "label": "Frame steel grade",
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
        # GROUP 4 - FOUNDATION
        # =====================================================================
        {
            "key": "foundation",
            "name": "4. Foundation",
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
        # GROUP 5 - LOAD CASE
        # =====================================================================
        {
            "key": "load_case",
            "name": "5. Load case",
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
