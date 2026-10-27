# =============================================================================
# SDSe - Lab: Cantilever Leaf Tester
# =============================================================================
# Structural-analysis test case for the Cantilever Leaf.
# Fixed spec (6 m column, 5 m outreach, 3 rib pairs, 2 m mid half-width).
# Renders the figure and dumps the raw geometry the structural solver
# will consume.
# =============================================================================

import streamlit as st

from viewers.figures.cantilever_leaf_lab import (
    compute_lab_leaf_geometry,
    build_cantilever_leaf_lab_figure,
)


LAB_TESTER_CSS = """
    <style>
    .stApp > header { display: none !important; }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px;
    }
    .ctl-topbar {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0 0 0.6rem 0;
        border-bottom: 1px solid #1e2a3a;
        margin-bottom: 1.2rem;
    }
    .ctl-wordmark {
        font-size: 1.1rem; font-weight: 700; color: #f39c12;
        letter-spacing: 2px;
    }
    .ctl-header {
        font-size: 1.4rem; font-weight: 700; color: #ffffff;
        margin: 0.4rem 0 0.3rem 0;
    }
    .ctl-sub {
        font-size: 0.9rem; color: #a8b8c8;
        margin-bottom: 1.2rem; line-height: 1.4;
    }
    .ctl-card {
        background-color: #121e2e; border: 1px solid #1e2a3a;
        border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.7rem;
    }
    .ctl-mono {
        font-family: 'SF Mono', Menlo, monospace;
        font-size: 0.8rem; color: #c8d8e8; white-space: pre-wrap;
    }
    </style>
"""


def render_tester_cantilever_leaf():
    st.markdown(LAB_TESTER_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="ctl-topbar">'
        '<div class="ctl-wordmark">SDSe LAB</div>'
        '<div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ctl-header">Cantilever Leaf Tester</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ctl-sub">'
        'Fixed structural-analysis test case. 6 m column, 5 m outreach, '
        '3 rib pairs, 2 m middle half-width. Geometry dump below is the '
        'input for the structural solver.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Build geometry + figure
    geom = compute_lab_leaf_geometry()
    fig  = build_cantilever_leaf_lab_figure(geom)

    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})

    with col_r:
        st.markdown("#### Spec")
        spec = geom["spec"]
        st.markdown(
            f'<div class="ctl-card ctl-mono">'
            f'column_height = {spec["column_height"]:.2f} m\n'
            f'outreach      = {spec["outreach"]:.2f} m\n'
            f'ribs_per_side = {spec["ribs_per_side"]}\n'
            f'half_w(mid)   = {spec["half_width_mid"]:.2f} m\n'
            f'rib_tilt      = {spec["rib_tilt_deg"]:.1f} deg\n'
            f'arc_radius    = {spec["arc_radius"]:.2f} m\n'
            f'strut_joint   = {spec["strut_joint"]:.2f} m\n'
            f'strut_angle   = {spec["strut_angle"]:.1f} deg'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("#### Ribs")
        lines = []
        for rib in geom["ribs"]:
            ax, ay, az = rib["attach"]
            lx, ly, lz = rib["left_tip"]
            rx, ry, rz = rib["right_tip"]
            lines.append(
                f'rib #{rib["index"]}  t={rib["t"]:.2f}  hw={rib["half_width"]:.3f} m\n'
                f'  attach = ({ax:.3f}, {ay:.3f}, {az:.3f})\n'
                f'  L tip  = ({lx:.3f}, {ly:.3f}, {lz:.3f})\n'
                f'  R tip  = ({rx:.3f}, {ry:.3f}, {rz:.3f})\n'
            )
        st.markdown(
            f'<div class="ctl-card ctl-mono">{"".join(lines)}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("#### Strut")
        sa = geom["strut"]["attach"]
        sb = geom["strut"]["base"]
        st.markdown(
            f'<div class="ctl-card ctl-mono">'
            f'attach = ({sa[0]:.3f}, {sa[1]:.3f}, {sa[2]:.3f})\n'
            f'base   = ({sb[0]:.3f}, {sb[1]:.3f}, {sb[2]:.3f})\n'
            f'length = '
            f'{((sa[0]-sb[0])**2 + (sa[1]-sb[1])**2 + (sa[2]-sb[2])**2)**0.5:.3f} m'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ---- Membrane extents summary
    m = geom["membrane"]
    st.markdown("#### Membrane extents")
    st.markdown(
        f'<div class="ctl-card ctl-mono">'
        f'x range = [{m["X"].min():.3f}, {m["X"].max():.3f}] m\n'
        f'y range = [{m["Y"].min():.3f}, {m["Y"].max():.3f}] m\n'
        f'z range = [{m["Z"].min():.3f}, {m["Z"].max():.3f}] m\n'
        f'grid    = {m["X"].shape[0]} x {m["X"].shape[1]} nodes'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ---- Back
    st.markdown('<div style="height: 1.2rem;"></div>', unsafe_allow_html=True)
    if st.button("Back to Lab", key="tcl_back", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()
