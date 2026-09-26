# =============================================================================
# SDSe Fluid Design Studio - MBS Tester Workshop
# =============================================================================
# Temporary research page. Tests the Membrane Boundary Schema engine
# across multiple shapes using the same nine-step pipeline.
#
# Doctrine (2026-09-26):
#   - The user supplies corners / parameters only. The engine derives
#     everything else: edge nodes, interior grid, mesh, solve.
#   - Segments N is the user's number of segments. Not converted.
#   - Mesh density is Mode A (fixed K) or Mode B (target ds metres).
#   - Focal point = centroid of boundary nodes in x-y, solved z.
#   - Every boundary node is held rigid (Stage 1 doctrine).
#   - Same parameters on every shape. Only the boundary changes.
#
# Shapes implemented in this file:
#   Lens      - two beam curves meeting at two tips.
#   Triangle  - three corners, three edges, user-editable corner xyz.
#   Crown     - N parabolic beams on an imaginary ground circle, with
#               a single membrane inside. Centre is a free point solved
#               by FDM. Apex tilt angle controls lean outward/inward.
#
# Shapes deferred to later passes:
#   Square, Circle, Tri-lobe with centre opening.
#
# Status: EXPERIMENTAL.
# =============================================================================

import numpy as np
import streamlit as st


# ---- Defaults -------------------------------------------------------------
DEFAULT_SEGMENTS = 7
DEFAULT_K = 5
DEFAULT_DS = 0.5
DEFAULT_WARP_Q = 2.0
DEFAULT_WEFT_Q = 2.0

# ---- Lens recipe constants ------------------------------------------------
LENS_SPAN = 3.0
LENS_APEX_WIDTH = 4.0
LENS_RISE = 1.5
LENS_SAG_FRACTION = 0.10

# ---- Triangle defaults ----------------------------------------------------
TRI_A_DEFAULT = (-1.5, -1.5, 0.0)
TRI_B_DEFAULT = ( 1.5, -1.5, 0.0)
TRI_C_DEFAULT = ( 0.0,  1.5, 1.5)

# ---- Crown defaults -------------------------------------------------------
CROWN_R_DEFAULT = 8.0
CROWN_N_DEFAULT = 3
CROWN_H_DEFAULT = 6.0
CROWN_THETA_DEFAULT = 90.0
CROWN_ROT_DEFAULT = 0.0
CROWN_CENTRE_RADIUS_DEFAULT = 0.0
CROWN_SAG_DEFAULT = 0.10


# =============================================================================
# MESH DENSITY HELPERS
# =============================================================================

def _nodes_per_edge(n_segments, edge_length, mode, K, ds):
    """
    Return total nodes along one edge and their fractions.

    The edge is divided into N equal segments. Each segment is then
    subdivided according to mode:
      Mode A (fixed K): K interior nodes per segment (K+1 sub-intervals).
      Mode B (target ds): K_i = max(1, round(seg_len / ds) - 1).
    """
    if n_segments < 1:
        n_segments = 1
    seg_len = float(edge_length) / float(n_segments)

    fractions = [0.0]
    for s in range(n_segments):
        if mode == "A":
            K_seg = max(1, int(K))
        else:
            K_seg = max(1, int(round(seg_len / float(ds))) - 1)

        n_sub = K_seg + 1
        seg_start = s / float(n_segments)
        for k in range(1, n_sub + 1):
            fractions.append(seg_start + k * (1.0 / n_segments) / n_sub)

    fractions = np.array(fractions, dtype=float)
    fractions[-1] = 1.0
    return len(fractions), fractions


def _resample_polyline(points, n_target):
    """Resample a polyline by arc length into n_target points."""
    pts = np.asarray(points, dtype=float)
    if len(pts) < 2:
        return np.tile(pts[0] if len(pts) else [0, 0, 0], (n_target, 1))
    diff = np.diff(pts, axis=0)
    seg = np.linalg.norm(diff, axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg)))
    total = float(s[-1])
    if total < 1e-9:
        return np.tile(pts[0], (n_target, 1))
    out = np.zeros((n_target, 3))
    for k in range(n_target):
        target = (k / (n_target - 1.0)) * total
        idx = int(np.searchsorted(s, target, side="right") - 1)
        idx = max(0, min(idx, len(pts) - 2))
        a = s[idx]
        b = s[idx + 1]
        if b - a < 1e-12:
            out[k] = pts[idx]
        else:
            t = (target - a) / (b - a)
            out[k] = pts[idx] * (1.0 - t) + pts[idx + 1] * t
    return out


