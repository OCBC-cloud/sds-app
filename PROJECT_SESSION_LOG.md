# SDSe — PROJECT SESSION LOG

The archive. Append only. Never overwritten.

Read this only when tracing a past decision. For the current
state, read PROJECT_STATE.md. For the doctrines, read
PROJECT_CONSTITUTION.md.

Entries are in chronological order. New entries are added at
the bottom.

---

## Cumulative Doctrine (distilled from all prior sessions)

The following are the hard-won lessons. They are not repeated in every entry below. They are the reason every session now begins the same way.

1.  **Read the code, not the handover.** Handovers describe intent, not state. Three handovers in a row claimed things were working that were not. Always open the file, compile it, and read the last known-good commit before acting.
2.  **The CI is the only truth.** A test suite that runs in under a second is not running. A real suite takes real time. A green checkmark with 0 tests is worse than a red failure.
3.  **The Chief's instinct is correct.** When the Chief raises an architectural question, the Chief has usually already seen the answer. Listen first. Confirm second. Propose third.
4.  **The writer is responsible for the format.** Long paste failures are caused by nested code fences and split messages, not by size. Rule 22 governs the delivery format.
5.  **One file, one block, one copy.** The rule. The doctrine. The law.
6.  **Draw from the settled, not the source.** Every attached element (edge cable, anchors, rings) must be drawn from the solved coordinates, never the static inputs. Rule 23.
7.  **The FDM is the starting point. The NFDM is the refinement.** Both are linear. Nonlinear FE is a different, heavier, server-side tool.
8.  **The bow is the physics.** When the boundary cable is free between anchors, the membrane pulls it inward. That inward curve is the loop. It is not a bug.

---

## 2026-10-06 (evening) — The FDM-to-NFDM architecture, and the record

**Branch:** modular-v10
**CI status at close:** green (`engine/nonlinear_equilibrium.py` v5.3)
**App status at close:** FDM path produces a bowed shape. NFDM path still does not converge at App scale.

### Why this entry exists

Last night produced ten versions of the nonlinear solver (v4.2 through v5.3). It ended with the physics correct, CI green on the four self-tests, but the App case (468 nodes) still not converging: 9 iterations, residual 5.4e3, wall-clock guard fired at 25 seconds. The physics is settled. The App case is too heavy for the current linear algebra on the free tier. This is now an optimisation problem, not a physics problem.

Mid-way through the night the Chief described the architecture he had in mind — the architecture he was working toward with the previous room before that room was lost. This entry records that architecture, the eight pieces that implement it, and the record-keeping that will carry it forward.

### Part 1 — The architecture, in the Chief's words

> "You see earlier with the other room. The edges
> did form loops but edge cable was not there.
> Can you find out why the loops formed back then?"

> "One thing even the result obtains from FDM, all
> floating points of the membrane must be freed
> again before firing the NFDM."

> "For cable supported edge all points except the
> anchor points at the anchors must be freed
> before FDM or NFDM working. Then only can get
> the bow loops."

> "When drawing the cables it must be from anchor
> point to each and every triangular beam facing
> lines or segments then anchor; the line is not
> a straight line from anchor to anchor."

> "When user input a new prestress value to
> replace the previous value the worked out shape
> and form of the saddle must be cached first as
> the starting of the new NFDM iteration starting
> point so that the whole thing don't have to
> start from scratch again."

> "We should retain the caches of the worked out
> shape and forms and the sets of data. So that
> user with a click of the previous or forward
> button can instantly recall the worked out
> model without reworking again."

> "By itself the files also store valuable
> information."

### Part 2 — The architecture, restated

The membrane is prestressed and wants to shrink.
Wherever the boundary is not held, it bows inward.
Where it is held — only at the anchors — it stays.
Between two anchors the boundary settles into
whatever curve the membrane's inward pull
produces. That curve is the loop.

The FDM finds that settled shape with only the
anchors fixed. It gives the position of every node
and the force in every edge. That is the initial
form-found membrane.

After that, a cable is drawn along the boundary
loop, following every mesh boundary edge, node by
node, anchor to anchor. Not a straight line. A
polyline through the mesh boundary. Each short
cable segment carries the force the FDM boundary
edge was already carrying.

The NFDM then takes over. All points except the
anchors stay free. The membrane and the cable are
both real. The solver adjusts the shape for the
coupled interaction. The user changes the edge
cable pretension and the loop responds.

Free and Pro tiers see only the FDM shape. The
loop is already there. Fast. Milliseconds.

Owner, Studio, Beta tiers see the NFDM refinement.
The user adjusts the edge cable pretension, the
loop responds, the forces are real, and the
numbers behind the shape are trustworthy.

### Part 3 — The eight pieces

