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
#
# Sources:
#   Steel grades      - EN 10025-2, adopted in Malaysia as MS EN 10025-2.
#                       Certified Malaysian producers include Nippon Steel,
#                       KOS, Dragon Steel, Amsteel Mills, Grand Faith,
#                       Shenheng Steel, Tangshan Shengcai (CIDB register).
#   Fabric suppliers  - Serge Ferrari (FR), Taiyo Kogyo / Birdair (JP/US),
#                       Verseidag (DE), Sioen (BE), Heytex (DE),
#                       Mehler Texnologies (DE), Chukoh (JP),
#                       Saint-Gobain / Sheerfill (FR/US), DERFLEX (CN),
#                       Nowofol (DE). Malaysia has no domestic membrane
#                       fabric manufacturer; membrane roofs in Malaysia
#                       are design-and-build specialist work with imported
#                       fabric.
#   Cable suppliers   - Redaelli (IT), Bridon (UK), Chinese locked-coil
#                       and spiral strand producers (Aulone, Honghao).
#                       Dimensions to EN 12385 and ETA 06/0126.
#
# History:
#   2026-09-13 - First version. Steel, fabric, cable placeholders.
#   2026-09-30 - Ferrari 702 recorded as Type III PVDF reference.
#   2026-10-07 - Extended to full supplier range. Cables to 156 mm and
#                24,860 kN. Fabrics include all major international
#                suppliers. Records with unconfirmed values marked None.
# =============================================================================

# =============================================================================
# STEEL AND STRUCTURAL MATERIALS
# =============================================================================
# fy  = yield strength (MPa)
# fu  = ultimate strength (MPa)
# E   = Young modulus (MPa)
# rho = density (kg/m^3)
# "default" = recommended grade when user does not specify
#
# Steel grades to EN 10025-2. Adopted in Malaysia as MS EN 10025-2:2011.
# Malaysian certified producers: Nippon Steel, KOS, Dragon Steel,
# Amsteel Mills, Grand Faith, Shenheng Steel, Tangshan Shengcai.

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
# Fields:
#   supplier                 - manufacturer name
#   reference                - product reference
#   f_u_warp / f_u_weft      - ultimate tensile strength (N/mm)
#   E_warp / E_weft          - elastic modulus (MPa)
#   t_mm                     - nominal thickness (mm)
#   kg_m2                    - mass per unit area (kg/m^2)
#   prestress_min_kN_per_m   - minimum recommended prestress
#   prestress_max_kN_per_m   - maximum recommended prestress
#   prestress_default_kN_per_m
#   ratio_limit              - warp/weft prestress ratio limit
#
# Records with None values are placeholders pending supplier datasheets.
# The App skips a record with None properties when selecting a fabric.

