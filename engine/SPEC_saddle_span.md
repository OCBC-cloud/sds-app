# SDSe - Saddle Span Specification

Internal engineering specification for the Saddle Span structure family.
This document is NOT shown to users. It defines the engine's behaviour.

---

## 1. Overview

Saddle Span is the flagship structure family of SDSe. It covers three
sub-types (Standard, Cantilever, Leaf), each a doubly-curved tensile
membrane supported by a combination of edge beams, ribs, cables, and
(in some sub-types) a central column.

The family is defined by:

- Anti-elastic membrane shape (up in one direction, down in the other)
- Central valley for rainwater drainage
- Edge-supported fabric
- Torsional and bending actions at supports
- Strict silent rules on minimum membrane slope

---

## 2. Sub-types

### 2.1 Standard Saddle Span

Two curved edge beams (arches) supporting a membrane between them.
Ground-anchored at both ends of each beam. No central column.

Typical use: large-span canopies, sports halls, entrance features.

### 2.2 Cantilevered Saddle Span

A uni-pole column rising from a baseplate, connecting to one
convergence point of the two beams. The column continues upward and
arcs across toward the opposite convergence point. The far end is
UNSUPPORTED - the arc holds it in mid-air.

Restriction: structure size <= 6m x 6m.
Base condition: rigid baseplate required (cantilever moment).

Typical use: small sculptural canopies, entrance features.

### 2.3 Leaf Variant

Radial ribs splay outward and upward from a central main beam.
Edge cables connect the outer rib tips. Ribs are spaced at user-chosen
angular intervals. The membrane drapes between ribs and along the main
beam, forming a natural valley under the main beam.

Column: uni-pole or truss, at least CHS 323.8 x 8.
Main beam: single CHS member (arc).
Ribs: single CHS purlins, bolted to main beam via cleat or gusset.

Restriction: structure size <= 6m x 6m (cantilever) OR larger if
supported at far end (per user selection).

Reference case: Chief's 10m x 10m prototype (Section 9).

---

## 3. Structural Elements

### 3.1 All sub-types

- Membrane fabric
- Edge beams OR edge cables (per sub-type)
- Tie-downs (cables or rigid struts)
- Anchors and baseplates
- Joint plates at nodes
- Optional central membrane opening with ring cable

### 3.2 Cantilever-specific

- Uni-pole column (vertical, from baseplate to beam joint)
- Curved arc arm (continues from column top toward far convergence)
- Rigid baseplate at column foot
- No far-end anchors (by definition of cantilever)

### 3.3 Leaf-specific

- Main beam (central arc, single CHS)
- N radial ribs per side (N >= 5, default 7)
- Edge cables (segment cables between rib tips)
- Curved strut from 1/3 of main beam down to column (bracket form)
- Rib-to-main-beam connections (cleat or gusset plate, bolted)
- Rib upward tilt angle (default 20 deg, range 5 deg to 40 deg)

---

## 4. Inputs

### 4.1 Required inputs

Geometry:
- Span (B)
- Width (LAA)
- Rise (A)
- Number of tie-down cable intervals (intervals along each beam)
- Number of anchors (= number of intervals, one per tie-down)
- Rib count per side (Leaf only, min 5, default 7)
- Rib plan angular spacing (Leaf only, default 45 deg)
- Rib upward tilt angle (Leaf only, default 20 deg, range 5-40 deg)

Materials:
- Section family (CHS, SHS, RHS, I-Beam) - user chooses
- Steel grade (S235, S275, S355, S420, S460)
- Fabric type (PVC, PTFE, ETFE and grade)
- Cable material (stainless or galvanised)
- Cable type (6x19, locked coil, spiral) and diameter
- Design standard (EU, MY, UK, CN, US)

Member configuration:
- Member type (single beam, planar truss, 3D space truss)
- Joint type above ground (welded or bolted)
- Joint type at ground (pinned or rigid)

Tie-down system:
- Type: cable (tensioned) or rigid member (strut)
- Vertical angle (default 45 deg)
- Horizontal spread (default 30 deg)

Configuration:
- Membrane-to-frame arrangement (A below, B above, C clamped)
- Cantilever sub-type selection (Standard, Cantilever, Leaf)

### 4.2 Optional inputs with defaults

- Edge beam curve type: parabolic
- Fabric sag percentage: 15
- Steel grade default: S355
- Cable diameter: auto-selected from tension
- Anchor height: 0 (ground level)
- Corrosion protection: galvanised + paint
- Central membrane opening: no
- Ring cable type: same as edge cables
- Column type (Leaf): uni-pole, CHS 323.8 x 8 minimum
- Main beam (Leaf): CHS 168.3 minimum
- Curved strut attachment: at 1/3 of main beam length
- Strut-column joint: pinned or rigid (user selectable)

