"""SDSe — ASCE 7 Cp map registry."""


def get_cp_map(shape_type):
    shape_type = shape_type.lower().strip()
    
    if shape_type == "flat":
        from engine.wind_cp_maps.asce_7.flat import compute_cp
        return compute_cp
    elif shape_type in ("dome", "curved_roof", "curved"):
        from engine.wind_cp_maps.asce_7.dome import compute_cp
        return compute_cp
    elif shape_type in ("multi_cone", "multi-cone", "multicone"):
        from engine.wind_cp_maps.asce_7.multi_cone import compute_cp
        return compute_cp
    elif shape_type in ("hypar", "hyperbolic_paraboloid", "saddle"):
        from engine.wind_cp_maps.asce_7.hypar import compute_cp
        return compute_cp
    else:
        raise ValueError("ASCE 7 Cp map not implemented for shape: %s" % shape_type)
