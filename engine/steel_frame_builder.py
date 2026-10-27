"""SDSe Engine — 3D Steel Frame Builder.

Builds the 3D steel frame from mesh data. Applies membrane reactions as
real 3D point loads to the nearest arch/rib/ring/drop node.

Fix: Eave anchors (Z>0) must fuse to arch nodes that are ABOVE the baseplate.
They must NOT fuse to fixed Z=0 nodes, or the loads go straight to ground.
"""

import numpy as np

NODE_ARCH = "arch"
NODE_RING = "ring"
NODE_DROP = "drop"
NODE_SPOKE = "spoke"


def _dist_sq(p1, p2):
    return float((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)


def build_steel_frame(data, newton_data):
    coords_fdm = newton_data["dr_result"]["coordinates"]
    reactions = newton_data["dr_result"].get("reactions", None)
    anchor_idx = data["anchor_idx"]

    nodes = []
    kinds = []
    loads = []
    elements = []
    fixed = []

    def add(pos, kind):
        nodes.append(np.array(pos, dtype=float))
        kinds.append(kind)
        loads.append(np.zeros(3))
        return len(nodes) - 1

    # --- Build primary arches from Z=0 to Z=0 ---
    spine_ids = []
    xp = data["xp"]
    zp = data["zp"]
    for k in range(len(xp)):
        spine_ids.append(add([xp[k], 0.0, zp[k]], NODE_ARCH))
    for k in range(len(spine_ids) - 1):
        elements.append({"a": spine_ids[k], "b": spine_ids[k+1], "section": "primary", "kind": NODE_ARCH})

    # --- Build ribs from Z=0 to Z=0 ---
    rib_paths = []
    for i, rib_x in enumerate(data["rib_x"]):
        path = []
        hw = data["rib_half_width"][i]
        pz = data["rib_peak_z"][i]
        n = 12
        for k in range(n + 1):
            t = k / float(n)
            y = -hw + 2 * hw * t
            u = y / hw if hw > 0 else 0.0
            z = pz * (1.0 - u ** 2)
            path.append(add([rib_x, y, z], NODE_ARCH))
        rib_paths.append(path)
        for k in range(len(path) - 1):
            elements.append({"a": path[k], "b": path[k+1], "section": "rib", "kind": NODE_ARCH})

    # --- Fix ONLY Z=0 baseplates ---
    for i, p in enumerate(nodes):
        if abs(p[2]) < 0.05:
            fixed.append(i)

    fixed_set = set(fixed)

    # --- Fuse eave anchors to nearest FREE arch node above baseplate ---
    anchor_map = {}
    for mesh_idx in anchor_idx:
        pos = coords_fdm[int(mesh_idx)]
        best, bestd = -1, float("inf")
        for i, np_ in enumerate(nodes):
            if kinds[i] != NODE_ARCH:
                continue
            if i in fixed_set:
                continue  # Skip fixed Z=0 nodes
            d = _dist_sq(pos, np_)
            if d < bestd:
                bestd, best = d, i
        if best >= 0:
            anchor_map[int(mesh_idx)] = best
            if reactions is not None:
                loads[best] += -np.asarray(reactions[mesh_idx], dtype=float)

    # --- Rings, drops, spokes ---
    ring_map = {}
    drop_map = {}
    for k, idx_list in enumerate(data["built"]["ring_indices"]):
        r_ids = []
        for mesh_node in idx_list:
            fid = add(coords_fdm[int(mesh_node)], NODE_RING)
            r_ids.append(fid)
            ring_map[int(mesh_node)] = fid
            if reactions is not None:
                loads[fid] += -np.asarray(reactions[mesh_node], dtype=float)
        for i in range(len(r_ids)):
            a, b = r_ids[i], r_ids[(i+1) % len(r_ids)]
            elements.append({"a": a, "b": b, "section": "ring", "kind": NODE_RING})

        cidx = int(data["built"]["centre_indices"][k])
        dpos = coords_fdm[cidx]
        drop_id = add(dpos, NODE_DROP)
        drop_map[cidx] = drop_id
        if reactions is not None:
            loads[drop_id] += -np.asarray(reactions[cidx], dtype=float)

        best, bestd = -1, float("inf")
        for i, np_ in enumerate(nodes):
            if kinds[i] != NODE_ARCH:
                continue
            d = _dist_sq(dpos, np_)
            if d < bestd:
                bestd, best = d, i
        if best >= 0:
            elements.append({"a": drop_id, "b": best, "section": "drop", "kind": NODE_DROP})

        for r_id in r_ids:
            if r_id != drop_id:
                elements.append({"a": r_id, "b": drop_id, "section": "spoke", "kind": NODE_SPOKE})

    nodes = np.asarray(nodes, dtype=float)
    loads = np.asarray(loads, dtype=float)

    total_load = float(np.sum(np.abs(loads)))
    total_reaction = 0.0
    if reactions is not None:
        for m in list(anchor_map) + list(ring_map) + list(drop_map):
            total_reaction += float(np.linalg.norm(reactions[m]))

    return {
        "nodes": nodes,
        "elements": elements,
        "fixed_indices": fixed,
        "node_kind": kinds,
        "membrane_loads": loads,
        "anchor_to_frame_id": anchor_map,
        "ring_to_frame_id": ring_map,
        "drop_to_frame_id": drop_map,
        "diagnostic_total_load_magnitude_N": total_load,
        "diagnostic_total_reaction_magnitude_N": total_reaction,
        "diagnostic_n_anchor_loads": len(anchor_map),
        "diagnostic_n_ring_loads": len(ring_map),
        "diagnostic_n_drop_loads": len(drop_map),
        "diagnostic_n_fixed": len(fixed),
        "diagnostic_n_elements": len(elements),
        "diagnostic_n_nodes": len(nodes),
    }
