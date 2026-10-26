"""SDSe — Analysis Report Page.

PE-grade structured report for tension membrane structures.

Legal stance:
  This is an AUTOMATED DESIGN AID, not a certified engineering document.
  No PE sign-off is provided by the app. The user assumes full responsibility.
"""

import base64
import datetime
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.materials import FABRIC_PROPERTIES
from data.sections import SECTION_PROPERTIES
from engine.connection_design import design_baseplate_and_foundation, design_corner_plate
from viewers.figures._shared import apply_common_layout


# =============================================================================
# PRINT CSS
# =============================================================================

def _inject_print_css():
    st.markdown(
        """
        <style>
        @media print {
            header[data-testid="stHeader"] { display: none !important; }
            [data-testid="stSidebar"] { display: none !important; }
            .stDeployButton { display: none !important; }
            .stButton { display: none !important; }
            .stDownloadButton { display: none !important; }
            .block-container { padding-top: 0.5rem !important; }
            .stMarkdown > div { page-break-inside: avoid; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# TITLE BLOCKS
# =============================================================================

def _title_block(title, subtitle, page_no=None):
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
                ANALYSIS REPORT
            </div>
            <div style="font-size: 16px; color: #495057; font-style: italic; margin-bottom: 24px;">
                Tension Membrane Structure · Multi-Cone Roof
            </div>
            <div style="font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; padding-top: 14px;">
                Report ID: <strong>SDSe-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}</strong> &nbsp;·&nbsp;
                Issued: <strong>{datetime.datetime.now().strftime('%d %B %Y')}</strong> &nbsp;·&nbsp;
                Revision: <strong>Rev A</strong>
            </div>
            <div style="font-size: 11px; color: #a8b8c8; margin-top: 10px; font-style: italic;">
                Automated design aid. Not a certified engineering document.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _executive_summary_box(is_safe, critical_items):
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
            <ul style="font-size: 13px; color: {text_color}; margin: 0; padding-left: 20px;">
                {items_html}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# 3D VIEW BUILDER
# =============================================================================

def _build_report_figure(data, newton_data):
    coords_to_draw = newton_data["dr_result"]["coordinates"]
    COL_MEMBRANE = "#4a7a9c"; COL_RING_EDGE = "#ffd166"; COL_PRIMARY = "#FF6B6B"
    COL_RIB = "#e07b39"; COL_SPOKE = "#c0c0c0"; COL_DROP = "#a0a0a0"
    fig = go.Figure()
    if len(data["tris"]) > 0:
        tri = np.asarray(data["tris"], dtype=int)
        fig.add_trace(go.Mesh3d(
            x=coords_to_draw[:, 0], y=coords_to_draw[:, 1], z=coords_to_draw[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            showlegend=False, hoverinfo="skip"
        ))
    fig.add_trace(go.Scatter3d(
        x=data["xp"], y=np.zeros_like(data["xp"]), z=data["zp"],
        mode="lines", line=dict(color=COL_PRIMARY, width=7), showlegend=False, hoverinfo="skip"
    ))
    for i in range(len(data["rib_x"])):
        y = np.linspace(-data["rib_half_width"][i], data["rib_half_width"][i], 80)
        u = y / data["rib_half_width"][i] if data["rib_half_width"][i] > 0 else np.zeros_like(y)
        z = data["rib_peak_z"][i] * (1.0 - u ** 2)
        x = np.full_like(y, data["rib_x"][i])
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode="lines",
            line=dict(color=COL_RIB, width=5), showlegend=False, hoverinfo="skip"))
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        pp = coords_to_draw[idx_list]
        closed = np.vstack([pp, pp[:1]])
        fig.add_trace(go.Scatter3d(x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
            mode="lines", line=dict(color=COL_RING_EDGE, width=5), showlegend=False, hoverinfo="skip"))
        centre_i = data["built"]["centre_indices"][k]; beam_i = data["built"]["beam_top_indices"][k]
        cx, cy, cz = coords_to_draw[centre_i]
        for poly_i in idx_list:
            fig.add_trace(go.Scatter3d(
                x=[cx, coords_to_draw[poly_i, 0]], y=[cy, coords_to_draw[poly_i, 1]],
                z=[cz, coords_to_draw[poly_i, 2]], mode="lines",
                line=dict(color=COL_SPOKE, width=2), showlegend=False, hoverinfo="skip"))
        bx, by, bz = coords_to_draw[beam_i]
        fig.add_trace(go.Scatter3d(
            x=[cx, bx], y=[cy, by], z=[cz, bz], mode="lines",
            line=dict(color=COL_DROP, width=4), showlegend=False, hoverinfo="skip"))
    apply_common_layout(fig, data["apex"])
    return fig


def _render_figure_to_png_base64(fig):
    try:
        img_bytes = fig.to_image(format="png", width=1200, height=700, scale=2)
        return base64.b64encode(img_bytes).decode("utf-8")
    except Exception:
        return None


# =============================================================================
# MAIN RENDERER
# =============================================================================

def render_SDSe_analysis_report():
    _inject_print_css()

    bcol1, bcol2, bcol3 = st.columns([1, 1, 3])
    with bcol1:
        if st.button("← Back to Lab", key="SDSe_rep_back_lab", use_container_width=True):
            st.session_state.page = "lab"; st.rerun()
    with bcol2:
        if st.button("← Back to Landing", key="SDSe_rep_back_landing", use_container_width=True):
            st.session_state.page = "landing"; st.rerun()

    data = st.session_state.get("fdm_results")
    newton_data = st.session_state.get("newton_results")
    stage3_data = st.session_state.get("stage3_results")
    
    if not data or not newton_data:
        st.warning("⚠ No analysis results available. Run the Lab page through Stage 2 first.")
        return

    nd = newton_data["dr_result"]
    det = newton_data.get("details", {}) or {}
    sec = newton_data.get("sections", {}) or {}
    fabric_family = newton_data.get("fabric_family", "PVDF")
    fabric_name = newton_data.get("fabric_name", "Unknown")
    code_choice = st.session_state.get("mc_code", "MS 1553")
    design_philosophy = st.session_state.get("mc_design_philosophy", "ULS Uplift")
    wind_speed = st.session_state.get("mc_wind_speed", 33.5)
    snow_depth = st.session_state.get("mc_snow_depth", 0.0)
    payload_kg = st.session_state.get("mc_payload", 0.0)
    span = data["span"]; apex = data["apex"]; mid_width = data["mid_width"]; eave_height = data["eave_height"]
    number_of_cones = st.session_state.get("mc_ncones", 1)
    secondary_count = st.session_state.get("mc_nribs", 3)
    final_pretension = newton_data.get("final_pretension", 1.0)

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
    f_u_min = 0.0
    if f_u_warp and f_u_weft:
        f_u_min = min(float(f_u_warp), float(f_u_weft))
        membrane_util = (max_principal_N_m / 1000.0) / f_u_min if f_u_min > 0 else 999.0

    # Read the real steel utilizations from Stage 3
    max_steel_util = 0.0
    stage3_det = {}
    stage3_sec = {}
    if stage3_data and "details" in stage3_data:
        stage3_det = stage3_data["details"]
        stage3_sec = stage3_data.get("sections", {})
    for key in ("primary", "rib", "ring", "drop", "spoke"):
        if key in stage3_det and stage3_det[key] is not None:
            u = stage3_det[key].get("max_util", 0.0)
            if u > max_steel_util:
                max_steel_util = u

    coords_to_draw = nd["coordinates"]
    max_deflection_mm = 0.0
    for i in range(len(data["coords_fdm"])):
        d = np.linalg.norm(coords_to_draw[i] - data["coords_fdm"][i])
        if d > max_deflection_mm:
            max_deflection_mm = d * 1000.0
    limit_mm = (span * 1000.0) / 200.0

    _masthead()

    # PAGE 1: EXECUTIVE SUMMARY
    _title_block("Executive Summary", "Verdict and critical results.", page_no=1)
    is_safe = (membrane_util <= 0.70 and max_steel_util <= 0.70 and max_deflection_mm <= limit_mm)
    critical_items = [
        ("Membrane Utilization", f"{membrane_util * 100:.1f}% (Limit 100%)"),
        ("Steel Frame Max Utilization", f"{max_steel_util * 100:.1f}% (Limit 70%)"),
        ("Max Deflection", f"{max_deflection_mm:.2f} mm (Limit {limit_mm:.1f} mm)"),
        ("Pretension Used", f"{final_pretension:.1f} kN/m"),
        ("Solver Convergence", f"{nd.get('reason', 'unknown')} in {nd.get('elapsed_seconds', 0):.2f} s"),
    ]
    _executive_summary_box(is_safe, critical_items)

    st.markdown("### Document Control")
    st.dataframe(pd.DataFrame([
        {"Field": "Project Name", "Value": "SDSe Multi-Cone Roof Analysis"},
        {"Field": "Report ID", "Value": f"SDSe-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}"},
        {"Field": "Date of Issue", "Value": datetime.datetime.now().strftime('%d %B %Y')},
        {"Field": "Revision", "Value": "Rev A"},
        {"Field": "Design Code", "Value": code_choice},
        {"Field": "Design Philosophy", "Value": design_philosophy},
        {"Field": "Issued By", "Value": "SDSe Engineering App (Automated)"},
        {"Field": "Verified By", "Value": "Not verified. This is a design aid."},
    ]), use_container_width=True, hide_index=True)

    st.markdown("### Form-Found Geometry")
    fig = _build_report_figure(data, newton_data)
    st.plotly_chart(fig, use_container_width=True, key="SDSe_report_3d_view")
    png_base64 = _render_figure_to_png_base64(fig)

    # PAGE 2: BASIS OF DESIGN
    _title_block("Basis of Design", "Codes, materials, geometry, and loads.", page_no=2)
    st.markdown(f"""
    - **Code:** {code_choice}
    - **Philosophy:** {design_philosophy}
    - **Fabric:** {fabric_name} ({fabric_family}), f_u = {f_u_min:.1f} kN/m
    - **Steel:** S355 (fy=355 MPa, E=210000 MPa)
    """)
    st.dataframe(pd.DataFrame([
        {"Parameter": "Span", "Value": f"{span:.1f} m"},
        {"Parameter": "Apex", "Value": f"{apex:.1f} m"},
        {"Parameter": "Mid-Width", "Value": f"{mid_width:.1f} m"},
        {"Parameter": "Eave Height", "Value": f"{eave_height:.1f} m"},
        {"Parameter": "Cones", "Value": str(number_of_cones)},
        {"Parameter": "Ribs", "Value": str(secondary_count)},
        {"Parameter": "Wind Speed", "Value": f"{wind_speed:.1f} m/s"},
        {"Parameter": "Snow Depth", "Value": f"{snow_depth:.2f} m"},
        {"Parameter": "Payload", "Value": f"{payload_kg:.0f} kg"},
    ]), use_container_width=True, hide_index=True)

    # PAGE 3: SOLVER TRACEABILITY
    _title_block("Solver Traceability", "FDM and NFDM convergence record.", page_no=3)
    st.markdown(f"""
    - **FDM Status:** {data['solve_ok']} · Residual: {data['residual_fdm']:.4e} N
    - **NFDM Reason:** `{nd.get('reason')}`
    - **Iterations:** {nd['iterations']} · Time: {nd['elapsed_seconds']:.2f} s
    - **Last Step:** {nd.get('last_step_m', 0.0) * 1000:.4f} mm
    - **Max Residual:** {nd.get('max_residual', nd['residual_norm']):.4e} N
    """)

    # PAGE 4: MEMBRANE
    _title_block("Membrane Verification", "Principal stress vs. fabric strength.", page_no=4)
    if f_u_warp and f_u_weft:
        st.dataframe(pd.DataFrame([
            {"Parameter": "σ_max", "Value": f"{max_principal_N_m / 1000.0:.2f} kN/m"},
            {"Parameter": "f_u (min)", "Value": f"{f_u_min:.1f} kN/m"},
            {"Parameter": "Utilization", "Value": f"{membrane_util * 100:.1f}%"},
            {"Parameter": "Limit", "Value": "100%"},
        ]), use_container_width=True, hide_index=True)
        if membrane_util > 0.90:
            st.error(f"✗ DANGER: {membrane_util * 100:.0f}% approaches fabric rupture.")
        elif membrane_util > 0.70:
            st.warning(f"⚠ WARNING: {membrane_util * 100:.0f}%.")
        else:
            st.success(f"✓ SAFE: {membrane_util * 100:.0f}%.")
        st.markdown(f"**Deflection:** {max_deflection_mm:.2f} mm (Limit {limit_mm:.1f} mm) → {'PASS' if max_deflection_mm <= limit_mm else 'FAIL'}")

    # PAGE 5: STEEL & CABLE
    _title_block("Steel & Cable Verification", "Member checks with calculation traceability.", page_no=5)
    
    member_rows = []
    for key, label in [("primary", "Primary_Arch"), ("rib", "Rib_Arch"), ("ring", "Ring_Beam"), ("drop", "Drop_Member"), ("spoke", "Radial_Spoke")]:
        if key not in stage3_det or stage3_det[key] is None:
            continue
        d = stage3_det[key]
        ms = stage3_sec.get(key, "?")
        props = SECTION_PROPERTIES.get(ms, {})
        A_mm2 = props.get("A", 1.0); W_el_mm3 = props.get("W_el", 1.0); I_mm4 = props.get("I", 1.0)
        N_cap = A_mm2 * 355; M_cap = W_el_mm3 * 355
        L_mm = 5.0 * 1000.0
        N_cr = (math.pi ** 2 * 210000 * I_mm4) / (L_mm ** 2) if L_mm > 0 else 1e18
        member_rows.append({
            "Member": label, "Section": ms, "L_eff (m)": "varies",
            "N_Ed (kN)": f"{d.get('max_N', 0)/1000:.1f}", "N_cap (kN)": f"{N_cap / 1000.0:.1f}",
            "N_cr (kN)": f"{N_cr / 1000.0:.1f}", "Util": f"{d.get('max_util', 0.0)* 100:.0f}%",
        })
    if member_rows:
        st.dataframe(pd.DataFrame(member_rows), use_container_width=True, hide_index=True)
        warn = [r for r in member_rows if float(r["Util"].rstrip("%")) > 70.0]
        if warn:
            st.error(f"✗ {len(warn)} member(s) exceed 70%.")
        else:
            st.success("✓ All members pass the 70% cap.")

    st.markdown(f"**Edge Cable:** {newton_data.get('cable_name', '?')} (A={newton_data.get('cable_A_mm2', 0):.1f} mm²)")

    # PAGE 6: FOUNDATION & CONNECTIONS (Now reading from Stage 3)
    _title_block("Foundation & Connections", "Baseplates and corner plates (3D Ground Reactions).", page_no=6)
    
    R = None
    anchor_map = {}
    if stage3_data and "frame_result" in stage3_data:
        R = stage3_data["frame_result"].get("reactions", None)
        anchor_map = stage3_data["frame_result"].get("anchor_to_frame_id", {})
        
    if R is not None and len(data["anchor_idx"]) > 0:
        design_tension_N = float(newton_data.get("design_tension_N", 0.0))
        anchor_idx = data["anchor_idx"]
        primary_sec = stage3_sec.get("primary", "CHS 100")

        st.markdown("### Baseplate Summary")
        bp_rows = []
        for idx in anchor_idx:
            frame_idx = anchor_map.get(idx)
            if frame_idx is None:
                continue
                
            r = R[frame_idx]
            # Pass the real eave height to get the real overturning moment
            design = design_baseplate_and_foundation(r, primary_sec, eave_height)
            bp_rows.append({
                "Node": idx, "X": f"{data['coords_fdm'][idx, 0]:.2f}", "Y": f"{data['coords_fdm'][idx, 1]:.2f}",
                "Fx (kN)": f"{r[0] / 1000.0:.1f}", "Fy (kN)": f"{r[1] / 1000.0:.1f}", "Fz (kN)": f"{r[2] / 1000.0:.1f}",
                "Plate": f"{design['plate_side_mm']}×{design['plate_side_mm']}×{design['plate_thickness_mm']}",
                "Bolts": f"{design['bolt_count']}×M{design['bolt_diameter_mm']}",
                "Pad": f"{design['pad_side_mm']}×{design['pad_side_mm']}",
            })
        st.dataframe(pd.DataFrame(bp_rows), use_container_width=True, hide_index=True)

        st.markdown("### Corner Plate Summary")
        st.info("Corner plates sized for **local vector forces** at each anchor.")
        cp_rows = []
        n_anchors = len(anchor_idx)
        for k in range(n_anchors):
            idx = anchor_idx[k]
            prev_idx = anchor_idx[(k - 1) % n_anchors]
            next_idx = anchor_idx[(k + 1) % n_anchors]
            v_prev = data["coords_fdm"][prev_idx] - data["coords_fdm"][idx]
            v_next = data["coords_fdm"][next_idx] - data["coords_fdm"][idx]
            L_prev = np.linalg.norm(v_prev); L_next = np.linalg.norm(v_next)
            F_res = design_tension_N * np.linalg.norm(v_prev / L_prev + v_next / L_next) if L_prev > 1e-9 and L_next > 1e-9 else design_tension_N
            cp = design_corner_plate(F_res, newton_data.get("cable_d_mm", 10.0), steel_fy_MPa=355)
            cp_rows.append({
                "Node": idx, "T (kN)": f"{F_res / 1000.0:.1f}",
                "Plate": f"{cp['plate_thickness_mm']}×{cp['plate_width_mm']}×{cp['plate_length_mm']}",
                "Weld": f"{cp['weld_size_mm']}×{cp['weld_length_mm']}",
                "Pin": str(cp['pin_diameter_mm']),
                "Weld%": f"{cp['weld_utilization'] * 100:.0f}%",
                "Pin%": f"{cp['pin_utilization'] * 100:.0f}%",
                "Governing Mode": cp.get("governing_mode", "?"),
            })
        st.dataframe(pd.DataFrame(cp_rows), use_container_width=True, hide_index=True)

    # PAGE 7: ASSUMPTIONS & DISCLAIMER
    _title_block("Assumptions & Disclaimer", "Scope, limitations, and legal notice.", page_no=7)
    st.markdown("""
    **Assumptions:**
    - Linear elastic members with tension-field membrane model.
    - ULS Uplift only. Downward loads approximated.
    - Euler buckling with L_eff = 0.7 × L.
    - Multi-cone Cp adaptation based on AS/NZS 1170.2 with cone concentration factor.
    - No fatigue, dynamic wind, or seismic.
    """)
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
        <strong>LEGAL DISCLAIMER</strong><br><br>
        This report is an <strong>automated design aid</strong> produced by the SDSe engineering app.
        It is <strong>NOT a certified engineering document</strong>.<br><br>
        It does <strong>not</strong> carry any PE signature, PE registration, or engineering certification.
        No licensed engineer has reviewed, verified, or signed off on this analysis.<br><br>
        All results, member sizes, and foundation dimensions are <strong>preliminary</strong> and must be
        independently verified by a licensed Professional Engineer before construction.<br><br>
        <strong>The user assumes full legal responsibility for any use of this report.</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # PAGE 8: EXPORT
    _title_block("Export & Copy", "Copy the report or download as a file.", page_no=8)

    report_md = _build_SDSe_markdown_report(
        span, apex, mid_width, eave_height, number_of_cones, secondary_count,
        code_choice, design_philosophy, wind_speed, snow_depth, payload_kg,
        fabric_family, fabric_name, final_pretension, nd,
        member_rows, is_safe, max_deflection_mm, limit_mm, membrane_util, max_steel_util,
        png_base64,
    )

    st.markdown("### Copy the Report")
    st.write("Select the text below and copy it. Or use the download button.")
    st.code(report_md, language="markdown")

    st.download_button(
        label="📥 Download SDSe Report (Markdown)",
        data=report_md,
        file_name=f"SDSe_Analysis_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    st.info("""
    **To print this report as PDF:**
    - **iPhone:** Tap Share → "Print" → pinch-zoom the preview → Share → "Save to Files".
    - **Android:** Tap ⋮ → "Print" → "Save as PDF".
    - **Desktop:** Ctrl+P (Windows) / Cmd+P (Mac) → "Save as PDF".
    """)

    st.markdown("---")
    if st.button("← Back to Lab", key="SDSe_report_bottom_back_lab", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()


# =============================================================================
# MARKDOWN EXPORT
# =============================================================================

def _build_SDSe_markdown_report(span, apex, mid_width, eave_height, cones, ribs,
                                 code, philosophy, wind, snow, payload,
                                 fabric_family, fabric_name, pretension, nd,
                                 member_rows, is_safe, defl_val, defl_limit,
                                 mem_util, steel_util, png_base64):
    lines = [
        "# SDSe ANALYSIS REPORT",
        "",
        f"**Report ID:** SDSe-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}  ",
        f"**Issued:** {datetime.datetime.now().strftime('%d %B %Y')}  ",
        f"**Revision:** Rev A  ",
        "",
        "**This is an automated design aid. Not a certified engineering document.**",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"**Overall Verdict: {'SAFE ✓' if is_safe else 'DANGER ✗'}**",
        "",
        f"- Membrane Utilization: {mem_util * 100:.1f}% (Limit 100%)",
        f"- Steel Max Utilization: {steel_util * 100:.1f}% (Limit 70%)",
        f"- Max Deflection: {defl_val:.2f} mm (Limit {defl_limit:.1f} mm)",
        "",
    ]
    if png_base64:
        lines.append("### Form-Found Geometry")
        lines.append(f"![3D View](data:image/png;base64,{png_base64})")
        lines.append("")
    lines += [
        "---",
        "",
        "## 1. Basis of Design",
        f"- **Design Code:** {code}",
        f"- **Philosophy:** {philosophy}",
        f"- **Fabric:** {fabric_name} ({fabric_family})",
        f"- **Steel:** S355",
        "",
        "## 2. Geometry",
        f"- Span: {span:.1f} m · Apex: {apex:.1f} m · Width: {mid_width:.1f} m · Eave: {eave_height:.1f} m",
        f"- Cones: {cones} · Ribs: {ribs}",
        "",
        "## 3. Load Case",
        f"- Wind: {wind:.1f} m/s · Snow: {snow:.2f} m · Payload: {payload:.0f} kg",
        f"- Pretension: {pretension:.1f} kN/m",
        f"- Solver: `{nd.get('reason')}` in {nd.get('elapsed_seconds', 0):.2f} s",
        "",
        "## 4. Steel Frame",
        "",
        "| Member | Section | L_eff (m) | N_Ed (kN) | N_cap (kN) | N_cr (kN) | Util |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in member_rows:
        lines.append(f"| {r['Member']} | {r['Section']} | {r['L_eff (m)']} | {r['N_Ed (kN)']} | {r['N_cap (kN)']} | {r['N_cr (kN)']} | {r['Util']} |")
    lines += [
        "",
        "## 5. Membrane",
        f"- Utilization: {mem_util * 100:.1f}% (Limit 100%)",
        "",
        "## 6. Deflection",
        f"- Max: {defl_val:.2f} mm (Limit {defl_limit:.1f} mm)",
        "",
        "## 7. Assumptions",
        "- Linear elastic members, tension-field membrane.",
        "- ULS Uplift only. Downward approximated.",
        "- Multi-cone Cp adapted from AS/NZS 1170.2 with cone concentration factor.",
        "- No fatigue, dynamic wind, or seismic.",
        "",
        "## 8. LEGAL DISCLAIMER",
        "",
        "This report is an automated design aid produced by the SDSe engineering app.",
        "It is NOT a certified engineering document.",
        "No PE has signed or verified this analysis.",
        "All results must be independently verified by a licensed PE before construction.",
        "The user assumes full legal responsibility for any use of this report.",
        "",
        "---",
        "",
        "**NOT FOR PE SIGN-OFF**",
        "",
        "This document carries no PE signature and no PE registration number.",
    ]
    return "\n".join(lines)