FABRIC_PROPERTIES = {

    # -------------------------------------------------------------------------
    # PVDF - PVC-polyester with PVDF topcoat.
    # The workhorse architectural membrane. 15-25 year life.
    # -------------------------------------------------------------------------
    "PVDF": {

        "Ferrari 402": {
            "supplier": "Serge Ferrari",
            "reference": "Precontraint 402",
            "f_u_warp": 40.0, "f_u_weft": 40.0,
            "E_warp": 800.0, "E_weft": 800.0,
            "t_mm": 0.60, "kg_m2": 0.60,
            "prestress_min_kN_per_m": 1.0,
            "prestress_max_kN_per_m": 3.0,
            "prestress_default_kN_per_m": 1.5,
            "ratio_limit": 4.0,
        },
        "Ferrari 502": {
            "supplier": "Serge Ferrari",
            "reference": "Precontraint 502",
            "f_u_warp": 48.0, "f_u_weft": 48.0,
            "E_warp": 1100.0, "E_weft": 1100.0,
            "t_mm": 0.80, "kg_m2": 0.80,
            "prestress_min_kN_per_m": 1.0,
            "prestress_max_kN_per_m": 3.5,
            "prestress_default_kN_per_m": 1.8,
            "ratio_limit": 4.0,
        },
        "Ferrari 702": {
            "supplier": "Serge Ferrari",
            "reference": "Precontraint 702 (Type III PVC-polyester, 1102 g/m2)",
            "f_u_warp": 56.0, "f_u_weft": 56.0,
            "E_warp": 1400.0, "E_weft": 1400.0,
            "t_mm": 1.02, "kg_m2": 1.102,
            "prestress_min_kN_per_m": 1.0,
            "prestress_max_kN_per_m": 4.0,
            "prestress_default_kN_per_m": 2.0,
            "ratio_limit": 4.0,
        },
        "Ferrari 1002": {
            "supplier": "Serge Ferrari",
            "reference": "Precontraint 1002",
            "f_u_warp": 64.0, "f_u_weft": 64.0,
            "E_warp": 1600.0, "E_weft": 1600.0,
            "t_mm": 1.20, "kg_m2": 1.30,
            "prestress_min_kN_per_m": 1.0,
            "prestress_max_kN_per_m": 5.0,
            "prestress_default_kN_per_m": 2.5,
            "ratio_limit": 4.0,
        },
        "Ferrari 1202": {
            "supplier": "Serge Ferrari",
            "reference": "Precontraint 1202",
            "f_u_warp": 72.0, "f_u_weft": 72.0,
            "E_warp": 1800.0, "E_weft": 1800.0,
            "t_mm": 1.40, "kg_m2": 1.50,
            "prestress_min_kN_per_m": 1.5,
            "prestress_max_kN_per_m": 6.0,
            "prestress_default_kN_per_m": 3.0,
            "ratio_limit": 4.0,
        },
        "Sioen Architect 650": {
            "supplier": "Sioen Industries",
            "reference": "Architect 650",
            "f_u_warp": None, "f_u_weft": None,   # values to be confirmed from supplier datasheet
            "E_warp": None, "E_weft": None,        # values to be confirmed from supplier datasheet
            "t_mm": None, "kg_m2": None,           # values to be confirmed from supplier datasheet
            "prestress_min_kN_per_m": 1.0,
            "prestress_max_kN_per_m": 4.0,
            "prestress_default_kN_per_m": 2.0,
            "ratio_limit": 4.0,
        },
        "Heytex B1200": {
            "supplier": "Heytex",
            "reference": "B1200 architectural",
            "f_u_warp": None, "f_u_weft": None,   # values to be confirmed from supplier datasheet
            "E_warp": None, "E_weft": None,        # values to be confirmed from supplier datasheet
            "t_mm": None, "kg_m2": None,           # values to be confirmed from supplier datasheet
            "prestress_min_kN_per_m": 1.0,
            "prestress_max_kN_per_m": 4.0,
            "prestress_default_kN_per_m": 2.0,
            "ratio_limit": 4.0,
        },
        "Mehler Valmex FR1000": {
            "supplier": "Mehler Texnologies",
            "reference": "Valmex FR1000",
            "f_u_warp": None, "f_u_weft": None,   # values to be confirmed from supplier datasheet
            "E_warp": None, "E_weft": None,        # values to be confirmed from supplier datasheet
            "t_mm": None, "kg_m2": None,           # values to be confirmed from supplier datasheet
            "prestress_min_kN_per_m": 1.0,
            "prestress_max_kN_per_m": 4.0,
            "prestress_default_kN_per_m": 2.0,
            "ratio_limit": 4.0,
        },
        "DERFLEX PVDF 1050": {
            "supplier": "DERFLEX",
            "reference": "PVDF-coated polyester 1050 g/m2",
            "f_u_warp": None, "f_u_weft": None,   # values to be confirmed from supplier datasheet
            "E_warp": None, "E_weft": None,        # values to be confirmed from supplier datasheet
            "t_mm": None, "kg_m2": 1.050,          # values to be confirmed from supplier datasheet
            "prestress_min_kN_per_m": 1.0,
            "prestress_max_kN_per_m": 4.0,
            "prestress_default_kN_per_m": 2.0,
            "ratio_limit": 4.0,
        },
        "default": "Ferrari 702",
    },

    # -------------------------------------------------------------------------
    # PTFE - glass-fibre woven, PTFE-coated.
    # Permanent roofs. 25-40 year life. Stronger and stiffer than PVDF.
    # -------------------------------------------------------------------------
    "PTFE": {
        "Sheerfill I": {
            "supplier": "Saint-Gobain / Sheerfill",
            "reference": "Sheerfill I",
            "f_u_warp": 140.0, "f_u_weft": 120.0,
            "E_warp": 1500.0, "E_weft": 1300.0,
            "t_mm": 0.8, "kg_m2": 1.2,
            "prestress_min_kN_per_m": 2.0,
            "prestress_max_kN_per_m": 6.0,
            "prestress_default_kN_per_m": 3.5,
            "ratio_limit": 4.0,
        },
        "Sheerfill II": {
            "supplier": "Saint-Gobain / Sheerfill",
            "reference": "Sheerfill II",
            "f_u_warp": 160.0, "f_u_weft": 140.0,
            "E_warp": 1700.0, "E_weft": 1500.0,
            "t_mm": 1.0, "kg_m2": 1.5,
            "prestress_min_kN_per_m": 2.5,
            "prestress_max_kN_per_m": 7.0,
            "prestress_default_kN_per_m": 4.0,
            "ratio_limit": 4.0,
        },
        "Verseidag B18089": {
            "supplier": "Verseidag",
            "reference": "B18089 PTFE glass-fibre",
            "f_u_warp": 180.0, "f_u_weft": 160.0,
            "E_warp": 1800.0, "E_weft": 1600.0,
            "t_mm": 1.1, "kg_m2": 1.6,
            "prestress_min_kN_per_m": 3.0,
            "prestress_max_kN_per_m": 8.0,
            "prestress_default_kN_per_m": 4.5,
            "ratio_limit": 4.0,
        },
        "Chukoh PTFE 9000": {
            "supplier": "Chukoh Chemical Industries",
            "reference": "PTFE glass-fibre, tensile 9000 N/5cm",
            "f_u_warp": 180.0, "f_u_weft": 170.0,
            "E_warp": None, "E_weft": None,        # values to be confirmed from supplier datasheet
            "t_mm": None, "kg_m2": 1.6,
            "prestress_min_kN_per_m": 3.0,
            "prestress_max_kN_per_m": 8.0,
            "prestress_default_kN_per_m": 4.5,
            "ratio_limit": 4.0,
        },
        "Chinese PTFE 9000": {
            "supplier": "Chinese PTFE producer (generic)",
            "reference": "PTFE glass-fibre, tensile 9000 N/5cm warp / 8500 N/5cm weft",
            "f_u_warp": 180.0, "f_u_weft": 170.0,
            "E_warp": None, "E_weft": None,        # values to be confirmed from supplier datasheet
            "t_mm": None, "kg_m2": 1.8,
            "prestress_min_kN_per_m": 3.0,
            "prestress_max_kN_per_m": 8.0,
            "prestress_default_kN_per_m": 4.5,
            "ratio_limit": 4.0,
        },
        "default": "Sheerfill I",
    },

    # -------------------------------------------------------------------------
    # ETFE - ethylene tetrafluoroethylene film.
    # Used as pneumatic cushions, not single-skin. Supplied as foil.
    # -------------------------------------------------------------------------
    "ETFE": {
        "Nowofol 200um": {
            "supplier": "Nowofol",
            "reference": "ETFE film 200 micron",
            "f_u_warp": 50.0, "f_u_weft": 50.0,
            "E_warp": 850.0, "E_weft": 850.0,
            "t_mm": 0.20, "kg_m2": 0.35,
            "prestress_min_kN_per_m": 0.5,
            "prestress_max_kN_per_m": 2.0,
            "prestress_default_kN_per_m": 1.0,
            "ratio_limit": 4.0,
        },
        "Nowofol 250um": {
            "supplier": "Nowofol",
            "reference": "ETFE film 250 micron",
            "f_u_warp": 52.0, "f_u_weft": 52.0,
            "E_warp": 900.0, "E_weft": 900.0,
            "t_mm": 0.25, "kg_m2": 0.44,
            "prestress_min_kN_per_m": 0.5,
            "prestress_max_kN_per_m": 2.0,
            "prestress_default_kN_per_m": 1.0,
            "ratio_limit": 4.0,
        },
        "Saint-Gobain ETFE 250um": {
            "supplier": "Saint-Gobain Performance Plastics",
            "reference": "ETFE film 250 micron",
            "f_u_warp": None, "f_u_weft": None,   # values to be confirmed from supplier datasheet
            "E_warp": None, "E_weft": None,        # values to be confirmed from supplier datasheet
            "t_mm": 0.25, "kg_m2": 0.44,
            "prestress_min_kN_per_m": 0.5,
            "prestress_max_kN_per_m": 2.0,
            "prestress_default_kN_per_m": 1.0,
            "ratio_limit": 4.0,
        },
        "default": "Nowofol 250um",
    },
}

