"""SDSe Engine — 3D Steel Frame Builder (Stable Geometry Loads).

Builds the 3D steel frame from mesh data. 
Uses fast geometric loads to feed the sizer without crashing.
"""

import numpy as np
from data.sections import SECTION_PROPERTIES

NODE_ARCH = "arch"
NODE_RING = "ring"
NODE_DROP = "drop"
NODE_SPOKE = "spoke"

KIND_PRIMARY = "primary"
KIND_RIB = "rib"
KIND_RING = "ring"
KIND_DROP = "drop"
KIND_SPOKE = "spoke"

_DEFAULT_SECTION = SECTION_PROPERTIES.get("CHS_60x3", {"A": 1.0, "I": 1.0})


def _interp_z_at_x(xp, zp, x_target):
    for k in range(len(xp) - 1):
        x0, x1 = xp[k], xp[k + 1]
        if (x0 <= x_target <= x1) or (x1 <= x_target <= x0):
            if abs(x1 - x0) < 1e-12:
                return float(zp[k])
            t = (x_target - x0) / (x1 - x0)
            return float(zp[k] + t * (zp[k + 1] - zp[k]))
    return float(zp[0])


def _build_spine_with_crossings(xp, zp, target_zs, target_xs):
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

    prev_idx = push_node(xp[0], zp[0])

    for k in range(len(xp) - 1):
        x_a, z_a = xp[k], zp[k]
        x_b, z_b = xp[k + 1], zp[k + 1]

        events = []

        for tx in target_xs:
            if (x_a <= tx <= x_b) or (x_b <= tx <= x_a):
                if abs(x_b - x_a) > 1e-12:
                    t = (tx - x_a) / (x_b - x_a)
                    if 1e-9 < t < 1.0 - 1e-9:
                        events.append((t, "x", tx))

        z_min = min(z_a, z_b)
        z_max = max(z_a, z_b)
        for tz in target_zs:
            if z_min <= tz <= z_max:
                if abs(z_b - z_a) > 1e-12:
                    t = (tz - z_a) / (z_b - z_a)
                    if 1e-9 < t < 1.0 - 1e-9:
                        events.append((t, "z", tz))

        events.sort(key=lambda e: e[0])

        for t, kind, val in events:
            x_ins = x_a + t * (x_b - x_a)
            z_ins = z_a + t * (z_b - z_a)
            new_idx = push_node(x_ins, z_ins)
            elements_spine.append({"a": prev_idx, "b": new_idx, "section": KIND_PRIMARY, "kind": KIND_PRIMARY})
            prev_idx = new_idx
            if kind == "z" and val not in crossmap_z:
                crossmap_z[val] = new_idx
            if kind == "x":
                crossmap_x[val] = new_idx

        next_idx = push_node(x_b, z_b)
        elements_spine.append({"a": prev_idx, "b": next_idx, "section": KIND_PRIMARY, "kind": KIND_PRIMARY})
        prev_idx = next_idx

    return spine_nodes, spine_zs, spine_xs, crossmap_z, crossmap_x, elements_spine


