# SDSe — UI Architecture

**Status:** DESIGN ONLY. NOT COMMITTED TO CODE.
**Last updated:** 2026-09-28.
**Execute:** when the Chief decides.
**Related:** PROJECT_CONSTITUTION.md (Part III-B), TIERS.md,
SUBSTRUCTURES.md, FILE_INVENTORY.md.

This document describes the UI architecture of the SDSe app.
It is a design. It has not been implemented. The app runs
today as it did yesterday.

When the Chief says "execute", this design becomes code. Until
then, nothing changes.

---

## PART 1 — PURPOSE

The app runs. The engine works. The screens are functional.
But the interface is not yet what it should be.

Three problems exist today:

  1. Every workshop is a hand-written file. Adding a structure
     means writing code. It should mean adding a recipe.

  2. The workshop files are long and hard to edit on the iPhone.
     Every change risks a paste corruption. The working method
     protects us, but the surface area is large.

  3. The interface is bespoke per structure. There is no
     consistency across workshops beyond the CSS helpers. The
     user has to learn each one separately.

This document describes the target architecture. It fixes all
three problems at once.

The doctrine is in PROJECT_CONSTITUTION.md, Part III-B. Read
that first. This document is the design that follows from it.

---

## PART 2 — THE DOCTRINE, RESTATED

The engine is universal. The interface is data.

The engine accepts boundaries, anchors, edge types, and force
densities. It does not know shapes. It is already universal,
and it stays that way.

The interface is a set of recipes. A recipe is a small data
file that describes one shape: how its boundary is built, what
inputs it accepts, how its 3D viewer draws it, and how it is
described in a marketing prompt.

Universal renderers read the recipes. There is one renderer
per layer:

  - One workshop renderer, which reads a workshop recipe and
    builds the input page.
  - One viewer renderer, which reads a viewer recipe and
    builds the 3D figure.
  - One prompt builder, which reads a prompt recipe and
    produces the marketing text.

The engines and the renderers are code. They change rarely.
The recipes are data. They change every time a new structure
is added.

Adding a new structure means writing four small recipe files.
It does not mean writing four new code files.

---

## PART 3 — THE RECIPE FORMAT

There are four kinds of recipe. Each one describes a different
layer of the shape.

  - A **shape recipe** describes the boundary. It is a
    function that returns a grid, a boundary, anchors, and
    edge types. This is what the engine consumes.

  - A **workshop recipe** describes the inputs. It is a data
    structure with a list of input groups, and within each
    group a list of inputs. Every input has a name, a label,
    a type, a default value, a range, and a unit.

  - A **viewer recipe** describes the 3D figure. It lists the
    members to draw (beams, cables, tie-downs, supports) and
    how to compute their positions from the workshop inputs.

  - A **prompt recipe** describes the marketing text. It
    produces a single sentence that describes the shape, with
    explicit scale.

Each recipe lives in its own file. The four files together
define one structure.

### 3.1 Shape recipe

A shape recipe is a Python function with a fixed signature:

    def build_shape(params):
        # returns (grid, boundary, anchors, edge_types)
        ...

`params` is a dict of the current workshop values. The function
reads the values it needs (span, apex, rise, and so on) and
returns the tuple that the engine consumes.

This is exactly the form that the five recipes in the Tester
already use. The Tester is the prototype of the shape recipe
pattern.

### 3.2 Workshop recipe

A workshop recipe is a Python dict:

    WORKSHOP_RECIPE = {
        "structure_key": "saddle_span",
        "variant_key": "standard_saddle",
        "title": "Standard Saddle Span",
        "groups": [
            {
                "key": "shape",
                "name": "Roof shape",
                "help": "Overall dimensions of the saddle span.",
                "inputs": [
                    {
                        "key": "span",
                        "label": "Span distance (m)",
                        "type": "number",
                        "default": 10.0,
                        "min": 4.0,
                        "max": 200.0,
                        "step": 0.5,
                    },
                    {
                        "key": "curve_type",
                        "label": "Beam curve",
                        "type": "dropdown",
                        "options": [
                            ["parabolic", "Parabolic"],
                            ["circular", "Circular"],
                            ["catenary", "Catenary"],
                        ],
                        "default": "parabolic",
                    },
                ],
            },
        ],
    }

