# MEMBRANE GUIDE — SDSe

Date created: 2026-09-22.
Status: living document. Additive.
Purpose: the single reference for how membranes behave in
SDSe, and how each structure's membrane is drawn.

Read this file before starting any new structure, or before
revising any existing one.

Related:
  engine/PLACEHOLDERS.md         — inputs waiting for the engines
  engine/SPEC_<structure>.md     — per-structure build specs

---

# PART 1 — THE PRINCIPLE

## 1.1 The membrane is the hero

A SDSe membrane is never a skin draped over the structure.

It is a tension surface. Its shape is determined by the
pretension equilibrium between the fabric and its edge cables.
The engineer does not draw the membrane shape. The engine
solves for it.

The membrane touches its structural members only at the
support points — the corners, or wherever the boundary
condition fixes it.

Between those supports, the membrane is a free span that finds
its own equilibrium form:

  - Every free edge is cable-supported and concave inward
    toward the membrane centre.
  - The surface between the edges is form-found: saddle, cone,
    dome, or the correct shape for the given boundary.
  - The magnitude of the concavity and the surface curvature is
    set by the pretension equilibrium, not chosen by the user.

This is the way all SDSe structures behave.

## 1.2 The one exception — attach-to-beam

If the user selects "attach to beam" instead of "detached from
beam", the beam becomes the boundary condition for that
membrane edge.

In that case:

  - The membrane edge follows the beam.
  - There is no free cable curve on that edge.
  - Concavity on that edge is zero.

This exception is explicitly chosen by the user. The default
is always detached (form-found). Detached is the true SDSe
form.

## 1.3 Where the principle applies

Every structure type. Every variant. Every viewer. Every
future spec.

There is no membrane type in SDSe where the membrane is drawn
as a flat or arbitrarily-shaped panel.

## 1.4 Staged implementation

Full form-finding requires the FDM engine, which is pending.

Until the FDM engine is in place, viewers will:

  - Draw membrane surfaces as saddle / cone / dome
    approximations between the support points.
  - Draw free edges as concave inward arcs with a fixed sag
    fraction (10–30% of edge length, user-adjustable).

These are approximations. They keep the viewer functional
while the engine is being built. Every such approximation is
marked in the code as TEMPORARY — replace with FDM result.

When the FDM engine lands, the fixed fractions are replaced by
the solved equilibrium state. The shape of every membrane in
every structure changes to match.

## 1.5 What the principle forbids

  - A membrane drawn as a flat panel between supports.
  - A membrane free edge drawn as a straight line (unless
    attach-to-beam).
  - A membrane surface draped over ribs, purlins, or beams.
  - A membrane that touches a structural member anywhere
    except at its support points.
  - A user-facing control that lets the user set the membrane
    shape directly, other than the pretension inputs which
    define the target stress state.

---

# PART 2 — THE THREE BOUNDARY FAMILIES

Every SDSe membrane has a boundary. The boundary is where the
membrane meets its structure. Almost every membrane in SDSe
belongs to one of three boundary families.

A structure can also belong to a combination of families — for
example, a saddle span has two edges attached to beams (edge-
based) and two free cable edges at its ends (corner-based).

## 2.1 Corner-based

Boundary: a finite number of discrete support points, called
corners.

Between the corners, the boundary is a free cable edge that
bows inward toward the membrane centre.

Examples:

  - Cantilever Hypar — four corners (two arm ends, two rib
    tips). All four edges are free cables.
  - Cantilever Leaf — many corners (the tips of the ribs).
    Free cable edges run between the rib tips.
  - Tensile Sail — 3 or 4 corners (anchor points). All edges
    are free cables.

Surface between corners: saddle, or a multi-lobed saddle if
there are more than four corners.

## 2.2 Edge-based

Boundary: one or more edges are attached along a linear
structural member — a curved beam, a straight beam, a wall, or
a rigid frame.

Where the membrane is attached to the member, the fabric edge
follows the member. Where the boundary is free, the fabric
edge is a free cable edge and bows inward.

Examples:

  - Cable Supported Saddle — the two long edges follow the
    curved beams. The two short edges at each end are free
    cable edges.
  - Beam Supported Saddle — same as above, with purlins
    crossing the span.
  - Wall-Mounted Shade — one edge attached to the wall.
    Remaining edges free.
  - Framed Tent — the frame defines the boundary all the way
    around. Membrane attached to the frame along its full
    perimeter.

Surface between supports: saddle, or the correct form-found
surface for the given boundary.

## 2.3 Loop-based

Boundary: a closed curved line — a ring, a circle, an oval, or
a polygon of discrete points.

