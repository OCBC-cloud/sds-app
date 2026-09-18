# SDSe — Marketing Render Workflow

Status: PLANNED (design documented, not yet built)
Created: 2026-09-18
Related: PROJECT_STATE.md, COMMERCIAL_MODEL.md

---

## 1. Purpose

Give users a way to produce beautiful, marketing-ready images of
their structures — without bloating the SDSe app with AI models or
API dependencies.

The app prepares the snapshot and the prompt. The user takes them to
an external image renderer. The user brings the result back. The
external tool is called, used, released. The SDSe system stays light.

This honours the SDS Constitution:

  "If we need some tools we will call and use it in our system and
   after finishing our job we will release it to make sure our
   system remains light."


## 2. The User Workflow (Version 1)

In the 3D viewer, a new section titled "Render This Structure"
contains the following steps:

  1. USER TUNES THE VIEW
     Rotate, zoom, position the structure in the 3D viewer.

  2. USER TAPS "CAPTURE CURRENT VIEW"
     The app captures the current Plotly view as a PNG snapshot.
     The snapshot is offered as a download.

  3. USER TAPS "COPY PROMPT"
     The app prepares a prompt (see Section 4) personalised with the
     user's structure parameters (type, variant, arrangement, key
     dimensions). The prompt is copied to the clipboard.

  4. USER OPENS AN EXTERNAL RENDERER
     Buttons provided:
       - Open Bing Image Creator
       - Open Midjourney
       - Open DALL-E
     Each opens in a new browser tab.

  5. USER PASTES SNAPSHOT AND PROMPT
     The user pastes the downloaded snapshot and the copied prompt
     into the external renderer. The renderer generates 1-4 images.

  6. USER SELECTS AND DOWNLOADS THE BEST IMAGE
     User picks the best image and downloads it.

  7. USER UPLOADS BACK TO SDSe
     A st.file_uploader accepts the rendered image.

  8. APP DISPLAYS AND OFFERS DOWNLOAD
     The rendered image is displayed. A download button lets the
     user save it locally.

  9. USER STORES LOCALLY
     The rendered image lives on the user's device. In a later
     version, it can be linked to a project and stored in cloud.


## 3. What Is Feasible (Honest Assessment)

| Step                            | Feasible? | Notes                      |
|---------------------------------|-----------|----------------------------|
| Capture 3D view as image        | YES       | Plotly to_image()          |
| Prepare prompt                  | YES       | Python strings             |
| Copy prompt to clipboard        | PARTLY    | st.code() + manual copy    |
| Open external tool via link     | YES       | Simple anchor tag          |
| User pastes into external tool  | MANUAL    | User does this             |
| User uploads rendered image     | YES       | st.file_uploader           |
| Display rendered image          | YES       | st.image()                 |
| Download rendered image         | YES       | st.download_button()       |
| Permanent cloud storage         | LATER     | Requires Phase 2 storage   |


## 4. Prompt Templates

These prompts are stored in `engine/render_prompts.py` (new file).
They are formatted with the user's structure parameters before
being shown to the user.

### Template A — Public Garden Scene

Photorealistic architectural photograph of an organic spiral
tensile canopy structure. Central green steel column with yellow
bud joints, red curved steel spines radiating outward, translucent
white fabric membrane stretched over each leaf-shaped segment,
arranged in a tiered helix climbing up the column. Structure placed
in a lush public garden at golden hour. Green trees, flowerbeds,
stone pathways, small water feature reflecting the canopy. People
walking underneath the structure. Warm late afternoon sunlight,
soft shadows, wide-angle architectural photography, extremely
detailed, shot on Canon EOS R5, 24mm lens, f/8, ISO 100.

### Template B — Monumental Square Scene

Photorealistic architectural photograph of an organic spiral
tensile canopy structure as the centerpiece of a modern urban
plaza. Central green steel column with yellow bud joints, red
curved steel spines, translucent white fabric membranes in a
tiered helix formation. Surrounding plaza with stone paving,
modern glass buildings in background, dusk lighting with the
canopy illuminated from below, pedestrians walking, city skyline
visible. Dramatic architectural photography, blue hour, wide angle.

### Template C — Event Venue Scene

