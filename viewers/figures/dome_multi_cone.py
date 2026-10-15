# =============================================================================
# SDSe - Dome Multi-Cone Viewer
# =============================================================================
# Builds the 3D figure for the Dome Multi-Cone variant.
#
# Reads all inputs from session state under the "ws_dm_" prefix.
#
# PIECE 3d — FRAME + EAVE POLYGON + CONES FROM PICKED CROSSINGS.
#   Adds: for each kept picked crossing, build a full cone:
#       drop member   from crossing, straight down by drop_length
#       ring          ring_diameter, HORIZONTAL (perpendicular to
#                     the ground plane)
#       spokes        radial members from ring centre to ring nodes
#
#   No membrane yet. The membrane comes in Piece 5.
#
# The frame (Piece 1, verified):
#   - Circle ground footprint.
#   - One master frame shape (parabolic / circular / catenary).
#   - N frames spaced along X, M frames spaced along Y.
#   - Each frame is ONE full curve: ground -> apex -> ground.
#   - Apexes step down from the crown to the outer edge.
#   - SPACING RULE: outer pair sits at +/- R*(N-1)/N. "3" means 3.
#
# The eave polygon (Piece 2):
#   - Each frame crosses z = eave_height twice.
#   - Anchors deduped, sorted by angle, joined with straight lines.
#   - Drawn in green. No cosmetic bow.
#
# The picked crossings (Piece 3c):
#   - Read from ws_dm_picked_crossings (set of (i, j) tuples).
#   - z looked up on the frame at each crossing.
#   - Picks with z <= eave_height are dropped.
#
# The cones (Piece 3d):
#   - Drop member straight down from crossing, length = drop_length.
#   - Ring at the bottom, radius = ring_diameter / 2.
#   - Ring plane is HORIZONTAL. Ring axis = (0, 0, 1).
#   - Spokes from ring centre to each ring polygon node.
#
# Signature matches the FIGURE_REGISTRY contract:
#   - no arguments
#   - returns a plotly.graph_objects.Figure
#
# History:
#   2026-10-14 - Piece 1. Frame only.
#   2026-10-14 - Piece 2. Add eave polygon.
#   2026-10-14 - Piece 2b. Corrected spacing rule. Removed ground circle.
#   2026-10-14 - Piece 3c. Add picked crossing markers.
#   2026-10-14 - Piece 3d. Replace markers with full cones.
#   2026-10-14 - Piece 3d fix. Ring orientation is now horizontal,
#                not perpendicular to the frame tangent. Vertical
#                drop, horizontal ring. Simpler and correct.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from viewers.figures._shared import apply_common_layout


# =============================================================================
# COLOURS AND CONSTANTS
# =============================================================================

FRAME_SAMPLES = 200
EAVE_DEDUPE_TOL_FRAC = 0.01
RING_NODES_MIN = 12
RING_NODES_MAX = 32

COL_FRAME_A = "#FF6B6B"
COL_FRAME_B = "#e07b39"
COL_EAVE = "#2ecc71"
COL_RING = "#ffd166"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"


# =============================================================================
# SESSION STATE HELPER
# =============================================================================

def _get(key, default=None):
    return st.session_state.get("ws_dm_" + key, default)


# =============================================================================
# THE DOME PROFILE
# =============================================================================

def _dome_profile_height(r_frac, crown_height, curve_type):
    r_frac = float(max(0.0, min(1.0, r_frac)))
    if curve_type == "circular":
        return crown_height * math.sqrt(max(0.0, 1.0 - r_frac * r_frac))
    if curve_type == "catenary":
        a = 2.5
        num = math.cosh(a * (1.0 - r_frac)) - math.cosh(a)
        den = 1.0 - math.cosh(a)
        return crown_height * num / den
    return crown_height * (1.0 - r_frac * r_frac)


# =============================================================================
# BUILD THE FRAME
# =============================================================================

def _build_frame_curve(half_chord, apex_height, curve_type, n_samples):
    s = np.linspace(-half_chord, +half_chord, n_samples)
    r_frac = np.abs(s) / max(half_chord, 1e-9)
    z = np.array([
        _dome_profile_height(float(rf), apex_height, curve_type)
        for rf in r_frac
    ])
    return s, z


