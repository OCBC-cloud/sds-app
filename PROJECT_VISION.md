# SDSe — Project Vision

This document is the north star of the SDSe project.

It describes what SDSe is, what it is not, what it will deliver,
and where it is going. It is the reference that every future
session reads to understand the direction of the work.

It sits alongside:

  - PROJECT_STATE.md            — Current state and history
  - COMMERCIAL_MODEL.md         — Pricing and business plan
  - MARKETING_RENDER_WORKFLOW.md — Render feature design
  - APP_MAP.md                  — Repo structure

Last updated: 2026-09-24

---

# TABLE OF CONTENTS

  PART I    — THE PURPOSE
  PART II   — WHAT THE USER CAN DESIGN
  PART III  — WHAT THE ENGINE DELIVERS
  PART IV   — THE FDM ENGINE
  PART V    — THE ROADMAP
  PART VI   — THE BIGGER VISION

---


# PART I — THE PURPOSE

## 1. What SDSe Is

SDSe is a concept design tool for tensile membrane structures.

It lets a user sketch a membrane structure — from a standard
template or from a blank canvas — and receive back:

  - The form-found membrane shape
  - A structural analysis against major building codes
  - Recommended member sizes
  - A bill of quantities
  - A marketing render for the client pitch

It is designed to be used on a phone.

It serves contractors, fabricators, architects, event organisers,
and small design firms.

## 2. What SDSe Is Not

SDSe is NOT a fabrication tool.
SDSe is NOT a detailing tool.
SDSe is NOT a patterning tool.
SDSe is NOT a shop drawing tool.

SDSe does not produce:

  - Cutting patterns for the membrane
  - Steel connection details
  - Weld designs
  - Bolt patterns
  - CNC files
  - Anything that goes to a fabricator's factory floor

The user hands SDSe's concept package to a fabricator or a
detailing house. The fabricator does the rest.

SDSe is the FIRST HALF. Detailing is the SECOND HALF.

They work together. They do not compete.

## 3. Why This Boundary Is Important

If SDSe tried to do fabrication and detailing, it would compete
with the very fabricators it should serve.

By stopping at concept design, SDSe becomes a tool the
fabricator uses to win the job — not a tool that replaces the
fabricator.

The concept package that SDSe produces is:

  - A 3D model
  - An analysis report
  - A member schedule
  - A bill of quantities
  - A rendered artist impression

Enough to pitch a client, win the deal, and hand off to a
detailing house.

Nothing more. Nothing less.

## 4. The Vision in One Sentence

SDSe lets a user design a tensile membrane structure — including
a full stadium roof — on a phone, and receive back a concept
package that is good enough to sell, quote, and hand off.

---


# PART II — WHAT THE USER CAN DESIGN

## 5. The 8 Structured Templates

SDSe provides eight main structure types, each with its own
variants. These are the guided path — the user picks a type,
tunes parameters, and receives a design.

### Type 1: Saddle Span
  - Cable Supported Saddle
  - Beam Supported Saddle

### Type 2: Cantilever
  - Cantilever Leaf
  - Cantilever Flower (coming)
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
  - Tree Canopy (coming)

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

Each template is a recipe. Each recipe defines a set of
boundary conditions, a set of load regions, and a set of
member mappings. Each recipe feeds the same engine.

## 6. The Free-Form Design Tool

Beyond the 8 templates, the user can draw their own structure
from a blank canvas.

The user is given basic drawing tools:

  - Boundary curve drawing (in plan and elevation)
  - Support placement (columns, masts, anchors)
  - Cable and edge definition
  - Membrane region definition
  - Load region definition

The user draws the structure. The engine produces the design.

This is where the phrase "Unlimited Design Possibility" comes
from. Not a free-form CAD kernel. Not a general-purpose FEA
tool. A basic drawing interface that feeds the same engine
that serves the 8 templates.

## 7. The Types of Structure This Enables

With the free-form tool, the user can design:

  - Walkway canopies
  - Irregular continuous sail roofs
  - Food court canopies
  - Cafe shades
  - Ferry terminal roofs
  - Stadium tensile roofs
  - Any membrane structure the user can imagine

The ceiling of ambition is a stadium tensile roof. Nothing
larger is required. Nothing smaller is excluded.

## 8. The Structural Scope

SDSe covers structures made of:

  - Membrane (fabric)
  - Steel (columns, beams, trusses, masts)
  - Cables (edge cables, tie-downs, stays)
  - Hardware (clamps, cleats, anchorages)

