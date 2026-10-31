# =============================================================================
# SDSe Engine - Structural Orchestrator (100% iPhone Computation)
# =============================================================================
# This file does NO matrix math on the server. 
# It builds the topology, sends it to the iPhone, and reads the results.
# =============================================================================

import numpy as np
from engine.SDSe_frame_topology import build_frame_topology
from ui.components.pyodide_integrator import solve_matrix_on_phone
from data.sections import SECTION_PROPERTIES
from data.materials import STEEL_MATERIALS

def run_structural_analysis(data):
    """
    Main entry point. 
    Sends ALL heavy math to the iPhone to prevent server OOM (Error 137).
    """
    # 1. Build the Geometry (This is lightweight)
    topology = build_frame_topology(data)
    
    # 2. Define the starting steel sections (smallest available)
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

    # 3. Iterate to find the right sections
    for iteration in range(10):
        section_props = {}
        for k, name in current_sections.items():
            section_props[k] = SECTION_PROPERTIES[name]
            
        # --- SEND TO IPHONE (Geometry + Sections) ---
        # We send the topology and section sizes. 
        # The iPhone will calculate the ULS loads and run the matrix solve.
        phone_result = solve_matrix_on_phone(
            topology=topology,
            loads=[], # Empty, the iPhone will calculate them
            sections=section_props,
            grade=grade_props,
            key=f"matrix_calc_{iteration}"
        )
        
        if phone_result is None:
            return {"error": "Waiting for iPhone to finish calculating..."}
            
        if "error" in phone_result:
            return {"error": "iPhone Solver Error: " + phone_result["error"]}
            
        results = phone_result
        
        # 4. Check utilization
        max_util = {k: 0.0 for k in current_sections.keys()}
        
        for elem in results.get("member_end_forces", []):
            kind = elem["kind"]
            if kind not in max_util:
                continue
                
            sec = section_props[kind]
            A_mm2 = sec["A"]
            Wy_mm3 = sec.get("Wy", sec.get("W_el", 1.0))
            Wz_mm3 = sec.get("Wz", sec.get("W_el", 1.0))
            
            N_kN = abs(elem["N"]) / 1000.0
            My_kNm = max(abs(elem["My_a"]), abs(elem["My_b"])) / 1e6
            Mz_kNm = max(abs(elem["Mz_a"]), abs(elem["Mz_b"])) / 1e6
            
            stress_util = 0.0
            if A_mm2 > 0: stress_util += (abs(N_kN) * 1000.0) / (A_mm2 * fy_MPa)
            if Wy_mm3 > 0: stress_util += (My_kNm * 1e6) / (Wy_mm3 * fy_MPa)
            if Wz_mm3 > 0: stress_util += (Mz_kNm * 1e6) / (Wz_mm3 * fy_MPa)
            
            if stress_util > max_util[kind]:
                max_util[kind] = stress_util

        failing = [k for k, u in max_util.items() if u > 0.85]
        if not failing:
            return {
                "sections": current_sections,
                "results": results,
                "max_utilization": max_util,
                "iterations": iteration + 1
            }

        for k in failing:
            current_name = current_sections[k]
            for i, (area, name, props) in enumerate(all_sections):
                if name == current_name and i + 1 < len(all_sections):
                    current_sections[k] = all_sections[i + 1][1]
                    break

    return {
        "error": "Could not converge. Structure requires sections larger than catalogue.",
        "sections": current_sections,
        "max_utilization": max_util
    }
