# =============================================================================
# SDSe Engine - 3D Frame Analysis Solver (Matrix Stiffness Method)
# =============================================================================
# This file solves the 3D frame using true stiffness matrices.
# It calculates displacements, reactions, and member end forces 
# (Axial, Shear, Moment, Torsion) for every element.
# =============================================================================

import numpy as np

EPS = 1e-12

def _element_stiffness_matrix_3d(E, G, A, Iy, Iz, J, L):
    """Returns the 12x12 local stiffness matrix for a 3D beam element."""
    if L < EPS:
        return np.zeros((12, 12))
    k_axial = E * A / L
    k_torsion = G * J / L
    k_bend_y = E * Iy / L**3
    k_bend_z = E * Iz / L**3

    K = np.zeros((12, 12), dtype=float)

    # Axial
    K[0, 0] = k_axial
    K[0, 6] = -k_axial
    K[6, 0] = -k_axial
    K[6, 6] = k_axial

    # Torsion
    K[3, 3] = k_torsion
    K[3, 9] = -k_torsion
    K[9, 3] = -k_torsion
    K[9, 9] = k_torsion

    # Bending about Y
    K[1, 1] = 12 * k_bend_y
    K[1, 5] = 6 * L * k_bend_y
    K[1, 7] = -12 * k_bend_y
    K[1, 11] = 6 * L * k_bend_y
    K[5, 1] = 6 * L * k_bend_y
    K[5, 5] = 4 * L**2 * k_bend_y
    K[5, 7] = -6 * L * k_bend_y
    K[5, 11] = 2 * L**2 * k_bend_y
    K[7, 1] = -12 * k_bend_y
    K[7, 5] = -6 * L * k_bend_y
    K[7, 7] = 12 * k_bend_y
    K[7, 11] = -6 * L * k_bend_y
    K[11, 1] = 6 * L * k_bend_y
    K[11, 5] = 2 * L**2 * k_bend_y
    K[11, 7] = -6 * L * k_bend_y
    K[11, 11] = 4 * L**2 * k_bend_y

    # Bending about Z
    K[2, 2] = 12 * k_bend_z
    K[2, 4] = -6 * L * k_bend_z
    K[2, 8] = -12 * k_bend_z
    K[2, 10] = -6 * L * k_bend_z
    K[4, 2] = -6 * L * k_bend_z
    K[4, 4] = 4 * L**2 * k_bend_z
    K[4, 8] = 6 * L * k_bend_z
    K[4, 10] = 2 * L**2 * k_bend_z
    K[8, 2] = -12 * k_bend_z
    K[8, 4] = 6 * L * k_bend_z
    K[8, 8] = 12 * k_bend_z
    K[8, 10] = 6 * L * k_bend_z
    K[10, 2] = -6 * L * k_bend_z
    K[10, 4] = 2 * L**2 * k_bend_z
    K[10, 8] = 6 * L * k_bend_z
    K[10, 10] = 4 * L**2 * k_bend_z

    return K

def _transformation_matrix(p1, p2):
    """Returns the 12x12 transformation matrix from local to global."""
    d = p2 - p1
    L = float(np.linalg.norm(d))
    if L < EPS:
        return np.eye(12)

    x_local = d / L
    
    # Choose a global up vector to avoid gimbal lock
    if abs(x_local[2]) < 0.9:
        v = np.array([0.0, 0.0, 1.0])
    else:
        v = np.array([1.0, 0.0, 0.0])
        
    y_local = np.cross(v, x_local)
    y_local = y_local / (np.linalg.norm(y_local) + EPS)
    z_local = np.cross(x_local, y_local)

    R = np.array([x_local, y_local, z_local], dtype=float)
    T = np.zeros((12, 12), dtype=float)
    for i in range(4):
        T[3*i:3*i+3, 3*i:3*i+3] = R
    return T

