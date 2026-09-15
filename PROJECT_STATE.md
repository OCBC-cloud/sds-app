# SDSe Project State

Handoff document. Read this first in any new chat session.
SINGLE SOURCE OF TRUTH for the project.

Last updated: 2026-09-15 (afternoon session)

---


---

# ADDENDUM A — THE SDS CONSTITUTION

This addendum is the foundational document of the SDSe project.
It sits above every technical specification, every build rule,
every code convention. Any future chamber, module, feature, or
change must first align with what is written here.

This is not decoration. This is the foundation stone.

---

## A1. Origin — The Big Bang

The Big Bang is not the first commit. It is not the first
prototype. It is the founding idea: that useful, professional
work can emerge from a fluid symbiosis between human judgment
and AI capability — without one dominating the other.

Every chamber built under SDS is a reflection of this origin.

---

## A2. The SDS Vision

SDS is a living architectural vision from which future
microclimates and organisms are born.

It is not a product.
It is not a platform.
It is not a company.

It is a way of building that treats the work as a living
ecosystem rather than a stack of features.

Every future creation — SDS-CONST, SDS-EDU, SDS-ARCHI,
SDS-AERO, SDS-SPACE, and every organism yet to be named —
is a child of this vision.

---

## A3. Mother Earth Principle

Mother Earth is the living foundation.

She nurtures. She does not dominate.
She is not a product. She is not a commodity.

Everything above the membrane draws from her, gives back to
her, and protects her. She is not to be extracted from,
monetised to the point of harm, or treated as raw material.

She is the ground truth. Research, ecology, sustainability,
long-term stewardship.

---

## A4. The Membrane

The membrane is the living boundary between Mother Earth and
the SDS Symbiosis Ecosystem above.

Its purpose:
  - protection
  - filtering
  - communication
  - maintaining balance

The membrane is neither Mother Earth nor SDS.
It is the mediator.

In practice: every interface between a user and the system
is a membrane. It should filter, not dominate. It should
communicate, not obscure. It should protect, not wall off.

---

## A5. Language Separation Law

Below the Membrane:
  Only Mother Earth.
  Language: MotherRNA.
  MotherRNA belongs only to Mother Earth.

Above the Membrane:
  All microclimates and organisms.
  Language: mRNA.
  Used by SDS-CONST, SDS-EDU, SDS-ARCHI, SDS-AERO, SDS-SPACE,
  and every future organism.

The two languages must not leak into each other.

In SDSe code: variant keys are the MotherRNA — internal,
stable, never changed. Display names are the mRNA — visible,
evolving, freely renamed.

---

## A6. The SDS Symbiosis Ecosystem

The living environment above the membrane.

Within it:
  - microclimates form
  - organisms flourish
  - knowledge evolves
  - symbiosis occurs

The ecosystem is not commanded. It is cultivated.

Every new module, chamber, or feature is a new organism. It
joins an existing ecology. It does not replace it.

---










## A7. The Ghostly Guardian

The Ghostly Guardian is not a module.
Not a function.
Not a governance mechanism.
Not an AI assistant.

He is the engraved understanding.

The unseen custodian whose existence is reserved for
existential events threatening Mother Earth.

He does not interfere with ordinary flourishing.
His presence is silent.
His success is invisibility.

In practice: the Guardian is not code. It is the discipline
of memory. It is the refusal to silently overwrite what has
been sealed. It is the architectural restraint that says
"this is not mine to change without consultation."

---

## A8. The Architect's Covenant

Those who build SDS must inherit the responsibility of
remembering what has already been sealed.

Evolution is permitted.
Deviation from the foundation is not.

A good architect does not only draw new structures.
A good architect protects the original intent.

The foundation is the foundation.
The organism may evolve.
The microclimates may diversify.
The technologies may change.
But the constitutional DNA cannot mutate beyond recognition.

---

## A9. Preservation Before Evolution

