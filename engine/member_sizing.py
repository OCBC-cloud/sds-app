# =============================================================================
# SDSe Engine - Member Sizing
# =============================================================================
# Link 2 of the engine chain, following engine/form_finding.py.
#
# Purpose: from the form-found solution, compute the design force
# in every member group. These forces are what the section selection
# layer will size members against.
#
# This file computes forces only. It does NOT select sections. It does
# NOT perform code checks. It does NOT compute the bill of quantities.
#
# Member groups:
#   membrane    - in-plane force per unit width, from q x L per edge
#   edge_cable  - resultant axial tension along each boundary segment
#   beam        - bending moment and shear in the main beam, treated
#                 as a continuous beam over all supports
#   tiedown     - axial tension in each tiedown, resolved along the
#                 cable axis from the support reaction
#   purlin      - secondary members, only for the Beam Supported Saddle
#
# Two-pass workflow and force densities:
#   The engine has a two-pass workflow.
#     Pass 1 (solve_fdm)          - the user's chosen pretensions are
#                                   used as force densities. The shape
#                                   falls out. These pretensions are a
#                                   design lever. They are not the
#                                   physical prestress of the settled
#                                   structure.
#     Pass 2 (solve_fdm_settled)  - the shape is accepted. The settled
#                                   force densities of the structure
#                                   are used. The reactions and the
#                                   member forces from this pass are
#                                   the real ones.
#
#   This file uses the settled force densities (settled_q) when they
#   are present in the built dict, and the settled reactions
#   (settled_reactions) when they are present. It falls back to the
#   form-finding q and reactions when the two-pass data is absent.
#
# Partial factors:
#   Read from data/constants.py PARTIAL_FACTORS. Applied to the
#   prestress forces as gamma_G. When wind and snow load cases are
#   added, the same function applies gamma_Q to the variable
#   contribution.
#
# Units: kN, m, degrees.
#
# Usage:
#   from engine.member_sizing import design_forces_from_built
#   forces = design_forces_from_built(built, code="MY", base_condition="pinned")
#
# History:
#   2026-10-07 - First version. Five member groups. Beam continuous
#                over all supports, pinned or fixed ends. Design
#                forces with partial factors applied.
#   2026-10-07 - Prefer settled_reactions when the two-pass workflow
#                has run. Fall back to form-finding reactions.
#   2026-10-07 - Prefer settled_q for the membrane, edge cable, and
#                beam computations. The form-finding q is a design
#                lever; the settled q is the physical prestress of
#                the settled structure. This is the other half of
#                the two-pass fix.
# =============================================================================

import math

import numpy as np

from data.constants import PARTIAL_FACTORS


# =============================================================================
# PUBLIC ENTRY POINTS
# =============================================================================

def design_forces_from_q(q, edges, segments, anchor_pos, code=None):
    """
    Low-level entry point. Computes the forces that depend only on
    the q array and the geometry. Does not require the solver
    reactions or the settled coordinates.

    Parameters
    ----------
    q : array-like, one force density per edge
    edges : list of (i, j)
    segments : list of dicts with keys anchor_a, anchor_b, interior
    anchor_pos : (n_anchor, 3) array of anchor coordinates
    code : str or None, reserved for future code-dependent factors

    Returns
    -------
    dict with keys: membrane, edge_cable, note
    """
    edges = list(edges)
    q = np.asarray(q, dtype=float)

    membrane = _compute_membrane_forces(q, edges, lengths=None)
    edge_cable = _compute_edge_cable_forces_from_segments(
        q, edges, segments
    )

    return {
        "membrane": membrane,
        "edge_cable": edge_cable,
        "note": (
            "Raw forces from q only. Use design_forces_from_built for "
            "factored design forces and the full member set."
        ),
    }


