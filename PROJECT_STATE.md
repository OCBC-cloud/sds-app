# SDSe — PROJECT STATE

Short. The state, right now. Read this first.
Then read PROJECT_CONSTITUTION.md for the doctrines.
Then read PROJECT_VISION.md for the destination.
Then read FILE_INVENTORY.md for what exists.

Last updated: 2026-09-25.
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

The Landing page currently has two buttons:
  Enter The Studio
  Open MBS Tester (experimental)

## 1.1 The MBS Tester (shape laboratory)

`ui/workshops/tester_mbs.py` is a shape laboratory, not a lens tester.
It proves the MBS engine works on any shape.

Three shapes are implemented:
  - Lens     - two beam curves meeting at two tips.
  - Triangle - three corners, three edges, user-editable xyz.
  - Crown    - N parabolic beams on an imaginary ground circle,
               with a single membrane inside. Centre solved by FDM.

Each shape is a recipe. Each recipe returns the same tuple
(grid, boundary, anchor_indices, edge_types). The engine does
not know what a "lens" or a "crown" is. It knows boundaries,
anchors, edge types, and an optional initial grid.

Status as of 2026-09-26: three shapes, all clean, all machine-
zero residual. The engine is universal. The recipe pattern is
proven.

---

# 2. THE FOLD IN THE CABLE SADDLE VIEWER

This is the top visible problem. It has been diagnosed.

## 2.1 What it is

Two zero-area triangles in the initial mesh, at the middle
of each free end:

  nodes (11, 35, 12)   and   (563, 564, 540)

They are at (i=0, j=11/12) and (i=23, j=11/12).
They are NOT at the beam corners.

## 2.2 Why

The free-end column of the mesh is a straight line with no
bow. The membrane's free edge has no shape of its own.
FDM then drags the free-end middle nodes 3 m upward.

The real structure has an EDGE CABLE along each free end,
bowing inward. It is not in the mesh. It is only drawn on
top of the result.

## 2.3 What was tried and did not work

- Arc-length mesh along the beam (2026-09-24 morning).
  Did not fix. Retained — harmless.
- Fix B — hold the free-end middle nodes.
  Did not fix. The degenerate triangles exist in the
  initial mesh, before solve_fdm. Retained as a mesh
  constraint.
- Fix C — z proportional to beam height.
  Made it worse. Reverted.

## 2.4 What the correct fix is

Fix D. Give the free-end cable its own chain of nodes,
bowing inward. Not drawn on top — in the mesh.

But we have since built a better engine for this. See § 3.

---

# 3. THE MBS ENGINE

`engine/membrane_boundary.py`. New. Under test.

## 3.1 What it does

Builds a triangular mesh for a membrane from:
  - a closed boundary (an ordered loop of 3D points),
  - anchor indices (which points are held),
  - edge types ("beam" or "cable").

It calls Transfinite Interpolation (TFI) to fill the
interior, and returns a mesh ready for solve_fdm.

## 3.2 What has been tested

The MBS Tester page (ui/workshops/tester_mbs.py) runs the
engine on a 3 m × 3 m boundary with four corners, all
edges "cable".

Result:
  - 81 nodes, 144 edges, 4 fixed, 77 free.
  - Every triangle has positive area.
  - The smallest 10 triangles all have area 1.576772e-02.
  - FDM residual is tiny.

The MESH IS VALID. The engine builds a proper mesh.

## 3.3 What went wrong on the visual

The 3D view showed a bow tie, not a saddle. The mesh
collapsed at two opposite edges.

## 3.4 Why

The boundary passed to the engine was a SQUARE with four
corners. Not a saddle. Not even a diamond. The four
corners are at the four points of a square, with alternating
z-heights.

The engine has only four points on the boundary. Between
them, it can only draw straight chords. FDM pulls the
chords inward. The result is the bow tie.

This is the correct result for that input. It is not a
bug in the engine. It is a wrong test.

## 3.5 What the correct test is

A saddle boundary with MANY points per edge:
  - four corners at alternating z-heights,
  - each edge subdivided into N points,
  - anchors at the corners, and optionally along the edges,
  - edge types set as required.

Then MBS builds the mesh, FDM solves it, and we see a
saddle.

The tester must be rewritten with a proper boundary.

---

# 4. WHAT IS NEXT

## 4.1 Immediate

Rewrite the MBS Tester to use a diamond boundary with many
points per edge. Then a lens boundary. Then apply the
engine to the Cable Supported Saddle viewer.

## 4.2 After that

- Migrate Beam Supported Saddle viewer to MBS + FDM.
- Migrate Cantilever Hypar viewer to MBS + FDM.
- Migrate Cantilever Leaf viewer to MBS + FDM.
- Rewrite engine/nfdm.py as a linear solve (see the
  constitution and the vision — the current version is an
  iterative nonlinear solver, which is the wrong method).

## 4.3 Long term

The BoQ, member sizing, and nonlinear FE stages are not
built. They are the eventual destination.

---

# 5. WORKFLOW

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

# 6. THE CHIEF

See PROJECT_CONSTITUTION.md, Part V for the Chief's working
method and the Chief's heritage.

---

End of PROJECT_STATE.md.
