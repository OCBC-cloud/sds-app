# =============================================================================
# SDSe - Mesh Z Diagnostic
# =============================================================================
# Diagnostic-only Lab page. Does NOT run the FDM solver.
#
# Purpose: for every fabric node in the multi-cone mesh, report
#   - its plan distance to the nearest ring centre
#   - its plan distance to the nearest ring circle
#   - its initial z (from the _z_at interpolation)
#   - the ring z it is closest to
#   - the vertical gap (ring_z - z_initial)
#
# The hypothesis this page tests:
#   the fabric nodes near a ring are being initialised at a z that
#   is far below the ring z. When they are then attached to the ring
#   and released, the FDM has to close that gap in one solve, which
#   produces a large residual.
#
# If the table shows vertical gaps of 0.3 m to 1.0 m for fabric
# nodes that ARE attached to the ring, that confirms the cause.
# If the gaps are small everywhere, the cause is elsewhere.
#
# No engine files are modified.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from viewers.figures._shared import (
    apply_common_layout,
    beam_curve,
    arclength_parametrisation,
)


# -----------------------------------------------------------------------------
# We import the helper functions from the multi-cone tester.
# Nothing in that file is modified. We just call its geometry builders.
# -----------------------------------------------------------------------------
from ui.workshops.tester_multi_cone import (
    _ellipse_y,
    _rib_stations,
    _tip_x_at_eave,
    _build_eave_anchors,
    _subdivide_polygon,
    _cone_arc_positions,
    _max_spacing_for,
    _ring_node_count,
    RIB_SEGMENTS,
    COL_PRIMARY,
    COL_RIB,
    COL_RING_EDGE,
)


COL_RING_HIGH = "#ffd166"
COL_RING_OK = "#4ade80"
COL_RING_BAD = "#ff6b6b"


def _build_geometry_and_z_table(
    span, apex, mid_width, eave_height, ring_diameter,
    curve_type, secondary_count, optional_ends, subdivisions,
    number_of_cones, ring_spacing, ring_clearance,
):
    """
    Rebuild the multi-cone geometry using the same helpers as
    tester_multi_cone.py, then produce a per-fabric-node table of
    z gaps to the nearest ring.
    """
    xp = np.linspace(-span / 2.0, span / 2.0, 200)
    zp = beam_curve(xp, span, apex, curve_type)
    s_p, total_p = arclength_parametrisation(xp, zp)

    rib_x = _rib_stations(secondary_count, optional_ends, span, xp, s_p, total_p)
    rib_peak_z = np.interp(rib_x, xp, zp)
    rib_half_width = np.array(
        [_ellipse_y(float(xr), span, mid_width) for xr in rib_x], dtype=float
    )

    s_rings = _cone_arc_positions(number_of_cones, ring_spacing, total_p)
    ring_specs = []
    x_rings = []
    for s_val in s_rings:
        x_val = float(np.interp(s_val, s_p, xp))
        bz_val = float(np.interp(s_val, s_p, zp))
        rz_val = bz_val - float(ring_clearance)
        x_rings.append(x_val)
        ring_specs.append({
            "cx": x_val,
            "cy": 0.0,
            "cz": rz_val,
            "r": float(ring_diameter) / 2.0,
            "beam_z": bz_val,
        })

    tip_x = _tip_x_at_eave(span, apex, eave_height, curve_type)
    anchors = _build_eave_anchors(
        rib_x, rib_half_width, rib_peak_z, eave_height, tip_x
    )
    perimeter_loop, anchor_idx = _subdivide_polygon(anchors, subdivisions)
    bd = np.diff(np.vstack([perimeter_loop, perimeter_loop[:1]]), axis=0)
    L_avg = float(np.mean(np.linalg.norm(bd, axis=1)))
    target_len = max(L_avg, 1e-6)

    poly_xy = perimeter_loop[:, :2]
    ring_centres_radii = [(float(s["cx"]), float(s["cy"]), float(s["r"]))
                          for s in ring_specs]

    xmin = float(np.min(perimeter_loop[:, 0]))
    xmax = float(np.max(perimeter_loop[:, 0]))
    ymin = float(np.min(perimeter_loop[:, 1]))
    ymax = float(np.max(perimeter_loop[:, 1]))

    h = float(target_len)
    xs = np.arange(xmin + 0.5 * h, xmax, h)
    ys = np.arange(ymin + 0.5 * h, ymax, h)

    def _point_in_polygon(x, y, poly):
        n = poly.shape[0]
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = poly[i, 0], poly[i, 1]
            xj, yj = poly[j, 0], poly[j, 1]
            if (yi > y) != (yj > y):
                xint = (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi
                if x < xint:
                    inside = not inside
            j = i
        return inside

    def _nearest_ring(x, y):
        best_d = float("inf")
        best_z = eave_height
        best_cx = 0.0
        best_cy = 0.0
        best_r = 0.0
        for spec in ring_specs:
            cx = float(spec["cx"]); cy = float(spec["cy"])
            r = float(spec["r"]); cz = float(spec["cz"])
            d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) - r
            if d < best_d:
                best_d = d
                best_z = cz
                best_cx = cx
                best_cy = cy
                best_r = r
        return max(best_d, 0.0), best_z, best_cx, best_cy, best_r

    def _z_at(x, y):
        d_ring, rz, _, _, _ = _nearest_ring(x, y)
        d_perim = float(np.min(np.linalg.norm(
            poly_xy - np.array([x, y]), axis=1
        )))
        denom = d_ring + d_perim
        if denom < 1e-9:
            return float(rz)
        w = d_ring / denom
        return float(rz + (eave_height - rz) * w)

    clearance_band = 0.6 * target_len
    interior_xy = []
    for x in xs:
        for y in ys:
            if not _point_in_polygon(x, y, poly_xy):
                continue
            too_close = False
            for (cx, cy, r) in ring_centres_radii:
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if d < r + clearance_band:
                    too_close = True
                    break
            if too_close:
                continue
            interior_xy.append((float(x), float(y)))

    rows = []
    for (x, y) in interior_xy:
        z_init = _z_at(x, y)
        d_ring, ring_z, cx, cy, r = _nearest_ring(x, y)
        d_centre = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        gap = ring_z - z_init
        rows.append({
            "x": x, "y": y, "z_init": z_init,
            "d_ring": d_ring, "d_centre": d_centre,
            "ring_z": ring_z, "gap": gap,
            "ring_cx": cx, "ring_cy": cy, "ring_r": r,
        })

    return {
        "rows": rows,
        "perimeter_loop": perimeter_loop,
        "ring_specs": ring_specs,
        "x_rings": x_rings,
        "target_len": target_len,
        "total_p": total_p,
        "xp": xp, "zp": zp,
        "rib_x": rib_x,
        "rib_peak_z": rib_peak_z,
        "rib_half_width": rib_half_width,
    }


