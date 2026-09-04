import streamlit as st
import json
import os
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import random
import string
import base64
import glob
import pandas as pd
from PIL import Image

# ============================================================
# PAGE CONFIG
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
    .stApp {
        background-color: #0a0e17 !important;
        color: #f0f4fa !important;
    }
    .stApp > header {
        background-color: transparent !important;
        display: none !important;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .stButton > button {
        background-color: #1e2a3a !important;
        color: #ffffff !important;
        border: 1px solid #2a3a4f !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        font-weight: 500 !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background-color: #2a3a4f !important;
        border-color: #4a7a9c !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #f39c12 !important;
        color: #0a0e17 !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stNumberInput > div > div > input {
        background-color: #141e2b !important;
        color: #ffffff !important;
        border: 1px solid #2a3a4f !important;
        border-radius: 8px !important;
    }
    .stSelectbox > div > div > div {
        background-color: #141e2b !important;
        color: #ffffff !important;
        border: 1px solid #2a3a4f !important;
        border-radius: 8px !important;
    }
    .stTextArea textarea {
        color: #ffffff !important;
        background-color: #141e2b !important;
    }
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    
    .dashboard-card {
        background-color: #141e2b;
        border-radius: 12px;
        padding: 1.5rem 1rem;
        border: 1px solid #1e2a3a;
        text-align: center;
    }
    .dashboard-card .icon {
        font-size: 2.5rem;
    }
    .dashboard-card .value {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 600;
    }
    .dashboard-card .label {
        color: #8a9aaa;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    .sds-card {
        background-color: #141e2b;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        border: 1px solid #1e2a3a;
        margin-bottom: 0.8rem;
    }
    .sds-card .title {
        color: #ffffff;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.4rem;
    }
    .sds-card .content {
        color: #b0c4de;
        font-size: 0.9rem;
    }
    .badge-confirmed { background-color: #2d6a4f; color: #a7f3d0; padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; }
    .badge-provided { background-color: #1e3a5f; color: #93c5fd; padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; }
    .badge-inferred { background-color: #7d5a2d; color: #fcd34d; padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; }
    .badge-unknown { background-color: #6b2d2d; color: #fca5a5; padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; }
    .badge-autogen { background-color: #3b3b6b; color: #c4b5fd; padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if "project_registered" not in st.session_state:
    st.session_state.project_registered = False
if "project_info" not in st.session_state:
    st.session_state.project_info = {}
if "typology" not in st.session_state:
    st.session_state.typology = None
if "params" not in st.session_state:
    st.session_state.params = {}
if "qa_answers" not in st.session_state:
    st.session_state.qa_answers = {}
if "locked" not in st.session_state:
    st.session_state.locked = False
if "show_project_browser" not in st.session_state:
    st.session_state.show_project_browser = False
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False
if "comments" not in st.session_state:
    st.session_state.comments = ""
if "engineering_annotations" not in st.session_state:
    st.session_state.engineering_annotations = {
        "show_wind": True,
        "show_tie_down": True,
        "show_load_path": True,
        "show_bracing": True
    }
if "materials" not in st.session_state:
    st.session_state.materials = {
        "steel_grade": "S355",
        "section_type": "Circular Hollow Section (CHS)",
        "section_size": "CHS 150x6",
        "fabric_type": "PVC-coated Polyester",
        "fabric_thickness": 0.8,
        "prestress": 3.0,
        "wire_rope_type": "Galvanized Steel (6x19)",
        "wire_rope_diameter": 10,
        "num_bays": 2,
        "tie_down_vertical_angle": 45,
        "wind_speed": 40,
        "safety_factor": 1.5
    }

# ============================================================
# CACHE HANDLER
# ============================================================
CACHE_DIR = ".sds_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "current_session.json")
PROJECTS_LIST_FILE = os.path.join(CACHE_DIR, "projects_index.json")

def save_cache():
    data = {
        "project_registered": st.session_state.project_registered,
        "project_info": st.session_state.project_info,
        "typology": st.session_state.typology,
        "params": st.session_state.params,
        "qa_answers": st.session_state.qa_answers,
        "locked": st.session_state.locked,
        "comments": st.session_state.comments,
        "materials": st.session_state.materials
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
    update_projects_index()

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

def update_projects_index():
    projects_index = []
    if os.path.exists(CACHE_DIR):
        for f in glob.glob(os.path.join(CACHE_DIR, "project_*.json")):
            try:
                with open(f, "r") as file:
                    data = json.load(file)
                    info = data.get("project_info", {})
                    projects_index.append({
                        "file": os.path.basename(f),
                        "name": info.get("name", "Untitled"),
                        "client": info.get("client", "Unknown"),
                        "reference": info.get("reference", "N/A"),
                        "typology": data.get("typology", "Unknown"),
                        "date": info.get("date", datetime.now().isoformat()),
                        "locked": data.get("locked", False)
                    })
            except:
                pass
    with open(PROJECTS_LIST_FILE, "w") as f:
        json.dump(projects_index, f, indent=2)

def load_project_from_file(filename):
    filepath = os.path.join(CACHE_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            st.session_state.project_registered = data.get("project_registered", False)
            st.session_state.project_info = data.get("project_info", {})
            st.session_state.typology = data.get("typology")
            st.session_state.params = data.get("params", {})
            st.session_state.qa_answers = data.get("qa_answers", {})
            st.session_state.locked = data.get("locked", False)
            st.session_state.comments = data.get("comments", "")
            st.session_state.materials = data.get("materials", {})
            return True
    return False

def delete_project_file(filename):
    filepath = os.path.join(CACHE_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        update_projects_index()
        return True
    return False

def go_to_dashboard():
    st.session_state.project_registered = False
    st.session_state.project_info = {}
    st.session_state.typology = None
    st.session_state.params = {}
    st.session_state.qa_answers = {}
    st.session_state.locked = False
    st.session_state.comments = ""
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    save_cache()

def save_project_as_new():
    if not st.session_state.project_info.get("name"):
        st.error("⚠️ Project name is required to save.")
        return
    ref = st.session_state.project_info.get("reference")
    if not ref:
        ref = f"SDS-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    data = {
        "project_registered": st.session_state.project_registered,
        "project_info": st.session_state.project_info,
        "typology": st.session_state.typology,
        "params": st.session_state.params,
        "qa_answers": st.session_state.qa_answers,
        "locked": st.session_state.locked,
        "comments": st.session_state.comments,
        "materials": st.session_state.materials
    }
    filename = f"project_{ref}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(CACHE_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f)
    st.success(f"✅ Project saved!")
    update_projects_index()
    save_cache()

def get_projects_list():
    if os.path.exists(PROJECTS_LIST_FILE):
        with open(PROJECTS_LIST_FILE, "r") as f:
            return json.load(f)
    return []

cached = load_cache()
if cached:
    st.session_state.project_registered = cached.get("project_registered", False)
    st.session_state.project_info = cached.get("project_info", {})
    st.session_state.typology = cached.get("typology")
    st.session_state.params = cached.get("params", {})
    st.session_state.qa_answers = cached.get("qa_answers", {})
    st.session_state.locked = cached.get("locked", False)
    st.session_state.comments = cached.get("comments", "")
    st.session_state.materials = cached.get("materials", {})

# ============================================================
# TYPOLOGIES
# ============================================================
TYPOLOGIES = {
    "saddle_span": {
        "name": "Saddle Span",
        "icon": "🏕️",
        "params": {
            "A": {"label": "Rise (m)", "min": 2.0, "max": 20.0, "step": 0.5, "default": 6.0},
            "B": {"label": "Span (m)", "min": 4.0, "max": 40.0, "step": 0.5, "default": 10.0},
            "LAA": {"label": "Apex Distance (m)", "min": 4.0, "max": 50.0, "step": 0.5, "default": 15.0}
        },
        "qa": [
            "Are these the two primary structural beams?",
            "Are both beams supported at their lower ends?",
            "Is the membrane attached continuously along the curved beams?",
            "Is dimension A (rise) the vertical height from support level to apex?",
            "Is dimension B the horizontal plan width between supports?",
            "Is LAA the distance between apex of Beam 1 and apex of Beam 2?"
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
            "Ridge height from ground?"
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
            "Prestress applied?"
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
            "Wind bracing in walls?"
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
# ENGINEERING FUNCTIONS
# ============================================================

def generate_bracing_positions(span, num_bays):
    if num_bays == 1:
        return [0.0]
    elif num_bays == 2:
        return [-span/3, span/3]
    elif num_bays == 3:
        return [-span/4, 0.0, span/4]
    else:
        return np.linspace(-span/2 * 0.8, span/2 * 0.8, num_bays).tolist()

def generate_tie_down_anchors(span, laa, height, x_positions, vertical_angle_deg):
    vertical_rad = np.radians(vertical_angle_deg)
    distance = height * np.tan(vertical_rad)
    anchors = []
    beam_ys = [-laa/2, laa/2]
    for beam_y in beam_ys:
        for beam_x in x_positions:
            anchors.append({
                "beam_x": beam_x,
                "beam_y": beam_y,
                "anchor_x": beam_x + distance,
                "anchor_y": beam_y,
                "anchor_z": 0
            })
    return anchors

def calculate_wind_load(wind_speed, area):
    rho = 1.225
    q = 0.5 * rho * wind_speed**2 / 1000
    return q * 1.2 * area

# ============================================================
# 3D GENERATOR
# ============================================================

def generate_saddle_span(params, materials=None, annotations=None):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    num_points = 50

    x = np.linspace(-span/2, span/2, num_points)
    z_beam = rise * (1 - (2 * x / span)**2)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    y2 = laa/2 * (1 - (2 * x / span)**2)

    fig = go.Figure()

    # Beams
    fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1', line=dict(color='#FF6B6B', width=6)))
    fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2', line=dict(color='#FF6B6B', width=6)))
    
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
            saddle_factor = 1 - 0.3 * (1 - (2 * v_val - 1)**2)
            z_pos = z_at_x * saddle_factor
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos
    
    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, 
                             colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
                             opacity=0.7, showscale=False))

    # Apex and supports
    fig.add_trace(go.Scatter3d(x=[0], y=[y1[num_points//2]], z=[rise], 
                               mode='markers', name='Apex', marker=dict(color='#FFD93D', size=8, symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[-span/2], y=[0], z=[0], 
                               mode='markers', name='Support', marker=dict(color='#4ECDC4', size=6, symbol='square')))

    # Bracing
    if materials is not None:
        num_bays = materials.get("num_bays", 2)
        bracing_x = generate_bracing_positions(span, num_bays)
        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            y1_pos = y1[idx]
            y2_pos = y2[idx]
            z_pos = z_beam[idx]
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[y1_pos, y2_pos], z=[z_pos, z_pos],
                mode='lines', name='Bracing',
                line=dict(color='#FF6B6B', width=2, dash='dash'),
                showlegend=False
            ))

    # Tie-downs
    if materials is not None:
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        num_bays = materials.get("num_bays", 2)
        bracing_x = generate_bracing_positions(span, num_bays)
        anchors = generate_tie_down_anchors(span, laa, rise, bracing_x, vertical_angle)
        for a in anchors:
            idx = np.argmin(np.abs(x - a["beam_x"]))
            beam_z = z_beam[idx]
            fig.add_trace(go.Scatter3d(
                x=[a["beam_x"], a["anchor_x"]],
                y=[a["beam_y"], a["anchor_y"]],
                z=[beam_z, a["anchor_z"]],
                mode='lines', name='Tie-Down',
                line=dict(color='#FFD93D', width=2),
                showlegend=False
            ))

    fig.update_layout(
        scene=dict(
            xaxis_title='Span (m)',
            yaxis_title='Width (m)',
            zaxis_title='Height (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2))
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(
            font=dict(color='#ffffff', size=8),
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(10,14,23,0.7)'
        )
    )
    return fig

def generate_tent(params):
    span = params.get("span_width", 10.0)
    ridge = params.get("ridge_height", 5.0)
    bays = params.get("num_bays", 4)
    bay_dist = params.get("bay_distance", 5.0)
    total_len = bays * bay_dist
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,total_len], z=[ridge,ridge], mode='lines', name='Ridge', line=dict(width=8, color='#f39c12')))
    fig.add_trace(go.Scatter3d(x=[-span/2,-span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Left', line=dict(width=5, color='#4a7a9c')))
    fig.add_trace(go.Scatter3d(x=[span/2,span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Right', line=dict(width=5, color='#4a7a9c')))
    X = np.linspace(-span/2, span/2, 30)
    Y = np.linspace(0, total_len, 30)
    X, Y = np.meshgrid(X, Y)
    Z = ridge * (1 - (X/(span/2))**2) * (1 - (Y/total_len)**2 * 0.1)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.5, colorscale='Reds', showscale=False))
    fig.update_layout(
        scene=dict(xaxis_title='Width', yaxis_title='Length', zaxis_title='Height',
                   xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0)
    )
    return fig

def generate_tensile(params):
    mast = params.get("mast_height", 8.0)
    length = params.get("span_length", 20.0)
    width = params.get("span_width", 15.0)
    cables = params.get("cable_count", 4)
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[0,mast], mode='lines', name='Mast', line=dict(width=10, color='#f39c12')))
    X = np.linspace(-length/2, length/2, 30)
    Y = np.linspace(-width/2, width/2, 30)
    X, Y = np.meshgrid(X, Y)
    Z = mast * np.exp(-((X/(length/2))**2 + (Y/(width/2))**2) * 0.5)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.4, colorscale='Greens', showscale=False))
    for i in range(cables):
        angle = i * 2*np.pi/cables
        x_end = length/2 * np.cos(angle)
        y_end = width/2 * np.sin(angle)
        fig.add_trace(go.Scatter3d(x=[0, x_end], y=[0, y_end], z=[mast, 0], mode='lines', line=dict(width=4, color='#4a7a9c')))
    fig.update_layout(
        scene=dict(xaxis_title='Length', yaxis_title='Width', zaxis_title='Height',
                   xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0)
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
    fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', name='Portal Frame', line=dict(width=8, color='#4a7a9c')))
    for i in range(bays):
        y = i * bay_spacing
        fig.add_trace(go.Scatter3d(x=x, y=[y]*len(x), z=z, mode='lines', line=dict(width=4, color='#4a7a9c', opacity=0.3)))
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), np.linspace(-span/2, span/2, 30))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.3, colorscale='Greys', showscale=False))
    fig.update_layout(
        scene=dict(xaxis_title='Width', yaxis_title='Length', zaxis_title='Height',
                   xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0)
    )
    return fig

def generate_custom(params):
    width = params.get("width", 10.0)
    length = params.get("length", 15.0)
    height = params.get("height", 8.0)
    fig = go.Figure()
    corners = [
        [-width/2, -length/2, 0], [width/2, -length/2, 0],
        [width/2, length/2, 0], [-width/2, length/2, 0],
        [-width/2, -length/2, height], [width/2, -length/2, height],
        [width/2, length/2, height], [-width/2, length/2, height]
    ]
    edges = [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]
    for i, j in edges:
        fig.add_trace(go.Scatter3d(
            x=[corners[i][0], corners[j][0]],
            y=[corners[i][1], corners[j][1]],
            z=[corners[i][2], corners[j][2]],
            mode='lines', line=dict(color='#4a7a9c', width=3), showlegend=False
        ))
    fig.update_layout(
        scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)',
                   xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
                   bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0)
    )
    return fig

GENERATORS = {
    "saddle_span": generate_saddle_span,
    "clear_span_tent": generate_tent,
    "tensile_membrane": generate_tensile,
    "portal_frame": generate_portal,
    "custom": generate_custom
}

# ============================================================
# RENDER UNIFIED WORKSPACE
# ============================================================

def render_unified_workspace():
    params = st.session_state.params
    materials = st.session_state.materials
    typ_key = st.session_state.typology
    typ = TYPOLOGIES[typ_key]
    info = st.session_state.project_info
    
    st.markdown("## 🧠 SDS Design Studio")
    st.caption("Design, confirm, and visualize your structure in real-time.")
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        # Project Info
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📊 Project Summary</div>', unsafe_allow_html=True)
        st.write(f"**Project:** {info.get('name', 'Untitled')}")
        st.write(f"**Client:** {info.get('client', 'Unknown')}")
        st.write(f"**Reference:** {info.get('reference', 'N/A')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Geometry
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📐 Geometry</div>', unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            new_a = st.number_input("Rise (A) m", min_value=2.0, max_value=20.0, step=0.5, value=float(params.get("A", 6.0)), format="%.1f")
            params["A"] = new_a
        with col_b:
            new_b = st.number_input("Span (B) m", min_value=4.0, max_value=40.0, step=0.5, value=float(params.get("B", 10.0)), format="%.1f")
            params["B"] = new_b
        with col_c:
            new_laa = st.number_input("LAA (m)", min_value=4.0, max_value=50.0, step=0.5, value=float(params.get("LAA", 15.0)), format="%.1f")
            params["LAA"] = new_laa
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Materials
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🏗️ Materials</div>', unsafe_allow_html=True)
        materials["steel_grade"] = st.selectbox("Steel Grade", ["S275", "S355", "S460"], index=1)
        materials["fabric_type"] = st.selectbox("Fabric Type", ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"], index=0)
        materials["fabric_thickness"] = st.selectbox("Fabric Thickness (mm)", [0.5, 0.8, 1.0, 1.2], index=1)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Bracing
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔗 Bracing</div>', unsafe_allow_html=True)
        materials["num_bays"] = st.selectbox("Bracing Bays", [1, 2, 3], index=1)
        materials["tie_down_vertical_angle"] = st.slider("Tie-Down Angle (°)", min_value=20, max_value=70, step=5, value=45)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.subheader("🔬 3D Model")
        
        # Annotation toggles
        col_anno1, col_anno2, col_anno3, col_anno4 = st.columns(4)
        with col_anno1:
            st.session_state.engineering_annotations["show_wind"] = st.checkbox("💨 Wind", value=True)
        with col_anno2:
            st.session_state.engineering_annotations["show_tie_down"] = st.checkbox("🔗 Tie", value=True)
        with col_anno3:
            st.session_state.engineering_annotations["show_bracing"] = st.checkbox("📐 Brace", value=True)
        with col_anno4:
            st.session_state.engineering_annotations["show_load_path"] = st.checkbox("📊 Load", value=True)
        
        # Generate 3D
        if typ_key == "custom":
            fig = generate_custom(params)
        else:
            fig = GENERATORS[typ_key](params)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        
        # Actions
        st.divider()
        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        with col_act1:
            if st.button("🔒 Lock", use_container_width=True):
                st.session_state.locked = True
                save_cache()
                st.rerun()
        with col_act2:
            if st.button("💾 Save", use_container_width=True, type="primary"):
                save_project_as_new()
        with col_act3:
            if st.button("📋 New", use_container_width=True):
                go_to_dashboard()
                st.rerun()
        with col_act4:
            if st.button("🏠 Home", use_container_width=True):
                go_to_dashboard()
                st.rerun()
    
    st.divider()
    
    # Q&A
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">❓ Design Confirmation</div>', unsafe_allow_html=True)
    for i, q in enumerate(typ["qa"]):
        key = f"qa_{i}"
        default = st.session_state.qa_answers.get(key, "Yes")
        ans = st.radio(q, ["Yes", "No", "Not Sure"], index=["Yes", "No", "Not Sure"].index(default), key=f"q_{i}")
        st.session_state.qa_answers[key] = ans
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Comments
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">💬 Comments</div>', unsafe_allow_html=True)
    comments = st.text_area("", value=st.session_state.comments, height=80)
    st.session_state.comments = comments
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# DASHBOARD
# ============================================================

def render_dashboard():
    st.title("🏗️ SDS Design Studio")
    st.caption("Parametric design for tensile structures, membrane roofs, and steel frames.")
    
    projects = get_projects_list()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="icon">📂</div>
            <div class="value">{len(projects)}</div>
            <div class="label">Saved Projects</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="icon">🏕️</div>
            <div class="value">{len(TYPOLOGIES)}</div>
            <div class="label">Structure Types</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        locked_count = sum(1 for p in projects if p.get("locked", False))
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="icon">🔒</div>
            <div class="value">{locked_count}</div>
            <div class="label">Locked Designs</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New Design", use_container_width=True, type="primary"):
            st.session_state.show_registration = True
            st.rerun()
    with col2:
        if projects:
            if st.button("📂 Open Project", use_container_width=True):
                st.session_state.show_project_browser = True
                st.rerun()
    
    if projects:
        st.subheader("📋 Recent Projects")
        for proj in projects[:5]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{proj.get('name', 'Untitled')}** — {proj.get('client', 'Unknown')}")
            with col2:
                if st.button("Open", key=f"dash_load_{proj.get('file')}"):
                    if load_project_from_file(proj.get('file')):
                        st.rerun()
            st.divider()

# ============================================================
# MAIN UI
# ============================================================

# Top Bar
col1, col2, col3, col4, col5 = st.columns([1, 3, 1, 1, 1])
with col1:
    if st.button("🏗️", help="Dashboard"):
        go_to_dashboard()
        st.rerun()
with col2:
    if st.session_state.project_registered:
        st.caption(f"📌 {st.session_state.project_info.get('name', 'Project')}")
    else:
        st.caption("📌 No Project")
with col3:
    if st.session_state.typology:
        typ = TYPOLOGIES.get(st.session_state.typology, {})
        st.caption(f"{typ.get('icon', '')} {typ.get('name', '')}")
with col4:
    if st.session_state.locked:
        st.caption("🔒 Locked")
with col5:
    if st.session_state.locked:
        if st.button("🔓 Unlock", use_container_width=True):
            st.session_state.locked = False
            save_cache()
            st.rerun()

# Project Browser
if st.session_state.show_project_browser:
    st.subheader("📂 Saved Projects")
    if st.button("⬅ Back"):
        st.session_state.show_project_browser = False
        st.rerun()
    projects = get_projects_list()
    if not projects:
        st.info("No saved projects found.")
    else:
        for proj in projects:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{proj.get('name', 'Untitled')}** — {proj.get('client', 'Unknown')}")
            with col2:
                if st.button("Load", key=f"load_{proj.get('file')}"):
                    if load_project_from_file(proj.get('file')):
                        st.session_state.show_project_browser = False
                        st.rerun()
            with col3:
                if st.button("Delete", key=f"del_{proj.get('file')}"):
                    delete_project_file(proj.get('file'))
                    st.rerun()
            st.divider()
    st.stop()

# Dashboard
if not st.session_state.project_registered and not st.session_state.show_registration:
    render_dashboard()
    st.stop()

# Registration
if st.session_state.show_registration:
    st.subheader("📋 New Project")
    if st.button("⬅ Back"):
        st.session_state.show_registration = False
        st.rerun()
    with st.form("register"):
        name = st.text_input("Project Name *")
        client = st.text_input("Client Name *")
        ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        submitted = st.form_submit_button("Start Design")
        if submitted and name and client:
            st.session_state.project_info = {
                "name": name,
                "client": client,
                "reference": f"SDS-{ref}",
                "date": datetime.now().isoformat()
            }
            st.session_state.project_registered = True
            st.session_state.show_registration = False
            save_cache()
            st.rerun()
    st.stop()

# Typology Selection
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
                save_cache()
                st.rerun()
        idx += 1
    st.stop()

# Main Workspace
render_unified_workspace()

# Footer
st.divider()
st.caption("SDS Design Studio | Auto-saved locally")

save_cache()
