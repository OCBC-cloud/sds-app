# SDSe — Substructures

**Status:** DESIGN ONLY. NOT COMMITTED TO CODE.
**Last updated:** 2026-09-28.
**Execute:** when the Chief decides.
**Related:** UI_ARCHITECTURE.md, TIERS.md, PROJECT_CONSTITUTION.md
(Part III-B).

This document describes the substructure categories used in every
SDSe workshop. Every structure is composed of the same six named
categories, plus an optional seventh. The specific inputs inside
each category differ per structure. The category names are the
same.

The document covers the four workshops that exist today:

  - Standard Saddle (Cable Supported Saddle)
  - Beam Supported Saddle
  - Cantilever Leaf
  - Cantilever Hypar

The shape currently called Crown-3Lobe is a recipe in the Tester.
It is not a workshop yet. Its classification and name will be
decided when the workshop is built. It is not listed here.

---

## PART 1 — PURPOSE

The workshop pattern described in UI_ARCHITECTURE.md uses six
substructure groups (plus Additional). The groups are the same
for every structure. This document lists the specific inputs
that belong to each group, for each of the four existing
structures.

The document is a migration guide. It shows how today's flat
list of 8 or 9 sections maps into the new six-group pattern.

The document also lists the exposure rules per access mode. The
rules are referenced from TIERS.md. They are design only. Not
executed.

---

## PART 2 — THE SEVEN CATEGORIES

Six named categories, plus an optional seventh.

  1. **Shape** — dimensions, curve, tilt, arrangement.
  2. **Membrane** — fabric type, fabric grade, pretension,
     attachment method, perimeter cable.
  3. **Frame** — steel grade, section family, member
     construction, supports, purlins, secondary beams.
  4. **Cables** — tie-down cables, edge cables, anchors.
  5. **Foundation** — soil, water table, foundation type.
  6. **Loads** — user payload, design standard, wind speed
     basis.
  7. **Additional** — optional. Empty by default. A named home
     for future inputs that do not fit the six.

The Additional group is only drawn when the recipe provides
inputs for it. Otherwise it is absent. The user sees six groups
for a typical structure, seven for a structure with additional
needs.

---

## PART 3 — THE INPUT FORMAT

Every input in a workshop recipe is a Python dict:

    {
        "key": "span",
        "label": "Span distance (m)",
        "type": "number",
        "default": 10.0,
        "min": 4.0,
        "max": 200.0,
        "step": 0.5,
    }

Fields:

  - **key** — the session-state key suffix. Combined with the
    structure and variant to give a unique session key.
  - **label** — the label shown to the user.
  - **type** — one of: number, integer, dropdown, radio, toggle.
  - **default** — the initial value.
  - **min**, **max**, **step** — for numeric types.
  - **options** — for dropdown and radio types. A list of
    [value, label] pairs.
  - **help** — optional help text.

The universal workshop renderer reads the type and builds the
correct widget.

There is no slider type. Sliders are never used in the new
pattern. Existing sliders in the four workshops will be
converted to number inputs during migration.

---

## PART 4 — STANDARD SADDLE

**Structure key:** saddle_span
**Variant key:** standard_saddle
**Session prefix:** ws_ss

### 4.1 Shape

Maps from the current "1. Geometry" section.

  - Span distance (m) — number — default 10.0.
  - Apex-to-apex distance (m) — number — default 15.0.
  - Rise (m) — number — default 6.2.
  - Beam curve type — dropdown — parabolic / circular /
    catenary. Default parabolic.

### 4.2 Membrane

Maps from the current "2. Materials" section (fabric part) and
"8. Membrane-to-Beam Attachment" section.

  - Fabric type — dropdown — from FABRIC_PROPERTIES. Default
    PVDF.
  - Fabric grade — dropdown — from the fabric type's grades.
    Default Type III.
  - Warp pretension (kN/m) — number — default 2.0.
  - Weft pretension (kN/m) — number — default 2.0.
  - Attachment method — radio — kader / segmented. Default
    kader.
  - Cable attachment count per beam — integer — only shown when
    segmented. Default 6.

