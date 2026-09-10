# =============================================================================
# SDSe - Material Properties
# =============================================================================
# Steel, fabric, cable, and joint material properties.
#
# Contents:
#   STEEL_MATERIALS    - structural material families and grades
#   FABRIC_PROPERTIES  - membrane fabric specifications
#   CABLE_PROPERTIES   - cable/rope specifications
#   JOINT_MULTIPLIERS  - connection factors (welded vs bolted)
#
# Usage:
#   from data.materials import STEEL_MATERIALS, FABRIC_PROPERTIES
# =============================================================================

# =============================================================================
# STEEL AND STRUCTURAL MATERIALS
# =============================================================================
# fy = yield strength (MPa)
# fu = ultimate strength (MPa)
# E  = Young modulus (MPa)
# rho = density (kg/m^3)
# "default" = recommended grade when user does not specify

STEEL_MATERIALS = {
    "Steel": {
        "S235": {"fy": 235, "fu": 360, "E": 210000, "rho": 7850},
        "S275": {"fy": 275, "fu": 430, "E": 210000, "rho": 7850},
        "S355": {"fy": 355, "fu": 510, "E": 210000, "rho": 7850},
        "S420": {"fy": 420, "fu": 520, "E": 210000, "rho": 7850},
        "S460": {"fy": 460, "fu": 540, "E": 210000, "rho": 7850},
        "default": "S355",
    },
    "Aluminum": {
        "6061-T6": {"fy": 240, "fu": 290, "E": 69000, "rho": 2700},
        "6082-T6": {"fy": 250, "fu": 295, "E": 70000, "rho": 2700},
        "default": "6061-T6",
    },
    "Wood": {
        "GL24h": {"fy": 24, "fu": 24, "E": 11000, "rho": 420},
        "GL28h": {"fy": 28, "fu": 28, "E": 12600, "rho": 440},
        "C24":   {"fy": 24, "fu": 24, "E": 11000, "rho": 420},
        "default": "GL28h",
    },
    "Composite": {
        "GFRP": {"fy": 300, "fu": 500, "E": 30000, "rho": 1800},
        "CFRP": {"fy": 800, "fu": 1200, "E": 120000, "rho": 1600},
        "default": "GFRP",
    },
}

# =============================================================================
# FABRIC PROPERTIES
# =============================================================================
# f_u_warp / f_u_weft = ultimate tensile strength (N/mm or kN/m depending
#                        on how the manufacturer quotes it)
# E_warp / E_weft     = elastic modulus (MPa)
# t_mm                = nominal thickness (mm)
# kg_m2               = mass per unit area (kg/m^2)

FABRIC_PROPERTIES = {
    "PVDF": {
        "Type I":   {"f_u_warp": 60,  "f_u_weft": 55,  "E_warp": 800,  "E_weft": 700,  "t_mm": 0.6, "kg_m2": 0.6},
        "Type II":  {"f_u_warp": 80,  "f_u_weft": 70,  "E_warp": 1000, "E_weft": 900,  "t_mm": 0.7, "kg_m2": 0.7},
        "Type III": {"f_u_warp": 100, "f_u_weft": 90,  "E_warp": 1200, "E_weft": 1000, "t_mm": 0.8, "kg_m2": 0.9},
        "Type IV":  {"f_u_warp": 120, "f_u_weft": 110, "E_warp": 1400, "E_weft": 1200, "t_mm": 0.9, "kg_m2": 1.1},
        "default": "Type III",
    },
    "PTFE": {
        "Type A": {"f_u_warp": 140, "f_u_weft": 120, "E_warp": 1500, "E_weft": 1300, "t_mm": 0.8, "kg_m2": 1.2},
        "Type B": {"f_u_warp": 160, "f_u_weft": 140, "E_warp": 1700, "E_weft": 1500, "t_mm": 1.0, "kg_m2": 1.5},
        "default": "Type A",
    },
    "ETFE": {
        "200um": {"f_u_warp": 50, "f_u_weft": 50, "E_warp": 850, "E_weft": 850, "t_mm": 0.20, "kg_m2": 0.35},
        "250um": {"f_u_warp": 52, "f_u_weft": 52, "E_warp": 900, "E_weft": 900, "t_mm": 0.25, "kg_m2": 0.44},
        "default": "250um",
    },
}

# =============================================================================
# CABLE PROPERTIES
# =============================================================================
# d    = diameter (mm)
# A    = cross-sectional area (mm^2)
# f_u  = ultimate tensile strength (MPa)
# E    = Young modulus (MPa)
# kg_m = mass per unit length (kg/m)

CABLE_PROPERTIES = {
    "Strand": {
        "6mm":  {"d": 6.0,  "A": 22.9,  "f_u": 1770, "E": 160000, "kg_m": 0.180},
        "8mm":  {"d": 8.0,  "A": 40.7,  "f_u": 1770, "E": 160000, "kg_m": 0.320},
        "10mm": {"d": 10.0, "A": 63.6,  "f_u": 1770, "E": 160000, "kg_m": 0.500},
        "12mm": {"d": 12.0, "A": 91.6,  "f_u": 1770, "E": 160000, "kg_m": 0.720},
        "14mm": {"d": 14.0, "A": 124.7, "f_u": 1770, "E": 160000, "kg_m": 0.980},
        "16mm": {"d": 16.0, "A": 162.9, "f_u": 1770, "E": 160000, "kg_m": 1.280},
        "18mm": {"d": 18.0, "A": 206.2, "f_u": 1770, "E": 160000, "kg_m": 1.620},
        "20mm": {"d": 20.0, "A": 254.6, "f_u": 1770, "E": 160000, "kg_m": 2.000},
        "22mm": {"d": 22.0, "A": 308.0, "f_u": 1770, "E": 160000, "kg_m": 2.420},
        "24mm": {"d": 24.0, "A": 366.6, "f_u": 1770, "E": 160000, "kg_m": 2.880},
        "default": "16mm",
    },
    "Locked Coil": {
        "40mm": {"d": 40.0, "A": 980.0,  "f_u": 1570, "E": 160000, "kg_m": 7.70},
        "50mm": {"d": 50.0, "A": 1530.0, "f_u": 1570, "E": 160000, "kg_m": 12.00},
        "60mm": {"d": 60.0, "A": 2200.0, "f_u": 1570, "E": 160000, "kg_m": 17.30},
        "default": "50mm",
    },
    "Spiral": {
        "12mm": {"d": 12.0, "A": 85.0,  "f_u": 1570, "E": 160000, "kg_m": 0.67},
        "16mm": {"d": 16.0, "A": 150.0, "f_u": 1570, "E": 160000, "kg_m": 1.18},
        "20mm": {"d": 20.0, "A": 235.0, "f_u": 1570, "E": 160000, "kg_m": 1.85},
        "default": "16mm",
    },
}

# =============================================================================
# JOINT MULTIPLIERS
# =============================================================================
# Multiply the design resistance by this factor depending on joint type.

JOINT_MULTIPLIERS = {
    "welded": {"factor": 1.2, "description": "Rigid moment connections"},
    "bolted": {"factor": 1.0, "description": "Pin connections - economical"},
}
