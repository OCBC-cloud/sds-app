# SDSe Project State

Handoff document. Read this first in any new chat session.
SINGLE SOURCE OF TRUTH for the project.

Last updated: 2026-09-14 (evening session - major update)

---

## 1. The Vision

SDSe is a guided structural design tool for tensile membrane,
curved-beam, and cable structures.

User flow: Landing -> Studio -> Registration -> Workshop -> Results.
Clean linear flow. No tabs. Back and home buttons everywhere.

Full flow builds a complete design: 3D view, health score, section
used, quantities, member schedule, exports (DXF, JSON), save/load.

The tool is designed to be used on a phone. It serves contractors,
PEs, architects, small fabricators, and students. Not just
specialist engineers.

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
  Results page restored: Quantities DONE. 3D viewer DONE.
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

## 5. THE CHUNKED PASTE METHOD (NEW - 2026-09-14)

This is now the ONLY safe way to deliver code changes on iPhone.

### The Problem We Solved

iOS Safari mangles long pastes. Even with Auto-Correction and Smart
Punctuation turned OFF, pasting a file over ~250 lines into GitHub
reliably corrupts it. We saw four separate corruptions in one day:

  - Stray tokens injected mid-string (e.g. `{"` appearing in text)
  - Missing closing quotes on long lines
  - Indent shifts on nested code blocks
  - Numbers split (e.g. `0.5` becomes `0. value5`)
  - Identifiers broken (e.g. `ws_ss_soil_bearing` becomes
    `ws_ss_soil._bearing`)
  - Entire lines reordered or duplicated

### The Solution

Split every long file into CHUNKS of roughly 150 lines each.
Paste one chunk at a time. Include trailing blank lines in each
chunk so the next paste has a clean landing zone.

### The Exact Procedure

  1. Clear the GitHub editor (Select All -> Cut)
  2. Paste CHUNK 1 (already contains trailing blank lines)
  3. Report back: confirm it landed clean
  4. Paste CHUNK 2 into the blank lines
  5. Report back: confirm it landed clean
  6. Paste CHUNK 3, and so on
  7. Commit at the end
  8. Reboot the app

### Rules For The Assistant

  - NEVER ask the user to add blank lines. iPhone editing is painful.
  - ALWAYS bake 6 trailing blank lines into each chunk.
  - ALWAYS split files over ~200 lines into chunks.
  - ALWAYS send one chunk at a time and wait for confirmation.
  - NEVER send a file over 250 lines as a single paste.

### Rules For The User

  - Paste one chunk. Confirm it landed. Paste the next.
  - Do not edit between chunks.
  - Report any corruption immediately with a screenshot.

### Why This Works

Short pastes are safe. The blank line buffer means the next paste
has whitespace to land in. One chunk at a time means a corruption
is caught immediately, and only that chunk needs re-pasting.

---

## 6. iOS Paste Warning

Required device settings (already applied):
  Settings > General > Keyboard:
    - Auto-Correction: OFF
    - Smart Punctuation: OFF

GitHub editor settings (already applied):
  - Spaces: 4
  - No wrap

Even with these settings, long pastes still corrupt. See Section 5
for the chunked paste method, which is the actual solution.

---

## 7. File Structure (branch modular-v10)

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
  structures.py              8 mains + variants + MEMBER_SCHEMA
  constants.py

engine/:
  __init__.py
  membrane.py                Message 1 done - mesh foundation
  SPEC_saddle_span.md        updated with Section 6A strut geometry

ui/:
  __init__.py
  landing.py                 Landing page - one screen, no scroll
  studio.py                  2 sections, 8 tiles
  registration.py            reads variants from data/structures.py
  workshop.py                router for variant workshops
  results.py                 3D view, health, section, readings, quantities
  workshops/
    __init__.py
    _shared.py               shared CSS + helpers for all workshops
    saddle_standard.py       8 sections, Default button, Add. Pay Load
    saddle_leaf.py           7 sections, pretension inputs