def build_steel_frame(data, newton_data):
    coords_fdm = newton_data["dr_result"]["coordinates"]
    built = data["built"]
    anchor_idx = data["anchor_idx"]
    eave_height = float(data["eave_height"])
    
    # =========================================================================
    # FAST STABLE LOADS: Geometric distribution based on prestress
    # =========================================================================
    n_nodes_mesh = len(coords_fdm)
    membrane_loads = np.zeros((n_nodes_mesh, 3), dtype=float)
    
    warp_q = float(data.get("warp_pretension", 20.0)) * 1000.0
    weft_q = float(data.get("weft_pretension", 20.0)) * 1000.0
    avg_pull = (warp_q + weft_q) / 2.0
    
    for ring_idx_list in built["ring_indices"]:
        for node_idx in ring_idx_list:
            membrane_loads[node_idx, 2] -= avg_pull * 0.5
            
    for cidx in built["centre_indices"]:
        membrane_loads[cidx, 2] -= avg_pull * 1.0

    edge_q = float(data.get("edge_cable_pretension", 25.0)) * 1000.0
    for anchor_mesh_idx in anchor_idx:
        px, py, pz = coords_fdm[anchor_mesh_idx]
        r = np.sqrt(px**2 + py**2)
        if r > 1e-6:
            membrane_loads[anchor_mesh_idx, 0] -= (px / r) * edge_q
            membrane_loads[anchor_mesh_idx, 1] -= (py / r) * edge_q
    # =========================================================================

    xp = data["xp"]
    zp = data["zp"]
    rib_xs = list(data["rib_x"])

    drop_zs = []
    for cidx in built["centre_indices"]:
        drop_zs.append(float(coords_fdm[int(cidx)][2]))

    target_zs = sorted(set([eave_height] + drop_zs))
    target_xs = list(rib_xs)

    spine_nodes, spine_zs, spine_xs, crossmap_z, crossmap_x, elements_spine = \
        _build_spine_with_crossings(xp, zp, target_zs, target_xs)

    nodes = list(spine_nodes)
    kinds = [KIND_PRIMARY] * len(spine_nodes)
    loads = [np.zeros(3) for _ in range(len(spine_nodes))]
    elements = list(elements_spine)

    def add(pos, kind):
        nodes.append(np.array(pos, dtype=float))
        kinds.append(kind)
        loads.append(np.zeros(3))
        return len(nodes) - 1

    for i, rib_x in enumerate(rib_xs):
        hw = data["rib_half_width"][i]
        apex_spine_idx = crossmap_x.get(float(rib_x))
        if apex_spine_idx is None:
            for idx, sx in enumerate(spine_xs):
                if abs(sx - rib_x) < 1e-9:
                    apex_spine_idx = idx
                    break
        if apex_spine_idx is None:
            continue
        apex_z = float(spine_zs[apex_spine_idx])

        n_half = 6
        y_vals_left = np.linspace(-hw, 0.0, n_half + 1)
        left_path = []
        for yv in y_vals_left[:-1]:
            u = yv / hw if hw > 0 else 0.0
            z = apex_z * (1.0 - u ** 2)
            idx = add([float(rib_x), float(yv), float(z)], KIND_RIB)
            left_path.append(idx)
        left_path.append(apex_spine_idx)

        for k in range(len(left_path) - 1):
            elements.append({"a": left_path[k], "b": left_path[k + 1], "section": KIND_RIB, "kind": KIND_RIB})

        y_vals_right = np.linspace(0.0, hw, n_half + 1)
        right_path = [apex_spine_idx]
        for yv in y_vals_right[1:]:
            u = yv / hw if hw > 0 else 0.0
            z = apex_z * (1.0 - u ** 2)
            idx = add([float(rib_x), float(yv), float(z)], KIND_RIB)
            right_path.append(idx)

        for k in range(len(right_path) - 1):
            elements.append({"a": right_path[k], "b": right_path[k+1], "section": KIND_RIB, "kind": KIND_RIB})

    fixed = []
    for i, p in enumerate(nodes):
        if abs(p[2]) < 1e-6:
            fixed.append(i)
    fixed_set = set(fixed)

    anchor_map = {}
    eave_spine_idxs = [idx for idx, sz in enumerate(spine_zs) if abs(sz - eave_height) < 1e-6]
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
            loads[best] += membrane_loads[int(mesh_idx)]

    ring_map = {}
    drop_map = {}
    for k, idx_list in enumerate(built["ring_indices"]):
        r_ids = []
        for mesh_node in idx_list:
            fid = add(coords_fdm[int(mesh_node)], KIND_RING)
            r_ids.append(fid)
            ring_map[int(mesh_node)] = fid
            loads[fid] += membrane_loads[int(mesh_node)]
        for i in range(len(r_ids)):
            a, b = r_ids[i], r_ids[(i + 1) % len(r_ids)]
            elements.append({"a": a, "b": b, "section": KIND_RING, "kind": KIND_RING})

        cidx = int(built["centre_indices"][k])
        dpos = coords_fdm[cidx]
        drop_id = add(dpos, KIND_DROP)
        drop_map[cidx] = drop_id
        loads[drop_id] += membrane_loads[cidx]

        drop_z = float(dpos[2])
        drop_spine_candidates = [idx for idx, sz in enumerate(spine_zs) if abs(sz - drop_z) < 1e-6]
        best, bestd = -1, float("inf")
        for cand_idx in drop_spine_candidates:
            d = (spine_xs[cand_idx] - dpos[0])**2
            if d < bestd:
                bestd, best = d, cand_idx
        if best >= 0:
            elements.append({"a": drop_id, "b": best, "section": KIND_DROP, "kind": KIND_DROP})

        for r_id in r_ids:
            if r_id != drop_id:
                elements.append({"a": r_id, "b": drop_id, "section": KIND_SPOKE, "kind": KIND_SPOKE})

    nodes = np.asarray(nodes, dtype=float)
    loads = np.asarray(loads, dtype=float)

    for elem in elements:
        if isinstance(elem["section"], str):
            elem["section"] = _DEFAULT_SECTION

    total_load = float(np.sum(np.abs(loads)))
    total_reaction = 0.0

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
