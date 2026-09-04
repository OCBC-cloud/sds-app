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
import pandas as pd
from io import BytesIO
import hashlib

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SDS Design Studio Pro",
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
    .stSuccess {
        background-color: #1a3a2a !important;
        border-left: 4px solid #2ecc71 !important;
        color: #f0f4fa !important;
    }
    .stError {
        background-color: #3a1a1a !important;
        border-left: 4px solid #e74c3c !important;
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
    .badge-pass { background-color: #2d6a4f; color: #a7f3d0; }
    .badge-fail { background-color: #6b2d2d; color: #fca5a5; }
    
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
    
    .comparison-card {
        background-color: #141e2b;
        border-radius: 12px;
        padding: 1rem;
        border: 2px solid #2a3a4f;
        margin: 0.5rem 0;
    }
    .comparison-card.best {
        border-color: #2ecc71;
    }
    .comparison-card.worst {
        border-color: #e74c3c;
    }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# MATERIAL DATABASE (NEW)
# ============================================================
MATERIAL_DATABASE = {
    "steel": {
        "S275": {
            "cost_per_kg": 0.90,
            "density": 7850,
            "yield_strength": 275,
            "ultimate_strength": 430,
            "modulus_elasticity": 210000,
            "description": "Structural steel - general purpose"
        },
        "S355": {
            "cost_per_kg": 1.20,
            "density": 7850,
            "yield_strength": 355,
            "ultimate_strength": 490,
            "modulus_elasticity": 210000,
            "description": "High strength structural steel"
        },
        "S460": {
            "cost_per_kg": 1.80,
            "density": 7850,
            "yield_strength": 460,
            "ultimate_strength": 550,
            "modulus_elasticity": 210000,
            "description": "Ultra-high strength steel"
        },
        "Aluminum 6061-T6": {
            "cost_per_kg": 4.50,
            "density": 2700,
            "yield_strength": 276,
            "ultimate_strength": 310,
            "modulus_elasticity": 69000,
            "description": "Lightweight aluminum alloy"
        }
    },
    "fabric": {
        "PVC-coated Polyester": {
            "cost_per_m2": 25.0,
            "weight_per_m2": 1.2,
            "lifespan_years": 20,
            "tensile_strength": 40,
            "fire_rating": "B1",
            "description": "Standard tensile membrane"
        },
        "PTFE-coated Fiberglass": {
            "cost_per_m2": 80.0,
            "weight_per_m2": 1.8,
            "lifespan_years": 35,
            "tensile_strength": 60,
            "fire_rating": "A",
            "description": "Premium architectural membrane"
        },
        "ETFE": {
            "cost_per_m2": 120.0,
            "weight_per_m2": 0.8,
            "lifespan_years": 50,
            "tensile_strength": 45,
            "fire_rating": "B1",
            "description": "High-performance fluoropolymer"
        }
    },
    "cables": {
        "Galvanized Steel (6x19)": {
            "cost_per_m": 5.0,
            "weight_per_m": 0.5,
            "breaking_load": 55,
            "description": "Standard galvanized wire rope"
        },
        "Stainless Steel (1x19)": {
            "cost_per_m": 12.0,
            "weight_per_m": 0.8,
            "breaking_load": 70,
            "description": "Corrosion-resistant cable"
        },
        "Polyester Rope": {
            "cost_per_m": 3.0,
            "weight_per_m": 0.2,
            "breaking_load": 30,
            "description": "Lightweight synthetic rope"
        }
    },
    "sections": {
        "CHS 100x5": {"area": 1492, "weight_per_m": 11.7, "second_moment": 2.3e6},
        "CHS 150x6": {"area": 2714, "weight_per_m": 21.3, "second_moment": 9.1e6},
        "CHS 200x8": {"area": 4826, "weight_per_m": 37.9, "second_moment": 28.7e6},
        "CHS 250x10": {"area": 7539, "weight_per_m": 59.2, "second_moment": 68.4e6},
        "RHS 150x100x6": {"area": 2784, "weight_per_m": 21.8, "second_moment": 8.3e6},
        "RHS 200x150x8": {"area": 5104, "weight_per_m": 40.0, "second_moment": 30.1e6},
        "I-100": {"area": 1030, "weight_per_m": 8.1, "second_moment": 4.5e6},
        "I-150": {"area": 2130, "weight_per_m": 16.7, "second_moment": 16.0e6},
        "I-200": {"area": 3310, "weight_per_m": 26.0, "second_moment": 38.0e6}
    }
}

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
        "show_bracing": True,
        "show_annotations": True
    }
if "design_phase" not in st.session_state:
    st.session_state.design_phase = "understand"
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
if "design_history" not in st.session_state:
    st.session_state.design_history = []
if "comparison_mode" not in st.session_state:
    st.session_state.comparison_mode = False
if "selected_for_comparison" not in st.session_state:
    st.session_state.selected_for_comparison = []

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
        "tie_down_horizontal_spread": 25,
        "safety_factor": 1.5
    }

# ============================================================
# CACHE HANDLER
# ============================================================
CACHE_DIR = ".sds_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "current_session.json")
PROJECTS_LIST_FILE = os.path.join(CACHE_DIR, "projects_index.json")
HISTORY_FILE = os.path.join(CACHE_DIR, "design_history.json")

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
        "materials": st.session_state.materials,
        "design_history": st.session_state.design_history[-10:]  # Keep last 10
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
                        "locked": data.get("locked", False),
                        "hash": hashlib.md5(json.dumps(data).encode()).hexdigest()[:8]
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
                "show_bracing": True,
                "show_annotations": True
            })
            st.session_state.design_phase = data.get("design_phase", "understand")
            st.session_state.comments = data.get("comments", "")
            st.session_state.materials = data.get("materials", {})
            st.session_state.design_history = data.get("design_history", [])
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
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    st.session_state.show_export = False
    st.session_state.show_proposal = False
    st.session_state.comparison_mode = False
    st.session_state.selected_for_comparison = []
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
        "materials": st.session_state.materials,
        "design_history": st.session_state.design_history
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
    
    # Save to history
    history_data = {
        "timestamp": datetime.now().isoformat(),
        "project": st.session_state.project_info.get("name"),
        "typology": st.session_state.typology,
        "params": st.session_state.params.copy(),
        "hash": hashlib.md5(json.dumps(data).encode()).hexdigest()[:8]
    }
    st.session_state.design_history.append(history_data)
    if len(st.session_state.design_history) > 20:
        st.session_state.design_history = st.session_state.design_history[-20:]
    
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
    st.session_state.custom_image = cached.get("custom_image")
    st.session_state.custom_description = cached.get("custom_description", "")
    st.session_state.engineering_annotations = cached.get("engineering_annotations", {
        "show_wind": True,
        "show_tie_down": True,
        "show_load_path": True,
        "show_bracing": True,
        "show_annotations": True
    })
    st.session_state.design_phase = cached.get("design_phase", "understand")
    st.session_state.comments = cached.get("comments", "")
    st.session_state.materials = cached.get("materials", {})
    st.session_state.design_history = cached.get("design_history", [])