### 4.3 Conditional inputs

- Temperature load: MANDATORY if span or apex distance > 40m
- Snow load: default 0 (Malaysia); override available
- Central opening area limit: max 1/6 of total roof plan area

---

## 5. Membrane-to-Frame Arrangements

Three configurations supported. User selects before design run.

### 5.1 Option A - Below Frame (default)

- Membrane sags below the ribs and main beam
- Valley forms BELOW the main beam line
- Water flows inward and downward toward the valley
- Beam is a ridge from the fabric's perspective (fabric hangs under it)
- Frame is visible from inside

Default choice. Used for Chief's leaf.

### 5.2 Option B - Above Frame

- Membrane arches over the ribs and main beam
- Ridge forms AT the main beam
- Valleys form between adjacent ribs
- Water flows outward from ridge toward perimeter
- Frame is hidden beneath fabric

### 5.3 Option C - Clamped at Beam

- Membrane is clamped directly to the main beam
- Beam becomes a linear gutter or drainage edge
- Water flows along the beam
- Clamp detail required at every node
- Beam must be checked for torsion (asymmetric fabric pull)

Each option changes:
- Membrane geometry (sag / arch / edge-flat)
- Stress field distribution
- Drainage path
- Beam loading direction and magnitude
- Local detailing requirements

The engine must compute all six consequences for the chosen option.

---

## 6. Structural Checks

### 6.1 Membrane (System A)

- Fabric warp tension <= f_u,warp / gamma_M,fabric
- Fabric weft tension <= f_u,weft / gamma_M,fabric
- Fabric curvature check (anti-elastic form maintained)
- Edge cable tension <= f_u,cable / gamma_M,cable
- Local membrane stress at clamped edges and near rib attachments
- Pre-tension balance across the surface
- Membrane slope check (SILENT RULE - Section 7)

### 6.2 Edge Beams (System D)

- Combined bending + axial interaction: N/N_Rd + M/M_Rd <= 1.0
- In-plane arch buckling
- Out-of-plane buckling
- Lateral-torsional buckling (if applicable)
- Deflection: L/250 typical

### 6.3 Tie-down Cables (System B)

- Cable tension <= f_u,cable / gamma_M,cable
- Anchor uplift resistance
- Cable sag under own weight
- Fatigue (if cyclic loading expected)

### 6.4 Joints and Connections

- Weld strength at beam-cable nodes
- Bolt shear at anchor points
- Bearing at baseplates
- Plate tearing
- Cleat / gusset plate check (Leaf ribs to main beam)
- Curved strut connection to column

### 6.5 Baseplate and Foundation

- Overturning moment (all sub-types)
- Torsion at baseplate (Cantilever and Leaf - governing)
- Baseplate bending stress
- Anchor bolt tension and shear
- Foundation eccentric bearing pressure
- Foundation uplift check
- Combined moment + torsion interaction at base

### 6.6 Cantilever-specific

