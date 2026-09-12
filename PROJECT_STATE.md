# SDSe Project State

Handoff document. Read this first in any new chat session.
This is the SINGLE SOURCE OF TRUTH for the project.

Last updated: 2026-09-13

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
- One button only: "Enter The Studio"
- No scrolling
- Title: SDSe
- Subtitle: Intelligent Fluid Design / Workplace
- Brand line: SDSe Fluid Design Studio
- Footer: All Major EN Code

### Page 2 - STUDIO (Structure Type Selection)
- Replaces the landing page
- Long scrollable page
- Grid of available structure types (final: 7)
- Each tile: icon (letter in circle) + name + description
- Plus a separate "Smart Guided Design" tile at top (orange gradient)
- Small SDSe wordmark top-left
- No back button (landing is a splash screen)

### Page 3 - REGISTRATION (Project + Variant)
- Replaces the studio page
- Top: project meta inputs (name, client, location, reference,
  engineer, date)
- Middle: variant selection for the chosen structure type
- Tapping a variant advances to Workshop
- Back button returns to Studio

### Page 4 - WORKSHOP (Inputs for this structure + variant)
- Replaces the registration page
- Breadcrumb: SDSe Fluid Design Studio / Structure / Variant
- Project header: name, client
- Collapsible input sections:
  Geometry, Materials, Members, Supports, Loads, Attachment,
  Baseplate/Foundation
- Mixed widgets: numbers for dimensions, sliders for angles,
  selectboxes for discrete choices
- Custom-styled section headers (accent orange)
- Inline validation with warnings
- Back button returns to Registration
- "Intelligent Design Computing" advances to Results

### Page 5 - RESULTS
- Replaces the workshop
- Breadcrumb at top
- Project header
- 3D viewer (from viewers/results_viewer.py)
- Health score card (placeholder until engine connected)
- Section used (placeholder until engine)
- Analysis readings: N_Ed, M_Ed, V_Ed, wind pressures,
  deflection (placeholder)
- Member schedule (geometric data real; sections auto)
- Quantities: steel weight, cable length, fabric area
- Preliminary Foundation panel (leaf)
- Anchor Reactions panel (standard saddle)
- Export: DXF (placeholder), JSON (working)
- Save Design (disabled, "coming soon")
- Back to Workshop, Home buttons

### Smart Guided Design (Alternative Path)
- 7-10 questions, each on its own screen
- Purpose, span, environment, aesthetic, permanence, budget
- At the end: recommends structure type + variant
- Drops user directly into Workshop with inputs pre-filled
- NOT YET BUILT

---

## 3. Navigation Rules

- Every page has a back button
- Every page has a home button (returns to Studio)
- Back button preserves state - no resetting
- Back button is context-aware

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

Plus, Phase 2 addition:
8. Membrane Ribbon (future - see Section 22)

---

## 5. Variant Mapping (FINAL)

### Saddle Span family
- A) Standard Saddle (built)
- B) Frame Supported Saddle (not built)
- C) Cantilever Leaf (built, DXF export works)
- D) Cantilever Flower (future vision)

### Tensile Sails Roof family (CORRECTED 2026-09-13)
- A) Hypar Sail - 3 Anchors (not built)
- B) Hypar Sail - 4 Anchors (not built)
- C) Ridge Sail (not built)
- D) Multiple Sails (not built)
- E) Wall Sail (not built)
- F) Column Sail (not built)

### Framed Tensile Roof family
- A) Simple Frame + Fabric (not built)
- B) Arched Frame + Fabric (not built)
- C) Trussed Frame + Fabric (not built)

### Uni-Pole Tensile Roof family
- A) Single Cone (not built)
- B) Multi-Cone Cluster (not built)
- C) Umbrella (not built)

### Canopy family (cantilever and wall-attached shade)
- A) Cantilever Flat Shade (not built)
- B) Cantilever Bell Shade (not built)
- C) Cantilever Pyramid Shade (not built)
- D) Cantilever Cone Shade (not built)
- E) Cable-Supported Cantilever (not built)
- F) Wall-Mounted Shade (not built)
- G) Tree Canopy (future)

### Frame Tent family
- A) Pyramid Tent (not built)
- B) Gable Tent (not built)
- C) Hip Tent (not built)
- D) Sail Tent (not built)

### Portal Frame family
- A) Simple Portal (not built)
- B) With Mezzanine (not built)
- C) With Crane (not built)
- D) Multi-Bay Portal (not built)

Variant lists to be refined when each structure type is designed.

### Classification Rule
- Structure type = what the user would naturally call it.
- Where two families overlap, place in the one matching user intent.
- Same engine recipe can serve multiple structure types.
- Do not force rigidity. Prefer clarity for the user.

---

## 6. Anchor Position Rule (CORRECTED 2026-09-13)

For any Hypar Sail variant:
- Anchors are at USER-DEFINED positions (x, y, z) - not fixed
- Anchor count is 3 or 4 for Hypar Sail (not more)
- Each anchor can be: column top, wall plate, or ground pedestal
- Each anchor can be at a DIFFERENT height