The membrane attaches to the loop. There are no free edges in
the corner sense. The fabric runs from the mast out to the
loop, in radial or helical fashion.

Examples:

  - Cone (Uni-Pole) — a central mast, a ring of anchors or an
    edge cable forming a closed loop.
  - Multi-Cone Cluster — several cones side by side.
  - Umbrella — a mast with an edge ring.

Surface between the mast and the ring: a cone, or a
cone-like form-found surface.

## 2.4 Combinations

Some structures belong to more than one family.

Examples:

  - Saddle Span is edge-based on its long edges, corner-
    based on its short edges.
  - A walkway with two saddle spans end to end is corner-
    based at the joint.

When a structure belongs to more than one family, the drawing
rules for each part follow the appropriate family. The
principle (Part 1) applies to the whole.

---

# PART 3 — HOW TO DRAW EACH FAMILY

Detailed drawing rules for each family, with code-level
guidance. This is the reference for anyone building a new
viewer.

## 3.1 Corner-based drawing

Steps:

1. Define every corner as a 3D point. Name them (A, B, C, D,
   or indexed if many).

2. For each pair of adjacent corners, draw a free cable edge
   that bows inward toward the membrane centre. In the
   placeholder implementation, the inward bow is a parabolic
   arc of magnitude `sag_frac × edge_length`, where sag_frac
   is user-adjustable.

3. The membrane surface is a Coons patch, or a higher-order
   surface if there are more than four corners. The patch is
   bounded by the free edges.

4. The cable follows the same curve as the fabric edge. One
   trace, one curve. There is no separate straight cable line.

5. The membrane touches each corner exactly once. It does not
   touch any member anywhere else.

## 3.2 Edge-based drawing

Steps:

1. Identify which edges follow structural members. For each,
   the edge is the member's own curve, offset zero.

2. Identify which edges are free. For each free edge, bow
   inward as in the corner-based rule.

3. Build the surface between the four boundary edges. If
   opposing edges are both attached to members, the surface
   is a ruled saddle. If one or more edges are free cable
   arcs, the surface is still a saddle but the curvature is
   influenced by the inward bow.

4. The cable exists only along the free edges. Attached edges
   have no visible cable — the fabric meets the member
   directly.

5. The membrane touches the members along the attached edges
   (not just at corner points). It touches the free edges
   only at their endpoints.

## 3.3 Loop-based drawing

Steps:

1. Define the mast axis (vertical) and the ring of anchors
   or edge cable (the loop).

2. The membrane is drawn as a surface of revolution between
   the mast and the loop, or as a triangulated shell if the
   ring is polygonal.

3. The ring itself may be a free cable edge (if it is an edge
   cable) or a fixed boundary (if it is anchored to ground
   points). If it is a free cable edge, it bows inward — a
   catenary sag between anchor points.

4. There is usually one edge cable running around the ring.
   In some cases there may be radial edge cables from the
   mast to the anchors.

5. The membrane touches the mast along a line (its top
   edge), and touches the ring along the loop. It does not
   touch structure anywhere else.

## 3.4 Combinations

Draw each family's part using its own rules. Join them at the
shared boundary. The principle (Part 1) holds throughout.

---

# PART 4 — PER-STRUCTURE REFERENCE

One section per structure. Each section follows the same
template:

  ### <Structure Name>

  Family:
    Corner-based / Edge-based / Loop-based / combination.

  Boundary conditions:
    Where does the membrane attach? Which members fix it?

  Free edges:
    Which edges are free? Which are attached?

  Surface type:
    Saddle / cone / dome / free-form.

  Reused from:
    Which existing structure is the closest ancestor?

  Notes for the viewer:
    How to draw the membrane. Specific corners, edges, and
    placeholders.

  Notes for the render prompt:
    How to describe the membrane in words, for the external
    renderer.

---

Sections to be added as structures are built or revised:

  - Cable Supported Saddle
  - Beam Supported Saddle
  - Cantilever Leaf
  - Cantilever Hypar
  - Cantilever Cone (future)
  - Cantilever Pyramid (future)
  - Cantilever Bell (future)
  - Cantilever Sail (future)
  - Cantilever Flower (future)
  - Uni-Pole Single Cone (future)
  - Uni-Pole Multi-Cone Cluster (future)
  - Uni-Pole Umbrella (future)
  - Tensile Sail — 3 Anchors (future)
  - Tensile Sail — 4 Anchors (future)
  - Multiple Wall-Anchored Sails (future)
  - Multiple Column-Mounted Sails (future)
  - Simple Frame + Fabric (future)
  - Arched Frame + Fabric (future)
  - Trussed Frame + Fabric (future)
  - Wall-Mounted Shade (future)
  - Cable-Supported Shade (future)
  - Tree Canopy (future)
  - Pyramid Tent (future)
  - Modular Tent (future)
  - Cone Tent (future)
  - A-Frame Tent (future)
  - Arch Tent (future)
  - Simple Portal (future)
  - With Mezzanine (future)
  - With Crane (future)
  - Multi-Bay Portal (future)

