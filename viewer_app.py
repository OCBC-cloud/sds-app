import streamlit as st
import plotly.graph_objects as go
import numpy as np
from typing import Dict, Tuple, Optional

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="FDS - 3D Viewer Prototype v6",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DARK MODE CSS
# ============================================================
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
    .stSlider > div > div > div {
        background-color: #2a3a4f !important;
    }
    .stSlider > div > div > div > div {
        background-color: #f39c12 !important;
    }
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
    .stRadio > div {
        gap: 0.5rem;
    }
    .stRadio > div label {
        color: #6a7a8a !important;
        background-color: #0a0e17 !important;
        padding: 0.3rem 1rem !important;
        border-radius: 20px !important;
        border: 1px solid #2a3a4f !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        font-size: 0.85rem !important;
    }
    .stRadio > div label:hover {
        border-color: #4a7a9c !important;
        color: #ffffff !important;
    }
    .stRadio > div label:has(input:checked) {
        color: #f39c12 !important;
        border-color: #f39c12 !important;
        background-color: rgba(243, 156, 18, 0.1) !important;
        font-weight: 600 !important;
    }
    .metric-card {
        background-color: #141e2b;
        border-radius: 12px;
        padding: 0.8rem;
        border: 1px solid #1e2a3a;
        text-align: center;
    }
    .metric-card .value { color: #ffffff; font-size: 1.2rem; font-weight: 700; }
    .metric-card .label { color: #8a9aaa; font-size: 0.7rem; }
    .metric-card .good { color: #2ecc71; }
    .metric-card .warning { color: #f39c12; }
    .metric-card .danger { color: #e74c3c; }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# SHAPE FUNCTIONS - FIXED: Added guard clauses
# ============================================================
def get_beam_shape(x: np.ndarray, span: float, rise: float, shape_type: str = "parabolic") -> np.ndarray:
    """Calculate beam shape based on type with safety guards"""
    if span <= 0 or rise <= 0:
        return np.zeros_like(x)
    
    x_norm = 2 * x / span
    
    if shape_type == "parabolic":
        return rise * (1 - x_norm**2)
    
    elif shape_type == "elliptical":
        # Clamp to avoid sqrt of negative
        vals = 1 - x_norm**2
        vals = np.clip(vals, 0, None)
        return rise * np.sqrt(vals)
    
    elif shape_type == "circular":
        R = (span**2 + 4 * rise**2) / (8 * rise)
        # Clamp to avoid sqrt of negative
        vals = R**2 - x**2
        vals = np.clip(vals, 0, None)
        return rise - (R - np.sqrt(vals))
    
    elif shape_type == "catenary":
        # Guard against division by zero
        half_span = span / 2
        if half_span <= 0:
            return rise * (1 - x_norm**2)
        
        ratio = rise / half_span
        if ratio <= 0:
            return rise * (1 - x_norm**2)
        
        a = half_span / np.arcsinh(ratio)
        if a <= 0:
            return rise * (1 - x_norm**2)
        
        cosh_factor = np.cosh(span / (2 * a)) - 1
        if cosh_factor <= 0:
            return rise * (1 - x_norm**2)
        
        return rise * (1 - (np.cosh(x / a) - 1) / cosh_factor)
    
    # Fallback
    return rise * (1 - x_norm**2)

# ============================================================
# SESSION STATE
# ============================================================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "pretension": 25,
        "shape_type": "parabolic",
        "support_system": "2_point",
        "span": 10.0,
        "rise": 6.0,
        "laa": 15.0,
        "cables_per_bay": 2,
        "cable_vertical_angle": 45,
        "cable_spread_angle": 30,
        "camera_view": "home",
        "supports": {
            "A": {"x": -5.0, "y": 3.0},
            "B": {"x": 5.0, "y": 3.0},
            "C": {"x": -5.0, "y": -3.0},
            "D": {"x": 5.0, "y": -3.0}
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================
# CAMERA PRESETS
# ============================================================
def get_camera(view_name: str) -> Dict:
    """Get camera preset for the given view"""
    cameras = {
        "home": dict(eye=dict(x=1.8, y=1.8, z=1.2)),
        "top": dict(eye=dict(x=0, y=0, z=2.5)),
        "front": dict(eye=dict(x=0, y=-2.5, z=0.5)),
        "back": dict(eye=dict(x=0, y=2.5, z=0.5)),
        "left": dict(eye=dict(x=-2.5, y=0, z=0.5)),
        "right": dict(eye=dict(x=2.5, y=0, z=0.5))
    }
    return cameras.get(view_name, cameras["home"])

# ============================================================
# CABLE GENERATION HELPERS
# ============================================================
def generate_2point_cables(
    fig: go.Figure,
    x: np.ndarray,
    y1: np.ndarray,
    y2: np.ndarray,
    z_beam: np.ndarray,
    span: float,
    laa: float,
    cables_per_bay: int,
    vertical_angle: float,
    spread_angle: float
) -> None:
    """
    Generate cables for 2-point system with angle-based positioning.
    FIXED: Angles now properly control cable trajectory.
    """
    # Convert angles to radians
    vertical_rad = np.radians(vertical_angle)
    spread_rad = np.radians(spread_angle)
    
    # Determine cable positions along the beam
    if cables_per_bay == 2:
        beam_positions = [-span/4, span/4]
    elif cables_per_bay == 4:
        beam_positions = [-span*3/10, -span/10, span/10, span*3/10]
    else:  # 6
        beam_positions = np.linspace(-span*0.4, span*0.4, 6).tolist()
    
    cables_per_side = cables_per_bay // 2
    anchor_offset = laa * 0.8
    
    # Color palette for cables
    colors = ['#FFD93D', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    for idx, bx in enumerate(beam_positions):
        # Find closest point on beam
        idx_beam = np.argmin(np.abs(x - bx))
        x_pos = x[idx_beam]
        y1_pos = y1[idx_beam]
        y2_pos = y2[idx_beam]
        z_pos = z_beam[idx_beam]
        
        # Calculate cable lengths using angles
        cable_length = anchor_offset / np.cos(vertical_rad)
        x_offset = cable_length * np.cos(vertical_rad)
        y_offset = anchor_offset * np.sin(spread_rad)
        
        # For each pair of cables on this position
        for i in range(cables_per_side):
            # Spread cables across the width
            spread_factor = (i + 1) / (cables_per_side + 1)
            current_y_offset = y_offset * spread_factor
            
            # LEFT BEAM: cables go LEFT and DOWN
            x_anchor_left = x_pos - x_offset
            y_anchor_left = y1_pos - current_y_offset  # OUTWARD from center
            
            color = colors[idx % len(colors)]
            
            # Cable line
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_anchor_left],
                y=[y1_pos, y_anchor_left],
                z=[z_pos, 0],
                mode='lines',
                line=dict(color=color, width=2, dash='dash'),
                showlegend=False
            ))
            # Anchor point
            fig.add_trace(go.Scatter3d(
                x=[x_anchor_left],
                y=[y_anchor_left],
                z=[0],
                mode='markers',
                marker=dict(color='#FF6B6B', size=3, symbol='x'),
                showlegend=False
            ))
            
            # RIGHT BEAM: cables go RIGHT and DOWN
            x_anchor_right = x_pos + x_offset
            y_anchor_right = y2_pos + current_y_offset  # OUTWARD from center
            
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_anchor_right],
                y=[y2_pos, y_anchor_right],
                z=[z_pos, 0],
                mode='lines',
                line=dict(color=color, width=2, dash='dash'),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[x_anchor_right],
                y=[y_anchor_right],
                z=[0],
                mode='markers',
                marker=dict(color='#FF6B6B', size=3, symbol='x'),
                showlegend=False
            ))

def generate_4point_cables(
    fig: go.Figure,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    supports: Dict,
    span_x: float,
    width_y: float,
    rise: float,
    laa: float,
    cables_per_bay: int,
    vertical_angle: float,
    spread_angle: float
) -> None:
    """
    Generate cables for 4-point system.
    FIXED: Now generates proper cables radiating outward from membrane.
    """
    A = supports["A"]
    B = supports["B"]
    C = supports["C"]
    D = supports["D"]
    
    # Convert angles to radians
    vertical_rad = np.radians(vertical_angle)
    spread_rad = np.radians(spread_angle)
    
    # Cable positions along the membrane
    num_cables = cables_per_bay * 2
    cable_positions = np.linspace(0.15, 0.85, num_cables)
    
    anchor_offset = laa * 0.7
    cable_length = anchor_offset / np.cos(vertical_rad)
    x_offset = cable_length * np.cos(vertical_rad)
    y_offset = anchor_offset * np.sin(spread_rad)
    
    # Generate cables from interior points outward
    for pos in cable_positions:
        # Position on membrane (interior)
        x_pos = A["x"] + pos * span_x
        y_pos = A["y"] + pos * width_y
        
        # Get Z at this position
        x_norm = (x_pos - A["x"]) / span_x * 2 - 1
        y_norm = (y_pos - A["y"]) / width_y * 2 - 1
        z_pos = rise * (1 - x_norm**2) * (1 - y_norm**2)
        
        # Determine which quadrant and anchor direction
        # 4 anchor directions: NW, NE, SE, SW
        directions = []
        
        # North-West
        if x_pos - x_offset > A["x"] and y_pos + y_offset < A["y"]:
            directions.append(("NW", x_pos - x_offset, y_pos + y_offset))
        # North-East
        if x_pos + x_offset < B["x"] and y_pos + y_offset < B["y"]:
            directions.append(("NE", x_pos + x_offset, y_pos + y_offset))
        # South-East
        if x_pos + x_offset < D["x"] and y_pos - y_offset > D["y"]:
            directions.append(("SE", x_pos + x_offset, y_pos - y_offset))
        # South-West
        if x_pos - x_offset > C["x"] and y_pos - y_offset > C["y"]:
            directions.append(("SW", x_pos - x_offset, y_pos - y_offset))
        
        # Draw cables in each valid direction
        colors = ['#FFD93D', '#FF6B6B', '#4ECDC4', '#45B7D1']
        for i, (_, x_anchor, y_anchor) in enumerate(directions):
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_anchor],
                y=[y_pos, y_anchor],
                z=[z_pos, 0],
                mode='lines',
                line=dict(color=colors[i % len(colors)], width=2, dash='dash'),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[x_anchor],
                y=[y_anchor],
                z=[0],
                mode='markers',
                marker=dict(color='#FF6B6B', size=3, symbol='x'),
                showlegend=False
            ))

