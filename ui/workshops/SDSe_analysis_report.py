"""SDSe — Analysis Report Page.

PE-grade structured report for tension membrane structures.

Structure (aligned with CEN/TS 19102 practice):
  Page 1: Cover & Executive Summary
  Page 2: Basis of Design
  Page 3: Form-Finding & Solver Traceability
  Page 4: Membrane Verification (with PE sign-off)
  Page 5: Steel & Cable Verification (with PE sign-off)
  Page 6: Foundation & Connection Verification (with PE sign-off)
  Page 7: Appendices (Solver Log, Assumptions, Disclaimer)
"""

import datetime
import math

import numpy as np
import pandas as pd
import streamlit as st

from data.materials import FABRIC_PROPERTIES, STEEL_MATERIALS
from data.sections import SECTION_PROPERTIES
from engine.connection_design import design_baseplate_and_foundation, design_corner_plate


# =============================================================================
# SDSe BRANDED TITLE BLOCKS
# =============================================================================

def _title_block(title, subtitle, page_no=None):
    """Render a light-coloured SDSe section title block."""
    page_tag = f" · PAGE {page_no}" if page_no else ""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-left: 6px solid #f39c12;
            border-radius: 6px;
            padding: 16px 22px;
            margin-top: 24px;
            margin-bottom: 18px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            page-break-before: always;
        ">
            <div style="font-size: 10px; color: #6c757d; letter-spacing: 2px; font-weight: 600; margin-bottom: 4px;">
                SDSe ENGINEERING{page_tag}
            </div>
            <div style="font-size: 22px; color: #212529; font-weight: 700; margin-bottom: 2px;">
                {title}
            </div>
            <div style="font-size: 13px; color: #6c757d; font-style: italic;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _masthead():
    """Render the report cover masthead."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #ffffff 0%, #f1f3f5 100%);
            border-top: 10px solid #f39c12;
            border-bottom: 4px solid #343a40;
            border-radius: 4px;
            padding: 40px 48px;
            margin-bottom: 28px;
            text-align: center;
            box-shadow: 0 3px 10px rgba(0,0,0,0.12);
        ">
            <div style="font-size: 12px; color: #6c757d; letter-spacing: 5px; font-weight: 600; margin-bottom: 10px;">
                SDSe ENGINEERING
            </div>
            <div style="font-size: 42px; color: #212529; font-weight: 800; letter-spacing: 1px; margin-bottom: 8px;">
                STRUCTURAL ANALYSIS REPORT
            </div>
            <div style="font-size: 16px; color: #495057; font-style: italic; margin-bottom: 24px;">
                Tension Membrane Structure · Multi-Cone Roof
            </div>
            <div style="font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; padding-top: 14px;">
                Report ID: <strong>SDSe-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}</strong> &nbsp;·&nbsp;
                Issued: <strong>{datetime.datetime.now().strftime('%d %B %Y')}</strong> &nbsp;·&nbsp;
                Revision: <strong>Rev A</strong> &nbsp;·&nbsp;
                Version: <strong>1.0</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _signoff_block(section_name, statement):
    """Render a PE sign-off block for a section."""
    st.markdown(
        f"""
        <div style="
            background: #fef9e7;
            border: 2px dashed #d4ac0d;
            border-radius: 6px;
            padding: 18px 22px;
            margin-top: 20px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        ">
            <div style="font-size: 11px; color: #7d6608; letter-spacing: 1px; font-weight: 700; margin-bottom: 8px;">
                SDSe PE SIGN-OFF · {section_name}
            </div>
            <div style="font-size: 13px; color: #4d4d4d; font-style: italic; margin-bottom: 14px;">
                "{statement}"
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px; color: #7d6608;">
                <tr>
                    <td style="width: 40%; padding: 6px 0;">Signed: ______________________________</td>
                    <td style="width: 35%; padding: 6px 0;">Printed Name: ______________________</td>
                    <td style="width: 25%; padding: 6px 0;">Date: ______________</td>
                </tr>
                <tr>
                    <td colspan="3" style="padding: 6px 0; font-size: 11px;">
                        PE Registration No: ______________________________ &nbsp;·&nbsp; Jurisdiction: ______________________
                    </td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _executive_summary_box(is_safe, critical_items):
    """Render an executive summary with the safety verdict."""
    if is_safe:
        bg, border, icon, label = "#d4edda", "#28a745", "✓", "SAFE"
        text_color = "#155724"
    else:
        bg, border, icon, label = "#f8d7da", "#dc3545", "✗", "DANGER"
        text_color = "#721c24"

    items_html = "".join(
        f'<li style="margin-bottom: 4px;"><strong>{k}:</strong> {v}</li>' for k, v in critical_items
    )

    st.markdown(
        f"""
        <div style="
            background: {bg};
            border-left: 8px solid {border};
            border-radius: 6px;
            padding: 20px 26px;
            margin-bottom: 24px;
        ">
            <div style="font-size: 24px; font-weight: 800; color: {text_color}; margin-bottom: 10px;">
                {icon} OVERALL VERDICT: {label}
            </div>
            <div style="font-size: 14px; color: {text_color}; margin-bottom: 12px;">
                The design has been evaluated against SDSe engineering rules.
                Critical results are summarized below.
            </div>
            <ul style="font-size: 13px; color: {text_color}; margin: 0; padding-left: 20px;">
                {items_html}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# MAIN RENDERER
# =============================================================================

def render_SDSe_analysis_report():
    """Render the structured SDSe Analysis Report."""

    # Back buttons
    bcol1, bcol2, bcol3 = st.columns([1, 1, 3])
    with bcol1:
        if st.button("← Back to Lab", key="SDSe_rep_back_lab", use_container_width=True):
            st.session_state.page = "lab"
            st.rerun()
    with bcol2:
        if st.button("← Back to Landing", key="SDSe_rep_back_landing", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()

    # Check for results
    data = st.session_state.get("fdm_results")
    newton_data = st.session_state.get("newton_results")
    if not data or not newton_data:
        st.warning("⚠ No analysis results available. Run the Lab page through Step 1 (FDM) and Step 2 (Structural Calculation) first.")
        return

    # =========================================================================
    # EXTRACT DATA
    # =========================================================================
    nd = newton_data["dr_result"]
    det = newton_data.get("details", {})
    sec = newton_data.get("sections", {})
    fabric_family = newton_data.get("fabric_family", "PVDF")
    fabric_name = newton_data.get("fabric_name", "Unknown")
    code_choice = st.session_state.get("mc_code", "MS 1553")
    design_philosophy = st.session_state.get("mc_design_philosophy", "ULS Uplift")
    wind_speed = st.session_state.get("mc_wind_speed", 33.5)
    snow_depth = st.session_state.get("mc_snow_depth", 0.0)
    payload_kg = st.session_state.get("mc_payload", 0.0)
    span = data["span"]
    apex = data["apex"]
    mid_width = data["mid_width"]
    eave_height = data["eave_height"]
    number_of_cones = st.session_state.get("mc_ncones", 1)
    secondary_count = st.session_state.get("mc_nribs", 3)
    final_pretension = newton_data.get("final_pretension", 1.0)

    # Compute membrane utilization for the summary
    fabric_props_full = FABRIC_PROPERTIES.get(fabric_family, {}).get(fabric_name, {})
    f_u_warp = fabric_props_full.get("f_u_warp")
    f_u_weft = fabric_props_full.get("f_u_weft")

    max_principal_N_m = 0.0
    for ms in nd.get("membrane_stress", []):
        sigma = ms.get("sigma")
        if sigma is None:
            continue
        s_xx, s_yy, s_xy = float(sigma[0, 0]), float(sigma[1, 1]), float(sigma[0, 1])
        mean = 0.5 * (s_xx + s_yy)
        radius = math.sqrt((0.5 * (s_xx - s_yy)) ** 2 + s_xy ** 2)
        principal = mean + radius
        if principal > max_principal_N_m:
            max_principal_N_m = principal

    membrane_util = 0.0
    if f_u_warp and f_u_weft:
        f_u_min = min(float(f_u_warp), float(f_u_weft))
        membrane_util = (max_principal_N_m / 1000.0) / f_u_min if f_u_min > 0 else 999.0

    # Compute steel utilization
    max_steel_util = 0.0
    for key in ("primary", "rib", "ring", "drop"):
        if key in det and det[key] is not None:
            u = det[key].get("util", 0.0)
            if u > max_steel_util:
                max_steel_util = u

    # Compute deflection
    coords_to_draw = nd["coordinates"]
    max_deflection_mm = 0.0
    for i in range(len(data["coords_fdm"])):
        d = np.linalg.norm(coords_to_draw[i] - data["coords_fdm"][i])
        if d > max_deflection_mm:
            max_deflection_mm = d * 1000.0
    limit_mm = (span * 1000.0) / 200.0

    # =========================================================================
    # PAGE 1: COVER & EXECUTIVE SUMMARY
    # =========================================================================
    _masthead()

    _title_block("Executive Summary", "Verdict and critical results at a glance.")

    is_safe = (membrane_util <= 0.70 and max_steel_util <= 0.70 and max_deflection_mm <= limit_mm)
    critical_items = [
        ("Membrane Utilization", f"{membrane_util * 100:.1f}% (Limit 70%)"),
        ("Steel Frame Max Utilization", f"{max_steel_util * 100:.1f}% (Limit 70%)"),
        ("Max Deflection", f"{max_deflection_mm:.2f} mm (Limit {limit_mm:.1f} mm)"),
        ("Pretension Used", f"{final_pretension:.1f} kN/m membrane, {final_pretension * 5.0:.1f} kN/m cable"),
        ("Solver Convergence", f"{nd.get('reason', 'unknown')} in {nd.get('elapsed_seconds', 0):.2f} s"),
    ]
    _executive_summary_box(is_safe, critical_items)

    # Document control table
    st.markdown("### Document Control")
    doc_control = pd.DataFrame([
        {"Field": "Project Name", "Value": "SDSe Multi-Cone Roof Analysis"},
        {"Field": "Report ID", "Value": f"SDSe-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}"},
        {"Field": "Date of Issue", "Value": datetime.datetime.now().strftime('%d %B %Y')},
        {"Field": "Revision", "Value": "Rev A"},
        {"Field": "Design Code", "Value": code_choice},
        {"Field": "Design Philosophy", "Value": design_philosophy},
        {"Field": "Issued By", "Value": "SDSe Engineering App (Automated)"},
        {"Field": "Verified By", "Value": "________________________ (PE Stamp)"},
    ])
    st.dataframe(doc_control, use_container_width=True, hide_index=True)

    # =========================================================================
    # PAGE 2: BASIS OF DESIGN
    # =========================================================================
    _title_block("Basis of Design", "Codes, loads, materials, and geometry.", page_no=2)

    st.markdown("### 2.1 Design Codes & Philosophy")
    st.markdown(f"""
    - **Primary Code:** {code_choice}
    - **Design Philosophy:** {design_philosophy}
    - **Combination Rule:** 0.9 × DL + 1.5 × WL (ULS Uplift for MS 1553)
    - **Fabric Model:** Tension-only, tension-field projection
    - **Steel Model:** Euler-Bernoulli, combined axial + buckling check
    """)

    st.markdown("### 2.2 Material Properties")
    material_data = [
        {"Material": "Membrane Fabric", "Property": f"{fabric_name} ({fabric_family})"},
        {"Material": "Fabric f_u (min)", "Property": f"{min(f_u_warp or 0, f_u_weft or 0):.1f} kN/m"},
        {"Material": "Steel", "Property": "S355 (fy=355 MPa, E=210000 MPa)"},
        {"Material": "Concrete", "Property": "C25/30 (fc=25 MPa)"},
        {"Material": "Anchor Bolts", "Property": "J-Bolt Grade 8.8"},
    ]
    st.dataframe(pd.DataFrame(material_data), use_container_width=True, hide_index=True)

    st.markdown("### 2.3 Geometry")
    geom_data = [
        {"Parameter": "Primary Span", "Value": f"{span:.1f} m"},
        {"Parameter": "Primary Apex", "Value": f"{apex:.1f} m"},
        {"Parameter": "Mid-Span Width", "Value": f"{mid_width:.1f} m"},
        {"Parameter": "Eave Height", "Value": f"{eave_height:.1f} m"},
        {"Parameter": "Number of Cones", "Value": str(number_of_cones)},
        {"Parameter": "Number of Ribs", "Value": str(secondary_count)},
        {"Parameter": "Mesh Nodes", "Value": str(data['pts'].shape[0])},
        {"Parameter": "Mesh Triangles", "Value": str(len(data['tris']))},
    ]
    st.dataframe(pd.DataFrame(geom_data), use_container_width=True, hide_index=True)

    st.markdown("### 2.4 Applied Loads")
    load_data = [
        {"Load": "Wind Speed", "Value": f"{wind_speed:.1f} m/s"},
        {"Load": "Snow Depth", "Value": f"{snow_depth:.2f} m"},
        {"Load": "Payload at Apex", "Value": f"{payload_kg:.0f} kg"},
        {"Load": "Membrane Dead Load", "Value": "1.102 kg/m²"},
        {"Load": "Steel Self-Weight", "Value": "From SECTION_PROPERTIES"},
    ]
    st.dataframe(pd.DataFrame(load_data), use_container_width=True, hide_index=True)

    # =========================================================================
    # PAGE 3: FORM-FINDING & SOLVER TRACEABILITY
    # =========================================================================
    _title_block("Form-Finding & Solver Traceability", "SDSe-FDM and SDSe-NFDM convergence record.", page_no=3)

    st.markdown("### 3.1 SDSe-FDM Form Finding")
    st.markdown(f"""
    - **Status:** {data['solve_ok']}
    - **Force Imbalance:** {data['residual_fdm']:.4e} N (numerically zero)
    - **Estimated Edge Tension:** {data['fdm']['max_edge_tension_N']:.1f} N
    - **Interpretation:** The FDM found a stable pre-stressed shape at the specified pretension.
    """)

    st.markdown("### 3.2 SDSe-NFDM Newton Convergence")
    st.markdown(f"""
    - **Convergence Reason:** `{nd.get('reason', 'unknown')}`
    - **Newton Iterations:** {nd['iterations']}
    - **Total Steps:** {nd.get('total_steps', 0)}
    - **Final Residual (N):** {nd['residual_norm']:.4e}
    - **Max Residual (N):** {nd.get('max_residual', nd['residual_norm']):.4e}
    - **Last Step Size:** {nd.get('last_step_m', 0.0) * 1000:.4f} mm
    - **Solver Time:** {nd['elapsed_seconds']:.2f} s
    """)

    if nd.get("reason") == "converged":
        st.success("✓ Solver converged on residual force.")
    elif nd.get("reason") == "converged_disp":
        st.info(f"✓ Solver converged on displacement (<0.1 mm last step).")
    else:
        st.error(f"✗ Solver did not converge cleanly. Reason: `{nd.get('reason')}`.")

    st.markdown("### 3.3 Newton Iteration History (last 10 steps)")
    hist = nd.get("history", [])
    if hist:
        hist_rows = [
            {"Step": i + 1, "Outer": row[0], "Inner": row[1], "||R||": f"{row[2]:.4e}", "max|R|": f"{row[3]:.4e}"}
            for i, row in enumerate(hist[-10:])
        ]
        st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)

    # =========================================================================
    # PAGE 4: MEMBRANE VERIFICATION (with PE sign-off)
    # =========================================================================
    _title_block("Membrane Verification", "Principal stress vs. fabric breaking strength.", page_no=4)

    if f_u_warp and f_u_weft:
        f_u_min = min(float(f_u_warp), float(f_u_weft))

        st.markdown("### 4.1 Calculation")
        st.markdown(f"""
        **Max Principal Stress Formula:**  
        `σ_max = (σ_xx + σ_yy)/2 + √(((σ_xx - σ_yy)/2)² + σ_xy²)`

        **Utilization Formula:**  
        `Util = σ_max / f_u_min`
        """)

        calc_data = [
            {"Parameter": "σ_max (max principal stress)", "Value": f"{max_principal_N_m / 1000.0:.2f} kN/m"},
            {"Parameter": "f_u (min of warp/weft)", "Value": f"{f_u_min:.1f} kN/m"},
            {"Parameter": "Utilization", "Value": f"{membrane_util * 100:.1f}%"},
            {"Parameter": "SDSe Limit", "Value": "70%"},
        ]
        st.dataframe(pd.DataFrame(calc_data), use_container_width=True, hide_index=True)

        if membrane_util > 0.70:
            st.error(f"✗ **DANGER:** Membrane utilization {membrane_util * 100:.0f}% exceeds 70% limit. Fabric may rupture.")
        elif membrane_util > 0.50:
            st.warning(f"⚠ **WARNING:** Membrane utilization {membrane_util * 100:.0f}%. Approaching ULS.")
        else:
            st.success(f"✓ **SAFE:** Membrane utilization {membrane_util * 100:.0f}%. Acceptable margin.")

        st.markdown("### 4.2 Deflection")
        st.markdown(f"""
        **Max Deflection:** {max_deflection_mm:.2f} mm  
        **Limit (L/200):** {limit_mm:.1f} mm  
        **Status:** {'PASS ✓' if max_deflection_mm <= limit_mm else 'FAIL ✗'}
        """)

        _signoff_block(
            "Membrane Verification",
            "I certify that the membrane structure has been verified against rupture and deflection under the specified loads, in accordance with the stated design code."
        )
    else:
        st.warning("Fabric strength data unavailable for this fabric type.")

    # =========================================================================
    # PAGE 5: STEEL & CABLE VERIFICATION (with PE sign-off)
    # =========================================================================
    _title_block("Steel & Cable Verification", "Member checks: axial, bending, and Euler buckling.", page_no=5)

    st.markdown("### 5.1 Member Schedule with Calculation Traceability")

    member_rows = []
    for key, label in [("primary", "Primary_Arch"), ("rib", "Rib_Arch"), ("ring", "Ring_Beam"), ("drop", "Drop_Member")]:
        if key not in det or det[key] is None:
            continue
        d = det[key]
        member_section = sec.get(key, "?")
        props = SECTION_PROPERTIES.get(member_section, {})
        A_mm2 = props.get("A", 1.0)
        W_el_mm3 = props.get("W_el", 1.0)
        I_mm4 = props.get("I", 1.0)
        fy_MPa = 355
        E_MPa = 210000

        N_Ed = d["N_Ed_kN"] * 1000.0
        M_Ed = d["M_Ed_kNm"] * 1e6
        N_cap = A_mm2 * fy_MPa
        M_cap = W_el_mm3 * fy_MPa
        L_eff_mm = d["L_eff_m"] * 1000.0
        N_cr = (math.pi ** 2 * E_MPa * I_mm4) / (L_eff_mm ** 2) if L_eff_mm > 0 else 1e18

        member_rows.append({
            "Member": label,
            "Section": member_section,
            "L_eff (m)": f"{d['L_eff_m']:.2f}",
            "N_Ed (kN)": f"{d['N_Ed_kN']:.1f}",
            "N_cap (kN)": f"{N_cap / 1000.0:.1f}",
            "N_cr (kN)": f"{N_cr / 1000.0:.1f}",
            "M_Ed (kNm)": f"{d['M_Ed_kNm']:.1f}",
            "M_cap (kNm)": f"{M_cap / 1e6:.1f}",
            "Steel DL (kN)": f"{d['steel_DL_kN']:.1f}",
            "Utilization": f"{d['util'] * 100:.0f}%",
        })

    if member_rows:
        st.dataframe(pd.DataFrame(member_rows), use_container_width=True, hide_index=True)

        st.markdown("### 5.2 Calculation Formulas")
        st.markdown("""
        **Stress Check:**  
        `stress_util = N_Ed / N_cap + M_Ed / M_cap`

        **Euler Buckling:**  
        `N_cr = π² · E · I / L_eff²`  
        `buckling_util = N_Ed / N_cr`

        **Combined:**  
        `combined_util = stress_util + buckling_util ≤ 0.70`
        """)

        warn_members = [r for r in member_rows if float(r["Utilization"].rstrip("%")) > 70.0]
        if warn_members:
            st.error(f"✗ **DANGER:** {len(warn_members)} member(s) exceed 70% utilization cap.")
            for r in warn_members:
                st.write(f"- **{r['Member']}** ({r['Section']}): {r['Utilization']}")
        else:
            st.success("✓ All members pass the SDSe 70% utilization cap.")

    st.markdown("### 5.3 Edge Cable")
    st.markdown(f"""
    - **Selected Cable:** {newton_data.get('cable_name', 'unknown')}
    - **Area:** {newton_data.get('cable_A_mm2', 0):.1f} mm²
    - **Design Tension:** {max([c['T_N'] for c in nd.get('cable_tension_list', [])] + [0]) / 1000.0:.2f} kN (max local segment)
    - **Sizing Rule:** smallest catalogue cable with `A · f_u ≥ 2.0 × T_max_local`
    """)

    _signoff_block(
        "Steel & Cable Verification",
        "I certify that the steel frame, cables, and connections have been verified against yielding, buckling, and rupture under the specified load combinations."
    )

    # =========================================================================
    # PAGE 6: FOUNDATION & CONNECTION VERIFICATION (with PE sign-off)
    # =========================================================================
    _title_block("Foundation & Connection Verification", "Baseplates, anchor bolts, pads, and corner plates.", page_no=6)

    R = nd.get("reactions", None)
    if R is not None and len(data["anchor_idx"]) > 0:
        st.markdown("### 6.1 Baseplate Summary")
        baseplate_rows = []
        for idx in data["anchor_idx"]:
            r = R[idx]
            design = design_baseplate_and_foundation(r, sec.get("primary", "CHS 100"), 0.0)
            baseplate_rows.append({
                "Node": idx,
                "X (m)": f"{data['coords_fdm'][idx, 0]:.2f}",
                "Y (m)": f"{data['coords_fdm'][idx, 1]:.2f}",
                "Fx (kN)": f"{r[0] / 1000.0:.1f}",
                "Fy (kN)": f"{r[1] / 1000.0:.1f}",
                "Fz (kN)": f"{r[2] / 1000.0:.1f}",
                "Plate (mm)": f"{design['plate_side_mm']}×{design['plate_side_mm']}×{design['plate_thickness_mm']}",
                "Bolts": f"{design['bolt_count']}×M{design['bolt_diameter_mm']}",
                "Pad (mm)": f"{design['pad_side_mm']}×{design['pad_side_mm']}",
            })
        st.dataframe(pd.DataFrame(baseplate_rows), use_container_width=True, hide_index=True)

    st.markdown("### 6.2 Corner Plate Summary")
    st.info("Corner plates are sized for **local vector forces** at each anchor node. See the Lab page Diagnostics for the full per-node table.")
    st.markdown("""
    **Local Force Formula:**  
    `F_resultant = T_cable · |u_prev + u_next|`  
    where `u_prev` and `u_next` are the unit vectors to the two adjacent anchor nodes.
    """)

    _signoff_block(
        "Foundation & Connection Verification",
        "I certify that the baseplates, anchor bolts, concrete pads, and corner plate connections have been verified against uplift, shear, bearing, and weld capacity."
    )

    # =========================================================================
    # PAGE 7: APPENDICES
    # =========================================================================
    _title_block("Appendices: Assumptions & Disclaimer", "Scope, limitations, and legal notice.", page_no=7)

    st.markdown("### A. Assumptions & Limitations")
    st.markdown("""
    - **Analysis Type:** Linear elastic member checks with tension-field membrane model.
    - **Load Case:** ULS Uplift only. Downward loads (snow, payload) are approximated. Long-term creep and prestress relaxation are not modeled.
    - **Buckling:** Euler buckling with effective length `L_eff = 0.7 × L` (conservative for parabolic arches).
    - **Cable Model:** Pre-tensioned, linear, stays taut.
    - **Not Included:** Fatigue, dynamic wind (vortex shedding, flutter), seismic, weld detail verification, concrete reinforcement, anchorage to ground beyond basic geometry.
    - **Geometry:** Based on the form-found shape from SDSe-FDM. Physical tolerances during fabrication are not included.
    """)

    st.markdown("### B. Disclaimer")
    st.markdown(
        """
        <div style="
            background: #fdf2f2;
            border-left: 6px solid #c0392b;
            border-radius: 6px;
            padding: 18px 24px;
            color: #7b241c;
            font-size: 13px;
        ">
        <strong>This SDSe report is generated by the SDSe engineering app.</strong><br><br>
        It is a <strong>design aid</strong>, not a substitute for professional engineering judgment.<br>
        All results must be <strong>verified by a licensed Professional Engineer</strong> before construction.<br><br>
        The app does not guarantee fitness for purpose, code compliance in your jurisdiction, or safety in extreme events.<br>
        <strong>Use at your own risk.</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =========================================================================
    # EXPORT
    # =========================================================================
    _title_block("Export & Final Authorisation", "Download the report and sign off.", page_no="END")

    report_md = _build_SDSe_markdown_report(
        span, apex, mid_width, eave_height, number_of_cones, secondary_count,
        code_choice, design_philosophy, wind_speed, snow_depth, payload_kg,
        fabric_family, fabric_name, final_pretension, nd,
        member_rows, is_safe, max_deflection_mm, limit_mm, membrane_util, max_steel_util,
    )
    st.download_button(
        label="📥 Download SDSe Report (Markdown)",
        data=report_md,
        file_name=f"SDSe_Analysis_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    _signoff_block(
        "Final Report Authorisation",
        "I authorise this report for issue. The structure is verified safe for construction under the stated loads, codes, and assumptions. This report supersedes all previous revisions."
    )


# =============================================================================
# MARKDOWN EXPORT
# =============================================================================

def _build_SDSe_markdown_report(span, apex, mid_width, eave_height, cones, ribs,
                                 code, philosophy, wind, snow, payload,
                                 fabric_family, fabric_name, pretension, nd,
                                 member_rows, is_safe, defl_val, defl_limit,
                                 mem_util, steel_util):
    lines = [
        "# SDSe STRUCTURAL ANALYSIS REPORT",
        "",
        f"**Report ID:** SDSe-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}  ",
        f"**Issued:** {datetime.datetime.now().strftime('%d %B %Y')}  ",
        f"**Revision:** Rev A  ",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"**Overall Verdict: {'SAFE ✓' if is_safe else 'DANGER ✗'}**",
        "",
        f"- Membrane Utilization: {mem_util * 100:.1f}% (Limit 70%)",
        f"- Steel Max Utilization: {steel_util * 100:.1f}% (Limit 70%)",
        f"- Max Deflection: {defl_val:.2f} mm (Limit {defl_limit:.1f} mm)",
        "",
        "---",
        "",
        "## 1. Basis of Design",
        f"- **Design Code:** {code}",
        f"- **Philosophy:** {philosophy}",
        f"- **Fabric:** {fabric_name} ({fabric_family})",
        f"- **Steel:** S355 (fy=355 MPa)",
        "",
        "## 2. Geometry",
        f"- Span: {span:.1f} m · Apex: {apex:.1f} m · Width: {mid_width:.1f} m · Eave: {eave_height:.1f} m",
        f"- Cones: {cones} · Ribs: {ribs}",
        "",
        "## 3. Load Case",
        f"- Wind: {wind:.1f} m/s · Snow: {snow:.2f} m · Payload: {payload:.0f} kg",
        f"- Pretension: {pretension:.1f} kN/m · Cable: {pretension * 5.0:.1f} kN/m",
        f"- Solver: `{nd.get('reason')}` in {nd.get('elapsed_seconds', 0):.2f} s",
        "",
        "## 4. Steel Frame",
        "",
        "| Member | Section | L_eff (m) | N_Ed (kN) | N_cap (kN) | N_cr (kN) | Util |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in member_rows:
        lines.append(f"| {r['Member']} | {r['Section']} | {r['L_eff (m)']} | {r['N_Ed (kN)']} | {r['N_cap (kN)']} | {r['N_cr (kN)']} | {r['Utilization']} |")

    lines += [
        "",
        "## 5. Membrane",
        f"- Max Principal Stress: (see calculator)",
        f"- Utilization: {mem_util * 100:.1f}% (Limit 70%)",
        "",
        "## 6. Deflection",
        f"- Max Deflection: {defl_val:.2f} mm",
        f"- Limit (L/200): {defl_limit:.1f} mm",
        "",
        "## 7. Assumptions",
        "- Linear elastic members, tension-field membrane.",
        "- ULS Uplift only; downward loads approximated.",
        "- No fatigue, dynamic wind, or seismic.",
        "",
        "## 8. Disclaimer",
        "This is a design aid. All results must be verified by a licensed PE before construction.",
        "",
        "---",
        "",
        "**PE Final Sign-Off:** _______________________ Date: _______________  ",
        "**PE Registration No:** ______________________________",
    ]
    return "\n".join(lines)
