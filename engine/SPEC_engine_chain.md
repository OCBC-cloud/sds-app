# SPEC — Engine Chain and Catalogues

Date: 2026-09-22.
Status: design spec. Not yet built.
Purpose: record the architecture of the SDSe calculation
engine — seven links, each tested against a known answer —
and the data catalogues that Links 4 to 6 depend on.

Related:
  engine/MEMBRANE_GUIDE.md
  engine/PLACEHOLDERS.md

---

## 1. The principle

SDSe is not built on one engine. It is built on a chain.

Each link in the chain has one job, one mathematical method,
and one test against a known answer. A link is trusted only
after it passes its test. Until then, its output is a
placeholder.

The chain:

  SHAPE → LOADS → FORCES → SIZES → QUANTITIES → REPORT

Every link feeds the next. A weak link weakens everything
downstream. The chain is only as reliable as its weakest link.

---

## 2. Link 1 — SHAPE (form-finding)

Purpose:
  Find the shape a membrane takes at equilibrium under
  prestress and its own weight.

Method:
  FDM (Force Density Method) first.
  NFDM (Natural Force Density Method) for the final.

Why:
  Both are the industry standard. Published, benchmarked,
  used by Easy, ixCube, RFEM's form-finding. Linear in the
  free-node coordinates — a sparse linear solve on the phone.

Where it runs:
  On the device. Milliseconds for a 100-node mesh.

Tested against:
  - Flat mesh, uniform prestress. Expected: stays flat.
  - Catenoid. Expected: matches the analytical minimal
    surface.
  - Asymmetric four-point hypar. Expected: saddles with no
    artificial symmetry.
  - Cone between a mast and a ring. Expected: forms a cone.

What it feeds:
  Link 3 (forces). Also the viewer, once its output is
  trustworthy.

---

## 3. Link 2 — LOADS

Purpose:
  Build the design load cases from the site and the code.

Method:
  The national annex of the applicable code.
  Wind — MS EN 1991-1-4 for Malaysia; EN 1991-1-4 with the
  relevant national annex elsewhere.
  Snow — EN 1991-1-3 (if applicable).
  Live — EN 1991-1-1.
  Seismic — EN 1998 (if applicable).

Why:
  The code says what to do. There is no "smart" way to apply
  wind. There is only the correct one, per the code.

Where it runs:
  On the device. Table lookups and simple formulas.

Tested against:
  - Each code's own worked examples.
  - Independent checks against published design examples.

What it feeds:
  Link 3 (forces).

---

## 4. Link 3 — FORCES (structural analysis)

Purpose:
  Take the form-found shape, apply the loads, find the new
  equilibrium, and give member forces.

Method:
  Three layers, in order of fidelity.

  Layer 3a — Linear cable-net analysis.
    Newton-Raphson on a small mesh.
    Fast. Correct for cables and light membranes.
    Already present in physics_engine.py.

  Layer 3b — Geometrically nonlinear membrane FE.
    Full membrane element formulation.
    Handles prestress, large deformation, wind uplift.
    Industry standard.
    Methods: dynamic relaxation, updated reference
    strategy, or standard Newton-Raphson on the full
    nonlinear residual.

  Layer 3c — Coupled analysis.
    Membrane + edge cables + beams + supports in one model.

Why:
  Linear analysis is wrong for tensile membranes. They are
  flexible; small loads cause large displacements. Nonlinear
  analysis is required. There is no cheaper method that is
  honest.

Where it runs:
  Layer 3a — on the device.
  Layer 3b — on the cloud.
  Layer 3c — on the cloud.

Tested against:
  - Layer 3a: 3D extension of the catenary, then a saddle
    with known analytical solution, then a simple cone.
  - Layer 3b: a flat prestressed panel with a known closed-
    form solution.
  - Layer 3c: a simple structure with an independent
    verification.

What it feeds:
  Link 4 (member design).

---

## 5. Link 4 — SIZES (member design)

Purpose:
  From member forces, choose the smallest safe section.

Method:
  The design code, applied member by member.
  Steel — EN 1993-1-1. Resistance, buckling, interaction.
  Cables — EN 1993-1-11 or the manufacturer's capacity
    curves.
  Fabric — biaxial stress state checked against the fabric's
    code capacity.

Why:
  The code says what to do. There is no "smart" way to size
  a beam. There is only the correct check.

Where it runs:
  On the device. A search through the section catalogue,
  checking each candidate against the code.

Depends on:
  The steel section catalogue (§8 below), the cable
  catalogue, and the fabric catalogue.

Tested against:
  - Each code's own worked examples.
  - A hand-checked design of a small steel beam under known
    loading.

What it feeds:
  Link 5 (quantities) and Link 6 (report).

---

## 6. Link 5 — QUANTITIES (BQ)

Purpose:
  Take the final geometry and member list, produce the
  bill of quantities.

Method:
  Arithmetic.
  Steel length × unit weight per metre = weight.
  Cable length × unit weight = weight.
  Membrane flattened area × unit weight per m² = weight.
  Hardware: counts × unit weight.

Why:
  The geometry is already known. The BQ is bookkeeping.

Where it runs:
  On the device. Trivial.

Depends on:
  The catalogues for unit weights and mass per m².

Tested against:
  - A hand count of a small structure.

What it feeds:
  Link 6 (report) and the user's quotation.

---

## 7. Link 6 — REPORT

