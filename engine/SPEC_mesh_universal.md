# SDSe — Universal Mesh Engine Specification

**Status:** DESIGN. Not yet executed.
**Last updated:** 2026-09-29.
**Related:** PROJECT_CONSTITUTION.md (Part III-B, Part V),
engine/SPEC_coordinate_file.md, engine/SPEC_dxf_import.md,
engine/SPEC_custom_boundary.md.

This document specifies the universal mesh engine for SDSe.
It builds a mesh from a closed boundary loop, divided into
segments, each segment classified as beam, cable, or wall.

The engine is universal. It knows no shapes. It knows
boundaries, segments, and types.

---

## 1. THE PRINCIPLE

The membrane boundary is a closed loop of anchors.

The loop is divided into segments by the anchors.

Each segment has a type:
    beam   — a beam. Fabric attached along the segment.
             All mesh nodes on this segment are held.
    cable  — a cable. Fabric attached only at the segment's
             endpoints (the anchors). The mesh nodes between
             the anchors are free. FDM solves them.
    wall   — a wall. Same mesh behaviour as beam. Recorded as
             a support, not a member, in the structural list.

The user decides the segment types. The recipe provides the
default. The engine reads the types and builds the mesh.

---

## 2. THE VOCABULARY

Fixed. No other words.

    boundary loop    — a closed sequence of 3D points.
    anchor           — a point on the boundary loop where two
                       segments meet. Always held.
    segment          — the gap between two consecutive anchors.
    segment type     — beam, cable, or wall.
    held             — a mesh node that solve_fdm does not move.
    released         — a mesh node that solve_fdm moves to
                       equilibrium.
    bow              — the inward curve of a released edge
                       under membrane tension. An equilibrium,
                       not a hack.

Words never used:
    free end, short end, long edge, free edge,
    column at support, degenerate column.

---

## 3. THE INPUT

    build_mesh_universal(
        boundary_loop,              # list of (x, y, z)
        segment_types,              # list of str, one per gap
        fill,                       # "tfi" | "polar" | "barycentric"
        subdivisions_per_segment,   # K, integer >= 1
        transverse_count,           # M, integer >= 2
        warp_q,                     # N/m, along the loop
        weft_q,                     # N/m, across the surface
        edge_q,                     # N/m, on cable segments
    )

**boundary_loop** — at least 3 points. Ordered. The last
point connects back to the first.

**segment_types** — one per gap. Length equals
len(boundary_loop) if the loop is closed. Each is "beam",
"cable", or "wall".

**fill** — the interior fill strategy. The recipe names it.
The engine does not detect it in v1.

**subdivisions_per_segment** (K) — how many extra mesh nodes
between consecutive anchors. Default 5.

**transverse_count** (M) — how many rows from the boundary
to the interior. For TFI and polar. Default 8.

**warp_q, weft_q, edge_q** — force densities in N/m.

---

## 4. THE OUTPUT

    {
        "points":      (n_nodes, 3) numpy array,
        "edges":       list of (i, j),
        "fixed_indices": list of int,
        "q":           (n_edges,) numpy array,
        "diagnostics": {
            "n_nodes": int,
            "n_edges": int,
            "n_fixed": int,
            "n_free": int,
            "fill_used": str,
            "segment_types": list of str,
            "n_anchors": int,
            "n_segments": int,
            "structural_connections": [],
        },
    }

The output is directly callable by solve_fdm:

    mesh = build_mesh_universal(...)
    res = solve_fdm(mesh["points"], mesh["edges"],
                    mesh["fixed_indices"], mesh["q"])

---

## 5. THE MESH TOPOLOGY

The mesh is a structured grid:

    i = 0 .. n_i - 1   along the boundary loop
    j = 0 .. n_j - 1   from the boundary inward

Where:

    n_i = number of mesh nodes around the boundary loop.
    n_j = transverse_count (M) for TFI and polar.
          For barycentric, n_j is derived from the loop's
          three sides.

**n_i is computed as:**

    n_i = sum over segments of K
        + number of anchors
        (with one anchor shared between consecutive segments
         in the closed loop)

Example: 14 anchors, 14 segments, K = 5.
    Each segment contributes K - 1 = 4 interior nodes.
    n_i = 14 anchors + 14 * 4 interior = 14 + 56 = 70.

**Total nodes:** n_i * n_j.

For 70 × 8 = 560 nodes.

---

## 6. THE HOLD RULE

Walk the boundary loop. For each mesh node:

    If the node is an anchor:
        Always held.

    If the node is on a segment's interior:
        If segment type is "beam": held.
        If segment type is "wall": held.
        If segment type is "cable": released.

    If the node is on the interior of the mesh
    (j not equal to 0):
        Always released.

That is the whole rule. No exceptions.

**The anchor is always held.** It is where two segments meet.
It cannot float. It is a structural connection.

---

## 7. THE Q ASSIGNMENT

For each edge in the mesh:

    Edge along the boundary loop direction:
        If the segment it belongs to is "cable": q = edge_q.
        Otherwise: q = warp_q.

    Edge across the surface (inward from the boundary):
        q = weft_q.

    Edge between two anchors on a cable segment:
        q = edge_q.