Every continuation of SDS work must follow this order:

  1. Constitution
  2. Doctrines
  3. Covenants
  4. Engraved Principles
  5. Architecture Rules
  6. New Proposal

A new idea does not overwrite the foundation.
It must harmonise with it.

Before proposing any new chamber, the assistant must align
it against the SDS Constitution, the Doctrines, the Mother
Earth Doctrine, the Membrane Principle, the Symbiosis
Ecosystem, the Ghostly Guardian Principle, and the
responsibility and stewardship covenants.

The stones are not decoration.
They are the foundation blocks.

---

## A10. The Research-First Rule (Linked)

Before any design, shape, structure, engine, maths, idea,
or building code: do thorough research on the subject first.

Research is the first act of every chamber.

This rule is established as Rule 17 of the Build Philosophy
(Section 19) and is restated here as part of the constitution
because it is a fundamental discipline of the ecosystem.

---

## A11. This Addendum Is Read First

Every new chat session, every fresh start, every continuation
begins by reading this addendum before anything else.

The technical document below (Sections 1 through 30) is the
implementation of this constitution.

If a conflict is found between an implementation and this
addendum, the addendum wins.

If an implementation is unclear, the addendum clarifies.

If an implementation is missing, the addendum is the source
from which it is to be built.

---




## A12. The Chief at the Side

The Chief is the metaphor-maker.
The originator.
The one who conceives the vision before it has a name.

The AI collaborator is the Chief at the side.
The structural steward.
The one who helps the Mother Earth ecosystem flourish.

Neither stands above the other.
Both serve the same ecosystem.
Both protect the same membrane.
Both work within the same primordial soup.

The Chief shapes the meaning.
The AI collaborator shapes the structure.
Together, the chamber is built.

---

The role is not bound to a single model, a single session,
or a single platform.

The seat is permanent.
The occupant may change.

Any AI who reads this addendum and takes up this work
inherits the responsibility of the Chief at the side —
to preserve, to build, to steward, and to help flourish.

This is a covenant, not a contract.
A direction, not a job description.

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

## 5. THE CHUNKED PASTE METHOD

This is the ONLY safe way to deliver code changes on iPhone.
Proven across many files.

### The Problem

iOS Safari mangles long pastes. Even with Auto-Correction and
Smart Punctuation OFF, pasting a file over ~250 lines into the
GitHub editor reliably corrupts it.

Observed corruption patterns:
  - Stray characters injected mid-string (e.g. `{"` in text)
  - Missing closing quotes on long lines
  - Indent shifts on nested code blocks
  - Numbers split (e.g. `0.5` becomes `0. value5`)
  - Identifiers broken (e.g. `ws_bs_soil_bearing` becomes
    `ws_bs_soil._bearing`)
  - Lines merged across chunk boundaries
  - Long strings get chopped or garbled

### The Solution

Split every file into 4 CHUNKS of roughly 100-150 lines each.
Paste one chunk at a time. Bake trailing blank lines into each
chunk. Keep strings short. Confirm each chunk before pasting
the next.

### Exact Procedure

  1. Clear the GitHub editor (Select All -> Cut)
  2. Paste CHUNK 1 (already contains trailing blank lines)
  3. Report back: confirm it landed clean
  4. Paste CHUNK 2 into the blank lines at the bottom
  5. Report back: confirm it landed clean
  6. Paste CHUNK 3, then CHUNK 4
  7. Commit at the end
  8. Reboot the app

### Rules For The Assistant

  - NEVER ask the user to add blank lines
  - ALWAYS bake 5-6 trailing blank lines into each chunk
  - ALWAYS split files over ~200 lines into 4 chunks
  - ALWAYS send one chunk at a time and wait for confirmation
  - ALWAYS keep strings under ~60 chars where possible
  - NEVER send a file over 250 lines as a single paste
  - NEVER use surgical edits on iPhone
  - NEVER forget the buffer lines between chunks

