# SDSe — PROJECT STATE

Short. The state, right now. Read this first.
Then read PROJECT_CONSTITUTION.md for the doctrines.
Then read PROJECT_VISION.md for the destination.
Then read FILE_INVENTORY.md for what exists.

Last updated: 2026-09-30 (evening).
Branch: modular-v10.
App URL: sds-modular-preview.streamlit.app.

---

# 1. WHAT IS LIVE

Four structures, each with a workshop and a viewer:

- Cable Supported Saddle     - FDM form-found. Uses the
                               triangulated mesh engine.
- Beam Supported Saddle      - drawn surface. No FDM.
- Cantilever Leaf            - drawn. Uses leaf_arrangement.
- Cantilever Hypar           - drawn Coons patch. No FDM.

The app is deployed. The user flow is:
Landing -> Studio -> Registration -> Workshop -> Results.

The Landing page has three buttons:
  Enter The Studio
  Open MBS Tester (experimental)
  Open Renderer Test (temporary test page)

---

# 2. THE UNIVERSAL MESH ENGINE - ARCHITECTURE 2026-09-30

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

# 3. THE UNIVERSAL WORKSHOP RENDERER

`ui/workshops/_renderer.py`. Built. Committed.

Reads a workshop recipe. Builds the input page.
Accordion groups. Five input types. No sliders.
Preview, warning, info boxes. Action buttons.

The Standard Saddle workshop is the first migration.
`ui/workshops/saddle_standard.py` is 12 lines.
The recipe is `data/recipes/standard_saddle.py`.

The recipe has NOT yet gained the three Shape inputs
(anchor_count, mesh_spacing, transverse_count). That is a
pending task. See Section 5.

---

# 4. THE MESH MIGRATION - WHERE WE ARE

## Done

Step 1: SPEC_mesh_triangulation.md written and committed.
Step 2: engine/mesh_triangulated.py built and committed.
Step 3: engine/mesh_triangulated_test.py built, run_tests.py
        pointed at it, CI green. All five cases pass.
Step 5: viewers/figures/standard_saddle_mbs.py rewritten
        to use the triangulated engine. Committed.

## Not yet done

Step 5 verification: the app has NOT yet been opened with
the new viewer. That is the FIRST ACTION of the next
session.

Step 6: delete engine/mesh_universal.py and its test.
Step 7: mark SPEC_mesh_topology.md and SPEC_mesh_universal.md
        as superseded.
FILE_INVENTORY.md update to reflect the new engine.

---

# 5. THE IMMEDIATE NEXT STEP

**Verify Step 5 in the app.**

1. Reboot the Streamlit app (Rule 13).
2. Open the Standard Saddle results page.
3. Screenshot the 3D view and the diagnostics expander.
4. Confirm: the membrane fills the saddle, no tip gap,
   the apex is covered by triangles, machine-zero residual.
5. If it works: proceed to Step 6 (delete the old engine).
6. If it does not work: diagnose from the traceback.

After Step 5 verification:

## Pending - Step 2E (deferred from earlier)

Update `data/recipes/standard_saddle.py`. The Shape group
gains three inputs:
  - Anchor count per beam (default 15).
  - Target mesh spacing (m) (default 0.5).
  - Transverse count (default 8).

These feed the triangulated engine's target_edge_length
and boundary density.

---

# 6. WORKFLOW

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

---

# 7. THE CHIEF

See PROJECT_CONSTITUTION.md, Part V for the Chief's working
method and the Chief's heritage.

---

# 8. THE LESSON OF 2026-09-30

The Chief asked a direct architectural question: why not
triangulate every shape the same way.

The AI resisted. The AI proposed structured methods,
three topologies, Coons patches, tip fans. Each was a
special case dressed up as a universal method.

The Chief was right from the first question.

**When the Chief raises an architectural question, the
Chief has usually already seen the answer. Listen first.
Confirm second. Propose third.**

---

End of PROJECT_STATE.md.
