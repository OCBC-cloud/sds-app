"""SDSe Engine - Universal Frame Analysis Controller.

Takes a steel frame (nodes, elements, fixed indices) and a dictionary
of applied loads (from the Load Extractor), runs the 3D solver, and 
auto-sizes the steel tubes.
"""

import numpy as np
from data.materials import STEEL_MATERIALS
from data.sections import SECTION_PROPERTIES
from engine.steel_frame_solver import solve_frame
from engine.steel_frame_sizer import _sections_by_area, _next_section_up, _member_utilization

def analyze_and_size_frame(frame_data, applied_loads, grade="S355", family="CHS", utilization_cap=0.85):
    """
    frame_data: dict with "nodes", "elements", "fixed_indices"
    applied_loads: dict mapping frame_node_idx -> [Fx, Fy, Fz]
    """
    all_sections = _sections_by_area(family)
    if not all_sections:
        return {"error": "No sections found in catalogue."}
        
    smallest = all_sections[0][0]
    # Default all member types to the smallest tube
    sections = {"primary": smallest, "rib": smallest, "spoke": smallest, "strut": smallest}
    
    grade_props = {
        "E": STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000),
        "G": STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000) / (2 * 1.3),
    }

    n_nodes = len(frame_data["nodes"])
    loads_6dof = np.zeros((n_nodes, 6), dtype=float)
    
    # Apply the loads from the membrane
    for node_idx, force_vec in applied_loads.items():
        loads_6dof[node_idx, 0:3] = force_vec

    # Loop until we find a size that works
    for iteration in range(15):
        elements_with_props = []
        for elem in frame_data["elements"]:
            sec_name = sections.get(elem["kind"], smallest)
            sec_props = SECTION_PROPERTIES.get(sec_name, {})
            elements_with_props.append({
                "a": elem["a"], "b": elem["b"],
                "section": sec_props, "kind": elem["kind"],
                "section_name": sec_name,
            })

        try:
            result = solve_frame(
                nodes=frame_data["nodes"],
                elements=elements_with_props,
                loads=loads_6dof,
                fixed_nodes=frame_data["fixed_indices"],
                grade_props=grade_props,
            )
        except Exception as e:
            return {"error": f"Solver failed: {e}"}

        # Check utilization for each member type
        util_by_type = {k: 0.0 for k in ("primary", "rib", "spoke", "strut")}
        
        for k, elem in enumerate(elements_with_props):
            end_forces = result["member_end_forces"][k]
            kind = elem["kind"]
            
            N_Ed = end_forces.get("N", 0.0)
            My_Ed = max(abs(end_forces.get("My_a", 0.0)), abs(end_forces.get("My_b", 0.0)))
            Mz_Ed = max(abs(end_forces.get("Mz_a", 0.0)), abs(end_forces.get("Mz_b", 0.0)))
            L = float(np.linalg.norm(frame_data["nodes"][elem["b"]] - frame_data["nodes"][elem["a"]]))

            util, _, _, _, _ = _member_utilization(elem["section_name"], N_Ed, My_Ed, Mz_Ed, L, grade)
            
            if util > util_by_type[kind]:
                util_by_type[kind] = util

        # Check if we need to size up
        failing_types = [k for k, u in util_by_type.items() if u > utilization_cap]
        if not failing_types:
            return {
                "status": "Converged",
                "sections": sections,
                "details": util_by_type,
                "frame_result": result,
                "iterations": iteration
            }

        progressed = False
        for ftype in failing_types:
            new_sec = _next_section_up(sections[ftype], family)
            if new_sec is not None and new_sec != sections[ftype]:
                sections[ftype] = new_sec
                progressed = True

        if not progressed:
            return {
                "status": "Failed",
                "error": "Catalogue exhausted. Structure too large for this load.",
                "sections": sections,
                "details": util_by_type
            }

    return {"status": "Failed", "error": "Max iterations reached."}