Every input is a dict. The dict's `type` field decides how the
input renders. The universal workshop renderer reads the type
and builds the correct widget.

Input types:

  - **number** — a numeric field with min, max, step, default.
  - **integer** — same, without decimals.
  - **dropdown** — a list of [value, label] pairs and a default.
  - **toggle** — on/off. Two labels. Default.
  - **radio** — a list of [value, label] pairs and a default.

There is no slider type. Sliders are never used.

### 3.3 Viewer recipe

A viewer recipe is a Python dict:

    VIEWER_RECIPE = {
        "members": [
            {
                "kind": "beam_curve",
                "source": "beam_L_points",
                "color": "#FF6B6B",
                "width": 8,
            },
            {
                "kind": "cable_line",
                "endpoints": "tiedown_pairs",
                "color": "#f1c40f",
                "width": 2,
            },
        ],
        "membrane": {
            "kind": "fdm_solved_mesh",
            "from_recipe": "standard_saddle",
        },
    }

The viewer renderer reads the recipe and builds the corresponding
Plotly traces. Each member is either a beam, a cable, or a
support. The membrane is the FDM-solved mesh from the shape
recipe.

### 3.4 Prompt recipe

A prompt recipe is a Python function:

    def describe(params):
        # returns (name, shape_sentence)
        ...

It reads the workshop params and returns a name and a shape
sentence. The prompt builder combines the shape sentence with
the camera phrase, the lighting, the scene, and the scale tail.

The current `_describe_standard_saddle` and its siblings are
already in this form. The Tester has proven the pattern.

---

## PART 4 — THE UNIVERSAL RENDERERS

Three renderers. Each one reads a recipe and produces the
output.

### 4.1 The workshop renderer

`ui/workshops/_renderer.py` (future file).

Reads a workshop recipe. For each group in the recipe:

  - If the group has inputs, draw an accordion header with the
    group name and help text.
  - If the accordion is expanded, iterate over the inputs and
    build the correct widget for each type.
  - Write the input value to session state under a key derived
    from the structure and variant.

The renderer is stateless. It reads the recipe. It writes to
session state. It does not know what any input means. It does
not contain any logic specific to a structure.

The renderer also enforces the visual rules:

  - No sliders. Ever.
  - Two-column layout for pairs of number inputs.
  - One column for text and radio inputs.
  - Preview boxes below inputs when the recipe provides a
    preview rule.
  - Warning boxes below the group when the recipe provides a
    warning rule.

### 4.2 The viewer renderer

`viewers/_renderer.py` (future file).

Reads a viewer recipe. For each member in the recipe:

  - Compute the geometry from the workshop params.
  - Add the correct Plotly trace.

For the membrane:

  - Call the shape recipe.
  - Call `solve_fdm` (or the MBS engine).
  - Draw the solved mesh.

The renderer is stateless. It reads the recipe. It draws the
figure. It does not know any specific structure.

### 4.3 The prompt builder

`engine/render_prompts.py` (existing, will be simplified).

The builder already exists. It reads a prompt recipe (the
per-variant `describe` function), combines it with the fixed
camera phrase, the lighting from TIMES, the scene from SCENES,
and the scale tail.

No change to the builder is required. Only the recipes are
moved into a per-structure file, instead of being inline in
`render_prompts.py`.

---

## PART 5 — THE SCREEN FLOW

The app has six screens today. The design keeps six. One is
new (the Access Gate). One is renamed (the Tester becomes a
page inside the same app).

The flow:

    Access Gate
        |
        v
    Landing
        |
        v
    Studio
        |
        v
    Registration
        |
        v
    Workshop
        |
        v
    Results

Each screen has a job. No screen does more than its job.

### 5.1 Access Gate (future)

New page. Before Landing.

Enter a code. Validate. Set access mode. Move to Landing.

Design only. Not executed. Detailed in TIERS.md.

### 5.2 Landing

The splash. Logo, title, subtitle, one primary button
("Enter The Studio"), one secondary button for the Tester
(Owner-only). Footer.

Unchanged from today, except the Tester button is Owner-only
when the tiers are executed.

### 5.3 Studio

The main menu. Top bar with the wordmark. Header "Choose Your
Structure Type". A guided-design tile at the top. Eight
structure tiles in two sections.

Unchanged from today.

### 5.4 Registration