Photorealistic photograph of an organic spiral tensile canopy
structure over an elegant outdoor event space. Central green
steel column, red curved spines, white fabric membranes in helix
formation. Underneath: round tables with white linens, string
lights, guests at a wedding reception. Evening setting, warm
golden lighting from the canopy, romantic atmosphere. Shot on
Canon EOS R5, 35mm lens, f/4.

### Template D — Retail / Hospitality Scene

Photorealistic photograph of an organic spiral tensile canopy
structure shading an outdoor cafe. Central green steel column,
red curved spines, white fabric membranes in helix formation.
Beneath: wooden tables, coffee cups, customers seated. Sunny
afternoon, dappled light through fabric, modern hospitality
setting, shallow depth of field, shot on Canon EOS R5, 50mm
lens, f/2.8.

### Template E — Saddle Span — Park Setting

Photorealistic architectural photograph of a saddle-shaped tensile
membrane structure spanning between two anchor points in a park.
White fabric, gentle double curvature, cables visible at edges.
Surrounded by green lawns, stone paving, trees. Mid-afternoon
sunlight, wide angle, architectural photography, extremely detailed.

### Template F — Uni-Pole Tensile Roof — Stadium Entrance

Photorealistic architectural photograph of a single-mast tensile
roof structure covering a stadium entrance. Central steel mast,
radial cables, white fabric membrane in a conical shape. Crowds
of people walking underneath, stadium facade in background, clear
sky. Wide angle architectural photography, dramatic scale.


## 5. Personalisation Rules

Before displaying a prompt, personalise it with the user's data:

  - Structure type and variant (e.g. "Cantilever Leaf")
  - Number of leaves or spans (e.g. "6 leaves")
  - Arrangement (e.g. "tiered helix" or "single")
  - Column height in metres
  - Outreach in metres

Example inserted sentence:

  "The structure is a Cantilever Leaf with 6 leaves arranged in a
   tiered helix, column height 4 metres, outreach 5 metres."

This sentence is inserted after the opening line of each template.


## 6. Storage Plan (Version 1 vs Version 2)

### Version 1 — Session-only
  - Rendered image displayed in the viewer.
  - Download button lets the user save it locally.
  - No permanent cloud storage.
  - Nothing added to the repository.
  - The app stays light.

### Version 2 — Later, with user accounts
  - Rendered images stored in the user's account.
  - Linked to their project.
  - Auto-used as Studio tile previews.
  - Included in "Generate marketing pack" exports.
  - Studio-tier users: company logo watermarked on renders.


## 7. Why This Respects the SDS Constitution

Call:    The app prepares the snapshot and prompt.
Use:     The user takes them to the external renderer.
Release: The external tool is closed after use.
Light:   The app never stores AI models, never pays for API
         calls, never becomes dependent on external services.

The tool is called. Used. Released. The system stays light.


## 8. Competitive Advantage

Most AI-hyped apps bundle generation into the product and become
bloated. SDSe stays disciplined — the value is in the structure
design, not the image generation.

The user gets:
  - Beautiful marketing images
  - No subscription to extra AI services
  - Full control over the renderer they use
  - No vendor lock-in

This is a genuine differentiator. It is also a selling point for
the app store listing.


## 9. Implementation Phases

### Phase 1 — Design documentation
  - This document.
  - Prompts saved as templates.
  - No code changes yet.

### Phase 2 — Basic workflow (Version 1)
  - New "Render This Structure" section in the 3D viewer.
  - Capture button (Plotly to_image).
  - Prompt display and copy.
  - External tool links.
  - Upload and display of the rendered image.
  - Download button.
  - No permanent storage.
  Estimated: 1 to 2 sessions.

### Phase 3 — Enhanced workflow (Version 2)
  - User accounts.
  - Cloud storage of renders.
  - Auto-link to projects.
  - Studio tile previews use the renders.
  - "Generate marketing pack" export.
  Estimated: after Phase 2 of the main app roadmap.


## 10. Document History

Created: 2026-09-18
  - Initial design documented
  - Five scene templates drafted
  - Feasibility assessed
  - Storage plan defined (session vs cloud)
  - Constitution alignment noted
  - Three-phase implementation plan drafted
