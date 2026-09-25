# =============================================================================
# SDSe Fluid Design Studio - MBS Tester Workshop
# =============================================================================
# Temporary research page. Tests the Membrane Boundary Schema engine.
#
# Reached from the landing page button "Open MBS Tester".
#
# Two tests:
#   Test 1 - Square boundary. Four corners. Minimal boundary.
#   Test 2 - Lens boundary. Two beams, two tips. Multi-point
#            boundary. The real Saddle Span shape.
#
# Purpose:
#   Run the MBS engine on each boundary, render the resulting
#   mesh in 3D, and report the diagnostics. This is the first
#   end-to-end test of the engine from inside the app.
#
# Isolation:
#   Self-contained. If the import fails, this page shows an
#   error and the rest of the app is unaffected.
#
# Status: EXPERIMENTAL. Not a shipping feature.
# =============================================================================

import numpy as np
import streamlit as st


def _build_square_boundary():
    """
    Test 1 - Square boundary.
    Four corners. Two low, two high. All edges "cable".
    Minimal boundary to test the mesh builder.
    """
    corners = np.array([
        [-1.5, -1.5, 0.0],   # SW, low
        [ 1.5, -1.5, 0.0],   # SE, low
        [ 1.5,  1.5, 2.0],   # NE, high
        [-1.5,  1.5, 2.0],   # NW, high
    ], dtype=float)
    anchor_indices = [0, 1, 2, 3]
    edge_types = ["cable", "cable", "cable", "cable"]
    return corners, anchor_indices, edge_types


def _build_lens_boundary(n_points_per_beam=20):
    """
    Test 2 - Lens boundary. Two beams, two tips.

    Beam L runs from the left tip to the right tip.
    Beam R runs from the right tip back to the left tip.
    The two tips are single points.

    Uses a parabola for the beam z-curve, and the same
    beam-plan formula as the shipping Saddle viewer.

    Boundary order (counter-clockwise):
      [Beam L points] + [Right tip] + [Beam R points] + [Left tip]
    """
    from viewers.figures._shared import beam_curve, arclength_parametrisation

    span = 3.0
    apex = 4.0
    rise = 1.5
    curve_type = "parabolic"

    # Sample the beam curve densely, then pick n points per beam
    # at equal arc-length.
    n_dense = 200
    x_dense = np.linspace(-span / 2.0, span / 2.0, n_dense)
    z_dense = beam_curve(x_dense, span, rise, curve_type)
    s_dense, total = arclength_parametrisation(x_dense, z_dense)

    # Pick n_points_per_beam points along arc length.
    # Include both endpoints of the beam (tips).
    # Use n-2 interior points, plus the two tips.
    arc_targets = np.linspace(0.0, total, n_points_per_beam)
    bx = np.interp(arc_targets, s_dense, x_dense)
    bz = np.interp(arc_targets, s_dense, z_dense)

    # Beam edges in plan: y1 (one side), y2 (other side).
    base_width = apex * 0.5
    y1_pts = -base_width * (1.0 - (2.0 * bx / span) ** 2)
    y2_pts = base_width * (1.0 - (2.0 * bx / span) ** 2)

    # Beam L: from left tip to right tip.
    # Both tips converge at y=0.
    # Force the first and last points of each beam to y=0 (tips).
    y1_pts[0] = 0.0
    y1_pts[-1] = 0.0
    y2_pts[0] = 0.0
    y2_pts[-1] = 0.0

    # Beam L as list of (x, y, z)
    beam_L = np.column_stack((bx, y1_pts, bz))
    # Beam R as list of (x, y, z) — same x/z, opposite y
    beam_R = np.column_stack((bx, y2_pts, bz))

    # Build the full boundary loop.
    # Beam L: left-to-right.
    # Right tip: the last point of Beam L, at y=0. Same as Beam L[-1].
    # Beam R: reversed, right-to-left. Skip the last point of Beam R
    # to avoid duplicating the right tip.
    # Left tip: the first point of Beam L, at y=0. Same as Beam L[0].

    boundary_list = []
    # Beam L, left to right
    for k in range(len(beam_L)):
        boundary_list.append(beam_L[k])
    # Beam R, right to left. Skip the first (which is the right tip,
    # already the last point of Beam L). Skip the last (which is
    # the left tip, already the first point of Beam L).
    for k in range(len(beam_R) - 2, 0, -1):
        boundary_list.append(beam_R[k])

    boundary = np.array(boundary_list, dtype=float)

    # Anchors: all boundary points.
    anchor_indices = list(range(len(boundary)))

    # Edge types: all "beam". The beam edges follow the beam
    # contour. The tips are single points held by the anchor.
    edge_types = ["beam"] * len(boundary)

    return boundary, anchor_indices, edge_types


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
            color="#4a7a9c",
            opacity=0.9,
            flatshading=False,
            name="Membrane",
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
                aspectmode="cube",
                bgcolor="#0e1117",
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.2)),
            ),
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="#ccc", size=11),
            height=480,
            margin=dict(l=0, r=0, b=0, t=30),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Could not render the 3D view:")
        st.code(str(e), language="text")


