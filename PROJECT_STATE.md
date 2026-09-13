# SDSe Project State

Handoff document. Read this first in any new chat session.
SINGLE SOURCE OF TRUTH for the project.

Last updated: 2026-09-14 (late session)

---

## 1. The Vision

SDSe is a guided structural design tool for tensile membrane,
curved-beam, and cable structures.

User flow: Landing -> Studio -> Registration -> Workshop -> Results.
Clean linear flow. No tabs. Back and home buttons everywhere.

Full flow builds a complete design: 3D view, health score, section
used, quantities, member schedule, exports (DXF, JSON), save/load.

---

## 2. Repo and Deployments

- GitHub repo: OCBC-cloud/sds-app
- Working branch: modular-v10
- Production branch: main
- Streamlit Cloud account: @ocbc-cloud
- Three apps deployed (free tier limit reached):
  1. sds-app . main . app.py            (old production SDSe)
  2. sds-app . main . viewer_app.py     (FDS viewer, starred)
  3. sds-app . modular-v10 . app.py     (modular preview - in development)

---

## 3. Phase Status

Phase A - UI shell - COMPLETE
Phase B - Restore v9.1 rich UI - IN PROGRESS
  Results page being restored feature by feature.
  Quantities section DONE.
  Member Schedule, Anchor Reactions, Foundation panel, Exports
  still to restore.
Phase C - Engine build - PENDING (membrane.py Message 1 done)
Phase D - Wire engine into Results - PENDING
Phase E - Trim to 7 structures - COMPLETE (became 8 mains)
Phase F - Smart Guided Design wizard - PENDING
Phase G - Output module (BQ, schedules) - PENDING
Phase H - DXF import - PENDING
Phase I - Membrane Ribbon (Type 9) - PENDING

---

## 4. CRITICAL WORKFLOW - The Reboot Rule

Whenever the code is correct on GitHub but the app still shows an
error OR shows old behaviour:

REBOOT the app on Streamlit Cloud. Not the browser refresh.

How to reboot:
  1. Open share.streamlit.io
  2. Find the app row: sds-app . modular-v10 . app.py
  3. Tap the three dots (menu) on that row
  4. Tap "Reboot"
  5. Wait 30 seconds
  6. Test the app again

Refreshing the browser tab does NOT reboot the app. Streamlit
keeps Python modules in memory and does not reload them on a
browser refresh.

This has caused MANY false alarms. Always reboot before diagnosing.

---

## 5. iOS Paste Warning

iOS Safari autocorrect and Smart Punctuation can silently mangle
pasted code.

Required settings (already applied):
  Settings > General > Keyboard:
    - Auto-Correction: OFF
    - Smart Punctuation: OFF

Also on GitHub editor:
  - Use "Spaces: 4", "No wrap" (already set)

Even with these off, very long pastes can still corrupt. When
a paste fails, keep lines short. Avoid very long single strings.

Known failure modes observed 2026-09-13 and 2026-09-14:
  - Stray tokens injected mid-string (e.g. `{"` appearing in text)
  - Missing closing quotes on long lines
  - Indent shifts on nested code blocks
  - File silently truncating or reordering lines

Fix: full file replacement. Never surgical edit. Rule 15.

---

## 6. File Structure (branch modular-v10)

Root:
  app.py                     thin entry - 42 lines
  PROJECT_STATE.md           this file
  README.md
  README_MODULAR.md
  physics_engine.py          Phase A catenary (not wired)
  requirements.txt
  run_tests.py               test runner for GitHub Actions
  test_membrane.py           redundant - to be deleted
  viewer_app.py              only on main branch, not modular-v10

.github/workflows/:
  test.yml                   GitHub Actions CI - WORKING

core/:
  __init__.py
  theme.py                   readability-focused CSS
  state.py                   session state init
  navigation.py              router

data/:
  __init__.py
  sections.py
  materials.py
  structures.py              UPDATED 2026-09-13 - 8 mains + variants
  constants.py

engine/:
  __init__.py
  membrane.py                Message 1 done - mesh foundation
  SPEC_saddle_span.md        updated with Section 6A strut geometry

ui/:
  __init__.py
  landing.py                 Landing page
  studio.py                  UPDATED 2026-09-13 - 2 sections, 8 tiles
  registration.py            UPDATED 2026-09-13 - reads data/structures.py
  workshop.py                router for variant workshops
  results.py                 UPDATED 2026-09-13 - Quantities added
  workshops/
    __init__.py
    saddle_standard.py       UPDATED 2026-09-14 - 8 sections, Foundation
    saddle_leaf.py           UPDATED 2026-09-14 - 7 sections, pretension

