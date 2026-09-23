# SDSe — Project State Addendum

Date: 2026-09-21.
Covers: 2026-09-19, 2026-09-20, 2026-09-21.

Read this file AFTER:

  - PROJECT_STATE.md       (last updated 2026-09-18)
  - PROJECT_VISION.md      (last updated 2026-09-19)

Those two files are unchanged. This addendum records what has
happened since they were last updated. Together, the three
files give the current picture.

---

## 1. Why an addendum

The main PROJECT_STATE.md and PROJECT_VISION.md contain the
Constitution, the Rules, the Five Systems Architecture, the
Roadmap, and the Vision. They are foundational documents.
They are not to be overwritten lightly.

But three days of work have happened since they were last
updated. Rather than rewrite them (and risk losing their
substance), this addendum sits alongside and records the
changes.

---

## 2. New structure built: Cantilever Hypar

Built end to end on 2026-09-20 and 2026-09-21.

Status: LIVE.

What was built:

  - Spec document: engine/SPEC_cantilever_hypar.md
  - Viewer: viewers/figures/cantilever_hypar.py
  - Workshop: ui/workshops/saddle_hypar.py
  - Registration wiring: data/structures.py + ui/workshop.py
  - Render prompt branch: engine/render_prompts.py
  - MEMBER_SCHEMA entry: data/structures.py

Geometry summary:

  Four membrane corners A, B, C, D.
  A and C are the arm ends. Both at the anchor height.
  B and D are the rib tips. Both higher than A and C.
  The membrane is a saddle bounded by four concave edges.
  The cable follows the same concave curve as the fabric edge.
  The rib is ONE continuous arc through three points:
    left rib tip, arm midpoint, right rib tip.
    Arm midpoint is the LOW point of the arc.
    Rib tips are the HIGH points.

User-adjustable inputs added for Hypar:

  - Column height (m)
  - Arm reach (m)
  - Anchor height fraction (0.55 to 0.80, default 0.65)
  - Rib reach (m)
  - Rib curve radius (m) — default 6.0
  - Membrane edge sag (%) — 0 to 30, default 15

Placeholder inputs (see engine/PLACEHOLDERS.md):

  - Column radius
  - Arm arc radius
  - Rib curve radius (until structural engine lands)
  - Membrane edge sag (until FDM engine lands)

The Hypar reuses the arrangement engine
(engine/leaf_arrangement.py) without change. All five
arrangements work: single, double, multiple, tree_stack,
tiered_helix.

---

## 3. Registration page cleaned up

Change: the Cantilever family on Registration now shows only
two entries.

  - Cantilever Leaf       — Select opens the Leaf workshop.
  - Cantilever Variants   — Select opens the Hypar workshop.
                            (Previously labelled "Cantilever Hypar".)

Removed from Registration (hidden, not shown at all):

  - Cantilever Flower
  - Cantilever Cone
  - Cantilever Pyramid
  - Cantilever Bell
  - Cantilever Sail

These remain in data/structures.py with available=False.
They will be reachable from inside the workshop's Section 1
once that routing is built.

Code change: ui/registration.py now SKIPS variants with
available=False, instead of showing them greyed out.

---

## 4. Render prompt engine rebuilt

Between 2026-09-19 and 2026-09-21, engine/render_prompts.py
went through a full rewrite.

What it is now:

  - Short, shape-only prompt per variant. Live from workshop
    values, not hardcoded.
  - Structure name + shape sentence + lighting + scene.
  - Character guard: prompt capped at 440 chars to stay below
    Bing Image Creator's 480-character limit. Nothing gets
    truncated by the renderer.
  - Each variant has its own shape-writer function.

Scenes:

  Added: Technical (neutral background). Overrides time-of-day
  lighting. Produces a clean product-shot with no scene, no
  people.

  Existing scenes kept: Public Garden, Monumental Square,
  Event Venue, Retail / Cafe, Motorsports Paddock, National
  Day Parade, Chinese Mountain Landscape, Air Force Base.

Time-of-day presets:

  Rewritten as four plain slots:
    Morning, Noon, Evening, Night.

  Replaces the earlier mixed set (Morning, Midday,
  Golden Hour, Evening / Dusk).

Camera and lens specs:

  Removed from all scenes. They are largely ignored by the AI
  and consumed character budget. The AI focuses on the shape.

Known limitation accepted:

  The external renderer does not always reproduce the exact
  structure. When the viewer shape is correct, the render is
  close. Renders are mood images, not engineering documentation.

---

