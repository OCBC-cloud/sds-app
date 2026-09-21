# =============================================================================
# SDSe - Structure Types Catalogue
# =============================================================================
# Canonical list of structure types, their variants, and the members
# that appear in each.
#
# STRUCTURE_TYPES    - main structure types (8 in Phase 1)
# STRUCTURE_VARIANTS - sub-types under each main type
# MEMBER_SCHEMA      - members present in each structure + variant
#
# History:
#   2026-09-13 - Reduced from 27 legacy types to 8 final mains.
#                Cantilever promoted to a main type.
#   2026-09-14 - Added MEMBER_SCHEMA for Member Schedule display.
#   2026-09-15 - Renamed display names for Saddle Span sub-types.
#   2026-09-21 - Cantilever list reduced to two visible entries:
#                "Cantilever Leaf" and "Cantilever Variants".
#                The five unbuilt variants (Flower, Cone, Pyramid,
#                Bell, Sail) remain in the file with available=False
#                for future reference but are hidden from the
#                registration page.
#                Hypar entry added to MEMBER_SCHEMA.
# =============================================================================

STRUCTURE_TYPES = {
    "saddle_span": {
        "name": "Saddle Span",
        "icon": "S",
        "description": "Curved saddle-shaped tensile structure",
        "category": "Tensile",
    },
    "cantilever": {
        "name": "Cantilever",
        "icon": "L",
        "description": "Single column with arm and membrane",
        "category": "Tensile",
    },
    "unipole_tensile": {
        "name": "Uni-Pole Tensile Roof",
        "icon": "U",
        "description": "Mast with radial membrane",
        "category": "Tensile",
    },
    "tensile_sails": {
        "name": "Tensile Sails Roof",
        "icon": "T",
        "description": "Hypar sails spanning between anchors",
        "category": "Tensile",
    },
    "framed_tensile": {
        "name": "Framed Tensile Roof",
        "icon": "R",
        "description": "Fabric on rigid frame",
        "category": "Tensile",
    },
    "canopy": {
        "name": "Canopy",
        "icon": "C",
        "description": "Wall-mounted, cable-supported, or tree shade",
        "category": "Tensile",
    },
    "frame_tent": {
        "name": "Frame Tent",
        "icon": "F",
        "description": "Framed tent structure",
        "category": "Frame",
    },
    "portal_frame": {
        "name": "Portal Frame",
        "icon": "P",
        "description": "Rigid steel frame structure",
        "category": "Frame",
    },
}