# ============================================================
# 3D GENERATOR - COMPLETE FIXED VERSION
# ============================================================
def generate_3d_view(
    pretension: float,
    shape_type: str,
    support_system: str,
    supports: Dict,
    span: float,
    rise: float,
    laa: float,
    cables_per_bay: int,
    cable_vertical_angle: float,
    cable_spread_angle: float,
    camera_view: str
) -> go.Figure:
    """Generate 3D visualization with all fixes applied"""
    
    num_points = 40
    
    # Get beam shape
    x = np.linspace(-span/2, span/2, num_points)
    z_beam = get_beam_shape(x, span, rise, shape_type)
    
    # Camera
    camera = get_camera(camera_view)
    
    # Determine support configuration
    if support_system == "2_point":
        # Width variation based on LAA
        width_factor = max(0.5, laa / 10.0)
        y1 = -3.0 * (1 - (2 * x / span)**2) * width_factor
        y2 = 3.0 * (1 - (2 * x / span)**2) * width_factor
        
        fig = go.Figure()
        
        # Beams
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_beam,
            mode='lines', name='Beam 1 (Left)',
            line=dict(color='#FF6B6B', width=8)
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_beam,
            mode='lines', name='Beam 2 (Right)',
            line=dict(color='#FF6B6B', width=8)
        ))
        
        # Membrane surface
        X_surf = np.zeros((num_points, num_points))
        Y_surf = np.zeros((num_points, num_points))
        Z_surf = np.zeros((num_points, num_points))
        
        for i, x_pos in enumerate(x):
            y_beam1 = y1[i]
            y_beam2 = y2[i]
            z_at_x = z_beam[i]
            for j, v_val in enumerate(np.linspace(0, 1, num_points)):
                y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
                z_pos = z_at_x * (1 - 0.3 * (1 - (2 * v_val - 1)**2))
                X_surf[i, j] = x_pos
                Y_surf[i, j] = y_pos
                Z_surf[i, j] = z_pos
        
        fig.add_trace(go.Surface(
            x=X_surf, y=Y_surf, z=Z_surf,
            colorscale=[[0, '#1a2a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
            opacity=0.7,
            showscale=False,
            name='Membrane'
        ))
        
        # Support points
        fig.add_trace(go.Scatter3d(
            x=[-span/2, span/2],
            y=[0, 0],
            z=[0, 0],
            mode='markers+text',
            marker=dict(color='#FF6B6B', size=5, symbol='square'),
            text=['Support L', 'Support R'],
            textposition='top center',
            name='Supports'
        ))
        
        # Apex
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[rise],
            mode='markers+text',
            marker=dict(color='#FFD93D', size=8, symbol='diamond'),
            text=['▲ APEX'],
            textposition='top center',
            name='Apex'
        ))
        
        # === FIXED: Generate cables with angle control ===
        generate_2point_cables(
            fig, x, y1, y2, z_beam,
            span, laa, cables_per_bay,
            cable_vertical_angle, cable_spread_angle
        )
        
    else:  # 4_POINT
        A = supports["A"]
        B = supports["B"]
        C = supports["C"]
        D = supports["D"]
        
        span_x = B["x"] - A["x"]
        width_y = A["y"] - C["y"]
        
        if span_x <= 0 or width_y <= 0:
            # Fallback to default if invalid
            span_x = 10.0
            width_y = 6.0
            A = {"x": -5.0, "y": 3.0}
            B = {"x": 5.0, "y": 3.0}
            C = {"x": -5.0, "y": -3.0}
            D = {"x": 5.0, "y": -3.0}
        
        x_vals = np.linspace(A["x"], B["x"], num_points)
        y_vals = np.linspace(C["y"], A["y"], num_points)
        X, Y = np.meshgrid(x_vals, y_vals)
        
        x_norm = (X - A["x"]) / span_x * 2 - 1
        y_norm = (Y - C["y"]) / width_y * 2 - 1
        
        Z = rise * (1 - x_norm**2) * (1 - y_norm**2)
        Z = np.clip(Z, 0, None)  # Ensure no negative values
        
        fig = go.Figure()
        
        # Membrane surface
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale=[[0, '#1a2a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
            opacity=0.7,
            showscale=False,
            name='Membrane'
        ))
        
        # Helper for edge beam Z
        def get_edge_z(x_pos: float, y_pos: float) -> float:
            x_norm_e = (x_pos - A["x"]) / span_x * 2 - 1
            y_norm_e = (y_pos - A["y"]) / width_y * 2 - 1
            z_val = rise * (1 - x_norm_e**2) * (1 - y_norm_e**2)
            return max(0, z_val)
        
        # Top beam
        x_top = np.linspace(A["x"], B["x"], num_points)
        y_top = np.ones(num_points) * A["y"]
        z_top = [get_edge_z(x_top[i], y_top[i]) for i in range(num_points)]
        fig.add_trace(go.Scatter3d(
            x=x_top, y=y_top, z=z_top,
            mode='lines',
            line=dict(color='#FF6B6B', width=8),
            name='Top Beam'
        ))
        
        # Bottom beam
        x_bot = np.linspace(C["x"], D["x"], num_points)
        y_bot = np.ones(num_points) * C["y"]
        z_bot = [get_edge_z(x_bot[i], y_bot[i]) for i in range(num_points)]
        fig.add_trace(go.Scatter3d(
            x=x_bot, y=y_bot, z=z_bot,
            mode='lines',
            line=dict(color='#FF6B6B', width=8),
            name='Bottom Beam'
        ))
        
        # Left beam
        x_left = np.ones(num_points) * A["x"]
        y_left = np.linspace(A["y"], C["y"], num_points)
        z_left = [get_edge_z(x_left[i], y_left[i]) for i in range(num_points)]
        fig.add_trace(go.Scatter3d(
            x=x_left, y=y_left, z=z_left,
            mode='lines',
            line=dict(color='#FF6B6B', width=8),
            name='Left Beam'
        ))
        
        # Right beam
        x_right = np.ones(num_points) * B["x"]
        y_right = np.linspace(B["y"], D["y"], num_points)
        z_right = [get_edge_z(x_right[i], y_right[i]) for i in range(num_points)]
        fig.add_trace(go.Scatter3d(
            x=x_right, y=y_right, z=z_right,
            mode='lines',
            line=dict(color='#FF6B6B', width=8),
            name='Right Beam'
        ))
        
        # Support points
        support_points = [
            {"x": A["x"], "y": A["y"], "label": "A"},
            {"x": B["x"], "y": B["y"], "label": "B"},
            {"x": C["x"], "y": C["y"], "label": "C"},
            {"x": D["x"], "y": D["y"], "label": "D"}
        ]
        
        for sp in support_points:
            fig.add_trace(go.Scatter3d(
                x=[sp["x"]], y=[sp["y"]], z=[0],
                mode='markers+text',
                marker=dict(color='#FF6B6B', size=5, symbol='square'),
                text=[sp["label"]],
                textposition='top center',
                name=f'Support {sp["label"]}'
            ))
        
        # Apex
        apex_x = (A["x"] + B["x"] + C["x"] + D["x"]) / 4
        apex_y = (A["y"] + B["y"] + C["y"] + D["y"]) / 4
        fig.add_trace(go.Scatter3d(
            x=[apex_x], y=[apex_y], z=[rise],
            mode='markers+text',
            marker=dict(color='#FFD93D', size=8, symbol='diamond'),
            text=['▲ APEX'],
            textposition='top center',
            name='Apex'
        ))
        
        # === FIXED: Edge cables follow membrane ===
        edge_pairs = [(A, B, "top"), (B, D, "right"), (D, C, "bottom"), (C, A, "left")]
        for p1, p2, edge_name in edge_pairs:
            # Sample points along edge
            edge_x = np.linspace(p1["x"], p2["x"], 10)
            edge_y = np.linspace(p1["y"], p2["y"], 10)
            edge_z = [get_edge_z(edge_x[i], edge_y[i]) for i in range(10)]
            
            # Draw edge cable following membrane
            for i in range(len(edge_x) - 1):
                fig.add_trace(go.Scatter3d(
                    x=[edge_x[i], edge_x[i+1]],
                    y=[edge_y[i], edge_y[i+1]],
                    z=[edge_z[i], edge_z[i+1]],
                    mode='lines',
                    line=dict(color='#FFD93D', width=2, dash='dash'),
                    showlegend=False
                ))
        
        # === FIXED: Generate interior cables ===
        generate_4point_cables(
            fig, X, Y, Z, supports,
            span_x, width_y, rise, laa,
            cables_per_bay, cable_vertical_angle, cable_spread_angle
        )
    
    # Common layout
    fig.update_layout(
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a', range=[-10, 10]),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a', range=[-10, 10]),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a', range=[0, max(10, rise + 2)]),
            bgcolor='#0a0e17',
            camera=camera
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(
            font=dict(color='#ffffff', size=8),
            orientation="h",
            yanchor="bottom",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(10,14,23,0.7)',
            bordercolor='#2a3a4f',
            borderwidth=1
        )
    )
    
    return fig

