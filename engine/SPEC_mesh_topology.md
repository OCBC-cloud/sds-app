# =============================================================================
# SDSe - SPEC: Mesh Topology Engine
# =============================================================================
# Status: DESIGN. Not yet implemented.
# Supersedes: engine/SPEC_mesh_universal.md (which described the
#             earlier fill-strategy approach).
# Author: AI lead, 2026-09-30. Chief's instruction: research-first,
#         industry pattern, AI leads without questions.
# =============================================================================


# 1. THE DECISION

The mesh builder follows the industry pattern that ixForten, EASY,
and the FDM literature all use:

  1. The SOLVER is universal. One kernel. Every shape uses it.
     We have this. engine/form_finding.py::solve_fdm.

  2. The MODEL is universal. Anchors, segments, types, force
     densities. One data model. Every shape describes itself
     with it.

  3. The MESH BUILDER is topology-specific. The professional
     tools offer rectangular meshes for rectangular boundaries,
     radial meshes for circular boundaries, and custom meshes
     for irregular boundaries. They do NOT try to make one fill
     algorithm cover every shape.

The earlier spec (SPEC_mesh_universal.md) described three fill
strategies chosen by name: "tfi", "polar", "barycentric". That
was wrong. It exposed a fill algorithm to the caller, which is a
lower-level concept than the shape's topology. The caller should
declare what the shape IS, not how to fill it.

This spec replaces that design with three topologies.


# 2. THE THREE TOPOLOGIES

Every membrane region the app will ever see falls into one of
three boundary topologies. The engine offers exactly one mesher
per topology.

## 2.1 Topology "twosided"

Boundary: two curves meeting at two shared endpoints.

  - Curve A (bottom): from tip P0 to tip P1.
  - Curve B (top):    from tip P1 back to tip P0.
  - The two tips P0 and P1 are each a SINGLE node, shared by
    both curves. They are not duplicated as columns.

Examples:
  - Standard Saddle (Beam L and Beam R).
  - Beam Supported Saddle.
  - Lens (two curves, two tips).
  - Any two-sided membrane region.

Mesh construction:

  Bilinear blend between the two curves:
      S(u, v) = (1 - v) * A(u) + v * B(u)
  where u is arc fraction along the curve, v is transverse
  fraction from curve A to curve B.

  The tips are single nodes:
      node at u=0, all v = P0    (one node, indexed once)
      node at u=1, all v = P1    (one node, indexed once)

  Internally: nodes at u=0 and u=1 are not duplicated across v.
  The mesh grid is (n_u + 1) x (M - 1) + 2: interior columns
  have M nodes each, and the two tip columns have one node each.

## 2.2 Topology "ring"

Boundary: a single closed curve with no self-touching.

  - One continuous loop of 3D points.
  - The loop does not pass through the same point twice.

Examples:
  - Crown (N lobes, ring perimeter).
  - Dome canopy.
  - Circular ring boundary.

Mesh construction:

  Concentric rings from the boundary inward, collapsing to a
  single centre node. Total nodes: n_i * (M - 1) + 1.

  This is what the current _fill_polar produces. The polar
  fill is correct for ring topologies. It keeps its behaviour.

## 2.3 Topology "quad"

Boundary: four sides, each a curve or a straight line.

  - Side A (bottom): curve or line from corner P00 to P10.
  - Side B (right):  curve or line from corner P10 to P11.
  - Side C (top):    curve or line from corner P11 to P01.
  - Side D (left):   curve or line from corner P01 to P00.
  - The four corners P00, P10, P11, P01 are single nodes.

Examples:
  - Custom boundary from a coordinate file (user-supplied polygon).
  - DXF import with a quadrilateral shape.
  - Rectangular patches inside a larger structure.

Mesh construction:

  Proper Coons patch with Boolean sum correction:

      S(u, v) = (1-v)*A(u) + v*C(u)
              + (1-u)*D(v) + u*B(v)
              - [ (1-u)(1-v)*P00 + u(1-v)*P10
                  + (1-u)v*P01   + uv*P11 ]

  The Boolean sum correction ensures the surface exactly matches
  all four boundary curves.

  This replaces the current _fill_tfi, which is a degenerate
  Coons patch (no correction term). The current version works
  only when all four sides are straight lines. The Coons version
  works for curved sides too.


# 3. WHY THESE THREE, AND ONLY THREE

Any simple closed curve in 3D can be decomposed into:
  - Two curves meeting at two points (twosided).
  - One curve with no self-touching (ring).
  - Four curves meeting at four corners (quad).

Topologies that require more sides (pentagon, hexagon, irregular
N-sided) are decomposed into one of the three. An N-sided region
is a quad with subdivided sides. A multi-panel structure is
multiple regions, each of one of the three types.

We do not need more. If a shape genuinely cannot be decomposed
into these three, it is a compound structure and gets multiple
engine calls, one per region.


# 4. THE ENGINE INTERFACE

The public function becomes:

    build_mesh_universal(topology, curves, corner_points,
                         segment_types, density, q_scalars,
                         **topology_options)

Where:

  topology         : "twosided" | "ring" | "quad"
  curves           : list of curve point arrays, one per side
  corner_points    : list of corner point tuples
  segment_types    : list per segment, for hold rule
  density          : K (subdivisions) and M (transverse count)
  q_scalars        : warp_q, weft_q, edge_q
  topology_options : per-topology extra parameters

Each topology has its own curve list shape:
  - twosided: curves = [curve_A, curve_B]
              corner_points = [P0, P1]
  - ring:     curves = [curve_loop]
              corner_points = []
  - quad:     curves = [A, B, C, D]
              corner_points = [P00, P10, P11, P01]

