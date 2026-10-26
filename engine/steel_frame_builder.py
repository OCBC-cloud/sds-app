"""SDSe Engine — 3D Steel Frame Builder.

Builds a 3D frame model from the multi-cone membrane mesh data.

The frame consists of:
  - Spine members       (primary arched beam, ground to ground)
  - Longitudinal members (ribs, ground to spine crossing)
  - Ring members        (closed polygon around each cone)
  - Drop members        (vertical from spine to ring centre)
  - Radial spokes       (from ring nodes to drop member)
  - Boundary cables     (tension-only edge cable)

Forces transferred from the membrane to the frame:
  - Cable end reactions at boundary anchors (CONNECTION_CABLE)

The builder produces:
  - nodes:               (N, 3) coordinates
  - elements:            list of {"a", "b", "section", "kind"}
  - fixed_indices:       nodes fixed in the 3D solver
  - node_kind:           list of str, one per node
  - membrane_loads:      (N, 3) array of forces from membrane (in N)
  - anchor_to_frame_id:  dict mapping membrane mesh index -> frame node id
  - cone_drop_node_ids:  list of frame node ids (one per cone)
"""

import numpy as np

from engine.membrane_connections import (
    normalize,
    vector_sum,
)


# =============================================================================
# NODE CLASSIFICATION
# =============================================================================

NODE_BOUNDARY = "boundary"
NODE_SPINE = "spine"
NODE_RIB = "rib"
NODE_RING = "ring"
NODE_DROP = "drop"
NODE_BASEPLATE = "baseplate"


# =============================================================================
# NODE MERGER
# =============================================================================

def _merge_close_nodes(nodes, tolerance=1e-4):
    """Return a mapping that merges coincident nodes."""
    if len(nodes) == 0:
        return np.zeros((0, 3)), np.zeros(0, dtype=int)
    
    unique = []
    merge_map = np.zeros(len(nodes), dtype=int)
    
    for i, n in enumerate(nodes):
        found = -1
        for j, u in enumerate(unique):
            if np.linalg.norm(n - u) < tolerance:
                found = j
                break
        if found < 0:
            unique.append(n)
            merge_map[i] = len(unique) - 1
        else:
            merge_map[i] = found
    
    return np.asarray(unique), merge_map


# =============================================================================
# FRAME BUILDER
# =============================================================================