def _plot_z_diagnostic(rows, ring_specs, perimeter_loop, xp, zp,
                       rib_x, rib_half_width, rib_peak_z, apex):
    fig = go.Figure()

    # Fabric nodes coloured by vertical gap to nearest ring.
    xs = [r["x"] for r in rows]
    ys = [r["y"] for r in rows]
    zs = [r["z_init"] for r in rows]
    gaps = [abs(r["gap"]) for r in rows]

    fig.add_trace(go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode="markers",
        marker=dict(
            size=5,
            color=gaps,
            colorscale=[
                [0.0, COL_RING_OK],
                [0.3, "#facc15"],
                [0.7, COL_RING_BAD],
                [1.0, "#7f1d1d"],
            ],
            colorbar=dict(
                title="|gap| (m)",
                tickfont=dict(color="#a8b8c8"),
                titlefont=dict(color="#a8b8c8"),
            ),
            showscale=True,
        ),
        name="fabric nodes",
    ))

    # Rings drawn at their true z.
    for spec in ring_specs:
        cx = float(spec["cx"]); cy = float(spec["cy"])
        cz = float(spec["cz"]); r = float(spec["r"])
        t = np.linspace(0.0, 2.0 * math.pi, 64)
        fig.add_trace(go.Scatter3d(
            x=cx + r * np.cos(t),
            y=cy + r * np.sin(t),
            z=np.full(64, cz),
            mode="lines",
            line=dict(color=COL_RING_EDGE, width=6),
            name="ring",
            showlegend=False,
        ))

    # Perimeter for context.
    pl = np.vstack([perimeter_loop, perimeter_loop[:1]])
    fig.add_trace(go.Scatter3d(
        x=pl[:, 0], y=pl[:, 1], z=pl[:, 2],
        mode="lines",
        line=dict(color="#4a7a9c", width=3, dash="dot"),
        name="eave",
        showlegend=False,
    ))

    # Primary beam and ribs for context.
    fig.add_trace(go.Scatter3d(
        x=xp, y=np.zeros_like(xp), z=zp,
        mode="lines", line=dict(color=COL_PRIMARY, width=5),
        name="primary", showlegend=False,
    ))
    for i in range(len(rib_x)):
        y = np.linspace(-rib_half_width[i], +rib_half_width[i], RIB_SEGMENTS)
        u = y / rib_half_width[i]
        z = rib_peak_z[i] * (1.0 - u ** 2)
        x = np.full_like(y, rib_x[i])
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode="lines", line=dict(color=COL_RIB, width=3),
            name="rib", showlegend=False,
        ))

    apply_common_layout(fig, apex)
    return fig


