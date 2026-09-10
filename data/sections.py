# =============================================================================
# SDSe - Section Properties Catalogue
# =============================================================================
# All structural sections available in the SDSe catalogue.
#
# Units:
#   A      = cross-sectional area (mm^2)
#   I      = second moment of area (mm^4)
#   W_el   = elastic section modulus (mm^3)
#   i      = radius of gyration (mm)
#   weight = mass per unit length (kg/m)
#   type   = section family (CHS, SHS, RHS, I-Beam, Angle, Channel)
#   depth  = nominal section depth (mm)
#
# Usage:
#   from data.sections import SECTION_PROPERTIES
#   sec = SECTION_PROPERTIES["CHS 114.3x5.0"]
# =============================================================================

SECTION_PROPERTIES = {
    # ===== CHS Sections =====
    "CHS 21.3x2.3": {"A": 137, "I": 0.006e6, "W_el": 0.6e3, "i": 6.7, "weight": 1.1, "type": "CHS", "depth": 21.3},
    "CHS 26.9x2.6": {"A": 198, "I": 0.015e6, "W_el": 1.1e3, "i": 8.7, "weight": 1.6, "type": "CHS", "depth": 26.9},
    "CHS 33.7x3.2": {"A": 307, "I": 0.035e6, "W_el": 2.1e3, "i": 10.7, "weight": 2.4, "type": "CHS", "depth": 33.7},
    "CHS 42.4x3.2": {"A": 394, "I": 0.075e6, "W_el": 3.5e3, "i": 13.8, "weight": 3.1, "type": "CHS", "depth": 42.4},
    "CHS 48.3x3.2": {"A": 453, "I": 0.12e6, "W_el": 5.0e3, "i": 16.3, "weight": 3.6, "type": "CHS", "depth": 48.3},
    "CHS 60.3x3.2": {"A": 574, "I": 0.24e6, "W_el": 8.0e3, "i": 20.5, "weight": 4.5, "type": "CHS", "depth": 60.3},
    "CHS 76.1x3.6": {"A": 820, "I": 0.54e6, "W_el": 14.2e3, "i": 25.7, "weight": 6.4, "type": "CHS", "depth": 76.1},
    "CHS 88.9x4.0": {"A": 1067, "I": 0.93e6, "W_el": 20.9e3, "i": 29.5, "weight": 8.4, "type": "CHS", "depth": 88.9},
    "CHS 101.6x4.0": {"A": 1226, "I": 1.42e6, "W_el": 28.0e3, "i": 34.0, "weight": 9.6, "type": "CHS", "depth": 101.6},
    "CHS 114.3x5.0": {"A": 1717, "I": 2.53e6, "W_el": 44.2e3, "i": 38.4, "weight": 13.5, "type": "CHS", "depth": 114.3},
    "CHS 139.7x6.3": {"A": 2642, "I": 5.90e6, "W_el": 84.5e3, "i": 47.3, "weight": 20.7, "type": "CHS", "depth": 139.7},
    "CHS 168.3x7.1": {"A": 3600, "I": 11.5e6, "W_el": 137e3, "i": 56.5, "weight": 28.3, "type": "CHS", "depth": 168.3},
    "CHS 219.1x8.0": {"A": 5305, "I": 29.0e6, "W_el": 265e3, "i": 73.9, "weight": 41.6, "type": "CHS", "depth": 219.1},
    "CHS 273.0x10.0": {"A": 8263, "I": 69.0e6, "W_el": 506e3, "i": 91.4, "weight": 64.9, "type": "CHS", "depth": 273.0},
    "CHS 323.9x12.5": {"A": 12228, "I": 148e6, "W_el": 912e3, "i": 110.0, "weight": 96.0, "type": "CHS", "depth": 323.9},
    "CHS 406.4x12.5": {"A": 15470, "I": 210e6, "W_el": 1030e3, "i": 116.6, "weight": 121.4, "type": "CHS", "depth": 406.4},
    "CHS 457.0x14.0": {"A": 19480, "I": 318e6, "W_el": 1390e3, "i": 127.8, "weight": 153.0, "type": "CHS", "depth": 457.0},
    "CHS 508.0x16.0": {"A": 24730, "I": 520e6, "W_el": 2050e3, "i": 145.0, "weight": 194.0, "type": "CHS", "depth": 508.0},
    "CHS 610.0x18.0": {"A": 33480, "I": 1430e6, "W_el": 4690e3, "i": 206.7, "weight": 262.8, "type": "CHS", "depth": 610.0},
    "CHS 711.0x20.0": {"A": 43420, "I": 2560e6, "W_el": 7200e3, "i": 242.9, "weight": 340.8, "type": "CHS", "depth": 711.0},
    "CHS 813.0x22.0": {"A": 54670, "I": 4300e6, "W_el": 10580e3, "i": 280.4, "weight": 429.0, "type": "CHS", "depth": 813.0},
    "CHS 914.0x25.0": {"A": 69820, "I": 6980e6, "W_el": 15280e3, "i": 316.1, "weight": 547.8, "type": "CHS", "depth": 914.0},
    "CHS 1016.0x28.0": {"A": 86920, "I": 10700e6, "W_el": 21060e3, "i": 350.8, "weight": 682.8, "type": "CHS", "depth": 1016.0},

    # ===== SHS Sections =====
    "SHS 50x50x3": {"A": 564, "I": 0.21e6, "W_el": 8.4e3, "i": 19.3, "weight": 4.4, "type": "SHS", "depth": 50},
    "SHS 50x50x4": {"A": 736, "I": 0.26e6, "W_el": 10.4e3, "i": 18.8, "weight": 5.8, "type": "SHS", "depth": 50},
    "SHS 75x75x3": {"A": 864, "I": 0.77e6, "W_el": 20.5e3, "i": 29.8, "weight": 6.8, "type": "SHS", "depth": 75},
    "SHS 75x75x4": {"A": 1136, "I": 0.97e6, "W_el": 25.9e3, "i": 29.2, "weight": 8.9, "type": "SHS", "depth": 75},
    "SHS 100x100x5": {"A": 1900, "I": 2.8e6, "W_el": 56.0e3, "i": 38.4, "weight": 14.9, "type": "SHS", "depth": 100},
    "SHS 100x100x6": {"A": 2256, "I": 3.2e6, "W_el": 64.0e3, "i": 37.7, "weight": 17.7, "type": "SHS", "depth": 100},
    "SHS 120x120x5": {"A": 2300, "I": 5.0e6, "W_el": 83.0e3, "i": 46.6, "weight": 18.1, "type": "SHS", "depth": 120},
    "SHS 150x150x6": {"A": 3456, "I": 11.9e6, "W_el": 159e3, "i": 58.7, "weight": 27.1, "type": "SHS", "depth": 150},
    "SHS 200x200x8": {"A": 6144, "I": 36.0e6, "W_el": 360e3, "i": 76.5, "weight": 48.2, "type": "SHS", "depth": 200},
    "SHS 250x250x10": {"A": 9600, "I": 88.0e6, "W_el": 704e3, "i": 95.7, "weight": 75.4, "type": "SHS", "depth": 250},
    "SHS 300x300x12": {"A": 13824, "I": 182e6, "W_el": 1213e3, "i": 114.8, "weight": 108.5, "type": "SHS", "depth": 300},

    # ===== RHS Sections =====
    "RHS 100x50x4": {"A": 1136, "I": 1.4e6, "W_el": 28.0e3, "i": 35.1, "weight": 8.9, "type": "RHS", "depth": 100},
    "RHS 100x50x5": {"A": 1400, "I": 1.7e6, "W_el": 34.0e3, "i": 34.8, "weight": 11.0, "type": "RHS", "depth": 100},
    "RHS 120x60x5": {"A": 1700, "I": 3.1e6, "W_el": 52.0e3, "i": 42.7, "weight": 13.3, "type": "RHS", "depth": 120},
    "RHS 150x100x5": {"A": 2450, "I": 6.8e6, "W_el": 91.0e3, "i": 52.7, "weight": 19.2, "type": "RHS", "depth": 150},
    "RHS 150x100x6": {"A": 2784, "I": 8.3e6, "W_el": 111e3, "i": 54.6, "weight": 21.8, "type": "RHS", "depth": 150},
    "RHS 200x100x6": {"A": 3504, "I": 16.4e6, "W_el": 164e3, "i": 68.4, "weight": 27.5, "type": "RHS", "depth": 200},
    "RHS 200x100x8": {"A": 4608, "I": 21.2e6, "W_el": 212e3, "i": 67.8, "weight": 36.2, "type": "RHS", "depth": 200},
    "RHS 200x150x8": {"A": 5104, "I": 30.1e6, "W_el": 301e3, "i": 76.8, "weight": 40.0, "type": "RHS", "depth": 200},
    "RHS 250x150x10": {"A": 7500, "I": 71.0e6, "W_el": 568e3, "i": 97.3, "weight": 58.9, "type": "RHS", "depth": 250},
    "RHS 300x200x12": {"A": 11424, "I": 156e6, "W_el": 1040e3, "i": 116.8, "weight": 89.7, "type": "RHS", "depth": 300},

    # ===== I-Beam Sections =====
    "I-100": {"A": 1030, "I": 4.5e6, "W_el": 90e3, "i": 66.1, "weight": 8.1, "type": "I-Beam", "depth": 100},
    "I-120": {"A": 1440, "I": 8.0e6, "W_el": 133e3, "i": 74.5, "weight": 11.3, "type": "I-Beam", "depth": 120},
    "I-140": {"A": 1700, "I": 12.0e6, "W_el": 171e3, "i": 84.0, "weight": 13.3, "type": "I-Beam", "depth": 140},
    "I-150": {"A": 2130, "I": 16.0e6, "W_el": 213e3, "i": 86.7, "weight": 16.7, "type": "I-Beam", "depth": 150},
    "I-160": {"A": 2410, "I": 20.0e6, "W_el": 250e3, "i": 91.1, "weight": 18.9, "type": "I-Beam", "depth": 160},
    "I-180": {"A": 2790, "I": 28.0e6, "W_el": 311e3, "i": 100.2, "weight": 21.9, "type": "I-Beam", "depth": 180},
    "I-200": {"A": 3310, "I": 38.0e6, "W_el": 380e3, "i": 107.1, "weight": 26.0, "type": "I-Beam", "depth": 200},
    "I-220": {"A": 3930, "I": 52.0e6, "W_el": 473e3, "i": 115.0, "weight": 30.8, "type": "I-Beam", "depth": 220},
    "I-250": {"A": 4820, "I": 76.0e6, "W_el": 608e3, "i": 125.6, "weight": 37.8, "type": "I-Beam", "depth": 250},
    "I-280": {"A": 5530, "I": 101.0e6, "W_el": 721e3, "i": 135.2, "weight": 43.4, "type": "I-Beam", "depth": 280},
    "I-300": {"A": 6720, "I": 136.0e6, "W_el": 907e3, "i": 142.3, "weight": 52.8, "type": "I-Beam", "depth": 300},
    "I-320": {"A": 7460, "I": 168.0e6, "W_el": 1050e3, "i": 150.1, "weight": 58.6, "type": "I-Beam", "depth": 320},
    "I-350": {"A": 9020, "I": 226.0e6, "W_el": 1290e3, "i": 158.3, "weight": 70.8, "type": "I-Beam", "depth": 350},
    "I-400": {"A": 11800, "I": 348.0e6, "W_el": 1740e3, "i": 171.8, "weight": 92.6, "type": "I-Beam", "depth": 400},
    "I-450": {"A": 14300, "I": 498.0e6, "W_el": 2210e3, "i": 186.7, "weight": 112.2, "type": "I-Beam", "depth": 450},
    "I-500": {"A": 17500, "I": 694.0e6, "W_el": 2780e3, "i": 199.2, "weight": 137.4, "type": "I-Beam", "depth": 500},

    # ===== Angle Sections =====
    "L40x40x4": {"A": 309, "I": 0.08e6, "W_el": 2.8e3, "i": 16.1, "weight": 2.4, "type": "Angle", "depth": 40},
    "L50x50x5": {"A": 480, "I": 0.18e6, "W_el": 5.1e3, "i": 19.4, "weight": 3.8, "type": "Angle", "depth": 50},
    "L60x60x6": {"A": 691, "I": 0.36e6, "W_el": 8.5e3, "i": 22.8, "weight": 5.4, "type": "Angle", "depth": 60},
    "L70x70x7": {"A": 941, "I": 0.64e6, "W_el": 12.8e3, "i": 26.1, "weight": 7.4, "type": "Angle", "depth": 70},
    "L80x80x8": {"A": 1229, "I": 1.04e6, "W_el": 18.2e3, "i": 29.1, "weight": 9.6, "type": "Angle", "depth": 80},
    "L90x90x9": {"A": 1553, "I": 1.58e6, "W_el": 24.7e3, "i": 31.9, "weight": 12.2, "type": "Angle", "depth": 90},
    "L100x100x10": {"A": 1910, "I": 2.28e6, "W_el": 32.0e3, "i": 34.5, "weight": 15.0, "type": "Angle", "depth": 100},
    "L120x120x12": {"A": 2752, "I": 4.52e6, "W_el": 53.0e3, "i": 40.5, "weight": 21.6, "type": "Angle", "depth": 120},

    # ===== Channel Sections =====
    "C100x50x6": {"A": 1010, "I": 2.8e6, "W_el": 56e3, "i": 52.6, "weight": 7.9, "type": "Channel", "depth": 100},
    "C120x60x7": {"A": 1380, "I": 5.2e6, "W_el": 87e3, "i": 61.4, "weight": 10.8, "type": "Channel", "depth": 120},
    "C150x75x8": {"A": 1910, "I": 10.2e6, "W_el": 136e3, "i": 73.1, "weight": 15.0, "type": "Channel", "depth": 150},
    "C180x80x9": {"A": 2330, "I": 16.0e6, "W_el": 178e3, "i": 82.9, "weight": 18.3, "type": "Channel", "depth": 180},
    "C200x90x10": {"A": 2890, "I": 24.0e6, "W_el": 240e3, "i": 91.1, "weight": 22.7, "type": "Channel", "depth": 200},
    "C250x100x12": {"A": 3930, "I": 48.0e6, "W_el": 384e3, "i": 110.5, "weight": 30.8, "type": "Channel", "depth": 250},
}