Project information (name, client, location, reference,
engineer, date). Then variant selection for the chosen
structure.

Unchanged from today.

### 5.5 Workshop

The input page. This is where the design changes.

Today: a flat list of expanders. Eight sections. All inputs
visible at once (through expansion).

Future: a set of accordion groups, one per substructure. Each
group collapsed by default. Each group's header shows the
current values as a summary. Tap to expand. The inputs inside
the group appear.

No sliders. Number fields, steppers, dropdowns, radios,
toggles only.

The universal workshop renderer builds this from the workshop
recipe. One renderer. Many recipes.

### 5.6 Results

The 3D viewer. The marketing render section (one-touch button).
The health score. Section used. Analysis readings. Quantities.
Actions.

Unchanged from today.

---

## PART 6 — THE WORKSHOP PATTERN

The workshop is the biggest change. This part describes it in
detail.

### 6.1 The substructure groups

Every structure has six substructure groups. The names are the
same for every structure. The inputs inside differ.

  - **Shape** — dimensions, curve, tilt.
  - **Membrane** — fabric, prestress, attachment method.
  - **Frame** — steel grade, section, member construction,
    supports.
  - **Cables** — tie-downs, edge cables, anchors.
  - **Foundation** — soil, foundation type.
  - **Loads** — payload, design standard.

Not every structure uses all six. A structure with no
foundation inputs hides the Foundation group. But the group
order is the same. The group keys are the same. The user
learns the pattern once.

### 6.2 The accordion

Each group is an accordion.

Collapsed by default. The header shows:

  - The group name.
  - A one-line summary of the current values.

For the Shape group: "Span 10.0 m · Rise 6.2 m · Parabolic".

For the Membrane group: "PVDF Type III · Warp 2.0 · Weft 2.0".

The summary is built by the recipe. The recipe provides a
`summary` function. The renderer calls it and prints the
result.

When tapped, the group expands. The inputs appear. When tapped
again, it collapses.

The user can expand any number of groups at once. There is no
"only one open" rule.

### 6.3 The input types

Five types. No others.

  - **number** — a numeric field.
  - **integer** — a numeric field with integer values.
  - **dropdown** — a select box with options.
  - **radio** — a radio group with options.
  - **toggle** — an on/off switch.

**Sliders are never used.** They are hard to control on a
phone, they are imprecise, and they do not accept typed
values.

Every input has:

  - a label,
  - a unit (if numeric),
  - a default value,
  - optional min and max,
  - optional step.

### 6.4 Preview boxes

Below some inputs, a preview box shows the calculated result of
the input.

For example, if the user sets a segmented attachment with 8
points along a 10 m span, the preview box shows "Approximate
spacing between attachments: 1.25 m".

The preview box is defined by the recipe. The renderer draws
it. The recipe provides a `preview` function per group.

### 6.5 Warning boxes

Below some groups, a warning box appears if a validation rule
fails.

For example, if the rise / span ratio is very low, the warning
box appears: "Rise / Span ratio is very low. Membrane may not
drain."

The warning rule is defined by the recipe. The renderer calls
it. If it returns a message, the warning box appears.

### 6.6 The one-touch render

The Results page already has a one-touch button: copy the
prompt and open Gemini.

This is the pattern for the whole app. Where an external
action is needed, the app does what it can (copy, prepare,
link) and the user does the rest. There is no fake
automation.

### 6.7 The action buttons

At the bottom of every workshop:

  - **Back to Registration** — secondary.
  - **Intelligent Design Computing** (or equivalent) — primary.

These move to the Results page.

The Tester has a different set. Not part of this pattern.

---

## PART 7 — THE SUBSTRUCTURE MAP

The detailed map of the six substructure categories, and the
inputs inside each, is in SUBSTRUCTURES.md.

This document references that file. The map is not duplicated
here.

Each structure has six categories:

  - Saddle Span (Standard) — same six.
  - Saddle Span (Beam Supported) — same six.
  - Cantilever Leaf — same six.
  - Cantilever Hypar — same six.
  - Crown-3Lobe — same six. (Currently in the Tester. To be
    promoted to a workshop.)

Different inputs inside each category. Same category names.
Same order. Same pattern.

---

## PART 8 — THE VISUAL LANGUAGE

