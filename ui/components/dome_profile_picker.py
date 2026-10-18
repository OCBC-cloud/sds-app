# =============================================================================
# SDSe - Dome Profile Picker
# =============================================================================
# A 2D elevation drawing board for the Dome Multi-Cone structure.
#
# The user shapes the dome frame curve with five control point sliders.
# A live preview curve draws on the plot. The curve is interpolated from
# the five Z-heights across the dome span.
#
# The five control points are:
#   P0 - Left base (at -span/2)
#   P1 - Left quarter
#   P2 - Apex (at 0)
#   P3 - Right quarter
#   P4 - Right base (at +span/2)
#
# The Z-heights are stored in session state under
#   ws_dm_custom_profile   (list of 5 floats, metres)
#
# The viewer (viewers/figures/dome_multi_cone.py) reads this array
# when curve_type == "custom" and interpolates it into the frame.
#
# This component does not build 3D geometry. It only collects the
# five control points and shows a live preview.
#
# History:
#   2026-10-18 - First version. 5-slider elevation drawer.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st


# =============================================================================
# CONSTANTS
# =============================================================================

COL_PREVIEW_CURVE = "#ffd166"     # gold, matches the ring colour
COL_PREVIEW_GRID = "#4a7a9c"      # blue, matches the membrane
COL_REFERENCE = "#a0a0a0"         # grey, for the parabola reference

PROFILE_KEY = "ws_dm_custom_profile"
_DEFAULT_PROFILE = [0.0, 6.75, 9.0, 6.75, 0.0]


# =============================================================================
# SESSION STATE HELPERS
# =============================================================================

def _get_profile():
    """Returns the current 5-point profile from session state, or the default."""
    profile = st.session_state.get(PROFILE_KEY, None)
    if profile is None or len(profile) != 5:
        profile = list(_DEFAULT_PROFILE)
        st.session_state[PROFILE_KEY] = profile
    return list(profile)


def _get_dome_inputs():
    """Read the two parameters the profile view needs."""
    diameter = float(st.session_state.get("ws_dm_dome_diameter", 18.0))
    crown = float(st.session_state.get("ws_dm_crown_height", 9.0))
    return diameter, crown


# =============================================================================
# PREVIEW PLOT
# =============================================================================

def _build_preview_figure(profile, diameter, crown):
    """
    Builds the 2D preview figure.
    
    The plot shows:
      - X axis: -diameter/2 to +diameter/2 (the span)
      - Y axis: 0 to crown (the height)
      - The current curve (from the 5 control points, interpolated)
      - The reference parabola (faint, for comparison)
      - The 5 control points (as markers)
    """
    span = max(diameter, 1.0)
    h_max = max(crown, 1.0)

    # X of the 5 control points: -span/2, -span/4, 0, +span/4, +span/2
    xs = np.array([-span / 2.0, -span / 4.0, 0.0, +span / 4.0, +span / 2.0])
    zs = np.array(profile, dtype=float)

    # Interpolate to 100 points for a smooth preview curve.
    # Use np.interp for linear, or a light smoothing. Linear is honest:
    # the user sees exactly the shape the engine will build.
    x_dense = np.linspace(-span / 2.0, +span / 2.0, 100)
    z_dense = np.interp(x_dense, xs, zs)

    # Reference parabola (crown * (1 - (x/half_span)^2))
    r_frac = np.abs(x_dense) / max(span / 2.0, 1e-9)
    z_ref = crown * (1.0 - r_frac ** 2)

    fig = go.Figure()

    # Reference parabola (faint)
    fig.add_trace(go.Scatter(
        x=x_dense,
        y=z_ref,
        mode="lines",
        line=dict(color=COL_REFERENCE, width=2, dash="dot"),
        name="Parabolic reference",
        hovertemplate="x: %{x:.2f}<br>z: %{y:.2f}<extra></extra>",
    ))

    # Current custom curve
    fig.add_trace(go.Scatter(
        x=x_dense,
        y=z_dense,
        mode="lines",
        line=dict(color=COL_PREVIEW_CURVE, width=4),
        name="Custom curve",
        hovertemplate="x: %{x:.2f}<br>z: %{y:.2f}<extra></extra>",
    ))

    # Control points
    fig.add_trace(go.Scatter(
        x=xs,
        y=zs,
        mode="markers",
        marker=dict(color=COL_PREVIEW_CURVE, size=10, symbol="circle"),
        name="Control points",
        hovertemplate=(
            "x: %{x:.2f}<br>z: %{y:.2f}<extra></extra>"
        ),
    ))

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=260,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#ffffff", size=12),
        xaxis=dict(
            title=dict(text="Span (m)", font=dict(color="#ffffff")),
            gridcolor="rgba(255,255,255,0.1)",
            zerolinecolor="rgba(255,255,255,0.2)",
            tickfont=dict(color="#ffffff"),
        ),
        yaxis=dict(
            title=dict(text="Height (m)", font=dict(color="#ffffff")),
            gridcolor="rgba(255,255,255,0.1)",
            zerolinecolor="rgba(255,255,255,0.2)",
            tickfont=dict(color="#ffffff"),
            range=[0, h_max * 1.1],
        ),
        showlegend=False,
    )

    return fig


