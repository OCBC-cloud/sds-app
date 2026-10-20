# SDSe — Commercial Model

Status: PLANNING (not committed to)
Last updated: 2026-10-20
Related: PROJECT_STATE.md, UI_ARCHITECTURE.md

---

## 1. Positioning

SDSe is a mobile-first conceptual design and visualization tool for tensile and curved-beam structures (canopies, sails, saddles, cantilevers). 

One-sentence market message:
  "The first CAD-quality tensile design studio that fits in your pocket. Sketch tensile canopies on your phone, show your client in 3D, and save the job before you leave the site."

What SDSe is NOT:
  - A desktop replacement for engineering-grade FEA tools (SAP2000, ETABS, Dlubal RFEM).
  - A fabrication detailing tool (like MPanel or ixCube).
  - A plugin requiring Rhino/Grasshopper.

What SDSe IS:
  - A mobile-native conceptual sketch and form-finding tool.
  - A sales aid for fabricators, contractors, and event organizers.
  - The only platform offering the specific combination of anisotropic FDM, nonlinear refinement, and a guided mobile UI.

## 2. Target Users (in priority order)

1. Canopy FABRICATORS & Contractors
   - Need to close deals on site.
   - Need to show clients a 3D view quickly.
   - Pain: Desktop tools are too slow or too complex for a sales call.

2. Event Organisers and RENTAL Companies
   - Need temporary structures sketched fast.
   - Need visual + rough quantities for quoting.

3. Architects and Engineers (small firms)
   - Need early-stage shape exploration.
   - Need to communicate the concept and the "bow" before full analysis.

4. Business Runners (F&B, retail, hospitality)
   - Want custom shade structures.
   - Need to see options before commissioning.

5. Students and Educators
   - Learning tensile and membrane structures.
   - Free tier serves this group.

## 3. Pricing Tiers

### Tier 1 — Free (Sketch)
Target: First-time users, students, casual testers.

Includes:
  - Full 3D design studio (all structure types).
  - Full workshop with all geometry controls.
  - Full 3D viewer (rotate, zoom, pan).
  - Watermarked screenshots.

Limits:
  - Max 3 saved projects.
  - No DXF export.
  - No JSON export.
  - No PDF report.
  - No BQ (Bill of Quantities).
  - Seed Schedule edits are locked.

Price: $0

### Tier 2 — Pro (Design & Export)
Target: Freelance architects, engineers, small fabricators, individual contractors.

Includes everything in Free, PLUS:
  - Unlimited saved projects.
  - Element Seed Schedule (unlocks saving edits, custom beam sections, custom cable pretensions).
  - DXF export (CAD integration).
  - JSON export (cross-device save/load).
  - PDF report (3D views, member schedule, rough quantities).
  - No watermark.
  - Cloud sync (projects saved to account).
  - Priority email support.

Price: $39 / month  OR  $390 / year (2 months free)
Estimated conversion from Free: 3% to 8%

### Tier 3 — Studio (Team & Commercial)
Target: Canopy fabricators, rental companies, event organizers, firms.

Includes everything in Pro, PLUS:
  - Team collaboration (up to 10 users per seat license).
  - Branded reports (company logo on PDFs, BQ, screenshots).
  - Standard library (materials, sections, fabric types pre-loaded).
  - Project templates (save standard designs as reusable).
  - Read-only API (pull project data into own systems).
  - BQ with pricing (user enters unit rates, app prices the BQ).
  - Client presentation mode (full-screen 3D, client-friendly controls).
  - Priority support + onboarding call.

Price: $149 / month  OR  $1,490 / year per seat
Estimated conversion from Free: 0.5% to 2%

## 4. Revenue Projection (18 months post-launch)

Assumptions:
  - Focus on fabricators + event organizers first.
  - Word-of-mouth + light paid marketing.
  - Free-to-Pro conversion 5% (based on the "time saved on site" value proposition).
  - Free-to-Studio conversion 0.5%.

