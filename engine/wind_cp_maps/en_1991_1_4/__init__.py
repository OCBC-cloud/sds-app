"""SDSe — EN 1991-1-4 Cp map registry."""


def get_cp_map(shape_type):
    shape_type = shape_type.lower().strip()
    
    if shape_type == "flat":
        from engine.wind_cp_maps.en_1991_1_4.flat import compute_cp
        return compute_cp
    elif shape_type in ("dome", "curved_roof", "curved"):
        from engine.wind_cp_maps.en_1991_1_4.dome import compute_cp
        return compute_cp
    elif shape_type in ("multi_cone", "multi-cone", "multicone"):
        from engine.wind_cp_maps.en_1991_1_4.multi_cone import compute_cp
        return compute_cp
    elif shape_type in ("hypar", "hyperbolic_paraboloid", "saddle"):
        from engine.wind_cp_maps.en_1991_1_4.hypar import compute_cp
        return compute_cp
    else:
        raise ValueError("EN 1991-1-4 Cp map not implemented for shape: %s" % shape_type)