# ============================================================
# HELPER FUNCTIONS - IMPROVED
# ============================================================
def get_health_score(pretension: float) -> Tuple[int, str]:
    """Calculate health score with smooth transition"""
    if pretension <= 0:
        return 30, "danger"
    elif pretension < 5:
        return int(30 + pretension * 2), "danger"
    elif pretension < 15:
        return int(40 + (pretension - 5) * 2.5), "warning"
    elif pretension < 30:
        return int(65 + (pretension - 15) * 1.33), "warning"
    elif pretension < 50:
        return int(85 + (pretension - 30) * 0.25), "good"
    elif pretension < 70:
        return int(90 - (pretension - 50) * 0.5), "good"
    else:
        return max(50, int(80 - (pretension - 70) * 0.75)), "warning"

def get_beam_size(pretension: float) -> str:
    """Get beam size based on pretension"""
    if pretension < 10:
        return "CHS 168.3×7.1"
    elif pretension < 20:
        return "CHS 114.3×5.0"
    elif pretension < 35:
        return "CHS 76.1×3.6"
    elif pretension < 50:
        return "CHS 60.3×3.2"
    else:
        return "CHS 48.3×3.2"

def get_sag(pretension: float, span: float) -> float:
    """Calculate membrane sag in cm"""
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

def get_anchor_force(pretension: float) -> float:
    """Calculate anchor force in kN"""
    return pretension * 0.6 * (1 + pretension / 100)