In order:

  1. engine/mesh_triangulated.py — release the
     boundary interior points when segment type
     is "cable". Only the anchors remain fixed.
     Loops appear in the App.
  2. engine/nonlinear_equilibrium.py — add
     cable_tensions_from_fdm. Each cable
     segment's initial pretension comes from the
     FDM boundary edge force: T = q_edge * L.
  3. viewers/figures/standard_saddle_mbs.py —
     NFDM runs from the FDM shape as the current
     geometry, the flat pattern as the reference,
     real cable chains along every mesh boundary
     edge, anchors only fixed.
  4. engine/nonlinear_equilibrium.py — accept a
     warm_start_points argument. If provided, use
     it as the starting current geometry.
  5. viewers/figures/standard_saddle_mbs.py —
     warm start from the previous NFDM result
     when only the prestress changes.
  6. Viewer UI — forward and back buttons to
     step through the history of solved states.
  7. Persistent solved-state store — every
     solved state saved to a file, loaded on app
     start.
  8. Project file format — the container that
     carries inputs, materials, sections, solved
     state, history, and the engine version. Every
     project is a file.

### Part 4 — What the project file carries

A project file contains everything the user did
to reach a solved state:

  - project identity: name, structure type,
    variant, date,
  - which recipe was used, and the recipe version,
  - every input value: span, apex, rise, curve
    type, anchor count, mesh spacing, materials,
    prestress values, cable pretensions,
    foundation, loads, design standard,
  - the material selection, exact record,
  - the section selection,
  - the solved state: coordinates, cable
    tensions, membrane stresses, iterations,
    reason,
  - the solved history, so the user can step
    back and forward,
  - the timestamp of every solve,
  - the version of the engine that solved it.

The App is disposable. The project files are
permanent. The engine evolves but the files carry
the intent.

### Part 5 — What is not touched

  - viewers/figures/beam_supported_saddle.py
  - the Beam Supported Saddle recipe, workshop,
    and viewer
  - engine/form_finding.py — the FDM solver
  - data/materials.py
  - data/recipes/standard_saddle.py
  - run_tests.py and the existing test suite

The Beam Supported model works. It will not be
disturbed.

### Part 6 — The record

The Chief's instruction, morning of 2026-10-06:

  "I think it's about time to safe files so that
   we don't have to rebuild every time, just
   recall to do the work."

To prevent the rebuild-every-session pattern, the
following documents are written and kept current:

  - ARCHITECTURE.md      — the system as it is.
  - DECISIONS.md         — every governing decision,
                           append only.
  - CURRENT_STATE.md     — what each file is at,
                           what works, what is in flight.
  - PLAN.md              — the eight pieces, in
                           order, with acceptance tests.
  - OPEN_QUESTIONS.md    — anything unresolved.
  - PROJECT_SESSION_LOG.md — this file. Append only.

These are read on day one of every new session,
before any code is written.

### Part 7 — The FDM path, proven

Late in the session the FDM path was finally
verified. Three changes to `viewers/figures/standard_saddle_mbs.py`
produced the shape.

1.  **The pull-back threshold.** Changed `T > 0.0`
    to `T > 1.0`. A pull-back of 1e-10 N is not a
    real cable tension; it is a numerical zero. It
    now falls back to `edge_q_scalar`.
2.  **The mode selector.** The tier split was
    wrongly assumed to be "Free and Pro get FDM,
    Owner and Studio get NFDM". The Chief corrected
    this: high tiers must be able to choose either.
    A radio selector was added to the Results page.
3.  **The auto-scaled edge cable pretension.**
    The recipe default is now `0.0` (auto). The
    viewer computes the auto value as
    `N_membrane * L_anchor`, where `L_anchor` is
    the distance between two adjacent anchors along
    the beam.

With the mode selector set to FDM, the shape now
shows the characteristic scalloped boundary. Each
scallop is the bow between two adjacent anchors.
This is the loop the Chief described.

Diagnostic at close:

    q path: dict
    warp_q: 3606.5746
    weft_q: 3606.5746
    edge_q_scalar: 54098.6197

    boundary: n=196 min=54098.6197 max=54098.6197 mean=54098.6197
    interior: n=7213 min=3606.5746 max=3606.5746 mean=3606.5746

    ratio boundary_mean / interior_mean = 15.0000

    Edge cable pretension: 30.000 kN (user)

The ratio of 15 is correct for a 30 kN user
value. If the user had entered 0 (auto), the
value would be about 2.0 kN, the ratio would be
about 1.0, and the bow would be deeper.

### Part 8 — What remains

  1. Tune the auto-scale. The ratio of 15 at
     the auto-computed value is too high.
     Correct is about 1.0. The formula
     `T_default = N_membrane * L_anchor` is
     off by a factor of roughly 15 for this
     mesh geometry. Either divide by a
     calibration factor or investigate the
     discrepancy and fix the formula.
  2. A viewer slider for live pretension
     control. After the auto-scale is tuned.
  3. NFDM path convergence at App scale.
     Still does not converge. Separate problem.
  4. Rule 23, TIERS.md, FILE_INVENTORY.md
     updates.

### Part 9 — The lesson

The Chief drove every step. When the FDM path
did not bow, the Chief asked why. When the AI
proposed a workaround, the Chief insisted on
the real thing. When the tier split did not
allow high tiers to choose FDM, the Chief
said so. When the pretension value was
questioned, the Chief said plainly that the
30 kN user value was why the ratio was high.

Every correction was the Chief's. The AI's
job is to type. The Chief's job is to think.

### The record

The record is the Chief's protection.
The record is the AI's discipline.
Both are needed. Both are kept.

---

End of PROJECT_SESSION_LOG.md.
New entries are added at the bottom. Nothing is
overwritten.
