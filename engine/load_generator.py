"""SDSe Engine - Environmental Load Generator.

Converts user inputs (wind speed, snow depth) into nodal forces.
Includes code-specific parameters for Malaysia, China, British, Euro, 
Japan, Korea, and Australia.
"""

import math
import numpy as np

# Air density at sea level, 15°C (kg/m^3)
RHO_AIR = 1.225

# =============================================================================
# CODE PARAMETERS
# =============================================================================
# Note: For complex geometries, Cp varies across the roof. We use a 
# conservative uniform uplift coefficient for tensile roofs in each code.
# Snow density varies by code, but 100 kg/m3 is standard for fresh snow.

CODE_PARAMS = {
    "Malaysia (MS 1553)": {
        "wind_cp": -0.8,       # Net uplift coefficient
        "snow_density": 100.0, # Rare in Malaysia, but standard for highlands
    },
    "Eurocode (EN 1991)": {
        "wind_cp": -0.7,
        "snow_density": 100.0,
    },
    "British (BS 6399)": {
        "wind_cp": -0.8,
        "snow_density": 100.0,
    },
    "Australia (AS 1170)": {
        "wind_cp": -0.7,
        "snow_density": 100.0,
    },
    "Japan (AIJ)": {
        "wind_cp": -0.9,
        "snow_density": 150.0, # Heavier wet snow
    },
    "Korea (KBC)": {
        "wind_cp": -0.8,
        "snow_density": 100.0,
    },
    "China (GB 50009)": {
        "wind_cp": -0.8,
        "snow_density": 150.0,
    },
}


def get_code_params(code_name):
    """Return the parameters for a specific code, or default to Malaysia."""
    return CODE_PARAMS.get(code_name, CODE_PARAMS["Malaysia (MS 1553)"])


# =============================================================================
# WIND LOAD
# =============================================================================

def generate_wind_load(coords_fdm, tris, wind_speed_ms, code_name="Malaysia (MS 1553)"):
    """
    Generate wind uplift pressure from wind speed (m/s).
    Uses Bernoulli: q = 0.5 * rho * v^2
    Applies the code-specific suction coefficient (Cp).
    Returns a nodal force vector (N).
    """
    params = get_code_params(code_name)
    cp_suction = params["wind_cp"]
    
    # q in Pa (N/m^2)
    q = 0.5 * RHO_AIR * (wind_speed_ms ** 2)
    pressure_Pa = q * cp_suction
    
    loads = np.zeros((coords_fdm.shape[0], 3), dtype=float)
    
    for (a, b, c) in tris:
        pa, pb, pc = coords_fdm[a], coords_fdm[b], coords_fdm[c]
        area = 0.5 * float(np.linalg.norm(np.cross(pb - pa, pc - pa)))
        
        # Force per node = pressure * area / 3
        force_z = (pressure_Pa * area) / 3.0
        
        loads[a, 2] += force_z
        loads[b, 2] += force_z
        loads[c, 2] += force_z
        
    return loads


# =============================================================================
# SNOW LOAD
# =============================================================================

def generate_snow_load(coords_fdm, tris, snow_depth_m, code_name="Malaysia (MS 1553)"):
    """
    Generate snow load from depth (m).
    Uses the code-specific snow density.
    Returns a downward nodal force vector (N).
    """
    params = get_code_params(code_name)
    density = params["snow_density"]
    g = 9.81
    
    # Snow pressure in Pa (N/m^2)
    pressure_Pa = snow_depth_m * density * g
    
    loads = np.zeros((coords_fdm.shape[0], 3), dtype=float)
    
    for (a, b, c) in tris:
        pa, pb, pc = coords_fdm[a], coords_fdm[b], coords_fdm[c]
        area = 0.5 * float(np.linalg.norm(np.cross(pb - pa, pc - pa)))
        
        force_z = -(pressure_Pa * area) / 3.0
        
        loads[a, 2] += force_z
        loads[b, 2] += force_z
        loads[c, 2] += force_z
        
    return loads


# =============================================================================
# PAYLOAD
# =============================================================================

def generate_payload_load(coords_fdm, apex_index, payload_kg):
    """Apply a point load at a specific node (e.g., the apex)."""
    loads = np.zeros((coords_fdm.shape[0], 3), dtype=float)
    if apex_index is not None and apex_index < len(coords_fdm):
        loads[apex_index, 2] -= (payload_kg * 9.81)
    return loads
