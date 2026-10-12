# =============================================================================
# SDSe - Form Finding Lab
# =============================================================================
# Lab page for the reduced-basis FDM solver.
#
# Uses the self-contained solver in engine/form_finding_test.py.
# Shows the smooth cable bow visually so the solver's behaviour can
# be seen, not just read as numbers.
#
# This page is a Lab page. It is not customer-facing.
#
# What you see:
#   - A cable, held at both ends.
#   - Transverse load applied at every interior node.
#   - dir_only at every interior node along Y.
#   - The solver finds the bow.
#   - Two views: 3D (the cable in space) and 2D (Y vs X).
#   - Residual numbers printed below.
#
# History:
#   2026-10-12 - First version.
# =============================================================================

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm


LAB_CSS = """
    <style>
    .stApp > header { display: none !important; }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px;
    }
    .ffl-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 0 0.6rem 0;
        border-bottom: 1px solid #1e2a3a;
        margin-bottom: 1.2rem;
    }
    .ffl-wordmark {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f39c12;
        letter-spacing: 2px;
    }
    .ffl-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0.2rem 0 0.2rem 0;
    }
    .ffl-sub {
        font-size: 0.9rem;
        color: #a8b8c8;
        margin-bottom: 1.2rem;
        line-height: 1.4;
    }
    .ffl-metric {
        background-color: #121e2e;
        border: 1px solid #1e2a3a;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.4rem;
    }
    .ffl-metric-label {
        font-size: 0.75rem;
        color: #a8b8c8;
        margin: 0;
    }
    .ffl-metric-value {
        font-size: 1.05rem;
        color: #ffffff;
        font-family: monospace;
        margin: 0.15rem 0 0 0;
    }
    .ffl-metric-ok  { color: #4ade80; }
    .ffl-metric-bad { color: #ff6b6b; }
    </style>
"""


def _build_cable(n_nodes, span_m):
    xs = np.linspace(0.0, span_m, n_nodes)
    points = np.column_stack([xs, np.zeros(n_nodes), np.zeros(n_nodes)])
    edges = [(i, i + 1) for i in range(n_nodes - 1)]
    fixed = [0, n_nodes - 1]
    dir_only = [(i, (0.0, 1.0, 0.0)) for i in range(1, n_nodes - 1)]
    return points, edges, fixed, dir_only


def _apply_transverse_load(n_nodes, load_n):
    loads = np.zeros((n_nodes, 3))
    for i in range(1, n_nodes - 1):
        loads[i, 1] = load_n
    return loads


def _plot_cable_3d(points_initial, points_bowed):
    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=points_initial[:, 0],
        y=points_initial[:, 1],
        z=points_initial[:, 2],
        mode="lines+markers",
        line=dict(color="#4a7a9c", width=4, dash="dot"),
        marker=dict(size=4, color="#4a7a9c"),
        name="initial (straight)",
    ))

    fig.add_trace(go.Scatter3d(
        x=points_bowed[:, 0],
        y=points_bowed[:, 1],
        z=points_bowed[:, 2],
        mode="lines+markers",
        line=dict(color="#f39c12", width=8),
        marker=dict(size=6, color="#f39c12"),
        name="bowed (solved)",
    ))

    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            aspectmode="data",
            bgcolor="#0d1620",
            xaxis=dict(gridcolor="#1e2a3a", color="#a8b8c8"),
            yaxis=dict(gridcolor="#1e2a3a", color="#a8b8c8"),
            zaxis=dict(gridcolor="#1e2a3a", color="#a8b8c8"),
        ),
        paper_bgcolor="#0d1620",
        font=dict(color="#a8b8c8"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=520,
        legend=dict(
            x=0.02, y=0.98,
            bgcolor="#121e2e",
            bordercolor="#1e2a3a",
            borderwidth=1,
            font=dict(color="#ffffff"),
        ),
    )
    return fig


