# =============================================================================
# SDSe Engine - Membrane Solver
# =============================================================================
# System A of the Five Systems architecture.
#
# Handles tensile membrane analysis for any shape: saddle, cone, sail,
# umbrella, leaf, or any other tensile fabric structure.
#
# Method:
#   - Phase 1 (this file, ongoing): mesh handling + FDM form-finding
#   - Later phases: Newton-Raphson load application, stress extraction
#
# Units:
#   Length: m
#   Force: N
#   Tension (membrane): N/m
#   Stress (fabric): MPa (N/mm^2)
#
# No shape-specific code. The mesh and boundary conditions define the shape.
# =============================================================================

import math

import numpy as np


# =============================================================================
# MESH DATA STRUCTURE
# =============================================================================

def create_mesh(points, edges, boundary_tags=None):
    """
    Create a membrane mesh.

    Parameters
    ----------
    points : list of (x, y, z) tuples
        Node coordinates. z is 0 for flat 2D tests, real height for 3D.
    edges : list of (i, j) tuples
        Each edge connects node i to node j. For a membrane grid, this is
        the collection of all edges between adjacent grid nodes.
    boundary_tags : dict, optional
        Node tags. Keys are node indices, values are strings:
        "free"     - interior node, free to move
        "fixed"    - boundary node, cannot move at all
        "edge"     - edge cable node (moves with cable, not membrane)
        Default: all interior nodes are "free", all boundary nodes are "fixed".

    Returns
    -------
    mesh : dict
        {
          "n_nodes": int,
          "n_edges": int,
          "points": list of (x, y, z),
          "edges": list of (i, j),
          "tags": dict of {node_index: tag},
          "free_indices": list of int,
          "fixed_indices": list of int,
        }
    """
    n_nodes = len(points)
    n_edges = len(edges)

    # Default tags: interior = free, boundary = fixed
    # Boundary = nodes that appear in an edge but not the "middle" of the mesh
    if boundary_tags is None:
        # Detect boundary nodes: nodes that appear only once in a specific
        # direction, or (simpler) nodes that are on the convex hull of the
        # xy projection. For a grid, we detect by checking the number of
        # neighbours.
        neighbours = {i: set() for i in range(n_nodes)}
        for (i, j) in edges:
            neighbours[i].add(j)
            neighbours[j].add(i)

        tags = {}
        for i in range(n_nodes):
            # A boundary node has fewer neighbours than a typical interior node.
            # For a grid, this is a heuristic; better detection comes later.
            if len(neighbours[i]) <= 3:
                tags[i] = "fixed"
            else:
                tags[i] = "free"
    else:
        tags = dict(boundary_tags)

    free_indices = [i for i in range(n_nodes) if tags.get(i, "free") == "free"]
    fixed_indices = [i for i in range(n_nodes) if tags.get(i, "fixed") == "fixed"]

    return {
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "points": list(points),
        "edges": list(edges),
        "tags": tags,
        "free_indices": free_indices,
        "fixed_indices": fixed_indices,
    }


# =============================================================================
# GEOMETRY UTILITIES
# =============================================================================

def edge_length(p1, p2):
    """Euclidean length between two 3D points."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def edge_vector(p1, p2):
    """Unit vector from p1 to p2. Returns (0,0,0) if points are identical."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-12:
        return (0.0, 0.0, 0.0)
    return (dx / length, dy / length, dz / length)


def all_edge_lengths(mesh):
    """Return list of lengths, one per edge, in order."""
    lengths = []
    for (i, j) in mesh["edges"]:
        lengths.append(edge_length(mesh["points"][i], mesh["points"][j]))
    return lengths


def count_neighbours(mesh):
    """Return dict {node_index: number_of_neighbours}."""
    neighbours = {i: 0 for i in range(mesh["n_nodes"])}
    for (i, j) in mesh["edges"]:
        neighbours[i] += 1
        neighbours[j] += 1
    return neighbours


# =============================================================================
# MESH BUILDERS - SIMPLE GRIDS
# =============================================================================

def build_flat_grid(nx, ny, lx, ly, z=0.0):
    """
    Build a flat rectangular grid mesh.

    Parameters
    ----------
    nx : int - number of nodes in x direction (>= 2)
    ny : int - number of nodes in y direction (>= 2)
    lx : float - length in x direction (m)
    ly : float - length in y direction (m)
    z : float - z coordinate (default 0, for flat tests)

    Returns
    -------
    mesh : dict (from create_mesh)
    """
    if nx < 2 or ny < 2:
        raise ValueError("Grid must be at least 2x2 nodes.")

    points = []
    for j in range(ny):
        for i in range(nx):
            x = lx * i / (nx - 1)
            y = ly * j / (ny - 1)
            points.append((x, y, z))

    edges = []
    # Horizontal edges
    for j in range(ny):
        for i in range(nx - 1):
            a = j * nx + i
            b = j * nx + (i + 1)
            edges.append((a, b))
    # Vertical edges
    for j in range(ny - 1):
        for i in range(nx):
            a = j * nx + i
            b = (j + 1) * nx + i
            edges.append((a, b))

    # Tag boundary nodes as fixed, interior as free
    tags = {}
    for j in range(ny):
        for i in range(nx):
            idx = j * nx + i
            is_boundary = (i == 0) or (i == nx - 1) or (j == 0) or (j == ny - 1)
            tags[idx] = "fixed" if is_boundary else "free"

    return create_mesh(points, edges, tags)