def _offsets(n, ground_radius):
    if n < 1:
        n = 1
    if n == 1:
        return [0.0]
    half_extent = ground_radius * (n - 1.0) / n
    return list(np.linspace(-half_extent, +half_extent, n))


def _build_dome_frame(ground_radius, crown_height, curve_type, n_x, n_y):
    frames = []
    apexes = []
    offsets_x = _offsets(n_x, ground_radius)
    offsets_y = _offsets(n_y, ground_radius)

    for offset in offsets_x:
        chord_half = math.sqrt(max(0.0, ground_radius ** 2 - offset ** 2))
        r_plan = abs(offset)
        apex_h = _dome_profile_height(
            r_plan / ground_radius, crown_height, curve_type
        )
        s, z = _build_frame_curve(chord_half, apex_h, curve_type, FRAME_SAMPLES)
        x = np.full_like(s, offset)
        y = s.copy()
        frames.append({
            "family": "A",
            "x": x, "y": y, "z": z,
            "offset": offset,
            "r_plan": r_plan,
            "apex_h": apex_h,
        })
        apexes.append((offset, 0.0, apex_h, apex_h, r_plan))

    for offset in offsets_y:
        chord_half = math.sqrt(max(0.0, ground_radius ** 2 - offset ** 2))
        r_plan = abs(offset)
        apex_h = _dome_profile_height(
            r_plan / ground_radius, crown_height, curve_type
        )
        s, z = _build_frame_curve(chord_half, apex_h, curve_type, FRAME_SAMPLES)
        x = s.copy()
        y = np.full_like(s, offset)
        frames.append({
            "family": "B",
            "x": x, "y": y, "z": z,
            "offset": offset,
            "r_plan": r_plan,
            "apex_h": apex_h,
        })
        apexes.append((0.0, offset, apex_h, apex_h, r_plan))

    return frames, apexes, offsets_x, offsets_y


# =============================================================================
# EAVE ANCHORS AND POLYGON
# =============================================================================

def _frame_crossings_at_eave(frame, eave_height):
    z = frame["z"]
    x = frame["x"]
    y = frame["y"]
    if z.max() < eave_height:
        return []
    crossings = []
    for k in range(len(z) - 1):
        z0, z1 = z[k], z[k + 1]
        if (z0 - eave_height) * (z1 - eave_height) <= 0.0 and z0 != z1:
            f = (eave_height - z0) / (z1 - z0)
            xx = x[k] + f * (x[k + 1] - x[k])
            yy = y[k] + f * (y[k + 1] - y[k])
            crossings.append((float(xx), float(yy), float(eave_height)))
    return crossings


def _dedupe_plan(points, tol):
    kept = []
    for p in points:
        too_close = False
        for q in kept:
            if math.hypot(p[0] - q[0], p[1] - q[1]) < tol:
                too_close = True
                break
        if not too_close:
            kept.append(p)
    return kept


def _order_by_angle(points):
    def _angle(p):
        return math.atan2(p[1], p[0])
    return sorted(points, key=_angle)


def _build_eave_polygon(frames, eave_height, ground_radius, dome_diameter):
    all_anchors = []
    for f in frames:
        pts = _frame_crossings_at_eave(f, eave_height)
        all_anchors.extend(pts)
    tol = EAVE_DEDUPE_TOL_FRAC * dome_diameter
    deduped = _dedupe_plan(all_anchors, tol)
    ordered = _order_by_angle(deduped)
    return ordered


# =============================================================================
# PICKED CROSSING RESOLUTION
# =============================================================================

def _frame_z_at_plan_offset(offset, cross_axis_value, ground_radius,
                             crown_height, curve_type):
    chord_half = math.sqrt(max(0.0, ground_radius ** 2 - offset ** 2))
    if abs(cross_axis_value) > chord_half + 1e-9:
        return None
    r_plan = abs(offset)
    apex_h = _dome_profile_height(
        r_plan / ground_radius, crown_height, curve_type
    )
    r_frac = abs(cross_axis_value) / max(chord_half, 1e-9)
    z = _dome_profile_height(r_frac, apex_h, curve_type)
    return float(z)


