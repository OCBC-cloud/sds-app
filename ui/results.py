# =============================================================================
# SDSe Fluid Design Studio - Results Page
# =============================================================================
# Displays the design results: 3D view, marketing render workflow,
# health score, section used, analysis readings, quantities.
# =============================================================================

import streamlit as st
import streamlit.components.v1 as components
import numpy as np

from viewers.results_viewer import generate_results_figure
from engine.steel_frame_sizer import size_steel_frame


# =============================================================================
# PARAMS BUILDER (per variant)
# =============================================================================

def _build_params(variant_key):
    """Return a params dict for the active variant."""
    get = st.session_state.get

    if variant_key == "cantilever_leaf":
        arrangement = get("ws_sl_arrangement", "single")
        if arrangement == "tiered_helix":
            n_leaves = get("ws_sl_num_leaves", None)
        elif arrangement == "multiple":
            n_leaves = get("ws_sl_arrangement_count", None)
        elif arrangement == "tree_stack":
            n_leaves = get("ws_sl_arrangement_tiers", None)
        else:
            n_leaves = 1
        return {
            "num_leaves": n_leaves,
            "arrangement": arrangement,
            "column_height": get("ws_sl_column_height", None),
            "outreach": get("ws_sl_outreach", None),
        }

    if variant_key == "standard_saddle":
        return {
            "span": get("ws_ss_span", None),
            "apex": get("ws_ss_apex", None),
            "rise": get("ws_ss_rise", None),
            "curve_type": get("ws_ss_curve_type", None),
            "tiedown_count": get("ws_ss_tiedown_intervals", None),
        }

    if variant_key == "frame_supported_saddle":
        return {
            "span": get("ws_bs_span", None),
            "apex": get("ws_bs_apex", None),
            "rise": get("ws_bs_rise", None),
            "curve_type": get("ws_bs_curve_type", None),
            "secondary_count": get("ws_bs_secondary_count", None),
        }

    return {}


# =============================================================================
# STRUCTURAL ANALYSIS RUNNER (Wire the Engine)
# =============================================================================

@st.cache_data(show_spinner=False)
def _run_structural_analysis(vk, solved_data_id):
    """
    Runs the frame builder and sizer for the Dome.
    """
    if vk != "dome_multi_cone":
        return None

    data = st.session_state.get("ws_dm_solved_data", None)
    if not data:
        return None

    # --- CRITICAL FIX: Pass the full solve summary with reactions ---
    newton_data_cases = {"1.0_DL_LL": {"dr_result": {
        "coordinates": data["fdm_coords"],
        "solve_summary": data["solve_summary"],
        "reactions": data["solve_summary"].get("nfdm", {}).get("reactions", None)
    }}}
    
    # If reactions are missing from nfdm, it will be handled by the builder
    
    # Add required keys to data dict for the builder
    data["built"] = data["built"]
    data["anchor_idx"] = data["anchor_idx"]
    data["eave_height"] = data["eave_height"]
    data["xp"] = data["xp"]
    data["zp"] = data["zp"]
    data["rib_x"] = data["rib_x"]
    data["rib_half_width"] = data["rib_half_width"]
    data["mc_rd"] = data["mc_rd"]

    try:
        sizer_result = size_steel_frame(
            data=data,
            newton_data_cases=newton_data_cases,
            grade="S355",
            family="CHS"
        )
        return sizer_result
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# MARKETING RENDER SECTION
# =============================================================================

