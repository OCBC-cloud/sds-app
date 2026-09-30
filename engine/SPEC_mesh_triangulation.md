# =============================================================================
# SDSe - SPEC: Triangulated Mesh Engine
# =============================================================================
# Status: DESIGN. Supersedes engine/SPEC_mesh_topology.md.
# Author: AI lead, 2026-09-30.
# =============================================================================


# 1. THE DECISION

The universal mesh method is CONSTRAINED DELAUNAY
TRIANGULATION of the boundary loop.

Not rectangular grids. Not polar rings. Not Coons
patches. Not three separate topologies with three
separate meshers.

One method. Every shape.

The triangle is the universal shape. Any polygon can
be triangulated. Any boundary can be triangulated.
Any point singularity is closed by triangulation.
Any curve is respected by triangulation.

The rectangle is a convenience. The polar ring is a
convenience. The Coons patch is a convenience. None
of them is the universal method. Triangulation is.

This is what the professional membrane tools do:
CAD boundary -> constrained triangulation -> lift
to 3D -> FDM. One pipeline. Every shape.


# 2. WHY THE STRUCTURED METHODS WERE WRONG AS THE
#    UNIVERSAL METHOD

The earlier design (SPEC_mesh_topology.md) proposed
three topologies:

  twosided  - two curves, two shared tips.
  ring      - one closed curve, rings to centre.
  quad      - four sides, Coons patch.

Each was a structured mesh. Each had its own node
layout, its own edge rules, its own triangle rules,
its own singularity handling.

This is three special cases, not a universal method.
Every new shape required either extending one of the
three, or adding a fourth topology.

Examples of the failure:

  - A pointed-rounded shape (one point face, one
    curve face) needed degenerate-side handling in
    the quad mesher. New code for one shape.

  - A saddle needed tip fans. New code for one shape.

  - The apex of a parabola needed finer spacing
    where the curve bends. Structured meshers place
    anchors uniformly along arc length; they cannot
    refine locally without user intervention.

A universal method does not need new code for each
new boundary. Triangulation does not. The three
structured methods do.

They were the wrong starting point. This spec
replaces them.


# 3. THE METHOD

## 3.1 Input

A closed boundary loop. Any shape.

  - An ordered list of 3D boundary points, forming a
    closed loop. The first point is also the last
    (implicitly). The loop may have any number of
    points.

  - Optional: anchor indices. Points where two
    segments meet. Always held in the FDM solve.

  - Optional: segment types. One per segment between
    consecutive anchors. Values: "beam", "cable",
    "wall".

  - Optional: a target edge length for the interior
    mesh. Default: mean boundary segment length.

  - Optional: a plan-view plane. Default: the best
    fit plane through the boundary, or the XY plane
    if the boundary is horizontal.

## 3.2 Triangulation in the plan view

Project the boundary onto the plan plane. The
projection is a closed 2D polygon.

Construct a constrained Delaunay triangulation of
the polygon's interior, with the polygon edges as
constraints.

The triangulation respects every boundary edge. No
triangle crosses the boundary. The interior fills
with triangles whose edge lengths approximate the
target edge length.

## 3.3 Lift to 3D

The triangulation is a 2D mesh. Each node has a
plan position (x, y). The 3D z of each node is
needed.

Boundary nodes: their z is already known from the
input boundary points.

Interior nodes: z is interpolated from the boundary
via a smooth lift. The simplest correct lift is the
Coons patch (used only for z, not for x-y). Other
lifts are possible; the Coons lift is the default
because it is exact on the boundary and smooth
inside.

The result is a 3D triangulated mesh: points, edges,
triangles.

## 3.4 Singularities

A point singularity is any boundary location where
the loop passes through the same point twice, or
where the boundary curvature is unbounded (a tip).

In the triangulation, a point singularity is a
boundary vertex. Triangles connect to it naturally.
No special handling. No fan. No degenerate column.
The triangulation closes the surface automatically.

## 3.5 Refinement

The user controls the mesh density via the target
edge length. Smaller target = finer mesh.

Optionally: local refinement near curvature. Where
the boundary curves sharply, the triangulation can
place smaller triangles. This is automatic when the
Delaunay algorithm includes a size field.

For the first implementation: uniform target edge
length. Local refinement is a later addition.


# 4. THE ENGINE INTERFACE