# =============================================================================
# SLIDERS
# =============================================================================

def _render_sliders(profile, crown):
    """
    Renders 5 sliders, one per control point.
    Returns the updated profile.
    """
    z_max = max(crown, 1.0)

    st.caption(
        "Adjust each control point. The curve redraws live. "
        "The 3D board uses this curve when you switch to the 3D View."
    )

    labels = [
        "Left base height (m)",
        "Left quarter height (m)",
        "Apex height (m)",
        "Right quarter height (m)",
        "Right base height (m)",
    ]

    new_profile = []
    for i, (lbl, val) in enumerate(zip(labels, profile)):
        # Read the value from the widget using a session key.
        widget_key = f"ws_dm_profile_slider_{i}"
        if widget_key not in st.session_state:
            st.session_state[widget_key] = float(val)

        v = st.slider(
            label=lbl,
            min_value=0.0,
            max_value=float(z_max * 1.2),
            value=float(st.session_state[widget_key]),
            step=0.05,
            key=widget_key,
        )
        new_profile.append(float(v))

    return new_profile


# =============================================================================
# PUBLIC RENDERER
# =============================================================================

def render_dome_profile_picker():
    """
    Render the Dome Multi-Cone Profile Picker board.

    Reads:
        ws_dm_dome_diameter
        ws_dm_crown_height
        ws_dm_custom_profile

    Writes:
        ws_dm_custom_profile (5 floats)
    """
    diameter, crown = _get_dome_inputs()
    profile = _get_profile()

    st.markdown(
        "<p style='color:#a8b8c8;margin-top:0;'>"
        "Draw the dome elevation curve. Five control points. "
        "The 3D board rebuilds the frame from this curve."
        "</p>",
        unsafe_allow_html=True,
    )

    # --- The preview plot ---
    fig = _build_preview_figure(profile, diameter, crown)
    st.plotly_chart(
        fig,
        use_container_width=True,
        key="ws_dm_profile_preview",
        config={"displayModeBar": False},
    )

    # --- The 5 sliders ---
    new_profile = _render_sliders(profile, crown)

    # --- Commit to session state if changed ---
    changed = any(
        abs(float(new_profile[i]) - float(profile[i])) > 1e-9
        for i in range(5)
    )
    if changed:
        st.session_state[PROFILE_KEY] = new_profile
        # Do NOT call st.rerun() here. The next natural rerender
        # (triggered by the slider release) will pick up the new
        # value and the preview will redraw.

    # --- Reset button ---
    st.markdown("---")
    if st.button("Reset to Parabolic", use_container_width=True):
        st.session_state[PROFILE_KEY] = list(_DEFAULT_PROFILE)
        for i in range(5):
            widget_key = f"ws_dm_profile_slider_{i}"
            st.session_state[widget_key] = float(_DEFAULT_PROFILE[i])
        st.rerun()


# =============================================================================
# END OF ui/components/dome_profile_picker.py
# =============================================================================
