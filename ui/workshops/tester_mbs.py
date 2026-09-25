# =============================================================================
# SDSe Fluid Design Studio - MBS Tester Workshop
# =============================================================================
# Temporary research page. Tests the Membrane Boundary Schema engine.
#
# Two tests:
#   Test 1 - Square boundary. Four corners.
#   Test 2 - Lens boundary. Built with engine/membrane_surface.py
#            using anchor + subdivision density.
#
# K = 5 subdivisions per anchor segment. With 7 anchors, that is
# n_u = 7 + 6*5 = 37 nodes along the beam. This decouples the
# structural anchor count from the mesh density, so the mesh
# samples the beam curvature accurately.
#
# Status: EXPERIMENTAL.
# =============================================================================

import numpy as np
import streamlit as st


# ---- Mesh density controls ------------------------------------------------
ANCHORS_PER_BEAM = 7
SUBDIVISIONS_PER_SEGMENT = 5
NODES_ACROSS = 8


def _build_square_boundary():
    corners = np.array([
        [-1.5, -1.5, 0.0],
        [ 1.5, -1.5, 0.0],
        [ 1.5,  1.5, 2.0],
        [-1.5,  1.5, 2.0],
    ], dtype=float)
    anchor_indices = [0, 1, 2, 3]
    edge_types = ["cable", "cable", "cable", "cable"]
    return corners, anchor_indices, edge_types


def _build_lens_surface(nx, ny, n_beam_samples=400):
    """
    Build the lens surface and boundary. Returns
    (initial_points, boundary, anchor_indices, edge_types).
    """
    from viewers.figures._shared import beam_curve
    from engine.membrane_surface import build_surface

    span = 3.0
    apex = 4.0
    rise = 1.5
    curve_type = "parabolic"

    x_dense = np.linspace(-span / 2.0, span / 2.0, n_beam_samples)
    z_dense = beam_curve(x_dense, span, rise, curve_type)

    base_width = apex * 0.5
    y_L_dense = -base_width * (1.0 - (2.0 * x_dense / span) ** 2)
    y_R_dense = base_width * (1.0 - (2.0 * x_dense / span) ** 2)

    y_L_dense[0] = 0.0
    y_L_dense[-1] = 0.0
    y_R_dense[0] = 0.0
    y_R_dense[-1] = 0.0

    beam_L = np.column_stack((x_dense, y_L_dense, z_dense))
    beam_R = np.column_stack((x_dense, y_R_dense, z_dense))

    grid = build_surface(
        beam_L_points=beam_L,
        beam_R_points=beam_R,
        n_anchors=ANCHORS_PER_BEAM,
        subdivisions_per_segment=SUBDIVISIONS_PER_SEGMENT,
        n_v=ny,
        sag_fraction=0.10,
        taper_ends=True,
    )

    boundary_list = []
    boundary_list.append(grid[0, 0])
    for i in range(1, nx - 1):
        boundary_list.append(grid[i, 0])
    boundary_list.append(grid[nx - 1, 0])
    for i in range(nx - 2, 0, -1):
        boundary_list.append(grid[i, ny - 1])

    boundary = np.array(boundary_list, dtype=float)
    anchor_indices = list(range(len(boundary)))
    edge_types = ["beam"] * len(boundary)
    return grid, boundary, anchor_indices, edge_types


def _build_triangles(nx, ny):
    """Return the triangle list as (n_tris, 3) array of node indices."""
    tri_i, tri_j, tri_k = [], [], []
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            b = (i + 1) * ny + j
            c = i * ny + (j + 1)
            d = (i + 1) * ny + (j + 1)
            tri_i.append(a); tri_j.append(b); tri_k.append(c)
            tri_i.append(b); tri_j.append(d); tri_k.append(c)
    return np.column_stack((tri_i, tri_j, tri_k))


