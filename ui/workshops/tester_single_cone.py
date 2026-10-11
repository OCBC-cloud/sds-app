"""Single Cone — Isolated solver test page.

Purpose: prove that engine.form_finding.solve_fdm produces a real
tensile cone when it is given:
  - a held inner ring (high)
  - a held outer boundary (low, at eave height)
  - a fan mesh between them with interior nodes at a NON-equilibrium
    starting z (flat, at eave height)

If the solver works, the interior nodes will bow outward and the
membrane will form a cone: high at the ring, low at the eave, with
curved radial lines and the fabric sagging between.

If the solver does NOT produce a cone, we have isolated the problem
to how the solver is called, and we fix that before adding any
multi-cone geometry.

No rings, no cones, no primary beam, no ribs, no drop members, no
edge cable, no anchors.  One ring circle, one eave circle, a fan
mesh, and a solve.
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding import solve_fdm
from viewers.figures._shared import apply_common_layout


COL_MEMBRANE = "#4a7a9c"
COL_RING = "#ffd166"
COL_EAVE = "#f1c40f"
COL_NODES = "#e0e0e0"


def _fan_mesh(cx, cy, cz, r_ring, r_eave,
              n_rays, n_radial, z_start):
    """
    Build a fan mesh between an inner ring circle and an outer eave
    circle.

    Interior radial nodes are placed on straight lines in plan
    (between ring and eave), all at z_start.  Not held.  Not on the
    straight line between ring and eave in 3D.  The solver has to
    find the shape.

    Returns dict: points, edges, fixed, ring_ids, eave_ids.
    """
    points = []
    ring_ids = []
    eave_ids = []

    # Ring circle nodes.
    for j in range(n_rays):
        t = 2.0 * math.pi * j / float(n_rays)
        x = cx + r_ring * math.cos(t)
        y = cy + r_ring * math.sin(t)
        z = cz
        ring_ids.append(len(points))
        points.append((x, y, z))

    # Eave circle nodes.
    for j in range(n_rays):
        t = 2.0 * math.pi * j / float(n_rays)
        x = cx + r_eave * math.cos(t)
        y = cy + r_eave * math.sin(t)
        z = 0.0
        eave_ids.append(len(points))
        points.append((x, y, z))

    # Interior radial nodes, one row per radial position.
    rows = []
    for m in range(n_radial):
        f = (m + 1) / float(n_radial + 1)
        row = []
        for j in range(n_rays):
            t = 2.0 * math.pi * j / float(n_rays)
            r_here = r_ring + f * (r_eave - r_ring)
            x = cx + r_here * math.cos(t)
            y = cy + r_here * math.sin(t)
            z = z_start
            row.append(len(points))
            points.append((x, y, z))
        rows.append(row)

    # Edges: radial strips between consecutive rays.
    edge_set = set()

    def add_edge(a, b):
        key = (a, b) if a < b else (b, a)
        edge_set.add(key)

    # Ring -> first row.
    for j in range(n_rays):
        add_edge(ring_ids[j], rows[0][j])
    # Between rows.
    for m in range(n_radial - 1):
        for j in range(n_rays):
            add_edge(rows[m][j], rows[m + 1][j])
    # Last row -> eave.
    for j in range(n_rays):
        add_edge(rows[-1][j], eave_ids[j])

    # Circumferential edges: within the ring, between rows, at the eave.
    for j in range(n_rays):
        jn = (j + 1) % n_rays
        add_edge(ring_ids[j], ring_ids[jn])
        add_edge(eave_ids[j], eave_ids[jn])
        for m in range(n_radial):
            add_edge(rows[m][j], rows[m][jn])

    edges = sorted(edge_set)

    # Fixed: every ring node and every eave node.
    fixed = list(ring_ids) + list(eave_ids)

    return {
        "points": np.asarray(points, dtype=float),
        "edges": edges,
        "fixed": fixed,
        "ring_ids": ring_ids,
        "eave_ids": eave_ids,
        "rows": rows,
    }


def render_tester_single_cone():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>"
        "Single Cone — Isolated Solver Test</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>One ring. One eave. "
        "A fan mesh with interior nodes starting FLAT. If the solver "
        "works, this will bow into a cone.</p>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        ring_radius = st.number_input(
            "Ring radius (m)", 0.1, 10.0, 1.0, 0.1, key="sc_ringr",
        )
    with c2:
        eave_radius = st.number_input(
            "Eave radius (m)", 1.0, 30.0, 8.0, 0.5, key="sc_eaver",
        )

    c1, c2 = st.columns(2)
    with c1:
        ring_z = st.number_input(
            "Ring z (m)", 0.5, 30.0, 7.0, 0.5, key="sc_ringz",
        )
    with c2:
        n_rays = int(st.number_input(
            "Rays (circumferential)", 8, 96, 32, 1, key="sc_nrays",
        ))

    n_radial = int(st.number_input(
        "Radial nodes between ring and eave", 2, 20, 6, 1, key="sc_nradial",
    ))

    c1, c2 = st.columns(2)
    with c1:
        warp_q_input = st.number_input(
            "Force density q (N/m)", 1.0, 100000.0, 2000.0, 100.0,
            key="sc_q",
        )
    with c2:
        z_start = st.number_input(
            "Interior nodes initial z (m)", -20.0, 30.0, 0.0, 0.5,
            key="sc_zstart",
        )

    cx = 0.0
    cy = 0.0
    cz = float(ring_z)

    built = _fan_mesh(cx, cy, cz, float(ring_radius),
                      float(eave_radius), n_rays, n_radial,
                      float(z_start))

    pts_init = built["points"]
    edges = built["edges"]
    fixed = built["fixed"]
    ring_ids = built["ring_ids"]
    eave_ids = built["eave_ids"]

    q = float(warp_q_input)
    q_arr = np.full(len(edges), q, dtype=float)

    try:
        fdm = solve_fdm(pts_init, edges, fixed, q_arr)
        coords = fdm["coordinates"]
        residual_norm = float(fdm["residual_norm"])
        solve_ok = True
        solve_err = ""
    except Exception as e:
        coords = pts_init.copy()
        residual_norm = float("nan")
        solve_ok = False
        solve_err = str(e)

    # Diagnostics on the shape.
    z_ring = coords[ring_ids, 2]
    z_eave = coords[eave_ids, 2]
    interior_ids = [i for i in range(pts_init.shape[0])
                    if i not in set(fixed)]
    z_interior = coords[interior_ids, 2] if interior_ids else np.array([])

    z_ring_min = float(np.min(z_ring))
    z_ring_max = float(np.max(z_ring))
    z_eave_min = float(np.min(z_eave))
    z_eave_max = float(np.max(z_eave))
    z_int_min = float(np.min(z_interior)) if z_interior.size else float("nan")
    z_int_max = float(np.max(z_interior)) if z_interior.size else float("nan")
    moved = float(np.max(np.linalg.norm(coords - pts_init, axis=1))) \
        if pts_init.shape[0] else 0.0

    st.write(
        "**Fixed nodes:** %d ring + %d eave = %d held.  "
        "Free nodes: %d."
        % (len(ring_ids), len(eave_ids), len(fixed),
           pts_init.shape[0] - len(fixed))
    )
    st.write(
        "**Ring z after solve:** min=%.3f  max=%.3f  (should be ~%.3f)"
        % (z_ring_min, z_ring_max, cz)
    )
    st.write(
        "**Eave z after solve:** min=%.3f  max=%.3f  (should be ~0.000)"
        % (z_eave_min, z_eave_max)
    )
    st.write(
        "**Interior z after solve:** min=%.3f  max=%.3f  (initial was "
        "%.3f; a cone should sit strictly between 0 and %.3f)"
        % (z_int_min, z_int_max, float(z_start), cz)
    )
    st.write("**Max free-node movement (m):** %.4f" % moved)
    st.write("**Solve OK:** %s" % str(solve_ok))
    if not solve_ok:
        st.write("**Solve error:** %s" % solve_err)
    else:
        st.write("**Residual norm:** %.6e" % residual_norm)

    fig = go.Figure()

    # Membrane mesh.
    from scipy.spatial import Delaunay
    # Simple fan triangulation: build triangles from the structured rows.
    row_ids = built["rows"]
    tris = []
    for j in range(n_rays):
        jn = (j + 1) % n_rays
        tris.append((ring_ids[j], ring_ids[jn], row_ids[0][j]))
        tris.append((ring_ids[jn], row_ids[0][jn], row_ids[0][j]))
        for m in range(n_radial - 1):
            a0 = row_ids[m][j]
            a1 = row_ids[m][jn]
            b0 = row_ids[m + 1][j]
            b1 = row_ids[m + 1][jn]
            tris.append((a0, a1, b1))
            tris.append((a0, b1, b0))
        tris.append((row_ids[-1][j], row_ids[-1][jn], eave_ids[j]))
        tris.append((row_ids[-1][jn], eave_ids[jn], eave_ids[j]))

    tris = np.asarray(tris, dtype=int)
    fig.add_trace(go.Mesh3d(
        x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
        i=tris[:, 0], j=tris[:, 1], k=tris[:, 2],
        color=COL_MEMBRANE, opacity=0.7, flatshading=True,
        name="membrane", showlegend=False, hoverinfo="skip",
    ))

    # Ring circle.
    ring_pts = coords[ring_ids]
    ring_closed = np.vstack([ring_pts, ring_pts[:1]])
    fig.add_trace(go.Scatter3d(
        x=ring_closed[:, 0], y=ring_closed[:, 1], z=ring_closed[:, 2],
        mode="lines", line=dict(color=COL_RING, width=6),
        name="ring", showlegend=False, hoverinfo="skip",
    ))

    # Eave circle.
    eave_pts = coords[eave_ids]
    eave_closed = np.vstack([eave_pts, eave_pts[:1]])
    fig.add_trace(go.Scatter3d(
        x=eave_closed[:, 0], y=eave_closed[:, 1], z=eave_closed[:, 2],
        mode="lines", line=dict(color=COL_EAVE, width=6),
        name="eave", showlegend=False, hoverinfo="skip",
    ))

    apply_common_layout(fig, float(ring_z))
    st.plotly_chart(fig, use_container_width=True, key="sc_3d")

    # Plan view.
    figp = go.Figure()
    figp.add_trace(go.Scatter(
        x=coords[ring_ids, 0], y=coords[ring_ids, 1],
        mode="lines", line=dict(color=COL_RING, width=3),
        name="ring", showlegend=False, hoverinfo="skip",
    ))
    figp.add_trace(go.Scatter(
        x=coords[eave_ids, 0], y=coords[eave_ids, 1],
        mode="lines", line=dict(color=COL_EAVE, width=3),
        name="eave", showlegend=False, hoverinfo="skip",
    ))
    figp.add_trace(go.Scatter(
        x=coords[interior_ids, 0], y=coords[interior_ids, 1],
        mode="markers", marker=dict(color=COL_NODES, size=3),
        name="interior", showlegend=False, hoverinfo="skip",
    ))
    figp.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="#0e1621",
        plot_bgcolor="#0e1621",
        font=dict(color="#a8b8c8"),
        xaxis=dict(title="X (m)", scaleanchor="y", scaleratio=1.0,
                   gridcolor="#1e2a3a", zerolinecolor="#1e2a3a"),
        yaxis=dict(title="Y (m)",
                   gridcolor="#1e2a3a", zerolinecolor="#1e2a3a"),
        title=dict(text="Plan view (after solve)",
                   font=dict(color="#f39c12", size=14)),
    )
    st.plotly_chart(figp, use_container_width=True, key="sc_plan")
