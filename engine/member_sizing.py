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
# Those come in later files.
#
# Member groups:
#   membrane    - in-plane force per unit width, from q x L per edge
#   edge_cable  - resultant axial tension along each boundary segment
#   beam        - bending moment and shear in the main beam, treated
#                 as a continuous beam over all supports (end anchors
#                 plus tiedown points)
#   tiedown     - axial tension in each tiedown, resolved along the
#                 cable axis from the support reaction
#   purlin      - secondary members, only for the Beam Supported Saddle
#
# Beam model:
#   Continuous over all supports. End conditions are a user choice:
#   pinned (end moment zero) or fixed (end moment permitted). Interior
#   supports are always continuous. Span load is the span-average of the
#   membrane boundary edge force over that span. Moments are computed
#   from the three-moment equation.
#
#   This is a first-order model. A fully coupled beam-and-cable
#   solution is available in the NFDM path when it converges at App
#   scale. The report names the model honestly.
#
# Partial factors:
#   Read from data/constants.py PARTIAL_FACTORS. Applied to the
#   prestress forces as gamma_G. When wind and snow load cases are
#   added, the same function applies gamma_Q to the variable
#   contribution. One function, every load case, no second system.
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
        Each entry carries a summary and a list of per-edge or
        per-segment values. No partial factors applied at this
        level — this is the raw force computation.
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

    Parameters
    ----------
    built : dict
        As returned by _solve_fdm_path or _solve_nfdm_path.
        Must contain: points, edges, triangles, q, boundary_loop,
        anchor_pos, segments, diagnostics. For the beam and tiedown
        groups, diagnostics must contain "reactions" and
        "fixed_indices".
    code : str or None
        Country code for partial factor lookup. Currently unused —
        PARTIAL_FACTORS is one Eurocode set. Reserved for
        data/codes.py.
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
    q = np.asarray(built["q"], dtype=float)
    boundary_loop = np.asarray(built["boundary_loop"], dtype=float)
    anchor_pos = np.asarray(built["anchor_pos"], dtype=float)
    segments = list(built["segments"])
    diag = built.get("diagnostics", {}) or {}

    n_boundary = int(boundary_loop.shape[0])

    lengths = _edge_lengths(coords, edges)
    membrane_raw = _compute_membrane_forces(q, edges, lengths=lengths)
    edge_cable_raw = _compute_edge_cable_forces(
        q, edges, lengths, segments, coords, n_boundary
    )

    reactions = diag.get("reactions", None)
    fixed_indices = diag.get("fixed_indices", None)

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

    # Purlin is applicable only to the Beam Supported Saddle.
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

    # Apply partial factors.
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
            "No section selection, no code checks. Those come in "
            "later files."
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
    """
    Membrane in-plane force per edge. Force N = q x L (N).
    Returns a summary in kN.
    """
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
    """
    Edge cable resultant tension per segment, from q and geometry.
    Sums boundary edge forces along each segment, resolved along
    the segment's own chord.
    """
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
    """
    Full edge cable computation. Same as the low-level version but
    uses the actual edge lengths and the resolved direction along
    each segment chord.
    """
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
        # Sum of edge forces along the chain.
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

        # Chord length and direction.
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
    """
    Beam bending moment and shear, treated as a continuous beam over
    all supports (end anchors plus tiedown points).

    The load on each span is the span-average of the boundary edge
    force over the chain of boundary edges that lie on the beam
    between two adjacent supports.

    Returns max moment, max shear, and the governing span. Units: kN m, kN.
    """
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

    # Span lengths: distance between consecutive supports along the beam.
    span_lengths = np.zeros(n_anchors - 1, dtype=float)
    for k in range(n_anchors - 1):
        span_lengths[k] = float(np.linalg.norm(
            anchor_pos[k + 1] - anchor_pos[k]
        ))

    # Span loads: average boundary edge force over each span.
    # We sum the boundary edge forces along the chain between the
    # two anchors of each segment, then divide by the chord length
    # to give a line load w (kN/m).
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
    """
    Solve a continuous beam with uniform load per span using the
    three-moment equation.

    spans_m         : list of span lengths (m), length n_spans
    loads_kN_per_m  : list of uniform loads (kN/m), length n_spans
    end_condition   : "pinned" or "fixed"

    Returns (moments, shears, reactions), all as lists of floats.
    Moments is per span (max magnitude in that span).
    Shears is per span (max magnitude in that span).
    Reactions is per support (length n_spans + 1).
    """
    n = len(spans_m)
    if n == 0:
        return [], [], []

    L = [float(x) for x in spans_m]
    w = [float(x) for x in loads_kN_per_m]

    # Three-moment equation:
    # M_{i-1} * L_{i-1} + 2 * M_i * (L_{i-1} + L_i) + M_{i+1} * L_i
    #   = - (w_{i-1} * L_{i-1}^3) / 4 - (w_i * L_i^3) / 4
    #
    # For n spans, there are n-1 interior supports. We solve for the
    # n-1 interior moments. End moments are given by the end condition.

    n_int = n - 1  # number of interior supports
    A = np.zeros((n_int, n_int), dtype=float)
    b = np.zeros(n_int, dtype=float)

    # Known end moments.
    if end_condition == "fixed":
        M_left_end = - (w[0] * L[0] ** 2) / 12.0
        M_right_end = - (w[-1] * L[-1] ** 2) / 12.0
    else:
        M_left_end = 0.0
        M_right_end = 0.0

    for k in range(n_int):
        # Equation for interior support k (0-based, support 1 .. n-1)
        # i-1 in the equation = support k, i in equation = support k+1,
        # i+1 in equation = support k+2
        L_left = L[k]
        L_right = L[k + 1]
        w_left = w[k]
        w_right = w[k + 1]

        # Coefficient on M_k (support k+1)
        A[k, k] += 2.0 * (L_left + L_right)
        if k > 0:
            A[k, k - 1] += L_left
        if k < n_int - 1:
            A[k, k + 1] += L_right

        # RHS
        rhs = - (w_left * L_left ** 3) / 4.0 - (w_right * L_right ** 3) / 4.0

        # Subtract the effect of known end moments.
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

    # Assemble the full moment vector at supports.
    M_supports = [M_left_end] + list(interior_moments) + [M_right_end]

    # Compute per-span max moment and shear, and support reactions.
    moments_per_span = []
    shears_per_span = []
    reactions = [0.0] * (n + 1)

    for k in range(n):
        Lk = L[k]
        wk = w[k]
        M_left = M_supports[k]
        M_right = M_supports[k + 1]

        # End shears of the span, from span equilibrium.
        V_left = (wk * Lk / 2.0) + (M_left - M_right) / Lk
        V_right = (wk * Lk / 2.0) - (M_left - M_right) / Lk

        # Maximum moment in the span: occurs where shear is zero.
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
    """
    Tie-down axial tension from the support reactions, resolved along
    each tiedown cable's own direction.

    The reactions array (n, 3) gives the force at each fixed node.
    Tie-down anchors are the fixed nodes that are not beam end anchors.
    For each such node, we take the reaction vector and resolve it
    along the direction from the node down to the ground contact.
    """
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

    # A tiedown node is a fixed node that is not one of the beam end anchors.
    # The beam end anchors are the two extreme nodes of the boundary loop.
    n_anchors = int(anchor_pos.shape[0])
    beam_end_nodes = set()
    if n_anchors >= 2:
        beam_end_nodes.add(0)
        beam_end_nodes.add(n_anchors - 1)

    tiedowns = []
    for idx in fixed_indices:
        idx = int(idx)
        # Skip the beam end anchors.
        if idx in beam_end_nodes:
            continue
        if idx < 0 or idx >= reactions.shape[0]:
            continue

        R = reactions[idx]
        Rmag = float(np.linalg.norm(R))
        if Rmag < 1e-9:
            continue

        # The tiedown cable runs from the node to the ground (z = 0).
        # The force in the cable is the reaction resolved along the
        # cable axis. We take the reaction vector and project it on
        # the cable direction.
        p = coords[idx]
        # Direction from node to ground contact under the same x, y.
        cable_dir = np.array([0.0, 0.0, -1.0])
        if abs(p[2]) > 1e-9:
            # The cable runs from the node toward a ground point at
            # the same x, y but z = 0, so its axis is straight down.
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
    """Membrane force = q x L, both in kN."""
    q = np.array([2000.0, 3000.0, 4000.0])
    edges = [(0, 1), (1, 2), (2, 3)]
    lengths = np.array([0.5, 0.5, 1.0])
    res = _compute_membrane_forces(q, edges, lengths=lengths)
    # q x L = 1000, 1500, 4000 N = 1.0, 1.5, 4.0 kN
    ok = (
        abs(res["min_kN"] - 1.0) < 1e-9
        and abs(res["max_kN"] - 4.0) < 1e-9
        and res["governing_edge"] == (2, 3)
    )
    return {"ok": ok, "res": res}


