"""SDSe Engine - Connection Design.

Takes reaction forces from the eave anchors, calculates the overturning
moment due to the eave height, and sizes:
- Baseplate dimensions (B x N x t) using the auto-sized column footprint
- Anchor bolt diameter, count, and embedment (J-Bolts)
- Concrete stump dimensions
- Concrete pad footing (resisting uplift, bearing, and overturning)
- Fin plate (corner plate) for cable connections, checked at ultimate.

All calculations are to ultimate limit state (ULS).
"""

import math

from data.sections import SECTION_PROPERTIES
from data.materials import STEEL_MATERIALS


def _lookup_column_diameter(column_section):
    """Look up the outer diameter of the auto-sized steel section."""
    props = SECTION_PROPERTIES.get(column_section, {})
    if "d" in props:
        return float(props["d"])
    return 200.0


def design_baseplate_and_foundation(reaction_N, column_section, eave_height_m=0.0,
                                     steel_fy_MPa=355, concrete_fc_MPa=25,
                                     bolt_grade=8.8):
    """
    Designs baseplate, J-bolts, concrete stump, and pad footing to ULS.
    reaction_N: [Rx, Ry, Rz] in Newtons. Positive Rz is uplift.
    """
    Rx, Ry, Rz = reaction_N
    d_col_mm = _lookup_column_diameter(column_section)

    Mx_Nm = Ry * eave_height_m
    My_Nm = Rx * eave_height_m
    M_total_Nmm = math.sqrt(Mx_Nm**2 + My_Nm**2) * 1000.0
    shear_N = math.sqrt(Rx**2 + Ry**2)

    # Grade 8.8 ultimate strength
    fu_bolt_MPa = 800.0
    # ULS design stress (0.6 is a common reduction for combined tension-shear)
    allowable_tension_MPa = 0.6 * fu_bolt_MPa
    allowable_shear_MPa = 0.4 * fu_bolt_MPa
    num_bolts = 4

    B_mm = max(d_col_mm + 100.0, 200.0)
    N_mm = B_mm

    bolt_d_mm = 16.0
    bolt_edge_mm = 1.5 * bolt_d_mm

    for _iteration in range(20):
        z_mm = B_mm - bolt_edge_mm
        T_bolts_N = (M_total_Nmm / z_mm) - (Rz / 2.0)
        T_bolts_N = max(0.0, T_bolts_N)

        req_area_tension = (T_bolts_N / num_bolts) / allowable_tension_MPa
        req_area_shear = (shear_N / num_bolts) / allowable_shear_MPa
        req_area_mm2 = max(req_area_tension, req_area_shear, 84.3)

        bolt_sizes = [
            (12, 84.3, 250), (16, 157.0, 350), (20, 245.0, 450),
            (24, 353.0, 550), (30, 561.0, 700), (36, 817.0, 850),
        ]
        new_bolt_d, bolt_A, bolt_embed = 36, 817.0, 850
        for d, A, embed in bolt_sizes:
            if A >= req_area_mm2:
                new_bolt_d, bolt_A, bolt_embed = d, A, embed
                break

        allowable_bearing_MPa = 0.6 * concrete_fc_MPa
        B_m = B_mm / 1000.0
        N_m = N_mm / 1000.0
        axial_MPa = abs(Rz) / (B_m * N_m * 1e6) if B_m * N_m > 0 else 0.0
        moment_MPa = 6.0 * M_total_Nmm / (B_mm * N_mm * N_mm) if N_mm > 0 else 0.0
        peak_pressure_MPa = axial_MPa + moment_MPa

        if peak_pressure_MPa <= allowable_bearing_MPa:
            if new_bolt_d == bolt_d_mm:
                break
        else:
            B_mm += 25.0
            N_mm += 25.0

        bolt_d_mm = new_bolt_d
        bolt_edge_mm = 1.5 * bolt_d_mm

    z_mm = B_mm - bolt_edge_mm
    T_bolts_N = max(0.0, (M_total_Nmm / z_mm) - (Rz / 2.0))

    c_mm = max((B_mm - d_col_mm) / 2.0 - bolt_edge_mm, 10.0)
    moment_per_bolt_Nmm = (T_bolts_N / num_bolts) * c_mm
    moment_per_bolt_Nmm += (shear_N / (2 * num_bolts)) * c_mm

    if moment_per_bolt_Nmm < 1.0:
        plate_thickness_mm = 12.0
    else:
        plate_thickness_mm = math.sqrt(6.0 * moment_per_bolt_Nmm / steel_fy_MPa)
        plate_thickness_mm = max(12.0, math.ceil(plate_thickness_mm / 2.0) * 2.0)

    bond_stress_MPa = 1.5
    if T_bolts_N > 0:
        cone_capacity_N = math.pi * bolt_d_mm * bolt_embed * bond_stress_MPa
        if cone_capacity_N < (T_bolts_N / num_bolts):
            bolt_embed = int((T_bolts_N / num_bolts) / (math.pi * bolt_d_mm * bond_stress_MPa))
            bolt_embed = math.ceil(bolt_embed / 50.0) * 50
    bolt_embed = max(bolt_embed, 250)

    stump_side_mm = max(B_mm + 100.0, 300.0)

    footing_thickness_m = 0.3
    soil_depth_m = 0.5
    rho_concrete = 2400
    rho_soil = 1800
    g = 9.81

    uplift_N = max(0.0, Rz)
    req_resist_N = uplift_N * 1.5
    stump_side_m = stump_side_mm / 1000.0
    stump_weight_N = (stump_side_m**2) * 1.0 * rho_concrete * g
    pad_req_N = max(0.0, req_resist_N - stump_weight_N)
    weight_per_m2 = (footing_thickness_m * rho_concrete * g) + (soil_depth_m * rho_soil * g)
    pad_area_m2 = pad_req_N / weight_per_m2 if weight_per_m2 > 0 else 0.0

    if M_total_Nmm > 0:
        pad_width_overturn = math.sqrt(6.0 * M_total_Nmm / (weight_per_m2 * 1e9)) if weight_per_m2 > 0 else 0.0
        pad_side_m = max(math.sqrt(pad_area_m2), pad_width_overturn, 1.5 * stump_side_m)
    else:
        pad_side_m = max(math.sqrt(pad_area_m2), 1.5 * stump_side_m)

    pad_side_mm = math.ceil(pad_side_m * 1000.0 / 50.0) * 50

    return {
        "plate_side_mm": int(B_mm),
        "plate_thickness_mm": int(plate_thickness_mm),
        "bolt_diameter_mm": int(bolt_d_mm),
        "bolt_count": int(num_bolts),
        "bolt_embedment_mm": int(bolt_embed),
        "stump_side_mm": int(stump_side_mm),
        "pad_side_mm": int(pad_side_mm),
        "pad_thickness_mm": int(footing_thickness_m * 1000),
        "overturning_moment_kNm": float(M_total_Nmm / 1e6),
        "bolt_tension_kN": float(T_bolts_N / 1000.0),
        "column_diameter_mm": int(d_col_mm),
        "bolt_type": "J-Bolt Grade 8.8",
        "concrete_grade": "C25/30 (25 MPa)",
    }