def _render_mesh_view(coords, tris, title):
    try:
        import plotly.graph_objects as go

        xyz_min = coords.min(axis=0)
        xyz_max = coords.max(axis=0)
        xyz_mid = (xyz_min + xyz_max) / 2.0
        span = float(max(xyz_max - xyz_min))
        pad = span * 0.15
        xr = [float(xyz_mid[0] - span / 2 - pad),
              float(xyz_mid[0] + span / 2 + pad)]
        yr = [float(xyz_mid[1] - span / 2 - pad),
              float(xyz_mid[1] + span / 2 + pad)]
        zr = [float(xyz_mid[2] - span / 2 - pad),
              float(xyz_mid[2] + span / 2 + pad)]

        fig = go.Figure()
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tris[:, 0], j=tris[:, 1], k=tris[:, 2],
            color="#4a7a9c", opacity=0.9, flatshading=False,
            showscale=False,
            lighting=dict(ambient=0.6, diffuse=0.9,
                          specular=0.2, roughness=0.5),
        ))
        fig.update_layout(
            title=dict(text=title, font=dict(color="#c8d4e0", size=13)),
            scene=dict(
                xaxis=dict(title="X (m)", gridcolor="#333",
                           color="#888", range=xr, autorange=False),
                yaxis=dict(title="Y (m)", gridcolor="#333",
                           color="#888", range=yr, autorange=False),
                zaxis=dict(title="Z (m)", gridcolor="#333",
                           color="#888", range=zr, autorange=False),
                aspectmode="cube", bgcolor="#0e1117",
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.2)),
            ),
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(color="#ccc", size=11),
            height=480, margin=dict(l=0, r=0, b=0, t=30),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Could not render the 3D view:")
        st.code(str(e), language="text")


def _compute_tri_areas(coords, tris):
    areas = np.zeros(len(tris))
    for k, tri in enumerate(tris):
        p0 = coords[tri[0]]
        p1 = coords[tri[1]]
        p2 = coords[tri[2]]
        areas[k] = 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0)))
    return areas


def _render_debug(initial_points, coords, tris, nx, ny,
                  skip_u=6):
    """
    Digitised debug output.

    skip_u : print only every skip_u-th column along the beam.
             Keeps the output manageable with the denser mesh.
             All columns across the width are always printed.
    """
    with st.expander("DIGITISED OUTPUT - COPY THIS", expanded=False):
        flat0 = initial_points.reshape(-1, 3)

        st.markdown("#### Initial grid coordinates "
                    "(every %d th column along beam)" % skip_u)
        lines = []
        for i in range(0, nx, skip_u):
            for j in range(ny):
                k = i * ny + j
                lines.append(
                    "node %3d  (i=%2d,j=%2d)  x=%+9.5f  y=%+9.5f  z=%+9.5f"
                    % (k, i, j, flat0[k, 0], flat0[k, 1], flat0[k, 2])
                )
        st.code("\n".join(lines), language="text")

        st.markdown("#### Solved coordinates "
                    "(every %d th column along beam)" % skip_u)
        lines = []
        for i in range(0, nx, skip_u):
            for j in range(ny):
                k = i * ny + j
                lines.append(
                    "node %3d  (i=%2d,j=%2d)  x=%+9.5f  y=%+9.5f  z=%+9.5f"
                    % (k, i, j, coords[k, 0], coords[k, 1], coords[k, 2])
                )
        st.code("\n".join(lines), language="text")

        st.markdown("#### Displacement per node "
                    "(every %d th column along beam)" % skip_u)
        lines = []
        disp = np.linalg.norm(coords - flat0, axis=1)
        for i in range(0, nx, skip_u):
            for j in range(ny):
                k = i * ny + j
                lines.append(
                    "node %3d  (i=%2d,j=%2d)  disp=%9.5f"
                    % (k, i, j, disp[k])
                )
        st.code("\n".join(lines), language="text")

        st.markdown("#### Summary")
        areas = _compute_tri_areas(coords, tris)
        st.write("Total triangles: %d" % len(tris))
        st.write("Minimum area: %.8e" % float(areas.min()))
        st.write("Maximum area: %.8e" % float(areas.max()))
        st.write("Mean area: %.8e" % float(areas.mean()))
        st.write("Zero-area count (< 1e-10): %d"
                 % int(np.sum(areas < 1e-10)))
        st.write("Near-zero count (< 1e-6): %d"
                 % int(np.sum(areas < 1e-6)))
        st.write("Positive count (>= 1e-6): %d"
                 % int(np.sum(areas >= 1e-6)))