VALIDITY RULE (CRITICAL):
A Hypar Sail is INVALID if all anchors are at ground level.
At least one anchor must be elevated above the others.

Anything beyond 4 anchors = Membrane Ribbon (Phase 2, Type 8).

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

| Structure | Systems used |
|---|---|
| Saddle Span | A + D |
| Tensile Sails Roof | A + B |
| Framed Tensile Roof | A + C |
| Uni-Pole Tensile Roof | A + B |
| Canopy | A + C |
| Frame Tent | A + C |
| Portal Frame | C only |

### Engine Module Plan (engine/ folder)
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
- For the FDS viewer (prototype sandbox): viewer_app.py on main
- For the Results page (production): viewers/results_viewer.py
- Production viewer takes inputs as parameters (no sidebar)
- Reads workshop inputs from session state
- Falls back to placeholder if a variant isn't supported

The FDS viewer stays as the prototyping tool.
The production viewer is the "official" viewer for the Results page.

---

## 9. Phase Plan (current)

Phase A - UI Shell - IN PROGRESS (11 of 13 chunks done)
  A0  core/theme.py                DONE
  A1  ui/__init__.py               DONE
  A2  ui/landing.py                DONE
  A3  ui/studio.py                 DONE
  A4  ui/registration.py           DONE
  A5.1 ui/workshop.py              DONE
  A5.2 ui/workshops/__init__.py + saddle_standard.py  DONE
  A5.3 ui/workshops/saddle_leaf.py DONE
  A6.1 viewers/__init__.py         DONE
  A6.2 viewers/results_viewer.py   DONE
  A6.3 ui/results.py               DONE
  A7  core/navigation.py           NEXT
  A8  app.py                       LAST

Phase B - Restore v9.1 rich behaviour (pending)
Phase C - Build the physics engines (pending)
  C.1 engine/membrane.py  (Message 1 done, Messages 2-4 pending)
  C.2 engine/cable_mast.py
  C.3 engine/frame.py
  C.4 engine/arch.py
  C.5 engine/truss.py
Phase D - Wire engine into Results (pending)
Phase E - Trim to 7 structures (pending)
Phase F - Smart Guided Design wizard (pending)
Phase G - Output module (BQ, alerts, schedules) (pending)
Phase H - DXF import + CAD round-trip (pending)
Phase I - Membrane Ribbon (Type 8) (pending)
Phase J - Concept structures (Mother Tree, Flower Roof) (pending)

---

## 10. Current Repository State

Repo: OCBC-cloud/sds-app
Working branch: modular-v10
Production branch: main

### Branch modular-v10 (44+ commits ahead of main)

Root:
- app.py                     (old - will be replaced in A8)
- PROJECT_STATE.md           this file
- README.md
- README_MODULAR.md
- physics_engine.py          (Phase A catenary - not wired)
- requirements.txt
- run_tests.py               (test runner for GitHub Actions)
- test_membrane.py           (redundant - to be deleted)
- viewer_app.py              (not on modular-v10, only main)

.github/workflows/:
- test.yml                   GitHub Actions CI

core/:
- __init__.py
- theme.py                   readability-focused CSS (updated 2026-09-13)
- state.py                   (old structure - will be cleaned up)

data/:
- __init__.py
- sections.py
- materials.py
- structures.py
- constants.py

engine/:
- __init__.py
- membrane.py                Message 1 done - mesh foundation
- SPEC_saddle_span.md        updated with Section 6A (strut geometry)

ui/:
- __init__.py
- landing.py                 Chunk A2
- studio.py                  Chunk A3
- registration.py            Chunk A4
- workshop.py                Chunk A5.1 router
- results.py                 Chunk A6.3
- workshops/
  - __init__.py
  - saddle_standard.py       Chunk A5.2
  - saddle_leaf.py           Chunk A5.3 (+ strut joint height)

viewers/:
- __init__.py
- results_viewer.py          Chunk A6.2

.streamlit/:
- config.toml

### Branch main
- Production SDSe app.py (old, pre-modular)
- viewer_app.py (FDS Viewer v3.2)
- dxf_export.py
- requirements.txt (includes ezdxf)

### Streamlit Cloud Account
- 3 apps deployed (free tier limit reached)
- Cannot create new apps without deleting one

---

## 11. GitHub Actions - CI Infrastructure

WORKING.

Workflow: .github/workflows/test.yml
Runner: run_tests.py

On every push to main or modular-v10, tests run automatically.
Green checkmark = pass. Red X = fail.
Free, private, no Streamlit needed.

Known warning: Node.js 20 deprecation (harmless).

---

## 12. Phase 4A - engine/membrane.py Status

Message 1 COMPLETE and verified by GitHub Actions on 2026-09-12.

What was built:
- Mesh data structure (create_mesh)
- Geometry helpers (edge_length, edge_vector, count_neighbours)
- Flat grid builder (build_flat_grid)
- Self-test (_verify_mesh_handling)

All tests pass.