## 5. Results page changed

What changed:

  - The viewer description and the dimensions strings are now
    drawn INSIDE the 3D chart (by viewers/results_viewer.py),
    not as separate HTML below it. They appear as amber
    annotations at the bottom of the plot area, matching the
    legend font size.
  - extract_display_params() removed. It was dumping every
    ws_* key as a junk list.
  - get_structure_summary() removed. Replaced by the
    workshop-written viewer strings.
  - The format_prompt() call now passes a params dict (per
    variant) so the shape sentence is live.

---

## 6. Bugs fixed since 2026-09-18

Bug: Column height showed stale value in the viewer
     dimensions string, and in the prompt.
Cause: Session-state keys were overwritten by widget defaults
       on background reruns when navigating from workshop to
       results.
Fix: Read the WIDGET key first, then fall back to the semantic
     session key. Applied in:
       ui/workshops/saddle_leaf.py
       ui/workshops/saddle_standard.py
       ui/workshops/saddle_frame.py
       ui/workshops/saddle_hypar.py

Bug: Edge cables crossed each other as a bowtie on the Hypar.
Cause: Corner order in the drawing was anchor -> left -> tip ->
       right -> anchor, which crosses itself.
Fix: Reordered to anchor -> tip -> right -> left -> anchor.

Bug: Viewer annotation font was larger than the legend font.
Cause: Annotation size was 13, legend was 8.
Fix: Annotation size reduced to 8.

Bug: Yellow joint marker on the arm cluttered the Hypar viewer.
Fix: Removed entirely. The strut now ends cleanly on the arm.

Bug: User-adjusted rib lengths did not affect the viewer in
     some cases due to widget key persistence.
Fix: Same widget-key-first read.

Bug: The registration page showed unbuilt variants as
     "Coming Soon", cluttering the page.
Fix: ui/registration.py now filters out available=False
     variants entirely.

---

## 7. New documents on file

engine/PRINCIPLES_membrane.md
  The form-finding principle. A SDSe membrane is a tension
  surface, not a draped skin. Touches structure only at its
  support points. Free edges are cable-supported and concave
  inward. Applies to every structure type.

engine/PLACEHOLDERS.md
  Single source of truth for inputs that are placeholders for
  the FDM engine and the structural calculation engine. When
  those engines land, open this file and remove the rows.

engine/SPEC_cantilever_hypar.md
  Full specification of the Hypar variant.

---

## 8. Update to PROJECT_STATE.md §6 (Canonical Data)

The MEMBER_SCHEMA in data/structures.py now includes one new
entry not mentioned in PROJECT_STATE.md:

  ("cantilever", "cantilever_hypar"):
    membrane + column + arm + strut + ribs + perimeter cable

PROJECT_STATE.md §6 should be read as if this row were added.

---

## 9. Update to PROJECT_STATE.md §4 (Structure Types)

Cantilever Hypar should be marked as BUILT, not listed only as
an aspirational variant.

Current live structures:

  - Cable Supported Saddle
  - Beam Supported Saddle
  - Cantilever Leaf
  - Cantilever Hypar

---

## 10. What is pending

Not built yet, kept on file:

  - Cantilever Flower
  - Cantilever Cone
  - Cantilever Pyramid
  - Cantilever Bell
  - Cantilever Sail

All five follow the same build pattern as Hypar:
  spec, viewer, workshop, wiring, render branch.

Section 1 cleanup:
  Inside the workshops, Section 1 (Object Shape) currently
  shows unbuilt variants as "coming soon" options. Cleanup is
  pending: either remove them or make them route to the
  correct workshop.

Saddle viewers:
  Standard Saddle and Beam Supported Saddle viewers are
  currently snapshot-based. To be upgraded to live 3D matching
  the Cantilever viewer pattern.

Results page panels:
  Member Schedule, Anchor Reactions, Foundation panel, Export
  DXF / JSON, Save / Load Design.

T&C gate on landing page:
  Planned. One file (ui/terms.py). Covers no-warranty, user
  responsibility, intellectual property, no reverse-
  engineering, data handling, governing law. Plus MyIPO
  copyright notification advice and NDA caution.

FDM engine and structural engine:
  Every placeholder in engine/PLACEHOLDERS.md is waiting for
  these. When they land, the placeholders are removed and the
  engines supply the values.

---

## 11. What is next