viewers/:
  __init__.py
  results_viewer.py          UPDATED 2026-09-14 - np.sin fix, vkey dispatch

.streamlit/:
  config.toml

---

## 7. Current Working State

Confirmed working end-to-end:
  - Landing page renders with Enter The Studio button
  - Studio page renders with 2 sections and 8 tiles
  - Registration page reads variants from data/structures.py
  - Workshop router dispatches to Standard Saddle and Cantilever Leaf
  - Cantilever Leaf 3D view renders (column, spine, ribs, strut, membrane)
  - Standard Saddle 3D view renders (two beams, membrane, tie-downs)
  - Results page renders with 3D viewer
  - Health Score card shows 100
  - Section Used card shows section name
  - Analysis Readings section shows 6 metric cards (all --)
  - Quantities section shows 3 cards (all --)

Not yet restored on Results:
  - Member Schedule table
  - Anchor Reactions / Preliminary Foundation
  - Export DXF button
  - Export JSON button
  - Save Design button

Not yet built:
  - Save Design to JSON file (download)
  - Load Design from JSON file (upload)
  - BQ page
  - Reports page
  - Smart Guided Design wizard
  - Foundation output panel on Results page

---

## 8. Structure Types - FINAL 8 MAINS

Reduced from 27 legacy types to 8 final mains on 2026-09-13.
Membrane Ribbon (Type 9) is Phase 2.

### Type 1: Saddle Span
  - Standard Saddle (workshop built)
  - Frame Supported Saddle (workshop not built)

### Type 2: Cantilever
  - Cantilever Leaf (workshop built)
  - Cantilever Flower (coming soon)
  - Cantilever Cone (workshop not built)
  - Cantilever Pyramid (workshop not built)
  - Cantilever Bell (workshop not built)
  - Cantilever Sail (workshop not built)
  - Cantilever Hypar (workshop not built)

### Type 3: Uni-Pole Tensile Roof
  - Single Cone
  - Multi-Cone Cluster
  - Umbrella

### Type 4: Tensile Sails Roof
  - Hypar Sail - 3 Anchors
  - Hypar Sail - 4 Anchors
  - Multiple Wall-Anchored Sails
  - Multiple Column-Mounted Sails

### Type 5: Framed Tensile Roof
  - Simple Frame + Fabric
  - Arched Frame + Fabric
  - Trussed Frame + Fabric

### Type 6: Canopy
  - Wall-Mounted Shade
  - Cable-Supported Shade
  - Tree Canopy (coming soon)

### Type 7: Frame Tent
  - Pyramid Tent
  - Modular Tent
  - Cone Tent
  - A-Frame Tent
  - Arch Tent

### Type 8: Portal Frame
  - Simple Portal
  - With Mezzanine
  - With Crane
  - Multi-Bay Portal

### Type 9 (Phase 2): Membrane Ribbon
  - Future

Key decisions:
  - Cantilever is its own main type (agreed 2026-09-13)
  - Leaf and Flower moved out of Saddle Span into Cantilever
  - Ridge Sail dropped (unclear definition)
  - Hip Tent dropped (not required)
  - Hypar appears under both Tensile Sails and Cantilever
    (intentional - spanning-between-anchors vs single-column)
  - Umbrella kept separate from Single Cone

---

## 9. Studio Page Layout - 2 SECTIONS

Agreed 2026-09-13.

Smart Guided Design tile at top (orange gradient)

### Section A - Tensile and Membrane (5 tiles)
  1. Saddle Span
  2. Cantilever
  3. Uni-Pole Tensile Roof
  4. Tensile Sails Roof
  5. Framed Tensile Roof

### Section B - Canopy and Frame (3 tiles)
  6. Canopy
  7. Frame Tent
  8. Portal Frame

Studio reads tiles from data/structures.py.
Tiles are defined in STUDIO_SECTION_A and STUDIO_SECTION_B lists
in ui/studio.py.

---

## 10. Canonical Data - data/structures.py

Single source of truth for structure types and variants.

Two dicts:
  STRUCTURE_TYPES    - main structure types (8 in Phase 1)
  STRUCTURE_VARIANTS - sub-types under each main type

Three helpers:
  get_structure(key)          returns structure dict or None
  get_variants(key)           returns list of variant dicts
  get_all_categories()        returns sorted list of categories

