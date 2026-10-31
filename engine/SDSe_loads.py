# =============================================================================
# SDSe Engine - Ultimate Limit State (ULS) Load Generator
# =============================================================================
# This file takes the final form-found shape (FDM) and calculates the 
# true Ultimate Limit State (ULS) forces based on wind code and material limits.
# =============================================================================

import numpy as np
from engine.SDSe_materials import calculate_uls_forces

# Standard steel density (kg/m^3)
RHO_STEEL = 7850.0
GRAVITY = 9.81

def calculate_uls_loads(topology, data):
    """
    Calculates the exact 3D force vectors on every node at Ultimate Limit State.
    Returns an array of shape (n_nodes, 3) in Newtons.
    """
    nodes = topology["nodes"]
    elements = topology["elements"]
    anchor_map = topology["anchor_to_frame_id"]
    ring_map = topology["ring_to_frame_id"]
    drop_map = topology["drop_to_frame_id"]
    
    n_nodes = len(nodes)
    loads = np.zeros((n_nodes, 3), dtype=float)

    # 1. Get the ULS material and wind parameters
    fabric_type = data.get("fabric_type", "PVDF")
    fabric_grade = data.get("fabric_grade", "Type III")
    wind_code = data.get("load_standard", "MY")
    
    uls = calculate_uls_forces(fabric_type, fabric_grade, wind_code)
    
    # The maximum tension the fabric is allowed to pull with
    allowable_tension_N_per_m = uls["allowable_warp_kNm"] * 1000.0
    wind_suction_kpa = abs(uls["wind_uls_suction_kpa"])
    
    # =========================================================================
    # 2. CALCULATE MEMBRANE PULL (Based on ULS Allowable Tension)
    # =========================================================================
    # The membrane pulls inward on the anchors at the allowable tension.
    for mesh_idx, frame_idx in anchor_map.items():
        px, py, pz = nodes[frame_idx]
        r = np.sqrt(px**2 + py**2)
        if r > 1e-6:
            # Pull towards the center
            loads[frame_idx, 0] -= (px / r) * allowable_tension_N_per_m
            loads[frame_idx, 1] -= (py / r) * allowable_tension_N_per_m
            # Vertical pull (assuming roughly 45 degree slope at the edge)
            loads[frame_idx, 2] -= allowable_tension_N_per_m

    # The membrane pulls down on the rings
    for mesh_idx, frame_idx in ring_map.items():
        loads[frame_idx, 2] -= allowable_tension_N_per_m * 0.5

    # The membrane pulls down on the drop poles
    for mesh_idx, frame_idx in drop_map.items():
        loads[frame_idx, 2] -= allowable_tension_N_per_m * 1.0

    # =========================================================================
    # 3. SELF-WEIGHT (Gravity on Steel Members)
    # =========================================================================
    for elem in elements:
        a = elem["a"]
        b = elem["b"]
        length = np.linalg.norm(nodes[b] - nodes[a])
        
        # Estimate mass based on member type (ULS preliminary sizing)
        if elem["kind"] == "primary":
            area_m2 = 0.005  # roughly CHS 168x8
        elif elem["kind"] == "rib":
            area_m2 = 0.003  # roughly CHS 114x6
        else:
            area_m2 = 0.001  # roughly CHS 60x3
            
        mass = length * area_m2 * RHO_STEEL
        weight_N = mass * GRAVITY
        
        loads[a, 2] -= weight_N * 0.5
        loads[b, 2] -= weight_N * 0.5

    # =========================================================================
    # 4. WIND LOAD (Horizontal Force on the projected area)
    # =========================================================================
    wind_pa = wind_suction_kpa * 1000.0
    
    for elem in elements:
        a = elem["a"]
        b = elem["b"]
        length = np.linalg.norm(nodes[b] - nodes[a])
        
        # Estimate diameter based on type
        if elem["kind"] == "primary":
            dia = 0.168
        elif elem["kind"] == "rib":
            dia = 0.114
        else:
            dia = 0.060
            
        area_proj = length * dia
        wind_force = area_proj * wind_pa
        
        # Apply wind in the +X direction (worst case scenario)
        loads[a, 0] += wind_force * 0.5
        loads[b, 0] += wind_force * 0.5

    return loads
