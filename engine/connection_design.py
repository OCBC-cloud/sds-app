"""SDSe Engine - Connection Design.

Takes reaction forces and cable tensions from the solver and sizes:
- Baseplate thickness
- Anchor bolt diameter, count, and embedment (J-Bolts)
- Concrete stump dimensions
- Fin plate thickness and weld size
"""

import math


def design_baseplate_and_foundation(reaction_N, steel_fy_MPa=355, concrete_fc_MPa=25):
    """
    Designs baseplate, J-bolts, and concrete stump for a given support reaction.
    reaction_N: A 3-element list/tuple [Rx, Ry, Rz] in Newtons.
                Positive Rz is uplift (tension on bolts).
                Negative Rz is compression (bearing on concrete).
    Returns a dict with the design results.
    """
    Rx, Ry, Rz = reaction_N
    
    # 1. Baseplate Bearing Check (Compression)
    # If Rz is negative, the plate pushes on the concrete.
    # Allowable bearing stress = 0.6 * f'c
    allowable_bearing_MPa = 0.6 * concrete_fc_MPa
    compression_N = max(0.0, -Rz)
    
    # Assume a square plate with a 4x margin over the bolt group
    # We will iterate to find a reasonable plate size
    plate_side_mm = 150.0 # start at 150x150
    while (compression_N / (plate_side_mm * plate_side_mm)) > allowable_bearing_MPa:
        plate_side_mm += 10.0
        if plate_side_mm > 600:
            plate_side_mm = 600
            break
            
    # 2. Anchor Bolt Design (Uplift / Tension)
    uplift_N = max(0.0, Rz)
    shear_N = math.sqrt(Rx**2 + Ry**2)
    
    # Use 2 bolts for small uplift, 4 for larger uplift to distribute shear
    num_bolts = 2 if uplift_N < 5000 else 4
    
    # Bolt material (Grade 8.8: tensile strength 800 MPa, allowable ~ 300 MPa)
    allowable_bolt_stress_MPa = 300.0
    
    # Required bolt area per bolt
    req_area_mm2 = (uplift_N / num_bolts) / allowable_bolt_stress_MPa
    
    # Size the bolt (M12, M16, M20, M24)
    bolt_sizes = [
        (12, 84.3, 250),  # (diameter, area, embedment mm)
        (16, 157.0, 350),
        (20, 245.0, 450),
        (24, 353.0, 550),
        (30, 561.0, 700),
    ]
    
    bolt_d = 16
    bolt_A = 157.0
    bolt_embed = 350
    for d, A, embed in bolt_sizes:
        if A >= req_area_mm2:
            bolt_d = d
            bolt_A = A
            bolt_embed = embed
            break

    # 3. Concrete Pull-out Cone Check (J-Bolt)
    # Capacity of a J-bolt embedded in concrete = pi * d * L * tau
    # tau (bond stress) is roughly 1.5 MPa for ribbed bolts.
    bond_stress_MPa = 1.5
    cone_capacity_N = math.pi * bolt_d * bolt_embed * bond_stress_MPa
    if cone_capacity_N < (uplift_N / num_bolts):
        # Need longer embedment
        bolt_embed = int((uplift_N / num_bolts) / (math.pi * bolt_d * bond_stress_MPa))
        # round to nearest 50
        bolt_embed = math.ceil(bolt_embed / 50.0) * 50
        
    # 4. Baseplate Thickness
    # Cantilever length from bolt to edge = (plate_side_mm - bolt_spacing) / 2
    bolt_spacing_mm = plate_side_mm * 0.6
    cantilever_mm = (plate_side_mm - bolt_spacing_mm) / 2.0
    
    # Moment per mm width of plate = Uplift_per_bolt * cantilever
    moment_per_mm = (uplift_N / num_bolts) * cantilever_mm
    
    # Plate thickness = sqrt(6 * M / (fy * b))
    plate_thickness_mm = math.sqrt(6 * moment_per_mm / steel_fy_MPa)
    plate_thickness_mm = max(10.0, math.ceil(plate_thickness_mm / 2.0) * 2.0)
    
    # 5. Concrete Stump Dimensions
    # Stump must be large enough to contain the bolts and the plate
    stump_side_mm = max(plate_side_mm + 100.0, 300.0)
    
    return {
        "plate_side_mm": int(plate_side_mm),
        "plate_thickness_mm": int(plate_thickness_mm),
        "bolt_diameter_mm": int(bolt_d),
        "bolt_count": int(num_bolts),
        "bolt_embedment_mm": int(bolt_embed),
        "stump_side_mm": int(stump_side_mm),
        "bolt_type": "J-Bolt Grade 4.6",
        "concrete_grade": "C25/30 (25 MPa)",
    }


def design_fin_plate(cable_tension_N, cable_diameter_mm, steel_fy_MPa=355):
    """
    Designs the fin plate and weld to connect a cable to the ring.
    cable_tension_N: Max tension in the cable.
    cable_diameter_mm: The physical diameter of the cable (e.g., 6mm).
    """
    # Weld design: fillet weld, E70 electrode (allowable ~ 100 MPa)
    weld_strength_MPa = 100.0
    # Weld length assumed as 2 sides of the plate
    plate_thickness_mm = 10.0 # start
    weld_length = 2 * plate_thickness_mm # two fillet welds
    
    # Weld throat = 0.707 * weld_size
    # Weld capacity = throat * length * strength
    # Solve for weld size
    weld_size_mm = cable_tension_N / (0.707 * weld_length * weld_strength_MPa)
    weld_size_mm = max(5.0, math.ceil(weld_size_mm)) # minimum 5mm fillet
    
    # Fin plate thickness (bearing of cable on plate)
    # Simplified: thickness = tension / (2 * cable_diameter * fy)
    plate_thickness_mm = cable_tension_N / (2 * cable_diameter_mm * steel_fy_MPa)
    plate_thickness_mm = max(10.0, math.ceil(plate_thickness_mm / 2.0) * 2.0)
    
    return {
        "fin_plate_thickness_mm": int(plate_thickness_mm),
        "weld_size_mm": int(weld_size_mm),
        "weld_length_mm": int(weld_length),
        "cable_diameter_mm": int(cable_diameter_mm),
    }
