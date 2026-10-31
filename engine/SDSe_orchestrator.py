# =============================================================================
# SDSe Engine - Structural Orchestrator (The Brain)
# =============================================================================
# Ties together the Topology, ULS Loads, and Frame Analysis.
# Calculates the exact member utilizations for the final steel sizes.
# =============================================================================

import numpy as np
from engine.SDSe_frame_topology import build_frame_topology
from engine.SDSe_loads import calculate_uls_loads
from engine.SDSe_frame_analysis import solve_frame_analysis
from data.sections import SECTION_PROPERTIES
from data.materials import STEEL_MATERIALS

def run_structural_analysis(data):
    """
    Main entry point for the structural engine.
    Returns a dict with the final sized sections, reactions, and member forces.
    """
    # 1. Build the Geometry
    topology = build_frame_topology(data)
    
    # 2. Calculate the Ultimate Loads (Wind, Gravity, Membrane)
    loads = calculate_uls_loads(topology, data)
    
    # 3. Define the starting steel sections (smallest available)
    # We iterate until the structure passes.
    grade = "S355"
    family = "CHS"
    
    all_sections = []
    for name, props in SECTION_PROPERTIES.items():
        if props.get("type") == family and "A" in props and "I" in props:
            all_sections.append((props["A"], name, props))
    all_sections.sort(key=lambda x: x[0])
    
    if not all_sections:
        return {"error": "No sections found in catalogue"}
        
    current_sections = {
        "primary": all_sections[0][0],
        "rib": all_sections[0][0],
        "ring": all_sections[0][0],
        "drop": all_sections[0][0],
        "spoke": all_sections[0][0],
    }
    
    grade_props = {
        "E": STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000),
        "G": STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000) / (2 * 1.3),
    }
    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("fy", 355)

    # 4. Iterate to find the right sections (Max 15 iterations)
    for iteration in range(15):
        # Build the section properties dictionary for the solver
        section_props = {}
        for k, name in current_sections.items():
            section_props[k] = SECTION_PROPERTIES[name]
            
        # Run the matrix stiffness solver
        results = solve_frame_analysis(topology, loads, section_props, grade_props)
        
        # Check utilization for every member
        max_util = {k: 0.0 for k in current_sections.keys()}
        
        for elem in results["member_end_forces"]:
            kind = elem["kind"]
            if kind not in max_util:
                continue
                
            sec = section_props[kind]
            A_mm2 = sec["A"]
            Wy_mm3 = sec.get("Wy", sec.get("W_el", 1.0))
            Wz_mm3 = sec.get("Wz", sec.get("W_el", 1.0))
            
            # Extract true forces
            N_kN = abs(elem["N"]) / 1000.0
            My_kNm = max(abs(elem["My_a"]), abs(elem["My_b"])) / 1e6
            Mz_kNm = max(abs(elem["Mz_a"]), abs(elem["Mz_b"])) / 1e6
            
            # Calculate utilization (Stress / Capacity)
            stress_util = 0.0
            if A_mm2 > 0: stress_util += (abs(N_kN) * 1000.0) / (A_mm2 * fy_MPa)
            if Wy_mm3 > 0: stress_util += (My_kNm * 1e6) / (Wy_mm3 * fy_MPa)
            if Wz_mm3 > 0: stress_util += (Mz_kNm * 1e6) / (Wz_mm3 * fy_MPa)
            
            if stress_util > max_util[kind]:
                max_util[kind] = stress_util

        # If everything is under 85% capacity, we are done!
        failing = [k for k, u in max_util.items() if u > 0.85]
        if not failing:
            return {
                "sections": current_sections,
                "results": results,
                "max_utilization": max_util,
                "iterations": iteration + 1
            }

        # If something is failing, upgrade that specific section
        for k in failing:
            current_name = current_sections[k]
            # Find the next bigger section
            for i, (area, name, props) in enumerate(all_sections):
                if name == current_name and i + 1 < len(all_sections):
                    current_sections[k] = all_sections[i + 1][1]
                    break

    return {
        "error": "Could not converge. Structure requires sections larger than catalogue.",
        "sections": current_sections,
        "max_utilization": max_util
    }
