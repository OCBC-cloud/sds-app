"""SDSe Engine - Environmental Load Generator.

Converts user inputs (wind speed, snow depth, payload) into nodal forces.
Generates three distinct load cases: uplift, downforce, dead_only.
"""

import math

import numpy as np

from data.materials import FABRIC_PROPERTIES
from engine.wind_cp_maps import get_cp_map
from engine.wind_cp_maps.base import (
    compute_slope_deg,
    find_nearest_cone_apex,
)

RHO_AIR = 1.225
GRAVITY = 9.81


# =============================================================================
# CODE PARAMETERS & SAFETY FACTORS
# =============================================================================

CODE_PARAMS = {
    "MS 1553": {
        "wind_cp": -0.7, "snow_density": 100.0,
        "factors": {"dead": 1.35, "wind": 1.5, "snow": 1.5, "uplift_dead": 0.9}
    },
    "EN 1991": {
        "wind_cp": -0.7, "snow_density": 100.0,
        "factors": {"dead": 1.35, "wind": 1.5, "snow": 1.5, "uplift_dead": 1.0}
    },
    "BS 6399": {
        "wind_cp": -0.8, "snow_density": 100.0,
        "factors": {"dead": 1.4, "wind": 1.4, "snow": 1.6, "uplift_dead": 1.0}
    },
    "AS 1170": {
        "wind_cp": -0.7, "snow_density": 100.0,
        "factors": {"dead": 1.2, "wind": 1.0, "snow": 1.0, "uplift_dead": 0.9}
    },
    "ASCE 7": {
        "wind_cp": -0.7, "snow_density": 100.0,
        "factors": {"dead": 1.2, "wind": 1.0, "snow": 1.6, "uplift_dead": 0.9}
    },
    "AIJ": {
        "wind_cp": -0.9, "snow_density": 150.0,
        "factors": {"dead": 1.2, "wind": 1.2, "snow": 1.4, "uplift_dead": 1.0}
    },
    "KBC": {
        "wind_cp": -0.8, "snow_density": 100.0,
        "factors": {"dead": 1.2, "wind": 1.2, "snow": 1.4, "uplift_dead": 1.0}
    },
    "GB 50009": {
        "wind_cp": -0.8, "snow_density": 150.0,
        "factors": {"dead": 1.2, "wind": 1.4, "snow": 1.4, "uplift_dead": 1.0}
    },
}


def get_code_params(code_name):
    return CODE_PARAMS.get(code_name, CODE_PARAMS["MS 1553"])


# =============================================================================
# BASE LOAD GENERATORS (Unfactored)
# =============================================================================

def _gen_wind_base(coords, tris, wind_speed_ms, code_name, shape_type,
                   h_over_d, cone_apexes=None, cone_radius_m=None,
                   wind_direction=(1.0, 0.0, 0.0)):
    """Generate surface-normal wind forces using the Cp map registry."""
    q = 0.5 * RHO_AIR * (wind_speed_ms ** 2)
    cp_map = get_cp_map(shape_type, code_name)
    
    loads = np.zeros((coords.shape[0], 3), dtype=float)
    
    total_uplift_N = 0.0
    max_pressure_Pa = 0.0
    pressures = []
    
    for (a, b, c) in tris:
        pa, pb, pc = coords[a], coords[b], coords[c]
        
        v1 = pb - pa
        v2 = pc - pa
        cross = np.cross(v1, v2)
        area = 0.5 * float(np.linalg.norm(cross))
        if area < 1e-12:
            continue
        normal = cross / (2.0 * area)
        
        slope_deg = compute_slope_deg(normal)
        
        normal_x = float(normal[0])
        if normal_x < -0.3:
            position = "windward"
        elif normal_x > 0.3:
            position = "leeward"
        else:
            position = "side"
        
        dist_from_apex = None
        if shape_type in ("multi_cone", "multi-cone", "multicone") and cone_apexes:
            centroid = (pa + pb + pc) / 3.0
            _, dist_from_apex = find_nearest_cone_apex(centroid, cone_apexes)
        
        try:
            cp = cp_map(
                slope_deg=slope_deg,
                h_over_d=h_over_d,
                position=position,
                distance_from_apex=dist_from_apex,
                cone_radius=cone_radius_m,
            )
        except TypeError:
            cp = cp_map(
                slope_deg=slope_deg,
                h_over_d=h_over_d,
                position=position,
            )
        
        pressure_Pa = cp * q
        force_vec = -pressure_Pa * area * normal
        
        loads[a] += force_vec / 3.0
        loads[b] += force_vec / 3.0
        loads[c] += force_vec / 3.0
        
        total_uplift_N += force_vec[2]
        if abs(pressure_Pa) > max_pressure_Pa:
            max_pressure_Pa = abs(pressure_Pa)
        pressures.append(pressure_Pa)
    
    diagnostics = {
        "q_Pa": q,
        "total_uplift_kN": total_uplift_N / 1000.0,
        "max_pressure_kPa": max_pressure_Pa / 1000.0,
        "mean_pressure_kPa": (np.mean(pressures) / 1000.0) if pressures else 0.0,
        "min_cp": min([p / q for p in pressures]) if q > 0 and pressures else 0.0,
        "max_cp": max([p / q for p in pressures]) if q > 0 and pressures else 0.0,
    }
    
    return loads, diagnostics


