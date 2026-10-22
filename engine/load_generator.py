"""SDSe Engine - Environmental Load Generator.

Converts user inputs (wind speed, snow depth) into nodal forces.
Includes code-specific parameters and partial safety factors (ULS).
"""

import math
import numpy as np

RHO_AIR = 1.225

# =============================================================================
# CODE PARAMETERS & SAFETY FACTORS
# =============================================================================

CODE_PARAMS = {
    "Malaysia (MS 1553)": {
        "wind_cp": -0.8, "snow_density": 100.0,
        "factors": {"dead": 1.35, "wind": 1.5, "snow": 1.5, "uplift_dead": 1.0}
    },
    "Eurocode (EN 1991)": {
        "wind_cp": -0.7, "snow_density": 100.0,
        "factors": {"dead": 1.35, "wind": 1.5, "snow": 1.5, "uplift_dead": 1.0}
    },
    "British (BS 6399)": {
        "wind_cp": -0.8, "snow_density": 100.0,
        "factors": {"dead": 1.4, "wind": 1.4, "snow": 1.6, "uplift_dead": 1.0}
    },
    "Australia (AS 1170)": {
        "wind_cp": -0.7, "snow_density": 100.0,
        "factors": {"dead": 1.2, "wind": 1.0, "snow": 1.0, "uplift_dead": 0.9}
    },
    "USA (ASCE 7)": {
        "wind_cp": -0.7, "snow_density": 100.0,
        "factors": {"dead": 1.2, "wind": 1.0, "snow": 1.6, "uplift_dead": 0.9}
    },
    "Japan (AIJ)": {
        "wind_cp": -0.9, "snow_density": 150.0,
        "factors": {"dead": 1.2, "wind": 1.2, "snow": 1.4, "uplift_dead": 1.0}
    },
    "Korea (KBC)": {
        "wind_cp": -0.8, "snow_density": 100.0,
        "factors": {"dead": 1.2, "wind": 1.2, "snow": 1.4, "uplift_dead": 1.0}
    },
    "China (GB 50009)": {
        "wind_cp": -0.8, "snow_density": 150.0,
        "factors": {"dead": 1.2, "wind": 1.4, "snow": 1.4, "uplift_dead": 1.0}
    },
}

def get_code_params(code_name):
    return CODE_PARAMS.get(code_name, CODE_PARAMS["Malaysia (MS 1553)"])

# =============================================================================
# BASE LOAD GENERATORS (Unfactored)
# =============================================================================

def _gen_wind_base(coords, tris, wind_speed_ms, code_name):
    params = get_code_params(code_name)
    q = 0.5 * RHO_AIR * (wind_speed_ms ** 2)
    pressure_Pa = q * params["wind_cp"]
    
    loads = np.zeros((coords.shape[0], 3), dtype=float)
    for (a, b, c) in tris:
        pa, pb, pc = coords[a], coords[b], coords[c]
        area = 0.5 * float(np.linalg.norm(np.cross(pb - pa, pc - pa)))
        force_z = (pressure_Pa * area) / 3.0
        loads[a, 2] += force_z; loads[b, 2] += force_z; loads[c, 2] += force_z
    return loads

def _gen_snow_base(coords, tris, snow_depth_m, code_name):
    params = get_code_params(code_name)
    pressure_Pa = snow_depth_m * params["snow_density"] * 9.81
    
    loads = np.zeros((coords.shape[0], 3), dtype=float)
    for (a, b, c) in tris:
        pa, pb, pc = coords[a], coords[b], coords[c]
        area = 0.5 * float(np.linalg.norm(np.cross(pb - pa, pc - pa)))
        force_z = -(pressure_Pa * area) / 3.0
        loads[a, 2] += force_z; loads[b, 2] += force_z; loads[c, 2] += force_z
    return loads

def _gen_dead_base(coords, tris, membrane_kg_m2=1.0):
    # Approx 1.0 kg/m2 for PVDF fabric
    pressure_Pa = membrane_kg_m2 * 9.81
    loads = np.zeros((coords.shape[0], 3), dtype=float)
    for (a, b, c) in tris:
        pa, pb, pc = coords[a], coords[b], coords[c]
        area = 0.5 * float(np.linalg.norm(np.cross(pb - pa, pc - pa)))
        force_z = -(pressure_Pa * area) / 3.0
        loads[a, 2] += force_z; loads[b, 2] += force_z; loads[c, 2] += force_z
    return loads

def generate_payload_load(coords_fdm, apex_index, payload_kg):
    loads = np.zeros((coords_fdm.shape[0], 3), dtype=float)
    if apex_index is not None and apex_index < len(coords_fdm):
        loads[apex_index, 2] -= (payload_kg * 9.81)
    return loads

# =============================================================================
# FACTORED LOAD GENERATOR (ULS)
# =============================================================================

def generate_uls_loads(coords, tris, code_name, wind_speed, snow_depth, payload_kg, apex_idx):
    """
    Generates factored loads for ULS.
    Includes both Gravity (max downward) and Uplift (max upward) scenarios.
    Returns a dictionary of load vectors.
    """
    params = get_code_params(code_name)
    f = params["factors"]
    
    # 1. Base Loads (Unfactored)
    dead_load = _gen_dead_base(coords, tris)
    snow_load = _gen_snow_base(coords, tris, snow_depth, code_name)
    wind_load = _gen_wind_base(coords, tris, wind_speed, code_name)
    payload_load = generate_payload_load(coords, apex_idx, payload_kg)
    
    # 2. ULS Combinations
    # Gravity Case: Dead + Snow + Payload (Wind ignored as it relieves gravity)
    uls_gravity = (dead_load * f["dead"]) + (snow_load * f["snow"]) + payload_load
    
    # Uplift Case: Min Dead + Wind (Snow ignored as it relieves uplift)
    uls_uplift = (dead_load * f["uplift_dead"]) + (wind_load * f["wind"])
    
    return {
        "gravity": uls_gravity,
        "uplift": uls_uplift,
        "service": dead_load + snow_load + wind_load + payload_load
    }
