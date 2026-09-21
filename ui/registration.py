# =============================================================================
# SDSe Fluid Design Studio - Registration Page
# =============================================================================
# Project meta inputs + variant selection.
# Date is captured automatically on first visit and never overwritten.
# Variants are read from data/structures.py (single source of truth).
#
# History:
#   2026-09-21 - Variants with available=False are now hidden entirely
#                instead of shown greyed out. This keeps the
#                Registration page clean. Unbuilt variants are
#                reachable later from inside the workshop Section 1.
# =============================================================================

from datetime import datetime

import streamlit as st

from data.structures import STRUCTURE_VARIANTS


def render_registration():
    structure_key = st.session_state.get("structure_key", "saddle_span")
    structure_name = st.session_state.get("structure_name", "Saddle Span")

    if "project_info" not in st.session_state:
        st.session_state.project_info = {
            "name": "",
            "client": "",
            "location": "",
            "reference": "",
            "engineer": "",
            "date": "",
        }

    info = st.session_state.project_info

    # Auto-capture date/time on first visit and never overwrite.
    if not info.get("date"):
        info["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    st.markdown(
        '<div style="font-size: 0.85rem; color: #a8b8c8; margin-bottom: 1.2rem;">'
        'SDSe Fluid Design Studio / '
        '<span style="color: #f39c12; font-weight: 600;">' + structure_name + '</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700; '
        'margin: 0 0 0.6rem 0; padding-bottom: 0.4rem; '
        'border-bottom: 1px solid #1e2a3a;">Project Information</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        info["name"] = st.text_input("Project Name", value=info.get("name", ""), key="reg_pname")
        info["client"] = st.text_input("Client Name", value=info.get("client", ""), key="reg_cname")
        info["location"] = st.text_input("Location", value=info.get("location", ""), key="reg_loc")
    with col2:
        info["reference"] = st.text_input("Project Reference", value=info.get("reference", ""), key="reg_ref")
        info["engineer"] = st.text_input("Engineer", value=info.get("engineer", ""), key="reg_eng")
        st.caption("Created: " + info["date"])

    st.session_state.project_info = info

    st.markdown(
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; padding-bottom: 0.4rem; '
        'border-bottom: 1px solid #1e2a3a;">Choose a Variant</div>',
        unsafe_allow_html=True,
    )

    all_variants = STRUCTURE_VARIANTS.get(structure_key, [])

    # Skip unavailable variants entirely (hidden, not greyed out).
    variants = [v for v in all_variants if v.get("available", True)]

    if not variants:
        st.info("Variants for this structure type are coming soon.")
        st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
        if st.button("Back to Studio", key="reg_back_empty", use_container_width=True):
            st.session_state.page = "studio"
            st.rerun()
        return

    for variant in variants:
        vk = variant.get("key", "")
        vn = variant.get("name", "")
        vd = variant.get("description", "")

        st.markdown(
            '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
            'border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.6rem;">'
            '<div style="color: #ffffff; font-size: 1rem; font-weight: 600; '
            'margin-bottom: 0.3rem;">' + vn + '</div>'
            '<div style="color: #a8b8c8; font-size: 0.85rem; line-height: 1.4;">'
            + vd + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        if st.button("Select " + vn, key="reg_var_" + structure_key + "_" + vk, use_container_width=True):
            st.session_state.variant_key = vk
            st.session_state.variant_name = vn
            st.session_state.page = "workshop"
            st.rerun()

    st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
    if st.button("Back to Studio", key="reg_back", use_container_width=True):
        st.session_state.page = "studio"
        st.rerun()





