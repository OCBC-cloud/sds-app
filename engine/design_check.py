# =============================================================================
# SDSe - Universal Design Check Engine
# =============================================================================
# Reads the output of the nonlinear solver and performs code-based
# checks on cables and membrane. Recommends sections.
# =============================================================================

import math

try:
    from data.materials import CABLE_PROPERTIES, FABRIC_PROPERTIES
except ImportError:
    CABLE_PROPERTIES = {}
    FABRIC_PROPERTIES = {}


def _check_cables(cable_tensions, target_material="Locked Coil"):
    """
    Check the cable tensions against the specified material family.
    Returns (max_tension_N, recommended_size, is_safe).
    """
    max_tension = 0.0
    if cable_tensions:
        # Find the highest tension across all cables
        for cb in cable_tensions:
            if cb["T_N"] > max_tension:
                max_tension = cb["T_N"]

    # Look up the material family
    family = CABLE_PROPERTIES.get(target_material, {})
    if not family:
        return max_tension / 1000.0, "Unknown Family", False

    # Loop through sizes to find the lightest one that can take the load
    best_size = None
    is_safe = False
    
    # We need a safety factor (e.g., 2.0 for cables to prevent fatigue)
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
                break  # Because the dict is ordered smallest to largest
    
    if best_size is None:
        best_size = "Oversize required"
        is_safe = False

    return max_tension / 1000.0, best_size, is_safe


def _check_membrane(stress_results, fabric_key="Ferrari 702"):
    """
    Check the membrane stresses against the fabric limits.
    Returns (max_stress_kN_m, allowable_stress_kN_m, is_safe).
    """
    max_stress_Pa = 0.0
    if stress_results:
        for tri in stress_results:
            # The stress tensor is a 2x2 matrix
            sigma = tri["sigma"]
            # We look at the principal stresses
            s1 = abs(sigma[0][0])
            s2 = abs(sigma[1][1])
            max_stress_Pa = max(max_stress_Pa, s1, s2)

    # Convert Pa to kN/m
    max_stress_kN_m = max_stress_Pa / 1000.0

    fabric = FABRIC_PROPERTIES.get("PVDF", {}).get(fabric_key, {})
    if not fabric:
        return max_stress_kN_m, 0.0, False

    # Look up the ultimate tensile strength (N/mm)
    f_u_warp = fabric.get("f_u_warp", 0.0)
    
    # Code check: allowable stress is ultimate / safety factor
    SAFETY_FACTOR = 4.0  # Typical for architectural fabric
    allowable_kN_m = (f_u_warp * 1000.0) / SAFETY_FACTOR

    is_safe = max_stress_kN_m <= allowable_kN_m
    
    return max_stress_kN_m, allowable_kN_m, is_safe


def calculate_design_checks(stress_results, cable_results):
    """
    Universal entry point.
    Takes the raw lists from the solver and returns a summary dict.
    """
    # 1. Check Cables
    max_cable_kN, rec_cable, cable_ok = _check_cables(cable_results)
    
    # 2. Check Membrane
    max_mem_kN_m, allowable_mem_kN_m, mem_ok = _check_membrane(stress_results)

    # 3. Overall Status
    overall_ok = cable_ok and mem_ok

    return {
        "max_cable_tension_kN": round(max_cable_kN, 1),
        "recommended_cable": rec_cable,
        "cable_status": "PASS" if cable_ok else "FAIL",
        
        "max_membrane_stress_kN_m": round(max_mem_kN_m, 1),
        "allowable_membrane_stress_kN_m": round(allowable_mem_kN_m, 1),
        "membrane_status": "PASS" if mem_ok else "FAIL",
        
        "overall_status": "PASS" if overall_ok else "FAIL",
        "recommended_beam_family": "CHS" # Placeholder until beam forces are extracted
    }
