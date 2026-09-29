# SDSe — DXF Import Specification

**Status:** DESIGN. Not yet executed.
**Last updated:** 2026-09-29.
**Related:** PROJECT_VISION.md (Stage 3), UI_ARCHITECTURE.md,
SUBSTRUCTURES.md, engine/SPEC_custom_boundary.md.

This document specifies how SDSe reads a DXF file for a user-drawn
membrane boundary. It is the contract between the CAD drawing and
the MBS engine.

The purpose: let the user draw any shape in a CAD tool they already
know. SDSe reads the boundary. The MBS engine form-finds the
membrane inside it. No canvas drawing tool inside SDSe.

---

## 1. THE PRINCIPLE

The user draws. The app solves.

CAD tools — AutoCAD, Rhino, SketchUp, FreeCAD, BricsCAD — are
mature. They already know how to draw. SDSe does not compete with
them. SDSe is the next link in the chain:

    CAD tool draws the boundary
        → SDSe form-finds the membrane
            → Fabricator details the structure

This is the same first-half / second-half doctrine as
PROJECT_VISION.md. The CAD tool is a new link at the front.

---

## 2. WHAT WE ACCEPT

**Format:** DXF only. Both ASCII and binary.

**File size:** 1 MB maximum. Hard limit.

**Units:** declared by the user at upload time.
Options: mm, cm, m, inches, feet.
The app scales to metres before solving.

**Layers:** only layers whose name starts with `SDSe_` are read.
Every other layer is ignored, at the layer-table level, before
any entity is parsed.

**Entities per layer:** one entity per layer.
- Boundary layers: one closed polyline.
- Column layers: one point or one short vertical line.
- Wall layers: one polyline (open or closed).
- Cable layers: one polyline (open).
- Anchor layers: one point.

Additional entities on the same layer are ignored.

---

## 3. THE LAYER NAMING CONVENTION

All SDSe layers use the prefix `SDSe_`. Lowercase is not accepted.
The suffix is a two-digit number starting from `01`.

    SDSe_BOUNDARY_01     Membrane boundary 1
    SDSe_BOUNDARY_02     Membrane boundary 2
    SDSe_BOUNDARY_03     Membrane boundary 3

    SDSe_COLUMN_01       Column position 1
    SDSe_COLUMN_02       Column position 2
    SDSe_COLUMN_03       Column position 3

    SDSe_WALL_01         Wall boundary 1
    SDSe_WALL_02         Wall boundary 2
    SDSe_WALL_03         Wall boundary 3

    SDSe_CABLE_01        Cable anchor line 1
    SDSe_CABLE_02        Cable anchor line 2
    SDSe_CABLE_03        Cable anchor line 3

    SDSe_ANCHOR_01       Ground anchor point 1
    SDSe_ANCHOR_02       Ground anchor point 2
    SDSe_ANCHOR_03       Ground anchor point 3

Maximum counts:
    Boundaries: 3.   (The PE designs the typical bay. Not 20 bays.)
    Columns:    3.
    Walls:      3.
    Cables:     3.
    Anchors:    3.

Any layer not matching this pattern is not read.

---

## 4. THE BAY LIMIT

Maximum 3 `SDSe_BOUNDARY_*` layers.

Reason: a PE designs the typical bay and applies the result to
the whole building. This is standard practice for modular
structures. Three bays is enough to cover typical, corner, and
end conditions.

The user is told this on the upload screen. If the real building
has 20 bays, they draw 3. The report notes: "Typical bays
verified. Applied to N bays at the engineer's judgement."

---

## 5. THE BOUNDARY POLYLINE

The `SDSe_BOUNDARY_*` layer must contain exactly one closed
polyline. The polyline defines the membrane boundary loop.

**Format accepted:**
- `LWPOLYLINE` (lightweight polyline). Most common.
- `POLYLINE` (older heavy form). Accepted for compatibility.

**Shape:**
- Closed. The first and last vertices coincide, or the closed
  flag is set. If open, the app closes it and warns the user.
- 2D or 3D. If all z equal → the boundary is treated as flat
  and the app lifts it by the "rise" input from the workshop.
  If z varies → the boundary is treated as 3D and solved in
  place.

**Vertex count:**
- Minimum: 4. Fewer than 4 cannot form a closed region.
- Maximum: 5,000. More than that is not a boundary — it is a
  survey. The user should simplify the polyline.

**Direction:** not important. The app does not care whether the
polyline is drawn clockwise or counter-clockwise.

---

## 6. THE OTHER LAYERS

**`SDSe_COLUMN_*`** — the column position.
One point, or one short vertical line. If a point: the column
rises straight up from that point. If a line: the line is the
column axis.

