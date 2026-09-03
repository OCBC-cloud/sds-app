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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
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
        border-radius: 8px !important;
        padding: 0.3rem 0.4rem !important;
        font-weight: 500 !important;
        font-size: 0.7rem !important;
        transition: all 0.2s !important;
        width: 100% !important;
        white-space: nowrap !important;
        min-height: 30px !important;
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
    
    /* Dashboard Cards */
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
    
    /* SDS-UNDERSTAND Cards */
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
    .sds-card .badge {
        display: inline-block;
        padding: 0.1rem 0.5rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 500;
        margin-left: 0.5rem;
    }
    .badge-confirmed { background-color: #2d6a4f; color: #a7f3d0; }
    .badge-inferred { background-color: #7d5a2d; color: #fcd34d; }
    .badge-unknown { background-color: #6b2d2d; color: #fca5a5; }
    .badge-provided { background-color: #1e3a5f; color: #93c5fd; }
    .badge-autogen { background-color: #3b3b6b; color: #c4b5fd; }
    
    /* Export Section */
    .export-section {
        background-color: #141e2b;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #2a3a4f;
        margin: 1rem 0;
    }
    .export-section a {
        color: #4a7a9c !important;
        text-decoration: underline;
        font-weight: 500;
    }
    .export-section a:hover {
        color: #f39c12 !important;
    }
    
    /* Proposal Drawings */
    .proposal-drawings {
        background-color: #0a0e17;
        border-radius: 12px;
        padding: 0.5rem;
        border: 1px solid #1e2a3a;
        margin: 0.5rem 0;
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
        "show_load_path": True,
        "show_bracing": True
    }
if "design_phase" not in st.session_state:
    st.session_state.design_phase = "input"
if "comments" not in st.session_state:
    st.session_state.comments = ""
if "show_project_browser" not in st.session_state:
    st.session_state.show_project_browser = False
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False
if "show_export" not in st.session_state:
    st.session_state.show_export = False
if "show_proposal" not in st.session_state:
    st.session_state.show_proposal = False

# Materials State
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
        "num_anchors": 2,
        "anchor_angle": 30,
        "wind_speed": 40,
        "snow_load": 0.5,
        "live_load": 0.5,
        "tie_down_vertical_angle": 45,
        "tie_down_horizontal_spread": 25
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
        "custom_image": st.session_state.custom_image,
        "custom_description": st.session_state.custom_description,
        "engineering_annotations": st.session_state.engineering_annotations,
        "design_phase": st.session_state.design_phase,
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
            st.session_state.custom_image = data.get("custom_image")
            st.session_state.custom_description = data.get("custom_description", "")
            st.session_state.engineering_annotations = data.get("engineering_annotations", {
                "show_wind": True,
                "show_tie_down": True,
                "show_load_path": True,
                "show_bracing": True
            })
            st.session_state.design_phase = data.get("design_phase", "input")
            st.session_state.comments = data.get("comments", "")
            st.session_state.materials = data.get("materials", {
                "steel_grade": "S355",
                "section_type": "Circular Hollow Section (CHS)",
                "section_size": "CHS 150x6",
                "fabric_type": "PVC-coated Polyester",
                "fabric_thickness": 0.8,
                "prestress": 3.0,
                "wire_rope_type": "Galvanized Steel (6x19)",
                "wire_rope_diameter": 10,
                "num_bays": 2,
                "num_anchors": 2,
                "anchor_angle": 30,
                "wind_speed": 40,
                "snow_load": 0.5,
                "live_load": 0.5,
                "tie_down_vertical_angle": 45,
                "tie_down_horizontal_spread": 25
            })
            st.session_state.mode = "design"
            st.session_state.show_registration = False
            st.session_state.show_project_browser = False
            st.session_state.show_export = False
            st.session_state.show_proposal = False
            save_cache()
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
    st.session_state.mode = "design"
    st.session_state.qa_answers = {}
    st.session_state.locked = False
    st.session_state.custom_image = None
    st.session_state.custom_description = ""
    st.session_state.design_phase = "input"
    st.session_state.comments = ""
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    st.session_state.show_export = False
    st.session_state.show_proposal = False
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    save_cache()

def clear_cache():
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    st.session_state.project_registered = False
    st.session_state.project_info = {}
    st.session_state.typology = None
    st.session_state.params = {}
    st.session_state.mode = "design"
    st.session_state.qa_answers = {}
    st.session_state.locked = False
    st.session_state.custom_image = None
    st.session_state.custom_description = ""
    st.session_state.design_phase = "input"
    st.session_state.comments = ""
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    st.session_state.show_export = False
    st.session_state.show_proposal = False
    update_projects_index()

def save_project_as_new():
    if not st.session_state.project_info.get("name"):
        st.error("⚠️ Project name is required to save.")
        return
    ref = st.session_state.project_info.get("reference")
    if not ref:
        ref = f"SDS-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    projects = get_projects_list()
    existing_file = None
    for proj in projects:
        if proj.get("reference") == ref:
            existing_file = proj.get("file")
            break
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
        "comments": st.session_state.comments,
        "materials": st.session_state.materials
    }
    if existing_file:
        filepath = os.path.join(CACHE_DIR, existing_file)
        with open(filepath, "w") as f:
            json.dump(data, f)
        st.success(f"✅ Project updated: {existing_file}")
    else:
        filename = f"project_{ref}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(CACHE_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(data, f)
        st.success(f"✅ Project saved as: {filename}")
    update_projects_index()

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
    st.session_state.custom_image = cached.get("custom_image")
    st.session_state.custom_description = cached.get("custom_description", "")
    st.session_state.engineering_annotations = cached.get("engineering_annotations", {
        "show_wind": True,
        "show_tie_down": True,
        "show_load_path": True,
        "show_bracing": True
    })
    st.session_state.design_phase = cached.get("design_phase", "input")
    st.session_state.comments = cached.get("comments", "")
    st.session_state.materials = cached.get("materials", {
        "steel_grade": "S355",
        "section_type": "Circular Hollow Section (CHS)",
        "section_size": "CHS 150x6",
        "fabric_type": "PVC-coated Polyester",
        "fabric_thickness": 0.8,
        "prestress": 3.0,
        "wire_rope_type": "Galvanized Steel (6x19)",
        "wire_rope_diameter": 10,
        "num_bays": 2,
        "num_anchors": 2,
        "anchor_angle": 30,
        "wind_speed": 40,
        "snow_load": 0.5,
        "live_load": 0.5,
        "tie_down_vertical_angle": 45,
        "tie_down_horizontal_spread": 25
    })

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
            "Is the apex/high point correctly identified at the top of the structure?",
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
# AUTO-GENERATION FUNCTIONS
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

def generate_tie_down_anchors_full(span, laa, height, vertical_angle_deg, horizontal_spread_deg):
    vertical_rad = np.radians(vertical_angle_deg)
    horizontal_rad = np.radians(horizontal_spread_deg)
    distance = height * np.tan(vertical_rad)
    quarter = span / 4
    three_quarter = 3 * span / 4
    anchors = []
    beam_ys = [-laa/2, laa/2]
    for beam_idx, beam_y in enumerate(beam_ys):
        for beam_x in [quarter, three_quarter]:
            for side in [-1, 1]:
                anchor_x = beam_x + distance * side * np.sin(horizontal_rad)
                anchor_y = beam_y + distance * np.cos(horizontal_rad)
                anchor_z = 0
                anchors.append({
                    "beam_x": beam_x,
                    "beam_y": beam_y,
                    "anchor_x": anchor_x,
                    "anchor_y": anchor_y,
                    "anchor_z": anchor_z,
                    "beam": beam_idx + 1,
                    "position": "quarter" if beam_x == quarter else "three_quarter",
                    "side": "left" if side == -1 else "right"
                })
    return anchors

def calculate_steel_weight(grade, section_type, section_size, length):
    weight_per_m = {
        "CHS 100x5": 11.7, "CHS 150x6": 21.3, "CHS 200x8": 37.9,
        "RHS 150x100x6": 22.2, "RHS 200x150x8": 39.3,
        "I-100": 10.0, "I-150": 18.0, "I-200": 26.0,
        "Pipe 100x5": 11.7, "Pipe 150x6": 21.3
    }
    return weight_per_m.get(section_size, 20.0) * length

def calculate_fabric_weight(fabric_type, thickness, area):
    weight_per_m2 = {
        "PVC-coated Polyester": {0.5: 0.6, 0.8: 0.9, 1.0: 1.2, 1.2: 1.4},
        "PTFE-coated Fiberglass": {0.5: 1.0, 0.8: 1.4, 1.0: 1.8, 1.2: 2.2},
        "ETFE": {0.5: 0.5, 0.8: 0.8, 1.0: 1.0, 1.2: 1.2}
    }
    return weight_per_m2.get(fabric_type, {}).get(thickness, 1.0) * area

def calculate_wind_load(wind_speed, area, drag_coefficient=1.2):
    rho = 1.225
    q = 0.5 * rho * wind_speed**2 / 1000
    return q * drag_coefficient * area

def calculate_tie_down_force(wind_load, self_weight_kn, num_anchors, vertical_angle_deg, safety_factor=1.5):
    uplift = wind_load * 0.8
    net_uplift = max(0, uplift - self_weight_kn * 0.5)
    per_anchor = net_uplift / num_anchors * safety_factor
    cable_force = per_anchor / np.cos(np.radians(vertical_angle_deg))
    return cable_force

# ============================================================
# PROPOSAL DRAWINGS (Matplotlib) — CORRECTED SYNTAX
# ============================================================

def generate_proposal_drawings(params, materials):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    fig.patch.set_facecolor('#0a0e17')
    
    # ---- Plan View (Top) ----
    ax = axes[0, 0]
    ax.set_facecolor('#141e2b')
    ax.set_title("Plan View", color='#ffffff', fontsize=10)
    x = np.linspace(-span/2, span/2, 30)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    y2 = laa/2 * (1 - (2 * x / span)**2)
    ax.plot(x, y1, color='#FF6B6B', linewidth=2, label='Beam 1')
    ax.plot(x, y2, color='#FF6B6B', linewidth=2, label='Beam 2')
    ax.scatter(0, y1[len(y1)//2], color='#FFD93D', s=50, zorder=5, label='Apex 1')
    ax.scatter(0, y2[len(y2)//2], color='#FFD93D', s=50, zorder=5, label='Apex 2')
    ax.scatter(-span/2, 0, color='#4ECDC4', s=50, zorder=5, label='Support 1')
    ax.scatter(span/2, 0, color='#4ECDC4', s=50, zorder=5, label='Support 2')
    
    anchors = generate_tie_down_anchors_full(span, laa, rise, materials.get("tie_down_vertical_angle", 45), materials.get("tie_down_horizontal_spread", 25))
    for a in anchors:
        ax.scatter(a["beam_x"], a["beam_y"], color='#FFD93D', s=30, zorder=5, marker='^', label='Tie-down' if a == anchors[0] else "")
        ax.scatter(a["anchor_x"], a["anchor_y"], color='#FF6B6B', s=30, zorder=5, marker='s', label='Anchor' if a == anchors[0] else "")
    
    ax.annotate(f'B = {span:.1f}m', xy=(0, -laa/2 - 1), color='#ffffff', fontsize=8, ha='center')
    ax.annotate(f'LAA = {laa:.1f}m', xy=(span/2 + 0.5, 0), color='#ffffff', fontsize=8, va='center')
    ax.set_xlabel('Span (m)', color='#b0c4de', fontsize=8)
    ax.set_ylabel('Width (m)', color='#b0c4de', fontsize=8)
    ax.tick_params(colors='#b0c4de', labelsize=7)
    ax.grid(True, color='#1a2a3a', linestyle='--', linewidth=0.5)
    ax.legend(loc='upper right', fontsize=6, facecolor='#141e2b', edgecolor='#2a3a4f')
    
    # ---- Front Elevation ----
    ax = axes[0, 1]
    ax.set_facecolor('#141e2b')
    ax.set_title("Front Elevation", color='#ffffff', fontsize=10)
    x = np.linspace(-span/2, span/2, 50)
    z = rise * (1 - (2 * x / span)**2)
    ax.plot(x, z, color='#FF6B6B', linewidth=2)
    ax.scatter(0, rise, color='#FFD93D', s=50, zorder=5, label='Apex')
    ax.scatter(-span/2, 0, color='#4ECDC4', s=50, zorder=5, label='Support')
    ax.scatter(span/2, 0, color='#4ECDC4', s=50, zorder=5, label='Support')
    ax.annotate(f'Rise (A) = {rise:.1f}m', xy=(0, rise/2), color='#ffffff', fontsize=8, ha='right')
    ax.annotate(f'Span (B) = {span:.1f}m', xy=(0, -0.5), color='#ffffff', fontsize=8, ha='center')
    ax.set_xlabel('Span (m)', color='#b0c4de', fontsize=8)
    ax.set_ylabel('Height (m)', color='#b0c4de', fontsize=8)
    ax.tick_params(colors='#b0c4de', labelsize=7)
    ax.grid(True, color='#1a2a3a', linestyle='--', linewidth=0.5)
    ax.set_ylim(-1, rise * 1.2)
    ax.legend(loc='upper right', fontsize=6, facecolor='#141e2b', edgecolor='#2a3a4f')
    
    # ---- Side Elevation ----
    ax = axes[1, 0]
    ax.set_facecolor('#141e2b')
    ax.set_title("Side Elevation", color='#ffffff', fontsize=10)
    x = np.linspace(-span/2, span/2, 50)
    z = rise * (1 - (2 * x / span)**2)
    ax.plot(x, z, color='#FF6B6B', linewidth=2)
    ax.scatter(0, rise, color='#FFD93D', s=50, zorder=5)
    ax.scatter(-span/2, 0, color='#4ECDC4', s=50, zorder=5)
    ax.scatter(span/2, 0, color='#4ECDC4', s=50, zorder=5)
    vertical_angle = materials.get("tie_down_vertical_angle", 45)
    distance = rise * np.tan(np.radians(vertical_angle))
    ax.plot([-span/4, -span/4 - distance], [rise * 0.5, 0], color='#FFD93D', linewidth=1.5, linestyle='--', label=f'Vertical {vertical_angle}°')
    ax.plot([span/4, span/4 + distance], [rise * 0.5, 0], color='#FFD93D', linewidth=1.5, linestyle='--')
    ax.annotate(f'A = {rise:.1f}m', xy=(0, rise/2), color='#ffffff', fontsize=8, ha='right')
    ax.annotate(f'B = {span:.1f}m', xy=(0, -0.5), color='#ffffff', fontsize=8, ha='center')
    ax.set_xlabel('Span (m)', color='#b0c4de', fontsize=8)
    ax.set_ylabel('Height (m)', color='#b0c4de', fontsize=8)
    ax.tick_params(colors='#b0c4de', labelsize=7)
    ax.grid(True, color='#1a2a3a', linestyle='--', linewidth=0.5)
    ax.set_ylim(-rise * 0.3, rise * 1.2)
    ax.legend(loc='upper right', fontsize=6, facecolor='#141e2b', edgecolor='#2a3a4f')
    
    # ---- Perspective View ----
    ax = axes[1, 1]
    ax.set_facecolor('#141e2b')
    ax.set_title("Perspective View", color='#ffffff', fontsize=10)
    x = np.linspace(-span/2, span/2, 30)
    y1 = -laa/2 * (1 - (2 * x / span)**2) * 0.5
    y2 = laa/2 * (1 - (2 * x / span)**2) * 0.5
    z = rise * (1 - (2 * x / span)**2)
    offset = 0.3 * span
    ax.plot(x + offset, z + y1, color='#FF6B6B', linewidth=2, label='Beam 1')
    ax.plot(x + offset, z + y2, color='#FF6B6B', linewidth=2, label='Beam 2')
    ax.fill_between(x + offset, z + y1, z + y2, color='#4a7a9c', alpha=0.3)
    ax.scatter(offset, rise, color='#FFD93D', s=50, zorder=5, label='Apex')
    ax.scatter(-span/2 + offset, 0, color='#4ECDC4', s=50, zorder=5, label='Support')
    ax.scatter(span/2 + offset, 0, color='#4ECDC4', s=50, zorder=5, label='Support')
    ax.annotate(f'A={rise:.1f}m', xy=(offset + 0.5, rise/2), color='#ffffff', fontsize=8)
    ax.annotate(f'B={span:.1f}m', xy=(0 + offset, -0.5), color='#ffffff', fontsize=8, ha='center')
    ax.annotate(f'LAA={laa:.1f}m', xy=(span/2 + offset + 0.5, 0), color='#ffffff', fontsize=8)
    ax.set_xlabel('Width', color='#b0c4de', fontsize=8)
    ax.set_ylabel('Height', color='#b0c4de', fontsize=8)
    ax.tick_params(colors='#b0c4de', labelsize=7)
    ax.grid(True, color='#1a2a3a', linestyle='--', linewidth=0.5)
    ax.set_xlim(-span/2 + offset - 1, span/2 + offset + 1)
    ax.set_ylim(-1, rise * 1.2)
    ax.legend(loc='upper right', fontsize=6, facecolor='#141e2b', edgecolor='#2a3a4f')
    
    plt.tight_layout()
    return fig

def get_proposal_download_link(fig, filename="proposal_drawings.png"):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='#0a0e17')
    buf.seek(0)
    img = Image.open(buf)
    buf2 = io.BytesIO()
    img.save(buf2, format='PNG')
    b64 = base64.b64encode(buf2.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">📄 Download Proposal Drawings (PNG)</a>'
    return href

# ============================================================
# 3D GENERATORS
# ============================================================

def generate_saddle_span(params, materials=None, annotations=None):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
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

    # Beams
    fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1', line=dict(color='#FF6B6B', width=6)))
    fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2', line=dict(color='#FF6B6B', width=6)))

    # Membrane
    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, 
                             colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
                             opacity=0.7, showscale=False))

    # Apex markers
    fig.add_trace(go.Scatter3d(x=[0], y=[y1[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 1', marker=dict(color='#FFD93D', size=6, symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[0], y=[y2[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 2', marker=dict(color='#FFD93D', size=6, symbol='diamond')))

    # Support markers
    fig.add_trace(go.Scatter3d(x=[-span/2], y=[0], z=[0], 
                               mode='markers', name='Support 1', marker=dict(color='#4ECDC4', size=6, symbol='square')))
    fig.add_trace(go.Scatter3d(x=[span/2], y=[0], z=[0], 
                               mode='markers', name='Support 2', marker=dict(color='#4ECDC4', size=6, symbol='square')))

    # Cross Bracing
    if materials and annotations and annotations.get("show_bracing", True):
        num_bays = materials.get("num_bays", 2)
        bracing_x = generate_bracing_positions(span, num_bays)
        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            y1_pos = y1[idx]
            y2_pos = y2[idx]
            z_pos = z_beam[idx]
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[y1_pos, y2_pos], z=[z_pos, z_pos],
                mode='lines', name='Cross Bracing',
                line=dict(color='#FF6B6B', width=2, dash='dash'),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[y2_pos, y1_pos], z=[z_pos, z_pos],
                mode='lines', name='Cross Bracing',
                line=dict(color='#FF6B6B', width=2, dash='dash'),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[bx], y=[(y1_pos + y2_pos)/2], z=[z_pos + 0.3],
                mode='text', text=[f'▲ {num_bays} bays'],
                textfont=dict(color='#FF6B6B', size=7),
                showlegend=False
            ))

    # Tie-Downs
    if materials and annotations and annotations.get("show_tie_down", True):
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        horizontal_spread = materials.get("tie_down_horizontal_spread", 25)
        anchors = generate_tie_down_anchors_full(span, laa, rise, vertical_angle, horizontal_spread)
        for a in anchors:
            fig.add_trace(go.Scatter3d(
                x=[a["beam_x"], a["anchor_x"]],
                y=[a["beam_y"], a["anchor_y"]],
                z=[rise * 0.5, a["anchor_z"]],
                mode='lines',
                name='Tie-Down Rope',
                line=dict(color='#FFD93D', width=2),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[a["anchor_x"]],
                y=[a["anchor_y"]],
                z=[a["anchor_z"]],
                mode='markers',
                name='Ground Anchor',
                marker=dict(color='#FF6B6B', size=5, symbol='x'),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[a["beam_x"]],
                y=[a["beam_y"]],
                z=[rise * 0.5 + 0.2],
                mode='text',
                text=[f'▲ {a["position"]} {a["side"]}'],
                textfont=dict(color='#FFD93D', size=6),
                showlegend=False
            ))

    # Wind Arrows
    if annotations and annotations.get("show_wind", True):
        fig.add_trace(go.Scatter3d(
            x=[-span/4, -span/4], y=[-laa/4, -laa/4], z=[rise*0.8, rise*1.2],
            mode='lines', name='Wind Load',
            line=dict(color='#FF6B6B', width=3, dash='dash'),
            showlegend=True
        ))
        fig.add_trace(go.Scatter3d(
            x=[span/4, span/4], y=[laa/4, laa/4], z=[rise*0.8, rise*1.2],
            mode='lines', name='Wind Load',
            line=dict(color='#FF6B6B', width=3, dash='dash'),
            showlegend=False
        ))

    # Load Path
    if annotations and annotations.get("show_load_path", True):
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[rise, rise-2],
            mode='lines', name='Load Path',
            line=dict(color='#FFD93D', width=4),
            showlegend=True
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
            font=dict(color='#ffffff', size=7),
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(10,14,23,0.7)',
            bordercolor='#2a3a4f',
            borderwidth=1,
            itemsizing='constant'
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
            xaxis_title='Width', yaxis_title='Length', zaxis_title='Height',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0),
        legend=dict(font=dict(color='#ffffff', size=7), orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, bgcolor='rgba(10,14,23,0.7)')
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
            xaxis_title='Length', yaxis_title='Width', zaxis_title='Height',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0),
        legend=dict(font=dict(color='#ffffff', size=7), orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, bgcolor='rgba(10,14,23,0.7)')
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
            xaxis_title='Width', yaxis_title='Length', zaxis_title='Height',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0),
        legend=dict(font=dict(color='#ffffff', size=7), orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, bgcolor='rgba(10,14,23,0.7)')
    )
    return fig

def generate_custom_bounding_box(params):
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
    fig.add_trace(go.Scatter3d(x=[0], y=[-length/2 - 1], z=[height/2], mode='text', text=[f"W: {width:.1f}m"], textfont=dict(color='#FFD93D', size=14), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[width/2 + 1], y=[0], z=[height/2], mode='text', text=[f"L: {length:.1f}m"], textfont=dict(color='#4ECDC4', size=14), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[width/2 + 0.5], y=[-length/2 - 0.5], z=[height/2], mode='text', text=[f"H: {height:.1f}m"], textfont=dict(color='#FF6B6B', size=14), showlegend=False))
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)',
            aspectmode='manual', aspectratio=dict(x=1.5, y=2.0, z=0.8),
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17', margin=dict(l=0, r=0, b=0, t=0)
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
        return f"⚠️ Image export failed: {str(e)}. Please use screenshot or Proposal Drawings."

def get_json_download_link(data, filename="project_data.json"):
    json_str = json.dumps(data, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">📄 Download Design Data (JSON)</a>'
    return href

def render_export_section():
    if not st.session_state.typology or not st.session_state.project_registered:
        st.info("No active project to export.")
        return
    st.markdown('<div class="export-section">', unsafe_allow_html=True)
    st.subheader("📤 Export Current Project")
    typ_key = st.session_state.typology
    params = st.session_state.params
    info = st.session_state.project_info
    materials = st.session_state.materials
    
    col1, col2 = st.columns(2)
    with col1:
        if typ_key in GENERATORS and typ_key != "custom":
            try:
                if typ_key == "saddle_span":
                    fig = generate_saddle_span(params, materials, st.session_state.engineering_annotations)
                else:
                    fig = GENERATORS[typ_key](params)
                img_link = get_image_download_link(fig)
                st.markdown(img_link, unsafe_allow_html=True)
            except Exception as e:
                st.info("📸 Use 'Proposal Drawings' button below for guaranteed export.")
        else:
            st.info("Image export available for standard typologies.")
    with col2:
        export_data = {
            "project": info,
            "typology": typ_key,
            "parameters": params,
            "qa_answers": st.session_state.qa_answers,
            "comments": st.session_state.comments,
            "materials": materials,
            "locked": st.session_state.locked,
            "export_date": datetime.now().isoformat()
        }
        if typ_key == "custom":
            export_data["custom_image"] = st.session_state.custom_image is not None
            export_data["custom_description"] = st.session_state.custom_description
        json_link = get_json_download_link(export_data)
        st.markdown(json_link, unsafe_allow_html=True)
    st.caption("Exports include geometry, materials, bracing, and tie-down configuration.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("📐 Proposal Drawings Package")
    st.caption("Generate a complete set of technical drawings: Plan, Front Elevation, Side Elevation, Perspective with dimensions.")
    if st.button("📊 Generate Proposal Drawings", use_container_width=True, type="primary"):
        st.session_state.show_proposal = True
        st.rerun()

def render_proposal_drawings():
    if not st.session_state.show_proposal:
        return
    st.subheader("📐 Proposal Drawings Package")
    params = st.session_state.params
    materials = st.session_state.materials
    fig = generate_proposal_drawings(params, materials)
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, facecolor='#0a0e17')
    buf.seek(0)
    
    try:
        img = Image.open(buf)
        img_array = np.array(img)
        st.image(img_array, caption="Plan, Front Elevation, Side Elevation, Perspective", use_container_width=True)
    except Exception as e:
        st.error(f"Failed to display image: {e}. Please try the download link below.")
    
    link = get_proposal_download_link(fig)
    st.markdown(link, unsafe_allow_html=True)
    
    if st.button("🔒 Close Drawings", use_container_width=True):
        st.session_state.show_proposal = False
        st.rerun()
    plt.close(fig)

# ============================================================
# MATERIALS & BRACING UI
# ============================================================

def render_materials_section():
    st.subheader("🏗️ Materials & Bracing")
    st.caption("Select materials and configure wind bracing and tie-downs.")
    m = st.session_state.materials
    
    st.markdown("### 🔩 Primary Structure")
    col1, col2, col3 = st.columns(3)
    with col1:
        m["steel_grade"] = st.selectbox("Steel Grade", ["S275", "S355", "S460", "6061-T6 (Aluminum)"], index=["S275", "S355", "S460", "6061-T6 (Aluminum)"].index(m.get("steel_grade", "S355")))
    with col2:
        m["section_type"] = st.selectbox("Section Type", ["Circular Hollow Section (CHS)", "Rectangular Hollow Section (RHS)", "I-Beam", "Pipe"], index=["Circular Hollow Section (CHS)", "Rectangular Hollow Section (RHS)", "I-Beam", "Pipe"].index(m.get("section_type", "Circular Hollow Section (CHS)")))
    with col3:
        section_sizes = {
            "Circular Hollow Section (CHS)": ["CHS 100x5", "CHS 150x6", "CHS 200x8", "CHS 250x10"],
            "Rectangular Hollow Section (RHS)": ["RHS 150x100x6", "RHS 200x150x8", "RHS 250x150x10"],
            "I-Beam": ["I-100", "I-150", "I-200", "I-250"],
            "Pipe": ["Pipe 100x5", "Pipe 150x6", "Pipe 200x8"]
        }
        m["section_size"] = st.selectbox("Section Size", section_sizes.get(m["section_type"], ["CHS 150x6"]), index=0)
    
    st.markdown("### 🧵 Membrane Fabric")
    col1, col2, col3 = st.columns(3)
    with col1:
        m["fabric_type"] = st.selectbox("Fabric Type", ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"], index=["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"].index(m.get("fabric_type", "PVC-coated Polyester")))
    with col2:
        m["fabric_thickness"] = st.selectbox("Thickness (mm)", [0.5, 0.8, 1.0, 1.2], index=[0.5, 0.8, 1.0, 1.2].index(m.get("fabric_thickness", 0.8)))
    with col3:
        m["prestress"] = st.selectbox("Prestress Level (kN/m)", [1.0, 3.0, 5.0], index=[1.0, 3.0, 5.0].index(m.get("prestress", 3.0)))
    
    st.markdown("### 🔗 Wind Bracing & Tie-Downs")
    st.caption("📐 Tie-downs are automatically placed at 1/4 and 3/4 points of each beam. Two tie-downs per beam (left and right sides).")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        m["num_bays"] = st.selectbox("Bracing Bays", [1, 2, 3], index=[1, 2, 3].index(m.get("num_bays", 2)), help="1=Apex only, 2=Third points, 3=Quarter points")
        span = st.session_state.params.get("B", 10.0)
        positions = generate_bracing_positions(span, m["num_bays"])
        st.caption(f"📍 Positions: {', '.join([f'{p:.1f}m' for p in positions])}")
    with col2:
        m["wire_rope_diameter"] = st.selectbox("Wire Rope Diameter (mm)", [6, 8, 10, 12, 14, 16, 20], index=[6, 8, 10, 12, 14, 16, 20].index(m.get("wire_rope_diameter", 10)))
    with col3:
        m["tie_down_vertical_angle"] = st.slider(
            "Vertical Angle (°)",
            min_value=20, max_value=70, step=5, value=m.get("tie_down_vertical_angle", 45),
            help="Angle of tie-down rope from horizontal (steeper = more uplift resistance)"
        )
    with col4:
        m["tie_down_horizontal_spread"] = st.slider(
            "Horizontal Spread (°)",
            min_value=10, max_value=60, step=5, value=m.get("tie_down_horizontal_spread", 25),
            help="Angle of tie-down spread outward from beam (wider = more lateral stability)"
        )
    
    st.markdown("### 🌬️ Environmental Loads")
    col1, col2, col3 = st.columns(3)
    with col1:
        m["wind_speed"] = st.number_input("Wind Speed (m/s)", min_value=20, max_value=80, step=5, value=m.get("wind_speed", 40))
    with col2:
        m["snow_load"] = st.number_input("Snow Load (kN/m²)", min_value=0.0, max_value=5.0, step=0.5, value=m.get("snow_load", 0.5))
    with col3:
        m["live_load"] = st.number_input("Live Load (kN/m²)", min_value=0.0, max_value=5.0, step=0.5, value=m.get("live_load", 0.5))
    
    st.session_state.materials = m
    save_cache()

# ============================================================
# TOP BAR
# ============================================================

def render_top_bar():
    cols = st.columns([0.8, 1.5, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
    with cols[0]:
        if st.button("🏗️", key="sds_logo", help="Go to Dashboard"):
            go_to_dashboard()
            st.rerun()
        st.caption("SDS")
    with cols[1]:
        if st.session_state.project_registered and st.session_state.project_info:
            st.caption(f"📌 {st.session_state.project_info.get('name', 'Project')[:15]}")
        else:
            st.caption("📌 No Project")
    with cols[2]:
        if st.session_state.typology:
            typ = TYPOLOGIES.get(st.session_state.typology, {})
            st.caption(f"{typ.get('icon', '')} {typ.get('name', '')[:10]}")
        else:
            st.caption("")
    with cols[3]:
        if st.button("🏠 Dash", use_container_width=True, help="Return to Main Dashboard"):
            go_to_dashboard()
            st.rerun()
    with cols[4]:
        if st.session_state.project_registered:
            if st.button("📂 Proj", use_container_width=True, help="View saved projects"):
                st.session_state.show_project_browser = not st.session_state.show_project_browser
                st.rerun()
    with cols[5]:
        if st.session_state.project_registered and st.session_state.typology:
            if st.button("💾 Save", use_container_width=True, help="Save current project"):
                save_project_as_new()
                st.rerun()
    with cols[6]:
        if st.session_state.project_registered:
            if st.button("📋 New", use_container_width=True, help="Start new project"):
                clear_cache()
                st.rerun()
    with cols[7]:
        if st.session_state.project_registered and st.session_state.typology:
            if st.session_state.mode == "design":
                if st.button("🔍 Pro", use_container_width=True, type="primary", help="Switch to engineering view"):
                    st.session_state.mode = "engineer"
                    st.rerun()
            else:
                if st.button("✏️ Edit", use_container_width=True, help="Switch back to design"):
                    st.session_state.mode = "design"
                    st.rerun()
    with cols[8]:
        if st.session_state.locked and st.session_state.typology:
            if st.button("🔓 Unlock", use_container_width=True, type="primary", help="Unlock the design to make changes"):
                st.session_state.locked = False
                st.session_state.mode = "design"
                st.session_state.design_phase = "review"
                save_cache()
                st.rerun()
        else:
            if st.button("📤 Exp", use_container_width=True, help="Export current project"):
                st.session_state.show_export = not st.session_state.show_export
                st.rerun()

# ============================================================
# PROJECT BROWSER
# ============================================================

def render_project_browser():
    st.subheader("📂 Saved Projects")
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        go_to_dashboard()
        st.rerun()
    projects = get_projects_list()
    if not projects:
        st.info("No saved projects found. Click 'Save' to save your current design.")
        return
    projects.sort(key=lambda x: x.get("date", ""), reverse=True)
    for proj in projects:
        st.markdown(f"""
        <div style="background-color:#141e2b; padding:0.5rem 1rem; border-radius:8px; margin-bottom:0.5rem; border-left:3px solid #4a7a9c;">
            <span style="color:#ffffff; font-weight:600;">📌 Name:</span> <span style="color:#b0c4de;">{proj.get('name', 'Untitled')}</span><br>
            <span style="color:#ffffff; font-weight:600;">👤 Client:</span> <span style="color:#b0c4de;">{proj.get('client', 'Unknown')}</span> &nbsp;|&nbsp; 
            <span style="color:#ffffff; font-weight:600;">🔑 Ref:</span> <span style="color:#b0c4de;">{proj.get('reference', 'N/A')}</span> &nbsp;|&nbsp; 
            <span style="color:#ffffff; font-weight:600;">🏗️ Type:</span> <span style="color:#b0c4de;">{proj.get('typology', 'Unknown')}</span> {'🔒' if proj.get('locked') else '📝'}
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([4, 1, 1])
        with col2:
            if st.button("📂 Load", key=f"load_{proj.get('file')}", use_container_width=True):
                if load_project_from_file(proj.get('file')):
                    st.success("✅ Project loaded!")
                    st.session_state.show_project_browser = False
                    st.rerun()
                else:
                    st.error("⚠️ Failed to load project.")
        with col3:
            if st.button("🗑️ Delete", key=f"del_{proj.get('file')}", use_container_width=True):
                if delete_project_file(proj.get('file')):
                    st.success(f"✅ Project {proj.get('name')} deleted.")
                    st.rerun()
                else:
                    st.error("⚠️ Failed to delete.")
        st.divider()

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
            if st.button("📂 Open Saved Project", use_container_width=True):
                st.session_state.show_project_browser = True
                st.rerun()
        else:
            st.button("📂 No Saved Projects", use_container_width=True, disabled=True)
    if projects:
        st.subheader("📋 Recent Projects")
        for proj in projects[:3]:
            st.markdown(f"""
            <div style="background-color:#141e2b; padding:0.3rem 0.8rem; border-radius:6px; margin-bottom:0.3rem; display:flex; justify-content:space-between; align-items:center;">
                <span><span style="color:#ffffff;">📌 {proj.get('name', 'Untitled')}</span> <span style="color:#8a9aaa;">| 👤 {proj.get('client', 'N/A')} | {proj.get('typology', 'Unknown')}</span></span>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("Open", key=f"dash_load_{proj.get('file')}", use_container_width=True):
                    if load_project_from_file(proj.get('file')):
                        st.rerun()
            st.divider()
    st.caption("💡 Select 'New Design' to start a project, or open an existing project from the list above.")

# ============================================================
# MAIN UI RENDER LOOP
# ============================================================

render_top_bar()

if st.session_state.show_export:
    render_export_section()
    if st.session_state.show_proposal:
        render_proposal_drawings()

if st.session_state.show_project_browser:
    render_project_browser()
    st.stop()

if not st.session_state.project_registered and not st.session_state.show_registration:
    render_dashboard()
    st.stop()

if st.session_state.show_registration or (st.session_state.project_registered and not st.session_state.typology):
    if st.session_state.show_registration or not st.session_state.project_registered:
        st.subheader("📋 New Project Registration")
        st.caption("Fill in the project details to get started.")
        if st.button("⬅ Back to Dashboard", use_container_width=True):
            go_to_dashboard()
            st.rerun()
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
                    st.session_state.design_phase = "input"
                    st.session_state.show_registration = False
                    save_cache()
                    st.rerun()
        st.caption("All data is cached locally. Your project will resume where you left off.")
        st.stop()

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

typ_key = st.session_state.typology
typ = TYPOLOGIES[typ_key]
params = st.session_state.params

if st.session_state.design_phase == "input":
    st.subheader(f"{typ['icon']} {typ['name']} — Design Inputs")
    st.subheader("📐 Geometry")
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
    
    if typ_key == "saddle_span":
        render_materials_section()
    
    if st.button("📋 Review Design in SDS-UNDERSTAND", use_container_width=True, type="primary"):
        st.session_state.design_phase = "review"
        save_cache()
        st.rerun()

elif st.session_state.design_phase == "review":
    st.subheader("🧠 SDS-UNDERSTAND — Engineering Understanding & Model Confirmation")
    st.caption("Review the interpretation summary and confirm your design assumptions before proceeding to engineering investigation.")
    
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">📊 Current Interpretation Summary</div>', unsafe_allow_html=True)
    m = st.session_state.materials
    summary_items = [
        ("PRIMARY STRUCTURE", f"{m.get('steel_grade', 'S355')} {m.get('section_type', 'CHS')} {m.get('section_size', '150x6')}", "badge-provided"),
        ("MEMBRANE", f"{m.get('fabric_type', 'PVC')} {m.get('fabric_thickness', 0.8)}mm, {m.get('prestress', 3.0)}kN/m", "badge-provided"),
        ("APEX POINT (P_A)", f"High point at {params.get('A', 6.0)}m", "badge-inferred"),
        ("SUPPORTS", "Two supports at beam bases", "badge-inferred"),
        ("DIMENSIONS", f"A={params.get('A', 6.0)}m, B={params.get('B', 10.0)}m, LAA={params.get('LAA', 15.0)}m", "badge-confirmed"),
        ("WIND BRACING", f"{m.get('num_bays', 2)} bays at {', '.join([f'{p:.1f}m' for p in generate_bracing_positions(params.get('B', 10.0), m.get('num_bays', 2))])}", "badge-autogen"),
        ("TIE-DOWNS", f"4 anchors: 1/4 & 3/4 points, {m.get('tie_down_vertical_angle', 45)}° vertical, {m.get('tie_down_horizontal_spread', 25)}° spread", "badge-autogen"),
        ("WIRE ROPE", f"{m.get('wire_rope_diameter', 10)}mm {m.get('wire_rope_type', 'Galvanized')}", "badge-provided"),
        ("UNKNOWN ITEMS", "Foundations, Connection Details", "badge-unknown")
    ]
    for label, value, badge in summary_items:
        st.markdown(f'<div style="display:flex; justify-content:space-between; padding:0.1rem 0; border-bottom:1px solid #1a2a3a;">'
                    f'<span style="color:#ffffff; font-weight:500;">{label}</span>'
                    f'<span style="color:#b0c4de;">{value} <span class="badge {badge}">{badge.replace("badge-", "").upper()}</span></span>'
                    f'</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">📌 Legend (Data Identity)</div>', unsafe_allow_html=True)
    st.markdown(f'<span class="badge badge-confirmed">CONFIRMED</span> <span style="color:#b0c4de;">Confirmed by User</span> &nbsp;|&nbsp; '
                f'<span class="badge badge-inferred">INFERRED</span> <span style="color:#b0c4de;">Inferred by SDS</span> &nbsp;|&nbsp; '
                f'<span class="badge badge-unknown">UNKNOWN</span> <span style="color:#b0c4de;">Not Yet Defined</span> &nbsp;|&nbsp; '
                f'<span class="badge badge-provided">PROVIDED</span> <span style="color:#b0c4de;">Provided by User</span> &nbsp;|&nbsp; '
                f'<span class="badge badge-autogen">AUTO-GEN</span> <span style="color:#b0c4de;">Auto-Generated</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">❓ Structured Questions</div>', unsafe_allow_html=True)
    st.caption("Confirm the following assumptions. These will be locked and stored in the engineering report.")
    for i, q in enumerate(typ["qa"]):
        key = f"qa_{i}"
        default = st.session_state.qa_answers.get(key, "Yes")
        if "?" in q:
            ans = st.radio(f"{i+1}. {q}", ["Yes", "No", "Not Sure"], index=["Yes", "No", "Not Sure"].index(default), key=f"understand_{i}")
        else:
            options = ["Open", "Enclosed", "PVC", "PTFE", "Steel"]
            ans = st.selectbox(f"{i+1}. {q}", options, index=options.index(default) if default in options else 0, key=f"understand_{i}")
        st.session_state.qa_answers[key] = ans
    save_cache()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">💬 Comments / Instructions</div>', unsafe_allow_html=True)
    comments = st.text_area("", value=st.session_state.comments, height=80, key="understand_comments", placeholder="Type your comment here...")
    st.session_state.comments = comments
    save_cache()
    st.markdown('</div>', unsafe_allow_html=True)
    
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
        uploaded_file = st.file_uploader("Upload sketch or photo (JPG/PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.session_state.custom_image = uploaded_file.getvalue()
            st.image(uploaded_file, caption="Design Reference", use_column_width=True)
        description = st.text_area("Describe your design:", value=st.session_state.custom_description, height=100, placeholder="e.g., Three curved steel beams meeting at a central ring...")
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
        anno_cols = st.columns(4)
        with anno_cols[0]:
            st.session_state.engineering_annotations["show_wind"] = st.checkbox("💨 Wind", value=st.session_state.engineering_annotations.get("show_wind", True))
        with anno_cols[1]:
            st.session_state.engineering_annotations["show_tie_down"] = st.checkbox("🔗 Tie-Down", value=st.session_state.engineering_annotations.get("show_tie_down", True))
        with anno_cols[2]:
            st.session_state.engineering_annotations["show_bracing"] = st.checkbox("📐 Bracing", value=st.session_state.engineering_annotations.get("show_bracing", True))
        with anno_cols[3]:
            st.session_state.engineering_annotations["show_load_path"] = st.checkbox("📊 Load", value=st.session_state.engineering_annotations.get("show_load_path", True))
        save_cache()
    
    if typ_key == "custom":
        fig = generate_custom_bounding_box(params)
        if st.session_state.custom_image:
            st.image(st.session_state.custom_image, caption="Design Reference", use_column_width=True)
        if st.session_state.custom_description:
            st.caption(f"📝 {st.session_state.custom_description}")
    else:
        if typ_key in GENERATORS:
            if typ_key == "saddle_span":
                fig = generate_saddle_span(params, st.session_state.materials, st.session_state.engineering_annotations)
            else:
                fig = GENERATORS[typ_key](params)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    
    # ---- STRUCTURAL CALCULATIONS ----
    if typ_key == "saddle_span":
        st.subheader("📊 Preliminary Structural Checks")
        m = st.session_state.materials
        span = params.get("B", 10.0)
        laa = params.get("LAA", 15.0)
        rise = params.get("A", 6.0)
        membrane_area = span * laa * 1.1
        steel_weight_kg = calculate_steel_weight(m.get("steel_grade", "S355"), m.get("section_type", "CHS"), m.get("section_size", "CHS 150x6"), span * 2)
        fabric_weight_kg = calculate_fabric_weight(m.get("fabric_type", "PVC-coated Polyester"), m.get("fabric_thickness", 0.8), membrane_area)
        total_weight_kg = steel_weight_kg + fabric_weight_kg
        total_weight_kn = total_weight_kg / 100
        wind_load = calculate_wind_load(m.get("wind_speed", 40), membrane_area)
        tie_down_force = calculate_tie_down_force(wind_load, total_weight_kn, 4, m.get("tie_down_vertical_angle", 45))
        rope_breaking_load = {6: 20, 8: 35, 10: 55, 12: 80, 14: 105, 16: 140, 20: 220}
        rope_capacity = rope_breaking_load.get(m.get("wire_rope_diameter", 10), 55)
        rope_check = tie_down_force < rope_capacity / 1.5
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Self-Weight", f"{total_weight_kn:.1f} kN")
            st.metric("Membrane Area", f"{membrane_area:.1f} m²")
        with col2:
            st.metric("Wind Load", f"{wind_load:.1f} kN")
            st.metric("Tie-Down Force/Anchor", f"{tie_down_force:.1f} kN")
        with col3:
            st.metric("Wire Rope Capacity", f"{rope_capacity:.1f} kN")
            st.metric("✅ Rope Check", "✅ PASS" if rope_check else "❌ FAIL", delta="Required < Capacity" if rope_check else "Required > Capacity", delta_color="normal" if rope_check else "inverse")
        if not rope_check:
            st.error(f"⚠️ Tie-down force ({tie_down_force:.1f} kN) exceeds wire rope capacity ({rope_capacity:.1f} kN). Please increase rope diameter or add more anchors.")
        else:
            st.success(f"✅ All preliminary checks passed. Structure is stable under wind loads.")
    
    st.subheader("📤 Export & Proposal")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        if st.button("📥 Export Package (Image + Data)", use_container_width=True):
            st.session_state.show_export = not st.session_state.show_export
            st.rerun()
    with col_e2:
        if st.button("📐 Proposal Drawings", use_container_width=True, type="primary"):
            st.session_state.show_proposal = True
            st.session_state.show_export = True
            st.rerun()
    
    if st.session_state.show_export:
        render_export_section()
    
    if st.session_state.show_proposal:
        render_proposal_drawings()
    
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
        if st.session_state.comments:
            st.write("---")
            st.write(f"**💬 Comments:** {st.session_state.comments}")
    
    if st.session_state.locked:
        if st.button("🔓 Unlock Design", use_container_width=True):
            st.session_state.locked = False
            st.session_state.mode = "design"
            st.session_state.design_phase = "review"
            save_cache()
            st.rerun()

st.caption("SDS Platform v3.0 | New Tie-Down System (1/4 Points + Dual Angles) | Fixed Syntax")
save_cache()