STRUCTURE_VARIANTS = {
    "saddle_span": [
        {"key": "standard_saddle",
         "name": "Cable Supported Saddle",
         "description": "Tie-down cables resist uplift. Suitable for spans up to about 20 m.",
         "available": True},
        {"key": "frame_supported_saddle",
         "name": "Beam Supported Saddle",
         "description": "Secondary beams and a rigid frame resist uplift. Suitable for larger spans.",
         "available": True},
    ],
    "cantilever": [
        {"key": "cantilever_leaf", "name": "Cantilever Leaf",
         "description": "Curved spine and radial ribs. Leaf shape.",
         "available": True},
        {"key": "cantilever_hypar", "name": "Cantilever Variants",
         "description": "Leaf, Hypar, and more. Choose inside the workshop.",
         "available": True},

        # ---- Hidden for now. Not shown on Registration.
        # Available flag is False so the registration page can filter
        # them out. They will become reachable from inside the
        # workshop's Section 1 once that routing is built.
        {"key": "cantilever_flower", "name": "Cantilever Flower",
         "description": "Multi-leaf layered spiral.",
         "available": False},
        {"key": "cantilever_cone", "name": "Cantilever Cone",
         "description": "Column with arm and cone membrane.",
         "available": False},
        {"key": "cantilever_pyramid", "name": "Cantilever Pyramid",
         "description": "Column with arm and pyramid membrane.",
         "available": False},
        {"key": "cantilever_bell", "name": "Cantilever Bell",
         "description": "Column with arm and bell-shaped membrane.",
         "available": False},
        {"key": "cantilever_sail", "name": "Cantilever Sail",
         "description": "Column with arm and sail membrane.",
         "available": False},
    ],
    "unipole_tensile": [
        {"key": "single_cone", "name": "Single Cone",
         "description": "Radial symmetry. One mast with cone fabric.",
         "available": True},
        {"key": "multi_cone_cluster", "name": "Multi-Cone Cluster",
         "description": "Multiple cone units in a cluster.",
         "available": True},
        {"key": "umbrella", "name": "Umbrella",
         "description": "Single mast with visible ribs and fabric.",
         "available": True},
    ],
    "tensile_sails": [
        {"key": "hypar_sail_3", "name": "Hypar Sail - 3 Anchors",
         "description": "Triangular hypar between three anchor points.",
         "available": True},
        {"key": "hypar_sail_4", "name": "Hypar Sail - 4 Anchors",
         "description": "Quad hypar between four anchor points.",
         "available": True},
        {"key": "multiple_wall_sails", "name": "Multiple Wall-Anchored Sails",
         "description": "Array of sails anchored to walls.",
         "available": True},
        {"key": "multiple_column_sails", "name": "Multiple Column-Mounted Sails",
         "description": "Array of sails anchored to columns.",
         "available": True},
    ],
    "framed_tensile": [
        {"key": "simple_frame", "name": "Simple Frame + Fabric",
         "description": "Straight frame members with fabric on top.",
         "available": True},
        {"key": "arched_frame", "name": "Arched Frame + Fabric",
         "description": "Curved arch members with fabric on top.",
         "available": True},
        {"key": "trussed_frame", "name": "Trussed Frame + Fabric",
         "description": "Triangulated truss frame with fabric on top.",
         "available": True},
    ],
    "canopy": [
        {"key": "wall_mounted_shade", "name": "Wall-Mounted Shade",
         "description": "Attached to wall and cantilevered out.",
         "available": True},
        {"key": "cable_supported_shade", "name": "Cable-Supported Shade",
         "description": "Mast with cables and shade surface.",
         "available": True},
        {"key": "tree_canopy", "name": "Tree Canopy",
         "description": "Trunk with branching arms and shade.",
         "available": False},
    ],
    "frame_tent": [
        {"key": "pyramid_tent", "name": "Pyramid Tent",
         "description": "Four-sided pyramid. Central pole.",
         "available": True},
        {"key": "modular_tent", "name": "Modular Tent",
         "description": "Modular frame units joined together.",
         "available": True},
        {"key": "cone_tent", "name": "Cone Tent",
         "description": "Circular cone tent with centre pole.",
         "available": True},
        {"key": "a_frame_tent", "name": "A-Frame Tent",
         "description": "Classic A-frame profile.",
         "available": True},
        {"key": "arch_tent", "name": "Arch Tent",
         "description": "Curved arch frame tent.",
         "available": True},
    ],
    "portal_frame": [
        {"key": "simple_portal", "name": "Simple Portal",
         "description": "Single span. Two columns and one rafter.",
         "available": True},
        {"key": "portal_with_mezzanine", "name": "With Mezzanine",
         "description": "Portal with an intermediate mezzanine floor.",
         "available": True},
        {"key": "portal_with_crane", "name": "With Crane",
         "description": "Portal with crane gantry beams.",
         "available": True},
        {"key": "multi_bay_portal", "name": "Multi-Bay Portal",
         "description": "Multiple bays side by side.",
         "available": True},
    ],
}


# =============================================================================
# MEMBER SCHEMA
# =============================================================================

_PLANAR_TRUSS_ROWS = [
    {"key": "truss_top", "label": "Top Chord",
     "section": "CHS --", "note": ""},
    {"key": "truss_bot", "label": "Bottom Chord",
     "section": "CHS --", "note": ""},
    {"key": "truss_vert", "label": "Vertical Chord",
     "section": "CHS --", "note": ""},
    {"key": "truss_diag", "label": "Diagonal Chord",
     "section": "CHS --", "note": ""},
]

