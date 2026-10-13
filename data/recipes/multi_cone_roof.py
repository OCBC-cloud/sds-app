# =============================================================================
# SDSe - Multi-Cone Roof Recipe
# =============================================================================
# Recipe for the Multi-Cone Roof workshop (Multi-Cone Cluster variant).
# Read by ui/workshops/_renderer.py to build the input page.
#
# Schema follows data/recipes/standard_saddle.py exactly:
#   - Six groups
#   - Only the five allowed input types: number, integer, dropdown,
#     radio, toggle
#   - Two numbers per row where they pair naturally
#   - No custom widgets, no sliders
#
# History:
#   2026-10-13 - First version. Migrated from the working Lab tester
#                (ui/workshops/tester_multi_cone.py, v21). The physics
#                of the tester is preserved. This file only carries
#                the inputs; the viewer lives in
#                viewers/figures/multi_cone_roof.py.
# =============================================================================

MULTI_CONE_ROOF_RECIPE = {
    "title": "Multi-Cone Roof",
    "breadcrumb": ("Multi-Cone Roof", "Multi-Cone Cluster"),
    "structure_label": "Multi-Cone Cluster",
    "prefix": "ws_mc",

    "defaults": {
        # Group 1 - Shape
        "span": 25.0,
        "apex": 9.0,
        "mid_width": 18.0,
        "eave_height": 2.8,
        "curve_type": "parabolic",
        "secondary_count": 3,
        "optional_ends": False,
        "subdivisions_per_edge": 17,

        # Group 2 - Cones
        "number_of_cones": 3,
        "cone_spacing": 5.0,
        "ring_diameter": 1.0,
        "ring_clearance": 1.0,

        # Group 3 - Prestress
        "warp_pretension": 1.0,
        "weft_pretension": 1.0,
        "edge_cable_pretension": 25.0,

        # Group 4 - Materials
        "fabric_type": "PVDF",
        "fabric_grade": "Type III",
        "edge_cable_type": "6x19",
        "edge_cable_material": "stainless",

        # Group 5 - Foundation
        "base_condition": "pinned",

        # Group 6 - Load case
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
            "help": "Primary geometry: span, apex, mid-width, eave, "
                    "and the rib and mesh subdivision.",
            "inputs": [
                {
                    "key": "span",
                    "label": "Primary span (m)",
                    "type": "number",
                    "default": 25.0,
                    "min": 6.0,
                    "max": 60.0,
                    "step": 0.5,
                },
                {
                    "key": "apex",
                    "label": "Primary apex (m)",
                    "type": "number",
                    "default": 9.0,
                    "min": 1.0,
                    "max": 30.0,
                    "step": 0.5,
                },
                {
                    "key": "mid_width",
                    "label": "Mid-span width (m)",
                    "type": "number",
                    "default": 18.0,
                    "min": 6.0,
                    "max": 60.0,
                    "step": 0.5,
                },
                {
                    "key": "eave_height",
                    "label": "Eave height (m)",
                    "type": "number",
                    "default": 2.8,
                    "min": 0.5,
                    "max": 10.0,
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
                    "key": "secondary_count",
                    "label": "Secondary beams",
                    "type": "integer",
                    "default": 3,
                    "min": 2,
                    "max": 20,
                    "step": 1,
                    "help": "Number of ribs across the primary span.",
                },
                {
                    "key": "optional_ends",
                    "label": "Optional end ribs",
                    "type": "toggle",
                    "default": False,
                    "help": "Add ribs at the very ends of the span.",
                },
                {
                    "key": "subdivisions_per_edge",
                    "label": "Subdivisions per edge",
                    "type": "integer",
                    "default": 17,
                    "min": 5,
                    "max": 25,
                    "step": 1,
                    "help": "Perimeter subdivision density. Higher is "
                            "smoother and slower.",
                },
            ],
        },

        # =====================================================================
        # GROUP 2 - CONES
        # =====================================================================
        {
            "key": "cones",
            "name": "2. Cones",
            "help": "Number, spacing, size and drop of the cone rings.",
            "inputs": [
                {
                    "key": "number_of_cones",
                    "label": "Number of cones",
                    "type": "integer",
                    "default": 3,
                    "min": 1,
                    "max": 20,
                    "step": 1,
                },
                {
                    "key": "cone_spacing",
                    "label": "Distance between adjacent cones (m)",
                    "type": "number",
                    "default": 5.0,
                    "min": 0.5,
                    "max": 10.0,
                    "step": 0.1,
                },
                {
                    "key": "ring_diameter",
                    "label": "Ring diameter (m)",
                    "type": "number",
                    "default": 1.0,
                    "min": 0.5,
                    "max": 10.0,
                    "step": 0.1,
                },
                {
                    "key": "ring_clearance",
                    "label": "Ring clearance below beam (m)",
                    "type": "number",
                    "default": 1.0,
                    "min": 0.1,
                    "max": 5.0,
                    "step": 0.1,
                    "help": "Vertical drop from the primary beam to the "
                            "ring centre.",
                },
            ],
        },

        # =====================================================================
        # GROUP 3 - PRESTRESS
        # =====================================================================
        {
            "key": "prestress",
            "name": "3. Prestress",
            "help": "Membrane warp and weft pretension, and edge cable "
                    "pretension.",
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
                    "help": "Direct force density for the perimeter cable. "
                            "Lower makes the cable bow more. Higher makes "
                            "it straighter.",
                },
            ],
        },

        # =====================================================================
        # GROUP 4 - MATERIALS
        # =====================================================================
        {
            "key": "materials",
            "name": "4. Materials",
            "help": "Fabric and edge cable selection.",
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
# END OF data/recipes/multi_cone_roof.py
# =============================================================================
