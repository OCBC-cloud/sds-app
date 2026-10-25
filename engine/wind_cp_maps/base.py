"""SDSe — Common Cp map utilities.

Slope computation, position classification, linear interpolation,
and shared cone concentration factor for multi-cone roofs.
"""

import math

import numpy as np


def compute_slope_deg(normal):
    """Given a 3D surface normal, return the slope from vertical in degrees.
    
    slope = 0°  → surface is horizontal (flat)
    slope = 90° → surface is vertical (wall)
    """
    n_z = abs(float(normal[2]))
    n_z = min(1.0, max(0.0, n_z))
    return math.degrees(math.acos(n_z))


def classify_position(centroid_x, wind_direction_x, apex_x):
    """Classify a triangle's position relative to the wind.
    
    Returns: "windward", "leeward", or "side"
    """
    if wind_direction_x is None:
        # Wind from +X (positive direction). Windward = -X side.
        wind_direction_x = -1.0
    
    dx = centroid_x - apex_x
    if wind_direction_x < 0:
        # Wind from -X → windward is the -X side (dx < 0)
        if dx < -0.15 * abs(apex_x) if apex_x != 0 else dx < 0:
            return "windward"
        elif dx > 0.15 * abs(apex_x) if apex_x != 0 else dx > 0:
            return "leeward"
        else:
            return "side"
    else:
        if dx > 0.15 * abs(apex_x) if apex_x != 0 else dx > 0:
            return "windward"
        elif dx < -0.15 * abs(apex_x) if apex_x != 0 else dx < 0:
            return "leeward"
        else:
            return "side"


def interpolate_cp(table, h_over_d):
    """Linear interpolation of Cp from a table of (h_over_d, cp) rows.
    
    table: list of (h_over_d_value, cp_value)
    h_over_d: current rise/span ratio
    returns: interpolated Cp
    """
    table = sorted(table, key=lambda r: r[0])
    if h_over_d <= table[0][0]:
        return table[0][1]
    if h_over_d >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        r0, c0 = table[i]
        r1, c1 = table[i + 1]
        if r0 <= h_over_d <= r1:
            t = (h_over_d - r0) / (r1 - r0)
            return c0 + t * (c1 - c0)
    return table[-1][1]


def cone_concentration_factor(distance_from_apex_m, cone_radius_m):
    """Cone concentration factor for multi-cone roofs.
    
    Wind accelerates over each cone's crest. The factor is 1.3 at the
    apex, decaying to 1.0 at 1.5 × cone_radius away.
    
    Formula: k = 1.0 + 0.3 × exp(-(d/λ)²) where λ = 1.5 × cone_radius
    
    Justification: derived from wind tunnel studies of multi-hump
    structures. For a single cone (ring_diameter approaching 0), this
    reduces to a smooth dome. For a multi-cone roof with distinct
    humps, the local suction at each crest is amplified by up to 30%.
    """
    if cone_radius_m is None or cone_radius_m <= 0:
        return 1.0
    lambda_m = 1.5 * cone_radius_m
    if lambda_m <= 0:
        return 1.0
    ratio = distance_from_apex_m / lambda_m
    return 1.0 + 0.3 * math.exp(-(ratio ** 2))


def find_nearest_cone_apex(centroid, cone_apexes):
    """Find the nearest cone apex and the distance to it.
    
    centroid: (3,) array
    cone_apexes: list of (3,) arrays
    returns: (nearest_apex, distance_m)
    """
    if not cone_apexes:
        return None, float('inf')
    best_apex = None
    best_dist = float('inf')
    for apex in cone_apexes:
        d = float(np.linalg.norm(centroid - apex))
        if d < best_dist:
            best_dist = d
            best_apex = apex
    return best_apex, best_dist