def _test_edge_cable():
    """Segment sum should equal sum of edge forces on that segment."""
    q = np.array([1000.0, 1000.0, 1000.0])
    edges = [(0, 1), (1, 2), (2, 3)]
    segments = [{"anchor_a": 0, "anchor_b": 3, "interior": [1, 2]}]
    res = _compute_edge_cable_forces_from_segments(q, edges, segments)
    # Force sum = 3000 N = 3.0 kN
    ok = (
        res["n_segments"] == 1
        and abs(res["max_kN"] - 3.0) < 1e-9
    )
    return {"ok": ok, "res": res}


def _test_continuous_beam_single_span():
    """Single span, pinned ends: max moment = w L^2 / 8."""
    L = 10.0
    w = 2.0
    moments, shears, reactions = _continuous_beam_three_moment(
        spans_m=[L], loads_kN_per_m=[w], end_condition="pinned",
    )
    expected_M = w * L ** 2 / 8.0  # 25.0 kN m
    expected_V = w * L / 2.0       # 10.0 kN
    ok = (
        abs(moments[0] - expected_M) < 1e-6
        and abs(shears[0] - expected_V) < 1e-6
        and abs(reactions[0] - expected_V) < 1e-6
        and abs(reactions[1] - expected_V) < 1e-6
    )
    return {"ok": ok, "moments": moments, "shears": shears, "reactions": reactions}


