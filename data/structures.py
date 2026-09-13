# =============================================================================
# SDSe - Structure Types Catalogue
# =============================================================================
# Canonical list of structure types and their variants.
#
# STRUCTURE_TYPES    - main structure types (8 in Phase 1)
# STRUCTURE_VARIANTS - sub-types under each main type
#
# Usage:
#   from data.structures import STRUCTURE_TYPES, STRUCTURE_VARIANTS
#
# History:
#   2026-09-13 - Reduced from 27 legacy types to 8 final mains.
#                Cantilever promoted to a main type.
#                Leaf and Flower moved out of Saddle Span.
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
        {"key": "standard_saddle", "name": "Standard Saddle",
         "description": "Tie-down supported. Beam in bending.",
         "available": True},
        {"key": "frame_supported_saddle", "name": "Frame Supported Saddle",
         "description": "Rigid frame support. Purlin, strut, and cable.",
         "available": True},
    ],
    "cantilever": [
        {"key": "cantilever_leaf", "name": "Cantilever Leaf",
         "description": "Curved spine and radial ribs. Leaf shape.",
         "available": True},
        {"key": "cantilever_flower", "name": "Cantilever Flower",
         "description": "Multi-leaf layered spiral.",
         "available": False},
        {"key": "cantilever_cone", "name": "Cantilever Cone",
         "description": "Column with arm and cone membrane.",
         "available": True},
        {"key": "cantilever_pyramid", "name": "Cantilever Pyramid",
         "description": "Column with arm and pyramid membrane.",
         "available": True},
        {"key": "cantilever_bell", "name": "Cantilever Bell",
         "description": "Column with arm and bell-shaped membrane.",
         "available": True},
        {"key": "cantilever_sail", "name": "Cantilever Sail",
         "description": "Column with arm and sail membrane.",
         "available": True},
        {"key": "cantilever_hypar", "name": "Cantilever Hypar",
         "description": "Column with arm and hypar membrane.",
         "available": True},
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


def get_structure(key):
    """Return the structure dict for a given key, or None."""
    return STRUCTURE_TYPES.get(key)


def get_variants(key):
    """Return the list of variants for a given structure key."""
    return STRUCTURE_VARIANTS.get(key, [])


def get_all_categories():
    """Return sorted list of unique categories."""
    return sorted(set(v.get("category", "") for v in STRUCTURE_TYPES.values()))