viewers/:
  __init__.py
  results_viewer.py          dispatches on variant_key alone

.streamlit/:
  config.toml

---

## 8. Current Working State

Confirmed working end-to-end:

  Landing page:
    - One screen, no scroll
    - SDSe badge, title, subtitle, divider, brand
    - Enter The Studio button
    - Footer

  Studio page:
    - Content starts near top (gap trimmed)
    - SDSe wordmark, "Choose Your Structure Type"
    - Smart Guided Design tile
    - Section A - Tensile and Membrane (5 tiles)
    - Section B - Canopy and Frame (3 tiles)

  Registration page:
    - Reads variants from data/structures.py
    - Auto-date captured on first visit
    - Variant selection with Coming Soon badges

  Workshop - Standard Saddle:
    - 8 collapsible sections
    - Geometry defaults: 10 / 15 / 6.2
    - Foundation section with Default button above soil inputs
    - Add. Pay Load (kg/m) with 0.00 default
    - Pretension sliders (membrane kN/m, cable kN)
    - All inputs persist

  Workshop - Cantilever Leaf:
    - 7 collapsible sections
    - Strut joint height fixed at 75% of column height
    - Pretension sliders
    - Foundation section

  Results page:
    - 3D viewer dispatches on variant_key
    - Standard Saddle and Cantilever Leaf both render
    - Health Score card (100)
    - Section Used card
    - Analysis Readings (6 metric cards, all --)
    - Quantities (3 cards, all --)

Not yet restored on Results:
  - Member Schedule table
  - Anchor Reactions / Preliminary Foundation panel
  - Export DXF button
  - Export JSON button
  - Save Design button

Not yet built:
  - Save Design to JSON file
  - Load Design from JSON file
  - BQ page
  - Reports page
  - Smart Guided Design wizard
  - Foundation output panel on Results
  - Workshops for the remaining 6 structure mains

---







## 9. Structure Types - FINAL 8 MAINS

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
  - Cantilever is its own main type
  - Leaf and Flower moved out of Saddle Span into Cantilever
  - Ridge Sail dropped
  - Hip Tent dropped
  - Hypar appears under both Tensile Sails and Cantilever
    (intentional - spanning-between-anchors vs single-column)
  - Umbrella kept separate from Single Cone

---

## 10. Studio Page Layout - 2 SECTIONS

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

## 11. Canonical Data - data/structures.py

Single source of truth for structure types, variants, and members.

Three dicts:
  STRUCTURE_TYPES    - main structure types (8 in Phase 1)
  STRUCTURE_VARIANTS - sub-types under each main type
  MEMBER_SCHEMA      - members present in each structure+variant

Helpers:
  get_structure(key)          returns structure dict or None
  get_variants(key)           returns list of variant dicts
  get_member_schema(sk, vk)   returns member schema for structure+variant
  expand_beam_rows(type)      returns chord rows for single/planar/space
  get_all_categories()        returns sorted list of categories

Variant dict format:
  {"key": "...", "name": "...", "description": "...",
   "available": True/False}

"available": False shows the "Coming Soon" badge in Registration.

MEMBER_SCHEMA per structure:
  ("saddle_span", "standard_saddle"):
    membrane + beam (expandable) + tie-down cables
  ("saddle_span", "frame_supported_saddle"):
    membrane + beam (expandable) + purlins (expandable)
    + strut + tie-down cables
  ("cantilever", "cantilever_leaf"):
    membrane + column + spine + ribs + perimeter cable

Beam expansion rules:
  single_beam   -> 1 row (Main Beam)
  planar_truss  -> 4 rows: top, bottom, vertical, diagonal
                   NO horizontal (planar is 2D)
  space_truss   -> 5 rows: top, bottom, vertical, horizontal, diagonal

---

## 12. Workshop Section Standard

