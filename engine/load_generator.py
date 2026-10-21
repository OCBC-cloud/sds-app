 # =============================================================================
# SDSe Engine - Load Generator (Wind, Snow, Payload)
# =============================================================================
# Calculates nodal loads from distributed pressures (wind, snow, dead).
# =============================================================================

import numpy as np
import math

try:
    from data.constants import WIND_SPEEDS
except ImportError:
    WIND_SPEEDS = {}

def generate_loads(points, triangles, wind_speed_ms, snow_depth_m, payload_kg_m2):
    """
    Returns an (N, 3) numpy array of nodal forces in Newtons.
    Downward loads are negative Z.
    """
    n_nodes = points.shape[0]
    loads = np.zeros((n_nodes, 3), dtype=float)

    # 1. Calculate pressures (Pa = N/m^2)
    
    # Wind Pressure (q = 0.613 * V^2)
    # We apply it as an UPLIFT (negative Z) on the windward side.
    # For a simplified approach, we apply it uniformly upward as suction.
    q_wind = 0.613 * (wind_speed_ms ** 2)
    
    # Snow Pressure (Density ~ 150 kg/m3 for fresh snow, 300 for settled)
    # We use a standard density of 200 kg/m3, g = 9.81
    q_snow = snow_depth_m * 200.0 * 9.81

    # Payload Pressure (kg/m2 to N/m2)
    q_payload = payload_kg_m2 * 9.81

    # Total downward pressure (Snow + Payload)
    q_down = q_snow + q_payload

    # 2. Distribute loads to nodes
    for tri in triangles:
        i, j, k = tri
        
        # Get vertices
        p0 = points[i]
        p1 = points[j]
        p2 = points[k]
        
        # Calculate area and normal
        e1 = p1 - p0
        e2 = p2 - p0
        cross = np.cross(e1, e2)
        area = 0.5 * np.linalg.norm(cross)
        
        if area < 1e-9:
            continue
            
        normal = cross / (2.0 * area)
        
        # Wind suction acts normal to the surface
        # We take the Z-component of the normal to scale the wind suction
        wind_factor = abs(normal[2])
        f_wind_mag = q_wind * area * wind_factor
        
        # Snow/Payload acts straight down (global Z)
        f_down_mag = q_down * area
        
        # Assemble force vector for this triangle
        f_vec = np.array([0.0, 0.0, f_down_mag - f_wind_mag])
        
        # Distribute to 3 nodes (1/3 each)
        loads[i] += f_vec / 3.0
        loads[j] += f_vec / 3.0
        loads[k] += f_vec / 3.0

    return loads
