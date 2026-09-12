# SDSe Project State

Handoff document. Read this first in any new chat session.
This is the SINGLE SOURCE OF TRUTH for the project.

Last updated: 2026-09-12

---

## 1. The Vision (in plain words)

SDSe is a guided structural design tool for tensile membrane,
curved-beam, and cable structures.

A user opens the app, enters a project, picks a structure type
and variant, enters the relevant inputs, taps one button, and
receives a complete design: 3D view, health score, member
sections, quantities, and exportable outputs (DXF).

The app has a clean linear flow. No tabs. No jumping between
screens. Every step is one choice. Every page has a back button
and a home button.

---

## 2. The App Flow (agreed)

### Page 1 - LANDING (Impact Page)
- Beautifully designed, sets the tone for the whole app
- Introduces the app
- One button only: "ENTER"
- No scrolling
- Clean and dramatic

### Page 2 - STUDIO (Structure Type Selection)
- Replaces the landing page (abrupt transition)
- Long scrollable page
- Grid of available structure types (final: 7)
- Each tile: name, icon, one-line description
- Plus a separate "Smart Guided Design" tile
- Tapping a structure type advances to Registration
- Tapping Guided Design starts the wizard

### Page 3 - REGISTRATION (Project + Variant)
- Replaces the studio page
- Top: project meta inputs
  - Project Name
  - Client Name
  - Location
  - Reference
  - Engineer
  - Date
- Middle: variant selection for this structure type
  - Example: Saddle Span -> A) Cable Supported, B) Frame Supported,
    C) Leaf, D) Cantilevered
  - Each variant has a short description
- Tapping a variant advances to the Workshop

### Page 4 - WORKSHOP (Inputs for this structure + variant)
- Replaces the registration page
- Top bar: breadcrumb - Project name / Structure type / Variant
- Body: all inputs for this structure type + variant
  - Grouped into collapsible sections:
    Geometry, Materials, Members, Supports, Loads
  - Field names are clear and unambiguous:
    "Rise" not "A", "Span Distance" not "B",
    "Apex-to-Apex Distance" not "LAA",
    "Number of Tie-down Cable Intervals" not "num_bays"
  - No abbreviations. No internal keys. Human language.
- Bottom: "Intelligent Design Computing" button
- Back button returns to Registration

### Page 5 - RESULTS
- Replaces the workshop
- 3D viewer at top (shared viewer, adapts to structure type)
- Health indicator (large, prominent)
- Section used (auto-selected member from engine)
- Essential analysis readings (forces, stresses, utilisation)
- Quantities table: membrane, steel, cables, all members
- Export buttons: DXF, JSON, Report
- Actions: Save design, Run again with different inputs
- Back button returns to Workshop (inputs preserved)
- Home button returns to Studio

### Smart Guided Design (Alternative Path)
- 7-10 questions, each on its own screen
- Purpose, span, environment, aesthetic, permanence, budget
- At the end: recommends structure type + variant
- Drops user directly into Workshop with inputs pre-filled

---

## 3. Navigation Rules

- Every page has a back button
- Every page has a home button (returns to Studio)
- Back button preserves state - no resetting
- Back button is context-aware:
  - From Results -> back to Workshop (inputs preserved)
  - From Workshop -> back to Registration
  - From Registration -> back to Studio
  - From Studio -> back to Landing

---

## 4. Structure Types (final target - 7)

1. Saddle Span
2. Tensile Sails Roof
3. Framed Tensile Roof
4. Uni-Pole Tensile Roof
5. Canopy
6. Frame Tent
7. Portal Frame

Each structure type has one or more variants.
Each variant has its own input page and its own engine recipe.

Current catalogue has 27 entries. Will be trimmed to these 7.

---

## 5. Variants (examples - to be finalised)

- Saddle Span: Cable Supported, Frame Supported, Leaf, Cantilevered
- Portal Frame: Simple, With Mezzanine, With Crane
- (Others to be specified per structure type)

---

## 6. Build Sequence (agreed)

### Phase A - UI Shell
- Landing page
- Studio page
- Registration page
- Workshop (placeholder inputs)
- Results (placeholder data)
- Full navigation with back and home buttons
- Nothing real yet, but the flow exists
- Advantage: user experiences the finished shape of the app early
- Feedback on flow happens before engine is done

### Phase B - Restore v9.1 Rich Behaviour
- Working 3D viewer (FDS viewer incorporated)
- Sensible placeholder results
- Health indicator with real numbers
- Section recommendations that make sense

