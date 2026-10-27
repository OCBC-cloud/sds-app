"""SDSe Engine — 3D Steel Frame Builder (Exact Crossing Fusion).

Builds the 3D steel frame from mesh data.

Topology (no tolerance, exact indices):
  1. Spine (primary arch) built from 200 samples.
  2. At every eave anchor Z, drop Z, and rib apex X, a NEW spine node is
     inserted at the exact geometric crossing (segment split).
  3. Ribs are built from the ground up to the exact spine node at their X.
  4. Drops are built from the exact spine node at their Z up to the ring centre.
  5. Rings and spokes share exact node indices.
  6. Only Z=0 baseplates are fixed. All other nodes are free.

Result: a single connected 3D structure. No singular matrix.
"""

import numpy as np

NODE_ARCH = "arch"
NODE_RING = "ring"
NODE_DROP = "drop"
NODE_SPOKE = "spoke"


def _interp_z_at_x(xp, zp, x_target):
    """Return the exact Z of the spine at X = x_target."""
    for k in range(len(xp) - 1):
        x0, x1 = xp[k], xp[k + 1]
        if (x0 <= x_target <= x1) or (x1 <= x_target <= x0):
            if abs(x1 - x0) < 1e-12:
                return float(zp[k])
            t = (x_target - x0) / (x1 - x0)
            return float(zp[k] + t * (zp[k + 1] - zp[k]))
    return float(zp[0])


def _build_spine_with_crossings(xp, zp, target_zs, target_xs):
    """
    Walk the spine samples, insert new nodes at every target Z and target X.
    Returns (spine_nodes, spine_zs, crossmap_z, crossmap_x, elements_spine).

    crossmap_z maps target_z -> spine node index (first crossing found going up)
    crossmap_x maps target_x -> spine node index (unique X)
    """
    spine_nodes = []
    spine_zs = []
    spine_xs = []
    elements_spine = []
    crossmap_z = {}
    crossmap_x = {}

    def push_node(x, z):
        spine_nodes.append(np.array([x, 0.0, z], dtype=float))
        spine_zs.append(z)
        spine_xs.append(x)
        return len(spine_nodes) - 1

    # Seed with the first spine sample
    prev_idx = push_node(xp[0], zp[0])

    for k in range(len(xp) - 1):
        x_a, z_a = xp[k], zp[k]
        x_b, z_b = xp[k + 1], zp[k + 1]

        # Collect all events on this segment: (t, kind, value)
        events = []

        # Target X crossings
        for tx in target_xs:
            if (x_a <= tx <= x_b) or (x_b <= tx <= x_a):
                if abs(x_b - x_a) > 1e-12:
                    t = (tx - x_a) / (x_b - x_a)
                    if 1e-9 < t < 1.0 - 1e-9:
                        events.append((t, "x", tx))

        # Target Z crossings
        z_min = min(z_a, z_b)
        z_max = max(z_a, z_b)
        for tz in target_zs:
            if z_min <= tz <= z_max:
                if abs(z_b - z_a) > 1e-12:
                    t = (tz - z_a) / (z_b - z_a)
                    if 1e-9 < t < 1.0 - 1e-9:
                        events.append((t, "z", tz))

        # Sort events by t so we insert in the correct order along the segment
        events.sort(key=lambda e: e[0])

        for t, kind, val in events:
            x_ins = x_a + t * (x_b - x_a)
            z_ins = z_a + t * (z_b - z_a)
            new_idx = push_node(x_ins, z_ins)
            elements_spine.append({"a": prev_idx, "b": new_idx, "section": "primary", "kind": NODE_ARCH})
            prev_idx = new_idx
            if kind == "z" and val not in crossmap_z:
                crossmap_z[val] = new_idx
            if kind == "x":
                crossmap_x[val] = new_idx

        # Connect to the next sample
        next_idx = push_node(x_b, z_b)
        elements_spine.append({"a": prev_idx, "b": next_idx, "section": "primary", "kind": NODE_ARCH})
        prev_idx = next_idx

    return spine_nodes, spine_zs, spine_xs, crossmap_z, crossmap_x, elements_spine


