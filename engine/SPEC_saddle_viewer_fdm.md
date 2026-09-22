# SPEC — Saddle Viewer Upgrade to FDM Form-Finding

Date: 2026-09-22.
Status: design spec. Not yet built.
Purpose: replace the placeholder membrane in the Cable Supported
Saddle viewer with a form-found surface produced by the FDM
kernel (engine/form_finding.py).

Related:
  engine/MEMBRANE_GUIDE.md
  engine/SPEC_engine_chain.md
  engine/form_finding.py
  viewers/figures/standard_saddle.py

---

## 1. Why

The current Cable Supported Saddle viewer draws the membrane as
a bilinear patch between the two curved beams, with a small
sag across the width. This is a drape, not a membrane. It does
not saddle. It does not form-found. It does not obey the
principle in engine/MEMBRANE_GUIDE.md.

This upgrade replaces the placeholder membrane with the FDM
result. The viewer calls the kernel, receives the equilibrium
coordinates, and draws the membrane exactly where the kernel
says it should be.

The beams, tie-downs, and ground supports do not change.

---

## 2. What the viewer must do

For one Cable Supported Saddle structure:

  1. Build a mesh of nodes over the membrane region.
     The mesh spans between the two beams (long edges) and
     between the two ends of the beams (short edges).

  2. Tag the boundary:
     - Long edges: attached to beams. Their nodes follow the
       beam curves exactly. Effectively fixed in 3D.
     - Short edges: free cable edges. Their nodes are pinned
       in plan but free to move in z (and along the edge).

  3. Assign force densities:
     - Beam-adjacent edges: high force density (beams are
       stiff, barely move).
     - Free-edge cable edges: force density derived from the
       user's cable pretension.
     - Interior membrane edges: force density derived from
       the user's membrane pretension.

  4. Call solve_fdm(mesh, fixed_indices, force_densities).

  5. Receive the coordinates.

  6. Draw the membrane surface through the FDM nodes.

  7. Draw the free-edge cables along the same curves as the
     boundary of the FDM membrane.

---

## 3. Inputs the viewer reads

From session state (all already present in the workshop):

  ws_ss_span              span between ground supports (m)
  ws_ss_apex              apex-to-apex distance (m)
  ws_ss_rise              rise at beam apex (m)
  ws_ss_curve_type        parabolic / circular / caternary
  ws_ss_membrane_pretension  membrane target stress (kN/m)
  ws_ss_cable_pretension     cable target tension (kN)
  ws_ss_tiedown_intervals tiedown count per side (4 or 8)

No new user inputs. No new workshop widgets.

---

## 4. Force densities — the conversion

This is the one piece of engineering that must be got right.

### 4.1 Interior membrane edges

The membrane force density q_mem is derived from the user's
membrane pretension T_mem (kN/m) and the mesh edge length L
in metres:

  q_mem = T_mem * 1000 / L

(The factor 1000 converts kN/m to N/m.)

Every interior edge in the mesh receives this same force
density, unless the mesh is non-uniform, in which case each
edge uses its own L.

### 4.2 Free-edge cable edges

The cable force density q_cab is derived from the user's cable
pretension T_cab (kN):

  q_cab = T_cab * 1000 / L_edge

where L_edge is the length of that edge.

### 4.3 Beam-adjacent edges

The beams are stiff steel. Their nodes are effectively fixed.
We model this by tagging the beam-adjacent nodes as fixed in
the FDM solve. No force density is needed for the beam edges
because the beam nodes do not move.

---

## 5. Mesh

The membrane mesh:

  nx nodes along the span (between the two beams).
  ny nodes across the width (from beam L to beam R).

Starting values:
  nx = 20
  ny = 20

That is 400 nodes and about 760 edges. FDM solves in
milliseconds.

The mesh is generated in the viewer, not stored in session
state. It is rebuilt on every render, matching the current
geometry.

---

## 6. What changes in the viewer file

File: viewers/figures/standard_saddle.py

Replace the block that builds the membrane surface:

  Current:
    n_u = 30, n_v = 30
    nested loops computing X_surf, Y_surf, Z_surf
    fig.add_trace(go.Surface(...))

  New:
    build the FDM mesh (nodes + edges)
    compute force densities
    call solve_fdm
    extract membrane surface from the FDM result
    fig.add_trace(go.Surface(...))

Replace the free-edge cable drawing:

  Current:
    no free-edge cable drawn (only tiedowns)

  New:
    draw the free-edge cables along the FDM's boundary
    curve on each short edge.

Everything else — beams, tie-downs, ground supports,
baseplate, camera, layout — remains unchanged.

---

## 7. What the viewer still does not do

The viewer does not yet:

  - Handle the "attach to beam" / "detach from beam"
    option in the workshop. Both modes use the same FDM
    call for now, with the beam edges fixed.
  - Use NFDM. That is a later upgrade.
  - Apply external loads. FDM form-finding here is
    load-free: the shape is the equilibrium under prestress
    alone. Loads come later, in Link 3.

These limits are acceptable. They are on the roadmap in
engine/SPEC_engine_chain.md.

---

## 8. What to test after the upgrade

Two manual checks in the app:

  1. Set the pretension to a mid-range value. Look at the
     membrane. It should saddle — the surface between the
     two beams should not be a cylinder. It should curve
     in both directions (concave up along one axis,
     concave down along the other).

  2. Change the pretension slider. The membrane should
     visibly respond: higher pretension → flatter surface;
     lower pretension → deeper sag or stronger saddle.

If the shape does not change with pretension, or if it
becomes non-smooth, something is wrong with the force
density conversion. We tune from there.

---

## 9. What is NOT changed

  - The beams (standard_saddle.py geometry).
  - The tie-down positions and angles.
  - The ground supports.
  - The camera and layout.
  - The workshop (saddle_standard.py). No new widgets.
  - The render prompt.

The upgrade is strictly inside the membrane drawing block of
the viewer.

---

## 10. Reversibility

If the FDM-driven membrane does not look right, or if it
introduces instability, we revert this one file to the
previous commit. The rest of the app is unaffected.

---

End of spec.





