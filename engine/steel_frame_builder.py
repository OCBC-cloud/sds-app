"""SDSe Engine — 3D Steel Frame Builder.

Builds a 3D frame model from the multi-cone membrane mesh data.

Load transfer:
    Every fixed node in the membrane solver is a point of load transfer
    to the steel frame. There are three types:
      - Boundary anchors (eave)
      - Ring nodes (cones)
      - Drop centres (cone apex)

    The membrane solver returns `reactions[i]` at each fixed node `i`.
    This is the force the support exerts ON the membrane. The force the
    membrane exerts ON the frame is `-reactions[i]`.

    We apply `-reactions[i]` as a load on the corresponding frame node,
    for every fixed membrane node. No deferrals.

Substructure method (per industry standard, RFEM, Tensys, BATS):
    The membrane is solved with fixed boundary conditions at the anchors,
    rings, and drops. The resulting reactions are transferred as loads
    onto the 3D steel frame. The frame then carries these loads to the
    ground. This is a conservative substructuring approximation. Full
    integrated analysis (membrane and frame solved simultaneously) is
    a future upgrade.
"""

import numpy as np

from engine.membrane_connections import normalize


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

def build_steel_frame(data, newton_data):
    """Build the 3D steel frame from the multi-cone mesh data."""
    coords_fdm = newton_data["dr_result"]["coordinates"]
    anchor_idx = data["anchor_idx"]

    # ==========================================================================
    # COLLECT ALL NODES
    # ==========================================================================
    all_nodes = []
    node_kind_list = []
    node_meta = []

    # Tracking maps: mesh node index -> old frame node index (pre-merge)
    anchor_old_id = {}
    ring_old_ids = {}       # mesh_idx -> old_id
    drop_old_ids = {}       # mesh_idx -> old_id

    # --- Boundary anchor nodes ---
    for mesh_idx in anchor_idx:
        pos = coords_fdm[int(mesh_idx)].copy()
        all_nodes.append(pos)
        node_kind_list.append(NODE_BOUNDARY)
        node_meta.append(("boundary", mesh_idx))
        anchor_old_id[int(mesh_idx)] = len(all_nodes) - 1

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
        for j, mesh_node in enumerate(idx_list):
            pos = coords_fdm[int(mesh_node)].copy()
            all_nodes.append(pos)
            node_kind_list.append(NODE_RING)
            node_meta.append(("ring", k, mesh_node))
            ring_old_ids[int(mesh_node)] = len(all_nodes) - 1
        centre_mesh_idx = int(data["built"]["centre_indices"][k])
        drop_pos = coords_fdm[centre_mesh_idx].copy()
        drop_start_indices.append(len(all_nodes))
        all_nodes.append(drop_pos)
        node_kind_list.append(NODE_DROP)
        node_meta.append(("drop", k, centre_mesh_idx))
        drop_old_ids[centre_mesh_idx] = len(all_nodes) - 1

    # --- Merge coincident nodes ---
    all_nodes = np.asarray(all_nodes, dtype=float)
    unique_nodes, merge_map = _merge_close_nodes(all_nodes)

    # Rebuild tracking maps with merge_map
    anchor_to_frame_id = {}
    for mesh_idx, old_id in anchor_old_id.items():
        anchor_to_frame_id[mesh_idx] = int(merge_map[old_id])

    ring_to_frame_id = {}
    for mesh_idx, old_id in ring_old_ids.items():
        ring_to_frame_id[mesh_idx] = int(merge_map[old_id])

    drop_to_frame_id = {}
    for mesh_idx, old_id in drop_old_ids.items():
        drop_to_frame_id[mesh_idx] = int(merge_map[old_id])

    # Consolidated node_kind
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
        a = int(merge_map[spine_start_idx + k])
        b = int(merge_map[spine_start_idx + k + 1])
        if a != b:
            elements.append({"a": a, "b": b, "section": "primary", "kind": NODE_SPINE})

    # Rib elements
    n_rib_segments = 12
    for i, rib_start_idx in enumerate(rib_start_indices):
        for k in range(n_rib_segments):
            a = int(merge_map[rib_start_idx + k])
            b = int(merge_map[rib_start_idx + k + 1])
            if a != b:
                elements.append({"a": a, "b": b, "section": "rib", "kind": NODE_RIB})

    # Ring elements
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        ring_start_idx = ring_start_indices[k]
        n_ring_nodes = len(idx_list)
        for i in range(n_ring_nodes):
            a = int(merge_map[ring_start_idx + i])
            b = int(merge_map[ring_start_idx + (i + 1) % n_ring_nodes])
            if a != b:
                elements.append({"a": a, "b": b, "section": "ring", "kind": NODE_RING})

    # Drop elements
    for k in range(len(data["built"]["centre_indices"])):
        drop_node = int(merge_map[drop_start_indices[k]])
        centre_mesh_idx = data["built"]["centre_indices"][k]
        cx = coords_fdm[centre_mesh_idx, 0]
        spine_xs = np.array([xp[m] for m in range(n_spine)])
        spine_k = int(np.argmin(np.abs(spine_xs - cx)))
        spine_node = int(merge_map[spine_start_idx + spine_k])
        if drop_node != spine_node:
            elements.append({"a": drop_node, "b": spine_node, "section": "drop", "kind": NODE_DROP})

    # Spoke elements
    for k in range(len(data["built"]["ring_indices"])):
        ring_start_idx = ring_start_indices[k]
        drop_node = int(merge_map[drop_start_indices[k]])
        n_ring_nodes = len(data["built"]["ring_indices"][k])
        for i in range(n_ring_nodes):
            a = int(merge_map[ring_start_idx + i])
            if a != drop_node:
                elements.append({"a": a, "b": drop_node, "section": "spoke", "kind": NODE_RING})

    # ==========================================================================
    # FIXED NODES (baseplates)
    # ==========================================================================
    # BUG FIX: Only fix nodes that are actual boundary anchors (eave).
    # Previously this swept all nodes near z=0, over-constraining the frame.
    fixed_indices = []
    for i, n in enumerate(unique_nodes):
        if merged_node_kind[i] == NODE_BOUNDARY and abs(n[2]) < 0.05:
            fixed_indices.append(i)
            # Note: Do NOT overwrite merged_node_kind[i] here.

    # ==========================================================================
    # LOAD TRANSFER: MEMBRANE REACTIONS -> FRAME LOADS
    # ==========================================================================
    membrane_loads = np.zeros((len(unique_nodes), 3), dtype=float)
    reactions = newton_data["dr_result"].get("reactions", None)

    if reactions is not None:
        # Boundary anchors
        for mesh_idx, frame_id in anchor_to_frame_id.items():
            r = reactions[mesh_idx]
            membrane_loads[frame_id] += -np.asarray(r, dtype=float)

        # Ring nodes
        for mesh_idx, frame_id in ring_to_frame_id.items():
            r = reactions[mesh_idx]
            membrane_loads[frame_id] += -np.asarray(r, dtype=float)

        # Drop centres
        for mesh_idx, frame_id in drop_to_frame_id.items():
            r = reactions[mesh_idx]
            membrane_loads[frame_id] += -np.asarray(r, dtype=float)

    # ==========================================================================
    # RETURN
    # ==========================================================================
    total_load_magnitude = float(np.sum(np.abs(membrane_loads)))
    total_reaction_magnitude = 0.0
    if reactions is not None:
        for mesh_idx in list(anchor_to_frame_id.keys()) + list(ring_to_frame_id.keys()) + list(drop_to_frame_id.keys()):
            total_reaction_magnitude += float(np.linalg.norm(reactions[mesh_idx]))

    return {
        "nodes": unique_nodes,
        "elements": elements,
        "fixed_indices": fixed_indices,
        "node_kind": merged_node_kind,
        "membrane_loads": membrane_loads,
        "anchor_to_frame_id": anchor_to_frame_id,
        "ring_to_frame_id": ring_to_frame_id,
        "drop_to_frame_id": drop_to_frame_id,
        # Diagnostics
        "diagnostic_total_load_magnitude_N": total_load_magnitude,
        "diagnostic_total_reaction_magnitude_N": total_reaction_magnitude,
        "diagnostic_n_anchor_loads": len(anchor_to_frame_id),
        "diagnostic_n_ring_loads": len(ring_to_frame_id),
        "diagnostic_n_drop_loads": len(drop_to_frame_id),
    }
