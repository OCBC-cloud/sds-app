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
#   2026-10-17 - Fix: removed dead "grid_pretension" widget.
#                Added Cone drop length and Cone diameter inputs.
#                Raised warp/weft defaults to 20 kN/m (matches tester).
#                Corrected labels: warp/weft are membrane prestress,
#                not grid members.
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
        "warp_pretension": 20.0,
        "weft_pretension": 20.0,
        "edge_cable_pretension": 25.0,

        # Group 3 - Cone geometry
        "drop_length": 1.0,
        "ring_diameter": 2.0,

        # Group 4 - Materials
        "fabric_type": "PVDF",
        "fabric_grade": "Type III",
        "frame_material": "S355",
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
            "key": "dome":_shape",
            "name": "1. Dome Shape",
 "            "expanded": True,
           ground "help": "Footprint, height, frame_out grid, eave, andline beam curve.",
            "inputs",
": [
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
                    "key                    "label": "Ground outline",
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
        # GROUP 2 - MEMBRANE PRESTRESS
        # =====================================================================
        {
            "key": "prestress",
            "name": "2. Membrane prestress",
            "help": "Warp and weft are the fabric's own prestress "
                    "(woven threads under tension). Edge cable is the "
                    "perimeter cable pretension. None of these apply "
                    "to the structural frame or rings.",
            "inputs": [
                {
                    "key": "warp_pretension",
                    "label": "Membrane warp prestress (kN/m)",
                    "type": "number",
                    "default": 20.0,
                    "min": 0.1,
                    "max": 100.0,
                    "step": 0.1,
                    "help": "Longitudinal fabric thread tension. "
                            "Typical PVDF Type III: 2–6 kN/m. "
                            "20 kN/m is high and useful for stiff form-finding.",
                },
                {
                    "key": "weft_pretension",
                    "label": "Membrane weft prestress (kN/m)",
                    "type": "number",
                    "default": 20.0,
                    "min": 0.1,
                    "max": 100.0,
                    "step": 0.1,
                    "help": "Transverse fabric thread tension. "
                            "Usually equal to or lower than warp.",
                },
                {
                    "key": "edge_cable_pretension",
                    "label": "Edge cable pretension (kN/m)",
                    "type": "number",
                    "default": 25.0,
                    "min": 0.1,
                    "max": 500.0,
                    "step": 0.5,
                    "help": "Perimeter cable pretension. "
                            "Carries the membrane's inward pull "
                            "to the eave anchors.",
                },
            ],
        },

        # =====================================================================
        # GROUP 3 - CONE GEOMETRY
        # =====================================================================
        {
            "key": "cone_geometry",
            "name": "3. Cone geometry",
            "help": "Cone size and depth. Positions are set in the "
                    "picker below this form.",
            "inputs": [
                {
                    "key": "ring_diameter",
                    "label": "Cone diameter (m)",
                    "type": "number",
                    "default": 2.0,
                    "min": 0.5,
                    "max": 10.0,
                    "step": 0.1,
                    "help": "Diameter of the top opening (ring) of each cone.",
                },
                {
                    "key": "drop_length",
                    "label": "Cone drop depth (m)",
                    "type": "number",
                    "default": 1.0,
                    "min": 0.1,
                    "max": 5.0,
                    "step": 0.1,
                    "help": "Vertical distance from the frame crossing "
                            "down to the ring. Longer drop = deeper cone.",
                },
            ],
        },

        # =====================================================================
        # GROUP 4 - MATERIALS
        # =====================================================================
        {
            "key": "materials",
            "name": "4. Materials",
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
