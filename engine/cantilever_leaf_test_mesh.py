"""SDSe Engine - Cantilever Leaf TEST Mesh & Cable Builder."""

import numpy as np
from scipy.spatial import Delaunay

def build_leaf_test_mesh(geom, membrane_tension=2000.0, cable_tension=5000.0):
    m = geom["membrane"]
    X, Y, Z = m["X"], m["Y"], m["Z"]
    
    pts_3d = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    pts_2d = pts_3d[:, :2]
    
    tri = Delaunay(pts_2d)
    triangles = tri.simplices
    
    edges_set = set()
    for (a, b, c) in triangles:
        for (p, q) in [(a,b), (b,c), (c,a)]:
            edges_set.add((min(p,q), max(p,q)))
    edges = list(edges_set)
    
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
            
    fixed_indices = list(boundary_ids)
            
    return {
        "points_3d": pts_3d,
        "edges": edges,
        "fixed_indices": fixed_indices,
        "q": q,
    }
