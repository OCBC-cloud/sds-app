# SDSe — FILE INVENTORY

Plain, factual list of every file in the repository. Read
alongside PROJECT_STATE.md. Updated whenever a file is added,
renamed, deleted, or its public interface changes.

Status values:
  ACTIVE     — used by the app right now.
  REFERENCE  — kept for the future, not called by anything.
  DOC        — documentation.
  TEST       — test-only, not called by the app.

Last updated: 2026-09-29.

---

# ROOT

- app.py
    Streamlit entry point. Bootstraps theme, session state,
    and dispatches to the router.
    ACTIVE.

- run_tests.py
    Test runner for GitHub Actions. Runs all engine tests.
    Updated 2026-09-29: added the universal mesh engine test.
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
    Part V: two kinds of constraint.
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

---

# /core/

- __init__.py
    Package marker.
    ACTIVE.

- navigation.py
    Page router. Maps page keys to render functions.
    Updated 2026-09-29: added renderer_test route.
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
    ACTIVE.

- sections.py
    Section property catalogue (CHS, SHS, RHS, I-Beam).
    ACTIVE.

- structures.py
    STRUCTURE_TYPES, STRUCTURE_VARIANTS, MEMBER_SCHEMA.
    ACTIVE.

# /data/recipes/

New in 2026-09-29. Workshop recipes for the universal renderer.

- __init__.py
    Package marker.
    ACTIVE.

- standard_saddle.py
    Recipe for the Cable Supported Saddle workshop.
    Six groups. Read by ui/workshops/_renderer.py.
    ACTIVE.

---

# /engine/

- __init__.py
    Package marker.
    ACTIVE.

- form_finding.py
    FDM solver. solve_fdm() and mesh_size_for_shape().
    Linear form-finding. Core of the shape engine.
    ACTIVE.

- membrane.py
    System A helper. Mesh handling utilities.
    Called by run_tests.py.
    ACTIVE.

- membrane_boundary.py
    Old MBS engine. Four-sided TFI path.
    Still called by the Tester shapes.
    Superseded for mixed boundaries by mesh_universal.py.
    ACTIVE (legacy).

- membrane_surface.py
    Lens surface builder. Called by the Tester Lens recipe.
    ACTIVE (legacy).

- mesh_universal.py
    NEW 2026-09-29. The universal mesh engine.
    Builds a mesh from a closed boundary loop, divided into
    segments, each classified beam / cable / wall.
    Three fills: tfi, polar, barycentric.
    Tested and proven. Not yet wired into any viewer.
    ACTIVE (isolated).

- mesh_universal_test.py
    NEW 2026-09-29. Standalone test for mesh_universal.py.
    Called by run_tests.py.
    TEST.

- leaf_arrangement.py
    Placement engine for Cantilever Leaf.
    ACTIVE.

- nfdm.py
    Old Natural Force Density Method kernel. Iterative nonlinear.
    Wrong method for NFDM. Kept as reference.
    REFERENCE.

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
    NEW 2026-09-29. DXF import design.
    Layer names, file size limits, bay limit.
    DOC.

- SPEC_coordinate_file.md
    NEW 2026-09-29. Coordinate file design.
    Plain CSV, four columns, two loops.
    DOC.

- SPEC_custom_boundary.md
    NEW 2026-09-29. Custom boundary structure design.
    A new structure type that uses DXF or coordinate file.
    DOC.

- SPEC_mesh_universal.md
    NEW 2026-09-29. Universal mesh engine specification.
    The contract for mesh_universal.py.
    DOC.

- SPEC_saddle_viewer_fd.md
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
    NEW 2026-09-29. Universal workshop renderer.
    Reads a recipe. Builds the input page.
    Not yet called by any real workshop.
    ACTIVE (isolated).

- _renderer_test.py
    NEW 2026-09-29. Temporary test page for the renderer.
    Removed after the first real workshop migrates.
    TEST.

- saddle_standard.py
    Cable Supported Saddle workshop.
    Migrated to the recipe pattern 2026-09-29.
    Now 12 lines. Calls render_workshop(STANDARD_SADDLE_RECIPE).
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
    Shape laboratory. Five shape recipes built on the MBS
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
    Updated 2026-09-29: standard_saddle now routes to
    standard_saddle_mbs.
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
    NEW 2026-09-29. MBS version of the Standard Saddle viewer.
    Still builds its own mesh via _build_saddle_mbs.
    To be replaced by a thin viewer that calls
    engine/mesh_universal.py. That is Step 2D.
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

# END OF FILE INVENTORY

Keep this file current. One line per change. Ten seconds
of discipline saves half a day of re-orientation.


