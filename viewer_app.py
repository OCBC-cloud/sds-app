# =============================================================================
# FDS - 3D Viewer Prototype v3
# =============================================================================
# Standalone 3D viewer for prototyping SDSe structural shapes without touching
# the main app. Now supports Standard Saddle, 4-Point Hypar, and Cantilever
# Leaf configurations.
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="FDS - 3D Viewer Prototype v3",
    layout="wide",
    initial_sidebar_state="expanded",
)


def rerun():
    """Compatible rerun for all Streamlit versions."""
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st.rerun()


# =============================================================================
# DARK MODE CSS
# =============================================================================

dark_mode_css = """
    <style>
    .stApp { background-color: #0a0e17 !important; color: #f0f4fa !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 600 !important; }
    label { color: #ffffff !important; font-weight: 400 !important; }
    .stButton > button {
        background-color: #1e2a3a !important; color: #ffffff !important;
        border: 1px solid #2a3a4f !important; border-radius: 8px !important;
        padding: 0.5rem 1rem !important; font-weight: 500 !important;
        width: 100% !important; transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #2a3a4f !important;
        border-color: #4a7a9c !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #f39c12 !important;
        color: #0a0e17 !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #f1c40f !important;
        transform: translateY(-2px) !important;
    }
    .stSlider > div > div > div { background-color: #2a3a4f !important; }
    .stSlider > div > div > div > div { background-color: #f39c12 !important; }
    .stNumberInput > div > div > input {
        background-color: #141e2b !important; color: #ffffff !important;
        border: 1px solid #2a3a4f !important; border-radius: 8px !important;
    }
    .stSelectbox > div > div > div {
        background-color: #141e2b !important; color: #ffffff !important;
        border: 1px solid #2a3a4f !important;
    }
    .stAlert { background-color: #1e2a3a !important; border-left: 4px solid #f39c12 !important; color: #f0f4fa !important; }
    .stInfo { background-color: #1a2a3a !important; border-left: 4px solid #4a7a9c !important; color: #f0f4fa !important; }
    .stSuccess { background-color: #1a3a2a !important; border-left: 4px solid #2ecc71 !important; color: #f0f4fa !important; }
    .metric-card {
        background-color: #141e2b;
        border-radius: 12px;
        padding: 0.8rem;
        border: 1px solid #1e2a3a;
        text-align: center;
    }
    .metric-card .value { color: #ffffff; font-size: 1.1rem; font-weight: 700; }
    .metric-card .label { color: #8a9aaa; font-size: 0.7rem; }
    .metric-card .good { color: #2ecc71; }
    .metric-card .warning { color: #f39c12; }
    .metric-card .danger { color: #e74c3c; }
    .sdse-badge {
        display: inline-block; padding: 2px 8px;
        border-radius: 10px; font-size: 0.7rem;
        font-weight: 600; margin-right: 4px;
    }
    .sdse-badge.leaf { background: #f39c1233; color: #f39c12; border: 1px solid #f39c12; }
    .sdse-badge.column { background: #2ecc7133; color: #2ecc71; border: 1px solid #2ecc71; }
    .sdse-badge.rib { background: #3498db33; color: #3498db; border: 1px solid #3498db; }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)


# =============================================================================
# SHAPE FUNCTIONS
# =============================================================================

def get_beam_shape(x, span, rise, shape_type="parabolic"):
    """Calculate beam shape based on type."""
    if span <= 0:
        return np.zeros_like(x)
    x_norm = 2 * x / span

    if shape_type == "parabolic":
        return rise * (1 - x_norm ** 2)
    elif shape_type == "elliptical":
        return rise * np.sqrt(np.maximum(0, 1 - x_norm ** 2))
    elif shape_type == "circular":
        R = (span ** 2 + 4 * rise ** 2) / (8 * rise) if rise > 0 else span / 2
        if R > 0:
            return rise - (R - np.sqrt(np.maximum(0, R ** 2 - x ** 2)))
        return rise * (1 - x_norm ** 2)
    elif shape_type == "catenary":
        if rise <= 0 or span <= 0:
            return rise * (1 - x_norm ** 2)
        try:
            a = span / (2 * np.arcsinh(rise / (span / 2))) if rise > 0 else 1
            if a > 0:
                return rise * (1 - (np.cosh(x / a) - 1) / (np.cosh(span / (2 * a)) - 1))
            else:
                return rise * (1 - x_norm ** 2)
        except Exception:
            return rise * (1 - x_norm ** 2)
    return rise * (1 - x_norm ** 2)


# =============================================================================
# SESSION STATE
# =============================================================================

if "pretension" not in st.session_state:
    st.session_state.pretension = 25
if "shape_type" not in st.session_state:
    st.session_state.shape_type = "parabolic"
if "support_system" not in st.session_state:
    st.session_state.support_system = "leaf"
if "span" not in st.session_state:
    st.session_state.span = 10.0
if "rise" not in st.session_state:
    st.session_state.rise = 6.0
if "laa" not in st.session_state:
    st.session_state.laa = 15.0
if "supports" not in st.session_state:
    st.session_state.supports = {
        "A": {"x": -5.0, "y": 3.0},
        "B": {"x": 5.0, "y": 3.0},
        "C": {"x": -5.0, "y": -3.0},
        "D": {"x": 5.0, "y": -3.0},
    }

# Leaf-specific state
if "leaf_column_height" not in st.session_state:
    st.session_state.leaf_column_height = 6.0
if "leaf_outreach" not in st.session_state:
    st.session_state.leaf_outreach = 8.0
if "leaf_ribs_per_side" not in st.session_state:
    st.session_state.leaf_ribs_per_side = 5
if "leaf_rib_tilt_deg" not in st.session_state:
    st.session_state.leaf_rib_tilt_deg = 20.0
if "leaf_rib_spacing_deg" not in st.session_state:
    st.session_state.leaf_rib_spacing_deg = 45.0
if "leaf_beam_arc_radius" not in st.session_state:
    st.session_state.leaf_beam_arc_radius = 5.0
if "leaf_membrane_sag_pct" not in st.session_state:
    st.session_state.leaf_membrane_sag_pct = 15.0
if "leaf_column_diameter" not in st.session_state:
    st.session_state.leaf_column_diameter = 323.8
if "leaf_show_ribs" not in st.session_state:
    st.session_state.leaf_show_ribs = True
if "leaf_show_cables" not in st.session_state:
    st.session_state.leaf_show_cables = True
if "leaf_show_column" not in st.session_state:
    st.session_state.leaf_show_column = True
if "leaf_show_membrane" not in st.session_state:
    st.session_state.leaf_show_membrane = True
if "leaf_show_strut" not in st.session_state:
    st.session_state.leaf_show_strut = True
if "leaf_show_opening" not in st.session_state:
    st.session_state.leaf_show_opening = False
if "leaf_opening_radius" not in st.session_state:
    st.session_state.leaf_opening_radius = 1.5


# =============================================================================
# 3D GENERATORS
# =============================================================================

def generate_3d_view(pretension, shape_type, support_system, supports, span, rise, laa):
    """Dispatch to the correct 3D generator."""

    if support_system == "leaf":
        return generate_leaf_3d(pretension)
    elif support_system == "2_point":
        return generate_two_point_3d(shape_type, span, rise, laa)
    else:  # 4_point
        return generate_four_point_3d(supports, rise)


def generate_two_point_3d(shape_type, span, rise, laa):
    """Standard saddle span: two curved beams + membrane."""
    num_points = 40

    x = np.linspace(-span / 2, span / 2, num_points)
    z_beam = get_beam_shape(x, span, rise, shape_type)

    base_width = 3.0 * (laa / 10.0)
    y1 = -base_width * (1 - (2 * x / span) ** 2)
    y2 = base_width * (1 - (2 * x / span) ** 2)

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=x, y=y1, z=z_beam,
        mode="lines", name="Beam 1 (Left)",
        line=dict(color="#FF6B6B", width=8),
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=y2, z=z_beam,
        mode="lines", name="Beam 2 (Right)",
        line=dict(color="#FF6B6B", width=8),
    ))

    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, x_pos in enumerate(x):
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = z_beam[i]
        for j, v_val in enumerate(np.linspace(0, 1, num_points)):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            z_pos = z_at_x * (1 - 0.3 * (1 - (2 * v_val - 1) ** 2))
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.7, showscale=False, name="Membrane",
    ))

    support_y = base_width
    fig.add_trace(go.Scatter3d(
        x=[-span / 2, span / 2],
        y=[-support_y, support_y],
        z=[0, 0],
        mode="markers+text",
        marker=dict(color="#FF6B6B", size=12, symbol="square"),
        text=["Support L", "Support R"],
        textposition="top center",
        name="Supports",
    ))

    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[rise],
        mode="markers+text",
        marker=dict(color="#FFD93D", size=14, symbol="diamond"),
        text=["APEX"],
        textposition="top center",
        name="Apex",
    ))

    return _apply_common_layout(fig, rise)


def generate_four_point_3d(supports, rise):
    """4-point hypar surface."""
    num_points = 40
    A = supports["A"]
    B = supports["B"]
    C = supports["C"]
    D = supports["D"]

    span_x = B["x"] - A["x"]
    width_y = C["y"] - A["y"]
    if span_x == 0:
        span_x = 1.0
    if width_y == 0:
        width_y = 1.0

    x_vals = np.linspace(A["x"], B["x"], num_points)
    y_vals = np.linspace(C["y"], A["y"], num_points)
    X, Y = np.meshgrid(x_vals, y_vals)

    x_norm = (X - A["x"]) / span_x * 2 - 1
    y_norm = (Y - C["y"]) / width_y * 2 - 1

    Z = rise * np.maximum(0, (1 - x_norm ** 2) * (1 - y_norm ** 2))

    fig = go.Figure()

    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.7, showscale=False, name="Membrane",
    ))

    for label, p1, p2 in [
        ("Top Beam", A, B),
        ("Bottom Beam", C, D),
        ("Left Beam", A, C),
        ("Right Beam", B, D),
    ]:
        x_line = np.linspace(p1["x"], p2["x"], num_points)
        y_line = np.linspace(p1["y"], p2["y"], num_points)
        x_n = (x_line - A["x"]) / span_x * 2 - 1
        y_n = (y_line - A["y"]) / width_y * 2 - 1
        z_line = rise * np.maximum(0, (1 - x_n ** 2) * (1 - y_n ** 2))
        fig.add_trace(go.Scatter3d(
            x=x_line, y=y_line, z=z_line,
            mode="lines",
            line=dict(color="#FF6B6B", width=8),
            name=label,
        ))

    return _apply_common_layout(fig, rise)


def generate_leaf_3d(pretension):
    """
    Cantilever leaf: column at origin + arc + radial ribs tilted upward +
    segment edge cables + membrane draped below ribs and main beam.
    """
    fig = go.Figure()

    col_h = st.session_state.leaf_column_height
    outreach = st.session_state.leaf_outreach
    ribs_per_side = int(st.session_state.leaf_ribs_per_side)
    rib_tilt_deg = st.session_state.leaf_rib_tilt_deg
    rib_spacing_deg = st.session_state.leaf_rib_spacing_deg
    arc_r = st.session_state.leaf_beam_arc_radius
    sag_pct = st.session_state.leaf_membrane_sag_pct / 100.0

    # ---- Column (vertical from origin to column top)
    if st.session_state.leaf_show_column:
        col_top = (0.0, 0.0, col_h)
        fig.add_trace(go.Scatter3d(
            x=[0, col_top[0]],
            y=[0, col_top[1]],
            z=[0, col_top[2]],
            mode="lines",
            line=dict(color="#2ecc71", width=10),
            name="Column",
        ))
        # Baseplate
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[0],
            mode="markers",
            marker=dict(color="#2ecc71", size=10, symbol="square"),
            name="Baseplate",
        ))

    # ---- Main beam (arc from column top, curving upward and outward)
    # Parameter along the arc from column top outward
    t_beam = np.linspace(0, 1, 60)
    # Main beam sweeps along x from 0 to outreach with an arc in z
    beam_x = outreach * t_beam
    # Vertical rise of main beam from column top; use arc_r to shape
    beam_z = col_h + arc_r * (1 - np.cos(t_beam * np.pi / 2))
    beam_y = np.zeros_like(t_beam)

    fig.add_trace(go.Scatter3d(
        x=beam_x, y=beam_y, z=beam_z,
        mode="lines",
        line=dict(color="#FF6B6B", width=8),
        name="Main Beam (arc)",
    ))

    # ---- Radial ribs (tilted upward, symmetric per side)
    rib_tilt = np.radians(rib_tilt_deg)
    rib_spacing = np.radians(rib_spacing_deg)

    # Sample positions along the main beam where ribs attach
    n_attach = ribs_per_side
    attach_t = np.linspace(0.15, 0.95, n_attach)

    rib_tip_x_list = []
    rib_tip_y_list = []
    rib_tip_z_list = []

    if st.session_state.leaf_show_ribs:
        for side in (-1, +1):
            for t in attach_t:
                # Attachment point on main beam
                idx = int(t * (len(beam_x) - 1))
                a_x = beam_x[idx]
                a_y = beam_y[idx]
                a_z = beam_z[idx]

                # Rib direction: outward in x, sideways in y (side), tilted up in z
                # Rib length scales with outreach
                rib_len = outreach * 0.6

                # Angle in plan from x-axis:
                # side +1 => ribs fan toward +y
                # side -1 => ribs fan toward -y
                plan_ang = side * rib_spacing * 0.5 * (1 + 0.5 * t)

                tip_x = a_x + rib_len * np.cos(plan_ang) * np.cos(rib_tilt)
                tip_y = a_y + rib_len * np.sin(plan_ang) * np.cos(rib_tilt)
                tip_z = a_z + rib_len * np.sin(rib_tilt)

                rib_tip_x_list.append(tip_x)
                rib_tip_y_list.append(tip_y)
                rib_tip_z_list.append(tip_z)

                fig.add_trace(go.Scatter3d(
                    x=[a_x, tip_x],
                    y=[a_y, tip_y],
                    z=[a_z, tip_z],
                    mode="lines",
                    line=dict(color="#3498db", width=4),
                    showlegend=False,
                ))

                # Rib attachment node on main beam
                fig.add_trace(go.Scatter3d(
                    x=[a_x], y=[a_y], z=[a_z],
                    mode="markers",
                    marker=dict(color="#3498db", size=3),
                    showlegend=False,
                ))

    # ---- Segment edge cables between rib tips (both sides)
    if st.session_state.leaf_show_cables and len(rib_tip_x_list) > 0:
        # split per side
        n = len(attach_t)
        for side_idx in range(2):
            side_slice = slice(side_idx * n, (side_idx + 1) * n)
            xs = rib_tip_x_list[side_slice]
            ys = rib_tip_y_list[side_slice]
            zs = rib_tip_z_list[side_slice]
            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=zs,
                mode="lines",
                line=dict(color="#FFD93D", width=2, dash="dash"),
                name="Edge cable" if side_idx == 0 else None,
                showlegend=(side_idx == 0),
            ))

    # ---- Membrane surface (Option A: sags below ribs and main beam)
    if st.session_state.leaf_show_membrane:
        n_u = 30
        n_v = 30
        U = np.linspace(0, 1, n_u)
        V = np.linspace(-1, 1, n_v)

        X_surf = np.zeros((n_u, n_v))
        Y_surf = np.zeros((n_u, n_v))
        Z_surf = np.zeros((n_u, n_v))

        for i_u, u in enumerate(U):
            idx = int(u * (len(beam_x) - 1))
            bx = beam_x[idx]
            bz = beam_z[idx]
            # Membrane sags below the beam line by sag_pct * (arc radius)
            sag_amount = sag_pct * arc_r
            for i_v, v in enumerate(V):
                # Spread in y proportional to u (narrow at column, wide at tip)
                y_spread = outreach * 0.5 * u
                # Membrane height: below beam line, with sag deeper in middle of v
                sag_v = (1 - v ** 2)  # 1 at centre of leaf, 0 at edges
                z_pos = bz - sag_amount * sag_v
                X_surf[i_u, i_v] = bx
                Y_surf[i_u, i_v] = v * y_spread
                Z_surf[i_u, i_v] = z_pos

        fig.add_trace(go.Surface(
            x=X_surf, y=Y_surf, z=Z_surf,
            colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
            opacity=0.6,
            showscale=False,
            name="Membrane",
        ))

    # ---- Curved strut from 1/3 of main beam down to column
    if st.session_state.leaf_show_strut:
        # Point at 1/3 of main beam
        idx_third = int(0.33 * (len(beam_x) - 1))
        px = beam_x[idx_third]
        py = beam_y[idx_third]
        pz = beam_z[idx_third]
        # Curved path to column at lower point
        t = np.linspace(0, 1, 25)
        # Curve dips down and back to column
        sx = px * (1 - t)
        sy = py * (1 - t)
        sz = pz + (col_h * 0.4 - pz) * t + 0.5 * np.sin(np.pi * t) * (col_h * 0.15)
        fig.add_trace(go.Scatter3d(
            x=sx, y=sy, z=sz,
            mode="lines",
            line=dict(color="#e67e22", width=4),
            name="Curved strut",
        ))

    # ---- Optional central membrane opening with ring cable
    if st.session_state.leaf_show_opening:
        r_op = st.session_state.leaf_opening_radius
        # Place opening near mid-leaf
        c_x = outreach * 0.5
        c_z = col_h + arc_r * 0.3
        # Ring cable (circle in xy plane)
        angles = np.linspace(0, 2 * np.pi, 40)
        ring_x = c_x + r_op * np.cos(angles)
        ring_y = r_op * np.sin(angles)
        ring_z = np.full_like(ring_x, c_z)
        fig.add_trace(go.Scatter3d(
            x=ring_x, y=ring_y, z=ring_z,
            mode="lines",
            line=dict(color="#f1c40f", width=3),
            name="Ring cable",
        ))

    return _apply_common_layout(fig, col_h + arc_r)


def _apply_common_layout(fig, rise_ref):
    """Apply shared Plotly layout to any figure."""
    z_max = max(10, rise_ref * 1.5)
    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            xaxis=dict(color="#b0c4de", gridcolor="#1a2a3a"),
            yaxis=dict(color="#b0c4de", gridcolor="#1a2a3a"),
            zaxis=dict(color="#b0c4de", gridcolor="#1a2a3a", range=[-2, z_max]),
            bgcolor="#0a0e17",
            aspectmode="data",
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
        ),
        paper_bgcolor="#0a0e17",
        margin=dict(l=0, r=0, b=0, t=0),
        height=600,
        legend=dict(
            font=dict(color="#ffffff", size=8),
            orientation="h",
            yanchor="bottom",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(10,14,23,0.7)",
            bordercolor="#2a3a4f",
            borderwidth=1,
        ),
    )
    return fig


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_health_score(pretension):
    if pretension < 5:
        return 40, "danger"
    elif pretension < 10:
        return 60, "warning"
    elif pretension < 20:
        return 75, "warning"
    elif pretension < 35:
        return 85, "good"
    elif pretension < 50:
        return 90, "good"
    else:
        return 80, "warning"


def get_beam_size(pretension):
    if pretension < 10:
        return "CHS 168.3x7.1"
    elif pretension < 20:
        return "CHS 114.3x5.0"
    elif pretension < 35:
        return "CHS 76.1x3.6"
    elif pretension < 50:
        return "CHS 60.3x3.2"
    else:
        return "CHS 48.3x3.2"


def get_sag(pretension, span):
    if pretension < 5:
        return 50 * (span / 10)
    elif pretension < 10:
        return 30 * (span / 10)
    elif pretension < 20:
        return 15 * (span / 10)
    elif pretension < 35:
        return 8 * (span / 10)
    else:
        return 4 * (span / 10)


def get_anchor_force(pretension):
    return pretension * 0.6 * (1 + pretension / 100)


# =============================================================================
# MAIN UI
# =============================================================================

st.title("FDS - 3D Viewer Prototype v3")
st.caption("Test pretension, support systems, shapes, LAA, and the cantilever leaf in real-time")

# badges
st.markdown(
    '<span class="sdse-badge leaf">LEAF</span>'
    '<span class="sdse-badge column">COLUMN</span>'
    '<span class="sdse-badge rib">RIBS</span>',
    unsafe_allow_html=True,
)
st.markdown("---")

col_viewport, col_controls = st.columns([2, 1])

with col_viewport:
    st.subheader("Live 3D Viewport")

    fig = generate_3d_view(
        pretension=st.session_state.pretension,
        shape_type=st.session_state.shape_type,
        support_system=st.session_state.support_system,
        supports=st.session_state.supports,
        span=st.session_state.span,
        rise=st.session_state.rise,
        laa=st.session_state.laa,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

    st.markdown("---")
    st.markdown("### Live Feedback")

    health, health_status = get_health_score(st.session_state.pretension)
    beam = get_beam_size(st.session_state.pretension)
    sag = get_sag(st.session_state.pretension, st.session_state.span)
    anchor = get_anchor_force(st.session_state.pretension)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        color = "#2ecc71" if health_status == "good" else "#f39c12" if health_status == "warning" else "#e74c3c"
        st.markdown(
            '<div class="metric-card">'
            '<div class="value" style="color:' + color + ';">' + str(health) + '%</div>'
            '<div class="label">Health Score</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="metric-card">'
            '<div class="value">' + beam + '</div>'
            '<div class="label">Beam Size</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="metric-card">'
            '<div class="value">' + ("%.1f cm" % sag) + '</div>'
            '<div class="label">Membrane Sag</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            '<div class="metric-card">'
            '<div class="value">' + ("%.1f kN" % anchor) + '</div>'
            '<div class="label">Anchor Force</div>'
            '</div>',
            unsafe_allow_html=True,
        )

with col_controls:
    st.subheader("Controls")

    pretension = st.slider(
        "Pretension (kN/m)",
        min_value=0,
        max_value=100,
        value=st.session_state.pretension,
        step=1,
    )
    if pretension != st.session_state.pretension:
        st.session_state.pretension = pretension
        rerun()

    st.markdown("---")

    st.markdown("**Support System**")
    support_labels = ["2_Point", "4_Point", "Leaf"]
    support_keys = ["2_point", "4_point", "leaf"]
    current_idx = support_keys.index(st.session_state.support_system)
    support = st.radio(
        "Support system",
        support_labels,
        index=current_idx,
        key="support_radio",
        label_visibility="collapsed",
    )
    support_key = support_keys[support_labels.index(support)]
    if support_key != st.session_state.support_system:
        st.session_state.support_system = support_key
        rerun()

    # ---- Leaf-specific controls
    if st.session_state.support_system == "leaf":
        st.markdown("---")
        st.markdown("**Leaf Geometry**")

        col_h = st.number_input(
            "Column Height (m)",
            2.0, 20.0,
            st.session_state.leaf_column_height,
            0.5,
        )
        if col_h != st.session_state.leaf_column_height:
            st.session_state.leaf_column_height = col_h
            rerun()

        outreach = st.number_input(
            "Leaf Outreach (m)",
            2.0, 20.0,
            st.session_state.leaf_outreach,
            0.5,
        )
        if outreach != st.session_state.leaf_outreach:
            st.session_state.leaf_outreach = outreach
            rerun()

        ribs = st.number_input(
            "Ribs per Side (min 5)",
            5, 15,
            int(st.session_state.leaf_ribs_per_side),
            1,
        )
        if int(ribs) != int(st.session_state.leaf_ribs_per_side):
            st.session_state.leaf_ribs_per_side = int(ribs)
            rerun()

        tilt = st.slider(
            "Rib Tilt (deg)",
            5.0, 40.0,
            st.session_state.leaf_rib_tilt_deg,
            1.0,
        )
        if tilt != st.session_state.leaf_rib_tilt_deg:
            st.session_state.leaf_rib_tilt_deg = tilt
            rerun()

        spacing = st.slider(
            "Rib Plan Spacing (deg)",
            15.0, 90.0,
            st.session_state.leaf_rib_spacing_deg,
            5.0,
        )
        if spacing != st.session_state.leaf_rib_spacing_deg:
            st.session_state.leaf_rib_spacing_deg = spacing
            rerun()

        arc_r = st.number_input(
            "Main Beam Arc Radius (m)",
            1.0, 15.0,
            st.session_state.leaf_beam_arc_radius,
            0.5,
        )
        if arc_r != st.session_state.leaf_beam_arc_radius:
            st.session_state.leaf_beam_arc_radius = arc_r
            rerun()

        sag_pct = st.slider(
            "Membrane Sag (%)",
            5.0, 40.0,
            st.session_state.leaf_membrane_sag_pct,
            1.0,
        )
        if sag_pct != st.session_state.leaf_membrane_sag_pct:
            st.session_state.leaf_membrane_sag_pct = sag_pct
            rerun()

        st.markdown("**Visibility**")
        c1, c2 = st.columns(2)
        with c1:
            v_col = st.checkbox("Column", value=st.session_state.leaf_show_column)
            v_rib = st.checkbox("Ribs", value=st.session_state.leaf_show_ribs)
            v_cab = st.checkbox("Cables", value=st.session_state.leaf_show_cables)
            v_str = st.checkbox("Strut", value=st.session_state.leaf_show_strut)
        with c2:
            v_mem = st.checkbox("Membrane", value=st.session_state.leaf_show_membrane)
            v_opn = st.checkbox("Opening", value=st.session_state.leaf_show_opening)

        if v_col != st.session_state.leaf_show_column:
            st.session_state.leaf_show_column = v_col
            rerun()
        if v_rib != st.session_state.leaf_show_ribs:
            st.session_state.leaf_show_ribs = v_rib
            rerun()
        if v_cab != st.session_state.leaf_show_cables:
            st.session_state.leaf_show_cables = v_cab
            rerun()
        if v_str != st.session_state.leaf_show_strut:
            st.session_state.leaf_show_strut = v_str
            rerun()
        if v_mem != st.session_state.leaf_show_membrane:
            st.session_state.leaf_show_membrane = v_mem
            rerun()
        if v_opn != st.session_state.leaf_show_opening:
            st.session_state.leaf_show_opening = v_opn
            rerun()

        if st.session_state.leaf_show_opening:
            op_r = st.slider(
                "Opening Radius (m)",
                0.5, 4.0,
                st.session_state.leaf_opening_radius,
                0.25,
            )
            if op_r != st.session_state.leaf_opening_radius:
                st.session_state.leaf_opening_radius = op_r
                rerun()

    # ---- Non-leaf: shape type
    if st.session_state.support_system in ("2_point",):
        st.markdown("---")
        st.markdown("**Shape Type**")
        shape = st.radio(
            "Shape",
            ["parabolic", "elliptical", "circular", "catenary"],
            index=["parabolic", "elliptical", "circular", "catenary"].index(st.session_state.shape_type),
            key="shape_radio",
            label_visibility="collapsed",
        )
        if shape != st.session_state.shape_type:
            st.session_state.shape_type = shape
            rerun()

    # ---- 4-point coords
    if st.session_state.support_system == "4_point":
        st.markdown("---")
        st.markdown("**4-Point Positions**")
        col_a, col_b = st.columns(2)
        with col_a:
            x_a = st.number_input("A X", -10.0, 10.0, st.session_state.supports["A"]["x"], 0.5)
            y_a = st.number_input("A Y", -10.0, 10.0, st.session_state.supports["A"]["y"], 0.5)
        with col_b:
            x_b = st.number_input("B X", -10.0, 10.0, st.session_state.supports["B"]["x"], 0.5)
            y_b = st.number_input("B Y", -10.0, 10.0, st.session_state.supports["B"]["y"], 0.5)
        col_c, col_d = st.columns(2)
        with col_c:
            x_c = st.number_input("C X", -10.0, 10.0, st.session_state.supports["C"]["x"], 0.5)
            y_c = st.number_input("C Y", -10.0, 10.0, st.session_state.supports["C"]["y"], 0.5)
        with col_d:
            x_d = st.number_input("D X", -10.0, 10.0, st.session_state.supports["D"]["x"], 0.5)
            y_d = st.number_input("D Y", -10.0, 10.0, st.session_state.supports["D"]["y"], 0.5)

        new_supports = {
            "A": {"x": x_a, "y": y_a},
            "B": {"x": x_b, "y": y_b},
            "C": {"x": x_c, "y": y_c},
            "D": {"x": x_d, "y": y_d},
        }
        if new_supports != st.session_state.supports:
            st.session_state.supports = new_supports
            rerun()

    st.markdown("---")

    # ---- Span, Rise, LAA only relevant for non-leaf
    if st.session_state.support_system != "leaf":
        col_span, col_rise = st.columns(2)
        with col_span:
            span = st.number_input("Span (m)", 4.0, 40.0, st.session_state.span, 0.5)
            if span != st.session_state.span:
                st.session_state.span = span
                rerun()
        with col_rise:
            rise = st.number_input("Rise (m)", 2.0, 20.0, st.session_state.rise, 0.5)
            if rise != st.session_state.rise:
                st.session_state.rise = rise
                rerun()

        laa = st.number_input(
            "Apex-to-Apex (LAA) m",
            2.0, 30.0,
            st.session_state.laa,
            0.5,
        )
        if laa != st.session_state.laa:
            st.session_state.laa = laa
            rerun()

    st.markdown("---")
    st.markdown("**Quick Presets**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset Leaf", use_container_width=True):
            st.session_state.support_system = "leaf"
            st.session_state.leaf_column_height = 6.0
            st.session_state.leaf_outreach = 8.0
            st.session_state.leaf_ribs_per_side = 5
            st.session_state.leaf_rib_tilt_deg = 20.0
            st.session_state.leaf_rib_spacing_deg = 45.0
            st.session_state.leaf_beam_arc_radius = 5.0
            st.session_state.leaf_membrane_sag_pct = 15.0
            rerun()
    with col2:
        if st.button("Ref Leaf (10x10)", use_container_width=True):
            st.session_state.support_system = "leaf"
            st.session_state.leaf_column_height = 10.0
            st.session_state.leaf_outreach = 10.0
            st.session_state.leaf_ribs_per_side = 7
            st.session_state.leaf_rib_tilt_deg = 20.0
            st.session_state.leaf_rib_spacing_deg = 45.0
            st.session_state.leaf_beam_arc_radius = 5.0
            st.session_state.leaf_membrane_sag_pct = 15.0
            rerun()


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("FDS - 3D Viewer Prototype v3 | Rigid in Principle. Fluid in Application.")
st.caption("Now supports: Standard Saddle, 4-Point Hypar, Cantilever Leaf.")
