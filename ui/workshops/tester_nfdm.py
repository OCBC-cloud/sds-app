# =============================================================================
# SDSe Fluid Design Studio - NFDM Tester Workshop
# =============================================================================
# Temporary research page. Reached only through the tester route.
#
# Purpose:
#   Run the NFDM kernel on the reduced catenoid benchmark, render
#   the resulting surface in 3D, and report the diagnostics.
#
#   This page exists to answer ONE question:
#     Does the NFDM kernel produce a smooth membrane surface,
#     without the fold that classical FDM gives?
#
#   If yes: NFDM is proven, and we can start migrating the
#   Saddle viewers to it.
#   If no: the page is deleted, and the app is unchanged.
#
# Isolation:
#   This file is self-contained. It imports only from engine/nfdm.py,
#   which is itself a new file. If the import fails, this page shows
#   an error and the rest of the app is unaffected. The page can be
#   removed by deleting this file and the tester route line in
#   core/navigation.py.
#
# Status: EXPERIMENTAL. Not a shipping feature.
# =============================================================================

import streamlit as st


def render_tester_nfdm():
    """Render the NFDM tester page."""

    st.markdown(
        '<div style="background-color:#3a1f1f;border-left:4px solid #e74c3c;'
        'border-radius:8px;padding:1rem;margin-bottom:1.2rem;">'
        '<div style="color:#e74c3c;font-weight:700;font-size:1.05rem;'
        'margin-bottom:0.3rem;">EXPERIMENTAL — NFDM TESTER</div>'
        '<div style="color:#c8d4e0;font-size:0.9rem;line-height:1.5;">'
        'This page is a research tool. It runs the Natural Force Density '
        'Method on the reduced catenoid benchmark. Not a product feature.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Natural Force Density Method")
    st.markdown(
        "The kernel solves a triangular membrane mesh for its "
        "equilibrium shape. If the surface is smooth and forms a "
        "saddle, the NFDM formulation is working. If it folds, the "
        "kernel needs work."
    )

    # ---- Import the kernel, guarded --------------------------------------
    try:
        from engine.nfdm import get_catenoid_for_viewer
    except Exception as e:
        st.error(
            "Could not load the NFDM kernel. The rest of the app is "
            "unaffected. Error:"
        )
        st.code(str(e), language="text")
        if st.button("Back to Landing", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()
        return

    # ---- Run the kernel ---------------------------------------------------
    if st.button("Run NFDM on reduced catenoid", type="primary", use_container_width=True):
        with st.spinner("Solving…"):
            try:
                coords, tris, boundary, res = get_catenoid_for_viewer()
                st.session_state["tester_nfdm_result"] = (coords, tris, boundary, res)
            except Exception as e:
                st.error("NFDM solve failed. Error:")
                st.code(str(e), language="text")

    # ---- Render the result -----------------------------------------------
    if "tester_nfdm_result" not in st.session_state:
        st.info("Tap the button above to run the benchmark.")
        if st.button("Back to Landing", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()
        return

    coords, tris, boundary, res = st.session_state["tester_nfdm_result"]

    try:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0],
            y=coords[:, 1],
            z=coords[:, 2],
            i=tris[:, 0],
            j=tris[:, 1],
            k=tris[:, 2],
            color="#7a8fa8",
            opacity=0.9,
            flatshading=False,
            name="Membrane",
            showscale=False,
            lighting=dict(ambient=0.6, diffuse=0.9, specular=0.2, roughness=0.5),
        ))
        fig.add_trace(go.Scatter3d(
            x=coords[boundary, 0],
            y=coords[boundary, 1],
            z=coords[boundary, 2],
            mode="markers",
            marker=dict(size=4, color="#c88a1f"),
            name="Boundary nodes",
        ))
        fig.update_layout(
            scene=dict(
                xaxis_title="X (m)",
                yaxis_title="Y (m)",
                zaxis_title="Z (m)",
                aspectmode="data",
                bgcolor="#0e1117",
                xaxis=dict(gridcolor="#333", color="#888"),
                yaxis=dict(gridcolor="#333", color="#888"),
                zaxis=dict(gridcolor="#333", color="#888"),
            ),
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="#ccc"),
            height=560,
            margin=dict(l=0, r=0, b=0, t=0),
            showlegend=True,
            legend=dict(x=0.02, y=0.98, bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Could not render the 3D view. Error:")
        st.code(str(e), language="text")

    # ---- Report ----------------------------------------------------------
    st.markdown("#### Diagnostics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Converged", "Yes" if res["converged"] else "No")
    c2.metric("Iterations", res["iterations"])
    c3.metric("Residual", "%.2e" % res["residual_norm"])
    c4.metric("Reason", res.get("reason", ""))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Min area", "%.4f" % res["min_area"])
    c6.metric("Max area", "%.4f" % res["max_area"])
    c7.metric("Min q", "%.4f" % res["min_q"])
    c8.metric("Negative q", res["negative_q"])

    st.markdown("---")

    if res["converged"] and res["negative_q"] == 0:
        st.success(
            "Kernel converged, no negative force densities. "
            "The surface should be a smooth membrane with no fold."
        )
    else:
        st.warning(
            "Kernel did not converge cleanly, or produced negative force "
            "densities. The surface may fold. This is honest information — "
            "the kernel needs work."
        )

    with st.expander("Full result dict"):
        safe = {k: v for k, v in res.items() if k != "history"}
        safe["history_len"] = len(res.get("history", []))
        st.json(safe)

    st.markdown("---")
    if st.button("Back to Landing", use_container_width=True):
        st.session_state.page = "landing"
        st.rerun()