The visual language is defined in `core/theme.py`. The design
does not duplicate it.

Colours used by the app:

  - Background: #0a0e17.
  - Surface: #121e2e, #141e2b, #1e2a3a.
  - Primary accent: #f39c12 (amber).
  - Secondary: #4a7a9c (steel blue).
  - Success: #2ecc71 (green).
  - Danger: #e74c3c (red).
  - Body text: #f0f4fa.
  - Muted text: #a8b8c8.

Component classes:

  - .sdse-card — generic container.
  - .dash-card — dashboard tile.
  - .path-card — the studio tiles.
  - .metric-card — the metric boxes.
  - .result-row — label / value rows.
  - .member-recommend — highlight for recommended sections.
  - .health-score — the big score display.
  - .sdse-badge — small tags.

The workshop CSS in `_shared.py` adds:

  - .ws-section — the workshop card.
  - .ws-section-title — the workshop title.
  - .ws-section-help — the help text.
  - .ws-preview-box — the preview box.
  - .ws-warning-box — the warning box.
  - .ws-info-box — the info box.

The two CSS systems (theme and workshop) use different prefixes
(.sdse- and .ws-). This is deliberate. The theme is global.
The workshop CSS is local to the workshop pages.

---

## PART 9 — THE MIGRATION PLAN

This part describes how to move from today's code to the
design in this document. It is not executed. It is the plan
for when the Chief says execute.

### 9.1 Step 1 — Build the universal workshop renderer

New file: `ui/workshops/_renderer.py`.

It reads a workshop recipe and builds the input page. It
enforces the accordion pattern. It enforces no sliders. It
supports all five input types.

Test it with a minimal recipe (two groups, four inputs). Do
not wire it into the app yet. Verify it in isolation.

### 9.2 Step 2 — Migrate one workshop

Choose the simplest workshop. Convert it to a recipe file.

Replace the workshop's current file with:

    from ui.workshops._renderer import render_workshop
    from data.recipes.standard_saddle import WORKSHOP_RECIPE

    def render_saddle_standard():
        render_workshop(WORKSHOP_RECIPE)

Test. If the migrated workshop looks and behaves the same as
before, the renderer is correct. If not, fix the renderer.

### 9.3 Step 3 — Migrate the remaining workshops

One at a time. Same pattern. Commit per workshop. Reboot.
Test. Move to the next.

The old workshop files are deleted only after the new ones
work. No regressions.

### 9.4 Step 4 — Build the universal viewer renderer

New file: `viewers/_renderer.py`.

It reads a viewer recipe and builds the 3D figure. Test it in
isolation.

### 9.5 Step 5 — Migrate one viewer

Choose the simplest viewer. Convert it to a recipe file. Test.
Migrate the others one at a time.

### 9.6 Step 6 — Move the prompt recipes

Move the per-variant `describe` functions out of
`render_prompts.py` into per-structure files.

`render_prompts.py` keeps the camera phrase, the scenes, the
times, and the assembler. The per-structure descriptions move.

### 9.7 Step 7 — Promote the Crown-3Lobe

Move the Crown-3Lobe shape from the Tester into a proper
workshop. Apply the recipe pattern. Add it to the Studio page.

### 9.8 Step 8 — Test the whole app

Every structure. Every workshop. Every viewer. Every prompt.

### 9.9 Rollback

If any step fails, the old file is restored from git. The
universal renderer is not committed until it works. No
regression is possible at any step.

---

## PART 10 — WHAT IS NOT EXECUTED

The following are documented but not executed:

  - The Access Gate and access codes. Design only. See
    TIERS.md.
  - The tier filter for workshop inputs. Design only. See
    SUBSTRUCTURES.md.
  - The Owner tools panel. Design only. See TIERS.md.
  - The Beta watermark. Design only. See TIERS.md.
  - The URL resilience plan (custom domain, status page).
    Business plan only. See TIERS.md.

None of the above changes the app today. All of it is planned.

---

## PART 11 — DOCUMENT HISTORY

Created: 2026-09-28.
  - Full UI architecture design.
  - Recipe format defined (shape, workshop, viewer, prompt).
  - Universal renderer design.
  - Screen flow documented.
  - Accordion workshop pattern defined.
  - Migration plan documented.
  - Status: DESIGN ONLY. NOT EXECUTED.