### 4.3 Frame

Maps from the current "2. Materials" section (steel part) and
"3. Member Construction" and "4. Ground Supports".

  - Steel grade — dropdown — S235 / S275 / S355 / S420 / S460.
    Default S355.
  - Section family — dropdown — CHS / SHS / RHS / I-Beam.
    Default CHS.
  - Member construction — radio — single beam / planar truss /
    space truss. Default single beam.
  - Support at start — radio — pinned / rigid. Default pinned.
  - Support at end — radio — pinned / rigid. Default pinned.

### 4.4 Cables

Maps from the current "5. Tie-down Cables and Pretension"
section.

  - Tie-down count — radio — 4 / 8 cables. Default 4.
  - Anchor uplift angle (deg) — number — default 45.
  - Anchor spread angle (deg) — number — default 30.
  - Cable type — dropdown — 6x19 / locked coil / spiral.
    Default 6x19.
  - Cable material — dropdown — galvanised / stainless.
    Default galvanised.
  - Ground anchor type — radio — pinned / rigid. Default
    pinned.
  - Edge cable pretension (kN) — number — default 5.0.

### 4.5 Foundation

Maps from the current "6. Baseplate and Preliminary
Foundation" section.

  - Soil bearing capacity (kN/m2) — number — default 150.0.
  - Water table depth (m) — number — default 3.0.
  - Soil type — dropdown — sand / clay / rock / filled.
    Default sand.
  - Foundation type — dropdown — pad / pile / raft. Default
    pad.

### 4.6 Loads

Maps from the current "7. Loads and Design Standard" section.

  - Additional payload (kg/m) — number — default 0.0.
  - Design standard — dropdown — EU / MY / UK / CN / US.
    Default MY.
  - Wind speed basis — preview (from WIND_SPEEDS, not an input).

### 4.7 Additional

Empty by default.

---

## PART 5 — BEAM SUPPORTED SADDLE

**Structure key:** saddle_span
**Variant key:** frame_supported_saddle
**Session prefix:** ws_bs

### 5.1 Shape

  - Span distance (m) — number — default 10.0.
  - Apex-to-apex distance (m) — number — default 15.0.
  - Rise (m) — number — default 6.2.
  - Beam curve type — dropdown. Default parabolic.

### 5.2 Membrane

  - Fabric type — dropdown.
  - Fabric grade — dropdown.
  - Membrane pretension (kN/m) — number — default 2.0.
  - Attachment method — radio — kader / segmented. Default
    kader.

### 5.3 Frame

Includes the beam, the secondary beams, and the purlins.

Beam:

  - Steel grade — dropdown. Default S355.
  - Section family — dropdown. Default CHS.
  - Beam construction — radio — single beam / planar truss /
    space truss. Default single beam.
  - Support at start — radio — pinned / rigid. Default pinned.
  - Support at end — radio — pinned / rigid. Default pinned.

Secondary beams:

  - Use system recommendation — radio — yes / no. Default yes.
  - Number per beam — dropdown — even numbers. Shown only when
    override.
  - Construction type — radio — single beam / planar truss /
    space truss. Default single beam.
  - Section family — dropdown. Default CHS.
  - Base connection — radio — pinned / rigid. Default pinned.
  - Uplift angle (deg) — number — default 45.
  - Spread angle (deg) — number — default 30.

Purlins:

  - Arrangement — preview (auto-computed by engine at 2.5 m
    intervals).
  - Purlin construction type — radio — single beam / planar
    truss / space truss. Default single beam.
  - Purlin section family — dropdown. Default CHS.

### 5.4 Cables

Empty for this structure today. Note: this structure does not
have tie-down cables; it has secondary beams instead.

### 5.5 Foundation

Same as Standard Saddle.

  - Soil bearing capacity — number — default 150.0.
  - Water table depth — number — default 3.0.
  - Soil type — dropdown. Default sand.
  - Foundation type — dropdown. Default pad.