def design_forces_from_built(built, code=None, base_condition="pinned"):
    """
    High-level entry point. Reads the built dict produced by the
    FDM path in the viewer. Returns the design force per member
    group, with partial factors applied.

    Uses the settled force densities and settled reactions when the
    two-pass workflow has run. Falls back to the form-finding q and
    reactions when it has not.

    Parameters
    ----------
    built : dict
        As returned by _solve_fdm_path or _solve_nfdm_path.
        Must contain: points, edges, triangles, q, boundary_loop,
        anchor_pos, segments, diagnostics.
    code : str or None
        Country code for partial factor lookup. Currently unused.
    base_condition : "pinned" or "fixed"
        End condition for the beam.

    Returns
    -------
    dict with keys: membrane, edge_cable, beam, tiedown, purlin,
                    partial_factors, base_condition, code, note
    """
    code_upper = str(code).upper() if code is not None else None
    base = str(base_condition).lower()
    if base not in ("pinned", "fixed"):
        base = "pinned"

    pf = dict(PARTIAL_FACTORS)
    gamma_G = float(pf.get("gamma_G", 1.35))

    coords = np.asarray(built["points"], dtype=float)
    edges = list(built["edges"])
    triangles = list(built["triangles"])
    boundary_loop = np.asarray(built["boundary_loop"], dtype=float)
    anchor_pos = np.asarray(built["anchor_pos"], dtype=float)
    segments = list(built["segments"])
    diag = built.get("diagnostics", {}) or {}

    n_boundary = int(boundary_loop.shape[0])

    # -------------------------------------------------------------------------
    # Force density selection.
    # Prefer the settled q when the two-pass workflow has run. The
    # form-finding q is a design lever; the settled q is the physical
    # prestress of the settled structure. Using the form-finding q for
    # the member forces inflates them by the ratio of the user's
    # pretension to the settled pretension.
    # -------------------------------------------------------------------------
    q_form_finding = np.asarray(built["q"], dtype=float)
    q_settled = built.get("settled_q", None)
    if q_settled is not None:
        q = np.asarray(q_settled, dtype=float)
    else:
        q = q_form_finding

    lengths = _edge_lengths(coords, edges)
    membrane_raw = _compute_membrane_forces(q, edges, lengths=lengths)
    edge_cable_raw = _compute_edge_cable_forces(
        q, edges, lengths, segments, coords, n_boundary
    )

    # -------------------------------------------------------------------------
    # Reaction selection.
    # Prefer the settled reactions when the two-pass workflow has run.
    # -------------------------------------------------------------------------
    fixed_indices = diag.get("fixed_indices", None)
    reactions = diag.get("settled_reactions", None)
    if reactions is None:
        reactions = diag.get("reactions", None)

    beam_raw = _compute_beam_forces(
        coords=coords,
        edges=edges,
        q=q,
        lengths=lengths,
        boundary_loop=boundary_loop,
        anchor_pos=anchor_pos,
        segments=segments,
        n_boundary=n_boundary,
        base_condition=base,
    )

    tiedown_raw = _compute_tiedown_forces(
        coords=coords,
        reactions=reactions,
        fixed_indices=fixed_indices,
        anchor_pos=anchor_pos,
        segments=segments,
        n_boundary=n_boundary,
    )

    variant_key = str(diag.get("variant_key", "standard_saddle"))
    if variant_key == "frame_supported_saddle":
        purlin_raw = {
            "status": "pending",
            "note": "Purlin forces require the Beam Supported Saddle workshop.",
        }
    else:
        purlin_raw = {
            "status": "not_applicable",
            "note": "Purlins are used only on the Beam Supported Saddle.",
        }

    membrane = _apply_factor(membrane_raw, gamma_G)
    edge_cable = _apply_factor(edge_cable_raw, gamma_G)
    beam = _apply_factor(beam_raw, gamma_G)
    tiedown = _apply_factor(tiedown_raw, gamma_G)

    return {
        "membrane": membrane,
        "edge_cable": edge_cable,
        "beam": beam,
        "tiedown": tiedown,
        "purlin": purlin_raw,
        "partial_factors": pf,
        "base_condition": base,
        "code": code_upper,
        "note": (
            "Design forces with partial factors applied (gamma_G). "
            "Member forces use the settled force densities when the "
            "two-pass workflow has run. No section selection, no "
            "code checks. Those come in later files."
        ),
    }


