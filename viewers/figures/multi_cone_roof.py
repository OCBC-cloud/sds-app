# =============================================================================
# SDSe - Dome Multi-Cone Viewer
# =============================================================================
# Builds the 3D figure for the Dome Multi-Cone variant.
#
# Reads all inputs from session state under the "ws_dm_" prefix.
#
# PIECE 5b — NFDM SOLVE, FORK A.
#   The membrane, the perimeter cable, the drop members, and the ring
#   chains are all coupled in one nonlinear equilibrium solve.
#
#   Fork A model (agreed with the Chief):
#     Held:   eave anchors, ring polygon nodes, ring centres,
#             attachment points (the picks).
#     Free:   every membrane interior node, every perimeter subdivision
#             node, every drop member node, every ring chain node.
#     Cables: perimeter chain along the eave (anchor to anchor),
#             one drop per cone (pick to ring centre),
#             one ring chain per cone (around the ring polygon).
#     Loads:  zero for now. No gravity, no wind, no snow yet.
#
#   Approximations accepted in Fork A:
#     - Frame treated as rigid. Eave anchors held.
#     - Rings modelled as cable chains. Bending not modelled.
#   These are flagged as approximations to be corrected when the
#   engine gains beam elements (Fork B).
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
#   2026-10-14 - Piece 3d fix. Ring orientation is now horizontal.
#   2026-10-14 - Piece 4. Support midpoint picks from the new picker.
#   2026-10-14 - Piece 5a. Membrane geometry from SDSe_mesh_rings.
#   2026-10-14 - Piece 5b. NFDM solve. Fork A coupling.
# =============================================================================

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.SDSe_mesh_builder import SDSe_mesh_rings
from engine.nonlinear_equilibrium import (
    solve_nonlinear_equilibrium,
    make_membrane_material,
)
from viewers.figures._shared import apply_common_layout


# =============================================================================
# COLOURS AND CONSTANTS
# =============================================================================

FRAME_SAMPLES = 200
EAVE_DEDUPE_TOL_FRAC = 0.01
EAVE_SUBDIVISIONS = 4

COL_FRAME_A = "#FF6B6B"
COL_FRAME_B = "#e07b39"
COL_EAVE = "#2ecc71"
COL_MEMBRANE = "#4a7a9c"
COL_RING = "#ffd166"
COL_SPOKE = "#c0c0c0"
COL_DROP = "#a0a0a0"

# Default material constants if session state doesn't provide them.
DEFAULT_FABRIC_TYPE = "PVDF"
DEFAULT_FABRIC_GRADE = "Type III"


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
            "family": "A", "x": x, "y": y, "z": z,
            "offset": offset, "r_plan": r_plan, "apex_h": apex_h,
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
            "family": "B", "x": x, "y": y, "z": z,
            "offset": offset, "r_plan": r_plan, "apex_h": apex_h,
        })
        apexes.append((0.0, offset, apex_h, apex_h, r_plan))

    return frames, apexes, offsets_x, offsets_y


# =============================================================================
# EAVE POLYGON
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


def _subdivide_eave_polygon(anchors, subdivisions):
    n_a = len(anchors)
    loop = []
    anchor_idx = []
    for i in range(n_a):
        a = anchors[i]
        b = anchors[(i + 1) % n_a]
        anchor_idx.append(len(loop))
        for k in range(subdivisions):
            f = k / float(subdivisions)
            loop.append((
                a[0] + f * (b[0] - a[0]),
                a[1] + f * (b[1] - a[1]),
                a[2] + f * (b[2] - a[2]),
            ))
    return np.asarray(loop, dtype=float), anchor_idx


# =============================================================================
# PICK RESOLUTION
# =============================================================================

def _normalise_pick(item):
    try:
        if len(item) == 3:
            kind = str(item[0])
            if kind not in ("C", "Am", "Bm"):
                return None
            return (kind, int(item[1]), int(item[2]))
        elif len(item) == 2:
            return ("C", int(item[0]), int(item[1]))
    except (TypeError, ValueError):
        return None
    return None


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


