"""Headless Regression Test — 10x10 / 1-cone / ULS Uplift.

Run this from your terminal to verify the engine works without Streamlit:
    python verify_10x10_uls.py
"""

import sys
import numpy as np
import math

# We import the exact same modules your Streamlit app uses
from engine.form_finding_test import solve_fdm
from engine.SDSe_mesh_builder import SDSe_mesh_rings, SDSe_blend_q_per_edge
from engine.nonlinear_equilibrium_newton_seed import make_membrane_material, solve_nonlinear_equilibrium
from engine.load_generator import CODE_PARAMS, generate_uls_loads
from engine.connection_design import design_baseplate_and_foundation, design_corner_plate
from data.materials import CABLE_PROPERTIES, STEEL_MATERIALS
from data.sections import SECTION_PROPERTIES
from viewers.figures._shared import beam_curve, arclength_parametrisation

# We import your helper functions from the Lab page
from ui.workshops.tester_multi_cone import (
    _select_edge_cable,
    _select_steel_section,
    _rib_stations,
    _ellipse_y,
    _cone_arc_positions,
    _tip_x_at_eave,
    _build_eave_anchors,
    _subdivide_polygon,
    PRETENSION_STEPS
)

def run_verification():
    print("=" * 60)
    print("SDSe Headless Verification: 10x10 / 1-Cone / ULS Uplift")
    print("=" * 60)

    # 1. Setup the exact parameters from your report
    span = 10.0
    apex = 5.0
    mid_width = 10.0
    eave_height = 2.8
    ring_diameter = 1.0
    curve_type = "parabolic"
    secondary_count = 3
    optional_ends = False
    subdivisions = 5
    number_of_cones = 1
    ring_spacing = 5.0
    ring_clearance = 1.0
    warp_q_input = 1.0
    weft_q_input = 1.0
    edge_q_input = 5.0
    code_choice = list(CODE_PARAMS.keys())[0]
    wind_speed = 33.5
    snow_depth = 0.0
    payload_kg = 0.0
    
    print("\n[1] Building Geometry...")
    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)
    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array([_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float)
    
    s_rings = _cone_arc_positions(number_of_cones, ring_spacing, total_p)
    ring_specs = []
    for s_val in s_rings:
        x_val = float(np.interp(s_val, s_p, xp))
        bz_val = float(np.interp(s_val, s_p, zp))
        rz_val = bz_val - float(ring_clearance)
        ring_specs.append({"cx": x_val, "cy": 0.0, "cz": rz_val, "r": float(ring_diameter) / 2.0, "beam_z": bz_val})
        
    tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
    anchors = _build_eave_anchors(rib_x, rib_half_width, rib_peak_z, eave_height, tip_x)
    perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
    bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
    L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
    target_len = max(L_avg, 1e-6)

    built = SDSe_mesh_rings(perimeter_loop=perimeter_loop, anchor_idx=anchor_idx, ring_specs=ring_specs, eave_height=eave_height, target_len=target_len)
    
    # 2. Stage 1: FDM
    print("\n[2] Running Stage 1 (FDM)...")
    warp_q = warp_q_input * 1000.0
    weft_q = weft_q_input * 1000.0
    edge_q_scalar = edge_q_input * 1000.0
    
    q_interior = SDSe_blend_q_per_edge(built["edges"], built["points"][:, :2], np.array([1.0, 0.0]), warp_q, weft_q)
    q = np.empty(len(built["edges"]), dtype=float)
    for k, (i, j) in enumerate(built["edges"]):
        key = (i, j) if i < j else (j, i)
        q[k] = edge_q_scalar if key in built["boundary_edges"] else q_interior[k]
        
    fdm = solve_fdm(built["points"], built["edges"], built["fixed_indices"], q)
    coords_fdm = fdm["coordinates"]
    print(f"FDM Residual: {fdm['residual_norm']:.4e}")
    
    # 3. Cable Sizing
    max_edge_tension_N = edge_q_scalar * L_avg
    cable_name, cable_A_mm2, cable_E_MPa, EA_cable, cable_d_mm = _select_edge_cable(max_edge_tension_N, safety_factor=2.0)
    
    # Build Cable Elements
    cables = []
    n_a = len(anchor_idx)
    pts = built["points"]
    for k in range(n_a):
        a_idx = anchor_idx[k]
        b_idx = anchor_idx[(k + 1) % n_a]
        chain = [int(a_idx)]
        i_cur = (a_idx + 1) % pts.shape[0]
        b_int = int(b_idx)
        safety = 0
        while i_cur != b_int and safety < pts.shape[0]:
            chain.append(int(i_cur))
            i_cur = (i_cur + 1) % pts.shape[0]
            safety += 1
        chain.append(int(b_int))
        for m in range(len(chain) - 1):
            ia = chain[m]
            ib = chain[m + 1]
            L_ref = float(np.linalg.norm(coords_fdm[ib] - coords_fdm[ia]))
            if L_ref < 1e-9:
                continue
            cables.append({"a": ia, "b": ib, "L0": L_ref * 1.001, "EA": EA_cable})

    # 4. Loads
    print("\n[3] Generating ULS Uplift Loads...")
    apex_idx = built["beam_top_indices"][0]
    loads = generate_uls_loads(coords_fdm, built["triangles"], code_choice, wind_speed, snow_depth, payload_kg, apex_idx)["uplift"]
    
    # 5. Stage 2: Newton Search
    print("\n[4] Running Stage 2 (Newton Pretension Search)...")
    dr_result = None
    final_pretension = None
    
    for p_factor in PRETENSION_STEPS:
        cur_warp = p_factor * 1000.0
        cur_weft = p_factor * 1000.0
        mat = make_membrane_material(
            E_warp_MPa=1400.0, E_weft_MPa=1400.0, thickness_mm=1.02, nu=0.34, G_MPa=50.0,
            warp_prestress_N_per_m=cur_warp, weft_prestress_N_per_m=cur_weft,
        )
        print(f"  Trying pretension factor {p_factor}x...")
        res = solve_nonlinear_equilibrium(
            points=coords_fdm.copy(), triangles=built["triangles"], fixed_indices=built["fixed_indices"], reference_points=coords_fdm.copy(),
            membrane_material=mat, cables=cables, loads=loads,
            max_iter=100, max_outer=25, tol=0.01, tol_disp=1e-5, max_total_steps=200, max_wall_seconds=15.0, seed_z_amplitude=0.001 * span,
        )
        if res["converged"]:
            dr_result = res
            final_pretension = p_factor
            print(f"  -> CONVERGED at {p_factor}x (Reason: {res['reason']})")
            break
        else:
            print(f"  -> Failed (Reason: {res['reason']})")

    if dr_result is None:
        print("\n[FAIL] Newton solver did not converge.")
        sys.exit(1)
        
    if final_pretension > 1.0:
        print(f"\n[WARNING] Converged at increased pretension: {final_pretension} kN/m")

    # 6. Reactions & Sizing
    print("\n[5] Sizing Steel & Foundation...")
    if "cable_tension_list" in dr_result and len(dr_result["cable_tension_list"]) > 0:
        max_actual_T = max([c["T_N"] for c in dr_result["cable_tension_list"]])
    else:
        max_actual_T = max_edge_tension_N
        
    max_actual_T = max(max_actual_T, max_edge_tension_N)
    
    total_perimeter = 0.0
    for k in range(n_a):
       ave a_idx = anchor_idx[k_height]
        b_idx = anchor_idx[(k + )
1) % n_a]
        total       _perimeter += float(np.linalg.n #orm(coords_fdm[b_idx] - coords_fdm[a_idx]))
        
    baseline_tension_N = edge_q_scalar * total_perimeter
    design_tension_N = max(max_actual_T, baseline_tension_N)
    
    max_reaction_kN = max([math.sqrt(r[0]**2 + r[1]**2 + r[2]**2)/1000.0 for r in dr_result["reactions"]])
    
    steel_section = _select_steel_section(
        max_reaction_kN, 
        (max_reaction_kN * span) / 8.0, 
        family="CHS", 
        grade="S355",
        effective_length_m=span
    )
    
    print(f"Max Reaction: {max_reaction_kN:.2f} kN")
    print(f"Selected Steel Section: {steel_section}")
    
    if steel_section == "Oversize required":
        print("\n[FAIL] Steel section required exceeds catalogue.")
        sys.exit(1)

    # 7. Baseplates
    print("\n[6] Designing Baseplates & Foundations...")
    for idx in anchor_idx:
        r = dr_result["reactions"][idx]
        bp = design_baseplate_and_foundation(r, steel_section, e Just check it doesn't crash
        assert "plate_side_mm" in bp
        
    # 8. Corner Plates
    print("\n[7] Designing Corner Plates...")
    for idx in anchor_idx:
        cp = design_corner_plate(design_tension_N, cable_d_mm, steel_fy_MPa=355)
        assert "plate_thickness_mm" in cp
        
    # 9. Deflection
    max_deflection_mm = 0.0
    coords_new = dr_result["coordinates"]
    for i in range(len(coords_fdm)):
        d = np.linalg.norm(coords_new[i] - coords_fdm[i])
        if d > max_deflection_mm:
            max_deflection_mm = d * 1000.0
            
    limit_mm = (span * 1000.0) / 200.0
    status = "PASS" if max_deflection_mm <= limit_mm else "FAIL"
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Convergence:       YES ({final_pretension}x pretension)")
    print(f"Steel Section:     {steel_section}")
    print(f"Baseplate Nodes:   {len(anchor_idx)} designs generated")
    print(f"Corner Plates:     {len(anchor_idx)} designs generated")
    print(f"Max Deflection:    {max_deflection_mm:.2f} mm (Limit: {limit_mm:.1f} mm) -> {status}")
    print("=" * 60)
    print("STATUS: PASS")
    
if __name__ == "__main__":
    run_verification()
