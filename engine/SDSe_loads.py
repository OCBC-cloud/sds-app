# =============================================================================
# SDSe Engine - Ultimate Limit State (ULS) Load Generator (Global Statics)
# =============================================================================
# Calculates True Surface Area and applies Code-Compliant Load Combinations
# for both Wind Uplift (Negative) and Wind Pressure (Positive).
# =============================================================================

import numpy as np
from data.materials import STEEL_MATERIALS

GRAVITY = 9.81

def calculate_uls_loads(topology, data, material_data):
    """
    Calculates the exact 3D force vectors on every node for both Uplift and Pressure.
    Returns a dictionary containing the loads for both cases and the true surface area.
    """
    nodes = topology["nodes"]
    elements = topology["elements"]
    anchor_map = topology["anchor_to_frame_id"]
    ring_map = topology["ring_to_frame_id"]
    
    n_nodes = len(nodes)
    loads_uplift = np.zeros((n_nodes, 3), dtype=float)
    loads_pressure = np.zeros((n_nodes, 3), dtype=float)

    # 1. Extract Material Properties from the database file
    f_u_warp = material_data.get("f_u_warp", 56.0) # kN/m
    # Apply safety factor of 6 for membrane
    allowable_tension_kN = f_u_warp / 6.0
    allowable_tension_N = allowable_tension_kN * 1000.0

    # 2. Calculate Code Wind Pressures (Based on 33.5 m/s for MY)
    wind_speed = 33.5 # m/s
    q_basic = 0.613 * (wind_speed ** 2) # Pa
    
    # Cp factors for dome (Suction and Pressure)
    cp_suction = -0.8
    cp_pressure = 0.5
    
    wind_suction_pa = abs(q_basic * cp_suction)
    wind_pressure_pa = q_basic * cp_pressure

    # 3. Calculate True Curved Surface Area
    fdm_coords = data["fdm_coords"]
    triangles = data["built"]["triangles"]
    
    true_surface_area = 0.0
    for tri in triangles:
        p0 = fdm_coords[int(tri[0])]
        p1 = fdm_coords[int(tri[1])]
        p2 = fdm_coords[int(tri[2])]
        cross_prod = np.cross(p1 - p0, p2 - p0)
        true_surface_area += 0.5 * np.linalg.norm(cross_prod)

    # Calculate Total Forces
    total_wind_uplift_N = wind_suction_pa * true_surface_area
    total_wind_pressure_N = wind_pressure_pa * true_surface_area
    
    dome_diameter = float(data.get("dome_diameter", 18.0))
    perimeter_length = np.pi * dome_diameter
    total_membrane_pull_N = allowable_tension_N * perimeter_length

    # 4. Calculate Self-Weight per node
    weights = np.zeros(n_nodes)
    for elem in elements:
        a = elem["a"]
        b = elem["b"]
        length = np.linalg.norm(nodes[b] - nodes[a])
        
        # Estimate mass based on member type
        area_m2 = 0.005 if elem["kind"] == "primary" else (0.003 if elem["kind"] == "rib" else 0.001)
        mass = length * area_m2 * 7850.0 # steel density
        weight_N = mass * GRAVITY
        
        weights[a] += weight_N * 0.5
        weights[b] += weight_N * 0.5

    # 5. Distribute Forces to Nodes
    n_anchors = max(len(anchor_map), 1)
    n_rings = max(len(ring_map), 1)
    
    wind_up_per_anchor = total_wind_uplift_N / n_anchors
    wind_down_per_anchor = total_wind_pressure_N / n_anchors
    pull_per_anchor = total_membrane_pull_N / n_anchors
    ring_force = allowable_tension_N * 1.5 / n_rings # Membrane pulling down on rings

    for i in range(n_nodes):
        px, py, pz = nodes[i]
        
        # --- CASE 1: UPLIFT (Wind Suction + Dead Load) ---
        # 1.0 * Dead Load + 1.5 * Wind Uplift
        loads_uplift[i, 2] -= 1.0 * weights[i] 
        
        # --- CASE 2: PRESSURE (Wind Push + Dead Load) ---
        # 1.35 * Dead Load + 1.5 * Wind Pressure
        loads_pressure[i, 2] -= 1.35 * weights[i]

    # Apply Anchor Loads
    for mesh_idx, frame_idx in anchor_map.items():
        px, py, pz = nodes[frame_idx]
        r = np.sqrt(px**2 + py**2)
        if r > 1e-6:
            # Inward pull from membrane (happens in both cases)
            loads_uplift[frame_idx, 0] -= 1.5 * (px / r) * pull_per_anchor
            loads_uplift[frame_idx, 1] -= 1.5 * (py / r) * pull_per_anchor
            loads_pressure[frame_idx, 0] -= 1.5 * (px / r) * pull_per_anchor
            loads_pressure[frame_idx, 1] -= 1.5 * (py / r) * pull_per_anchor
            
            # Wind Forces
            loads_uplift[frame_idx, 2] += 1.5 * wind_up_per_anchor
            loads_pressure[frame_idx, 2] -= 1.5 * wind_down_per_anchor

    # Apply Ring Loads (Downward)
    for mesh_idx, frame_idx in ring_map.items():
        loads_uplift[frame_idx, 2] -= 1.5 * ring_force
        loads_pressure[frame_idx, 2] -= 1.5 * ring_force

    return {
        "uplift": loads_uplift,
        "pressure": loads_pressure,
        "surface_area": true_surface_area,
        "total_wind_uplift_N": total_wind_uplift_N,
        "total_wind_pressure_N": total_wind_pressure_N
    }