def render_tester_mbs():
    st.markdown(
        '<div style="background-color:#1f2a3a;border-left:4px solid #3498db;'
        'border-radius:8px;padding:1rem;margin-bottom:1.2rem;">'
        '<div style="color:#3498db;font-weight:700;font-size:1.05rem;'
        'margin-bottom:0.3rem;">EXPERIMENTAL - MBS TESTER</div>'
        '<div style="color:#c8d4e0;font-size:0.9rem;line-height:1.5;">'
        'Mesh density decoupled from anchor count. '
        'Anchors=%d. Subdivisions=%d. Nodes along beam=%d.'
        '</div></div>'
        % (ANCHORS_PER_BEAM, SUBDIVISIONS_PER_SEGMENT,
           ANCHORS_PER_BEAM + (ANCHORS_PER_BEAM - 1) * SUBDIVISIONS_PER_SEGMENT),
        unsafe_allow_html=True,
    )

    try:
        from engine.membrane_boundary import build_and_solve
    except Exception as e:
        st.error("Could not load the MBS engine.")
        st.code(str(e), language="text")
        if st.button("Back to Landing", use_container_width=True,
                     key="mbs_back_import_fail"):
            st.session_state.page = "landing"
            st.rerun()
        return

    nx = ANCHORS_PER_BEAM + (ANCHORS_PER_BEAM - 1) * SUBDIVISIONS_PER_SEGMENT
    ny = NODES_ACROSS

    col1, col2 = st.columns(2)
    with col1:
        run_square = st.button(
            "Run square (4 corners)",
            type="primary", use_container_width=True,
            key="mbs_run_square",
        )
    with col2:
        run_lens = st.button(
            "Run lens (surface engine)",
            type="primary", use_container_width=True,
            key="mbs_run_lens",
        )

    if run_square:
        with st.spinner("Building square mesh..."):
            try:
                boundary, anchors, etypes = _build_square_boundary()
                result = build_and_solve(
                    boundary=boundary,
                    anchor_indices=anchors,
                    edge_types=etypes,
                    nx=nx, ny=ny,
                    membrane_q=1.0, cable_q=5.0,
                )
                st.session_state["mbs_square"] = {
                    "result": result, "boundary": boundary,
                    "initial": result["mesh"]["points"].copy(),
                }
            except Exception as e:
                st.error("Square test raised an error:")
                st.code(str(e), language="text")

    if run_lens:
        with st.spinner("Building lens surface and mesh..."):
            try:
                grid, boundary, anchors, etypes = _build_lens_surface(
                    nx=nx, ny=ny)
                result = build_and_solve(
                    boundary=boundary,
                    anchor_indices=anchors,
                    edge_types=etypes,
                    nx=nx, ny=ny,
                    membrane_q=1.0, cable_q=1.0,
                    initial_points=grid,
                )
                st.session_state["mbs_lens"] = {
                    "result": result, "boundary": boundary,
                    "initial": grid.reshape(-1, 3).copy(),
                }
            except Exception as e:
                st.error("Lens test raised an error:")
                st.code(str(e), language="text")

    has_square = "mbs_square" in st.session_state
    has_lens = "mbs_lens" in st.session_state

    if not has_square and not has_lens:
        st.info("Tap one of the buttons above to run a test.")
        if st.button("Back to Landing", use_container_width=True,
                     key="mbs_back_noresult"):
            st.session_state.page = "landing"
            st.rerun()
        return

    tris = _build_triangles(nx, ny)

    if has_lens:
        st.markdown("### Test 2 — Lens (surface engine)")
        entry = st.session_state["mbs_lens"]
        result = entry["result"]
        boundary = entry["boundary"]
        initial = entry["initial"]
        coords = result["coordinates"]

        _render_mesh_view(coords, tris, "Lens boundary - MBS result")

        m = result["mesh"]["diagnostics"]
        s = result["solve_result"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nodes", m["n_nodes"])
        c2.metric("Edges", m["n_edges"])
        c3.metric("Fixed", m["n_fixed"])
        c4.metric("Free", m["n_free"])
        d1, d2 = st.columns(2)
        d1.metric("FDM residual", "%.4e" % s["residual_norm"])
        d2.metric("Boundary points", len(boundary))

        _render_debug(initial, coords, tris, nx, ny, skip_u=6)

    if has_square:
        st.markdown("### Test 1 — Square (4 corners)")
        entry = st.session_state["mbs_square"]
        result = entry["result"]
        boundary = entry["boundary"]
        initial = entry["initial"]
        coords = result["coordinates"]

        _render_mesh_view(coords, tris, "Square boundary - MBS result")

        m = result["mesh"]["diagnostics"]
        s = result["solve_result"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nodes", m["n_nodes"])
        c2.metric("Edges", m["n_edges"])
        c3.metric("Fixed", m["n_fixed"])
        c4.metric("Free", m["n_free"])
        d1, d2 = st.columns(2)
        d1.metric("FDM residual", "%.4e" % s["residual_norm"])
        d2.metric("Boundary points", len(boundary))

        _render_debug(initial, coords, tris, nx, ny, skip_u=6)

    if st.button("Back to Landing", use_container_width=True,
                 key="mbs_back_bottom"):
        st.session_state.page = "landing"
        st.rerun()





                     
