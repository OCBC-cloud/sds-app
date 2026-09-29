# SDSe — Mesh From Segments Specification

**Status:** DESIGN. Not yet executed.
**Last updated:** 2026-09-29.
**Related:** engine/SPEC_coordinate_file.md,
engine/SPEC_dxf_import.md, engine/SPEC_custom_boundary.md,
PROJECT_CONSTITUTION.md (Part III-B, Part V).

This document specifies the universal mesh engine for SDSe.
It is the engine that builds a mesh from anchor coordinates
and segment classifications. It replaces the four-sided TFI
path of engine/membrane_boundary.py for all shapes with a
clear boundary loop.

---

## 1. WHY A NEW ENGINE

Today, engine/membrane_boundary.py builds meshes via
_boundary_as_four_sides and TFI. It assumes four sides. It
works for shapes that happen to be four-sided after corner
detection: Lens, Triangle, Crown, Prototype-Lobe.

The Crown-3Lobe bypasses this. It builds its nodes, edges,
fixed_indices explicitly. It calls solve_fdm directly.

The Standard Saddle fails with the four-sided path. Its
free-end cable interiors need to be free. The four-sided
engine has no rule for that.

The new engine generalises the Crown-3Lobe pattern:

    - Any number of anchors. Not four.
    - Any number of segments. Not four.
    - Per-segment classification: beam, cable, or wall.
    - Per-segment hold rule:
        beam  → hold all mesh nodes on this segment.
        cable → hold only the two endpoint anchors.
        wall  → hold all mesh nodes on this segment
                (same behaviour as beam).
    - Anchors are always held (structural).
    - Interior of the membrane is always free.

This is the professional standard. It matches how ixCube
and similar tools handle mixed beam/cable boundaries.

---

## 2. THE TWO LISTS (Part V DOCTRINE)

Two separate lists. Two meanings. Two lifetimes.

**List 1 — Mesh constraints.**
Which mesh nodes solve_fdm holds. Derived from segment
types. Beam and wall segments hold all their nodes. Cable
segments hold only their anchors.

**List 2 — Structural connections.**
How the real structure attaches: pinned or rigid. Which
member is a beam, which is a cable, which is a wall
support. Not read by solve_fdm today. Populated in
Stage 3.

The engine returns both. The viewer draws the mesh. The
future structural solver reads the second list.

---

## 3. THE INPUT

The engine accepts two loops, mesh density, and force
densities.