Recommended order for the next session:

  1. Pick one Cantilever variant to build next.
     Candidates: Cone, Pyramid, Bell, Sail, Flower.
     Each is a copy of the Hypar pattern.

  2. Or upgrade the two Saddle viewers to live 3D.

  3. Or add the Results page panels (Member Schedule first).

  4. Or add the T&C gate.

Any of these is a bounded task. The repository is in a clean,
committed, stable state as of this addendum.

---

## 12. The state of the repository

As of 2026-09-21 (evening, Malaysian time):

  - Every changed file is committed.
  - The Streamlit app reboots cleanly.
  - The Registration page is tidy.
  - Cantilever Hypar renders correctly in the external
    AI renderer.
  - No outstanding bugs.

Nothing is broken. Nothing is in flight. The project is ready
for the next session to pick up any of the items above.

---

## 13. The Chief's working method (restated)

  - iPhone, GitHub web editor, Streamlit Cloud.
  - No terminal. No local Python.
  - Chunked paste method for files over 300 lines.
  - Complete file replacements, not surgical edits.
  - Commit between chunks when the editor risks being closed.
  - Reboot the Streamlit app after any commit that changes
    runtime files.
  - Honesty. No fabrication.
  - No going around the world in code.

This is inherited from the main PROJECT_STATE.md. Restated here
so the addendum is self-contained.

---

End of addendum.

# SDSe — PROJECT STATE

Date: 2026-09-23 (evening)
Branch: modular-v10
App URL: sds-modular-preview.streamlit.app (aka ew.streamlit.app)
Status: Working. Stable. One wrong test built. Corrected plan recorded below.

---

# 1. WHAT IS LIVE AND WORKING

Structures with working viewers and workshops:

- Cable Supported Saddle
- Beam Supported Saddle
- Cantilever Leaf
- Cantilever Hypar

Engines:

- engine/form_finding.py — FDM solver. Rewritten today.
- engine/nfdm.py — NFDM kernel. NEW today. Experimental.
- engine/leaf_arrangement.py — unchanged.
- engine/render_prompts.py — unchanged.

Viewers:

- viewers/results_viewer.py — unchanged.
- viewers/figures/standard_saddle.py — unchanged today (touched earlier in the week).

Workshops:

- ui/workshops/saddle_standard.py — unchanged today.
- ui/workshops/tester_nfdm.py — NEW today. Experimental. Reached from landing page button.

UI:

- ui/landing.py — one temporary button added today: "Open NFDM Tester".
- core/navigation.py — one route added today: "tester_nfdm".

---

# 2. WHAT WAS COMMITTED TODAY (2026-09-23)

Morning:
- engine/form_finding.py — full rewrite.
  - mesh_size_for_shape(span_m, n_sides, n_corners) added.
  - mesh_size_for_span(span_m) kept as rectangle wrapper.
  - z-only test gate corrected: constraint is the gate, not residual.

Afternoon:
- Repository OCBC-cloud/sds-nfdm-lab created (research lab, separate).
- engine/nfdm.py written into the lab first.

Evening (in sds-app, on modular-v10):
- engine/nfdm.py — NFDM kernel.
  - triangle_natural_force_densities()
  - ke_from_q()
  - assemble_global_K()
  - solve_nfdm() — Newton-Raphson with backtracking line search.
  - make_flat_grid(), make_reduced_catenoid(), make_settled_hypar().
  - get_catenoid_for_viewer(), get_hypar_for_viewer().
- ui/workshops/tester_nfdm.py — tester page.
- core/navigation.py — tester_nfdm route added.
- ui/landing.py — temporary "Open NFDM Tester" button added.

---

# 3. THE STATE OF THE PROBLEM

## 3.1 The fold is still present

In the shipping Saddle viewer, on the current modular-v10, the
membrane still folds onto itself near the base. Two dark voids
visible in the 3D view.

The fold persists whether the edge-cables toggle is on or off.

This is not solved. It is the original problem from this morning.

## 3.2 The NFDM tester runs, but does not converge

The tester is deployed and reachable. The button works. The
kernel runs. The result, on both benchmarks:

- Reduced catenoid: CHECK. Does not converge. The interior
  collapses into a twisted ribbon instead of forming a saddle.
  reason = max_iter. negative_q large.
- Settled hypar: NOT COMPLETED. Streamlit Cloud throttled the
  app's CPU mid-solve. The kernel did not finish.

## 3.3 Streamlit Cloud throttles iterative solvers

The free tier of Streamlit Cloud has a CPU budget per hour. A
NFDM solve that runs 60-120 Newton iterations with a
576x576 matrix assembly each iteration exceeds that budget.
The app was throttled at ~20:30 on 2026-09-23. Throttle lifts
at 23:32 on the same date.

