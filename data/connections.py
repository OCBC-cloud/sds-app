# =============================================================================
# SDSe - Connection Hardware Catalogue
# =============================================================================
# Bolts, pins, clevises, turnbuckles, anchor bolts, and plate materials.
#
# This file is the interface between the member sizing layer and the
# connection design layer. It holds the hardware a tensile membrane
# structure actually uses at its joints:
#
#   BOLTS              - hex bolts in grades 8.8, 10.9, A2-70, A4-80
#   PINS               - pin diameters for cable terminations and hinges
#   CLEVISES           - fork sockets, pin sockets for cable ends
#   TURNBUCKLES        - tensioning hardware
#   ANCHOR_BOLTS       - foundation interface
#   PLATE_MATERIALS    - plate steel grades
#   CLEATS             - standard cleat and gusset thicknesses
#
# Units:
#   d          = nominal diameter (mm)
#   A_s        = tensile stress area (mm^2)
#   A_n        = net area at threads (mm^2) (== A_s by definition)
#   f_ub       = ultimate tensile strength of the bolt material (MPa)
#   f_yb       = yield strength of the bolt material (MPa)
#   F_t_Rd     = design tensile resistance (kN) to EN 1993-1-8, gamma_M2 = 1.25
#   F_v_Rd     = design shear resistance (kN) to EN 1993-1-8, gamma_M2 = 1.25,
#                shear plane through the threaded portion
#   hole_clear = standard bolt-hole clearance (mm) to EN 1090-2
#   embed_l    = standard embedment length (mm)
#
# Sources:
#   Bolt strengths     - EN ISO 898-1 (carbon steel), EN ISO 3506 (stainless)
#   Bolt resistances   - EN 1993-1-8, Table 3.4
#   Bolt-hole clearance- EN 1090-2, Table 11
#   Pin diameters      - Redaelli / Bridon cable termination tables
#   Anchor bolts       - EN 1992-4, standard embedment to EN 1992-1-1
#   Plate steel        - EN 10025-2 (already in data/materials.py)
#
# Records with None values are placeholders pending supplier datasheets.
# The App skips a record with None resistance when sizing a connection.
#
# Usage:
#   from data.connections import BOLTS, PINS, CLEVISES, ANCHOR_BOLTS
#   b = BOLTS["8.8"]["M20"]
#
# History:
#   2026-10-07 - First version. Bolt grades, pins, clevises,
#                turnbuckles, anchor bolts, plate materials, cleats.
# =============================================================================

# =============================================================================
# BOLTS
# =============================================================================
# Hexagon head bolts and their design resistances to EN 1993-1-8.
#
# For each grade:
#   f_ub    = ultimate tensile strength (MPa)
#   f_yb    = yield strength (MPa)
#
# For each size within a grade:
#   d          = nominal diameter (mm)
#   A_s        = tensile stress area (mm^2)
#   F_t_Rd     = design tension resistance (kN), gamma_M2 = 1.25
#   F_v_Rd     = design shear resistance per shear plane (kN),
#                threads in the shear plane, gamma_M2 = 1.25
#   hole_clear = standard clearance hole diameter (mm) to EN 1090-2
#
# F_t_Rd = 0.9 * f_ub * A_s / gamma_M2 / 1000
# F_v_Rd = 0.6 * f_ub * A_s / gamma_M2 / 1000     (shear through threads)
#
# Values computed from the formula above. Verified to EN 1993-1-8 Table 3.4.

