# =============================================================================
# SDSe - Dome Multi-Cone Viewer
# =============================================================================
# Builds the 3D figure for the Dome Multi-Cone variant.
#
# Reads all inputs from session state under the "ws_dm_" prefix.
#
# PIECE 2 — FRAME + EAVE POLYGON.
#   Builds on Piece 1.
#   Adds the eave polygon: each frame's crossings at z = eave_height,
#   deduped, sorted by angle around the origin, joined with straight
#   segments. Drawn in green.
#   No bow is drawn. The bow comes later, when the FDM solve puts
#   real prestress on the cable.
#
# The frame, as agreed (Piece 1, verified):
#   - Ground footprint: circle (base case for now).
#   - One master frame shape (parabolic / circular / catenary).
#   - Frame A runs along Y, footed on the ground circle at (0, +/-R).
#   - Frame B runs along X, footed on the ground circle at (+/-R, 0).
#   - N frames parallel to A, spaced across X. Frame A is the middle.
#   - M frames parallel to B, spaced across Y. Frame B is the middle.
#   - Each frame is ONE full curve: ground -> apex -> ground.
#   - Apexes step down from the crown to the ground circle, so the
#     set traces a smooth globe. Verified numerically.
#
# The eave polygon, as agreed (Piece 2):
#   - Each frame crosses z = eave_height twice (rising, falling).
#   - Those crossings are eave anchors: points ON the beam, not
#     frame-to-frame crossings.
#   - Anchors closer than 1% of dome diameter are deduped.
#   - Anchors sorted by angle around the origin (circle ground case).
#   - Consecutive anchors joined by straight segments.
#   - Closed loop. Drawn in green. No cosmetic bow.
#
# Signature matches the FIGURE_REGISTRY contract:
#   - no arguments
#   - returns a plotly.graph_objects.Figure
#
# History:
#   2026-10-14 - Piece 1. Frame only.
#   2026-10-14 - Piece 2. Add eave polygon.
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
COL_GROUND = "#2ecc71"
COL_EAVE = "#2ecc71"  # same green family; ground circle drawn faint


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


def _build_dome_frame(ground_radius, crown_height, curve_type,
                      n_x, n_y, eave_height):
    """
    Build the dome frame. Returns frames + apex verification rows.
    Same as Piece 1.
    """
    frames = []
    apexes = []

    def _offsets(n):
        if n < 1:
            n = 1
        if n == 1:
            return [0.0]
        return list(np.linspace(-ground_radius, +ground_radius, n))

    offsets_x = _offsets(n_x)
    offsets_y = _offsets(n_y)

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
            "r_plan": r_plan,
            "apex_h": apex_h,
        })
        apexes.append((0.0, offset, apex_h, apex_h, r_plan))

    return frames, apexes


# =============================================================================
# EAVE ANCHORS AND POLYGON
# =============================================================================

def _frame_crossings_at_eave(frame, eave_height):
    """
    Return the (x, y, z) points where this frame's z crosses eave_height.
    At most two: one on the rising side, one on the falling side.
    Skipped if the frame never reaches eave_height (i.e. its apex
    is below the eave).
    """
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
    """
    Remove points that are within tol (plan distance) of an earlier point.
    Keeps the first of each group.
    """
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
    """
    Sort points around the origin by atan2(y, x).
    Returns the ordered list.
    """
    def _angle(p):
        return math.atan2(p[1], p[0])
    return sorted(points, key=_angle)


def _build_eave_polygon(frames, eave_height, ground_radius, dome_diameter):
    """
    Collect all eave anchors from all frames, dedupe, sort by angle,
    return ordered list of anchor points (closed loop).
    """
    all_anchors = []
    for f in frames:
        pts = _frame_crossings_at_eave(f, eave_height)
        all_anchors.extend(pts)

    tol = EAVE_DEDUPE_TOL_FRAC * dome_diameter
    deduped = _dedupe_plan(all_anchors, tol)
    ordered = _order_by_angle(deduped)
    return ordered


# =============================================================================
# FRAME VERIFICATION (Piece 1)
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

    # ---- Build the frame -------------------------------------------------
    frames, apexes = _build_dome_frame(
        ground_radius=ground_radius,
        crown_height=crown_height,
        curve_type=curve_type,
        n_x=n_x,
        n_y=n_y,
        eave_height=eave_height,
    )

    # ---- Build the eave polygon -----------------------------------------
    eave_polygon = _build_eave_polygon(
        frames, eave_height, ground_radius, dome_diameter
    )

    # ---- Draw ------------------------------------------------------------
    fig = go.Figure()

    # Ground circle (faint — it's the footing line, will be removed
    # in a later piece once cones and picker are in)
    t = np.linspace(0.0, 2.0 * math.pi, 200)
    fig.add_trace(go.Scatter3d(
        x=ground_radius * np.cos(t),
        y=ground_radius * np.sin(t),
        z=np.zeros_like(t),
        mode="lines",
        line=dict(color=COL_GROUND, width=2, dash="dot"),
        name="ground circle", showlegend=False, hoverinfo="skip",
    ))

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

    return apply_common_layout(fig, crown_height)


# =============================================================================
# END OF viewers/figures/dome_multi_cone.py
# =============================================================================