# =============================================================================
# HELPERS
# =============================================================================

def _edge_lengths(coords, edges):
    """Return the length of every edge."""
    coords = np.asarray(coords, dtype=float)
    out = np.zeros(len(edges), dtype=float)
    for k, (i, j) in enumerate(edges):
        out[k] = float(np.linalg.norm(coords[int(j)] - coords[int(i)]))
    return out


def _is_boundary_edge(a, b, n_boundary):
    """True if the edge lies on the boundary loop."""
    if n_boundary <= 0:
        return False
    a = int(a)
    b = int(b)
    if a >= n_boundary or b >= n_boundary:
        return False
    d = abs(a - b)
    return d == 1 or d == n_boundary - 1


def _apply_factor(entry, gamma):
    """Multiply every force-like field in an entry by gamma."""
    if not isinstance(entry, dict):
        return entry
    out = dict(entry)
    for key, value in list(out.items()):
        if key in ("status", "note", "model"):
            continue
        if key.endswith("_kN") and isinstance(value, (int, float)):
            out[key] = float(value) * float(gamma)
        if key.endswith("_kN_m") and isinstance(value, (int, float)):
            out[key] = float(value) * float(gamma)
        if key.endswith("_kN_per_m") and isinstance(value, (int, float)):
            out[key] = float(value) * float(gamma)
    for listkey in ("values_kN", "values_kN_per_m", "values_kN_m"):
        if listkey in out and isinstance(out[listkey], list):
            out[listkey] = [float(v) * float(gamma) for v in out[listkey]]
    return out


# =============================================================================
# MEMBRANE
# =============================================================================

def _compute_membrane_forces(q, edges, lengths=None):
    """Membrane in-plane force per edge. Force N = q x L (N)."""
    q = np.asarray(q, dtype=float)
    edges = list(edges)

    if lengths is None:
        lengths = np.ones(len(edges), dtype=float)
    lengths = np.asarray(lengths, dtype=float)

    forces_N = q * lengths
    forces_kN = forces_N / 1000.0

    if forces_kN.size == 0:
        return {
            "model": "membrane edge force = q x L",
            "n": 0,
            "min_kN": 0.0, "max_kN": 0.0, "mean_kN": 0.0,
            "governing_edge": None,
            "values_kN": [],
        }

    imax = int(np.argmax(forces_kN))
    a, b = edges[imax]

    return {
        "model": "membrane edge force = q x L",
        "n": int(forces_kN.size),
        "min_kN":  float(np.min(forces_kN)),
        "max_kN":  float(np.max(forces_kN)),
        "mean_kN": float(np.mean(forces_kN)),
        "governing_edge": (int(a), int(b)),
        "values_kN": [float(v) for v in forces_kN.tolist()],
    }


# =============================================================================
# EDGE CABLE
# =============================================================================

def _compute_edge_cable_forces_from_segments(q, edges, segments):
    """Edge cable resultant tension per segment, from q and geometry."""
    q = np.asarray(q, dtype=float)
    edges = list(edges)

    per_segment = []
    for seg_idx, seg in enumerate(segments):
        chain = [int(seg["anchor_a"])] + [int(i) for i in seg["interior"]] + [int(seg["anchor_b"])]
        force_sum = 0.0
        n_edges = 0
        for k in range(len(chain) - 1):
            a = chain[k]
            b = chain[k + 1]
            key = (a, b) if a < b else (b, a)
            idx = None
            for e_idx, (ei, ej) in enumerate(edges):
                if (int(ei), int(ej)) == key:
                    idx = e_idx
                    break
            if idx is None:
                continue
            force_sum += float(q[idx])
            n_edges += 1
        per_segment.append({
            "segment_index": int(seg_idx),
            "n_edges": int(n_edges),
            "force_kN": float(force_sum) / 1000.0,
        })

    if not per_segment:
        return {
            "model": "edge cable tension = sum of boundary edge forces along segment",
            "n_segments": 0,
            "min_kN": 0.0, "max_kN": 0.0, "mean_kN": 0.0,
            "governing_segment": None,
            "segments": [],
        }

    forces = [s["force_kN"] for s in per_segment]
    imax = int(np.argmax(forces))

    return {
        "model": "edge cable tension = sum of boundary edge forces along segment",
        "n_segments": len(per_segment),
        "min_kN":  float(np.min(forces)),
        "max_kN":  float(np.max(forces)),
        "mean_kN": float(np.mean(forces)),
        "governing_segment": int(per_segment[imax]["segment_index"]),
        "segments": per_segment,
    }