Implication: NFDM as currently set up cannot run in the free
tier in production. This constrains how NFDM can be used.

---

# 4. THE CORRECTED ARCHITECTURE

The following was agreed between the Chief and the AI on the
evening of 2026-09-23. It supersedes the assumption in the
original handoff that NFDM would form-find the shape.

## 4.1 Two stages, two jobs

STAGE 1 — FORM FINDING (classical FDM)

  Job: produce the settled shape of the membrane.
  Method: solve_fdm — linear, one matrix solve, milliseconds.
  Output: coordinates of the equilibrium shape.
  Properties: taut, smooth, no fold — as proven by the
              shipping Cantilever Hypar viewer.

STAGE 2 — PHYSICS REFINEMENT (NFDM)

  Job: take the FDM shape and compute the real physics.
  Method: subdivide the FDM shape into a triangular mesh,
          apply the biaxial (warp / weft) prestress and
          self-weight, and solve for the stress state.
  Output: the same shape, but with real membrane forces,
          cable forces, and stress resultants — the numbers
          needed for the BoQ.
  Constraint: must be fast enough to run inside the free tier.

## 4.2 What this means for NFDM

NFDM is NOT for forming the shape.

NFDM is for turning an already-settled FDM shape into a
physical membrane model, with real stresses, so that the
BoQ, member sizing, and cable forces can be computed.

## 4.3 What this means for the tester

The tester built today tests the WRONG thing. It asks NFDM to
form-find from a cold start. That is not its job in our design.

The tester must be rebuilt to test the correct pipeline:

  FDM input (span, apex, rise, pretension, self-weight)
       |
       v
  FDM shape (settled, taut, smooth)
       |
       v
  NFDM refinement (triangular mesh, real stresses)
       |
       v
  Coordinates + membrane forces + cable forces

---

# 5. OPEN QUESTIONS

1. Is the fold in the shipping Saddle viewer fixable by
   tuning the FDM mesh and the side-cable stiffness factor
   alone? The Cantilever Hypar suggests yes. This needs to be
   tested before committing to NFDM for the Saddle.

2. What is the minimum NFDM mesh size that runs inside the
   Streamlit Cloud free tier? The current 192-triangle mesh
   is too heavy. A coarser mesh may be enough for the physics.

3. Should warp/weft prestresses be separate inputs, or a
   single biaxial value for now? The shipping Saddle workshop
   currently exposes a single membrane pretension.

4. Should the temporary tester button on the landing page be
   kept until the rebuilt tester is in place? Recommendation:
   yes, keep it, replace the contents of tester_nfdm.py.

---

# 6. WHAT IS NOT DONE

- The NFDM tester has NOT produced a clean converged result.
- The Saddle viewer fold is NOT fixed.
- The FDM → NFDM pipeline is NOT built.
- The BoQ is NOT wired to NFDM.
- The temporary landing-page button is still present.
- The lab repository (sds-nfdm-lab) is orphaned for now; the
  kernel lives in sds-app only.

---

# 7. NEXT SESSION — FIRST STEPS

1. Decide whether the Saddle fold is a mesh-tuning problem
   in FDM, before building anything more on NFDM.
2. If yes: tune the Saddle viewer mesh and the side-cable
   stiffness. Test. Iterate until the fold is gone.
3. If no: rebuild the tester as the correct pipeline —
   FDM shape first, NFDM refinement second. Coarse mesh.
4. Only then: decide whether the BoQ stage reads NFDM output.

---

# 8. DOCTRINES PRESERVED TODAY

- Preservation before evolution: no shipping viewer, workshop,
  or engine file was deleted or repurposed.
- Research first: NFDM was explored in isolation, not in the
  shipping path.
- The membrane is the hero. Steel follows.
- The Chief at the side.
- Language separation: untouched this session.
- Complete files only. No surgical edits to shipping code.

---

# 9. THE CHIEF'S NOTES

Two observations from the Chief, 2026-09-23 evening:

1. The FDM skeleton must come first. NFDM is the refiner,
   not the form-finder.

2. The Cantilever Hypar already produces a smooth taut
   saddle in milliseconds. That is the target. Any method
   that takes minutes is doing the wrong job.

Both are correct. Both are now recorded above.

---

# SDSe — PROJECT STATE

Date: 2026-09-23 (evening, amended)
Branch: modular-v10
App URL: sds-modular-preview.streamlit.app (aka ew.streamlit.app)
Status: Working. Stable. One wrong test built. Corrected plan recorded below.