def render_mesh_z_diagnostic():
    st.markdown(
        "<h2 style='color:#f39c12;margin-bottom:0.2rem;'>Mesh Z Diagnostic</h2>"
        "<p style='color:#a8b8c8;margin-top:0;'>No solver. No roof. "
        "Every fabric node, its initial z, and the vertical gap to the "
        "nearest ring. This is the evidence table.</p>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        span = st.number_input("Primary span (m)", 6.0, 60.0, 18.0, 0.5,
                                key="d_span")
    with c2:
        apex = st.number_input("Primary apex (m)", 1.0, 30.0, 9.0, 0.5,
                                key="d_apex")

    c1, c2 = st.columns(2)
    with c1:
        mid_width = st.number_input("Mid-span width (m)", 6.0, 60.0, 18.0, 0.5,
                                     key="d_width")
    with c2:
        eave_height = st.number_input("Eave height (m)", 0.5, 10.0, 2.8, 0.1,
                                       key="d_eave")

    c1, c2 = st.columns(2)
    with c1:
        ring_diameter = st.number_input("Ring diameter (m)", 0.5, 10.0, 0.5, 0.1,
                                         key="d_rd")
    with c2:
        curve_type = st.selectbox(
            "Curve type", ["parabolic", "circular", "catenary"],
            index=0, key="d_curve",
        )

    c1, c2 = st.columns(2)
    with c1:
        secondary_count = int(st.number_input("Secondary count", 2, 20, 3, 1,
                                                key="d_nribs"))
    with c2:
        optional_ends = st.toggle("Optional ends", value=False,
                                    key="d_optends")

    subdivisions = int(st.number_input(
        "Subdivisions per edge", 5, 25, 11, 1, key="d_subdiv"
    ))

    c1, c2 = st.columns(2)
    with c1:
        number_of_cones = int(st.number_input(
            "Number of cones", 1, 20, 3, 1, key="d_ncones"
        ))
    with c2:
        ring_spacing = st.number_input(
            "Distance between adjacent cones (m, along beam)",
            0.5, 10.0, 3.0, 0.1, key="d_spacing"
        )

    ring_clearance = st.number_input(
        "Ring clearance below beam (m)", 0.1, 5.0, 1.0, 0.1, key="d_clr",
    )

    if st.button("Run diagnostic", key="d_run", type="primary",
                 use_container_width=True):
        try:
            geom = _build_geometry_and_z_table(
                span, apex, mid_width, eave_height, ring_diameter,
                curve_type, secondary_count, optional_ends, subdivisions,
                number_of_cones, ring_spacing, ring_clearance,
            )
        except Exception as e:
            st.error("Diagnostic failed: " + str(e))
            return

        rows = geom["rows"]
        if len(rows) == 0:
            st.warning("No fabric nodes generated.")
            return

        gaps = np.array([abs(r["gap"]) for r in rows])
        d_rings = np.array([r["d_ring"] for r in rows])

        # Summary stats.
        st.markdown("#### Summary")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Fabric nodes", len(rows))
        with m2:
            st.metric("Max |gap| (m)", "%.4f" % float(gaps.max()))
        with m3:
            st.metric("Mean |gap| (m)", "%.4f" % float(gaps.mean()))
        with m4:
            n_big = int(np.sum(gaps > 0.20))
            st.metric("Nodes |gap| > 0.20 m", n_big)

        # Histogram of gaps.
        st.markdown("#### Distribution of vertical gap")
        bins = [0.0, 0.05, 0.10, 0.20, 0.30, 0.50, 0.75, 1.00, 2.00, 5.00]
        counts = []
        for i in range(len(bins) - 1):
            c = int(np.sum((gaps >= bins[i]) & (gaps < bins[i + 1])))
            counts.append(c)
        hist_lines = ["range (m)         count"]
        hist_lines.append("-" * 30)
        for i in range(len(bins) - 1):
            hist_lines.append(
                "%5.2f - %5.2f     %6d" % (bins[i], bins[i + 1], counts[i])
            )
        st.code("\n".join(hist_lines), language="text")

        # Table sorted by |gap| descending.
        st.markdown("#### Fabric nodes sorted by |gap| (largest first)")
        rows_sorted = sorted(rows, key=lambda r: -abs(r["gap"]))
        lines = [
            "%6s  %9s  %9s  %9s  %9s  %9s  %9s  %9s"
            % ("idx", "x", "y", "z_init", "d_ring", "d_centre", "ring_z", "gap")
        ]
        lines.append("-" * 82)
        for i, r in enumerate(rows_sorted):
            lines.append(
                "%6d  %9.4f  %9.4f  %9.4f  %9.4f  %9.4f  %9.4f  %+9.4f"
                % (i, r["x"], r["y"], r["z_init"],
                   r["d_ring"], r["d_centre"], r["ring_z"], r["gap"])
            )
        st.code("\n".join(lines), language="text")

        # 3D plot.
        st.markdown("#### 3D view — fabric nodes coloured by |gap|")
        st.plotly_chart(
            _plot_z_diagnostic(
                rows, geom["ring_specs"], geom["perimeter_loop"],
                geom["xp"], geom["zp"],
                geom["rib_x"], geom["rib_half_width"], geom["rib_peak_z"],
                apex,
            ),
            use_container_width=True,
            key="d_plot",
        )


# =============================================================================
# END OF ui/workshops/mesh_z_diagnostic.py
# =============================================================================
