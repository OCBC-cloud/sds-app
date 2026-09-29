# SDSe — Custom Boundary Structure Specification

**Status:** DESIGN. Not yet executed.
**Last updated:** 2026-09-29.
**Related:** engine/SPEC_dxf_import.md, UI_ARCHITECTURE.md,
SUBSTRUCTURES.md, PROJECT_VISION.md.

This document specifies the `custom_boundary` structure — the
SDSe structure type that uses a user-drawn DXF boundary instead
of a fixed template shape.

It is the bridge between the CAD drawing and the MBS engine.
The user draws any shape. The app form-finds the membrane
inside it. The structure type is the same. Only the boundary
source differs.

---

## 1. PURPOSE

Every SDSe structure today is a template. Standard Saddle,
Beam Supported Saddle, Cantilever Leaf, Cantilever Hypar,
Crown-3Lobe. Each has a fixed geometric family. The user picks
and tunes parameters.

`custom_boundary` breaks that. The user draws the boundary in
a CAD tool. SDSe reads it. The MBS engine form-finds the
membrane. The user's shape is solved as it was drawn.

The result is a design engine, not a template picker.

---

## 2. WHAT THE USER DOES

1. Opens their CAD tool — AutoCAD, Rhino, SketchUp, FreeCAD,
   BricsCAD, anything that exports DXF.
2. Draws the boundary of the membrane structure they want.
3. Puts the boundary on a layer named `SDSe_BOUNDARY_01`.
4. Optionally adds: column position on `SDSe_COLUMN_01`, wall
   line on `SDSe_WALL_01`, cable line on `SDSe_CABLE_01`,
   anchor point on `SDSe_ANCHOR_01`.
5. Exports DXF. Keeps the file under 1 MB. Purges everything
   not on an `SDSe_*` layer.
6. Uploads the DXF to the app.
7. Declares units, rise (if flat), column height.
8. Marks each boundary segment as beam, cable, or wall — or
   accepts the default.
9. Fills the rest of the workshop — membrane, frame, cables,
   foundation, loads.
10. Runs the form-finding.
11. Sees the 3D result.
12. Prepares the render prompt and the BoQ.

Steps 1–5 happen outside the app. The user works in CAD.
Steps 6–12 happen inside the app. The user works in SDSe.

---

## 3. HOW IT APPEARS IN THE STUDIO

The Studio page today shows 8 structure types:

    Saddle Span
    Cantilever
    Uni-Pole Tensile Roof
    Tensile Sails Roof
    Framed Tensile Roof
    Canopy
    Frame Tent
    Portal Frame

A 9th tile is added:

    Custom Boundary

Icon: a small outline shape.
Description: "Draw your own boundary in CAD. Upload the DXF.
SDSe form-finds the membrane."

On tap: goes to Registration. Registration asks for project
info as usual. Then the user selects the "Custom Boundary"
variant — there is only one.

On arriving at the Workshop: the Shape group opens with the
DXF upload widget at the top.

---

## 4. THE WORKSHOP

The `custom_boundary` workshop is a recipe, like all others.
Six substructure groups.

### 4.1 Shape

The Shape group is different from other structures. It has:

    DXF File              [ upload widget ]
    Units                 [ mm / cm / m / in / ft ]
    Rise (m)              [ number, only if boundary is flat ]
    Boundary type         [ cable-supported / beam-supported /
                            mixed ]
    Resample N            [ integer, default 7, segments per edge ]

After upload, a preview box shows:

    Boundary read: 128 vertices.
    Corners detected: 4.
    Bounding box: 10.2 m × 15.0 m × 0.0 m.
    Layers found: SDSe_BOUNDARY_01, SDSe_COLUMN_01.

If corners are detected, a small block follows:

    Segment 1 (Corner 1 to Corner 2):
        [ beam / cable / wall ]
    Segment 2 (Corner 2 to Corner 3):
        [ beam / cable / wall ]
    ...

Defaults: all segments cable. Corners are anchors.

### 4.2 Membrane

Same as every other structure:
Fabric type, Fabric grade, Attachment method, Pretension.

### 4.3 Frame

Same as every other structure:
Steel grade, Section family, Member construction, Supports.

But there is one extra: the columns read from the DXF.

    Columns found in DXF: 2
    Column 1: (x, y) — height 6.0 m
    Column 2: (x, y) — height 6.0 m

Each column is a mast or post. The user can adjust the column
height per column. Column section is auto or manual.

### 4.4 Cables

Same as every other structure:
Tie-down count, angles, cable type, material, pretension.

Plus: the cable anchor lines read from the DXF.

    Cable lines found: 2
    Line 1: 4.0 m length
    Line 2: 4.0 m length

### 4.5 Foundation

Same as every other structure:
Soil bearing, water table, soil type, foundation type.

Plus: the ground anchor points read from the DXF. Each anchor
point gets its own foundation entry.

### 4.6 Loads

Same as every other structure:
Additional payload, design standard.

---

## 5. THE SHAPE RECIPE