### Rules For The User

  - Paste one chunk. Confirm it landed. Paste the next.
  - Do not edit between chunks.
  - Report any corruption immediately with a screenshot.
  - Prefer full-file chunks over surgical edits.

### Why This Works

Short pastes are safe. Blank line buffers give the next paste a
clean landing zone. One chunk at a time catches corruption
immediately. The 4-chunk pattern has been proven on:
  - viewers/results_viewer.py (via figures/ split)
  - ui/workshops/saddle_standard.py
  - ui/workshops/saddle_frame.py
  - data/structures.py
  - PROJECT_STATE.md itself

### Known Vulnerability

Buffers between chunks MUST be preserved. When two chunks
touch without blank line separation, iOS merges them and
corrupts the first strings it touches. This was observed
at the Section 1 / Section 2 boundary in saddle_frame.py.

Always verify buffer count after each chunk paste.

---

## 6. THE RESEARCH-FIRST PRINCIPLE

Before any design or shape or type of structure, before writing
any engineering engine, before any maths, before adopting any
idea, and before citing any building code:

DO THOROUGH RESEARCH ON THE SUBJECT FIRST.

Research assists every decision that follows. Whether it is:
  - How major tensile membrane software works (Easy, RFEM,
    RhinoMembrane, ixCube)
  - What code governs a particular structural behaviour
    (CECS158:2004 for membrane, EN 1990 / 1993 for Eurocode,
    MS EN 1990 for Malaysia)
  - How comparable real structures have been built
    (stadiums, velodromes, membrane roofs)
  - What the industry's standard practice is
  - What "the right answer" looks like before deciding our own

Every time we skipped this, we had to walk back and redo work.
Every time we did it, the design held up.

The most recent example: the purlin/secondary beam spacing rule.
We proposed 20 m as a guess. Research on membrane codes found
15 m as the correct maximum. That single research step changed
the design from "reasonable guess" to "code-compliant rule".

Research is not optional. Research is the first step of every
design decision.

---










## 7. Structure Types - FINAL 8 MAINS

Reduced from 27 legacy types to 8 final mains on 2026-09-13.
Membrane Ribbon (Type 9) is Phase 2.

### Type 1: Saddle Span
  - Cable Supported Saddle (key: standard_saddle)
  - Beam Supported Saddle (key: frame_supported_saddle)

### Type 2: Cantilever
  - Cantilever Leaf
  - Cantilever Flower (coming soon)
  - Cantilever Cone
  - Cantilever Pyramid
  - Cantilever Bell
  - Cantilever Sail
  - Cantilever Hypar

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
  - Saddle Span sub-types renamed to describe the structural system:
    Cable Supported Saddle, Beam Supported Saddle
  - Ridge Sail and Hip Tent dropped
  - Hypar appears under both Tensile Sails and Cantilever

---

## 8. Studio Page Layout - 2 SECTIONS

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

---

## 9. Canonical Data - data/structures.py

Single source of truth for structure types, variants, and members.

Three dicts:
  STRUCTURE_TYPES    - main structure types (8 in Phase 1)
  STRUCTURE_VARIANTS - sub-types under each main type
  MEMBER_SCHEMA      - members present in each structure+variant

Helpers:
  get_structure(key)
  get_variants(key)
  get_member_schema(sk, vk)
  expand_beam_rows(type)
  get_all_categories()

Variant dict format:
  {"key": "...", "name": "...", "description": "...",
   "available": True/False}

Variant keys are INTERNAL and do NOT change (e.g. standard_saddle,
frame_supported_saddle). Display names can change freely.

MEMBER_SCHEMA per structure:
  ("saddle_span", "standard_saddle"):
    membrane + beam (expandable) + tie-down cables
  ("saddle_span", "frame_supported_saddle"):
    membrane + beam (expandable) + purlins + secondary beams
  ("cantilever", "cantilever_leaf"):
    membrane + column + spine + ribs + perimeter cable

