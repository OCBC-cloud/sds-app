# PLACEHOLDERS — Temporary Inputs and Values

Status: active. Update whenever a placeholder is added or removed.
Date: 2026-09-21.
Related: engine/PRINCIPLES_membrane.md, engine/SPEC_*.md.

---

## 1. Purpose of this document

In the finished SDSe app, member sizes and membrane shapes are
determined by the structural calculation engine and the FDM
form-finding engine. The user does not type those values.

Until those engines are built, the app uses placeholder inputs
so the viewer can draw something and the workshops can be
exercised end to end.

This document is the **single source of truth** for which inputs
are placeholders and which are real user inputs.

When a structural or FDM engine lands:

1. Find its placeholder inputs in this document.
2. Remove them from the user interface.
3. Have the engine supply the value instead.
4. Delete the row from this document.
5. Commit with message `placeholders: remove <name>`.

---

## 2. Placeholder inputs (to be removed when engines land)

| Input | Where | Purpose now | Replaced by |
|---|---|---|---|
| Column radius | All pole-mounted variants | Draws the column thickness | Structural calc engine |
| Section family (CHS / SHS / RHS) | All workshops | Draws the cross-section | Structural calc engine |
| Steel grade | All workshops | Label only | Structural calc engine |
| Fabric type and grade | All workshops | Label only | FDM engine + fabric catalogue |
| Main beam arc radius | Cantilever Leaf | Draws the arm curve | Structural calc engine (span and shape driven) |
| Ribs per side | Cantilever Leaf | Number of ribs drawn | Structural calc engine (spacing driven by load) |
| Rib tilt / rib bend angle | Cantilever Leaf | Draws rib inclination | Structural calc engine |
| Rib plan spacing | Cantilever Leaf | Angular position of ribs | Structural calc engine |
| Strut angle | Cantilever Leaf | Draws the strut | Structural calc engine (moment equilibrium) |
| Rib reach | Cantilever Hypar | Draws the rib extent | Structural calc engine |
| Rib bend angle | Cantilever Hypar | Draws the rib arc | Structural calc engine |
| Anchor height fraction | Cantilever Hypar | Where the arm attaches | Structural calc engine (moment equilibrium) |
| Secondary beam count (auto) | Beam Supported Saddle | Number of secondary beams | Structural calc engine |
| Purlin spacing (auto) | Beam Supported Saddle | Draws purlin positions | Structural calc engine |
| Membrane edge sag (10–15%) | All viewers | Draws the saddle surface | FDM form-finding result |

---

## 3. Real user inputs (kept — do NOT remove)

These describe the problem. They stay.

| Input | Reason |
|---|---|
| Column height | User's design choice |
| Span / apex / rise | User's design choice (Saddle variants) |
| Arm reach | User's design choice (Cantilever Hypar) |
| Leaf outreach | User's design choice (Cantilever Leaf) |
| Number of leaves / units | User's design choice (Multiple / Tiered Helix) |
| Number of tiers | User's design choice (Tree Stack) |
| Membrane pretension | User's target stress state (real input, not placeholder) |
| Cable pretension | User's target stress state |
| Tie-down count (4 / 8) | User's design choice |
| Uplift angle / spread angle | User's design choice |
| Add. Pay Load | User's equipment loads |
| Soil bearing capacity | From the site |
| Soil type | From the site |
| Water table depth | From the site |
| Foundation type | User's design choice |
| Design standard | User's country |
| Attachment method (kader / segmented) | User's design choice |
| Column type (unipole / truss) | User's design choice |
| Member construction (single beam / truss) | User's design choice |

---

## 4. Convention in the code

Every placeholder input is marked in the code with a comment:

    # PLACEHOLDER — replaced by structural calc engine.
    # See engine/PLACEHOLDERS.md. Remove this input from the UI
    # when the engine lands.

Every placeholder drawing value (not a user input, but a value
we compute to fake the real answer) is marked:

    # PLACEHOLDER VALUE — replace with FDM / structural result.
    # See engine/PLACEHOLDERS.md.

---

## 5. Convention in specs

Every spec file begins with a pointer line:

    PLACEHOLDER INPUTS: see engine/PLACEHOLDERS.md.

Do not duplicate the list in the spec. One source of truth.

---

## 6. What this document does NOT cover

- Real, permanent design decisions (the ones in §3 above).
- Regulatory requirements (design codes, safety factors).
- Legal or commercial terms.

---

End of document.





