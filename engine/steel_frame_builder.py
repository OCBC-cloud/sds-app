"""SDSe Engine — 3D Steel Frame Builder.

Builds a 3D frame model from the multi-cone membrane mesh data.
"""

import numpy as np

# =============================================================================
# NODE CLASSIFICATION
# =============================================================================

NODE_BOUNDARY = "boundary"
NODE_SPINE = "spine"
NODE_RIB = "rib"
NODE_RING = "ring"
NODE_DROP = "drop"
NODE_BASEPLATE = "baseplate"


def build_steel_frame(data, newton_data):
    """Build the 3D steel frame from the multi-cone mesh data."""
    coords_fdm = newton_data["dr_result"]["coordinates"]
    anchor_idx = data["anchor_idx"]
    reactions = newton_data["dr_result"].get("reactions", None)

    nodes = []
    node_kind = []
    elements = []
    membrane_loads = []
    anchor_to_frame_id = {}
    ring_to_frame_id = {}
    drop_to_frame_id = {}
    fixed_indices = []

    def add_node(pos, kind):
        nodes.append(pos)
        node_kind.append(kind)
        membrane_loads.append(np.zeros(3, dtype=float))
        return len(nodes) - 1

    # --- Boundary anchor nodes ---
    for mesh_idx in anchor_idx:
        pos = coords_fdm[int(mesh_idx)].copy()
        frame_id = add_node(pos, NODE_BOUNDARY)
        anchor_to_frame_id[int(mesh_idx)] = frame_id
        
        # FIX: Boundary anchors are ALWAYS fixed. No z-height check.
        fixed_indices.append(frame_id)

        # Transfer load: Force membrane exerts ON frame = -reaction
        if reactions is not None:
            r = reactions[mesh_idx]
            membrane_loads[frame_id] += -np.asarray(r, dtype=float)

    # --- Spine nodes ---
    xp = data["xp"]
    zp = data["zp"]
    spine_start_idx = len(nodes)
    for k in range(len(xp)):
        pos = np.array([xp[k], 0.0, zp[k]], dtype=float)
        add_node(pos, NODE_SPINE)

    # --- Rib nodes ---
    rib_start_indices = []
    for i, rib_x in enumerate(data["rib_x"]):
        rib_start_idx = len(nodes)
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
            add_node(pos, NODE_RIB)

    # --- Ring nodes and drop nodes ---
    ring_start_indices = []
    drop_start_indices = []
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        ring_start_idx = len(nodes)
        ring_start_indices.append(ring_start_idx)
        for j, mesh_node in enumerate(idx_list):
            pos = coords_fdm[int(mesh_node)].copy()
            frame_id = add_node(pos, NODE_RING)
            ring_to_frame_id[int(mesh_node)] = frame_id
            
            if reactions is not None:
                r = reactions[mesh_node]
                membrane_loads[frame_id] += -np.asarray(r, dtype=float)

        centre_mesh_idx = int(data["built"]["centre_indices"][k])
        drop_pos = coords_fdm[centre_mesh_idx].copy()
        drop_start_indices.append(len(nodes))
        frame_id = add_node(drop_pos, NODE_DROP)
        drop_to_frame_id[centre_mesh_idx] = frame_id
        
        if reactions is not None:
            r = reactions[centre_mesh_idx]
            membrane_loads[frame_id] += -np.asarray(r, dtype=float)

    nodes = np.asarray(nodes, dtype=float)
    membrane_loads = np.asarray(membrane_loads, dtype=float)

    # SAFETY: If somehow fixed_indices is still empty, grab the first 4 boundary nodes
    if len(fixed_indices) == 0 and len(anchor_to_frame_id) > 0:
        fixed_indices = list(anchor_to_frame_id.values())[:4]

    # ==========================================================================
    # BUILD ELEMENTS
    # ==========================================================================
    
    # Spine elements
    n_spine = len(xp)
    for k in range(n_spine - 1):
        a = spine_start_idx + k
        b = spine_start_idx + k + 1
        if a != b:
            elements.append({"a": a, "b": b, "section": "primary", "kind": NODE_SPINE})

    # Rib elements
    n_rib_segments = 12
    for i, rib_start_idx in enumerate(rib_start_indices):
        for k in range(n_rib_segments):
            a = rib_start_idx + k
            b = rib_start_idx + k + 1
            if a != b:
                elements.append({"a": a, "b": b, "section": "rib", "kind": NODE_RIB})

    # Ring elements
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        ring_start_idx = ring_start_indices[k]
        n_ring_nodes = len(idx_list)
        for i in range(n_ring_nodes):
            a = ring_start_idx + i
            b = ring_start_idx + (i + 1) % n_ring_nodes
            if a != b:
                elements.append({"a": a, "b": b, "section": "ring", "kind": NODE_RING})

    # Drop elements
    for k in range(len(data["built"]["centre_indices"])):
        drop_node = drop_start_indices[k]
        centre_mesh_idx = data["built"]["centre_indices"][k]
        cx = coords_fdm[centre_mesh_idx, 0]
        spine_xs = np.array([xp[m] for m in range(n_spine)])
        spine_k = int(np.argmin(np.abs(spine_xs - cx)))
        spine_node = spine_start_idx + spine_k
        if drop_node != spine_node:
            elements.append({"a": drop_node, "b": spine_node, "section": "drop", "kind": NODE_DROP})

    # Spoke elements
    for k in range(len(data["built"]["ring_indices"])):
        ring_start_idx = ring_start_indices[k]
        drop_node = drop_start_indices[k]
        n_ring_nodes = len(data["built"]["ring_indices"][k])
        for i in range(n_ring_nodes):
            a = ring_start_idx + i
            if a != drop_node:
                elements.append({"a": a, "b": drop_node, "section": "spoke", "kind": NODE_RING})

    # ==========================================================================
    # RETURN
    # ==========================================================================
    total_load_magnitude = float(np.sum(np.abs(membrane_loads)))
    total_reaction_magnitude = 0.0
    if reactions is not None:
        for mesh_idx in list(anchor_to_frame_id.keys()) + list(ring_to_frame_id.keys()) + list(drop_to_frame_id.keys()):
            total_reaction_magnitude += float(np.linalg.norm(reactions[mesh_idx]))

    return {
        "nodes": nodes,
        "elements": elements,
        "fixed_indices": fixed_indices,
        "node_kind": node_kind,
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
