# SDSe — Project State Addendum

Date: 2026-09-21.
Covers: 2026-09-19, 2026-09-20, 2026-09-21.

Read this file AFTER:

  - PROJECT_STATE.md       (last updated 2026-09-18)
  - PROJECT_VISION.md      (last updated 2026-09-19)

Those two files are unchanged. This addendum records what has
happened since they were last updated. Together, the three
files give the current picture.

---

## 1. Why an addendum

The main PROJECT_STATE.md and PROJECT_VISION.md contain the
Constitution, the Rules, the Five Systems Architecture, the
Roadmap, and the Vision. They are foundational documents.
They are not to be overwritten lightly.

But three days of work have happened since they were last
updated. Rather than rewrite them (and risk losing their
substance), this addendum sits alongside and records the
changes.

---

## 2. New structure built: Cantilever Hypar

Built end to end on 2026-09-20 and 2026-09-21.

Status: LIVE.

What was built:

  - Spec document: engine/SPEC_cantilever_hypar.md
  - Viewer: viewers/figures/cantilever_hypar.py
  - Workshop: ui/workshops/saddle_hypar.py
  - Registration wiring: data/structures.py + ui/workshop.py
  - Render prompt branch: engine/render_prompts.py
  - MEMBER_SCHEMA entry: data/structures.py

Geometry summary:

  Four membrane corners A, B, C, D.
  A and C are the arm ends. Both at the anchor height.
  B and D are the rib tips. Both higher than A and C.
  The membrane is a saddle bounded by four concave edges.
  The cable follows the same concave curve as the fabric edge.
  The rib is ONE continuous arc through three points:
    left rib tip, arm midpoint, right rib tip.
    Arm midpoint is the LOW point of the arc.
    Rib tips are the HIGH points.

User-adjustable inputs added for Hypar:

  - Column height (m)
  - Arm reach (m)
  - Anchor height fraction (0.55 to 0.80, default 0.65)
  - Rib reach (m)
  - Rib curve radius (m) — default 6.0
  - Membrane edge sag (%) — 0 to 30, default 15

Placeholder inputs (see engine/PLACEHOLDERS.md):

  - Column radius
  - Arm arc radius
  - Rib curve radius (until structural engine lands)
  - Membrane edge sag (until FDM engine lands)

The Hypar reuses the arrangement engine
(engine/leaf_arrangement.py) without change. All five
arrangements work: single, double, multiple, tree_stack,
tiered_helix.

---

## 3. Registration page cleaned up

Change: the Cantilever family on Registration now shows only
two entries.

  - Cantilever Leaf       — Select opens the Leaf workshop.
  - Cantilever Variants   — Select opens the Hypar workshop.
                            (Previously labelled "Cantilever Hypar".)

Removed from Registration (hidden, not shown at all):

  - Cantilever Flower
  - Cantilever Cone
  - Cantilever Pyramid
  - Cantilever Bell
  - Cantilever Sail

These remain in data/structures.py with available=False.
They will be reachable from inside the workshop's Section 1
once that routing is built.

Code change: ui/registration.py now SKIPS variants with
available=False, instead of showing them greyed out.

---

## 4. Render prompt engine rebuilt

Between 2026-09-19 and 2026-09-21, engine/render_prompts.py
went through a full rewrite.

What it is now:

  - Short, shape-only prompt per variant. Live from workshop
    values, not hardcoded.
  - Structure name + shape sentence + lighting + scene.
  - Character guard: prompt capped at 440 chars to stay below
    Bing Image Creator's 480-character limit. Nothing gets
    truncated by the renderer.
  - Each variant has its own shape-writer function.

Scenes:

  Added: Technical (neutral background). Overrides time-of-day
  lighting. Produces a clean product-shot with no scene, no
  people.

  Existing scenes kept: Public Garden, Monumental Square,
  Event Venue, Retail / Cafe, Motorsports Paddock, National
  Day Parade, Chinese Mountain Landscape, Air Force Base.

Time-of-day presets:

  Rewritten as four plain slots:
    Morning, Noon, Evening, Night.

  Replaces the earlier mixed set (Morning, Midday,
  Golden Hour, Evening / Dusk).

Camera and lens specs:

  Removed from all scenes. They are largely ignored by the AI
  and consumed character budget. The AI focuses on the shape.

Known limitation accepted:

  The external renderer does not always reproduce the exact
  structure. When the viewer shape is correct, the render is
  close. Renders are mood images, not engineering documentation.

---

## 5. Results page changed

What changed:

  - The viewer description and the dimensions strings are now
    drawn INSIDE the 3D chart (by viewers/results_viewer.py),
    not as separate HTML below it. They appear as amber
    annotations at the bottom of the plot area, matching the
    legend font size.
  - extract_display_params() removed. It was dumping every
    ws_* key as a junk list.
  - get_structure_summary() removed. Replaced by the
    workshop-written viewer strings.
  - The format_prompt() call now passes a params dict (per
    variant) so the shape sentence is live.

---

## 6. Bugs fixed since 2026-09-18

