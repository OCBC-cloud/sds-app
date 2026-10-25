"""SDSe — AS/NZS 1170.2 Cp map registry.

Base code for MS 1553 (Malaysia).
"""


def get_cp_map(shape_type):
    """Return the Cp mapper for the given shape."""
    shape_type = shape_type.lower().strip()
    
    if shape_type == "flat":
        from engine.wind_cp_maps.asnzs_1170_2.flat import compute_cp
        return compute_cp
    elif shape_type in ("dome", "curved_roof", "curved"):
        from engine.wind_cp_maps.asnzs_1170_2.dome import compute_cp
        return compute_cp
    elif shape_type in ("multi_cone", "multi-cone", "multicone"):
        from engine.wind_cp_maps.asnzs_1170_2.multi_cone import compute_cp
        return compute_cp
    elif shape_type in ("hypar", "hyperbolic_paraboloid", "saddle"):
        from engine.wind_cp_maps.asnzs_1170_2.hypar import compute_cp
        return compute_cp
    else:
        raise ValueError("AS/NZS 1170.2 Cp map not implemented for shape: %s" % shape_type)