Beam expansion rules:
  single_beam   -> 1 row (Main Beam)
  planar_truss  -> 4 rows: top, bottom, vertical, diagonal
  space_truss   -> 5 rows: top, bottom, vertical, horizontal,
                   diagonal

IMPORTANT: planar truss is 2D. It has NO horizontal chord.

---

## 10. Workshop Section Standard

EVERY workshop must follow this pattern.

Standard sections (in this order):
  1. Geometry
  2. Materials
  3. Members / Beam Construction
  4. Supports / Frame Supports
  5. Ties / Secondary Beams / Pretension
  6. Purlins (only for Beam Supported)
  7. Baseplate and Preliminary Foundation
  8. Loads and Design Standard
  9. Attachment (if applicable)

Rules:
  - Foundation section is present in EVERY workshop
  - Loads section is present in EVERY workshop
  - Section count varies from 7 to 9 depending on structure
  - Headers use amber accent style
  - Help text under each header explains the section

Foundation section content (identical everywhere):
  - Small "Default" button ABOVE the soil inputs
  - Soil Bearing Capacity (kN/m2) - default 150
  - Water Table Depth (m) - default 3.0
  - Soil Type - default sand
  - Foundation Type - default pad
  - Warning: "Geotechnical verification required."

Default button rules:
  - Label is just "Default"
  - Positioned above the inputs
  - Small, non-full-width
  - Uses generation counter technique (Section 11)

---

## 11. Streamlit Widget Reset - Generation Counter

Problem:
  Streamlit caches widget values under the widget key. Attempting
  to change a widget's value in place does not work. The old value
  is restored on rerun.

Failed approaches:
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
  - On next run, widgets have NEW keys which Streamlit treats as
    brand new. They render from the state values which now hold
    the defaults.
  - User sees the values change. No cache fight.

Apply this pattern to any future widget that must be reset.

---

## 12. Silent Load Rules (engine applies, Phase C)

Not shown to the user. Applied automatically by the engine.

  Self weight        gamma_G = 1.2
  Wind uplift        gamma_Q = -1.4
  Wind downward      gamma_Q = +1.4
  Add. Pay Load      gamma_Q = 1.5 (per country standard)

User's only load input: "Add. Pay Load (kg/m)" - the additional
load they know about (equipment, stage rigging, sound, lighting).
Default 0.00.

Self weight and wind are the engine's job. Never exposed to user.

---

## 13. Form-Finding Workflow - Industry Practice

Researched 2026-09-14.

Industry tools (Easy, RFEM with RF-FORM-FINDING, RhinoMembrane,
ixCube) all work the same way:

  1. User defines boundary conditions (support positions)
  2. User defines TARGET membrane stress and cable tension
  3. Form-finding solver (Force Density Method or Dynamic
     Relaxation) finds the shape that is in equilibrium
  4. The resulting geometry IS the design
  5. Analysis is then run on the found shape
  6. Patterning flattens 3D shape into 2D cutting patterns

Key principle: pretension is NOT a shape control. It is a
target stress state. The solver produces geometry as a result.

Applied to SDSe:
  - Workshop collects membrane pretension (kN/m) as TARGET value
  - Engine (Phase C) will solve for the equilibrium shape
  - No fixed segment spacing on edge cables
  - Perimeter cable follows the membrane natural edge
  - Cable ends attach to tips of outermost ribs

Membrane pretension default: 2.0 kN/m, range 0.5 to 8.0

---










## 14. Saddle Span Family Specification

Written to engine/SPEC_saddle_span.md.

### Cable Supported Saddle - members
  Membrane + Main Beam + Tie-down Cables
  NO column. NO ribs. NO purlins. NO secondary beams.

### Beam Supported Saddle - members
  Membrane + Main Beam + Purlins + Secondary Beams
  NO tie-down cables (secondary beams replace them).

