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
if "engineering_annotations" not in st.session_state:
    st.session_state.engineering_annotations = {
        "show_wind": True,
        "show_tie_down": True,
        "show_load_path": True,
        "show_bracing": True
    }
if "design_phase" not in st.session_state:
    st.session_state.design_phase = "understand"
if "comments" not in st.session_state:
    st.session_state.comments = ""
if "user_notes" not in st.session_state:
    st.session_state.user_notes = ""
if "show_project_browser" not in st.session_state:
    st.session_state.show_project_browser = False
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False
if "custom_members" not in st.session_state:
    st.session_state.custom_members = []
if "tie_down_attachments" not in st.session_state:
    st.session_state.tie_down_attachments = []

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
        "bracing_preset": "two_quarter",
        "custom_bracing_positions": [],
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
        "engineering_annotations": st.session_state.engineering_annotations,
        "design_phase": st.session_state.design_phase,
        "comments": st.session_state.comments,
        "user_notes": st.session_state.user_notes,
        "materials": st.session_state.materials,
        "custom_members": st.session_state.custom_members,
        "tie_down_attachments": st.session_state.tie_down_attachments
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
            typ = data.get("typology")
            if typ is None:
                params = data.get("params", {})
                if "A" in params and "B" in params and "LAA" in params:
                    typ = "saddle_span"
                elif "span_width" in params and "ridge_height" in params:
                    typ = "clear_span_tent"
                elif "mast_height" in params:
                    typ = "tensile_membrane"
                elif "eave_height" in params:
                    typ = "portal_frame"
                else:
                    typ = "custom"
            st.session_state.typology = typ
            st.session_state.params = data.get("params", {})
            st.session_state.qa_answers = data.get("qa_answers", {})
            st.session_state.locked = data.get("locked", False)
            st.session_state.engineering_annotations = data.get("engineering_annotations", {
                "show_wind": True,
                "show_tie_down": True,
                "show_load_path": True,
                "show_bracing": True
            })
            st.session_state.design_phase = data.get("design_phase", "understand")
            st.session_state.comments = data.get("comments", "")
            st.session_state.user_notes = data.get("user_notes", "")
            st.session_state.materials = data.get("materials", {
                "steel_grade": "S355",
                "section_type": "Circular Hollow Section (CHS)",
                "section_size": "CHS 150x6",
                "fabric_type": "PVC-coated Polyester",
                "fabric_thickness": 0.8,
                "prestress": 3.0,
                "wire_rope_type": "Galvanized Steel (6x19)",
                "wire_rope_diameter": 10,
                "bracing_preset": "two_quarter",
                "custom_bracing_positions": [],
                "wind_speed": 40,
                "snow_load": 0.5,
                "live_load": 0.5,
                "tie_down_vertical_angle": 45,
                "tie_down_horizontal_spread": 25
            })
            st.session_state.custom_members = data.get("custom_members", [])
            st.session_state.tie_down_attachments = data.get("tie_down_attachments", [])
            st.session_state.show_registration = False
            st.session_state.show_project_browser = False
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
    st.session_state.qa_answers = {}
    st.session_state.locked = False
    st.session_state.design_phase = "understand"
    st.session_state.comments = ""
    st.session_state.user_notes = ""
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    st.session_state.custom_members = []
    st.session_state.tie_down_attachments = []
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
    st.session_state.qa_answers = {}
    st.session_state.locked = False
    st.session_state.design_phase = "understand"
    st.session_state.comments = ""
    st.session_state.user_notes = ""
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    st.session_state.custom_members = []
    st.session_state.tie_down_attachments = []
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
        "engineering_annotations": st.session_state.engineering_annotations,
        "design_phase": st.session_state.design_phase,
        "comments": st.session_state.comments,
        "user_notes": st.session_state.user_notes,
        "materials": st.session_state.materials,
        "custom_members": st.session_state.custom_members,
        "tie_down_attachments": st.session_state.tie_down_attachments
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
    typ = cached.get("typology")
    if typ is None:
        params = cached.get("params", {})
        if "A" in params and "B" in params and "LAA" in params:
            typ = "saddle_span"
        elif "span_width" in params and "ridge_height" in params:
            typ = "clear_span_tent"
        elif "mast_height" in params:
            typ = "tensile_membrane"
        elif "eave_height" in params:
            typ = "portal_frame"
        else:
            typ = "custom"
    st.session_state.typology = typ
    st.session_state.params = cached.get("params", {})
    st.session_state.qa_answers = cached.get("qa_answers", {})
    st.session_state.locked = cached.get("locked", False)
    st.session_state.engineering_annotations = cached.get("engineering_annotations", {
        "show_wind": True,
        "show_tie_down": True,
        "show_load_path": True,
        "show_bracing": True
    })
    st.session_state.design_phase = cached.get("design_phase", "understand")
    st.session_state.comments = cached.get("comments", "")
    st.session_state.user_notes = cached.get("user_notes", "")
    st.session_state.materials = cached.get("materials", {
        "steel_grade": "S355",
        "section_type": "Circular Hollow Section (CHS)",
        "section_size": "CHS 150x6",
        "fabric_type": "PVC-coated Polyester",
        "fabric_thickness": 0.8,
        "prestress": 3.0,
        "wire_rope_type": "Galvanized Steel (6x19)",
        "wire_rope_diameter": 10,
        "bracing_preset": "two_quarter",
        "custom_bracing_positions": [],
        "wind_speed": 40,
        "snow_load": 0.5,
        "live_load": 0.5,
        "tie_down_vertical_angle": 45,
        "tie_down_horizontal_spread": 25
    })
    st.session_state.custom_members = cached.get("custom_members", [])
    st.session_state.tie_down_attachments = cached.get("tie_down_attachments", [])

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
# ENGINEERING-DRIVEN BRACING & TIE-DOWN POSITIONS
# ============================================================