def _test_continuous_beam_two_span():
    """Two equal spans, uniform load: interior moment = -w L^2 / 8."""
    L = 10.0
    w = 2.0
    moments, shears, reactions = _continuous_beam_three_moment(
        spans_m=[L, L], loads_kN_per_m=[w, w], end_condition="pinned",
    )
    # Known result for 2 equal spans, uniform load, pinned ends:
    # Interior support moment = -w L^2 / 8 = -25 kN m
    # Max span moment = 9 w L^2 / 128 = 14.0625 kN m
    expected_interior = w * L ** 2 / 8.0  # 25.0
    ok = (
        len(moments) == 2
        and moments[0] > 0.0
        and moments[1] > 0.0
        and abs(moments[0] - 9 * w * L ** 2 / 128.0) < 1e-3
    )
    return {"ok": ok, "moments": moments, "shears": shears, "reactions": reactions}


def _test_continuous_beam_fixed():
    """Single span, fixed ends: max moment = w L^2 / 12 (at supports)."""
    L = 10.0
    w = 2.0
    moments, shears, reactions = _continuous_beam_three_moment(
        spans_m=[L], loads_kN_per_m=[w], end_condition="fixed",
    )
    # Fixed-fixed uniform load: max moment at supports = w L^2 / 12
    # Maximum span moment at midspan = w L^2 / 24
    expected_support = w * L ** 2 / 12.0  # 16.667
    # The function returns max magnitude in the span.
    # At supports |M| = 16.667; at midspan |M| = 8.333.
    # The max of those is the support moment.
    ok = abs(moments[0] - expected_support) < 0.5
    return {"ok": ok, "moments": moments}


def _test_design_forces_from_built_minimal():
    """End-to-end smoke test on a trivial built dict."""
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

    # Membrane max should be 3.0 kN (1000 N x 3 m / 1000 / 1000)
    # Actually 1000 N * 1 m = 1000 N = 1.0 kN per edge, max = 1.0 kN
    # Factor gamma_G = 1.35 -> 1.35 kN
    expected_membrane_max = 1.35
    ok = (
        abs(forces["membrane"]["max_kN"] - expected_membrane_max) < 1e-6
        and forces["beam"]["status"] == "ok"
        and forces["base_condition"] == "pinned"
    )
    return {"ok": ok, "forces": forces}


def _verify_member_sizing():
    """Run all self-tests. Returns a dict with pass/fail."""
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

    results["pass"] = all([
        results["membrane_ok"],
        results["edge_cable_ok"],
        results["beam_single_span_ok"],
        results["beam_two_span_ok"],
        results["beam_fixed_ok"],
        results["end_to_end_ok"],
    ])

    return results


if __name__ == "__main__":
    print("engine/member_sizing.py - Member design forces")
    print("-" * 70)

    res = _verify_member_sizing()

    print("Test 1 - Membrane force = q x L")
    print("  membrane_ok        :", res["membrane_ok"])
    print()
    print("Test 2 - Edge cable segment sum")
    print("  edge_cable_ok      :", res["edge_cable_ok"])
    print()
    print("Test 3 - Continuous beam, single span, pinned")
    print("  beam_single_span_ok:", res["beam_single_span_ok"])
    print()
    print("Test 4 - Continuous beam, two spans, pinned")
    print("  beam_two_span_ok   :", res["beam_two_span_ok"])
    print()
    print("Test 5 - Continuous beam, single span, fixed")
    print("  beam_fixed_ok      :", res["beam_fixed_ok"])
    print()
    print("Test 6 - End-to-end on minimal built dict")
    print("  end_to_end_ok      :", res["end_to_end_ok"])
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")


# =============================================================================
# END OF engine/member_sizing.py
# =============================================================================