---

# 1. WHAT IS LIVE AND WORKING

Structures with working viewers and workshops:

- Cable Supported Saddle
- Beam Supported Saddle
- Cantilever Leaf
- Cantilever Hypar

Engines:

- engine/form_finding.py — FDM solver. Rewritten today.
- engine/nfdm.py — NFDM kernel. NEW today. Experimental. Incorrect.
- engine/leaf_arrangement.py — unchanged.
- engine/render_prompts.py — unchanged.

Viewers:

- viewers/results_viewer.py — unchanged.
- viewers/figures/standard_saddle.py — unchanged today.

Workshops:

- ui/workshops/saddle_standard.py — unchanged today.
- ui/workshops/tester_nfdm.py — NEW today. Experimental.

UI:

- ui/landing.py — one temporary button: "Open NFDM Tester".
- core/navigation.py — one route: "tester_nfdm".

---

# 2. WHAT WAS COMMITTED TODAY (2026-09-23)

Morning:
- engine/form_finding.py — full rewrite.
  - mesh_size_for_shape(span_m, n_sides, n_corners) added.
  - mesh_size_for_span(span_m) kept as rectangle wrapper.
  - z-only test gate corrected.

Afternoon:
- Repository OCBC-cloud/sds-nfdm-lab created (research lab).

Evening (in sds-app, on modular-v10):
- engine/nfdm.py — NFDM kernel. Iterative. Wrong. See Section 10.
- ui/workshops/tester_nfdm.py — tester page.
- core/navigation.py — tester_nfdm route added.
- ui/landing.py — temporary "Open NFDM Tester" button added.

---

# 3. THE STATE OF THE PROBLEM

## 3.1 The fold is still present

In the shipping Saddle viewer, on the current modular-v10, the
membrane still folds onto itself near the base. Two dark voids
visible in the 3D view.

The fold persists whether the edge-cables toggle is on or off.

This is not solved. It is the original problem from this morning.

## 3.2 The NFDM tester runs, but does not converge

The tester is deployed. The button works. The kernel runs. The
result, on both benchmarks:

- Reduced catenoid: CHECK. Does not converge. Interior collapses
  into a twisted ribbon. reason = max_iter. negative_q large.
- Settled hypar: NOT COMPLETED. Streamlit Cloud throttled CPU.

## 3.3 Streamlit Cloud throttled the app

At ~20:30 on 2026-09-23, Streamlit Cloud reduced the app's CPU
because the kernel exceeded the free tier's per-hour budget.
Throttle lifts at 23:32 on the same date.

At the time, this appeared to mean NFDM cannot run in the free
tier. Section 10 corrects that reading.

---

# 4. THE CORRECTED ARCHITECTURE

Agreed between the Chief and the AI, evening of 2026-09-23.
Supersedes the handoff assumption that NFDM would form-find.

## 4.1 Two stages, two jobs

STAGE 1 — FORM FINDING (classical FDM)

  Job: settle the shape of the membrane.
  Method: solve_fdm — linear, one matrix solve, milliseconds.
  Output: coordinates of the equilibrium shape.
  Properties: taut, smooth, no fold.

STAGE 2 — PHYSICS REFINEMENT (NFDM)

  Job: take the FDM shape and compute the real physics.
  Method: subdivide into triangles, apply biaxial prestress
          and self-weight, solve for the stress state.
  Output: same shape, with membrane forces and stress resultants.

## 4.2 What this means for NFDM

NFDM is NOT for forming the shape.

NFDM is for turning an already-settled FDM shape into a
physical membrane model, for the BoQ and member sizing.

## 4.3 What this means for the tester

The tester built today tests the WRONG thing. It asks NFDM to
form-find from a cold start. It must be rebuilt as:

  FDM input (span, apex, rise, pretension, self-weight)
       |
       v
  FDM shape (settled, taut, smooth)
       |
       v
  NFDM refinement (triangular mesh, real stresses)
       |
       v
  Coordinates + membrane forces + cable forces

---

# 5. OPEN QUESTIONS

1. Is the fold in the shipping Saddle viewer fixable by tuning
   the FDM mesh and side-cable stiffness alone? The Cantilever
   Hypar suggests yes. Test before committing to NFDM.

2. What is the minimum NFDM mesh size that runs cleanly and
   quickly? Depends on Section 10 rewrite.

3. Warp and weft pretenses: separate inputs, or single biaxial
   value for now? The Saddle workshop currently exposes one.