def _gen_snow_base(coords, tris, snow_depth_m, code_name):
    params = get_code_params(code_name)
    base_pressure_Pa = snow_depth_m * params["snow_density"] * GRAVITY
    
    loads = np.zeros((coords.shape[0], 3), dtype=float)
    
    for (a, b, c) in tris:
        pa, pb, pc = coords[a], coords[b], coords[c]
        cross = np.cross(pb - pa, pc - pa)
        area = 0.5 * float(np.linalg.norm(cross))
        if area < 1e-12:
            continue
        normal = cross / (2.0 * area)
        slope_deg = compute_slope_deg(normal)
        
        if slope_deg <= 30.0:
            mu = 0.8
        elif slope_deg >= 60.0:
            mu = 0.0
        else:
            t = (slope_deg - 30.0) / 30.0
            mu = 0.8 * (1.0 - t)
        
        pressure_Pa = mu * base_pressure_Pa
        force_z = -pressure_Pa * area / 3.0
        loads[a, 2] += force_z
        loads[b, 2] += force_z
        loads[c, 2] += force_z
    
    return loads


def _gen_dead_base(coords, tris, membrane_kg_m2=1.102):
    pressure_Pa = membrane_kg_m2 * GRAVITY
    loads = np.zeros((coords.shape[0], 3), dtype=float)
    for (a, b, c) in tris:
        pa, pb, pc = coords[a], coords[b], coords[c]
        area = 0.5 * float(np.linalg.norm(np.cross(pb - pa, pc - pa)))
        force_z = -(pressure_Pa * area) / 3.0
        loads[a, 2] += force_z
        loads[b, 2] += force_z
        loads[c, 2] += force_z
    return loads


def generate_payload_load(coords_fdm, tris, apex_index, payload_kg):
    loads = np.zeros((coords_fdm.shape[0], 3), dtype=float)
    if apex_index is None or apex_index >= len(coords_fdm) or payload_kg <= 0:
        return loads
    
    payload_N = payload_kg * GRAVITY
    adjacent_areas = []
    for (a, b, c) in tris:
        if apex_index in (a, b, c):
            pa, pb, pc = coords_fdm[a], coords_fdm[b], coords_fdm[c]
            area = 0.5 * float(np.linalg.norm(np.cross(pb - pa, pc - pa)))
            adjacent_areas.append((a, b, c, area))
    
    total_area = sum(t[3] for t in adjacent_areas)
    if total_area < 1e-12:
        loads[apex_index, 2] -= payload_N
        return loads
    
    for (a, b, c, area) in adjacent_areas:
        share = payload_N * (area / total_area)
        loads[a, 2] -= share / 3.0
        loads[b, 2] -= share / 3.0
        loads[c, 2] -= share / 3.0
    
    return loads


# =============================================================================
# THE THREE PROFESSIONAL LOAD CASES
# =============================================================================

def generate_uls_loads(coords, tris, code_name, wind_speed, snow_depth,
                        payload_kg, apex_idx,
                        shape_type="multi_cone",
                        h_over_d=0.0,
                        cone_apexes=None,
                        cone_radius_m=None,
                        membrane_kg_m2=1.102):
    """
    Returns three distinct load cases:
      - uplift: dead × 0.9 + wind_suction × 1.5
      - downforce: dead × 1.35 + wind_pressure × 1.5 + snow × 1.5 + payload × 1.5
      - dead_only: dead × 1.35
    """
    params = get_code_params(code_name)
    f = params["factors"]
    
    dead_load = _gen_dead_base(coords, tris, membrane_kg_m2)
    snow_load = _gen_snow_base(coords, tris, snow_depth, code_name)
    
    wind_suction_load, wind_suction_diag = _gen_wind_base(
        coords, tris, wind_speed, code_name, shape_type,
        h_over_d, cone_apexes, cone_radius_m,
    )
    # Wind pressure (downforce) is the opposite of suction
    wind_pressure_load = -wind_suction_load.copy()
    
    payload_load = generate_payload_load(coords, tris, apex_idx, payload_kg)
    
    # Case A: Uplift (wind suction)
    uls_uplift = (dead_load * f["uplift_dead"]) + (wind_suction_load * f["wind"])
    
    # Case B: Downforce (wind pressure + snow + payload)
    uls_downforce = (dead_load * f["dead"]) + (wind_pressure_load * f["wind"]) + (snow_load * f["snow"]) + (payload_load * 1.5)
    
    # Case C: Dead only
    uls_dead_only = dead_load * f["dead"]
    
    return {
        "uplift": uls_uplift,
        "downforce": uls_downforce,
        "dead_only": uls_dead_only,
        "wind_diagnostics": wind_suction_diag,
    }
