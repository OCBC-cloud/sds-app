# SDSe — PROJECT STATE

Short. The state, right now. Read this first.
Then read PROJECT_CONSTITUTION.md for the doctrines.
Then read PROJECT_VISION.md for the destination.
Then read FILE_INVENTORY.md for what exists.

Last updated: 2026-10-06.
Branch: modular-v10.
App URL: sds-modular-preview.streamlit.app.

---

# 1. WHAT IS LIVE

Four structures, each with a workshop and a viewer:

- Cable Supported Saddle     - FDM form-found. Triangulated engine. Anisotropic FDM. Responds to warp/weft.
- Beam Supported Saddle      - drawn surface. No FDM.
- Cantilever Leaf            - drawn. Uses leaf_arrangement.
- Cantilever Hypar           - drawn Coons patch. No FDM.

The app is deployed. The user flow is:
Landing -> Studio -> Registration -> Workshop -> Results.

The Landing page has two active buttons:
  Enter The Studio
  Open MBS Tester (experimental)

A third button, "Open Renderer Test", is present but
is being retired. It is a temporary test page that
is no longer needed.

---

# 2. THE UNIVERSAL MESH ENGINE

**The universal mesh method is CONSTRAINED DELAUNAY
TRIANGULATION of the boundary loop.**

One method. Every shape.

The triangle is the universal shape. Any polygon can be
triangulated. Any boundary can be triangulated. Any point
singularity (a saddle tip, a ring centre) closes by
triangulation. Any curve is respected.

The design is in `engine/SPEC_mesh_triangulation.md`.

## The engine

`engine/mesh_triangulated.py`. Built. Tested. In use.

The public function is `build_mesh_triangulated`. It takes
a closed boundary loop, projects to a plan plane, runs
`scipy.spatial.Delaunay`, filters to the polygon interior,
lifts the interior nodes to 3D, and returns:

    points, edges, triangles, fixed_indices, q, diagnostics

The solver (`solve_fdm`) is unchanged. It has always been
universal.

## The dependency

`scipy.spatial.Delaunay`. scipy is in `requirements.txt`.

The `triangle` package was tried first and could not be
built on Streamlit Cloud. scipy replaced it.

## The test

`engine/mesh_triangulated_test.py`. Five boundary inputs:

  - saddle (two parabolic curves, two tips)
  - hexagon
  - pointed_rounded (one tip, one curved face)
  - irregular (10-vertex polygon)
  - curved_quad (four parabolic sides)

CI result: PASS. Zero zero-area triangles and machine-zero
FDM residuals across all five cases.

## What this supersedes

The earlier design (`engine/SPEC_mesh_topology.md`) proposed
three structured topologies:

  twosided  - two curves, two shared tips.
  ring      - one closed curve, rings to centre.
  quad      - four sides, Coons patch.

Those were three special cases. They are superseded. Kept
for history only.

The earlier engine (`engine/mesh_universal.py`, the three
structured meshers) is still live as a fallback. It is
not used by the viewer. It will be deleted in Step 6 of
the migration.

---

# 3. THE FORM-FINDER — ANISOTROPIC FDM

The Laplace lift was retired on 2026-10-01. It was
isotropic by construction. It could not respond to
warp/weft pretension. It has been replaced by the
Force Density Method with a per-edge anisotropic q.

The chain inside `build_mesh_triangulated`:

  4. Assemble points.
  5. Edges.
  6. Fixed indices.
  7. Anisotropic q (from `assign_anisotropic_q`).
  8. FDM solve (`solve_fdm`).
  9. Diagnostics.

The anisotropic rule:

    q_edge = warp_q * cos^2(theta)
           + weft_q * sin^2(theta)

where theta is the angle between the edge and the
warp direction in the plan plane. The warp direction
is auto-detected from the bounding box long axis.
Optionally rotatable later.

The three functions live in `engine/form_finding.py`:

    assign_anisotropic_q
    auto_warp_dir
    rotate_warp_dir

The solver `solve_fdm` is unchanged. It always
accepted a per-edge q array. The missing piece was
building the anisotropic array upstream. That piece
is now built and wired. Verified in the app on
2026-10-01: three different warp/weft settings
produce three visibly different saddle shapes.

The Standard Saddle pretension inputs, after today:

    Warp Pretension (kN/m)      default 1.0   range 0.1 - 100.0
    Weft Pretension (kN/m)      default 1.0   range 0.1 - 100.0
    Edge Cable Pretension (kN)  default 5.0   range 0.1 - 500.0

DEFAULTS and `_preview_pretension` are kept in step.

Published practice for a stadium-scale roof places
warp/weft pretension in the 3 - 6 kN/m band, edge
cable 30 - 150 kN. The app exposes the range so the
engineer can explore.

---

# 4. THE UNIVERSAL WORKSHOP RENDERER

