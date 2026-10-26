"""SDSe Engine — 3D Steel Frame Sizer.

Iteratively sizes the member sections of a 3D steel frame so that every
member passes:
  - Combined stress check (axial + bending)
  - Euler buckling check
  - 70% utilization cap
"""

import math

import numpy as np

from data.materials import STEEL_MATERIALS
from data.sections import SECTION_PROPERTIES
from engine.steel_frame_solver import solve_frame
from engine.steel_frame_builder import build_steel_frame


# =============================================================================
# SECTION CATALOGUE HELPERS
# =============================================================================

def _sections_by_area(family="CHS"):
    """Return sections sorted by area (smallest first)."""
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
    """Return the next larger section by area."""
    all_sections = _sections_by_area(family)
    for i, (name, _) in enumerate(all_sections):
        if name == current_name:
            if i + 1 < len(all_sections):
                return all_sections[i + 1][0]
            else:
                return None
    return all_sections[0][0] if all_sections else None


# =============================================================================
# MEMBER UTILIZATION
# =============================================================================

def _member_utilization(section_name, N_Ed_N, My_Ed_Nm, Mz_Ed_Nm,
                         L_m, grade="S355", K=1.0):
    """Compute the utilization of a section for the given forces."""
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
    """Check the ring's hoop compression."""
    props = SECTION_PROPERTIES.get(section_name, {})
    if not props or "A" not in props:
        return 999.0

    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(grade, {}).get("fy", 355)
    A_mm2 = props.get("A", 1.0)
    N_cap = A_mm2 * fy_MPa

    N_hoop = membrane_force_at_ring_N * ring_radius_m
    return abs(N_hoop) / N_cap if N_cap > 0 else 999.0


# =============================================================================
# MAIN SIZER
# =============================================================================

def size_steel_frame(data, newton_data, code_choice="MS 1553",
                      grade="S355", family="CHS", max_iterations=12,
                      utilization_cap=0.70):
    """Size all frame members so every one passes the utilization cap."""
    all_sections = _sections_by_area(family)
    if not all_sections:
        return {
            "sections": {}, "frame_result": None, "details": {},
            "iteration_log": [{"error": "No sections in catalogue"}]
        }

    smallest = all_sections[0][0]
    sections = {
        "primary": smallest,
        "rib": smallest,
        "ring": smallest,
        "drop": smallest,
        "spoke": smallest,
    }

    iteration_log = []

    for iteration in range(max_iterations):
        frame = build_steel_frame(data, newton_data)
        frame["sections_map"] = sections

        elements = []
        for elem in frame["elements"]:
            sec_name = sections.get(elem["section"], smallest)
            sec_props = SECTION_PROPERTIES.get(sec_name, {})
            elements.append({
                "a": elem["a"],
                "b": elem["b"],
                "section": sec_props,
                "kind": elem["kind"],
                "section_name": sec_name,
            })

        loads_6dof = np.zeros((len(frame["nodes"]), 6), dtype=float)
        loads_6dof[:, 0:3] = frame["membrane_loads"]

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

        util_by_type = {
            "primary": {"max_util": 0.0, "max_N": 0.0, "max_My": 0.0, "max_Mz": 0.0, "count": 0},
            "rib":     {"max_util": 0.0, "max_N": 0.0, "max_My": 0.0, "max_Mz": 0.0, "count": 0},
            "ring":    {"max_util": 0.0, "max_N": 0.0, "max_My": 0.0, "max_Mz": 0.0, "count": 0},
            "drop":    {"max_util": 0.0, "max_N": 0.0, "max_My": 0.0, "max_Mz": 0.0, "count": 0},
            "spoke":   {"max_util": 0.0, "max_N": 0.0, "max_My": 0.0, "max_Mz": 0.0, "count": 0},
        }

        for k, elem in enumerate(elements):
            end_forces = result["member_end_forces"][k]
            kind = elem["kind"]
            if kind not in util_by_type:
                continue

            N_Ed = end_forces.get("N", 0.0)
            My_a = end_forces.get("My_a", 0.0)
            My_b = end_forces.get("My_b", 0.0)
            Mz_a = end_forces.get("Mz_a", 0.0)
            Mz_b = end_forces.get("Mz_b", 0.0)
            My_Ed = max(abs(My_a), abs(My_b))
            Mz_Ed = max(abs(Mz_a), abs(Mz_b))

            L = float(np.linalg.norm(
                frame["nodes"][elem["b"]] - frame["nodes"][elem["a"]]
            ))

            util, _, _, _, _ = _member_utilization(
                elem["section_name"], N_Ed, My_Ed, Mz_Ed, L, grade
            )

            if kind == "ring":
                ring_radius = data.get("ring_diameter", 1.0) / 2.0
                membrane_force_estimate = max(abs(N_Ed), 1000.0)
                hoop_util = _ring_hoop_utilization(
                    elem["section_name"], membrane_force_estimate, ring_radius, grade
                )
                util = max(util, hoop_util)

            util_by_type[kind]["max_util"] = max(util_by_type[kind]["max_util"], util)
            util_by_type[kind]["max_N"] = max(util_by_type[kind]["max_N"], abs(N_Ed))
            util_by_type[kind]["max_My"] = max(util_by_type[kind]["max_My"], My_Ed)
            util_by_type[kind]["max_Mz"] = max(util_by_type[kind]["max_Mz"], Mz_Ed)
            util_by_type[kind]["count"] += 1

        iteration_log.append({
            "iteration": iteration,
            "sections": dict(sections),
            "utilizations": {k: v["max_util"] for k, v in util_by_type.items()},
            "forces": {
                k: {
                    "max_N_kN": v["max_N"] / 1000.0,
                    "max_My_kNm": v["max_My"] / 1e6,
                    "max_Mz_kNm": v["max_Mz"] / 1e6,
                }
                for k, v in util_by_type.items()
            },
        })

        failing_types = [k for k, v in util_by_type.items() if v["max_util"] > utilization_cap]

        if not failing_types:
            result["anchor_to_frame_id"] = frame["anchor_to_frame_id"]
            return {
                "sections": sections,
                "frame_result": result,
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
            result["anchor_to_frame_id"] = frame["anchor_to_frame_id"]
            return {
                "sections": sections,
                "frame_result": result,
                "details": util_by_type,
                "iteration_log": iteration_log,
                "error": "Oversize required — catalogue exhausted",
            }

    result["anchor_to_frame_id"] = frame["anchor_to_frame_id"]
    return {
        "sections": sections,
        "frame_result": result,
        "details": util_by_type,
        "iteration_log": iteration_log,
        "error": "Max iterations reached without convergence",
    }
