"""SDSe Engine - Cantilever Leaf TEST Mesh & Cable Builder.

Phase 1: 
- Only pins the exact rib tip and beam tip nodes.
- Cable bows freely between anchors.
- Supports "membrane free from spine" toggle.
"""

import numpy as np
from scipy.spatial import Delaunay

def build_leaf_test_mesh(geom, membrane_tension=2000.0, cable_tension=5000.0, attached_to_spine=True):
    m = geom["membrane"]
    X, Y, Z = m["X"], m["Y"], m["Z"]
    
    pts_3d = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    pts_2d = pts_3d[:, :2]
    
    # 1. Delaunay triangulation
    tri = Delaunay(pts_2d)
    triangles = tri.simplices
    
    # 2. Extract edges
    edges_set = set()
    for (a, b, c) in triangles:
        for (p, q) in [(a,b), (b,c), (c,a)]:
            edges_set.add((min(p,q), max(p,q)))
    edges = list(edges_set)
    
    # 3. Identify the true structural anchors (Rib tips and Beam tip)
    fixed_indices = []
    
    # Get exact tip coordinates from geometry
    anchor_coords = [np.array(geom["beam"]["x"][-1], dtype=object), 
                     np.array(geom["beam"]["y"][-1], dtype=object), 
                     np.array(geom["beam"]["z"][-1], dtype=object)]
    beam_tip = np.array([geom["beam"]["x"][-1], geom["beam"]["y"][-1], geom["beam"]["z"][-1]])
    
    rib_tips = []
    for rib in geom["ribs"]:
        rib_tips.append(np.array(rib["left_tip"]))
        rib_tips.append(np.array(rib["right_tip"]))
        
    # Find the mesh nodes closest to these tips and pin them
    for target in [beam_tip] + rib_tips:
        dists = np.linalg.norm(pts_3d - target, axis=1)
        closest_idx = np.argmin(dists)
        if dists[closest_idx] < 0.5: # tolerance
            fixed_indices.append(closest_idx)
            
    # 4. Assign stiffness (q)
    n_u, n_v = X.shape
    boundary_ids = set()
    for i in range(n_u):
        boundary_ids.add(i * n_v + 0)          
        boundary_ids.add(i * n_v + (n_v - 1))  
    for j in range(n_v):
        boundary_ids.add(0 * n_v + j)          
        boundary_ids.add((n_u - 1) * n_v + j)  
        
    q = np.zeros(len(edges))
    for k, (a, b) in enumerate(edges):
        if a in boundary_ids and b in boundary_ids:
            q[k] = cable_tension 
        else:
            q[k] = membrane_tension 
            
    # 5. Apply "Free from Spine" logic
    final_edges = []
    final_q = []
    
    if not attached_to_spine:
        # If free, we disconnect the middle nodes from the spine
        # (This requires identifying nodes near Y=0 and removing them)
        mid_nodes = set()
        for i in range(n_u):
            # The center of the grid is usually index n_v // 2
            mid_nodes.add(i * n_v + (n_v // 2))
            
        for k, (a, b) in enumerate(edges):
            if a not in mid_nodes and b not in mid_nodes:
                final_edges.append((a, b))
                final_q.append(q[k])
        edges = final_edges
        q = final_q
            
    return {
        "points_3d": pts_3d,
        "edges": edges,
        "fixed_indices": fixed_indices,
        "q": q,
    }
