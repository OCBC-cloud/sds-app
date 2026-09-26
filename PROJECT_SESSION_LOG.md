# SDSe — PROJECT SESSION LOG

The archive. Append only. Never overwritten.

Read this only when tracing a past decision. For the current
state, read PROJECT_STATE.md. For the doctrines, read
PROJECT_CONSTITUTION.md.

Entries are in chronological order. New entries are added at
the bottom.

---

# 2026-09-11 through 2026-09-12 — Phase 1

Project structure created.
CI running on GitHub Actions.
engine/membrane.py Message 1 done.
Self-test passing.

---

# 2026-09-13 through 2026-09-14 — UI flow

UI flow spec defined.
Variant mapping established.
Tie-down rules drafted.
Strut geometry defined.
Structure list reduced to 8 mains.
Studio split into 2 sections.
Registration reads from data/structures.py.
Viewer dispatches on variant_key.
Landing fits one screen.
Foundation Default button (generation counter).
Add. Pay Load replaces Live Load.
Chunked paste method established.
Silent load rules documented.

---

# 2026-09-15 — Saddle Span family complete

Cable Supported Saddle (renamed from Standard Saddle).
Beam Supported Saddle (renamed from Frame Supported
Saddle).
Research-first principle adopted.
Arc length via numerical integration.
Purlin 2.5 m rule locked.
Secondary beam 15 m rule locked.

---

# 2026-09-16 — Spiral engine

engine/leaf_arrangement.py created.
viewers/figures/cantilever_leaf.py rebuilt.
ui/workshops/saddle_leaf.py rebuilt. Five arrangements.

---

# 2026-09-17 — Three bugs closed

Rib override persistence.
leaf_room crash.
Membrane detach on override.
Natural parabolic beam curve.
Strut angle input.
Rules 18-22 documented.
COMMERCIAL_MODEL.md created.

---

# 2026-09-18 — Marketing render built

engine/render_prompts.py created.
ui/results.py rebuilt.
First successful render tested by Chief.
MARKETING_RENDER_WORKFLOW.md created.
PROJECT_STATE.md fully rebuilt.

---

# 2026-09-19 through 2026-09-21 — Cantilever Hypar

New structure built end to end: spec, viewer, workshop,
registration wiring, render branch, MEMBER_SCHEMA entry.

Cantilever family cleaned on Registration: Leaf, and
Variants (routes to Hypar).

Hypar defaults: column height, arm reach, anchor fraction
0.65, rib reach, rib radius 6.0, edge sag 15%.

Render prompts rebuilt: short shape-only prompts,
440-char guard, scenes updated, time-of-day simplified.

engine/PRINCIPLES_membrane.md created.
engine/PLACEHOLDERS.md created.
engine/SPEC_cantilever_hypar.md created.

Results page: viewer strings drawn inside the 3D chart.

PROJECT_STATE_ADDENDUM_2026-09-21.md created.

---

# 2026-09-22 — Cable Supported Saddle viewer FDM migration

The Standard Saddle viewer was upgraded so the membrane
is form-found by solve_fdm.

Segmented Edge mode added: only discrete cable attachment
points are fixed; the fabric edge between them is a chain
of short cable segments.

SIDE_CABLE_STIFFNESS_FACTOR = 6.0 introduced.

First successful engine-driven edge bow.

---

# 2026-09-23 — Full day. Multiple threads.

**Morning:**
engine/form_finding.py full rewrite.
mesh_size_for_shape() added.
mesh_size_for_span() kept as a wrapper.
z-only test gate corrected: constraint is the gate,
not residual.

**Afternoon:**
Repository OCBC-cloud/sds-nfdm-lab created as a research
lab, separate from sds-app.

**Evening:**
engine/nfdm.py written (iterative nonlinear — wrong).
ui/workshops/tester_nfdm.py written.
core/navigation.py gets a tester route.
ui/landing.py gets a tester button.

**Late evening:**
viewers/figures/standard_saddle.py instrumented with
diagnostics.
Fold measured.
Streamlit Cloud throttled the app for exceeding the
free-tier CPU budget — due to the iterative NFDM
kernel.

---

# 2026-09-24 — Corrections and doctrine

**Morning:**
viewers/figures/standard_saddle.py mesh nodes placed by
arc length instead of x. Zero-area triangles persist.
Confirmed the fold is NOT a mesh-along-beam problem.

PROJECT_VISION.md corrected: FDM and NFDM are both
linear; iteration belongs to nonlinear FE. Added
Pauletti 2006 and BATS references.

**Midday:**
Chief states the doctrine of two kinds of constraint —
mesh constraint vs structural connection.

PROJECT_STATE.md rewritten from scratch to consolidate
everything and record the doctrine.

**Late evening:**
engine/membrane_boundary.py written (MBS engine).

run_tests.py gained test_mbs_engine().

First run of the MBS test: n_fixed=2, min_tri_area=0.
Bug identified: fixing boundary indices instead of
mesh node indices.

Fix applied. Second run cancelled by GitHub.

**Night:**
Third MBS test run cancelled by GitHub.
Diagnosis: GitHub infrastructure, not our code.

Plan for the next day: build an in-app MBS tester.

---

# 2026-09-25 — Workflow cleanup and MBS tester

