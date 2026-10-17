# =============================================================================
# SDSe - Dome Multi-Cone Viewer
# =============================================================================
# Builds the 3D figure for the Dome Multi-Cone variant.
#
# Reads all inputs from session state under the "ws_dm_" prefix.
#
# PIECE 5b — FDM SEED ONLY (NFDM TEMPORARILY DISABLED).
#
#   Two solves, run in sequence:
#     1. FDM. Linear form-finding. Rings and drops treated as rigid.
#        Fixed set: eave anchors + ring polygon nodes + ring centres
#        + beam tops. Always converges. Fast.
#     2. NFDM. TEMPORARILY DISABLED. 
#        The solver is bypassed by forcing a 0.001s wall-clock limit.
#        The viewer draws the pure FDM mesh to allow for clean geometry
#        checking without the interference of a failing NFDM run.
#
#   If FDM fails, the unsolved mesh is drawn.
#
#   Performance guards:
#     - Solves are cached together.
#     - Coarser mesh: target_len = diameter / 30.
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
#   2026-10-14 - Piece 5b. NFDM solve. Cached. Lean mesh. Hard cap.
#   2026-10-14 - Piece 5b fix. FDM seed, then NFDM refine.
#   2026-10-16 - Fix: Disabled NFDM temporarily to isolate FDM mesh.
#   2026-10-17 - Fix: Increased eave subdivisions. Added independent
#                edge cable pretension. Set ring default to 1.0.
#                Removed visual eave polygon line.
# =============================================================================

import hashlib
import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engine.form_finding_test import solve_fdm
from engine.SDSe_mesh_builder import (
    SDSe_mesh_rings,
    SDSe_blend_q_per_edge,
)
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
EAVE_SUBDIVISIONS = 17  # Increased from 4 to match tester density

# Solver performance guards.
SOLVE_TARGET_LEN_FRAC = 30.0   # target mesh edge = dome_diameter / this
SOLVE_WALL_SECONDS = 25.0      # hard cap on the NFDM solve
SOLVE_MAX_ITER = 40
SOLVE_MAX_OUTER = 6
SOLVE_TOL = 1e-2

COL_FRAME_A = "#FF6B6B"
COL_FRAME_B = "#e07b39"
COL_EAVE = "#2ecc71"
COL_MEMBRANE = "#4a7a9c"
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
    return max(12, min(24, n))


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
# CACHED FDM + NFDM SOLVE
# =============================================================================

def _hash_mesh(pts, tris, cables, fdm_fixed, nfdm_fixed, material_key):
    h = hashlib.sha256()
    h.update(np.round(pts, 6).astype(np.float64).tobytes())
    h.update(np.asarray(tris, dtype=np.int32).tobytes())
    for cb in cables:
        h.update(bytes(str((int(cb["a"]), int(cb["b"]))), "utf-8"))
        h.update(np.float64(cb["L0"]).tobytes())
        h.update(np.float64(cb["EA"]).tobytes())
    h.update(np.asarray(fdm_fixed, dtype=np.int32).tobytes())
    h.update(np.asarray(nfdm_fixed, dtype=np.int32).tobytes())
    h.update(bytes(material_key, "utf-8"))
    return h.hexdigest()


def _pack_edges(edges):
    buf = bytearray()
    for (a, b) in edges:
        buf += np.int32(int(a)).tobytes()
        buf += np.int32(int(b)).tobytes()
    return bytes(buf)


def _unpack_edges(edges_bytes):
    arr = np.frombuffer(edges_bytes, dtype=np.int32)
    return [(int(arr[i]), int(arr[i + 1]))
            for i in range(0, len(arr), 2)]


def _pack_cables(cables):
    buf = bytearray()
    for cb in cables:
        buf += np.int32(int(cb["a"])).tobytes()
        buf += np.int32(int(cb["b"])).tobytes()
        buf += np.float64(float(cb["L0"])).tobytes()
        buf += np.float64(float(cb["EA"])).tobytes()
    return bytes(buf)


