"""SDSe Engine — 3D Steel Frame Sizer (Three Cases, Worst-Case).

Accepts three load cases (uplift, downforce, dead_only).
Runs the frame solver for each case.
Sizes each member for the WORST utilization across all three cases.

Includes diagnostic prints to trace exactly where the force becomes zero.
"""

import math

import numpy as np
import streamlit as st

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

    N_cap = A_mm2 * fy_MPa
    My_cap = Wy_mm3 * fy_MPa
    Mz_cap = Wz_mm3 * fy_MPa

    stress_util = 0.0
    if N_cap > 0:
        stress_util += abs(N_Ed_N) / N_cap
    if My_cap > 0:
        stress_util += abs(My_Ed_Nm) / My_cap
    if Mz_cap > 0:
        stress_util += abs(Mz_Ed_Nm) / Mz_cap

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
                      utilization_cap=0.70):
    """
    newton_data_cases: dict of { "uplift": {"dr_result": ...}, "downforce": {...}, "dead_only": {...} }
    """
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

    # --- DEBUG 1: Load arriving at the builder ---
    for case_name, frame in frames_by_case.items():
        total_load = frame.get("diagnostic_total_load_magnitude_N", 0.0)
        st.write(f"DEBUG 1 — Case {case_name}: Total membrane load = {total_load:.1f} N")
        st.write(f"DEBUG 1b — Case {case_name}: Fixed nodes = {len(frame['fixed_indices'])}, Elements = {len(frame['elements'])}")

    for iteration in range(max_iterations):
        util_by_type = {
            k: {"max_util": 0.0, "max_N": 0.0, "governing_case": "n/a"}
            for k in ("primary", "rib", "ring", "drop", "spoke")
        }
        last_result = None

        for case_name, frame in frames_by_case.items():
            elements = []
            for elem in frame["elements"]:
                sec_name = sections.get(elem["section"], smallest)
                sec_props = SECTION_PROPERTIES.get(sec_name, {})
                elements.append({
                    "a": elem["a"], "b": elem["b"],
                    "section": sec_props, "kind": elem["kind"],
                    "section_name": sec_name,
                })

            loads_6dof = np.zeros((len(frame["nodes"]), 6), dtype=float)
            loads_6dof[:, 0:3] = frame["membrane_loads"]

            # --- DEBUG 2: Force arriving at the solver ---
            if iteration == 0 and case_name == "uplift":
                st.write(f"DEBUG 2 — F_global sum (all 3 DOF × all nodes) = {np.sum(np.abs(loads_6dof)):.1f} N")

            grade_props = {
                "E": STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000),
                "G": STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("E", 210000) / (2 * 1.3),
            }

            result = solve_frame(
                nodes=frame["nodes"],
                elements=elements,
                loads=loads_6dof,
                fixed_nodes=frame["fixed_indices"],
                grade_props=grade_props,
            )
            last_result = result

            # --- DEBUG 3 & 4: What comes back from the solver ---
            if iteration == 0 and case_name == "uplift":
                disp_sum = np.sum(np.abs(result["displacements"]))
                st.write(f"DEBUG 3 — u_global sum (displacement) = {disp_sum:.4e}")
                if len(result["member_end_forces"]) > 0:
                    max_N = max(abs(f["N"]) for f in result["member_end_forces"])
                    max_My = max(max(abs(f["My_a"]), abs(f["My_b"])) for f in result["member_end_forces"])
                    st.write(f"DEBUG 4 — Max |N| = {max_N:.1f} N · Max |My| = {max_My:.1f} N·m")
                else:
                    st.write("DEBUG 4 — Member end forces list is EMPTY")

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
            if last_result is not None:
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
            if last_result is not None:
                last_result["anchor_to_frame_id"] = frames_by_case["uplift"]["anchor_to_frame_id"]
            return {
                "sections": sections, "frame_result": last_result,
                "details": util_by_type, "iteration_log": iteration_log,
                "error": "Oversize required — catalogue exhausted",
            }

    return {
        "sections": sections, "frame_result": last_result,
        "details": util_by_type, "iteration_log": iteration_log,
        "error": "Max iterations reached without convergence",
    }