The first four (the built structures) will be written next.

---

# APPENDIX A — GLOSSARY

Corner — a discrete support point where the membrane touches
structure and from which its edges hang.

Free edge — an edge of the membrane between two corners, not
attached to a member, supported only by an edge cable.

Attached edge — an edge of the membrane that follows a
structural member (beam, wall, frame) with zero offset.

Edge cable — the tension element that supports a free edge.
It follows the same concave curve as the fabric.

Support point — any place where the membrane touches a
structural member. Either a corner or an attached edge.

Form-finding — solving for the equilibrium shape of a
membrane given its boundary conditions, its pretension, and
its loads. Performed by the FDM engine (pending).

Pretension — the target stress state of the fabric and
cables. Not a shape control. The solver produces the shape
that is in equilibrium with the target state.

Saddle — a surface that curves in opposite directions along
its two principal axes. Characteristic of four-corner
membranes where opposite corners are at different heights.

Cone — a surface of revolution between a mast and a ring.

Dome — a surface of revolution bulging upward. Less common
in tensile membranes; the fabric usually sags.

---

# APPENDIX B — CHANGE LOG

Format: date — change — reason.

2026-09-22 — File created. Consolidates the contents of
  PRINCIPLES_membrane.md and UNDERSTANDING_cantilever_hypar.md
  into one reference, and adds the boundary-family framework.

---

End of document.





---

### Cable Supported Saddle

Family:
  Combination. Edge-based on the two long edges (which follow
  the curved beams). Corner-based on the two short ends.

Boundary conditions:
  Two curved steel edge beams rise from two ground supports
  and converge toward a low point between them. The membrane
  attaches along each beam (long edges, edge-based). The two
  short ends of the membrane are free — they span between the
  ends of the two beams and are supported only by edge cables.

Free edges:
  The two short ends. Each is a free cable edge running
  between the near-end of beam L and the near-end of beam R
  (or between the far ends).

Attached edges:
  The two long edges. Each follows its beam exactly.

Surface type:
  Saddle (hypar). The two beams arc upward; the two free
  short ends bow inward. The combination is a classic hypar.

Reused from:
  The Cantilever Hypar provides the membrane-drawing method
  (four corners, concave free edges, Coons patch surface).
  The two-beam structure itself is unchanged.

Notes for the viewer:
  - Define four corners: the four ends of the two beams.
  - Draw the two long edges as the beam curves (offset zero).
  - Draw the two short edges as concave inward arcs, using the
    same sag slider as the Cantilever Hypar.
  - Draw the membrane surface as a Coons patch bounded by
    those four edges.
  - Draw cables only along the two short edges. The long edges
    have no separate cable — the fabric meets the beams.
  - Do not change the beams, ground supports, or tie-down
    cables. Their geometry is already correct.

Notes for the render prompt:
  Shape sentence for the external renderer:

    "Cable Supported Saddle Span tensile membrane structure.
     Two curved steel edge beams rise from two ground supports
     and converge toward a low point between them, holding a
     taut saddle fabric membrane whose short ends curve
     inward under tension and whose long edges follow the
     beams. Tie-down cables run from each beam to ground
     anchors."

  No numbers. No span, apex, or rise. Shape only.

---

### Beam Supported Saddle

Family:
  Same as Cable Supported Saddle. Combination. Edge-based on
  the two long edges. Corner-based on the two short ends.

Boundary conditions:
  Identical to Cable Supported Saddle, plus cross purlins
  that run across the span and secondary beams that tie the
  main beams down to ground anchors instead of cables.

Free edges:
  The two short ends. Concave inward.

Attached edges:
  The two long edges. Each follows its beam.

Surface type:
  Saddle (hypar). Same as Cable Supported Saddle.

Reused from:
  Same as Cable Supported Saddle.

Notes for the viewer:
  - Everything from Cable Supported Saddle.
  - Purlins and secondary beams stay where they are. They do
    not affect the membrane. The membrane does not touch them
    anywhere.
  - Only the membrane surface and the two short-end cables
    change.