EVERY workshop must follow this pattern.

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
  - Small "Default" button ABOVE the soil inputs (not below)
  - Assumed Soil Bearing Capacity (kN/m2) - default 150
  - Water Table Depth (m) - default 3.0
  - Soil Type (sand / clay / rock / filled) - default sand
  - Foundation Type (pad / pile / raft) - default pad
  - Warning: "Geotechnical verification required."

Default button rules:
  - Label is just "Default" (short, no lecture)
  - Positioned above the inputs (invitation, not afterthought)
  - Small, non-full-width
  - Refreshes the four soil inputs to defaults
  - Uses the generation counter technique (Section 13)

---

## 13. Streamlit Widget Reset - Generation Counter

Problem:
  Streamlit caches widget values under the widget key. Attempting
  to change a widget's value in place does not work. The old value
  is restored on rerun.

Failed approaches we tried (all unsuccessful):
  - Setting st.session_state[key] = new_value then rerun
  - Deleting the widget key then rerun
  - Two-stage flag + delete (eliminated the crash but not the reset)

Working solution - generation counter:
  - A counter lives in session state: ws_xx_found_widget_generation
  - Widget keys include the counter: "my_input_" + str(gen)
  - When Default is pressed:
      1. Set the four state values to defaults
      2. Bump the counter (gen = gen + 1)
      3. rerun
  - On next run, widgets have NEW keys (e.g. ..._1) which Streamlit
    treats as brand new. They render from the state values which
    now hold the defaults.
  - The user sees the values change. No cache fight.

Apply this pattern to any future widget that needs to be reset.

---

## 14. Silent Load Rules (engine applies, Phase C)

Not shown to the user. Applied automatically by the engine.

  Self weight        gamma_G = 1.2
  Wind uplift        gamma_Q = -1.4
  Wind downward      gamma_Q = +1.4
  Add. Pay Load      gamma_Q = 1.5 (per country standard)

The user's only input is "Add. Pay Load (kg/m)" - the additional
load they know about (equipment, stage rigging, sound, lighting).
Self weight and wind are the engine's job.

Default for Add. Pay Load is 0.00 - no extra user load.

---

## 15. Form-Finding Workflow - Industry Practice

Researched 2026-09-14.

Industry tools (Easy, RFEM with RF-FORM-FINDING, RhinoMembrane,
ixCube) all work the same way:

  1. User defines boundary conditions (support positions, etc.)
  2. User defines TARGET membrane stress and cable tension
  3. Form-finding solver (Force Density Method or Dynamic
     Relaxation) finds the shape that is in equilibrium
  4. The resulting geometry IS the design - the shape emerges
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

## 16. Saddle Span Specification

Written to engine/SPEC_saddle_span.md.

### Standard Saddle - members
  - Membrane
  - Beam (single member OR planar truss OR 3D truss)
  - Cable (tie-downs)
  NO column. NO ribs. NO purlins.

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
                  + diagonal chord. NO horizontal (2D).
  3D truss      = top chord + bottom chord + vertical chord
                  + horizontal chord + diagonal chord.

### Reference case - 10m x 10m Leaf prototype
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
  FIXED at 75% of column height (agreed 2026-09-14)
  No user input. Engine assigns automatically.
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

## 17. Tie-down Cables - Lock-in Rule

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
  - Pattern is symmetric about both axes
  - Visual effect: fence perimeter around the structure

Engine will compute optimal attach points at form-finding time.

---







## 18. Foundation - Preliminary Sizing

Applies to ALL structures (Section 6 of every workshop).

Inputs:
  - Assumed Soil Bearing Capacity (kN/m2) - default 150
  - Soil Type (sand / clay / rock / filled) - default sand
  - Water Table Depth (m) - default 3.0
  - Foundation Type (pad / pile / raft) - default pad

Default button ("Default") above the inputs resets the four values
using the generation counter technique (Section 13).

Outputs (on Results page - not yet built):
  - Preliminary pad size = Reaction / Bearing capacity
  - Note: "Subject to geotechnical verification. Reinforcement
    and detailing not provided. Engage a geotechnical engineer."

