"""SDSe — ASCE 7 Flat Roof Cp Map.

ASCE 7-22, Figure 27.3-2.
"""


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None):
    # Field average for a flat roof, h ≤ 18m: Cp = -0.9
    return -0.9