### 5.6 Loads

  - Additional payload (kg/m) — number — default 0.0.
  - Design standard — dropdown. Default MY.
  - Wind speed basis — preview.

### 5.7 Additional

Empty by default.

---

## PART 6 — CANTILEVER LEAF

**Structure key:** cantilever
**Variant key:** cantilever_leaf
**Session prefix:** ws_sl

### 6.1 Shape

Includes the object shape, the geometry, and the arrangement.

Object shape:

  - Base object — radio — leaf (active) / flower / bell / hypar
    (coming soon). Default leaf.

Geometry:

  - Column height (m) — number — default 10.0.
  - Leaf outreach (m) — number — default 10.0.
  - Ribs per side — integer — default 7, min 5, max 7.
  - Rib tilt angle (deg) — number — default 20, min 5, max 40.
  - Rib plan spacing (deg) — number — default 45, min 15, max
    90.
  - Main beam arc radius (m) — number — default 5.0.
  - Spine curve type — dropdown — parabolic / circular /
    catenary. Default parabolic.

Arrangement:

  - Arrangement — radio — single / double / multiple / tree
    stack / tiered helix. Default single.
  - Number of objects (multiple) — integer — default 4.
  - Number of tiers (tree) — integer — default 1.
  - Leaf zone height (tiered helix) — number — default 7.0.
  - Number of leaves (tiered helix) — integer — default 8.
  - Column radius (tiered helix) — number — default 0.15.
  - Leaf angular width (tiered helix) — number — default 60.
  - Scale mode (tiered helix) — radio — full scale / taper up /
    taper down. Default taper up.
  - Taper ratio — number — default 0.88.

### 6.2 Membrane

  - Fabric type — dropdown.
  - Fabric grade — dropdown.
  - Membrane pretension (kN/m) — number — default 2.0.
  - Attachment method — radio — kader / segmented. Default
    kader.
  - Perimeter cable type — dropdown — 6x19 / locked coil /
    spiral. Default 6x19.
  - Perimeter cable material — dropdown — stainless /
    galvanised. Default stainless.

### 6.3 Frame

  - Steel grade — dropdown. Default S355.
  - Section family — dropdown. Default CHS.
  - Column type — radio — unipole / truss. Default unipole.
  - Column section preference — radio — auto / manual. Default
    auto.
  - Strut angle (deg) — number — default 42.
  - Rib section family — dropdown. Default CHS.
  - Rib section preference — radio — auto / manual. Default
    auto.
  - Rib-to-spine connection — radio — bolted / welded. Default
    bolted.

### 6.4 Cables

  - Perimeter cable is listed under Membrane in this structure.
    No other cable inputs today.

### 6.5 Foundation

  - Soil bearing capacity — number — default 150.0.
  - Water table depth — number — default 3.0.
  - Soil type — dropdown. Default sand.
  - Foundation type — dropdown. Default pad.

### 6.6 Loads

  - Additional payload (kg/m) — number — default 0.0.
  - Design standard — dropdown. Default MY.
  - Wind speed basis — preview.

### 6.7 Additional

  - Rib length overrides (Adjust Rib Lengths room) — the
    dedicated leaf_room.py.
  - Reset to computed lengths — an action button.

---

## PART 7 — CANTILEVER HYPAR

**Structure key:** cantilever
**Variant key:** cantilever_hypar
**Session prefix:** ws_ch

### 7.1 Shape

Object shape:

  - Base object — radio — leaf (coming) / flower (coming) /
    bell (coming) / hypar (active). Default hypar.

Geometry:

  - Column height (m) — number — default 10.0.
  - Arm reach (m) — number — default 6.0.
  - Anchor height fraction — number — default 0.65, min 0.55,
    max 0.80.
  - Rib reach (m) — number — default 3.0.
  - Rib curve radius (m) — number — default 6.0.
  - Membrane edge sag (%) — number — default 15, min 0, max 30.

