"""SDSe — AS/NZS 1170.2 Multi-Cone Roof Cp Map (Adaptation).

AS/NZS 1170.2 does not explicitly cover multi-cone roofs.
This module adapts the dome Cp (Section 5.3B) with a cone concentration
factor that amplifies the local suction at each cone apex.

Engineering basis:
  - Wind accelerates over each cone's crest.
  - Peak suction at the crest is amplified by up to 30% relative to
    an equivalent smooth dome.
  - Decay to base dome Cp at ~1.5 × cone radius away from apex.

The k_cone factor is documented in
engine/wind_cp_maps/base.py:cone_concentration_factor().
"""

import math

from engine.wind_cp_maps.base import cone_concentration_factor
from engine.wind_cp_maps.asnzs_1170_2.dome import compute_cp as dome_compute_cp


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None, cone_radius=None):
    """AS/NZS 1170.2 multi-cone Cp (adapted from dome + cone factor).
    
    slope_deg: local surface slope
    h_over_d: rise/span ratio
    position: "windward", "leeward", or "side"
    distance_from_apex: distance in meters from the nearest cone apex
    cone_radius: characteristic cone radius (from ring_diameter / 2)
    """
    base_cp = dome_compute_cp(slope_deg, h_over_d, position)
    
    if distance_from_apex is None or cone_radius is None:
        return base_cp
    
    k_cone = cone_concentration_factor(distance_from_apex, cone_radius)
    return base_cp * k_cone