**`SDSe_WALL_*`** — a wall boundary. One polyline.
The membrane attaches to the wall along this line. The wall is
held in the mesh — no cable bow. A wall is functionally a beam
for mesh purposes, but is labelled "wall" in the diagnostic so
the eventual PE knows it is a support, not a member.

**`SDSe_CABLE_*`** — a cable anchor line. One polyline.
Where an edge cable or tie-down anchors. Not the cable itself —
the line the cable attaches to.

**`SDSe_ANCHOR_*`** — a ground anchor. One point.
Where a tie-down cable terminates at the ground.

---

## 7. WHAT WE REJECT

The app refuses the file, with a clear message, if:

- File size > 1 MB.
- No layer matches `SDSe_*`.
- No `SDSe_BOUNDARY_*` layer exists.
- A `SDSe_BOUNDARY_*` layer contains no closed polyline.
- A `SDSe_BOUNDARY_*` layer contains more than one polyline.
- A boundary polyline has fewer than 4 vertices.
- More than 3 `SDSe_BOUNDARY_*` layers exist.
- The user does not declare units.

The rejection message names the specific problem. No generic
"invalid file" errors.

---

## 8. WHAT WE IGNORE

- Any layer not starting with `SDSe_`.
- Any entity on an `SDSe_*` layer that is not the primary entity
  for that layer type.
- Hatches, text, dimensions, blocks, inserts, viewports,
  viewport layouts, paperspace, model-space extras.
- Anything in the DXF header beyond the layer table.

We read the layer table first. If no `SDSe_*` layer exists, we
stop immediately — we do not scan the rest of the file.

---

## 9. THE PARSER

Library: `ezdxf`. Well-known. Mature. Pure Python. Add to
`requirements.txt`.

The parser flow:

    1. Read file bytes. Check size < 1 MB.
    2. Open with ezdxf. Do not explode blocks.
    3. Read the layer table. Collect layers starting with
       "SDSe_".
    4. If none, error: "No SDSe_ layers found."
    5. If no SDSe_BOUNDARY_*, error: "No boundary layer found."
    6. For each SDSe_ layer, extract the primary entity.
    7. For each boundary, extract the vertex list. Close if
       needed. Resample to N points per edge.
    8. Scale by user-declared units.
    9. Detect corners (sharp direction changes).
    10. Present a small UI: mark each segment as beam or cable.
        Defaults: corners are anchors. Segments between corners
        default to cable.
    11. Hand the boundary to the MBS engine.

The parser never crashes on a malformed file. It returns a clear
error message.

---

## 10. THE UI AT UPLOAD TIME

A small upload block. Five fields:

    DXF File          [ upload widget ]
    Units             [ mm / cm / m / in / ft ]
    Rise (m)          [ number, only if boundary is flat ]
    Column height (m) [ number ]
    Boundary type     [ cable-supported / beam-supported /
                        mixed ]

After upload, a preview box shows:

    Boundary read: 128 vertices.
    Corners detected: 4.
    Bounding box: 10.2 m × 15.0 m × 0.0 m.
    Layers found: SDSe_BOUNDARY_01, SDSe_COLUMN_01.

The user can then mark segments as beam or cable if they wish.
The default is cable for all segments, anchors at corners.

---

## 11. TIER 2 — LATER

The v1 above handles one closed boundary on each layer, up to 3
boundaries total.

A later revision adds:

- Shared-edge detection: if two boundaries touch along a chain
  of vertices, they are merged into one continuous membrane or
  coupled as two panels with a shared ridge.
- Column-to-boundary association: a column inside a boundary is
  automatically linked to that boundary's membrane.
- Load region layers: `SDSe_LOAD_01`, etc. Regions where a
  specific load applies (snow pocket, water ponding zone).

Not in v1. Recorded here so the design is not lost.

---

## 12. WHAT THIS UNLOCKS

Every shape. Not a template picker. A design engine.

- A morning glory canopy drawn in Rhino.
- A stadium roof traced from an architect's site plan.
- A market canopy from a client's Pinterest board.
- A ferry terminal from a photo of a similar project.
- A modular factory roof — 3 typical bays, applied to 20.

The user already has CAD. We accept its output. We solve.
We report. The PE signs.

This is the shortest path from a template app to a design engine.
It does not require building a canvas tool. It requires reading
a file.

---

## 13. DOCUMENT HISTORY

Created: 2026-09-29.
  - Layer naming convention: SDSe_* with two-digit suffix.
  - File size limit: 1 MB.
  - Bay limit: 3 boundaries.
  - Wall boundaries: held like beams, labelled "wall".
  - Parser flow documented.
  - Tier 2 plan recorded.
  - Status: DESIGN. NOT EXECUTED.




