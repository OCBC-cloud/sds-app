# =============================================================================
# SDSe - Standard Saddle Recipe
# =============================================================================
# Recipe for the Cable Supported Saddle workshop.
# Read by ui/workshops/_renderer.py to build the input page.
#
# Schema (from _renderer.py):
#   top level : title, breadcrumb, structure_label, prefix,
#               defaults, groups, actions, viewer_strings (optional)
#   group     : key, name, inputs, help (opt), expanded (opt),
#               preview (opt), warning (opt), info (opt), defaults (opt)
#   input     : key, label, type, plus type-specific fields
#   input types: number, integer, dropdown, radio, toggle
#   options   : [ [value, label], ... ]
#
# History:
#   2026-10-09 - Rewritten to match the renderer schema exactly.
#                Replaces mesh_spacing with subdivisions_per_segment.
# =============================================================================

STANDARD_SADDLE_RECIPE = {
    "title": "Standard Saddle Span",
    "breadcrumb": ("Saddle Span", "Cable Supported Saddle"),
    "structure_label": "Standard Saddle Span",
    "prefix": "ws_ss",

    "defaults": {
        "span": 10.0,
        "apex": 15.0,
        "rise": 6.2,
        "curve_type": "parabolic",
        "anchor_count": 8,
        "subdivisions_per_segment": 5,
        "fabric_type": "PVDF",
        "fabric_grade": "Type III",
        "edge_cable_type": "6x19",
        "edge_cable_material": "stainless",
        "warp_pretension": 2.0,
        "weft_pretension": 2.0,
        "edge_cable_pretension": 0.0,
        "attachment_type": "cable_supported",
        "tiedown_intervals": 2,
        "uplift_angle": 45.0,
        "spread_angle": 30.0,
        "base_condition": "pinned",
        "snow_in_brief": False,
        "load_standard": "MY",
    },

    "groups": [

        # =====================================================================
        # GROUP 1 - SHAPE
        # =====================================================================
        {
            "key": "shape",
            "name": "1. Shape",
            "expanded": True,
            "help": "Overall dimensions and boundary subdivision.",
            "inputs": [
                {
                    "key": "span",
                    "label": "Span (m)",
                    "type": "number",
                    "default": 10.0,
                    "min": 4.0,
                    "max": 200.0,
                    "step": 0.5,
                },
                {
                    "key": "apex",
                    "label": "Apex - plan width (m)",
                    "type": "number",
                    "default": 15.0,
                    "min": 4.0,
                    "max": 200.0,
                    "step": 0.5,
                },
                {
                    "key": "rise",
                    "label": "Rise - beam height (m)",
                    "type": "number",
                    "default": 6.2,
                    "min": 0.5,
                    "max": 50.0,
                    "step": 0.1,
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
                {
                    "key": "anchor_count",
                    "label": "Anchors per beam",
                    "type": "integer",
                    "default": 8,
                    "min": 3,
                    "max": 40,
                    "step": 1,
                },
                {
                    "key": "subdivisions_per_segment",
                    "label": "Subdivisions per segment",
                    "type": "integer",
                    "default": 5,
                    "min": 1,
                    "max": 50,
                    "step": 1,
                    "help": "Number of subdivision points between any two "
                            "adjacent anchors. Same count on every segment.",
                },
            ],
        },

        # =====================================================================
        # GROUP 2 - MATERIALS
        # =====================================================================
        {
            "key": "materials",
            "name": "2. Materials",
            "help": "Fabric and cable selection.",
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
                    "key": "edge_cable_type",
                    "label": "Edge cable type",
                    "type": "dropdown",
                    "options": [
                        ["6x19", "6x19"],
                        ["Locked Coil", "Locked Coil"],
                        ["Spiral", "Spiral"],
                    ],
                    "default": "6x19",
                },
                {
                    "key": "edge_cable_material",
                    "label": "Edge cable material",
                    "type": "dropdown",
                    "options": [
                        ["stainless", "Stainless"],
                        ["galvanized", "Galvanized"],
                        ["bright", "Bright"],
                    ],
                    "default": "stainless",
                },
            ],
        },

        # =====================================================================
        # GROUP 3 - PRESTRESS
        # =====================================================================
        {
            "key": "prestress",
            "name": "3. Prestress",
            "help": "Membrane pretension and boundary attachment.",
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
                    "label": "Edge cable pretension (kN) [0 = auto]",
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
                    "options": [
                        ["kader", "Kader Guider (continuous)"],
                        ["cable_supported", "Cable Supported (anchors)"],
                    ],
                    "default": "cable_supported",
                },
            ],
        },

        # =====================================================================
        # GROUP 4 - TIE-DOWNS
        # =====================================================================
        {
            "key": "tiedowns",
            "name": "4. Tie-downs",
            "help": "Ground tie-down cables and anchor geometry.",
            "inputs": [
                {
                    "key": "tiedown_intervals",
                    "label": "Tie-down intervals",
                    "type": "dropdown",
                    "options": [
                        [2, "2"],
                        [4, "4"],
                        [8, "8"],
                    ],
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
            "key": "foundation",
            "name": "5. Foundation",
            "help": "Base support condition and load brief.",
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
                {
                    "key": "snow_in_brief",
                    "label": "Snow in brief",
                    "type": "toggle",
                    "default": False,
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
# END OF data/recipes/standard_saddle.py
# =============================================================================
