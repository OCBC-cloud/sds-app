# =============================================================================
# SDSe Engine - Structural Orchestrator (Global Statics - Fixed KeyError)
# =============================================================================

import numpy as np
from engine.SDSe_frame_topology import build_frame_topology
from engine.SDSe_loads import calculate_uls_loads
from data.sections import SECTION_PROPERTIES
from data.materials import STEEL_MATERIALS, FABRIC_PROPERTIES

def run_structural_analysis(data):
    topology = build_frame_topology(data)
    
    fabric_type = data.get("fabric_type", "PVDF")
    fabric_grade = data.get("fabric_grade", "Ferrari 702")
    material_data = FABRIC_PROPERTIES.get(fabric_type, {}).get(fabric_grade, FABRIC_PROPERTIES["PVDF"]["Ferrari 702"])
    
    loads_dict = calculate_uls_loads(topology, data, material_data)
    
    grade = "S355"
    family = "CHS"
    
    # 1. Safely find the smallest section in the catalogue
    all_sections = []
    for name, props in SECTION_PROPERTIES.items():
        if props.get("type") == family and "A" in props and "I" in props:
            all_sections.append((props["A"], name))
    all_sections.sort(key=lambda x: x[0])
    
    if not all_sections:
        return {"error": "No valid CHS sections found in the catalogue."}
        
    smallest_section_name = all_sections[0][1]
    
    # Start with the smallest section for all members
    current_sections = {k: smallest_section_name for k in ("primary", "rib", "ring", "drop", "spoke")}
    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("fy", 355)

    # 2. Iterate to find the right size
    for iteration in range(10):
        # Fetch properties safely
        try:
            section_props = {k: SECTION_PROPERTIES[name] for k, name in current_sections.items()}
        except KeyError as e:
            return {"error": f"Section not found in catalogue: {e}"}
        
        max_util = {k: 0.0 for k in current_sections.keys()}
        
        primary_sec = section_props["primary"]
        A_mm2 = primary_sec.get("A", 1.0)
        Wy_mm3 = primary_sec.get("Wy", primary_sec.get("W_el", 1.0))
        
        # Calculate global wind forces
        max_wind_N = max(loads_dict["total_wind_uplift_N"], loads_dict["total_wind_pressure_N"])
        dome_height = float(data.get("crown_height", 9.0))
        global_moment_Nm = max_wind_N * (dome_height / 2.0)
        
        global_axial_N = np.sum(np.abs(loads_dict["pressure"][:, 0])) 
        
        # Calculate utilization for primary
        stress_util = 0.0
        if A_mm2 > 0: stress_util += global_axial_N / (A_mm2 * fy_MPa)
        if Wy_mm3 > 0: stress_util += (global_moment_Nm * 1000.0) / (Wy_mm3 * fy_MPa)
        
        # Apply same utilization to all members for simplification
        for k in max_util.keys():
            max_util[k] = stress_util

        failing = [k for k, u in max_util.items() if u > 0.85]
        if not failing:
            return {
                "sections": current_sections,
                "max_utilization": max_util,
                "loads": loads_dict,
                "status": "PASS"
            }

        # Upgrade the failing sections
        for k in failing:
            current_name = current_sections[k]
            for i, (area, name) in enumerate(all_sections):
                if name == current_name and i + 1 < len(all_sections):
                    current_sections[k] = all_sections[i + 1][1]
                    break

    return {"error": "Structure fails under ULS loads. Requires larger sections."}