def _report_diagnostics(result, boundary, nx, ny):
    mesh = result["mesh"]
    solve = result["solve_result"]
    coords = result["coordinates"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nodes", mesh["diagnostics"]["n_nodes"])
    c2.metric("Edges", mesh["diagnostics"]["n_edges"])
    c3.metric("Fixed", mesh["diagnostics"]["n_fixed"])
    c4.metric("Free", mesh["diagnostics"]["n_free"])

    d1, d2 = st.columns(2)
    d1.metric("FDM residual", "%.4e" % solve["residual_norm"])
    d2.metric("Boundary points", len(boundary))

    # Compute triangle areas.
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
    st.markdown("**Smallest 10 initial triangles:**")
    st.code("\n".join(rows), language="text")

    return tri_areas


def render_tester_mbs():
    """Render the MBS engine tester page."""

    st.markdown(
        '<div style="background-color:#1f2a3a;border-left:4px solid #3498db;'
        'border-radius:8px;padding:1rem;margin-bottom:1.2rem;">'
        '<div style="color:#3498db;font-weight:700;font-size:1.05rem;'
        'margin-bottom:0.3rem;">EXPERIMENTAL - MBS TESTER</div>'
        '<div style="color:#c8d4e0;font-size:0.9rem;line-height:1.5;">'
        'Research tool. Two tests: a four-corner square, and a '
        'lens boundary with two beams and two tips. Compare the '
        'resulting meshes.'
        '</div></div>',
        unsafe_allow_html=True,
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

    # ---- Two buttons ------------------------------------------------------
    nx = 8
    ny = 8

    col1, col2 = st.columns(2)
    with col1:
        run_square = st.button(
            "Run square (4 corners)",
            type="primary",
            use_container_width=True,
            key="mbs_run_square",
        )
    with col2:
        run_lens = st.button(
            "Run lens (2 beams)",
            type="primary",
            use_container_width=True,
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
                    membrane_q=1.0,
                    cable_q=5.0,
                )
                st.session_state["mbs_square"] = {
                    "result": result, "boundary": boundary,
                }
            except Exception as e:
                st.error("Square test raised an error:")
                st.code(str(e), language="text")

    if run_lens:
        with st.spinner("Building lens mesh..."):
            try:
                boundary, anchors, etypes = _build_lens_boundary(
                    n_points_per_beam=20)
                result = build_and_solve(
                    boundary=boundary,
                    anchor_indices=anchors,
                    edge_types=etypes,
                    nx=nx, ny=ny,
                    membrane_q=1.0,
                    cable_q=1.0,
                )
                st.session_state["mbs_lens"] = {
                    "result": result, "boundary": boundary,
                }
            except Exception as e:
                st.error("Lens test raised an error:")
                st.code(str(e), language="text")

    # ---- Render whichever results exist ----------------------------------
    has_square = "mbs_square" in st.session_state
    has_lens = "mbs_lens" in st.session_state

    if not has_square and not has_lens:
        st.info("Tap one of the buttons above to run a test.")
        if st.button("Back to Landing", use_container_width=True,
                     key="mbs_back_noresult"):
            st.session_state.page = "landing"
            st.rerun()
        return

    if has_square:
        st.markdown("### Test 1 — Square (4 corners)")
        entry = st.session_state["mbs_square"]
        result = entry["result"]
        boundary = entry["boundary"]
        mesh = result["mesh"]
        coords = result["coordinates"]
        n_nodes = mesh["diagnostics"]["n_nodes"]

        # Build triangles from the grid.
        tri_i, tri_j, tri_k = [], [], []
        for i in range(nx - 1):
            for j in range(ny - 1):
                a = i * ny + j
                b = (i + 1) * ny + j
                c = i * ny + (j + 1)
                d = (i + 1) * ny + (j + 1)
                tri_i.append(a); tri_j.append(b); tri_k.append(c)
                tri_i.append(b); tri_j.append(d); tri_k.append(c)
        tris = np.column_stack((tri_i, tri_j, tri_k))

        _render_mesh_view(coords, tris, "Square boundary - MBS result")
        _report_diagnostics(result, boundary, nx, ny)
        st.markdown("---")

    if has_lens:
        st.markdown("### Test 2 — Lens (2 beams, 2 tips)")
        entry = st.session_state["mbs_lens"]
        result = entry["result"]
        boundary = entry["boundary"]
        mesh = result["mesh"]
        coords = result["coordinates"]

        tri_i, tri_j, tri_k = [], [], []
        for i in range(nx - 1):
            for j in range(ny - 1):
                a = i * ny + j
                b = (i + 1) * ny + j
                c = i * ny + (j + 1)
                d = (i + 1) * ny + (j + 1)
                tri_i.append(a); tri_j.append(b); tri_k.append(c)
                tri_i.append(b); tri_j.append(d); tri_k.append(c)
        tris = np.column_stack((tri_i, tri_j, tri_k))

        _render_mesh_view(coords, tris, "Lens boundary - MBS result")
        _report_diagnostics(result, boundary, nx, ny)
        st.markdown("---")

    if st.button("Back to Landing", use_container_width=True,
                 key="mbs_back_bottom"):
        st.session_state.page = "landing"
        st.rerun()
