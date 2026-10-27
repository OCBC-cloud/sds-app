"""SDSe Engine - Membrane to Steel Load Extractor.

Calculates the exact 3D force vectors that the tensioned membrane
pulls on the steel frame. This is the "bridge" between the fabric physics
and the steel frame physics.

The math:
  For any cable/edge connecting Node A and Node B with tension T (Newtons),
  the force exerted on Node A is T * (unit vector from B to A).
"""

import numpy as np


def extract_frame_loads(coords, edges, edge_forces, steel_nodes_map):
    """
    Extracts the pulling forces on the steel frame.

    Args:
        coords (np.array): (N, 3) The final settled coordinates of the membrane.
        edges (list of tuples): The mesh edges [(a, b), ...].
        edge_forces (dict or list): The tension T (Newtons) in each edge. 
                                    If a dict, keys are (a, b) sorted tuples. 
                                    If a list, matches the edges list.
        steel_nodes_map (dict): Maps membrane node index -> steel frame node index.

    Returns:
        dict: A dictionary mapping steel frame node index -> [Fx, Fy, Fz] array.
    """
    # Initialize loads for all steel nodes to zero
    steel_loads = {}
    for s_node in set(steel_nodes_map.values()):
        steel_loads[s_node] = np.zeros(3, dtype=float)

    # Ensure edge_forces is a dictionary for easy lookup
    if isinstance(edge_forces, (list, np.ndarray)):
        force_dict = {}
        for k, edge in enumerate(edges):
            key = (min(edge[0], edge[1]), max(edge[0], edge[1]))
            force_dict[key] = edge_forces[k]
    else:
        force_dict = edge_forces

    # Iterate over all edges that touch a steel node
    for edge in edges:
        a, b = edge
        key = (min(a, b), max(a, b))
        
        tension = force_dict.get(key, 0.0)
        if tension <= 0.0:
            continue  # Fabric only pulls, never pushes

        # If node A is a steel anchor, calculate force on A
        if a in steel_nodes_map:
            s_node_a = steel_nodes_map[a]
            vec = coords[a] - coords[b]
            dist = np.linalg.norm(vec)
            if dist > 1e-9:
                # Force = Tension * unit_vector
                force_on_a = tension * (vec / dist)
                steel_loads[s_node_a] += force_on_a

        # If node B is a steel anchor, calculate force on B
        if b in steel_nodes_map:
            s_node_b = steel_nodes_map[b]
            vec = coords[b] - coords[a]
            dist = np.linalg.norm(vec)
            if dist > 1e-9:
                force_on_b = tension * (vec / dist)
                steel_loads[s_node_b] += force_on_b

    return steel_loads
