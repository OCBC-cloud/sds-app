import streamlit as st
import json
import os
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import random
import string
import base64
import shutil
import glob

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SDS Design Studio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CUSTOM DARK MODE CSS — FIX COMMENT TEXT COLOR
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
    .stApp > header > div {
        display: none !important;
    }
    .stApp > div > div {
        background-color: #0a0e17 !important;
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
    .stSubheader {
        color: #e0e8f0 !important;
    }
    label, .stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
        color: #ffffff !important;
        font-weight: 400 !important;
        font-size: 1rem !important;
    }
    .stCaption, .stMarkdown, .stInfo, .stWarning {
        color: #e0e8f0 !important;
    }
    .stRadio label {
        color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        text-shadow: 0 0 4px rgba(0,0,0,0.8) !important;
    }
    .stRadio label span {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    .stRadio > div {
        background-color: #141e2b !important;
        padding: 0.75rem !important;
        border-radius: 8px !important;
        border: 1px solid #2a3a4f !important;
    }
    .stButton > button {
        background-color: #1e2a3a !important;
        color: #ffffff !important;
        border: 1px solid #2a3a4f !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background-color: #2a3a4f !important;
        border-color: #4a7a9c !important;
        color: white !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #f39c12 !important;
        color: #0a0e17 !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #f1c40f !important;
        color: #0a0e17 !important;
    }
    .stNumberInput > div > div > input {
        background-color: #141e2b !important;
        color: #ffffff !important;
        border: 1px solid #2a3a4f !important;
        border-radius: 8px !important;
        font-size: 1.1rem !important;
        padding: 0.5rem !important;
    }
    .stNumberInput > div > div > input:focus {
        border-color: #f39c12 !important;
        box-shadow: 0 0 0 2px rgba(243, 156, 18, 0.2) !important;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background-color: #141e2b !important;
        color: #ffffff !important;
        border: 1px solid #2a3a4f !important;
        border-radius: 8px !important;
    }
    /* FORCE TEXT AREA TEXT COLOR TO WHITE */
    .stTextArea textarea {
        color: #ffffff !important;
        background-color: #141e2b !important;
    }
    .streamlit-expanderHeader {
        background-color: #141e2b !important;
        border-radius: 8px !important;
        border: 1px solid #1e2a3a !important;
        color: #ffffff !important;
    }
    .streamlit-expanderContent {
        background-color: #0f1822 !important;
        border: 1px solid #1e2a3a !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        color: #f0f4fa !important;
    }
    .streamlit-expanderContent p, 
    .streamlit-expanderContent span, 
    .streamlit-expanderContent label {
        color: #f0f4fa !important;
    }
    .stAlert {
        background-color: #1e2a3a !important;
        border-left: 4px solid #f39c12 !important;
        color: #f0f4fa !important;
    }
    .stInfo {
        background-color: #1a2a3a !important;
        border-left: 4px solid #4a7a9c !important;
        color: #f0f4fa !important;
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
        transition: all 0.2s;
    }
    .dashboard-card:hover {
        border-color: #4a7a9c;
        background-color: #1a2a3a;
    }
    .dashboard-card .icon {
        font-size: 2.5rem;
    }
    .dashboard-card .label {
        color: #8a9aaa;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    .dashboard-card .value {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 600;
    }
    /* Top bar buttons – ensure labels are visible */
    .stButton button {
        font-size: 0.8rem !important;
        padding: 0.4rem 0.6rem !important;
        white-space: nowrap !important;
    }
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
if "engineering_annotations" not in st.session_state:
    st.session_state.engineering_annotations = {
        "show_wind": True,
        "show_tie_down": True,
        "show_load_path": True
    }
if "design_phase" not in st.session_state:
    st.session_state.design_phase = "input"
if "comments" not in st.session_state:
    st.session_state.comments = ""
if "show_project_browser" not in st.session_state:
    st.session_state.show_project_browser = False
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False

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
        "custom_image": st.session_state.custom_image,
        "custom_description": st.session_state.custom_description,
        "engineering_annotations": st.session_state.engineering_annotations,
        "design_phase": st.session_state.design_phase,
        "comments": st.session_state.comments
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
            st.session_state.custom_image = data.get("custom_image")
            st.session_state.custom_description = data.get("custom_description", "")
            st.session_state.engineering_annotations = data.get("engineering_annotations", {
                "show_wind": True,
                "show_tie_down": True,
                "show_load_path": True
            })
            st.session_state.design_phase = data.get("design_phase", "input")
            st.session_state.comments = data.get("comments", "")
            st.session_state.mode = "design"
            st.session_state.show_registration = False
            save_cache()
            return True
    return False

def clear_cache():
    """Reset only the current session, keep saved projects intact"""
    # Delete only the current session file, not the whole cache directory
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    # Reset session state
    st.session_state.project_registered = False
    st.session_state.project_info = {}
    st.session_state.typology = None
    st.session_state.params = {}
    st.session_state.mode = "design"
    st.session_state.qa_answers = {}
    st.session_state.locked = False
    st.session_state.custom_image = None
    st.session_state.custom_description = ""
    st.session_state.engineering_annotations = {
        "show_wind": True,
        "show_tie_down": True,
        "show_load_path": True
    }
    st.session_state.design_phase = "input"
    st.session_state.comments = ""
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    # Update index (removes any orphan references, but keeps project files)
    update_projects_index()

def save_project_as_new():
    if not st.session_state.project_info.get("name"):
        st.error("⚠️ Project name is required to save.")
        return
    
    ref = st.session_state.project_info.get("reference", f"SDS-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}")
    filename = f"project_{ref}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    data = {
        "project_registered": st.session_state.project_registered,
        "project_info": st.session_state.project_info,
        "typology": st.session_state.typology,
        "params": st.session_state.params,
        "qa_answers": st.session_state.qa_answers,
        "locked": st.session_state.locked,
        "custom_image": st.session_state.custom_image,
        "custom_description": st.session_state.custom_description,
        "engineering_annotations": st.session_state.engineering_annotations,
        "design_phase": st.session_state.design_phase,
        "comments": st.session_state.comments
    }
    with open(os.path.join(CACHE_DIR, filename), "w") as f:
        json.dump(data, f)
    
    update_projects_index()
    st.success(f"✅ Project saved as: {filename}")

