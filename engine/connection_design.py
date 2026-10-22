"""SDSe Engine - Connection Design.

Takes reaction forces and cable tensions from the solver and sizes:
- Baseplate thickness
- Anchor bolt diameter, count, and embedment (J-Bolts) checking
  both tension and shear.
- Concrete stump dimensions
- Concrete pad footing (resisting uplift)
- Fin plate thickness and weld size
"""

import math


def design_baseplate_and_foundation(reaction_N, steel_fy_MPa=355, concrete_fc_MPa=25):
    """
    Designs baseplate, J-bolts, concrete stump, and pad footing.
    reaction_N: [Rx, Ry, Rz] in Newtons. Positive Rz is uplift.
    """
    Rx, Ry, Rz = reaction_N
    
    # 1. Baseplate Bearing Check (Compression)
    allowable_bearing_MPa = 0.6 * concrete_fc_MPa
    compression_N = max(0.0, -Rz)
    
    plate_side_mm = 150.0
    while (compression_N / (plate_side_mm * plate_side_mm)) > allowable_bearing_MPa:
        plate_side_mm += 10.0
        if plate_side_mm > 600:
            plate_side_mm = 600
            break
            
    # 2. Anchor Bolt Design (Uplift / Tension and Shear)
    uplift_N = max(0.0, Rz)
    shear_N = math.sqrt(Rx**2 + Ry**2)
    
    # Use 4 bolts for any significant load to resist shear in any direction
    num_bolts = 4
    
    # Allowable stresses for Grade 8.8 bolts (MPa)
    allowable_tension_MPa = 300.0
    allowable_shear_MPa = 180.0 # roughly 0.6 * tension
    
    # Required area per bolt for tension and shear
    req_area_tension = (uplift_N / num_bolts) / allowable_tension_MPa
    req_area_shear = (shear_N / num_bolts) / allowable_shear_MPa
    
    # Take the larger of the two requirements
    req_area_mm2 = max(req_area_tension, req_area_shear)
    
    # Bolt sizes: (diameter, area, embedment)
    bolt_sizes = [
        (12, 84.3, 250), 
        (16, 157.0, 350), 
        (20, 245.0, 450),
        (24, 353.0, 550), 
        (30, 561.0, 700),
        (36, 817.0, 850),
    ]
    
    bolt_d, bolt_A, bolt_embed = 24, 353.0, 550 # Default to M24 if loads are crazy high
    for d, A, embed in bolt_sizes:
        if A >= req_area_mm2:
            bolt_d, bolt_A, bolt_embed = d, A, embed
            break

    # 3. Concrete Pull-out Cone Check (J-Bolt)
    bond_stress_MPa = 1.5
    cone_capacity_N = math.pi * bolt_d * bolt_embed * bond_stress_MPa
    if cone_capacity_N < (uplift_N / num_bolts):
        bolt_embed = int((uplift_N / num_bolts) / (math.pi * bolt_d * bond_stress_MPa))
        bolt_embed = math.ceil(bolt_embed / 50.0) * 50
        
    # 4. Baseplate Thickness
    bolt_spacing_mm = plate_side_mm * 0.6
    cantilever_mm = (plate_side_mm - bolt_spacing_mm) / 2.0
    
    # If there is no uplift, base thickness on shear prying or min thickness
    if uplift_N < 1000:
        plate_thickness_mm = 10.0
    else:
        moment_per_mm = (uplift_N / num_bolts) * cantilever_mm
        plate_thickness_mm = math.sqrt(6 * moment_per_mm / steel_fy_MPa)
        plate_thickness_mm = max(10.0, math.ceil(plate_thickness_mm / 2.0) * 2.0)
    
    # 5. Concrete Stump Dimensions
    stump_side_mm = max(plate_side_mm + 100.0, 300.0)
    
    # 6. Concrete Pad Footing (Resisting Uplift)
    footing_thickness_m = 0.3
    soil_depth_m = 0.5
    rho_concrete = 2400
    rho_soil = 1800
    g = 9.81
    
    req_resist_N = uplift_N * 1.5
    
    stump_side_m = stump_side_mm / 1000.0
    stump_weight_N = (stump_side_m**2) * 1.0 * rho_concrete * g
    
    pad_req_N = max(0.0, req_resist_N - stump_weight_N)
    weight_per_m2 = (footing_thickness_m * rho_concrete * g) + (soil_depth_m * rho_soil * g)
    
    pad_area_m2 = pad_req_N / weight_per_m2 if weight_per_m2 > 0 else 0.0
    min_pad_area = (1.5 * stump_side_m)**2
    pad_area_m2 = max(pad_area_m2, min_pad_area)
    
    pad_side_m = math.sqrt(pad_area_m2)
    pad_side_mm = math.ceil(pad_side_m * 1000.0 / 50.0) * 50
    
    return {
        "plate_side_mm": int(plate_side_mm),
        "plate_thickness_mm": int(plate_thickness_mm),
        "bolt_diameter_mm": int(bolt_d),
        "bolt_count": int(num_bolts),
        "bolt_embedment_mm": int(bolt_embed),
        "stump_side_mm": int(stump_side_mm),
        "pad_side_mm": int(pad_side_mm),
        "pad_thickness_mm": int(footing_thickness_m * 1000),
        "bolt_type": "J-Bolt Grade 8.8",
        "concrete_grade": "C25/30 (25 MPa)",
    }


def design_fin_plate(cable_tension_N, cable_diameter_mm, steel_fy_MPa=355):
    """Designs the fin plate and weld to connect a cable to the ring."""
    weld_strength_MPa = 100.0
    plate_thickness_mm = 10.0
    weld_length = 2 * plate_thickness_mm
    
    weld_size_mm = cable_tension_N / (0.707 * weld_length * weld_strength_MPa)
    weld_size_mm = max(5.0, math.ceil(weld_size_mm))
    
    plate_thickness_mm = cable_tension_N / (2 * cable_diameter_mm * steel_fy_MPa)
    plate_thickness_mm = max(10.0, math.ceil(plate_thickness_mm / 2.0) * 2.0)
    
    return {
        "fin_plate_thickness_mm": int(plate_thickness_mm),
        "weld_size_mm": int(weld_size_mm),
        "weld_length_mm": int(weld_length),
        "cable_diameter_mm": int(cable_diameter_mm),
    }