def _resolve_pick(pick, offsets_x, offsets_y, ground_radius,
                   crown_height, curve_type, eave_height):
    kind, i, j = pick
    n_x = len(offsets_x)
    n_y = len(offsets_y)

    if kind == "C":
        if i < 0 or i >= n_x or j < 0 or j >= n_y:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": None, "y": None, "z": None,
                          "reason": "index out of range"}
        xi = offsets_x[i]
        yj = offsets_y[j]
        za = _frame_z_at_plan_offset(
            xi, yj, ground_radius, crown_height, curve_type
        )
        zb = _frame_z_at_plan_offset(
            yj, xi, ground_radius, crown_height, curve_type
        )
        if za is None or zb is None:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": xi, "y": yj, "z": None,
                          "reason": "crossing outside frame chord"}
        z = 0.5 * (za + zb)
        px, py = xi, yj

    elif kind == "Am":
        if i < 0 or i >= n_x:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": None, "y": None, "z": None,
                          "reason": "i out of range"}
        if j < 0 or j + 1 >= n_y:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": None, "y": None, "z": None,
                          "reason": "j out of range"}
        xi = offsets_x[i]
        y0 = offsets_y[j]
        y1 = offsets_y[j + 1]
        if xi * xi + y0 * y0 > ground_radius ** 2 + 1e-9:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": None, "y": None, "z": None,
                          "reason": "left crossing outside circle"}
        if xi * xi + y1 * y1 > ground_radius ** 2 + 1e-9:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": None, "y": None, "z": None,
                          "reason": "right crossing outside circle"}
        px = xi
        py = 0.5 * (y0 + y1)
        z = _frame_z_at_plan_offset(
            xi, py, ground_radius, crown_height, curve_type
        )
        if z is None:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": px, "y": py, "z": None,
                          "reason": "outside frame chord"}

    elif kind == "Bm":
        if j < 0 or j >= n_y:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": None, "y": None, "z": None,
                          "reason": "j out of range"}
        if i < 0 or i + 1 >= n_x:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": None, "y": None, "z": None,
                          "reason": "i out of range"}
        yj = offsets_y[j]
        x0 = offsets_x[i]
        x1 = offsets_x[i + 1]
        if x0 * x0 + yj * yj > ground_radius ** 2 + 1e-9:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": None, "y": None, "z": None,
                          "reason": "lower crossing outside circle"}
        if x1 * x1 + yj * yj > ground_radius ** 2 + 1e-9:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": None, "y": None, "z": None,
                          "reason": "upper crossing outside circle"}
        px = 0.5 * (x0 + x1)
        py = yj
        z = _frame_z_at_plan_offset(
            yj, px, ground_radius, crown_height, curve_type
        )
        if z is None:
            return None, {"kind": kind, "i": i, "j": j,
                          "x": px, "y": py, "z": None,
                          "reason": "outside frame chord"}

    else:
        return None, {"kind": kind, "i": i, "j": j,
                      "x": None, "y": None, "z": None,
                      "reason": "unknown pick kind"}

    if z > eave_height + 1e-9:
        return ({"kind": kind, "i": i, "j": j,
                 "x": float(px), "y": float(py), "z": float(z)},
                None)
    else:
        return None, {"kind": kind, "i": i, "j": j,
                      "x": float(px), "y": float(py), "z": float(z),
                      "reason": "at or below eave height"}


# =============================================================================
# CONE BUILDING
# =============================================================================

def _ring_node_count(radius, target_len):
    n = int(round(2.0 * math.pi * radius / max(target_len, 1e-6)))
    return max(12, min(32, n))


