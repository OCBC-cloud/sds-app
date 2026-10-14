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
physics. This is why the Dome Multi-Cone does not draw correctly and why
fixes have to be made in multiple places. One builder, one source of truth,
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
| `_build_cone_mesh`      | `SDSe_mesh_rings_spine`  | The whole v21 mesh build for cone rings on a spine |

The v21 perimeter-free physics is preserved: only structural anchors are
held; every intermediate perimeter node is fully free (3 DOF). This is
what makes the perimeter cable bow correctly.

The solver called by consumers is `engine.form_finding_test.solve_fdm` —
the proven reduced-basis FDM solver. SDSe_mesh_builder does not contain
its own solver.

## 4. Architecture — one file, one dispatcher, many builders

`SDSe_mesh_builder.py` contains:

- A shared core — the physics and helpers from §3, plus edge assembly,
  boundary detection, and the common
  `points / edges / triangles / fixed / boundary_edges` return shape.
- A family of shape-specific builders — each one short, each one
  responsible only for assembling the right inputs for the shape and
  calling the shared core.
- One dispatcher — `SDSe_build_mesh(shape, **kwargs)` — that routes to
  the correct builder.

### 4.1 The builders

| Function                  | Purpose                                 | Shape / case                       |
| ------------------------- | --------------------------------------- | ---------------------------------- |
| `SDSe_build_mesh`         | Dispatcher                              | —                                  |
| `SDSe_mesh_flat`          | No holes, no rings, plain membrane      | Simple panels                      |
| `SDSe_mesh_kader`         | Two beams with kader track, no rings    | Saddle — kader mode                |
| `SDSe_mesh_cable`         | Cable-held perimeter, no rings          | Saddle — cable mode, MBS           |
| `SDSe_mesh_rings_spine`   | Cone rings on a single primary beam     | Multi-Cone Cluster, Lab tester     |
| `SDSe_mesh_rings_picker`  | Cone rings at user-picked plan crossings| Dome Multi-Cone                    |
| `SDSe_mesh_rings_cable`   | Cone rings + cable boundary + kader     | Future combined shapes             |

### 4.2 What varies between builders

Only four things:

1. How the boundary loop is assembled — shape-specific geometry.
2. Whether there are holes — cone shapes have ring holes; others do not.
3. How the ring specs are computed — arc-position on a spine, versus
   picked crossings on a plan grid, versus none.
4. Which boundary nodes are structural anchors — shape-specific.

Everything else — Laplace lift, Delaunay, triangle filtering, edge
assembly, boundary detection, fixed set, anisotropic q — is identical
and lives in the shared core.

## 5. v1 scope

Builders in v1:

- `SDSe_build_mesh` (dispatcher)
- `SDSe_mesh_rings_spine` — the Lab tester's builder, needed first

Deferred to v2, after v1 is proven:

- `SDSe_mesh_rings_picker` — needed for the Dome rewrite
- `SDSe_mesh_cable` — needed for the MBS saddle switch
- `SDSe_mesh_flat`
- `SDSe_mesh_kader`
- `SDSe_mesh_rings_cable`

v1 delivers the shared core plus one builder. That builder is the one
the Lab tester uses. Proven in the Lab, then v2 begins.

## 6. Proof path — the takeover sequence

Each step is done in order. No step begins until the previous is
signed off.

**Step 1 — Write `engine/SDSe_mesh_builder.py` (v1).**
- Contains the dispatcher, the shared core, and `SDSe_mesh_rings_spine`.
- No existing file is touched.
- SDSe_mesh_builder is tested in isolation with unit inputs.

**Step 2 — Wire the Lab tester to SDSe_mesh_builder.**
- Edit `ui/workshops/tester_multi_cone.py`:
  - Remove its local `_build_cone_mesh`, `_laplace_lift_fabric`,
    `_blend_q_per_edge`, `_ring_node_count`, `_point_in_polygon`.
  - Import the equivalents from `engine.SDSe_mesh_builder`.
  - Call `SDSe_mesh_rings_spine` in place of the old `_build_cone_mesh`.
- Behaviour is expected to be identical.

**Step 3 — Prove it draws identically.**
- Open the app → Lab → Multi-Cone Roof Tester.
- Use the same inputs as before (span 25, apex 9, mid width 18, eave 2.8,
  3 cones, 5 m spacing, default q values).
- Compare the 3D view to the previous render.
- If pixel-identical in the mesh, rings, cable bow, membrane sag — proven.
- If not identical, diff outputs, fix SDSe_mesh_builder, retest.
- No further step begins until identical.

**Step 4 — Production Multi-Cone switches to SDSe_mesh_builder.**
- Edit `viewers/figures/multi_cone_roof.py` to import from
  SDSe_mesh_builder.
- Remove its local copies of the same functions.
- Verify in the app: Multi-Cone Cluster variant draws identically to
  before.

**Step 5 — Dome Multi-Cone builds on SDSe_mesh_builder.**
- Add `SDSe_mesh_rings_picker` to SDSe_mesh_builder (v2).
- Rewrite `viewers/figures/dome_multi_cone.py` to use it.
- Verify in the app: Dome Multi-Cone draws correctly.

**Step 6 — MBS saddle switches to SDSe_mesh_builder (later).**
- Add `SDSe_mesh_cable` to SDSe_mesh_builder (v2).
- Migrate `viewers/figures/standard_saddle_mbs.py` to use it.
- Verify in the app: Standard Saddle draws identically.

**Step 7 — Old saddle builder (later).**
- Migrate `viewers/figures/saddle_standard.py` if and when the owner
  decides it should use the same engine.
- Verify: Standard Saddle (old path) draws identically.

Each step supersedes a specific old builder in the audit trail (see §9).

## 7. Files that will change — one at a time

Order of edits. Each one shown to the Chief, one file per message,
wait for "done," then next.

1. `engine/SDSe_mesh_builder.py` — new file. v1 core + `SDSe_mesh_rings_spine`.
2. `ui/workshops/tester_multi_cone.py` — wire to the new engine, remove
   local copies.
3. `viewers/figures/multi_cone_roof.py` — switch to the new engine.
4. `engine/SDSe_mesh_builder.py` — add `SDSe_mesh_rings_picker` (v2).
5. `viewers/figures/dome_multi_cone.py` — rewrite to use SDSe_mesh_builder.
6. `engine/SDSe_mesh_builder.py` — add `SDSe_mesh_cable` (v3).
7. `viewers/figures/standard_saddle_mbs.py` — switch to SDSe_mesh_builder.

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

| Date       | Old builder                                            | New builder              | Status  | Notes  |
| ---------- | ------------------------------------------------------ | ------------------------ | ------- | ------ |
| —          | `_build_cone_mesh` in `ui/workshops/tester_multi_cone.py` | `SDSe_mesh_rings_spine`  | pending | Step 2 |
| —          | `_build_cone_mesh` in `viewers/figures/multi_cone_roof.py` | `SDSe_mesh_rings_spine` | pending | Step 4 |
| —          | `_build_dome_mesh` in `viewers/figures/dome_multi_cone.py` | `SDSe_mesh_rings_picker`| pending | Step 5 |
| —          | `build_mesh_triangulated` in `engine/mesh_triangulated.py` | `SDSe_mesh_cable`       | pending | Step 6 |
| —          | grid builder in `viewers/figures/saddle_standard.py`     | `SDSe_mesh_cable`        | pending | Step 7 |

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