def build_steel_frame(data, newton_data, connection_types=None):
    """Build the 3D steel frame from the multi-cone mesh data."""
    if connection_types is None:
        connection_types = {
            "boundary": "cable",
            "ring": "rigid",
        }
    
    # ==========================================================================
    # COLLECT ALL NODES
    # ==========================================================================
    all_nodes = []
    node_kind_list = []
    node_meta = []
    
    coords_fdm = newton_data["dr_result"]["coordinates"]
    anchor_idx = data["anchor_idx"]
    anchor_to_frame_id_old = {}
    
    # --- Boundary anchor nodes ---
    for mesh_idx in anchor_idx:
        pos = coords_fdm[mesh_idx].copy()
        all_nodes.append(pos)
        node_kind_list.append(NODE_BOUNDARY)
        node_meta.append(("boundary", mesh_idx))
        anchor_to_frame_id_old[int(mesh_idx)] = len(all_nodes) - 1
    
    # --- Spine nodes ---
    xp = data["xp"]
    zp = data["zp"]
    spine_start_idx = len(all_nodes)
    for k in range(len(xp)):
        pos = np.array([xp[k], 0.0, zp[k]], dtype=float)
        all_nodes.append(pos)
        node_kind_list.append(NODE_SPINE)
        node_meta.append(("spine", k))
    
    # --- Rib nodes ---
    rib_start_indices = []
    for i, rib_x in enumerate(data["rib_x"]):
        rib_start_idx = len(all_nodes)
        rib_start_indices.append(rib_start_idx)
        half_width = data["rib_half_width"][i]
        peak_z = data["rib_peak_z"][i]
        n_rib = 12
        for k in range(n_rib + 1):
            t = k / float(n_rib)
            y = -half_width + 2 * half_width * t
            u = y / half_width if half_width > 0 else 0
            z = peak_z * (1.0 - u ** 2)
            pos = np.array([rib_x, y, z], dtype=float)
            all_nodes.append(pos)
            node_kind_list.append(NODE_RIB)
            node_meta.append(("rib", i, k))
    
    # --- Ring nodes and drop nodes ---
    ring_start_indices = []
    drop_start_indices = []
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        ring_start_idx = len(all_nodes)
        ring_start_indices.append(ring_start_idx)
        for mesh_node in idx_list:
            pos = coords_fdm[mesh_node].copy()
            all_nodes.append(pos)
            node_kind_list.append(NODE_RING)
            node_meta.append(("ring", k, mesh_node))
        centre_mesh_idx = data["built"]["centre_indices"][k]
        drop_pos = coords_fdm[centre_mesh_idx].copy()
        drop_start_indices.append(len(all_nodes))
        all_nodes.append(drop_pos)
        node_kind_list.append(NODE_DROP)
        node_meta.append(("drop", k, centre_mesh_idx))
    
    # --- Merge coincident nodes ---
    all_nodes = np.asarray(all_nodes, dtype=float)
    unique_nodes, merge_map = _merge_close_nodes(all_nodes)
    
    anchor_to_frame_id = {}
    for mesh_idx, old_id in anchor_to_frame_id_old.items():
        anchor_to_frame_id[mesh_idx] = int(merge_map[old_id])
    
    # Consolidate node_kind
    merged_node_kind = [""] * len(unique_nodes)
    for old_id, kind in enumerate(node_kind_list):
        new_id = int(merge_map[old_id])
        if not merged_node_kind[new_id]:
            merged_node_kind[new_id] = kind
    
    # ==========================================================================
    # BUILD ELEMENTS
    # ==========================================================================
    elements = []
    
    # Spine elements
    n_spine = len(xp)
    for k in range(n_spine - 1):
        old_a = spine_start_idx + k
        old_b = spine_start_idx + k + 1
        a = int(merge_map[old_a])
        b = int(merge_map[old_b])
        if a != b:
            elements.append({"a": a, "b": b, "section": "primary", "kind": NODE_SPINE})
    
    # Rib elements
    n_rib_segments = 12
    for i, rib_start_idx in enumerate(rib_start_indices):
        for k in range(n_rib_segments):
            old_a = rib_start_idx + k
            old_b = rib_start_idx + k + 1
            a = int(merge_map[old_a])
            b = int(merge_map[old_b])
            if a != b:
                elements.append({"a": a, "b": b, "section": "rib", "kind": NODE_RIB})
    
    # Ring elements
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        ring_start_idx = ring_start_indices[k]
        n_ring_nodes = len(idx_list)
        for i in range(n_ring_nodes):
            old_a = ring_start_idx + i
            old_b = ring_start_idx + (i + 1) % n_ring_nodes
            a = int(merge_map[old_a])
            b = int(merge_map[old_b])
            if a != b:
                elements.append({"a": a, "b": b, "section": "ring", "kind": NODE_RING})
    
    # Drop elements
    for k in range(len(data["built"]["centre_indices"])):
        drop_node_old = drop_start_indices[k]
        drop_node = int(merge_map[drop_node_old])
        centre_mesh_idx = data["built"]["centre_indices"][k]
        cx = coords_fdm[centre_mesh_idx, 0]
        spine_xs = np.array([xp[m] for m in range(n_spine)])
        spine_k = int(np.argmin(np.abs(spine_xs - cx)))
        spine_node_old = spine_start_idx + spine_k
        spine_node = int(merge_map[spine_node_old])
        if drop_node != spine_node:
            elements.append({"a": drop_node, "b": spine_node, "section": "drop", "kind": NODE_DROP})
    
    # Spoke elements (ring node to drop node)
    for k in range(len(data["built"]["ring_indices"])):
        ring_start_idx = ring_start_indices[k]
        drop_node_old = drop_start_indices[k]
        drop_node = int(merge_map[drop_node_old])
        n_ring_nodes = len(data["built"]["ring_indices"][k])
        for i in range(n_ring_nodes):
            old_a = ring_start_idx + i
            a = int(merge_map[old_a])
            if a != drop_node:
                elements.append({"a": a, "b": drop_node, "section": "spoke", "kind": NODE_RING})
    
    # ==========================================================================
    # FIXED NODES (baseplates)
    # ==========================================================================
    fixed_indices = []
    for i, n in enumerate(unique_nodes):
        if abs(n[2]) < 0.05:
            fixed_indices.append(i)
            merged_node_kind[i] = NODE_BASEPLATE
    
    # ==========================================================================
    # MEMBRANE LOADS → FRAME NODES
    # ==========================================================================
    # This is the critical section. The membrane solver reports cable tension
    # per segment in cable_tension_list, keyed by (a, b) membrane mesh indices.
    # The boundary is SUBDIVIDED, so anchors are NOT directly connected to
    # each other — there are intermediate mesh nodes between them.
    #
    # We must therefore build a full adjacency map of every cable segment,
    # indexed by both endpoints. Then each anchor finds all segments touching
    # it and sums their tension vectors.
    
    membrane_loads = np.zeros((len(unique_nodes), 3), dtype=float)
    
    cable_tension_list = newton_data["dr_result"].get("cable_tension_list", [])
    
    # Build full adjacency: mesh_node -> list of (other_end, T_N, direction_from_this_node_to_other)
    adjacent_cables = {}
    for ct in cable_tension_list:
        a = int(ct["a"])
        b = int(ct["b"])
        T_N = float(ct["T_N"])
        if T_N <= 0:
            continue
        pos_a = coords_fdm[a]
        pos_b = coords_fdm[b]
        dir_a_to_b = normalize(pos_b - pos_a)
        dir_b_to_a = normalize(pos_a - pos_b)
        adjacent_cables.setdefault(a, []).append((b, T_N, dir_a_to_b))
        adjacent_cables.setdefault(b, []).append((a, T_N, dir_b_to_a))
    
    # For each boundary anchor, sum the tension vectors from all segments touching it
    n_cables_applied = 0
    total_force_magnitude = 0.0
    for mesh_idx in anchor_idx:
        mesh_idx_int = int(mesh_idx)
        anchor_pos = coords_fdm[mesh_idx_int]
        
        forces_at_anchor = []
        cables_here = adjacent_cables.get(mesh_idx_int, [])
        
        for (other_idx, T_N, _dir) in cables_here:
            other_pos = coords_fdm[other_idx]
            direction = normalize(other_pos - anchor_pos)
            forces_at_anchor.append(T_N * direction)
            n_cables_applied += 1
        
        total_force = vector_sum(forces_at_anchor)
        total_force_magnitude += float(np.linalg.norm(total_force))
        
        frame_node_id = anchor_to_frame_id[mesh_idx_int]
        membrane_loads[frame_node_id] += total_force
    
    # ==========================================================================
    # RETURN
    # ==========================================================================
    return {
        "nodes": unique_nodes,
        "elements": elements,
        "fixed_indices": fixed_indices,
        "node_kind": merged_node_kind,
        "membrane_loads": membrane_loads,
        "anchor_to_frame_id": anchor_to_frame_id,
        "cone_drop_node_ids": [int(merge_map[d]) for d in drop_start_indices],
        "cone_ring_node_starts": [int(merge_map[s]) for s in ring_start_indices],
        # Diagnostics
        "diagnostic_n_cables_applied": n_cables_applied,
        "diagnostic_total_force_magnitude_N": total_force_magnitude,
    }
