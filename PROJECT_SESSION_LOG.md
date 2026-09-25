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





