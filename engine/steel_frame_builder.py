"""SDSe Engine — 3D Steel Frame Builder.

Builds a 3D frame model from the multi-cone membrane mesh data.

The frame consists of:
  - Spine members       (primary arched beam, ground to ground)
  - Longitudinal members (ribs, ground to spine crossing)
  - Ring members        (closed polygon around each cone)
  - Drop members        (vertical from spine to ring centre)
  - Radial spokes       (from ring nodes to drop member)
  - Boundary cables     (tension-only edge cable)

Node classification:
  - BOUNDARY nodes: membrane edge anchors (where cables terminate)
  - SPINE nodes:    along the primary beam
  - RIB nodes:      along each longitudinal member
  - RING nodes:     around each cone ring
  - DROP nodes:     centre of each ring, at the top of the drop member
  - SPOKE nodes:    ring nodes (spokes connect ring node → drop node)
  - BASEPLATE nodes: ground anchors (fixed in the solver)

Forces transferred from the membrane to the frame:
  - Cable end reactions at boundary anchors (CONNECTION_CABLE)
  - Rigid membrane pull at ring nodes (CONNECTION_RIGID with spokes)
  - Optional KADER transverse forces at rib nodes (future)

The builder produces:
  - nodes: (N, 3) coordinates
  - elements: list of {"a": int, "b": int, "section": str}
  - fixed_indices: nodes fixed in the 3D solver
  - node_kind: list of str, one per node ("boundary", "spine", "ring", etc.)
  - membrane_loads: (N, 3) array of forces from the membrane
  - section_lookup: dict, "primary"→CHS, "rib"→CHS, etc.
"""

import numpy as np

