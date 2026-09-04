import streamlit as st
import json
import os
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import base64

# ============================================================
# PAGE CONFIG (Mobile-Friendly)
# ============================================================
st.set_page_config(
    page_title="SDS Design Studio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit's default menu/footer for a clean app
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .stButton > button {
        font-size: 1.2rem;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        font-weight: 600;
    }
    .stSlider > div > div > div {
        padding: 0.5rem 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 700;
    }
    .reportview-container .markdown-text-container {
        padding: 1rem;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ============================================================
# ENHANCED TYPOLOGY CONFIGURATIONS
# ============================================================
TYPOLOGIES = {
    "saddle_span": {
        "name": "Saddle Span",
        "icon": "🏕️",
        "description": "Dual curved beams with saddle membrane",
        "color": "#FF6B35",
        "params": {
            "A": {"label": "Rise (m)", "min": 2.0, "max": 20.0, "step": 0.5, "default": 6.0},
            "B": {"label": "Span (m)", "min": 4.0, "max": 40.0, "step": 0.5, "default": 10.0},
            "LAA": {"label": "Apex Distance (m)", "min": 4.0, "max": 50.0, "step": 0.5, "default": 15.0},
            "H": {"label": "Exp. Rise (m)", "min": 2.0, "max": 20.0, "step": 0.5, "default": 6.0}
        },
        "qa": [
            "Two primary curved beams?",
            "Supported at lower ends?",
            "Membrane continuous along beams?",
            "P_A is the apex?",
            "A is vertical rise?",
            "B is horizontal span?",
            "LAA is apex-to-apex distance?"
        ]
    },
    "clear_span_tent": {
        "name": "Clear-Span Tent",
        "icon": "🏗️",
        "description": "Column-free tension fabric structure",
        "color": "#E74C3C",
        "params": {
            "span_width": {"label": "Span Width (m)", "min": 3.0, "max": 80.0, "step": 0.5, "default": 10.0},
            "ridge_height": {"label": "Ridge Height (m)", "min": 2.5, "max": 12.0, "step": 0.5, "default": 5.0},
            "bay_distance": {"label": "Bay Distance (m)", "min": 3.0, "max": 10.0, "step": 0.5, "default": 5.0},
            "num_bays": {"label": "Number of Bays", "min": 1, "max": 20, "step": 1, "default": 4}
        },
        "qa": [
            "Zero interior columns?",
            "Pin-based supports?",
            "Fabric tensioned at ridge?",
            "Sidewalls open or enclosed?",
            "Ridge height from ground?",
            "Uniform bay distances?",
            "Span measured between outer legs?"
        ]
    },
    "tensile_membrane": {
        "name": "Tensile Membrane",
        "icon": "⛺",
        "description": "Mast-supported tensile fabric structure",
        "color": "#2ECC71",
        "params": {
            "mast_height": {"label": "Mast Height (m)", "min": 3.0, "max": 30.0, "step": 0.5, "default": 8.0},
            "span_length": {"label": "Span Length (m)", "min": 5.0, "max": 100.0, "step": 0.5, "default": 20.0},
            "span_width": {"label": "Span Width (m)", "min": 5.0, "max": 80.0, "step": 0.5, "default": 15.0},
            "cable_count": {"label": "Number of Cables", "min": 2, "max": 12, "step": 1, "default": 4}
        },
        "qa": [
            "Boundary tension membrane?",
            "Interior masts present?",
            "Anticlastic or synclastic?",
            "Edge cables included?",
            "Prestress applied?",
            "Cables anchored to ground?",
            "Fabric type: PVC or PTFE?"
        ]
    },
    "portal_frame": {
        "name": "Portal Frame",
        "icon": "🏛️",
        "description": "Rigid steel frame with crane capability",
        "color": "#3498DB",
        "params": {
            "eave_height": {"label": "Eave Height (m)", "min": 3.0, "max": 15.0, "step": 0.5, "default": 6.0},
            "span_width": {"label": "Span Width (m)", "min": 10.0, "max": 50.0, "step": 0.5, "default": 20.0},
            "bay_spacing": {"label": "Bay Spacing (m)", "min": 4.0, "max": 12.0, "step": 0.5, "default": 6.0},
            "roof_pitch": {"label": "Roof Pitch (deg)", "min": 1.0, "max": 15.0, "step": 0.5, "default": 5.0},
            "num_bays": {"label": "Number of Bays", "min": 2, "max": 30, "step": 1, "default": 5},
            "crane_load": {"label": "Crane Load (tonnes)", "min": 0.0, "max": 50.0, "step": 0.5, "default": 0.0}
        },
        "qa": [
            "Column bases pin-supported?",
            "Roof purlin-supported?",
            "Overhead crane (yes/no)?",
            "Fully enclosed cladding?",
            "Wind bracing in walls?",
            "Roof material type?",
            "Crane loads considered?"
        ]
    },
    # NEW: Hyperbolic Paraboloid
    "hypar": {
        "name": "Hypar Roof",
        "icon": "🌀",
        "description": "Hyperbolic paraboloid shell structure",
        "color": "#9B59B6",
        "params": {
            "span_x": {"label": "X-Span (m)", "min": 5.0, "max": 40.0, "step": 0.5, "default": 15.0},
            "span_y": {"label": "Y-Span (m)", "min": 5.0, "max": 40.0, "step": 0.5, "default": 15.0},
            "height": {"label": "Height (m)", "min": 2.0, "max": 15.0, "step": 0.5, "default": 6.0},
            "twist": {"label": "Twist Factor", "min": 0.1, "max": 1.0, "step": 0.05, "default": 0.5}
        },
        "qa": [
            "Double-curved surface?",
            "Supported at corners?",
            "Concrete or steel shell?",
            "Thickness adequate?",
            "Edge beams included?",
            "Formwork required?",
            "Architectural finish?"
        ]
    },
    # NEW: Truss System
    "truss": {
        "name": "Truss System",
        "icon": "📐",
        "description": "Triangulated steel truss framework",
        "color": "#F39C12",
        "params": {
            "span": {"label": "Span (m)", "min": 5.0, "max": 60.0, "step": 0.5, "default": 20.0},
            "depth": {"label": "Depth (m)", "min": 0.5, "max": 5.0, "step": 0.25, "default": 2.0},
            "bay_count": {"label": "Number of Bays", "min": 2, "max": 20, "step": 1, "default": 8},
            "loading": {"label": "Loading (kN/m²)", "min": 0.5, "max": 10.0, "step": 0.5, "default": 2.0}
        },
        "qa": [
            "Parallel chord truss?",
            "Pin or fixed connections?",
            "Roof cladding attached?",
            "Bracing provided?",
            "Deflection limits met?",
            "Fire protection needed?",
            "Lifting points included?"
        ]
    }
}

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "typology" not in st.session_state:
    st.session_state.typology = None
if "params" not in st.session_state:
    st.session_state.params = {}
if "mode" not in st.session_state:
    st.session_state.mode = "design"
if "qa_answers" not in st.session_state:
    st.session_state.qa_answers = {}
if "locked" not in st.session_state:
    st.session_state.locked = False
if "view_history" not in st.session_state:
    st.session_state.view_history = []
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "design_notes" not in st.session_state:
    st.session_state.design_notes = ""

# ============================================================
# ENHANCED CACHE HANDLER
# ============================================================
CACHE_DIR = ".sds_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "current_session.json")
HISTORY_FILE = os.path.join(CACHE_DIR, "design_history.json")

def save_cache():
    data = {
        "typology": st.session_state.typology,
        "params": st.session_state.params,
        "qa_answers": st.session_state.qa_answers,
        "locked": st.session_state.locked,
        "design_notes": st.session_state.design_notes,
        "timestamp": datetime.now().isoformat()
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    # Save to history
    if st.session_state.typology:
        history = load_history()
        history.append(data)
        if len(history) > 50:  # Keep last 50 designs
            history = history[-50:]
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

# Auto-load cache on boot
cached = load_cache()
if cached:
    st.session_state.typology = cached.get("typology")
    st.session_state.params = cached.get("params", {})
    st.session_state.qa_answers = cached.get("qa_answers", {})
    st.session_state.locked = cached.get("locked", False)
    st.session_state.design_notes = cached.get("design_notes", "")

# ============================================================
# ADVANCED 3D GEOMETRY GENERATORS
# ============================================================
def generate_saddle_span(params):
    A = params.get("A", 6.0)
    B = params.get("B", 10.0)
    LAA = params.get("LAA", 15.0)
    H = params.get("H", 6.0)
    
    x = np.linspace(-B/2, B/2, 30)
    y1 = A * (1 - (x/(B/2))**2)
    y2 = A * (1 - (x/(B/2))**2)
    
    fig = go.Figure()
    
    # Beams with gradient
    fig.add_trace(go.Scatter3d(
        x=x, y=[0]*len(x), z=y1, 
        mode='lines', 
        name='Beam 1', 
        line=dict(width=10, color='#FF6B35')
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=[LAA]*len(x), z=y2, 
        mode='lines', 
        name='Beam 2', 
        line=dict(width=10, color='#FF6B35')
    ))
    
    # Support points with labels
    support_points = [
        (-B/2, 0, 0), (B/2, 0, 0),
        (-B/2, LAA, 0), (B/2, LAA, 0)
    ]
    sx, sy, sz = zip(*support_points)
    fig.add_trace(go.Scatter3d(
        x=sx, y=sy, z=sz,
        mode='markers+text',
        name='Supports',
        marker=dict(size=12, color='red', symbol='circle'),
        text=['Support']*4,
        textposition='bottom center'
    ))
    
    # Apex points
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, LAA], z=[A, A],
        mode='markers+text',
        name='Apex',
        marker=dict(size=16, color='gold', symbol='diamond'),
        text=['Apex']*2,
        textposition='top center'
    ))
    
    # Enhanced saddle surface with curvature lines
    Y, X = np.meshgrid(np.linspace(0, LAA, 30), x)
    Z = A * (1 - (X/(B/2))**2) * (1 - 0.3 * (Y/LAA)**2) + 0.2 * A * (Y/LAA) * (1 - Y/LAA)
    
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z, 
        opacity=0.6, 
        colorscale='Viridis', 
        showscale=True,
        name='Membrane'
    ))
    
    # Add contour lines for structural analysis
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z-0.01,
        opacity=0.1,
        colorscale='RdBu',
        showscale=False,
        contours={
            "z": {"show": True, "usecolormap": True, "highlightcolor": "#ffffff", "project": {"z": True}}
        }
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Span (m)',
            yaxis_title='Width (m)',
            zaxis_title='Height (m)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
            annotations=[
                dict(showarrow=False, x=0, y=LAA/2, z=A*0.8, text=f"A={A}m", font=dict(size=12))
            ]
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        showlegend=True
    )
    return fig