The function returns the same dict as before:
    points, edges, fixed_indices, q, diagnostics

fixed_indices remain FLAT node indices, ready for solve_fdm.

The diagnostics gain a "topology_used" field.


# 5. NODE TOPOLOGY AT THE TIPS

This is the critical fix. In the twosided topology, the two
tips P0 and P1 are each a SINGLE node in the mesh, not a
column of nodes.

In the earlier design, a closed boundary loop with duplicated
tips produced K nodes at each tip, all at the same point in
space. That is the "degenerate column at the support" that
has plagued the Standard Saddle from the beginning.

The twosided mesher must:
  - Place one node at P0.
  - Place one node at P1.
  - Build interior columns for u in (0, 1) only.
  - Never place a column of coincident nodes at either tip.

Total node count for twosided:
    (K * n_curve - 1) * M + 2   (for M transverse rows)
where n_curve is the number of interior nodes per curve, and
K is the subdivisions per curve segment.

The two "+2" nodes are P0 and P1.





# 6. THE SEGMENT TYPES

The hold rule is unchanged:

  - Anchor (a point where two segments meet): always held.
  - Segment interior, beam or wall: held.
  - Segment interior, cable: released.
  - Mesh interior: always released.

In the twosided topology, the "segments" are the beam segments
along each curve. The anchors are where those segments meet.
The tips P0 and P1 are anchors and are always held.

The current hold rule implementation works for this. No change.


# 7. THE FIXED INDICES

The current engine translates boundary-row indices to flat
node indices. The twosided topology has a different node layout
(tips are single nodes, not columns). The translation must be
aware of the topology.

This is the main implementation complexity. The engine must
produce correct flat node indices for the twosided layout.


# 8. THE VIEWER'S ROLE

The Standard Saddle viewer declares its topology and supplies
the two curves:

    topology = "twosided"
    curve_A  = Beam L points (far tip -> near tip)
    curve_B  = Beam R points (near tip -> far tip)
    corners  = [far_tip, near_tip]

The viewer does NOT build a closed boundary loop with duplicated
tips. It builds two curves and two corner points.

This is the shape-specific part. The viewer knows its shape
is two-sided. The engine knows how to mesh a two-sided region.
The interface between them is the topology declaration.


# 9. THE TEST PLAN

For each topology, one test case in
engine/mesh_universal_test.py:

  - twosided: a saddle boundary (two parabolic curves meeting
    at two tips). Confirm:
      * The two tips are single nodes (not columns).
      * Zero zero-area triangles.
      * Machine-zero residual after solve_fdm.
      * The mesh fills the region between the curves.

  - ring: the existing hexagon polar test. Confirm the fix
    does not break it.

  - quad: a curved-boundary quad (parabolic sides). Confirm:
      * The Coons patch fills correctly.
      * The boundary matches the input curves exactly.
      * The existing straight-line quad test still passes.

All three tests must pass before the engine is called universal.


# 10. WHAT CHANGES IN THE CODEBASE

engine/mesh_universal.py:
  - Public function signature: topology instead of fill.
  - Three internal meshers: _mesh_twosided, _mesh_ring, _mesh_quad.
  - _mesh_ring = current polar fill (kept).
  - _mesh_quad = Coons patch (upgrades current _fill_tfi).
  - _mesh_twosided = new.
  - _build_fixed_indices: unchanged for ring and quad, new logic
    for twosided.
  - q assignment: unchanged in structure, adapted per topology.

engine/mesh_universal_test.py:
  - Add three topology tests.
  - The current four tests remain (they become ring and quad
    tests under the new API).

viewers/figures/standard_saddle_mbs.py:
  - _build_boundary_loop replaced by _build_saddle_curves.
  - Call to build_mesh_universal uses topology="twosided".
  - The tips are single shared points.

engine/SPEC_mesh_universal.md:
  - Superseded by this spec. Marked as historical.

engine/SPEC_mesh_topology.md:
  - This file. The current design.


# 11. MIGRATION ORDER

Step 1: Add this spec (this file). No code change.
Step 2: Rewrite engine/mesh_universal.py. Three meshers.
Step 3: Update engine/mesh_universal_test.py. Three tests.
Step 4: Confirm CI green with the new engine.
Step 5: Update viewers/figures/standard_saddle_mbs.py.
Step 6: Confirm the saddle mesh in the app.

Each step is one commit. Each step is verified by CI before the
next step begins.


# 12. WHAT THIS DESIGN DOES NOT DO

It does not attempt to auto-detect topology from the boundary
points. The caller declares the topology. The engine trusts the
caller. Auto-detection would be fragile, and the caller always
knows which case it is.

It does not attempt to handle N-sided regions directly. Those
are decomposed into quads.

It does not attempt to handle multi-panel structures with a
single call. Each panel is one region, one call.

It does not attempt to handle self-intersecting boundaries.
Those are not physical membranes and are rejected.


# 13. THE HISTORY OF THIS DECISION

2026-09-29: First universal mesh engine built. Three fills:
            tfi, polar, barycentric. Four tests passed.
2026-09-30: The Standard Saddle viewer wired to the engine.
            The mesh collapsed to a thin band. The saddle
            topology was not handled by any of the three fills.
2026-09-30: Chief's instruction: research first. Confirm the
            industry pattern. The industry uses FDM as the
            universal solver, and shape-specific mesh generators.
            Not one fill algorithm for every shape.
2026-09-30: This spec. The engine adopts the industry pattern:
            three topologies, one mesher per topology, solver
            remains universal.


# END OF SPEC





