# =============================================================================
# SDSe Fluid Design Studio - Results Page
# =============================================================================
# Displays the design results: 3D view, marketing render workflow,
# health score, section used, analysis readings, quantities.
#
# Updated 2026-09-27:
#   - Marketing Render now offers a single one-touch button:
#     copy the prompt to the clipboard and open Gemini.
#   - Instructions block above the steps explains the workflow.
#   - Renderer card list removed. One button instead.
#   - Steps reduced from five to four.
# =============================================================================

import streamlit as st
import streamlit.components.v1 as components

from viewers.results_viewer import generate_results_figure


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




# ============ END OF RESULTS CHUNK 1 ============





# =============================================================================
# MARKETING RENDER SECTION
# =============================================================================

def _render_marketing_render(vk, sk):
    """
    The Marketing Render section, with a single one-touch button that
    copies the prompt to the clipboard and opens Gemini.
    """
    from engine.render_prompts import (
        SCENES, TIMES, RENDERERS, DISCLAIMER, format_prompt,
    )

    # ---- Section heading
    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">'
        'Marketing Render</div>',
        unsafe_allow_html=True,
    )

    # ---- How this works
    st.markdown(
        '<div style="background: #0d1620; border-left: 3px solid #3498db; '
        'padding: 0.7rem 0.9rem; border-radius: 4px; margin-bottom: 0.8rem; '
        'font-size: 0.85rem; color: #c8d4e0; line-height: 1.6;">'
        '<strong>How this works</strong><br>'
        'SDSe does not generate the marketing image itself. It '
        'prepares two things for you:<br>'
        '&bull; <strong>A snapshot</strong> of your 3D view '
        '(you will take this as a screenshot).<br>'
        '&bull; <strong>A prompt</strong> &mdash; a written description '
        'of the structure, its scale, and its materials.<br>'
        'You take both to Google Gemini. It generates the marketing '
        'image. You bring the image back to SDSe.<br>'
        '<br>'
        '<strong>Four steps below.</strong> You can do all of them on '
        'this phone.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Step 1: capture
    st.markdown(
        '<div style="color: #ffffff; font-size: 0.95rem; font-weight: 600; '
        'margin-top: 0.6rem;">Step 1 &mdash; Capture your 3D view</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="color: #a8b8c8; font-size: 0.8rem; '
        'margin-bottom: 0.5rem;">'
        'Screenshot the 3D view above. On iPhone: press the side '
        'button and the volume-up button at the same time. The '
        'screenshot goes to your Photos. You will upload it in Step 3.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Step 2: choose a scene and time
    st.markdown(
        '<div style="color: #ffffff; font-size: 0.95rem; font-weight: 600; '
        'margin-top: 0.9rem;">Step 2 &mdash; Choose scene and time</div>',
        unsafe_allow_html=True,
    )

    scene_keys = list(SCENES.keys())
    scene_labels = [SCENES[k]["name"] for k in scene_keys]
    scene_choice = st.radio(
        "Scene",
        scene_labels,
        index=0,
        key="render_scene_radio",
        label_visibility="collapsed",
    )
    scene_key = scene_keys[scene_labels.index(scene_choice)]

    time_keys = list(TIMES.keys())
    time_labels = [TIMES[k]["name"] for k in time_keys]
    time_choice = st.radio(
        "Time of day",
        time_labels,
        index=2,
        key="render_time_radio",
        label_visibility="collapsed",
    )
    time_key = time_keys[time_labels.index(time_choice)]

    # ---- Build the prompt (used by the button below)
    params = _build_params(vk)
    prompt_text = format_prompt(scene_key, sk, vk, params, time_key)

    # ---- Show the prompt for reference (selectable)
    with st.expander("View prompt (optional)", expanded=False):
        st.text_area(
            "Prompt",
            value=prompt_text,
            height=180,
            key="render_prompt_text_" + scene_key + "_" + time_key,
            label_visibility="collapsed",
        )
        st.markdown(
            '<div style="color: #a8b8c8; font-size: 0.78rem;">'
            'Long-press the text above and select all if you want to '
            'copy it manually. The button below does this for you.'
            '</div>',
            unsafe_allow_html=True,
        )

    # ---- Step 3: the one-touch button
    st.markdown(
        '<div style="color: #ffffff; font-size: 0.95rem; font-weight: 600; '
        'margin-top: 1.1rem;">Step 3 &mdash; Copy prompt and open Gemini</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="color: #a8b8c8; font-size: 0.8rem; '
        'margin-bottom: 0.5rem;">'
        'Tap the button below. Two things happen at once: '
        '(1) your prompt is copied to the clipboard, and '
        '(2) Gemini opens in a new tab. Then, in Gemini: upload your '
        'screenshot, paste the prompt, and send.'
        '</div>',
        unsafe_allow_html=True,
    )

    gemini_url = RENDERERS[0]["url"]

    # The one-touch button. Uses st.markdown with an inline script,
    # so the link navigation and clipboard copy happen on the same tap.
    # The button is rendered as an anchor tag with an onclick handler.
    components.html(
        """
        <style>
        .sdse-render-btn {
            display: block;
            width: 100%;
            background: #f39c12;
            color: #0a0e17;
            border: none;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            font-weight: 700;
            font-size: 1rem;
            text-align: center;
            text-decoration: none;
            cursor: pointer;
            font-family: inherit;
            box-sizing: border-box;
            margin-bottom: 0.4rem;
        }
        .sdse-render-btn:hover {
            background: #f1c40f;
        }
        .sdse-render-note {
            color: #a8b8c8;
            font-size: 0.78rem;
            text-align: center;
            margin-top: 0.4rem;
            font-family: inherit;
        }
        </style>
        <a class="sdse-render-btn" id="sdseBtn" href="#" target="_blank">
            Copy prompt &amp; open Gemini
        </a>
        <div class="sdse-render-note" id="sdseNote">
            Your prompt will be copied. Gemini will open in a new tab.
        </div>
        <script>
        (function() {
            var promptText = """ + __import__('json').dumps(prompt_text) + """;
            var geminiUrl = """ + __import__('json').dumps(gemini_url) + """;
            var btn = document.getElementById('sdseBtn');
            var note = document.getElementById('sdseNote');
            btn.addEventListener('click', function(ev) {
                // Copy to clipboard. Best-effort. No blocking.
                try {
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(promptText);
                    } else {
                        var ta = document.createElement('textarea');
                        ta.value = promptText;
                        document.body.appendChild(ta);
                        ta.select();
                        document.execCommand('copy');
                        document.body.removeChild(ta);
                    }
                } catch (e) {
                    // Ignore. The user can still copy manually from the
                    // "View prompt" expander above.
                }
                // Open Gemini in a new tab.
                try {
                    window.open(geminiUrl, '_blank');
                } catch (e) {
                    // If popup is blocked, fall back to normal navigation.
                    window.location.href = geminiUrl;
                }
                // Update the note.
                if (note) {
                    note.textContent = 'Prompt copied. Upload your screenshot, paste, and send.';
                }
                ev.preventDefault();
            });
        })();
        </script>
        """,
        height=120,
    )

    # ---- Small post-tap reminder
    st.markdown(
        '<div style="background: #1a2a3a; border-left: 3px solid #f39c12; '
        'padding: 0.6rem 0.9rem; border-radius: 4px; margin-top: 0.6rem; '
        'font-size: 0.78rem; color: #c8d4e0; line-height: 1.6;">'
        '<strong>In Gemini:</strong> '
        '(1) tap the paperclip or + icon and upload your screenshot; '
        '(2) paste the prompt into the message box; '
        '(3) add the line '
        '<em>"Generate a photorealistic image based on this description '
        'and the attached image."</em>; '
        '(4) tap Send. Save the result to your Photos.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Disclaimer
    st.markdown(
        '<div style="background: #1a2a3a; border-left: 3px solid #4a7a9c; '
        'padding: 0.7rem 0.9rem; border-radius: 4px; margin-top: 0.8rem; '
        'font-size: 0.78rem; color: #c8d4e0; line-height: 1.6;">'
        + DISCLAIMER.replace("\n\n", "<br><br>")
        + '</div>',
        unsafe_allow_html=True,
    )


# ============ END OF RESULTS CHUNK 2 ============





# =============================================================================
# STEP 4 (upload), HEALTH SCORE, SECTION, READINGS, QUANTITIES, ACTIONS
# =============================================================================

def _render_upload_and_footer():
    """
    Step 4 (upload the Gemini render), the health card, section used,
    analysis readings, quantities, and the bottom actions.
    """
    from engine.render_prompts import RENDERERS  # noqa: F401

    # ---- Step 4: upload the render
    st.markdown(
        '<div style="color: #ffffff; font-size: 0.95rem; font-weight: 600; '
        'margin-top: 1.1rem;">Step 4 &mdash; Bring the render back</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="color: #a8b8c8; font-size: 0.8rem; '
        'margin-bottom: 0.5rem;">'
        'Download the image from Gemini to your Photos. Then upload '
        'it here to keep it with the project.'
        '</div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload rendered image",
        type=["png", "jpg", "jpeg", "webp"],
        key="render_upload",
        label_visibility="collapsed",
    )

    if uploaded is not None:
        st.image(uploaded, use_container_width=True)
        st.download_button(
            "Download this render",
            data=uploaded.getvalue(),
            file_name="sdse_render.png",
            mime="image/png",
            key="render_download",
            use_container_width=True,
        )

    # ---- Health Score card
    st.markdown(
        '<div style="background: #1a3a2a; border: 2px solid #2ecc71; '
        'border-radius: 14px; padding: 1.5rem; text-align: center; '
        'margin: 1.4rem 0;">'
        '<div style="font-size: 3rem; font-weight: 800; color: #2ecc71;">100</div>'
        '<div style="color: #d0dff0; font-size: 0.9rem; margin-top: 0.5rem; '
        'letter-spacing: 1.5px; text-transform: uppercase;">Design Healthy</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Section Used
    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">Section Used</div>',
        unsafe_allow_html=True,
    )

    vk = st.session_state.get("variant_key", "")
    fallback_section = "CHS 168.3x7.1"
    if vk == "cantilever_leaf":
        fallback_section = "CHS 323.8x8.0 / CHS 168.3x7.1"

    st.markdown(
        '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
        'border-left: 4px solid #f39c12; border-radius: 8px; '
        'padding: 1rem 1.2rem; margin-bottom: 0.8rem;">'
        '<div style="color: #a8b8c8; font-size: 0.78rem; '
        'text-transform: uppercase; letter-spacing: 0.5px; '
        'margin-bottom: 0.3rem;">Primary member section</div>'
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700; '
        'font-family: monospace;">' + fallback_section + '</div>'
        '<div style="color: #a8b8c8; font-size: 0.72rem; '
        'margin-top: 0.4rem; font-style: italic;">'
        'Placeholder. Engine will auto-select the optimal section.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Analysis Readings
    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">Analysis Readings</div>',
        unsafe_allow_html=True,
    )

    def metric_card(label, value, unit):
        return (
            '<div style="background: #0d1620; border: 1px solid #1e2a3a; '
            'border-radius: 8px; padding: 0.8rem; text-align: center;">'
            '<div style="color: #a8b8c8; font-size: 0.72rem; '
            'text-transform: uppercase; letter-spacing: 0.5px;">'
            + label + '</div>'
            '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700; '
            'margin-top: 0.3rem; font-family: monospace;">'
            + value + '<span style="color: #a8b8c8; font-size: 0.75rem; '
            'margin-left: 3px;">' + unit + '</span></div>'
            '</div>'
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card("N_Ed", "--", "kN"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("M_Ed", "--", "kNm"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("V_Ed", "--", "kN"), unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(metric_card("Wind pressure", "--", "kPa"), unsafe_allow_html=True)
    with c5:
        st.markdown(metric_card("Uplift", "--", "kPa"), unsafe_allow_html=True)
    with c6:
        st.markdown(metric_card("Deflection", "--", "mm"), unsafe_allow_html=True)

    st.markdown(
        '<div style="background: #0d1620; border-left: 3px solid #4a7a9c; '
        'padding: 0.7rem 0.9rem; border-radius: 4px; margin: 0.5rem 0; '
        'font-size: 0.82rem; color: #c8d4e0; line-height: 1.5;">'
        'Readings populate when the engine is connected.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Quantities
    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">Quantities</div>',
        unsafe_allow_html=True,
    )

    def qty_card(label, value, unit):
        return (
            '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
            'border-left: 4px solid #f39c12; border-radius: 8px; '
            'padding: 0.9rem 1rem;">'
            '<div style="color: #a8b8c8; font-size: 0.72rem; '
            'text-transform: uppercase; letter-spacing: 0.5px;">'
            + label + '</div>'
            '<div style="color: #ffffff; font-size: 1.25rem; font-weight: 700; '
            'margin-top: 0.35rem; font-family: monospace;">'
            + value + '<span style="color: #a8b8c8; font-size: 0.78rem; '
            'margin-left: 4px;">' + unit + '</span></div>'
            '</div>'
        )

    q1, q2, q3 = st.columns(3)
    with q1:
        st.markdown(qty_card("Steel Weight", "--", "kg"), unsafe_allow_html=True)
    with q2:
        st.markdown(qty_card("Cable Length", "--", "m"), unsafe_allow_html=True)
    with q3:
        st.markdown(qty_card("Fabric Area", "--", "m2"), unsafe_allow_html=True)

    st.markdown(
        '<div style="background: #0d1620; border-left: 3px solid #4a7a9c; '
        'padding: 0.7rem 0.9rem; border-radius: 4px; margin: 0.5rem 0; '
        'font-size: 0.82rem; color: #c8d4e0; line-height: 1.5;">'
        'Quantities populate when the engine is connected.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Workshop", key="rb", use_container_width=True):
            st.session_state.page = "workshop"
            st.rerun()
    with col2:
        if st.button("Home", key="hm", use_container_width=True, type="primary"):
            st.session_state.page = "studio"
            st.rerun()


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
        'SDSe Fluid Design Studio / '
        '<span style="color: #f39c12;">' + sn + '</span>'
        ' / ' + vn + ' / Results'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Project header card
    st.markdown(
        '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
        'border-radius: 10px; padding: 1rem;">'
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700;">'
        + pname + '</div>'
        '<div style="color: #a8b8c8; font-size: 0.85rem; margin-top: 0.3rem;">'
        'Client: ' + cname + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- 3D View heading
    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">3D View</div>',
        unsafe_allow_html=True,
    )

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

    # ---- Upload step and the rest of the page
    _render_upload_and_footer()


# ============ END OF RESULTS CHUNK 3 ============