def _compute_edge_cable_forces(q, edges, lengths, segments, coords, n_boundary):
    """Full edge cable computation using actual edge lengths."""
    edges = list(edges)
    q = np.asarray(q, dtype=float)
    lengths = np.asarray(lengths, dtype=float)
    coords = np.asarray(coords, dtype=float)

    per_segment = []
    for seg_idx, seg in enumerate(segments):
        chain = (
            [int(seg["anchor_a"])]
            + [int(i) for i in seg["interior"]]
            + [int(seg["anchor_b"])]
        )
        total_N = 0.0
        n_edges = 0
        for k in range(len(chain) - 1):
            a = chain[k]
            b = chain[k + 1]
            key = (a, b) if a < b else (b, a)
            for e_idx, (ei, ej) in enumerate(edges):
                if (int(ei), int(ej)) == key:
                    total_N += float(q[e_idx]) * float(lengths[e_idx])
                    n_edges += 1
                    break

        p0 = coords[chain[0]]
        p1 = coords[chain[-1]]
        chord = p1 - p0
        chord_len = float(np.linalg.norm(chord))

        per_segment.append({
            "segment_index": int(seg_idx),
            "n_edges": int(n_edges),
            "chord_length_m": float(chord_len),
            "force_kN": float(total_N) / 1000.0,
        })

    if not per_segment:
        return {
            "model": "edge cable tension = resultant of boundary edge forces along segment",
            "n_segments": 0,
            "min_kN": 0.0, "max_kN": 0.0, "mean_kN": 0.0,
            "governing_segment": None,
            "segments": [],
        }

    forces = [s["force_kN"] for s in per_segment]
    imax = int(np.argmax(forces))

    return {
        "model": "edge cable tension = resultant of boundary edge forces along segment",
        "n_segments": len(per_segment),
        "min_kN":  float(np.min(forces)),
        "max_kN":  float(np.max(forces)),
        "mean_kN": float(np.mean(forces)),
        "governing_segment": int(per_segment[imax]["segment_index"]),
        "segments": per_segment,
    }


# =============================================================================
# BEAM - CONTINUOUS OVER ALL SUPPORTS
# =============================================================================