The public function:

    build_mesh_triangulated(
        boundary_loop,           # (n, 3) array
        anchor_indices,          # list of int, or None
        segment_types,           # list of str, or None
        target_edge_length,      # float, or None
        plan_plane,              # (normal, point) or None
        warp_q, weft_q, edge_q,  # floats, for q assignment
    )

Returns:

    dict with keys:
        points          (n_nodes, 3) array
        edges           list of (i, j) tuples
        triangles       list of (a, b, c) tuples
        fixed_indices   list of int, FLAT node indices
        q               (n_edges,) array
        diagnostics     dict

Every shape uses this one function. No topology
parameter. No fill parameter. Just: boundary in,
triangulated mesh out.


# 5. THE HOLD RULE

Unchanged from before.

  Anchor (a point where two segments meet): held.
  Segment interior, beam:                  held.
  Segment interior, wall:                  held.
  Segment interior, cable:                 released.
  Interior mesh nodes:                     released.

Boundary nodes are held or released by segment type.
Interior nodes are always released.

The FDM solver (solve_fdm) is unchanged. It takes
points, edges, fixed_indices, q. Triangulation
produces all four.


# 6. THE FORCE DENSITIES

Per-edge q, assigned by segment type on the boundary
and by warp/weft on the interior.

  Boundary edge on a beam segment:  q = warp_q
  Boundary edge on a wall segment:  q = warp_q
  Boundary edge on a cable segment: q = edge_q
  Interior edge, all segments:      q = weft_q

The exact interior warp/weft distinction (edges
aligned with the warp direction vs the weft
direction) is not well-defined for an unstructured
mesh. The first implementation uses weft_q for all
interior edges. A refinement in a later version may
classify interior edges by their direction relative
to a reference axis.

This is a known simplification. It is recorded here
so it is not mistaken for a complete treatment.


# 7. WHAT THIS REPLACES

The three structured topologies (twosided, ring,
quad) are superseded.

engine/mesh_universal.py:
  - Rewritten to a single triangulation builder.
  - No _mesh_twosided, _mesh_ring, _mesh_quad.
  - One function: build_mesh_triangulated.

engine/mesh_universal_test.py:
  - Rewritten for the single method.
  - Test cases:
      * a saddle boundary (two curves, two tips),
      * a hexagon ring,
      * a pointed-rounded shape,
      * an irregular polygon,
      * a curved quad.
    Same engine call for each. Different boundary.

viewers/figures/standard_saddle_mbs.py:
  - Rewritten to call build_mesh_triangulated.
  - The viewer draws triangles from result["triangles"].
  - The viewer does not build any mesh logic itself.

engine/SPEC_mesh_topology.md:
  - Marked as superseded.
  - Kept for history.


# 8. THE TEST PLAN

One test function. Multiple boundary inputs.

For each boundary input:
  - Build the mesh with build_mesh_triangulated.
  - Confirm: no triangle crosses the boundary.
  - Confirm: no zero-area triangles.
  - Confirm: the fixed_indices are correct.
  - Solve with solve_fdm.
  - Confirm: machine-zero residual.
  - Confirm: the mesh fills the region.

The boundary inputs:
  - Saddle: two parabolic curves, two tips.
  - Ring: hexagon.
  - Pointed-rounded: one point, one parabolic curve.
  - Irregular: an arbitrary polygon with 10 vertices.
  - Curved quad: four parabolic sides.

Every one of these uses the same function. The
distinguishing feature is only the boundary input.

If any boundary fails, the method fails. Fix the
method, not the boundary.


# 9. THE MIGRATION

Step 1: Write this spec (this file).
Step 2: Add the triangulation engine.
Step 3: Rewrite the test.
Step 4: Confirm CI green.
Step 5: Rewrite the viewer.
Step 6: Confirm the saddle mesh in the app.
Step 7: Migrate the Tester to the same engine.

Each step is one commit. Each verified by CI before
the next step begins.


# 10. DEPENDENCIES
NOTE (2026-09-30, later the same day):
The `triangle` package cannot be built on Streamlit Cloud.
The installer fails with a non-zero exit code. The primary
dependency is now `scipy.spatial.Delaunay`, which is already
installed via scipy (a Streamlit Cloud base package).

