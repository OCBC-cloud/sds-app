# SDSe — PROJECT STATE

Short. The state, right now. Read this first.
Then read PROJECT_CONSTITUTION.md for the doctrines.
Then read PROJECT_VISION.md for the destination.
Then read FILE_INVENTORY.md for what exists.

Last updated: 2026-09-29.
Branch: modular-v10.
App URL: sds-modular-preview.streamlit.app.

---

# 1. WHAT IS LIVE

Four structures, each with a workshop and a viewer:

- Cable Supported Saddle     — FDM form-found. Has a fold.
- Beam Supported Saddle      — drawn surface. No FDM. No fold.
- Cantilever Leaf            — drawn. Uses leaf_arrangement.
- Cantilever Hypar           — drawn Coons patch. No FDM.

The app is deployed. The user flow is:
Landing -> Studio -> Registration -> Workshop -> Results.

The Landing page has two buttons:
  Enter The Studio
  Open MBS Tester (experimental)

An additional hidden test route exists:
  renderer_test  — reached by ?page=renderer_test or the
  temporary button. For testing the universal workshop
  renderer.

---

# 2. THE UNIVERSAL MESH ENGINE (NEW 2026-09-29)

`engine/mesh_universal.py`. Built. Tested. Proven.

Input:
  - boundary_loop  — a closed loop of 3D anchors.
  - segment_types  — one per gap: "beam", "cable", "wall".
  - fill           — "tfi", "polar", "barycentric".
  - subdivisions_per_segment (K).
  - transverse_count (M).
  - warp_q, weft_q, edge_q.

Output:
  - points, edges, fixed_indices, q, diagnostics.

The hold rule:
  Anchor                  -> always held.
  Segment interior, beam  -> held.
  Segment interior, wall  -> held.
  Segment interior, cable -> released.
  Mesh interior           -> always released.

Test results (CI, 2026-09-29):
  Flat quad, all beam        - zero=0  minArea=3.15e-05
  Flat quad, all cable       - zero=0  minArea=1.93e-06
  Mixed: 2 beam, 2 cable     - zero=0  minArea=6.11e-06
  Hexagon, polar fill        - zero=0  minArea=9.21e-05
  ALL TESTS PASS

This is the engine that will kill the fold in every shape.
It is NOT yet wired into any viewer. That is Step 2D.

---

# 3. THE UNIVERSAL WORKSHOP RENDERER (NEW 2026-09-29)

`ui/workshops/_renderer.py`. Built. Committed.

Reads a workshop recipe. Builds the input page.
Accordion groups. Five input types. No sliders.
Preview, warning, info boxes. Action buttons.

Tested via `ui/workshops/_renderer_test.py` — a temporary
test page. Once the first real workshop migrates, the test
page is removed.

The Standard Saddle workshop is the first migration.
`ui/workshops/saddle_standard.py` is now 12 lines.
The recipe is `data/recipes/standard_saddle.py`.

---

# 4. THE FOLD IN THE CABLE SADDLE VIEWER

Two zero-area triangles in the old mesh at the supports.

Cause (final diagnosis): the old viewer built a rectangular
grid with a support column. The column is degenerate — all
its nodes are at the same point. A bow hack hid the
degeneracy but did not fix it.

The correct fix: build the mesh from a boundary loop.
Anchors along the beams. No column at the support. The
support is a point, not a column.

`engine/mesh_universal.py` implements the correct model.
Step 2D wires it into the viewer.

---

# 5. WHAT IS NEXT

## 5.1 Immediate (Step 2D)

Rewrite `viewers/figures/standard_saddle_mbs.py` to call
`build_mesh_universal`.

The viewer:
  - Builds the boundary loop: 7 anchors on each beam
    (14 total), at equal arc length.
  - Segment types: all 14 are "beam".
  - Calls build_mesh_universal with fill="tfi".
  - Calls solve_fdm on the result.
  - Draws the mesh, beams, tie-downs, supports.

The fold dies when this happens.

## 5.2 Next (Step 2E)

Update `data/recipes/standard_saddle.py`. The Shape group
gains three inputs:
  - Anchor count per beam (default 7).
  - Target mesh spacing (m) (default 0.5).
  - Transverse count (default 8).

The recipe converts spacing to K before calling the
engine. K = max(5, round(segment_length / spacing)).

## 5.3 After that

  - Beam Supported Saddle migrates.
  - Coordinate file path (custom_boundary).
  - DXF path (custom_boundary).
  - Crown, Triangle, Lens migrate.

---

# 6. WORKFLOW

Every session starts by reading, in order:

  1. PROJECT_STATE.md            (this file — 3 minutes)
  2. PROJECT_CONSTITUTION.md     (the doctrines — when deciding)
  3. PROJECT_VISION.md           (the destination — when planning)
  4. FILE_INVENTORY.md           (what exists — when coding)

The session log lives in PROJECT_SESSION_LOG.md. Read it only
when tracing a past decision.

Every commit that adds, renames, or deletes a file also
updates FILE_INVENTORY.md.

Every major decision is recorded in PROJECT_SESSION_LOG.md,
appended, not overwritten.

---

# 7. THE CHIEF

See PROJECT_CONSTITUTION.md, Part V for the Chief's working
method and the Chief's heritage.

---

End of PROJECT_STATE.md.