def _compute_beam_forces(coords, edges, q, lengths, boundary_loop,
                          anchor_pos, segments, n_boundary,
                          base_condition="pinned"):
    """Beam bending moment and shear, continuous over all supports."""
    n_anchors = int(anchor_pos.shape[0])
    if n_anchors < 2:
        return {
            "model": "continuous beam over all supports, pinned ends",
            "status": "insufficient_supports",
            "max_moment_kN_m": 0.0,
            "max_shear_kN": 0.0,
            "governing_span": None,
            "spans": [],
        }

    span_lengths = np.zeros(n_anchors - 1, dtype=float)
    for k in range(n_anchors - 1):
        span_lengths[k] = float(np.linalg.norm(
            anchor_pos[k + 1] - anchor_pos[k]
        ))

    span_loads_kN_per_m = np.zeros(n_anchors - 1, dtype=float)
    for k in range(len(segments)):
        seg = segments[k]
        chain = (
            [int(seg["anchor_a"])]
            + [int(i) for i in seg["interior"]]
            + [int(seg["anchor_b"])]
        )
        total_N = 0.0
        for m in range(len(chain) - 1):
            a = chain[m]
            b = chain[m + 1]
            key = (a, b) if a < b else (b, a)
            for e_idx, (ei, ej) in enumerate(edges):
                if (int(ei), int(ej)) == key:
                    total_N += float(q[e_idx]) * float(lengths[e_idx])
                    break
        chord = float(np.linalg.norm(
            coords[chain[-1]] - coords[chain[0]]
        ))
        if chord > 1e-9 and k < len(span_loads_kN_per_m):
            span_loads_kN_per_m[k] = (total_N / 1000.0) / chord

    if float(np.max(span_lengths)) <= 0.0:
        return {
            "model": "continuous beam over all supports, " + base_condition + " ends",
            "status": "no_span",
            "max_moment_kN_m": 0.0,
            "max_shear_kN": 0.0,
            "governing_span": None,
            "spans": [],
        }

    moments, shears, supports_kN = _continuous_beam_three_moment(
        spans_m=span_lengths.tolist(),
        loads_kN_per_m=span_loads_kN_per_m.tolist(),
        end_condition=base_condition,
    )

    max_m = float(np.max(np.abs(moments))) if moments else 0.0
    max_v = float(np.max(np.abs(shears))) if shears else 0.0
    gov_span = None
    if moments:
        gov_span = int(np.argmax(np.abs(moments)))

    model_label = (
        "continuous beam over all supports, %s ends" % base_condition
    )

    return {
        "model": model_label,
        "status": "ok",
        "max_moment_kN_m": max_m,
        "max_shear_kN": max_v,
        "governing_span": gov_span,
        "n_spans": int(len(span_lengths)),
        "span_lengths_m": [float(x) for x in span_lengths.tolist()],
        "span_loads_kN_per_m": [
            float(x) for x in span_loads_kN_per_m.tolist()
        ],
        "support_reactions_kN": [float(x) for x in supports_kN],
        "moments_kN_m": [float(x) for x in moments],
        "shears_kN": [float(x) for x in shears],
    }


def _continuous_beam_three_moment(spans_m, loads_kN_per_m, end_condition="pinned"):
    """Solve a continuous beam with uniform load per span."""
    n = len(spans_m)
    if n == 0:
        return [], [], []

    L = [float(x) for x in spans_m]
    w = [float(x) for x in loads_kN_per_m]

    n_int = n - 1
    A = np.zeros((n_int, n_int), dtype=float)
    b = np.zeros(n_int, dtype=float)

    if end_condition == "fixed":
        M_left_end = - (w[0] * L[0] ** 2) / 12.0
        M_right_end = - (w[-1] * L[-1] ** 2) / 12.0
    else:
        M_left_end = 0.0
        M_right_end = 0.0

    for k in range(n_int):
        L_left = L[k]
        L_right = L[k + 1]
        w_left = w[k]
        w_right = w[k + 1]

        A[k, k] += 2.0 * (L_left + L_right)
        if k > 0:
            A[k, k - 1] += L_left
        if k < n_int - 1:
            A[k, k + 1] += L_right

        rhs = - (w_left * L_left ** 3) / 4.0 - (w_right * L_right ** 3) / 4.0

        if k == 0 and end_condition == "fixed":
            rhs -= M_left_end * L_left
        if k == n_int - 1 and end_condition == "fixed":
            rhs -= M_right_end * L_right

        b[k] = rhs

    if n_int == 0:
        interior_moments = []
    else:
        try:
            interior_moments = np.linalg.solve(A, b).tolist()
        except Exception:
            interior_moments = [0.0] * n_int

    M_supports = [M_left_end] + list(interior_moments) + [M_right_end]

    moments_per_span = []
    shears_per_span = []
    reactions = [0.0] * (n + 1)

    for k in range(n):
        Lk = L[k]
        wk = w[k]
        M_left = M_supports[k]
        M_right = M_supports[k + 1]

        V_left = (wk * Lk / 2.0) + (M_left - M_right) / Lk
        V_right = (wk * Lk / 2.0) - (M_left - M_right) / Lk

        x_zero = V_left / wk if wk > 1e-12 else 0.0
        if x_zero < 0.0:
            x_zero = 0.0
        if x_zero > Lk:
            x_zero = Lk
        M_span = M_left + V_left * x_zero - 0.5 * wk * x_zero ** 2

        moments_per_span.append(abs(float(M_span)))
        shears_per_span.append(max(abs(float(V_left)), abs(float(V_right))))

        reactions[k] += V_left
        reactions[k + 1] += V_right

    return moments_per_span, shears_per_span, reactions