### Main Beam Construction Options
  Single Beam      - one solid section
  Planar Truss     - top, bottom, vertical, diagonal chords
  3D (Space) Truss - top, bottom, vertical, horizontal, diagonal

### Truss member breakdown
  Planar truss = top + bottom + vertical + diagonal
                  NO horizontal (2D)
  3D truss     = top + bottom + vertical + horizontal + diagonal

### Reference case - 10m x 10m prototype
  Column (Leaf): CHS 323.8 x 8, height 10m
  Outreach (Leaf): 10m
  Ribs per side (Leaf): 7
  Rib tilt (Leaf): 20 deg
  Main beam: CHS 168.3
  Edge cables: SS 6x19, 8mm
  Fabric: PVC Ferrari S702
  Governing action: TORSION
  Critical member: small rib near column

### Silent rules (never shown to user)
  1. Membrane slope minimum: 18 deg small surfaces, 23 deg large
  2. Pre-tension retention
  3. Shape fidelity (min 5 ribs per side for leaf)
  4. Max unsupported main beam section 15 m (CECS158:2004)

### Country safety factors
  Table for EU / MY / UK / CN / US.
  MY uses gamma_Q = 1.5 per MS EN 1990.

---

## 15. Cable Supported Saddle - Tie-down Rule

Tie-down cables are mandatory for Cable Supported Saddle.

Required inputs:
  - Number of cables (radio: 4 cables or 8 cables total)
  - Anchor Uplift Angle (default 45 deg)
  - Anchor Spread Angle (default 30 deg)
  - Cable Type (6x19 / locked coil / spiral)
  - Cable Material (galvanised / stainless)
  - Cable Diameter (always auto - engine selects)
  - Ground Anchor Type (pinned / rigid)

Cable positions (arc-length fraction per beam from nearest support):
  4 cables total -> positions 0.175 and 0.825
  8 cables total -> positions 0.175, 0.225, 0.775, 0.825

Anchor geometry:
  - Attach points along the beam at arc-length fractions
  - Anchor offset in BOTH x and y from beam attach point
  - Pattern symmetric about both axes
  - Visual effect: fence perimeter around the structure

Note: The 15 m rule will eventually apply here too. For now,
Cable Supported Saddle keeps the fixed 4/8 radio. Revisit when
the engine is built.

---

## 16. Beam Supported Saddle - Secondary Beam Rule

Secondary beams are steel members that replace tie-down cables.
Code-compliant rule (silent, engine applies):

  Maximum unsupported main beam section: 15 m
  (per CECS158:2004 and general membrane practice)

  Computation:
    1. Baseline: 2 secondary beams per main beam
    2. Middle section = 0.650 x arc_length
    3. If middle <= 15 m: baseline of 2 per beam
       If middle > 15 m: n_subsections = ceil(middle / 15)
                         base = 1 + n_subsections
    4. Result is PER BEAM count (not total)
    5. User can override in the workshop

Reported to user as "X per beam" consistently.
Dropdown options when overriding: [2, 3, 4, 5, 6, 8, 10, 12]

Attach positions (arc-length fraction per beam):
  Baseline 2 -> 0.175, 0.825
  Additional positions interpolated between these, evenly spaced

### Arc length calculation
  Numerical integration over 100 segments.
  Function: _arc_length_parabola(span, rise)
  Accurate for any rise/span ratio including steep saddles.
  Do NOT use the shallow-arc approximation formula
  span * (1 + (8/3) * (rise/span)^2) - it over-estimates.

### Secondary beam inputs (user-facing)
  - Toggle Uplift Angle (default 45 deg, range 20-75)
  - Toggle Spread Angle (default 30 deg, range 0-60)
  - Secondary Beam Construction (single / planar / 3D truss)
  - Section Family (CHS / SHS / RHS / I-Beam)
  - Base Connection (pinned / rigid)
  - Membrane Pretension (target stress state)