4. Keep the temporary landing-page tester button? Recommendation:
   keep until the rebuilt tester is in place.

---

# 6. WHAT IS NOT DONE

- The NFDM tester has NOT produced a clean result.
- The Saddle viewer fold is NOT fixed.
- The FDM → NFDM pipeline is NOT built.
- BoQ is NOT wired to NFDM.
- The temporary landing-page button is present.
- The lab repository (sds-nfdm-lab) is orphaned.

---

# 7. NEXT SESSION — FIRST STEPS

1. Read Section 10 first. It changes what NFDM is.
2. Decide: is the Saddle fold a mesh-tuning problem in FDM?
   If yes, tune the mesh and side-cable stiffness first.
3. Replace solve_nfdm with the published linear formulation.
4. Rebuild the tester as FDM-shape → NFDM-refinement.
5. Only then: decide whether BoQ reads NFDM output.

---

# 8. DOCTRINES PRESERVED TODAY

- Preservation before evolution.
- Research first.
- The membrane is the hero. Steel follows.
- The Chief at the side.
- Language separation: untouched.
- Complete files only. No surgical edits to shipping code.

---

# 9. THE CHIEF'S NOTES

Two observations from the Chief, 2026-09-23 evening:

1. The FDM skeleton must come first. NFDM is the refiner,
   not the form-finder.

2. The Cantilever Hypar already produces a smooth taut
   saddle in milliseconds. That is the target. Any method
   that takes minutes is doing the wrong job.

Both are correct. Both are now recorded above.

---

# 10. THE CRITICAL CORRECTION — NFDM IS LINEAR

Amended 2026-09-23, evening. Based on a search of the actual
professional tools and papers.

## 10.1 What the professional tools do

ixCube 4-10:
  Uses BOTH FDM and NFDM. FDM first for the cable network.
  NFDM for the membrane refinement. Not from a cold start.

Easy (Technet GmbH):
  Uses FDM alone for form-finding. The Easy.Form page states:
  "The force density method guarantees a linear calculation
  without approximate values. Our algorithms are optimized
  and guarantee a fast calculation, even for very large
  structures." Nonlinear FE is used only for load analysis
  afterward.

BATS (University of São Paulo):
  Uses FDM for cables, NFDM for membranes. The authors report
  "gains in performance compared to other available tools,
  due to the linear nature of FDM and NFDM, as well as the
  use of optimized linear solvers."

## 10.2 The finding

FDM and NFDM are BOTH essentially LINEAR methods. Each is a
matrix solve, not an iterative nonlinear solver.

## 10.3 Our mistake

engine/nfdm.py, as built today, runs Newton-Raphson with a
line search. That is an ITERATIVE NONLINEAR solver. That is
not what published NFDM is.

That is why it is slow. That is why it did not converge. That
is why Streamlit Cloud throttled us.

The published NFDM is a LINEAR method. One solve, not 120.

## 10.4 What this means for mobile hosting

Once solve_nfdm is rewritten as the published LINEAR
formulation:

- FDM: milliseconds. Runs on a phone.
- NFDM: seconds at most. Runs on a phone.
- Nonlinear FE (load analysis): heavy. Runs on a server only.

The mobile hosting question is not a hardware question. It is
an algorithm question. Once the algorithm is correct, mobile
hosting is not a problem.

## 10.5 Next step, concretely

Replace solve_nfdm with the published linear formulation.

Read: Pauletti, R. M. O. — Natural Force Density Method.
Read: BATS implementation notes from the Pauletti group.
Then rewrite engine/nfdm.py.

Only then does the FDM → NFDM pipeline make sense.

---

# 11. WHAT WE NOW KNOW ABOUT MEMBRANE FORM-FINDING, IN ONE PAGE

For the next session and for any future reader:

1. A membrane is a tension surface. It is not draped.

2. FDM forms the shape. FDM is linear. FDM is fast.

3. NFDM refines the shape into a physical membrane model.
   NFDM is also linear. NFDM is also fast.

4. Nonlinear FE is for load analysis only. It does not
   belong on the critical path for shape. It does not
   belong on a phone.

5. Professional software uses exactly this pipeline.
   ixCube. Easy. BATS. All the same.

6. Mobile hosting is possible because FDM and NFDM are
   linear. The heavy work — nonlinear FE — is deferred
   to the server, or to a paid compute tier.

7. Our task is not to invent this. Our task is to
   implement it correctly, small, and honest.

---

End of document.