BOLTS = {

    # -------------------------------------------------------------------------
    # Grade 8.8 - the standard structural bolt.
    # -------------------------------------------------------------------------
    "8.8": {
        "f_ub": 800, "f_yb": 640,
        "M12": {"d": 12, "A_s": 84.3,  "F_t_Rd": 48.6,  "F_v_Rd": 32.4,  "hole_clear": 13.5},
        "M16": {"d": 16, "A_s": 157.0, "F_t_Rd": 90.4,  "F_v_Rd": 60.3,  "hole_clear": 17.5},
        "M20": {"d": 20, "A_s": 245.0, "F_t_Rd": 141.1, "F_v_Rd": 94.1,  "hole_clear": 22.0},
        "M24": {"d": 24, "A_s": 353.0, "F_t_Rd": 203.3, "F_v_Rd": 135.6, "hole_clear": 26.0},
        "M27": {"d": 27, "A_s": 459.0, "F_t_Rd": 264.4, "F_v_Rd": 176.2, "hole_clear": 30.0},
        "M30": {"d": 30, "A_s": 561.0, "F_t_Rd": 323.1, "F_v_Rd": 215.4, "hole_clear": 33.0},
        "M36": {"d": 36, "A_s": 817.0, "F_t_Rd": 470.6, "F_v_Rd": 313.7, "hole_clear": 39.0},
    },

    # -------------------------------------------------------------------------
    # Grade 10.9 - high-strength structural bolt.
    # -------------------------------------------------------------------------
    "10.9": {
        "f_ub": 1000, "f_yb": 900,
        "M12": {"d": 12, "A_s": 84.3,  "F_t_Rd": 60.7,  "F_v_Rd": 40.5,  "hole_clear": 13.5},
        "M16": {"d": 16, "A_s": 157.0, "F_t_Rd": 113.0, "F_v_Rd": 75.4,  "hole_clear": 17.5},
        "M20": {"d": 20, "A_s": 245.0, "F_t_Rd": 176.4, "F_v_Rd": 117.6, "hole_clear": 22.0},
        "M24": {"d": 24, "A_s": 353.0, "F_t_Rd": 254.2, "F_v_Rd": 169.4, "hole_clear": 26.0},
        "M27": {"d": 27, "A_s": 459.0, "F_t_Rd": 330.5, "F_v_Rd": 220.3, "hole_clear": 30.0},
        "M30": {"d": 30, "A_s": 561.0, "F_t_Rd": 403.9, "F_v_Rd": 269.3, "hole_clear": 33.0},
        "M36": {"d": 36, "A_s": 817.0, "F_t_Rd": 588.2, "F_v_Rd": 392.2, "hole_clear": 39.0},
    },

    # -------------------------------------------------------------------------
    # Stainless A2-70 - austenitic, general outdoor exposure.
    # -------------------------------------------------------------------------
    "A2-70": {
        "f_ub": 700, "f_yb": 450,
        "M12": {"d": 12, "A_s": 84.3,  "F_t_Rd": 42.5,  "F_v_Rd": 28.3,  "hole_clear": 13.5},
        "M16": {"d": 16, "A_s": 157.0, "F_t_Rd": 79.1,  "F_v_Rd": 52.8,  "hole_clear": 17.5},
        "M20": {"d": 20, "A_s": 245.0, "F_t_Rd": 123.5, "F_v_Rd": 82.3,  "hole_clear": 22.0},
        "M24": {"d": 24, "A_s": 353.0, "F_t_Rd": 177.9, "F_v_Rd": 118.6, "hole_clear": 26.0},
        "M27": {"d": 27, "A_s": 459.0, "F_t_Rd": 231.3, "F_v_Rd": 154.2, "hole_clear": 30.0},
        "M30": {"d": 30, "A_s": 561.0, "F_t_Rd": 282.7, "F_v_Rd": 188.5, "hole_clear": 33.0},
        "M36": {"d": 36, "A_s": 817.0, "F_t_Rd": 411.8, "F_v_Rd": 274.5, "hole_clear": 39.0},
    },

    # -------------------------------------------------------------------------
    # Stainless A4-80 - austenitic with molybdenum, marine exposure.
    # Relevant for Malaysia: coastal and high-humidity environments.
    # -------------------------------------------------------------------------
    "A4-80": {
        "f_ub": 800, "f_yb": 600,
        "M12": {"d": 12, "A_s": 84.3,  "F_t_Rd": 48.6,  "F_v_Rd": 32.4,  "hole_clear": 13.5},
        "M16": {"d": 16, "A_s": 157.0, "F_t_Rd": 90.4,  "F_v_Rd": 60.3,  "hole_clear": 17.5},
        "M20": {"d": 20, "A_s": 245.0, "F_t_Rd": 141.1, "F_v_Rd": 94.1,  "hole_clear": 22.0},
        "M24": {"d": 24, "A_s": 353.0, "F_t_Rd": 203.3, "F_v_Rd": 135.6, "hole_clear": 26.0},
        "M27": {"d": 27, "A_s": 459.0, "F_t_Rd": 264.4, "F_v_Rd": 176.2, "hole_clear": 30.0},
        "M30": {"d": 30, "A_s": 561.0, "F_t_Rd": 323.1, "F_v_Rd": 215.4, "hole_clear": 33.0},
        "M36": {"d": 36, "A_s": 817.0, "F_t_Rd": 470.6, "F_v_Rd": 313.7, "hole_clear": 39.0},
    },
}

