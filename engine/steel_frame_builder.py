"""SDSe Engine — 3D Steel Frame Builder (Unified Topology).

Builds a 3D frame model from the multi-cone membrane mesh data using 
automated topology discovery.

Logic:
1. Baseplates: Discovered by finding nodes at Z=0.
2. Eave Anchors: Fused to the nearest arch/rib node. Not fixed.
3. Cone (Ring + Spokes): Built automatically from the mesh indices.
4. Load Transfer: True 3D reaction vectors applied directly to the fused nodes.
"""

import numpy as np

NODE_ARCH = "arch"
NODE_RING = "ring"
NODE_DROP = "drop"
NODE_SPOKE = "spoke"

def _distance_sq(p1, p2):
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2

def build_steel_frame(data, newton_data):
    coords_fdm = newton_data["dr_result"]["coordinates"]
    reactions = newton_data["dr_result"].get("reactions", None)
    anchor_idx = data["anchor_idx"]

    nodes = []
    node_kind = []
    membrane_loads = []
    elements = []
    fixed_indices = []
    
    def add_node(pos, kind):
        nodes.append(np.array(pos, dtype=float))
        node_kind.append(kind)
        membrane_loads.append(np.zeros(3, dtype=float))
        return len(nodes) - 1

    # =========================================================================
    # 1. BUILD THE ARCH AND RIB SKELETON
    # =========================================================================
    spine_indices = []
    xp = data["xp"]
    zp = data["zp"]
    for k in range(len(xp)):
        pos = np.array([xp[k], 0.0, zp[k]], dtype=float)
        spine_indices.append(add_node(pos, NODE_ARCH))
        
    for k in range(len(spine_indices) - 1):
        elements.append({"a": spine_indices[k], "b": spine_indices[k+1], "section": "primary", "kind": NODE_ARCH})

    rib_indices = []
    for i, rib_x in enumerate(data["rib_x"]):
        rib_path = []
        half_width = data["rib_half_width"][i]
        peak_z = data["rib_peak_z"][i]
        n_rib = 12
        for k in range(n_rib + 1):
            t = k / float(n_rib)
            y = -half_width + 2 * half_width * t
            u = y / half_width if half_width > 0 else 0
            z = peak_z * (1.0 - u ** 2)
            pos = np.array([rib_x, y, z], dtype=float)
            rib_path.append(add_node(pos, NODE_ARCH))
            
        rib_indices.append(rib_path)
        for k in range(len(rib_path) - 1):
            elements.append({"a": rib_path[k], "b": rib_path[k+1], "section": "rib", "kind": NODE_ARCH})

    # =========================================================================
    # 2. DISCOVER BASEPLATES (Z=0)
    # =========================================================================
    for i, pos in enumerate(nodes):
        if abs(pos[2]) < 0.05:
            fixed_indices.append(i)

    # =========================================================================
    # 3. FUSE EAVE ANCHORS AND APPLY LOADS
    # =========================================================================
    anchor_to_frame_id = {}
    for mesh_idx in anchor_idx:
        anchor_pos = coords_fdm[int(mesh_idx)]
        best_dist = float('inf')
        best_node = -1
        for i, node_pos in enumerate(nodes):
            if node_kind[i] == NODE_ARCH:
                dist = _distance_sq(anchor_pos, node_pos)
                if dist < best_dist:
                    best_dist = dist
                    best_node = i
                    
        if reactions is not None:
            r = reactions[mesh_idx]
            membrane_loads[best_node] += -np.asarray(r, dtype=float)
            
        anchor_to_frame_id[int(mesh_idx)] = best_node

    # =========================================================================
    # 4. BUILD CONE TOPOLOGY (RINGS, SPOKES, DROPS)
    # =========================================================================
    ring_to_frame_id = {}
    drop_to_frame_id = {}
    
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        ring_nodes = []
        for mesh_node in idx_list:
            pos = coords_fdm[int(mesh_node)]
            frame_id = add_node(pos, NODE_RING)
            ring_nodes.append(frame_id)
            ring_to_frame_id[int(mesh_node)] = frame_id
            if reactions is not None:
                membrane_loads[frame_id] += -np.asarray(reactions[mesh_node], dtype=float)
                
        for i in range(len(ring_nodes)):
            a = ring_nodes[i]
            b = ring_nodes[(i + 1) % len(ring_nodes)]
            elements.append({"a": a, "b": b, "section": "ring", "kind": NODE_RING})

        centre_mesh_idx = int(data["built"]["centre_indices"][k])
        drop_pos = coords_fdm[centre_mesh_idx]
        drop_node_id = add_node(drop_pos, NODE_DROP)
        drop_to_frame_id[centre_mesh_idx] = drop_node_id
        if reactions is not None:
            membrane_loads[drop_node_id] += -np.asarray(reactions[centre_mesh_idx], dtype=float)
            
        best_dist = float('inf')
        best_arch = -1
        for i, node_pos in enumerate(nodes):
            if node_kind[i] == NODE_ARCH:
                dist = _distance_sq(drop_pos, node_pos)
                if dist < best_dist:
                    best_dist = dist
                    best_arch = i
        if best_arch != -1:
            elements.append({"a": drop_node_id, "b": best_arch, "section": "drop", "kind": NODE_DROP})

        for r_node in ring_nodes:
            if r_node != drop_node_id:
                elements.append({"a": r_node, "b": drop_node_id, "section": "spoke", "kind": NODE_SPOKE})

    # =========================================================================
    # RETURN
    # =========================================================================
    nodes = np.asarray(nodes, dtype=float)
    membrane_loads = np.asarray(membrane_loads, dtype=float)

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
        "diagnostic_total_load_magnitude_N": total_load_magnitude,
        "diagnostic_total_reaction_magnitude_N": total_reaction_magnitude,
    }
