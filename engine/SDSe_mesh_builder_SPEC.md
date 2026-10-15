## 3. The proven physics — frozen

The core physics of SDSe_mesh_builder is verbatim from
`ui/workshops/tester_multi_cone.py` v21 (2026-10-13). No re-derivation.
No invention. The following functions are lifted from v21 and renamed
with the `SDSe_` prefix:

| v21 name                | SDSe name                | Role                                              |
| ----------------------- | ------------------------ | ------------------------------------------------- |
| `_laplace_lift_fabric`  | `SDSe_laplace_lift`      | Laplace-lift interior fabric z to meet boundary   |
| `_blend_q_per_edge`     | `SDSe_blend_q_per_edge`  | Anisotropic warp/weft force density per edge      |
| `_ring_node_count`      | `SDSe_ring_node_count`   | Adaptive node count per ring                      |
| `_point_in_polygon`     | `SDSe_point_in_polygon`  | Ray-cast plan test                                |
| `_build_cone_mesh`      | `SDSe_mesh_rings`        | Mesh with rings and holes, any shape              |

The v21 perimeter-free physics is preserved: only structural anchors
are held; every intermediate perimeter node is fully free (3 DOF).
This is what makes the perimeter cable bow correctly.

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

Any shape with a closed perimeter and rings can call
`SDSe_mesh_rings`. A spine with cones. A dome with cones hanging off
a frame grid. Anything.