Next:
- Message 2 - Force Density Method solver
- Message 3 - Newton-Raphson load application
- Message 4 - Stress extraction

---

## 13. Saddle Span Specification - COMPLETE

Written to engine/SPEC_saddle_span.md on modular-v10.
Updated 2026-09-13 with Section 6A (strut geometry).

### Three Sub-types
1. Standard Saddle Span
2. Cantilevered Saddle Span (<= 6m x 6m)
3. Leaf Variant (<= 6m x 6m)

### Section 6A - Strut Geometry (NEW)

The Cantilever Leaf has a curved strut that runs from a point at
approximately 1/3 along the main beam down to the uni-pole column.

Strut-column joint height:
- Default: 60 percent of column height
- Valid range: 40 percent to 75 percent of column height
- User can override in the workshop

Effect of higher joint:
- Shorter strut -> less bending
- Steeper strut -> more axial (compression)
- Less eccentricity -> smaller moment into column
- Smaller baseplate moment -> smaller footing

### Chief's Reference Case - 10m x 10m Leaf Prototype
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

## 14. Tie-down Cables - Lock-in Rule

Tie-down cables are mandatory structural elements for all Saddle Span
family variants (except Leaf, which is a cantilever) and for Canopy
variants.

They must appear in:
- The Workshop input page (dedicated section)
- The 3D viewer (always visible unless toggled off)
- The engine (cable tension + anchor uplift checks)
- The member schedule
- The Bill of Quantities

Inputs (all mandatory):
- Number of Tie-down Intervals
- Anchor Uplift Angle (default 45 deg)
- Anchor Spread Angle (default 30 deg)
- Cable Type (6x19 / locked coil / spiral)
- Cable Material (galvanised / stainless)
- Cable Diameter (always automatic - engine selects)
- Ground Anchor Type (pinned / rigid)

Checks:
- Cable tension <= f_u,cable / gamma_M,cable
- Anchor uplift resistance
- Anchor base plate bearing
- Cable anchorage at the beam node

Never bypass this rule.

---

## 15. Foundation - Preliminary Sizing Rule

For the Cantilever Leaf (and any cantilevered sub-type), the workshop
collects soil inputs and the Results page shows a preliminary
foundation size.

Inputs (all in Section 6 of the leaf workshop):
- Assumed Soil Bearing Capacity (kN/m2)
- Soil Type (sand / clay / rock / filled)
- Water Table Depth (m)
- Foundation Type (pad / pile / raft)

Outputs (on Results page):
- Preliminary pad size = Reaction / Bearing capacity
- Note: "Subject to geotechnical verification. Footing reinforcement
  and detailing not provided. Engage a geotechnical engineer."

A full Foundation engine (System F) is planned for a later phase.

---

## 16. Build Philosophy (Rules Locked In)

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
11. Any edit to app.py or data/ or core/ or engine/ or ui/ is on modular-v10.
12. Once a structure type is tested and stable, it is promoted
    to main as a new structure type - NOT as a replacement.
13. Each structure type has its own preset inputs, calculations,
    displays, and format.

---

## 17. Owner

Chief. First-time app builder.
Uses iPhone + GitHub web editor + Streamlit Cloud.
No terminal, no local Python environment.
Needs step-by-step guidance with screenshots.
Requires full file replacements (not surgical patches) for reliability.

---

## 18. Next Actions (Next Session)

### Immediate
1. A7 - core/navigation.py - the router
2. A8 - app.py - the thin new entry point
3. Test the full flow end to end

### After A8
4. Verify the flow works: landing -> studio -> registration ->
   workshop -> results
5. Fix any bugs found
6. Then continue Phase C - engine/membrane.py Message 2

### Soon
7. Delete test_membrane.py (redundant)
8. Update core/state.py for the new page defaults
9. Refine the FDS viewer to match the production viewer (optional)

### Later
10. Continue engine build (membrane Messages 2-4)
11. Write remaining structure specs
12. Wire engine into Results page

---

## 19. How to Resume in a New Chat

Paste this entire file into a new chat, then add:

"Resuming SDSe. Phase A nearly done - 11 of 13 chunks.
Next: A7 (core/navigation.py) and A8 (app.py) to complete
the UI shell. Then test the full flow end to end."

The new chat will confirm:
1. Repo: OCBC-cloud/sds-app
2. Branch: modular-v10 (working) and main (production)
3. Current phase: Phase A - UI shell - nearly complete

Then wait for Chief's go-ahead.

---

## 20. Document History

- Created: 2026-09-11 (Phase 1 handoff)
- Updated: 2026-09-12 (evening) - Phase 1 complete, CI in place,
  engine/membrane.py Message 1 done
- Updated: 2026-09-12 (late evening) - UI flow specification agreed,
  build sequence locked in
- Updated: 2026-09-13 - Variant mapping, tie-down rule, strut
  geometry Section 6A added. Phase A UI shell 11 of 13 chunks
  complete. All ui/ files built. viewers/ folder created.
  Awaiting A7 (navigation) and A8 (app.py) to complete Phase A.

---

End of project state.