# ============================================================
# ENHANCED TYPOLOGIES
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
# ENHANCED ENGINEERING FUNCTIONS
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

def generate_tie_down_anchors_at_positions(span, laa, height, x_positions, vertical_angle_deg, horizontal_spread_deg):
    vertical_rad = np.radians(vertical_angle_deg)
    horizontal_rad = np.radians(horizontal_spread_deg)
    distance = height * np.tan(vertical_rad)
    anchors = []
    beam_ys = [-laa/2, laa/2]
    for beam_idx, beam_y in enumerate(beam_ys):
        for beam_x in x_positions:
            anchor_x = beam_x + distance * np.sin(horizontal_rad)
            anchor_y = beam_y
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

def calculate_steel_weight(grade, section_type, section_size, length):
    section = MATERIAL_DATABASE["sections"].get(section_size, {"weight_per_m": 20.0})
    return section["weight_per_m"] * length

def calculate_fabric_weight(fabric_type, thickness, area):
    fabric = MATERIAL_DATABASE["fabric"].get(fabric_type, {})
    weight_per_m2 = fabric.get("weight_per_m2", 1.2)
    return weight_per_m2 * area

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

def generate_load_combinations(params, materials):
    """Generate structural load combinations per Eurocode"""
    dead_load = materials.get("dead_load", 1.0)
    live_load = materials.get("live_load", 0.5)
    snow_load = materials.get("snow_load", 0.5)
    wind_load = materials.get("wind_load", 0.8)
    
    combinations = {
        "ULS_1": 1.35 * dead_load + 1.5 * live_load,
        "ULS_2": 1.35 * dead_load + 1.5 * snow_load,
        "ULS_3": 1.35 * dead_load + 1.5 * wind_load,
        "ULS_4": 1.0 * dead_load + 1.5 * wind_load + 0.7 * live_load,
        "SLS_1": 1.0 * dead_load + 1.0 * live_load,
        "SLS_2": 1.0 * dead_load + 0.7 * wind_load
    }
    return combinations

def calculate_cost_estimate(params, materials, typology):
    """Calculate total project cost with material database"""
    span = params.get("B", 10.0)
    laa = params.get("LAA", 15.0)
    rise = params.get("A", 6.0)
    
    # Steel cost
    steel_length = span * 2 + laa * 2
    steel_weight = calculate_steel_weight(
        materials.get("steel_grade", "S355"),
        materials.get("section_type", "CHS"),
        materials.get("section_size", "CHS 150x6"),
        steel_length
    )
    steel_cost = steel_weight * MATERIAL_DATABASE["steel"][materials.get("steel_grade", "S355")]["cost_per_kg"]
    
    # Fabric cost
    membrane_area = span * laa * 1.1
    fabric_cost = membrane_area * MATERIAL_DATABASE["fabric"][materials.get("fabric_type", "PVC-coated Polyester")]["cost_per_m2"]
    
    # Cable cost
    cable_length = laa * 2 + span * 2
    cable_cost = cable_length * MATERIAL_DATABASE["cables"][materials.get("wire_rope_type", "Galvanized Steel (6x19)")]["cost_per_m"]
    
    # Labor and installation (estimated)
    labor_cost = (steel_weight + membrane_area) * 2.0
    
    total_cost = steel_cost + fabric_cost + cable_cost + labor_cost
    
    return {
        "steel_cost": steel_cost,
        "fabric_cost": fabric_cost,
        "cable_cost": cable_cost,
        "labor_cost": labor_cost,
        "total_cost": total_cost,
        "cost_per_m2": total_cost / membrane_area if membrane_area > 0 else 0
    }