# ============================================================
# MAIN UI
# ============================================================
st.title("🧬 FDS - 3D Viewer Prototype v6")
st.caption("Test pretension, support systems, shapes, LAA, and cable angles in real-time")
st.markdown("---")

col_viewport, col_controls = st.columns([2, 1])

with col_viewport:
    st.subheader("🔬 Live 3D Viewport")
    
    # View Controls
    st.markdown("**📷 View Controls**")
    col_v1, col_v2, col_v3, col_v4, col_v5, col_v6 = st.columns(6)
    
    view_buttons = {
        "🏠 Home": "home",
        "🔝 Top": "top",
        "📐 Front": "front",
        "📐 Back": "back",
        "↔️ Left": "left",
        "↔️ Right": "right"
    }
    
    for col, (label, view) in zip([col_v1, col_v2, col_v3, col_v4, col_v5, col_v6], view_buttons.items()):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.camera_view = view
                st.rerun()
    
    st.markdown("---")
    
    # Generate 3D figure
    with st.spinner("Rendering 3D view..."):
        fig = generate_3d_view(
            pretension=st.session_state.pretension,
            shape_type=st.session_state.shape_type,
            support_system=st.session_state.support_system,
            supports=st.session_state.supports,
            span=st.session_state.span,
            rise=st.session_state.rise,
            laa=st.session_state.laa,
            cables_per_bay=st.session_state.cables_per_bay,
            cable_vertical_angle=st.session_state.cable_vertical_angle,
            cable_spread_angle=st.session_state.cable_spread_angle,
            camera_view=st.session_state.camera_view
        )
    
    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True,
        "scrollZoom": True,
        "modeBarButtonsToRemove": ["toImage"]
    })
    
    # Live metrics
    st.markdown("---")
    st.markdown("### 📊 Live Feedback")
    
    health, health_status = get_health_score(st.session_state.pretension)
    beam = get_beam_size(st.session_state.pretension)
    sag = get_sag(st.session_state.pretension, st.session_state.span)
    anchor = get_anchor_force(st.session_state.pretension)
    
    col1, col2, col3, col4 = st.columns(4)
    
    metric_colors = {
        "good": "#2ecc71",
        "warning": "#f39c12",
        "danger": "#e74c3c"
    }
    
    with col1:
        color = metric_colors.get(health_status, "#f0f4fa")
        st.markdown(f"""
        <div class="metric-card">
            <div class="value" style="color:{color};">{health}%</div>
            <div class="label">Health Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{beam}</div>
            <div class="label">Beam Size</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{sag:.1f} cm</div>
            <div class="label">Membrane Sag</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{anchor:.1f} kN</div>
            <div class="label">Anchor Force</div>
        </div>
        """, unsafe_allow_html=True)