The `triangle` option below is NOT used. It is kept for
historical record only.
Constrained Delaunay triangulation has a standard
Python implementation: `triangle` (a wrapper around
Jonathan Shewchuk's Triangle library).

  pip install triangle

It is well-tested, fast, and used by the scientific
Python community. It handles constrained edges, size
fields, and refinement.

The alternative is to implement the algorithm from
scratch. That is a project of its own, and not
necessary. Use `triangle`.

If `triangle` cannot be installed on Streamlit
Cloud, the fallback is the pure-Python
`scipy.spatial.Delaunay` plus a boundary-edge
correction pass. This is slower and less robust.
The `triangle` package is the primary choice.


# 11. WHAT THIS DESIGN DOES NOT DO

It does not attempt to handle non-planar boundaries
by triangulating in 3D directly. It projects to a
plan plane, triangulates, and lifts back. This is
correct for boundaries that do not fold over
themselves in plan view. For boundaries that do,
a different method is needed. Not in this spec.

It does not attempt to handle self-intersecting
boundaries. Those are not physical membranes.

It does not attempt to handle multiple regions
joined at shared edges. Each region is a separate
call. Joining is a later feature.

It does not provide local refinement in the first
implementation. Uniform target edge length only.


# 12. THE PRINCIPLE

One method. Every shape.

The boundary is the input. The triangulation is the
output. The solver is unchanged. The viewer is
unchanged.

Every future shape is a new boundary. Not a new
method.

Every shape. One method.


# END OF SPEC





# =============================================================================
# APPENDIX A - THE PUBLIC FUNCTION IN DETAIL
# =============================================================================

def build_mesh_triangulated(
    boundary_loop,
    anchor_indices=None,
    segment_types=None,
    target_edge_length=None,
    plan_plane=None,
    warp_q=2000.0,
    weft_q=2000.0,
    edge_q=5000.0,
):
    """
    Build a triangulated mesh from a closed boundary loop.

    Parameters
    ----------
    boundary_loop : (n, 3) array
        Ordered boundary points forming a closed loop.
        The loop is closed by convention: the last point
        connects back to the first. Do not duplicate the
        first point at the end.

    anchor_indices : list of int, or None
        Indices into boundary_loop. Points where two
        segments meet. Always held in the FDM solve.
        If None, every boundary point is treated as
        part of one continuous segment of type "cable".

    segment_types : list of str, or None
        One per segment between consecutive anchors.
        Length must equal len(anchor_indices) if anchors
        are given, or len(boundary_loop) if the whole
        loop is one segment chain.
        Values: "beam", "cable", "wall".
        If None, all segments are "cable".

    target_edge_length : float, or None
        Approximate edge length for the interior mesh.
        If None, uses the mean length of the boundary
        segments.

    plan_plane : ((3,) normal, (3,) point), or None
        The plane onto which the boundary is projected
        for 2D triangulation. If None, uses the XY
        plane (normal = [0, 0, 1], point = [0, 0, 0]).

    warp_q : float
        Force density along beam and wall segments.
        Applied to boundary edges on those segments.

    weft_q : float
        Force density for the interior mesh.
        Applied to all interior edges.

    edge_q : float
        Force density along cable segments.
        Applied to boundary edges on those segments.

    Returns
    -------
    dict:
        points          (n_nodes, 3) array
        edges           list of (i, j) tuples
        triangles       list of (a, b, c) tuples
        fixed_indices   list of int, FLAT node indices
        q               (n_edges,) array
        diagnostics     dict
    """


# =============================================================================
# APPENDIX B - THE NODE AND EDGE CONTRACT
# =============================================================================

The mesh returned is a standard triangle mesh.

  - points: every node in the mesh. Boundary nodes
    come first (in the order of the boundary loop),
    then interior nodes added by the triangulation.

  - edges: every unique edge in the mesh. Each edge
    appears once. Boundary edges and interior edges
    are both listed. Edge (i, j) with i < j is the
    canonical form.

  - triangles: every triangle. Each is (a, b, c) in
    counter-clockwise order when viewed from the
    plan direction.

  - fixed_indices: FLAT node indices. Ready for
    solve_fdm. Boundary nodes on beam or wall
    segments are fixed. Boundary nodes on cable
    segments are released except at anchors.
    Interior nodes are always released.

  - q: one value per edge. Assigned by the rule in
    section 6.

  - diagnostics: counts, flags, and audit trail.


# =============================================================================
# APPENDIX C - THE LIFT FROM 2D TO 3D
# =============================================================================

The triangulation produces a 2D mesh in the plan
plane. Each node has (u, v) in that plane.

To produce 3D coordinates:

  1. Boundary nodes: use their original (x, y, z)
     from the input boundary_loop.

  2. Interior nodes: their (x, y) is the plan
     position projected back to world coordinates.
     Their z is interpolated from the boundary.

The interpolation of interior z:

  - Simplest: bilinear over a bounding rectangle.
    Fast, but not exact at curved boundaries.

  - Better: Coons patch over the boundary. Used
    here. Exact at the boundary edges, smooth
    inside. Requires decomposing the boundary into
    four sides or approximating it as such.

  - Simplest correct: use the mean z of the boundary
    nodes for all interior nodes. Wrong for any
    curved surface, but trivially correct for a
    flat boundary.

For the first implementation, use the Coons lift
for boundaries that decompose into four sides (or
fewer, with degenerate sides). For other boundaries,
use the mean-z fallback.

The choice is recorded in diagnostics["lift_used"].

A refinement for a later version: solve a Laplace
equation for interior z with the boundary z as the
boundary condition. That is the mathematically
optimal smooth lift. It is more expensive but exact.


# =============================================================================
# APPENDIX D - THE CALL SEQUENCE
# =============================================================================

Inside build_mesh_triangulated:

  1. Validate inputs:
       - boundary_loop is (n, 3), n >= 3.
       - anchor_indices, if given, are valid indices.
       - segment_types, if given, matches the expected
         length.

  2. Determine the plan plane. If plan_plane is None,
     use the XY plane. The XY plane is the correct
     choice for a horizontal boundary. For a vertical
     or tilted boundary, the caller must supply the
     plane.

  3. Project the boundary onto the plan plane,
     producing a 2D polygon.

  4. Call the constrained Delaunay triangulator.
     Input: the 2D polygon, and the target edge
     length. Output: 2D triangles and interior nodes.

  5. Merge the input boundary nodes (already 3D) with
     the interior nodes (2D + interpolated z).

  6. Build the edges list. Every edge that appears in
     any triangle is unique.

  7. Assign q per edge, by the rule in section 6.

  8. Compute fixed_indices by the hold rule.

  9. Assemble the diagnostics dict.

  10. Return the dict.

The result is a fully-formed mesh, ready for
solve_fdm.





# =============================================================================
# APPENDIX E - MIGRATION AND CLEANUP
# =============================================================================
#
# This is the list of files to add, rewrite, mark
# superseded, or delete when the triangulation engine
# is built.
#
# Files are grouped by action. Do the actions in order.
#

# -----------------------------------------------------------------------------
# E1. FILES TO ADD
# -----------------------------------------------------------------------------
#
# engine/mesh_triangulated.py
#     The new universal mesh engine. Contains
#     build_mesh_triangulated and its helpers.
#     Replaces engine/mesh_universal.py.
#
# engine/mesh_triangulated_test.py
#     The test for the new engine. Uses the boundary
#     inputs listed in section 8.
#
# These are the only two new files. Everything else is
# rewrite, supersede, or delete.

# -----------------------------------------------------------------------------
# E2. FILES TO REWRITE
# -----------------------------------------------------------------------------
#
# engine/mesh_universal.py
#     REWRITE. Replaced by engine/mesh_triangulated.py.
#     Option A: delete it entirely and update imports.
#     Option B: keep it, but as a thin shim that calls
#     the new engine, so old callers still work during
#     the migration.
#     Recommendation: Option A. Delete. Update imports.
#
# engine/mesh_universal_test.py
#     DELETE. Replaced by mesh_triangulated_test.py.
#
# viewers/figures/standard_saddle_mbs.py
#     REWRITE. Remove _build_saddle_curves (the two-
#     curve model). Replace with a single
#     build_boundary_loop call. Remove _grid_to_triangles.
#     Remove _compute_K (the engine chooses density now).
#     Draw triangles from result["triangles"].
#     The viewer becomes thin. About 200 lines.
#
# run_tests.py
#     REWRITE the entry for mesh_universal_test.
#     Point it at mesh_triangulated_test.
#     One line change.

# -----------------------------------------------------------------------------
# E3. FILES TO MARK SUPERSEDED (KEEP FOR HISTORY)
# -----------------------------------------------------------------------------
#
# engine/SPEC_mesh_topology.md
#     MARK SUPERSEDED at the top. Add a note:
#       "Superseded by engine/SPEC_mesh_triangulation.md
#        on 2026-09-30."
#     Do not delete. The history matters.
#
# engine/SPEC_mesh_universal.md
#     MARK SUPERSEDED. Already superseded once by
#     SPEC_mesh_topology.md. Now superseded again.
#     Add a second note with the new date.
#     Do not delete.
#
# engine/membrane_boundary.py
#     MARK AS LEGACY at the top. It is the old MBS
#     engine, still used by the Tester. Leave it
#     working. Mark it legacy. Plan to migrate the
#     Tester later.
#
# engine/membrane_surface.py
#     MARK AS LEGACY. Same as above.

# -----------------------------------------------------------------------------
# E4. FILES TO DELETE
# -----------------------------------------------------------------------------
#
# engine/mesh_universal.py
#     DELETE after the new engine is built and tested.
#     Not before. The old engine is the fallback until
#     the new one passes its tests.
#
# engine/mesh_universal_test.py
#     DELETE at the same time.
#
# No other deletions. Everything else is in active
# use or being marked for history.

# -----------------------------------------------------------------------------
# E5. FILES THAT ARE NOT TOUCHED
# -----------------------------------------------------------------------------
#
# engine/form_finding.py
#     UNCHANGED. solve_fdm is universal. The new engine
#     calls it the same way.
#
# engine/membrane.py
#     UNCHANGED.
#
# engine/leaf_arrangement.py
#     UNCHANGED.
#
# engine/render_prompts.py
#     UNCHANGED.
#
# viewers/figures/_shared.py
#     UNCHANGED.
#
# viewers/figures/standard_saddle.py
#     UNCHANGED. It is the old viewer. Kept as fallback.
#
# viewers/results_viewer.py
#     UNCHANGED. Already dispatches to
#     standard_saddle_mbs.
#
# ui/workshops/saddle_standard.py
#     UNCHANGED.
#
# data/recipes/standard_saddle.py
#     TO BE UPDATED in Step 2E (separate task). Not
#     part of this migration.
#
# ui/workshops/tester_mbs.py
#     UNCHANGED for now. Migrates to the new engine
#     in a later session.

# -----------------------------------------------------------------------------
# E6. THE ORDER OF WORK
# -----------------------------------------------------------------------------
#
# Step 1: This spec. (DONE.)
#
# Step 2: Add engine/mesh_triangulated.py.
#         The new universal engine.
#         Commit alone. CI must stay green.
#
# Step 3: Add engine/mesh_triangulated_test.py.
#         Point run_tests.py at it. Comment out or
#         delete the mesh_universal_test entry.
#         Commit. CI must pass the new test.
#
# Step 4: Rewrite viewers/figures/standard_saddle_mbs.py
#         to call the new engine. Commit. CI green.
#         Reboot the app. Verify the saddle mesh fills.
#
# Step 5: Delete engine/mesh_universal.py and
#         engine/mesh_universal_test.py.
#         Update any remaining imports.
#         Commit. CI green.
#
# Step 6: Mark the superseded specs.
#         engine/SPEC_mesh_topology.md
#         engine/SPEC_mesh_universal.md
#         Add the superseded note at the top of each.
#         Commit.
#
# Step 7: Update PROJECT_STATE.md and
#         PROJECT_SESSION_LOG.md and FILE_INVENTORY.md
#         to reflect the new architecture.
#         Commit.

# -----------------------------------------------------------------------------
# E7. WHY THE OLD ENGINE IS KEPT UNTIL STEP 5
# -----------------------------------------------------------------------------
#
# The old mesh_universal.py works for the ring and
# quad cases. It produces correct meshes for those.
# We do not want to lose that until the new engine
# is proven to handle them equally well.
#
# The new engine must pass all five boundary tests
# before the old engine is deleted:
#
#   saddle, ring, pointed-rounded, irregular,
#   curved quad.
#
# If any of the five fails, the old engine stays,
# and we fix the new one until all five pass.

# -----------------------------------------------------------------------------
# E8. SUMMARY
# -----------------------------------------------------------------------------
#
# 2 files added.
# 4 files rewritten (mesh_universal, mesh_universal_test,
#   standard_saddle_mbs, run_tests).
# 4 files marked superseded/legacy.
# 2 files deleted (after the new engine is proven).
# 11 files untouched.
#
# Total: 12 files touched. 11 files not touched.
#
# The result: one universal mesh engine. Every shape.
# One method.

# END OF SPEC