| Metric                     | Conservative | Realistic | Optimistic |
|----------------------------|--------------|-----------|------------|
| Total downloads            | 5,000        | 20,000    | 60,000     |
| Pro subscribers (5%)       | 250          | 1,000     | 3,000      |
| Studio seats (0.5%)        | 25           | 100       | 300        |
| Monthly Pro revenue        | $9,750       | $39,000   | $117,000   |
| Monthly Studio revenue     | $3,725       | $14,900   | $44,700    |
| Monthly total              | $13,475      | $53,900   | $161,700   |
| Annual total               | ~$161,000    | ~$646,000 | ~$1,940,000|

## 5. Additional Revenue Streams (after main tiers work)

### Marketplace of standard designs
  - Fabricators upload standard canopy templates.
  - Other users pay $5 to $50 per template.
  - Platform commission: 20% to 30%.
  - Low delivery cost, high margin.

### White-label licensing
  - Fabricator's branded version of SDSe for their sales reps.
  - Setup fee: $5,000.
  - Monthly: $500.
  - B2B target.

### Training and certification
  - "Certified SDSe Designer" course.
  - Price: $199.
  - Videos, exercises, exam, certificate.
  - High margin, low delivery cost.

## 6. Prerequisites Before Paid Launch

The app must have these before paid tiers go live:

  1. User accounts (authentication, profile, project list).
  2. Cloud project storage (projects saved to account).
  3. Save / Load JSON (offline-friendly).
  4. DXF export.
  5. Basic PDF report.
  6. Element Seed Schedule persistence (saving edits to session/cloud).

Estimated development time: 2 to 4 months of focused work.
After that: launch Free + Pro tiers. Studio tier follows later.

## 7. Competitive Landscape (Deep Search Summary)

Direct phone-app competitors: NONE found for tensile/curved structures. 
(Note: A Stanford 2011 iPad proof-of-concept for membrane form-finding existed, but it was never commercialized).

Adjacent phone apps (structural, but general):
  - SkyCiv Mobile (beam, truss, frame analysis).
  - BeamDesign (FEM, 1D frames).

Desktop / browser competitors (heavy):
  - Dlubal RFEM (with RF-FORM-FINDING) — Desktop, quote-only, ~$1,000-$3,000+/yr.
  - SAP2000 / ETABS — Desktop, quote-only, thousands per year.
  - ixCube 4-10 — Membrane specialist, desktop.
  - Easy — Tensile structures, desktop.
  - MPanel — AutoCAD/Rhino plugin.
  - Rhino + Grasshopper (Kangaroo, K2Engineering) — Requires desktop, license, and scripting.
  - Formfinder — Conceptual, desktop (Vienna-based).

SDSe's white space:
  Mobile-first. Conceptual. Tensile-focused. No desktop equivalent offers the same on-site sketching workflow, and no mobile app offers the physics-backed form-finding and visualization.

## 8. Marketing Channels (initial)

  - LinkedIn (fabricators, architects, engineers).
  - YouTube (short demos: "design a canopy in 3 minutes").
  - Industry forums (tensile structure communities).
  - Trade shows (ASEAN, Malaysia, Singapore, Indonesia).
  - Word of mouth (fabricator to fabricator).

## 9. Open Questions

  - Should the Free tier include DXF export at low resolution?
  - Should Pro be seat-based or per-user?
  - What happens to Pro projects if user downgrades?
  - Is Studio pricing per seat or per company?
  - Do we offer regional pricing (SE Asia discount)?

These are decisions for after user testing and first revenue.

## 10. Document History

Created: 2026-09-17
  - Initial commercial model documented.
  - Three tiers defined: Free, Pro, Studio.
  - Revenue projection drafted.
  - Prerequisites list defined.
  - Competitive landscape noted.

Updated: 2026-10-20
  - Integrated deep search findings (no mobile competitors, desktop tools are the benchmark).
  - Adjusted Pro tier price to $39/month.
  - Highlighted "Element Seed Schedule" as a Pro feature.
  - Refined revenue projections based on higher value proposition.
