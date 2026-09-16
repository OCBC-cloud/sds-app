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
#   The caller (UI) decides:
#       - where the leaf zone starts (first_leaf_height)
#       - how tall the leaf zone is (leaf_zone_height)
#       - how many leaves
#       - what scale mode
#       - etc.
#
#   The engine decides:
#       - how many helix turns
#       - how to space leaves vertically
#       - angular positions
#       - collision avoidance
#       - bud joint lengths
#
# DENSITY:
#   There is no explicit "density" parameter. Density is implied by
#   the ratio of leaves to leaf_zone_height. A user who wants dense
#   stacking sets a short zone with many leaves. A user who wants
#   loose stacking sets a tall zone with few leaves.
#
# Units:
#   Length: m
#   Angle: degrees (inputs), radians (internal)
# =============================================================================

import math


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_BUD_FIXED_OFFSET = 0.45        # m - the +450mm standard
DEFAULT_SILHOUETTE_OVERLAP = 0.125     # 1/8 overlap maximum
DEFAULT_TAPER_RATIO = 0.88             # 12% reduction per leaf in taper mode
GOLDEN_ANGLE_DEG = 137.507764          # natural phyllotaxis angle
MIN_LEAF_ZONE_RATIO = 0.05             # minimum fraction of zone actually used
MAX_TURNS = 6.0                        # cap to avoid absurd geometry


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

    Parameters
    ----------
    first_leaf_height : float
        Height (m) of the first leaf's bud tip, measured from ground.
    leaf_zone_height : float
        Vertical height (m) of the zone that contains all leaves.
    num_leaves : int
        Number of leaves to place. Must be >= 1.
    column_radius : float
        Radius (m) of the column. Used for bud joint length = radius + 450mm.
    leaf_angular_width : float
        Angular width (degrees) of the mother leaf in plan view.
        Used for collision avoidance.
    scale_mode : str
        "full_scale"  - every leaf same size
        "taper_up"    - each leaf smaller than the one below (natural tree)
        "taper_down"  - each leaf larger than the one below (inverted)
    taper_ratio : float
        Scale multiplier between consecutive leaves. Only used when
        scale_mode is "taper_up" or "taper_down". Must be in (0, 1].
    bud_fixed_offset : float
        Fixed offset (m) added to column radius to get bud length.
        Default 0.45 (the +450mm standard).
    silhouette_overlap_max : float
        Maximum allowed angular overlap between adjacent leaves,
        as a fraction of leaf_angular_width. Default 0.125 (1/8).

    Returns
    -------
    result : dict
        {
          "buds": [
              {
                "index": int,
                "axis_attach": (x, y, z),   # where bud meets column axis
                "bud_tip": (x, y, z),       # where leaf attaches
                "bud_length": float,        # = column_radius + bud_fixed_offset
                "yaw_deg": float,           # leaf rotation around Z
                "scale": float,             # leaf size multiplier
              },
              ...
          ],
          "meta": {
              "first_leaf_height": float,
              "leaf_zone_height": float,
              "num_leaves": int,
              "total_turns": float,
              "vertical_spacing": float,
              "bud_length": float,
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

    # ---- Bud joint length (radius + fixed offset) -------------------------
    bud_length = column_radius + bud_fixed_offset

    # ---- Helix turns ------------------------------------------------------
    # The leaf's angular width in plan determines how many leaves fit
    # per turn without overlapping more than silhouette_overlap_max.
    #
    # Effective angular width per leaf = leaf_angular_width * (1 - overlap_max)
    effective_step = leaf_angular_width * (1.0 - silhouette_overlap_max)
    if effective_step < 1.0:
        effective_step = 1.0  # prevent divide-by-near-zero

    leaves_per_turn = 360.0 / effective_step
    total_turns = num_leaves / leaves_per_turn

    if total_turns > MAX_TURNS:
        warnings.append(
            "Requested {} leaves would require {:.2f} turns; capped at {}.".format(
                num_leaves, total_turns, MAX_TURNS
            )
        )
        total_turns = MAX_TURNS

    # ---- Vertical spacing -------------------------------------------------
    # Distribute leaves across the leaf zone. First leaf at bottom of zone,
    # last leaf at top. If only 1 leaf, it sits at the bottom.
    if num_leaves > 1:
        vertical_spacing = leaf_zone_height / (num_leaves - 1)
    else:
        vertical_spacing = 0.0

    # ---- Angular step -----------------------------------------------------
    # Total angular sweep = total_turns * 360 degrees.
    # Angular step between consecutive leaves = sweep / (num_leaves - 1).
    if num_leaves > 1:
        total_sweep_deg = total_turns * 360.0
        angle_step = total_sweep_deg / (num_leaves - 1)
    else:
        angle_step = 0.0

    # ---- Build bud placements --------------------------------------------
    buds = []
    for i in range(num_leaves):
        # Vertical position: from first_leaf_height up to end of zone
        z_attach = first_leaf_height + (i * vertical_spacing)

        # Angular position: from 0, sweeping around the column
        yaw_deg = i * angle_step
        yaw_rad = math.radians(yaw_deg)

        # Bud tip position: on the column axis at z_attach
        # The bud itself extends radially outward by bud_length
        # at the leaf's yaw angle.
        axis_attach = (0.0, 0.0, z_attach)
        bud_tip = (
            bud_length * math.cos(yaw_rad),
            bud_length * math.sin(yaw_rad),
            z_attach,
        )

        # Scale factor based on taper mode
        if scale_mode == "taper_up":
            scale = taper_ratio ** i
        elif scale_mode == "taper_down":
            scale = taper_ratio ** (num_leaves - 1 - i)
        else:  # "full_scale"
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

    # ---- Assemble result --------------------------------------------------
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


# =============================================================================
# SELF-TEST
# =============================================================================

def _verify_leaf_arrangement():
    """Basic sanity checks on the placement engine."""
    results = {}

    # Test 1: single leaf
    r = place_leaves(
        first_leaf_height=3.0,
        leaf_zone_height=7.0,
        num_leaves=1,
        column_radius=0.15,
        leaf_angular_width=45.0,
    )
    results["single_leaf_count"] = len(r["buds"])
    results["single_leaf_ok"] = len(r["buds"]) == 1
    results["single_leaf_z"] = r["buds"][0]["z_attach"]
    results["single_leaf_z_ok"] = abs(r["buds"][0]["z_attach"] - 3.0) < 1e-9

    # Test 2: bud length = radius + 450mm
    r2 = place_leaves(
        first_leaf_height=3.0, leaf_zone_height=7.0, num_leaves=4,
        column_radius=0.20, leaf_angular_width=45.0,
    )
    results["bud_length"] = r2["meta"]["bud_length"]
    results["bud_length_ok"] = abs(r2["meta"]["bud_length"] - 0.65) < 1e-9

    # Test 3: vertical spacing
    r3 = place_leaves(
        first_leaf_height=3.0, leaf_zone_height=6.0, num_leaves=4,
        column_radius=0.15, leaf_angular_width=45.0,
    )
    results["vertical_spacing"] = r3["meta"]["vertical_spacing"]
    results["vertical_spacing_ok"] = abs(r3["meta"]["vertical_spacing"] - 2.0) < 1e-9
    results["last_leaf_z"] = r3["buds"][-1]["z_attach"]
    results["last_leaf_z_ok"] = abs(r3["buds"][-1]["z_attach"] - 9.0) < 1e-9

    # Test 4: taper_up scale
    r4 = place_leaves(
        first_leaf_height=3.0, leaf_zone_height=6.0, num_leaves=3,
        column_radius=0.15, leaf_angular_width=45.0,
        scale_mode="taper_up", taper_ratio=0.5,
    )
    scales = [b["scale"] for b in r4["buds"]]
    results["taper_up_scales"] = scales
    results["taper_up_ok"] = (
        abs(scales[0] - 1.0) < 1e-9
        and abs(scales[1] - 0.5) < 1e-9
        and abs(scales[2] - 0.25) < 1e-9
    )

    # Test 5: taper_down reverses
    r5 = place_leaves(
        first_leaf_height=3.0, leaf_zone_height=6.0, num_leaves=3,
        column_radius=0.15, leaf_angular_width=45.0,
        scale_mode="taper_down", taper_ratio=0.5,
    )
    scales5 = [b["scale"] for b in r5["buds"]]
    results["taper_down_ok"] = (
        abs(scales5[0] - 0.25) < 1e-9
        and abs(scales5[1] - 0.5) < 1e-9
        and abs(scales5[2] - 1.0) < 1e-9
    )

    # Test 6: bud tips lie on a circle of radius bud_length
    for b in r3["buds"]:
        x, y, z = b["bud_tip"]
        r_xy = math.sqrt(x * x + y * y)
        if abs(r_xy - r3["meta"]["bud_length"]) > 1e-9:
            results["bud_tip_radius_ok"] = False
            break
    else:
        results["bud_tip_radius_ok"] = True

    # Overall
    results["pass"] = all([
        results["single_leaf_ok"],
        results["single_leaf_z_ok"],
        results["bud_length_ok"],
        results["vertical_spacing_ok"],
        results["last_leaf_z_ok"],
        results["taper_up_ok"],
        results["taper_down_ok"],
        results["bud_tip_radius_ok"],
    ])
    return results


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("engine/leaf_arrangement.py - tiered helix placement engine")
    print("-" * 70)
    res = _verify_leaf_arrangement()
    for k, v in res.items():
        print("{:24s}: {}".format(k, v))
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")
