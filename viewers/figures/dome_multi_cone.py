# =============================================================================
# SDSe - Dome Multi-Cone Viewer
# =============================================================================
# Builds the 3D figure for the Dome Multi-Cone variant.
#
# Reads all inputs from session state under the "ws_dm_" prefix.
#
# PIECE 3c — FRAME + EAVE POLYGON + PICKED CROSSING MARKERS.
#   Adds: the viewer reads ws_dm_picked_crossings from session state
#   (written by the picker component), computes the actual z on the
#   frame at each picked crossing, drops any pick whose z is not
#   strictly above eave height, and draws a small marker at each
#   kept position.
#
#   No cones yet. Cones come in Piece 3d. Markers first, to prove
#   the geometry lookup end to end.
#
#   Owner-tier diagnostic lists the dropped picks and why.
#
# The frame, as agreed (Piece 1, verified):
#   - Ground footprint: circle (base case for now).
#   - One master frame shape (parabolic / circular / catenary).
#   - Frame A runs along Y, footed on the ground circle at (0, +/-R).
#   - Frame B runs along X, footed on the ground circle at (+/-R, 0).
#   - N frames parallel to A, spaced across X. Frame A is the middle.
#   - M frames parallel to B, spaced across Y. Frame B is the middle.
#   - Each frame is ONE full curve: ground -> apex -> ground.
#   - Apexes step down from the crown to the outer edge.
#   - SPACING RULE: outer pair sits at +/- R*(N-1)/N, strictly
#     inside the circle. "3" means exactly 3 real frames.
#
# The eave polygon:
#   - Each frame crosses z = eave_height twice (rising, falling).
#   - Those crossings are eave anchors.
#   - Anchors closer than 1% of dome diameter are deduped.
#   - Anchors sorted by angle around the origin.
#   - Consecutive anchors joined by straight segments.
#   - Closed loop. Drawn in green. No cosmetic bow.
#
# The picked crossing markers:
#   - Picks are read as a set of (i, j) tuples from session state.
#   - i is the Family A frame index, j is the Family B frame index.
#   - The actual 3D position of the crossing is looked up on the
#     frame curve at plan position (x_i, y_j).
#   - Picks whose z <= eave_height are silently dropped, with an
#     owner-tier diagnostic listing the drops.
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
EAVE_DEDUPE_TOL_FRAC = 0.01  # fraction of dome diameter

COL_FRAME_A = "#FF6B6B"
COL_FRAME_B = "#e07b39"
COL_EAVE = "#2ecc71"
COL_MARKER = "#f1c40f"


# =============================================================================
# SESSION STATE HELPER
# =============================================================================

def _get(key, default=None):
    return st.session_state.get("ws_dm_" + key, default)


# =============================================================================
# THE DOME PROFILE — determines the globe surface
# =============================================================================

def _dome_profile_height(r_frac, crown_height, curve_type):
    """
    Height of the dome surface at normalised radius r_frac in [0, 1].
    r_frac = 0 at crown, 1 at the ground circle.
    """
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
    """
    One frame in its own 2D plane (s, z). s from -half_chord to +half_chord.
    z rises from ground at both ends to apex_height at s = 0.
    """
    s = np.linspace(-half_chord, +half_chord, n_samples)
    r_frac = np.abs(s) / max(half_chord, 1e-9)
    z = np.array([
        _dome_profile_height(float(rf), apex_height, curve_type)
        for rf in r_frac
    ])
    return s, z


def _offsets(n, ground_radius):
    """
    Evenly spaced offsets for n frames along one axis.
    Outer pair sits at +/- R * (n-1)/n, strictly inside the circle.
    """
    if n < 1:
        n = 1
    if n == 1:
        return [0.0]
    half_extent = ground_radius * (n - 1.0) / n
    return list(np.linspace(-half_extent, +half_extent, n))


def _build_dome_frame(ground_radius, crown_height, curve_type, n_x, n_y):
    """
    Build the dome frame. Returns:
        frames   list of dicts, each with x, y, z arrays and metadata
        apexes   list of (x, y, z, apex_h, r_plan) tuples for verification
        offsets_x, offsets_y  lists of frame offsets for plan lookups
    """
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
# PICKED CROSSING LOOKUP
# =============================================================================