# =============================================================================
# CABLE PROPERTIES
# =============================================================================
# Fields:
#   d      - nominal diameter (mm)
#   A      - metallic cross-sectional area (mm^2)
#   f_u    - ultimate tensile strength (MPa)
#   E      - Young modulus (MPa)
#   kg_m   - mass per unit length (kg/m)
#   supplier  - manufacturer
#   finish    - corrosion protection system
#
# Breaking load = A * f_u / 1000 (kN).
#
# Dimensions to EN 12385 and ETA 06/0126. Sources: Redaelli (IT),
# Bridon (UK), Chinese locked-coil and spiral strand producers.

CABLE_PROPERTIES = {

    # -------------------------------------------------------------------------
    # Strand (6x19 and similar open spiral, hot-dip galvanized or bright).
    # Small to medium tension members. 1770 MPa standard grade.
    # -------------------------------------------------------------------------
    "Strand": {
        "6mm":  {"d": 6.0,  "A": 22.9,  "f_u": 1770, "E": 160000, "kg_m": 0.180, "supplier": "generic", "finish": "galvanized"},
        "8mm":  {"d": 8.0,  "A": 40.7,  "f_u": 1770, "E": 160000, "kg_m": 0.320, "supplier": "generic", "finish": "galvanized"},
        "10mm": {"d": 10.0, "A": 63.6,  "f_u": 1770, "E": 160000, "kg_m": 0.500, "supplier": "generic", "finish": "galvanized"},
        "12mm": {"d": 12.0, "A": 91.6,  "f_u": 1770, "E": 160000, "kg_m": 0.720, "supplier": "generic", "finish": "galvanized"},
        "14mm": {"d": 14.0, "A": 124.7, "f_u": 1770, "E": 160000, "kg_m": 0.980, "supplier": "generic", "finish": "galvanized"},
        "16mm": {"d": 16.0, "A": 162.9, "f_u": 1770, "E": 160000, "kg_m": 1.280, "supplier": "generic", "finish": "galvanized"},
        "18mm": {"d": 18.0, "A": 206.2, "f_u": 1770, "E": 160000, "kg_m": 1.620, "supplier": "generic", "finish": "galvanized"},
        "20mm": {"d": 20.0, "A": 254.6, "f_u": 1770, "E": 160000, "kg_m": 2.000, "supplier": "generic", "finish": "galvanized"},
        "22mm": {"d": 22.0, "A": 308.0, "f_u": 1770, "E": 160000, "kg_m": 2.420, "supplier": "generic", "finish": "galvanized"},
        "24mm": {"d": 24.0, "A": 366.6, "f_u": 1770, "E": 160000, "kg_m": 2.880, "supplier": "generic", "finish": "galvanized"},
        "default": "16mm",
    },

    # -------------------------------------------------------------------------
    # Bridon Dyform 6 - compacted strand, high modulus, high strength.
    # Grades EIP/1960 and EIP/2160. Small to medium tension members
    # with higher capacity per unit diameter than standard strand.
    # -------------------------------------------------------------------------
    "Dyform 6": {
        "Dyform6 8mm 1960":  {"d": 8.0,  "A": 49.0,  "f_u": 1960, "E": 160000, "kg_m": 0.39, "supplier": "Bridon", "finish": "galvanized"},
        "Dyform6 10mm 1960": {"d": 10.0, "A": 76.0,  "f_u": 1960, "E": 160000, "kg_m": 0.60, "supplier": "Bridon", "finish": "galvanized"},
        "Dyform6 12mm 1960": {"d": 12.0, "A": 110.0, "f_u": 1960, "E": 160000, "kg_m": 0.87, "supplier": "Bridon", "finish": "galvanized"},
        "Dyform6 14mm 1960": {"d": 14.0, "A": 149.0, "f_u": 1960, "E": 160000, "kg_m": 1.18, "supplier": "Bridon", "finish": "galvanized"},
        "Dyform6 16mm 1960": {"d": 16.0, "A": 195.0, "f_u": 1960, "E": 160000, "kg_m": 1.55, "supplier": "Bridon", "finish": "galvanized"},
        "Dyform6 8mm 2160":  {"d": 8.0,  "A": 49.0,  "f_u": 2160, "E": 160000, "kg_m": 0.39, "supplier": "Bridon", "finish": "galvanized"},
        "Dyform6 10mm 2160": {"d": 10.0, "A": 76.0,  "f_u": 2160, "E": 160000, "kg_m": 0.60, "supplier": "Bridon", "finish": "galvanized"},
        "Dyform6 12mm 2160": {"d": 12.0, "A": 110.0, "f_u": 2160, "E": 160000, "kg_m": 0.87, "supplier": "Bridon", "finish": "galvanized"},
        "Dyform6 14mm 2160": {"d": 14.0, "A": 149.0, "f_u": 2160, "E": 160000, "kg_m": 1.18, "supplier": "Bridon", "finish": "galvanized"},
        "Dyform6 16mm 2160": {"d": 16.0, "A": 195.0, "f_u": 2160, "E": 160000, "kg_m": 1.55, "supplier": "Bridon", "finish": "galvanized"},
        "default": "Dyform6 16mm 1960",
    },

    # -------------------------------------------------------------------------
    # Redaelli FLX spiral strand.
    # 14-40 mm, breaking load 180-1450 kN.
    # -------------------------------------------------------------------------
    "Redaelli FLX": {
        "FLX 14": {"d": 14.0, "A": 115.0, "f_u": 1570, "E": 160000, "kg_m": 0.91, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 16": {"d": 16.0, "A": 150.0, "f_u": 1570, "E": 160000, "kg_m": 1.18, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 18": {"d": 18.0, "A": 190.0, "f_u": 1570, "E": 160000, "kg_m": 1.50, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 20": {"d": 20.0, "A": 235.0, "f_u": 1570, "E": 160000, "kg_m": 1.85, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 22": {"d": 22.0, "A": 285.0, "f_u": 1570, "E": 160000, "kg_m": 2.24, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 24": {"d": 24.0, "A": 340.0, "f_u": 1570, "E": 160000, "kg_m": 2.67, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 26": {"d": 26.0, "A": 400.0, "f_u": 1570, "E": 160000, "kg_m": 3.14, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 28": {"d": 28.0, "A": 465.0, "f_u": 1570, "E": 160000, "kg_m": 3.65, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 30": {"d": 30.0, "A": 535.0, "f_u": 1570, "E": 160000, "kg_m": 4.20, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 32": {"d": 32.0, "A": 610.0, "f_u": 1570, "E": 160000, "kg_m": 4.79, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 34": {"d": 34.0, "A": 690.0, "f_u": 1570, "E": 160000, "kg_m": 5.42, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 36": {"d": 36.0, "A": 775.0, "f_u": 1570, "E": 160000, "kg_m": 6.09, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 38": {"d": 38.0, "A": 865.0, "f_u": 1570, "E": 160000, "kg_m": 6.79, "supplier": "Redaelli", "finish": "galvanized"},
        "FLX 40": {"d": 40.0, "A": 920.0, "f_u": 1570, "E": 160000, "kg_m": 7.23, "supplier": "Redaelli", "finish": "galvanized"},
        "default": "FLX 24",
    },

    # -------------------------------------------------------------------------
    # Redaelli FLC - full locked coil.
    # 16-156 mm, breaking load 180-24,860 kN. The heavy-lift range.
    # -------------------------------------------------------------------------
    "Locked Coil": {
        "FLC 16":  {"d": 16.0,  "A": 148.0,   "f_u": 1570, "E": 160000, "kg_m": 1.17,  "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 20":  {"d": 20.0,  "A": 232.0,   "f_u": 1570, "E": 160000, "kg_m": 1.83,  "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 24":  {"d": 24.0,  "A": 335.0,   "f_u": 1570, "E": 160000, "kg_m": 2.64,  "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 28":  {"d": 28.0,  "A": 456.0,   "f_u": 1570, "E": 160000, "kg_m": 3.59,  "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 32":  {"d": 32.0,  "A": 596.0,   "f_u": 1570, "E": 160000, "kg_m": 4.69,  "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 36":  {"d": 36.0,  "A": 754.0,   "f_u": 1570, "E": 160000, "kg_m": 5.93,  "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 40":  {"d": 40.0,  "A": 980.0,   "f_u": 1570, "E": 160000, "kg_m": 7.70,  "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 44":  {"d": 44.0,  "A": 1190.0,  "f_u": 1570, "E": 160000, "kg_m": 9.35,  "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 48":  {"d": 48.0,  "A": 1410.0,  "f_u": 1570, "E": 160000, "kg_m": 11.10, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 52":  {"d": 52.0,  "A": 1660.0,  "f_u": 1570, "E": 160000, "kg_m": 13.00, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 56":  {"d": 56.0,  "A": 1920.0,  "f_u": 1570, "E": 160000, "kg_m": 15.10, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 60":  {"d": 60.0,  "A": 2200.0,  "f_u": 1570, "E": 160000, "kg_m": 17.30, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 70":  {"d": 70.0,  "A": 3000.0,  "f_u": 1570, "E": 160000, "kg_m": 23.60, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 80":  {"d": 80.0,  "A": 3920.0,  "f_u": 1570, "E": 160000, "kg_m": 30.80, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 90":  {"d": 90.0,  "A": 4960.0,  "f_u": 1570, "E": 160000, "kg_m": 39.00, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 100": {"d": 100.0, "A": 6130.0,  "f_u": 1570, "E": 160000, "kg_m": 48.20, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 120": {"d": 120.0, "A": 8830.0,  "f_u": 1570, "E": 160000, "kg_m": 69.40, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 152": {"d": 152.0, "A": 15040.0, "f_u": 1570, "E": 160000, "kg_m": 118.2, "supplier": "Redaelli", "finish": "galvanized"},
        "FLC 156": {"d": 156.0, "A": 15830.0, "f_u": 1570, "E": 160000, "kg_m": 124.4, "supplier": "Redaelli", "finish": "galvanized"},
        "default": "FLC 60",
    },

    # -------------------------------------------------------------------------
    # Spiral strand - open spiral, standard grade.
    # Small to medium, general-purpose.
    # -------------------------------------------------------------------------
    "Spiral": {
        "12mm": {"d": 12.0, "A": 85.0,  "f_u": 1570, "E": 160000, "kg_m": 0.67, "supplier": "generic", "finish": "galvanized"},
        "16mm": {"d": 16.0, "A": 150.0, "f_u": 1570, "E": 160000, "kg_m": 1.18, "supplier": "generic", "finish": "galvanized"},
        "20mm": {"d": 20.0, "A": 235.0, "f_u": 1570, "E": 160000, "kg_m": 1.85, "supplier": "generic", "finish": "galvanized"},
        "24mm": {"d": 24.0, "A": 340.0, "f_u": 1570, "E": 160000, "kg_m": 2.67, "supplier": "generic", "finish": "galvanized"},
        "28mm": {"d": 28.0, "A": 465.0, "f_u": 1570, "E": 160000, "kg_m": 3.65, "supplier": "generic", "finish": "galvanized"},
        "32mm": {"d": 32.0, "A": 610.0, "f_u": 1570, "E": 160000, "kg_m": 4.79, "supplier": "generic", "finish": "galvanized"},
        "default": "16mm",
    },
}

# =============================================================================
# JOINT MULTIPLIERS
# =============================================================================
# Multiply the design resistance by this factor depending on joint type.
# To EN 1993-1-8.

JOINT_MULTIPLIERS = {
    "welded": {"factor": 1.2, "description": "Rigid moment connections"},
    "bolted": {"factor": 1.0, "description": "Pin connections - economical"},
}

# =============================================================================
# END OF data/materials.py
# =============================================================================