def _build_cone_geometry(pick, drop_length, ring_diameter, target_len):
    cx = pick["x"]
    cy = pick["y"]
    cz = pick["z"]

    ring_z = cz - drop_length
    ring_centre = (float(cx), float(cy), float(ring_z))

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
        "pick_kind": pick["kind"],
        "pick_ij": (pick["i"], pick["j"]),
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
            "x": ax, "y": ay, "r_plan": r_plan,
            "apex_h": az, "ref_h": ref_h, "diff": diff,
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

    warp_pretension = float(_get("warp_pretension", 1.0))
    weft_pretension = float(_get("weft_pretension", 1.0))
    edge_cable_pretension = float(_get("edge_cable_pretension", 25.0))

    ground_radius = max(dome_diameter / 2.0, 1e-6)

    # ---- Read picked positions ------------------------------------------
    picked_raw = _get("picked_crossings", None)
    if picked_raw is None:
        picked_raw = set()
    normalised_picks = set()
    for item in picked_raw:
        p = _normalise_pick(item)
        if p is not None:
            normalised_picks.add(p)

    # ---- Build frame -----------------------------------------------------
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
    kept_picks = []
    dropped_picks = []
    for pick in sorted(normalised_picks):
        kept, dropped = _resolve_pick(
            pick, offsets_x, offsets_y,
            ground_radius, crown_height, curve_type, eave_height,
        )
        if kept is not None:
            kept_picks.append(kept)
        if dropped is not None:
            dropped_picks.append(dropped)

    # ---- Build cones -----------------------------------------------------
    target_len = max(dome_diameter / 40.0, 0.4)
    cones = []
    for pick in kept_picks:
        cone = _build_cone_geometry(
            pick, drop_length, ring_diameter, target_len,
        )
        if cone is not None:
            cones.append(cone)

    # ---- Build membrane mesh via shared engine ---------------------------
    built = None
    membrane_target_len = max(dome_diameter / 30.0, 0.5)
    perimeter_loop = None
    anchor_idx = None
    if len(eave_polygon) >= 3:
        perimeter_loop, anchor_idx = _subdivide_eave_polygon(
            eave_polygon, EAVE_SUBDIVISIONS
        )
        ring_specs = []
        for cone in cones:
            rc = cone["ring_centre"]
            rn = cone["ring_nodes"]
            if len(rn) >= 2:
                rr = math.hypot(rn[0][0] - rc[0], rn[0][1] - rc[1])
            else:
                rr = ring_diameter / 2.0
            ring_specs.append({
                "cx": float(rc[0]), "cy": float(rc[1]),
                "cz": float(rc[2]), "r": float(rr),
                "beam_z": float(cone["crossing"][2]),
            })
        try:
            built = SDSe_mesh_rings(
                perimeter_loop=perimeter_loop,
                anchor_idx=anchor_idx,
                ring_specs=ring_specs,
                eave_height=eave_height,
                target_len=membrane_target_len,
            )
        except Exception as e:
            st.warning("Membrane build failed: " + str(e))
            built = None

    # ---- NFDM solve (Fork A) ---------------------------------------------
    # If the membrane mesh built, run the coupled NFDM solve.
    # If not, draw the unsolved geometry only.
    solved_coords = None
    solve_summary = None
    if built is not None:
        pts = built["points"].copy()
        tris = built["triangles"]
        n_nodes = pts.shape[0]

        # ---- Fixed set: eave anchors + ring polygon nodes ---------------
        # The eave anchors are the perimeter_loop indices in anchor_idx.
        # The ring polygon nodes are indices from built["ring_indices"].
        fixed_set = set()
        for i in anchor_idx:
            fixed_set.add(int(i))
        for idx_list in built["ring_indices"]:
            for i in idx_list:
                fixed_set.add(int(i))
        # Ring centres and beam tops: held, per Fork A.
        for ci in built["centre_indices"]:
            fixed_set.add(int(ci))
        for bi in built["beam_top_indices"]:
            fixed_set.add(int(bi))
        fixed_indices = sorted(fixed_set)

        # ---- Build cable elements ---------------------------------------
        cables = []

        # Perimeter cable: anchor-to-anchor along the eave polygon.
        n_a = len(anchor_idx)
        # Young's modulus and area for the perimeter cable. Reasonable
        # defaults for a steel strand: E = 160 GPa, A from the pretension
        # so the cable reaches the right tension.
        E_cable_Pa = 160.0e9
        # Choose A so that a typical strain gives the desired prestress.
        # For pretension T_pre and reference length L_ref, we set
        # L0 = L_ref / (1 + T_pre / EA). Pick A from a nominal T_pre.
        # We use the L_ref of the shortest eave segment as a reference.
        eave_seg_lengths = []
        for k in range(n_a):
            a_idx = anchor_idx[k]
            b_idx = anchor_idx[(k + 1) % n_a]
            L = float(np.linalg.norm(pts[b_idx] - pts[a_idx]))
            if L > 1e-9:
                eave_seg_lengths.append(L)
        if eave_seg_lengths:
            L_ref_mean = float(np.mean(eave_seg_lengths))
        else:
            L_ref_mean = 1.0
        # Choose A so that T_pre / (EA) is a sensible strain.
        # We target a strain of 0.001 (0.1%). A = T_pre / (E * 0.001).
        T_pre_N = max(edge_cable_pretension, 0.1) * 1000.0
        A_cable_m2 = max(T_pre_N / (E_cable_Pa * 0.001), 1e-6)
        EA_cable = A_cable_m2 * E_cable_Pa

        for k in range(n_a):
            a_idx = anchor_idx[k]
            b_idx = anchor_idx[(k + 1) % n_a]
            # chain: anchor -> subdivisions -> anchor.
            # The subdivisions between consecutive anchors in
            # perimeter_loop are at indices anchor_idx[k]+1 .. anchor_idx[k+1]-1
            # (modulo loop wrap).
            chain = [int(a_idx)]
            i_cur = (a_idx + 1) % pts.shape[0]
            b_int = int(b_idx)
            safety = 0
            while i_cur != b_int and safety < pts.shape[0]:
                chain.append(int(i_cur))
                i_cur = (i_cur + 1) % pts.shape[0]
                safety += 1
            chain.append(int(b_int))

            for m in range(len(chain) - 1):
                ia = chain[m]
                ib = chain[m + 1]
                L_ref = float(np.linalg.norm(pts[ib] - pts[ia]))
                if L_ref < 1e-9:
                    continue
                L0 = L_ref / (1.0 + T_pre_N / EA_cable)
                cables.append({
                    "a": ia, "b": ib,
                    "L0": L0, "EA": EA_cable,
                })

        # Drop members and ring chains.
        # For each cone:
        #   - drop: from centre_i to beam_top_i (built indices).
        #   - ring chain: around the ring polygon (built ring_indices).
        # Note: the engine's reference length for a cable is taken
        # from L0. We supply L0 directly so the pretension is
        # consistent. For drops and ring chains we set a small
        # pretension so they are taut initially.
        T_drop_pre_N = 500.0  # N, small
        T_ring_pre_N = 500.0  # N, small
        # Area for drop and ring steel. Assume a small steel section.
        E_steel_Pa = 210.0e9
        A_drop_m2 = 1e-4   # 100 mm^2, typical small steel bar
        A_ring_m2 = 1e-4
        EA_drop = A_drop_m2 * E_steel_Pa
        EA_ring = A_ring_m2 * E_steel_Pa

        for k, idx_list in enumerate(built["ring_indices"]):
            centre_i = int(built["centre_indices"][k])
            beam_i = int(built["beam_top_indices"][k])

            # Drop member: beam_top -> ring centre
            L_drop_ref = float(
                np.linalg.norm(pts[centre_i] - pts[beam_i])
            )
            if L_drop_ref > 1e-9:
                L0_drop = L_drop_ref / (1.0 + T_drop_pre_N / EA_drop)
                cables.append({
                    "a": beam_i, "b": centre_i,
                    "L0": L0_drop, "EA": EA_drop,
                })

            # Ring chain: closed loop around the ring polygon nodes.
            n_poly = len(idx_list)
            for m in range(n_poly):
                ia = int(idx_list[m])
                ib = int(idx_list[(m + 1) % n_poly])
                L_ref = float(np.linalg.norm(pts[ib] - pts[ia]))
                if L_ref < 1e-9:
                    continue
                L0 = L_ref / (1.0 + T_ring_pre_N / EA_ring)
                cables.append({
                    "a": ia, "b": ib,
                    "L0": L0, "EA": EA_ring,
                })

        # ---- Material ---------------------------------------------------
        # Defaults from make_membrane_material. In future we could
        # read fabric_type and fabric_grade from session state.
        material = make_membrane_material(
            E_warp_MPa=1400.0,
            E_weft_MPa=1400.0,
            thickness_mm=1.02,
            nu=0.34,
            G_MPa=50.0,
            warp_prestress_N_per_m=warp_pretension * 1000.0,
            weft_prestress_N_per_m=weft_pretension * 1000.0,
        )

        # ---- Solve ------------------------------------------------------
        try:
            res = solve_nonlinear_equilibrium(
                points=pts,
                triangles=tris,
                fixed_indices=fixed_indices,
                reference_points=pts.copy(),
                membrane_material=material,
                cables=cables,
                loads=None,
                max_iter=60,
                tol=1e-2,
            )
            solved_coords = res["coordinates"]
            solve_summary = {
                "converged": bool(res.get("converged", False)),
                "reason": str(res.get("reason", "")),
                "iterations": int(res.get("iterations", 0)),
                "total_steps": int(res.get("total_steps", 0)),
                "residual_norm": float(res.get("residual_norm", 0.0)),
                "max_residual": float(res.get("max_residual", 0.0)),
                "elapsed_seconds": float(res.get("elapsed_seconds", 0.0)),
                "n_cables": len(cables),
                "n_fixed": len(fixed_indices),
                "n_nodes": int(pts.shape[0]),
                "n_triangles": len(tris),
            }
        except Exception as e:
            st.warning("NFDM solve failed: " + str(e))
            solved_coords = None
            solve_summary = None

    # ---- Draw ------------------------------------------------------------
    fig = go.Figure()

    # Membrane: solved if available, else unsolved.
    if built is not None and len(built["triangles"]) > 0:
        tri = np.asarray(built["triangles"], dtype=int)
        draw_pts = solved_coords if solved_coords is not None else built["points"]
        fig.add_trace(go.Mesh3d(
            x=draw_pts[:, 0], y=draw_pts[:, 1], z=draw_pts[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            name="membrane", showlegend=False, hoverinfo="skip",
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

    # Cones. If solved, draw the ring and drop at the solved positions.
    if solved_coords is not None and built is not None:
        for k, idx_list in enumerate(built["ring_indices"]):
            centre_i = int(built["centre_indices"][k])
            beam_i = int(built["beam_top_indices"][k])

            # Drop member from solved positions
            bx, by, bz = solved_coords[beam_i]
            cx, cy, cz = solved_coords[centre_i]
            fig.add_trace(go.Scatter3d(
                x=[bx, cx], y=[by, cy], z=[bz, cz],
                mode="lines",
                line=dict(color=COL_DROP, width=4),
                name="drop", showlegend=False, hoverinfo="skip",
            ))
            # Ring polygon from solved positions
            pp = solved_coords[idx_list]
            closed = np.vstack([pp, pp[:1]])
            fig.add_trace(go.Scatter3d(
                x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
                mode="lines",
                line=dict(color=COL_RING, width=5),
                name="ring", showlegend=False, hoverinfo="skip",
            ))
            # Spokes from ring centre to each ring node
            for poly_i in idx_list:
                fig.add_trace(go.Scatter3d(
                    x=[cx, solved_coords[poly_i, 0]],
                    y=[cy, solved_coords[poly_i, 1]],
                    z=[cz, solved_coords[poly_i, 2]],
                    mode="lines",
                    line=dict(color=COL_SPOKE, width=2),
                    name="spoke", showlegend=False, hoverinfo="skip",
                ))
    else:
        # Unsolved: draw as-built
        for cone in cones:
            cx, cy, cz = cone["crossing"]
            rx, ry, rz = cone["ring_centre"]
            fig.add_trace(go.Scatter3d(
                x=[cx, rx], y=[cy, ry], z=[cz, rz],
                mode="lines",
                line=dict(color=COL_DROP, width=4),
                name="drop", showlegend=False, hoverinfo="skip",
            ))
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

        with st.expander("Picked positions (owner tier)", expanded=False):
            st.write(
                "**Total picks: %d. Kept: %d. Dropped: %d. "
                "Cones built: %d.**"
                % (len(normalised_picks), len(kept_picks),
                   len(dropped_picks), len(cones))
            )
            if kept_picks:
                st.markdown("**Kept (z above eave height):**")
                table = (
                    "  idx   kind  i    j      x          y          z\n"
                    "  ---  ----  ---  ---   ---------  ---------  ---------\n"
                )
                for k, p in enumerate(kept_picks):
                    table += (
                        "  %3d  %-4s  %3d  %3d   %+8.4f  %+8.4f  %8.4f\n"
                        % (k, p["kind"], p["i"], p["j"],
                           p["x"], p["y"], p["z"])
                    )
                st.code(table, language="text")
            if dropped_picks:
                st.markdown("**Dropped:**")
                table = (
                    "  idx   kind  i    j      x          y          z        reason\n"
                    "  ---  ----  ---  ---   ---------  ---------  ---------  ------\n"
                )
                for k, p in enumerate(dropped_picks):
                    x_s = ("%+8.4f" % p["x"]) if p["x"] is not None else "     ---"
                    y_s = ("%+8.4f" % p["y"]) if p["y"] is not None else "     ---"
                    z_s = ("%8.4f" % p["z"]) if p["z"] is not None else "     ---"
                    table += (
                        "  %3d  %-4s  %3d  %3d   %s  %s  %s  %s\n"
                        % (k, p["kind"], p["i"], p["j"],
                           x_s, y_s, z_s, p["reason"])
                    )
                st.code(table, language="text")

        with st.expander("Membrane geometry (owner tier)", expanded=False):
            if built is None:
                st.write("**Membrane not built.**")
            else:
                st.write(
                    "- Perimeter nodes: **%d**" % built["n_perimeter"]
                )
                st.write(
                    "- Interior fabric nodes: **%d**" % built["n_interior"]
                )
                st.write(
                    "- Total mesh nodes: **%d**"
                    % built["points"].shape[0]
                )
                st.write("- Mesh edges: **%d**" % len(built["edges"]))
                st.write("- Mesh triangles: **%d**" % len(built["triangles"]))
                st.write("- Held nodes: **%d**" % len(built["fixed_indices"]))
                st.write("- Ring holes: **%d**" % len(built["ring_indices"]))

        with st.expander("NFDM solve (owner tier)", expanded=False):
            if solve_summary is None:
                st.write("**NFDM solve not run.** "
                         "(No membrane mesh, or solve failed.)")
            else:
                st.write("**Fork A** — frame rigid, rings as cable chains.")
                st.write(
                    "- Converged: **%s**" % str(solve_summary["converged"])
                )
                st.write("- Reason: **%s**" % solve_summary["reason"])
                st.write("- Iterations: **%d**"
                         % solve_summary["iterations"])
                st.write("- Total steps: **%d**"
                         % solve_summary["total_steps"])
                st.write("- Elapsed (s): **%.2f**"
                         % solve_summary["elapsed_seconds"])
                st.write("- Residual norm: **%.4e**"
                         % solve_summary["residual_norm"])
                st.write("- Max residual: **%.4e**"
                         % solve_summary["max_residual"])
                st.write("- Nodes: **%d**" % solve_summary["n_nodes"])
                st.write("- Triangles: **%d**"
                         % solve_summary["n_triangles"])
                st.write("- Held nodes: **%d**" % solve_summary["n_fixed"])
                st.write("- Cable elements: **%d**"
                         % solve_summary["n_cables"])

        with st.expander("Cone geometry (owner tier)", expanded=False):
            st.write("One entry per built cone.")
            table = (
                "  idx   kind  i    j      crossing (x,y,z)          "
                "ring centre (x,y,z)        nodes\n"
                "  ---  ----  ---  ---   -------------------------  "
                "-------------------------  -----\n"
            )
            for k, cone in enumerate(cones):
                cx, cy, cz = cone["crossing"]
                rx, ry, rz = cone["ring_centre"]
                pi, pj = cone["pick_ij"]
                table += (
                    "  %3d  %-4s  %3d  %3d   "
                    "(%+7.3f,%+7.3f,%6.3f)  "
                    "(%+7.3f,%+7.3f,%6.3f)  %5d\n"
                    % (k, cone["pick_kind"], pi, pj,
                       cx, cy, cz, rx, ry, rz,
                       cone["ring_node_count"])
                )
            st.code(table, language="text")

    return apply_common_layout(fig, crown_height)


# =============================================================================
# END OF viewers/figures/dome_multi_cone.py
# =============================================================================
