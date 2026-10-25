"""SDSe — Wind Cp Map Registry.

Returns the code-compliant pressure coefficient (Cp) mapper
for a given roof shape and design code.

Shapes: "flat", "dome", "multi_cone", "hypar", "saddle"
Codes:  "MS 1553", "EN 1991", "ASCE 7"

Each mapper implements:
    compute_cp(slope_deg, h_over_d, position, distance_from_apex=None)
    -> returns Cp (negative = suction/uplift)
"""


def get_cp_map(shape_type, code_name):
    """Return the Cp mapper for the given shape and code."""
    
    shape_type = shape_type.lower().strip()
    
    # Normalize code name
    if "1553" in code_name or "MS" in code_name or "AS/NZS" in code_name or "Australia" in code_name:
        code_family = "asnzs"
    elif "1991" in code_name or "Euro" in code_name or "EN" in code_name:
        code_family = "en"
    elif "ASCE" in code_name or "USA" in code_name:
        code_family = "asce"
    else:
        # Default to AS/NZS (MS 1553 base)
        code_family = "asnzs"
    
    if code_family == "asnzs":
        from engine.wind_cp_maps.asnzs_1170_2 import get_cp_map as get_asnzs
        return get_asnzs(shape_type)
    elif code_family == "en":
        from engine.wind_cp_maps.en_1991_1_4 import get_cp_map as get_en
        return get_en(shape_type)
    elif code_family == "asce":
        from engine.wind_cp_maps.asce_7 import get_cp_map as get_asce
        return get_asce(shape_type)
    else:
        raise ValueError("Unknown code: %s" % code_name)


def list_supported_shapes():
    """Return the list of shapes with Cp maps implemented."""
    return ["flat", "dome", "multi_cone", "hypar", "saddle"]


def list_supported_codes():
    """Return the list of codes with Cp maps implemented."""
    return ["MS 1553 (AS/NZS 1170.2)", "EN 1991-1-4", "ASCE 7"]
