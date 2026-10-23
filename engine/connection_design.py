"""SDSe Engine - Connection Design.

Takes reaction forces from the eave anchors, calculates the overturning
moment due to the eave height, and sizes:
- Baseplate thickness
- Anchor bolt diameter, count, and embedment (J-Bolts)
- Concrete stump dimensions
- Concrete pad footing (resisting uplift and overturning)
- Fin plate thickness and weld size
"""

import math


def design_baseplate_and_foundation(reaction_N, eave_height_m=0.0, steel_fy_MPa=355, concrete_fc_MPa=25):
    """
    Designs baseplate, J-bolts, concrete stump, and pad footing.
    reaction_N: [Rx, Ry, Rz] in Newtons. Positive Rz is uplift.
    eave_height_m: The lever arm from the eave anchor to the ground.
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
            
    # 2. Overturning Moment (The Lever Arm)
    # The shear at the eave creates a moment at the base.
    Mx_Nm = Ry * eave_height_m  # Y-shear creates X-moment
    My_Nm = Rx * eave_height_m  # X-shear creates Y-moment
    M_total_Nm = math.sqrt(Mx_Nm**2 + My_Nm**2)
    
    # 3. Anchor Bolt Design (Uplift + Moment)
    uplift_N = max(0.0, Rz)
    shear_N = math.sqrt(Rx**2 + Ry**2)
    
    num_bolts = 4
    allowable_tension_MPa = 300.0
    allowable_shear_MPa = 180.0 
    
    # Moment causes additional tension on the "uplifted" side of the plate
    # Assume the bolt group lever arm is 0.6 * plate_side
    bolt_lever_arm_mm = plate_side_mm * 0.6
    moment_tension_N = M_total_Nm * 1000.0 / bolt_lever_arm_mm
    
    total_tension_N = uplift_N + moment_tension_N
    
    req_area_tension = (total_tension_N / num_bolts) / allowable_tension_MPa
    req_area_shear = (shear_N / num_bolts) / allowable_shear_MPa
    
    req_area_mm2 = max(req_area_tension, req_area_shear)
    
    bolt_sizes = [
        (12, 84.3, 250), 
        (16, 157.0, 350), 
        (20, 245.0, 450),
        (24, 353.0, 550), 
        (30, 561.0, 700),
        (36, 817.0, 850),
    ]
    
    bolt_d, bolt_A, bolt_embed = 36, 817.0, 850 
    for d, A, embed in bolt_sizes:
        if A >= req_area_mm2:
            bolt_d, bolt_A, bolt_embed = d, A, embed
            break

    # 4. Concrete Pull-out Cone Check (J-Bolt)
    bond_stress_MPa = 1.5
    cone_capacity_N = math.pi * bolt_d * bolt_embed * bond_stress_MPa
    if cone_capacity_N < (total_tension_N / num_bolts):
        bolt_embed = int((total_tension_N / num_bolts) / (math.pi * bolt_d * bond_stress_MPa))
        bolt_embed = math.ceil(bolt_embed / 50.0) * 50
        
    # 5. Baseplate Thickness (Combined Bending from Uplift, Shear, and Moment)
    bolt_spacing_mm = plate_side_mm * 0.6
    cantilever_mm = (plate_side_mm - bolt_spacing_mm) / 2.0
    
    moment_tension_plate = (total_tension_N / num_bolts) * cantilever_mm
    moment_shear_plate = (shear_N / (2 * num_bolts)) * cantilever_mm
    
    total_moment_plate = moment_tension_plate + moment_shear_plate
    
    if total_moment_plate < 1.0:
        plate_thickness_mm = 10.0 
    else:
        plate_thickness_mm = math.sqrt(6 * total_moment_plate / steel_fy_MPa)
        plate_thickness_mm = max(10.0, math.ceil(plate_thickness_mm / 2.0) * 2.0)
    
    # 6. Concrete Stump Dimensions
    stump_side_mm = max(plate_side_mm + 100.0, 300.0)
    
    # 7. Concrete Pad Footing (Resisting Uplift and Overturning)
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
    
    # Overturning check: The pad must be wide enough to resist the moment
    # Weight of pad + soil = M / lever_arm
    if M_total_Nm > 0:
        # Required pad width from overturning = sqrt(6 * M / (weight_per_m2))
        pad_width_overturn = math.sqrt(6 * M_total_Nm / weight_per_m2) if weight_per_m2 > 0 else 0.0
        pad_side_m = max(math.sqrt(pad_area_m2), pad_width_overturn, 1.5 * stump_side_m)
    else:
        pad_side_m = max(math.sqrt(pad_area_m2), 1.5 * stump_side_m)
        
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
        "overturning_moment_kNm": float(M_total_Nm / 1000.0),
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