Used by:
  ui/studio.py                (imports STRUCTURE_TYPES)
  ui/registration.py          (imports STRUCTURE_VARIANTS)

Variant dict format:
  {"key": "...", "name": "...", "description": "...",
   "available": True/False}

"available": False shows the "Coming Soon" badge in Registration.

---

## 11. Workshop Section Standard

Agreed 2026-09-14. EVERY workshop must follow this pattern.

Standard sections (in this order):
  1. Geometry
  2. Materials
  3. Members / Column and Spine
  4. Supports / Ribs
  5. Ties / Attachment / Pretension
  6. Baseplate and Preliminary Foundation
  7. Loads and Design Standard
  8. Attachment (if applicable)

Rules:
  - Section 6 (Foundation) is present in EVERY workshop
  - Section 7 (Loads) is present in EVERY workshop
  - Section count can vary from 7 to 9 depending on structure
  - Headers use the amber accent style
  - Help text under each header explains the section

Foundation section content (identical everywhere):
  - Assumed Soil Bearing Capacity (kN/m2) - default 150
  - Water Table Depth (m)
  - Soil Type (sand / clay / rock / filled)
  - Foundation Type (pad / pile / raft)
  - Warning: "Geotechnical verification required. Engage a
    geotechnical engineer to confirm."

---

## 12. Form-Finding Workflow - Industry Practice

Researched 2026-09-14.

Industry tools (Easy, RFEM with RF-FORM-FINDING, RhinoMembrane,
ixCube) all work the same way:

  1. User defines boundary conditions (support positions, etc.)
  2. User defines TARGET membrane stress and cable tension
  3. Form-finding solver (Force Density Method or Dynamic
     Relaxation) finds the shape that is in equilibrium
  4. The resulting geometry IS the design - the shape emerges,
     it is not drawn
  5. Analysis is then run on the found shape
  6. Patterning flattens the 3D shape into 2D cutting patterns

Key principle: pretension is NOT a shape control. It is a
target stress state. The solver produces geometry as a result.

Applied to SDSe:
  - Workshop collects membrane pretension (kN/m) and cable
    pretension (kN) as TARGET values
  - Engine (Phase C) will solve for the equilibrium shape
  - No fixed segment spacing on edge cables - the solver places
    segment boundaries where the membrane geometry demands
  - Perimeter cable follows the membrane natural edge
  - Cable ends attach to the tips of the outermost ribs

Membrane pretension default: 2.0 kN/m, range 0.5 to 8.0
Cable pretension default: 5.0 kN, range 0.5 to 50.0

---

## 13. Saddle Span Specification

Written to engine/SPEC_saddle_span.md.

### Standard Saddle - members
  - Membrane
  - Beam (single member OR planar truss OR 3D truss)
  - Cable (tie-downs)
  NO column. NO ribs. NO purlins.

  Beam options:
    single member beam     - one row in member schedule
    planar truss           - top, bottom, vertical, diagonal chord
    3D truss               - top, bottom, vertical, horizontal,
                             diagonal chord

### Frame Supported Saddle - members
  - Membrane
  - Beam (single OR planar truss OR 3D truss)
  - Purlins (single OR planar truss OR 3D truss)
  - Strut (rigid support replaces tie-down action)
  - Cable
  NO column. NO ribs.

### Cantilever Leaf / Flower - members
  - Membrane
  - Column (uni-pole mast)
  - Ribs
  - Cable (perimeter)
  NO beam. NO purlins. NO strut.
  (The column spine IS the beam)

### Truss member breakdown
  Planar truss  = top chord + bottom chord + vertical chord
                  + diagonal chord
  3D truss      = top chord + bottom chord + vertical chord
                  + horizontal chord + diagonal chord

Member schedule displays each chord type as its own row
when present.

### Chief's reference case - 10m x 10m Leaf prototype
  Column: CHS 323.8 x 8, height 10m
  Outreach: 10m
  Ribs per side: 7
  Rib tilt: 20 deg
  Main beam: CHS 168.3
  Edge cables: SS 6x19, 8mm
  Fabric: PVC Ferrari S702
  Governing action: TORSION
  Critical member: small rib near column

### Section 6A - strut joint height
  FIXED at 75% of column height (updated 2026-09-14)
  No user input. Engine assigns automatically.
  Higher joint reduces moment transfer to baseplate.
  For a 10m column: strut joint = 7.50 m

### Silent rules (never shown to user)
  1. Membrane slope minimum:
     18 deg for small exposed surfaces (area <= 100 m2 or
     dim <= 15m)
     23 deg for large exposed surfaces
  2. Pre-tension retention
  3. Shape fidelity (min 5 ribs per side for leaf)

