"""SDSe — AS/NZS 1170.2 Flat Roof Cp Map.

Section 5.3A of AS/NZS 1170.2.
For a flat roof with impermeable surface, Cp = -0.7 uniformly.
"""


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None):
    """AS/NZS 1170.2 flat roof Cp.
    
    Returns Cp = -0.7 (uniform suction).
    """
    return -0.7