# ============================================================
# PDF REPORT GENERATOR (NEW)
# ============================================================
def generate_pdf_report(params, materials, typology, project_info, qa_answers, comments):
    """Generate a professional PDF report using reportlab"""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch, cm
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#f39c12'),
            spaceAfter=30
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4a7a9c'),
            spaceAfter=12
        )
        
        # Cover page
        story.append(Paragraph("SDS DESIGN STUDIO", title_style))
        story.append(Paragraph("Professional Engineering Report", styles['Heading2']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"<b>Project:</b> {project_info.get('name', 'Untitled')}", styles['Normal']))
        story.append(Paragraph(f"<b>Client:</b> {project_info.get('client', 'Unknown')}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Paragraph(f"<b>Reference:</b> {project_info.get('reference', 'N/A')}", styles['Normal']))
        story.append(PageBreak())
        
        # Parameters summary
        story.append(Paragraph("Design Parameters", heading_style))
        param_data = [["Parameter", "Value", "Unit"]]
        for key, value in params.items():
            param_data.append([key.upper(), f"{value:.1f}", "m"])
        param_table = Table(param_data, colWidths=[2*inch, 1.5*inch, 1*inch])
        param_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a3a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#141e2b')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2a3a4f'))
        ]))
        story.append(param_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Materials summary
        story.append(Paragraph("Materials", heading_style))
        mat_data = [
            ["Material", "Specification", "Value"],
            ["Steel", materials.get("steel_grade", "S355"), materials.get("section_size", "CHS 150x6")],
            ["Fabric", materials.get("fabric_type", "PVC"), f"{materials.get('fabric_thickness', 0.8)}mm"],
            ["Cables", materials.get("wire_rope_type", "Galvanized"), f"{materials.get('wire_rope_diameter', 10)}mm"]
        ]
        mat_table = Table(mat_data, colWidths=[2*inch, 2*inch, 1.5*inch])
        mat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a3a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#141e2b')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2a3a4f'))
        ]))
        story.append(mat_table)
        story.append(PageBreak())
        
        # Load combinations
        story.append(Paragraph("Load Combinations", heading_style))
        load_combo = generate_load_combinations(params, materials)
        combo_data = [["Combination", "Load Value (kN)"]]
        for key, value in load_combo.items():
            combo_data.append([key, f"{value:.2f}"])
        combo_table = Table(combo_data, colWidths=[2*inch, 2*inch])
        combo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a3a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#141e2b')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2a3a4f'))
        ]))
        story.append(combo_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Cost estimate
        story.append(Paragraph("Cost Estimate", heading_style))
        cost_data = calculate_cost_estimate(params, materials, typology)
        cost_table_data = [
            ["Item", "Cost (USD)"],
            ["Steel", f"${cost_data['steel_cost']:.2f}"],
            ["Fabric", f"${cost_data['fabric_cost']:.2f}"],
            ["Cables", f"${cost_data['cable_cost']:.2f}"],
            ["Labor", f"${cost_data['labor_cost']:.2f}"],
            ["", ""],
            ["TOTAL", f"${cost_data['total_cost']:.2f}"],
            ["Cost per m²", f"${cost_data['cost_per_m2']:.2f}"]
        ]
        cost_table = Table(cost_table_data, colWidths=[2*inch, 2*inch])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a3a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#141e2b')),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f39c12')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#0a0e17')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2a3a4f'))
        ]))
        story.append(cost_table)
        story.append(PageBreak())
        
        # Q&A Confirmations
        story.append(Paragraph("Design Confirmations", heading_style))
        for i, q in enumerate(typology.get("qa", [])):
            ans = qa_answers.get(f"qa_{i}", "Not answered")
            story.append(Paragraph(f"<b>{i+1}.</b> {q} <b>→</b> {ans}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Comments
        if comments:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Design Notes", heading_style))
            story.append(Paragraph(comments, styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("<i>Generated by SDS Design Studio Pro</i>", styles['Normal']))
        story.append(Paragraph(f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except ImportError:
        return None

# ============================================================
# 3D GENERATOR WITH ANNOTATIONS (ENHANCED)
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

    fig = go.Figure()

    # Beams
    fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1', line=dict(color='#FF6B6B', width=6)))
    fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2', line=dict(color='#FF6B6B', width=6)))
    
    # Membrane
    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, 
                             colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
                             opacity=0.7, showscale=False))

    # Apex and supports
    fig.add_trace(go.Scatter3d(x=[0], y=[y1[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 1', marker=dict(color='#FFD93D', size=8, symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[0], y=[y2[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 2', marker=dict(color='#FFD93D', size=8, symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[-span/2], y=[0], z=[0], 
                               mode='markers', name='Support 1', marker=dict(color='#4ECDC4', size=6, symbol='square')))
    fig.add_trace(go.Scatter3d(x=[span/2], y=[0], z=[0], 
                               mode='markers', name='Support 2', marker=dict(color='#4ECDC4', size=6, symbol='square')))

    # 3D Annotations (NEW)
    show_annotations = True
    if annotations is not None:
        show_annotations = annotations.get("show_annotations", True)
    
    if show_annotations:
        # Dimension annotations
        fig.add_trace(go.Scatter3d(
            x=[-span/2, 0], y=[0, 0], z=[0, rise],
            mode='lines', name='Rise (A)',
            line=dict(color='#FFD93D', width=2, dash='dash'),
            showlegend=True
        ))
        fig.add_trace(go.Scatter3d(
            x=[-span/2, span/2], y=[-laa/2, -laa/2], z=[0, 0],
            mode='lines', name='Span (B)',
            line=dict(color='#4ECDC4', width=2, dash='dash'),
            showlegend=True
        ))
        # Text annotations using scatter with text
        fig.add_trace(go.Scatter3d(
            x=[0], y=[-laa/2], z=[rise/2],
            mode='text', text=[f'A = {rise:.1f}m'],
            textfont=dict(color='#FFD93D', size=12),
            showlegend=False
        ))
        fig.add_trace(go.Scatter3d(
            x=[0], y=[-laa/2 - 1.5], z=[0],
            mode='text', text=[f'B = {span:.1f}m'],
            textfont=dict(color='#4ECDC4', size=12),
            showlegend=False
        ))

    # Engineering annotations (Wind, Tie-Down, Bracing, Load Path)
    num_bays = 2
    if materials is not None:
        num_bays = materials.get("num_bays", 2)
    bracing_x = generate_bracing_positions(span, num_bays)

    show_bracing = True
    if annotations is not None:
        show_bracing = annotations.get("show_bracing", True)
    
    if materials is not None and show_bracing:
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

    show_tie_down = True
    if annotations is not None:
        show_tie_down = annotations.get("show_tie_down", True)
    
    if materials is not None and show_tie_down:
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
                line=dict(color='#FFD93D', width=2),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[a["anchor_x"]],
                y=[a["anchor_y"]],
                z=[a["anchor_z"]],
                mode='markers', name='Ground Anchor',
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
            line=dict(color='#FF6B6B', width=3, dash='dash'), showlegend=True
        ))
        # Wind direction arrow (text)
        fig.add_trace(go.Scatter3d(
            x=[-span/4], y=[-laa/4], z=[rise*1.3],
            mode='text', text=['💨 WIND'],
            textfont=dict(color='#FF6B6B', size=10),
            showlegend=False
        ))

    show_load_path = True
    if annotations is not None:
        show_load_path = annotations.get("show_load_path", True)
    if show_load_path:
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[rise, rise-2],
            mode='lines', name='Load Path',
            line=dict(color='#FFD93D', width=4), showlegend=True
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
            font=dict(color='#ffffff', size=6),
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
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
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
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
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
# DESIGN COMPARISON MODE (NEW)
# ============================================================
def render_comparison_mode():
    st.subheader("📊 Design Comparison Mode")
    
    # Get available designs from history
    history = st.session_state.design_history
    if not history:
        st.info("No design history available for comparison. Save some designs first!")
        if st.button("⬅ Back to Design"):
            st.session_state.comparison_mode = False
            st.rerun()
        return
    
    # Select designs to compare
    st.write("Select up to 3 designs to compare:")
    selected = []
    cols = st.columns(3)
    for i, design in enumerate(history[-10:]):
        with cols[i % 3]:
            if st.checkbox(f"Design {i+1}", key=f"compare_{i}"):
                selected.append(design)
    
    if len(selected) < 2:
        st.warning("Select at least 2 designs to compare")
        return
    
    # Comparison table
    st.subheader("📋 Comparison Summary")
    compare_data = []
    
    for design in selected:
        params = design.get("params", {})
        row = {
            "Design": f"{design.get('timestamp', '')[:10]}",
            "Rise (m)": params.get("A", "N/A"),
            "Span (m)": params.get("B", "N/A"),
            "LAA (m)": params.get("LAA", "N/A"),
            "Hash": design.get("hash", "N/A")
        }
        compare_data.append(row)
    
    df = pd.DataFrame(compare_data)
    st.dataframe(df, use_container_width=True)
    
    # Visual comparison (radar chart)
    try:
        import plotly.express as px
        df_radar = pd.DataFrame(compare_data)
        df_radar = df_radar.set_index("Design")
        numeric_cols = ["Rise (m)", "Span (m)", "LAA (m)"]
        fig = go.Figure()
        for design in df_radar.index:
            fig.add_trace(go.Scatterpolar(
                r=df_radar.loc[design, numeric_cols].values,
                theta=numeric_cols,
                fill='toself',
                name=design
            ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, max(df_radar[numeric_cols].max())])
            ),
            paper_bgcolor='#0a0e17',
            font=dict(color='#ffffff')
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Radar chart unavailable: {e}")
    
    if st.button("⬅ Back to Design"):
        st.session_state.comparison_mode = False
        st.rerun()

# ============================================================
# UNIFIED UI RENDERER
# ============================================================

def render_unified_workspace():
    """The single SDS-UNDERSTAND workspace where everything happens"""
    
    params = st.session_state.params
    materials = st.session_state.materials
    typ_key = st.session_state.typology
    typ = TYPOLOGIES[typ_key]
    info = st.session_state.project_info
    
    st.markdown("## 🧠 SDS-UNDERSTAND — Engineering Understanding & Model Confirmation")
    st.caption("Review, confirm, and edit your design in one unified workspace. Changes update the 3D model in real-time.")
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        # Project summary card
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📊 Current Interpretation Summary</div>', unsafe_allow_html=True)
        m = materials
        summary_items = [
            ("PRIMARY STRUCTURE", f"{m.get('steel_grade', 'S355')} {m.get('section_type', 'CHS')} {m.get('section_size', '150x6')}", "badge-provided"),
            ("MEMBRANE", f"{m.get('fabric_type', 'PVC')} {m.get('fabric_thickness', 0.8)}mm, {m.get('prestress', 3.0)}kN/m", "badge-provided"),
            ("APEX POINT (P_A)", f"High point at {params.get('A', 6.0)}m", "badge-inferred"),
            ("SUPPORTS", "Two supports at beam bases", "badge-inferred"),
            ("DIMENSIONS", f"A={params.get('A', 6.0)}m, B={params.get('B', 10.0)}m, LAA={params.get('LAA', 15.0)}m", "badge-confirmed"),
            ("WIND BRACING", f"{m.get('num_bays', 2)} bays at {', '.join([f'{p:.1f}m' for p in generate_bracing_positions(params.get('B', 10.0), m.get('num_bays', 2))])}", "badge-autogen"),
            ("TIE-DOWNS", f"Aligned to bracing: {m.get('num_bays', 2)} positions, {m.get('tie_down_vertical_angle', 45)}° vertical", "badge-autogen"),
            ("WIRE ROPE", f"{m.get('wire_rope_diameter', 10)}mm {m.get('wire_rope_type', 'Galvanized')}", "badge-provided"),
        ]
        for label, value, badge in summary_items:
            st.markdown(f'<div style="display:flex; justify-content:space-between; padding:0.1rem 0; border-bottom:1px solid #1a2a3a;">'
                        f'<span style="color:#ffffff; font-weight:500;">{label}</span>'
                        f'<span style="color:#b0c4de;">{value} <span class="badge {badge}">{badge.replace("badge-", "").upper()}</span></span>'
                        f'</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Legend
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📌 Legend</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="badge badge-confirmed">CONFIRMED</span> <span style="color:#b0c4de;">User</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-inferred">INFERRED</span> <span style="color:#b0c4de;">SDS</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-unknown">UNKNOWN</span> <span style="color:#b0c4de;">Not Defined</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-provided">PROVIDED</span> <span style="color:#b0c4de;">User</span> &nbsp;|&nbsp; '
                    f'<span class="badge badge-autogen">AUTO-GEN</span> <span style="color:#b0c4de;">Auto</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Geometry inputs
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📐 Geometry</div>', unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            new_a = st.number_input("Rise (A) (m)", min_value=2.0, max_value=20.0, step=0.5, value=float(params.get("A", 6.0)), format="%.1f", key="unified_a")
            params["A"] = new_a
        with col_b:
            new_b = st.number_input("Span (B) (m)", min_value=4.0, max_value=40.0, step=0.5, value=float(params.get("B", 10.0)), format="%.1f", key="unified_b")
            params["B"] = new_b
        with col_c:
            new_laa = st.number_input("Apex Dist (LAA) (m)", min_value=4.0, max_value=50.0, step=0.5, value=float(params.get("LAA", 15.0)), format="%.1f", key="unified_laa")
            params["LAA"] = new_laa
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Materials
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🏗️ Materials</div>', unsafe_allow_html=True)
        
        # Material selection with database info
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            steel_options = list(MATERIAL_DATABASE["steel"].keys())
            materials["steel_grade"] = st.selectbox("Steel Grade", steel_options, 
                index=steel_options.index(materials.get("steel_grade", "S355")) if materials.get("steel_grade") in steel_options else 0, 
                key="unified_steel")
            # Show steel properties
            steel_props = MATERIAL_DATABASE["steel"].get(materials["steel_grade"], {})
            st.caption(f"Yield: {steel_props.get('yield_strength', 'N/A')} MPa | Cost: ${steel_props.get('cost_per_kg', 'N/A')}/kg")
            
        with col_m2:
            fabric_options = list(MATERIAL_DATABASE["fabric"].keys())
            materials["fabric_type"] = st.selectbox("Fabric Type", fabric_options,
                index=fabric_options.index(materials.get("fabric_type", "PVC-coated Polyester")) if materials.get("fabric_type") in fabric_options else 0,
                key="unified_fabric")
            fabric_props = MATERIAL_DATABASE["fabric"].get(materials["fabric_type"], {})
            st.caption(f"Lifespan: {fabric_props.get('lifespan_years', 'N/A')} yrs | Cost: ${fabric_props.get('cost_per_m2', 'N/A')}/m²")
        
        col_m3, col_m4 = st.columns(2)
        with col_m3:
            section_options = list(MATERIAL_DATABASE["sections"].keys())
            materials["section_size"] = st.selectbox("Section Size", section_options,
                index=section_options.index(materials.get("section_size", "CHS 150x6")) if materials.get("section_size") in section_options else 0,
                key="unified_section")
        with col_m4:
            cable_options = list(MATERIAL_DATABASE["cables"].keys())
            materials["wire_rope_type"] = st.selectbox("Cable Type", cable_options,
                index=cable_options.index(materials.get("wire_rope_type", "Galvanized Steel (6x19)")) if materials.get("wire_rope_type") in cable_options else 0,
                key="unified_cable")
        
        col_m5, col_m6 = st.columns(2)
        with col_m5:
            materials["fabric_thickness"] = st.selectbox("Fabric Thickness (mm)", [0.5, 0.8, 1.0, 1.2],
                index=[0.5, 0.8, 1.0, 1.2].index(materials.get("fabric_thickness", 0.8)), key="unified_thickness")
        with col_m6:
            materials["wire_rope_diameter"] = st.selectbox("Cable Diameter (mm)", [6, 8, 10, 12, 14, 16, 20],
                index=[6, 8, 10, 12, 14, 16, 20].index(materials.get("wire_rope_diameter", 10)), key="unified_rope")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Bracing & Tie-Downs
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔗 Bracing & Tie-Downs</div>', unsafe_allow_html=True)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            materials["num_bays"] = st.selectbox("Bracing Bays", [1, 2, 3], 
                index=[1, 2, 3].index(materials.get("num_bays", 2)), key="unified_bays")
            span = params.get("B", 10.0)
            positions = generate_bracing_positions(span, materials["num_bays"])
            st.caption(f"📍 Positions: {', '.join([f'{p:.1f}m' for p in positions])}")
        with col_b2:
            materials["tie_down_vertical_angle"] = st.slider("Tie-Down Angle (°)", min_value=20, max_value=70, step=5, 
                value=materials.get("tie_down_vertical_angle", 45), key="unified_vertical")
        
        # Wind and loads
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            materials["wind_speed"] = st.number_input("Wind Speed (m/s)", min_value=10, max_value=80, step=5, 
                value=materials.get("wind_speed", 40), key="unified_wind")
        with col_w2:
            materials["safety_factor"] = st.number_input("Safety Factor", min_value=1.0, max_value=3.0, step=0.1,
                value=materials.get("safety_factor", 1.5), key="unified_safety")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Design history
        if st.session_state.design_history:
            st.markdown('<div class="sds-card">', unsafe_allow_html=True)
            st.markdown('<div class="title">📜 Design History</div>', unsafe_allow_html=True)
            for i, design in enumerate(st.session_state.design_history[-5:]):
                st.write(f"{i+1}. {design.get('timestamp', '')[:16]} - {design.get('project', 'Unknown')} ({design.get('hash', '')})")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.subheader("🔬 3D Model")
        
        # Annotation toggles
        anno_cols = st.columns(5)
        with anno_cols[0]:
            st.session_state.engineering_annotations["show_annotations"] = st.checkbox("📏 Dims", 
                value=st.session_state.engineering_annotations.get("show_annotations", True))
        with anno_cols[1]:
            st.session_state.engineering_annotations["show_wind"] = st.checkbox("💨 Wind", 
                value=st.session_state.engineering_annotations.get("show_wind", True))
        with anno_cols[2]:
            st.session_state.engineering_annotations["show_tie_down"] = st.checkbox("🔗 Tie", 
                value=st.session_state.engineering_annotations.get("show_tie_down", True))
        with anno_cols[3]:
            st.session_state.engineering_annotations["show_bracing"] = st.checkbox("📐 Brace", 
                value=st.session_state.engineering_annotations.get("show_bracing", True))
        with anno_cols[4]:
            st.session_state.engineering_annotations["show_load_path"] = st.checkbox("📊 Load", 
                value=st.session_state.engineering_annotations.get("show_load_path", True))
        
        # Generate 3D model
        if typ_key == "custom":
            fig = generate_custom_bounding_box(params)
            st.info("📝 Custom design — 3D view shows bounding box.")
        else:
            if typ_key == "saddle_span":
                fig = generate_saddle_span(params, materials, st.session_state.engineering_annotations)
            else:
                fig = GENERATORS[typ_key](params)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        
        # Structural analysis
        if typ_key == "saddle_span":
            with st.expander("📊 Structural Analysis & Load Combinations", expanded=True):
                m = materials
                span = params.get("B", 10.0)
                laa = params.get("LAA", 15.0)
                rise = params.get("A", 6.0)
                membrane_area = span * laa * 1.1
                
                steel_weight_kg = calculate_steel_weight(m.get("steel_grade", "S355"), 
                    m.get("section_type", "CHS"), m.get("section_size", "CHS 150x6"), span * 2)
                fabric_weight_kg = calculate_fabric_weight(m.get("fabric_type", "PVC-coated Polyester"), 
                    m.get("fabric_thickness", 0.8), membrane_area)
                total_weight_kg = steel_weight_kg + fabric_weight_kg
                total_weight_kn = total_weight_kg / 100
                wind_load = calculate_wind_load(m.get("wind_speed", 40), membrane_area)
                num_bays = m.get("num_bays", 2)
                bracing_x = generate_bracing_positions(span, num_bays)
                num_anchors = len(bracing_x) * 2
                tie_down_force = calculate_tie_down_force(wind_load, total_weight_kn, num_anchors, 
                    m.get("tie_down_vertical_angle", 45), m.get("safety_factor", 1.5))
                rope_capacity = MATERIAL_DATABASE["cables"].get(m.get("wire_rope_type", "Galvanized Steel (6x19)"), {})
                rope_capacity_kn = rope_capacity.get("breaking_load", 55)
                rope_check = tie_down_force < rope_capacity_kn / 1.5
                
                # Load combinations
                load_data = {
                    "dead_load": total_weight_kn,
                    "live_load": m.get("live_load", 0.5),
                    "snow_load": m.get("snow_load", 0.5),
                    "wind_load": wind_load
                }
                combinations = generate_load_combinations(load_data, m)
                
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("Self-Weight", f"{total_weight_kn:.1f} kN")
                    st.metric("Membrane Area", f"{membrane_area:.1f} m²")
                with col_s2:
                    st.metric("Wind Load", f"{wind_load:.1f} kN")
                    st.metric("Tie-Down Force/Anchor", f"{tie_down_force:.1f} kN")
                with col_s3:
                    st.metric("Rope Capacity", f"{rope_capacity_kn:.1f} kN")
                    st.metric("✅ Rope Check", "✅ PASS" if rope_check else "❌ FAIL", 
                        delta="Safe" if rope_check else "Unsafe", 
                        delta_color="normal" if rope_check else "inverse")
                
                # Load combinations table
                st.write("**Load Combinations (Eurocode):**")
                combo_df = pd.DataFrame({
                    "Combination": list(combinations.keys()),
                    "Value (kN)": [f"{v:.2f}" for v in combinations.values()]
                })
                st.dataframe(combo_df, use_container_width=True, hide_index=True)
                
                if not rope_check:
                    st.error(f"⚠️ Tie-down force ({tie_down_force:.1f} kN) exceeds rope capacity ({rope_capacity_kn:.1f} kN). Please increase cable diameter or add more anchors.")
                else:
                    st.success("✅ All preliminary checks passed. Structure is stable under wind loads.")
        
        # Action buttons
        st.divider()
        col_act1, col_act2, col_act3, col_act4, col_act5 = st.columns(5)
        with col_act1:
            if st.button("📸 Hi-Res Image", use_container_width=True, type="primary"):
                if typ_key != "custom" and typ_key in GENERATORS:
                    try:
                        if typ_key == "saddle_span":
                            fig_render = generate_saddle_span(params, materials, st.session_state.engineering_annotations)
                        else:
                            fig_render = GENERATORS[typ_key](params)
                        img_bytes = fig_render.to_image(format="png", scale=3, width=1200, height=800)
                        b64 = base64.b64encode(img_bytes).decode()
                        href = f'<a href="data:image/png;base64,{b64}" download="design_high_res.png">📥 Download</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    except Exception as e:
                        st.warning(f"⚠️ Render failed: {e}")
                else:
                    st.info("Render available for standard typologies.")
        with col_act2:
            if st.button("📄 PDF Report", use_container_width=True):
                pdf_bytes = generate_pdf_report(
                    params, materials, typ, info, 
                    st.session_state.qa_answers, st.session_state.comments
                )
                if pdf_bytes:
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="SDS_Report_{info.get("reference", "project")}.pdf">📥 Download PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                else:
                    st.warning("PDF generation requires reportlab. Install: pip install reportlab")
        with col_act3:
            if st.button("📊 Compare", use_container_width=True):
                st.session_state.comparison_mode = True
                st.rerun()
        with col_act4:
            if st.button("🔒 Lock", use_container_width=True):
                st.session_state.locked = True
                save_cache()
                st.rerun()
        with col_act5:
            if st.button("💾 Save", use_container_width=True, type="primary"):
                save_project_as_new()
    
    st.divider()
    
    # Q&A Section
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
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Comments
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">💬 Comments / Instructions</div>', unsafe_allow_html=True)
    comments = st.text_area("", value=st.session_state.comments, height=80, key="understand_comments", 
        placeholder="Type your comment here...")
    st.session_state.comments = comments
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("🔒 LOCK & PROCEED", use_container_width=True, type="primary"):
        st.session_state.locked = True
        save_cache()
        st.success("✅ Design locked! You can now view the final model and export.")

# ============================================================
# MAIN DASHBOARD
# ============================================================

def render_dashboard():
    st.title("🏗️ SDS Design Studio Pro")
    st.caption("Parametric design for tensile structures, membrane roofs, and steel frames.")
    st.markdown("### *Roots Protected. Branches Free. Ecosystem Growing.*")
    
    projects = get_projects_list()
    
    # Dashboard cards
    col1, col2, col3, col4 = st.columns(4)
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
    with col4:
        history_count = len(st.session_state.design_history)
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="icon">📊</div>
            <div class="value">{history_count}</div>
            <div class="label">Design History</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ New Design", use_container_width=True, type="primary"):
            st.session_state.show_registration = True
            st.rerun()
    with col2:
        if projects:
            if st.button("📂 Open Project", use_container_width=True):
                st.session_state.show_project_browser = True
                st.rerun()
        else:
            st.button("📂 No Projects", use_container_width=True, disabled=True)
    with col3:
        if st.session_state.design_history:
            if st.button("📊 Compare Designs", use_container_width=True):
                st.session_state.comparison_mode = True
                st.rerun()
    
    if projects:
        st.subheader("📋 Recent Projects")
        for proj in projects[:5]:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**{proj.get('name', 'Untitled')}** — 👤 {proj.get('client', 'N/A')} | {proj.get('typology', 'Unknown')}")
            with col2:
                if st.button("📂 Open", key=f"dash_load_{proj.get('file')}", use_container_width=True):
                    if load_project_from_file(proj.get('file')):
                        st.rerun()
            with col3:
                status = "🔒" if proj.get("locked") else "📝"
                st.write(status)
            with col4:
                st.caption(proj.get("date", "")[:10])
            st.divider()
    
    st.caption("💡 Select 'New Design' to start a project, or open an existing project from the list above.")

# ============================================================
# MAIN UI RENDER LOOP
# ============================================================

# --- TOP BAR ---
cols = st.columns([0.8, 1.5, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
with cols[0]:
    if st.button("🏗️", key="sds_logo", help="Go to Dashboard"):
        go_to_dashboard()
        st.rerun()
    st.caption("SDS Pro")
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
    if st.button("🏠 Dash", use_container_width=True, help="Main Dashboard"):
        go_to_dashboard()
        st.rerun()
with cols[4]:
    if st.session_state.project_registered:
        if st.button("📂 Proj", use_container_width=True, help="Saved projects"):
            st.session_state.show_project_browser = not st.session_state.show_project_browser
            st.rerun()
with cols[5]:
    if st.session_state.project_registered and st.session_state.typology:
        if st.button("💾 Save", use_container_width=True, help="Save project"):
            save_project_as_new()
            st.rerun()
with cols[6]:
    if st.session_state.project_registered:
        if st.button("📋 New", use_container_width=True, help="New project"):
            clear_cache()
            st.rerun()
with cols[7]:
    if st.session_state.design_history:
        if st.button("📊 Comp", use_container_width=True, help="Compare designs"):
            st.session_state.comparison_mode = not st.session_state.comparison_mode
            st.rerun()
with cols[8]:
    if st.session_state.locked and st.session_state.typology:
        if st.button("🔓 Unlock", use_container_width=True, type="primary"):
            st.session_state.locked = False
            save_cache()
            st.rerun()

# --- PROJECT BROWSER ---
if st.session_state.show_project_browser:
    st.subheader("📂 Saved Projects")
    if st.button("⬅ Back", use_container_width=True):
        st.session_state.show_project_browser = False
        st.rerun()
    projects = get_projects_list()
    if not projects:
        st.info("No saved projects found.")
    else:
        projects.sort(key=lambda x: x.get("date", ""), reverse=True)
        for proj in projects:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"📌 {proj.get('name', 'Untitled')} — 👤 {proj.get('client', 'Unknown')}")
                st.caption(f"🏗️ {proj.get('typology', 'Unknown')} | 🔑 {proj.get('reference', 'N/A')} {'🔒' if proj.get('locked') else '📝'}")
            with col2:
                if st.button("📂 Load", key=f"load_{proj.get('file')}", use_container_width=True):
                    if load_project_from_file(proj.get('file')):
                        st.success("✅ Project loaded!")
                        st.session_state.show_project_browser = False
                        st.rerun()
            with col3:
                if st.button("🗑️ Del", key=f"del_{proj.get('file')}", use_container_width=True):
                    if delete_project_file(proj.get('file')):
                        st.success(f"✅ Deleted.")
                        st.rerun()
            with col4:
                st.caption(proj.get("date", "")[:10])
            st.divider()
    st.stop()

# --- COMPARISON MODE ---
if st.session_state.comparison_mode:
    render_comparison_mode()
    st.stop()

# --- DASHBOARD ---
if not st.session_state.project_registered and not st.session_state.show_registration:
    render_dashboard()
    st.stop()

# --- PROJECT REGISTRATION ---
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
                architect = st.text_input("🏛️ Architect", placeholder="e.g., Foster + Partners")
                engineer = st.text_input("🔧 Engineer", placeholder="e.g., Arup")
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
                    save_cache()
                    st.rerun()
        st.caption("All data is cached locally. Your project will resume where you left off.")
        st.stop()

# --- TYPOLOGY CATALOG ---
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
                st.session_state.design_phase = "understand"
                save_cache()
                st.rerun()
        idx += 1
    st.caption("💡 Select a structure type to begin designing.")
    st.stop()

# --- UNIFIED SDS-UNDERSTAND WORKSPACE ---
if st.session_state.typology is not None:
    render_unified_workspace()

st.caption("SDS Platform v5.0 | Pro Edition | Roots Protected. Branches Free. Ecosystem Growing.")
save_cache()
