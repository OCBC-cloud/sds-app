# UNDERSTANDING — Cantilever Hypar Membrane

Date: 2026-09-22.
Status: reference document.
Purpose: to record, in plain language, what was built for the
Cantilever Hypar on 2026-09-20 and 2026-09-21, and to set the
mandate for revisiting the earlier structures so that every
membrane in SDSe behaves as a true tensile membrane roof.

Related:
  engine/PRINCIPLES_membrane.md
  engine/PLACEHOLDERS.md
  engine/SPEC_cantilever_hypar.md

---

## 0. Why this document exists

The Cantilever Hypar was built over two days, with several
false starts. Each false start taught us something about how a
tensile membrane should be modelled in SDSe. Those lessons are
now embedded in the Hypar viewer and workshop, but they are not
written down anywhere except in code comments.

This document writes them down. It is the reference for the
next phase of work: revisiting the earlier structures
(Cable Supported Saddle, Beam Supported Saddle, Cantilever
Leaf) and upgrading their membrane behaviour — and if needed,
their total mechanics — to match.

The goal is simple: every structure in SDSe should be modelled
as a proper tensile membrane roof. Not a skin draped over a
frame. Not a flat panel stretched between supports. A tension
surface that finds its own equilibrium form.

---

## 1. The idea, in one sentence

Cantilever Hypar is a saddle membrane cantilevered out
sideways from a column, with the membrane supported only at
four points: the two ends of a curved arm and the two tips of
a curved rib that crosses the arm at its midpoint.

Everything else in the code flows from that sentence.

---

## 2. The membrane is the hero

This is the principle in engine/PRINCIPLES_membrane.md. It is
the single biggest idea behind the entire build.

The membrane is not draped over the structure. It is a
tension surface. It touches the structure only at its support
points. Between those points, it finds its own form: a saddle.
The steel is placed to suit the membrane, not the other way
round.

Every attempt before this one failed because this rule was
ignored. The work was drawing the steel first and patching a
membrane between it. When the order was reversed — membrane
first, steel follows — the whole build snapped into focus.

This rule governs every future structure in SDSe.

---

## 3. The four corners A, B, C, D

The Hypar membrane has exactly four support points. Named in
the code as A, B, C, D.

  A — the arm's anchor end, on the column, at height
      anchor_z (default 65% of column height).
  C — the arm's free tip end, reaching out at arm_reach
      horizontally. Same height as A.
  B — one rib tip, at +rib_reach in the cross direction.
  D — the other rib tip, at -rib_reach. Same height as B.

Therefore:

  A and C are LOW.
  B and D are HIGH.
  Two opposite pairs alternate around the boundary.

That IS a hypar. A saddle. The high points pull up, the low
points pull down, and the surface between them curves in
opposite directions along its two diagonals.

The four corners define the whole shape. Everything else is
derived from them.

---

## 4. The cables run along the fabric edges

The cable is not a separate straight line drawn next to the
fabric. The cable IS the fabric edge. One curve, one trace,
drawn together.

That curve is CONCAVE INWARD. Between any two corners, the
fabric and the cable together bow in toward the centre of the
membrane. Not a straight chord. A curve.

The magnitude of that bow is a user input — the "Membrane
Edge Sag (%)" slider. 0% means straight edges. 30% means deep
concave edges. 15% is the default.

This is the placeholder for the FDM engine. When the real
form-finding arrives, the sag will come from pretension
equilibrium, not from a slider. Until then, the user can see
the effect directly.

---

## 5. The rib is one continuous arc

The rib is not two separate members. It is ONE continuous arc
that passes through three points:

  the left rib tip (point D),
  the arm's midpoint (the low point of the arc),
  the right rib tip (point B).

The arm's midpoint is the LOWEST point of the rib arc. The
two tips are the HIGHEST. That shape — a wide, shallow U — is
what makes the saddle.

The arc has a RADIUS. That radius is a user input — "Rib
Curve Radius (m)". If the user gives a radius that cannot
physically reach both tips at the given rib reach, the engine
adjusts it automatically and warns. That way the geometry
always stays coherent.

---

## 6. The arm

The arm is a curved steel member running from A to C. One end
anchors to the column at anchor_z. The other end is free, out
at arm_reach. It arcs UPWARD in the middle. Both ends are at
the same height.

Visually it is the red curve in the viewer.

---

## 7. The strut

A diagonal steel member from the column top down to a point
on the arm. Its job is to triangulate the arm into the column
so that the cantilever moment is not carried as pure bending
into the column base.

The engine computes where the strut meets the arm. For now
that is a simple geometry intersection. Later, when the
structural engine lands, it will be a mechanics-optimum.

The strut is the orange line in the viewer. It ends cleanly
on the arm — no joint marker, no bolt, no decoration.

---

## 8. The column

Straight vertical. No curvature, no taper (yet). Thickness
comes from column_radius — a placeholder until the structural
engine picks a real section.

Green in the viewer.

---

## 9. The membrane surface

Between the four concave edges, the surface is built as a
Coons patch. That is a mathematical way of saying: take the
four boundary curves and smoothly fill the interior so that
it matches all four edges and their tangent directions.

The result is a proper saddle. High at B and D, low at A and
C, curved in the middle.

This is not the true form-found shape. It is the closest
approximation we can build without the FDM engine. The shape
is right; the exact surface curvature is a placeholder.

---

## 10. The arrangement engine

Everything above describes ONE mother object — one hypar
canopy on one column.

