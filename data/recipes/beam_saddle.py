# =============================================================================
# SDSe - Beam Supported Saddle Recipe
# =============================================================================
# Recipe for the Beam Supported Saddle workshop.
# =============================================================================

BEAM_SADDLE_RECIPE = {
    "title": "Beam Supported Saddle",
    "breadcrumb": ("Saddle Span", "Beam Supported Saddle"),
    "structure_label": "Beam Supported Saddle Span",
    "prefix": "ws_bs",

    "defaults": {
        "span": 10.0,
        "apex": 15.0,
        "rise": 6.2,
        "curve_type": "parabolic",
        "steel_grade": "S355",
        "section_family": "CHS",
        "fabric_type": "PVDF",
        "fabric_grade": "Type III",
        "member_construction": "single_beam",
        "support_type_start": "pinned",
        "support_type_end": "pinned",
        "secondary_count": 2,
        "secondary_count_override": False,
        "secondary_construction": "single_beam",
        "secondary_section_family": "CHS",
        "secondary_base_connection": "pinned",
        "uplift_angle": 45,
        "spread_angle": 30,
        "membrane_pretension": 2.0,
        "purlin_construction": "single_beam",
        "purlin_section_family": "CHS",
        "soil_bearing": 150.0,
        "soil_type": "sand",
        "water_table": 3.0,
        "foundation_type": "pad",
        "add_payload": 0.0,
        "design_standard": "MY",
        "attachment_type": "kader",
    },

    "groups": [
        {
            "key": "geometry",
            "name": "1. Geometry",
            "expanded": True,
            "inputs": [
                {"key": "span", "label": "Span Distance (m)", "type": "number", "min": 4.0, "max": 200.0, "step": 0.5},
                {"key": "apex", "label": "Apex-to-Apex (m)", "type": "number", "min": 4.0, "max": 200.0, "step": 0.5},
                {"key": "rise", "label": "Rise (m)", "type": "number", "min": 0.5, "max": 50.0, "step": 0.1},
                {"key": "curve_type", "label": "Beam Curve", "type": "dropdown", "options": [["parabolic", "Parabolic"], ["circular", "Circular"], ["catenary", "Catenary"]]},
            ],
        },
        {
            "key": "materials",
            "name": "2. Materials",
            "inputs": [
                {"key": "steel_grade", "label": "Steel Grade", "type": "dropdown", "options": [["S235", "S235"], ["S275", "S275"], ["S355", "S355"], ["S420", "S420"], ["S460", "S460"]]},
                {"key": "section_family", "label": "Section Family", "type": "dropdown", "options": [["CHS", "CHS"], ["SHS", "SHS"], ["RHS", "RHS"], ["I-Beam", "I-Beam"]]},
                {"key": "fabric_type", "label": "Fabric Type", "type": "dropdown", "options": [["PVDF", "PVDF"], ["PTFE", "PTFE"], ["ETFE", "ETFE"]]},
                {"key": "fabric_grade", "label": "Fabric Grade", "type": "dropdown", "options": [["Type III", "Type III"], ["Type IV", "Type IV"]]},
            ],
        },
        {
            "key": "beam_construction",
            "name": "3. Beam Construction",
            "inputs": [
                {"key": "member_construction", "label": "Beam Type", "type": "radio", "options": [["single_beam", "Single Beam"], ["planar_truss", "Planar Truss"], ["space_truss", "Space Truss"]]},
            ],
        },
        {
            "key": "frame_supports",
            "name": "4. Frame Supports",
            "inputs": [
                {"key": "support_type_start", "label": "Support at Start", "type": "radio", "options": [["pinned", "Pinned"], ["rigid", "Rigid"]]},
                {"key": "support_type_end", "label": "Support at End", "type": "radio", "options": [["pinned", "Pinned"], ["rigid", "Rigid"]]},
            ],
        },
        {
            "key": "secondary",
            "name": "5. Secondary Beams",
            "inputs": [
                {"key": "secondary_count_override", "label": "Override System Recommendation?", "type": "toggle", "default": False},
                {"key": "secondary_count", "label": "Number per Main Beam", "type": "integer", "min": 2, "max": 20, "step": 2},
                {"key": "uplift_angle", "label": "Uplift Angle (deg)", "type": "integer", "min": 20, "max": 75, "step": 1},
                {"key": "spread_angle", "label": "Spread Angle (deg)", "type": "integer", "min": 0, "max": 60, "step": 1},
                {"key": "secondary_construction", "label": "Construction Type", "type": "radio", "options": [["single_beam", "Single Beam"], ["planar_truss", "Planar Truss"], ["space_truss", "Space Truss"]]},
                {"key": "secondary_section_family", "label": "Section Family", "type": "dropdown", "options": [["CHS", "CHS"], ["SHS", "SHS"], ["RHS", "RHS"], ["I-Beam", "I-Beam"]]},
                {"key": "secondary_base_connection", "label": "Base Connection", "type": "radio", "options": [["pinned", "Pinned"], ["rigid", "Rigid"]]},
                {"key": "membrane_pretension", "label": "Membrane Pretension (kN/m)", "type": "number", "min": 0.5, "max": 8.0, "step": 0.1},
            ],
        },
        {
            "key": "purlins",
            "name": "6. Purlins",
            "inputs": [
                {"key": "purlin_construction", "label": "Construction Type", "type": "radio", "options": [["single_beam", "Single Beam"], ["planar_truss", "Planar Truss"], ["space_truss", "Space Truss"]]},
                {"key": "purlin_section_family", "label": "Section Family", "type": "dropdown", "options": [["CHS", "CHS"], ["SHS", "SHS"], ["RHS", "RHS"], ["I-Beam", "I-Beam"]]},
            ],
        },
        {
            "key": "foundation",
            "name": "7. Foundation",
            "inputs": [
                {"key": "soil_bearing", "label": "Soil Bearing (kN/m2)", "type": "number", "min": 50.0, "max": 1000.0, "step": 10.0},
                {"key": "water_table", "label": "Water Table Depth (m)", "type": "number", "min": 0.5, "max": 20.0, "step": 0.5},
                {"key": "soil_type", "label": "Soil Type", "type": "dropdown", "options": [["sand", "Sand"], ["clay", "Clay"], ["rock", "Rock"], ["filled", "Filled"]]},
                {"key": "foundation_type", "label": "Foundation Type", "type": "dropdown", "options": [["pad", "Pad Footing"], ["pile", "Pile Group"], ["raft", "Raft"]]},
            ],
        },
        {
            "key": "loads",
            "name": "8. Loads",
            "inputs": [
                {"key": "add_payload", "label": "Add. Pay Load (kg/m)", "type": "number", "min": 0.0, "max": 500.0, "step": 5.0},
                {"key": "design_standard", "label": "Design Standard", "type": "dropdown", "options": [["EU", "EU"], ["MY", "MY"], ["UK", "UK"], ["CN", "CN"], ["US", "US"]]},
            ],
        },
        {
            "key": "attachment",
            "name": "9. Attachment",
            "inputs": [
                {"key": "attachment_type", "label": "Attachment Method", "type": "radio", "options": [["kader", "Kader Guider"], ["segmented", "Segmented Edge"]]},
            ],
        },
    ],

    "actions": {
        "back_page": "registration",
        "primary_label": "Intelligent Design Computing",
        "primary_page": "results",
    },
}
