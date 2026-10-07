# =============================================================================
# SDSe - Engineering Constants (PROVISIONAL)
# =============================================================================
# Wind speeds, partial safety factors, and terrain categories used
# throughout the app.
#
# *** THIS FILE IS A PROVISIONAL PLACEHOLDER. ***
#
# It provides reference values for the workshop defaults and for the
# report's Design Basis section. It is NOT the code implementation.
#
# The real code-based tables are planned for data/codes.py, which will
# hold, per country and per code:
#   - basic wind speed by location and return period
#   - terrain category and exposure factors
#   - directional and seasonal factors
#   - altitude correction
#   - snow ground load by location
#   - partial factors per load case and per combination
#   - load combination rules (ULS, SLS, accidental)
#
# Until data/codes.py is built, this file provides:
#   WIND_SPEEDS       - basic reference wind speed per country (m/s)
#   PARTIAL_FACTORS   - Eurocode partial safety factors
#   TERRAIN_CATEGORIES- Eurocode and ASCE terrain exposure categories
#
# The App does not yet perform a design wind check. It solves
# prestress only. Wind and snow load cases arrive with data/codes.py.
#
# Contents:
#   WIND_SPEEDS        - basic reference wind speed per country (m/s)
#   PARTIAL_FACTORS    - Eurocode partial safety factors
#   TERRAIN_CATEGORIES - Eurocode and ASCE terrain exposure categories
#
# Usage:
#   from data.constants import WIND_SPEEDS, PARTIAL_FACTORS
# =============================================================================

# =============================================================================
# BASIC REFERENCE WIND SPEEDS PER COUNTRY
# =============================================================================
# One value per country. This is the basic reference wind speed at
# 10 m above open ground, 50-year return period, gust.
#
# This is NOT a design wind speed. Real design wind loading depends on
# terrain, height, direction, return period, altitude, and topography,
# all of which will be handled by data/codes.py.
#
# The values below are reference values from the national codes, at
# the coastal or most onerous default zone. Where the code specifies
# multiple zones, the value is the maximum for that country.
#
# Source standards:
#   MY - MS 1553:2015 (Peninsular Malaysia coastal default)
#   SG - SS EN 1991-1-4 Singapore National Annex
#   ID - SNI 1727:2020
#   TH - Thai Building Control Act, DPT Standard 1311-50
#   VN - TCVN 2737:2023
#   CN - GB 50009-2012
#   EU - EN 1991-1-4 (no National Annex, base value)
#   UK - BS EN 1991-1-4 UK National Annex
#   US - ASCE 7-22 (basic wind speed, Risk Category II, 3-second gust)
#   AU - AS/NZS 1170.2:2021 (Region A, coastal)
#
# Country codes:
#   MY = Malaysia
#   SG = Singapore
#   ID = Indonesia
#   TH = Thailand
#   VN = Vietnam
#   CN = China
#   EU = European Union (base, no NA)
#   UK = United Kingdom (with NA)
#   US = United States
#   AU = Australia

WIND_SPEEDS = {
    "MY": {"v_b_m_s": 33.5, "standard": "MS 1553:2015"},
    "SG": {"v_b_m_s": 30.0, "standard": "SS EN 1991-1-4 NA"},
    "ID": {"v_b_m_s": 40.0, "standard": "SNI 1727:2020"},
    "TH": {"v_b_m_s": 28.0, "standard": "DPT Standard 1311-50"},
    "VN": {"v_b_m_s": 38.0, "standard": "TCVN 2737:2023"},
    "CN": {"v_b_m_s": 28.0, "standard": "GB 50009-2012"},
    "EU": {"v_b_m_s": 30.0, "standard": "EN 1991-1-4 (base)"},
    "UK": {"v_b_m_s": 26.0, "standard": "BS EN 1991-1-4 NA"},
    "US": {"v_b_m_s": 38.0, "standard": "ASCE 7-22"},
    "AU": {"v_b_m_s": 40.0, "standard": "AS/NZS 1170.2:2021"},
}

# =============================================================================
# PARTIAL SAFETY FACTORS
# =============================================================================
# Eurocode set, to EN 1990:2002 and EN 1993-1-1.
#
# This single set is used by default. Per-code tables will live in
# data/codes.py. This block is retained for the report's Design Basis
# section, so the report can name the source of the factors.
#
#   gamma_G       - permanent action factor (unfavourable)
#   gamma_Q_wind  - variable action factor, wind (unfavourable)
#   gamma_Q_snow  - variable action factor, snow (unfavourable)
#   gamma_M0      - cross-section resistance
#   gamma_M1      - member buckling resistance
#   gamma_M2      - net section and connections

PARTIAL_FACTORS = {
    "code":           "EN 1990:2002 / EN 1993-1-1",
    "gamma_G":        1.35,
    "gamma_Q_wind":   1.50,
    "gamma_Q_snow":   1.50,
    "gamma_M0":       1.00,
    "gamma_M1":       1.00,
    "gamma_M2":       1.25,
}

# =============================================================================
# TERRAIN CATEGORIES
# =============================================================================
# Eurocode and ASCE terrain exposure categories, kept side by side so
# that the report can name the terrain and so that data/codes.py has a
# place to write the exposure factors per code.
#
# Eurocode (EN 1991-1-4, § 4.3):
#   0 - Sea, lake, flat, unobstructed coastal areas
#   I - Lake or flat plain with negligible vegetation
#   II - Country with low vegetation, hedges, scattered obstacles
#   III - Suburban, forest, or industrial areas
#   IV - Urban areas with tall buildings, city centres
#
# ASCE 7 (§ 26.7):
#   B - Urban and suburban, wooded areas
#   C - Open terrain with scattered obstructions
#   D - Flat, unobstructed areas and water surfaces

TERRAIN_CATEGORIES = {
    "eurocode": {
        "0": {
            "description": "Sea, lake, flat, unobstructed coastal areas",
        },
        "I": {
            "description": "Lake or flat plain with negligible vegetation",
        },
        "II": {
            "description": "Country with low vegetation, hedges, scattered obstacles",
        },
        "III": {
            "description": "Suburban, forest, or industrial areas",
        },
        "IV": {
            "description": "Urban areas with tall buildings, city centres",
        },
    },
    "asce": {
        "B": {
            "description": "Urban and suburban, wooded areas",
        },
        "C": {
            "description": "Open terrain with scattered obstructions",
        },
        "D": {
            "description": "Flat, unobstructed areas and water surfaces",
        },
    },
}

# =============================================================================
# PROVISIONAL STATUS
# =============================================================================
# The three dicts above are provisional. Before the App performs a real
# design wind check, data/codes.py must be built, and it must provide:
#
#   1. Basic wind speed lookup by location (city, postcode, or coordinate)
#      for each supported code.
#   2. Terrain category to exposure factor conversion, with height variation.
#   3. Directional and seasonal factors.
#   4. Altitude correction where the code specifies it.
#   5. Return period factors for service lives other than 50 years.
#   6. Snow ground load lookup by location.
#   7. Partial factors per load case and per combination.
#   8. Load combination rules: ULS (wind dominant, snow dominant), SLS,
#      and accidental, per code.
#
# When data/codes.py is built, this file's WIND_SPEEDS and PARTIAL_FACTORS
# become the "default code" fallback, and per-code tables are added.
#
# Until then, the App does not perform a design wind check.
# The wind speeds in this file are used only as reference values in
# the workshop and in the report's Design Basis section.
# =============================================================================

# =============================================================================
# END OF data/constants.py
# =============================================================================