# =============================================================================
# SHAPE RECIPES
# =============================================================================
# Each recipe returns:
#   (grid, boundary, anchor_indices, edge_types)
# grid           : (nx, ny, 3) initial surface, or None for TFI
# boundary       : (M, 3) closed loop of 3D points
# anchor_indices : list of ints into boundary
# edge_types     : list of "beam" or "cable" per anchor

def _build_lens_recipe(n_segments, mode, K, ds):
    """Lens - two beam curves meeting at two tips."""
    from viewers.figures._shared import beam_curve
    from engine.membrane_surface import build_surface

    n_anchors = int(n_segments) + 1
    subdivisions = int(K) if mode == "A" else 5
    n_v = 8

    x_dense = np.linspace(-LENS_SPAN / 2.0, LENS_SPAN / 2.0, 400)
    z_dense = beam_curve(x_dense, LENS_SPAN, LENS_RISE, "parabolic")

    base_width = LENS_APEX_WIDTH * 0.5
    y_L_dense = -base_width * (1.0 - (2.0 * x_dense / LENS_SPAN) ** 2)
    y_R_dense = base_width * (1.0 - (2.0 * x_dense / LENS_SPAN) ** 2)
    y_L_dense[0] = 0.0
    y_L_dense[-1] = 0.0
    y_R_dense[0] = 0.0
    y_R_dense[-1] = 0.0

    beam_L = np.column_stack((x_dense, y_L_dense, z_dense))
    beam_R = np.column_stack((x_dense, y_R_dense, z_dense))

    grid = build_surface(
        beam_L_points=beam_L,
        beam_R_points=beam_R,
        n_anchors=n_anchors,
        subdivisions_per_segment=subdivisions,
        n_v=n_v,
        sag_fraction=LENS_SAG_FRACTION,
        taper_ends=True,
    )

    nx = grid.shape[0]
    boundary_list = [grid[0, 0]]
    for i in range(1, nx - 1):
        boundary_list.append(grid[i, 0])
    boundary_list.append(grid[nx - 1, 0])
    for i in range(nx - 2, 0, -1):
        boundary_list.append(grid[i, n_v - 1])

    boundary = np.array(boundary_list, dtype=float)
    anchors = list(range(len(boundary)))
    edge_types = ["beam"] * len(boundary)
    return grid, boundary, anchors, edge_types


def _build_triangle_recipe(corner_A, corner_B, corner_C,
                            n_segments, mode, K, ds):
    """Triangle - three corners, three straight edges."""
    corners = [np.asarray(corner_A, dtype=float),
               np.asarray(corner_B, dtype=float),
               np.asarray(corner_C, dtype=float)]

    boundary_pts = []
    for e in range(3):
        p0 = corners[e]
        p1 = corners[(e + 1) % 3]
        edge_length = float(np.linalg.norm(p1 - p0))
        n_nodes, fractions = _nodes_per_edge(
            n_segments, edge_length, mode, K, ds
        )
        for f in fractions[:-1]:
            boundary_pts.append(p0 * (1.0 - f) + p1 * f)

    boundary = np.array(boundary_pts, dtype=float)
    anchors = list(range(len(boundary)))
    edge_types = ["beam"] * len(boundary)

    if mode == "A":
        K_use = max(1, int(K))
    else:
        lengths = [float(np.linalg.norm(corners[(e + 1) % 3] - corners[e]))
                   for e in range(3)]
        avg_len = float(np.mean(lengths))
        seg_len_avg = avg_len / float(max(1, n_segments))
        K_use = max(1, int(round(seg_len_avg / float(ds))) - 1)

    nx = n_segments + (n_segments - 1) * K_use + 1
    ny = 8

    grid = np.zeros((nx, ny, 3))
    for i in range(nx):
        u = i / (nx - 1.0)
        for j in range(ny):
            v = j / (ny - 1.0)
            wA = max(0.0, 1.0 - u - v)
            wB = max(0.0, u)
            wC = max(0.0, v)
            total = wA + wB + wC
            if total < 1e-9:
                wA, wB, wC = 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0
            else:
                wA /= total
                wB /= total
                wC /= total
            pt = wA * corners[0] + wB * corners[1] + wC * corners[2]
            grid[i, j] = pt

    return grid, boundary, anchors, edge_types


