# SPEC — Cantilever Hypar

Status: designed, not built.
Date: 2026-09-21.
Related: SPEC_cantilever_leaf.md (if exists), engine/render_prompts.py.

---

## 1. Summary

Cantilever Hypar is a sibling of Cantilever Leaf.

Same column. Same five arrangement modes. Same tiering logic.
Different mother object: an asymmetric four-cornered saddle canopy
cantilevered out sideways from the column.

The arrangement logic reuses Cantilever Leaf exactly. Only the
geometry of the mother object changes.

---

## 2. Mother object geometry

A single Cantilever Hypar canopy, in words:

- One vertical column, at one end of the structure (not central).
- One main arc arm. One end anchors to the column at approximately
  2/3 of column height. The other end reaches out and is free.
  This free end defines the reach of the canopy.
- One diagonal strut. Runs from the top of the column down and
  outward to meet the anchored end of the arm at the 2/3 point.
  It triangulates the arm into the column so the column is not
  twisted by cantilever moment.
- Two perpendicular bent ribs. Branch off at the exact midpoint
  of the main arm, one left and one right, perpendicular to the
  arm. Their tips are the outer roof corners.
- One saddle membrane. A taut four-cornered hypar sheet spanning:
    the anchored end of the arm,
    the free end of the arm,
    the left rib tip,
    the right rib tip.
- Edge cables. Run along the four edges of the membrane. They
  are pulled inward by the saddle curvature and terminate at the
  four structural corners above.

Load path, in one line:
  membrane tension -> edges -> cables -> arm + rib tips ->
  arm -> column at 2/3 height -> column top strut triangulates ->
  column -> baseplate -> ground.

---

## 3. Parameters (proposed)

Same interface shape as Cantilever Leaf. Reuses column height,
outreach (here: the arm reach), and rib concept. New parameters
needed for the mother object:

- Column height (m)                  - reused from Leaf
- Arm reach (m)                      - new (was Leaf's "outreach")
- Arm anchor height (m or fraction)  - new, default 2/3 of column
- Rib length (m)                     - new, radius of the two
                                        perpendicular bent ribs
- Rib tilt angle (deg)               - reused from Leaf concept
- Column radius (m)                  - reused from Leaf
- Membrane pretension (kN/m)         - reused from Leaf

The arm arc radius is a derived quantity from reach and anchor
height, or user-set. Decide at build time.

---

## 4. Arrangement modes (identical to Cantilever Leaf)

- single      - one hypar on the column
- double      - two mirrored hypars
- multiple    - N hypars around the column (radial)
- tree_stack  - hypars stacked in tiers, scale factor 0.75
- tiered_helix - hypars spiralling up the column

The five modes are implemented by the arrangement code already
present in Cantilever Leaf. No new arrangement logic required.
The Hypar workshop will call the same arrangement functions and
supply a different mother-object geometry to the viewer.

---

## 5. Viewer requirements

The 3D viewer for one hypar mother object:

- Column (green cylinder)
- Baseplate (green block at column base)
- Diagonal strut from column top to anchor point (orange line)
- Main arc arm (red curve)
- Two perpendicular bent ribs (red curves, or a distinct colour
  to separate them from the arm)
- Saddle membrane (blue semi-transparent surface across the
  four corners)
- Edge cables (dashed lines along the four membrane edges,
  yellow by convention, matching saddle-span convention)
- Column joint marker (yellow sphere) at the anchor point on
  the column

The viewer will follow the same pattern as cantilever_leaf.py:
read parameters from session state, draw the mother object,
then let the arrangement layer multiply / stack / helix.

---

## 6. Render description (for engine/render_prompts.py)

One clean shape sentence, live from params, in the same style
as the other variants. Draft:

  "Cantilever Hypar tensile membrane structure. One curved arc
   arm cantilevered from a column at [anchor height] m, with two
   perpendicular ribs at its midpoint, holding a taut four-corner
   saddle fabric membrane pulled inward by edge cables."

No numbers on the membrane. Only the anchor height and reach,
matching the style of the Leaf and Saddle prompts.

---

## 7. What is reused from Cantilever Leaf, exactly

Reuse without change:

- The whole Arrangement section (Section 9) logic.
- Tier scale factor 0.75 (tree_stack).
- Helix turns computation (tiered_helix).
- The viewer strings block pattern (description + dimensions,
  read widget keys first).
- The workshop CSS, helpers, and box functions.
- The results page integration (nothing to change).
- The render prompt engine structure (add one branch in
  _describe_structure).

Change, specifically for Hypar:

- The mother-object geometry drawer in viewers/figures/.
- The shape sentence in engine/render_prompts.py
  (_describe_cantilever_hypar).
- The section names and labels inside the workshop.

---

## 8. What is NOT in this spec

- Exact mathematics of the saddle membrane form-finding.
  That is part of the FDM engine, pending.
- Structural analysis of the arm and column. Pending.
- Member sizing. Pending.
- The exact wording of every numeric default. Propose at build.

---

## 9. Build order (suggested)

1. Decide the exact viewer geometry of one hypar mother object.
   Prototype it in viewers/figures/cantilever_hypar.py.
2. Create ui/workshops/saddle_hypar.py, mirroring saddle_leaf.py.
   Replace mother-object parameters. Reuse arrangement.
3. Add Cantilever Hypar to the registration page's structure
   list, alongside Cantilever Leaf.
4. Add the shape sentence to engine/render_prompts.py.
5. Test all five arrangements in the viewer and in the renderer.

---

End of spec.