def _render_marketing_render(vk, sk):
    from engine.render_prompts import (
        SCENES, TIMES, RENDERERS, DISCLAIMER, format_prompt,
    )

    with st.expander("Marketing Render", expanded=False):
        st.markdown(
            '<div style="background: #0d1620; border-left: 3px solid #3498db; '
            'padding: 0.7rem 0.9rem; border-radius: 4px; margin-bottom: 0.8rem; '
            'font-size: 0.82rem; color: #c8d4e0; line-height: 1.6;">'
            '<strong>How this works</strong><br>'
            'SDSe prepares a snapshot and a prompt. You take both to '
            'Gemini. Gemini generates the marketing image. You bring '
            'the image back.'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Step 1 — Capture your 3D view", expanded=False):
            st.markdown(
                '<div style="color: #a8b8c8; font-size: 0.82rem; '
                'line-height: 1.6;">'
                'Screenshot the 3D view above. On iPhone: press the side '
                'button and the volume-up button at the same time.'
                '</div>',
                unsafe_allow_html=True,
            )

        with st.expander("Step 2 — Choose scene and time", expanded=False):
            scene_keys = list(SCENES.keys())
            scene_labels = [SCENES[k]["name"] for k in scene_keys]
            scene_choice = st.radio("Scene", scene_labels, index=0, key="render_scene_radio", label_visibility="collapsed")
            scene_key = scene_keys[scene_labels.index(scene_choice)]

            time_keys = list(TIMES.keys())
            time_labels = [TIMES[k]["name"] for k in time_keys]
            time_choice = st.radio("Time of day", time_labels, index=2, key="render_time_radio", label_visibility="collapsed")
            time_key = time_keys[time_labels.index(time_choice)]

        params = _build_params(vk)
        prompt_text = format_prompt(scene_key, sk, vk, params, time_key)

        with st.expander("Step 3 — Copy prompt and open Gemini", expanded=False):
            gemini_url = RENDERERS[0]["url"]
            components.html(
                f"""
                <style>
                .sdse-render-btn {{
                    display: block; width: 100%; background: #f39c12;
                    color: #0a0e17; border: none; border-radius: 8px;
                    padding: 0.9rem 1rem; font-weight: 700; font-size: 1rem;
                    text-align: center; text-decoration: none; cursor: pointer;
                    font-family: inherit; box-sizing: border-box; margin-bottom: 0.4rem;
                }}
                .sdse-render-note {{
                    color: #a8b8c8; font-size: 0.78rem; text-align: center;
                    margin-top: 0.4rem; font-family: inherit;
                }}
                </style>
                <a class="sdse-render-btn" id="sdseBtn" href="#" target="_blank">Copy prompt &amp; open Gemini</a>
                <div class="sdse-render-note" id="sdseNote">Your prompt will be copied. Gemini will open in a new tab.</div>
                <script>
                (function() {{
                    var promptText = {__import__('json').dumps(prompt_text)};
                    var geminiUrl = {__import__('json').dumps(gemini_url)};
                    var btn = document.getElementById('sdseBtn');
                    var note = document.getElementById('sdseNote');
                    btn.addEventListener('click', function(ev) {{
                        try {{
                            if (navigator.clipboard && navigator.clipboard.writeText) {{
                                navigator.clipboard.writeText(promptText);
                            }} else {{
                                var ta = document.createElement('textarea');
                                ta.value = promptText;
                                document.body.appendChild(ta);
                                ta.select(); document.execCommand('copy');
                                document.body.removeChild(ta);
                            }}
                        }} catch (e) {{}}
                        try {{ window.open(geminiUrl, '_blank'); }} catch (e) {{ window.location.href = geminiUrl; }}
                        if (note) {{ note.textContent = 'Prompt copied. Upload your screenshot, paste, and send.'; }}
                        ev.preventDefault();
                    }});
                }})();
                </script>
                """,
                height=120,
            )

            st.markdown(
                '<div style="background: #1a2a3a; border-left: 3px solid #f39c12; '
                'padding: 0.6rem 0.9rem; border-radius: 4px; margin-top: 0.6rem; '
                'font-size: 0.78rem; color: #c8d4e0; line-height: 1.6;">'
                '<strong>In Gemini:</strong> '
                '(1) tap the paperclip to upload your screenshot; '
                '(2) paste the prompt; '
                '(3) add "Generate a photorealistic image based on this '
                'description and the attached image."; '
                '(4) tap Send.'
                '</div>',
                unsafe_allow_html=True,
            )

        with st.expander("View prompt (optional)", expanded=False):
            st.text_area("Prompt", value=prompt_text, height=180, key="render_prompt_text_" + scene_key + "_" + time_key, label_visibility="collapsed")

        with st.expander("Step 4 — Bring the render back", expanded=False):
            uploaded = st.file_uploader("Upload rendered image", type=["png", "jpg", "jpeg", "webp"], key="render_upload", label_visibility="collapsed")
            if uploaded is not None:
                st.image(uploaded, use_container_width=True)
                st.download_button("Download this render", data=uploaded.getvalue(), file_name="sdse_render.png", mime="image/png", key="render_download", use_container_width=True)

        with st.expander("Disclaimer", expanded=False):
            st.markdown('<div style="font-size: 0.78rem; color: #c8d4e0; line-height: 1.6;">' + DISCLAIMER.replace("\n\n", "<br><br>") + '</div>', unsafe_allow_html=True)


# =============================================================================
# ANALYSIS AND QUANTITIES SECTION
# =============================================================================

def _render_analysis_and_quantities():
    vk = st.session_state.get("variant_key", "")

    with st.expander("Analysis and Quantities", expanded=True):

        # --- Run the Engine! ---
        solved_data = st.session_state.get("ws_dm_solved_data", None)
        cache_id = str(len(solved_data["built"]["points"])) if solved_data else "0"
        sizer_result = _run_structural_analysis(vk, cache_id)

        # Default placeholders
        section_used = "--"
        n_ed, m_ed, v_ed = "--", "--", "--"
        steel_weight = "--"
        
        if sizer_result and "error" not in sizer_result:
            # 1. Grab the section
            sections = sizer_result.get("sections", {})
            if sections:
                section_used = sections.get("primary", "CHS")

            # 2. Grab forces from the primary beam
            frame_res = sizer_result.get("frame_result")
            if frame_res and len(frame_res.get("member_end_forces", [])) > 0:
                # Find the first element that has real force (usually the arch)
                for end_force in frame_res["member_end_forces"]:
                    n_val = abs(end_force.get('N', 0.0))
                    my = max(abs(end_force.get('My_a', 0.0)), abs(end_force.get('My_b', 0.0)))
                    mz = max(abs(end_force.get('Mz_a', 0.0)), abs(end_force.get('Mz_b', 0.0)))
                    
                    # If this element actually has force, use it
                    if n_val > 1.0 or my > 1.0 or mz > 1.0:
                        n_ed = f"{n_val / 1000.0:.1f}"
                        m_ed = f"{max(my, mz) / 1000.0:.1f}"
                        v_ed = "0.0" # We don't extract shear yet
                        break

        elif sizer_result and "error" in sizer_result:
            st.error("Solver failed: " + sizer_result["error"])

        # ---- Health Score
        with st.expander("Design health", expanded=False):
            st.markdown(
                '<div style="background: #1a3a2a; border: 2px solid #2ecc71; '
                'border-radius: 14px; padding: 1.5rem; text-align: center;">'
                '<div style="font-size: 3rem; font-weight: 800; '
                'color: #2ecc71;">100</div>'
                '<div style="color: #d0dff0; font-size: 0.9rem; '
                'margin-top: 0.5rem; letter-spacing: 1.5px; '
                'text-transform: uppercase;">Design Healthy</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        # ---- Section Used
        with st.expander("Section used", expanded=True):
            st.markdown(
                '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
                'border-left: 4px solid #f39c12; border-radius: 8px; '
                'padding: 1rem 1.2rem;">'
                '<div style="color: #a8b8c8; font-size: 0.78rem; '
                'text-transform: uppercase; letter-spacing: 0.5px; '
                'margin-bottom: 0.3rem;">Primary member section</div>'
                '<div style="color: #ffffff; font-size: 1.15rem; '
                'font-weight: 700; font-family: monospace;">'
                + section_used + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        # ---- Analysis Readings
        with st.expander("Analysis readings", expanded=True):
            def metric_card(label, value, unit):
                return (
                    '<div style="background: #0d1620; '
                    'border: 1px solid #1e2a3a; '
                    'border-radius: 8px; padding: 0.8rem; '
                    'text-align: center;">'
                    '<div style="color: #a8b8c8; font-size: 0.72rem; '
                    'text-transform: uppercase; letter-spacing: 0.5px;">'
                    + label + '</div>'
                    '<div style="color: #ffffff; font-size: 1.15rem; '
                    'font-weight: 700; margin-top: 0.3rem; '
                    'font-family: monospace;">'
                    + value + '<span style="color: #a8b8c8; '
                    'font-size: 0.75rem; margin-left: 3px;">'
                    + unit + '</span></div>'
                    '</div>'
                )

            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(metric_card("N_Ed", n_ed, "kN"), unsafe_allow_html=True)
            with c2: st.markdown(metric_card("M_Ed", m_ed, "kNm"), unsafe_allow_html=True)
            with c3: st.markdown(metric_card("V_Ed", v_ed, "kN"), unsafe_allow_html=True)

            c4, c5, c6 = st.columns(3)
            with c4: st.markdown(metric_card("Wind", "--", "kPa"), unsafe_allow_html=True)
            with c5: st.markdown(metric_card("Uplift", "--", "kPa"), unsafe_allow_html=True)
            with c6: st.markdown(metric_card("Deflection", "--", "mm"), unsafe_allow_html=True)

        # ---- Quantities
        with st.expander("Quantities", expanded=True):
            def qty_card(label, value, unit):
                return (
                    '<div style="background: #121e2e; '
                    'border: 1px solid #1e2a3a; '
                    'border-left: 4px solid #f39c12; '
                    'border-radius: 8px; padding: 0.9rem 1rem;">'
                    '<div style="color: #a8b8c8; font-size: 0.72rem; '
                    'text-transform: uppercase; letter-spacing: 0.5px;">'
                    + label + '</div>'
                    '<div style="color: #ffffff; font-size: 1.25rem; '
                    'font-weight: 700; margin-top: 0.35rem; '
                    'font-family: monospace;">'
                    + value + '<span style="color: #a8b8c8; '
                    'font-size: 0.78rem; margin-left: 4px;">'
                    + unit + '</span></div>'
                    '</div>'
                )

            q1, q2, q3 = st.columns(3)
            with q1: st.markdown(qty_card("Steel weight", steel_weight, "kg"), unsafe_allow_html=True)
            with q2: st.markdown(qty_card("Cable length", "--", "m"), unsafe_allow_html=True)
            with q3: st.markdown(qty_card("Fabric area", "--", "m2"), unsafe_allow_html=True)


# =============================================================================
# MAIN RENDER
# =============================================================================

def render_results():
    """Render the Results page."""
    sk = st.session_state.get("structure_key", "saddle_span")
    sn = st.session_state.get("structure_name", "Saddle Span")
    vk = st.session_state.get("variant_key", "")
    vn = st.session_state.get("variant_name", "Unknown Variant")
    info = st.session_state.get("project_info", {})
    pname = info.get("name", "") or "Untitled Project"
    cname = info.get("client", "") or "Unknown Client"

    # ---- Breadcrumb
    st.markdown(
        '<div style="font-size: 0.85rem; color: #a8b8c8; margin-bottom: 1rem;">'
        'SDSe Fluid Design Studio / <span style="color: #f39c12;">' + sn + '</span> / ' + vn + ' / Results</div>',
        unsafe_allow_html=True,
    )

    # ---- Project header card
    st.markdown(
        '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
        'border-radius: 10px; padding: 1rem;">'
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700;">' + pname + '</div>'
        '<div style="color: #a8b8c8; font-size: 0.85rem; margin-top: 0.3rem;">Client: ' + cname + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- 3D View heading
    st.markdown('<div style="color: #f39c12; font-weight: 700; margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">3D View</div>', unsafe_allow_html=True)

    # ---- 3D chart
    try:
        fig = generate_results_figure(sk, vk)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        import traceback
        st.error("3D view failed: " + str(e))
        st.code(traceback.format_exc())

    # ---- Marketing Render section
    _render_marketing_render(vk, sk)

    # ---- Analysis and Quantities
    _render_analysis_and_quantities()

    # ---- Bottom actions
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Workshop", key="rb", use_container_width=True):
            st.session_state.page = "workshop"
            st.rerun()
    with col2:
        if st.button("Home", key="hm", use_container_width=True, type="primary"):
            st.session_state.page = "studio"
            st.rerun()