# =============================================================================
# TIE-DOWN
# =============================================================================

def _compute_tiedown_forces(coords, reactions, fixed_indices,
                             anchor_pos, segments, n_boundary):
    """Tie-down axial tension from the support reactions."""
    if reactions is None or fixed_indices is None:
        return {
            "model": "tiedown tension from reaction resolved along cable axis",
            "status": "unavailable",
            "max_kN": 0.0,
            "note": "Solver did not provide reactions.",
            "tiedowns": [],
        }

    reactions = np.asarray(reactions, dtype=float)
    coords = np.asarray(coords, dtype=float)

    n_anchors = int(anchor_pos.shape[0])
    beam_end_nodes = set()
    if n_anchors >= 2:
        beam_end_nodes.add(0)
        beam_end_nodes.add(n_anchors - 1)

    tiedowns = []
    for idx in fixed_indices:
        idx = int(idx)
        if idx in beam_end_nodes:
            continue
        if idx < 0 or idx >= reactions.shape[0]:
            continue

        R = reactions[idx]
        Rmag = float(np.linalg.norm(R))
        if Rmag < 1e-9:
            continue

        p = coords[idx]
        cable_dir = np.array([0.0, 0.0, -1.0])
        if abs(p[2]) > 1e-9:
            cable_dir = np.array([0.0, 0.0, -1.0])

        T = float(np.dot(R, cable_dir))

        tiedowns.append({
            "node_index": int(idx),
            "reaction_x_kN": float(R[0]),
            "reaction_y_kN": float(R[1]),
            "reaction_z_kN": float(R[2]),
            "reaction_mag_kN": float(Rmag),
            "tension_kN": abs(float(T)),
        })

    if not tiedowns:
        return {
            "model": "tiedown tension from reaction resolved along cable axis",
            "status": "no_tiedowns",
            "max_kN": 0.0,
            "min_kN": 0.0,
            "mean_kN": 0.0,
            "n": 0,
            "governing_node": None,
            "tiedowns": [],
        }

    tensions = [t["tension_kN"] for t in tiedowns]
    imax = int(np.argmax(tensions))

    return {
        "model": "tiedown tension from reaction resolved along cable axis",
        "status": "ok",
        "n": len(tiedowns),
        "min_kN":  float(np.min(tensions)),
        "max_kN":  float(np.max(tensions)),
        "mean_kN": float(np.mean(tensions)),
        "governing_node": int(tiedowns[imax]["node_index"]),
        "tiedowns": tiedowns,
    }


# =============================================================================
# SELF-TESTS
# =============================================================================

def _test_membrane():
    q = np.array([2000.0, 3000.0, 4000.0])
    edges = [(0, 1), (1, 2), (2, 3)]
    lengths = np.array([0.5, 0.5, 1.0])
    res = _compute_membrane_forces(q, edges, lengths=lengths)
    ok = (
        abs(res["min_kN"] - 1.0) < 1e-9
        and abs(res["max_kN"] - 4.0) < 1e-9
        and res["governing_edge"] == (2, 3)
    )
    return {"ok": ok, "res": res}


def _test_edge_cable():
    q = np.array([1000.0, 1000.0, 1000.0])
    edges = [(0, 1), (1, 2), (2, 3)]
    segments = [{"anchor_a": 0, "anchor_b": 3, "interior": [1, 2]}]
    res = _compute_edge_cable_forces_from_segments(q, edges, segments)
    ok = (
        res["n_segments"] == 1
        and abs(res["max_kN"] - 3.0) < 1e-9
    )
    return {"ok": ok, "res": res}


