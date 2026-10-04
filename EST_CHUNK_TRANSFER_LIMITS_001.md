# =============================================================================
# SDSe Engine - Test Module for Chunk Transfer Limits
# =============================================================================
# This is a standalone Python module used ONLY to test whether a
# large real code file can be copied from a chat room and pasted
# into GitHub as one continuous piece.
#
# It is not part of the SDSe app. It is not imported by any viewer
# or recipe. It is not wired into run_tests.py.
#
# Delete this file after the test is complete.
#
# The code below is real, working Python. It uses only numpy. It
# contains functions, classes, nested loops, docstrings, blank
# lines, indentation at multiple levels, string literals with
# punctuation, and numeric constants. If it copies and pastes
# cleanly, then a file of this size and complexity transfers
# through the clipboard without loss.
#
# The module provides:
#   - vector and matrix helpers
#   - a small mesh topology structure
#   - area, length, normal computations
#   - a quadratic solver
#   - a gradient descent minimiser
#   - self-check functions
#
# Author: SDSe test harness.
# Date:   2026-10-04.
# =============================================================================

import math

import numpy as np


# =============================================================================
# CONSTANTS
# =============================================================================

EPS = 1e-12
TOL = 1e-9
DEG2RAD = math.pi / 180.0
RAD2DEG = 180.0 / math.pi


# =============================================================================
# VECTOR HELPERS
# =============================================================================

def normalize(v):
    """
    Return the unit vector in the direction of v.

    Raises ValueError if v is the zero vector.

    Parameters
    ----------
    v : array-like of shape (n,)

    Returns
    -------
    u : numpy array of shape (n,)
    """
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    if n <= EPS:
        raise ValueError("normalize: zero-length vector")
    return v / n


def dot(a, b):
    """Return the dot product of two vectors."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.dot(a, b))


def cross(a, b):
    """Return the 3D cross product of two vectors."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return np.cross(a, b)