- Column combined compression + bending
- Arc arm bending + torsion (as it wraps over membrane)
- Tip deflection (L/200 or L/250 depending on code)
- Far-end uplift check (nothing resists it except structure's own stability)
- Rigid baseplate moment capacity

### 6.7 Leaf-specific

- Rib bending + axial (inclined members)
- Rib buckling under compression
- Rib local buckling under torsion
- Main beam torsion
- Rib-to-main-beam joint shear and bearing
- Strut compression + bending (curved strut)
- Strut buckling
- Torsion at column (governing action)
- Rib tip deflection

### 6.8 Central Opening (if present)

- Ring cable tension <= f_u / gamma_M,cable
- Local membrane stress at opening edge
- Opening area check <= 1/6 total roof area
- Ring cable shape maintenance (closed loop)

---

## 6A. Strut Geometry (Leaf Variant)

The Cantilever Leaf has a curved strut that runs from a point at
approximately 1/3 along the main beam down to the uni-pole column.
This strut provides a second support point for the beam and
triangulates the beam-column junction, significantly reducing the
moment transferred to the column base.

### 6A.1 Strut-column joint height

The height at which the strut meets the column is auto-determined
by the system, with user override allowed.

Default rule:
- Joint height = 60 percent of column height
- Valid range: 40 percent to 75 percent of column height
- User can override in the workshop within this range

### 6A.2 Effect of joint height (engineering rationale)

Higher strut-column joint:
- Shorter strut length -> less bending in the strut
- Steeper strut angle -> more of the load in axial compression
- Less eccentricity -> smaller moment transferred to the column
- Smaller baseplate moment -> smaller foundation footprint

Trade-off: if the joint rises too close to the column top, the
strut becomes nearly vertical and loses its bracing role. Hence
the 75 percent upper bound.

### 6A.3 Minimum for adequate bracing

Below 40 percent of column height, the strut angle becomes too
shallow and the bending penalty outweighs the benefit. Designs
below this threshold are flagged.

### 6A.4 Implementation notes

- The workshop exposes "Strut Joint Height (m)" in the Column
  and Spine section, pre-filled with 60 percent of column height.
- The value is passed to the 3D viewer, which draws the strut to
  the correct joint height.
- The value is passed to the engine, which computes forces based
  on the actual strut geometry.
- The value affects the baseplate reaction, which affects the
  preliminary foundation size.

### 6A.5 Reference

This is a design decision made 2026-09-13. It addresses a
structural efficiency gain identified by Chief during review of
the Cantilever Leaf variant. The higher strut joint reduces
moment transfer to the baseplate and foundation, producing a
more economical structure without compromising stability.

---

## 7. Silent Rules (Internal Only)

These rules govern engine behaviour. They are NEVER mentioned in the
user interface, output, report, or bill of quantities.

### 7.1 Tensile Membrane Slope Rule (silent)

Minimum membrane slope required:
- 18 degrees for small exposed surfaces
- 23 degrees for large exposed surfaces

Small / large definition:
- Small: plan area <= 100 m2 OR max dimension <= 15m
- Large: above that

If minimum slope is violated:
- Engine auto-adjusts rib tilt or suggests geometric change
- User sees a generic recommendation without the threshold value
- Design is blocked only if violation is severe

### 7.2 Flutter / Ponding Prevention (silent)

The slope rule exists to prevent:
- Ponding (water pooling on the membrane)
- Flutter (fabric lift under gust)
- Loss of pre-tension under load

Never mentioned to user. The user experiences these as
"the system just knows what works."

### 7.3 Pre-tension Retention (silent)

The engine verifies pre-tension is maintained at all load cases.
Never mentioned to user.

### 7.4 Shape Fidelity Guidance (silent)

For Leaf sub-type, minimum rib count per side is 5. Below this, the
membrane sags too much and the shape stops reading as a leaf.

Never mentioned to user as "shape fidelity." Only as "geometry
recommendation."

---

## 8. Output Schedule

### 8.1 Member Schedule

Every member listed with:
- ID (M1, M2, ...)
- Role (edge beam, main beam, rib, strut, edge cable, tie-down,
        membrane, baseplate)
- Section name
- Material
- Length
- Weight
- Force (kN) - tension positive, compression negative
- Moment (kNm) where applicable
- Utilisation (0.85 = 85%)
- Status (pass / warn / fail)

### 8.2 Joint Schedule

Every connection node listed with:
- Node ID
- Members meeting at node
- Plate size and thickness
- Bolt count and diameter
- Weld size (if welded)
- Base plate dimensions (if ground)

### 8.3 Health Score

Computed from actual utilisation ratios. 100 only when every member
is under 1.0 utilisation. Deducted points per overstress. Aggregated
pass / warn / fail indicator.

### 8.4 Alerts

Generated when:
- Member above 90% utilisation: "engineer review recommended"
- Member above 100% utilisation: "design fails, increase section"
- Member below 10% utilisation: "over-designed, consider smaller section"
- Tip deflection exceeds L/250: "deflection concern"
- Baseplate torsion above limit: silent adjustment applied

### 8.5 Bill of Quantities

Complete itemised BQ:
- Structural steel (weight, section, length)
- Cables (type, diameter, length, weight)
- Membrane fabric (type, area, weight)
- Joints and connections (nr)
- Baseplates and anchors (nr)
- Surface protection (area)

Grouped by category with totals and grand total.

### 8.6 3D View

Rendered with members coloured by utilisation:
- Green: below 75%
- Yellow: 75% to 100%
- Red: above 100%

Toggle visibility of member categories.

### 8.7 Drainage Output

Flow direction indicator only. No drainage hardware designed.
- "Flow direction: inward to central valley"
- "Valley drains at tip"
- Warnings if flow is inconsistent with geometry

---

## 9. Reference Case - Chief's 10m x 10m Leaf Prototype

This is the verification case for the Leaf sub-type. The engine must
reproduce these results.

### 9.1 Geometry

- Column: CHS 323.8 x 8, uni-pole, height 10m from base to beam joint
- Column to leaf tip outreach: 10m
- Longest perpendicular leaf dimension: ~10m
- Leaf plan area: ~80 m2 (~80% of 10m x 10m)
- Beam arm curve radius: ~5m
- Ribs per side: 7 (total 14 ribs + 1 main beam = 15 members)
- Rib plan angular spacing: 45 deg
- Rib upward tilt angle: ~20 deg
- Membrane-to-frame arrangement: Option A (below frame)

### 9.2 Members

- Main beam (central arc): CHS 168.3
- Radial ribs: CHS 168.3 tapering to CHS 76 at outer ties
- Column: CHS 323.8 x 8
- Curved strut: from 1/3 of main beam to column at lower point

### 9.3 Cables

- Edge cables: stainless steel 6x19, 8mm diameter
- Pre-tension: 1 kN/m
- Segment cables between rib tips (one per bay)

### 9.4 Fabric

- PVC Ferrari S702
- Pre-tension: 1 kN/m warp and weft

### 9.5 Loads

- Wind speed: 33.5 m/s (Malaysia)
- gamma_G: 1.2 (favourable, uplift case)
- gamma_Q: 1.4 (original prototype) / 1.5 (MS EN 1990)
- Uplift case with -1.4 wind: governed

### 9.6 Results (Chief's prototype)

- Governing load case: TORSION
- Critical member: a small rib near the column
  (stress concentration at rib-to-main-beam joint close to column)
- Baseplate reaction: large torsional moment
- Foundation required: buried 1200mm deep, base 2500 x 2000mm

### 9.7 Lessons

- The shape translated easily to engineering
- Torsion, not bending, was governing
- Foundation sizing driven by torsion, not gravity
- Dense ribs needed for both shape fidelity and drainage slope
- "Mother Tree" concept emerged: multiple leaves on a tall trunk

---

## 10. Country-Specific Safety Factors

The engine maintains a per-standard factor table.

| Factor | EU (EN) | MY (MS EN) | UK (BS EN) | CN (GB) | US (ASCE) |
|--------|---------|------------|------------|---------|-----------|
| gamma_G | 1.35 | 1.35 | 1.35 | 1.35 | 1.2 |
| gamma_G_fav | 1.0 | 1.0 | 1.0 | 1.0 | 0.9 |
| gamma_Q | 1.5 | 1.5 | 1.5 | 1.4 | 1.6 |
| gamma_M0 | 1.0 | 1.0 | 1.0 | 1.1 | 0.9 |
| gamma_M1 | 1.0 | 1.0 | 1.0 | 1.1 | 0.9 |
| gamma_M2 | 1.25 | 1.2 | 1.25 | 1.25 | 0.75 |
| gamma_M_fabric | 4.0 | 4.0 | 4.0 | 5.0 | 4.0 |
| gamma_M_cable | 1.5 | 1.5 | 1.5 | 1.8 | 1.67 |

Note: MY uses gamma_Q = 1.5 per MS EN 1990.

---

## 11. Concept Ideas (Future Phases)

### 11.1 Mother Tree

A tall vertical trunk (large column) with multiple Leaf sub-structures
cantilevered at different heights in a spiral pattern, growing from
large at the bottom to small at the top.

Requires multi-storey analysis, cumulative torsion calculation, and
a completely different structural system. Separate structure type.

Target phase: 10 or later.

### 11.2 Flower Roof

A central mast with N petals radiating outward, each petal being a
Leaf variant. Ring beam or ring cable connects petal outer tips.
Membrane spans between petals or covers all petals as one fabric.

Approximately 10x the complexity of a single Leaf.
Separate structure type.

Target phase: after Leaf is fully verified.

---

## 12. Engine Module Mapping

The Saddle Span family uses these engines:

- Standard: System A (membrane) + System D (arch edges)
- Cantilever: System A + System D + System B (base torsion)
- Leaf: System A + System B + System C (ribs) + System D (main beam arc)

Recipe file: engine/recipes.py
Function: analyse_saddle_span(params, materials, sub_type)

---

## 13. Verification Plan

### Standard sub-type
- Test: rectangular hypar, uniform tension field
- Reference: biaxial membrane theory
- Pass: <1% difference

### Cantilever sub-type
- Test: single cantilevered arch, UDL
- Reference: cantilever bending + torsion
- Pass: <2% difference

### Leaf sub-type
- Test: Chief's 10m x 10m prototype
- Reference: full Eurocode analysis
- Pass: section sizes match within one size, utilisation within 10%
- Critical check: torsion at baseplate within 5%

---

End of Saddle Span specification.
