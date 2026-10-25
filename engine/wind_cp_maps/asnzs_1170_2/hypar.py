"""SDSe — AS/NZS 1170.2 Hypar (Saddle) Roof Cp Map (Adaptation).

AS/NZS 1170.2 does not cover hyperbolic paraboloid (saddle) roofs.
This module implements a first-principles adaptation based on:
  - High corners (windward) experience stagnation but the convex
    curvature of the saddle produces local suction peaks around
    the high corners and along the diagonal tension field.
  - Low corners (leeward) are in the wake region.
  
Reference: Engineering judgment for tensile saddle roofs, aligned
with the general approach of AS/NZS 1170.2 for non-standard shapes.
"""

from engine.wind_cp_maps.base import interpolate_cp


# Cp at the high corner (windward), low corner (leeward), and mid-edge
_CP_HIGH_CORNER = -1.2
_CP_LOW_CORNER = -0.5
_CP_MID_EDGE = -0.7


def compute_cp(slope_deg, h_over_d, position, distance_from_apex=None):
    """Hypar Cp.
    
    For a saddle, the surface normal flips direction relative to the
    wind, so we use the slope to interpolate between high and low corners.
    
    slope_deg: 0 = flat, 45 = steep. For a typical saddle, slopes
    vary from 0 (center) to ~30-45 (corners).
    """
    # Normalize slope contribution: steeper → closer to high corner
    if slope_deg <= 5:
        # Nearly flat
        return _CP_MID_EDGE
    elif slope_deg >= 30:
        # Steep corner
        return _CP_HIGH_CORNER
    else:
        # Interpolate
        t = (slope_deg - 5) / 25.0
        return _CP_MID_EDGE + t * (_CP_HIGH_CORNER - _CP_MID_EDGE)