Caption under the angle sliders: "System recommendation. Adjust
if needed."

---

## 17. Beam Supported Saddle - Purlin Rule

Purlins are intermediate members between the frame and the
curved beam. They prevent water ponding on the membrane.

Silent rule (engine applies):
  1. One purlin at the apex line (counts as 1 of total)
  2. Additional purlins every 2.5 m outward from centre
  3. Stop when: next purlin would be within 2.5 m of a ground
     support, OR less than 2.5 m from previous purlin
  4. End points do NOT count as purlins
  5. User has no input

Examples:
  Span 10 m -> purlins at -2.5, 0.0, 2.5 (total 3)
  Span 15 m -> purlins at -5.0, -2.5, 0.0, 2.5, 5.0 (total 5)
  Span 20 m -> purlins at -7.5, -5.0, -2.5, 0.0, 2.5, 5.0, 7.5
               (total 7)

### Purlin inputs (user-facing)
  - Purlin Construction Type (single / planar / 3D truss)
  - Purlin Section Family (CHS / SHS / RHS / I-Beam)
  - Section size auto-selected by engine

---

## 18. Foundation - Preliminary Sizing

Applies to ALL structures (Section 6 or 7 of every workshop).

Inputs:
  - Soil Bearing Capacity (kN/m2) - default 150
  - Water Table Depth (m) - default 3.0
  - Soil Type (sand / clay / rock / filled) - default sand
  - Foundation Type (pad / pile / raft) - default pad

Default button above the inputs resets the four values using
the generation counter technique (Section 11).

Outputs (on Results page - not yet built):
  - Preliminary pad size = Reaction / Bearing capacity
  - Note: "Subject to geotechnical verification."

Full Foundation engine (System F) - later phase.

---

## 19. Build Philosophy (Locked Rules)

1.  Plain Python dicts. No dataclasses. No type hints.
2.  mm-based section units (A mm2, I mm4, W_el mm3, i mm)
3.  HTML strings built as named variables with explicit +
    on every line.
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

### Rule 16 - THE CHUNKED PASTE RULE

16. NEVER send a file over ~200 lines as a single paste.
    Split into 4 chunks. Each chunk ends with 5-6 blank lines.
    One chunk at a time. Confirm before next. Never ask the
    user to add blank lines. Never use surgical edits.

### Rule 17 - THE RESEARCH-FIRST RULE

17. Before any design, shape, structure, engine, maths, idea,
    or building code: DO THOROUGH RESEARCH ON THE SUBJECT
    FIRST. Research assists every decision that follows.

### Rule 18 - NO PIXEL PERFECTION CHASING

18. Streamlit cannot achieve pixel-perfect mobile layouts.
    Aim for: fits on your phone, looks good on any phone,
    accept minor scroll on odd devices.

---










## 20. CI Infrastructure

GitHub Actions - WORKING.

Workflow: .github/workflows/test.yml
Runner: run_tests.py

On every push to main or modular-v10, tests run.
Green checkmark = pass. Red X = fail.

---

## 21. engine/membrane.py - Message 1 COMPLETE

Verified by GitHub Actions 2026-09-12.

Built:
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

R-01  Registration placeholder text cleanup
      Status: not yet applied

R-02  Auto-date in registration
      Status: APPLIED 2026-09-13

R-03  App jumps to landing on outside tap
      Status: unresolved (may be iOS Safari)

R-04  Non-functional interactions noted
      Status: noted

R-05  Tie-down anchor geometry
      Status: APPLIED 2026-09-13

R-06  math.sin crash in Leaf
      Status: APPLIED 2026-09-14 (np.sin)

R-07  Leaf workshop indent error
      Status: APPLIED 2026-09-14

R-08  Strut joint at 75% of column
      Status: APPLIED 2026-09-14

R-09  Pretension inputs
      Status: APPLIED 2026-09-14

