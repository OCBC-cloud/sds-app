## 9. Audit trail — supersession log

Every supersession is recorded here as it happens. This is how future
agents know what replaced what, and when.

| Date       | Old builder                                                | New builder                | Status | Notes                                    |
| ---------- | ---------------------------------------------------------- | -------------------------- | ------ | ---------------------------------------- |
| 2026-10-14 | `_build_cone_mesh` in `ui/workshops/tester_multi_cone.py`  | `SDSe_mesh_rings_spine`    | done   | Lab tester rebuilt on SDSe engine        |
| 2026-10-14 | `_build_cone_mesh` in `viewers/figures/multi_cone_roof.py` | `SDSe_mesh_rings_spine`    | done   | Production Multi-Cone rebuilt on SDSe engine |
| —          | `_build_dome_mesh` in `viewers/figures/dome_multi_cone.py` | `SDSe_mesh_rings_picker`   | pending | Step 5 — dome rebuild                    |
| —          | `build_mesh_triangulated` in `engine/mesh_triangulated.py` | `SDSe_mesh_cable`          | pending | Step 6 — MBS saddle switch               |
| —          | grid builder in `viewers/figures/saddle_standard.py`       | `SDSe_mesh_cable`          | pending | Step 7 — old saddle switch               |
