# =============================================================================
# SDSe - Engineering Constants
# =============================================================================
# Wind speeds and partial safety factors used throughout the app.
#
# Contents:
#   WIND_SPEEDS      - basic wind speed per country code (m/s)
#   PARTIAL_FACTORS  - Eurocode partial safety factors
#
# Usage:
#   from data.constants import WIND_SPEEDS, PARTIAL_FACTORS
# =============================================================================

# =============================================================================
# BASIC WIND SPEEDS PER COUNTRY
# =============================================================================
# EU  = European Union (EN 1991-1-4 default)
# CN  = China (GB 50009)
# UK  = United Kingdom (BS EN 1991-1-4 NA)
# MY  = Malaysia (MS 1553) - default
# US  = United States (ASCE 7)

WIND_SPEEDS = {
    "EU": 30.0,
    "CN": 28.0,
    "UK": 26.0,
    "MY": 33.5,
    "US": 38.0,
}

# =============================================================================
# PARTIAL SAFETY FACTORS (EN 1990 / EN 1993)
# =============================================================================
# gamma_G       - permanent action factor (unfavourable)
# gamma_Q_wind  - variable action factor (wind, unfavourable)
# gamma_M0      - cross-section resistance
# gamma_M1      - member buckling resistance
# gamma_M2      - net section / connections (MY national annex)

PARTIAL_FACTORS = {
    "gamma_G":      1.35,
    "gamma_Q_wind": 1.50,
    "gamma_M0":     1.00,
    "gamma_M1":     1.00,
    "gamma_M2":     1.20,
}
