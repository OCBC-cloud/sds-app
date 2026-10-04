# SDSe — FILE INVENTORY

Plain, factual list of every file in the repository. Read
alongside PROJECT_STATE.md. Updated whenever a file is added,
renamed, deleted, or its public interface changes.

Status values:
  ACTIVE     — used by the app right now.
  REFERENCE  — kept for the future, not called by anything.
  DOC        — documentation.
  TEST       — test-only, not called by the app.

Last updated: 2026-10-04.

---

# ROOT

- app.py
    Streamlit entry point. Bootstraps theme, session state,
    and dispatches to the router.
    ACTIVE.

- run_tests.py
    Test runner for GitHub Actions. Runs all engine tests.
    Fixed 2026-10-03: the __main__ guard was trapped inside
    main(). The tests now actually execute.
    ACTIVE.

- benchmark_hypar.py
    Standalone benchmark against SDS-CONST Benchmark 001.
    Not wired into the app. Run by run_tests.py.
    TEST.

- requirements.txt
    Python dependencies for Streamlit Cloud.
    ACTIVE.

- physics_engine.py
    Legacy physics module. Superseded by engine/form_finding.py.
    REFERENCE.

- viewer_app.py
    Legacy viewer. Superseded by viewers/results_viewer.py.
    REFERENCE.

- PROJECT_STATE.md
    Single source of truth. Current state. Read first.
    DOC.

- PROJECT_CONSTITUTION.md
    The doctrines. Part III-B: the Universal Engine Doctrine.
    Part V: two kinds of constraint. Rule 22: one file, one
    block, one copy.
    DOC.

- PROJECT_VISION.md
    North star. Purpose, scope, roadmap.
    DOC.

- PROJECT_SESSION_LOG.md
    The archive. Append only.
    DOC.

- FILE_INVENTORY.md
    This file.
    DOC.

- SUBSTRUCTURES.md
    The seven substructure categories. The input map for the
    four existing workshops. Exposure table per access mode.
    Design only. Not executed.
    DOC.

- UI_ARCHITECTURE.md
    The universal workshop pattern. Six groups plus additional.
    The migration guide for the four existing workshops.
    Design only. Not executed.
    DOC.

- TIERS.md
    The five access modes. The access gate. The beta window.
    The Owner role. URL resilience plan. Design only. Not
    executed.
    DOC.

- COMMERCIAL_MODEL.md
    Pricing tiers, target users, revenue projection.
    DOC.

- MARKETING_RENDER_WORKFLOW.md
    Design for the marketing render feature.
    DOC.

- README.md
    Initial project readme.
    DOC.

- README_MODULAR.md
    Readme for the modular-v10 branch.
    DOC.

- HANDOVER_2026-10-03.md
    The handover that opened the 2026-10-03 session. Its
    diagnosis was incomplete: two of three things it claimed
    were working were not. Kept for history. Superseded by
    PROJECT_STATE.md and PROJECT_SESSION_LOG.md. Should be
    deleted.
    REFERENCE.

---

# /core/

- __init__.py
    Package marker.
    ACTIVE.

- navigation.py
    Page router. Maps page keys to render functions.
    ACTIVE.

- state.py
    Session state initialisation.
    ACTIVE.

- theme.py
    Global CSS and theme applied on every page.
    ACTIVE.

---

# /data/

- __init__.py
    Package marker.
    ACTIVE.

- constants.py
    Wind speeds and global constants.
    ACTIVE.

- materials.py
    Material properties: steel grades, fabric types, grades.
    Ferrari 702 record for Type III PVDF is complete. Other
    PVDF grades are placeholders.
    ACTIVE.

- sections.py
    Section property catalogue (CHS, SHS, RHS, I-Beam).
    ACTIVE.

- structures.py
    STRUCTURE_TYPES, STRUCTURE_VARIANTS, MEMBER_SCHEMA.
    ACTIVE.

# /data/recipes/

- __init__.py
    Package marker.
    ACTIVE.

- standard_saddle.py
    Recipe for the Cable Supported Saddle workshop.
    Six groups. Read by ui/workshops/_renderer.py.
    Has NOT yet gained the three Shape inputs
    (anchor_count, mesh_spacing, transverse_count).
    ACTIVE.

---

# /engine/

- __init__.py
    Package marker.
    ACTIVE.

- form_finding.py
    FDM solver. solve_fdm() and mesh_size_for_shape().
    Plus the anisotropic q functions:
    assign_anisotropic_q, auto_warp_dir, rotate_warp_dir.
    Linear form-finding. Core of the shape engine.
    ACTIVE.

- mesh_triangulated.py
    The universal mesh engine. build_mesh_triangulated()
    takes a closed boundary loop, projects to plan, runs
    scipy.spatial.Delaunay, filters to the polygon interior,
    lifts interior nodes, and runs FDM.
    The universal engine. Live.
    ACTIVE.

- mesh_triangulated_test.py
    Five boundary inputs. All pass. Zero zero-area
    triangles, machine-zero FDM residuals.
    TEST.

- membrane.py
    System A helper. Mesh handling utilities.
    Called by run_tests.py.
    ACTIVE.

- membrane_boundary.py
    Old MBS engine. Four-sided TFI path.
    Still called by the Tester shapes.
    ACTIVE (legacy).

- membrane_surface.py
    Lens surface builder. Called by the Tester Lens recipe.
    ACTIVE (legacy).

- leaf_arrangement.py
    Placement engine for Cantilever Leaf.
    ACTIVE.

- nfdm.py
    Pauletti Natural Force Density Method kernel.
    Newton-Raphson with backtracking line search.
    Isolated and tested. Nothing in the shipping app calls it.
    Stage 2 foundation.
    REFERENCE.