_SPACE_TRUSS_ROWS = [
    {"key": "truss_top", "label": "Top Chord",
     "section": "CHS --", "note": ""},
    {"key": "truss_bot", "label": "Bottom Chord",
     "section": "CHS --", "note": ""},
    {"key": "truss_vert", "label": "Vertical Chord",
     "section": "CHS --", "note": ""},
    {"key": "truss_horiz", "label": "Horizontal Chord",
     "section": "CHS --", "note": ""},
    {"key": "truss_diag", "label": "Diagonal Chord",
     "section": "CHS --", "note": ""},
]


MEMBER_SCHEMA = {
    ("saddle_span", "standard_saddle"): {
        "membrane_first": True,
        "beam_expandable": True,
        "beam_label_single": "Main Beam",
        "cables_last": [
            {"key": "tiedown_cable", "label": "Tie-down Cables",
             "section": "SS 6x19 --", "note": "Uplift resistance"},
        ],
    },
    ("saddle_span", "frame_supported_saddle"): {
        "membrane_first": True,
        "beam_expandable": True,
        "beam_label_single": "Main Beam",
        "purlins_expandable": True,
        "extra_rows_before_cables": [
            {"key": "secondary_beam", "label": "Secondary Beams",
             "section": "CHS --", "note": "Replaces tie-down uplift action"},
        ],
    },
    ("cantilever", "cantilever_leaf"): {
        "membrane_first": True,
        "fixed_middle": [
            {"key": "column", "label": "Column (Uni-Pole)",
             "section": "CHS --", "note": "Base fixed"},
            {"key": "spine", "label": "Curved Spine",
             "section": "CHS --", "note": "Main beam"},
            {"key": "ribs", "label": "Radial Ribs",
             "section": "CHS --", "note": "Both sides"},
        ],
        "cables_last": [
            {"key": "perimeter_cable", "label": "Perimeter Cable",
             "section": "SS 6x19 --", "note": "Follows membrane edge"},
        ],
    },
    ("cantilever", "cantilever_hypar"): {
        "membrane_first": True,
        "fixed_middle": [
            {"key": "column", "label": "Column (Uni-Pole)",
             "section": "CHS --", "note": "Base fixed"},
            {"key": "arm", "label": "Curved Arc Arm",
             "section": "CHS --", "note": "Cantilever arm"},
            {"key": "strut", "label": "Diagonal Strut",
             "section": "CHS --", "note": "Triangulates arm to column"},
            {"key": "ribs", "label": "Perpendicular Ribs",
             "section": "CHS --", "note": "Two, at arm midpoint"},
        ],
        "cables_last": [
            {"key": "perimeter_cable", "label": "Perimeter Cable",
             "section": "SS 6x19 --", "note": "Follows membrane edge"},
        ],
    },
}


def expand_beam_rows(construction_type):
    """Return the list of member rows for a beam of the given construction type."""
    if construction_type == "planar_truss":
        return [dict(r) for r in _PLANAR_TRUSS_ROWS]
    if construction_type == "space_truss":
        return [dict(r) for r in _SPACE_TRUSS_ROWS]
    return [
        {"key": "main_beam", "label": "Main Beam",
         "section": "CHS --", "note": ""},
    ]


def get_structure(key):
    """Return the structure dict for a given key, or None."""
    return STRUCTURE_TYPES.get(key)


def get_variants(key):
    """Return the list of variants for a given structure key."""
    return STRUCTURE_VARIANTS.get(key, [])


def get_member_schema(structure_key, variant_key):
    """Return the member schema for a structure+variant, or None."""
    return MEMBER_SCHEMA.get((structure_key, variant_key))


def get_all_categories():
    """Return sorted list of unique categories."""
    return sorted(set(v.get("category", "") for v in STRUCTURE_TYPES.values()))





