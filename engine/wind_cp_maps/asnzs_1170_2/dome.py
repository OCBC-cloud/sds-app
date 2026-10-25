"""SDSe — AS/NZS 1170.2 Dome (Curved Roof) Cp Map.

Section 5.3B of AS/NZS 1170.2.
For a domed roof, Cp varies with:
  - Rise/span ratio (h/d)
  - Position: windward, leeward, or side
  - Local surface slope

Reference: AS/NZS 1170.2:2021, Table 5.3(B).
"""

from engine.wind_cp_maps.base import interpolate_cp


# Cp tables: (h_over_d, Cp) for windward, leeward, side
_CP_WINDWARD = [
    (0.0, -0.7),
    (0.1, -0.9),
    (0.2, -1.1),
    (0.3, -1.3),
    (0.4, -1.5),
    (0.5, -1.7),
]

_CP_LEEWARD = [
    (0.0, -0.6),
    (0.1, -0.7),
    (0.2, -0.8),
    (0.3, -0.9),
    (0.4, -1.0),
    (0.5, -1.1),
]

_CP_SIDE = [
    (0.0, -0.7),
    (0.1, -0.9),
    (0.2, -1.1),
    (0.3, -1.3),
    (0.4, -1.5),
    (0.5, -1.7),
]


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None):
    """AS/NZS 1170.2 dome Cp.
    
    slope_deg: local surface slope (0=flat, 90=vertical)
    h_over_d: rise/span ratio
    position: "windward", "leeward", "side"
    """
    if position == "windward":
        return interpolate_cp(_CP_WINDWARD, h_over_d)
    elif position == "leeward":
        return interpolate_cp(_CP_LEEWARD, h_over_d)
    else:
        return interpolate_cp(_CP_SIDE, h_over_d)
