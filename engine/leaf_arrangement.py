# =============================================================================
# SDSe Engine - Leaf Arrangement
# =============================================================================
# System B of the Five Systems architecture.
#
# Places N leaves in a helical arrangement along a vertical zone,
# with collision avoidance and optional tapering.
#
# DESIGN PRINCIPLE:
#   This engine is a PURE STATELESS FUNCTION. It has no memory, no UI,
#   no session state. It receives a set of parameters and returns a
#   set of placements. Same inputs -> same outputs.
#
# Units:
#   Length: m
#   Angle: degrees (inputs), radians (internal)
# =============================================================================

import math


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_BUD_FIXED_OFFSET = 0.45
DEFAULT_SILHOUETTE_OVERLAP = 0.125
DEFAULT_TAPER_RATIO = 0.88
GOLDEN_ANGLE_DEG = 137.507764
MIN_LEAF_ZONE_RATIO = 0.05
MAX_TURNS = 6.0


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def place_leaves(
    first_leaf_height,
    leaf_zone_height,
    num_leaves,
    column_radius,
    leaf_angular_width,
    scale_mode="taper_up",
    taper_ratio=DEFAULT_TAPER_RATIO,
    bud_fixed_offset=DEFAULT_BUD_FIXED_OFFSET,
    silhouette_overlap_max=DEFAULT_SILHOUETTE_OVERLAP,
):
    """
    Place N leaves in a helical arrangement along a vertical zone.

    Returns
    -------
    result : dict
        {
          "buds": [
              {
                "index": int,
                "axis_attach": (x, y, z),
                "bud_tip": (x, y, z),
                "bud_length": float,
                "yaw_deg": float,
                "scale": float,
                "z_attach": float,
              },
              ...
          ],
          "meta": {
              "first_leaf_height": float,
              "leaf_zone_height": float,
              "num_leaves": int,
              "column_radius": float,
              "bud_length": float,
              "total_turns": float,
              "vertical_spacing": float,
              "angle_step_deg": float,
              "scale_mode": str,
              "taper_ratio": float,
              "warnings": [str, ...],
          },
        }
    """
    warnings = []

    # ---- Input validation -------------------------------------------------
    if num_leaves < 1:
        warnings.append("num_leaves must be >= 1; forced to 1.")
        num_leaves = 1

    if leaf_zone_height <= 0:
        warnings.append("leaf_zone_height must be > 0; forced to 0.5m.")
        leaf_zone_height = 0.5

    if column_radius <= 0:
        warnings.append("column_radius must be > 0; forced to 0.05m.")
        column_radius = 0.05

    if leaf_angular_width <= 0 or leaf_angular_width >= 360:
        warnings.append("leaf_angular_width must be in (0, 360); forced to 45.")
        leaf_angular_width = 45.0

    if taper_ratio <= 0 or taper_ratio > 1:
        warnings.append("taper_ratio must be in (0, 1]; forced to 0.88.")
        taper_ratio = DEFAULT_TAPER_RATIO

    # ---- Bud joint length -------------------------------------------------
    bud_length = column_radius + bud_fixed_offset

    # ---- Helix turns ------------------------------------------------------
    effective_step = leaf_angular_width * (1.0 - silhouette_overlap_max)
    if effective_step < 1.0:
        effective_step = 1.0

    leaves_per_turn = 360.0 / effective_step
    total_turns = num_leaves / leaves_per_turn

    if total_turns > MAX_TURNS:
        warnings.append(
            "Requested {0} leaves would require {1:.2f} turns; capped at {2}.".format(
                num_leaves, total_turns, MAX_TURNS
            )
        )
        total_turns = MAX_TURNS

    # ---- Vertical spacing -------------------------------------------------
    if num_leaves > 1:
        vertical_spacing = leaf_zone_height / (num_leaves - 1)
    else:
        vertical_spacing = 0.0

    # ---- Angular step -----------------------------------------------------
    if num_leaves > 1:
        total_sweep_deg = total_turns * 360.0
        angle_step = total_sweep_deg / (num_leaves - 1)
    else:
        angle_step = 0.0

    # ---- Build bud placements ---------------------------------------------
    buds = []
    for i in range(num_leaves):
        z_attach = first_leaf_height + (i * vertical_spacing)
        yaw_deg = i * angle_step
        yaw_rad = math.radians(yaw_deg)

        axis_attach = (0.0, 0.0, z_attach)
        bud_tip = (
            bud_length * math.cos(yaw_rad),
            bud_length * math.sin(yaw_rad),
            z_attach,
        )

        if scale_mode == "taper_up":
            scale = taper_ratio ** i
        elif scale_mode == "taper_down":
            scale = taper_ratio ** (num_leaves - 1 - i)
        else:
            scale = 1.0

        buds.append({
            "index": i,
            "axis_attach": axis_attach,
            "bud_tip": bud_tip,
            "bud_length": bud_length,
            "yaw_deg": yaw_deg,
            "scale": scale,
            "z_attach": z_attach,
        })

    return {
        "buds": buds,
        "meta": {
            "first_leaf_height": first_leaf_height,
            "leaf_zone_height": leaf_zone_height,
            "num_leaves": num_leaves,
            "column_radius": column_radius,
            "bud_length": bud_length,
            "total_turns": total_turns,
            "vertical_spacing": vertical_spacing,
            "angle_step_deg": angle_step,
            "scale_mode": scale_mode,
            "taper_ratio": taper_ratio,
            "warnings": warnings,
        },
    }