Notes for the render prompt:
  Shape sentence:

    "Beam Supported Saddle Span tensile membrane structure.
     Two curved steel edge beams rise from two ground supports
     and converge toward a low point between them, holding a
     taut saddle fabric membrane whose short ends curve
     inward under tension and whose long edges follow the
     beams. Cross purlins span the membrane, and rigid
     secondary beams tie the main beams down to ground
     anchors."

  No numbers.

---






---

### Cantilever Leaf

Family:
  Corner-based. Many corners — one for each rib tip, plus the
  arm's free end if the spine is exposed.

Boundary conditions:
  A vertical column. A curved spine (the main beam) leaves the
  column and curves upward and outward. Ribs branch off the
  spine at intervals, spreading left and right. Each rib is
  curved. The membrane hangs between the rib tips.

Free edges:
  Every edge between adjacent rib tips. Each is a free cable
  edge and bows inward.

Attached edges:
  None. The membrane attaches only at the rib tips. It does
  not touch the ribs along their length, only at their tips.

Surface type:
  Multi-lobed saddle. Between the tips of adjacent ribs, the
  surface forms a saddle. Between the base rib tips (near
  the column) and the outer rib tips, the surface forms
  another saddle. The overall effect is a soft, multi-lobed
  canopy.

Reused from:
  The Cantilever Hypar provides the drawing method — corners,
  concave free edges, Coons-patch surface. But where Hypar
  has four corners, Leaf has as many corners as there are
  rib tips, and the surface is a multi-lobe patch rather
  than a single saddle.

Notes for the viewer:
  - Define every rib tip as a corner.
  - Draw free edges between adjacent rib tips. Each is a
    concave inward arc.
  - Build the surface as a multi-lobe Coons patch, or as a
    triangular mesh between the rib tips.
  - Draw cables along every free edge.
  - Draw the ribs and the spine as they are. They do not
    affect the membrane surface — the membrane only touches
    the rib tips.
  - The rib override feature (Adjust Rib Lengths) moves the
    rib tips. The membrane follows. This is already how the
    current viewer works. The rebuild keeps that behavior.
  - The current viewer attaches the membrane to the ribs all
    along their length (a skin). The rebuilt version attaches
    only at the tips.

Notes for the render prompt:
  Shape sentence:

    "Cantilever Leaf tensile membrane structure. A vertical
     column supports curved leaf-shaped fabric canopies
     radiating outward and upward, each canopy stretched
     between the tips of adjacent radial ribs and curving
     inward along its free edges."

  No numbers. No column height, no outreach.

---

### Cantilever Hypar

Family:
  Corner-based. Four corners.

Boundary conditions:
  A vertical column. A curved arm (the main beam) leaves the
  column at anchor_z and arcs upward to a free tip. Two ribs
  meet the arm's midpoint. The rib tips sit higher than the
  arm's midpoint. The membrane spans the four corners.

Free edges:
  All four. Each is a concave inward arc.

Attached edges:
  None. The membrane attaches only at the four corners.

Surface type:
  Saddle (hypar). The two arm ends are low; the two rib tips
  are high. Opposite corners match in height. The surface
  between them is a true saddle.

Reused from:
  This is the reference structure for the four-corner
  membrane-drawing method. The viewer already implements it.

Notes for the viewer:
  - Corners A, B, C, D:
      A = arm anchor end (low)
      C = arm free tip end (low)
      B = right rib tip (high)
      D = left rib tip (high)
  - Every pair of adjacent corners is joined by a concave
    inward free edge.
  - Cables follow the same concave curves as the fabric edges.
    One trace, one curve. No separate straight cable line.
  - The rib is one continuous arc through three points: left
    rib tip, arm midpoint, right rib tip. The arm's midpoint
    is the low point of the arc.
  - The membrane surface is a Coons patch between the four
    concave edges.
  - The rib curve radius and the membrane edge sag are both
    user inputs.

Notes for the render prompt:
  Shape sentence:

    "Cantilever Hypar tensile membrane structure. A curved
     arm cantilevered from the column, with two perpendicular
     ribs at its midpoint, holding a taut four-corner saddle
     fabric membrane whose edges curve inward under tension."

  No numbers.

---






---

# PART 5 — FUTURE STRUCTURES (reserved sections)

The following structures are not yet built. Their reserved
sections are listed here so that the family assignment is
already decided when we build them. Sections will be filled
in as each structure is built.

### Cantilever Cone
Family: expected corner-based, three or four corners.
Surface: saddle or partial cone.

### Cantilever Pyramid
Family: expected corner-based, four corners.
Surface: pyramid-like saddle.

