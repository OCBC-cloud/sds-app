"""SDSe Engine - Connection Design.

Takes reaction forces from the eave anchors, calculates the overturning
moment due to the eave height, and sizes:
- Baseplate dimensions (B x N x t) using the auto-sized column footprint
- Anchor bolt diameter, count, and embedment (J-Bolts)
- Concrete stump dimensions
- Concrete pad footing (resisting uplift, bearing, and overturning)
- Fin plate thickness and weld size

The baseplate is designed as a real moment-resisting baseplate:
- The bolts are placed at the edges to maximize the lever arm.
- The plate gets wider under moment (to resist concrete bearing).
- The plate thickness is driven by the cantilever from the bolt to the column.
"""

import math

from data.sections import SECTION_PROPERTIES
from data.materials import STEEL_MATERIALS


def _lookup_column_diameter(column_section):
    """Look up the outer diameter of the auto-sized steel section."""
    props = SECTION_PROPERTIES.get(column_section, {})
    if "d" in props:
        return float(props["d"])
    # Fallback for unknown section
    return 200.0


def design_baseplate_and_foundation(reaction_N, column_section, eave_height_m=0.0,
                                     steel_fy_MPa=355, concrete_fc_MPa=25,
                                     bolt_grade=8.8):
    """
    Designs baseplate, J-bolts, concrete stump, and pad footing.
    reaction_N: [Rx, Ry, Rz] in Newtons. Positive Rz is uplift.
    column_section: the CHS section string (e.g., "CHS 273.0x10.0")
    eave_height_m: the lever arm from the eave anchor to the ground.
    """
    Rx, Ry, Rz = reaction_N
    d_col_mm = _lookup_column_diameter(column_section)

    # Overturning moment from the eave lever arm
    Mx_Nm = Ry * eave_height_m
    My_Nm = Rx * eave_height_m
    M_total_Nmm = math.sqrt(Mx_Nm**2 + My_Nm**2) * 1000.0
    shear_N = math.sqrt(Rx**2 + Ry**2)

    # Bolt material properties
    fy_bolt_MPa = 800.0 * (bolt_grade / 8.8)  # Grade 8.8 = 800 MPa ultimate
    allowable_tension_MPa = 0.6 * fy_bolt_MPa
    allowable_shear_MPa = 0.4 * fy_bolt_MPa
    num_bolts = 4

    # ---------------- Step 1: Plate width from bolt layout ----------------
    # Start with a plate that gives edge distance of 1.5 * bolt_d
    # We iterate because the bolt diameter depends on the moment, which depends on B.
    B_mm = max(d_col_mm + 100.0, 200.0)
    N_mm = B_mm  # square plate for simplicity

    bolt_d_mm = 16.0
    bolt_edge_mm = 1.5 * bolt_d_mm

    for _iteration in range(20):
        # Total bolt tension from the moment
        z_mm = B_mm - bolt_edge_mm  # lever arm from tension bolt to compression toe
        T_bolts_N = (M_total_Nmm / z_mm) - (Rz / 2.0)
        T_bolts_N = max(0.0, T_bolts_N)

        # Required bolt area
        req_area_tension = (T_bolts_N / num_bolts) / allowable_tension_MPa
        req_area_shear = (shear_N / num_bolts) / allowable_shear_MPa
        req_area_mm2 = max(req_area_tension, req_area_shear, 84.3)  # M12 minimum

        # Choose bolt size
        bolt_sizes = [
            (12, 84.3, 250), (16, 157.0, 350), (20, 245.0, 450),
            (24, 353.0, 550), (30, 561.0, 700), (36, 817.0, 850),
        ]
        new_bolt_d, bolt_A, bolt_embed = 36, 817.0, 850
        for d, A, embed in bolt_sizes:
            if A >= req_area_mm2:
                new_bolt_d, bolt_A, bolt_embed = d, A, embed
                break

        # Check if the plate needs to grow for concrete bearing
        # Peak pressure = axial/B^2 + 6M/B^3 (at the compression edge)
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

    # ---------------- Step 2: Final bolt tension ----------------
    z_mm = B_mm - bolt_edge_mm
    T_bolts_N = max(0.0, (M_total_Nmm / z_mm) - (Rz / 2.0))

    # ---------------- Step 3: Plate thickness ----------------
    # Cantilever from bolt line to column face
    c_mm = max((B_mm - d_col_mm) / 2.0 - bolt_edge_mm, 10.0)
    moment_per_bolt_Nmm = (T_bolts_N / num_bolts) * c_mm
    # Plus shear moment
    moment_per_bolt_Nmm += (shear_N / (2 * num_bolts)) * c_mm

    if moment_per_bolt_Nmm < 1.0:
        plate_thickness_mm = 12.0
    else:
        plate_thickness_mm = math.sqrt(6.0 * moment_per_bolt_Nmm / steel_fy_MPa)
        plate_thickness_mm = max(12.0, math.ceil(plate_thickness_mm / 2.0) * 2.0)

    # ---------------- Step 4: Bolt embedment (pull-out) ----------------
    bond_stress_MPa = 1.5
    if T_bolts_N > 0:
        cone_capacity_N = math.pi * bolt_d_mm * bolt_embed * bond_stress_MPa
        if cone_capacity_N < (T_bolts_N / num_bolts):
            bolt_embed = int((T_bolts_N / num_bolts) / (math.pi * bolt_d_mm * bond_stress_MPa))
            bolt_embed = math.ceil(bolt_embed / 50.0) * 50
    bolt_embed = max(bolt_embed, 250)

    # ---------------- Step 5: Concrete stump ----------------
    stump_side_mm = max(B_mm + 100.0, 300.0)

    # ---------------- Step 6: Pad footing ----------------
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

    # Overturning check
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
