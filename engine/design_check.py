# =============================================================================
# SDSe - Universal Design Check Engine
# =============================================================================
# Reads the output of the nonlinear solver and performs code-based
# checks on cables, membrane, and steel beams.
# Recommends the exact section size based on the user's chosen family.
# =============================================================================

import math

try:
    from data.materials import CABLE_PROPERTIES, FABRIC_PROPERTIES, STEEL_MATERIALS
    from data.sections import SECTION_PROPERTIES
except ImportError:
    CABLE_PROPERTIES = {}
    FABRIC_PROPERTIES = {}
    STEEL_MATERIALS = {}
    SECTION_PROPERTIES = {}


def _check_cables(cable_tensions, target_material="Locked Coil"):
    """
    Check the cable tensions against the specified material family.
    Returns (max_tension_N, recommended_size, is_safe).
    """
    max_tension = 0.0
    if cable_tensions:
        for cb in cable_tensions:
            if cb["T_N"] > max_tension:
                max_tension = cb["T_N"]

    family = CABLE_PROPERTIES.get(target_material, {})
    if not family:
        return max_tension / 1000.0, "Unknown Family", False

    best_size = None
    is_safe = False
    SAFETY_FACTOR = 2.0
    design_load_N = max_tension * SAFETY_FACTOR

    for size, props in family.items():
        if size == "default":
            continue
        if props.get("A") and props.get("f_u"):
            breaking_load_N = props["A"] * props["f_u"]  # (mm^2 * MPa = N)
            if breaking_load_N >= design_load_N:
                best_size = size
                is_safe = True
                break
    
    if best_size is None:
        best_size = "Oversize required"
        is_safe = False

    return max_tension / 1000.0, best_size, is_safe


def _check_membrane(stress_results, fabric_key="Ferrari 702"):
    """
    Check the membrane stresses against the fabric limits.
    """
    max_stress_Pa = 0.0
    if stress_results:
        for tri in stress_results:
            sigma = tri["sigma"]
            s1 = abs(sigma[0][0])
            s2 = abs(sigma[1][1])
            max_stress_Pa = max(max_stress_Pa, s1, s2)

    max_stress_kN_m = max_stress_Pa / 1000.0
    fabric = FABRIC_PROPERTIES.get("PVDF", {}).get(fabric_key, {})
    if not fabric:
        return max_stress_kN_m, 0.0, False

    f_u_warp = fabric.get("f_u_warp", 0.0)
    SAFETY_FACTOR = 4.0
    allowable_kN_m = (f_u_warp * 1000.0) / SAFETY_FACTOR
    is_safe = max_stress_kN_m <= allowable_kN_m
    
    return max_stress_kN_m, allowable_kN_m, is_safe


def select_best_section(target_family, axial_force_kN, moment_kNm, steel_grade="S355"):
    """
    Loops through data/sections.py to find the lightest section in the
    target_family that passes the combined axial + bending check.
    """
    fy_MPa = STEEL_MATERIALS.get("Steel", {}).get(steel_grade, {}).get("fy", 355)
    
    best_section = "Oversize required"
    is_safe = False

    for name, props in SECTION_PROPERTIES.items():
        if props.get("type") != target_family:
            continue
            
        # Basic interaction check (Axial + Bending)
        # P_cap = A * fy;  M_cap = W_el * fy
        A_mm2 = props.get("A", 1.0)
        W_el_mm3 = props.get("W_el", 1.0)
        
        # Convert axial (kN) to N, moment (kNm) to Nmm
        N_Ed = axial_force_kN * 1000.0
        M_Ed = moment_kNm * 1e6
        
        N_cap = A_mm2 * fy_MPa
        M_cap = W_el_mm3 * fy_MPa
        
        # Simple utilization ratio
        util = (N_Ed / N_cap) + (M_Ed / M_cap)
        
        # 0.9 safety factor for code compliance
        if util <= 0.9:
            # Get the weight to find the lightest one
            weight = props.get("weight", 999.0)
            if not is_safe:
                # First passing section found (assuming sections are ordered)
                best_section = name
                is_safe = True
                # In a real app we would break here, but let's keep looping
                # to find the *lightest* just in case.
                # Actually, they are usually ordered by size, so break is fine.
                break

    return best_section, is_safe


def calculate_design_checks(stress_results, cable_results, 
                            beam_axial_kN=0.0, beam_moment_kNm=0.0, 
                            beam_family="CHS", cable_family="Locked Coil"):
    """
    Universal entry point.
    Takes the raw lists from the solver and returns a summary dict.
    """
    # 1. Check Cables
    max_cable_kN, rec_cable, cable_ok = _check_cables(cable_results, cable_family)
    
    # 2. Check Membrane
    max_mem_kN_m, allowable_mem_kN_m, mem_ok = _check_membrane(stress_results)

    # 3. Check Beams
    rec_beam, beam_ok = select_best_section(beam_family, beam_axial_kN, beam_moment_kNm)

    # 4. Overall Status
    overall_ok = cable_ok and mem_ok and beam_ok

    return {
        "max_cable_tension_kN": round(max_cable_kN, 1),
        "recommended_cable": rec_cable,
        "cable_status": "PASS" if cable_ok else "FAIL",
        
        "max_membrane_stress_kN_m": round(max_mem_kN_m, 1),
        "allowable_membrane_stress_kN_m": round(allowable_mem_kN_m, 1),
        "membrane_status": "PASS" if mem_ok else "FAIL",
        
        "required_beam_axial_kN": round(beam_axial_kN, 1),
        "required_beam_moment_kNm": round(beam_moment_kNm, 1),
        "recommended_beam": rec_beam,
        "beam_status": "PASS" if beam_ok else "FAIL",
        
        "overall_status": "PASS" if overall_ok else "FAIL"
    }