# =============================================================================
# CROWN RECIPE
# =============================================================================
# A ring of N parabolic beams arranged around an imaginary ground circle,
# with a single membrane filling inside. The centre is a free point solved
# by FDM (no user-supplied centre height).
#
# Apex tilt angle theta (from horizontal):
#   theta = 90  -> apex straight up.
#   theta < 90  -> apex leans radially outward.
#   theta > 90  -> apex leans radially inward.
#
# The ground circle is a construction aid only. It is not drawn and is
# not part of the boundary. Only the N beams form the membrane boundary.

def _build_beam_parabola(p_support_a, p_apex, p_support_b, n_points):
    """
    Build a parabolic beam from support A through apex to support B.
    Returns n_points points along the curve.
    Simple formulation: quadratic Bezier-like with the apex as the
    controlling vertex. Symmetric about the apex.
    """
    A = np.asarray(p_support_a, dtype=float)
    B = np.asarray(p_apex, dtype=float)
    C = np.asarray(p_support_b, dtype=float)

    t = np.linspace(0.0, 1.0, n_points)
    # Two linear pieces joined with a parabolic correction.
    p_lin = np.outer(1.0 - t, A) + np.outer(t, C)
    # Parabolic lift that peaks at t = 0.5 and matches apex deviation.
    middle = 0.5 * (A + C)
    lift = B - middle
    profile = 4.0 * t * (1.0 - t)  # 0 at ends, 1 at middle
    p = p_lin + np.outer(profile, lift)
    return p


def _build_crown_recipe(R, N, H, theta_deg, rot_deg,
                        n_segments, mode, K, ds,
                        centre_radius=0.0,
                        sag_fraction=CROWN_SAG_DEFAULT):
    """
    Build the crown: N beams on an imaginary ground circle, membrane
    inside, centre solved as a free point.

    Returns (grid, boundary, anchor_indices, edge_types).
    """
    R = float(R)
    N = int(max(3, N))
    H = float(H)
    theta = np.radians(float(theta_deg))
    rot = np.radians(float(rot_deg))

    # ---- Support points on the imaginary circle.
    supports = []
    for k in range(N):
        ang = rot + 2.0 * np.pi * k / float(N)
        x = R * np.cos(ang)
        y = R * np.sin(ang)
        supports.append(np.array([x, y, 0.0]))

    # ---- Apex position for each beam (midpoint of arc between supports).
    # Radial offset by H / tan(theta). If theta near 90, offset -> 0.
    if abs(np.sin(theta)) < 1e-6:
        # Vertical apex: no radial offset.
        radial_offset = 0.0
    else:
        radial_offset = H / np.tan(theta)

    apexes = []
    for k in range(N):
        a = supports[k]
        b = supports[(k + 1) % N]
        mid_ang = rot + 2.0 * np.pi * (k + 0.5) / float(N)
        mid_r = R + radial_offset
        mx = mid_r * np.cos(mid_ang)
        my = mid_r * np.sin(mid_ang)
        apexes.append(np.array([mx, my, H]))

    # ---- Grid dimensions.
    # Angular resolution: total number of boundary node slots, one beam
    # per edge length. Use the beam's own arc length for density.
    if mode == "A":
        K_use = max(1, int(K))
    else:
        # Average edge length across the N beams.
        lens = []
        for k in range(N):
            a = supports[k]
            b = supports[(k + 1) % N]
            L = float(np.linalg.norm(b - a))
            lens.append(L)
        avg_len = float(np.mean(lens))
        seg_len_avg = avg_len / float(max(1, n_segments))
        K_use = max(1, int(round(seg_len_avg / float(ds))) - 1)

    # Points per beam curve (dense sampling for the initial surface).
    samples_per_beam = 40
    # Grid resolution: nx around the ring, ny radially inward.
    nx = N * (n_segments + (n_segments - 1) * K_use)
    if nx < 3 * N:
        nx = 3 * N
    ny = max(8, n_segments + 2)

    # ---- Build each beam curve, sampled densely.
    beam_curves = []
    for k in range(N):
        a = supports[k]
        b = supports[(k + 1) % N]
        apex = apexes[k]
        curve = _build_beam_parabola(a, apex, b, samples_per_beam)
        beam_curves.append(curve)

    # ---- Boundary: concatenate the N beams, skipping duplicated joins.
    boundary_pts = []
    for k in range(N):
        curve = beam_curves[k]
        # Skip the last point of each beam (it equals the first of the next).
        for p in curve[:-1]:
            boundary_pts.append(p)
    boundary = np.array(boundary_pts, dtype=float)
    anchors = list(range(len(boundary)))
    edge_types = ["beam"] * len(boundary)

    # ---- Initial surface grid: (nx, ny).
    # i indexes around the ring, j indexes radially inward.
    # At j = 0, points sit on the boundary (beams).
    # At j = ny-1, all points converge to the centre.
    #
    # Centre is the mean of the supports, at a height derived from the
    # sag profile. The FDM solve will move it to equilibrium.
    centre_xy = np.mean(np.array(supports), axis=0)
    centre_z_guess = H * (1.0 - sag_fraction)
    centre_pt = np.array([centre_xy[0], centre_xy[1], centre_z_guess])

    # Build the boundary as a resampled ring of nx points for smooth
    # interpolation from boundary to centre.
    boundary_ring = _resample_polyline(
        np.vstack((boundary, boundary[0:1])), nx
    )

    grid = np.zeros((nx, ny, 3))
    for i in range(nx):
        B = boundary_ring[i]
        for j in range(ny):
            v = j / (ny - 1.0)
            # Linear interpolation from boundary to centre.
            base = B * (1.0 - v) + centre_pt * v
            # Radial sag: dip the middle of the radial span slightly,
            # like the lens's sag_fraction.
            sag_profile = 4.0 * v * (1.0 - v)
            base[2] -= sag_fraction * H * sag_profile
            grid[i, j] = base

    return grid, boundary, anchors, edge_types