def get_projects_list():
    if os.path.exists(PROJECTS_LIST_FILE):
        with open(PROJECTS_LIST_FILE, "r") as f:
            return json.load(f)
    return []

# Load cache on boot
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
    st.session_state.engineering_annotations = cached.get("engineering_annotations", {
        "show_wind": True,
        "show_tie_down": True,
        "show_load_path": True
    })
    st.session_state.design_phase = cached.get("design_phase", "input")
    st.session_state.comments = cached.get("comments", "")

# ============================================================
# TYPOLOGIES
# ============================================================
TYPOLOGIES = {
    "saddle_span": {
        "name": "Saddle Span",
        "icon": "🏕️",
        "params": {
            "A": {"label": "Rise (m)", "min": 2.0, "max": 20.0, "step": 0.5, "default": 13.0},
            "B": {"label": "Span (m)", "min": 4.0, "max": 40.0, "step": 0.5, "default": 5.0},
            "LAA": {"label": "Apex Distance (m)", "min": 4.0, "max": 50.0, "step": 0.5, "default": 10.0}
        },
        "qa": [
            "Are these the two primary structural beams?",
            "Are both beams supported at their lower ends?",
            "Is the membrane attached continuously along the curved beams?",
            "Is the circled point (P_A) the apex/high point of the structure?",
            "Is dimension A (rise) the vertical height from support level to apex as shown?",
            "Is dimension B the horizontal plan width between supports as shown?",
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
# 3D GENERATORS (unchanged)
# ============================================================

def generate_saddle_span(params, annotations=None):
    span = params.get("B", 5.0)
    rise = params.get("A", 13.0)
    laa = params.get("LAA", 10.0)
    num_points = 50

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

    fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1', line=dict(color='#FF6B6B', width=8)))
    fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2', line=dict(color='#FF6B6B', width=8)))

    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, 
                             colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
                             opacity=0.8, showscale=False))

    fig.add_trace(go.Scatter3d(x=[0], y=[y1[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 1', marker=dict(color='#FFD93D', size=12, symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[0], y=[y2[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 2', marker=dict(color='#FFD93D', size=12, symbol='diamond')))

    fig.add_trace(go.Scatter3d(x=[-span/2], y=[0], z=[0], 
                               mode='markers', name='Support 1', marker=dict(color='#4ECDC4', size=10, symbol='square')))
    fig.add_trace(go.Scatter3d(x=[span/2], y=[0], z=[0], 
                               mode='markers', name='Support 2', marker=dict(color='#4ECDC4', size=10, symbol='square')))

    if annotations:
        if annotations.get("show_wind", True):
            fig.add_trace(go.Scatter3d(
                x=[-span/4, -span/4], y=[-laa/4, -laa/4], z=[rise*0.8, rise*1.2],
                mode='lines',
                name='Wind Load',
                line=dict(color='#FF6B6B', width=4, dash='dash')
            ))
            fig.add_trace(go.Scatter3d(
                x=[span/4, span/4], y=[laa/4, laa/4], z=[rise*0.8, rise*1.2],
                mode='lines',
                name='Wind Load',
                line=dict(color='#FF6B6B', width=4, dash='dash')
            ))

        if annotations.get("show_tie_down", True):
            fig.add_trace(go.Scatter3d(
                x=[-span/2, -span/2, span/2, span/2],
                y=[-1, 1, -1, 1],
                z=[-0.5, -0.5, -0.5, -0.5],
                mode='markers',
                name='Tie-Down Anchors',
                marker=dict(color='#4ECDC4', size=14, symbol='x')
            ))

        if annotations.get("show_load_path", True):
            fig.add_trace(go.Scatter3d(
                x=[0, 0], y=[0, 0], z=[rise, rise-2],
                mode='lines',
                name='Load Path',
                line=dict(color='#FFD93D', width=5)
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
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(
            font=dict(color='#ffffff'),
            bgcolor='rgba(10,14,23,0.8)',
            bordercolor='#2a3a4f',
            borderwidth=1
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
        scene=dict(
            xaxis_title='Width',
            yaxis_title='Length',
            zaxis_title='Height',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
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
        scene=dict(
            xaxis_title='Length',
            yaxis_title='Width',
            zaxis_title='Height',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
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
    fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', name='Portal Frame', line=dict(width=8, color='#4a7a9c')))
    for i in range(bays):
        y = i * bay_spacing
        fig.add_trace(go.Scatter3d(x=x, y=[y]*len(x), z=z, mode='lines', line=dict(width=4, color='#4a7a9c', opacity=0.3)))
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), np.linspace(-span/2, span/2, 30))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.3, colorscale='Greys', showscale=False))
    fig.update_layout(
        scene=dict(
            xaxis_title='Width',
            yaxis_title='Length',
            zaxis_title='Height',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
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
        textfont=dict(color='#FFD93D', size=14),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[width/2 + 1], y=[0], z=[height/2],
        mode='text',
        text=[f"L: {length:.1f}m"],
        textfont=dict(color='#4ECDC4', size=14),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[width/2 + 0.5], y=[-length/2 - 0.5], z=[height/2],
        mode='text',
        text=[f"H: {height:.1f}m"],
        textfont=dict(color='#FF6B6B', size=14),
        showlegend=False
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)',
            yaxis_title='Length (m)',
            zaxis_title='Height (m)',
            aspectmode='manual',
            aspectratio=dict(x=1.5, y=2.0, z=0.8),
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
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
# EXPORT FUNCTIONS
# ============================================================

def get_image_download_link(fig, filename="design_3d.png"):
    try:
        img_bytes = fig.to_image(format="png", scale=2)
        b64 = base64.b64encode(img_bytes).decode()
        href = f'<a href="data:image/png;base64,{b64}" download="{filename}">📥 Download 3D Image (PNG)</a>'
        return href
    except Exception as e:
        return f"⚠️ Image export failed: {str(e)}. Please use the screenshot feature on your device."

def get_json_download_link(data, filename="project_data.json"):
    json_str = json.dumps(data, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">📄 Download Design Data (JSON)</a>'
    return href

# ============================================================
# NAVIGATION: TOP BAR — CLEAR LABELS
# ============================================================
def render_top_bar():
    cols = st.columns([1, 2, 0.8, 1, 1, 1.2, 1.2])
    
    with cols[0]:
        st.markdown("🏗️ **SDS**")
    
    with cols[1]:
        if st.session_state.project_registered and st.session_state.project_info:
            st.caption(f"📌 {st.session_state.project_info.get('name', 'Project')[:25]}")
        else:
            st.caption("📌 No Project")
    
    with cols[2]:
        if st.session_state.typology:
            typ = TYPOLOGIES.get(st.session_state.typology, {})
            st.caption(f"{typ.get('icon', '')} {typ.get('name', '')[:12]}")
        else:
            st.caption("")
    
    with cols[3]:
        if st.session_state.project_registered:
            if st.button("📂 Projects", use_container_width=True, help="View all saved projects"):
                st.session_state.show_project_browser = not st.session_state.show_project_browser
                st.rerun()
    
    with cols[4]:
        if st.session_state.project_registered and st.session_state.typology:
            if st.button("💾 Save", use_container_width=True, help="Save current project"):
                save_project_as_new()
                st.rerun()
    
    with cols[5]:
        if st.session_state.project_registered:
            if st.button("📋 New Project", use_container_width=True, help="Start a new project (current work will be cleared)"):
                clear_cache()
                st.rerun()
    
    with cols[6]:
        if st.session_state.project_registered and st.session_state.typology:
            if st.session_state.mode == "design":
                if st.button("🔍 Pro View", use_container_width=True, type="primary", help="Switch to engineering view"):
                    st.session_state.mode = "engineer"
                    st.rerun()
            else:
                if st.button("✏️ Edit", use_container_width=True, help="Switch back to design mode"):
                    st.session_state.mode = "design"
                    st.rerun()

# ============================================================
# PROJECT BROWSER
# ============================================================
def render_project_browser():
    st.subheader("📂 Saved Projects")
    
    projects = get_projects_list()
    if not projects:
        st.info("No saved projects found. Click 'Save' to save your current design.")
        return
    
    projects.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    for proj in projects:
        col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1])
        with col1:
            st.write(f"**{proj.get('name', 'Untitled')}**")
        with col2:
            st.caption(f"👤 {proj.get('client', 'N/A')} | 🔑 {proj.get('reference', 'N/A')}")
        with col3:
            st.caption(f"{proj.get('typology', 'Unknown')} {'🔒' if proj.get('locked') else '📝'}")
        with col4:
            if st.button("📂 Load", key=f"load_{proj.get('file')}", use_container_width=True):
                if load_project_from_file(proj.get('file')):
                    st.success("✅ Project loaded!")
                    st.session_state.show_project_browser = False
                    st.rerun()
                else:
                    st.error("⚠️ Failed to load project.")
        st.divider()
    
    if st.button("🔒 Close Projects", use_container_width=True):
        st.session_state.show_project_browser = False
        st.rerun()

# ============================================================
# DASHBOARD — LANDING PAGE
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
            if st.button("📂 Open Saved Project", use_container_width=True):
                st.session_state.show_project_browser = True
                st.rerun()
        else:
            st.button("📂 No Saved Projects", use_container_width=True, disabled=True)
    
    if projects:
        st.subheader("📋 Recent Projects")
        for proj in projects[:3]:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{proj.get('name', 'Untitled')}**")
            with col2:
                st.caption(f"👤 {proj.get('client', 'N/A')} | {proj.get('typology', 'Unknown')}")
            with col3:
                if st.button("Open", key=f"dash_load_{proj.get('file')}", use_container_width=True):
                    if load_project_from_file(proj.get('file')):
                        st.rerun()
            st.divider()
    
    st.caption("💡 Select 'New Design' to start a project, or open an existing project from the list above.")

# ============================================================
# UI RENDERING
# ============================================================

# ---- TOP BAR (Always visible) ----
render_top_bar()

# ---- PROJECT BROWSER (Toggle) ----
if st.session_state.show_project_browser:
    render_project_browser()
    st.stop()

# ---- DASHBOARD (Landing page) ----
if not st.session_state.project_registered and not st.session_state.show_registration:
    render_dashboard()
    st.stop()

# ---- PROJECT REGISTRATION ----
if st.session_state.show_registration or (st.session_state.project_registered and not st.session_state.typology):
    if st.session_state.show_registration or not st.session_state.project_registered:
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
            
            ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            project_ref = st.text_input("🔑 Project Reference", value=f"SDS-{ref}")
            
            col_submit1, col_submit2 = st.columns([3, 1])
            with col_submit1:
                submitted = st.form_submit_button("🚀 Start Design Studio", use_container_width=True, type="primary")
            with col_submit2:
                if st.form_submit_button("⬅ Back", use_container_width=True):
                    st.session_state.show_registration = False
                    st.rerun()
            
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
                    st.session_state.design_phase = "input"
                    st.session_state.show_registration = False
                    save_cache()
                    st.rerun()
        
        st.caption("All data is cached locally. Your project will resume where you left off.")
        st.stop()

# ---- After registration, show catalog if no typology selected ----
info = st.session_state.project_info

if st.session_state.project_registered and st.session_state.typology is None:
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
                st.session_state.mode = "design"
                st.session_state.design_phase = "input"
                save_cache()
                st.rerun()
        idx += 1
    st.caption("💡 Select a structure type to begin designing.")
    st.stop()

# ---- ACTIVE TYPOLOGY VIEW ----
typ_key = st.session_state.typology
typ = TYPOLOGIES[typ_key]
params = st.session_state.params

# ---- DESIGN INPUT PHASE ----
if st.session_state.design_phase == "input":
    st.subheader(f"{typ['icon']} {typ['name']} — Design Inputs")
    
    st.subheader("📐 Dimensions")
    cols = st.columns(2)
    col_idx = 0
    for p_key, p_def in typ["params"].items():
        with cols[col_idx % 2]:
            val = st.number_input(
                p_def["label"],
                min_value=float(p_def["min"]),
                max_value=float(p_def["max"]),
                step=float(p_def["step"]),
                value=float(params.get(p_key, p_def["default"])),
                format="%.1f"
            )
            params[p_key] = val
        col_idx += 1
    save_cache()
    
    if st.button("📋 Review Design in SDS-UNDERSTAND", use_container_width=True, type="primary"):
        st.session_state.design_phase = "review"
        save_cache()
        st.rerun()

# ---- SDS-UNDERSTAND BOARD ----
elif st.session_state.design_phase == "review":
    st.subheader("🧠 SDS-UNDERSTAND — Engineering Understanding & Model Confirmation")
    st.caption("Review the interpretation summary and confirm your design assumptions before proceeding to engineering investigation.")
    
    st.subheader("📊 Current Interpretation Summary")
    summary_data = {
        "PRIMARY STRUCTURE": "Two curved beams — 🟡 Inferred",
        "MEMBRANE": "Saddle / anticlastic form — 🟡 Inferred",
        "APEX POINT (P_A)": f"High point of structure at {params.get('A', 13.0)}m — 🟡 Inferred",
        "SUPPORTS": "Two supports at beam bases — 🟡 Inferred",
        "DIMENSIONS": f"A={params.get('A', 13.0)}m, B={params.get('B', 5.0)}m, LAA={params.get('LAA', 10.0)}m — 🟢 Provided by User",
        "UNKNOWN ITEMS": "Material, Beams, Prestress, Bracing, Foundations etc. — 🔴 Unknown"
    }
    
    for key, value in summary_data.items():
        st.markdown(f"**{key}:** {value}")
    
    st.divider()
    
    st.subheader("📌 Legend (Data Identity)")
    col_leg1, col_leg2, col_leg3 = st.columns(3)
    with col_leg1:
        st.markdown("🟢 **Confirmed by User**")
    with col_leg2:
        st.markdown("🟡 **Inferred by SDS** *(To be confirmed)*")
    with col_leg3:
        st.markdown("🔴 **Unknown / Not Yet Defined**")
    
    st.divider()
    
    st.subheader("❓ Structured Questions")
    st.caption("Confirm the following assumptions about your design. These will be locked and stored in the engineering report.")
    
    for i, q in enumerate(typ["qa"]):
        key = f"qa_{i}"
        default = st.session_state.qa_answers.get(key, "Yes")
        if "?" in q:
            ans = st.radio(
                f"{i+1}. {q}",
                ["Yes", "No", "Not Sure"],
                index=["Yes", "No", "Not Sure"].index(default),
                key=f"understand_{i}"
            )
        else:
            options = ["Open", "Enclosed", "PVC", "PTFE", "Steel"]
            ans = st.selectbox(
                f"{i+1}. {q}",
                options,
                index=options.index(default) if default in options else 0,
                key=f"understand_{i}"
            )
        st.session_state.qa_answers[key] = ans
    save_cache()
    
    st.subheader("💬 Add Comments / Instructions")
    comments = st.text_area(
        "Type your comment here...",
        value=st.session_state.comments,
        height=100,
        key="understand_comments"
    )
    st.session_state.comments = comments
    save_cache()
    
    st.divider()
    
    col_lock1, col_lock2 = st.columns([3, 1])
    with col_lock1:
        if st.button("🔒 LOCK & PROCEED TO INVESTIGATION", use_container_width=True, type="primary"):
            st.session_state.locked = True
            st.session_state.mode = "engineer"
            st.session_state.design_phase = "engineering"
            save_cache()
            st.rerun()
    with col_lock2:
        if st.button("⬅ Modify", use_container_width=True):
            st.session_state.design_phase = "input"
            save_cache()
            st.rerun()
    
    st.caption("Once you lock, the interpretation will be frozen and you will proceed to the Engineering Investigation phase.")

# ---- ENGINEERING INVESTIGATION ----
elif st.session_state.design_phase == "engineering" or st.session_state.locked:
    if not st.session_state.locked:
        st.session_state.locked = True
        st.session_state.mode = "engineer"
        save_cache()
    
    st.subheader(f"{typ['icon']} {typ['name']} — Engineering Investigation")
    
    if st.session_state.locked:
        st.warning("🔒 Design is LOCKED. Click 'Unlock' below to make changes.")
    
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
            width = st.number_input("Width (m)", min_value=1.0, max_value=100.0, step=0.5, value=params.get("width", 10.0), format="%.1f")
            params["width"] = width
        with cols[1]:
            length = st.number_input("Length (m)", min_value=1.0, max_value=100.0, step=0.5, value=params.get("length", 15.0), format="%.1f")
            params["length"] = length
        with cols[2]:
            height = st.number_input("Height (m)", min_value=1.0, max_value=50.0, step=0.5, value=params.get("height", 8.0), format="%.1f")
            params["height"] = height
        
        st.info("📝 This is a custom design. The 3D view shows a bounding box placeholder.")
    
    st.subheader("🔬 Engineering View")
    
    if st.session_state.mode == "engineer":
        st.caption("Toggle engineering annotations:")
        anno_cols = st.columns(3)
        with anno_cols[0]:
            st.session_state.engineering_annotations["show_wind"] = st.checkbox("💨 Wind Load", value=st.session_state.engineering_annotations.get("show_wind", True))
        with anno_cols[1]:
            st.session_state.engineering_annotations["show_tie_down"] = st.checkbox("🔗 Tie-Down Anchors", value=st.session_state.engineering_annotations.get("show_tie_down", True))
        with anno_cols[2]:
            st.session_state.engineering_annotations["show_load_path"] = st.checkbox("📊 Load Path", value=st.session_state.engineering_annotations.get("show_load_path", True))
        save_cache()
    
    if typ_key == "custom":
        fig = generate_custom_bounding_box(params)
        if st.session_state.custom_image:
            st.image(st.session_state.custom_image, caption="Design Reference", use_column_width=True)
        if st.session_state.custom_description:
            st.caption(f"📝 {st.session_state.custom_description}")
    else:
        if typ_key in GENERATORS:
            if st.session_state.mode == "engineer" and typ_key == "saddle_span":
                fig = generate_saddle_span(params, st.session_state.engineering_annotations)
            else:
                fig = GENERATORS[typ_key](params)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    
    with st.expander("📋 Design Summary & Export"):
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
        
        if st.session_state.comments:
            st.write("---")
            st.write(f"**💬 Comments:** {st.session_state.comments}")
        
        st.write("---")
        st.subheader("📤 Export")
        
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            if typ_key != "custom" and typ_key in GENERATORS:
                try:
                    if st.session_state.mode == "engineer" and typ_key == "saddle_span":
                        fig_export = generate_saddle_span(params, st.session_state.engineering_annotations)
                    else:
                        fig_export = GENERATORS[typ_key](params)
                    img_link = get_image_download_link(fig_export)
                    st.markdown(img_link, unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"⚠️ Image export requires additional setup: {str(e)}")
            else:
                st.info("📸 Image export available for standard typologies.")
        
        with col_exp2:
            export_data = {
                "project": info,
                "typology": typ_key,
                "parameters": params,
                "qa_answers": st.session_state.qa_answers,
                "comments": st.session_state.comments,
                "locked": st.session_state.locked,
                "export_date": datetime.now().isoformat()
            }
            if typ_key == "custom":
                export_data["custom_image"] = st.session_state.custom_image is not None
                export_data["custom_description"] = st.session_state.custom_description
            json_link = get_json_download_link(export_data)
            st.markdown(json_link, unsafe_allow_html=True)
    
    if st.session_state.locked:
        if st.button("🔓 Unlock Design", use_container_width=True):
            st.session_state.locked = False
            st.session_state.mode = "design"
            st.session_state.design_phase = "review"
            save_cache()
            st.rerun()

st.caption("SDS Platform v1.0 | Save Works | Comments Visible | Clean Navigation")
save_cache()
