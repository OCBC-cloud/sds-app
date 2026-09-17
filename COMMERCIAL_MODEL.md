# SDSe — Commercial Model

Status: PLANNING (not committed to)
Last updated: 2026-09-17
Related: PROJECT_STATE.md

---

## 1. Positioning

SDSe is a mobile-first conceptual design tool for tensile and
curved-beam structures (canopies, sails, saddles, cantilevers).

One-sentence market message:

  "Sketch tensile canopies on your phone. Show your client in 3D.
   Save the job before you leave the site."

What SDSe is NOT:
  - Not a structural analysis engine (yet — Phase C pending)
  - Not competing with RFEM, ixCube, Easy, MPanel
  - Not an engineering-grade FEA tool

What SDSe IS:
  - A conceptual sketch tool for the early stage of design
  - A sales aid for fabricators, contractors, event organisers
  - A mobile-first workflow that no desktop tool offers


## 2. Target Users (in priority order)

1. Canopy FABRICATORS
   - Need to close deals on site
   - Need to show clients a 3D view quickly
   - Pain: desktop tools are too slow for sales calls

2. Event Organisers and RENTAL Companies
   - Need temporary structures sketched fast
   - Need visual + rough quantities for quoting

3. Architects and Engineers (small firms)
   - Need early-stage shape exploration
   - Need to communicate concept before full analysis

4. Business Runners (F&B, retail, hospitality)
   - Want custom shade structures
   - Need to see options before commissioning

5. Students and Educators
   - Learning tensile and membrane structures
   - Free tier serves this group


## 3. Pricing Tiers

### Tier 1 — Free (Sketch)
Target: first-time users, students, casual testers.

Includes:
  - Full 3D design studio (all 8 structure types, all variants)
  - All arrangements (single, double, multiple, tree_stack, tiered_helix)
  - Full workshop with all geometry controls
  - Full 3D viewer (rotate, zoom, pan)
  - Watermarked screenshots

Limits:
  - Max 3 saved projects
  - No DXF export
  - No JSON export
  - No PDF report
  - No BQ (Bill of Quantities)

Price: $0

### Tier 2 — Pro (Design & Export)
Target: freelance architects, engineers, small fabricators, individual contractors.

Includes everything in Free, PLUS:
  - Unlimited saved projects
  - DXF export (CAD integration)
  - JSON export (cross-device save/load)
  - PDF report (3D views, member schedule, rough quantities)
  - No watermark
  - Cloud sync (projects saved to account)
  - Priority email support

Price: $29 / month  OR  $290 / year (2 months free)

Estimated conversion from Free: 3% to 8%

### Tier 3 — Studio (Team & Commercial)
Target: canopy fabricators, rental companies, event organisers, firms.

Includes everything in Pro, PLUS:
  - Team collaboration (up to 10 users per seat license)
  - Branded reports (company logo on PDFs, BQ, screenshots)
  - Standard library (materials, sections, fabric types pre-loaded)
  - Project templates (save standard designs as reusable)
  - Read-only API (pull project data into own systems)
  - BQ with pricing (user enters unit rates, app prices the BQ)
  - Client presentation mode (full-screen 3D, client-friendly controls)
  - Priority support + onboarding call

Price: $149 / month  OR  $1,490 / year per seat

Estimated conversion from Free: 0.5% to 2%


## 4. Revenue Projection (18 months post-launch)

Assumptions:
  - Focus on fabricators + event organisers first
  - Word-of-mouth + light paid marketing
  - Free-to-Pro conversion 5%
  - Free-to-Studio conversion 0.5%

| Metric                     | Conservative | Realistic | Optimistic |
|----------------------------|--------------|-----------|------------|
| Total downloads            | 5,000        | 20,000    | 60,000     |
| Pro subscribers (5%)       | 250          | 1,000     | 3,000      |
| Studio seats (0.5%)        | 25           | 100       | 300        |
| Monthly Pro revenue        | $7,250       | $29,000   | $87,000    |
| Monthly Studio revenue     | $3,725       | $14,900   | $44,700    |
| Monthly total              | $11,000      | $44,000   | $132,000   |
| Annual total               | ~$130,000    | ~$525,000 | ~$1,580,000|


## 5. Additional Revenue Streams (after main tiers work)

### Marketplace of standard designs
  - Fabricators upload standard canopy templates
  - Other users pay $5 to $50 per template
  - Platform commission: 20% to 30%
  - Low delivery cost, high margin

### White-label licensing
  - Fabricator's branded version of SDSe for their sales reps
  - Setup fee: $5,000
  - Monthly: $500
  - B2B target

### Training and certification
  - "Certified SDSe Designer" course
  - Price: $199
  - Videos, exercises, exam, certificate
  - High margin, low delivery cost


## 6. Prerequisites Before Launch

The app must have these before paid tiers go live:

  1. User accounts (authentication, profile, project list)
  2. Cloud project storage (projects saved to account)
  3. Save / Load JSON (offline-friendly)
  4. DXF export
  5. Basic PDF report

Estimated development time: 2 to 4 months of focused work.

After that: launch Free + Pro tiers. Studio tier follows later.


## 7. Competitive Landscape (summary)

Direct phone-app competitors: NONE found for tensile/curved structures.

Adjacent phone apps (structural, but general):
  - SkyCiv Mobile (beam, truss, frame analysis)
  - BeamDesign (FEM, 1D frames)

Desktop / browser competitors (heavy):
  - Dlubal RFEM (with RF-FORM-FINDING)
  - ixCube 4-10 (membrane specialist)
  - Easy (tensile structures)
  - MPanel (AutoCAD/Rhino plugin)
  - BATS (Grasshopper plugin)
  - Formfinder (conceptual, Vienna-based)

SDSe's white space:
  Mobile-first. Conceptual. Tensile-focused. No desktop equivalent
  offers the same on-site sketching workflow.


## 8. Marketing Channels (initial)

  - LinkedIn (fabricators, architects, engineers)
  - YouTube (short demos: "design a canopy in 3 minutes")
  - Industry forums (tensile structure communities)
  - Trade shows (ASEAN, Malaysia, Singapore, Indonesia)
  - Word of mouth (fabricator to fabricator)


## 9. Open Questions

  - Should the Free tier include DXF export at low resolution?
  - Should Pro be seat-based or per-user?
  - What happens to Pro projects if user downgrades?
  - Is Studio pricing per seat or per company?
  - Do we offer regional pricing (SE Asia discount)?

These are decisions for after user testing and first revenue.


## 10. Document History

Created: 2026-09-17
  - Initial commercial model documented
  - Three tiers defined: Free, Pro, Studio
  - Revenue projection drafted
  - Prerequisites list defined
  - Competitive landscape noted