def get_bracing_preset(span, preset, num_custom_points=None):
    if preset == "two_quarter":
        return [-span/4, span/4]
    elif preset == "three_quarter":
        return [-span/4, 0.0, span/4]
    elif preset == "third":
        return [-span/3, span/3]
    elif preset == "support_mid":
        return [-span/2, 0.0, span/2]
    elif preset == "fifths":
        return [-2*span/5, -span/5, 0.0, span/5, 2*span/5]
    elif preset == "custom" and num_custom_points:
        if isinstance(num_custom_points, list):
            return num_custom_points
        else:
            if num_custom_points == 1:
                return [0.0]
            else:
                spacing = span / (num_custom_points + 1)
                return [(-span/2) + spacing * (i+1) for i in range(num_custom_points)]
    else:
        return [-span/4, 0.0, span/4]

def get_preset_description(preset):
    descriptions = {
        "two_quarter": "🔄 Two Quarter Points (1/4 and 3/4) – Two tie‑downs per beam, placed at quarter points. Best for general uplift control without mid‑span tie‑down.",
        "three_quarter": "🏗️ Three Quarter Points (1/4, 1/2, 3/4) – Three per beam, includes mid‑span. Recommended when uplift is highest at mid‑span.",
        "third": "📐 Third Points (1/3, 2/3) – Two per beam, for longer spans where shear is critical.",
        "support_mid": "🏛️ Supports + Mid-Span – Three per beam, for structures with concentrated loads at mid‑span.",
        "fifths": "📏 Fifths (1/5, 2/5, 3/5, 4/5) – Four per beam, fine‑grained control for large spans.",
        "custom": "🛠️ Custom Positions – Define exact X‑coordinates for advanced users."
    }
    return descriptions.get(preset, "Engineering-preset bracing positions.")

# ============================================================
# 3D GENERATORS – TIGHTER MEMBRANE, RADIAL ANCHORS, SMALL MARKERS, ASPECT RATIO 2.5:1.5:1.0
# ============================================================

def generate_tie_down_anchors_at_positions(span, laa, height, x_positions, vertical_angle_deg, horizontal_spread_deg):
    vertical_rad = np.radians(vertical_angle_deg)
    distance = height * np.tan(vertical_rad)
    anchors = []
    beam_ys = [-laa/2, laa/2]
    for beam_idx, beam_y in enumerate(beam_ys):
        for beam_x in x_positions:
            if abs(beam_x) < 1e-6 and abs(beam_y) < 1e-6:
                vec = np.array([1.0, 0.0])
            else:
                vec = np.array([beam_x, beam_y])
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            else:
                vec = np.array([1.0, 0.0])
            anchor_x = beam_x + distance * vec[0]
            anchor_y = beam_y + distance * vec[1]
            anchor_z = 0
            anchors.append({
                "beam_x": beam_x,
                "beam_y": beam_y,
                "anchor_x": anchor_x,
                "anchor_y": anchor_y,
                "anchor_z": anchor_z,
                "beam": beam_idx + 1,
                "position": f"x={beam_x:.1f}m"
            })
    return anchors

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

    # Membrane surface – tighter saddle (factor 0.1)
    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, x_pos in enumerate(x):
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = z_beam[i]
        for j, v_val in enumerate(np.linspace(0, 1, num_points)):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            saddle_factor = 1 - 0.1 * (1 - (2 * v_val - 1)**2)
            z_pos = z_at_x * saddle_factor
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1', line=dict(color='#FF6B6B', width=8)))
    fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2', line=dict(color='#FF6B6B', width=8)))
    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, 
                             colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
                             opacity=0.6, showscale=False))

    fig.add_trace(go.Scatter3d(x=[0], y=[y1[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 1', marker=dict(color='#FFD93D', size=6, symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[0], y=[y2[num_points//2]], z=[