def generate_hypar(params):
    span_x = params.get("span_x", 15.0)
    span_y = params.get("span_y", 15.0)
    height = params.get("height", 6.0)
    twist = params.get("twist", 0.5)
    
    x = np.linspace(-span_x/2, span_x/2, 30)
    y = np.linspace(-span_y/2, span_y/2, 30)
    X, Y = np.meshgrid(x, y)
    Z = height * (X/span_x)**2 - twist * height * (Y/span_y)**2
    
    fig = go.Figure()
    
    # Hypar surface
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        opacity=0.7,
        colorscale='Plasma',
        showscale=True,
        name='Hypar Surface'
    ))
    
    # Edge beams
    for x_val in [-span_x/2, span_x/2]:
        fig.add_trace(go.Scatter3d(
            x=[x_val]*len(y), y=y, z=height * (x_val/span_x)**2 - twist * height * (y/span_y)**2,
            mode='lines',
            line=dict(width=6, color='white'),
            name='Edge Beam'
        ))
    
    # Corner supports
    corners = [(-span_x/2, -span_y/2), (-span_x/2, span_y/2), 
               (span_x/2, -span_y/2), (span_x/2, span_y/2)]
    cx, cy, cz = [], [], []
    for c in corners:
        cx.append(c[0])
        cy.append(c[1])
        cz.append(height * (c[0]/span_x)**2 - twist * height * (c[1]/span_y)**2)
    
    fig.add_trace(go.Scatter3d(
        x=cx, y=cy, z=cz,
        mode='markers',
        marker=dict(size=12, color='red'),
        name='Support Points'
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Height (m)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

def generate_truss(params):
    span = params.get("span", 20.0)
    depth = params.get("depth", 2.0)
    bays = params.get("bay_count", 8)
    loading = params.get("loading", 2.0)
    
    bay_len = span / bays
    fig = go.Figure()
    
    # Top chord
    x_top = np.linspace(-span/2, span/2, bays+1)
    y_top = [depth/2] * len(x_top)
    
    # Bottom chord
    x_bot = np.linspace(-span/2, span/2, bays+1)
    y_bot = [-depth/2] * len(x_bot)
    
    # Top chord line
    fig.add_trace(go.Scatter3d(
        x=x_top, y=[0]*len(x_top), z=y_top,
        mode='lines+markers',
        line=dict(width=6, color='#2C3E50'),
        marker=dict(size=4, color='#2C3E50'),
        name='Top Chord'
    ))
    
    # Bottom chord line
    fig.add_trace(go.Scatter3d(
        x=x_bot, y=[0]*len(x_bot), z=y_bot,
        mode='lines+markers',
        line=dict(width=6, color='#2C3E50'),
        marker=dict(size=4, color='#2C3E50'),
        name='Bottom Chord'
    ))
    
    # Web members (zigzag pattern)
    for i in range(bays):
        # Diagonal members
        x1 = -span/2 + i * bay_len
        x2 = -span/2 + (i+1) * bay_len
        
        # V-formation
        fig.add_trace(go.Scatter3d(
            x=[x1, x1 + bay_len/2],
            y=[0, 0],
            z=[depth/2, -depth/2],
            mode='lines',
            line=dict(width=3, color='#E74C3C'),
            showlegend=False
        ))
        fig.add_trace(go.Scatter3d(
            x=[x1 + bay_len/2, x2],
            y=[0, 0],
            z=[-depth/2, depth/2],
            mode='lines',
            line=dict(width=3, color='#E74C3C'),
            showlegend=False
        ))
        
        # Vertical members
        fig.add_trace(go.Scatter3d(
            x=[x1, x1],
            y=[0, 0],
            z=[depth/2, -depth/2],
            mode='lines',
            line=dict(width=2, color='#95A5A6', dash='dash'),
            showlegend=False
        ))
    
    # Deflection indicator (visual only)
    defl_factor = loading * 0.01  # Simplified deflection
    x_def = np.linspace(-span/2, span/2, 20)
    y_def = -defl_factor * (1 - (x_def/(span/2))**2)
    fig.add_trace(go.Scatter3d(
        x=x_def, y=[0.2]*len(x_def), z=y_def,
        mode='lines',
        line=dict(width=2, color='red', dash='dash'),
        name=f'Deflection (approx)'
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Span (m)',
            yaxis_title='Bay',
            zaxis_title='Depth (m)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(x=0.01, y=0.99)
    )
    return fig

def generate_tent(params):
    span = params.get("span_width", 10.0)
    ridge = params.get("ridge_height", 5.0)
    bays = params.get("num_bays", 4)
    bay_dist = params.get("bay_distance", 5.0)
    total_len = bays * bay_dist
    
    x = np.linspace(-span/2, span/2, 20)
    z = ridge * (1 - (x/(span/2))**2)
    
    fig = go.Figure()
    
    # Ridge line with gradient
    fig.add_trace(go.Scatter3d(
        x=[0,0], y=[0,total_len], z=[ridge,ridge],
        mode='lines',
        name='Ridge',
        line=dict(width=12, color='#FF6B35')
    ))
    
    # Eave lines
    fig.add_trace(go.Scatter3d(
        x=[-span/2,-span/2], y=[0,total_len], z=[0,0],
        mode='lines',
        name='Eave Left',
        line=dict(width=4, color='#2C3E50')
    ))
    fig.add_trace(go.Scatter3d(
        x=[span/2,span/2], y=[0,total_len], z=[0,0],
        mode='lines',
        name='Eave Right',
        line=dict(width=4, color='#2C3E50')
    ))
    
    # Fabric surface with improved rendering
    Y, X = np.meshgrid(np.linspace(0, total_len, 20), x)
    Z = ridge * (1 - (X/(span/2))**2) * (1 - (Y/total_len)**2 * 0.1)
    
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        opacity=0.6,
        colorscale='Reds',
        showscale=True,
        name='Fabric'
    ))
    
    # Support points
    fig.add_trace(go.Scatter3d(
        x=[-span/2, span/2, -span/2, span/2],
        y=[0, 0, total_len, total_len],
        z=[0, 0, 0, 0],
        mode='markers',
        marker=dict(size=10, color='green'),
        name='Supports'
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)',
            yaxis_title='Length (m)',
            zaxis_title='Height (m)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

def generate_tensile(params):
    mast = params.get("mast_height", 8.0)
    length = params.get("span_length", 20.0)
    width = params.get("span_width", 15.0)
    cables = params.get("cable_count", 4)
    
    fig = go.Figure()
    
    # Mast with gradient
    fig.add_trace(go.Scatter3d(
        x=[0,0], y=[0,0], z=[0,mast],
        mode='lines',
        name='Mast',
        line=dict(width=14, color='#2C3E50')
    ))
    
    # Mast top with glow effect
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[mast],
        mode='markers',
        name='Mast Top',
        marker=dict(size=16, color='gold', symbol='diamond')
    ))
    
    # Membrane surface
    X = np.linspace(-length/2, length/2, 30)
    Y = np.linspace(-width/2, width/2, 30)
    X, Y = np.meshgrid(X, Y)
    Z = mast * np.exp(-((X/(length/2))**2 + (Y/(width/2))**2) * 0.5)
    
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        opacity=0.6,
        colorscale='Greens',
        showscale=True,
        name='Membrane'
    ))
    
    # Cable lines with stress indication
    for i in range(cables):
        angle = i * 2*np.pi/cables
        x_end = length/2 * np.cos(angle)
        y_end = width/2 * np.sin(angle)
        # Cable thickness varies with angle
        thickness = 3 + np.sin(angle)  # Visual stress indicator
        fig.add_trace(go.Scatter3d(
            x=[0, x_end], y=[0, y_end], z=[mast, 0],
            mode='lines',
            line=dict(width=thickness, color='gray'),
            name=f'Cable {i+1}'
        ))
    
    # Anchor points
    for i in range(cables):
        angle = i * 2*np.pi/cables
        x_end = length/2 * np.cos(angle)
        y_end = width/2 * np.sin(angle)
        fig.add_trace(go.Scatter3d(
            x=[x_end], y=[y_end], z=[0],
            mode='markers',
            marker=dict(size=8, color='red'),
            showlegend=False
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Length (m)',
            yaxis_title='Width (m)',
            zaxis_title='Height (m)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

def generate_portal(params):
    eave = params.get("eave_height", 6.0)
    span = params.get("span_width", 20.0)
    pitch = params.get("roof_pitch", 5.0)
    bays = params.get("num_bays", 5)
    bay_spacing = params.get("bay_spacing", 6.0)
    crane_load = params.get("crane_load", 0.0)
    total_len = bays * bay_spacing
    
    roof_rise = span/2 * np.tan(np.radians(pitch))
    ridge = eave + roof_rise
    
    fig = go.Figure()
    
    # Portal frame geometry
    x = [-span/2, -span/2, 0, span/2, span/2]
    z = [0, eave, ridge, eave, 0]
    
    # Main frame (highlighted)
    fig.add_trace(go.Scatter3d(
        x=x, y=[0]*len(x), z=z,
        mode='lines+markers',
        name='Main Frame',
        line=dict(width=10, color='#2C3E50'),
        marker=dict(size=6, color='#2C3E50')
    ))
    
    # All bays with fading opacity
    for i in range(bays):
        y = i * bay_spacing
        opacity = 1.0 if i == 0 else 0.3 + 0.7 * (1 - i/bays)
        color = '#3498DB' if i % 2 == 0 else '#2980B9'
        fig.add_trace(go.Scatter3d(
            x=x, y=[y]*len(x), z=z,
            mode='lines',
            line=dict(width=4, color=color, opacity=opacity),
            name=f'Bay {i+1}' if i == 0 else None,
            showlegend=(i == 0)
        ))
    
    # Roof sheeting with gradient
    Y, X = np.meshgrid(np.linspace(0, total_len, 20), np.linspace(-span/2, span/2, 30))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        opacity=0.4,
        colorscale='Greys',
        showscale=True,
        name='Roof Sheeting'
    ))
    
    # Crane system if load > 0
    if crane_load > 0:
        crane_height = eave * 0.6
        # Crane bridge
        fig.add_trace(go.Scatter3d(
            x=[-span/3, span/3],
            y=[total_len/4, total_len/4],
            z=[crane_height, crane_height],
            mode='lines',
            name=f'Crane Bridge ({crane_load}t)',
            line=dict(width=8, color='#E74C3C')
        ))
        # Crane hook
        fig.add_trace(go.Scatter3d(
            x=[0], y=[total_len/4], z=[0],
            mode='markers',
            marker=dict(size=10, color='#E74C3C', symbol='circle'),
            name='Hook Point'
        ))
        # Crane travel path
        fig.add_trace(go.Scatter3d(
            x=[-span/4, span/4],
            y=[total_len/4, total_len/4],
            z=[crane_height, crane_height],
            mode='lines',
            line=dict(width=2, color='#E74C3C', dash='dash'),
            name='Travel Path'
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)',
            yaxis_title='Length (m)',
            zaxis_title='Height (m)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

GENERATORS = {
    "saddle_span": generate_saddle_span,
    "clear_span_tent": generate_tent,
    "tensile_membrane": generate_tensile,
    "portal_frame": generate_portal,
    "hypar": generate_hypar,
    "truss": generate_truss
}

# ============================================================
# ENHANCED UI RENDERING
# ============================================================
st.title("🏗️ SDS Design Studio")

# ---- SIDEBAR (Hidden but accessible) ----
with st.sidebar:
    st.header("⚙️ Tools")
    if st.button("📊 Export Design Summary", use_container_width=True):
        st.session_state.show_export = True
    if st.button("🔄 Reset All", use_container_width=True):
        for key in st.session_state.keys():
            if key not in ["typology", "params", "qa_answers"]:
                del st.session_state[key]
        st.session_state.typology = None
        st.session_state.params = {}
        st.session_state.qa_answers = {}
        st.rerun()
    st.divider()
    st.caption(f"Session: {datetime.now().strftime('%H:%M')}")

# ---- CATALOG VIEW ----
if st.session_state.typology is None:
    st.subheader("Choose a structure type:")
    
    # Enhanced catalog with descriptions
    cols = st.columns(2)
    idx = 0
    for key, typ in TYPOLOGIES.items():
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"""
                <div style='border: 2px solid {typ["color"]}; border-radius: 12px; padding: 0.75rem; margin-bottom: 0.5rem;'>
                    <h3 style='margin: 0;'>{typ['icon']} {typ['name']}</h3>
                    <p style='margin: 0; font-size: 0.8rem; opacity: 0.7;'>{typ['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Select {typ['name']}", use_container_width=True, key=f"btn_{key}"):
                    st.session_state.typology = key
                    st.session_state.params = {p: v["default"] for p, v in typ["params"].items()}
                    st.session_state.qa_answers = {}
                    st.session_state.locked = False
                    save_cache()
                    st.rerun()
        idx += 1
    
    # Design history
    history = load_history()
    if history:
        with st.expander("📜 Recent Designs"):
            for i, design in enumerate(history[-5:]):
                typ = design.get("typology", "Unknown")
                if typ in TYPOLOGIES:
                    st.write(f"{TYPOLOGIES[typ]['icon']} {TYPOLOGIES[typ]['name']} - {design.get('timestamp', '')[:10]}")
    
    st.stop()

# ---- ACTIVE TYPOLOGY VIEW ----
typ_key = st.session_state.typology
typ = TYPOLOGIES[typ_key]
params = st.session_state.params

# Header with enhanced controls
col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
with col1:
    if st.button("⬅", help="Back to catalog", key="back_btn"):
        st.session_state.typology = None
        st.session_state.mode = "design"
        st.session_state.locked = False
        save_cache()
        st.rerun()
with col2:
    st.subheader(f"{typ['icon']} {typ['name']}")
with col3:
    if st.session_state.mode == "design":
        if st.button("🔍 Pro View", use_container_width=True, key="pro_btn"):
            st.session_state.mode = "engineer"
            save_cache()
            st.rerun()
    else:
        if st.button("✏️ Edit", use_container_width=True, key="edit_btn"):
            st.session_state.mode = "design"
            save_cache()
            st.rerun()
with col4:
    if st.button("⭐ Favorite", use_container_width=True, key="fav_btn"):
        if typ_key not in st.session_state.favorites:
            st.session_state.favorites.append(typ_key)
            st.success("Added to favorites!")

# ---- LOCK STATUS ----
if st.session_state.locked:
    st.warning("🔒 Design is LOCKED. Edit mode is disabled.")

# ---- 3D PREVIEW with controls ----
st.subheader("📐 3D Preview")
if typ_key in GENERATORS:
    fig = GENERATORS[typ_key](params)
    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["toImage"],
        "displaylogo": False
    })

# ---- DESIGN MODE: Sliders + Q&A ----
if st.session_state.mode == "design" and not st.session_state.locked:
    # Parameters with enhanced layout
    st.subheader("📐 Dimensions")
    
    # Group sliders in rows
    param_items = list(typ["params"].items())
    for i in range(0, len(param_items), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(param_items):
                p_key, p_def = param_items[i + j]
                with cols[j]:
                    val = st.slider(
                        p_def["label"],
                        min_value=float(p_def["min"]),
                        max_value=float(p_def["max"]),
                        step=float(p_def["step"]),
                        value=float(params.get(p_key, p_def["default"])),
                        key=f"slider_{p_key}"
                    )
                    params[p_key] = val
                    # Show real-time value
                    st.caption(f"Current: {val:.1f}")
    
    # Auto-save
    save_cache()
    
    # Design Notes
    st.subheader("📝 Design Notes")
    st.session_state.design_notes = st.text_area(
        "Add notes about your design:",
        value=st.session_state.design_notes,
        height=100,
        placeholder="Enter design notes, constraints, or special requirements..."
    )
    
    # Q&A Board with categorization
    st.subheader("📋 Confirm Design")
    
    # Split Q&A into categories
    qa_items = typ["qa"]
    for i, q in enumerate(qa_items):
        key = f"qa_{i}"
        default = st.session_state.qa_answers.get(key, "Yes")
        
        # Categorize questions
        if "material" in q.lower() or "fabric" in q.lower():
            options = ["PVC", "PTFE", "Steel", "Aluminum", "Glass"]
        elif "support" in q.lower() or "base" in q.lower():
            options = ["Yes", "No", "Not Sure", "N/A"]
        elif "load" in q.lower() or "crane" in q.lower():
            options = ["Yes", "No", "N/A"]
        else:
            options = ["Yes", "No", "Not Sure"]
        
        ans = st.radio(q, options, index=options.index(default) if default in options else 0, key=key)
        st.session_state.qa_answers[key] = ans
    
    save_cache()
    
    # Lock Button with confirmation
    if st.button("🔒 LOCK & PROCEED", use_container_width=True, type="primary", key="lock_btn"):
        if st.session_state.design_notes.strip():
            st.session_state.locked = True
            save_cache()
            st.rerun()
        else:
            st.warning("Please add design notes before locking.")
            st.session_state.locked = True  # Allow lock even without notes
            save_cache()
            st.rerun()

# ---- ENGINEER MODE ----
if st.session_state.mode == "engineer" or st.session_state.locked:
    st.subheader("🔬 Structural Analysis")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Parameter Count", len(params))
    with col2:
        total_load = sum(params.values()) / len(params) if params else 0
        st.metric("⚖️ Avg Load", f"{total_load:.1f}")
    with col3:
        st.metric("📅 Saved", datetime.now().strftime("%H:%M"))
    
    # Parameter summary
    with st.expander("📊 Parameters Summary", expanded=True):
        for p_key, p_def in typ["params"].items():
            val = params.get(p_key, p_def["default"])
            st.metric(p_def["label"], f"{val:.1f}")
    
    # Design notes
    if st.session_state.design_notes:
        with st.expander("📝 Design Notes", expanded=True):
            st.write(st.session_state.design_notes)
    
    # Q&A summary
    with st.expander("📋 Design Confirmations"):
        for i, q in enumerate(typ["qa"]):
            ans = st.session_state.qa_answers.get(f"qa_{i}", "Not answered")
            st.write(f"**{q}** → {ans}")
    
    # Structural analysis indicators
    with st.expander("📐 Structural Indicators"):
        # Calculate some simple indicators
        if typ_key == "saddle_span":
            A = params.get("A", 6.0)
            B = params.get("B", 10.0)
            ratio = A/B
            st.metric("A/B Ratio", f"{ratio:.2f}", 
                     delta="Shallow" if ratio < 0.5 else "Steep" if ratio > 1.0 else "Optimal")
            st.progress(min(ratio, 1.0))
            
        elif typ_key == "portal_frame":
            eave = params.get("eave_height", 6.0)
            span = params.get("span_width", 20.0)
            pitch = params.get("roof_pitch", 5.0)
            st.metric("Span/Height Ratio", f"{span/eave:.1f}")
            st.metric("Roof Slope", f"{pitch}°")
            
        elif typ_key == "truss":
            span = params.get("span", 20.0)
            depth = params.get("depth", 2.0)
            st.metric("Span/Depth Ratio", f"{span/depth:.1f}")
            if span/depth > 15:
                st.warning("⚠️ High span/depth ratio - consider increasing depth")
    
    # Export function
    if st.button("📊 Export Design Summary", use_container_width=True):
        summary = f"""
        SDS Design Studio - Export
        ============================
        Typology: {typ['icon']} {typ['name']}
        Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
        Parameters:
        {chr(10).join([f"  {p_def['label']}: {params.get(p_key, p_def['default']):.1f}" for p_key, p_def in typ['params'].items()])}
        
        Design Notes:
        {st.session_state.design_notes if st.session_state.design_notes else 'None'}
        
        Confirmations:
        {chr(10).join([f"  {q}: {st.session_state.qa_answers.get(f'qa_{i}', 'Not answered')}" for i, q in enumerate(typ['qa'])])}
        """
        st.download_button(
            label="📥 Download Summary",
            data=summary,
            file_name=f"SDS_Design_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # Unlock button
    if st.session_state.locked:
        if st.button("🔓 Unlock to Edit", use_container_width=True, key="unlock_btn"):
            st.session_state.locked = False
            st.session_state.mode = "design"
            save_cache()
            st.rerun()

# ---- FOOTER ----
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption("SDS Platform v1.1 | Built for mobile")
with col2:
    st.caption(f"Auto-saved: {datetime.now().strftime('%H:%M:%S')}")

# ============================================================
# RUN: Save cache on every interaction
# ============================================================
save_cache()