### Phase C - Build the Engine
- engine/membrane.py (System A - in progress)
- engine/cable_mast.py (System B)
- engine/frame.py (System C)
- engine/arch.py (System D)
- engine/truss.py (System E)
- Combined Action engine (merges C, D, E for steel members)

### Phase D - Wire Engine In
- Workshop button calls real engine
- Results page shows real numbers

### Phase E - Trim to 7 Structures
- One workshop per structure type
- One variant per variant
- Catalogue trimmed from 27 to 7

### Phase F - Smart Guided Design Wizard
- 7-10 question flow
- Recommends structure + variant
- Drops user into Workshop

### Phase G - Output Module
- Member schedule
- Joint schedule
- Health alerts
- Full Bill of Quantities
- Report generation

### Phase H - DXF Import and Round-Trip
- Import DXF back into SDSe
- Edit in CAD, re-import, refine

---

## 7. The Five Systems Engine Architecture

Every structure reduces to a small number of fundamental
structural systems. Shapes are cosmetic; actions are physical.

### The Five Systems

- System A - Tension Membrane (cable net)
- System B - Cable + Masts / Struts
- System C - Frame / Beam (bending)
- System D - Arch / Curved Beam (combined)
- System E - Truss (axial)

### The Recipe Concept

A structure type is a recipe over the five systems.

| Structure | Systems used |
|---|---|
| Saddle Span | A + D |
| Tensile Sails Roof | A + B |
| Framed Tensile Roof | A + C |
| Uni-Pole Tensile Roof | A + B |
| Canopy | A + C |
| Frame Tent | A + C |
| Portal Frame | C only |

### Engine Module Plan

engine/
- membrane.py       System A
- cable_mast.py     System B
- frame.py          System C
- arch.py           System D
- truss.py          System E
- recipes.py        structure dispatchers
- ec_checks.py      EN 1993 resistance helpers
- output.py         schedules, health, alerts, BQ

---

## 8. The 3D Viewer Strategy

- Preference: ONE viewer serving all structure types
- The FDS Viewer Prototype v3.2 becomes this unified viewer
- The viewer takes structure type + inputs as parameters
- It dispatches to the correct geometry generator per type
- If a shared viewer would disturb other structures' presets,
  inputs, calculations, or displays, then create an additional
  separate viewer window instead of disturbing existing behaviour
- Single viewer strongly preferred

---

## 9. Current Repository State

Repo: OCBC-cloud/sds-app

### Branch: main
- Live SDSe app (sahfpaexbknah.streamlit.app) - deployed from app.py
- FDS Viewer (sahfpaexbknah.streamlit.app) - deployed from viewer_app.py
- dxf_export.py - DXF export module (working)
- requirements.txt - includes ezdxf

### Branch: modular-v10
- 22 commits ahead of main, 9 commits behind
- Phase 1 modular rebuild (COMPLETE and verified)
- Saddle Span spec written
- engine/membrane.py Message 1 (mesh foundation, verified)
- GitHub Actions CI (test.yml) - working
- run_tests.py - test runner
- PROJECT_STATE.md - this file

### Streamlit Cloud Account
- 3 apps deployed (free tier limit reached)
- Cannot create new apps without deleting one

---

## 10. Phase 1 - Modular Rebuild (COMPLETE)

Verified working on modular-v10 branch and modular-preview app.

### Files on modular-v10

Root:
- app.py
- README.md
- README_MODULAR.md
- PROJECT_STATE.md (this file)
- physics_engine.py (Phase A catenary, not wired)
- requirements.txt
- test_membrane.py (redundant, to be deleted)
- run_tests.py

.github/workflows/:
- test.yml (GitHub Actions)

data/:
- __init__.py
- sections.py
- materials.py
- structures.py
- constants.py

core/:
- __init__.py
- theme.py
- state.py

engine/:
- __init__.py
- membrane.py
- SPEC_saddle_span.md

.streamlit/:
- config.toml

---

## 11. Known Issues (to fix in future phases)

### Regression from Phase 1
The modular rebuild (app.py on modular-v10) reduced v9.1's rich UI:
- Rich 3D saddle span viewer with tie-down cables - LOST
- Detailed results display - LOST
- Real health indicator - LOST (currently hardcoded 100)
- Member schedule - LOST
- Quantity takeoff display - LOST
- Deflection display - LOST

These will be RESTORED in Phase B.

### Live app issues (on main)
- 3D viewer shows flat yellow surface (not proper saddle)
- Standard defaults to CN instead of MY
- Oversized section recommendations
- Health score 0.0 inconsistent with passing checks
- Haphazard interface layout

