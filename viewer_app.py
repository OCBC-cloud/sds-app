import streamlit as st
import plotly.graph_objects as go
import numpy as np

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="FDS - 3D Viewer Prototype",
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
    .stRadio > div label[data-checked="true"] {
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
# SHAPE FUNCTIONS
# ============================================================
def get_beam_shape(x, span, rise, shape_type="parabolic"):
    """Calculate beam shape based on type"""
    if span <= 0:
        return np.zeros_like(x)
    x_norm = 2 * x / span
    if shape_type == "parabolic":
        return rise * (1 - x_norm**2)
    elif shape_type == "elliptical":
        return rise * np.sqrt(1 - x_norm**2)
    elif shape_type == "circular":
        R = (span**2 + 4*rise**2) / (8*rise)
        return rise - (R - np.sqrt(R**2 - x**2))
    elif shape_type == "catenary":
        a = span / (2 * np.arcsinh(rise / (span/2))) if rise > 0 else 1
        return rise * (1 - (np.cosh(x/a) - 1) / (np.cosh(span/(2*a)) - 1)) if a > 0 else rise * (1 - x_norm**2)
    return rise * (1 - x_norm**2)

# ============================================================
# SESSION STATE
# ============================================================
if "pretension" not in st.session_state:
    st.session_state.pretension = 25
if "shape_type" not in st.session_state:
    st.session_state.shape_type = "parabolic"
if "support_system" not in st.session_state:
    st.session_state.support_system = "2_point"
if "span" not in st.session_state:
    st.session_state.span = 10.0
if "rise" not in st.session_state:
    st.session_state.rise = 6.0
if "supports" not in st.session_state:
    st.session_state.supports = {
        "A": {"x": -5.0, "y": 3.0},
        "B": {"x": 5.0, "y": 3.0},
        "C": {"x": -5.0, "y": -3.0},
        "D": {"x": 5.0, "y": -3.0}
    }

# ============================================================
# 3D GENERATOR
# ============================================================
def generate_3d_view(pretension, shape_type, support_system, supports, span, rise):
    """Generate 3D visualization with all parameters"""
    
    num_points = 40
    
    # Get beam shape
    x = np.linspace(-span/2, span/2, num_points)
    z_beam = get_beam_shape(x, span, rise, shape_type)
    
    # Determine support configuration
    if support_system == "2_point":
        y1 = -3.0 * (1 - (2 * x / span)**2)
        y2 = 3.0 * (1 - (2 * x / span)**2)
        
        fig = go.Figure()
        
        # Beams
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_beam,
            mode='lines', name='Beam 1',
            line=dict(color='#FF6B6B', width=8)
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_beam,
            mode='lines', name='Beam 2',
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
            marker=dict(color='#FF6B6B', size=12, symbol='square'),
            text=['Support L', 'Support R'],
            textposition='top center',
            name='Supports'
        ))
        
        # Apex
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[rise],
            mode='markers+text',
            marker=dict(color='#FFD93D', size=14, symbol='diamond'),
            text=['▲ APEX'],
            textposition='top center',
            name='Apex'
        ))
        
    else:  # 4_point
        A = supports["A"]
        B = supports["B"]
        C = supports["C"]
        D = supports["D"]
        
        # Calculate span and width
        span_x = B["x"] - A["x"]
        width_y = C["y"] - A["y"]
        
        x_vals = np.linspace(A["x"], B["x"], num_points)
        y_vals = np.linspace(C["y"], A["y"], num_points)
        X, Y = np.meshgrid(x_vals, y_vals)
        
        x_norm = (X - A["x"]) / span_x * 2 - 1
        y_norm = (Y - C["y"]) / width_y * 2 - 1
        
        Z = rise * (1 - x_norm**2) * (1 - y_norm**2)
        
        fig = go.Figure()
        
        # Membrane surface
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale=[[0, '#1a2a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
            opacity=0.7,
            showscale=False,
            name='Membrane'
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
                marker=dict(color='#FF6B6B', size=12, symbol='square'),
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
            marker=dict(color='#FFD93D', size=14, symbol='diamond'),
            text=['▲ APEX'],
            textposition='top center',
            name='Apex'
        ))
        
        # Edge cables
        edge_pairs = [(A, B), (B, D), (D, C), (C, A)]
        for p1, p2 in edge_pairs:
            fig.add_trace(go.Scatter3d(
                x=[p1["x"], p2["x"]],
                y=[p1["y"], p2["y"]],
                z=[0, 0],
                mode='lines',
                line=dict(color='#FFD93D', width=3, dash='dash'),
                showlegend=False
            ))
    
    # Common layout
    fig.update_layout(
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a', range=[-8, 8]),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a', range=[-8, 8]),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a', range=[0, 10]),
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2))
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
# HELPER FUNCTIONS
# ============================================================
def get_health_score(pretension):
    """Calculate health score based on pretension"""
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
    """Get beam size based on pretension"""
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
    """Calculate membrane sag"""
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
    """Calculate anchor force"""
    return pretension * 0.6 * (1 + pretension / 100)

