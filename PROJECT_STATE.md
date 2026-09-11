# SDSe Project State

Handoff document. Read this first in any new chat session.

---

## Repo and Deployments

- GitHub repo: OCBC-cloud/sds-app
- Working branch: modular-v10
- Production branch: main (still on v9.1, untouched)
- Live app: sahfpaexbknah.streamlit.app
- Preview app: modular-preview.streamlit.app
  (deploys from modular-v10 branch, entry app.py)
- Standalone 3D viewer app: viewer_app.py on main

---

## Owner

Chief. First-time app builder. Uses iPhone + GitHub web editor
+ Streamlit Cloud. No terminal, no local Python environment.
Needs step-by-step guidance with screenshots.

---

## Build Philosophy

- Plain Python dicts, no dataclasses, no type hints
- mm-based section units (A mm2, I mm4, W_el mm3, i mm)
- HTML strings built as named variables with explicit `+`
  on every line. Never mix implicit literal concatenation with
  variable interpolation inside st.markdown().
- ASCII only in code. Use &mdash; &middot; etc. for HTML entities.
- Two blank lines at the end of every delivered chunk.
- One file per chunk. One commit per file.
- Verify each phase before moving to the next.

---

## Phase Plan

Phase 1 - Skeleton + data extraction - COMPLETE
Phase 2 - Split UI pages into ui/ folder - NEXT
Phase 3 - Split 3D viewers into viewers/ folder
Phase 4 - Build physics engine in engine/
Phase 5 - Wire engine into workspace
Phase 6 - Trim structures from 27 to 7

---

## Phase 1 Files (all on modular-v10)

Root:
- app.py               Thin shell + page functions inline
- README.md            Original
- README_MODULAR.md    Architecture doc
- physics_engine.py    Phase A catenary solver (not wired yet)
- requirements.txt
- viewer_app.py

data/ package:
- __init__.py          Marker
- sections.py          SECTION_PROPERTIES (55 sections)
- materials.py         STEEL_MATERIALS, FABRIC_PROPERTIES,
                       CABLE_PROPERTIES, JOINT_MULTIPLIERS
- structures.py        STRUCTURE_TYPES (27 entries, trimmed to 7 in Phase 6)
- constants.py         WIND_SPEEDS, PARTIAL_FACTORS

core/ package:
- __init__.py          Convenience exports
- theme.py             DARK_MODE_CSS, apply_theme()
- state.py             init_session_state(), clear_previous_project_data()

.streamlit/:
- config.toml          Dark theme, primaryColor #f39c12

---

## Phase 1 Verification

VERIFIED. Preview app at modular-preview.streamlit.app runs
cleanly. All screenshots confirmed:
- Top nav with all 6 buttons visible
- Dashboard, Workspace, BQ, Reports all render
- 3D viewer shows saddle span surface with red parabolic
  edge beams, blue membrane, orange purlins
- Health score 100%
- Member selection CHS 114.3x5.0 Standard PASS
- Secondary Beams SHS 100x100x5
- Cables 6x19 Galvanized 12mm

---

## Final Target Structures (7)

1. Saddle Span
2. Tensile Sails Roof
3. Framed Tensile Roof
4. Uni-Pole Tensile Roof
5. Canopy
6. Frame Tent
7. Portal Frame

Current catalogue has 27. Phase 6 trims to these 7.

---

## Physics Engine Status

physics_engine.py exists. Phase A only: 2D catenary solver
with Newton-Raphson cable element kernel. Not yet verified
in Streamlit. Not yet wired into the app.

Planned Phase 4 additions:
- force_density.py    Phase B form-finding
- nonlinear_solver.py Phase C load application (cable + beam elements)
- membrane.py         Phase D membrane stresses
- mast_tiedown.py     Phase E mast, tie-down, anchor checks
- ec_checks.py        EN 1993 resistance checks

---

## Architecture Rules for New Chats

