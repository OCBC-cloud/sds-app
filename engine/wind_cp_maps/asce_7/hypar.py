"""SDSe — ASCE 7 Hypar Cp Map (Adaptation)."""

_CP_HIGH_CORNER = -1.3
_CP_LOW_CORNER = -0.6
_CP_MID_EDGE = -0.8


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None):
    if slope_deg <= 5:
        return _CP_MID_EDGE
    elif slope_deg >= 30:
        return _CP_HIGH_CORNER
    else:
        t = (slope_deg - 5) / 25.0
        return _CP_MID_EDGE + t * (_CP_HIGH_CORNER - _CP_MID_EDGE)