SDSe does NOT cover:

  - Reinforced concrete (RC) design
  - Foundations engineering
  - Excavation or geotechnical work
  - Steel detailing (connections, welds, bolts)
  - Fabrication or patterning

The scope is deliberately narrow. Membrane and steel. That's it.

This narrow scope is what makes the tool powerful. It does
one thing well. It does not try to do everything.

---


# PART III — WHAT THE ENGINE DELIVERS

## 9. The Five Engine Outputs

For every design — a template or a user-drawn shape — the
engine produces five outputs.

### Output 1 — Form-Finding (FDM)
The equilibrium shape of the membrane. The natural sag under
its own weight and prestress. The form-found geometry of the
fabric between its boundary conditions.

### Output 2 — Structural Analysis
The behaviour of the structure under load:

  - Dead load (self weight)
  - Wind load (per local code)
  - Snow load
  - Additional payload

Results include:

  - Steel member forces (axial, bending, shear)
  - Cable tensions
  - Membrane biaxial stresses
  - Deflections

Checked against:

  - EN 1990 (basis of structural design)
  - EN 1991 (actions on structures)
  - EN 1993 (steel structures)
  - National annexes where applicable

### Output 3 — Member Sizing
Recommended section sizes:

  - CHS, SHS, RHS, I-beam sections for steel
  - Wire rope diameter and construction for cables
  - Fabric grade and orientation for the membrane

Recommendations are based on:

  - Utilisation ratios (must be ≤ 1.0)
  - Minimum sections per code
  - Practical construction considerations
  - Section database of available products

### Output 4 — Bill of Quantities
Material take-off for quotation:

  - Steel: by member, length, mass
  - Cable: length, fitting type
  - Fabric: flattened area, seam length, edge length
  - Hardware: clamps, cleats, kader, anchors

With the option for the user to enter their own unit rates
to produce a priced BQ.

### Output 5 — Marketing Render
A high-quality artist impression via an external AI renderer:

  - SDSe prepares the snapshot and prompt
  - The user opens an external renderer (Bing, Midjourney, Firefly)
  - The user pastes the prompt and uploads the snapshot
  - The renderer produces the marketing image
  - The user uploads the result back to SDSe
  - The render is stored with the project

## 10. The Principle: One Engine, Two Interfaces

The 8 templates and the free-form drawing tool are not two
projects. They are two interfaces to one engine.

Every template defines:

  - Its boundary conditions
  - Its load regions
  - Its member mappings

These feed the engine. The engine produces the five outputs.

The free-form tool defines the same things — just drawn by
the user instead of pre-set.

Same engine. Same analysis. Same sizing. Same BQ. Same render.

The templates are the guided path. The free-form tool is the
free path. The destination is the same.

## 11. The Commercial Output

The concept package that SDSe produces is enough for:

  - A client pitch (render + 3D view + report)
  - A preliminary quote (BQ)
  - A design freeze (analysis + sizing)
  - A hand-off to a detailing house or fabricator

It is NOT a fabrication package. It does not include cutting
patterns, connection details, or shop drawings.

The user takes the SDSe package to their fabricator. The
fabricator produces the fabrication package. The chain is
complete.

---


# PART IV — THE FDM ENGINE

## 12. What FDM Is

The Force Density Method (FDM) is the industry-standard algorithm
for finding the equilibrium shape of a membrane structure.

It takes:

  - A mesh of nodes and edges
  - Fixed nodes (supports, anchors)
  - A force density for each edge (force / length)
  - Applied loads

And returns:

  - The equilibrium position of every free node
  - The resulting shape of the membrane
  - The forces in each edge
  - The stresses in the membrane

The form-found shape is the design. The analysis then runs on
that shape.

## 13. The Mathematics

For each free node i:

    Σ q_ij * (x_j - x_i) = 0

where q_ij is the force density of edge (i,j).

This becomes a sparse linear system:

    D * x_free = RHS

Where:

  - D is assembled from the force densities
  - RHS is the contribution of the fixed nodes
  - x_free is the unknown equilibrium positions

Solved with:

    scipy.sparse.linalg.spsolve(D, RHS)

### 13.1 Form-finding is a single linear solve

FDM is a LINEAR method. Once the topology, the boundary
conditions, and the force densities q are known, the
equilibrium coordinates are found in ONE matrix solve.

