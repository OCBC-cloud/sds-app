# SPEC — Cantilever Hypar

Status: designed, not built.
Date: 2026-09-21.
Related: engine/PRINCIPLES_membrane.md, engine/PLACEHOLDERS.md.

PLACEHOLDER INPUTS: see engine/PLACEHOLDERS.md.

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
  Straight, no curvature. Thickness is a placeholder (see §9).

- One main arc arm. One end anchors to the column at approximately
  2/3 of column height (parameter: anchor height fraction, default
  0.65). The arm arcs UPWARD in the middle. Both ends of the arm
  — the anchor end and the free tip end — sit at the SAME height.
  The tip is out horizontally at the arm reach distance.

- One diagonal strut. Runs from the column top down and outward
  toward the arm. It crosses the arm at the structural anchor
  point. That crossing point is computed by geometry, not fixed.

- Two perpendicular bent ribs. Attach at the exact midpoint of
  the main arm (the highest point of the arm's arc). One rib to
  the left, one to the right, perpendicular to the arm. Each rib
  arcs UPWARD: both rib tips are HIGHER than the rib anchor on
  the beam. Seen from the side, the two rib tips and the rib
  anchor form a symmetric arc with the anchor at its middle
  (lowest point of the rib arc).

- One saddle membrane. A taut four-cornered hypar sheet spanning:
    the anchored end of the arm (lower),
    the free end of the arm (lower, same height as anchor),
    the left rib tip (higher),
    the right rib tip (higher).
  Opposite corners match in height. This is a true hypar.

- Edge cables. Run along the four edges of the membrane. They
  are concave inward toward the membrane centre (per
  PRINCIPLES_membrane.md). Magnitude is a placeholder (10–15%
  of edge length) until the FDM engine lands.

Load path, in one line:
  membrane tension -> edges -> cables -> arm + rib tips ->
  arm -> column at the anchor point -> strut triangulates ->
  column -> baseplate -> ground.

---

## 3. Parameters

Real user inputs (kept):

- Column height (m)
- Arm reach (m)
- Anchor height fraction (default 0.65, range 0.55 to 0.80)
- Rib reach (m)
- Rib bend angle (deg, default 15, range 5 to 40)

Placeholder inputs (see engine/PLACEHOLDERS.md):

- Column radius (m)
- Arm arc radius (m)

Derived internally (not user inputs):

- Strut intersection point (geometry intersection)
- Rib arc length (from rib reach and rib bend angle)
- Membrane four corners (from the four structural points above)
- Membrane surface (bilinear saddle between the four corners,
  10–15% edge sag placeholder until FDM lands)

Arrangement inputs, identical to Cantilever Leaf:

- Arrangement mode (single / double / multiple / tree_stack /
  tiered_helix)
- Number of units around column (multiple mode)
- Number of tiers (tree_stack mode)
- Number of leaves (tiered_helix mode)
- Leaf zone height (tiered_helix mode)
- Taper mode and ratio (tiered_helix mode)

---

## 4. Arrangement modes (identical to Cantilever Leaf)

- single      - one hypar on the column
- double      - two mirrored hypars
- multiple    - N hypars around the column (radial)
- tree_stack  - hypars stacked in tiers, scale factor 0.75
- tiered_helix - hypars spiralling up the column

The five modes reuse engine/leaf_arrangement.py exactly.
The engine is shape-agnostic: it produces position, rotation,
and scale for the mother object, and does not care what the
object is. No new arrangement code required.

---

## 5. Viewer requirements

The 3D viewer for one hypar mother object:

- Column (green vertical line, no curvature)
- Baseplate (green marker at column base)
- Main arc arm (red curve, rising in the middle, both ends at
  the same height)
- Diagonal strut (orange line from column top to the arm's
  structural anchor point)
- Two perpendicular bent ribs (blue curves, arcing upward,
  both tips higher than the rib anchor at the arm)
- Saddle membrane (blue semi-transparent surface across the
  four corners, edges concave inward)
- Edge cables (yellow dashed lines along the four membrane
  edges, concave inward)
- Column joint marker (yellow sphere at the structural anchor
  point on the arm)

The viewer will follow the same pattern as cantilever_leaf.py:
read parameters from session state, draw the mother object,
then let the arrangement layer multiply / stack / helix.

---

## 6. Render description (engine/render_prompts.py)

One clean shape sentence, live from params, in the same style
as the other variants. Draft:

  "Cantilever Hypar tensile membrane structure. One curved arc
   arm cantilevered from a column, with two perpendicular ribs
   at its midpoint, holding a taut four-corner saddle fabric
   membrane whose edges curve inward under tension."

Only the anchor height fraction appears as a number, matching
the style of the Leaf and Saddle prompts.

---

## 7. What is reused from Cantilever Leaf, exactly

Reuse without change:

- engine/leaf_arrangement.py — the arrangement engine.
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

## 8. Workshop prefix and variant key

Prefix:      ws_ch_
Variant key: cantilever_hypar

---

## 9. What is NOT in this spec

- Exact mathematics of the saddle membrane form-finding.
  Pending FDM engine.
- Structural analysis of the arm, ribs, strut, and column.
  Pending structural calc engine.
- Member sizing for any member. Pending structural calc engine.
- The exact numeric defaults for placeholder inputs beyond
  what is stated above. Propose at build.

---

## 10. Build order

1. viewers/figures/cantilever_hypar.py — mother-object geometry.
2. ui/workshops/saddle_hypar.py — mirror of saddle_leaf.py.
3. Registration wiring: un-hide Cantilever Hypar, wire button.
4. Dispatcher: add cantilever_hypar to viewers/results_viewer.py.
5. Render prompt: add _describe_cantilever_hypar.
6. Test all five arrangements in the viewer and in the renderer.

---

End of spec.





