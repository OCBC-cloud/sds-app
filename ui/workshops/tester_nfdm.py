# =============================================================================
# SDSe Fluid Design Studio - NFDM Tester Workshop
# =============================================================================
# Temporary research page. Reached from the landing page button.
#
# Updated 2026-09-23 (evening):
#   - Two benchmarks: reduced catenoid and settled hypar.
#   - Single-panel diagnostics, so one screenshot captures all.
#   - Explicit camera auto-fit. Whole object in view.
#
# Purpose:
#   Run the NFDM kernel on two starting meshes and compare the
#   results. The catenoid is the analytical reference. The hypar
#   matches the shape family the shipping Cantilever Hypar
#   viewer produces, so NFDM starts from a near-equilibrium
#   saddle instead of a flat patch.
#
# Isolation:
#   Self-contained. If the kernel import fails, this page shows
#   an error and the rest of the app is unaffected.
#
# Status: EXPERIMENTAL. Not a shipping feature.
# =============================================================================

import streamlit as st


# ---------------------------------------------------------------------------
# 3D VIEW HELPER
# ---------------------------------------------------------------------------

def _render_mesh_view(coords, tris, boundary, title):
    """Render a 3D mesh with a camera that frames the whole object."""
    try:
        import plotly.graph_objects as go

        xyz_min = coords.min(axis=0)
        xyz_max = coords.max(axis=0)
        xyz_mid = (xyz_min + xyz_max) / 2.0
        span = float(max(xyz_max - xyz_min))
        pad = span * 0.15
        xr = [float(xyz_mid[0] - span / 2 - pad), float(xyz_mid[0] + span / 2 + pad)]
        yr = [float(xyz_mid[1] - span / 2 - pad), float(xyz_mid[1] + span / 2 + pad)]
        zr = [float(xyz_mid[2] - span / 2 - pad), float(xyz_mid[2] + span / 2 + pad)]

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
            title=dict(text=title, font=dict(color="#c8d4e0", size=13)),
            scene=dict(
                xaxis=dict(title="X (m)", gridcolor="#333", color="#888",
                           range=xr, autorange=False),
                yaxis=dict(title="Y (m)", gridcolor="#333", color="#888",
                           range=yr, autorange=False),
                zaxis=dict(title="Z (m)", gridcolor="#333", color="#888",
                           range=zr, autorange=False),
                aspectmode="cube",
                bgcolor="#0e1117",
                camera=dict(
                    eye=dict(x=1.6, y=1.6, z=1.2),
                    up=dict(x=0, y=0, z=1),
                ),
            ),
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="#ccc", size=11),
            height=500,
            margin=dict(l=0, r=0, b=0, t=30),
            showlegend=True,
            legend=dict(x=0.02, y=0.98, bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Could not render the 3D view. Error:")
        st.code(str(e), language="text")


def _render_diagnostics(res):
    """Render a single compact panel with all diagnostics."""
    status = "PASS" if (res["converged"] and res["negative_q"] == 0) else "CHECK"
    status_color = "#27ae60" if status == "PASS" else "#e67e22"
    reason = str(res.get("reason", ""))

    st.markdown(
        '<div style="background-color:#121e2e;border:1px solid #1e2a3a;'
        'border-radius:10px;padding:1rem 1.2rem;margin-top:0.6rem;'
        'font-family:ui-monospace,Menlo,monospace;font-size:0.85rem;'
        'color:#c8d4e0;line-height:1.7;">'
        '<div style="color:' + status_color + ';font-weight:700;'
        'font-size:1rem;margin-bottom:0.5rem;">'
        'NFDM RESULT &nbsp; ' + status +
        '</div>'
        'converged       = ' + str(res["converged"]) + '<br>'
        'iterations      = ' + str(res["iterations"]) + '<br>'
        'reason          = ' + reason + '<br>'
        'residual_norm   = ' + ("%.4e" % res["residual_norm"]) + '<br>'
        'negative_q      = ' + str(res["negative_q"]) + '<br>'
        'min_q           = ' + ("%.6f" % res["min_q"]) + '<br>'
        'max_q           = ' + ("%.6f" % res["max_q"]) + '<br>'
        'min_area        = ' + ("%.6f" % res["min_area"]) + '<br>'
        'max_area        = ' + ("%.6f" % res["max_area"]) + '<br>'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# MAIN RENDER
# ---------------------------------------------------------------------------

def render_tester_nfdm():
    """Render the NFDM tester page."""

    st.markdown(
        '<div style="background-color:#3a1f1f;border-left:4px solid #e74c3c;'
        'border-radius:8px;padding:1rem;margin-bottom:1.2rem;">'
        '<div style="color:#e74c3c;font-weight:700;font-size:1.05rem;'
        'margin-bottom:0.3rem;">EXPERIMENTAL - NFDM TESTER</div>'
        '<div style="color:#c8d4e0;font-size:0.9rem;line-height:1.5;">'
        'Research tool. Runs the Natural Force Density Method on two '
        'starting meshes: the reduced catenoid (analytical reference) '
        'and the settled hypar (the shape family our Cantilever Hypar '
        'viewer produces). Not a product feature.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Natural Force Density Method")
    st.markdown(
        "The kernel solves a triangular membrane mesh for its equilibrium "
        "shape. If the surface is smooth and forms a saddle, the NFDM "
        "formulation is working. If it folds, the kernel needs work."
    )

    # ---- Import the kernel, guarded --------------------------------------
    try:
        from engine.nfdm import get_catenoid_for_viewer, get_hypar_for_viewer
    except Exception as e:
        st.error("Could not load the NFDM kernel. The rest of the app is unaffected. Error:")
        st.code(str(e), language="text")
        if st.button("Back to Landing", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()
        return

    # ---- Two buttons ------------------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        run_cat = st.button(
            "Run reduced catenoid",
            type="primary",
            use_container_width=True,
            key="tester_run_cat",
        )
    with col2:
        run_hypar = st.button(
            "Run settled hypar",
            type="primary",
            use_container_width=True,
            key="tester_run_hypar",
        )

    if run_cat:
        with st.spinner("Solving catenoid..."):
            try:
                coords, tris, boundary, res = get_catenoid_for_viewer()
                st.session_state["tester_nfdm_cat"] = (coords, tris, boundary, res)
            except Exception as e:
                st.error("NFDM catenoid solve failed. Error:")
                st.code(str(e), language="text")

    if run_hypar:
        with st.spinner("Solving hypar..."):
            try:
                coords, tris, boundary, res = get_hypar_for_viewer()
                st.session_state["tester_nfdm_hypar"] = (coords, tris, boundary, res)
            except Exception as e:
                st.error("NFDM hypar solve failed. Error:")
                st.code(str(e), language="text")

    # ---- Show whichever results exist ------------------------------------
    has_cat = "tester_nfdm_cat" in st.session_state
    has_hypar = "tester_nfdm_hypar" in st.session_state

    if not has_cat and not has_hypar:
        st.info("Tap one of the buttons above to run a benchmark.")
        if st.button("Back to Landing", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()
        return

    if has_hypar:
        coords_h, tris_h, boundary_h, res_h = st.session_state["tester_nfdm_hypar"]
        st.markdown("#### Settled hypar")
        _render_mesh_view(coords_h, tris_h, boundary_h, "Hypar starting mesh, NFDM result")
        _render_diagnostics(res_h)

    if has_cat:
        coords_c, tris_c, boundary_c, res_c = st.session_state["tester_nfdm_cat"]
        st.markdown("#### Reduced catenoid")
        _render_mesh_view(coords_c, tris_c, boundary_c, "Catenoid starting mesh, NFDM result")
        _render_diagnostics(res_c)

    st.markdown(
        '<div style="margin-top:0.8rem;padding:0.8rem 1rem;'
        'background-color:#1a2a1a;border-left:4px solid #27ae60;'
        'border-radius:6px;color:#c8d4e0;font-size:0.85rem;'
        'line-height:1.5;">'
        '<strong style="color:#27ae60;">How to read this:</strong><br>'
        '<em>PASS</em> - kernel converged and no elements went slack. '
        'A smooth membrane surface with no fold.<br>'
        '<em>CHECK</em> - the solver did not converge cleanly, or some '
        'elements are in slack (negative q). The surface may still look '
        'plausible but the kernel needs tuning.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    if st.button("Back to Landing", use_container_width=True, key="tester_back_bottom"):
        st.session_state.page = "landing"
        st.rerun()