Bug: Column height showed stale value in the viewer
     dimensions string, and in the prompt.
Cause: Session-state keys were overwritten by widget defaults
       on background reruns when navigating from workshop to
       results.
Fix: Read the WIDGET key first, then fall back to the semantic
     session key. Applied in:
       ui/workshops/saddle_leaf.py
       ui/workshops/saddle_standard.py
       ui/workshops/saddle_frame.py
       ui/workshops/saddle_hypar.py

Bug: Edge cables crossed each other as a bowtie on the Hypar.
Cause: Corner order in the drawing was anchor -> left -> tip ->
       right -> anchor, which crosses itself.
Fix: Reordered to anchor -> tip -> right -> left -> anchor.

Bug: Viewer annotation font was larger than the legend font.
Cause: Annotation size was 13, legend was 8.
Fix: Annotation size reduced to 8.

Bug: Yellow joint marker on the arm cluttered the Hypar viewer.
Fix: Removed entirely. The strut now ends cleanly on the arm.

Bug: User-adjusted rib lengths did not affect the viewer in
     some cases due to widget key persistence.
Fix: Same widget-key-first read.

Bug: The registration page showed unbuilt variants as
     "Coming Soon", cluttering the page.
Fix: ui/registration.py now filters out available=False
     variants entirely.

---

## 7. New documents on file

engine/PRINCIPLES_membrane.md
  The form-finding principle. A SDSe membrane is a tension
  surface, not a draped skin. Touches structure only at its
  support points. Free edges are cable-supported and concave
  inward. Applies to every structure type.

engine/PLACEHOLDERS.md
  Single source of truth for inputs that are placeholders for
  the FDM engine and the structural calculation engine. When
  those engines land, open this file and remove the rows.

engine/SPEC_cantilever_hypar.md
  Full specification of the Hypar variant.

---

## 8. Update to PROJECT_STATE.md §6 (Canonical Data)

The MEMBER_SCHEMA in data/structures.py now includes one new
entry not mentioned in PROJECT_STATE.md:

  ("cantilever", "cantilever_hypar"):
    membrane + column + arm + strut + ribs + perimeter cable

PROJECT_STATE.md §6 should be read as if this row were added.

---

## 9. Update to PROJECT_STATE.md §4 (Structure Types)

Cantilever Hypar should be marked as BUILT, not listed only as
an aspirational variant.

Current live structures:

  - Cable Supported Saddle
  - Beam Supported Saddle
  - Cantilever Leaf
  - Cantilever Hypar

---

## 10. What is pending

Not built yet, kept on file:

  - Cantilever Flower
  - Cantilever Cone
  - Cantilever Pyramid
  - Cantilever Bell
  - Cantilever Sail

All five follow the same build pattern as Hypar:
  spec, viewer, workshop, wiring, render branch.

Section 1 cleanup:
  Inside the workshops, Section 1 (Object Shape) currently
  shows unbuilt variants as "coming soon" options. Cleanup is
  pending: either remove them or make them route to the
  correct workshop.

Saddle viewers:
  Standard Saddle and Beam Supported Saddle viewers are
  currently snapshot-based. To be upgraded to live 3D matching
  the Cantilever viewer pattern.

Results page panels:
  Member Schedule, Anchor Reactions, Foundation panel, Export
  DXF / JSON, Save / Load Design.

T&C gate on landing page:
  Planned. One file (ui/terms.py). Covers no-warranty, user
  responsibility, intellectual property, no reverse-
  engineering, data handling, governing law. Plus MyIPO
  copyright notification advice and NDA caution.

FDM engine and structural engine:
  Every placeholder in engine/PLACEHOLDERS.md is waiting for
  these. When they land, the placeholders are removed and the
  engines supply the values.

---

## 11. What is next

Recommended order for the next session:

  1. Pick one Cantilever variant to build next.
     Candidates: Cone, Pyramid, Bell, Sail, Flower.
     Each is a copy of the Hypar pattern.

  2. Or upgrade the two Saddle viewers to live 3D.

  3. Or add the Results page panels (Member Schedule first).

  4. Or add the T&C gate.

Any of these is a bounded task. The repository is in a clean,
committed, stable state as of this addendum.

---

## 12. The state of the repository

As of 2026-09-21 (evening, Malaysian time):

  - Every changed file is committed.
  - The Streamlit app reboots cleanly.
  - The Registration page is tidy.
  - Cantilever Hypar renders correctly in the external
    AI renderer.
  - No outstanding bugs.

Nothing is broken. Nothing is in flight. The project is ready
for the next session to pick up any of the items above.

---

## 13. The Chief's working method (restated)

  - iPhone, GitHub web editor, Streamlit Cloud.
  - No terminal. No local Python.
  - Chunked paste method for files over 300 lines.
  - Complete file replacements, not surgical edits.
  - Commit between chunks when the editor risks being closed.
  - Reboot the Streamlit app after any commit that changes
    runtime files.
  - Honesty. No fabrication.
  - No going around the world in code.

This is inherited from the main PROJECT_STATE.md. Restated here
so the addendum is self-contained.

---

End of addendum.