def design_corner_plate(cable_tension_N, cable_diameter_mm, steel_fy_MPa=355):
    """
    Designs the corner fin plate (gusset) that transfers the cable tension
    to the ring beam, checked at ULS for:
    - Weld capacity (fillet weld)
    - Bearing on the pin hole
    - Tear-out of the pin hole
    - Net-section rupture of the plate
    - Pin shear
    
    Returns a dict with plate thickness, weld size, pin diameter, utilizations,
    and the governing mode (which constraint set the final plate thickness).
    """
    # Ultimate strengths
    fu_steel_MPa = 1.2 * steel_fy_MPa   # ULS rupture
    fu_weld_MPa = 480.0                  # E70 electrode ULS
    fu_pin_MPa = 800.0                   # Grade 8.8 pin

    # Design factor for the whole connection
    design_factor = 1.0  # ULS already factored in the cable tension
    
    T_design_N = cable_tension_N * design_factor

    # ---------------- Weld ----------------
    plate_length_mm = max(100.0, 4.0 * cable_diameter_mm)
    weld_throat_factor = 0.707
    weld_area_mm2 = 2 * weld_throat_factor * plate_length_mm  # per mm of weld size
    weld_size_mm = T_design_N / (weld_area_mm2 * fu_weld_MPa)
    weld_size_mm = max(5.0, math.ceil(weld_size_mm))

    # ---------------- Pin bearing ----------------
    plate_thickness_bearing = T_design_N / (cable_diameter_mm * fu_steel_MPa)

    # ---------------- Tear-out ----------------
    edge_distance_mm = max(2.0 * cable_diameter_mm, 40.0)
    tearout_capacity_N = 2 * plate_thickness_bearing * edge_distance_mm * fu_steel_MPa / 2.0
    plate_thickness_tearout = T_design_N / (2 * edge_distance_mm * fu_steel_MPa)

    # ---------------- Net section rupture ----------------
    plate_width_mm = max(80.0, 3.0 * cable_diameter_mm)
    net_width_mm = plate_width_mm - cable_diameter_mm
    plate_thickness_net = T_design_N / (net_width_mm * fu_steel_MPa)

    # ---------------- Pin shear ----------------
    pin_area_req_mm2 = T_design_N / (fu_pin_MPa * 0.6)  # 0.6 is the ULS shear factor
    pin_d_mm = math.sqrt(4.0 * pin_area_req_mm2 / math.pi)
    pin_d_mm = max(cable_diameter_mm, math.ceil(pin_d_mm))

    # ---------------- Final plate thickness ----------------
    raw_required_thickness = max(
        plate_thickness_bearing,
        plate_thickness_tearout,
        plate_thickness_net,
    )
    plate_thickness_mm = max(raw_required_thickness, 10.0)
    plate_thickness_mm = math.ceil(plate_thickness_mm)

    # ---------------- Utilizations ----------------
    weld_util = T_design_N / (weld_area_mm2 * weld_size_mm * fu_weld_MPa)
    pin_shear_capacity_N = math.pi * (pin_d_mm / 2.0)**2 * fu_pin_MPa * 0.6
    pin_util = T_design_N / pin_shear_capacity_N

    # ---------------- Governing mode ----------------
    # Determine which constraint set the final plate thickness.
    # Order of precedence:
    # 1. MINIMUM     — plate is at the 10mm fabrication minimum
    # 2. CABLE_DIAMETER — pin is at cable diameter (force is small)
    # 3. STRENGTH    — plate thickness is governed by net-section (or bearing/tearout)
    # 4. WELD_SIZE   — plate is thin but weld requires a thick plate (rare)
    if raw_required_thickness < 10.0:
        governing_mode = "MINIMUM"
    elif pin_d_mm <= cable_diameter_mm:
        governing_mode = "CABLE_DIAMETER"
    elif raw_required_thickness == plate_thickness_net:
        governing_mode = "STRENGTH"
    else:
        governing_mode = "WELD_SIZE"

    return {
        "plate_thickness_mm": int(plate_thickness_mm),
        "plate_length_mm": int(plate_length_mm),
        "plate_width_mm": int(plate_width_mm),
        "weld_size_mm": int(weld_size_mm),
        "weld_length_mm": int(plate_length_mm),
        "pin_diameter_mm": int(pin_d_mm),
        "edge_distance_mm": int(edge_distance_mm),
        "weld_utilization": float(weld_util),
        "pin_utilization": float(pin_util),
        "governing_mode": governing_mode,
    }
