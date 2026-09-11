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