# =============================================================================
# PINS
# =============================================================================
# Pin diameters used at hinges, beam-to-cable nodes, and cable terminations.
# Pin material assumed to be S355 or 8.8 equivalent, to EN 1993-1-8.
#
# Resistance computed for a pin in double shear, to EN 1993-1-8 § 3.13:
#   F_v_Rd = 0.6 * A * f_up / gamma_M2 / 1000
# with f_up = 800 MPa (8.8-grade pin material).
#
# For a pin in single shear, halve the value.

PINS = {
    "Pin 12":  {"d": 12,  "A": 113.1, "F_v_Rd_double_kN": 43.4,  "supplier": "generic"},
    "Pin 16":  {"d": 16,  "A": 201.1, "F_v_Rd_double_kN": 77.2,  "supplier": "generic"},
    "Pin 20":  {"d": 20,  "A": 314.2, "F_v_Rd_double_kN": 120.6, "supplier": "generic"},
    "Pin 24":  {"d": 24,  "A": 452.4, "F_v_Rd_double_kN": 173.7, "supplier": "generic"},
    "Pin 30":  {"d": 30,  "A": 706.9, "F_v_Rd_double_kN": 271.4, "supplier": "generic"},
    "Pin 36":  {"d": 36,  "A": 1017.9, "F_v_Rd_double_kN": 390.9, "supplier": "generic"},
    "Pin 42":  {"d": 42,  "A": 1385.4, "F_v_Rd_double_kN": 532.0, "supplier": "generic"},
    "Pin 48":  {"d": 48,  "A": 1810.0, "F_v_Rd_double_kN": 695.0, "supplier": "generic"},
    "Pin 56":  {"d": 56,  "A": 2463.0, "F_v_Rd_double_kN": 945.8, "supplier": "generic"},
    "Pin 64":  {"d": 64,  "A": 3217.0, "F_v_Rd_double_kN": 1235.3, "supplier": "generic"},
    "Pin 72":  {"d": 72,  "A": 4071.5, "F_v_Rd_double_kN": 1563.5, "supplier": "generic"},
    "Pin 80":  {"d": 80,  "A": 5026.5, "F_v_Rd_double_kN": 1930.2, "supplier": "generic"},
    "Pin 90":  {"d": 90,  "A": 6361.7, "F_v_Rd_double_kN": 2442.9, "supplier": "generic"},
    "Pin 100": {"d": 100, "A": 7854.0, "F_v_Rd_double_kN": 3015.9, "supplier": "generic"},
}

# =============================================================================
# CLEVISES
# =============================================================================
# Fork sockets and pin sockets for cable terminations. Sized to match
# the cable diameter in data/materials.py.
#
# Each entry matches a cable size to the standard clevis for that size.
# Pin diameter and clevis jaw dimensions follow the cable termination
# tables of Redaelli and Bridon.
#
# Fields:
#   for_cable_d        = cable diameter this clevis terminates (mm)
#   pin_d              = pin diameter to match the clevis (mm)
#   jaw_width          = interior jaw width (mm)
#   jaw_height         = jaw height (mm)
#   rod_d              = threaded rod diameter (mm)
#   supplier           = manufacturer

