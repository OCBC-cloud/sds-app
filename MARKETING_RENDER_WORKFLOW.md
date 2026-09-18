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

## 11. Legal & Disclaimer

### 11.1 Position on Third-Party Renderers

SDSe provides the structure snapshot and a personalised prompt. The
user takes these to a third-party image renderer of their choice.
SDSe does not generate images. SDSe does not send images anywhere.
SDSe does not endorse or partner with any renderer.

This separation is deliberate. It keeps the SDSe system light, keeps
the user in control, and avoids any appearance of a partnership that
does not exist.

### 11.2 Renderers Under Consideration

The following renderers may be offered in the SDSe interface. They
are listed as possible options for the user to consider. Each opens
in a new browser tab. SDSe is not affiliated with any of them.

  - Bing Image Creator
    https://www.bing.com/create

  - Midjourney
    https://www.midjourney.com

  - Adobe Firefly
    https://firefly.adobe.com

  - DALL-E (via ChatGPT)
    https://chat.openai.com

  - Stable Diffusion (via Replicate)
    https://replicate.com

The list may change over time. Users are free to use any renderer
they prefer. The SDSe interface does not require the use of any
specific external service.

### 11.3 Disclaimer Text (to appear in the app)

The following text should be displayed in the Render section of the
SDSe interface, directly below the renderer links:

  ---

  SDSe is not affiliated with any of the renderers listed above.
  These are third-party tools offered for your consideration.
  Each opens in a new browser tab. Use of any renderer is subject
  to that renderer's own terms of service.

  Before using any rendered image for commercial purposes, please
  check the terms of the renderer you used. Not all renderers
  permit commercial use of generated images.

  AI-generated images may have uncertain copyright status. Consult
  a legal professional before using them in commercial material.

  ---

### 11.4 Why This Wording

The disclaimer is written to:

  - State clearly that SDSe is not affiliated with the renderers.
  - Present the renderers as options for the user to consider,
    not as recommendations or endorsements.
  - Remind the user of their own responsibility regarding the
    renderer's terms and commercial use.
  - Note the uncertain copyright status of AI-generated images
    without alarming the user.

The tone is gentle and factual. It informs without creating fear.

### 11.5 What the SDSe App Must Not Do

To remain clear of any partnership implication, the SDSe app must
not:

  - Display any renderer's logo. Only plain text names.
  - Say "powered by", "in partnership with", or "recommended by"
    any renderer.
  - Auto-send images to any renderer on the user's behalf.
  - Claim that the app generates images. It prepares snapshot and
    prompt. The user and the external renderer do the rest.
  - Store the user's images on any renderer's server.

If any of these are added later, the legal position changes.
The design decision documented here must be revisited first.

### 11.6 Malaysian Context (Note Only)

As of 2026-09-18, Malaysian copyright law does not have settled
rules on AI-generated works. There is no case law in Malaysia on
whether AI-generated images can be copyrighted.

This does not affect the SDSe app's design, but it is a reminder
that AI-related legal territory is still developing. The disclaimer
text in Section 11.3 is written defensively to account for this
uncertainty.

### 11.7 Document History (this section)

Added: 2026-09-18
  - Legal and disclaimer section added
  - Renderer list documented with plain links
  - Disclaimer text drafted in gentle, factual tone
  - Clear separation between SDSe and any renderer established