def _unpack_cables(cables_bytes):
    arr = np.frombuffer(cables_bytes, dtype=np.uint8)
    cables = []
    stride = 24
    for off in range(0, len(arr), stride):
        a = int(np.frombuffer(arr[off:off + 4], dtype=np.int32)[0])
        b = int(np.frombuffer(arr[off + 4:off + 8],
                               dtype=np.int32)[0])
        L0 = float(np.frombuffer(arr[off + 8:off + 16],
                                  dtype=np.float64)[0])
        EA = float(np.frombuffer(arr[off + 16:off + 24],
                                  dtype=np.float64)[0])
        cables.append({"a": a, "b": b, "L0": L0, "EA": EA})
    return cables


@st.cache_data(show_spinner=False, max_entries=8)
def _cached_solve(mesh_hash,
                   pts_bytes, tris_bytes, edges_bytes,
                   fdm_fixed_bytes, nfdm_fixed_bytes,
                   cables_bytes, q_interior_bytes,
                   boundary_edge_keys_bytes, edge_q_scalar,
                   warp_prestress, weft_prestress,
                   max_iter, max_outer, tol, wall_seconds):
    """
    Cached FDM seed + NFDM refine. Returns:
        fdm_coords_bytes, nfdm_coords_bytes or b"", summary
    All numpy arrays are passed as bytes so Streamlit can hash them.
    """
    pts = np.frombuffer(pts_bytes, dtype=np.float64).reshape(-1, 3).copy()
    tris = np.frombuffer(tris_bytes, dtype=np.int32).reshape(-1, 3).tolist()
    edges = _unpack_edges(edges_bytes)
    fdm_fixed = np.frombuffer(fdm_fixed_bytes, dtype=np.int32).tolist()
    nfdm_fixed = np.frombuffer(nfdm_fixed_bytes, dtype=np.int32).tolist()
    cables = _unpack_cables(cables_bytes)
    q_interior = np.frombuffer(q_interior_bytes, dtype=np.float64).copy()

    boundary_edge_set = set()
    arr_b = np.frombuffer(boundary_edge_keys_bytes, dtype=np.int32)
    for i in range(0, len(arr_b), 2):
        boundary_edge_set.add((int(arr_b[i]), int(arr_b[i + 1])))

    # ---- Build q array for FDM --------------------------------------
    # Interior q from the passed-in blend, boundary edges use scalar.
    q_fdm = np.empty(len(edges), dtype=np.float64)
    for k, (i, j) in enumerate(edges):
        key = (i, j) if i < j else (j, i)
        if key in boundary_edge_set:
            q_fdm[k] = edge_q_scalar
        else:
            q_fdm[k] = q_interior[k]

    # ---- FDM solve --------------------------------------------------
    fdm_summary = {"converged": False, "reason": "not run"}
    try:
        fdm_res = solve_fdm(pts.copy(), edges, fdm_fixed, q_fdm)
        fdm_coords = fdm_res["coordinates"]
        fdm_summary = {
            "converged": True,
            "reason": "ok",
            "residual_norm": float(fdm_res.get("residual_norm", 0.0)),
            "n_free": int(fdm_res.get("n_free", 0)),
            "n_fixed": int(fdm_res.get("n_fixed", 0)),
        }
    except Exception as e:
        fdm_coords = pts.copy()
        fdm_summary = {"converged": False, "reason": "exception: " + str(e),
                        "residual_norm": 0.0, "n_free": 0, "n_fixed": 0}

    # ---- NFDM refine, seeded from FDM -------------------------------
    material = make_membrane_material(
        E_warp_MPa=1400.0,
        E_weft_MPa=1400.0,
        thickness_mm=1.02,
        nu=0.34,
        G_MPa=50.0,
        warp_prestress_N_per_m=warp_prestress,
        weft_prestress_N_per_m=weft_prestress,
    )

    nfdm_summary = {"converged": False, "reason": "not run",
                     "iterations": 0, "total_steps": 0,
                     "elapsed_seconds": 0.0,
                     "residual_norm": 0.0, "max_residual": 0.0,
                     "n_cables": len(cables), "n_fixed": len(nfdm_fixed),
                     "n_nodes": int(pts.shape[0]),
                     "n_triangles": len(tris)}
    nfdm_coords = None
    try:
        nfdm_res = solve_nonlinear_equilibrium(
            points=fdm_coords.copy(),
            triangles=tris,
            fixed_indices=nfdm_fixed,
            reference_points=fdm_coords.copy(),
            membrane_material=material,
            cables=cables,
            loads=None,
            max_iter=max_iter,
            max_outer=max_outer,
            tol=tol,
            max_wall_seconds=wall_seconds,
        )
        nfdm_coords = nfdm_res["coordinates"]
        nfdm_summary = {
            "converged": bool(nfdm_res.get("converged", False)),
            "reason": str(nfdm_res.get("reason", "")),
            "iterations": int(nfdm_res.get("iterations", 0)),
            "total_steps": int(nfdm_res.get("total_steps", 0)),
            "elapsed_seconds": float(nfdm_res.get("elapsed_seconds", 0.0)),
            "residual_norm": float(nfdm_res.get("residual_norm", 0.0)),
            "max_residual": float(nfdm_res.get("max_residual", 0.0)),
            "n_cables": len(cables),
            "n_fixed": len(nfdm_fixed),
            "n_nodes": int(pts.shape[0]),
            "n_triangles": len(tris),
        }
    except Exception as e:
        nfdm_summary["reason"] = "exception: " + str(e)

    return (
        fdm_coords.tobytes(),
        nfdm_coords.tobytes() if nfdm_coords is not None else b"",
        {"fdm": fdm_summary, "nfdm": nfdm_summary},
    )


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
    ring_diameter = float(_get("ring_diameter", 1.0))

    warp_pretension = float(_get("warp_pretension", 1.0))
    weft_pretension = float(_get("weft_pretension", 1.0))
    edge_cable_pretension = float(_get("edge_cable_pretension", 3.0))

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
    membrane_target_len = max(dome_diameter / SOLVE_TARGET_LEN_FRAC, 0.5)
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

    # ---- Build q, FDM fixed, NFDM fixed, cables --------------------------
    fdm_coords = None
    nfdm_coords = None
    solve_summary = None

    if built is not None:
        pts = built["points"].copy()
        tris = built["triangles"]
        edges = built["edges"]
        boundary_edge_set = built["boundary_edges"]

        # ---- Compute q_interior for the blend --------------------------
        pts_2d = pts[:, :2]
        warp_q = max(warp_pretension, 0.1) * 1000.0
        weft_q = max(weft_pretension, 0.1) * 1000.0
        warp_dir = np.array([1.0, 0.0])
        q_interior = SDSe_blend_q_per_edge(
            edges, pts_2d, warp_dir, warp_q, weft_q
        )
        edge_q_scalar = max(edge_cable_pretension, 0.1) * 1000.0

        # ---- FDM fixed set: eave anchors + ring nodes + centres + tops -
        fdm_fixed_set = set()
        for i in anchor_idx:
            fdm_fixed_set.add(int(i))
        for idx_list in built["ring_indices"]:
            for i in idx_list:
                fdm_fixed_set.add(int(i))
        for ci in built["centre_indices"]:
            fdm_fixed_set.add(int(ci))
        for bi in built["beam_top_indices"]:
            fdm_fixed_set.add(int(bi))
        fdm_fixed = sorted(fdm_fixed_set)

        # ---- NFDM fixed set: eave anchors + ring nodes + beam tops ----
        # (ring centres free — drops can deflect)
        nfdm_fixed_set = set()
        for i in anchor_idx:
            nfdm_fixed_set.add(int(i))
        for idx_list in built["ring_indices"]:
            for i in idx_list:
                nfdm_fixed_set.add(int(i))
        for bi in built["beam_top_indices"]:
            nfdm_fixed_set.add(int(bi))
        nfdm_fixed = sorted(nfdm_fixed_set)

        # ---- Cable set (NFDM only) ------------------------------------
        cables = []
        E_cable_Pa = 160.0e9
        n_a = len(anchor_idx)
        T_pre_N = max(edge_cable_pretension, 0.1) * 1000.0
        A_cable_m2 = max(T_pre_N / (E_cable_Pa * 0.001), 1e-6)
        EA_cable = A_cable_m2 * E_cable_Pa

        for k in range(n_a):
            a_idx = anchor_idx[k]
            b_idx = anchor_idx[(k + 1) % n_a]
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
                cables.append({"a": ia, "b": ib, "L0": L0, "EA": EA_cable})

        T_drop_pre_N = 500.0
        T_ring_pre_N = 500.0
        E_steel_Pa = 210.0e9
        EA_drop = 1e-4 * E_steel_Pa
        EA_ring = 1e-4 * E_steel_Pa

        for k, idx_list in enumerate(built["ring_indices"]):
            centre_i = int(built["centre_indices"][k])
            beam_i = int(built["beam_top_indices"][k])
            L_drop_ref = float(np.linalg.norm(pts[centre_i] - pts[beam_i]))
            if L_drop_ref > 1e-9:
                L0_drop = L_drop_ref / (1.0 + T_drop_pre_N / EA_drop)
                cables.append({
                    "a": beam_i, "b": centre_i,
                    "L0": L0_drop, "EA": EA_drop,
                })
            n_poly = len(idx_list)
            for m in range(n_poly):
                ia = int(idx_list[m])
                ib = int(idx_list[(m + 1) % n_poly])
                L_ref = float(np.linalg.norm(pts[ib] - pts[ia]))
                if L_ref < 1e-9:
                    continue
                L0 = L_ref / (1.0 + T_ring_pre_N / EA_ring)
                cables.append({"a": ia, "b": ib, "L0": L0, "EA": EA_ring})

        # ---- Cache key -------------------------------------------------
        material_key = "PVDF_TypeIII_%.4f_%.4f" % (
            warp_pretension, weft_pretension
        )
        mesh_hash = _hash_mesh(
            pts, tris, cables, fdm_fixed, nfdm_fixed, material_key
        )

        # ---- Pack boundary edge keys for the cache --------------------
        boundary_keys_flat = []
        for (a, b) in boundary_edge_set:
            boundary_keys_flat.append(int(a))
            boundary_keys_flat.append(int(b))
        boundary_keys_arr = np.asarray(
            boundary_keys_flat, dtype=np.int32
        )

        # ---- Call cached solve (NFDM temporarily disabled) ------------
        with st.spinner("Solving FDM seed..."):
            fdm_bytes, _, summary = _cached_solve(
                mesh_hash,
                pts.astype(np.float64).tobytes(),
                np.asarray(tris, dtype=np.int32).tobytes(),
                _pack_edges(edges),
                np.asarray(fdm_fixed, dtype=np.int32).tobytes(),
                np.asarray(nfdm_fixed, dtype=np.int32).tobytes(),
                _pack_cables(cables),
                q_interior.astype(np.float64).tobytes(),
                boundary_keys_arr.tobytes(),
                float(edge_q_scalar),
                float(warp_pretension * 1000.0),
                float(weft_pretension * 1000.0),
                int(SOLVE_MAX_ITER),
                int(SOLVE_MAX_OUTER),
                float(SOLVE_TOL),
                0.001,  # 1 ms wall cap forces NFDM to abort instantly
            )
            fdm_coords = np.frombuffer(
                fdm_bytes, dtype=np.float64
            ).reshape(-1, 3).copy()
            nfdm_coords = None  # Force viewer to draw FDM shape only
            solve_summary = summary

    # ---- Draw ------------------------------------------------------------
    fig = go.Figure()

    # Choose the coords to draw: Since NFDM is off, draw FDM.
    draw_pts = None
    if built is not None:
        if fdm_coords is not None:
            draw_pts = fdm_coords
        else:
            draw_pts = built["points"]

    if built is not None and len(built["triangles"]) > 0 and draw_pts is not None:
        tri = np.asarray(built["triangles"], dtype=int)
        fig.add_trace(go.Mesh3d(
            x=draw_pts[:, 0], y=draw_pts[:, 1], z=draw_pts[:, 2],
            i=tri[:, 0], j=tri[:, 1], k=tri[:, 2],
            color=COL_MEMBRANE, opacity=0.55, flatshading=True,
            name="membrane", showlegend=False, hoverinfo="skip",
        ))

    for f in frames:
        color = COL_FRAME_A if f["family"] == "A" else COL_FRAME_B
        fig.add_trace(go.Scatter3d(
            x=f["x"], y=f["y"], z=f["z"],
            mode="lines",
            line=dict(color=color, width=4),
            name="frame " + f["family"],
            showlegend=False, hoverinfo="skip",
        ))

    # EAVE POLYGON LINE REMOVED HERE AS REQUESTED

    # Cones: draw from solved positions if available.
    if draw_pts is not None and built is not None:
        for k, idx_list in enumerate(built["ring_indices"]):
            centre_i = int(built["centre_indices"][k])
            beam_i = int(built["beam_top_indices"][k])
            bx, by, bz = draw_pts[beam_i]
            cx, cy, cz = draw_pts[centre_i]
            fig.add_trace(go.Scatter3d(
                x=[bx, cx], y=[by, cy], z=[bz, cz],
                mode="lines",
                line=dict(color=COL_DROP, width=4),
                name="drop", showlegend=False, hoverinfo="skip",
            ))
            pp = draw_pts[idx_list]
            closed = np.vstack([pp, pp[:1]])
            fig.add_trace(go.Scatter3d(
                x=closed[:, 0], y=closed[:, 1], z=closed[:, 2],
                mode="lines",
                line=dict(color=COL_RING, width=5),
                name="ring", showlegend=False, hoverinfo="skip",
            ))
            for poly_i in idx_list:
                fig.add_trace(go.Scatter3d(
                    x=[cx, draw_pts[poly_i, 0]],
                    y=[cy, draw_pts[poly_i, 1]],
                    z=[cz, draw_pts[poly_i, 2]],
                    mode="lines",
                    line=dict(color=COL_SPOKE, width=2),
                    name="spoke", showlegend=False, hoverinfo="skip",
                ))
    else:
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

        with st.expander("Picked positions (owner tier)", expanded=False):
            st.write(
                "**Total picks: %d. Kept: %d. Dropped: %d. Cones: %d.**"
                % (len(normalised_picks), len(kept_picks),
                   len(dropped_picks), len(cones))
            )

        with st.expander("Membrane geometry (owner tier)", expanded=False):
            if built is None:
                st.write("**Membrane not built.**")
            else:
                st.write("- Perimeter nodes: **%d**" % built["n_perimeter"])
                st.write("- Interior fabric nodes: **%d**" % built["n_interior"])
                st.write("- Total mesh nodes: **%d**"
                         % built["points"].shape[0])
                st.write("- Mesh edges: **%d**" % len(built["edges"]))
                st.write("- Mesh triangles: **%d**" % len(built["triangles"]))
                st.write("- Held nodes (FDM): **%d**"
                         % (len(fdm_fixed) if fdm_coords is not None else 0))
                st.write("- Ring holes: **%d**" % len(built["ring_indices"]))

        with st.expander("FDM + NFDM solve (owner tier)", expanded=False):
            st.write("**NFDM temporarily disabled for pure FDM mesh testing.**")
            if solve_summary is None:
                st.write("**Solve not run.**")
            else:
                f = solve_summary["fdm"]
                st.write("- FDM converged: **%s**" % str(f["converged"]))
                st.write("- FDM reason: **%s**" % f["reason"])
                st.write("- FDM residual: **%.4e**" % f["residual_norm"])
                st.write(
                    "**Mesh target: diameter / %.0f. Cached.**"
                    % SOLVE_TARGET_LEN_FRAC
                )

    return apply_common_layout(fig, crown_height)


# =============================================================================
# END OF viewers/figures/dome_multi_cone.py
# =============================================================================