def _build_crown_lobe_prototype(R=8.0, H=6.0,
                                 n_anchors=7, subdivisions=5,
                                 nx=None, ny=12):
    """
    Prototype single-lobe of the crown.

    Frame A: support 1 -> apex -> support 2, parabolic curve.
    Radial path: support1 -> D (centre) -> support2, straight lines.
    Mesh: (nx, ny) grid, barycentric-mapped onto the lobe triangle
    with vertices at support1, support2, D.

    Boundary held: only the frame (j=0 row).
    Free: everything else, including D at j=ny-1.
    """
    import numpy as np

    R = float(R)
    H = float(H)

    angle_1 = 0.0
    angle_2 = 2.0 * np.pi / 3.0
    angle_mid = 0.5 * (angle_1 + angle_2)

    p_a1 = np.array([R * np.cos(angle_1), R * np.sin(angle_1), 0.0])
    p_a7 = np.array([R * np.cos(angle_2), R * np.sin(angle_2), 0.0])
    p_apex = np.array([R * np.cos(angle_mid), R * np.sin(angle_mid), H])
    p_D = np.array([0.0, 0.0, H])

    n_frame_pts = n_anchors + (n_anchors - 1) * subdivisions
    t = np.linspace(0.0, 1.0, n_frame_pts)
    p_lin = np.outer(1.0 - t, p_a1) + np.outer(t, p_a7)
    middle = 0.5 * (p_a1 + p_a7)
    lift = p_apex - middle
    profile = 4.0 * t * (1.0 - t)
    frame = p_lin + np.outer(profile, lift)

    if nx is None:
        nx = n_frame_pts

    grid = np.zeros((nx, ny, 3))
    for i in range(nx):
        u = i / (nx - 1.0)
        frame_pt = frame[int(round(u * (n_frame_pts - 1)))]
        for j in range(ny):
            v = j / (ny - 1.0)
            base = frame_pt * (1.0 - v) + p_D * v
            sag = 0.10 * H * (4.0 * v * (1.0 - v))
            base = base.copy()
            base[2] -= sag
            grid[i, j] = base

    boundary = frame.copy()
    anchors = list(range(len(boundary)))
    edge_types = ["beam"] * len(boundary)

    return grid, boundary, anchors, edge_types



# ---- Registry -------------------------------------------------------------
# The Tester reads this dict. Add new shapes here.

SHAPE_RECIPES = {
    "Lens": _build_lens_recipe,
    "Triangle": _build_triangle_recipe,
    "Crown": _build_crown_recipe,
}


# =============================================================================
# RENDER HELPERS
# =============================================================================