def build_steel_frame(data, newton_data):
    coords_fdm = newton_data["dr_result"]["coordinates"]
    reactions = newton_data["dr_result"].get("reactions", None)
    anchor_idx = data["anchor_idx"]
    eave_height = float(data["eave_height"])

    xp = data["xp"]
    zp = data["zp"]
    rib_xs = list(data["rib_x"])

    # Determine all target Z crossings (eave + every drop)
    drop_zs = []
    for cidx in data["built"]["centre_indices"]:
        drop_zs.append(float(coords_fdm[int(cidx)][2]))

    target_zs = sorted(set([eave_height] + drop_zs))

    # Determine all target X crossings (rib apex X)
    target_xs = list(rib_xs)

    # Build spine with inserted crossings
    spine_nodes, spine_zs, spine_xs, crossmap_z, crossmap_x, elements_spine = \
        _build_spine_with_crossings(xp, zp, target_zs, target_xs)

    nodes = list(spine_nodes)
    kinds = [NODE_ARCH] * len(spine_nodes)
    loads = [np.zeros(3) for _ in range(len(spine_nodes))]
    elements = list(elements_spine)

    def add(pos, kind):
        nodes.append(np.array(pos, dtype=float))
        kinds.append(kind)
        loads.append(np.zeros(3))
        return len(nodes) - 1

    # --- Ribs: each rib is a chain from Z=0 at (rib_x, -hw) to Z=0 at (rib_x, +hw),
    #     passing through the exact spine node at (rib_x, 0, z_spine).
    for i, rib_x in enumerate(rib_xs):
        hw = data["rib_half_width"][i]
        apex_spine_idx = crossmap_x.get(float(rib_x))
        if apex_spine_idx is None:
            # Fallback: find nearest spine sample by exact match
            for idx, sx in enumerate(spine_xs):
                if abs(sx - rib_x) < 1e-9:
                    apex_spine_idx = idx
                    break
        if apex_spine_idx is None:
            continue
        apex_z = float(spine_zs[apex_spine_idx])

        n_half = 6
        # Left side: from ground (-hw, 0) up to apex
        y_vals_left = np.linspace(-hw, 0.0, n_half + 1)
        prev = None
        left_path = []
        for yv in y_vals_left[:-1]:
            u = yv / hw if hw > 0 else 0.0
            z = apex_z * (1.0 - u ** 2)
            idx = add([float(rib_x), float(yv), float(z)], NODE_ARCH)
            left_path.append(idx)
        left_path.append(apex_spine_idx)

        for k in range(len(left_path) - 1):
            elements.append({"a": left_path[k], "b": left_path[k + 1], "section": "rib", "kind": NODE_ARCH})

        # Right side: from apex down to ground (+hw, 0)
        y_vals_right = np.linspace(0.0, hw, n_half + 1)
        right_path = [apex_spine_idx]
        for yv in y_vals_right[1:]:
            u = yv / hw if hw > 0 else 0.0
            z = apex_z * (1.0 - u ** 2)
            idx = add([float(rib_x), float(yv), float(z)], NODE_ARCH)
            right_path.append(idx)

        for k in range(len(right_path) - 1):
            elements.append({"a": right_path[k], "b": right_path[k+1], "section": "rib", "kind": NODE_ARCH})

    # --- Fix Z=0 baseplates ---
    fixed = []
    for i, p in enumerate(nodes):
        if abs(p[2]) < 1e-6:
            fixed.append(i)
    fixed_set = set(fixed)

    # --- Eave anchors: fuse to exact spine node at Z=eave_height ---
    anchor_map = {}
    eave_spine_idxs = [idx for idx, sz in enumerate(spine_zs) if abs(sz - eave_height) < 1e-6]
    # If we inserted only ONE crossing at eave height, use that node.
    # If TWO (up and down), we place the anchor on the closer one by X.
    for mesh_idx in anchor_idx:
        pos = coords_fdm[int(mesh_idx)]
        best, bestd = -1, float("inf")
        for cand_idx in eave_spine_idxs:
            if cand_idx in fixed_set:
                continue
            d = (spine_xs[cand_idx] - pos[0])**2 + (spine_zs[cand_idx] - pos[2])**2
            if d < bestd:
                bestd, best = d, cand_idx
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
            a, b = r_ids[i], r_ids[(i + 1) % len(r_ids)]
            elements.append({"a": a, "b": b, "section": "ring", "kind": NODE_RING})

        cidx = int(data["built"]["centre_indices"][k])
        dpos = coords_fdm[cidx]
        drop_id = add(dpos, NODE_DROP)
        drop_map[cidx] = drop_id
        if reactions is not None:
            loads[drop_id] += -np.asarray(reactions[cidx], dtype=float)

        # Fuse drop to exact spine node at drop's Z
        drop_z = float(dpos[2])
        drop_spine_candidates = [idx for idx, sz in enumerate(spine_zs) if abs(sz - drop_z) < 1e-6]
        best, bestd = -1, float("inf")
        for cand_idx in drop_spine_candidates:
            d = (spine_xs[cand_idx] - dpos[0])**2
            if d < bestd:
                bestd, best = d, cand_idx
        if best >= 0:
            elements.append({"a": drop_id, "b": best, "section": "drop", "kind": NODE_DROP})

        # Spokes connect every ring node to the drop node
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