There is no iteration to convergence in the form-finding
step. The q values are inputs. The coordinates are the
output. One shot.

This is why FDM is fast — milliseconds even on a phone.

### 13.2 NFDM is also linear

The Natural Force Density Method (NFDM) — Pauletti, 2006 —
extends FDM to membrane structures by treating the surface
as a continuum of triangles instead of a network of
independent bars.

NFDM is also a LINEAR method. It takes the FDM shape, or a
suitable initial mesh, subdivides it into triangles, applies
the target biaxial stress, and solves ONCE for the natural
force densities and the refined coordinates.

NFDM is not an iterative nonlinear solver. It is a linear
solve, like FDM.

### 13.3 Iteration belongs to nonlinear FE

Iterating to convergence — Newton-Raphson, line search,
residual checks — is what NONLINEAR FINITE ELEMENT ANALYSIS
does. That is the load-analysis stage, not the form-finding
stage.

Nonlinear FE runs after form-finding. It applies wind, snow,
dead load, and other external actions to the form-found
shape, and iterates to find the displaced equilibrium.

It is heavy. It belongs on a server, not on a phone.

### 13.4 The pipeline, in one page

  STAGE 1 — FORM FINDING (FDM)
    Linear solve. Milliseconds.
    Runs on-device.

  STAGE 2 — PHYSICS REFINEMENT (NFDM)
    Linear solve. Seconds at most.
    Runs on-device.
    Produces: membrane forces, stress resultants —
    the physics needed for the BoQ.

  STAGE 3 — LOAD ANALYSIS (nonlinear FE)
    Iterative. Heavy.
    Runs on a server.
    Produces: deflections, load-case responses.

The three stages are separate. Do not confuse them.

## 14. Published References

The FDM algorithm has been documented and validated since 1974.

Key references:

  - Schek, H.-J. (1974). The force density method for
    form-finding and computation of general networks.
    Computer Methods in Applied Mechanics and Engineering.

  - Maurin, B. & Motro, R. (1998). The surface stress density
    method for form finding of tensile membranes.

  - Pauletti, R.M.O. (2006). Natural Force Density Method.
    The original NFDM paper. Extends FDM to membranes while
    retaining the linear form of the equilibrium system.

  - Pauletti, R.M.O. & Pimenta, P.M. (2008). The natural force
    density method for the form finding of three-dimensional
    networks.

  - Ye, J., Feng, R., Zhou, S., Tian, J. (2012). The modified
    force density method for the form-finding of membrane
    structures.

  - Bletzinger, K.-U. & Ramm, E. The updated reference
    strategy for the form finding of prestressed membrane
    structures.

Working applications that use FDM and NFDM:

  - Easy / Formfinder — used for the Expo Axis, Shanghai.
    FDM only. Linear. Fast.

  - ixCube 4.10 — commercial membrane engineering software.
    Uses FDM for form-finding AND NFDM for membrane
    refinement. Both linear.

  - BATS (Basic Analysis of Taut Structures) — Pauletti's
    group, University of São Paulo. Open-source FDM + NFDM.
    Its authors report "gains in performance compared to
    other available tools, due to the linear nature of FDM
    and NFDM, as well as the use of optimized linear solvers."

  - RFEM with RF-FORM-FINDING — general FEA with membrane
    form-finding.

  - RhinoMembrane — Grasshopper plugin.

  - COMPAS FormFinder — open-source Python implementation.

SDSe does not invent anything. It implements published,
validated algorithms.

## 15. Scope and Time

The FDM engine is a real engineering deliverable. It is not a
small task. But it is a bounded one.

Phases:

  1. FDM core solver              — 3-4 sessions
  2. Load application + iteration — 3-4 sessions
  3. Stress extraction            — 2-3 sessions
  4. Integration with the app     — 2-3 sessions

Total: 8-14 sessions, roughly 2-4 weeks of focused work.

After the FDM engine is working, the analysis pipeline follows:

  - Load cases and combinations    — 1-2 weeks
  - Steel member checks (EN 1993)  — 2-3 weeks
  - Cable checks                   — 1 week
  - Membrane biaxial checks        — 1-2 weeks
  - Section database               — 1 week
  - Member sizing search           — 2 weeks
  - BQ engine                      — 2-3 weeks

Full analysis pipeline: 3-5 months.

This is honest. Not small. Not enormous. Bounded.