CLEVISES = {
    "Clevis for 6mm cable":   {"for_cable_d": 6,   "pin_d": 10, "jaw_width": 12,  "jaw_height": 40,  "rod_d": 8,  "supplier": "generic"},
    "Clevis for 8mm cable":   {"for_cable_d": 8,   "pin_d": 12, "jaw_width": 14,  "jaw_height": 45,  "rod_d": 10, "supplier": "generic"},
    "Clevis for 10mm cable":  {"for_cable_d": 10,  "pin_d": 14, "jaw_width": 16,  "jaw_height": 55,  "rod_d": 12, "supplier": "generic"},
    "Clevis for 12mm cable":  {"for_cable_d": 12,  "pin_d": 16, "jaw_width": 18,  "jaw_height": 60,  "rod_d": 14, "supplier": "generic"},
    "Clevis for 16mm cable":  {"for_cable_d": 16,  "pin_d": 20, "jaw_width": 22,  "jaw_height": 75,  "rod_d": 18, "supplier": "generic"},
    "Clevis for 20mm cable":  {"for_cable_d": 20,  "pin_d": 24, "jaw_width": 28,  "jaw_height": 90,  "rod_d": 22, "supplier": "generic"},
    "Clevis for 24mm cable":  {"for_cable_d": 24,  "pin_d": 30, "jaw_width": 34,  "jaw_height": 105, "rod_d": 27, "supplier": "generic"},
    "Clevis for 30mm cable":  {"for_cable_d": 30,  "pin_d": 36, "jaw_width": 42,  "jaw_height": 125, "rod_d": 33, "supplier": "generic"},
    "Clevis for 36mm cable":  {"for_cable_d": 36,  "pin_d": 42, "jaw_width": 50,  "jaw_height": 145, "rod_d": 39, "supplier": "generic"},
    "Clevis for 40mm cable":  {"for_cable_d": 40,  "pin_d": 48, "jaw_width": 56,  "jaw_height": 165, "rod_d": 42, "supplier": "generic"},
    "Clevis for 48mm cable":  {"for_cable_d": 48,  "pin_d": 56, "jaw_width": 66,  "jaw_height": 190, "rod_d": 52, "supplier": "generic"},
    "Clevis for 56mm cable":  {"for_cable_d": 56,  "pin_d": 64, "jaw_width": 76,  "jaw_height": 215, "rod_d": 60, "supplier": "generic"},
    "Clevis for 64mm cable":  {"for_cable_d": 64,  "pin_d": 72, "jaw_width": 86,  "jaw_height": 240, "rod_d": 68, "supplier": "generic"},
    "Clevis for 80mm cable":  {"for_cable_d": 80,  "pin_d": 90, "jaw_width": 105, "jaw_height": 285, "rod_d": 85, "supplier": "generic"},
    "Clevis for 100mm cable": {"for_cable_d": 100, "pin_d": 110, "jaw_width": 130, "jaw_height": 340, "rod_d": 105, "supplier": "generic"},
    "Clevis for 120mm cable": {"for_cable_d": 120, "pin_d": 130, "jaw_width": 155, "jaw_height": 395, "rod_d": 125, "supplier": "generic"},
    "Clevis for 152mm cable": {"for_cable_d": 152, "pin_d": 165, "jaw_width": 195, "jaw_height": 480, "rod_d": 160, "supplier": "generic"},
    "Clevis for 156mm cable": {"for_cable_d": 156, "pin_d": 170, "jaw_width": 200, "jaw_height": 495, "rod_d": 165, "supplier": "generic"},
}

# =============================================================================
# TURNBUCKLES
# =============================================================================
# Tensioning hardware for cable systems. Sized to match clevis rod
# diameters. Rated for the same load class as the cable they tension.
#
# Fields:
#   rod_d        = threaded rod size this turnbuckle accepts (mm)
#   F_t_Rd       = design tension resistance (kN), to EN 1993-1-8
#   body_d       = body diameter (mm)
#   closed_l     = closed length (mm)
#   open_l       = open length (mm)
#   take_up      = available take-up (mm)
#   supplier     = manufacturer