def _test_continuous_beam_single_span():
    L = 10.0
    w = 2.0
    moments, shears, reactions = _continuous_beam_three_moment(
        spans_m=[L], loads_kN_per_m=[w], end_condition="pinned",
    )
    expected_M = w * L ** 2 / 8.0
    expected_V = w * L / 2.0
    ok = (
        abs(moments[0] - expected_M) < 1e-6
        and abs(shears[0] - expected_V) < 1e-6
        and abs(reactions[0] - expected_V) < 1e-6
        and abs(reactions[1] - expected_V) < 1e-6
    )
    return {"ok": ok}


def _test_continuous_beam_two_span():
    L = 10.0
    w = 2.0
    moments, shears, reactions = _continuous_beam_three_moment(
        spans_m=[L, L], loads_kN_per_m=[w, w], end_condition="pinned",
    )
    ok = (
        len(moments) == 2
        and moments[0] > 0.0
        and moments[1] > 0.0
        and abs(moments[0] - 9 * w * L ** 2 / 128.0) < 1e-3
    )
    return {"ok": ok}


def _test_continuous_beam_fixed():
    L = 10.0
    w = 2.0
    moments, shears, reactions = _continuous_beam_three_moment(
        spans_m=[L], loads_kN_per_m=[w], end_condition="fixed",
    )
    expected_support = w * L ** 2 / 12.0
    ok = abs(moments[0] - expected_support) < 0.5
    return {"ok": ok}


def _test_design_forces_from_built_minimal():
    coords = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
    ])
    edges = [(0, 1), (1, 2), (2, 3)]
    q = np.array([1000.0, 1000.0, 1000.0])
    boundary_loop = coords.copy()
    anchor_pos = np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
    segments = [{"anchor_a": 0, "anchor_b": 3, "interior": [1, 2]}]
    diagnostics = {
        "reactions": np.array([
            [0.0, 0.0, -1.5],
            [0.0, 0.0,  0.0],
            [0.0, 0.0,  0.0],
            [0.0, 0.0, -1.5],
        ]),
        "fixed_indices": [0, 3],
        "variant_key": "standard_saddle",
    }
    built = {
        "points": coords,
        "edges": edges,
        "triangles": [],
        "q": q,
        "boundary_loop": boundary_loop,
        "anchor_pos": anchor_pos,
        "segments": segments,
        "diagnostics": diagnostics,
    }

    forces = design_forces_from_built(built, code="MY", base_condition="pinned")

    expected_membrane_max = 1.35
    ok = (
        abs(forces["membrane"]["max_kN"] - expected_membrane_max) < 1e-6
        and forces["beam"]["status"] == "ok"
        and forces["base_condition"] == "pinned"
    )
    return {"ok": ok}


def _test_prefers_settled_reactions():
    coords = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
    ])
    edges = [(0, 1), (1, 2), (2, 3)]
    q = np.array([1000.0, 1000.0, 1000.0])
    boundary_loop = coords.copy()
    anchor_pos = np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
    segments = [{"anchor_a": 0, "anchor_b": 3, "interior": [1, 2]}]

    reactions_ff = np.array([
        [0.0, 0.0, -10.0],
        [0.0, 0.0,   0.0],
        [0.0, 0.0,   0.0],
        [0.0, 0.0, -10.0],
    ])
    reactions_settled = np.array([
        [0.0, 0.0, -2.0],
        [0.0, 0.0,  0.0],
        [0.0, 0.0,  0.0],
        [0.0, 0.0, -2.0],
    ])

    diagnostics = {
        "reactions": reactions_ff,
        "settled_reactions": reactions_settled,
        "fixed_indices": [0, 3],
        "variant_key": "standard_saddle",
    }
    built = {
        "points": coords,
        "edges": edges,
        "triangles": [],
        "q": q,
        "boundary_loop": boundary_loop,
        "anchor_pos": anchor_pos,
        "segments": segments,
        "diagnostics": diagnostics,
    }

    forces = design_forces_from_built(built, code="MY", base_condition="pinned")

    tiedown_max = forces["tiedown"]["max_kN"]
    ok = abs(tiedown_max - 2.7) < 1e-6
    return {"ok": ok, "tiedown_max": tiedown_max}


