"""SDSe — EN 1991-1-4 Flat Roof Cp Map.

EN 1991-1-4, Section 7.2.3 and Table 7.2.
For a flat roof, Cp varies by zone (A, B, C, D, E, F, G, H).
For simplicity, use the field average Cp = -0.7.
Zone-based refinement is deferred to a future session.
"""


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None):
    return -0.7