def _resolve_picked_crossings(picked_set, offsets_x, offsets_y,
                                ground_radius, crown_height, curve_type,
                                eave_height):
    kept = []
    dropped = []
    for (i, j) in sorted(picked_set):
        if i < 0 or i >= len(offsets_x) or j < 0 or j >= len(offsets_y):
            dropped.append({
                "i": i, "j": j, "x": None, "y": None, "z": None,
                "reason": "index out of range",
            })
            continue
        xi = offsets_x[i]
        yj = offsets_y[j]
        za = _frame_z_at_plan_offset(
            xi, yj, ground_radius, crown_height, curve_type
        )
        zb = _frame_z_at_plan_offset(
            yj, xi, ground_radius, crown_height, curve_type
        )
        if za is None or zb is None:
            dropped.append({
                "i": i, "j": j, "x": xi, "y": yj, "z": None,
                "reason": "crossing outside frame chord",
            })
            continue
        z = 0.5 * (za + zb)
        if z > eave_height + 1e-9:
            kept.append({
                "i": i, "j": j, "x": float(xi), "y": float(yj),
                "z": float(z),
            })
        else:
            dropped.append({
                "i": i, "j": j, "x": float(xi), "y": float(yj),
                "z": float(z),
                "reason": "at or below eave height",
            })
    return kept, dropped


# =============================================================================
# CONE BUILDING
# =============================================================================

def _ring_node_count(radius, target_len):
    n = int(round(2.0 * math.pi * radius / max(target_len, 1e-6)))
    return max(RING_NODES_MIN, min(RING_NODES_MAX, n))


def _build_cone_geometry(crossing, drop_length, ring_diameter, target_len):
    """
    Build one cone at a crossing.

    The drop member is straight down from the crossing.
    The ring plane is HORIZONTAL. Ring axis = (0, 0, 1).

    Returns a dict with:
        crossing      the (x, y, z) of the attachment point
        ring_centre   (x, y, z) of the ring centre
        ring_nodes    list of (x, y, z), the ring polygon
        ring_axis     (0, 0, 1)
        ring_node_count
    """
    cx = crossing["x"]
    cy = crossing["y"]
    cz = crossing["z"]

    # Vertical drop.
    ring_z = cz - drop_length
    ring_centre = (float(cx), float(cy), float(ring_z))

    # Horizontal ring: nodes at (cx + r cos t, cy + r sin t, ring_z).
    ring_radius = ring_diameter / 2.0
    n_nodes = _ring_node_count(ring_radius, target_len)
    t = np.linspace(0.0, 2.0 * math.pi, n_nodes, endpoint=False)
    ring_nodes = [
        (float(cx + ring_radius * math.cos(tk)),
         float(cy + ring_radius * math.sin(tk)),
         float(ring_z))
        for tk in t
    ]

    return {
        "crossing": (float(cx), float(cy), float(cz)),
        "ring_centre": ring_centre,
        "ring_nodes": ring_nodes,
        "ring_axis": (0.0, 0.0, 1.0),
        "ring_node_count": n_nodes,
    }


# =============================================================================
# FRAME VERIFICATION
# =============================================================================

def _verify_frame_against_globe(apexes, ground_radius, crown_height, curve_type):
    tol = max(1e-3 * crown_height, 1e-6)
    rows = []
    for (ax, ay, az, apex_h, r_plan) in apexes:
        r_frac = r_plan / max(ground_radius, 1e-9)
        ref_h = _dome_profile_height(r_frac, crown_height, curve_type)
        diff = abs(az - ref_h)
        rows.append({
            "x": ax, "y": ay,
            "r_plan": r_plan,
            "apex_h": az,
            "ref_h": ref_h,
            "diff": diff,
            "ok": diff <= tol,
        })
    return rows


# =============================================================================
# PUBLIC FIGURE BUILDER
# =============================================================================

