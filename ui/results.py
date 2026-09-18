# =============================================================================
# SDSe Fluid Design Studio - Results Page
# =============================================================================
# Displays the design results: 3D view, structure summary,
# marketing render workflow, health score, section used,
# analysis readings, quantities.
#
# Updated 2026-09-18:
#   - Marketing Render section added (external renderer workflow)
# =============================================================================

import streamlit as st

from viewers.results_viewer import generate_results_figure
from viewers.figures._descriptions import get_structure_summary


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

    # ---- 3D View
    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">3D View</div>',
        unsafe_allow_html=True,
    )

    try:
        fig = generate_results_figure(sk, vk)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        import traceback
        st.error("3D view failed: " + str(e))
        st.code(traceback.format_exc())

    # ---- Structure summary (below 3D view)
    summary_html = get_structure_summary(vk)
    if summary_html:
        st.markdown(summary_html, unsafe_allow_html=True)






    # ---- Marketing Render (external renderer workflow)
    st.markdown(
        '<div style="color: #f39c12; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; font-size: 1.05rem;">'
        'Marketing Render</div>',
        unsafe_allow_html=True,
    )

    from engine.render_prompts import (
        SCENES, RENDERERS, DISCLAIMER, format_prompt,
    )

    st.markdown(
        '<div style="background: #0d1620; border-left: 3px solid #3498db; '
        'padding: 0.7rem 0.9rem; border-radius: 4px; margin-bottom: 0.8rem; '
        'font-size: 0.85rem; color: #c8d4e0; line-height: 1.6;">'
        '<strong>Turn your structure into a marketing image.</strong><br>'
        'Follow the steps below. SDSe prepares the snapshot and the '
        'prompt. You take them to an external renderer of your choice. '
        'Bring the result back.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Step 1: capture
    st.markdown(
        '<div style="color: #ffffff; font-size: 0.95rem; font-weight: 600; '
        'margin-top: 0.6rem;">Step 1 - Capture your 3D view</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="color: #a8b8c8; font-size: 0.8rem; '
        'margin-bottom: 0.5rem;">'
        'Take a screenshot of the 3D view above. You will upload it '
        'to the external renderer in Step 4.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Step 2: choose a scene
    st.markdown(
        '<div style="color: #ffffff; font-size: 0.95rem; font-weight: 600; '
        'margin-top: 0.9rem;">Step 2 - Choose a scene</div>',
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

    # ---- Step 3: build and show the prompt
    st.markdown(
        '<div style="color: #ffffff; font-size: 0.95rem; font-weight: 600; '
        'margin-top: 0.9rem;">Step 3 - Your prompt</div>',
        unsafe_allow_html=True,
    )

    render_params = {
        "num_leaves": st.session_state.get("ws_sl_num_leaves", None),
        "arrangement": st.session_state.get("ws_sl_arrangement", None),
        "column_height": st.session_state.get("ws_sl_column_height", None),
        "outreach": st.session_state.get("ws_sl_outreach", None),
    }

    prompt_text = format_prompt(scene_key, sk, vk, render_params)

    st.text_area(
        "Prompt (select all, copy)",
        value=prompt_text,
        height=180,
        key="render_prompt_text",
    )

    st.markdown(
        '<div style="color: #a8b8c8; font-size: 0.8rem; '
        'margin-top: -0.4rem; margin-bottom: 0.8rem;">'
        'Long-press the text above, select all, and copy.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Step 4: open an external renderer
    st.markdown(
        '<div style="color: #ffffff; font-size: 0.95rem; font-weight: 600; '
        'margin-top: 0.9rem;">Step 4 - Open an external renderer</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="color: #a8b8c8; font-size: 0.8rem; '
        'margin-bottom: 0.5rem;">'
        'Tap one of the options below. It opens in a new tab. Paste '
        'the prompt and upload your snapshot.'
        '</div>',
        unsafe_allow_html=True,
    )

    for r in RENDERERS:
        st.markdown(
            '<a href="' + r["url"] + '" target="_blank" '
            'style="display: block; background: #121e2e; '
            'border: 1px solid #1e2a3a; border-left: 4px solid #f39c12; '
            'border-radius: 8px; padding: 0.8rem 1rem; '
            'margin-bottom: 0.5rem; text-decoration: none;">'
            '<div style="color: #ffffff; font-weight: 600; '
            'font-size: 0.95rem;">' + r["name"] + '</div>'
            '<div style="color: #a8b8c8; font-size: 0.78rem; '
            'margin-top: 0.2rem;">' + r["note"] + '</div>'
            '</a>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="background: #1a2a3a; border-left: 3px solid #4a7a9c; '
        'padding: 0.7rem 0.9rem; border-radius: 4px; margin-top: 0.8rem; '
        'font-size: 0.78rem; color: #c8d4e0; line-height: 1.6;">'
        + DISCLAIMER.replace("\n\n", "<br><br>")
        + '</div>',
        unsafe_allow_html=True,
    )

    # ---- Step 5: upload the render
    st.markdown(
        '<div style="color: #ffffff; font-size: 0.95rem; font-weight: 600; '
        'margin-top: 1rem;">Step 5 - Upload your render</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="color: #a8b8c8; font-size: 0.8rem; '
        'margin-bottom: 0.5rem;">'
        'After the external renderer generates the image, download it, '
        'then upload it here.'
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