# ============================================================
# MAIN UI
# ============================================================
st.title("🧬 FDS - 3D Viewer Prototype")
st.caption("Test pretension, support systems, and shapes in real-time")
st.markdown("---")

# Main layout: 3D viewport on top, controls below
col_viewport, col_controls = st.columns([2, 1])

with col_viewport:
    st.subheader("🔬 Live 3D Viewport")
    
    # Generate and display 3D figure
    fig = generate_3d_view(
        pretension=st.session_state.pretension,
        shape_type=st.session_state.shape_type,
        support_system=st.session_state.support_system,
        supports=st.session_state.supports,
        span=st.session_state.span,
        rise=st.session_state.rise
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    
    # Live metrics
    st.markdown("---")
    st.markdown("### 📊 Live Feedback")
    
    health, health_status = get_health_score(st.session_state.pretension)
    beam = get_beam_size(st.session_state.pretension)
    sag = get_sag(st.session_state.pretension, st.session_state.span)
    anchor = get_anchor_force(st.session_state.pretension)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        color = "#2ecc71" if health_status == "good" else "#f39c12" if health_status == "warning" else "#e74c3c"
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
    
    # Pretension Slider
    pretension = st.slider(
        "🔧 Pretension (kN/m)",
        min_value=0,
        max_value=100,
        value=st.session_state.pretension,
        step=1,
        help="Higher pretension = tighter membrane, lighter beams"
    )
    if pretension != st.session_state.pretension:
        st.session_state.pretension = pretension
        st.rerun()
    
    st.markdown("---")
    
    # Shape Selection
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
    
    # Support System
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
    
    # 4-Point Controls
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
        
        st.session_state.supports["A"] = {"x": x_a, "y": y_a}
        st.session_state.supports["B"] = {"x": x_b, "y": y_b}
        st.session_state.supports["C"] = {"x": x_c, "y": y_c}
        st.session_state.supports["D"] = {"x": x_d, "y": y_d}
    
    st.markdown("---")
    
    # Span and Rise
    span = st.number_input("📏 Span (m)", 4.0, 40.0, st.session_state.span, 0.5)
    if span != st.session_state.span:
        st.session_state.span = span
        st.rerun()
    
    rise = st.number_input("📐 Rise (m)", 2.0, 20.0, st.session_state.rise, 0.5)
    if rise != st.session_state.rise:
        st.session_state.rise = rise
        st.rerun()
    
    st.markdown("---")
    
    # Quick presets
    st.markdown("**⚡ Quick Presets**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.pretension = 25
            st.session_state.shape_type = "parabolic"
            st.session_state.support_system = "2_point"
            st.session_state.span = 10.0
            st.session_state.rise = 6.0
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
st.caption("🧬 FDS - 3D Viewer Prototype | Rigid in Principle. Fluid in Application.")
st.caption("🔬 Use this standalone viewer to test pretension, shapes, and support systems in real-time.")
