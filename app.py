import streamlit as st
import json
import os
import numpy as np
from datetime import datetime
import random
import string
import base64
import glob
import plotly.graph_objects as go
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
# CUSTOM DARK MODE CSS (same as before)
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
    st.session_state.design_phase = "understand"
if "comments" not in st.session_state:
    st.session_state.comments = ""
if "user_notes" not in st.session_state:
    st.session_state.user_notes = ""
if "show_project_browser" not in st.session_state:
    st.session_state.show_project_browser = False
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False
if "show_export" not in st.session_state:
    st.session_state.show_export = False
if "show_proposal" not in st.session_state:
    st.session_state.show_proposal = False

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

if "custom_members" not in st.session_state:
    st.session_state.custom_members = []
if "tie_down_attachments" not in st.session_state:
    st.session_state.tie_down_attachments = []
if "bracing_points" not in st.session_state:
    st.session_state.bracing_points = []

# ============================================================
# CACHE HANDLER (same as before)
# ============================================================
CACHE_DIR = ".sds_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "current_session.json")
PROJECTS_LIST_FILE = os.path.join(CACHE_DIR, "projects_index.json")

def save_cache():
    data = {
        "project_registered": st.session_state.project_registered,
        "project_info": st       .session_state.project_info,
        "typology": st.session_state.typology,
        " "params": st.session_state.params,
qa_answers": st.session_state.qa_answers,
        "locked": st.session_state.locked,
        "custom_image": st.session_state.custom_image,
        "custom_description": st.session_state.custom_description,
        "engineering_annotations": st.session_state.engineering_annotations,
        "design_phase": st.session_state.design_phase,
        "comments": st.session_state.comments,
        "user_notes": st.session_state.user_notes,
        "materials": st.session_state.materials,
        "custom_members": st.session_state.custom_members,
        "tie_down_attachments": st.session_state.tie_down_attachments,
        "bracing_points": st.session_state.bracing_points
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
            st.session_state.custom_image = data.get("custom_image")
            st.session_state.custom_description = data.get("custom_description", "")
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
                "num_bays": 2,
                "num_anchors": 2,
                "anchor_angle": 30,
                "wind_speed": 40,
                "snow_load": 0.5,
                "live_load": 0.5,
                "tie_down_vertical_angle": 45,
                "tie_down_horizontal_spread": 25
            })
            st.session_state.custom_members = data.get("custom_members", [])
            st.session_state.tie_down_attachments = data.get("tie_down_attachments", [])
            st.session_state.bracing_points = data.get("bracing_points", [])
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
    st.session_state.qa_answers = {}
    st.session_state.locked = False
    st.session_state.custom_image = None
    st.session_state.custom_description = ""
    st.session_state.design_phase = "understand"
    st.session_state.comments = ""
    st.session_state.user_notes = ""
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    st.session_state.show_export = False
    st.session_state.show_proposal = False
    st.session_state.custom_members = []
    st.session_state.tie_down_attachments = []
    st.session_state.bracing_points = []
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
    st.session_state.custom_image = None
    st.session_state.custom_description = ""
    st.session_state.design_phase = "understand"
    st.session_state.comments = ""
    st.session_state.user_notes = ""
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    st.session_state.show_export = False
    st.session_state.show_proposal = False
    st.session_state.custom_members = []
    st.session_state.tie_down_attachments = []
    st.session_state.bracing_points = []
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
        "user_notes": st.session_state.user_notes,
        "materials": st.session_state.materials,
        "custom_members": st.session_state.custom_members,
        "tie_down_attachments": st.session_state.tie_down_attachments,
        "bracing_points": st.session_state.bracing_points
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
    st.session_state.custom_image = cached.get("custom_image")
    st.session_state.custom_description = cached.get("custom_description", "")
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
        "num_bays": 2,
        "num_anchors": 2,
        "anchor_angle": 30,
        "wind_speed": 40,
        "snow_load": 0.5,
        "live_load": 0.5,
        "tie_down_vertical_angle": 45,
        "tie_down_horizontal_spread": 25
    })
    st.session_state.custom_members = cached.get("custom_members", [])
    st.session_state.tie_down_attachments = cached.get("tie_down_attachments", [])
    st.session_state.bracing_points = cached.get("bracing_points", [])

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
# THREE.JS COMPONENT
# ============================================================