def angle_between(a, b):
    """
    Return the angle between two vectors in radians.

    Uses the arccos of the normalised dot product, clamped
    to avoid numerical errors outside the valid domain of
    the arccos function.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na <= EPS or nb <= EPS:
        raise ValueError("angle_between: zero-length vector")
    c = float(np.dot(a, b)) / (na * nb)
    if c > 1.0:
        c = 1.0
    if c < -1.0:
        c = -1.0
    return float(math.acos(c))


def project_onto(v, u):
    """
    Return the projection of v onto the direction of u.

    The result is a vector parallel to u whose length is
    the component of v along u.
    """
    u = normalize(u)
    return dot(v, u) * u


def reject_from(v, u):
    """
    Return the component of v perpendicular to u.

    This is v minus its projection onto u.
    """
    return np.asarray(v, dtype=float) - project_onto(v, u)


# =============================================================================
# MATRIX HELPERS
# =============================================================================

def symmetric_part(A):
    """Return the symmetric part of a square matrix."""
    A = np.asarray(A, dtype=float)
    return 0.5 * (A + A.T)


def antisymmetric_part(A):
    """Return the antisymmetric part of a square matrix."""
    A = np.asarray(A, dtype=float)
    return 0.5 * (A - A.T)


def is_symmetric(A, tol=TOL):
    """Return True if A equals its transpose within tolerance."""
    A = np.asarray(A, dtype=float)
    return bool(np.allclose(A, A.T, atol=tol))


def is_positive_definite(A):
    """
    Return True if the symmetric matrix A is positive definite.

    Uses the Cholesky factorisation. Any matrix whose
    Cholesky factor exists is positive definite.
    """
    A = np.asarray(A, dtype=float)
    if A.shape[0] != A.shape[1]:
        return False
    try:
        np.linalg.cholesky(symmetric_part(A))
        return True
    except np.linalg.LinAlgError:
        return False


def principal_components_2x2(sigma):
    """
    Return the two principal values and the rotation angle
    of a symmetric 2x2 matrix.

    The principal values are returned in ascending order.
    The rotation angle is the angle in radians of the
    eigenvector associated with the larger principal value,
    measured counter-clockwise from the x-axis.
    """
    sigma = np.asarray(sigma, dtype=float)
    if sigma.shape != (2, 2):
        raise ValueError("principal_components_2x2: expected 2x2")
    s = symmetric_part(sigma)
    vals, vecs = np.linalg.eigh(s)
    big = vecs[:, 1]
    theta = float(math.atan2(big[1], big[0]))
    return float(vals[0]), float(vals[1]), theta


def rotation_2x2(theta):
    """Return the 2D rotation matrix for angle theta in radians."""
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s],
                     [s,  c]], dtype=float)


# =============================================================================
# SMALL QUADRATIC SOLVER
# =============================================================================

def solve_quadratic(a, b, c):
    """
    Return the real roots of a*x^2 + b*x + c = 0.

    Returns a list of zero, one, or two floats. Repeated
    roots are collapsed to a single float. Complex roots
    are discarded.
    """
    if abs(a) < EPS:
        if abs(b) < EPS:
            return []
        return [-c / b]
    disc = b * b - 4.0 * a * c
    if disc < -EPS:
        return []
    if disc < EPS:
        return [-b / (2.0 * a)]
    sq = math.sqrt(disc)
    r1 = (-b + sq) / (2.0 * a)
    r2 = (-b - sq) / (2.0 * a)
    if r1 > r2:
        r1, r2 = r2, r1
    return [r1, r2]


# =============================================================================
# TRIANGLE GEOMETRY
# =============================================================================

def triangle_area(p0, p1, p2):
    """Return the area of the triangle p0-p1-p2."""
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    e0 = p1 - p0
    e1 = p2 - p0
    return 0.5 * float(np.linalg.norm(np.cross(e0, e1)))


def triangle_normal(p0, p1, p2):
    """Return the unit normal of the triangle p0-p1-p2."""
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    n = np.cross(p1 - p0, p2 - p0)
    mag = float(np.linalg.norm(n))
    if mag <= EPS:
        raise ValueError("triangle_normal: degenerate triangle")
    return n / mag


def triangle_centroid(p0, p1, p2):
    """Return the centroid of the triangle p0-p1-p2."""
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    return (p0 + p1 + p2) / 3.0


def triangle_edge_lengths(p0, p1, p2):
    """Return the three edge lengths of the triangle."""
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    a = float(np.linalg.norm(p1 - p0))
    b = float(np.linalg.norm(p2 - p1))
    c = float(np.linalg.norm(p0 - p2))
    return a, b, c


def triangle_circumradius(p0, p1, p2):
    """Return the circumradius of the triangle."""
    a, b, c = triangle_edge_lengths(p0, p1, p2)
    area = triangle_area(p0, p1, p2)
    if area <= EPS:
        return float("inf")
    return (a * b * c) / (4.0 * area)


def triangle_inradius(p0, p1, p2):
    """Return the inradius of the triangle."""
    a, b, c = triangle_edge_lengths(p0, p1, p2)
    s = 0.5 * (a + b + c)
    area = triangle_area(p0, p1, p2)
    if s <= EPS:
        return 0.0
    return area / s


# =============================================================================
# MESH STRUCTURE
# =============================================================================

class Mesh:
    """
    A simple triangulated mesh container.

    Attributes
    ----------
    points    : (n, 3) array of node coordinates.
    triangles : (m, 3) array of triangle node indices.
    edges     : list of (i, j) unique undirected edges.
    """

    def __init__(self, points, triangles):
        self.points = np.asarray(points, dtype=float)
        self.triangles = np.asarray(triangles, dtype=int)
        self.edges = self._build_edges()

    def _build_edges(self):
        seen = set()
        out = []
        for tri in self.triangles:
            a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
            for u, v in ((a, b), (b, c), (c, a)):
                key = (min(u, v), max(u, v))
                if key in seen:
                    continue
                seen.add(key)
                out.append(key)
        return out

    def n_points(self):
        """Return the number of nodes."""
        return int(self.points.shape[0])

    def n_triangles(self):
        """Return the number of triangles."""
        return int(self.triangles.shape[0])

    def n_edges(self):
        """Return the number of edges."""
        return len(self.edges)

    def edge_lengths(self):
        """Return an array of edge lengths, in edge order."""
        out = np.zeros(len(self.edges), dtype=float)
        for k, (i, j) in enumerate(self.edges):
            out[k] = float(np.linalg.norm(self.points[j] - self.points[i]))
        return out

    def triangle_areas(self):
        """Return an array of triangle areas, in triangle order."""
        out = np.zeros(self.n_triangles(), dtype=float)
        for k, tri in enumerate(self.triangles):
            p0 = self.points[int(tri[0])]
            p1 = self.points[int(tri[1])]
            p2 = self.points[int(tri[2])]
            out[k] = triangle_area(p0, p1, p2)
        return out

    def bounding_box(self):
        """Return (min, max) corners of the axis-aligned bounding box."""
        mn = np.min(self.points, axis=0)
        mx = np.max(self.points, axis=0)
        return mn, mx

    def centroid(self):
        """Return the mean of all nodes."""
        return np.mean(self.points, axis=0)

    def adjacency(self):
        """
        Return a list of neighbour node indices for each node.

        Two nodes are neighbours if they share an edge.
        """
        n = self.n_points()
        out = [[] for _ in range(n)]
        for i, j in self.edges:
            out[i].append(j)
            out[j].append(i)
        return out

    def boundary_nodes(self):
        """
        Return a sorted list of node indices that lie on the
        boundary of the mesh.

        A node is on the boundary if the number of triangles
        that contain it is not equal to the number of edges
        around it. This is a simple version that works for
        closed and open meshes without holes.
        """
        n = self.n_points()
        edge_count = [0] * n
        for i, j in self.edges:
            edge_count[i] += 1
            edge_count[j] += 1
        tri_count = [0] * n
        for tri in self.triangles:
            for nd in tri:
                tri_count[int(nd)] += 1
        boundary = []
        for k in range(n):
            if edge_count[k] != tri_count[k]:
                boundary.append(k)
        return boundary

    def stats(self):
        """Return a dict of simple statistics about the mesh."""
        areas = self.triangle_areas()
        lengths = self.edge_lengths()
        mn, mx = self.bounding_box()
        return {
            "n_points": self.n_points(),
            "n_triangles": self.n_triangles(),
            "n_edges": self.n_edges(),
            "min_area": float(areas.min()) if areas.size else 0.0,
            "max_area": float(areas.max()) if areas.size else 0.0,
            "mean_area": float(areas.mean()) if areas.size else 0.0,
            "min_edge": float(lengths.min()) if lengths.size else 0.0,
            "max_edge": float(lengths.max()) if lengths.size else 0.0,
            "mean_edge": float(lengths.mean()) if lengths.size else 0.0,
            "bbox_min": mn.tolist(),
            "bbox_max": mx.tolist(),
        }


# =============================================================================
# GRADIENT DESCENT MINIMISER
# =============================================================================

def gradient_descent(f, grad_f, x0, lr=0.01, max_iter=1000, tol=1e-7):
    """
    Minimise f(x) starting from x0 using fixed-step gradient descent.

    Parameters
    ----------
    f       : callable, returns a float.
    grad_f  : callable, returns the gradient vector.
    x0      : (n,) starting point.
    lr      : learning rate.
    max_iter: maximum iterations.
    tol     : convergence tolerance on the gradient norm.

    Returns
    -------
    dict with keys: x, f_x, iterations, converged, history.
    """
    x = np.asarray(x0, dtype=float).copy()
    history = []
    converged = False
    for it in range(1, max_iter + 1):
        g = np.asarray(grad_f(x), dtype=float)
        gn = float(np.linalg.norm(g))
        fx = float(f(x))
        history.append((it, fx, gn))
        if gn < tol:
            converged = True
            break
        x = x - lr * g
    return {
        "x": x,
        "f_x": float(f(x)),
        "iterations": len(history),
        "converged": converged,
        "history": history,
    }


# =============================================================================
# SELF-CHECKS
# =============================================================================

def _test_vector_helpers():
    v = np.array([3.0, 4.0, 0.0])
    u = normalize(v)
    ok_norm = abs(float(np.linalg.norm(u)) - 1.0) < TOL
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 1.0, 0.0])
    ok_angle = abs(angle_between(a, b) - math.pi / 2.0) < TOL
    return ok_norm and ok_angle


def _test_matrix_helpers():
    A = np.array([[2.0, 1.0],
                  [1.0, 3.0]])
    ok_sym = is_symmetric(A)
    ok_pd = is_positive_definite(A)
    s1, s2, th = principal_components_2x2(A)
    ok_order = s1 <= s2
    return ok_sym and ok_pd and ok_order


def _test_quadratic():
    r = solve_quadratic(1.0, -3.0, 2.0)
    ok_roots = len(r) == 2 and abs(r[0] - 1.0) < TOL and abs(r[1] - 2.0) < TOL
    r2 = solve_quadratic(1.0, 0.0, 1.0)
    ok_complex = len(r2) == 0
    r3 = solve_quadratic(1.0, -2.0, 1.0)
    ok_repeat = len(r3) == 1 and abs(r3[0] - 1.0) < TOL
    return ok_roots and ok_complex and ok_repeat


def _test_mesh():
    pts = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 1.0, 0.0],
    ])
    tris = np.array([
        [0, 1, 2],
        [1, 3, 2],
    ])
    m = Mesh(pts, tris)
    ok_n = m.n_points() == 4 and m.n_triangles() == 2
    stats = m.stats()
    ok_stats = abs(stats["mean_area"] - 0.5) < TOL
    return ok_n and ok_stats


def _test_gradient_descent():
    def f(x):
        return float((x[0] - 2.0) ** 2 + (x[1] + 1.0) ** 2)

    def g(x):
        return np.array([2.0 * (x[0] - 2.0),
                         2.0 * (x[1] + 1.0)])

    res = gradient_descent(f, g, np.array([5.0, 5.0]),
                           lr=0.1, max_iter=500, tol=1e-6)
    return res["converged"] and abs(res["f_x"]) < 1e-6


def run_all_checks():
    """Run all self-checks. Return True if all pass."""
    checks = [
        ("vectors", _test_vector_helpers),
        ("matrices", _test_matrix_helpers),
        ("quadratic", _test_quadratic),
        ("mesh", _test_mesh),
        ("gradient_descent", _test_gradient_descent),
    ]
    all_ok = True
    for name, fn in checks:
        try:
            ok = bool(fn())
        except Exception as e:
            ok = False
            print("FAIL " + name + ": " + str(e))
        else:
            print(("PASS " if ok else "FAIL ") + name)
        if not ok:
            all_ok = False
    return all_ok


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("TEST_CHUNK_TRANSFER_LIMITS_002")
    print("-" * 60)
    ok = run_all_checks()
    print("-" * 60)
    print("RESULT:", "PASS" if ok else "FAIL")