The arrangement engine (engine/leaf_arrangement.py) takes
that mother object and multiplies it. Five modes:

  single       — one canopy, as designed.
  double       — two mirrored canopies, 180 degrees apart.
  multiple     — N canopies evenly around the column.
  tree_stack   — canopies stacked in tiers, scale 0.75 each,
                 rotated 45 degrees per tier.
  tiered_helix — canopies spiralling up the column, using the
                 golden-angle placement engine.

Crucially, the arrangement engine does not know what the
mother object is. It returns position, rotation, and scale for
each copy. It is shape-agnostic. The same engine that places
Cantilever Leaves places Cantilever Hypars. No new code.

That is the payoff of the modular design. Every future variant
gets the five arrangements for free.

---

## 11. The workshop

ui/workshops/saddle_hypar.py. Nine collapsible sections:

  1. Object Shape
  2. Geometry
  3. Materials
  4. Column and Strut
  5. Ribs
  6. Membrane Attachment
  7. Baseplate and Foundation
  8. Loads and Design Standard
  9. Arrangement

The user tunes geometry in Section 2 — the heart of the
workshop. Everything else follows the standard workshop
pattern established with the earlier structures.

---

## 12. The user inputs — what is real, what is placeholder

Real user inputs (they describe the problem):

  Column height
  Arm reach
  Anchor height fraction
  Rib reach
  Rib curve radius
  Membrane edge sag
  Membrane pretension
  Foundation, loads, design standard
  Arrangement mode

Placeholders (they stand in for what the engines will compute):

  Column radius         — will come from the structural engine
  Arm arc radius        — same
  Rib curve radius      — same
  Membrane edge sag     — will come from the FDM engine

Every placeholder is documented in engine/PLACEHOLDERS.md.
When the structural and FDM engines land, that one file is
opened, the rows are found, the inputs are removed from the
UI, and the engines supply the values.

---

## 13. The render prompt

The Results page hands the user a short prompt for an external
AI renderer:

  "Photorealistic architectural photograph of a Cantilever
   Hypar tensile membrane structure. A curved arm cantilevered
   from the column, with two perpendicular ribs at its
   midpoint, holding a taut four-corner saddle fabric
   membrane whose edges curve inward under tension."

Then lighting. Then scene.

Three parts: shape, lighting, scene. Short. No technical spec
sheet. No camera settings. Fits under Bing's 480-character
limit.

The AI does not reproduce the structure perfectly. It
produces a MOOD image. Close enough to sell. Not engineering
documentation. That limitation is accepted and documented.

---

## 14. What makes the whole build coherent

Every piece of the code is answering the same question: what
is the membrane doing, and what is the structure doing to make
that possible?

  The membrane defines the four corners.
  The four corners define the cables and edges.
  The cables define the ribs and the arm.
  The strut and column tie the arm into the ground.
  The arrangement engine multiplies the whole mother object.

The membrane is the hero. Everything else follows.

That is the essence of the code, and the essence of the
design.

---

## 15. What waits for the engines

Three things are not yet built, and the code is written to
accommodate them.

The FDM engine will replace the Coons patch with a
form-found surface, computed from pretension equilibrium.
The sag will no longer be a slider.

The structural engine will replace every placeholder input
with a computed value: column section, arm section, rib
radius, everything.

A full render scene will eventually place the structure with
real people, real lighting, real environment. Not essential
for the concept package, but good for the pitch.

Each of these is a bounded piece of work. None is a research
project. The membrane-first principle, the placeholder
document, and the modular architecture are what make them
possible.

---

## 16. The mandate for the next phase

The Cantilever Hypar is now a proper tensile membrane
structure in the app. The membrane behaves as a tension
surface. The cables run along the edges as concave curves.
The ribs and arm are shaped to suit the membrane.

The other three live structures do not yet behave this way:

  Cable Supported Saddle       — flat membrane panel in the
                                 viewer, no concave edges
  Beam Supported Saddle        — same
  Cantilever Leaf              — membrane follows the ribs,
                                 not a free tension surface

The next phase is to revisit each of them, one at a time, and
upgrade their membrane behaviour to match the Hypar pattern.
If a structure needs its total mechanics rethought — not just
its membrane — that is on the table too.

The sequence:

  1. Write a short spec for each structure describing what its
     membrane corners are, where they attach, how its free
     edges behave, and what its supporting members need to do.

  2. Rebuild the viewer so the membrane is drawn first, from
     its corners outward, with concave edges and a saddle
     surface.

  3. Adjust the workshop inputs to expose any parameter the
     new membrane behaviour needs (edge sag, corner positions,
     curvature radius, etc.).

  4. Adjust the render prompt shape sentence so the words
     match the new membrane shape.

  5. Add placeholder rows to engine/PLACEHOLDERS.md for any
     input that will be replaced when the FDM engine lands.

  6. Add or update the arrangement behavior if the structure
     supports multiple mother objects.

  7. Test end to end. Renders should match the viewer.

The order of work: start with Cable Supported Saddle, then
Beam Supported Saddle, then Cantilever Leaf.

The same understanding that produced the Hypar will produce
the upgraded versions of these three. The principles do not
change. Only the geometry does.

---

## 17. The bigger picture

Once all four structures share the same membrane-first
approach, SDSe will have a coherent design language. Every
structure in the app will be a proper tensile membrane, drawn
the way a tensile membrane should be drawn.

That is when the FDM engine will slot in cleanly. It will
replace the Coons patch, but the surrounding geometry will
already be right. The membrane will be in the right place,
supported at the right corners, with the right free edges. All
the engine has to do is find the exact equilibrium surface.

Without the membrane-first rebuild, the FDM engine would have
to fight the existing geometry. With it, the engine plugs in.

This is the reason the rebuild is worth doing.

---

End of document.





