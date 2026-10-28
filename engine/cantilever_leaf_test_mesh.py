"""SDSe Engine - Cantilever Leaf TEST Mesh & Cable Builder.

Phase 1: 
- Exact rib tip and beam tip nodes are pinned to the steel.
- Perimeter cable nodes are free to bow.
- Interior fabric nodes are free to sag.
"""

import numpy as np
from scipy.spatial import Delaunay

def build_leaf_test_mesh(geom, membrane_tension=2000.0, cable_tension=5000.0, attached_to_spine=True):
    m = geom["membrane"]
    X, Y, Z = m["X"], m["Y"], m["Z"]
    
    # 1. Start with the base 24x24 grid
    base_pts = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    
    # 2. Inject the exact rib tips and beam tip as new nodes
    # This ensures we have nodes exactly on the steel frame for pinning
    extra_pts = []
    anchor_indices = []
    
    # Beam tip
    beam_tip = np.array([geom["beam"]["x"][-1], geom["beam"]["y"][-1], geom["beam"]["z"][-1]])
    anchor_indices.append(len(base_pts) + len(extra_pts))
    extra_pts.append(beam_tip)
    
    # Rib tips
    for rib in geom["ribs"]:
        anchor_indices.append(len(base_pts) + len(extra_pts))
        extra_pts.append(np.array(rib["left_tip"]))
        
        anchor_indices.append(len(base_pts) + len(extra_pts))
        extra_pts.append(np.array(rib["right_tip"]))
        
    # Combine base points and injected anchor points
    pts_3d = np.vstack([base_pts, extra_pts])
    pts_2d = pts_3d[:, :2]
    
    # 3. Delaunay triangulation of the combined points
    tri = Delaunay(pts_2d)
    triangles = tri.simplices
    
    # 4. Extract edges
    edges_set = set()
    for (a, b, c) in triangles:
        for (p, q) in [(a,b), (b,c), (c,a)]:
            edges_set.add((min(p,q), max(p,q)))
    edges = list(edges_set)
    
    # 5. Assign stiffness (q) based on position
    n_u, n_v = X.shape
    # The boundary nodes are the original grid's outer edges
    boundary_ids = set()
    for i in range(n_u):
        boundary_ids.add(i * n_v + 0)          
        boundary_ids.add(i * n_v + (n_v - 1))  
    for j in range(n_v):
        boundary_ids.add(0 * n_v + j)          
        boundary_ids.add((n_u - 1) * n_v + j)  
        
    q = np.zeros(len(edges))
    for k, (a, b) in enumerate(edges):
        # If the edge connects two nodes that are on the original boundary, it's a cable
        if a in boundary_ids and b in boundary_ids:
            q[k] = cable_tension 
        else:
            q[k] = membrane_tension 
            
    # 6. Apply "Free from Spine" logic
    final_edges = []
    final_q = []
    
    if not attached_to_spine:
        mid_nodes = set()
        for i in range(n_u):
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
        "fixed_indices": anchor_indices, # ONLY the injected tips are fixed
        "q": q,
    }
