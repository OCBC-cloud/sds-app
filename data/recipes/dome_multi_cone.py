# =============================================================================
# SDSe - Dome Multi-Cone Recipe
# =============================================================================
# History:
#   2026-10-21 - Added Loads group with Wind Speed, Snow Depth, and
#                Additional Payload. The viewer now passes these to
#                the load generator and the solver.
# =============================================================================

DOME_MULTI_CONE_RECIPE = {
    "title": "Dome Multi-Cone Roof",
    "breadcrumb": ("Multi-Cone Roof", "Dome Multi-Cone"),
    "structure_label": "Dome Multi-Cone",
    "prefix": "ws_dm",

    "defaults": {
        "dome_diameter": 18.0,
        "crown_height": 9.0,
        "meridians_x": 5,
        "meridians_y": 5,
        "eave_height": 3.2,
        "curve_type": "parabolic",
        "drop_length": 1.0,
        "ring_diameter": 1.0,
        "warp_pretension": 20.0,
        "weft_pretension": 20.0,
        "edge_cable_pretension": 45.0,
        # New load inputs
        "wind_speed": 30.0,
        "snow_depth": 0.0,
        "add_payload": 0.0,
    },

    "groups": [
        {
            "key": "geometry",
            "name": "1. Geometry",
            "expanded": True,
            "help": "Overall dimensions of the dome.",
            "inputs": [
                {"key": "dome_diameter", "label": "Dome Diameter (m)", "type": "number", "min": 4.0, "max": 100.0, "step": 0.5},
                {"key": "crown_height", "label": "Crown Height (m)", "type": "number", "min": 1.0, "max": 30.0, "step": 0.5},
                {"key": "meridians_x", "label": "Meridians X", "type": "integer", "min": 1, "max": 20, "step": 1},
                {"key": "meridians_y", "label": "Meridians Y", "type": "integer", "min": 1, "max": 20, "step": 1},
                {"key": "eave_height", "label": "Eave Height (m)", "type": "number", "min": 0.5, "max": 20.0, "step": 0.1},
                {"key": "curve_type", "label": "Curve Type", "type": "dropdown", "options": [["parabolic", "Parabolic"], ["circular", "Circular"], ["catenary", "Catenary"], ["custom", "Custom (Draw Profile)"]]},
            ],
        },
        {
            "key": "cones",
            "name": "2. Cones",
            "help": "Size of the cone ring at each picked position.",
            "inputs": [
                {"key": "drop_length", "label": "Drop Length (m)", "type": "number", "min": 0.1, "max": 10.0, "step": 0.1},
                {"key": "ring_diameter", "label": "Ring Diameter (m)", "type": "number", "min": 0.1, "max": 5.0, "step": 0.1},
            ],
        },
        {
            "key": "prestress",
            "name": "3. Prestress",
            "help": "Membrane and cable pretension.",
            "inputs": [
                {"key": "warp_pretension", "label": "Warp Pretension (kN/m)", "type": "number", "min": 0.1, "max": 100.0, "step": 0.1},
                {"key": "weft_pretension", "label": "Weft Pretension (kN/m)", "type": "number", "min": 0.1, "max": 100.0, "step": 0.1},
                {"key": "edge_cable_pretension", "label": "Edge Cable Pretension (kN)", "type": "number", "min": 0.1, "max": 500.0, "step": 0.5},
            ],
        },
        {
            "key": "loads",
            "name": "4. Loads",
            "help": "Wind, snow, and additional payload.",
            "inputs": [
                {"key": "wind_speed", "label": "Design Wind Speed (m/s)", "type": "number", "min": 10.0, "max": 80.0, "step": 1.0},
                {"key": "snow_depth", "label": "Snow Depth (m)", "type": "number", "min": 0.0, "max": 2.0, "step": 0.05},
                {"key": "add_payload", "label": "Additional Payload (kg/m2)", "type": "number", "min": 0.0, "max": 500.0, "step": 5.0},
            ],
        },
    ],

    "actions": {
        "back_page": "registration",
        "primary_label": "Intelligent Design Computing",
        "primary_page": "results",
    },
}
