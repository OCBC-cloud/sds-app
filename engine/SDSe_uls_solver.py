# =============================================================================
# SDSe Engine - Ultimate Limit State (ULS) Global Statics Solver
# =============================================================================
# This file does the Global Statics math (no matrix solver).
# It is called by the Dome Viewer and saves results to session state.
# =============================================================================

import numpy as np
from data.materials import FABRIC_PROPERTIES

def run_uls_analysis(built, fdm_coords, dome_diameter, crown_height, fabric_type, fabric_grade):
    """
    Calculates the True Surface Area and Global Wind Forces.
    Returns a dictionary of results.
    """
    # 1. Calculate True Curved Surface Area
    pts = built["points"]
    tris = built["triangles"]
    true_surface_area = 0.0
    
    for tri in tris:
        p0 = pts[int(tri[0])]
        p1 = pts[int(tri[1])]
        p2 = pts[int(tri[2])]
        cross_prod = np.cross(p1 - p0, p2 - p0)
        true_surface_area += 0.5 * np.linalg.norm(cross_prod)

    # 2. Get Fabric Material Data
    fabric = FABRIC_PROPERTIES.get(fabric_type, {}).get(fabric_grade, FABRIC_PROPERTIES["PVDF"]["Ferrari 702"])
    f_u_warp = fabric.get("f_u_warp", 56.0) # kN/m
    allowable_tension_kN = f_u_warp / 6.0 # Safety factor 6
    allowable_tension_N = allowable_tension_kN * 1000.0

    # 3. Calculate Ultimate Wind Load (MS 1553: 33.5 m/s)
    wind_speed = 33.5 # m/s
    q_basic_pa = 0.613 * (wind_speed ** 2)
    cp_uplift = -0.8
    wind_uplift_pa = abs(q_basic_pa * cp_uplift)
    total_uplift_N = wind_uplift_pa * true_surface_area

    # 4. Calculate Membrane Pull
    perimeter_length = np.pi * dome_diameter
    total_membrane_pull_N = allowable_tension_N * perimeter_length

    # 5. Calculate Reactions
    n_anchors = 12 # Estimated for a standard dome
    wind_per_anchor_kN = (total_uplift_N / n_anchors) / 1000.0
    pull_per_anchor_kN = (total_membrane_pull_N / n_anchors) / 1000.0

    # 6. Quick Overturning Moment for Steel Sizing
    global_moment_kNm = (total_uplift_N / 1000.0) * (crown_height / 2.0)

    return {
        "surface_area_m2": true_surface_area,
        "total_uplift_kN": total_uplift_N / 1000.0,
        "total_membrane_pull_kN": total_membrane_pull_N / 1000.0,
        "wind_per_anchor_kN": wind_per_anchor_kN,
        "pull_per_anchor_kN": pull_per_anchor_kN,
        "overturning_moment_kNm": global_moment_kNm,
        "n_anchors": n_anchors,
        "wind_speed_ms": wind_speed
    }
