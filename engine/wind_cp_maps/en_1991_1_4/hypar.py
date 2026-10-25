"""SDSe — EN 1991-1-4 Hypar Cp Map (Adaptation)."""

_CP_HIGH_CORNER = -1.1
_CP_LOW_CORNER = -0.5
_CP_MID_EDGE = -0.7


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None):
    if slope_deg <= 5:
        return _CP_MID_EDGE
    elif slope_deg >= 30:
        return _CP_HIGH_CORNER
    else:
        t = (slope_deg - 5) / 25.0
        return _CP_MID_EDGE + t * (_CP_HIGH_CORNER - _CP_MID_EDGE)