Purpose:
  Assemble everything into a client-ready document.

Method:
  PDF or HTML assembly. No computation.

Where it runs:
  On the device or the cloud.

Tested against:
  - A manually assembled report for a small structure.

---

## 8. The catalogues

The catalogues are not a link in the chain. They are the
data that Links 4, 5, and 6 depend on.

Without catalogues, member design cannot run, the BQ cannot
produce weights, and the report cannot cite sections.

### 8.1 Steel section catalogue

File: data/catalogues/steel_sections.csv

Fields per row:
  name              e.g. "CHS 168.3 x 7.1"
  family            CHS, SHS, RHS, I-beam, angle, flat bar
  dimensions        in a compact form: 168.3x7.1
  area_mm2
  iy_mm4            second moment of area, y-axis
  iz_mm4            second moment of area, z-axis
  ry_mm             radius of gyration, y
  rz_mm             radius of gyration, z
  wel_y_mm3         elastic section modulus, y
  wel_z_mm3         elastic section modulus, z
  wpl_y_mm3         plastic section modulus, y
  wpl_z_mm3         plastic section modulus, z
  mass_kg_m
  grades            comma-separated list of grades available

### 8.2 Cable catalogue

File: data/catalogues/cables.csv

Fields per row:
  name              e.g. "6x19 IWRC Galv 12 mm"
  construction      6x19, 6x36, locked coil, spiral
  diameter_mm
  mbl_kN            minimum breaking load
  mass_kg_m
  EA_N              axial stiffness
  material          galvanised, stainless

### 8.3 Fabric catalogue

File: data/catalogues/fabrics.csv

Fields per row:
  name              e.g. "PVDF Type III 1050"
  type              PVDF, PTFE, ETFE, PVC
  grade             Type I, II, III, IV, V
  mass_g_m2
  warp_strength_kn_m
  weft_strength_kn_m
  warp_modulus_kn_m
  weft_modulus_kn_m
  fire_rating
  translucency_pct

### 8.4 Hardware catalogue

File: data/catalogues/hardware.csv
Fields to be decided when the BQ engine is built.

### 8.5 Loading

A small Python module data/catalogue_loader.py reads each
CSV and returns a list of dicts.

The rest of the app asks the loader for a section by name,
or for a list of available sections, or for the mass per
metre of a chosen section. It never reads the CSV directly.

### 8.6 Extensibility

A user can add a section, a cable, or a fabric by editing
the CSV in a text editor or spreadsheet. No code change. No
restart needed beyond a page reload.

This is deliberate. A fabricator who stocks a particular
section can add it. A student with a manufacturer's
datasheet can add it. The catalogue grows with the users.

---

## 9. Build order

  1. FDM form-finding engine.
     Test against catenoid, flat mesh, hypar.
  2. NFDM upgrade.
     Test against the same benchmarks.
  3. Load library — MS EN and EN.
     Test against code examples.
  4. 3D nonlinear cable-net analysis (extension of
     physics_engine.py).
     Test against a saddle with known analytical solution.
  5. Membrane FE analysis — on the cloud.
     Test against a flat prestressed panel.
  6. Steel section catalogue.
     First 20-30 CHS sections, then SHS, RHS, I-beams.
  7. Cable catalogue.
     First the 6x19 galvanised range, then stainless and
     locked coil.
  8. Fabric catalogue.
     First the main PVDF and PTFE types.
  9. Member design module.
     Test against code examples.
 10. Foundation sizing.
     Test against a textbook footing.
 11. BQ engine.
     Test against a hand count.
 12. Report module.
     Test against a manual assembly.

---

## 10. Where each link runs

  On the device:
    Link 1 (FDM/NFDM)
    Link 2 (loads)
    Link 3a (linear cable-net)
    Link 4 (member design)
    Link 5 (BQ)
    Link 6 (report)
    The catalogues

  On the cloud:
    Link 3b (membrane FE)
    Link 3c (coupled analysis)

The device is the fast thought engine. The cloud is the deep
analysis engine. Both feed the same chain.

---

## 11. What this means for the app

The app has been built with placeholders in the workshops.
Every placeholder waits for one of these links to exist.

When a link lands, its placeholders are removed:

  - Membrane edge sag slider → replaced by FDM result.
  - Column radius → replaced by member design.
  - Arm arc radius → replaced by member design.
  - Rib curve radius → replaced by member design.

The rest of the app does not change. It reads the same
session state, calls the same viewers, and displays the same
results — but the values they receive come from real
calculations, not placeholder inputs.

That is the payoff of the placeholder document: the day a
link lands, we know exactly what to remove and what to
replace.

---

## 12. What this document does not cover

  - The exact implementation of each link. Each link will
    have its own spec when built.
  - The exact format of every catalogue field. Refined when
    each catalogue is built.
  - The exact cloud architecture. Decided when Link 3b is
    built.

---

## 13. References

  Schek, H.-J. (1974). The force density method for form-
    finding and computation of general networks.

  Pauletti, R.M.O. & Pimenta, P.M. (2008). The natural force
    density method for the form finding of three-dimensional
    networks.

  Bletzinger, K.-U. & Ramm, E. The updated reference strategy
    for the form finding of prestressed membrane structures.

  EN 1990, EN 1991 (all parts), EN 1993 (all parts),
    EN 1997, with national annexes as applicable.

---

End of spec.





