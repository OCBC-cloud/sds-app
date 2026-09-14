# =============================================================================
# SDSe - Shared Figure Helpers
# =============================================================================
# Common geometry helpers used by all figure builders.
# Imported by individual variant files under viewers/figures/.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go


# =============================================================================
# LAYOUT
# =============================================================================

def apply_common_layout(fig, rise_ref):
    """Apply shared Plotly layout to any figure."""
    z_max = max(10, rise_ref * 1.5)

    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            xaxis=dict(color="#b0c4de", gridcolor="#1a2a3a"),
            yaxis=dict(color="#b0c4de", gridcolor="#1a2a3a"),
            zaxis=dict(color="#b0c4de", gridcolor="#1a2a3a", range=[-2, z_max]),
            bgcolor="#0a0e17",
            aspectmode="data",
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
        ),
        paper_bgcolor="#0a0e17",
        margin=dict(l=0, r=0, b=0, t=0),
        height=600,
        legend=dict(
            font=dict(color="#ffffff", size=8),
            orientation="h",
            yanchor="bottom",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(10,14,23,0.7)",
            bordercolor="#2a3a4f",
            borderwidth=1,
        ),
    )
    return fig


# =============================================================================
# BEAM CURVE
# =============================================================================

def beam_curve(x, span, rise, curve_type):
    """Return z values along the beam for the given curve type."""
    if span <= 0:
        return np.zeros_like(x)
    x_norm = 2.0 * x / span
    if curve_type == "parabolic":
        return rise * (1.0 - x_norm ** 2)
    elif curve_type == "circular":
        R = (span ** 2 + 4 * rise ** 2) / (8 * rise) if rise > 0 else span / 2
        if R > 0:
            return rise - (R - np.sqrt(np.maximum(0, R ** 2 - x ** 2)))
        return rise * (1.0 - x_norm ** 2)
    elif curve_type == "catenary":
        if rise <= 0:
            return rise * (1.0 - x_norm ** 2)
        try:
            a = span / (2.0 * math.asinh(rise / (span / 2.0))) if rise > 0 else 1.0
            if a > 0:
                return rise * (1.0 - (np.cosh(x / a) - 1.0) / (np.cosh(span / (2.0 * a)) - 1.0))
            return rise * (1.0 - x_norm ** 2)
        except Exception:
            return rise * (1.0 - x_norm ** 2)
    return rise * (1.0 - x_norm ** 2)


# =============================================================================
# ARC LENGTH
# =============================================================================

def arclength_parametrisation(x, z):
    """
    Given arrays of x and z points along a curve, return:
      - s: cumulative arc length from the start
      - total: total arc length
    Used to find a point at a given arc-length fraction.
    """
    dx = np.diff(x)
    dz = np.diff(z)
    seg = np.sqrt(dx * dx + dz * dz)
    s = np.concatenate(([0.0], np.cumsum(seg)))
    total = s[-1] if len(s) > 0 else 0.0
    return s, total


def find_index_at_arclength_fraction(s, total, fraction):
    """Return the index of the point closest to arc-length fraction * total."""
    if total <= 0:
        return 0
    target = fraction * total
    idx = int(np.argmin(np.abs(s - target)))
    return idx