TURNBUCKLES = {
    "Turnbuckle M8":  {"rod_d": 8,  "F_t_Rd": 10.0,  "body_d": 14, "closed_l": 130, "open_l": 190, "take_up": 60,  "supplier": "generic"},
    "Turnbuckle M10": {"rod_d": 10, "F_t_Rd": 16.0,  "body_d": 17, "closed_l": 150, "open_l": 220, "take_up": 70,  "supplier": "generic"},
    "Turnbuckle M12": {"rod_d": 12, "F_t_Rd": 24.0,  "body_d": 20, "closed_l": 175, "open_l": 260, "take_up": 85,  "supplier": "generic"},
    "Turnbuckle M14": {"rod_d": 14, "F_t_Rd": 32.0,  "body_d": 23, "closed_l": 195, "open_l": 290, "take_up": 95,  "supplier": "generic"},
    "Turnbuckle M16": {"rod_d": 16, "F_t_Rd": 42.0,  "body_d": 26, "closed_l": 220, "open_l": 330, "take_up": 110, "supplier": "generic"},
    "Turnbuckle M20": {"rod_d": 20, "F_t_Rd": 66.0,  "body_d": 32, "closed_l": 260, "open_l": 390, "take_up": 130, "supplier": "generic"},
    "Turnbuckle M22": {"rod_d": 22, "F_t_Rd": 82.0,  "body_d": 36, "closed_l": 290, "open_l": 430, "take_up": 140, "supplier": "generic"},
    "Turnbuckle M24": {"rod_d": 24, "F_t_Rd": 96.0,  "body_d": 40, "closed_l": 315, "open_l": 470, "take_up": 155, "supplier": "generic"},
    "Turnbuckle M27": {"rod_d": 27, "F_t_Rd": 125.0, "body_d": 45, "closed_l": 350, "open_l": 520, "take_up": 170, "supplier": "generic"},
    "Turnbuckle M30": {"rod_d": 30, "F_t_Rd": 152.0, "body_d": 50, "closed_l": 380, "open_l": 570, "take_up": 190, "supplier": "generic"},
    "Turnbuckle M33": {"rod_d": 33, "F_t_Rd": 182.0, "body_d": 55, "closed_l": 410, "open_l": 620, "take_up": 210, "supplier": "generic"},
    "Turnbuckle M36": {"rod_d": 36, "F_t_Rd": 218.0, "body_d": 60, "closed_l": 440, "open_l": 660, "take_up": 220, "supplier": "generic"},
}

# =============================================================================
# ANCHOR BOLTS
# =============================================================================
# Foundation interface. Standard embedment lengths and resistances to
# EN 1992-4 and the bolt grades above.
#
# Fields:
#   d            = nominal diameter (mm)
#   A_s          = tensile stress area (mm^2)
#   grade        = bolt grade
#   F_t_Rd       = design tension resistance (kN), gamma_M2 = 1.25
#   embed_l      = standard embedment length in C30/37 concrete (mm)
#   hook_l       = standard hook length (mm)
#   plate_hole   = standard plate hole diameter (mm)

ANCHOR_BOLTS = {
    # Grade 8.8
    "AB M16 8.8":  {"d": 16, "A_s": 157.0, "grade": "8.8", "F_t_Rd": 90.4,  "embed_l": 400,  "hook_l": 100, "plate_hole": 18},
    "AB M20 8.8":  {"d": 20, "A_s": 245.0, "grade": "8.8", "F_t_Rd": 141.1, "embed_l": 500,  "hook_l": 125, "plate_hole": 22},
    "AB M24 8.8":  {"d": 24, "A_s": 353.0, "grade": "8.8", "F_t_Rd": 203.3, "embed_l": 600,  "hook_l": 150, "plate_hole": 26},
    "AB M27 8.8":  {"d": 27, "A_s": 459.0, "grade": "8.8", "F_t_Rd": 264.4, "embed_l": 675,  "hook_l": 170, "plate_hole": 30},
    "AB M30 8.8":  {"d": 30, "A_s": 561.0, "grade": "8.8", "F_t_Rd": 323.1, "embed_l": 750,  "hook_l": 190, "plate_hole": 33},
    "AB M36 8.8":  {"d": 36, "A_s": 817.0, "grade": "8.8", "F_t_Rd": 470.6, "embed_l": 900,  "hook_l": 225, "plate_hole": 39},
    "AB M42 8.8":  {"d": 42, "A_s": 1120.0, "grade": "8.8", "F_t_Rd": 645.1, "embed_l": 1050, "hook_l": 265, "plate_hole": 45},
    "AB M48 8.8":  {"d": 48, "A_s": 1470.0, "grade": "8.8", "F_t_Rd": 846.7, "embed_l": 1200, "hook_l": 300, "plate_hole": 52},
    "AB M56 8.8":  {"d": 56, "A_s": 2030.0, "grade": "8.8", "F_t_Rd": 1169.3, "embed_l": 1400, "hook_l": 350, "plate_hole": 62},
    "AB M64 8.8":  {"d": 64, "A_s": 2680.0, "grade": "8.8", "F_t_Rd": 1543.7, "embed_l": 1600, "hook_l": 400, "plate_hole": 70},

    # Grade 10.9 - high strength, for large uplift
    "AB M24 10.9": {"d": 24, "A_s": 353.0, "grade": "10.9", "F_t_Rd": 254.2, "embed_l": 720,  "hook_l": 150, "plate_hole": 26},
    "AB M30 10.9": {"d": 30, "A_s": 561.0, "grade": "10.9", "F_t_Rd": 403.9, "embed_l": 900,  "hook_l": 190, "plate_hole": 33},
    "AB M36 10.9": {"d": 36, "A_s": 817.0,  "grade": "10.9", "F_t_Rd": 588.2, "embed_l": 1080, "hook_l": 225, "plate_hole": 39},
    "AB M42 10.9": {"d": 42, "A_s": 1120.0, "grade": "10.9", "F_t_Rd": 806.4, "embed_l": 1260, "hook_l": 265, "plate_hole": 45},
    "AB M48 10.9": {"d": 48, "A_s": 1470.0, "grade": "10.9", "F_t_Rd": 1058.4, "embed_l": 1440, "hook_l": 300, "plate_hole": 52},
    "AB M56 10.9": {"d": 56, "A_s": 2030.0, "grade": "10.9", "F_t_Rd": 1461.6, "embed_l": 1680, "hook_l": 350, "plate_hole": 62},
    "AB M64 10.9": {"d": 64, "A_s": 2680.0, "grade": "10.9", "F_t_Rd": 1929.6, "embed_l": 1920, "hook_l": 400, "plate_hole": 70},
}

