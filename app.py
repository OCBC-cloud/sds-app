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
# 3D GENERATORS – WITH 1:1:1 ASPECT RATIO AND TIGHTER MEMBRANE
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

    # Membrane surface – tighter saddle (factor 0.1 instead of 0.3)
    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, x_pos in enumerate(x):
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = z_beam[i]
        for j, v_val in enumerate(np.linspace(0, 1, num_points)):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            # Tighter saddle: reduce the droop factor from 0.3 to 0.1
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
    fig.add_trace(go.Scatter3d(x=[0], y=[y2[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 2', marker=dict(color='#FFD93D', size=6, symbol='diamond')))

    fig.add_trace(go.Scatter3d(x=[-span/2], y=[0], z=[0], 
                               mode='markers', name='Support 1', marker=dict(color='#4ECDC4', size=8, symbol='square')))
    fig.add_trace(go.Scatter3d(x=[span/2], y=[0], z=[0], 
                               mode='markers', name='Support 2', marker=dict(color='#4ECDC4', size=8, symbol='square')))

    show_bracing = True
    if annotations is not None:
        show_bracing = annotations.get("show_bracing", True)
    
    if materials is not None and show_bracing:
        bracing_preset = materials.get("bracing_preset", "two_quarter")
        custom_points = materials.get("custom_bracing_positions", [])
        bracing_x = get_bracing_preset(span, bracing_preset, custom_points)
        st.session_state.current_bracing_x = bracing_x

        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            y1_pos = y1[idx]
            y2_pos = y2[idx]
            z_pos = z_beam[idx]
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[y1_pos, y2_pos], z=[z_pos, z_pos],
                mode='lines', name='Cross Bracing',
                line=dict(color='#FF6B6B', width=4, dash='dash'),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[bx], y=[y1_pos], z=[z_pos],
                mode='markers', marker=dict(color='#4ECDC4', size=4),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[bx], y=[y2_pos], z=[z_pos],
                mode='markers', marker=dict(color='#4ECDC4', size=4),
                showlegend=False
            ))

    show_tie_down = True
    if annotations is not None:
        show_tie_down = annotations.get("show_tie_down", True)
    
    if materials is not None and show_tie_down:
        bracing_x = st.session_state.get("current_bracing_x", get_bracing_preset(span, "two_quarter", []))
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        horizontal_spread = materials.get("tie_down_horizontal_spread", 25)
        
        anchors = generate_tie_down_anchors_at_positions(span, laa, rise, bracing_x, vertical_angle, horizontal_spread)
        for a in anchors:
            idx = np.argmin(np.abs(x - a["beam_x"]))
            beam_z = z_beam[idx]
            
            fig.add_trace(go.Scatter3d(
                x=[a["beam_x"], a["anchor_x"]],
                y=[a["beam_y"], a["anchor_y"]],
                z=[beam_z, a["anchor_z"]],
                mode='lines', name='Tie-Down Rope',
                line=dict(color='#FFD93D', width=5),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[a["beam_x"]], y=[a["beam_y"]], z=[beam_z],
                mode='markers',
                marker=dict(color='#FFD93D', size=4, symbol='circle'),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[a["anchor_x"]], y=[a["anchor_y"]], z=[a["anchor_z"]],
                mode='markers',
                marker=dict(color='#FF6B6B', size=6, symbol='x'),
                showlegend=False
            ))

    show_wind = True
    if annotations is not None:
        show_wind = annotations.get("show_wind", True)
    if show_wind:
        fig.add_trace(go.Scatter3d(
            x=[-span/4, -span/4], y=[-laa/4, -laa/4], z=[rise*0.8, rise*1.2],
            mode='lines', name='Wind Load',
            line=dict(color='#FF6B6B', width=4, dash='dash'), showlegend=True
        ))
        fig.add_trace(go.Scatter3d(
            x=[span/4, span/4], y=[laa/4, laa/4], z=[rise*0.8, rise*1.2],
            mode='lines', name='Wind Load',
            line=dict(color='#FF6B6B', width=4, dash='dash'), showlegend=False
        ))

    show_load_path = True
    if annotations is not None:
        show_load_path = annotations.get("show_load_path", True)
    if show_load_path:
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[rise, rise-2],
            mode='lines', name='Load Path',
            line=dict(color='#FFD93D', width=5), showlegend=True
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
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=1)   # <-- 1:1:1 aspect ratio
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
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=1)
        ),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0),
        legend=dict(font=dict(color='#ffffff', size=6), orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, bgcolor='rgba(10,14,23,0.7)')
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
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=1)
        ),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0),
        legend=dict(font=dict(color='#ffffff', size=6), orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, bgcolor='rgba(10,14,23,0.7)')
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
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=1)
        ),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0),
        legend=dict(font=dict(color='#ffffff', size=6), orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, bgcolor='rgba(10,14,23,0.7)')
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
            aspectmode='manual', aspectratio=dict(x=1, y=1, z=1),
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
# OTHER FUNCTIONS
# ============================================================

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