The `custom_boundary` shape recipe is a function with the
standard signature:

    def build_shape(params):
        # reads the DXF boundary from params
        # returns (grid, boundary, anchors, edge_types)

Unlike other structures, the boundary does not come from a
formula. It comes from the file. The recipe reads the parsed
DXF from session state and hands the boundary to the MBS
engine.

The MBS engine does the rest. It builds the mesh from the
boundary. It solves it. It returns the coordinates.

No special engine. No special code. The recipe is the only
new part. The engine is universal.

---

## 6. THE VIEWER

The viewer for `custom_boundary`:

- Draws the membrane as a triangulated mesh of solved
  coordinates. Same as every other viewer.
- Draws the columns as vertical lines from their DXF positions.
- Draws the walls as lines on the boundary.
- Draws the cable anchor lines.
- Draws the anchors as small markers.
- Draws the tie-down cables if configured.

Everything is placed in 3D as read from the DXF, scaled by the
declared units.

The viewer does not know what shape the user drew. It only
knows the boundary the recipe returns. Same universality as
the MBS engine.

---

## 7. THE RENDER PROMPT

The `custom_boundary` render prompt recipe reads the shape
parameters and produces a text description. Since we cannot
know what the user drew, the prompt is generic:

    A tensile membrane canopy structure with an irregular
    boundary, spanning approximately X m × Y m, at a height
    of Z m, supported by N columns.

The user can edit the prompt before sending it to the renderer.
Or they can paste their own prompt.

This is the one place where custom boundary is weaker than a
template structure — we cannot auto-describe the shape. The
user supplies the words.

---

## 8. THE BOQ

The BoQ for `custom_boundary` reads the same as every other
structure:

- Steel: by member, length, mass. Columns and frame members
  from the DXF positions and the workshop inputs.
- Cable: length, fitting type. From the DXF cable lines.
- Fabric: flattened area, seam length, edge length. From the
  solved mesh.
- Hardware: clamps, cleats, kader, anchors.

The DXF positions drive the geometric quantities. The
workshop inputs drive the material selections.

---

## 9. THE TIER GATING

Like every structure, the `custom_boundary` workshop respects
the tier exposure rules from TIERS.md:

    Category     | Owner  | Beta   | Studio | Pro    | Free
    -------------|--------|--------|--------|--------|-------
    Shape        | Edit   | Edit   | Edit   | Edit   | Read
    Membrane     | Edit   | Edit   | Edit   | Edit   | Read
    Frame        | Edit   | Edit   | Edit   | Edit   | Hide
    Cables       | Edit   | Edit   | Edit   | Edit   | Hide
    Foundation   | Edit   | Edit   | Edit   | Read   | Hide
    Loads        | Edit   | Edit   | Read   | Hide   | Hide

A Free user can upload the DXF and see the result, but cannot
edit the frame, cables, foundation, or loads.

A Pro user can edit everything except loads.

A Studio user can edit everything.

This is the same pattern as every other structure.

---

## 10. WHAT IS NEEDED TO BUILD IT

Files to create:

    engine/dxf_parser.py          — the DXF reader
    ui/workshops/custom_boundary.py — thin wrapper, calls renderer
    data/recipes/custom_boundary.py — the workshop recipe
    viewers/figures/custom_boundary.py — the 3D viewer
    engine/recipes/custom_boundary_shape.py — the shape recipe

Files to change:

    data/structures.py            — add the new structure type
    ui/studio.py                  — add the Studio tile
    requirements.txt              — add ezdxf
    core/navigation.py            — add the route if needed

Effort estimate: 4 to 6 sessions.

Breakdown:
    1 session  — dxf_parser.py. Read, filter, extract, validate.
    1 session  — custom_boundary_shape.py. Boundary cleaning,
                 resampling, corner detection, MBS handoff.
    1 session  — the workshop recipe and file wiring.
    1-2 sessions — the viewer.
    1 session  — end-to-end testing with a real DXF.

---

## 11. WHAT IS NOT IN SCOPE (v1)

- Multiple membranes from one DXF beyond 3 boundaries.
- Shared-edge coupling between boundaries.
- Load regions from DXF.
- Non-DXF formats (DWG, IFC, STEP).
- 3D solids or surfaces as boundaries.
- Automatic edge classification beyond corner detection.

These are recorded for Tier 2.

---

## 12. THE OUTCOME

The app is no longer a template picker.

The user can draw any shape and solve it. A morning glory. A
stadium ring. A market canopy. A modular factory roof. A
custom logo-shaped shade structure. Anything the user can draw
in CAD is a membrane the app can form-find.

The CAD tool does the drawing. SDSe does the physics. The
fabricator does the detailing.

Three links. One chain. The design studio is complete.

---

## 13. DOCUMENT HISTORY

Created: 2026-09-29.
  - Structure type defined: custom_boundary.
  - Workshop recipe specified: six groups, DXF upload in Shape.
  - Shape recipe signature: same as every other structure.
  - Viewer specified: DXF positions drive geometry.
  - Tier gating inherits the standard pattern.
  - Build effort estimated: 4-6 sessions.
  - Status: DESIGN. NOT EXECUTED.




