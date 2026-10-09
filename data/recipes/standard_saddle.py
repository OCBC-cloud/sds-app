# =============================================================================
# SDSe - Standard Saddle Recipe
# =============================================================================
# Recipe for the Cable Supported Saddle workshop.
# Read by ui/workshops/_renderer.py to build the input page.
#
# Structure of a recipe:
#   groups : list of accordion groups
#   each group has:
#     name    - the group header (shown as an accordion title)
#     inputs  - list of input definitions
#   each input has:
#     key       - the session state key (ws_ss_<key>)
#     label     - the display label
#     type      - the input type (see below)
#     default   - the default value
#     ...
#
# Input types supported by the universal workshop renderer:
#   number    - numeric text input
#   integer   - integer text input
#   select    - dropdown, requires options
#   radio     - radio buttons, requires options
#   text      - free text
#   checkbox  - toggle
#   slider    - numeric slider (used sparingly, per the doctrine)
#
# Six groups per the SDSe doctrine. No sliders.
#
# Updated 2026-10-09:
#   - Replaced mesh_spacing with subdivisions_per_segment. The user
#     now controls the number of subdivision points between any two
#     anchors directly. Uniform across every segment. Default 5.
#     For beam boundaries, subdivision follows the beam arc. For
#     cable boundaries, subdivision follows the straight chord.
#
# History:
#   2026-10-04 - Step 2E. Anchors and subdivision.
#   2026-10-05 - Pull-back related inputs.
#   2026-10-06 - Auto edge pretension noted in preview.
#   2026-10-09 - subdivisions_per_segment replaces mesh_spacing.
# =============================================================================

RECIPE = {
    "structure_key": "saddle_span",
    "variant_key": "standard_saddle",
    "title": "Cable Supported Saddle",
    "subtitle": (
        "Tie-down cables resist uplift. Suitable for spans up to "
        "about 20 m."
    ),

    "groups": [

        # =====================================================================
        # GROUP 1 - SHAPE
        # =====================================================================
        {
            "name": "1. Shape",
            "inputs": [
                {
                    "key": "span",
                    "label": "Span (m)",
                    "type": "number",
                    "default": 10.0,
                    "min": 1.0,
                    "step": 0.5,
                },
                {
                    "key": "apex",
                    "label": "Apex - plan width (m)",
                    "type": "number",
                    "default": 15.0,
                    "min": 1.0,
                    "step": 0.5,
                },
                {
                    "key": "rise",
                    "label": "Rise - beam height (m)",
                    "type": "number",
                    "default": 6.2,
                    "min": 0.5,
                    "step": 0.2,
                },
                {
                    "key": "curve_type",
                    "label": "Beam curve",
                    "type": "select",
                    "options": ["parabolic", "circular", "elliptical"],
                    "default": "parabolic",
                },
                {
                    "key": "anchor_count",
                    "label": "Anchor count per beam",
                    "type": "integer",
                    "default": 8,
                    "min": 2,
                    "max": 20,
                },
                {
                    "key": "subdivisions_per_segment",
                    "label": "Subdivisions per segment",
                    "type": "integer",
                    "default": 5,
                    "min": 1,
                    "max": 50,
                },
            ],
        },

        # =====================================================================
        # GROUP 2 - MATERIALS
        # =====================================================================
        {
            "name": "2. Materials",
            "inputs": [
                {
                    "key": "fabric_type",
                    "label": "Fabric type",
                    "type": "select",
                    "options": ["PVDF", "PTFE", "ETFE"],
                    "default": "PVDF",
                },
                {
                    "key": "fabric_grade",
                    "label": "Fabric grade",
                    "type": "select",
                    "options": ["Type I", "Type II", "Type III", "Type IV"],
                    "default": "Type III",
                },
                {
                    "key": "edge_cable_type",
                    "label": "Edge cable type",
                    "type": "select",
                    "options": ["6x19", "Locked Coil", "Spiral"],
                    "default": "6x19",
                },
                {
                    "key": "edge_cable_material",
                    "label": "Edge cable material",
                    "type": "select",
                    "options": ["stainless", "galvanized", "bright"],
                    "default": "stainless",
                },
            ],
        },

        # =====================================================================
        # GROUP 3 - PRESTRESS
        # =====================================================================
        {
            "name": "3. Prestress",
            "inputs": [
                {
                    "key": "warp_pretension",
                    "label": "Warp pretension (kN/m)",
                    "type": "number",
                    "default": 2.0,
                    "min": 0.1,
                    "max": 100.0,
                    "step": 0.1,
                },
                {
                    "key": "weft_pretension",
                    "label": "Weft pretension (kN/m)",
                    "type": "number",
                    "default": 2.0,
                    "min": 0.1,
                    "max": 100.0,
                    "step": 0.1,
                },
                {
                    "key": "edge_cable_pretension",
                    "label": "Edge cable pretension (kN) - 0 = auto",
                    "type": "number",
                    "default": 0.0,
                    "min": 0.0,
                    "max": 500.0,
                    "step": 0.5,
                },
                {
                    "key": "attachment_type",
                    "label": "Boundary attachment",
                    "type": "radio",
                    "options": ["kader", "cable_supported"],
                    "default": "cable_supported",
                },
            ],
        },

        # =====================================================================
        # GROUP 4 - TIE-DOWNS
        # =====================================================================
        {
            "name": "4. Tie-downs",
            "inputs": [
                {
                    "key": "tiedown_intervals",
                    "label": "Tie-down intervals",
                    "type": "select",
                    "options": [2, 4, 8],
                    "default": 2,
                },
                {
                    "key": "uplift_angle",
                    "label": "Uplift angle (deg)",
                    "type": "number",
                    "default": 45.0,
                    "min": 10.0,
                    "max": 85.0,
                    "step": 1.0,
                },
                {
                    "key": "spread_angle",
                    "label": "Spread angle (deg)",
                    "type": "number",
                    "default": 30.0,
                    "min": 0.0,
                    "max": 80.0,
                    "step": 1.0,
                },
            ],
        },

        # =====================================================================
        # GROUP 5 - FOUNDATION
        # =====================================================================
        {
            "name": "5. Foundation",
            "inputs": [
                {
                    "key": "base_condition",
                    "label": "Base condition",
                    "type": "radio",
                    "options": ["pinned", "fixed"],
                    "default": "pinned",
                },
                {
                    "key": "snow_in_brief",
                    "label": "Snow in brief",
                    "type": "checkbox",
                    "default": False,
                },
            ],
        },

        # =====================================================================
        # GROUP 6 - LOAD CASE
        # =====================================================================
        {
            "name": "6. Load case",
            "inputs": [
                {
                    "key": "load_standard",
                    "label": "Design standard",
                    "type": "select",
                    "options": ["MY", "SG", "ID", "TH", "VN", "CN", "EU", "UK", "US", "AU"],
                    "default": "MY",
                },
            ],
        },
    ],

    "preview_keys": [
        "span",
        "apex",
        "rise",
        "anchor_count",
        "subdivisions_per_segment",
        "warp_pretension",
        "weft_pretension",
        "edge_cable_pretension",
        "attachment_type",
    ],

    "action_label": "Build Shape",
}


# =============================================================================
# END OF data/recipes/standard_saddle.py
# =============================================================================
