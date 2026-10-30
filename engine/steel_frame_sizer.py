"""SDSe Engine — 3D Steel Frame Sizer (Three Cases, Worst-Case, Defensive).

Accepts three load cases. Runs the frame solver for each.
Sizes each member for the WORST utilization across all valid cases.
"""

import math

import numpy as np

from data.materials import STEEL_MATERIALS
from data.sections import SECTION_PROPERTIES
from engine.steel_frame_solver import solve_frame
from engine.steel_frame_builder import build_steel_frame


def _sections_by_area(family="CHS"):
    items = []
    for name, props in SECTION_PROPERTIES.items():
        if props.get("type") != family:
            continue
        if "A" not in props or "I" not in props:
            continue
        items.append((props["A"], name, props))
    items.sort(key=lambda x: x[0])
    return [(name, props) for _, name, props in items]


def _next_section_up(current_name, family="CHS"):
    all_sections = _sections_by_area(family)
    for i, (name, _) in enumerate(all_sections):
        if name == current_name:
            if i + 1 < len(all_sections):
                return all_sections[i + 1][0]
            else:
                return None
    return all_sections[0][0] if all_sections else None


def _member_utilization(section_name, N_Ed_N, My_Ed_Nm, Mz_Ed_Nm,
                         L_m, grade="S355", K=1.0):
    props = SECTION_PROPERTIES.get(section_name, {})
    if not props or "A" not in props:
        return 999.0, 1.0, 1.0, 1.0, 1.0

    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("fy", 355)
    E_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000)

    A_mm2 = props.get("A", 1.0)
    Wy_mm3 = props.get("Wy", props.get("W_el", 1.0))
    Wz_mm3 = props.get("Wz", props.get("W_el", 1.0))
    I_mm4 = props.get("I", 1.0)

    # CAPACITIES (in Newtons and N-mm)
    N_cap = A_mm2 * fy_MPa
    My_cap = Wy_mm3 * fy_MPa
    Mz_cap = Wz_mm3 * fy_MPa

    stress_util = 0.0
    if N_cap > 0:
        stress_util += abs(N_Ed_N) / N_cap
    
    # FIXED: Convert My_Ed and Mz_Ed from N-m to N-mm before dividing!
    if My_cap > 0:
        stress_util += (abs(My_Ed_Nm) * 1000.0) / My_cap
    if Mz_cap > 0:
        stress_util += (abs(Mz_Ed_Nm) * 1000.0) / Mz_cap

    buckling_util = 0.0
    if N_Ed_N < 0 and L_m > 0:
        L_mm = L_m * 1000.0
        N_cr = (math.pi ** 2 * E_MPa * I_mm4) / ((K * L_mm) ** 2)
        if N_cr > 0:
            buckling_util = abs(N_Ed_N) / N_cr

    combined = stress_util + buckling_util
    return combined, N_cap, N_cr if N_Ed_N < 0 else 1e18, My_cap, Mz_cap


def _ring_hoop_utilization(section_name, membrane_force_at_ring_N,
                            ring_radius_m, grade="S355"):
    props = SECTION_PROPERTIES.get(section_name, {})
    if not props or "A" not in props:
        return 999.0

    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("fy", 355)
    A_mm2 = props.get("A", 1.0)
    N_cap = A_mm2 * fy_MPa

    N_hoop = membrane_force_at_ring_N * ring_radius_m
    return abs(N_hoop) / N_cap if N_cap > 0 else 999.0