def _render_mesh_view(coords, tris, title):
    try:
        import plotly.graph_objects as go

        xyz_min = coords.min(axis=0)
        xyz_max = coords.max(axis=0)
        xyz_mid = (xyz_min + xyz_max) / 2.0
        span = float(max(xyz_max - xyz_min))
        pad = span * 0.15
        xr = [float(xyz_mid[0] - span / 2 - pad),
              float(xyz_mid[0] + span / 2 + pad)]
        yr = [float(xyz_mid[1] - span / 2 - pad),
              float(xyz_mid[1] + span / 2 + pad)]
        zr = [float(xyz_mid[2] - span / 2 - pad),
              float(xyz_mid[2] + span / 2 + pad)]

        fig = go.Figure()
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            i=tris[:, 0], j=tris[:, 1], k=tris[:, 2],
            color="#4a7a9c", opacity=0.9, flatshading=False,
            showscale=False,
            lighting=dict(ambient=0.6, diffuse=0.9,
                          specular=0.2, roughness=0.5),
        ))
        fig.update_layout(
            title=dict(text=title, font=dict(color="#c8d4e0", size=13)),
            scene=dict(
                xaxis=dict(title="X (m)", gridcolor="#333",
                           color="#888", range=xr, autorange=False),
                yaxis=dict(title="Y (m)", gridcolor="#333",
                           color="#888", range=yr, autorange=False),
                zaxis=dict(title="Z (m)", gridcolor="#333",
                           color="#888", range=zr, autorange=False),
                aspectmode="cube", bgcolor="#0e1117",
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.2)),
            ),
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(color="#ccc", size=11),
            height=480, margin=dict(l=0, r=0, b=0, t=30),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Could not render the 3D view:")
        st.code(str(e), language="text")


def _build_triangles(nx, ny):
    tri_i, tri_j, tri_k = [], [], []
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            b = (i + 1) * ny + j
            c = i * ny + (j + 1)
            d = (i + 1) * ny + (j + 1)
            tri_i.append(a); tri_j.append(b); tri_k.append(c)
            tri_i.append(b); tri_j.append(d); tri_k.append(c)
    return np.column_stack((tri_i, tri_j, tri_k))


def _compute_tri_areas(coords, tris):
    areas = np.zeros(len(tris))
    for k, tri in enumerate(tris):
        p0 = coords[tri[0]]
        p1 = coords[tri[1]]
        p2 = coords[tri[2]]
        areas[k] = 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0)))
    return areas


def _build_per_edge_q(edges, ny, warp_q, weft_q):
    """
    Build a per-edge q array from warp and weft.
    An edge connects nodes in different i-columns -> warp.
    Otherwise -> weft.
    """
    q = np.zeros(len(edges))
    for k, (a, b) in enumerate(edges):
        ia = a // ny
        ib = b // ny
        if ia != ib:
            q[k] = float(warp_q)
        else:
            q[k] = float(weft_q)
    return q


def _compute_focal_point(boundary_nodes, coords, ny):
    """Focal point: centroid of boundary in x-y, solved z at that (x,y)."""
    if len(boundary_nodes) == 0:
        return (0.0, 0.0, 0.0)
    cx = float(np.mean(boundary_nodes[:, 0]))
    cy = float(np.mean(boundary_nodes[:, 1]))
    dx = coords[:, 0] - cx
    dy = coords[:, 1] - cy
    dist2 = dx * dx + dy * dy
    k = int(np.argmin(dist2))
    cz = float(coords[k, 2])
    return (cx, cy, cz)




# =============================================================================
# RENDER: DEBUG OUTPUT
# =============================================================================