from engine.membrane_connections import (
    CONNECTION_RIGID,
    CONNECTION_CABLE,
    CONNECTION_SPOKE,
    transfer_connection,
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
NODE_SADDLE_TIP = "saddle_tip"  # For hypar shapes


# =============================================================================
# NODE MERGER
# =============================================================================

def _merge_close_nodes(nodes, tolerance=1e-4):
    """Return a mapping that merges coincident nodes.
    
    Two nodes are coincident if their 3D distance is < tolerance.
    Returns: (unique_nodes, merge_map) where merge_map[i] = index in unique_nodes.
    """
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
    """
    Build the 3D steel frame from the multi-cone mesh data.
    
    Returns a dict with:
      nodes:              (N, 3) array
      elements:           list of {"a": int, "b": int, "section": str, "kind": str}
      fixed_indices:      list of node indices fixed in the solver
      node_kind:          list of str, one per node
      membrane_loads:     (N, 3) array of forces from membrane (in N)
      cone_drop_node_ids: list of node ids (one per cone)
      boundary_node_ids:  list of node ids (membrane anchors)
    """
    if connection_types is None:
        # Default universal connection types
        connection_types = {
            "boundary": CONNECTION_CABLE,
            "ring": CONNECTION_RIGID,
        }
    
    # ==========================================================================
    # COLLECT ALL NODES
    # ==========================================================================
    # We gather nodes from three sources:
    #   1. Baseplate nodes (arch springing points)
    #   2. Boundary anchor nodes (membrane boundary terminations)
    #   3. Spine, rib, ring, drop nodes (frame nodes along each member)
    # We then merge coincident nodes so the frame is connected.
    
    all_nodes = []
    node_kind_list = []
    node_meta = []  # (kind, source_dict) - for reconstructing indices
    
    # --- Baseplate / boundary nodes ---
    coords_fdm = newton_data["dr_result"]["coordinates"]
    anchor_idx = data["anchor_idx"]
    anchor_to_frame_id = {}
    
    for mesh_idx in anchor_idx:
        pos = coords_fdm[mesh_idx].copy()
        all_nodes.append(pos)
        node_kind_list.append(NODE_BOUNDARY)
        node_meta.append(("boundary", mesh_idx))
        anchor_to_frame_id[int(mesh_idx)] = len(all_nodes) - 1
    
    # --- Spine nodes (from xp, zp) ---
    xp = data["xp"]; zp = data["zp"]
    spine_y = 0.0
    spine_start_idx = len(all_nodes)
    for k in range(len(xp)):
        pos = np.array([xp[k], spine_y, zp[k]], dtype=float)
        all_nodes.append(pos)
        node_kind_list.append(NODE_SPINE)
        node_meta.append(("spine", k))
    
    # --- Rib nodes (each rib polyline) ---
    rib_start_indices = []
    for i, rib_x in enumerate(data["rib_x"]):
        rib_start_idx = len(all_nodes)
        rib_start_indices.append(rib_start_idx)
        half_width = data["rib_half_width"][i]
        peak_z = data["rib_peak_z"][i]
        n_rib = 12  # segments per rib
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
        # Drop centre node
        centre_mesh_idx = data["built"]["centre_indices"][k]
        drop_pos = coords_fdm[centre_mesh_idx].copy()
        drop_start_indices.append(len(all_nodes))
        all_nodes.append(drop_pos)
        node_kind_list.append(NODE_DROP)
        node_meta.append(("drop", k, centre_mesh_idx))
    
    # --- Merge coincident nodes ---
    all_nodes = np.asarray(all_nodes, dtype=float)
    unique_nodes, merge_map = _merge_close_nodes(all_nodes)
    
    # Rebuild anchor_to_frame_id with merge_map
    for mesh_idx, old_id in anchor_to_frame_id.items():
        anchor_to_frame_id[mesh_idx] = int(merge_map[old_id])
    
    # Rebuild spine/rib/ring/drop start indices with merge_map
    merged_spine_start = int(merge_map[spine_start_idx]) if spine_start_idx < len(merge_map) else -1
    merged_rib_starts = [int(merge_map[s]) for s in rib_start_indices]
    merged_ring_starts = [int(merge_map[s]) for s in ring_start_indices]
    merged_drop_starts = [int(merge_map[s]) for s in drop_start_indices]
    
    # Consolidate node_kind (use majority kind per merged node)
    merged_node_kind = [""] * len(unique_nodes)
    merged_node_sources = [[] for _ in range(len(unique_nodes))]
    for old_id, kind in enumerate(node_kind_list):
        new_id = int(merge_map[old_id])
        merged_node_sources[new_id].append((kind, node_meta[old_id]))
        if not merged_node_kind[new_id]:
            merged_node_kind[new_id] = kind
    
    # ==========================================================================
    # BUILD ELEMENTS
    # ==========================================================================
    elements = []
    
    # --- Spine elements (consecutive nodes along spine) ---
    n_spine = len(xp)
    for k in range(n_spine - 1):
        old_a = spine_start_idx + k
        old_b = spine_start_idx + k + 1
        a = int(merge_map[old_a])
        b = int(merge_map[old_b])
        if a != b:
            elements.append({"a": a, "b": b, "section": "primary", "kind": NODE_SPINE})
    
    # --- Rib elements (consecutive nodes along each rib) ---
    n_rib_segments = 12
    for i, rib_start_idx in enumerate(rib_start_indices):
        for k in range(n_rib_segments):
            old_a = rib_start_idx + k
            old_b = rib_start_idx + k + 1
            a = int(merge_map[old_a])
            b = int(merge_map[old_b])
            if a != b:
                elements.append({"a": a, "b": b, "section": "rib", "kind": NODE_RIB})
    
    # --- Ring elements (consecutive nodes around each ring) ---
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
    
    # --- Drop elements (drop centre to spine crossing node) ---
    for k in range(len(data["built"]["centre_indices"])):
        drop_node_old = drop_start_indices[k]
        drop_node = int(merge_map[drop_node_old])
        # Find spine node at same x
        centre_mesh_idx = data["built"]["centre_indices"][k]
        cx = coords_fdm[centre_mesh_idx, 0]
        # Nearest spine node
        spine_xs = np.array([xp[m] for m in range(n_spine)])
        spine_k = int(np.argmin(np.abs(spine_xs - cx)))
        spine_node_old = spine_start_idx + spine_k
        spine_node = int(merge_map[spine_node_old])
        if drop_node != spine_node:
            elements.append({"a": drop_node, "b": spine_node, "section": "drop", "kind": NODE_DROP})
    
    # --- Spoke elements (ring node to drop node for each cone) ---
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
    # Any node at z < 0.05 is treated as a baseplate (fixed).
    fixed_indices = []
    for i, n in enumerate(unique_nodes):
        if abs(n[2]) < 0.05:
            fixed_indices.append(i)
            merged_node_kind[i] = NODE_BASEPLATE
    
    # ==========================================================================
    # MEMBRANE LOADS → FRAME NODES
    # ==========================================================================
    # For each boundary anchor, compute the cable end reactions at that node
    # from the adjacent boundary cables, and transfer to the frame.
    
    membrane_loads = np.zeros((len(unique_nodes), 3), dtype=float)
    
    # Get cable tensions from the membrane solve
    cable_tension_list = newton_data["dr_result"].get("cable_tension_list", [])
    cable_tension_by_segment = {}
    for ct in cable_tension_list:
        cable_tension_by_segment[(int(ct["a"]), int(ct["b"]))] = float(ct["T_N"])
    
    # For each boundary anchor, sum the cable tension vectors from the two
    # adjacent cable segments. Each adjacent cable pulls the anchor toward
    # its far end.
    n_anchors = len(anchor_idx)
    for i, mesh_idx in enumerate(anchor_idx):
        prev_anchor_mesh = anchor_idx[(i - 1) % n_anchors]
        next_anchor_mesh = anchor_idx[(i + 1) % n_anchors]
        anchor_pos = coords_fdm[mesh_idx]
        
        forces_at_anchor = []
        
        # Cable from prev to this anchor: tension pulls toward prev
        key_prev = (min(mesh_idx, prev_anchor_mesh), max(mesh_idx, prev_anchor_mesh))
        T_prev = cable_tension_by_segment.get(key_prev, 0.0)
        if T_prev > 0:
            direction = normalize(coords_fdm[prev_anchor_mesh] - anchor_pos)
            forces_at_anchor.append(T_prev * direction)
        
        # Cable from this anchor to next: tension pulls toward next
        key_next = (min(mesh_idx, next_anchor_mesh), max(mesh_idx, next_anchor_mesh))
        T_next = cable_tension_by_segment.get(key_next, 0.0)
        if T_next > 0:
            direction = normalize(coords_fdm[next_anchor_mesh] - anchor_pos)
            forces_at_anchor.append(T_next * direction)
        
        total_force = vector_sum(forces_at_anchor)
        
        # Transfer to frame node
        frame_node_id = anchor_to_frame_id[mesh_idx]
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
        "cone_ring_node_starts": merged_ring_starts,
    }
