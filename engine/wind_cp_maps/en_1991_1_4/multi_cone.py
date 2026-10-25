"""SDSe — EN 1991-1-4 Multi-Cone Cp Map (Adaptation).

EN 1991-1-4 does not cover multi-cone roofs. Adaptation follows the
same approach as AS/NZS 1170.2: base dome Cp with a cone
concentration factor.
"""

from engine.wind_cp_maps.base import cone_concentration_factor
from engine.wind_cp_maps.en_1991_1_4.dome import compute_cp as dome_compute_cp


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None, cone_radius=None):
    base_cp = dome_compute_cp(slope_deg, h_over_d, position)
    
    if distance_from_apex is None or cone_radius is None:
        return base_cp
    
    k_cone = cone_concentration_factor(distance_from_apex, cone_radius)
    return base_cp * k_cone