def size_steel_frame(data, newton_data_cases, code_choice="MS 1553",
                      grade="S355", family="CHS", max_iterations=12,
                      utilization_cap=0.85):
    """Sizes for worst utilization across all CONVERGED cases."""
    all_sections = _sections_by_area(family)
    if not all_sections:
        return {"sections": {}, "frame_result": None, "details": {}, "iteration_log": []}

    smallest = all_sections[0][0]
    sections = {k: smallest for k in ("primary", "rib", "ring", "drop", "spoke")}
    iteration_log = []

    # Build the frame for each case
    frames_by_case = {}
    for case_name, nd in newton_data_cases.items():
        frames_by_case[case_name] = build_steel_frame(data, nd)

    for iteration in range(max_iterations):
        util_by_type = {
            k: {"max_util": 0.0, "max_N": 0.0, "governing_case": "n/a"}
            for k in ("primary", "rib", "ring", "drop", "spoke")
        }
        last_result = None

        for case_name, frame in frames_by_case.items():
            elements = []
            for elem in frame["elements"]:
                # Safely handle if 'section' is a string or a dict
                sec_key = elem["section"]
                if isinstance(sec_key, dict):
                    # It's the default dictionary we injected in the builder
                    sec_name = smallest
                else:
                    # It's the string kind (e.g., "primary")
                    sec_name = sections.get(sec_key, smallest)
                
                sec_props = SECTION_PROPERTIES.get(sec_name, {})

            loads_6dof = np.zeros((len(frame["nodes"]), 6), dtype=float)
            loads_6dof[:, 0:3] = frame["membrane_loads"]

            grade_props = {
                "E": STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000),
                "G": STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000) / (2 * 1.3),
            }

            try:
                result = solve_frame(
                    nodes=frame["nodes"],
                    elements=elements,
                    loads=loads_6dof,
                    fixed_nodes=frame["fixed_indices"],
                    grade_props=grade_props,
                )
            except Exception:
                continue

            if len(result["member_end_forces"]) != len(elements):
                continue

            last_result = result

            for k, elem in enumerate(elements):
                end_forces = result["member_end_forces"][k]
                kind = elem["kind"]
                if kind not in util_by_type:
                    continue

                N_Ed = end_forces.get("N", 0.0)
                My_Ed = max(abs(end_forces.get("My_a", 0.0)), abs(end_forces.get("My_b", 0.0)))
                Mz_Ed = max(abs(end_forces.get("Mz_a", 0.0)), abs(end_forces.get("Mz_b", 0.0)))
                L = float(np.linalg.norm(frame["nodes"][elem["b"]] - frame["nodes"][elem["a"]]))

                util, _, _, _, _ = _member_utilization(elem["section_name"], N_Ed, My_Ed, Mz_Ed, L, grade)

                if kind == "ring":
                    ring_radius = data.get("mc_rd", data.get("ring_diameter", 1.0)) / 2.0
                    membrane_force_estimate = max(abs(N_Ed), 1000.0)
                    hoop_util = _ring_hoop_utilization(elem["section_name"], membrane_force_estimate, ring_radius, grade)
                    util = max(util, hoop_util)

                if util > util_by_type[kind]["max_util"]:
                    util_by_type[kind]["max_util"] = util
                    util_by_type[kind]["max_N"] = abs(N_Ed)
                    util_by_type[kind]["governing_case"] = case_name

        iteration_log.append({"iteration": iteration, "sections": dict(sections)})

        failing_types = [k for k, v in util_by_type.items() if v["max_util"] > utilization_cap]
        if not failing_types:
            if last_result is not None and "uplift" in frames_by_case:
                last_result["anchor_to_frame_id"] = frames_by_case["uplift"]["anchor_to_frame_id"]
            return {
                "sections": sections,
                "frame_result": last_result,
                "details": util_by_type,
                "iteration_log": iteration_log,
            }

        progressed = False
        for ftype in failing_types:
            new_sec = _next_section_up(sections[ftype], family)
            if new_sec is not None and new_sec != sections[ftype]:
                sections[ftype] = new_sec
                progressed = True

        if not progressed:
            if last_result is not None and "uplift" in frames_by_case:
                last_result["anchor_to_frame_id"] = frames_by_case["uplift"]["anchor_to_frame_id"]
            return {
                "sections": sections, "frame_result": last_result,
                "details": util_by_type, "iteration_log": iteration_log,
                "error": "Oversize required — catalogue exhausted",
            }

    if last_result is not None and "uplift" in frames_by_case:
        last_result["anchor_to_frame_id"] = frames_by_case["uplift"]["anchor_to_frame_id"]
    return {
        "sections": sections, "frame_result": last_result,
        "details": util_by_type, "iteration_log": iteration_log,
        "error": "Max iterations reached without convergence",
    }
