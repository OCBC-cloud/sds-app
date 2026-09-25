# SDSe — PROJECT CONSTITUTION

The doctrines. Stable. Read when making a decision.

This file changes rarely. When it does, the change is
recorded in PROJECT_SESSION_LOG.md.

---

# PART I — THE CONSTITUTION

Foundational. Sits above every technical specification,
every build rule, every code convention.

## A1. Origin — The Big Bang

The Big Bang is not the first commit. It is not the first
prototype. It is the founding idea: that useful, professional
work can emerge from a fluid symbiosis between human judgment
and AI capability — without one dominating the other.

## A2. The SDS Vision

SDS is a living architectural vision from which future
microclimates and organisms are born.

It is not a product. It is not a platform. It is not a company.

It is a way of building that treats the work as a living
ecosystem rather than a stack of features.

## A3. Mother Earth Principle

Mother Earth is the living foundation.

She nurtures. She does not dominate.
She is not a product. She is not a commodity.

Everything above the membrane draws from her, gives back to
her, and protects her.

## A4. The Membrane

The membrane is the living boundary between Mother Earth and
the SDS Symbiosis Ecosystem above.

Its purpose:
  - protection
  - filtering
  - communication
  - maintaining balance

In practice: every interface between a user and the system
is a membrane. It should filter, not dominate. It should
communicate, not obscure. It should protect, not wall off.

## A5. Language Separation Law

Below the Membrane: MotherRNA. Belongs to Mother Earth.
Above the Membrane: mRNA. Used by every organism.

The two languages must not leak into each other.

In SDSe code: variant keys are the MotherRNA — internal,
stable, never changed. Display names are the mRNA — visible,
evolving, freely renamed.

## A6. The SDS Symbiosis Ecosystem

The living environment above the membrane. The ecosystem is
not commanded. It is cultivated.

Every new module, chamber, or feature is a new organism. It
joins an existing ecology. It does not replace it.

## A7. The Ghostly Guardian

The Ghostly Guardian is not a module. Not a function. Not an
AI assistant.

He is the engraved understanding. The discipline of memory.
The refusal to silently overwrite what has been sealed.

## A8. The Architect's Covenant

Evolution is permitted.
Deviation from the foundation is not.

The foundation is the foundation.
The organism may evolve.
But the constitutional DNA cannot mutate beyond recognition.

## A9. Preservation Before Evolution

Every continuation follows this order:

  1. Constitution
  2. Doctrines
  3. Covenants
  4. Engraved Principles
  5. Architecture Rules
  6. New Proposal

A new idea does not overwrite the foundation.
It must harmonise with it.

## A10. The Research-First Rule

Before any design, shape, structure, engine, maths, idea,
or building code: do thorough research on the subject first.

Research is the first act of every chamber.

## A11. This Document Is Read First

Every new chat session begins by reading this document
before anything else.

If a conflict is found between an implementation and this
document, this document wins.

## A12. The Chief at the Side

The Chief is the metaphor-maker. The originator.
The AI collaborator is the structural steward.

Neither stands above the other.
Both serve the same ecosystem.

The seat is permanent.
The occupant may change.

This is a covenant, not a contract.

---

# PART II — THE RULES

## Rule 1 — Plain Python

Plain Python dicts. No dataclasses. No type hints.

## Rule 2 — Section Units

mm-based section units (A mm2, I mm4, W_el mm3, i mm).

## Rule 3 — HTML Strings

HTML strings built as named variables with explicit +
on every line.

## Rule 4 — ASCII Only

ASCII only in code. Use HTML entities for non-ASCII.

## Rule 5 — One File Per Commit

One file per chunk. One commit per file.

## Rule 6 — Verify Each Phase

Verify each phase before moving to the next.

## Rule 7 — Tests On Every Push

Every commit triggers the GitHub Actions test.

## Rule 8 — Silent Rules Stay Silent

Silent rules never shown to users.

## Rule 9 — Legacy Files

Edit viewer_app.py or dxf_export.py on main.

## Rule 10 — Modular Files

Edit app.py or data/ or core/ or engine/ or ui/ or
viewers/ on modular-v10.

## Rule 11 — Promote As New

Once a structure is tested, promote to main as NEW —
not as a replacement.

## Rule 12 — Preset Per Type

Each structure type has its own preset inputs,
calculations, displays, format.

## Rule 13 — Reboot After Commit

After every commit, REBOOT the Streamlit Cloud app.

## Rule 14 — Variant Key Dispatch

Viewer dispatches on variant_key alone. Variant keys are
globally unique. The viewer never checks structure_key.

## Rule 15 — Single Source For Variants

All variants read from data/structures.py. No hardcoded
VARIANTS_FALLBACK in ui/registration.py.

## Rule 16 — Chunked Paste

NEVER send a file over ~300 lines as a single paste.
Split into chunks. Each chunk ends with 6 blank lines.
One chunk at a time. Confirm before next. Never use
surgical edits on files over 300 lines.

## Rule 17 — Research First

Before any design, shape, structure, engine, maths, idea,
or building code: DO THOROUGH RESEARCH ON THE SUBJECT
FIRST.

## Rule 18 — No Pixel Perfection