# =============================================================================
# SELF-TEST - MESH HANDLING
# =============================================================================

def _verify_mesh_handling():
    """
    Verify basic mesh operations. Not a physics test - just data handling.
    Returns dict with test results.
    """
    results = {}

    # Test 1: edge length
    p1 = (0.0, 0.0, 0.0)
    p2 = (3.0, 4.0, 0.0)
    L = edge_length(p1, p2)
    results["edge_length_3_4_5"] = L
    results["edge_length_ok"] = abs(L - 5.0) < 1e-9

    # Test 2: unit vector
    v = edge_vector((0.0, 0.0, 0.0), (10.0, 0.0, 0.0))
    results["unit_vector_x"] = v
    results["unit_vector_ok"] = abs(v[0] - 1.0) < 1e-9 and abs(v[1]) < 1e-9

    # Test 3: flat grid construction
    mesh = build_flat_grid(nx=3, ny=3, lx=2.0, ly=2.0)
    results["grid_nodes"] = mesh["n_nodes"]
    results["grid_edges"] = mesh["n_edges"]
    results["grid_nodes_ok"] = mesh["n_nodes"] == 9
    results["grid_edges_ok"] = mesh["n_edges"] == 12  # 3x2 horizontal + 2x3 vertical

    # Test 4: boundary detection
    # 3x3 grid: 8 boundary nodes, 1 interior
    results["grid_free_count"] = len(mesh["free_indices"])
    results["grid_fixed_count"] = len(mesh["fixed_indices"])
    results["grid_boundary_ok"] = (
        len(mesh["free_indices"]) == 1 and len(mesh["fixed_indices"]) == 8
    )

    # Test 5: neighbour count on interior node
    neighbours = count_neighbours(mesh)
    # Interior node (index 4, the center) should have 4 neighbours
    results["interior_neighbours"] = neighbours[4]
    results["interior_neighbours_ok"] = neighbours[4] == 4

    # Test 6: mesh edge lengths
    lengths = all_edge_lengths(mesh)
    # For a 3x3 grid over 2m x 2m, all edges are 1m long
    results["uniform_edge_lengths"] = all(abs(L - 1.0) < 1e-9 for L in lengths)
    results["edge_lengths_ok"] = results["uniform_edge_lengths"]

    # Overall pass
    results["pass"] = (
        results["edge_length_ok"]
        and results["unit_vector_ok"]
        and results["grid_nodes_ok"]
        and results["grid_edges_ok"]
        and results["grid_boundary_ok"]
        and results["interior_neighbours_ok"]
        and results["edge_lengths_ok"]
    )

    return results


# =============================================================================
# ENTRY POINT FOR SELF-TEST
# =============================================================================

if __name__ == "__main__":
    print("engine/membrane.py - Phase 4A Message 1 - mesh handling verification")
    print("-" * 70)

    res = _verify_mesh_handling()

    print("Edge length test (3,4,0) -> expected 5.0, got %.6f" % res["edge_length_3_4_5"])
    print("Edge length OK      :", res["edge_length_ok"])

    print("Unit vector test    :", res["unit_vector_x"])
    print("Unit vector OK      :", res["unit_vector_ok"])

    print("Grid nodes          :", res["grid_nodes"], "(expected 9)")
    print("Grid edges          :", res["grid_edges"], "(expected 12)")
    print("Grid nodes OK       :", res["grid_nodes_ok"])
    print("Grid edges OK       :", res["grid_edges_ok"])

    print("Free nodes          :", res["grid_free_count"], "(expected 1)")
    print("Fixed nodes         :", res["grid_fixed_count"], "(expected 8)")
    print("Boundary OK         :", res["grid_boundary_ok"])

    print("Interior neighbours :", res["interior_neighbours"], "(expected 4)")
    print("Interior OK         :", res["interior_neighbours_ok"])

    print("Uniform edge lengths:", res["uniform_edge_lengths"])
    print("Edge lengths OK     :", res["edge_lengths_ok"])

    print("-" * 70)
    if res["pass"]:
        print("MESSAGE 1 GATE: PASS")
    else:
        print("MESSAGE 1 GATE: FAIL - investigate above")
