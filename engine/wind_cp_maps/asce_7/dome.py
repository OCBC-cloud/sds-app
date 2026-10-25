"""SDSe — ASCE 7 Dome Cp Map.

ASCE 7-22, Figure 27.3-2 (Dome Roofs).
Cp varies with rise/span ratio and position.
"""

from engine.wind_cp_maps.base import interpolate_cp


_CP_WINDWARD = [
    (0.0, -0.9),
    (0.1, -1.0),
    (0.2, -1.1),
    (0.3, -1.2),
    (0.4, -1.3),
    (0.5, -1.4),
]

_CP_LEEWARD = [
    (0.0, -0.7),
    (0.1, -0.8),
    (0.2, -0.9),
    (0.3, -1.0),
    (0.4, -1.1),
    (0.5, -1.2),
]

_CP_SIDE = [
    (0.0, -0.9),
    (0.1, -1.0),
    (0.2, -1.1),
    (0.3, -1.2),
    (0.4, -1.3),
    (0.5, -1.4),
]


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None):
    if position == "windward":
        return interpolate_cp(_CP_WINDWARD, h_over_d)
    elif position == "leeward":
        return interpolate_cp(_CP_LEEWARD, h_over_d)
    else:
        return interpolate_cp(_CP_SIDE, h_over_d)