### Cantilever Bell
Family: expected corner-based, many corners (around a rim).
Surface: bell-shaped concave surface.

### Cantilever Sail
Family: expected corner-based, three or four corners.
Surface: saddle.

### Cantilever Flower
Family: expected corner-based with multiple leaf lobes per
        unit. May combine with arrangement engine.

### Uni-Pole Single Cone
Family: expected loop-based.
Surface: cone between a mast and a ring.

### Uni-Pole Multi-Cone Cluster
Family: expected loop-based, multiple cones side by side.

### Uni-Pole Umbrella
Family: expected loop-based, mast with edge ring.

### Tensile Sail — 3 Anchors
Family: corner-based. Three corners.
Surface: triangular hypar.

### Tensile Sail — 4 Anchors
Family: corner-based. Four corners.
Surface: quad hypar.

### Multiple Wall-Anchored Sails
Family: edge-based. One edge attached to the wall.
Surface: saddle between the wall edge and the free edges.

### Multiple Column-Mounted Sails
Family: corner-based at column anchors plus free edges.

### Simple Frame + Fabric
Family: edge-based. Attached to a rigid frame all round.

### Arched Frame + Fabric
Family: edge-based. Attached to arches.

### Trussed Frame + Fabric
Family: edge-based. Attached to a truss.

### Wall-Mounted Shade
Family: edge-based. One edge attached to the wall.
Surface: saddle or single-curve.

### Cable-Supported Shade
Family: corner-based or mixed.

### Tree Canopy
Family: corner-based with many corners (branch tips).

### Pyramid Tent
Family: edge-based. Frame-defined boundary.

### Modular Tent
Family: edge-based. Modular frame units joined.

### Cone Tent
Family: loop-based. Central pole, edge ring.

### A-Frame Tent
Family: edge-based. Two sloped sides.

### Arch Tent
Family: edge-based. Curved arch frame.

### Simple Portal
Family: edge-based. Frame-defined boundary.

### With Mezzanine
Family: edge-based, same as Simple Portal.

### With Crane
Family: edge-based, same as Simple Portal.

### Multi-Bay Portal
Family: edge-based, multiple frames side by side.

---

# PART 6 — HOW THIS FILE IS USED

## 6.1 When starting a new structure

1. Read Part 1 (the principle).
2. Read Part 2 (the three boundary families).
3. Decide which family the new structure belongs to, or
   which combination of families.
4. Look up the closest existing structure's section in
   Part 4. Study how its membrane is drawn.
5. Write the new section for the new structure, using the
   template in Part 4.
6. Write the build spec at engine/SPEC_<structure>.md.
7. Build the viewer following Part 3's drawing rules for
   the structure's family.
8. Build the workshop. Wire the registration. Add the
   render prompt branch.
9. Test end to end.
10. Append the new section to Part 4 of this file.

## 6.2 When revising an existing structure

1. Open that structure's section in Part 4.
2. Compare what it says to what the viewer currently draws.
3. If the viewer does not match the principle, note the
   gaps.
4. Rebuild the viewer to match the family's drawing rules
   (Part 3).
5. Update the section in Part 4 with any new understanding.

## 6.3 When the FDM engine lands

1. Every placeholder in engine/PLACEHOLDERS.md is removed.
2. Every fixed sag fraction is replaced by the form-found
   equilibrium result.
3. This file's sections are updated: "placeholder value"
   becomes "FDM result".
4. The shape of every membrane in the app changes to the
   real form-found surface.

## 6.4 What this file does NOT do

  - It does not replace engine/PLACEHOLDERS.md. That file
    tracks inputs waiting for engines. This file tracks
    membrane behavior and drawing rules.
  - It does not replace engine/SPEC_<structure>.md files.
    Those describe what to build. This file describes how
    membranes behave.
  - It does not replace PROJECT_STATE.md or
    PROJECT_VISION.md. Those are project-level. This is
    membrane-level.

---

# APPENDIX C — CONSOLIDATION NOTES

This file consolidates and supersedes:

  - engine/PRINCIPLES_membrane.md
  - engine/UNDERSTANDING_cantilever_hypar.md

Both of those files were written earlier in the project. Their
content is now in Part 1 and Part 4 of this file, respectively
and expanded.

After this file is committed, the two older files should be
deleted. They are no longer the source of truth. Keeping them
risks a future reader opening the wrong document.

The deletion is a deliberate, single step: a small commit that
removes both files and leaves only MEMBRANE_GUIDE.md.

If at any point a reader is unsure which file is authoritative,
the answer is this file.

---

End of document.