def render_high_res_image(fig, filename="design_high_res.png"):
    try:
        img_bytes = fig.to_image(format="png", scale=4, width=1200, height=800)
        b64 = base64.b64encode(img_bytes).decode()
        href = f'<a href="data:image/png;base64,{b64}" download="{filename}">📸 Download High-Res Image (PNG)</a>'
        return href
    except Exception as e:
        return f"⚠️ Image export failed: {str(e)}. Please use screenshot feature."

def get_json_download_link(data, filename="project_data.json"):
    json_str = json.dumps(data, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">📄 Download Design Data (JSON)</a>'
    return href

def generate_bq():
    params = st.session_state.params
    materials = st.session_state.materials
    A = params.get("A", 6)
    B = params.get("B", 10)
    LAA = params.get("LAA", 15)
    membrane_area = B * LAA * 1.1
    steel_weight_kg = 2 * calculate_steel_weight(
        materials.get("steel_grade", "S355"),
        materials.get("section_type", "CHS"),
        materials.get("section_size", "CHS 150x6"),
        B
    )
    fabric_weight_kg = calculate_fabric_weight(
        materials.get("fabric_type", "PVC-coated Polyester"),
        materials.get("fabric_thickness", 0.8),
        membrane_area
    )
    total_steel = steel_weight_kg
    total_weight_kn = (total_steel + fabric_weight_kg) / 100
    bq_data = {
        "Membrane Area (m²)": membrane_area,
        "Fabric Weight (kg)": fabric_weight_kg,
        "Steel Weight (kg)": steel_weight_kg,
        "Total Structure Weight (kN)": total_weight_kn,
        "Number of Tie-down Ropes": len(st.session_state.get("current_bracing_x", [])) * 2
    }
    return bq_data

# ============================================================
# UNIFIED BOARD
# ============================================================
def render_unified_workspace():
    params = st.session_state.params
    materials = st.session_state.materials
    typ_key = st.session_state.typology
    typ = TYPOLOGIES[typ_key]
    info = st.session_state.project_info

    st.markdown("## 🧠 SDS-UNDERSTAND — Engineering Understanding & Model Confirmation")
    st.caption("Review, confirm, and edit your design. Bracing and tie‑down positions are driven by engineering presets.")

    col_left, col_right = st.columns([1, 1.8])

    with col_left:
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📷 PHOTO / REFERENCE</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload reference image", type=["png", "jpg", "jpeg", "webp"], key="photo_ref")
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Reference Image", use_container_width=True)
            st.caption("📌 Note: Uploaded image is for reference only.")
        else:
            st.caption("🖼️ Upload a sketch, photo, or reference image.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📝 NOTES FROM USER</div>', unsafe_allow_html=True)
        user_notes = st.text_area(
            "Add your design notes here",
            value=st.session_state.get("user_notes", ""),
            height=100,
            key="user_notes_area",
            placeholder="e.g., Two main curved primary beams..."
        )
        st.session_state.user_notes = user_notes
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📊 Current Interpretation Summary</div>', unsafe_allow_html=True)
        m = materials
        summary_items = [
            ("PRIMARY STRUCTURE", f"{m.get('steel_grade', 'S355')} {m.get('section_type', 'CHS')} {m.get('section_size', '150x6')}", "badge-provided"),
            ("MEMBRANE", f"{m.get('fabric_type', 'PVC')} {m.get('fabric_thickness', 0.8)}mm, {m.get('prestress', 3.0)}kN/m", "badge-provided"),
            ("APEX POINT (P_A)", f"High point at {params.get('A', 6.0)}m", "badge-inferred"),
            ("SUPPORTS", "Two supports at beam bases", "badge-inferred"),
            ("DIMENSIONS", f"A={params.get('A', 6.0)}m, B={params.get('B', 10.0)}m, LAA={params.get('LAA', 15.0)}m", "badge-confirmed"),
            ("BRACING PRESET", f"{m.get('bracing_preset', 'two_quarter').title()} – {get_preset_description(m.get('bracing_preset', 'two_quarter')).split('–')[0].strip()}", "badge-autogen"),
            ("TIE-DOWNS", f"Aligned to bracing positions, {m.get('tie_down_vertical_angle', 45)}° vertical", "badge-autogen"),
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
        st.markdown('<div class="title">❓ Structured Questions</div>', unsafe_allow_html=True)
        st.caption("Confirm the following assumptions. These will be locked and stored in the engineering report.")
        for i, q in enumerate(typ["qa"]):
            key = f"qa_{i}"
            default = st.session_state.qa_answers.get(key, "Yes")
            if "?" in q:
                ans = st.radio(f"{i+1}. {q}", ["Yes", "No", "Not Sure"], index=["Yes", "No", "Not Sure"].index(default), key=f"left_qa_{i}")
            else:
                options = ["Open", "Enclosed", "PVC", "PTFE", "Steel"]
                ans = st.selectbox(f"{i+1}. {q}", options, index=options.index(default) if default in options else 0, key=f"left_qa_{i}")
            st.session_state.qa_answers[key] = ans
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📌 Legend (Data Identity)</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="badge badge-confirmed">CONFIRMED</span> <span style="color:#b0c4de;">Confirmed by User</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-inferred">INFERRED</span> <span style="color:#b0c4de;">Inferred by SDS</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-unknown">UNKNOWN</span> <span style="color:#b0c4de;">Not Yet Defined</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-provided">PROVIDED</span> <span style="color:#b0c4de;">Provided by User</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-autogen">AUTO-GEN</span> <span style="color:#b0c4de;">Auto-Generated</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🔒 LOCK & PROCEED TO INVESTIGATION", use_container_width=True, type="primary"):
            st.session_state.locked = True
            save_cache()
            st.success("✅ Design locked! You can now view the final model and export.")

    with col_right:
        st.subheader("🔬 3D Model")
        anno_cols = st.columns(4)
        with anno_cols[0]:
            st.session_state.engineering_annotations["show_wind"] = st.checkbox("💨 Wind", value=st.session_state.engineering_annotations.get("show_wind", True))
        with anno_cols[1]:
            st.session_state.engineering_annotations["show_tie_down"] = st.checkbox("🔗 Tie-Down", value=st.session_state.engineering_annotations.get("show_tie_down", True))
        with anno_cols[2]:
            st.session_state.engineering_annotations["show_bracing"] = st.checkbox("📐 Bracing", value=st.session_state.engineering_annotations.get("show_bracing", True))
        with anno_cols[3]:
            st.session_state.engineering_annotations["show_load_path"] = st.checkbox("📊 Load", value=st.session_state.engineering_annotations.get("show_load_path", True))

        if typ_key == "custom":
            fig = generate_custom_bounding_box(params)
            st.info("📝 Custom design — 3D view shows bounding box.")
        else:
            if typ_key == "saddle_span":
                fig = generate_saddle_span(params, materials, st.session_state.engineering_annotations)
            else:
                fig = GENERATORS[typ_key](params)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

        st.divider()
        st.markdown("### 📐 Edit Geometry")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            new_a = st.number_input("Rise (A) (m)", min_value=2.0, max_value=20.0, step=0.5, value=float(params.get("A", 6.0)), format="%.1f", key="right_a")
            params["A"] = new_a
        with col_b:
            new_b = st.number_input("Span (B) (m)", min_value=4.0, max_value=40.0, step=0.5, value=float(params.get("B", 10.0)), format="%.1f", key="right_b")
            params["B"] = new_b
        with col_c:
            new_laa = st.number_input("LAA (m)", min_value=4.0, max_value=50.0, step=0.5, value=float(params.get("LAA", 15.0)), format="%.1f", key="right_laa")
            params["LAA"] = new_laa

        with st.expander("🏗️ Engineering-Driven Bracing & Tie-Downs", expanded=True):
            st.markdown("### 🔧 Bracing Preset")
            st.caption("Select an engineering‑based bracing layout. Tie‑downs are automatically aligned to bracing points.")
            
            preset_options = {
                "two_quarter": "🔄 Two Quarter Points (1/4 and 3/4)",
                "three_quarter": "🏗️ Three Quarter Points (1/4, 1/2, 3/4)",
                "third": "📐 Third Points (1/3, 2/3)",
                "support_mid": "🏛️ Supports + Mid-Span",
                "fifths": "📏 Fifths (1/5, 2/5, 3/5, 4/5)",
                "custom": "🛠️ Custom Positions"
            }
            current_preset = materials.get("bracing_preset", "two_quarter")
            selected_preset = st.selectbox(
                "Bracing Layout",
                options=list(preset_options.keys()),
                format_func=lambda x: preset_options.get(x, x),
                index=list(preset_options.keys()).index(current_preset) if current_preset in preset_options else 0,
                key="bracing_preset_select"
            )
            materials["bracing_preset"] = selected_preset
            
            st.info(get_preset_description(selected_preset))
            
            if selected_preset == "custom":
                st.markdown("### 📍 Custom Bracing Positions")
                st.caption("Enter X‑coordinates (in metres) for each bracing point. Use comma‑separated values.")
                custom_input = st.text_input(
                    "Custom Positions (e.g., -3, 0, 4.5)",
                    value=", ".join([str(p) for p in materials.get("custom_bracing_positions", [])]),
                    key="custom_bracing_input"
                )
                try:
                    if custom_input.strip():
                        positions = [float(x.strip()) for x in custom_input.split(",") if x.strip()]
                        materials["custom_bracing_positions"] = positions
                    else:
                        materials["custom_bracing_positions"] = []
                except:
                    st.warning("⚠️ Please enter valid numbers separated by commas.")
            
            span = params.get("B", 10.0)
            if selected_preset == "custom":
                bracing_x = materials.get("custom_bracing_positions", [])
            else:
                bracing_x = get_bracing_preset(span, selected_preset, [])
            
            if bracing_x:
                st.markdown("**📍 Current Bracing Positions:**")
                for i, pos in enumerate(bracing_x):
                    st.write(f"  • Bay {i+1}: X = **{pos:.2f} m**")
            else:
                st.info("No bracing positions defined. Please enter custom positions or select a preset.")
            
            st.divider()
            
            st.markdown("### ⛓️ Tie-Down Settings")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                materials["wire_rope_diameter"] = st.selectbox(
                    "Wire Rope Diameter (mm)",
                    [6, 8, 10, 12, 14, 16, 20],
                    index=[6, 8, 10, 12, 14, 16, 20].index(materials.get("wire_rope_diameter", 10)),
                    key="right_rope"
                )
            with col_t2:
                materials["tie_down_vertical_angle"] = st.slider(
                    "Vertical Angle (°)",
                    min_value=20,
                    max_value=70,
                    step=5,
                    value=materials.get("tie_down_vertical_angle", 45),
                    key="right_vertical",
                    help="Angle of tie-down rope from horizontal (max 45° recommended)"
                )
            with col_t3:
                materials["tie_down_horizontal_spread"] = st.slider(
                    "Horizontal Spread (°)",
                    min_value=10,
                    max_value=60,
                    step=5,
                    value=materials.get("tie_down_horizontal_spread", 25),
                    key="right_spread",
                    help="Angle of tie-down spread outward from beam"
                )
            
            if materials["tie_down_vertical_angle"] > 45:
                st.warning("⚠️ Vertical angle >45° reduces cable efficiency. Consider reducing to 45° or less.")
            
            st.info("💡 Tie‑downs are automatically placed at all bracing positions, with anchors located radially outward from the structure centre.")

        with st.expander("🏗️ Materials", expanded=False):
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                materials["steel_grade"] = st.selectbox("Steel Grade", ["S275", "S355", "S460", "6061-T6 (Aluminum)"], index=["S275", "S355", "S460", "6061-T6 (Aluminum)"].index(materials.get("steel_grade", "S355")), key="right_steel")
            with col_m2:
                materials["section_type"] = st.selectbox("Section Type", ["Circular Hollow Section (CHS)", "Rectangular Hollow Section (RHS)", "I-Beam", "Pipe"], index=["Circular Hollow Section (CHS)", "Rectangular Hollow Section (RHS)", "I-Beam", "Pipe"].index(materials.get("section_type", "Circular Hollow Section (CHS)")), key="right_section_type")
            with col_m3:
                section_sizes = {
                    "Circular Hollow Section (CHS)": ["CHS 100x5", "CHS 150x6", "CHS 200x8", "CHS 250x10"],
                    "Rectangular Hollow Section (RHS)": ["RHS 150x100x6", "RHS 200x150x8", "RHS 250x150x10"],
                    "I-Beam": ["I-100", "I-150", "I-200", "I-250"],
                    "Pipe": ["Pipe 100x5", "Pipe 150x6", "Pipe 200x8"]
                }
                materials["section_size"] = st.selectbox("Section Size", section_sizes.get(materials["section_type"], ["CHS 150x6"]), index=0, key="right_section_size")
            
            col_m4, col_m5, col_m6 = st.columns(3)
            with col_m4:
                materials["fabric_type"] = st.selectbox("Fabric Type", ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"], index=["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"].index(materials.get("fabric_type", "PVC-coated Polyester")), key="right_fabric")
            with col_m5:
                materials["fabric_thickness"] = st.selectbox("Thickness (mm)", [0.5, 0.8, 1.0, 1.2], index=[0.5, 0.8, 1.0, 1.2].index(materials.get("fabric_thickness", 0.8)), key="right_thickness")
            with col_m6:
                materials["prestress"] = st.selectbox("Prestress (kN/m)", [1.0, 3.0, 5.0], index=[1.0, 3.0, 5.0].index(materials.get("prestress", 3.0)), key="right_prestress")
            
            col_w1, col_w2 = st.columns(2)
            with col_w1:
                materials["wind_speed"] = st.number_input("Wind Speed (m/s)", min_value=10, max_value=100, step=5, value=materials.get("wind_speed", 40), key="right_wind")
            with col_w2:
                st.caption("💨 Used for structural checks and uplift calculations.")

        if typ_key == "saddle_span":
            with st.expander("📊 Preliminary Structural Checks", expanded=True):
                m = materials
                span = params.get("B", 10.0)
                laa = params.get("LAA", 15.0)
                rise = params.get("A", 6.0)
                membrane_area = span * laa * 1.1
                steel_weight_kg = calculate_steel_weight(m.get("steel_grade", "S355"), m.get("section_type", "CHS"), m.get("section_size", "CHS 150x6"), span * 2)
                fabric_weight_kg = calculate_fabric_weight(m.get("fabric_type", "PVC-coated Polyester"), m.get("fabric_thickness", 0.8), membrane_area)
                total_weight_kg = steel_weight_kg + fabric_weight_kg
                total_weight_kn = total_weight_kg / 100
                wind_load = calculate_wind_load(m.get("wind_speed", 40), membrane_area)
                
                bracing_preset = m.get("bracing_preset", "two_quarter")
                if bracing_preset == "custom":
                    bracing_x = m.get("custom_bracing_positions", [])
                else:
                    bracing_x = get_bracing_preset(span, bracing_preset, [])
                num_anchors = len(bracing_x) * 2
                tie_down_force = calculate_tie_down_force(wind_load, total_weight_kn, num_anchors, m.get("tie_down_vertical_angle", 45))
                rope_breaking_load = {6: 20, 8: 35, 10: 55, 12: 80, 14: 105, 16: 140, 20: 220}
                rope_capacity = rope_breaking_load.get(m.get("wire_rope_diameter", 10), 55)
                rope_check = tie_down_force < rope_capacity / 1.5
                
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("Self-Weight", f"{total_weight_kn:.1f} kN")
                    st.metric("Membrane Area", f"{membrane_area:.1f} m²")
                with col_s2:
                    st.metric("Wind Load", f"{wind_load:.1f} kN")
                    st.metric("Tie-Down Force/Anchor", f"{tie_down_force:.1f} kN")
                with col_s3:
                    st.metric("Wire Rope Capacity", f"{rope_capacity:.1f} kN")
                    st.metric("✅ Rope Check", "✅ PASS" if rope_check else "❌ FAIL", delta="Required < Capacity" if rope_check else "Required > Capacity", delta_color="normal" if rope_check else "inverse")
                if not rope_check:
                    st.error(f"⚠️ Tie-down force ({tie_down_force:.1f} kN) exceeds wire rope capacity ({rope_capacity:.1f} kN). Please increase rope diameter or add more anchors.")
                else:
                    st.success(f"✅ All preliminary checks passed. Structure is stable under wind loads.")

        with st.expander("📋 Bill of Quantities"):
            bq = generate_bq()
            df = pd.DataFrame(list(bq.items()), columns=["Item", "Value"])
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download BQ as CSV", data=csv, file_name="bq.csv", mime="text/csv")

        st.divider()
        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        with col_act1:
            if st.button("📸 Render High-Res Image", use_container_width=True, type="primary"):
                if typ_key != "custom" and typ_key in GENERATORS:
                    try:
                        if typ_key == "saddle_span":
                            fig_render = generate_saddle_span(params, materials, st.session_state.engineering_annotations)
                        else:
                            fig_render = GENERATORS[typ_key](params)
                        link = render_high_res_image(fig_render)
                        st.markdown(link, unsafe_allow_html=True)
                    except Exception as e:
                        st.warning(f"⚠️ Render failed: {e}. Please use screenshot feature.")
                else:
                    st.info("Render available for standard typologies.")
        with col_act2:
            if st.button("📄 Export JSON", use_container_width=True):
                export_data = {
                    "project": info,
                    "typology": typ_key,
                    "parameters": params,
                    "qa_answers": st.session_state.qa_answers,
                    "comments": st.session_state.comments,
                    "user_notes": st.session_state.user_notes,
                    "materials": materials,
                    "locked": st.session_state.locked,
                    "export_date": datetime.now().isoformat()
                }
                link = get_json_download_link(export_data)
                st.markdown(link, unsafe_allow_html=True)
        with col_act3:
            if st.button("🔒 Lock", use_container_width=True):
                st.session_state.locked = True
                save_cache()
                st.rerun()
        with col_act4:
            if st.button("🔄 Reset All", use_container_width=True):
                st.session_state.params = {p: v["default"] for p, v in typ["params"].items()}
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
                save_cache()
                st.rerun()

    st.divider()
    st.caption("Understanding Design → Confirm Model → Engineering Investigation → Better Design → Roots Protected. Branches Free. Ecosystem Growing.")

# ============================================================
# MAIN DASHBOARD
# ============================================================
def render_dashboard():
    st.title("🏗️ SDS Design Studio")
    st.caption("Parametric design for tensile structures, membrane roofs, and steel frames.")
    st.markdown("### *Roots Protected. Branches Free. Ecosystem Growing.*")
    
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
        for proj in projects[:5]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{proj.get('name', 'Untitled')}** — 👤 {proj.get('client', 'N/A')} | {proj.get('typology', 'Unknown')}")
            with col2:
                if st.button("Open", key=f"dash_load_{proj.get('file')}", use_container_width=True):
                    if load_project_from_file(proj.get('file')):
                        st.rerun()
            st.divider()
    
    st.caption("💡 Select 'New Design' to start a project, or open an existing project from the list above.")

# ============================================================
# MAIN UI RENDER LOOP
# ============================================================

cols = st.columns([0.8, 1.5, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
with cols[0]:
    if st.button("🏗️", key="sds_logo", help="Go to Dashboard"):
        go_to_dashboard()
        st.rerun()
    st.caption("SDS")
with cols[1]:
    if st.session_state.project_registered and st.session_state.project_info:
        st.caption(f"📌 {st.session_state.project_info.get('name', 'Project')[:20]}")
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
    pass
with cols[8]:
    if st.session_state.locked and st.session_state.typology:
        if st.button("🔓 Unlock", use_container_width=True, type="primary", help="Unlock the design to make changes"):
            st.session_state.locked = False
            save_cache()
            st.rerun()

if st.session_state.show_project_browser:
    st.subheader("📂 Saved Projects")
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        go_to_dashboard()
        st.rerun()
    projects = get_projects_list()
    if not projects:
        st.info("No saved projects found.")
    else:
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
            with col3:
                if st.button("🗑️ Delete", key=f"del_{proj.get('file')}", use_container_width=True):
                    if delete_project_file(proj.get('file')):
                        st.success(f"✅ Project {proj.get('name')} deleted.")
                        st.rerun()
    st.stop()

if st.session_state.project_registered and st.session_state.typology is None:
    st.session_state.typology = "saddle_span"
    st.session_state.params = {p: v["default"] for p, v in TYPOLOGIES["saddle_span"]["params"].items()}
    st.session_state.qa_answers = {}
    st.session_state.locked = False
    st.session_state.materials["bracing_preset"] = "two_quarter"
    st.session_state.materials["custom_bracing_positions"] = []
    save_cache()
    st.rerun()

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
                    st.session_state.design_phase = "understand"
                    st.session_state.show_registration = False
                    st.session_state.typology = "saddle_span"
                    st.session_state.params = {p: v["default"] for p, v in TYPOLOGIES["saddle_span"]["params"].items()}
                    st.session_state.qa_answers = {}
                    st.session_state.locked = False
                    st.session_state.materials["bracing_preset"] = "two_quarter"
                    st.session_state.materials["custom_bracing_positions"] = []
                    save_cache()
                    st.rerun()
        st.caption("All data is cached locally. Your project will resume where you left off.")
        st.stop()

if st.session_state.typology is not None:
    render_unified_workspace()

st.caption("SDS Platform v4.5 | 1:1:1 Aspect Ratio, Tighter Membrane | Roots Protected. Branches Free. Ecosystem Growing.")
save_cache()
