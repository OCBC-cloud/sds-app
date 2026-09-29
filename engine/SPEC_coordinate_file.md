# SDSe — Coordinate File Specification

**Status:** DESIGN. Not yet executed.
**Last updated:** 2026-09-29.
**Related:** engine/SPEC_dxf_import.md, engine/SPEC_custom_boundary.md,
engine/SPEC_mesh_from_segments.md.

This document specifies how SDSe reads a plain coordinate file —
a list of anchor points typed or pasted by the user — as an
alternative to a DXF.

The purpose: let the user provide exact 3D anchor coordinates
without needing a CAD tool. A PE with a PDF and a ruler types
11 coordinates in five minutes. The engine meshes.

---

## 1. THE PRINCIPLE

Three input paths to the same engine:

    Path 1 — Template shapes. Picked from a menu.
    Path 2 — DXF file. Drawn in CAD, exported, uploaded.
    Path 3 — Coordinate file. Typed or pasted as text.

All three produce the same thing: a list of anchor
coordinates and segment types. The engine does not know
which path was used.

---

## 2. THE FILE FORMAT

Plain CSV. Comma-separated. One anchor per row.

    x, y, z, segment_type

Columns:
    x              — X coordinate (number)
    y              — Y coordinate (number)
    z              — Z coordinate (number)
    segment_type   — "beam" | "cable" | "wall"

The segment_type on a row describes the segment FROM this
anchor TO the next anchor in the file.

The last row's segment_type is ignored for an open loop.
For a closed loop, it describes the segment from the last
anchor back to the first.

Example — 11 wall anchors:

    x, y, z, segment_type
    0.0, 0.0, 3.2, wall
    2.5, 0.0, 4.1, wall
    5.0, 0.0, 4.8, wall
    7.5, 0.0, 5.2, wall
    10.0, 0.0, 4.8, wall
    12.5, 0.0, 4.1, wall
    15.0, 0.0, 3.2, wall
    17.5, 0.0, 2.0, wall
    20.0, 0.0, 0.8, wall
    22.5, 0.0, 0.2, wall
    25.0, 0.0, 0.0, wall

Example — mixed beam and cable loop:

    x, y, z, segment_type
    0.0, 0.0, 0.0, beam
    10.0, 0.0, 6.0, beam
    10.0, 15.0, 0.0, cable
    0.0, 15.0, 0.0, cable

---

## 3. THE HEADER LINE

The header is optional.

If the first row starts with a non-numeric character (like
"x" or "#"), it is treated as a header and skipped.

If the first row starts with a number, it is treated as the
first anchor.

Comments starting with "#" are ignored everywhere.

---

## 4. THE TWO LOOPS

A membrane has two boundary loops:
    LOOP_A — the primary boundary.
    LOOP_B — the opposite boundary.

Each loop is a separate file, or a separate section in one
file.

**Two files.** Upload LOOP_A and LOOP_B separately in the
workshop. Simplest. Recommended.

**One file, two sections.** A separator line begins LOOP_B:

    # LOOP_A
    0.0, 0.0, 3.2, wall
    ...

    # LOOP_B
    0.0, 10.0, 0.0, cable
    ...

For v1, two separate files. Simpler to parse.

---

## 5. THE UNITS

Declared by the user at upload time, not in the file.

Options: mm, cm, m, inches, feet.
The app scales to metres before solving.

This matches the DXF import path. Same dropdown, same
options, same scaling.

---

## 6. THE MESH DENSITY

Declared by the user at upload time, not in the file.

    subdivisions_per_segment (K) — extra mesh nodes per segment.
    transverse_count (M) — mesh rows between the two loops.

Defaults: K = 5, M = 8.

These match the Tester's density inputs. Same meaning, same
range.

---

## 7. WHAT WE ACCEPT

**File size:** 100 KB maximum. A coordinate file is small.
If it is bigger than 100 KB, something is wrong.

**Rows:** between 2 and 500 anchors per loop.

**Format:** plain text. ASCII or UTF-8. Comma or whitespace
separated. Both work.

**Headers:** optional.

**Comments:** lines starting with `#` are ignored.

---

## 8. WHAT WE REJECT

The app refuses the file, with a clear message, if:

- File size > 100 KB.
- Fewer than 2 anchors in a loop.
- More than 500 anchors in a loop.
- A row has fewer than 3 numeric columns.
- A row has non-numeric x, y, or z.
- A segment_type is not "beam", "cable", or "wall".

The rejection message names the specific row and column.

---

## 9. HOW IT APPEARS IN THE APP

The `custom_boundary` workshop has a Shape group. At the top
of that group, a radio button:

    Input method:
        ( ) Upload DXF
        ( ) Upload coordinate file
        ( ) Draw in app (later)

For "Upload coordinate file", the Shape group shows:

    LOOP_A file        [ upload widget ]
    LOOP_B file        [ upload widget ]
    Units              [ mm / cm / m / in / ft ]
    Subdivisions (K)   [ integer, default 5 ]
    Transverse count (M) [ integer, default 8 ]

After upload, a preview box shows:

    LOOP_A read: 11 anchors, 10 wall segments.
    LOOP_B read:  8 anchors,  8 cable segments.
    Bounding box: 25.0 m × 15.0 m × 5.2 m.

Then the workshop continues as normal — membrane, frame,
cables, foundation, loads.

---

## 10. WHY THIS IS THE RIGHT FIRST STEP

DXF requires:
    - The user to have a CAD tool.
    - The user to know how to export DXF.
    - The user to know how to purge layers and put the
      boundary on `SDSe_BOUNDARY_01`.
    - A parser that handles `LWPOLYLINE`, `POLYLINE`, units,
      layer tables.

The coordinate file requires:
    - The user to have any text editor.
    - The user to type or paste numbers.
    - A parser that reads CSV.

**The coordinate file is a tenth the work. And it serves the
same user need:** exact anchor coordinates from a survey or
a drawing.

Build the coordinate file first. Then DXF. Both feed the
same engine.

---

## 11. WHAT THIS UNLOCKS

The wall-anchor scenario, immediately:

A building with 11 anchor points on one wall. The membrane
attaches to the wall. The other edge is a cable.

The user types 11 coordinates for the wall. 8 coordinates
for the cable edge. Uploads both. Chooses units. Runs.

The engine meshes. FDM solves. The membrane bows inward
along the cable edge. The wall edge stays flat.

**This is a real engineering deliverable in the app.** No CAD
license. No drawing. No DXF.

---

## 12. DOCUMENT HISTORY

Created: 2026-09-29.
  - Coordinate file format: plain CSV, four columns.
  - Two loops: LOOP_A and LOOP_B. Separate files.
  - Units declared at upload.
  - Mesh density declared at upload.
  - Validation rules documented.
  - Build order: coordinate file before DXF.
  - Status: DESIGN. NOT EXECUTED.