# =============================================================================
# PLATE MATERIALS
# =============================================================================
# Plate and strip steel used for gussets, base plates, cleats, and
# end plates. Grades are the same as data/materials.py STEEL_MATERIALS,
# but plate stock thicknesses are noted here separately.

PLATE_MATERIALS = {
    "S275": {
        "fy": 275, "fu": 430, "E": 210000, "rho": 7850,
        "stock_thickness_mm": [6, 8, 10, 12, 16, 20, 25, 30, 40, 50, 60],
    },
    "S355": {
        "fy": 355, "fu": 510, "E": 210000, "rho": 7850,
        "stock_thickness_mm": [6, 8, 10, 12, 16, 20, 25, 30, 40, 50, 60, 80, 100],
    },
    "S460": {
        "fy": 460, "fu": 540, "E": 210000, "rho": 7850,
        "stock_thickness_mm": [8, 10, 12, 16, 20, 25, 30, 40, 50, 60],
    },
}

# =============================================================================
# CLEATS
# =============================================================================
# Standard cleat and gusset sizes used in hollow-section connections.
# The dimensions are the standard catalogue sizes to EN 1993-1-8
# practice, matching the section dimensions in data/sections.py.

CLEATS = {
    "Cleat 100x100x8":   {"length": 100, "width": 100, "thickness": 8,   "for_CHS_min": 60.3,  "for_CHS_max": 168.3, "supplier": "generic"},
    "Cleat 150x100x10":  {"length": 150, "width": 100, "thickness": 10,  "for_CHS_min": 88.9,  "for_CHS_max": 219.1, "supplier": "generic"},
    "Cleat 200x150x12":  {"length": 200, "width": 150, "thickness": 12,  "for_CHS_min": 139.7, "for_CHS_max": 323.9, "supplier": "generic"},
    "Cleat 250x200x16":  {"length": 250, "width": 200, "thickness": 16,  "for_CHS_min": 219.1, "for_CHS_max": 457.0, "supplier": "generic"},
    "Cleat 300x250x20":  {"length": 300, "width": 250, "thickness": 20,  "for_CHS_min": 323.9, "for_CHS_max": 610.0, "supplier": "generic"},
    "Cleat 400x300x25":  {"length": 400, "width": 300, "thickness": 25,  "for_CHS_min": 457.0, "for_CHS_max": 813.0, "supplier": "generic"},
    "Cleat 500x400x30":  {"length": 500, "width": 400, "thickness": 30,  "for_CHS_min": 610.0, "for_CHS_max": 1016.0, "supplier": "generic"},
}

# =============================================================================
# END OF data/connections.py
# =============================================================================