### Country safety factors
  Table for EU / MY / UK / CN / US.
  MY uses gamma_Q = 1.5 per MS EN 1990.

---

## 14. Tie-down Cables - Lock-in Rule

Tie-down cables are mandatory for Standard Saddle and Frame
Supported Saddle. Not used on Cantilever Leaf (cantilever).

Required inputs:
  - Number of Tie-down Intervals
  - Anchor Uplift Angle (default 45 deg)
  - Anchor Spread Angle (default 30 deg)
  - Cable Type (6x19 / locked coil / spiral)
  - Cable Material (galvanised / stainless)
  - Cable Diameter (always auto - engine selects)
  - Ground Anchor Type (pinned / rigid)

Anchor geometry:
  - Attach points along the beam, distributed across outer 70%
    of span (t_min=0.15, t_max=0.85)
  - Anchor is offset in BOTH x and y from the beam attach point
  - X offset pushes outward along the span, away from centre
  - Y offset pushes outward from the beam
  - Both offsets computed from uplift angle and spread angle
  - Pattern is symmetric about both axes
  - Visual effect: fence perimeter around the structure

Engine will compute optimal attach points at form-finding time.

---

## 15. Foundation - Preliminary Sizing

Applies to ALL structures (Section 6 of every workshop).

Inputs:
  - Assumed Soil Bearing Capacity (kN/m2) - default 150
  - Soil Type (sand / clay / rock / filled)
  - Water Table Depth (m)
  - Foundation Type (pad / pile / raft)

Outputs (on Results page - not yet built):
  - Preliminary pad size = Reaction / Bearing capacity
  - Note: "Subject to geotechnical verification. Reinforcement
    and detailing not provided. Engage a geotechnical engineer."

Full Foundation engine (System F) - later phase.

---

## 16. Build Philosophy (Locked Rules)

1. Plain Python dicts. No dataclasses. No type hints.
2. mm-based section units (A mm2, I mm4, W_el mm3, i mm)
3. HTML strings built as named variables with explicit +
   on every line. Never mix implicit literal concatenation
   with variable interpolation inside st.markdown().
4. ASCII only in code. Use HTML entities for non-ASCII.
5. Two blank lines at end of every delivered chunk.
6. One file per chunk. One commit per file.
7. Verify each phase before moving to the next.
8. Every commit triggers GitHub Actions test.
9. Silent rules never shown to users.
10. Edit viewer_app.py or dxf_export.py on main.
11. Edit app.py or data/ or core/ or engine/ or ui/ or viewers/
    on modular-v10.
12. Once a structure is tested, promote to main as NEW - not
    as a replacement.
13. Each structure type has its own preset inputs, calculations,
    displays, format.
14. After every commit, REBOOT the Streamlit Cloud app.
15. FULL FILE REPLACEMENTS ONLY. No surgical edits. iOS Safari
    mangles pasted code unpredictably. A full-file replacement
    is always safer than hunting for one bad character.
16. Viewer dispatches on variant_key alone. Variant keys are
    globally unique. The viewer never checks structure_key.
17. All variants read from data/structures.py. No hardcoded
    VARIANTS_FALLBACK in ui/registration.py.

---

## 17. CI Infrastructure

GitHub Actions - WORKING.

Workflow: .github/workflows/test.yml
Runner: run_tests.py

On every push to main or modular-v10, tests run.
Green checkmark = pass. Red X = fail.
Free. Private. No Streamlit needed.

---

## 18. engine/membrane.py - Message 1 COMPLETE

Verified by GitHub Actions 2026-09-12.

What was built:
  - Mesh data structure (create_mesh)
  - Geometry helpers (edge_length, edge_vector, count_neighbours)
  - Flat grid builder (build_flat_grid)
  - Self-test (_verify_mesh_handling)

Next:
  - Message 2: Force Density Method solver
  - Message 3: Newton-Raphson load application
  - Message 4: Stress extraction

---

## 19. Refinements List (Running)

R-01 - Registration page: remove placeholder text from
        Project Name, Client Name, Project Reference, Engineer.
        Keep placeholder on Location.
        Status: not yet applied.

R-02 - Date field automatic (datetime.now()).
        Status: APPLIED 2026-09-13.

R-03 - App jumps to landing when tapping outside input fields.
        Status: unresolved.

R-04 - Non-functional interactions (buttons).
        Status: noted, may be by design.

