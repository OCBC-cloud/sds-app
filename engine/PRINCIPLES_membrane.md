# PRINCIPLES — Membrane Form-Finding

Status: foundational principle. Applies to every structure type.
Date: 2026-09-21.
Supersedes: any earlier wording in individual specs that contradicts this.

---

## 1. The core principle

A SDSe membrane is never a skin draped over the structure.

It is a **tension surface**. Its shape is determined by the pretension
equilibrium between the fabric and its edge cables. The engineer does
not draw the membrane shape. The engine solves for it.

The membrane touches its structural members **only at the support
points** — the corners, or wherever the boundary condition fixes it.

Between those supports, the membrane is a **free span** that finds its
own equilibrium form:

- Every free edge is **cable-supported** and **concave inward**
  toward the membrane centre.
- The surface between the edges is a **saddle** (or the correct
  form-found shape for the given boundary conditions), never a flat
  or arbitrarily-shaped panel.
- The magnitude of the edge concavity and the surface curvature is
  set by the **pretension equilibrium**, not chosen by the user.

This is the way all SDSe structures behave.

---

## 2. The one exception — attach-to-beam

If the user selects **"attach to beam"** instead of **"detached from
beam"** in the alternative selection box, then the beam becomes the
boundary condition for that membrane edge.

In that case:

- The membrane edge follows the beam.
- There is no free cable curve on that edge.
- Concavity on that edge is zero.

This exception must be **explicitly chosen by the user**. The default
is always **detached** (form-found). Detached is the true SDSe form.

---

## 3. Where the principle applies

Every structure type. Every variant. Every viewer. Every future spec.

Saddles, sails, cantilevers, tents, framed structures, portal frames,
and every structure type added in the future.

There is no membrane type in SDSe where the membrane is drawn as a
flat or arbitrarily-shaped panel.

---

## 4. Staged implementation

Full form-finding requires the FDM engine, which is pending.

Until the FDM engine is in place, viewers will:

- Draw membrane surfaces as saddle approximations between the support
  points.
- Draw free edges as concave inward arcs with a **fixed sag fraction
  of 10–15% of edge length**.

These are approximations. They exist to keep the viewer functional
while the engine is being built. Every such approximation is marked
in the code as **TEMPORARY — replace with FDM result**.

When the FDM engine lands, the fixed fractions are replaced by the
solved equilibrium state. The shape of every membrane in every
structure changes to match.

---

## 5. What this principle forbids

- A membrane drawn as a flat panel between supports.
- A membrane edge drawn as a straight line (unless attach-to-beam).
- A membrane surface draped over ribs, purlins, or beams.
- A membrane that touches a structural member anywhere except at
  its support points.
- A user-facing control that lets the user set the membrane shape
  directly, other than the pretension inputs which define the
  target stress state.

---

## 6. Reference from other documents

Every future spec that describes a membrane structure must reference
this document at its head. Any specific dimension in a spec that
contradicts this document is wrong and must be changed.

---

End of principles.