Arrangement:

  - Same five arrangements as Cantilever Leaf.
  - Same inputs for multiple / tree / tiered helix.
  - Same defaults.

### 7.2 Membrane

  - Fabric type — dropdown.
  - Fabric grade — dropdown.
  - Membrane pretension (kN/m) — number — default 2.0.
  - Attachment method — radio — kader / segmented. Default
    kader.
  - Perimeter cable type — dropdown. Default 6x19.
  - Perimeter cable material — dropdown. Default stainless.

### 7.3 Frame

  - Steel grade — dropdown. Default S355.
  - Section family — dropdown. Default CHS.
  - Column type — radio — unipole / truss. Default unipole.
  - Column section preference — radio — auto / manual. Default
    auto.
  - Rib section family — dropdown. Default CHS.
  - Rib section preference — radio — auto / manual. Default
    auto.
  - Rib-to-arm connection — radio — bolted / welded. Default
    bolted.

### 7.4 Cables

  - Perimeter cable is listed under Membrane in this structure.
    No other cable inputs today.

### 7.5 Foundation

  - Same as Cantilever Leaf.
  - Soil bearing capacity — number — default 150.0.
  - Water table depth — number — default 3.0.
  - Soil type — dropdown. Default sand.
  - Foundation type — dropdown. Default pad.

### 7.6 Loads

  - Additional payload (kg/m) — number — default 0.0.
  - Design standard — dropdown. Default MY.
  - Wind speed basis — preview.

### 7.7 Additional

  - Empty by default.

---

## PART 8 — EXPOSURE PER ACCESS MODE

Every input has one of three exposure states per access mode:

  - **Editable** — the user sees and can change the input.
  - **Read-only** — the user sees the input but cannot change
    it.
  - **Hidden** — the user does not see the input.

The following table is the design. It is referenced from
TIERS.md. It is not executed.

| Category | Owner | Beta | Studio | Pro | Free |
|---|---|---|---|---|---|
| Shape | Editable | Editable | Editable | Editable | Editable |
| Membrane | Editable | Editable | Editable | Editable | Read-only |
| Frame | Editable | Editable | Editable | Editable | Hidden |
| Cables | Editable | Editable | Editable | Editable | Hidden |
| Foundation | Editable | Editable | Editable | Read-only | Hidden |
| Loads | Editable | Editable | Read-only | Hidden | Hidden |
| Additional | Editable | Editable | Editable | Editable | Hidden |

Notes:

  - **Owner** sees and controls everything.
  - **Beta** sees the full product. Output is watermarked.
  - **Studio** is the full commercial product.
  - **Pro** is Studio minus foundation editing, minus loads
    editing.
  - **Free** is a shape sketch. Membrane is read-only. Nothing
    else is visible.

The detailed per-input exposure will be listed in a future
revision once the tier system is executed.

---

## PART 9 — WHAT IS NOT YET LISTED

The following structures exist in `data/structures.py` as
placeholders. They have no workshop yet. They are not in this
document.

  - Uni-Pole Tensile Roof (single cone, multi-cone cluster,
    umbrella).
  - Tensile Sails Roof (hypar sail 3, hypar sail 4, multiple
    wall sails, multiple column sails).
  - Framed Tensile Roof (simple frame, arched frame, trussed
    frame).
  - Canopy (wall-mounted, cable-supported, tree).
  - Frame Tent (pyramid, modular, cone, A-frame, arch).
  - Portal Frame (simple, with mezzanine, with crane, multi-bay).

The shape currently called **Crown-3Lobe** is a recipe in the
Tester. It is not a workshop yet. Its classification and name
will be decided when the workshop is built.

When any of the above becomes a workshop, this document is
updated with the new substructure map.

---

## PART 10 — DOCUMENT HISTORY

Created: 2026-09-28.
  - Seven substructure categories defined.
  - Input format defined.
  - Input map for the four existing workshops documented.
  - Exposure table per access mode drafted.
  - Not-yet-listed structures noted.
  - Status: DESIGN ONLY. NOT EXECUTED.
