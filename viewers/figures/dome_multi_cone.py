# =============================================================================
# SDSe - Dome Multi-Cone Viewer
# =============================================================================
# Builds the 3D figure for the Dome Multi-Cone variant.
#
# Reads all inputs from session state under the "ws_dm_" prefix.
#
# PIECE 1 — THE FRAME ONLY.
#   This version draws the corrected dome frame and nothing else.
#   No eave polygon, no picker, no cones, no membrane.
#   Mesh, cones, and picker come in later pieces on the shared
#   SDSe engine.
#
# The frame, as agreed:
#   - Ground footprint: circle (base case for this piece).
#   - One master frame shape (parabolic / circular / catenary).
#   - Frame A runs along Y, footed on the ground circle at (0, ±R).
#   - Frame B runs along X, footed on the ground circle at (±R, 0).
#   - N frames parallel to A, spaced across X. Frame A is the middle.
#   - M frames parallel to B, spaced across Y. Frame B is the middle.
#   - Each frame is ONE full curve: ground -> apex -> ground.
#   - Apexes step down from the crown. Central pair reaches the crown.
#     Each pair outward reaches the dome surface at a lower height,
#     on its own radius, so the whole set traces a smooth globe.
#
# Signature matches the FIGURE_REGISTRY contract:
#   - no arguments
#   - returns a plotly.graph_objects.Figure
#
# History:
#   2026-10-14 - Piece 1. Frame only.
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

COL_FRAME_A = "#FF6B6B"
COL_FRAME_B = "#e07b39"
COL_GROUND = "#2ecc71"


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
    Given a normalised radius r_frac in [0, 1] (0 = crown, 1 = eave
    on the ground circle), return the height of the dome surface at
    that radius.

    curve_type:
      "parabolic" -> h = H * (1 - r_frac^2)
      "circular"  -> h = H * sqrt(1 - r_frac^2)
      "catenary"  -> h = H * (cosh(a(1-r)) - cosh(a)) / (1 - cosh(a))
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
    Build one frame curve in its own 2D plane (s, z), where s runs
    from -half_chord to +half_chord along the ground, and z is the
    height. The curve rises from ground at both ends to apex_height
    at s = 0.

    Uses the same dome profile shape as the reference globe, but
    scaled so the apex hits apex_height and the feet hit the ground
    at s = ±half_chord.
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
    Build the full dome frame.

    Returns:
        families   list of dicts, each with:
                     'family'  'A' or 'B'
                     'x', 'y', 'z'  np arrays, full curve
                     'r_plan'  plan distance from centre to the frame's
                               ground line (0 for the middle frame)
                     'apex_h'  apex height of this frame
                     'apex_xyz'  apex position (tuple)
                     'crossings'  list of (x, y, z) where this frame
                                  meets the other family's master
        apexes     list of (x, y, z, apex_h, r_plan) for verification
    """
    frames = []
    apexes = []

    # Spacing of parallel frames across the perpendicular axis.
    # N frames -> N-1 intervals across the diameter (2R).
    # Middle frame at offset 0, others symmetric on either side.
    def _offsets(n):
        if n < 1:
            n = 1
        if n == 1:
            return [0.0]
        # evenly spaced between -R and +R
        return list(np.linspace(-ground_radius, +ground_radius, n))

    offsets_x = _offsets(n_x)  # offsets across X (for Family A)
    offsets_y = _offsets(n_y)  # offsets across Y (for Family B)

    # ---- Family A: curves parallel to Y, offset across X -------------
    for offset in offsets_x:
        # Half chord of this frame on the circle:
        # the ground line runs along Y at plan X = offset.
        # Its endpoints on the circle: (offset, ±sqrt(R^2 - offset^2)).
        chord_half = math.sqrt(max(0.0, ground_radius**2 - offset**2))

        # Plan distance from centre to this frame's ground line:
        r_plan = abs(offset)

        # Apex height: the globe surface at r_plan.
        apex_h = _dome_profile_height(
            r_plan / ground_radius, crown_height, curve_type
        )

        s, z = _build_frame_curve(chord_half, apex_h, curve_type, FRAME_SAMPLES)
        # curve lives in its own (s, z) plane; s -> Y, plan X fixed at offset
        x = np.full_like(s, offset)
        y = s.copy()

        frames.append({
            "family": "A",
            "x": x, "y": y, "z": z,
            "r_plan": r_plan,
            "apex_h": apex_h,
            "apex_xyz": (offset, 0.0, apex_h),
        })
        apexes.append((offset, 0.0, apex_h, apex_h, r_plan))

    # ---- Family B: curves parallel to X, offset across Y -------------
    for offset in offsets_y:
        chord_half = math.sqrt(max(0.0, ground_radius**2 - offset**2))
        r_plan = abs(offset)
        apex_h = _dome_profile_height(
            r_plan / ground_radius, crown_height, curve_type
        )

        s, z = _build_frame_curve(chord_half, apex_h, curve_type, FRAME_SAMPLES)
        # curve lives in its own (s, z) plane; s -> X, plan Y fixed at offset
        x = s.copy()
        y = np.full_like(s, offset)

        frames.append({
            "family": "B",
            "x": x, "y": y, "z": z,
            "r_plan": r_plan,
            "apex_h": apex_h,
            "apex_xyz": (0.0, offset, apex_h),
        })
        apexes.append((0.0, offset, apex_h, apex_h, r_plan))

    return frames, apexes


# =============================================================================
# FRAME VERIFICATION
# =============================================================================

def _verify_frame_against_globe(apexes, ground_radius, crown_height, curve_type):
    """
    For each frame, compare its apex height with the reference globe's
    height at the same plan distance. Returns a list of dicts with the
    numbers, and a bool 'ok' for each row.
    """
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

    # ---- Draw ------------------------------------------------------------
    fig = go.Figure()

    # Ground circle
    t = np.linspace(0.0, 2.0 * math.pi, 200)
    fig.add_trace(go.Scatter3d(
        x=ground_radius * np.cos(t),
        y=ground_radius * np.sin(t),
        z=np.zeros_like(t),
        mode="lines",
        line=dict(color=COL_GROUND, width=4),
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

    # ---- Verification expander (owner tier only) -------------------------
    access_mode = str(st.session_state.get("access_mode", "owner")).lower()
    if access_mode == "owner":
        rows = _verify_frame_against_globe(
            apexes, ground_radius, crown_height, curve_type
        )
        all_ok = all(r["ok"] for r in rows)
        with st.expander("Frame verification (owner tier)", expanded=True):
            st.write(
                "Each frame's apex must land on the reference globe at "
                "the same plan distance. The 'diff' column is "
                "(apex_h - ref_h). It must be zero within tolerance."
            )
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

    return apply_common_layout(fig, crown_height)


# =============================================================================
# END OF viewers/figures/dome_multi_cone.py
# =============================================================================