def _frame_z_at_plan_offset(offset, cross_axis_value, ground_radius,
                             crown_height, curve_type):
    """
    Given a frame whose ground offset is `offset` on one axis and
    `cross_axis_value` is the position ALONG the frame (i.e. the
    other axis), return the z of the frame at that position.

    For a Family A frame (runs along Y, offset on X):
        offset       = x
        cross_axis_value = y
    For a Family B frame (runs along X, offset on Y):
        offset       = y
        cross_axis_value = x

    Returns z (float) or None if the plan position is outside the frame's
    chord (i.e. the frame doesn't reach there).
    """
    chord_half = math.sqrt(max(0.0, ground_radius ** 2 - offset ** 2))
    if abs(cross_axis_value) > chord_half + 1e-9:
        return None
    r_plan = abs(offset)
    apex_h = _dome_profile_height(
        r_plan / ground_radius, crown_height, curve_type
    )
    # Along the frame, the profile depends on the normalised distance
    # from the apex. For a frame with chord_half width, the apex is at
    # cross_axis_value = 0, and the ends are at +/- chord_half.
    r_frac = abs(cross_axis_value) / max(chord_half, 1e-9)
    # r_frac in [0, 1] maps to the profile of the frame curve. But the
    # frame's apex_h is already the globe height at r_plan. The shape
    # along the frame is the same profile scaled so the apex is apex_h
    # and the ends are on the ground.
    # The frame's own curve: z(s) = profile_shape(r_frac) * apex_h, where
    # profile_shape uses the SAME curve_type. So we evaluate the profile
    # at r_frac with crown height apex_h.
    z = _dome_profile_height(r_frac, apex_h, curve_type)
    return float(z)


def _resolve_picked_crossings(picked_set, offsets_x, offsets_y,
                                ground_radius, crown_height, curve_type,
                                eave_height):
    """
    For each picked (i, j) crossing, compute its (x, y, z).
    Returns:
        kept     list of {i, j, x, y, z} for picks with z > eave_height
        dropped  list of {i, j, x, y, z, reason} for picks that were
                 dropped (z <= eave_height or z is None)
    """
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
        # Family A frame at x = xi runs along Y. Its z at (xi, yj)
        # is the frame's z at cross-axis position yj.
        za = _frame_z_at_plan_offset(
            xi, yj, ground_radius, crown_height, curve_type
        )
        # Family B frame at y = yj runs along X. Its z at (xi, yj)
        # is the frame's z at cross-axis position xi.
        zb = _frame_z_at_plan_offset(
            yj, xi, ground_radius, crown_height, curve_type
        )
        if za is None or zb is None:
            dropped.append({
                "i": i, "j": j, "x": xi, "y": yj, "z": None,
                "reason": "crossing outside frame chord",
            })
            continue
        # Both frames pass through the same point in plan; their z
        # values agree by construction. Use the average for numeric
        # safety.
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

    # ---- Build the eave polygon -----------------------------------------
    eave_polygon = _build_eave_polygon(
        frames, eave_height, ground_radius, dome_diameter
    )

    # ---- Resolve picks ---------------------------------------------------
    kept_picks, dropped_picks = _resolve_picked_crossings(
        picked_set, offsets_x, offsets_y,
        ground_radius, crown_height, curve_type, eave_height,
    )

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

    # Eave polygon — closed loop, straight segments
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

    # Picked crossing markers
    if len(kept_picks) > 0:
        mx = [p["x"] for p in kept_picks]
        my = [p["y"] for p in kept_picks]
        mz = [p["z"] for p in kept_picks]
        fig.add_trace(go.Scatter3d(
            x=mx, y=my, z=mz,
            mode="markers",
            marker=dict(color=COL_MARKER, size=7, symbol="circle"),
            name="picked crossings",
            showlegend=False, hoverinfo="skip",
        ))

    # ---- Verification expanders (owner tier only) ------------------------
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
            st.write(
                "Eave anchors at z = eave_height, deduped and sorted "
                "by angle around the origin. Straight segments. "
                "No bow — the bow comes later when the FDM solve "
                "puts real prestress on the cable."
            )
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
                "Picks are read from the picker. For each pick, the "
                "viewer looks up the actual z on the frame at that "
                "plan position. Picks with z **strictly above** eave "
                "height are kept. Everything else is dropped."
            )
            st.write(
                "**Total picks: %d. Kept: %d. Dropped: %d.**"
                % (len(picked_set), len(kept_picks), len(dropped_picks))
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

    return apply_common_layout(fig, crown_height)


# =============================================================================
# END OF viewers/figures/dome_multi_cone.py
# =============================================================================