The rule is simple: cable edges get edge_q, other
boundary edges get warp_q, interior edges get weft_q.

---

## 8. THE INITIAL POSITIONS

**Boundary nodes (j = 0):**
    Lie exactly on the boundary loop. Anchors at anchor
    positions. Interior nodes interpolated linearly between
    the two anchors of their segment.

**Interior nodes (j >= 1):**
    Filled by the chosen fill strategy from the boundary
    inward.

**No sag hack.** No `z_init = bz - sag`. The initial
positions come from the geometry and the fill. FDM finds
the equilibrium.

This is the correction from the old viewer. The old viewer
applied a sag formula that pulled boundary nodes below the
ground. That caused the fold. The new engine does not sag.

---

## 9. THE FILL STRATEGIES

### 9.1 TFI (Transfinite Interpolation)

    For a quad-shaped loop. Two opposite sides are the "u"
    sides. The other two are the "v" sides. The interior
    is a bilinear blend.

    Use for: Standard Saddle, Beam Supported Saddle, wall
    with opposite cable edge, any four-sided-ish loop.

### 9.2 Polar

    For a ring-shaped loop. Every boundary node connects to
    a centre point, or to a chain of concentric rings.

    Use for: Crown, circle, morning glory, any roughly
    circular boundary.

### 9.3 Barycentric

    For a triangle-shaped loop. Three sides, three corners.
    Interior nodes are area-weighted blends of the three
    corners.

    Use for: Triangle, any three-sided shape.

### 9.4 Future — irregular

    For free-form DXF boundaries that are not quad, circle,
    or triangle. Medial axis fill or triangulated fill.

    Deferred to v2. Not in this engine yet.

---

## 10. THE RECIPE'S RESPONSIBILITY

The recipe declares:

    - The boundary loop (or how to build it).
    - The segment types.
    - The fill method.
    - The mesh density (K, M).

The recipe does not build the mesh. It hands the
declaration to the engine. The engine does the rest.

---

## 11. THE VIEWER'S RESPONSIBILITY

The viewer draws the solved mesh. It draws the beams as
lines or tubes. It draws the cables as lines. It draws the
walls as lines. It draws the supports as markers.

The viewer does not build the mesh. It reads the solved
coordinates from session state and draws them.

**The viewer is thin.** All the geometry comes from the
recipe and the engine.

---

## 12. WHAT THIS REPLACES

In the Standard Saddle viewer: the bespoke
_build_saddle_mbs function is deleted. The viewer builds
the boundary loop (14 anchors on the two beams), passes it
to the engine. The engine meshes. The viewer draws.

In the Standard Saddle recipe: the Shape group gains
segment-type inputs. Default is all beam. User can change
any segment.

In every future shape: the same pattern. Declare the
boundary. Declare the types. Call the engine. Draw the
result.

---

## 13. THE STRUCTURAL CONNECTION LIST

The engine returns an empty `structural_connections` list
today. It is a placeholder.

When Stage 3 (nonlinear FE) lands, the engine populates
this list from the segment types:

    beam segment: {"kind": "member", "type": "beam",
                   "connection": "pinned" | "rigid"}
    cable segment: {"kind": "member", "type": "cable",
                    "connection": "pinned"}
    wall segment: {"kind": "support", "type": "wall",
                   "connection": "pinned"}

The list is not read by solve_fdm. It is read by the future
structural solver.

Two lists. Two lifetimes. Part V of the constitution.

---

## 14. WHAT THIS UNLOCKS

**Standard Saddle.** Loop with 14 anchors (7 per beam).
Segment types: all beam by default. Fill: TFI.

**Beam Supported Saddle.** Same loop, more segments (for
secondary beams and purlins).

**Crown.** Loop around a circle. Fill: polar. Free centre.

**Triangle.** Loop with 3 anchors. Fill: barycentric.

**Lens.** Loop with a few anchors. Fill: TFI.

**Wall + cable.** Loop with wall anchors and cable anchors.
Fill: TFI.

**Custom boundary (DXF).** Loop from DXF. Fill: chosen by
the parser based on shape detection.

**Custom boundary (coordinate file).** Loop from CSV. Fill:
same.

**Morning glory.** Loop from CAD or description. Fill:
polar or TFI.

**One engine. Every shape.**

---

## 15. WHAT IS NOT IN THIS ENGINE

- Merged multi-lobe shapes (Crown-3Lobe). Bespoke.
- Irregular fill (medial axis, triangulated). v2.
- Beam flexibility. Stage 3.
- Load cases. Stage 3.
- Nonlinear iteration. Stage 3.

This engine is Stage 1. It is FDM. It is linear. It
solves in milliseconds. It is universal.

---

## 16. DOCUMENT HISTORY

Created: 2026-09-29.
  - Universal engine specified.
  - Three fill methods: TFI, polar, barycentric.
  - Segment-based hold rule.
  - No sag hack. No free-end vocabulary.
  - Structural connections list reserved for Stage 3.
  - Status: DESIGN. NOT EXECUTED.