- nfdm_tension_field.py
    Tension-field projection. project_tension_field() plus
    two helpers. sigma_TF = Q diag(max(s1,0), max(s2,0)) Q^T.
    Verified. Stage 2 foundation.
    REFERENCE.

- nfdm_tension_field_test.py
    Six tests for the projection. All pass.
    TEST.

- render_prompts.py
    Marketing render prompt engine.
    ACTIVE.

- MEMBRANE_GUIDE.md
    Membrane principle. Boundary families, drawing rules.
    DOC.

- PLACEHOLDERS.md
    Single source of truth for placeholder inputs.
    DOC.

- SPEC_engine_chain.md
    The seven-link chain: SHAPE, LOADS, FORCES, SIZES,
    QUANTITIES, REPORT, CATALOGUES.
    DOC.

- SPEC_cantilever_hypar.md
    Specification of the Cantilever Hypar variant.
    DOC.

- SPEC_saddle_span.md
    Saddle Span structure specification.
    DOC.

- SPEC_dxf_import.md
    DXF import design.
    DOC.

- SPEC_coordinate_file.md
    Coordinate file design.
    DOC.

- SPEC_custom_boundary.md
    Custom boundary structure design.
    DOC.

- SPEC_mesh_triangulation.md
    The live universal mesh specification. Constrained
    Delaunay triangulation of the boundary loop.
    DOC.

- SPEC_saddle_viewer_fdm.md
    Saddle viewer FDM specification.
    DOC.

---

# /ui/

- __init__.py
    Package marker.
    ACTIVE.

- landing.py
    Splash screen. Enter The Studio, Open MBS Tester,
    Open Renderer Test (temporary).
    ACTIVE.

- studio.py
    Main structure type menu. Eight tiles across two sections.
    ACTIVE.

- registration.py
    Project information and variant selection.
    ACTIVE.

- workshop.py
    Dispatcher. Routes to the correct workshop for the
    selected variant.
    ACTIVE.

- results.py
    Results page. 3D viewer, summary, marketing render.
    ACTIVE.

---

# /ui/rooms/

- __init__.py
    Package marker.
    ACTIVE.

- leaf_room.py
    Rib Length Adjustment room for the Cantilever Leaf.
    ACTIVE.

---

# /ui/workshops/

- __init__.py
    Package marker.
    ACTIVE.

- _shared.py
    Shared workshop CSS and helpers.
    ACTIVE.

- _renderer.py
    Universal workshop renderer. Reads a recipe. Builds
    the input page.
    ACTIVE.

- _renderer_test.py
    Temporary test page for the renderer. Removed after
    the first real workshop migrates.
    TEST.

- saddle_standard.py
    Cable Supported Saddle workshop. Migrated to the recipe
    pattern. 12 lines. Calls render_workshop().
    ACTIVE.

- saddle_frame.py
    Beam Supported Saddle workshop. Hand-written. 9 sections.
    ACTIVE.

- saddle_leaf.py
    Cantilever Leaf workshop. Hand-written. 9 sections.
    ACTIVE.

- saddle_hypar.py
    Cantilever Hypar workshop. Hand-written. 9 sections.
    ACTIVE.

- tester_mbs.py
    Shape laboratory. Shape recipes built on the MBS
    engine. Experimental. Owner-only.
    ACTIVE (temporary).

---

# /viewers/

- __init__.py
    Package marker.
    ACTIVE.

- results_viewer.py
    Dispatcher. Routes on variant_key to the correct figure
    builder.
    ACTIVE.

---

# /viewers/figures/

- __init__.py
    Package marker.
    ACTIVE.

- _shared.py
    Shared figure helpers: apply_common_layout, beam_curve,
    arclength_parametrisation, find_index_at_arclength_fraction.
    ACTIVE.

- _descriptions.py
    Structure summary descriptions used by viewers.
    ACTIVE.

- standard_saddle.py
    OLD Cable Supported Saddle viewer. Hand-built rectangular
    mesh. Has the fold. Kept as fallback.
    ACTIVE (legacy).

- standard_saddle_mbs.py
    MBS version of the Standard Saddle viewer. Uses the
    triangulated engine. Live.
    ACTIVE.

- beam_supported_saddle.py
    Beam Supported Saddle viewer. Draws surface from a
    formula. To be migrated.
    ACTIVE (needs migration).

- cantilever_hypar.py
    Cantilever Hypar viewer. Draws a Coons patch. To be
    migrated.
    ACTIVE (needs migration).

- cantilever_leaf.py
    Cantilever Leaf viewer. Draws. Uses leaf_arrangement.
    ACTIVE.

---

# /.github/workflows/

- test.yml
    GitHub Actions workflow. Runs run_tests.py on push.
    ACTIVE.

---

# /.streamlit/

- config.toml
    Streamlit configuration (theme, layout).
    ACTIVE.

---

# /.devcontainer/

- devcontainer.json
    Dev container configuration.
    REFERENCE.

---

# FILES DELETED (no longer present)

These were listed in older versions of this file. They are
gone from the repository. Kept here as a record.

- engine/mesh_universal.py — superseded by mesh_triangulated.py.
- engine/mesh_universal_test.py — its test.
- engine/SPEC_mesh_topology.md — superseded by
  SPEC_mesh_triangulation.md.
- engine/SPEC_mesh_universal.md — superseded.
- engine/SPEC_mesh_from_segments.md — superseded.
- HANDOVER_2026-10-01 — superseded by HANDOVER_2026-10-03.md.
- TEST_CHUNK_TRANSFER_LIMITS_001.md — test artifact, deleted.
- EST_CHUNK_TRANSFER_LIMITS_001.md — test artifact, deleted.

---

# END OF FILE INVENTORY

Keep this file current. One line per change. Ten seconds
of discipline saves half a day of re-orientation.
