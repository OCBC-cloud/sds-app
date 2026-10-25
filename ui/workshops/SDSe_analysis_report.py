"""SDSe — Analysis Report Page.

Owner-only feature (2026-10-25).
Unified report format for every structure type:
Multi-Cone, Dome, Saddle, Leaf, Hypar.

Designed for on-screen review and PDF export.
"""

import datetime
import math

import numpy as np
import pandas as pd
import streamlit as st

from data.materials import FABRIC_PROPERTIES, CABLE_PROPERTIES, STEEL_MATERIALS
from data.sections import SECTION_PROPERTIES
from engine.connection_design import (
    design_baseplate_and_foundation,
    design_corner_plate,
)


# =============================================================================
# SDSe BRANDED TITLE BLOCK (light theme, PDF-ready)
# =============================================================================

def _render_SDSe_title_block(title, subtitle):
    """Render a light-coloured SDSe title block for report sections."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-left: 6px solid #f39c12;
            border-radius: 6px;
            padding: 14px 20px;
            margin-bottom: 18px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        ">
            <div style="
                font-size: 11px;
                color: #6c757d;
                letter-spacing: 2px;
                font-weight: 600;
                margin-bottom: 4px;
            ">SDSe ENGINEERING</div>
            <div style="
                font-size: 22px;
                color: #212529;
                font-weight: 700;
                margin-bottom: 2px;
            ">{title}</div>
            <div style="
                font-size: 13px;
                color: #6c757d;
                font-style: italic;
            ">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_SDSe_masthead():
    """Render the top SDSe cover block."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #ffffff 0%, #f1f3f5 100%);
            border-top: 8px solid #f39c12;
            border-bottom: 3px solid #343a40;
            border-radius: 4px;
            padding: 30px 40px;
            margin-bottom: 24px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <div style="
                font-size: 12px;
                color: #6c757d;
                letter-spacing: 4px;
                font-weight: 600;
                margin-bottom: 8px;
            ">SDSe ENGINEERING</div>
            <div style="
                font-size: 34px;
                color: #212529;
                font-weight: 800;
                letter-spacing: 1px;
                margin-bottom: 6px;
            ">ANALYSIS REPORT</div>
            <div style="
                font-size: 15px;
                color: #495057;
                font-style: italic;
                margin-bottom: 16px;
            ">Structural Design Services · SDS-app</div>
            <div style="
                font-size: 13px;
                color: #6c757d;
                border-top: 1px solid #dee2e6;
                padding-top: 12px;
                margin-top: 8px;
            ">
                Report ID: <strong>SDSe-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}</strong> &nbsp;·&nbsp;
                Issued: <strong>{datetime.datetime.now().strftime('%d %B %Y, %H:%M')}</strong> &nbsp;·&nbsp;
                Version: <strong>1.0</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_SDSe_signoff(label):
    """Render a PE sign-off block."""
    st.markdown(
        f"""
        <div style="
            background: #fef9e7;
            border: 1px dashed #d4ac0d;
            border-radius: 4px;
            padding: 12px 18px;
            margin-top: 12px;
            margin-bottom: 12px;
            font-size: 13px;
            color: #7d6608;
        ">
            <strong>SDSe PE Sign-Off — {label}</strong><br>
            Signed: ______________________________ &nbsp;&nbsp;
            Printed Name: ______________________________ &nbsp;&nbsp;
            Date: _______________
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# MAIN RENDERER
# =============================================================================

def render_SDSe_analysis_report():
    """Render the unified SDSe Analysis Report for any structure."""
    
    # --- BACK BUTTONS ---
    bcol1, bcol2, bcol3 = st.columns([1, 1, 3])
    with bcol1:
        if st.button("← Back to Lab", key="SDSe_rep_back_lab", use_container_width=True):
            st.session_state.page = "lab"
            st.rerun()
    with bcol2:
        if st.button("← Back to Landing", key="SDSe_rep_back_landing", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()

    # --- MASTHEAD ---
    _render_SDSe_masthead()

    # --- CHECK FOR RESULTS ---
    data = st.session_state.get("fdm_results")
    newton_data = st.session_state.get("newton_results")

    if not data or not newton_data:
        st.warning("⚠ No analysis results available. Run the Lab page through Step 1 (FDM) and Step 2 (Structural Calculation) first.")
        return

    # --- EXTRACT DATA ---
    nd = newton_data["dr_result"]
    det = newton_data.get("details", {})
    sec = newton_data.get("sections", {})
    fabric_family = newton_data.get("fabric_family", "PVDF")
    fabric_name = newton_data.get("fabric_name", "Unknown")
    code_choice = st.session_state.get("mc_code", "MS 1553")
    design_philosophy = st.session_state.get("mc_design_philosophy", "Serviceability (Unfactored)")
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

    # =========================================================================
    # SDSe-01: PROJECT INFORMATION
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-01: Project Information",
        "Owner, design code, materials, and report metadata."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        **Project Name:** SDSe Multi-Cone Roof Analysis  
        **Date of Issue:** {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}  
        **Design Code:** {code_choice}  
        **Design Philosophy:** {design_philosophy}  
        """)
    with c2:
        st.markdown(f"""
        **Fabric:** {fabric_name} ({fabric_family})  
        **Steel Grade:** S355  
        **Concrete Grade:** C25/30  
        **Bolt Grade:** J-Bolt Grade 8.8  
        """)

    # =========================================================================
    # SDSe-02: GEOMETRY & MESH
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-02: Geometry & Mesh",
        "Form-found geometry and finite element mesh summary."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Primary Span", f"{span:.1f} m")
        st.metric("Primary Apex", f"{apex:.1f} m")
    with c2:
        st.metric("Mid-Span Width", f"{mid_width:.1f} m")
        st.metric("Eave Height", f"{eave_height:.1f} m")
    with c3:
        st.metric("Cones", f"{number_of_cones}")
        st.metric("Ribs", f"{secondary_count}")

    st.markdown(f"""
    - **Mesh Nodes:** {data['pts'].shape[0]}  
    - **Mesh Triangles:** {len(data['tris'])}  
    - **Held Nodes (Baseplates):** {len(data['fixed'])}  
    - **Membrane Type:** PVDF Type III fabric, tension-field model  
    """)

    # =========================================================================
    # SDSe-03: LOAD CASE & CONVERGENCE
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-03: Load Case & Convergence",
        "Environmental loads and SDSe-NFDM solver convergence."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        **Wind Speed:** {wind_speed:.1f} m/s  
        **Snow Depth:** {snow_depth:.2f} m  
        **Payload at Apex:** {payload_kg:.0f} kg  
        """)
    with c2:
        st.markdown(f"""
        **Pretension Used:** {final_pretension:.1f} kN/m (membrane), {final_pretension * 5.0:.1f} kN/m (cable)  
        **Convergence Reason:** `{nd['reason']}`  
        **Iterations:** {nd['iterations']}  
        **Solver Time:** {nd['elapsed_seconds']:.2f} s  
        **Last Step Size:** {nd.get('last_step_m', 0.0) * 1000:.4f} mm  
        """)

    if nd.get("reason") == "converged":
        st.success("✓ SDSe-NFDM solver converged on residual force.")
    elif nd.get("reason") == "converged_disp":
        st.info(f"✓ SDSe-NFDM solver converged on displacement (last step {nd.get('last_step_m', 0.0) * 1000:.2f} mm < 0.1 mm threshold).")
    else:
        st.error(f"✗ SDSe-NFDM solver did not converge cleanly. Reason: `{nd.get('reason', 'unknown')}`. Report may be unreliable.")

    # =========================================================================
    # SDSe-04: MEMBRANE VERIFICATION
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-04: Membrane Verification",
        "Principal stress check against fabric breaking strength (SDSe-Membrane)."
    )

    family = FABRIC_PROPERTIES.get(fabric_family, {})
    fabric_props = family.get(fabric_name, {})
    f_u_warp = fabric_props.get("f_u_warp", None)
    f_u_weft = fabric_props.get("f_u_weft", None)

    if f_u_warp and f_u_weft:
        f_u_min = min(float(f_u_warp), float(f_u_weft))
        max_principal_N_m = 0.0
        for ms in nd.get("membrane_stress", []):
            sigma = ms.get("sigma", None)
            if sigma is None:
                continue
            s_xx, s_yy, s_xy = float(sigma[0, 0]), float(sigma[1, 1]), float(sigma[0, 1])
            mean = 0.5 * (s_xx + s_yy)
            diff = 0.5 * (s_xx - s_yy)
            radius = math.sqrt(diff ** 2 + s_xy ** 2)
            principal = mean + radius
            if principal > max_principal_N_m:
                max_principal_N_m = principal

        util = (max_principal_N_m / 1000.0) / f_u_min if f_u_min > 0 else 999.0

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            **Fabric Family:** {fabric_family}  
            **Fabric Type:** {fabric_name}  
            **f_u (min):** {f_u_min:.1f} kN/m  
            **Max Principal Tension:** {max_principal_N_m / 1000.0:.2f} kN/m  
            """)
        with c2:
            st.markdown(f"""
            **Utilization:** {util * 100:.1f}%  
            **Limit (SDSe Rule):** 70%  
            """)

        if util > 0.70:
            st.error(f"✗ **SDSe DANGER:** Fabric utilization at {util * 100:.0f}%. Membrane may rupture. Increase pretension, add cones, or choose a stronger fabric.")
        elif util > 0.50:
            st.warning(f"⚠ **SDSe WARNING:** Fabric utilization at {util * 100:.0f}%. Approaching ULS.")
        else:
            st.success(f"✓ **SDSe SAFE:** Fabric utilization at {util * 100:.0f}%. Acceptable margin.")

        _render_SDSe_signoff("Membrane Verification")
    else:
        st.warning("Fabric strength data unavailable for this fabric type.")

    # =========================================================================
    # SDSe-05: STEEL FRAME VERIFICATION
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-05: Steel Frame Verification",
        "Member schedule, axial demand, self-weight, and Euler buckling (SDSe-Steel)."
    )

    member_rows = []
    for key, label in [("primary", "Primary_Arch"), ("rib", "Rib_Arch"), ("ring", "Ring_Beam"), ("drop", "Drop_Member")]:
        if key in det and det[key] is not None:
            d = det[key]
            member_rows.append({
                "Member": label,
                "Section": sec.get(key, "?"),
                "L_eff (m)": f"{d['L_eff_m']:.2f}",
                "N_Ed (kN)": f"{d['N_Ed_kN']:.1f}",
                "M_Ed (kNm)": f"{d['M_Ed_kNm']:.1f}",
                "Steel DL (kN)": f"{d['steel_DL_kN']:.1f}",
                "Membrane DL (kN)": f"{d['membrane_DL_kN']:.1f}",
                "Utilization": f"{d['util'] * 100:.0f}%",
            })

    if member_rows:
        df = pd.DataFrame(member_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        warn_members = [r for r in member_rows if float(r["Utilization"].rstrip("%")) > 70.0]
        if warn_members:
            st.error(f"✗ **SDSe DANGER:** {len(warn_members)} member(s) exceed the 70% utilization cap.")
            for r in warn_members:
                st.write(f"- **{r['Member']}** ({r['Section']}): {r['Utilization']}")
        else:
            st.success("✓ All members pass the SDSe 70% utilization cap.")

    _render_SDSe_signoff("Steel Frame Verification")

    # =========================================================================
    # SDSe-06: FOUNDATION & CONNECTIONS
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-06: Foundation & Connections",
        "Baseplate design, anchor reactions, and corner plate sizing (SDSe-Foundation)."
    )

    st.markdown("### Baseplate Summary")
    R = nd.get("reactions", None)
    if R is not None and len(data["anchor_idx"]) > 0:
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

    st.markdown("### Corner Plate Summary")
    st.info("Corner plates sized for **local vector forces** at each node (not global perimeter). See Lab page Diagnostics for the full per-node table.")

    _render_SDSe_signoff("Foundation & Connections")

    # =========================================================================
    # SDSe-07: DEFLECTION CHECK
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-07: Deflection Check",
        "Serviceability verification against L/200 limit."
    )

    coords_to_draw = nd["coordinates"]
    max_deflection_mm = 0.0
    max_def_idx = -1
    for i in range(len(data["coords_fdm"])):
        d = np.linalg.norm(coords_to_draw[i] - data["coords_fdm"][i])
        if d > max_deflection_mm:
            max_deflection_mm = d * 1000.0
            max_def_idx = i
    limit_mm = (span * 1000.0) / 200.0
    status = "PASS" if max_deflection_mm <= limit_mm else "FAIL"

    if status == "PASS":
        st.success(f"✓ Max deflection {max_deflection_mm:.2f} mm at Node {max_def_idx} (Limit: {limit_mm:.1f} mm) → **PASS**")
    else:
        st.error(f"✗ Max deflection {max_deflection_mm:.2f} mm at Node {max_def_idx} (Limit: {limit_mm:.1f} mm) → **FAIL**")

    # =========================================================================
    # SDSe-08: SOLVER LOG
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-08: Solver Log",
        "SDSe-FDM and SDSe-NFDM iteration history for engineering audit."
    )

    st.markdown("### SDSe-FDM Form Finding")
    st.markdown(f"""
    - **Status:** {data['solve_ok']}  
    - **Force Imbalance:** {data['residual_fdm']:.4e} N  
    - **Estimated Edge Tension:** {data['fdm']['max_edge_tension_N']:.1f} N  
    """)

    st.markdown("### SDSe-NFDM Newton History (last 10 steps)")
    hist = nd.get("history", [])
    if hist:
        hist_rows = [{"Step": i, "Outer": row[0], "Inner": row[1], "||R||": f"{row[2]:.4e}", "max|R|": f"{row[3]:.4e}"} for i, row in enumerate(hist[-10:])]
        st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)

    # =========================================================================
    # SDSe-09: ASSUMPTIONS & LIMITATIONS
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-09: Assumptions & Limitations",
        "Scope of the SDSe analysis and known gaps."
    )

    st.markdown("""
    - **Member Check:** Linear Euler-Bernoulli with combined stress + Euler buckling.
    - **Membrane Model:** Tension-only with principal stress projection (tension-field).
    - **Cable Model:** Pre-tensioned, linear. Slack cables not modeled.
    - **Buckling Length:** `L_eff = 0.7 × L` (conservative for parabolic arches).
    - **Load Case:** **ULS Uplift only.** Downward loads (snow, payload) are approximated. Serviceability deflections for dead load are not included.
    - **Not Included:** Fatigue, dynamic wind, seismic, weld details, concrete reinforcement, anchorage to ground beyond basic geometry.
    """)

    # =========================================================================
    # SDSe-10: DISCLAIMER
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-10: Disclaimer",
        "Legal scope of this report."
    )

    st.markdown(
        """
        <div style="
            background: #fdf2f2;
            border-left: 4px solid #c0392b;
            border-radius: 4px;
            padding: 14px 20px;
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
    # SDSe-11: EXPORT & SIGN-OFF
    # =========================================================================
    _render_SDSe_title_block(
        "SDSe-11: Export & Final Sign-Off",
        "Download the SDSe report and authorise the design."
    )

    report_md = _build_SDSe_markdown_report(
        span, apex, mid_width, eave_height, number_of_cones, secondary_count,
        code_choice, design_philosophy, wind_speed, snow_depth, payload_kg,
        fabric_family, fabric_name, final_pretension, nd,
        member_rows, status, max_deflection_mm, limit_mm
    )
    st.download_button(
        label="📥 Download SDSe Report (Markdown)",
        data=report_md,
        file_name=f"SDSe_Analysis_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    _render_SDSe_signoff("Final Report Authorisation")


# =============================================================================
# MARKDOWN EXPORT
# =============================================================================

def _build_SDSe_markdown_report(span, apex, mid_width, eave_height, cones, ribs,
                                code, philosophy, wind, snow, payload,
                                fabric_family, fabric_name, pretension, nd,
                                member_rows, defl_status, defl_val, defl_limit):
    """Build the SDSe unified markdown report."""
    lines = []
    lines.append("# SDSe ANALYSIS REPORT")
    lines.append("")
    lines.append(f"**Report ID:** SDSe-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}  ")
    lines.append(f"**Issued:** {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}  ")
    lines.append(f"**Version:** 1.0  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## SDSe-01: Project Information")
    lines.append(f"- **Design Code:** {code}")
    lines.append(f"- **Design Philosophy:** {philosophy}")
    lines.append(f"- **Fabric:** {fabric_name} ({fabric_family})")
    lines.append(f"- **Steel Grade:** S355")
    lines.append("")
    lines.append("## SDSe-02: Geometry & Mesh")
    lines.append(f"- **Span:** {span:.1f} m")
    lines.append(f"- **Apex:** {apex:.1f} m")
    lines.append(f"- **Mid-Width:** {mid_width:.1f} m")
    lines.append(f"- **Eave Height:** {eave_height:.1f} m")
    lines.append(f"- **Cones:** {cones}")
    lines.append(f"- **Ribs:** {ribs}")
    lines.append("")
    lines.append("## SDSe-03: Load Case & Convergence")
    lines.append(f"- **Wind Speed:** {wind:.1f} m/s")
    lines.append(f"- **Snow Depth:** {snow:.2f} m")
    lines.append(f"- **Payload:** {payload:.0f} kg")
    lines.append(f"- **Pretension:** {pretension:.1f} kN/m (membrane), {pretension * 5.0:.1f} kN/m (cable)")
    lines.append(f"- **Convergence:** `{nd.get('reason', 'unknown')}` in {nd.get('elapsed_seconds', 0):.2f} s")
    lines.append("")
    lines.append("## SDSe-05: Steel Frame")
    lines.append("")
    lines.append("| Member | Section | L_eff (m) | N_Ed (kN) | M_Ed (kNm) | Steel DL (kN) | Membrane DL (kN) | Utilization |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in member_rows:
        lines.append(f"| {r['Member']} | {r['Section']} | {r['L_eff (m)']} | {r['N_Ed (kN)']} | {r['M_Ed (kNm)']} | {r['Steel DL (kN)']} | {r['Membrane DL (kN)']} | {r['Utilization']} |")
    lines.append("")
    lines.append("## SDSe-07: Deflection")
    lines.append(f"- **Max Deflection:** {defl_val:.2f} mm")
    lines.append(f"- **Limit:** {defl_limit:.1f} mm")
    lines.append(f"- **Status:** {defl_status}")
    lines.append("")
    lines.append("## SDSe-09: Assumptions")
    lines.append("- Linear Euler-Bernoulli members with Euler buckling")
    lines.append("- Tension-only membrane with tension-field projection")
    lines.append("- ULS Uplift only; downward loads approximate")
    lines.append("- No fatigue, dynamic wind, or seismic")
    lines.append("")
    lines.append("## SDSe-10: Disclaimer")
    lines.append("This is a design aid, not a substitute for professional engineering judgment.")
    lines.append("All results must be verified by a licensed Professional Engineer before construction.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**SDSe Final Sign-Off:** _______________________ Date: _______________")
    return "\n".join(lines)