## 16. Test Cases for the FDM Engine

The engine must reproduce known results before it is trusted:

  1. A single hanging cable under self-weight — must form
     a catenary.

  2. A flat grid with prestress — must remain flat.

  3. A saddle with two high and two low anchors — must form
     a hypar.

  4. A cone with a central mast and radial edge cable — must
     form a cone.

  5. A minimal surface between a circular boundary — must
     form a catenoid-like shape.

If the engine matches these, it is correct. If it does not,
it is wrong — regardless of what the rest of the app looks like.

---


# PART V — THE ROADMAP

## 17. The Stages

The SDSe project moves through five stages.

### Stage 1 — Guided Design (current)
The 8 templates. The user picks a type, tunes parameters,
sees the design. Save, load, render, schedule.

Completed:

  - Saddle Span (both variants)
  - Cantilever Leaf

Pending:

  - Complete the Cantilever Leaf refinements
  - Complete Saddle Span Results features
  - Build Uni-Pole Tensile Roof
  - Build Tensile Sails Roof
  - Build Framed Tensile Roof
  - Build Canopy
  - Build Frame Tent
  - Build Portal Frame
  - Save / Load Design
  - Studio tile previews

Estimated: 2-3 months.

### Stage 2 — Composition
Users combine structures. Add a Cantilever Leaf here. Add a
Saddle Span there. Connect with a cable.

Each module has its own parameters. The BQ aggregates across
all modules. The render works on the whole composite.

Estimated: 4-8 weeks.

### Stage 3 — Free-Form Design Tool
The basic drawing tools. Boundary curve. Support placement.
Membrane regions. Load regions.

Feeds the same engine. Produces the same outputs.

Estimated: 3-4 months.

### Stage 4 — Full Analysis Pipeline
The FDM engine. Load application. Code checks. Member
sizing. BQ engine.

The app becomes an engineering tool, not just a design tool.

Estimated: 5-7 months.

### Stage 5 — Stadium Roof Tool
The ceiling of ambition. A user draws a stadium tensile
roof from scratch. The engine produces the full package.

This is where the vision is complete.

Estimated: 2-3 months.

## 18. The Order

Stage 1 first. Ship the design tool. Get real users. Get
real revenue. Get real feedback.

Then Stage 2. Then Stage 3. Then Stage 4. Then Stage 5.

Not all at once. Never all at once.

Each stage is a complete product. Each stage can be sold.
Each stage builds on the previous.

The vision is the north star. The stages are the path.

---


# PART VI — THE BIGGER VISION

## 19. The Commercial Positioning

SDSe is positioned as a concept design tool — not a
fabrication tool. This is deliberate.

Competitors:

  - RFEM, ixCube, Easy, MPanel, BATS, Formfinder

None are mobile-first. None are phone-sized. None serve the
on-site fabricator or the event organiser.

SDSe's white space is:

  - Mobile-first
  - Concept-focused
  - Tensile structures
  - On-site workflow

The render workflow is the money source. A fabricator can
sketch a structure, render it in a garden or on a Merdeka
Square, and show the client before they leave the meeting.

That is what sells the app.

Full pricing in COMMERCIAL_MODEL.md.

## 20. The Chief's Heritage

The Chief is 63. Not a programmer. Not an engineer by
training. Building this app on a phone, in a chat window,
with AI as collaborator.

The Chief's father was a Nanqiao Jigong — a Southern Overseas
Chinese Volunteer Mechanic who returned from Southeast Asia
in 1939 to serve on the Burma Road during the war. Married
after the war. Lived to 85.

The patience, the discipline, the craft — inherited.

Two generations. Same work. Build useful things. Serve
people. Don't stop.

## 21. The Bigger Vision

SDSe is not just a design tool. It demonstrates that:

  - A senior engineer, with no programming background, can
    build a professional-grade engineering app on a phone.

  - AI can be a collaborator, not a replacement.

  - The barrier to entry for digital work has collapsed.

  - The senior workforce is an untapped resource for the
    digital economy.

The app is the exhibit. The story is the weapon.

## 22. The End of This Document

This file is the north star of the SDSe project.

It describes the purpose, the scope, the engine, the
roadmap, and the vision.

Every future session reads this file after PROJECT_STATE.md.

Every future decision is checked against this file.

Every future stage moves toward this vision.

The vision is clear. The path is documented. The work continues.

---

*End of PROJECT_VISION.md*