**Morning:**
NFDM tester deleted entirely:
  - ui/workshops/tester_nfdm.py deleted.
  - core/navigation.py — route removed.
  - ui/landing.py — button removed.
  - engine/nfdm.py kept as reference.

run_tests.py — MBS test removed temporarily.
GitHub emails stopped.

MBS tester built:
  - ui/workshops/tester_mbs.py — new file.
  - core/navigation.py — tester_mbs route added.
  - ui/landing.py — "Open MBS Tester" button added.

**First MBS test run (in-app):**
Boundary: 3 m × 3 m square, four corners, all edges
cable.
Result:
  - 81 nodes, 144 edges, 4 fixed, 77 free.
  - min_tri_area = 1.576772e-02.
  - All smallest 10 triangles identical area.
  - FDM residual tiny.

The mesh is valid. The engine works.

The 3D view showed a bow tie. Diagnosis: the boundary
is a square with four points, not a saddle. The engine
built the correct mesh for that input. FDM collapsed
it, as expected. Not a bug. A wrong test.

**Chief identifies the workflow problem:**
Four days of re-finding files. The state file had
grown to 900 lines with three addenda. Unusable.

**Decision:** Split into three files.
  - PROJECT_STATE.md — short, current, 150 lines.
  - PROJECT_CONSTITUTION.md — doctrines, stable.
  - PROJECT_SESSION_LOG.md — this file, append only.

FILE_INVENTORY.md created — every file, one line each,
marked ACTIVE / REFERENCE / DOC.

**Next task:**
Rewrite the MBS Tester to use a diamond boundary with
many points per edge. Then a lens boundary. Then
migrate the Cable Supported Saddle viewer to the MBS
engine.

---

End of PROJECT_SESSION_LOG.md.

New entries are added at the bottom. Nothing is
overwritten.



## 2026-09-26 - Shape-Building Doctrine (Chief's instruction)

### The problem
We need the MBS Tester to be a shape laboratory, not a lens-only
bench. The engine must accept user instructions for any shape
(triangle, square, circle, arbitrary polygon), build the
boundary, mesh it, solve it, and report - using the same nine-
step pipeline as the proven lens test. Only the boundary recipe
changes. The engine does not know shapes.

### Segment count N
The user supplies the number of segments N. N is what the user
says. It is not divided, not multiplied, not reinterpreted.

- A triangle has 3 edges. Each edge is divided into N segments.
- A square has 4 edges. Same rule.
- A circle is treated as a loop. N segments around the whole loop.
- N defaults to 7. The user may enter any N >= 1.

Nodes sit at segment ends. Corners are shared between adjacent
edges. Node counts follow from N and the corner count. They are
not a separate input.

### Mesh density - two modes
A second, independent input controls mesh density. Two modes:

Mode A - Fixed subdivisions per segment (K).
Same K on every shape. Default K = 5. Best for like-for-like
comparison between shapes. This is the current lens behaviour.

Mode B - Target node spacing (ds, in metres).
K is derived per segment from its length:

    K = max(1, round(segment_length / ds) - 1)

Default ds = 0.5 m. Long segments get more nodes automatically.
Best for realistic mesh quality on real structures.

Same mode + same number on every shape = fair comparison.
Different shapes have different edge lengths, so they produce
different node counts. That is correct, not a violation of the
"same parameters" doctrine. The parameters are inputs, not
outputs.

### Focal point (datum)
Every shape has a datum point.

Rule:
- The x-y of the datum is the geometric centroid of the
  boundary nodes.
- The z of the datum is the solved membrane z at that point
  (interpolated from the solved mesh).
- Refinement of this rule (medial axis, curvature centre) is
  deferred until the engine has been proven on multiple shapes.

### Universal engine, many recipes
The engine does not know shapes. It knows:

  - a boundary (closed loop of 3D points),
  - anchor indices,
  - edge types ("beam" or "cable"),
  - optional initial_points (a surface grid).

Everything else is a shape recipe. A recipe produces the tuple
above for one shape and one N. Recipes are added one at a time,
each with the same signature. No engine change per shape.

### Same parameters on all shapes
Same N. Same K (or same ds). Same default prestress. Same
solve. Same diagnostics. Same reaction report. Only the
boundary changes.

### What this means for the Tester
The Tester gains:
  - a shape selector (Lens, Triangle, Square, Circle, ...),
  - a segment count N (default 7),
  - a mesh-density mode selector (Mode A / Mode B),
  - the K value (Mode A) or ds value (Mode B),
  - unchanged tuning windows (Warp, Weft),
  - unchanged disabled toggles (Beam/Cable, Rigid/Flexible),
  - one Run button.

Each shape's recipe is a function with the same signature. The
Tester reads the user's shape choice and calls the right recipe.

### Consequence
If the engine produces a clean, symmetric, machine-zero-residual
saddle for lens, triangle, square, and circle with the same
parameters, then universality is proven - not by argument, but
by the same code running on different boundaries. Then the
engine is ready to be wired into real structures (Cable
Supported Saddle, Beam Supported Saddle, Cantilever Hypar,
Cantilever Leaf), each calling the same engine.

### Stage 2 note
Releasing the beam from rigid to flexible is Stage 2. It needs
beam elements (EA, EI) and a coupled solver. Not in this
session. The reaction report from Stage 1 provides the input
to the Stage 2 beam-stiffness check. Not before.