def solve_frame_analysis(topology, loads, section_props, grade_props):
    """
    Solves the 3D frame and returns displacements, reactions, and member forces.
    """
    nodes = topology["nodes"]
    elements = topology["elements"]
    fixed_nodes = topology["fixed_indices"]
    
    n_nodes = nodes.shape[0]
    n_dof = 6 * n_nodes

    E = grade_props.get("E", 210000.0) * 1e6
    G = grade_props.get("G", E / (2 * (1 + 0.3)))

    K_global = np.zeros((n_dof, n_dof), dtype=float)
    F_global = np.zeros(n_dof, dtype=float)

    # Assemble Global Force Vector
    for i in range(n_nodes):
        for j in range(3):
            F_global[6*i + j] = loads[i, j]

    # Assemble Global Stiffness Matrix
    for elem in elements:
        a = elem["a"]
        b = elem["b"]
        kind = elem["kind"]
        
        sec = section_props.get(kind, section_props.get("primary"))
        
        L = float(np.linalg.norm(nodes[b] - nodes[a]))
        if L < EPS:
            continue
            
        K_local = _element_stiffness_matrix_3d(
            E, G, sec["A"], sec.get("Iy", sec["I"]), sec.get("Iz", sec["I"]), sec.get("J", sec["I"] * 2), L
        )
        T = _transformation_matrix(nodes[a], nodes[b])
        K_global_elem = T.T @ K_local @ T

        # Add to Global Matrix
        for i in range(12):
            for j in range(12):
                gi = 6 * (a if i < 6 else b) + (i % 6)
                gj = 6 * (a if j < 6 else b) + (j % 6)
                K_global[gi, gj] += K_global_elem[i, j]

    # Apply Boundary Conditions (Fixed Baseplates)
    fixed_set = set(int(i) for i in fixed_nodes)
    free_dofs = []
    for i in range(n_nodes):
        if i not in fixed_set:
            for j in range(6):
                free_dofs.append(6 * i + j)
                
    free_dofs = np.array(free_dofs, dtype=int)

    if len(free_dofs) == 0:
        return {"displacements": np.zeros(n_dof), "reactions": np.zeros((n_nodes, 6)), "member_end_forces": []}

    # Solve the system K_ff * u_f = F_f
    K_ff = K_global[np.ix_(free_dofs, free_dofs)]
    F_f = F_global[free_dofs]

    try:
        u_f = np.linalg.solve(K_ff, F_f)
    except np.linalg.LinAlgError:
        try:
            u_f, _, _, _ = np.linalg.lstsq(K_ff, F_f, rcond=None)
        except Exception:
            u_f = np.zeros_like(F_f)

    # Reconstruct full displacement vector
    u_global = np.zeros(n_dof)
    u_global[free_dofs] = u_f

    # Calculate Reactions at Fixed Nodes
    R_global = K_global @ u_global - F_global
    reactions = np.zeros((n_nodes, 6))
    for i in range(n_nodes):
        if i in fixed_set:
            for j in range(6):
                reactions[i, j] = R_global[6*i + j]

    # Calculate Member End Forces (Axial, Shear, Moment, Torsion)
    member_end_forces = []
    for elem in elements:
        a = elem["a"]
        b = elem["b"]
        kind = elem["kind"]
        sec = section_props.get(kind, section_props.get("primary"))
        
        L = float(np.linalg.norm(nodes[b] - nodes[a]))
        if L < EPS:
            member_end_forces.append({"a": a, "b": b, "N": 0.0, "V_y": 0.0, "V_z": 0.0, "My_a": 0.0, "My_b": 0.0, "Mz_a": 0.0, "Mz_b": 0.0, "T": 0.0})
            continue
            
        K_local = _element_stiffness_matrix_3d(
            E, G, sec["A"], sec.get("Iy", sec["I"]), sec.get("Iz", sec["I"]), sec.get("J", sec["I"] * 2), L
        )
        T = _transformation_matrix(nodes[a], nodes[b])
        elem_dofs = list(range(6 * a, 6 * a + 6)) + list(range(6 * b, 6 * b + 6))
        
        u_elem = u_global[elem_dofs]
        u_local = T @ u_elem
        f_local = K_local @ u_local
        
        member_end_forces.append({
            "a": a, "b": b, "kind": kind,
            "N": f_local[0],           # Axial
            "V_y": f_local[1],         # Shear Y
            "V_z": f_local[2],         # Shear Z
            "T": f_local[3],           # Torsion
            "My_a": f_local[4], "My_b": f_local[10],  # Moment about Y
            "Mz_a": f_local[5], "Mz_b": f_local[11],  # Moment about Z
        })

    return {
        "displacements": u_global,
        "reactions": reactions,
        "member_end_forces": member_end_forces,
    }
