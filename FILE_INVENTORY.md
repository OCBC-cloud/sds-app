# SDSe — FILE INVENTORY

Plain, factual list of every file in the repository. Read
alongside PROJECT_STATE.md. Updated whenever a file is added,
renamed, deleted, or its public interface changes.

Status values:
  ACTIVE     — used by the app right now.
  REFERENCE  — kept for the future, not called by anything.
  DOC        — documentation.

Last updated: 2026-09-25.

---

# ROOT

- app.py
    Streamlit entry point. Bootstraps theme, session state,
    and dispatches to the router.
    ACTIVE.

- run_tests.py
    Test runner for GitHub Actions. Runs the two engine tests.
    MBS test removed temporarily (2026-09-25).
    ACTIVE.

- requirements.txt
    Python dependencies for Streamlit Cloud.
    ACTIVE.

- physics_engine.py
    Legacy physics module. Superseded by engine/form_finding.py.
    Not called by the current app.
    REFERENCE.

- viewer_app.py
    Legacy viewer. Superseded by viewers/results_viewer.py.
    Not called by the current app.
    REFERENCE.

- PROJECT_STATE.md
    Single source of truth. Constitution, method, current
    state, next actions.
    DOC.

- PROJECT_VISION.md
    North star. Purpose, scope, engine architecture, roadmap.
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
    Section property catalogue (CHS, SHS, RHS, I-beam).
    ACTIVE.

- structures.py
    STRUCTURE_TYPES, STRUCTURE_VARIANTS, MEMBER_SCHEMA.
    Canonical definition of every structure in the app.
    ACTIVE.

---

# /engine/

The physics and engineering modules. Each one is either a
numerical solver, a geometry engine, or a specification document.

- __init__.py
    Package marker.
    ACTIVE.

- form_finding.py
    FDM solver. solve_fdm() and mesh_size_for_shape().
    Linear form-finding. Core of the shape engine.
    ACTIVE.

- membrane.py
    System A helper. Mesh handling utilities.
    Used by run_tests.py.
    ACTIVE.

- membrane_boundary.py
    Membrane Boundary Schema (MBS) engine. Builds a triangular
    membrane mesh from a closed boundary, anchors, and edge
    types. Calls solve_fdm. New file. Under test.
    ACTIVE.

- leaf_arrangement.py
    Placement engine for Cantilever Leaf. Single, double,
    multiple, tree_stack, tiered_helix.
    ACTIVE.

- nfdm.py
    Natural Force Density Method kernel. Iterative nonlinear
    formulation. NOT the published linear NFDM. Not called
    by anything. Kept as reference for a future linear rewrite.
    REFERENCE.

- render_prompts.py
    Marketing render prompt engine. Shape sentence, scene,
    lighting. Bing-safe character limit.
    ACTIVE.

- MEMBRANE_GUIDE.md
    The membrane principle. Boundary families, drawing rules,
    per-structure reference. Doctrine document.
    DOC.

- PLACEHOLDERS.md
    Single source of truth for inputs waiting for the FDM
    and structural engines.
    DOC.

- SPEC_engine_chain.md
    The seven-link chain: SHAPE, LOADS, FORCES, SIZES,
    QUANTITIES, REPORT, CATALOGUES.
    DOC.

- SPEC_cantilever_hypar.md
    Full specification of the Cantilever Hypar variant.
    DOC.

- SPEC_saddle_span.md
    Saddle Span structure specification.
    DOC.

- SPEC_saddle_viewer_fd…
    Saddle viewer FDM specification.
    DOC.

---

# /ui/

Page-level Streamlit modules.

- __init__.py
    Package marker.
    ACTIVE.

- landing.py
    Splash screen. Two buttons: Enter The Studio, Open MBS Tester.
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
    Results page. 3D viewer, summary, marketing render section.
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

One file per variant. Each defines a render_*() function.

- __init__.py
    Package marker.
    ACTIVE.

- _shared.py
    Shared workshop CSS and helper functions
    (section_header, render_breadcrumb, preview_box, etc.).
    ACTIVE.

- saddle_standard.py
    Cable Supported Saddle workshop. Warp, weft, edge cable
    pretension as number fields. Free-end toggle removed.
    ACTIVE.

- saddle_frame.py
    Beam Supported Saddle workshop.
    ACTIVE.

- saddle_leaf.py
    Cantilever Leaf workshop. Five arrangements.
    ACTIVE.

- saddle_hypar.py
    Cantilever Hypar workshop.
    ACTIVE.

- tester_mbs.py
    MBS engine tester. Temporary. Runs the MBS engine on a
    small saddle and displays diagnostics. Experimental.
    ACTIVE (temporary).

---

# /viewers/

Viewer dispatcher and figure builders.

- __init__.py
    Package marker.
    ACTIVE.

- results_viewer.py
    Dispatcher. Routes on variant_key to the correct figure
    builder.
    ACTIVE.

---

# /viewers/figures/

One file per variant. Each builds a Plotly figure.

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
    Cable Supported Saddle viewer. FDM-solved mesh. Has the
    known fold. Diagnostics block present.
    ACTIVE.

- beam_supported_saddle…
    Beam Supported Saddle viewer. Draws surface from a
    formula. Does not call solve_fdm. To be migrated.
    ACTIVE (needs migration).

- cantilever_hypar.py
    Cantilever Hypar viewer. Draws a Coons patch. Does not
    call solve_fdm. To be migrated.
    ACTIVE (needs migration).

- cantilever_leaf.py
    Cantilever Leaf viewer. Draws. Uses leaf_arrangement.
    ACTIVE.

---

# /.github/workflows/

- test.yml
    GitHub Actions workflow. Runs run_tests.py on push to
    main and modular-v10.
    ACTIVE.

---

# /.streamlit/

- config.toml
    Streamlit configuration (theme, layout).
    ACTIVE.

---

# /data — deleted from _shared list

Note: `data/` folder contains no `_shared.py`. Listed above
in the correct section.

---

# END OF FILE INVENTORY

Keep this file current. One line per change. Ten seconds of
discipline saves half a day of re-orientation.