def threejs_component(data):
    data_json = json.dumps(data, default=str)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SDS 3D Viewer</title>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #0a0e17; font-family: sans-serif; }}
            #container {{ width: 100%; height: 100%; }}
            #info {{ position: absolute; bottom: 10px; left: 10px; color: #b0c4de; font-size: 12px; pointer-events: none; }}
            #controls-hint {{ position: absolute; top: 10px; right: 10px; color: #b0c4de; font-size: 12px; background: rgba(10,14,23,0.7); padding: 6px 12px; border-radius: 4px; border: 1px solid #2a3a4f; pointer-events: none; }}
            #context-menu {{ position: absolute; background: #141e2b; border: 1px solid #2a3a4f; border-radius: 8px; padding: 10px; display: none; min-width: 150px; z-index: 100; color: #f0f4fa; }}
            #context-menu button {{ background: #1e2a3a; border: none; color: #f0f4fa; padding: 5px 12px; margin: 3px 0; width: 100%; text-align: left; border-radius: 4px; cursor: pointer; }}
            #context-menu button:hover {{ background: #2a3a4f; }}
        </style>
    </head>
    <body>
        <div id="container"></div>
        <div id="info">SDS 3D Viewer – Click a bracing point to attach tie‑down</div>
        <div id="controls-hint">🖱️ Rotate: drag | Zoom: scroll | Click: select</div>
        <div id="context-menu"></div>

        <script type="importmap">
            {{
                "imports": {{
                    "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
                    "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
                }}
            }}
        </script>
        <script type="module">
            import * as THREE from 'three';
            import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
            import {{ CSS2DRenderer, CSS2DObject }} from 'three/addons/renderers/CSS2DRenderer.js';

            const designData = {data_json};

            const container = document.getElementById('container');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0e17);

            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(12, 8, 16);
            camera.lookAt(0, 3, 0);

            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            container.appendChild(renderer.domElement);

            const labelRenderer = new CSS2DRenderer();
            labelRenderer.setSize(container.clientWidth, container.clientHeight);
            labelRenderer.domElement.style.position = 'absolute';
            labelRenderer.domElement.style.top = '0';
            labelRenderer.domElement.style.left = '0';
            labelRenderer.domElement.style.pointerEvents = 'none';
            container.appendChild(labelRenderer.domElement);

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.1;
            controls.target.set(0, 3, 0);
            controls.update();

            const ambient = new THREE.AmbientLight(0x404060);
            scene.add(ambient);
            const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
            dirLight.position.set(10, 20, 10);
            scene.add(dirLight);
            const fillLight = new THREE.DirectionalLight(0x4488ff, 0.5);
            fillLight.position.set(-10, 0, 10);
            scene.add(fillLight);

            const gridHelper = new THREE.GridHelper(30, 20, 0x2a3a4f, 0x1a2a3a);
            gridHelper.position.y = -0.01;
            scene.add(gridHelper);

            const mainGroup = new THREE.Group();
            scene.add(mainGroup);
            const labelGroup = new THREE.Group();
            scene.add(labelGroup);
            const clickableObjects = [];

            function createBeam(points, color = 0xFF6B6B, width = 0.15) {{
                const curve = new THREE.CatmullRomCurve3(points);
                const geometry = new THREE.TubeGeometry(curve, 50, width, 8, false);
                const material = new THREE.MeshStandardMaterial({{ color, roughness: 0.6, metalness: 0.3 }});
                const mesh = new THREE.Mesh(geometry, material);
                mesh.castShadow = true;
                mesh.receiveShadow = true;
                return mesh;
            }}

            function buildScene(data) {{
                while(mainGroup.children.length) mainGroup.remove(mainGroup.children[0]);
                while(labelGroup.children.length) labelGroup.remove(labelGroup.children[0]);
                clickableObjects.length = 0;

                const {{ params, materials, custom_members, tie_down_attachments, bracing_points, annotations }} = data;
                const A = params.A || 6;
                const B = params.B || 10;
                const LAA = params.LAA || 15;
                const numPoints = 50;

                const x = Array.from({{length: numPoints}}, (_, i) => -B/2 + i * B/(numPoints-1));
                const z_beam = x.map(xi => A * (1 - (2*xi/B)**2));
                const y1 = x.map(xi => -LAA/2 * (1 - (2*xi/B)**2));
                const y2 = x.map(xi => LAA/2 * (1 - (2*xi/B)**2));

                const pts1 = x.map((xi, i) => new THREE.Vector3(xi, y1[i], z_beam[i]));
                const beam1 = createBeam(pts1, 0xFF6B6B, 0.15);
                mainGroup.add(beam1);
                const pts2 = x.map((xi, i) => new THREE.Vector3(xi, y2[i], z_beam[i]));
                const beam2 = createBeam(pts2, 0xFF6B6B, 0.15);
                mainGroup.add(beam2);

                const membranePoints = [];
                for (let i = 0; i < numPoints; i++) {{
                    for (let j = 0; j < numPoints; j++) {{
                        const t = j / (numPoints-1);
                        const xi = x[i];
                        const y = y1[i] * (1 - t) + y2[i] * t;
                        const z = z_beam[i] * (1 - 0.3 * (1 - (2*t - 1)**2));
                        membranePoints.push(new THREE.Vector3(xi, y, z));
                    }}
                }}
                const geom = new THREE.BufferGeometry();
                const vertices = [];
                const indices = [];
                for (let i = 0; i < numPoints - 1; i++) {{
                    for (let j = 0; j < numPoints - 1; j++) {{
                        const idx = i * numPoints + j;
                        const p1 = membranePoints[idx];
                        const p2 = membranePoints[idx + 1];
                        const p3 = membranePoints[idx + numPoints + 1];
                        const p4 = membranePoints[idx + numPoints];
                        vertices.push(p1.x, p1.y, p1.z, p2.x, p2.y, p2.z, p3.x, p3.y, p3.z, p4.x, p4.y, p4.z);
                        const base = (i * (numPoints-1) + j) * 4;
                        indices.push(base, base+1, base+2, base, base+2, base+3);
                    }}
                }}
                geom.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
                geom.setIndex(indices);
                geom.computeVertexNormals();
                const mat = new THREE.MeshPhongMaterial({{
                    color: 0x4a7a9c,
                    transparent: true,
                    opacity: 0.5,
                    side: THREE.DoubleSide,
                    roughness: 0.4,
                    metalness: 0.1
                }});
                const membrane = new THREE.Mesh(geom, mat);
                mainGroup.add(membrane);

                const apexMat = new THREE.MeshStandardMaterial({{ color: 0xFFD93D, emissive: 0xFFD93D, emissiveIntensity: 0.3 }});
                const sphereGeo = new THREE.SphereGeometry(0.3, 16, 16);
                const apex1 = new THREE.Mesh(sphereGeo, apexMat);
                apex1.position.set(0, y1[Math.floor(numPoints/2)], A);
                mainGroup.add(apex1);
                const apex2 = new THREE.Mesh(sphereGeo, apexMat);
                apex2.position.set(0, y2[Math.floor(numPoints/2)], A);
                mainGroup.add(apex2);

                const supportMat = new THREE.MeshStandardMaterial({{ color: 0x4ECDC4 }});
                const supportGeo = new THREE.BoxGeometry(0.4, 0.1, 0.4);
                const s1 = new THREE.Mesh(supportGeo, supportMat);
                s1.position.set(-B/2, 0, 0);
                mainGroup.add(s1);
                const s2 = new THREE.Mesh(supportGeo, supportMat);
                s2.position.set(B/2, 0, 0);
                mainGroup.add(s2);

                if (bracing_points && bracing_points.length) {{
                    const bpMat = new THREE.MeshStandardMaterial({{ color: 0x4ECDC4, emissive: 0x4ECDC4, emissiveIntensity: 0.2 }});
                    bracing_points.forEach((bp, idx) => {{
                        const pos = new THREE.Vector3(bp.x, bp.y, bp.z);
                        const sphere = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 8), bpMat);
                        sphere.position.copy(pos);
                        sphere.userData = {{ type: 'bracingPoint', bayIndex: bp.bayIndex, index: idx }};
                        mainGroup.add(sphere);
                        clickableObjects.push(sphere);
                        const div = document.createElement('div');
                        div.textContent = `B${{bp.bayIndex}}`;
                        div.style.color = '#b0c4de';
                        div.style.fontSize = '10px';
                        div.style.fontWeight = 'bold';
                        div.style.textShadow = '1px 1px 2px rgba(0,0,0,0.8)';
                        const label = new CSS2DObject(div);
                        label.position.set(bp.x, bp.y + 0.4, bp.z);
                        labelGroup.add(label);
                    }});
                }}

                if (annotations.showTieDown && tie_down_attachments) {{
                    tie_down_attachments.forEach(td => {{
                        const start = new THREE.Vector3(td.startX, td.startY, td.startZ);
                        const end = new THREE.Vector3(td.endX, td.endY, td.endZ);
                        const points = [start, end];
                        const curve = new THREE.CatmullRomCurve3(points);
                        const tubeGeo = new THREE.TubeGeometry(curve, 10, 0.03, 6, false);
                        const ropeMat = new THREE.MeshStandardMaterial({{ color: 0xFFD93D, emissive: 0xFFD93D, emissiveIntensity: 0.1 }});
                        const rope = new THREE.Mesh(tubeGeo, ropeMat);
                        mainGroup.add(rope);
                        const anchorMat = new THREE.MeshStandardMaterial({{ color: 0xFF6B6B }});
                        const anchor = new THREE.Mesh(new THREE.SphereGeometry(0.15, 8, 8), anchorMat);
                        anchor.position.copy(end);
                        mainGroup.add(anchor);
                    }});
                }}

                if (annotations.showWind) {{
                    const arrowColor = 0xFF6B6B;
                    const dir = new THREE.Vector3(0, 1, 0);
                    const origin = new THREE.Vector3(-B/4, -LAA/4, A*0.8);
                    const arrowLen = 1.5;
                    const arrowHelper = new THREE.ArrowHelper(dir, origin, arrowLen, arrowColor, 0.3, 0.2);
                    mainGroup.add(arrowHelper);
                    const origin2 = new THREE.Vector3(B/4, LAA/4, A*0.8);
                    const arrowHelper2 = new THREE.ArrowHelper(dir, origin2, arrowLen, arrowColor, 0.3, 0.2);
                    mainGroup.add(arrowHelper2);
                }}

                if (annotations.showLoadPath) {{
                    const pts = [new THREE.Vector3(0, 0, A), new THREE.Vector3(0, 0, A-2)];
                    const curve = new THREE.CatmullRomCurve3(pts);
                    const tubeGeo = new THREE.TubeGeometry(curve, 10, 0.04, 6, false);
                    const mat = new THREE.MeshStandardMaterial({{ color: 0xFFD93D, emissive: 0xFFD93D, emissiveIntensity: 0.2, transparent: true, opacity: 0.6 }});
                    const loadLine = new THREE.Mesh(tubeGeo, mat);
                    mainGroup.add(loadLine);
                }}

                if (custom_members && custom_members.length) {{
                    custom_members.forEach(m => {{
                        const start = new THREE.Vector3(m.startX, m.startY, m.startZ);
                        const end = new THREE.Vector3(m.endX, m.endY, m.endZ);
                        const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
                        const direction = new THREE.Vector3().subVectors(end, start);
                        const length = direction.length();
                        const cylinder = new THREE.Mesh(
                            new THREE.CylinderGeometry(0.06, 0.06, length, 6),
                            new THREE.MeshStandardMaterial({{ color: 0x4a7a9c, emissive: 0x4a7a9c, emissiveIntensity: 0.1 }})
                        );
                        cylinder.position.copy(mid);
                        cylinder.quaternion.setFromUnitVectors(
                            new THREE.Vector3(0, 1, 0),
                            direction.clone().normalize()
                        );
                        mainGroup.add(cylinder);
                    }});
                }}
            }}

            const raycaster = new THREE.Raycaster();
            const pointer = new THREE.Vector2();
            let selectedObject = null;

            renderer.domElement.addEventListener('click', (event) => {{
                const rect = renderer.domElement.getBoundingClientRect();
                pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

                raycaster.setFromCamera(pointer, camera);
                const intersects = raycaster.intersectObjects(clickableObjects);

                const menu = document.getElementById('context-menu');
                if (intersects.length > 0) {{
                    const hit = intersects[0].object;
                    if (hit.userData.type === 'bracingPoint') {{
                        menu.style.display = 'block';
                        menu.style.left = event.clientX + 'px';
                        menu.style.top = event.clientY + 'px';
                        menu.innerHTML = `
                            <div style="font-weight:bold; margin-bottom:5px;">Bracing Point ${{hit.userData.bayIndex}}</div>
                            <button data-action="attach-tie" data-bay="${{hit.userData.bayIndex}}" data-idx="${{hit.userData.index}}">🔗 Attach Tie‑down</button>
                            <button data-action="add-strut" data-bay="${{hit.userData.bayIndex}}">➕ Add Strut here</button>
                            <button data-action="close" style="margin-top:5px;">✖ Cancel</button>
                        `;
                        window._selectedBay = hit.userData.bayIndex;
                        window._selectedIdx = hit.userData.index;
                    }} else {{
                        menu.style.display = 'none';
                    }}
                }} else {{
                    menu.style.display = 'none';
                }}
            }});

            document.getElementById('context-menu').addEventListener('click', (e) => {{
                const target = e.target.closest('button');
                if (!target) return;
                const action = target.dataset.action;
                if (action === 'close') {{
                    document.getElementById('context-menu').style.display = 'none';
                    return;
                }}
                const bay = parseInt(target.dataset.bay);
                const idx = parseInt(target.dataset.idx);
                const url = new URL(window.parent.location.href);
                url.searchParams.set('sds_event', action);
                url.searchParams.set('sds_bay', bay);
                url.searchParams.set('sds_idx', idx);
                window.parent.location.href = url.href;
                document.getElementById('context-menu').style.display = 'none';
            }});

            buildScene(designData);

            window.addEventListener('resize', () => {{
                const w = container.clientWidth;
                const h = container.clientHeight;
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                renderer.setSize(w, h);
                labelRenderer.setSize(w, h);
            }});

            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
                labelRenderer.render(scene, camera);
            }}
            animate();

            window.addEventListener('message', (event) => {{
                if (event.data.type === 'update-scene') {{
                    Object.assign(designData, event.data.data);
                    buildScene(designData);
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html

# ============================================================
# HANDLE EVENTS FROM THREE.JS
# ============================================================
def handle_threejs_events():
    qp = st.query_params
    event = qp.get("sds_event")
    if event:
        bay = int(qp.get("sds_bay", 0))
        idx = int(qp.get("sds_idx", 0))
        if event == "attach-tie":
            if st.session_state.bracing_points and idx < len(st.session_state.bracing_points):
                bp = st.session_state.bracing_points[idx]
                v_angle = np.radians(st.session_state.materials.get("tie_down_vertical_angle", 45))
                h_angle = np.radians(st.session_state.materials.get("tie_down_horizontal_spread", 25))
                distance = bp.z * np.tan(v_angle)
                anchor_x = bp.x + distance * np.sin(h_angle)
                anchor_y = bp.y
                anchor_z = 0
                td = {
                    "bayIndex": bay,
                    "startX": bp.x,
                    "startY": bp.y,
                    "startZ": bp.z,
                    "endX": anchor_x,
                    "endY": anchor_y,
                    "endZ": anchor_z,
                    "ropeDiameter": st.session_state.materials.get("wire_rope_diameter", 10),
                    "verticalAngle": st.session_state.materials.get("tie_down_vertical_angle", 45),
                    "horizontalAngle": st.session_state.materials.get("tie_down_horizontal_spread", 25)
                }
                st.session_state.tie_down_attachments.append(td)
                st.success(f"✅ Tie-down attached to bay {bay}")
        elif event == "add-strut":
            if st.session_state.bracing_points and idx < len(st.session_state.bracing_points):
                bp = st.session_state.bracing_points[idx]
                A = st.session_state.params.get("A", 6)
                B = st.session_state.params.get("B", 10)
                LAA = st.session_state.params.get("LAA", 15)
                x_pos = bp.x
                z = A * (1 - (2*x_pos/B)**2)
                y_left = -LAA/2 * (1 - (2*x_pos/B)**2)
                y_right = LAA/2 * (1 - (2*x_pos/B)**2)
                member = {
                    "type": "Strut",
                    "section": st.session_state.materials.get("section_size", "CHS 150x6"),
                    "bay": bay,
                    "startX": x_pos,
                    "startY": y_left,
                    "startZ": z,
                    "endX": x_pos,
                    "endY": y_right,
                    "endZ": z
                }
                st.session_state.custom_members.append(member)
                st.success(f"✅ Strut added at bay {bay}")
        st.query_params.clear()
        st.rerun()

# ============================================================
# RENDER HIGH-RES IMAGE
# ============================================================
def render_high_res_image_from_threejs():
    st.info("High-res image export will be available from the Three.js viewer (right‑click → Save as).")

# ============================================================
# BILL OF QUANTITIES
# ============================================================
def generate_bq():
    params = st.session_state.params
    materials = st.session_state.materials
    custom_members = st.session_state.custom_members
    tie_attachments = st.session_state.tie_down_attachments
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
    extra_steel = 0
    for m in custom_members:
        length = np.sqrt((m["endX"]-m["startX"])**2 + (m["endY"]-m["startY"])**2 + (m["endZ"]-m["startZ"])**2)
        extra_steel += calculate_steel_weight(
            materials.get("steel_grade", "S355"),
            materials.get("section_type", "CHS"),
            m.get("section", "CHS 150x6"),
            length
        )
    total_steel = steel_weight_kg + extra_steel
    total_weight_kn = (total_steel + fabric_weight_kg) / 100
    rope_length = 0
    for td in tie_attachments:
        length = np.sqrt((td["endX"]-td["startX"])**2 + (td["endY"]-td["startY"])**2 + (td["endZ"]-td["startZ"])**2)
        rope_length += length
    bq_data = {
        "Membrane Area (m²)": membrane_area,
        "Fabric Weight (kg)": fabric_weight_kg,
        "Main Beams Steel (kg)": steel_weight_kg,
        "Additional Members (kg)": extra_steel,
        "Total Steel (kg)": total_steel,
        "Total Structure Weight (kN)": total_weight_kn,
        "Number of Tie-down Ropes": len(tie_attachments),
        "Total Rope Length (m)": rope_length
    }
    return bq_data

# ============================================================
# UNIFIED BOARD – WITH VISIBLE GEOMETRY INPUTS
# ============================================================
def render_unified_workspace():
    params = st.session_state.params
    materials = st.session_state.materials
    typ_key = st.session_state.typology
    typ = TYPOLOGIES[typ_key]
    info = st.session_state.project_info

    st.markdown("## 🧠 SDS-UNDERSTAND — Engineering Understanding & Model Confirmation")
    st.caption("Interactive 3D board with click‑to‑edit. Click a bracing point to attach tie‑downs or add struts.")

    handle_threejs_events()

    col_left, col_right = st.columns([1, 1.8])

    with col_left:
        # Photo / Reference
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📷 PHOTO / REFERENCE</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload reference image", type=["png", "jpg", "jpeg", "webp"], key="photo_ref")
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Reference Image", use_container_width=True)
            st.caption("📌 Note: Uploaded image is for reference only.")
        else:
            st.caption("🖼️ Upload a sketch, photo, or reference image.")
        st.markdown('</div>', unsafe_allow_html=True)

        # User Given Dimensions (read-only summary)
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📏 USER GIVEN DIMENSIONS</div>', unsafe_allow_html=True)
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.metric("A (Rise)", f"{params.get('A', 6.0):.1f} m")
        with col_d2:
            st.metric("B (Span)", f"{params.get('B', 10.0):.1f} m")
        with col_d3:
            st.metric("LAA (Apex to Apex)", f"{params.get('LAA', 15.0):.1f} m")
        st.caption("✏️ Edit these values in the right column below.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Notes
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

        # Summary
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📊 Current Interpretation Summary</div>', unsafe_allow_html=True)
        m = materials
        summary_items = [
            ("PRIMARY STRUCTURE", f"{m.get('steel_grade', 'S355')} {m.get('section_type', 'CHS')} {m.get('section_size', '150x6')}", "badge-provided"),
            ("MEMBRANE", f"{m.get('fabric_type', 'PVC')} {m.get('fabric_thickness', 0.8)}mm, {m.get('prestress', 3.0)}kN/m", "badge-provided"),
            ("APEX POINT (P_A)", f"High point at {params.get('A', 6.0)}m", "badge-inferred"),
            ("SUPPORTS", "Two supports at beam bases", "badge-inferred"),
            ("DIMENSIONS", f"A={params.get('A', 6.0)}m, B={params.get('B', 10.0)}m, LAA={params.get('LAA', 15.0)}m", "badge-confirmed"),
            ("WIND BRACING", f"{m.get('num_bays', 2)} bays", "badge-autogen"),
            ("TIE-DOWNS", f"{len(st.session_state.tie_down_attachments)} attached", "badge-autogen"),
            ("CUSTOM MEMBERS", f"{len(st.session_state.custom_members)} added", "badge-autogen")
        ]
        for label, value, badge in summary_items:
            st.markdown(f'<div style="display:flex; justify-content:space-between; padding:0.1rem 0; border-bottom:1px solid #1a2a3a;">'
                        f'<span style="color:#ffffff; font-weight:500;">{label}</span>'
                        f'<span style="color:#b0c4de;">{value} <span class="badge {badge}">{badge.replace("badge-", "").upper()}</span></span>'
                        f'</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Structured Questions
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">❓ Structured Questions</div>', unsafe_allow_html=True)
        st.caption("Confirm the following assumptions.")
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

        # Legend
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📌 Legend</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="badge badge-confirmed">CONFIRMED</span> <span style="color:#b0c4de;">Confirmed by User</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-inferred">INFERRED</span> <span style="color:#b0c4de;">Inferred by SDS</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-unknown">UNKNOWN</span> <span style="color:#b0c4de;">Not Yet Defined</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-provided">PROVIDED</span> <span style="color:#b0c4de;">Provided by User</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-autogen">AUTO-GEN</span> <span style="color:#b0c4de;">Auto-Generated</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Lock button
        if st.button("🔒 LOCK & PROCEED TO INVESTIGATION", use_container_width=True, type="primary"):
            st.session_state.locked = True
            save_cache()
            st.success("✅ Design locked! You can now view the final model and export.")

    with col_right:
        st.subheader("🔬 Interactive 3D Model (Three.js)")
        st.caption("Click a bracing point (blue sphere) to attach a tie‑down or add a strut.")

        # --- GEOMETRY INPUTS – ALWAYS VISIBLE ---
        st.markdown("### 📐 Edit Geometry (A, B, LAA)")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            new_a = st.number_input(
                "Rise (A) (m)",
                min_value=2.0,
                max_value=20.0,
                step=0.5,
                value=float(params.get("A", 6.0)),
                format="%.1f",
                key="right_a"
            )
            params["A"] = new_a
        with col_b:
            new_b = st.number_input(
                "Span (B) (m)",
                min_value=4.0,
                max_value=40.0,
                step=0.5,
                value=float(params.get("B", 10.0)),
                format="%.1f",
                key="right_b"
            )
            params["B"] = new_b
        with col_c:
            new_laa = st.number_input(
                "LAA (m)",
                min_value=4.0,
                max_value=50.0,
                step=0.5,
                value=float(params.get("LAA", 15.0)),
                format="%.1f",
                key="right_laa"
            )
            params["LAA"] = new_laa
        st.divider()

        # --- MATERIALS & BRACING (in expander) ---
        with st.expander("🏗️ Materials & Bracing", expanded=False):
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
            
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                materials["num_bays"] = st.selectbox("Bracing Bays", [1, 2, 3], index=[1, 2, 3].index(materials.get("num_bays", 2)), key="right_bays", help="1=Apex only, 2=Third points, 3=Quarter points")
                span = params.get("B", 10.0)
                positions = generate_bracing_positions(span, materials["num_bays"])
                st.caption(f"📍 Positions: {', '.join([f'{p:.1f}m' for p in positions])}")
            with col_b2:
                materials["wire_rope_diameter"] = st.selectbox("Wire Rope Diameter (mm)", [6, 8, 10, 12, 14, 16, 20], index=[6, 8, 10, 12, 14, 16, 20].index(materials.get("wire_rope_diameter", 10)), key="right_rope")
            with col_b3:
                materials["tie_down_vertical_angle"] = st.slider("Vertical Angle (°)", min_value=20, max_value=70, step=5, value=materials.get("tie_down_vertical_angle", 45), key="right_vertical", help="Angle of tie-down rope from horizontal")
            col_b4, col_b5 = st.columns(2)
            with col_b4:
                materials["tie_down_horizontal_spread"] = st.slider("Horizontal Spread (°)", min_value=10, max_value=60, step=5, value=materials.get("tie_down_horizontal_spread", 25), key="right_spread", help="Angle of tie-down spread outward from beam")
            with col_b5:
                st.caption("💡 Tie-downs auto-align to bracing positions")

        # Prepare data for Three.js
        num_bays = materials.get("num_bays", 2)
        span = params.get("B", 10)
        laa = params.get("LAA", 15)
        rise = params.get("A", 6)
        positions = generate_bracing_positions(span, num_bays)
        bracing_points = []
        for idx, x_pos in enumerate(positions):
            z = rise * (1 - (2*x_pos/span)**2)
            y1 = -laa/2 * (1 - (2*x_pos/span)**2)
            y2 = laa/2 * (1 - (2*x_pos/span)**2)
            bracing_points.append({"x": x_pos, "y": y1, "z": z, "bayIndex": idx})
            bracing_points.append({"x": x_pos, "y": y2, "z": z, "bayIndex": idx})
        st.session_state.bracing_points = bracing_points

        three_data = {
            "params": params,
            "materials": materials,
            "custom_members": st.session_state.custom_members,
            "tie_down_attachments": st.session_state.tie_down_attachments,
            "bracing_points": bracing_points,
            "annotations": st.session_state.engineering_annotations
        }

        html = threejs_component(three_data)
        st.components.v1.html(html, height=600, scrolling=False)

        # Annotation toggles
        anno_cols = st.columns(4)
        with anno_cols[0]:
            st.session_state.engineering_annotations["show_wind"] = st.checkbox("💨 Wind", value=st.session_state.engineering_annotations.get("show_wind", True))
        with anno_cols[1]:
            st.session_state.engineering_annotations["show_tie_down"] = st.checkbox("🔗 Tie-Down", value=st.session_state.engineering_annotations.get("show_tie_down", True))
        with anno_cols[2]:
            st.session_state.engineering_annotations["show_bracing"] = st.checkbox("📐 Bracing", value=st.session_state.engineering_annotations.get("show_bracing", True))
        with anno_cols[3]:
            st.session_state.engineering_annotations["show_load_path"] = st.checkbox("📊 Load", value=st.session_state.engineering_annotations.get("show_load_path", True))

        # Structural Checks
        with st.expander("📊 Preliminary Structural Checks", expanded=True):
            m = materials
            span = params.get("B", 10.0)
            laa = params.get("LAA", 15.0)
            rise = params.get("A", 6.0)
            membrane_area = span * laa * 1.1
            steel_weight_kg = 2 * calculate_steel_weight(
                m.get("steel_grade", "S355"),
                m.get("section_type", "CHS"),
                m.get("section_size", "CHS 150x6"),
                span
            )
            fabric_weight_kg = calculate_fabric_weight(
                m.get("fabric_type", "PVC-coated Polyester"),
                m.get("fabric_thickness", 0.8),
                membrane_area
            )
            total_weight_kg = steel_weight_kg + fabric_weight_kg
            total_weight_kn = total_weight_kg / 100
            wind_load = calculate_wind_load(m.get("wind_speed", 40), membrane_area)
            num_bays = m.get("num_bays", 2)
            bracing_x = generate_bracing_positions(span, num_bays)
            num_anchors = len(bracing_x) * 2
            tie_down_force = calculate_tie_down_force(
                wind_load,
                total_weight_kn,
                num_anchors,
                m.get("tie_down_vertical_angle", 45)
            )
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
                st.metric("✅ Rope Check", "✅ PASS" if rope_check else "❌ FAIL")
            if not rope_check:
                st.error(f"⚠️ Tie-down force ({tie_down_force:.1f} kN) exceeds rope capacity ({rope_capacity:.1f} kN).")
            else:
                st.success("✅ All preliminary checks passed.")

        # Bill of Quantities
        with st.expander("📋 Bill of Quantities"):
            bq = generate_bq()
            df = pd.DataFrame(list(bq.items()), columns=["Item", "Value"])
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download BQ as CSV", data=csv, file_name="bq.csv", mime="text/csv")

        # Actions
        st.divider()
        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        with col_act1:
            if st.button("📸 Render High-Res Image", use_container_width=True, type="primary"):
                render_high_res_image_from_threejs()
                st.info("Use right‑click → Save image as from the 3D view, or use the browser's screenshot tool.")
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
                    "custom_members": st.session_state.custom_members,
                    "tie_down_attachments": st.session_state.tie_down_attachments,
                    "locked": st.session_state.locked,
                    "export_date": datetime.now().isoformat()
                }
                json_str = json.dumps(export_data, indent=2)
                b64 = base64.b64encode(json_str.encode()).decode()
                href = f'<a href="data:application/json;base64,{b64}" download="project_data.json">📄 Download JSON</a>'
                st.markdown(href, unsafe_allow_html=True)
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
                    "num_bays": 2,
                    "num_anchors": 2,
                    "anchor_angle": 30,
                    "wind_speed": 40,
                    "snow_load": 0.5,
                    "live_load": 0.5,
                    "tie_down_vertical_angle": 45,
                    "tie_down_horizontal_spread": 25
                }
                st.session_state.custom_members = []
                st.session_state.tie_down_attachments = []
                st.session_state.bracing_points = []
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
                    save_cache()
                    st.rerun()
        st.caption("All data is cached locally. Your project will resume where you left off.")
        st.stop()

if st.session_state.typology is not None:
    render_unified_workspace()

st.caption("SDS Platform v5.0 | Three.js Interactive Board | Roots Protected. Branches Free. Ecosystem Growing.")
save_cache()
