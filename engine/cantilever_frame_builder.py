import numpy as np
from viewers.figures.cantilever_leaf_lab import compute_lab_leaf_geometry

KIND_PRIMARY = "primary"
KIND_RIB = "rib"
KIND_STRUT = "spoke"

def build_cantilever_frame(col_h, outreach, half_width_mid, rib_tilt_deg, arc_r, strut_joint, strut_angle, ribs_per_side):
    geom = compute_lab_leaf_geometry(col_h, outreach, half_width_mid, rib_tilt_deg, arc_r, strut_joint, strut_angle, ribs_per_side)
    
    nodes = [np.array([0.0, 0.0, 0.0])] # Node 0: Base
    fixed_indices = [0]
    
    nodes.append(np.array([0.0, 0.0, strut_joint])) # Node 1: Strut Joint
    nodes.append(np.array([0.0, 0.0, col_h]))       # Node 2: Top of Column
    
    elements = [
        {"a": 0, "b": 1, "section": KIND_PRIMARY, "kind": KIND_PRIMARY},
        {"a": 1, "b": 2, "section": KIND_PRIMARY, "kind": KIND_PRIMARY}
    ]
    
    # Spine
    b = geom["beam"]
    spine_indices = [2]
    for i in range(1, len(b["x"])):
        idx = len(nodes)
        nodes.append(np.array([b["x"][i], b["y"][i], b["z"][i]]))
        spine_indices.append(idx)
        elements.append({"a": spine_indices[-2], "b": idx, "section": KIND_PRIMARY, "kind": KIND_PRIMARY})
        
    # Ribs
    for rib in geom["ribs"]:
        ax, ay, az = rib["attach"]
        attach_node = spine_indices[np.argmin(np.linalg.norm(np.array(nodes)[spine_indices] - np.array([ax, ay, az]), axis=1))]
        
        l_idx = len(nodes)
        nodes.append(np.array(rib["left_tip"]))
        elements.append({"a": attach_node, "b": l_idx, "section": KIND_RIB, "kind": KIND_RIB})
        
        r_idx = len(nodes)
        nodes.append(np.array(rib["right_tip"]))
        elements.append({"a": attach_node, "b": r_idx, "section": KIND_RIB, "kind": KIND_RIB})

    # Strut
    sa = geom["strut"]["attach"]
    strut_attach_node = spine_indices[np.argmin(np.linalg.norm(np.array(nodes)[spine_indices] - np.array(sa), axis=1))]
    elements.append({"a": strut_attach_node, "b": 1, "section": KIND_STRUT, "kind": KIND_STRUT})

    return {"nodes": np.asarray(nodes, dtype=float), "elements": elements, "fixed_indices": fixed_indices}