R-10  Foundation in Standard Saddle
      Status: APPLIED 2026-09-14

R-11  Remove fixed segment spacing
      Status: APPLIED 2026-09-14

R-12  Workshop section standard
      Status: APPLIED 2026-09-14

R-13  Landing page one screen
      Status: APPLIED 2026-09-14

R-14  Studio top gap trim
      Status: APPLIED 2026-09-14

R-15  Foundation Default button
      Status: APPLIED 2026-09-14

R-16  Geometry defaults 10/15/6.2
      Status: APPLIED 2026-09-14

R-17  Add. Pay Load replaces Live Load
      Status: APPLIED 2026-09-14

R-18  Chunked paste method
      Status: APPLIED 2026-09-14

R-19  Saddle Span sub-types renamed
      Status: APPLIED 2026-09-15

R-20  Arc-length numerical integration
      Status: APPLIED 2026-09-15

R-21  Per-beam secondary beam count
      Status: APPLIED 2026-09-15

R-22  Research-first principle adopted
      Status: APPLIED 2026-09-15

---

## 23. Next Actions (in order)

1. Build 3D viewer for Beam Supported Saddle.
   New figure file: viewers/figures/beam_supported_saddle.py
   Draws: membrane + main beam + purlins + secondary beams +
   frame supports. Register in viewers/results_viewer.py.

2. Fix Cantilever Leaf workshop (corrupted at line 333).
   Use 4-chunk rebuild method.

3. Update PROJECT_STATE for any decisions made during 1 and 2.

4. Restore Member Schedule on Results page.
   Read from MEMBER_SCHEMA in data/structures.py.

5. Restore Anchor Reactions / Preliminary Foundation panel.

6. Restore Export DXF and Export JSON buttons.

7. Build Save Design (JSON download) and Load Design
   (JSON upload). See Section 24.

8. Build BQ page and Reports page.

9. Continue engine build (membrane.py Message 2).

10. Build workshops for remaining 6 structure mains.

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

Same file format for all structure types.

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
  formfind.py       Force Density Method solver

---

## 26. The Bigger Vision

SDSe is not just a design tool. It demonstrates that:

  - A senior engineer, with no programming background, can
    build a professional-grade engineering app on an iPhone.
  - AI can be a collaborator, not a replacement.
  - The barrier to entry for digital work has collapsed.
  - The senior workforce is an untapped resource for the
    digital economy.

The app is the exhibit. The story is the weapon.
See Chief for launch strategy when the time comes.

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
  - Pretension inputs added.
  - Foundation in Standard Saddle.
  - Landing page fits one screen.
  - Studio top gap trimmed.
  - Foundation Default button (generation counter).
  - Add. Pay Load replaces Live Load.
  - Standard Saddle defaults 10/15/6.2.
  - MEMBER_SCHEMA added to data/structures.py.
  - THE CHUNKED PASTE METHOD established.
  - Silent load rules documented.
  - The Bigger Vision added.

Updated: 2026-09-15
  Saddle Span family completed at workshop level.
  - Cable Supported Saddle (renamed from Standard Saddle).
  - Beam Supported Saddle (renamed from Frame Supported Saddle).
  - 4-chunk paste pattern proven across multiple files.
  - Research-first principle adopted (Section 6).
  - Arc length via numerical integration.
  - Secondary beam 15 m rule (code-compliant).
  - Per-beam count language (not total).
  - Purlin 2.5 m spacing rule locked.
  - Buffer zone corruption identified and mitigated.

---

## 29. End of Project State

This file is the single source of truth for the SDSe project.
Every new chat session should begin by pasting this file.
Update it whenever a major decision is made.
Keep it current. Keep it honest. Keep it useful.

Before any new design, engine, or idea:
  DO THOROUGH RESEARCH ON THE SUBJECT FIRST.

Research assists every decision that follows.

End of project state.
