import streamlit as st
import json
import os
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import random
import string

# ============================================================
# PAGE CONFIG (Mobile-Friendly | Dark Mode)
# ============================================================
st.set_page_config(
    page_title="SDS Design Studio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CUSTOM DARK MODE CSS
# ============================================================
dark_mode_css = """
    <style>
    /* Main background */
    .stApp {
        background-color: #0a0e17;
        color: #e0e6ed;
    }
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0rem;
    }
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #f0f4fa !important;
        font-weight: 600 !important;
    }
    .stSubheader {
        color: #b0c4de !important;
    }
    /* Cards and Containers */
    .stButton > button {
        background-color: #1e2a3a;
        color: #e0e6ed;
        border: 1px solid #2a3a4f;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #2a3a4f;
        border-color: #4a7a9c;
        color: white;
    }
    .stButton > button:active {
        background-color: #3a4a5f;
    }
    /* Primary button (Lock / Submit) */
    .stButton > button[kind="primary"] {
        background-color: #f39c12;
        color: #0a0e17;
        border: none;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #f1c40f;
        color: #0a0e17;
    }
    /* Sliders */
    .stSlider > div > div > div {
        background-color: #1e2a3a !important;
    }
    .stSlider > div > div > div > div {
        background-color: #f39c12 !important;
    }
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background-color: #141e2b !important;
        color: #e0e6ed !important;
        border: 1px solid #2a3a4f !important;
        border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #f39c12 !important;
        box-shadow: 0 0 0 2px rgba(243, 156, 18, 0.2) !important;
    }
    /* Labels */
    .stSlider label, .stTextInput label, .stTextArea label, .stSelectbox label {
        color: #b0c4de !important;
        font-weight: 400 !important;
    }
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #141e2b !important;
        border-radius: 8px !important;
        border: 1px solid #1e2a3a !important;
        color: #e0e6ed !important;
    }
    .streamlit-expanderContent {
        background-color: #0a0e17 !important;
        border: 1px solid #1e2a3a !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }
    /* Info/Warning boxes */
    .stAlert {
        background-color: #1e2a3a !important;
        border-left: 4px solid #f39c12 !important;
        color: #e0e6ed !important;
    }
    .stInfo {
        background-color: #1a2a3a !important;
        border-left: 4px solid #4a7a9c !important;
    }
    /* Caption */
    .stCaption {
        color: #5a6a7a !important;
    }
    /* Radio buttons */
    .stRadio > div {
        background-color: #141e2b !important;
        padding: 0.5rem;
        border-radius: 8px;
    }
    .stRadio label {
        color: #e0e6ed !important;
    }
    /* Selectbox dropdown */
    .stSelectbox > div > div > div > div {
        background-color: #141e2b !important;
        color: #e0e6ed !important;
    }
    /* Image caption */
    .stImage > div > div > div > p {
        color: #5a6a7a !important;
    }
    /* Hide default streamlit header/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "project_registered" not in st.session_state:
    st.session_state.project_registered = False
if "project_info" not in st.session_state:
    st.session_state.project_info = {}
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
if "custom_image" not in st.session_state:
    st.session_state.custom_image = None
if "custom_description" not in st.session_state:
    st.session_state.custom_description = ""

# ============================================================
# CACHE HANDLER (Silent Auto-Save)
# ============================================================
CACHE_DIR = ".sds_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "current_session.json")

def save_cache():
    data = {
        "project_registered": st.session_state.project_registered,
        "project_info": st.session_state.project_info,
        "typology": st.session_state.typology,
        "params": st.session_state.params,
        "qa_answers": st.session_state.qa_answers,
        "locked": st.session_state.locked,
        "custom_image": st.session_state.custom_image,
        "custom_description": st.session_state.custom_description
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

# Auto-load cache on boot
cached = load_cache()
if cached:
    st.session_state.project_registered = cached.get("project_registered", False)
    st.session_state.project_info = cached.get("project_info", {})
    st.session_state.typology = cached.get("typology")
    st.session_state.params = cached.get("params", {})
    st.session_state.qa_answers = cached.get("qa_answers", {})
    st.session_state.locked = cached.get("locked", False)
    st.session_state.custom_image = cached.get("custom_image")
    st.session_state.custom_description = cached.get("custom_description", "")

# ============================================================
# TYPOLOGY CONFIGURATIONS (Built-in)
# ============================================================
TYPOLOGIES = {
    "saddle_span": {
        "name": "Saddle Span",
        "icon": "🏕️",
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
    "custom": {
        "name": "Custom Design",
        "icon": "🧩",
        "params": {
            "width": {"label": "Overall Width (m)", "min": 1.0, "max": 100.0, "step": 0.5, "default": 10.0},
            "length": {"label": "Overall Length (m)", "min": 1.0, "max": 100.0, "step": 0.5, "default": 15.0},
            "height": {"label": "Overall Height (m)", "min": 1.0, "max": 50.0, "step": 0.5, "default": 8.0}
        },
        "qa": [
            "This is a custom design. Add your description below."
        ]
    }
}

# ============================================================
# 3D GEOMETRY GENERATORS
# ============================================================

def generate_saddle_span(params):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    num_points = 40

    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()

    x = np.linspace(-span/2, span/2, num_points)
    z_beam = rise * (1 - (2 * x / span)**2)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    y2 = laa/2 * (1 - (2 * x / span)**2)

    u = np.linspace(0, 1, num_points)
    v = np.linspace(0, 1, num_points)

    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, u_val in enumerate(u):
        x_pos = -span/2 + u_val * span
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = rise * (1 - (2 * x_pos / span)**2) if abs(x_pos) <= span/2 else 0

        for j, v_val in enumerate(v):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            saddle_factor = 1 - 0.3 * (1 - (2 * v_val - 1)**2)
            z_pos = z_at_x * saddle_factor
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1', line=dict(color='#FF6B6B', width=6)))
    fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2', line=dict(color='#FF6B6B', width=6)))
    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, colorscale=[[0, '#2a3a4f'], [1, '#4a6a8a']], opacity=0.7, showscale=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[y1[num_points//2]], z=[rise], mode='markers', name='Apex 1', marker=dict(color='#FFD93D', size=10)))
    fig.add_trace(go.Scatter3d(x=[0], y=[y2[num_points//2]], z=[rise], mode='markers', name='Apex 2', marker=dict(color='#FFD93D', size=10)))
    fig.add_trace(go.Scatter3d(x=[-span/2], y=[0], z=[0], mode='markers', name='Support 1', marker=dict(color='#4ECDC4', size=10)))
    fig.add_trace(go.Scatter3d(x=[span/2], y=[0], z=[0], mode='markers', name='Support 2', marker=dict(color='#4ECDC4', size=10)))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Span (m)',
            yaxis_title='Width (m)',
            zaxis_title='Height (m)',
            xaxis=dict(color='#b0c4de'),
            yaxis=dict(color='#b0c4de'),
            zaxis=dict(color='#b0c4de'),
            bgcolor='#0a0e17'
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0,r=0,b=0,t=0)
    )
    return fig

def generate_tent(params):
    span = params.get("span_width", 10.0)
    ridge = params.get("ridge_height", 5.0)
    bays = params.get("num_bays", 4)
    bay_dist = params.get("bay_distance", 5.0)
    total_len = bays * bay_dist
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,total_len], z=[ridge,ridge], mode='lines', name='Ridge', line=dict(width=6, color='#f39c12')))
    fig.add_trace(go.Scatter3d(x=[-span/2,-span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Left', line=dict(width=4, color='#4a7a9c')))
    fig.add_trace(go.Scatter3d(x=[span/2,span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Right', line=dict(width=4, color='#4a7a9c')))
    X = np.linspace(-span/2, span/2, 20)
    Y = np.linspace(0, total_len, 20)
    X, Y = np.meshgrid(X, Y)
    Z = ridge * (1 - (X/(span/2))**2) * (1 - (Y/total_len)**2 * 0.1)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.5, colorscale=[[0, '#2a3a4f'], [1, '#6a4a2a']], showscale=False))
    fig.update_layout(
        scene=dict(
            xaxis_title='Width',
            yaxis_title='Length',
            zaxis_title='Height',
            xaxis=dict(color='#b0c4de'),
            yaxis=dict(color='#b0c4de'),
            zaxis=dict(color='#b0c4de'),
            bgcolor='#0a0e17'
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0,r=0,b=0,t=0)
    )
    return fig

def generate_tensile(params):
    mast = params.get("mast_height", 8.0)
    length = params.get("span_length", 20.0)
    width = params.get("span_width", 15.0)
    cables = params.get("cable_count", 4)
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[0,mast], mode='lines', name='Mast', line=dict(width=8, color='#f39c12')))
    X = np.linspace(-length/2, length/2, 20)
    Y = np.linspace(-width/2, width/2, 20)
    X, Y = np.meshgrid(X, Y)
    Z = mast * np.exp(-((X/(length/2))**2 + (Y/(width/2))**2) * 0.5)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.4, colorscale=[[0, '#1a3a2a'], [1, '#3a6a4a']], showscale=False))
    for i in range(cables):
        angle = i * 2*np.pi/cables
        x_end = length/2 * np.cos(angle)
        y_end = width/2 * np.sin(angle)
        fig.add_trace(go.Scatter3d(x=[0, x_end], y=[0, y_end], z=[mast, 0], mode='lines', line=dict(width=3, color='#4a7a9c')))
    fig.update_layout(
        scene=dict(
            xaxis_title='Length',
            yaxis_title='Width',
            zaxis_title='Height',
            xaxis=dict(color='#b0c4de'),
            yaxis=dict(color='#b0c4de'),
            zaxis=dict(color='#b0c4de'),
            bgcolor='#0a0e17'
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0,r=0,b=0,t=0)
    )
    return fig

def generate_portal(params):
    eave = params.get("eave_height", 6.0)
    span = params.get("span_width", 20.0)
    pitch = params.get("roof_pitch", 5.0)
    bays = params.get("num_bays", 5)
    bay_spacing = params.get("bay_spacing", 6.0)
    total_len = bays * bay_spacing
    roof_rise = span/2 * np.tan(np.radians(pitch))
    ridge = eave + roof_rise
    fig = go.Figure()
    x = [-span/2, -span/2, 0, span/2, span/2]
    z = [0, eave, ridge, eave, 0]
    fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', name='Portal Frame', line=dict(width=6, color='#4a7a9c')))
    for i in range(bays):
        y = i * bay_spacing
        fig.add_trace(go.Scatter3d(x=x, y=[y]*len(x), z=z, mode='lines', line=dict(width=3, color='#4a7a9c', opacity=0.3)))
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), np.linspace(-span/2, span/2, 20))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.3, colorscale=[[0, '#1a1a2a'], [1, '#3a3a5a']], showscale=False))
    fig.update_layout(
        scene=dict(
            xaxis_title='Width',
            yaxis_title='Length',
            zaxis_title='Height',
            xaxis=dict(color='#b0c4de'),
            yaxis=dict(color='#b0c4de'),
            zaxis=dict(color='#b0c4de'),
            bgcolor='#0a0e17'
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0,r=0,b=0,t=0)
    )
    return fig

def generate_custom_bounding_box(params):
    width = params.get("width", 10.0)
    length = params.get("length", 15.0)
    height = params.get("height", 8.0)
    
    fig = go.Figure()
    
    corners = [
        [-width/2, -length/2, 0],
        [width/2, -length/2, 0],
        [width/2, length/2, 0],
        [-width/2, length/2, 0],
        [-width/2, -length/2, height],
        [width/2, -length/2, height],
        [width/2, length/2, height],
        [-width/2, length/2, height]
    ]
    
    edges = [
        (0,1), (1,2), (2,3), (3,0),
        (4,5), (5,6), (6,7), (7,4),
        (0,4), (1,5), (2,6), (3,7)
    ]
    
    for i, j in edges:
        fig.add_trace(go.Scatter3d(
            x=[corners[i][0], corners[j][0]],
            y=[corners[i][1], corners[j][1]],
            z=[corners[i][2], corners[j][2]],
            mode='lines',
            line=dict(color='#4a7a9c', width=3),
            showlegend=False
        ))
    
    fig.add_trace(go.Scatter3d(
        x=[0], y=[-length/2 - 1], z=[height/2],
        mode='text',
        text=[f"W: {width:.1f}m"],
        textfont=dict(color='#FFD93D', size=12),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[width/2 + 1], y=[0], z=[height/2],
        mode='text',
        text=[f"L: {length:.1f}m"],
        textfont=dict(color='#4ECDC4', size=12),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[width/2 + 0.5], y=[-length/2 - 0.5], z=[height/2],
        mode='text',
        text=[f"H: {height:.1f}m"],
        textfont=dict(color='#FF6B6B', size=12),
        showlegend=False
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)',
            yaxis_title='Length (m)',
            zaxis_title='Height (m)',
            aspectmode='manual',
            aspectratio=dict(x=1.5, y=2.0, z=0.8),
            xaxis=dict(color='#b0c4de'),
            yaxis=dict(color='#b0c4de'),
            zaxis=dict(color='#b0c4de'),
            bgcolor='#0a0e17'
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

GENERATORS = {
    "saddle_span": generate_saddle_span,
    "clear_span_tent": generate_tent,
    "tensile_membrane": generate_tensile,
    "portal_frame": generate_portal,
    "custom": generate_custom_bounding_box
}

# ============================================================
# UI RENDERING
# ============================================================

# ---- PROJECT REGISTRATION SCREEN ----
if not st.session_state.project_registered:
    st.title("🏗️ SDS Design Studio")
    st.subheader("📋 New Project Registration")
    st.caption("Fill in the project details to get started.")
    
    with st.form("project_registration_form"):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("📌 Project Name *", placeholder="e.g., Marina Bay Canopy")
            client_name = st.text_input("👤 Client Name *", placeholder="e.g., Marina Bay Sands")
        with col2:
            architect = st.text_input("🏛️ Architect (optional)", placeholder="e.g., Foster + Partners")
            engineer = st.text_input("🔧 Engineer (optional)", placeholder="e.g., Arup")
        
        location = st.text_input("📍 Location", placeholder="e.g., Singapore")
        project_date = st.date_input("📅 Date", value=datetime.today())
        
        # Auto-generate project reference
        ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        project_ref = st.text_input("🔑 Project Reference", value=f"SDS-{ref}")
        
        submitted = st.form_submit_button("🚀 Start Design Studio", use_container_width=True, type="primary")
        
        if submitted:
            if not project_name or not client_name:
                st.error("⚠️ Project Name and Client Name are required.")
            else:
                st.session_state.project_info = {
                    "name": project_name,
                    "client": client_name,
                    "architect": architect,
                    "engineer": engineer,
                    "location": location,
                    "date": project_date.isoformat(),
                    "reference": project_ref
                }
                st.session_state.project_registered = True
                save_cache()
                st.rerun()
    
    st.caption("All data is cached locally. Your project will resume where you left off.")
    st.stop()

# ---- MAIN DASHBOARD (After Registration) ----
# Show project banner
info = st.session_state.project_info
st.markdown(f"""
<div style="background-color:#141e2b; padding:0.75rem 1rem; border-radius:12px; margin-bottom:1rem; border-left:4px solid #f39c12;">
    <span style="color:#b0c4de; font-size:0.8rem;">🔑 {info.get('reference', 'N/A')}</span>
    <span style="color:#f0f4fa; font-weight:600; margin-left:1rem;">{info.get('name', 'Untitled')}</span>
    <span style="color:#5a6a7a; margin-left:1rem;">👤 {info.get('client', 'N/A')}</span>
    <span style="color:#5a6a7a; margin-left:1rem;">🏛️ {info.get('architect', '—')}</span>
    <span style="color:#5a6a7a; margin-left:1rem;">🔧 {info.get('engineer', '—')}</span>
</div>
""", unsafe_allow_html=True)

# ---- TYPOLOGY CATALOG ----
if st.session_state.typology is None:
    st.subheader("Choose a structure type:")
    cols = st.columns(2)
    idx = 0
    for key, typ in TYPOLOGIES.items():
        with cols[idx % 2]:
            if st.button(f"{typ['icon']} {typ['name']}", use_container_width=True):
                st.session_state.typology = key
                st.session_state.params = {p: v["default"] for p, v in typ["params"].items()}
                st.session_state.qa_answers = {}
                st.session_state.locked = False
                save_cache()
                st.rerun()
        idx += 1
    
    # Show "New Project" button to re-register
    if st.button("🔄 New Project", use_container_width=True):
        st.session_state.project_registered = False
        st.session_state.project_info = {}
        st.session_state.typology = None
        save_cache()
        st.rerun()
    
    st.stop()

# ---- ACTIVE TYPOLOGY VIEW ----
typ_key = st.session_state.typology
typ = TYPOLOGIES[typ_key]
params = st.session_state.params

col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if st.button("⬅", help="Back to catalog"):
        st.session_state.typology = None
        st.session_state.mode = "design"
        st.session_state.locked = False
        save_cache()
        st.rerun()
with col2:
    st.subheader(f"{typ['icon']} {typ['name']}")
with col3:
    if st.session_state.mode == "design":
        if st.button("🔍 Pro View", use_container_width=True):
            st.session_state.mode = "engineer"
            save_cache()
            st.rerun()
    else:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.mode = "design"
            save_cache()
            st.rerun()

if st.session_state.locked:
    st.warning("🔒 Design is LOCKED. Edit mode is disabled.")

# ---- CUSTOM TYPOLOGY ----
if typ_key == "custom":
    st.subheader("📋 Design Brief")
    
    uploaded_file = st.file_uploader(
        "Upload sketch or photo (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        help="Upload a sketch, photo, or reference image for your custom design."
    )
    
    if uploaded_file:
        st.session_state.custom_image = uploaded_file.getvalue()
        st.image(uploaded_file, caption="Design Reference", use_column_width=True)
    
    description = st.text_area(
        "Describe your design:",
        value=st.session_state.custom_description,
        placeholder="e.g., Three curved steel beams meeting at a central ring...",
        height=100
    )
    st.session_state.custom_description = description
    
    st.subheader("📐 Bounding Box Dimensions")
    cols = st.columns(3)
    with cols[0]:
        width = st.slider("Width (m)", min_value=1.0, max_value=100.0, step=0.5, value=params.get("width", 10.0))
        params["width"] = width
    with cols[1]:
        length = st.slider("Length (m)", min_value=1.0, max_value=100.0, step=0.5, value=params.get("length", 15.0))
        params["length"] = length
    with cols[2]:
        height = st.slider("Height (m)", min_value=1.0, max_value=50.0, step=0.5, value=params.get("height", 8.0))
        params["height"] = height
    
    st.info("📝 This is a custom design. The 3D view shows a bounding box placeholder.")
    
    if st.button("🔒 LOCK DESIGN BRIEF", use_container_width=True, type="primary"):
        st.session_state.locked = True
        save_cache()
        st.rerun()

# ---- REGULAR TYPOLOGIES ----
else:
    if st.session_state.mode == "design" and not st.session_state.locked:
        st.subheader("📐 Dimensions")
        cols = st.columns(2)
        col_idx = 0
        for p_key, p_def in typ["params"].items():
            with cols[col_idx % 2]:
                val = st.slider(
                    p_def["label"],
                    min_value=float(p_def["min"]),
                    max_value=float(p_def["max"]),
                    step=float(p_def["step"]),
                    value=float(params.get(p_key, p_def["default"]))
                )
                params[p_key] = val
            col_idx += 1
        
        save_cache()
        
        st.subheader("📋 Confirm Design")
        for i, q in enumerate(typ["qa"]):
            key = f"qa_{i}"
            default = st.session_state.qa_answers.get(key, "Yes")
            if "?" in q:
                ans = st.radio(q, ["Yes", "No", "Not Sure"], index=["Yes","No","Not Sure"].index(default), key=key)
            else:
                options = ["Open", "Enclosed", "PVC", "PTFE", "Steel"]
                ans = st.selectbox(q, options, index=options.index(default) if default in options else 0, key=key)
            st.session_state.qa_answers[key] = ans
        save_cache()
        
        if st.button("🔒 LOCK & PROCEED", use_container_width=True, type="primary"):
            st.session_state.locked = True
            save_cache()
            st.rerun()

# ---- ENGINEER MODE / LOCKED ----
if st.session_state.mode == "engineer" or st.session_state.locked:
    st.subheader("🔬 3D View")
    
    if typ_key == "custom":
        fig = generate_custom_bounding_box(params)
        if st.session_state.custom_image:
            st.image(st.session_state.custom_image, caption="Design Reference", use_column_width=True)
        if st.session_state.custom_description:
            st.caption(f"📝 {st.session_state.custom_description}")
    else:
        if typ_key in GENERATORS:
            fig = GENERATORS[typ_key](params)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    with st.expander("📋 Design Summary"):
        st.write(f"**Project:** {info.get('name', 'N/A')}")
        st.write(f"**Client:** {info.get('client', 'N/A')}")
        if info.get('architect'):
            st.write(f"**Architect:** {info.get('architect')}")
        if info.get('engineer'):
            st.write(f"**Engineer:** {info.get('engineer')}")
        st.write("---")
        for i, q in enumerate(typ["qa"]):
            ans = st.session_state.qa_answers.get(f"qa_{i}", "Not answered")
            st.write(f"**{q}** → {ans}")
        
        if typ_key == "custom":
            st.write("**📝 Custom Design Brief**")
            st.write(f"Width: {params.get('width', 10.0):.1f}m")
            st.write(f"Length: {params.get('length', 15.0):.1f}m")
            st.write(f"Height: {params.get('height', 8.0):.1f}m")
            if st.session_state.custom_description:
                st.write(f"Description: {st.session_state.custom_description}")
    
    if st.session_state.locked:
        if st.button("🔓 Unlock to Edit", use_container_width=True):
            st.session_state.locked = False
            st.session_state.mode = "design"
            save_cache()
            st.rerun()

st.caption("SDS Platform v1.0 | Dark Mode | Project Dashboard | Cache auto-saves all changes.")
save_cache()
