"""SDSe Engine — 3D Steel Frame Builder (Exact Crossing Fusion).

Builds the 3D steel frame from mesh data using REAL reaction forces from the NFDM solver.
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
    # REAL LOADS: Pull the exact residual forces from the solver!
    # =========================================================================
    # newton_data["dr_result"] now contains the "reactions" from v5.5
    raw_reactions = newton_data["dr_result"].get("reactions", None)
    
    if raw_reactions is None or len(raw_reactions) != len(coords_fdm):
        # Fallback if reactions are missing
        membrane_loads = np.zeros_like(coords_fdm)
    else:
        membrane_loads = np.asarray(raw_reactions, dtype=float)
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

    # --- Ribs ---
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

    # --- Fix Z=0 baseplates ---
    fixed = []
    for i, p in enumerate(nodes):
        if abs(p[2]) < 1e-6:
            fixed.append(i)
    fixed_set = set(fixed)

    # --- Eave anchors ---
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
            # APPLY REAL LOAD
            loads[best] += membrane_loads[int(mesh_idx)]

    # --- Rings, drops, spokes ---
    ring_map = {}
    drop_map = {}
    for k, idx_list in enumerate(built["ring_indices"]):
        r_ids = []
        for mesh_node in idx_list:
            fid = add(coords_fdm[int(mesh_node)], KIND_RING)
            r_ids.append(fid)
            ring_map[int(mesh_node)] = fid
            # APPLY REAL LOAD
            loads[fid] += membrane_loads[int(mesh_node)]
        for i in range(len(r_ids)):
            a, b = r_ids[i], r_ids[(i + 1) % len(r_ids)]
            elements.append({"a": a, "b": b, "section": KIND_RING, "kind": KIND_RING})

        cidx = int(built["centre_indices"][k])
        dpos = coords_fdm[cidx]
        drop_id = add(dpos, KIND_DROP)
        drop_map[cidx] = drop_id
        # APPLY REAL LOAD
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
    if membrane_loads is not None:
        for m in list(anchor_map) + list(ring_map) + list(drop_map):
            total_reaction += float(np.linalg.norm(membrane_loads[m]))

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
