"""SDSe — EN 1991-1-4 Dome Cp Map.

EN 1991-1-4, Section 7.2.8 for domes.
Cp varies with rise/diameter (r/h) and position.
"""

from engine.wind_cp_maps.base import interpolate_cp


# EN 1991-1-4 dome Cp for r/h = 1 (hemisphere)
_CP_WINDWARD = [
    (0.0, -0.7),
    (0.1, -0.8),
    (0.2, -1.0),
    (0.3, -1.2),
    (0.4, -1.4),
    (0.5, -1.5),
]

_CP_LEEWARD = [
    (0.0, -0.5),
    (0.1, -0.6),
    (0.2, -0.7),
    (0.3, -0.8),
    (0.4, -0.9),
    (0.5, -1.0),
]

_CP_SIDE = [
    (0.0, -0.7),
    (0.1, -0.8),
    (0.2, -1.0),
    (0.3, -1.2),
    (0.4, -1.4),
    (0.5, -1.5),
]


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None):
    if position == "windward":
        return interpolate_cp(_CP_WINDWARD, h_over_d)
    elif position == "leeward":
        return interpolate_cp(_CP_LEEWARD, h_over_d)
    else:
        return interpolate_cp(_CP_SIDE, h_over_d)