Full Foundation engine (System F) - later phase.

---

## 19. Build Philosophy (Locked Rules)

1.  Plain Python dicts. No dataclasses. No type hints.
2.  mm-based section units (A mm2, I mm4, W_el mm3, i mm)
3.  HTML strings built as named variables with explicit +
    on every line. Never mix implicit literal concatenation
    with variable interpolation inside st.markdown().
4.  ASCII only in code. Use HTML entities for non-ASCII.
5.  One file per chunk. One commit per file.
6.  Verify each phase before moving to the next.
7.  Every commit triggers GitHub Actions test.
8.  Silent rules never shown to users.
9.  Edit viewer_app.py or dxf_export.py on main.
10. Edit app.py or data/ or core/ or engine/ or ui/ or viewers/
    on modular-v10.
11. Once a structure is tested, promote to main as NEW - not
    as a replacement.
12. Each structure type has its own preset inputs, calculations,
    displays, format.
13. After every commit, REBOOT the Streamlit Cloud app.
14. Viewer dispatches on variant_key alone. Variant keys are
    globally unique. The viewer never checks structure_key.
15. All variants read from data/structures.py. No hardcoded
    VARIANTS_FALLBACK in ui/registration.py.

### Rule 16 - THE CHUNKED PASTE RULE (NEW 2026-09-14)

16. NEVER send a file over ~200 lines as a single paste on iPhone.
    Split it into chunks of ~150 lines each. Each chunk ends with
    6 blank lines. Paste one chunk at a time, confirm it landed,
    then paste the next. Never ask the user to add blank lines.
    Never ask the user to do surgical edits on iPhone.

### Rule 17 - NO PIXEL PERFECTION CHASING (NEW 2026-09-14)

17. Streamlit cannot achieve pixel-perfect mobile layouts across
    all phones and OSs. Do not chase perfection. Aim for: fits on
    your phone, looks good on any phone, accept minor scroll on
    odd devices. Future native shell is a Phase J discussion.

---

## 20. CI Infrastructure

GitHub Actions - WORKING.

Workflow: .github/workflows/test.yml
Runner: run_tests.py

On every push to main or modular-v10, tests run.
Green checkmark = pass. Red X = fail.
Free. Private. No Streamlit needed.

---

## 21. engine/membrane.py - Message 1 COMPLETE

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

## 22. Refinements List (Running)

R-01 - Registration page: remove placeholder text from Project
        Name, Client Name, Project Reference, Engineer.
        Keep placeholder on Location.
        Status: not yet applied.

R-02 - Date field automatic (datetime.now()).
        Status: APPLIED 2026-09-13.

R-03 - App jumps to landing when tapping outside input fields.
        Status: unresolved (may be iOS Safari behaviour).

R-04 - Non-functional interactions (buttons).
        Status: noted, may be by design.

R-05 - Tie-down anchor geometry.
        Status: APPLIED 2026-09-13.

R-06 - Fix math.sin crash in Leaf strut geometry.
        Status: APPLIED 2026-09-14 (np.sin).

R-07 - Fix Leaf workshop indent error.
        Status: APPLIED 2026-09-14.

R-08 - Lock strut joint at 75% of column height.
        Status: APPLIED 2026-09-14.

R-09 - Add pretension inputs to Leaf and Standard Saddle.
        Status: APPLIED 2026-09-14.

R-10 - Add Foundation section to Standard Saddle.
        Status: APPLIED 2026-09-14.

R-11 - Remove fixed segment spacing from edge cables.
        Status: APPLIED 2026-09-14.

R-12 - Workshop section standard locked (8 sections).
        Status: APPLIED 2026-09-14.

R-13 - Landing page: fit one screen, no scroll.
        Status: APPLIED 2026-09-14.

R-14 - Studio page: trim top gap.
        Status: APPLIED 2026-09-14.