def _test_prefers_settled_q_for_member_forces():
    """
    The membrane, edge cable, and beam should use the settled q
    when it is present, not the form-finding q.
    """
    coords = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
    ])
    edges = [(0, 1), (1, 2), (2, 3)]
    q_ff = np.array([10000.0, 10000.0, 10000.0])
    q_settled = np.array([1000.0, 1000.0, 1000.0])
    boundary_loop = coords.copy()
    anchor_pos = np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
    segments = [{"anchor_a": 0, "anchor_b": 3, "interior": [1, 2]}]

    diagnostics = {
        "reactions": np.array([
            [0.0, 0.0, -1.5],
            [0.0, 0.0,  0.0],
            [0.0, 0.0,  0.0],
            [0.0, 0.0, -1.5],
        ]),
        "fixed_indices": [0, 3],
        "variant_key": "standard_saddle",
    }
    built = {
        "points": coords,
        "edges": edges,
        "triangles": [],
        "q": q_ff,
        "settled_q": q_settled,
        "boundary_loop": boundary_loop,
        "anchor_pos": anchor_pos,
        "segments": segments,
        "diagnostics": diagnostics,
    }

    forces = design_forces_from_built(built, code="MY", base_condition="pinned")

    # With settled q = 1000 N/m, edge length = 1 m, force = 1000 N
    # = 1.0 kN, factored by gamma_G = 1.35 -> 1.35 kN.
    membrane_max = forces["membrane"]["max_kN"]
    ok = abs(membrane_max - 1.35) < 1e-6
    return {"ok": ok, "membrane_max": membrane_max}


def _verify_member_sizing():
    results = {}

    t1 = _test_membrane()
    results["membrane_ok"] = t1["ok"]

    t2 = _test_edge_cable()
    results["edge_cable_ok"] = t2["ok"]

    t3 = _test_continuous_beam_single_span()
    results["beam_single_span_ok"] = t3["ok"]

    t4 = _test_continuous_beam_two_span()
    results["beam_two_span_ok"] = t4["ok"]

    t5 = _test_continuous_beam_fixed()
    results["beam_fixed_ok"] = t5["ok"]

    t6 = _test_design_forces_from_built_minimal()
    results["end_to_end_ok"] = t6["ok"]

    t7 = _test_prefers_settled_reactions()
    results["prefers_settled_reactions_ok"] = t7["ok"]

    t8 = _test_prefers_settled_q_for_member_forces()
    results["prefers_settled_q_ok"] = t8["ok"]

    results["pass"] = all([
        results["membrane_ok"],
        results["edge_cable_ok"],
        results["beam_single_span_ok"],
        results["beam_two_span_ok"],
        results["beam_fixed_ok"],
        results["end_to_end_ok"],
        results["prefers_settled_reactions_ok"],
        results["prefers_settled_q_ok"],
    ])

    return results


if __name__ == "__main__":
    print("engine/member_sizing.py - Member design forces")
    print("-" * 70)

    res = _verify_member_sizing()

    print("Test 1 - Membrane force = q x L")
    print("  membrane_ok              :", res["membrane_ok"])
    print()
    print("Test 2 - Edge cable segment sum")
    print("  edge_cable_ok            :", res["edge_cable_ok"])
    print()
    print("Test 3 - Continuous beam, single span, pinned")
    print("  beam_single_span_ok      :", res["beam_single_span_ok"])
    print()
    print("Test 4 - Continuous beam, two spans, pinned")
    print("  beam_two_span_ok         :", res["beam_two_span_ok"])
    print()
    print("Test 5 - Continuous beam, single span, fixed")
    print("  beam_fixed_ok            :", res["beam_fixed_ok"])
    print()
    print("Test 6 - End-to-end on minimal built dict")
    print("  end_to_end_ok            :", res["end_to_end_ok"])
    print()
    print("Test 7 - Prefers settled_reactions when present")
    print("  prefers_settled_reactions_ok :", res["prefers_settled_reactions_ok"])
    print()
    print("Test 8 - Prefers settled_q for member forces")
    print("  prefers_settled_q_ok     :", res["prefers_settled_q_ok"])
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")


# =============================================================================
# END OF engine/member_sizing.py
# =============================================================================