- Keep production app.py on main working until full rebuild done
- Build everything on modular-v10
- Do not merge to main until Phase 6 complete
- Every phase verified before next phase starts
- Do not re-send entire files if surgical fix possible
- Send code in single fenced blocks with no prose inside

---

## Quick Commands for New Chat

To resume: paste this file content + current error message
(if any) + say which phase you want to start.

New chat should reply with a 3-line summary confirming:
1. Repo: OCBC-cloud/sds-app
2. Branch: modular-v10
3. Phase: [whatever you're starting]

Then wait for Chief's instruction.

---

## Session Update - 2026-09-11 (evening)

### Done today
- Phase 1 modular rebuild COMPLETE and verified on modular-v10
- Engine architecture decided: Five Systems (A-E) + Recipes
- Saddle Span spec written: engine/SPEC_saddle_span.md
- Saddle Span has 3 sub-types: Standard, Cantilever, Leaf
- Chief's 10m x 10m leaf prototype recorded as reference case
- Silent slope rules adopted (18 deg / 23 deg, never shown to user)
- Country-code safety factor table adopted
- MS EN 1990 gamma_Q = 1.5 adopted for MY
- Membrane-to-frame options A/B/C all supported
- Torsion identified as governing action for leaf sub-type
- FDS standalone 3D viewer identified (viewer_app.py on main)
- FDS viewer v3.1 with leaf support written (not yet committed)

### In progress
- Leaf shape iteration in FDS viewer
- Shape still needs refinement: currently looks like feather fan,
  should look like a graceful leaf

### Next actions
1. Commit and test FDS viewer v3.1
2. Iterate leaf shape until it looks right
3. Then write remaining 6 structure specs
   (Tensile Sails, Framed Tensile, Uni-Pole, Canopy,
    Frame Tent, Portal Frame)
4. Then begin Phase 2 (split UI into ui/ folder)

### Branch status
- modular-v10: 16+ commits ahead of main, safe
- main: production SDSe untouched, FDS viewer being updated

### Files to know about
- PROJECT_STATE.md (this file) - handoff doc
- engine/SPEC_saddle_span.md - saddle span spec
- viewer_app.py (on main) - FDS standalone viewer
- app.py (on modular-v10) - main SDSe modular rebuild

# SDSe Project State

Handoff document. Read this first in any new chat session.

---

## Repo and Deployments

- GitHub repo: OCBC-cloud/sds-app
- Working branch: modular-v10
- Production branch: main (production SDSe app still on main)
- Live app: sahfpaexbknah.streamlit.app
- Preview app: modular-preview.streamlit.app
  (deploys from modular-v10 branch, entry app.py)
- FDS viewer app: viewer_app.py on main
  (standalone 3D sandbox, deploys from main)

---

## Owner

Chief. First-time app builder. Uses iPhone + GitHub web editor
+ Streamlit Cloud. No terminal, no local Python environment.
Needs step-by-step guidance with screenshots.

---

## Build Philosophy

- Plain Python dicts, no dataclasses, no type hints
- mm-based section units (A mm2, I mm4, W_el mm3, i mm)
- HTML strings built as named variables with explicit `+`
  on every line. Never mix implicit literal concatenation with
  variable interpolation inside st.markdown().
- ASCII only in code. Use &mdash; &middot; etc. for HTML entities.
- Two blank lines at the end of every delivered chunk.
- One file per chunk. One commit per file.
- Verify each phase before moving to the next.

---

## Phase Plan

Phase 1 - Skeleton + data extraction - COMPLETE
Phase 2 - Split UI pages into ui/ folder - NEXT
Phase 3 - Split 3D viewers into viewers/ folder
Phase 4 - Build physics engine in engine/
Phase 5 - Wire engine into workspace
Phase 6 - Trim structures from 27 to 7
Phase 7 - Intelligent design wizard
Phase 8 - Full output module (schedules, alerts, BQ)
Phase 9 - CAD Interoperability (DXF export/import)
Phase 10 - Concept structures (Mother Tree, Flower Roof)

---

## Phase 1 Files (all on modular-v10)

Root:
- app.py               Thin shell + page functions inline
- README.md            Original
- README_MODULAR.md    Architecture doc
- PROJECT_STATE.md     This file
- physics_engine.py    Phase A catenary solver (not wired yet)
- requirements.txt
- viewer_app.py        (not on modular-v10, only on main)

data/ package:
- __init__.py          Marker
- sections.py          SECTION_PROPERTIES (55 sections)
- materials.py         STEEL_MATERIALS, FABRIC_PROPERTIES,
                       CABLE_PROPERTIES, JOINT_MULTIPLIERS
- structures.py        STRUCTURE_TYPES (27 entries)
- constants.py         WIND_SPEEDS, PARTIAL_FACTORS

core/ package:
- __init__.py          Convenience exports
- theme.py             DARK_MODE_CSS, apply_theme()
- state.py             init_session_state(), clear_previous_project_data()

engine/ package:
- SPEC_saddle_span.md  Saddle Span full specification

.streamlit/:
- config.toml          Dark theme, primaryColor #f39c12

---

## FDS Viewer Files (on main)

Root:
- viewer_app.py        FDS 3D Viewer Prototype v3.2
                       (deploys standalone from main)
- dxf_export.py        DXF export module (working)
- requirements.txt     includes ezdxf

---

## Phase 1 Verification

VERIFIED. Preview app at modular-preview.streamlit.app runs
cleanly. All screenshots confirmed:
- Top nav with all buttons visible
- Dashboard, Workspace, BQ, Reports all render
- 3D viewer shows saddle span surface
- Health score 100%
- Member selection CHS 114.3x5.0 Standard PASS
- Secondary Beams SHS 100x100x5
- Cables 6x19 Galvanized 12mm

---

## FDS Viewer v3.2 - DXF Export COMPLETE

VERIFIED working. First export produced:
- File: sdse_leaf_2026-09-11.dxf
- Size: 353 KB
- Opens in ZWCAD Mobile (CAD software)
- Contains named layers: COLUMN, BASEPLATE, MAIN_BEAM, RIBS,
  CABLE_PERIMETER, MEMBRANE, STRUT, RING_CABLE, NODES
- Embeds SDSe metadata in header

### Known issues to address
- Faceted membrane (30x30 grid, not smooth surface)
- Rib tips vs perimeter cable alignment (minor gaps)
- Tip convergence precision
- Strut curvature (polyline vs smooth curve)
- No member sizes yet (waiting on engine)
- Baseplate is a point, not a plate

### Cache fix applied
The viewer_app.py uses `importlib.reload(sys.modules['dxf_export'])`
at the top to bypass Streamlit module cache on every startup.
This was required after multiple failed attempts to update
dxf_export.py without this fix.

---

## Final Target Structures (7)

1. Saddle Span
2. Tensile Sails Roof
3. Framed Tensile Roof
4. Uni-Pole Tensile Roof
5. Canopy
6. Frame Tent
7. Portal Frame

Current catalogue has 27. Phase 6 trims to these 7.

---

## Engine Architecture - Five Systems

Every structure reduces to a small number of fundamental
structural systems. Shapes are cosmetic; actions are physical.

### The Five Systems

- System A - Tension Membrane (cable net)
- System B - Cable + Masts / Struts
- System C - Frame / Beam (bending)
- System D - Arch / Curved Beam (combined)
- System E - Truss (axial)

### The Recipe Concept

A "structure type" is a recipe over the five systems.

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

## Saddle Span Specification (COMPLETE)

Written to engine/SPEC_saddle_span.md on modular-v10.

### Three Sub-types

1. Standard Saddle Span
2. Cantilevered Saddle Span (<= 6m x 6m)
3. Leaf Variant (<= 6m x 6m)

### Chief's Reference Case - 10m x 10m Leaf Prototype

Geometry:
- Column: CHS 323.8 x 8, uni-pole, height 10m
- Outreach: 10m
- Plan area: ~80 m2 (~80 percent of 10x10)
- Main beam arc radius: ~5m
- Ribs per side: 7 (total 14 + 1 main beam)
- Rib plan spacing: 45 deg
- Rib tilt: ~20 deg upward
- Membrane-to-frame: Option A (below frame)

Members:
- Main beam: CHS 168.3
- Ribs: CHS 168.3 tapering to CHS 76
- Column: CHS 323.8 x 8

Cables:
- Stainless steel 6x19, 8mm diameter
- Segment cables between rib tips

Fabric:
- PVC Ferrari S702
- Pre-tension 1 kN/m

Loads:
- Wind 33.5 m/s (Malaysia)
- gamma_G 1.2 (favourable for uplift)
- gamma_Q 1.4 (Chief's model) / 1.5 (MS EN 1990)

Results (Chief's prototype):
- Governing action: TORSION (not bending)
- Critical member: small rib near column
- Foundation: 1200mm deep, base 2500 x 2000mm

### Membrane-to-Frame Options (all three supported)

A. Below frame (default) - valley under beam
B. Above frame - ridge at beam
C. Clamped at beam - beam as gutter

### Silent Rules (never shown to user)

1. Tensile membrane slope minimum:
   - 18 deg for small exposed surfaces (area <= 100 m2 or dim <= 15m)
   - 23 deg for large exposed surfaces
2. Pre-tension retention
3. Shape fidelity (min 5 ribs per side for leaf)

### Country-Specific Safety Factors

Per-standard table for EU / MY / UK / CN / US.
MY uses gamma_Q = 1.5 (MS EN 1990).

### Concept Ideas (future phases)

- Mother Tree - multi-leaf tower
- Flower Roof - petals radiating from a central mast

---

## CAD Interoperability Status

### Export - WORKING
- ezdxf library installed
- DXF export module built and tested
- Self-describing layer convention
- Metadata embedded in header

### Import - NOT YET BUILT
- Planned for later
- Same layer convention would allow round-trip
- Would allow editing in CAD and re-import

---

## Workflow Rules Locked In

1. One file per chunk. One commit per file.
2. HTML strings built as named variables with explicit +
   on every line.
3. ASCII only in code.
4. Two blank lines at end of every delivered chunk.
5. Verify each phase before moving to next.
6. Keep production app on main; build on modular-v10.
7. PROJECT_STATE.md is the handoff document for new chats.
8. FDS viewer is the shape sandbox, deployed from main.
9. Silent rules are never shown to users.
10. Any edit to viewer_app.py or dxf_export.py is on main.
11. Any edit to app.py or data/ or core/ is on modular-v10.

---

## Repo State at End of Day 2026-09-11

Branch modular-v10:
- 16+ commits ahead of main
- Phase 1 complete and verified
- engine/SPEC_saddle_span.md committed
- PROJECT_STATE.md committed

Branch main:
- Production SDSe app.py (still old, pre-modular)
- viewer_app.py FDS Viewer v3.2 (working)
- dxf_export.py (working)
- Original v9.1 code

---

## Next Actions (Next Session)

### Immediate
1. Optional: refine leaf geometry to close CAD-visible gaps
   (membrane facets, rib-cable alignment, tip convergence,
   strut curvature)
2. OR: begin engine/membrane.py (first real physics engine)

### Soon
3. Write remaining six structure specs
4. Begin Phase 2 (split UI into ui/ folder)

### Later
5. Phase 4 - Build the physics engines (A-E)
6. Phase 5 - Build recipes.py
7. Phase 6 - Wire recipes into workspace
8. Phase 7 - Trim to 7 structures with full physics
9. Phase 8 - Intelligent design wizard
10. Phase 9 - Full output module (schedules, alerts, BQ)
11. Phase 10 - DXF import + CAD round-trip

---

## Next Session Start

Open new chat with this file's content + message:
"Resuming SDSe. Phase 1 complete. FDS viewer v3.2 with
DXF export working. Ready for next step. Options: refine
leaf geometry, or begin engine/membrane.py."

---

End of project state.
