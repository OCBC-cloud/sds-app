# SDSe_mesh_builder_SPEC.md

**Status:** approved
**Author:** agent, session 2026-10-14
**Supersedes:** none (this is the founding document)
**Component:** `engine/SDSe_mesh_builder.py`
**Language:** English

---

## 1. Purpose

`SDSe_mesh_builder` is the permanent, unified membrane mesh builder for all
SDSe shapes. It replaces the several overlapping mesh builders that currently
exist across the codebase.

It exists because today's codebase has at least four different mesh-building
code paths, each slightly different, each with its own copy of the same
physics. This is why the Dome Multi-Cone did not draw correctly and why
fixes had to be made in multiple places. One builder, one source of truth,
is the fix.

## 2. Doctrine

1. This builder is permanent. It will eventually serve every shape in the
   system that has a membrane.
2. Old builders are superseded one at a time. Never deleted. Retained for
   reference.
3. A shape is switched to SDSe_mesh_builder only after the new builder is
   proven to draw identically to the old one, on the same inputs, in the
   same Lab.
4. Nothing user-facing changes until the engine is proven in the Lab.
5. One file at a time. Each change is named explicitly, shown to the Chief,
   and signed off before the next.

## 3. The proven physics — frozen

The core physics of SDSe_mesh_builder is verbatim from
`ui/workshops/tester_multi_cone.py` v21 (2026-10-13). No re-derivation.
No invention. The following functions are lifted from v21 and renamed with
the `SDSe_` prefix:

| v21 name                | SDSe name                | Role                                              |
| ----------------------- | ------------------------ | ------------------------------------------------- |
| `_laplace_lift_fabric`  | `SDSe_laplace_lift`      | Laplace-lift interior fabric z to meet boundary   |
| `_blend_q_per_edge`     | `SDSe_blend_q_per_edge`  | Anisotropic warp/weft force density per edge      |
| `_ring_node_count`      | `SDSe_ring_node_count`   | Adaptive node count per ring                      |
| `_point_in_polygon`     | `SDSe_point_in_polygon`  | Ray-cast plan test                                |
| `_build_cone_mesh`      | `SDSe_mesh_rings`        | Mesh with rings and holes, any shape              |

The v21 perimeter-free physics is preserved: only structural anchors are
held; every intermediate perimeter node is fully free (3 DOF). This is
what makes the perimeter cable bow correctly.

The solver called by consumers is `engine.form_finding_test.solve_fdm` —
the proven reduced-basis FDM solver. SDSe_mesh_builder does not contain
its own solver.

### 3.1 The contract

The engine is a mesh builder. It does not know what shape is being
meshed, what a picker is, what a cone is, or what a spine is. It takes
a geometry description and returns a mesh.

The caller (a viewer file) assembles the inputs:

- `perimeter_loop` — closed boundary of the membrane
- `anchor_idx` — which perimeter nodes are held
- `ring_specs` — one dict per ring hole
- `eave_height` — z of the boundary
- `target_len` — mesh density

The engine returns points, edges, triangles, fixed set, and boundary
edges. The caller then runs the FDM solve and draws.

Any shape with a closed perimeter and rings can call `SDSe_mesh_rings`.
A spine with cones. A dome with cones hanging off a frame grid. Anything.

## 4. Architecture — one file, one dispatcher, many builders

`SDSe_mesh_builder.py` contains:

- A shared core — the physics and helpers from §3, plus edge assembly,
  boundary detection, and the common
  `points / edges / triangles / fixed / boundary_edges` return shape.
- A family of shape-agnostic builders — each one short, each one
  responsible only for assembling the right inputs and calling the
  shared core.
- One dispatcher — `SDSe_build_mesh(shape, **kwargs)` — that routes to
  the correct builder.

### 4.1 The builders

| Function                  | Purpose                                 | Status      |
| ------------------------- | --------------------------------------- | ----------- |
| `SDSe_build_mesh`         | Dispatcher                              | Delivered   |
| `SDSe_mesh_rings`         | Mesh with rings and holes, any shape    | Delivered   |
| `SDSe_mesh_flat`          | No holes, no rings, plain membrane      | Not yet     |
| `SDSe_mesh_kader`         | Two beams with kader track              | Not yet     |
| `SDSe_mesh_cable`         | Cable-held perimeter, no rings          | Not yet     |
| `SDSe_mesh_rings_cable`   | Rings + cable boundary + kader          | Not yet     |

`SDSe_mesh_rings` was originally named `SDSe_mesh_rings_spine` because it
was first used by the Multi-Cone viewer, which has a primary beam. The
name was misleading: the function takes a perimeter and a list of rings,
not a spine. It was renamed on 2026-10-14. Multi-Cone, the Lab tester,
and Dome Multi-Cone all call it.

### 4.2 What varies between builders

Only four things:

1. How the boundary loop is assembled — shape-specific geometry.
2. Whether there are holes — cone shapes have ring holes; others do not.
3. How the ring specs are computed — arc-position on a spine, versus
   picked positions on a plan grid, versus none.
4. Which boundary nodes are structural anchors — shape-specific.

Everything else — Laplace lift, Delaunay, triangle filtering, edge
assembly, boundary detection, fixed set, anisotropic q — is identical
and lives in the shared core.

## 5. Scope

Delivered:

- `SDSe_build_mesh` (dispatcher)
- `SDSe_mesh_rings` — the general ring-and-hole mesher

Not yet delivered:

- `SDSe_mesh_flat`
- `SDSe_mesh_kader`
- `SDSe_mesh_cable`
- `SDSe_mesh_rings_cable`

## 6. Proof path — the takeover sequence

Each step is done in order. No step begins until the previous is
signed off.

**Step 1 — Write `engine/SDSe_mesh_builder.py`.**
- Done. Contains the dispatcher, the shared core, and `SDSe_mesh_rings`.

**Step 2 — Wire the Lab tester to SDSe_mesh_builder.**
- Done. `ui/workshops/tester_multi_cone.py` removed its local copies
  and now imports `SDSe_mesh_rings` and `SDSe_blend_q_per_edge` from
  the engine.

**Step 3 — Prove it draws identically.**
- Done. Lab tester draws the Multi-Cone shape correctly, verified by
  the Chief on 2026-10-14.

**Step 4 — Production Multi-Cone switches to SDSe_mesh_builder.**
- Done. `viewers/figures/multi_cone_roof.py` draws on the shared engine.

**Step 5 — Dome Multi-Cone builds on SDSe_mesh_builder.**
- Frame, eave polygon, and cones delivered (Pieces 1–4).
- Membrane wiring is the next piece.

**Step 6 — MBS saddle switches to SDSe_mesh_builder (later).**
- Add `SDSe_mesh_cable` to the engine.
- Migrate `viewers/figures/standard_saddle_mbs.py`.
- Verify in the app: Standard Saddle draws identically.

**Step 7 — Old saddle builder (later).**
- Migrate `viewers/figures/saddle_standard.py` if and when the owner
  decides it should use the same engine.
- Verify: Standard Saddle (old path) draws identically.

Each step supersedes a specific old builder in the audit trail (see §9).

## 7. Files that change — one at a time

Order of edits. Each one shown to the Chief, one file per message,
wait for "done," then next.

1. `engine/SDSe_mesh_builder.py` — done.
2. `ui/workshops/tester_multi_cone.py` — done.
3. `viewers/figures/multi_cone_roof.py` — done.
4. `viewers/figures/dome_multi_cone.py` — in progress. Frame, eave
   polygon, cones delivered. Membrane wiring pending.
5. `viewers/figures/standard_saddle_mbs.py` — later.

## 8. Files that are NOT touched

Until their turn comes, these files remain exactly as they are. Working
code stays working.

- `engine/mesh_triangulated.py` — retained. Superseded by
  SDSe_mesh_builder, but not deleted. Other code may still import it.
- `viewers/figures/saddle_standard.py` — retained. Old saddle path.
- `engine/form_finding.py` — retained. Old solver. Heritage.
- `engine/form_finding_test.py` — retained. The proven solver
  SDSe_mesh_builder calls.
- `engine/nonlinear_equilibrium.py` — retained. NFDM path.
- `viewers/figures/_shared.py` — retained. Shared layout and beam_curve
  helpers.
- `.github/workflows/test.yml`, `run_tests.py` — CI. Not modified.

## 9. Audit trail — supersession log

Every supersession is recorded here as it happens. This is how future
agents know what replaced what, and when.

| Date       | Change                                                                     | Status  | Notes                                         |
| ---------- | -------------------------------------------------------------------------- | ------- | --------------------------------------------- |
| 2026-10-14 | `_build_cone_mesh` in `ui/workshops/tester_multi_cone.py` → `SDSe_mesh_rings` | done    | Lab tester rebuilt on SDSe engine             |
| 2026-10-14 | `_build_cone_mesh` in `viewers/figures/multi_cone_roof.py` → `SDSe_mesh_rings` | done    | Production Multi-Cone rebuilt on SDSe engine  |
| 2026-10-14 | Renamed `SDSe_mesh_rings_spine` → `SDSe_mesh_rings`                        | done    | Not spine-specific. Takes a perimeter and rings. Any shape can call it. |
| 2026-10-14 | Dome Multi-Cone frame, eave polygon, cones delivered                       | done    | Via `viewers/figures/dome_multi_cone.py`.      |
| —          | Dome Multi-Cone membrane wired to `SDSe_mesh_rings`                        | pending | Piece 5                                       |
| —          | `build_mesh_triangulated` in `engine/mesh_triangulated.py` → `SDSe_mesh_cable` | pending | MBS saddle switch                             |
| —          | Grid builder in `viewers/figures/saddle_standard.py` → `SDSe_mesh_cable`   | pending | Old saddle switch                             |

Old builders are not deleted. They live on in their original files until
a shape switches to the SDSe engine, at which point the local builder is
removed from the viewer, not from the codebase.

## 10. Naming convention

- All SDSe core engines: `engine/SDSe_<component>.py` — Pascal prefix,
  lowercase body.
- All functions inside: `SDSe_<function_name>` — Pascal prefix,
  snake_case body.
- Non-core code (viewers, workshops, recipes, data) keeps its existing
  lowercase snake_case naming.

## 11. What "proven healthy" means

A shape is switched to SDSe_mesh_builder only when, on the same inputs
as before:

- The mesh draws identically (same node count within rounding, same
  triangle count, same visual).
- The rings draw identically.
- The cable bow is the same shape.
- The membrane sags identically.
- The FDM solve returns the same residual order of magnitude.

If any of those fail, the switch is rolled back, SDSe_mesh_builder is
corrected, and the proof is re-run.

## 12. Approval

Approved by the Chief on 2026-10-14. This is the standing record for
this component. Future changes to SDSe_mesh_builder update §4 (builders)
and §9 (audit trail).

---

**End of spec.**