def _render_debug(initial_points, coords, tris, nx, ny, skip_u=6):
    with st.expander("DIGITISED OUTPUT - COPY THIS", expanded=False):
        flat0 = initial_points.reshape(-1, 3)

        st.markdown("#### Initial grid coordinates "
                    "(every %d th column)" % skip_u)
        lines = []
        for i in range(0, nx, skip_u):
            for j in range(ny):
                k = i * ny + j
                lines.append(
                    "node %3d  (i=%2d,j=%2d)  x=%+9.5f  y=%+9.5f  z=%+9.5f"
                    % (k, i, j, flat0[k, 0], flat0[k, 1], flat0[k, 2])
                )
        st.code("\n".join(lines), language="text")

        st.markdown("#### Solved coordinates "
                    "(every %d th column)" % skip_u)
        lines = []
        for i in range(0, nx, skip_u):
            for j in range(ny):
                k = i * ny + j
                lines.append(
                    "node %3d  (i=%2d,j=%2d)  x=%+9.5f  y=%+9.5f  z=%+9.5f"
                    % (k, i, j, coords[k, 0], coords[k, 1], coords[k, 2])
                )
        st.code("\n".join(lines), language="text")

        st.markdown("#### Displacement per node "
                    "(every %d th column)" % skip_u)
        lines = []
        disp = np.linalg.norm(coords - flat0, axis=1)
        for i in range(0, nx, skip_u):
            for j in range(ny):
                k = i * ny + j
                lines.append(
                    "node %3d  (i=%2d,j=%2d)  disp=%9.5f"
                    % (k, i, j, disp[k])
                )
        st.code("\n".join(lines), language="text")

        st.markdown("#### Summary")
        areas = _compute_tri_areas(coords, tris)
        st.write("Total triangles: %d" % len(tris))
        st.write("Minimum area: %.8e" % float(areas.min()))
        st.write("Maximum area: %.8e" % float(areas.max()))
        st.write("Mean area: %.8e" % float(areas.mean()))
        st.write("Zero-area count (< 1e-10): %d"
                 % int(np.sum(areas < 1e-10)))
        st.write("Near-zero count (< 1e-6): %d"
                 % int(np.sum(areas < 1e-6)))
        st.write("Positive count (>= 1e-6): %d"
                 % int(np.sum(areas >= 1e-6)))


# =============================================================================
# RENDER: HEADER
# =============================================================================

