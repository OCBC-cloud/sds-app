"""SDSe Engine - Cantilever Leaf Frame Builder.

Converts the 2D/3D Lab Leaf geometry into a 3D Finite Element frame.
Unlike the roof builder, the rib tips are FREE. They act as cantilever
outriggers, transferring load back to the main spine and the strut.
"""

import numpy as np

# Re-use the exact geometry we built for the Lab Tester
from viewers.figures.cantilever_leaf_lab import compute_lab_leaf_geometry

KIND_PRIMARY = "primary"
KIND_RIB = "rib"
KIND_STRUT = "spoke"  # mapped to "spoke" so the sizer knows it's a strut/tie

def build_cantilever_frame():
    geom = compute_lab_leaf_geometry()
    
    nodes = []
    elements = []
    fixed_indices = []
    
    # 1. Build the Column & Baseplate
    nodes.append(np.array([0.0, 0.0, 0.0])) # Node 0: Base
    fixed_indices.append(0)
    
    nodes.append(np.array([0.0, 0.0, 6.0])) # Node 1: Top of column
    elements.append({"a": 0, "b": 1, "section": KIND_PRIMARY, "kind": KIND_PRIMARY})
    
    # 2. Build the Main Spine (Beam)
    b = geom["beam"]
    spine_indices = []
    for i in range(len(b["x"])):
        if i == 0:
            # The spine starts at the top of the column (Node 1)
            spine_indices.append(1)
        else:
            idx = len(nodes)
            nodes.append(np.array([b["x"][i], b["y"][i], b["z"][i]]))
            spine_indices.append(idx)
            elements.append({
                "a": spine_indices[-2], 
                "b": idx, 
                "section": KIND_PRIMARY, 
                "kind": KIND_PRIMARY
            })
            
    # 3. Build the Ribs
    for rib in geom["ribs"]:
        ax, ay, az = rib["attach"]
        lx, ly, lz = rib["left_tip"]
        rx, ry, rz = rib["right_tip"]
        
        # Find the spine node closest to the attach point
        attach_node = 1
        min_dist = float('inf')
        for s_idx in spine_indices:
            dist = np.linalg.norm(nodes[s_idx] - np.array([ax, ay, az]))
            if dist < min_dist:
                min_dist = dist
                attach_node = s_idx
                
        # Left rib
        left_idx = len(nodes)
        nodes.append(np.array([lx, ly, lz]))
        elements.append({"a": attach_node, "b": left_idx, "section": KIND_RIB, "kind": KIND_RIB})
        
        # Right rib
        right_idx = len(nodes)
        nodes.append(np.array([rx, ry, rz]))
        elements.append({"a": attach_node, "b": right_idx, "section": KIND_RIB, "kind": KIND_RIB})

    # 4. Build the Strut (Backstay)
    sa = geom["strut"]["attach"]
    sb = geom["strut"]["base"]
    
    # Find spine node closest to strut attach
    strut_attach_node = spine_indices[-1]
    min_dist = float('inf')
    for s_idx in spine_indices:
        dist = np.linalg.norm(nodes[s_idx] - np.array(sa))
        if dist < min_dist:
            min_dist = dist
            strut_attach_node = s_idx

    strut_base_idx = len(nodes)
    nodes.append(np.array(sb))
    fixed_indices.append(strut_base_idx) 
    
    elements.append({"a": strut_attach_node, "b": strut_base_idx, "section": KIND_STRUT, "kind": KIND_STRUT})

    nodes = np.asarray(nodes, dtype=float)

    return {
        "nodes": nodes,
        "elements": elements,
        "fixed_indices": fixed_indices,
    }