def _plot_cable_2d(points_initial, points_bowed):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=points_initial[:, 0],
        y=points_initial[:, 1],
        mode="lines+markers",
        line=dict(color="#4a7a9c", width=2, dash="dot"),
        marker=dict(size=6, color="#4a7a9c"),
        name="initial (straight)",
    ))

    fig.add_trace(go.Scatter(
        x=points_bowed[:, 0],
        y=points_bowed[:, 1],
        mode="lines+markers",
        line=dict(color="#f39c12", width=4),
        marker=dict(size=8, color="#f39c12"),
        name="bowed (solved)",
    ))

    fig.update_layout(
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        plot_bgcolor="#0d1620",
        paper_bgcolor="#0d1620",
        font=dict(color="#a8b8c8"),
        xaxis=dict(gridcolor="#1e2a3a", color="#a8b8c8", zeroline=True,
                   zerolinecolor="#2a3a4a"),
        yaxis=dict(gridcolor="#1e2a3a", color="#a8b8c8", zeroline=True,
                   zerolinecolor="#2a3a4a"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=420,
        legend=dict(
            x=0.02, y=0.98,
            bgcolor="#121e2e",
            bordercolor="#1e2a3a",
            borderwidth=1,
            font=dict(color="#ffffff"),
        ),
    )
    return fig


def _metric(label, value, ok=None):
    cls = ""
    if ok is True:
        cls = " ffl-metric-ok"
    elif ok is False:
        cls = " ffl-metric-bad"
    return (
        '<div class="ffl-metric">'
        '<p class="ffl-metric-label">' + label + '</p>'
        '<p class="ffl-metric-value' + cls + '">' + value + '</p>'
        '</div>'
    )


def render_form_finding_lab():
    st.markdown(LAB_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="ffl-topbar">'
        '<div class="ffl-wordmark">SDSe LAB</div>'
        '<div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="ffl-header">Form Finding Lab</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ffl-sub">'
        'A taut cable, held at both ends, with a transverse load. '
        'Every interior node is free only along Y (dir_only). '
        'The solver finds the bow. What you see is what the solver '
        'found, not what a formula predicted.'
        '</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        n_nodes = int(st.number_input(
            "Node count", 5, 101, 21, 2, key="ffl_nodes"
        ))
    with c2:
        span_m = float(st.number_input(
            "Span (m)", 1.0, 100.0, 20.0, 1.0, key="ffl_span"
        ))
    with c3:
        load_n = float(st.number_input(
            "Transverse load per node (N)", 0.0, 100000.0, 100.0, 10.0,
            key="ffl_load"
        ))

    c1, c2, c3 = st.columns(3)
    with c1:
        q_value = float(st.number_input(
            "Force density q (N/m)", 1.0, 100000.0, 1000.0, 100.0,
            key="ffl_q"
        ))
    with c2:
        st.write("")
        st.write("")
        solve_clicked = st.button(
            "Solve", key="ffl_solve", use_container_width=True,
            type="primary",
        )
    with c3:
        st.write("")
        st.write("")
        if st.button("Back to Lab", key="ffl_back", use_container_width=True):
            st.session_state.page = "lab"
            st.rerun()

    if not solve_clicked:
        st.info("Set the parameters, then press Solve.")
        return

    points, edges, fixed, dir_only = _build_cable(n_nodes, span_m)
    loads = _apply_transverse_load(n_nodes, load_n)

    try:
        result = solve_fdm(points, edges, fixed, q_value,
                           loads=loads, dir_only_indices=dir_only)
    except Exception as e:
        st.error("Solve failed: " + str(e))
        return

    coords = result["coordinates"]
    residual = result["residual_norm"]
    n_free = result["n_free"]
    n_fixed = result["n_fixed"]
    dof_count = result["dof_count"]

    y_max = float(np.max(coords[:, 1]))
    y_mid = float(coords[n_nodes // 2, 1])
    x_drift = float(np.max(np.abs(coords[:, 0] - points[:, 0])))
    z_drift = float(np.max(np.abs(coords[:, 2])))

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(_metric("Max Y (m)", "%.4f" % y_max), unsafe_allow_html=True)
    with m2:
        st.markdown(_metric("Y at mid (m)", "%.4f" % y_mid), unsafe_allow_html=True)
    with m3:
        st.markdown(
            _metric("X drift (m)", "%.3e" % x_drift, ok=(x_drift < 1e-9)),
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            _metric("Z drift (m)", "%.3e" % z_drift, ok=(z_drift < 1e-9)),
            unsafe_allow_html=True,
        )

    m5, m6, m7 = st.columns(3)
    with m5:
        st.markdown(
            _metric("Residual (N)", "%.3e" % residual, ok=(residual < 1e-6)),
            unsafe_allow_html=True,
        )
    with m6:
        st.markdown(
            _metric("DOF count", str(dof_count)), unsafe_allow_html=True
        )
    with m7:
        st.markdown(
            _metric("Free / Fixed",
                    str(n_free) + " / " + str(n_fixed)),
            unsafe_allow_html=True,
        )

    st.markdown("#### 3D view")
    st.plotly_chart(
        _plot_cable_3d(points, coords),
        use_container_width=True,
        key="ffl_3d",
    )

    st.markdown("#### Plan view (Y vs X)")
    st.plotly_chart(
        _plot_cable_2d(points, coords),
        use_container_width=True,
        key="ffl_2d",
    )

    with st.expander("Node coordinates", expanded=False):
        lines = ["idx      x_init     y_init     x_final    y_final    y_shift"]
        lines.append("-" * 70)
        for i in range(n_nodes):
            xi = points[i, 0]
            yi = points[i, 1]
            xf = coords[i, 0]
            yf = coords[i, 1]
            lines.append(
                "%4d  %10.5f %10.5f %10.5f %10.5f %10.5f"
                % (i, xi, yi, xf, yf, yf - yi)
            )
        st.code("\n".join(lines), language="text")


# =============================================================================
# END OF ui/workshops/form_finding_lab.py
# =============================================================================