R-15 - Foundation Default button (small, above inputs).
        Status: APPLIED 2026-09-14.

R-16 - Geometry defaults 10/15/6.2 for Standard Saddle.
        Status: APPLIED 2026-09-14.

R-17 - "Add. Pay Load" replaces "Live Load on Beam".
        Status: APPLIED 2026-09-14.

R-18 - Chunked paste method established.
        Status: APPLIED 2026-09-14. See Section 5.

---

## 23. Next Actions (in order)

1. Test the full flow: Landing -> Studio -> Saddle Span ->
   Standard Saddle -> Workshop -> Results -> back to Workshop.
   Confirm 3D view renders and Default button works.

2. Apply the same treatments to ui/workshops/saddle_leaf.py:
   - Rebuild using the chunked paste method
   - Add Default button (above soil inputs)
   - Rename load label to "Add. Pay Load (kg/m)"
   - Consider updating Leaf geometry defaults if needed
   - Keep 7 sections (Leaf has no separate "beam" section -
     the column spine IS the beam)

3. Restore the next Results page feature - Member Schedule.
   Must show only the members relevant to that structure +
   variant combination. Read from MEMBER_SCHEMA in
   data/structures.py. Beam rows expand by construction type
   (single/planar/space).

4. Restore Anchor Reactions / Preliminary Foundation panel
   on Results page.

5. Restore Export DXF and Export JSON buttons.

6. Build Save Design (JSON download) and Load Design
   (JSON upload). See Section 24.

7. Build BQ page and Reports page.

8. Continue engine build (membrane.py Message 2:
   Force Density Method).

9. Build workshops for the remaining 6 structure mains,
   each following the section standard.

---

## 24. Save Design Feature (Planned)

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

## 25. The Five Systems Engine Architecture

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

## 26. The Bigger Vision (for context, not for now)

SDSe is not just a design tool. It is a demonstration that:

  - A senior citizen, with no programming background, can build
    a professional-grade engineering app on an iPhone.
  - AI can be a collaborator, not a replacement.
  - The barrier to entry for digital work has collapsed.
  - The senior workforce is an untapped resource for the
    digital economy.

The app is the exhibit. The story is the weapon.
See Chief for the launch strategy when the time comes.

This section is a reminder. Not an action item.

---

## 27. Owner

Chief. First-time app builder, working engineer.
Age 63. Not a programmer by background.
iPhone + GitHub web editor + Streamlit Cloud.
No terminal. No local Python environment.
Needs step-by-step guidance with screenshots.
Chunked paste method required (Section 5).
Prefers full file replacement over surgical edits.
Uses ASCII-only mindset on iOS.

---

## 28. Document History

Created: 2026-09-11 (Phase 1 handoff)

Updated: 2026-09-12
  Phase 1 complete. CI running. membrane.py Message 1 done.

Updated: 2026-09-13
  UI flow spec, variant mapping, tie-down rules, strut geometry.
  Phase A nearly complete. Most features restored on Results.

Updated: 2026-09-14
  Major restructuring day.
  - Structure list reduced to 8 mains. Cantilever promoted.
  - Studio now 2 sections. Registration reads from data/structures.py.
  - Viewer dispatches on variant_key.
  - Fixed math.sin and indent crashes in Leaf.
  - Strut joint locked at 75%.
  - Pretension inputs added to both workshops.
  - Foundation section added to Standard Saddle.
  - Both workshops follow the 8-section standard.
  - Landing page fits one screen.
  - Studio top gap trimmed.
  - Foundation Default button (small, above inputs, generation
    counter technique).
  - Add. Pay Load replaces Live Load on Beam.
  - Standard Saddle geometry defaults 10/15/6.2.
  - MEMBER_SCHEMA added to data/structures.py.
  - THE CHUNKED PASTE METHOD established (Section 5). This
    solves the recurring iOS paste mangling problem for good.
  - Silent load rules documented (Section 14).
  - The Bigger Vision added (Section 26).

---

End of project state.