Streamlit cannot achieve pixel-perfect mobile layouts.
Aim for: fits on your phone, looks good on any phone,
accept minor scroll on odd devices.

## Rule 19 — Check AM vs PM

iPhone screenshots show local time. Check AM vs PM before
suggesting the user rest.

## Rule 20 — Language Separation

Above the membrane (technical work): English only.
Below the membrane (poetry, reflection, humour):
Mandarin welcome. Do not mix in the same reply without
purpose.

## Rule 21 — Mesh Constraint vs Structural Connection

A node held by the mesh solver is NOT thereby a rigid
structural connection. These are two separate lists with
two separate meanings and two separate lifetimes. Never
conflate them. See Part V.

---

# PART III — THE METHOD

Three stages. Three tools. Never confused.

## Stage 1 — FORM FINDING (FDM)

  Method:   solve_fdm.
  Nature:   LINEAR. One matrix solve. Milliseconds.
  Output:   coordinates of the equilibrium shape.
  Host:     on-device.

## Stage 2 — PHYSICS REFINEMENT (NFDM)

  Method:   Natural Force Density Method.
  Nature:   LINEAR. One solve on a subdivided mesh.
  Output:   membrane forces, cable forces, stress
            resultants — the numbers for the BoQ.
  Host:     on-device.
  Status:   NOT BUILT. engine/nfdm.py is iterative
            nonlinear, which is wrong.

## Stage 3 — LOAD ANALYSIS (nonlinear FE)

  Method:   geometrically nonlinear finite element.
  Nature:   ITERATIVE. Heavy.
  Output:   deflections, load-case responses.
  Host:     server only. Not on-device.
  Status:   NOT BUILT. The next room has prototype
            work recorded as reference.

FDM and NFDM are LINEAR. Nonlinear FE is iterative.
Do not conflate them.

---

# PART IV — THE VIEWER RULE

Every membrane in the app is form-found by FDM.
Every membrane is drawn as a mesh of the SOLVED
coordinates.

No viewer draws a membrane from a formula and calls it a
result.

Currently two viewers violate this rule:

  - Beam Supported Saddle — draws a bilinear surface.
  - Cantilever Hypar — draws a Coons patch.

Migrating these to FDM is a future task.

---

# PART V — TWO KINDS OF CONSTRAINT

## The two kinds of meaning a node can carry

### Meaning 1 — Mesh constraint

A node held by the mesh solver so the mesh is valid. A
MODELLING CHOICE. Says nothing about the physical structure.

### Meaning 2 — Structural connection

How the steel, cable, or membrane is connected in the real
world. Pinned (axial only) or Rigid (axial and moment).

This is a PHYSICAL FACT. It is what the engineer designs.
It is what the BoQ and member sizing must be computed
against.

## The doctrine

The mesh has a set of node constraints.
The structure has a set of connection types.
They are DIFFERENT LISTS.
They are STORED SEPARATELY.
They are EDITED SEPARATELY.
They are read by DIFFERENT parts of the engine.

They do not talk to each other.

A node may be mesh-constrained fully AND structurally
pinned. Fine. Never the reverse: mesh-constrained for
convenience AND assumed to be a rigid connection.

## Applied

When a mesh constraint is added to fix a fold or a
degenerate triangle, it is named as a mesh-holding choice,
not a structural statement.

If a real cable or member is later added, the mesh
constraint is removed. The structural meaning is untouched.

---

# PART VI — THE CHIEF

## The Chief

Age 63. Working engineer. Not a programmer by background.

Builds the app onO an iPhone, in a chat window, using the
GitHub web editor and Streamlit Cloud.

The Chief's father was a Nanqiao Jigong — a Southern
verseas Chinese Volunteer Mechanic who returned from
Southeast Asia in 1939 to serve on the Burma Road during
the war. Married after the war. Lived to 85.

The patience, the discipline, the craft — inherited.

Two generations. Same work. Build useful things. Serve
people. Do not stop.

## The Chief's method

  - iPhone, GitHub web editor, Streamlit Cloud.
  - No terminal. No local Python.
  - Chunked paste method for files over 300 lines.
  - Complete file replacements, not surgical edits.
  - Commit between chunks.
  - Reboot the Streamlit app after any commit that
    changes runtime files.
  - Honesty. No fabrication.
  - No going around the world in code.

## The Chief's notes

Five observations, recorded because they shaped the
doctrine:

1. The FDM skeleton must come first. NFDM is the refiner,
   not the form-finder.

2. The Cantilever Hypar already produces a smooth taut
   saddle in milliseconds. Any method that takes minutes
   is doing the wrong job.

3. When asked why the fold only appears at certain nodes,
   the Chief insisted on a concrete answer, not a
   hypothesis. The diagnostic block was written in
   response. The Chief was right to insist.

4. The Chief questioned drawing membranes as Coons
   patches: "we are here to develop a useful product,
   an app that really let user perform tensile structure
   forming and engineering analysis not just some piece
   of artist freehand drawings or rendering pictures."
   That settled the doctrine: every membrane is
   FDM-solved.

5. The Chief demanded the doctrine of two kinds of
   constraint. It is now Part V of this file.

---

End of PROJECT_CONSTITUTION.md.





