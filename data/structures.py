# =============================================================================
# SDSe - Structure Types Catalogue
# =============================================================================
# All structure types available in SDSe.
#
# Each entry contains:
#   name        - display name
#   icon        - single character marker (ASCII-only for mobile safety)
#   description - one-line description shown in the catalog
#   category    - Tensile / Frame / Spatial / Specialized
#
# NOTE: This catalogue is the v9.1 baseline (27 structures). Phase 6 of the
#       modular rebuild trims this list down to the final 7 structures:
#       1. Saddle Span
#       2. Tensile Sails Roof
#       3. Framed Tensile Roof
#       4. Uni-Pole Tensile Roof
#       5. Canopy
#       6. Frame Tent
#       7. Portal Frame
#
# Usage:
#   from data.structures import STRUCTURE_TYPES
# =============================================================================

STRUCTURE_TYPES = {
    # ===== Curved Beams (featured) =====
    "parabolic_beam": {
        "name": "Parabolic Curved Beam",
        "icon": "P",
        "description": "Parabolic arch beam with single or truss members",
        "category": "Frame",
    },
    "circular_beam": {
        "name": "Circular Curved Beam",
        "icon": "C",
        "description": "Circular arch beam with single or truss members",
        "category": "Frame",
    },

    # ===== Tensile =====
    "saddle_span": {
        "name": "Saddle Span",
        "icon": "S",
        "description": "Curved saddle-shaped tensile structure",
        "category": "Tensile",
    },
    "clear_span_tent": {
        "name": "Clear-Span Tent",
        "icon": "T",
        "description": "Column-free tensile tent structure",
        "category": "Tensile",
    },
    "tensile_membrane": {
        "name": "Tensile Membrane",
        "icon": "M",
        "description": "Tensioned fabric membrane structure",
        "category": "Tensile",
    },
    "cable_net": {
        "name": "Cable Net",
        "icon": "N",
        "description": "Interconnected cable grid structure",
        "category": "Tensile",
    },
    "cable_stayed": {
        "name": "Cable-Stayed",
        "icon": "K",
        "description": "Cable-supported tensile structure",
        "category": "Tensile",
    },
    "mast_supported": {
        "name": "Mast Supported",
        "icon": "U",
        "description": "Central mast with tensioned membrane",
        "category": "Tensile",
    },
    "stress_ribbon": {
        "name": "Stress Ribbon",
        "icon": "R",
        "description": "Tensioned ribbon bridge structure",
        "category": "Tensile",
    },
    "inflatable_structure": {
        "name": "Inflatable Structure",
        "icon": "I",
        "description": "Air-supported membrane structure",
        "category": "Tensile",
    },

    # ===== Frame =====
    "portal_frame": {
        "name": "Portal Frame",
        "icon": "F",
        "description": "Rigid steel frame structure",
        "category": "Frame",
    },
    "arch_structure": {
        "name": "Arch Structure",
        "icon": "A",
        "description": "Curved arch supporting structure",
        "category": "Frame",
    },
    "frame_system": {
        "name": "Frame System",
        "icon": "f",
        "description": "Traditional frame structure",
        "category": "Frame",
    },
    "fabricated_beam": {
        "name": "Fabricated Beam",
        "icon": "B",
        "description": "Custom fabricated beam structure",
        "category": "Frame",
    },
    "shell_structure": {
        "name": "Shell Structure",
        "icon": "H",
        "description": "Thin shell structural surface",
        "category": "Frame",
    },
    "folded_plate": {
        "name": "Folded Plate",
        "icon": "D",
        "description": "Folded structural surface",
        "category": "Frame",
    },

    # ===== Spatial =====
    "geodesic_dome": {
        "name": "Geodesic Dome",
        "icon": "G",
        "description": "Spherical lattice shell structure",
        "category": "Spatial",
    },
    "space_frame": {
        "name": "Space Frame",
        "icon": "X",
        "description": "3D truss network structure",
        "category": "Spatial",
    },
    "grid_shell": {
        "name": "Grid Shell",
        "icon": "Y",
        "description": "Grid-based shell structure",
        "category": "Spatial",
    },
    "tensegrity": {
        "name": "Tensegrity",
        "icon": "Q",
        "description": "Tension-integrity structure",
        "category": "Spatial",
    },
    "hybrid_system": {
        "name": "Hybrid System",
        "icon": "Z",
        "description": "Combined structural systems",
        "category": "Spatial",
    },

    # ===== Specialized =====
    "retractable_roof": {
        "name": "Retractable Roof",
        "icon": "V",
        "description": "Opening and closing roof system",
        "category": "Specialized",
    },
    "suspension_bridge": {
        "name": "Suspension Bridge",
        "icon": "b",
        "description": "Cable-suspended bridge structure",
        "category": "Specialized",
    },
    "truss_system": {
        "name": "Truss System",
        "icon": "t",
        "description": "Triangulated truss structure",
        "category": "Specialized",
    },
    "roof_system": {
        "name": "Roof System",
        "icon": "r",
        "description": "Comprehensive roof structure",
        "category": "Specialized",
    },
    "shade_structure": {
        "name": "Shade Structure",
        "icon": "h",
        "description": "Architectural shading system",
        "category": "Specialized",
    },
    "bridge_viaduct": {
        "name": "Bridge/Viaduct",
        "icon": "w",
        "description": "Structural bridge system",
        "category": "Specialized",
    },
}


def get_structure(name):
    """Return the structure dict for a given name, or None."""
    return STRUCTURE_TYPES.get(name)


def get_structures_by_category(category):
    """Return list of (key, structure) tuples filtered by category."""
    return [(k, v) for k, v in STRUCTURE_TYPES.items() if v.get("category") == category]


def get_all_categories():
    """Return sorted list of unique categories."""
    return sorted(set(v.get("category", "") for v in STRUCTURE_TYPES.values()))
