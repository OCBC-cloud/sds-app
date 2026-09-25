# =============================================================================
# SDSe Fluid Design Studio - MBS Tester Workshop
# =============================================================================
# Temporary research page. Tests the Membrane Boundary Schema engine.
#
# Reached from the landing page button "Open MBS Tester".
#
# Purpose:
#   Run the MBS engine on a small saddle boundary, render the
#   resulting mesh in 3D, and report the diagnostics. This is
#   the first end-to-end test of the engine from inside the app.
#
#   If the mesh has positive triangle areas and the FDM solver
#   converges cleanly, the engine is proven. If not, the
#   diagnostics tell us where to look.
#
# Isolation:
#   This file is self-contained. It imports only from
#   engine/membrane_boundary.py. If the import fails, this page
#   shows an error and the rest of the app is unaffected.
#
# Status: EXPERIMENTAL. Not a shipping feature.
# =============================================================================

import numpy as np
import streamlit as st


def render_tester_mbs():
    """Render the MBS engine tester page."""

    st.markdown(
        '<div style="background-color:#1f2a3a;border-left:4px solid #3498db;'
        'border-radius:8px;padding:1rem;margin-bottom:1.2rem;">'
        '<div style="color:#3498db;font-weight:700;font-size:1.05rem;'
        'margin-bottom:0.3rem;">EXPERIMENTAL - MBS TESTER</div>'
        '<div style="color:#c8d4e0;font-size:0.9rem;line-height:1.5;">'
        'Research tool. Runs the Membrane Boundary Schema engine '
        'on a small saddle boundary, solves with FDM, and reports '
        'the mesh diagnostics. Not a product feature.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Membrane Boundary Schema")
    st.markdown(
        "The MBS engine builds a triangular membrane mesh from a "
        "closed boundary, a set of anchors, and the type of each "
        "edge between anchors (beam or cable). It then solves the "
        "form with FDM. If the mesh has positive triangle areas "
        "and the solver converges, the engine is working."
    )

    # ---- Import the engine, guarded --------------------------------------
    try:
        from engine.membrane_boundary import build_and_solve
    except Exception as e:
        st.error("Could not load the MBS engine. The rest of the app "
                 "is unaffected. Error:")
        st.code(str(e), language="text")
        if st.button("Back to Landing", use_container_width=True,
                     key="mbs_back_import_fail"):
            st.session_state.page = "landing"
            st.rerun()
        return

    # ---- Run the engine on a 3x3 saddle ----------------------------------
    if st.button("Run MBS engine on 3m x 3m saddle",
                 type="primary",
                 use_container_width=True,
                 key="mbs_run"):

        with st.spinner("Building mesh and solving..."):

            # 3m x 3m saddle boundary.
            # Two low corners at z=0, two high corners at z=2.
            boundary = np.array([
                [-1.5, -1.5, 0.0],
                [ 1.5, -1.5, 0.0],
                [ 1.5,  1.5, 2.0],
                [-1.5,  1.5, 2.0],
            ], dtype=float)

            anchor_indices = [0, 1, 2, 3]
            edge_types = ["cable", "cable", "cable", "cable"]

            try:
                result = build_and_solve(
                    boundary=boundary,
                    anchor_indices=anchor_indices,
                    edge_types=edge_types,
                    nx=8, ny=8,
                    membrane_q=1.0,
                    cable_q=5.0,
                )
                st.session_state["tester_mbs_result"] = result
            except Exception as e:
                st.error("MBS engine raised an error:")
                st.code(str(e), language="text")

    # ---- Render the result -----------------------------------------------
    if "tester_mbs_result" not in st.session_state:
        st.info("Tap the button above to run the MBS engine.")
        if st.button("Back to Landing", use_container_width=True,
                     key="mbs_back_noresult"):
            st.session_state.page = "landing"
            st.rerun()
        return

    result = st.session_state["tester_mbs_result"]
    coords = result["coordinates"]
    mesh = result["mesh"]
    solve = result["solve_result"]

    # Build triangle list from the mesh grid.
    nx = mesh["diagnostics"]["nx"]
    ny = mesh["diagnostics"]["ny"]
    tri_i = []
    tri_j = []
    tri_k = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            b = (i + 1) * ny + j
            c = i * ny + (j + 1)
            d = (i + 1) * ny + (j + 1)
            tri_i.append(a); tri_j.append(b); tri_k.append(c)
            tri_i.append(b); tri_j.append(d); tri_k.append(c)

    tri_i = np.array(tri_i, dtype=int)
    tri_j = np.array(tri_j, dtype=int)
    tri_k = np.array(tri_k, dtype=int)

    # ---- 3D view ---------------------------------------------------------
    try:
        import plotly.graph_objects as go

        # Auto-fit camera to the whole object.
        xyz_min = coords.min(axis=0)
        xyz_max = coords.max(axis=0)
        xyz_mid = (xyz_min + xyz_max) / 2.0
        span = float(max(xyz_max - xyz_min))
        pad = span * 0.15
        xr = [float(xyz_mid[0] - span/2 - pad),
              float(xyz_mid[0] + span/2 + pad)]
        yr = [float(xyz_mid[1] - span/2 - pad),
              float(xyz_mid[1] + span/2 + pad)]
        zr = [float(xyz_mid[2] - span/2 - pad),
              float(xyz_mid[2] + span/2 + pad)]

        fig = go.Figure()
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tri_i, j=tri_j, k=tri_k,
            color="#4a7a9c",
            opacity=0.9,
            flatshading=False,
            name="Membrane",
            showscale=False,
            lighting=dict(ambient=0.6, diffuse=0.9,
                          specular=0.2, roughness=0.5),
        ))
        fig.add_trace(go.Scatter3d(
            x=boundary[:, 0], y=boundary[:, 1], z=boundary[:, 2],
            mode="markers",
            marker=dict(size=6, color="#f39c12", symbol="diamond"),
            name="Anchors",
        ))
        fig.update_layout(
            scene=dict(
                xaxis=dict(title="X (m)", gridcolor="#333",
                           color="#888", range=xr, autorange=False),
                yaxis=dict(title="Y (m)", gridcolor="#333",
                           color="#888", range=yr, autorange=False),
                zaxis=dict(title="Z (m)", gridcolor="#333",
                           color="#888", range=zr, autorange=False),
                aspectmode="cube",
                bgcolor="#0e1117",
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.2)),
            ),
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="#ccc", size=11),
            height=520,
            margin=dict(l=0, r=0, b=0, t=0),
            showlegend=True,
            legend=dict(x=0.02, y=0.98, bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error("Could not render the 3D view:")
        st.code(str(e), language="text")

    # ---- Diagnostics -----------------------------------------------------
    st.markdown("#### Diagnostics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nodes", mesh["diagnostics"]["n_nodes"])
    c2.metric("Edges", mesh["diagnostics"]["n_edges"])
    c3.metric("Fixed", mesh["diagnostics"]["n_fixed"])
    c4.metric("Free", mesh["diagnostics"]["n_free"])

    d1, d2 = st.columns(2)
    d1.metric("FDM residual", "%.4e" % solve["residual_norm"])
    d2.metric("Corners fixed", len(mesh["diagnostics"]["corners"]))

    # ---- Smallest triangles ---------------------------------------------
    st.markdown("#### Smallest 10 initial triangles")
    points0 = mesh["points"]
    tri_areas = []
    tri_list = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            b = (i + 1) * ny + j
            c = i * ny + (j + 1)
            d = (i + 1) * ny + (j + 1)
            for tri in ((a, b, c), (b, d, c)):
                p0 = points0[tri[0]]
                p1 = points0[tri[1]]
                p2 = points0[tri[2]]
                area = 0.5 * float(np.linalg.norm(
                    np.cross(p1 - p0, p2 - p0)))
                tri_areas.append(area)
                tri_list.append(tri)

    tri_areas = np.array(tri_areas)
    order = np.argsort(tri_areas)[:10]
    rows = []
    for rank, idx in enumerate(order):
        tri = tri_list[idx]
        rows.append(
            "rank " + str(rank + 1) +
            "  nodes " + str(tri) +
            "  area=" + ("%.6e" % tri_areas[idx])
        )
    st.code("\n".join(rows), language="text")

    st.markdown("---")
    if st.button("Back to Landing", use_container_width=True,
                 key="mbs_back_bottom"):
        st.session_state.page = "landing"
        st.rerun()





                     