def build_dome_multi_cone():
    # ---- Read inputs -----------------------------------------------------
    dome_diameter = float(_get("dome_diameter", 18.0))
    crown_height = float(_get("crown_height", 9.0))
    n_x = int(_get("meridians_x", 5))
    n_y = int(_get("meridians_y", 5))
    eave_height = float(_get("eave_height", 3.2))
    curve_type = str(_get("curve_type", "parabolic"))
    drop_length = float(_get("drop_length", 1.0))
    ring_diameter = float(_get("ring_diameter", 2.0))

    ground_radius = max(dome_diameter / 2.0, 1e-6)

    # ---- Read picked crossings -------------------------------------------
    picked_raw = _get("picked_crossings", None)
    if picked_raw is None:
        picked_set = set()
    else:
        try:
            picked_set = set(
                (int(i), int(j)) for (i, j) in picked_raw
            )
        except (TypeError, ValueError):
            picked_set = set()

    # ---- Build the frame -------------------------------------------------
    frames, apexes, offsets_x, offsets_y = _build_dome_frame(
        ground_radius=ground_radius,
        crown_height=crown_height,
        curve_type=curve_type,
        n_x=n_x,
        n_y=n_y,
    )

    # ---- Eave polygon ----------------------------------------------------
    eave_polygon = _build_eave_polygon(
        frames, eave_height, ground_radius, dome_diameter
    )

    # ---- Resolve picks ---------------------------------------------------
    kept_picks, dropped_picks = _resolve_picked_crossings(
        picked_set, offsets_x, offsets_y,
        ground_radius, crown_height, curve_type, eave_height,
    )

    # ---- Build cones -----------------------------------------------------
    target_len = max(dome_diameter / 40.0, 0.4)
    cones = []
    for pick in kept_picks:
        cone = _build_cone_geometry(
            pick, drop_length, ring_diameter, target_len,
        )
        if cone is not None:
            cones.append(cone)

    # ---- Draw ------------------------------------------------------------
    fig = go.Figure()

    # Frames
    for f in frames:
        color = COL_FRAME_A if f["family"] == "A" else COL_FRAME_B
        fig.add_trace(go.Scatter3d(
            x=f["x"], y=f["y"], z=f["z"],
            mode="lines",
            line=dict(color=color, width=4),
            name="frame " + f["family"],
            showlegend=False, hoverinfo="skip",
        ))

    # Eave polygon
    if len(eave_polygon) >= 3:
        ex = [p[0] for p in eave_polygon] + [eave_polygon[0][0]]
        ey = [p[1] for p in eave_polygon] + [eave_polygon[0][1]]
        ez = [p[2] for p in eave_polygon] + [eave_polygon[0][2]]
        fig.add_trace(go.Scatter3d(
            x=ex, y=ey, z=ez,
            mode="lines",
            line=dict(color=COL_EAVE, width=6),
            name="eave polygon",
            showlegend=False, hoverinfo="skip",
        ))

    # Cones
    for cone in cones:
        cx, cy, cz = cone["crossing"]
        rx, ry, rz = cone["ring_centre"]

        # Drop member — crossing to ring centre, vertical
        fig.add_trace(go.Scatter3d(
            x=[cx, rx], y=[cy, ry], z=[cz, rz],
            mode="lines",
            line=dict(color=COL_DROP, width=4),
            name="drop", showlegend=False, hoverinfo="skip",
        ))

        # Ring polygon — closed loop, horizontal
        rn = cone["ring_nodes"]
        rxx = [p[0] for p in rn] + [rn[0][0]]
        ryy = [p[1] for p in rn] + [rn[0][1]]
        rzz = [p[2] for p in rn] + [rn[0][2]]
        fig.add_trace(go.Scatter3d(
            x=rxx, y=ryy, z=rzz,
            mode="lines",
            line=dict(color=COL_RING, width=5),
            name="ring", showlegend=False, hoverinfo="skip",
        ))

        # Spokes from ring centre to each ring node
        for p in rn:
            fig.add_trace(go.Scatter3d(
                x=[rx, p[0]], y=[ry, p[1]], z=[rz, p[2]],
                mode="lines",
                line=dict(color=COL_SPOKE, width=2),
                name="spoke", showlegend=False, hoverinfo="skip",
            ))

    # ---- Owner-tier expanders --------------------------------------------
    access_mode = str(st.session_state.get("access_mode", "owner")).lower()
    if access_mode == "owner":
        rows = _verify_frame_against_globe(
            apexes, ground_radius, crown_height, curve_type
        )
        all_ok = all(r["ok"] for r in rows)
        with st.expander("Frame verification (owner tier)", expanded=False):
            st.write("Overall: **" + ("OK" if all_ok else "FAIL") + "**")
            table = (
                "  idx   x          y          r_plan     apex_h     "
                "ref_h      diff       ok\n"
                "  ---   ---------  ---------  ---------  ---------  "
                "---------  ---------  ------\n"
            )
            for k, r in enumerate(rows):
                table += (
                    "  %3d   %+8.4f  %+8.4f  %8.4f  %8.4f  %8.4f  "
                    "%9.2e  %s\n"
                    % (k, r["x"], r["y"], r["r_plan"], r["apex_h"],
                       r["ref_h"], r["diff"], "ok" if r["ok"] else "FAIL")
                )
            st.code(table, language="text")

        with st.expander("Eave polygon (owner tier)", expanded=False):
            st.write("Total anchors after dedupe: **%d**" % len(eave_polygon))
            if len(eave_polygon) >= 3:
                table = (
                    "  idx      x          y          z\n"
                    "  ---   ---------  ---------  ---------\n"
                )
                for k, p in enumerate(eave_polygon):
                    table += "  %3d   %+8.4f  %+8.4f  %8.4f\n" % (
                        k, p[0], p[1], p[2]
                    )
                st.code(table, language="text")

        with st.expander("Picked crossings (owner tier)", expanded=False):
            st.write(
                "**Total picks: %d. Kept: %d. Dropped: %d. "
                "Cones built: %d.**"
                % (len(picked_set), len(kept_picks),
                   len(dropped_picks), len(cones))
            )

            if kept_picks:
                st.markdown("**Kept (z above eave height):**")
                table = (
                    "  idx   i   j      x          y          z\n"
                    "  ---  --  --   ---------  ---------  ---------\n"
                )
                for k, p in enumerate(kept_picks):
                    table += (
                        "  %3d  %2d  %2d   %+8.4f  %+8.4f  %8.4f\n"
                        % (k, p["i"], p["j"], p["x"], p["y"], p["z"])
                    )
                st.code(table, language="text")

            if dropped_picks:
                st.markdown("**Dropped:**")
                table = (
                    "  idx   i   j      x          y          z        reason\n"
                    "  ---  --  --   ---------  ---------  ---------  ------\n"
                )
                for k, p in enumerate(dropped_picks):
                    x_s = ("%+8.4f" % p["x"]) if p["x"] is not None else "     ---"
                    y_s = ("%+8.4f" % p["y"]) if p["y"] is not None else "     ---"
                    z_s = ("%8.4f" % p["z"]) if p["z"] is not None else "     ---"
                    table += (
                        "  %3d  %2d  %2d   %s  %s  %s  %s\n"
                        % (k, p["i"], p["j"], x_s, y_s, z_s, p["reason"])
                    )
                st.code(table, language="text")

        with st.expander("Cone geometry (owner tier)", expanded=False):
            st.write(
                "One entry per built cone. Drop member is vertical. "
                "Ring plane is horizontal (perpendicular to ground)."
            )
            table = (
                "  idx   crossing (x,y,z)          ring centre (x,y,z)        "
                "ring axis          nodes\n"
                "  ---   -------------------------  -------------------------  "
                "-----------------  -----\n"
            )
            for k, cone in enumerate(cones):
                cx, cy, cz = cone["crossing"]
                rx, ry, rz = cone["ring_centre"]
                ax, ay, az = cone["ring_axis"]
                table += (
                    "  %3d   (%+7.3f,%+7.3f,%6.3f)  "
                    "(%+7.3f,%+7.3f,%6.3f)  "
                    "(%+4.2f,%+4.2f,%+4.2f)  %5d\n"
                    % (k, cx, cy, cz, rx, ry, rz, ax, ay, az,
                       cone["ring_node_count"])
                )
            st.code(table, language="text")

    return apply_common_layout(fig, crown_height)


# =============================================================================
# END OF viewers/figures/dome_multi_cone.py
# =============================================================================