R-05 - Tie-down anchor geometry: anchors radiate outward
        radially from centre.
        Status: APPLIED 2026-09-13.

R-06 - Fix math.sin crash in Leaf strut geometry.
        Status: APPLIED 2026-09-14 (np.sin).

R-07 - Fix Leaf workshop indent error at line 333.
        Status: APPLIED 2026-09-14 (full rebuild).

R-08 - Lock strut joint at 75% of column height.
        Status: APPLIED 2026-09-14.

R-09 - Add pretension inputs to Leaf and Standard Saddle.
        Status: APPLIED 2026-09-14.

R-10 - Add Foundation section to Standard Saddle.
        Status: APPLIED 2026-09-14.

R-11 - Remove fixed segment spacing from edge cables.
        Status: APPLIED 2026-09-14. Replaced by form-finding note.

R-12 - Workshop section standard locked (8 sections).
        Status: APPLIED 2026-09-14.

---

## 20. Next Actions (in order)

1. Test Saddle Span -> Standard Saddle full flow end to end.
   Check that all 8 sections render and 3D view draws.

2. Test Cantilever -> Cantilever Leaf full flow end to end.
   Check that all 7 sections render and 3D view draws.

3. Restore the next Results page feature - Member Schedule.
   Must show only the members relevant to that structure +
   variant combination. See Section 13 for member composition
   rules. Schema to be defined per structure.

4. Restore Anchor Reactions / Preliminary Foundation panel
   on Results page.

5. Restore Export DXF and Export JSON buttons.

6. Build Save Design (JSON download) and Load Design
   (JSON upload). See Section 21.

7. Build BQ page and Reports page.

8. Continue engine build (membrane.py Message 2:
   Force Density Method).

9. Build workshops for the remaining structure variants.
   Each must follow the 8-section standard.

---

## 21. Save Design Feature (Planned)

Current state: nothing is saved. Refresh loses everything.

Solution: Save Design as JSON download + Load Design upload.

Save Design:
  - Downloads a .json file with all workshop inputs +
    project_info + structure_key + variant_key + date
  - Filename: project_{ref}_{timestamp}.json

Load Design:
  - Upload .json file
  - Restores all session state
  - Jumps to Results

Applies to all structure types. Same file format.
Implementation: ~50 lines. To be added to ui/results.py and
either ui/landing.py or ui/studio.py.

---

## 22. The Five Systems Engine Architecture

Every structure reduces to a small number of fundamental
structural systems.

  System A - Tension Membrane (cable net)
  System B - Cable + Masts / Struts
  System C - Frame / Beam (bending)
  System D - Arch / Curved Beam (combined)
  System E - Truss (axial)

Recipe concept: each structure type is a combination of systems.

  Saddle Span       A + D
  Tensile Sails     A + B
  Framed Tensile    A + C
  Uni-Pole Tensile  A + B
  Cantilever        A + B (with bending in the arm)
  Canopy            A + C
  Frame Tent        A + C
  Portal Frame      C only

Engine modules planned:
  membrane.py       System A (Message 1 done)
  cable_mast.py     System B
  frame.py          System C
  arch.py           System D
  truss.py          System E
  recipes.py        dispatchers
  ec_checks.py      EN 1993 helpers
  output.py         schedules, health, alerts, BQ
  formfind.py       Force Density Method solver (Phase C)

---

## 23. Owner

Chief. First-time app builder.
iPhone + GitHub web editor + Streamlit Cloud.
No terminal. No local Python environment.
Needs step-by-step guidance with screenshots.
Prefers full file replacements over surgical edits.

---

## 24. Document History

Created: 2026-09-11 (Phase 1 handoff)
Updated: 2026-09-12 - Phase 1 complete, CI running, membrane
         Message 1 done
Updated: 2026-09-13 - UI flow spec, variant mapping,
         tie-down rules, strut geometry, Phase A nearly
         complete, most features restored on Results page,
         two pending fixes, reboot workflow established
Updated: 2026-09-14 - Structure list reduced to 8 mains.
         Cantilever promoted to main type. Studio now 2
         sections. Registration reads from data/structures.py.
         Viewer dispatches on variant_key. Fixed math.sin and
         indent crashes in Leaf. Strut joint locked at 75%.
         Pretension inputs added. Foundation section added to
         Standard Saddle. Both workshops follow the 8-section
         standard. Form-finding workflow researched and
         documented. Full-file replacement rule (Rule 15)
         reinforced after iOS paste damage.

---

End of project state.