These will be REPLACED by the new UI flow (Phase A)
and the engine (Phase C).

### FDS Viewer issues
- Membrane is faceted (30x30 grid)
- Ribs-cable alignment minor gaps
- Strut is a polyline (not smooth curve)
- Baseplate is a point
- No member sizes yet

These are cosmetic and will be refined as needed.

---

## 12. GitHub Actions - CI Infrastructure

WORKING.

Workflow: .github/workflows/test.yml
Runner: run_tests.py

On every push to main or modular-v10, tests run automatically.
Green checkmark = pass. Red X = fail.
Free, private, no Streamlit needed.

Known warning: Node.js 20 deprecation (harmless).

---

## 13. Phase 4A - engine/membrane.py - Message 1 COMPLETE

Verified by GitHub Actions on 2026-09-12.

What was built:
- Mesh data structure (create_mesh)
- Geometry helpers (edge_length, edge_vector, count_neighbours)
- Flat grid builder (build_flat_grid)
- Self-test (_verify_mesh_handling)

All tests pass.

Next: Message 2 - Force Density Method solver.

---

## 14. Saddle Span Specification

Written to engine/SPEC_saddle_span.md on modular-v10.

### Three Sub-types
1. Standard Saddle Span
2. Cantilevered Saddle Span (<= 6m x 6m)
3. Leaf Variant (<= 6m x 6m)

### Chief's Reference Case - 10m x 10m Leaf
- Column: CHS 323.8 x 8, height 10m
- Outreach: 10m
- Ribs per side: 7
- Rib tilt: 20 deg
- Rib spacing: 45 deg
- Main beam: CHS 168.3
- Ribs: CHS 168.3 to CHS 76
- Edge cables: SS 6x19, 8mm
- Fabric: PVC Ferrari S702
- Governing action: TORSION
- Critical member: small rib near column

### Silent Rules (never shown to user)
1. Membrane slope minimum:
   - 18 deg for small exposed surfaces (area <= 100 m2 or dim <= 15m)
   - 23 deg for large exposed surfaces
2. Pre-tension retention
3. Shape fidelity (min 5 ribs per side for leaf)

### Country Safety Factors
Per-standard table for EU / MY / UK / CN / US.
MY uses gamma_Q = 1.5 (MS EN 1990).

---

## 15. Build Philosophy (Rules Locked In)

1. Plain Python dicts, no dataclasses, no type hints
2. mm-based section units (A mm2, I mm4, W_el mm3, i mm)
3. HTML strings built as named variables with explicit +
   on every line. Never mix implicit literal concatenation
   with variable interpolation inside st.markdown().
4. ASCII only in code. Use HTML entities for non-ASCII.
5. Two blank lines at the end of every delivered chunk.
6. One file per chunk. One commit per file.
7. Verify each phase before moving to the next.
8. Every commit triggers GitHub Actions test.
   Wait for green before proceeding.
9. Silent rules are never shown to users.
10. Any edit to viewer_app.py or dxf_export.py is on main.
11. Any edit to app.py or data/ or core/ or engine/ is on modular-v10.
12. Once a structure type is tested and stable, it is promoted
    to main as a new structure type - NOT as a replacement.
13. Each structure type has its own preset inputs, calculations,
    displays, and format.

---

## 16. Privacy Decision

Made 2026-09-12: Keep repo and apps public during development.
Lock down later when there is something worth protecting.
Do not raise this question again unless Chief brings it up.

---

## 17. Owner

Chief. First-time app builder.
Uses iPhone + GitHub web editor + Streamlit Cloud.
No terminal, no local Python environment.
Needs step-by-step guidance with screenshots.

---

## 18. How to Resume in a New Chat

Paste this entire file into a new chat, then add:

"Resuming SDSe. Phase A - building the UI shell.
Landing, Studio, Registration, Workshop, Results.
No code yet - confirm you have read this file and are
aligned with the plan."

The new chat will confirm three things:
1. Repo: OCBC-cloud/sds-app
2. Branch: modular-v10 (working) and main (production)
3. Current phase: Phase A - UI shell

Then wait for Chief's go-ahead.

---

## 19. Document History

- Created: 2026-09-11 (Phase 1 handoff)
- Updated: 2026-09-12 (evening) - Phase 1 complete, CI in place,
  engine/membrane.py Message 1 done
- Updated: 2026-09-12 (late evening) - UI flow specification agreed,
  build sequence locked in, this document expanded to full
  vision + architecture + state

---

End of project state.