`ui/workshops/_renderer.py`. Built. Committed.

Reads a workshop recipe. Builds the input page.
Accordion groups. Five input types. No sliders.
Preview, warning, info boxes. Action buttons.

The Standard Saddle workshop is the first migration.
`ui/workshops/saddle_standard.py` is 12 lines.
The recipe is `data/recipes/standard_saddle.py`.

The recipe has NOT yet gained the three Shape inputs
(anchor_count, mesh_spacing, transverse_count). That is a
pending task. See Section 7.

---

# 5. THE NONLINEAR SOLVER (NFDM) — STATUS

`engine/nonlinear_equilibrium.py` at v5.3. CI green.
Four self-tests pass. Physics verified.

The App case (468 nodes) does not converge in the
25-second wall-clock budget. This is a performance
issue, not a physics issue. The solver is correct.

The path forward:
- Warm start from the FDM result.
- Sparse assembly and sparse solve (in progress).
- Reduce element re-evaluation across line-search trials.
- Defer full App-scale convergence to the next optimisation phase.

---

# 6. THE MESH MIGRATION — DONE

## Completed

Step 1: SPEC_mesh_triangulation.md written. Committed.
Step 2: engine/mesh_triangulated.py built. Committed.
Step 3: engine/mesh_triangulated_test.py built. CI green.
        All five boundary cases pass.
Step 4: (merged into Step 2.)
Step 5: viewers/figures/standard_saddle_mbs.py rewritten
        to use the triangulated engine. Committed and
        verified in the app.

## Bugs fixed

2026-10-01
  1. Paste corruption in _triangulate_polygon, at lines
     317 and 323. Two surgical line replacements.
  2. KD-tree overrun in _laplace_lift for meshes with
     fewer than 9 points. Fixed by clamping
     k = min(8, n_nodes - 1).

2026-10-03
  1. engine/nfdm_tension_field_test.py was empty. The
     six tests were rewritten. All pass.
  2. run_tests.py __main__ guard was inside main().
     Dedented to module level. Tests now execute.
  3. Test 2 principal check was wrong. Asserted
     s[1] < 0 on a test where s[1] is exactly 0. Fixed.

2026-10-06
  1. Ten sequential versions of nonlinear_equilibrium.py
     (v4.2 to v5.3) corrected tangent signs, residual
     convention, outer-loop logic, line search, sparse
     assembly, and test criteria.
  2. FDM path threshold: pull-back < 1.0 N treated as
     numerical zero, falls back to edge_q_scalar.
  3. Mode selector: high tiers may choose FDM or NFDM.
  4. Auto-scaled edge cable pretension: recipe default
     is 0.0 (auto), viewer computes N_membrane * L_anchor.

## Still to do

Step 6: Delete engine/mesh_universal.py and its test.
Step 7: Mark SPEC_mesh_topology.md and
        SPEC_mesh_universal.md as superseded.
FILE_INVENTORY.md update to reflect the new engine.
HANDOVER_2026-10-01 deletion.

---

# 7. THE IMMEDIATE NEXT STEP

Three tasks remain. In order.

  1. Step 2E. Expose three Shape inputs in
     data/recipes/standard_saddle.py:

       anchor_count        default 15
       mesh_spacing        default 0.5
       transverse_count    default 8

     Required to make Cable Supported do something.
     Half a day. Requires a design decision on how
     anchor_count interacts with the loop size, and
     how _build_boundary_loop is reworked.

  2. The wrapper design conversation for
     solve_nfdm_tension_field. Not code. Design.

     The handover's proposed wrapper (call solve_nfdm,
     project outside, re-solve) is wrong. The
     projection must fire inside the element routine.
     That makes it Level 2 work, not a wrapper.

  3. FILE_INVENTORY.md rewrite and DIRECTORY_MAP.md
     creation. Both deferred until Step 2E is done,
     so the rewrite is done once and reflects the
     final state.

Then Stage 2 — NFDM, in the tension-field form.

---

# 8. WORKFLOW

Every session starts by reading, in order:

  1. PROJECT_STATE.md            (this file - 3 minutes)
  2. PROJECT_CONSTITUTION.md     (the doctrines - when deciding)
  3. PROJECT_VISION.md           (the destination - when planning)
  4. FILE_INVENTORY.md           (what exists - when coding)

The session log lives in PROJECT_SESSION_LOG.md. Read the
last three entries first.

Every commit that adds, renames, or deletes a file also
updates FILE_INVENTORY.md.

Every major decision is recorded in PROJECT_SESSION_LOG.md,
appended, not overwritten.

Files written for GitHub follow Rule 22 — one file, one
block, one copy. See PROJECT_CONSTITUTION.md.

---

# 9. THE CHIEF

See PROJECT_CONSTITUTION.md, Part VI for the Chief's working
method and the Chief's heritage.

---

End of PROJECT_STATE.md.