def _render_header():
    st.markdown(
        '<div style="background-color:#1f2a3a;border-left:4px solid #3498db;'
        'border-radius:8px;padding:1rem;margin-bottom:1.2rem;">'
        '<div style="color:#3498db;font-weight:700;font-size:1.05rem;'
        'margin-bottom:0.3rem;">EXPERIMENTAL - MBS TESTER</div>'
        '<div style="color:#c8d4e0;font-size:0.9rem;line-height:1.5;">'
        'Shape laboratory. User supplies corners or parameters. '
        'Engine derives everything else. Same nine-step pipeline '
        'for every shape.'
        '</div></div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# RENDER: SHAPE CONTROLS
# =============================================================================

def _render_shape_controls():
    st.markdown("#### Shape")
    shape_name = st.selectbox(
        "Shape",
        options=list(SHAPE_RECIPES.keys()),
        index=0,
        key="mbs_shape",
        label_visibility="collapsed",
    )

    st.markdown("#### Segments per edge (N)")
    n_segments = st.number_input(
        "N",
        min_value=1, max_value=50, value=DEFAULT_SEGMENTS,
        step=1,
        key="mbs_segments",
        label_visibility="collapsed",
    )

    st.markdown("#### Mesh density")
    density_mode = st.selectbox(
        "Mode",
        options=["Mode A - Fixed K", "Mode B - Target spacing ds"],
        index=0,
        key="mbs_density_mode",
        label_visibility="collapsed",
    )
    mode_key = "A" if density_mode.startswith("Mode A") else "B"

    K_val = DEFAULT_K
    ds_val = DEFAULT_DS
    if mode_key == "A":
        K_val = st.number_input(
            "K (subdivisions per segment)",
            min_value=1, max_value=50, value=DEFAULT_K,
            step=1,
            key="mbs_K",
        )
    else:
        ds_val = st.number_input(
            "Target spacing ds (m)",
            min_value=0.05, max_value=10.0, value=DEFAULT_DS,
            step=0.05, format="%.2f",
            key="mbs_ds",
        )

    return shape_name, int(n_segments), mode_key, int(K_val), float(ds_val)


# =============================================================================
# RENDER: SHAPE-SPECIFIC INPUTS
# =============================================================================

def _render_corner_inputs(shape_name):
    """
    Shape-specific inputs. Returns a dict of parameters keyed by
    the shape name. Empty for shapes with no user-editable inputs.
    """
    params = {}

    if shape_name == "Triangle":
        st.markdown("#### Triangle corners (user-editable)")
        cols = st.columns(3)
        labels = ["A", "B", "C"]
        defaults = [TRI_A_DEFAULT, TRI_B_DEFAULT, TRI_C_DEFAULT]
        for c, (label, dflt) in zip(cols, zip(labels, defaults)):
            with c:
                st.markdown("**Corner %s**" % label)
                x = st.number_input("x", value=float(dflt[0]),
                                     step=0.1, key="mbs_tri_%s_x" % label)
                y = st.number_input("y", value=float(dflt[1]),
                                     step=0.1, key="mbs_tri_%s_y" % label)
                z = st.number_input("z", value=float(dflt[2]),
                                     step=0.1, key="mbs_tri_%s_z" % label)
                params[label] = (x, y, z)

    if shape_name == "Crown":
        st.markdown("#### Crown parameters")
        c1, c2, c3 = st.columns(3)
        with c1:
            R = st.number_input(
                "Radius R (m)",
                min_value=1.0, max_value=100.0,
                value=CROWN_R_DEFAULT, step=0.5, format="%.2f",
                key="mbs_crown_R",
            )
        with c2:
            N = st.number_input(
                "Number of beams N",
                min_value=3, max_value=12,
                value=CROWN_N_DEFAULT, step=1,
                key="mbs_crown_N",
            )
        with c3:
            H = st.number_input(
                "Apex height H (m)",
                min_value=0.5, max_value=50.0,
                value=CROWN_H_DEFAULT, step=0.5, format="%.2f",
                key="mbs_crown_H",
            )

        d1, d2, d3 = st.columns(3)
        with d1:
            theta = st.number_input(
                "Tilt angle theta (deg)",
                min_value=35.0, max_value=145.0,
                value=CROWN_THETA_DEFAULT, step=1.0, format="%.1f",
                key="mbs_crown_theta",
                help="From horizontal. 90 = straight up. "
                     "<90 leans outward. >90 leans inward.",
            )
        with d2:
            rot = st.number_input(
                "Rotation offset (deg)",
                min_value=0.0, max_value=359.0,
                value=CROWN_ROT_DEFAULT, step=1.0, format="%.1f",
                key="mbs_crown_rot",
            )
        with d3:
            centre_r = st.number_input(
                "Centre radius (m)",
                min_value=0.0, max_value=50.0,
                value=CROWN_CENTRE_RADIUS_DEFAULT,
                step=0.1, format="%.2f",
                key="mbs_crown_centre_r",
                help="0 = centre is a free point. >0 reserved "
                     "for future centre-opening support.",
            )

        params["R"] = float(R)
        params["N"] = int(N)
        params["H"] = float(H)
        params["theta"] = float(theta)
        params["rot"] = float(rot)
        params["centre_radius"] = float(centre_r)

    return params


# =============================================================================
# RENDER: PRESTRESS + MODE
# =============================================================================

def _render_tuning_windows():
    st.markdown("#### Prestress tuning (kN/m)")
    c1, c2, c3 = st.columns(3)

    with c1:
        warp_q = st.number_input(
            "Warp (along)",
            min_value=0.01, max_value=100.0, value=DEFAULT_WARP_Q,
            step=0.1, format="%.2f",
            key="mbs_warp_q",
        )
    with c2:
        weft_q = st.number_input(
            "Weft (across)",
            min_value=0.01, max_value=100.0, value=DEFAULT_WEFT_Q,
            step=0.1, format="%.2f",
            key="mbs_weft_q",
        )
    with c3:
        st.number_input(
            "Beam/Cable (reserved)",
            min_value=0.01, max_value=100.0, value=5.0,
            step=0.1, format="%.2f",
            key="mbs_beam_cable_q",
            disabled=True,
            help="Reserved. Awaiting engine support.",
        )

    return float(warp_q), float(weft_q)


def _render_mode_toggles():
    st.markdown("#### Boundary mode")
    m1, m2 = st.columns(2)
    with m1:
        st.selectbox(
            "Beam/Cable",
            options=["Beam (rigid)", "Cable (tensioned)"],
            index=0, key="mbs_mode_beam_cable",
            disabled=True,
            help="Awaiting engine support.",
        )
    with m2:
        st.selectbox(
            "Rigid/Flexible",
            options=["Rigid (Stage 1)", "Flexible (Stage 2)"],
            index=0, key="mbs_mode_rigid_flex",
            disabled=True,
            help="Flexible boundary is Stage 2. Not yet built.",
        )


# =============================================================================
# MAIN RENDER
# =============================================================================

def render_tester_mbs():
    _render_header()

    try:
        from engine.membrane_boundary import build_and_solve, build_mesh
    except Exception as e:
        st.error("Could not load the MBS engine.")
        st.code(str(e), language="text")
        if st.button("Back to Landing", use_container_width=True,
                     key="mbs_back_import_fail"):
            st.session_state.page = "landing"
            st.rerun()
        return

    shape_name, n_segments, mode_key, K_val, ds_val = _render_shape_controls()
    params = _render_corner_inputs(shape_name)
    warp_q, weft_q = _render_tuning_windows()
    _render_mode_toggles()

    st.markdown("---")

    run_test = st.button(
        "Run test",
        type="primary", use_container_width=True,
        key="mbs_run_test",
    )

    if run_test:
        with st.spinner("Building %s and solving..." % shape_name):
            try:
                if shape_name == "Lens":
                    grid, boundary, anchors, etypes = _build_lens_recipe(
                        n_segments, mode_key, K_val, ds_val)
                elif shape_name == "Triangle":
                    grid, boundary, anchors, etypes = _build_triangle_recipe(
                        params["A"], params["B"], params["C"],
                        n_segments, mode_key, K_val, ds_val)
                elif shape_name == "Crown":
                    grid, boundary, anchors, etypes = _build_crown_recipe(
                        R=params["R"],
                        N=params["N"],
                        H=params["H"],
                        theta_deg=params["theta"],
                        rot_deg=params["rot"],
                        n_segments=n_segments,
                        mode=mode_key,
                        K=K_val,
                        ds=ds_val,
                        centre_radius=params["centre_radius"],
                    )
                else:
                    st.error("Shape not implemented: %s" % shape_name)
                    return

                nx = grid.shape[0]
                ny = grid.shape[1]

                mesh_preview = build_mesh(
                    boundary=boundary,
                    anchor_indices=anchors,
                    edge_types=etypes,
                    nx=nx, ny=ny,
                    membrane_q=1.0, cable_q=1.0,
                    initial_points=grid,
                )
                per_edge_q = _build_per_edge_q(
                    mesh_preview["edges"], ny,
                    warp_q=warp_q, weft_q=weft_q,
                )

                if shape_name == "Crown":
                    held_edges = ["i_min", "i_max", "j_min"]
                else:
                    held_edges = None

                result = build_and_solve(
                    boundary=boundary,
                    anchor_indices=anchors,
                    edge_types=etypes,
                    nx=nx, ny=ny,
                    membrane_q=1.0, cable_q=1.0,
                    initial_points=grid,
                    per_edge_q=per_edge_q,
                    held_grid_edges=held_edges,
                )

                st.session_state["mbs_result"] = {
                    "shape": shape_name,
                    "result": result,
                    "boundary": boundary,
                    "initial": grid.reshape(-1, 3).copy(),
                    "nx": nx,
                    "ny": ny,
                }
            except Exception as e:
                st.error("Shape %s raised an error:" % shape_name)
                st.code(str(e), language="text")

    if "mbs_result" not in st.session_state:
        st.info("Tap Run test above.")
        if st.button("Back to Landing", use_container_width=True,
                     key="mbs_back_noresult"):
            st.session_state.page = "landing"
            st.rerun()
        return

    entry = st.session_state["mbs_result"]
    result = entry["result"]
    boundary = entry["boundary"]
    initial = entry["initial"]
    coords = result["coordinates"]
    nx = entry["nx"]
    ny = entry["ny"]

    tris = _build_triangles(nx, ny)

    st.markdown("### Result - %s" % entry["shape"])
    _render_mesh_view(coords, tris, "%s - MBS result" % entry["shape"])

    m = result["mesh"]["diagnostics"]
    s = result["solve_result"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nodes", m["n_nodes"])
    c2.metric("Edges", m["n_edges"])
    c3.metric("Fixed", m["n_fixed"])
    c4.metric("Free", m["n_free"])
    d1, d2 = st.columns(2)
    d1.metric("FDM residual", "%.4e" % s["residual_norm"])
    d2.metric("Boundary points", len(boundary))

    fx, fy, fz = _compute_focal_point(boundary, coords, ny)
    st.markdown("**Focal point (datum)**")
    f1, f2, f3 = st.columns(3)
    f1.metric("Focal x (m)", "%.4f" % fx)
    f2.metric("Focal y (m)", "%.4f" % fy)
    f3.metric("Focal z (m)", "%.4f" % fz)

    _render_debug(initial, coords, tris, nx, ny, skip_u=6)

    if st.button("Back to Landing", use_container_width=True,
                 key="mbs_back_bottom"):
        st.session_state.page = "landing"
        st.rerun()


# =============================================================================
# END OF ui/workshops/tester_mbs.py
# =============================================================================