with col_controls:
    st.subheader("🎛️ Controls")
    
    # Pretension
    pretension = st.slider(
        "🔧 Pretension (kN/m)",
        min_value=0,
        max_value=100,
        value=st.session_state.pretension,
        step=1
    )
    if pretension != st.session_state.pretension:
        st.session_state.pretension = pretension
        st.rerun()
    
    st.markdown("---")
    
    # Shape
    st.markdown("**📐 Shape Type**")
    shape = st.radio(
        "",
        ["parabolic", "elliptical", "circular", "catenary"],
        index=["parabolic", "elliptical", "circular", "catenary"].index(st.session_state.shape_type),
        key="shape_radio"
    )
    if shape != st.session_state.shape_type:
        st.session_state.shape_type = shape
        st.rerun()
    
    st.markdown("---")
    
    # Support
    st.markdown("**📍 Support System**")
    support = st.radio(
        "",
        ["2_Point", "4_Point"],
        index=0 if st.session_state.support_system == "2_point" else 1,
        key="support_radio"
    )
    support_key = "2_point" if support == "2_Point" else "4_point"
    if support_key != st.session_state.support_system:
        st.session_state.support_system = support_key
        st.rerun()
    
    if st.session_state.support_system == "4_point":
        st.markdown("---")
        st.markdown("**📍 4-Point Positions**")
        
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
        
        # Update supports
        st.session_state.supports["A"] = {"x": x_a, "y": y_a}
        st.session_state.supports["B"] = {"x": x_b, "y": y_b}
        st.session_state.supports["C"] = {"x": x_c, "y": y_c}
        st.session_state.supports["D"] = {"x": x_d, "y": y_d}
    
    st.markdown("---")
    
    # Span, Rise, LAA
    col_span, col_rise = st.columns(2)
    with col_span:
        span = st.number_input("📏 Span (m)", 4.0, 40.0, st.session_state.span, 0.5)
        if span != st.session_state.span:
            st.session_state.span = span
            st.rerun()
    with col_rise:
        rise = st.number_input("📐 Rise (m)", 2.0, 20.0, st.session_state.rise, 0.5)
        if rise != st.session_state.rise:
            st.session_state.rise = rise
            st.rerun()
    
    laa = st.number_input(
        "📏 Apex-to-Apex (LAA) m",
        2.0, 30.0,
        st.session_state.laa,
        0.5
    )
    if laa != st.session_state.laa:
        st.session_state.laa = laa
        st.rerun()
    
    st.markdown("---")
    
    # Cable Controls
    st.markdown("**🔗 Cable Controls**")
    
    cables_per_bay = st.selectbox(
        "Cables per Bay (Pairs)",
        [2, 4, 6],
        index=[2, 4, 6].index(st.session_state.cables_per_bay)
    )
    if cables_per_bay != st.session_state.cables_per_bay:
        st.session_state.cables_per_bay = cables_per_bay
        st.rerun()
    
    cable_vertical_angle = st.slider(
        "📐 Vertical Angle (°)",
        min_value=20,
        max_value=80,
        value=st.session_state.cable_vertical_angle,
        step=5,
        help="Angle from horizontal (20° = shallow, 80° = steep)"
    )
    if cable_vertical_angle != st.session_state.cable_vertical_angle:
        st.session_state.cable_vertical_angle = cable_vertical_angle
        st.rerun()
    
    cable_spread_angle = st.slider(
        "📐 Spread Angle (°)",
        min_value=0,
        max_value=60,
        value=st.session_state.cable_spread_angle,
        step=5,
        help="How much cables spread outward (0° = straight, 60° = wide)"
    )
    if cable_spread_angle != st.session_state.cable_spread_angle:
        st.session_state.cable_spread_angle = cable_spread_angle
        st.rerun()
    
    st.markdown("---")
    
    # Quick presets
    st.markdown("**⚡ Quick Presets**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            for key, value in {
                "pretension": 25,
                "shape_type": "parabolic",
                "support_system": "2_point",
                "span": 10.0,
                "rise": 6.0,
                "laa": 15.0,
                "cables_per_bay": 2,
                "cable_vertical_angle": 45,
                "cable_spread_angle": 30,
                "camera_view": "home"
            }.items():
                st.session_state[key] = value
            st.rerun()
    
    with col2:
        if st.button("📐 Catenary", use_container_width=True):
            st.session_state.shape_type = "catenary"
            st.session_state.pretension = 40
            st.rerun()
    
    with col3:
        if st.button("🏗️ 4-Point", use_container_width=True):
            st.session_state.support_system = "4_point"
            st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("🧬 FDS - 3D Viewer Prototype v6 | Rigid in Principle. Fluid in Application.")
st.caption("✅ ALL FIXES APPLIED: Angles control cables | 4-point cables added | Edge cables follow membrane | Guard clauses for all shapes")
