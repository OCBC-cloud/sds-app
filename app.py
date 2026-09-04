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
import matplotlib.pyplot as plt

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SDS Design Studio - Saddle Span Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# DARK MODE CSS
# ============================================================
dark_mode_css = """
    <style>
    .stApp {
        background-color: #0a0e17 !important;
        color: #f0f4fa !important;
    }
    .stApp > header { display: none !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; max-width: 100% !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 600 !important; }
    label { color: #ffffff !important; font-weight: 400 !important; }
    .stButton > button {
        background-color: #1e2a3a !important;
        color: #ffffff !important;
        border: 1px solid #2a3a4f !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        width: 100% !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover { background-color: #2a3a4f !important; border-color: #4a7a9c !important; }
    .stButton > button[kind="primary"] { background-color: #f39c12 !important; color: #0a0e17 !important; border: none !important; font-weight: 600 !important; }
    .stButton > button[kind="primary"]:hover { background-color: #f1c40f !important; }
    .stNumberInput > div > div > input { background-color: #141e2b !important; color: #ffffff !important; border: 1px solid #2a3a4f !important; border-radius: 8px !important; }
    .stSelectbox > div > div > div { background-color: #141e2b !important; color: #ffffff !important; border: 1px solid #2a3a4f !important; border-radius: 8px !important; }
    .stTextArea textarea { color: #ffffff !important; background-color: #141e2b !important; border: 1px solid #2a3a4f !important; border-radius: 8px !important; }
    .stAlert { background-color: #1e2a3a !important; border-left: 4px solid #f39c12 !important; color: #f0f4fa !important; }
    .stInfo { background-color: #1a2a3a !important; border-left: 4px solid #4a7a9c !important; color: #f0f4fa !important; }
    .stSuccess { background-color: #1a3a2a !important; border-left: 4px solid #2ecc71 !important; color: #f0f4fa !important; }
    .stError { background-color: #3a1a1a !important; border-left: 4px solid #e74c3c !important; color: #f0f4fa !important; }
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    
    .dashboard-card { background-color: #141e2b; border-radius: 12px; padding: 1.5rem 1rem; border: 1px solid #1e2a3a; text-align: center; margin-bottom: 0.5rem; }
    .dashboard-card .icon { font-size: 2.5rem; }
    .dashboard-card .value { color: #ffffff; font-size: 1.5rem; font-weight: 700; }
    .dashboard-card .label { color: #8a9aaa; font-size: 0.8rem; margin-top: 0.3rem; }
    
    .sds-card { background-color: #141e2b; border-radius: 12px; padding: 1rem 1.2rem; border: 1px solid #1e2a3a; margin-bottom: 0.8rem; }
    .sds-card .title { color: #ffffff; font-weight: 600; font-size: 1rem; margin-bottom: 0.5rem; }
    .sds-card .content { color: #b0c4de; font-size: 0.9rem; }
    
    .standard-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 0.3rem;
    }
    .badge-eu { background-color: #003399; color: #ffffff; }
    .badge-cn { background-color: #DE2910; color: #ffffff; }
    .badge-uk { background-color: #012169; color: #ffffff; }
    .badge-my { background-color: #CC0000; color: #ffffff; }
    .badge-us { background-color: #B22234; color: #ffffff; }
    
    .health-score-good { color: #2ecc71; font-weight: 700; font-size: 1.5rem; }
    .health-score-fair { color: #f39c12; font-weight: 700; font-size: 1.5rem; }
    .health-score-poor { color: #e74c3c; font-weight: 700; font-size: 1.5rem; }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# ENHANCED MATERIAL DATABASE
# ============================================================
# ===== STEEL GRADES =====
STEEL_GRADES = {
    "S235": {"fy": 235, "fu": 360, "E": 210000, "density": 7850, "cost_per_kg": 0.90, "description": "General structural steel"},
    "S275": {"fy": 275, "fu": 430, "E": 210000, "density": 7850, "cost_per_kg": 1.00, "description": "Standard structural steel"},
    "S355": {"fy": 355, "fu": 490, "E": 210000, "density": 7850, "cost_per_kg": 1.20, "description": "High strength steel"},
    "S420": {"fy": 420, "fu": 520, "E": 210000, "density": 7850, "cost_per_kg": 1.50, "description": "Very high strength steel"},
    "S460": {"fy": 460, "fu": 550, "E": 210000, "density": 7850, "cost_per_kg": 1.80, "description": "Ultra-high strength steel"}
}

# ===== ALUMINUM GRADES =====
ALUMINUM_GRADES = {
    "6061-T6": {"fy": 276, "fu": 310, "E": 69000, "density": 2700, "cost_per_kg": 4.50, "description": "General purpose aluminum"},
    "6063-T6": {"fy": 214, "fu": 241, "E": 69000, "density": 2700, "cost_per_kg": 4.00, "description": "Architectural aluminum"},
    "5083-H116": {"fy": 230, "fu": 310, "E": 69000, "density": 2660, "cost_per_kg": 5.00, "description": "Marine grade aluminum"},
    "7022-T6": {"fy": 460, "fu": 510, "E": 69000, "density": 2780, "cost_per_kg": 8.00, "description": "High strength aluminum"}
}

# ===== WOOD GRADES =====
WOOD_GRADES = {
    "Glulam": {"fy": 40, "fu": 55, "E": 12000, "density": 550, "cost_per_m3": 800, "description": "Glued laminated timber"},
    "LVL": {"fy": 45, "fu": 60, "E": 13500, "density": 600, "cost_per_m3": 700, "description": "Laminated veneer lumber"},
    "CLT": {"fy": 30, "fu": 45, "E": 10000, "density": 500, "cost_per_m3": 1200, "description": "Cross-laminated timber"},
    "Mass Timber": {"fy": 35, "fu": 50, "E": 11000, "density": 550, "cost_per_m3": 1000, "description": "Mass timber panels"}
}

# ===== COMPOSITE GRADES =====
COMPOSITE_GRADES = {
    "GFRP": {"fy": 300, "fu": 450, "E": 30000, "density": 2000, "cost_per_kg": 15.00, "description": "Glass fiber reinforced polymer"},
    "CFRP": {"fy": 600, "fu": 900, "E": 120000, "density": 1600, "cost_per_kg": 30.00, "description": "Carbon fiber reinforced polymer"}
}

# ===== SECTION PROPERTIES (ENHANCED) =====
SECTION_PROPERTIES = {
    "CHS 88.9x4.0": {"A": 1067, "I": 0.93e6, "W_el": 20.9e3, "i": 29.5, "weight": 8.38, "type": "CHS"},
    "CHS 114.3x5.0": {"A": 1717, "I": 2.53e6, "W_el": 44.2e3, "i": 38.4, "weight": 13.5, "type": "CHS"},
    "CHS 139.7x6.3": {"A": 2642, "I": 5.90e6, "W_el": 84.5e3, "i": 47.3, "weight": 20.7, "type": "CHS"},
    "CHS 168.3x7.1": {"A": 3600, "I": 11.5e6, "W_el": 137e3, "i": 56.5, "weight": 28.3, "type": "CHS"},
    "CHS 219.1x8.0": {"A": 5305, "I": 29.0e6, "W_el": 265e3, "i": 73.9, "weight": 41.6, "type": "CHS"},
    "CHS 273.0x10.0": {"A": 8263, "I": 69.0e6, "W_el": 506e3, "i": 91.4, "weight": 64.9, "type": "CHS"},
    "CHS 323.9x12.5": {"A": 12228, "I": 148e6, "W_el": 912e3, "i": 110.0, "weight": 96.0, "type": "CHS"},
    "RHS 150x100x6": {"A": 2784, "I": 8.3e6, "W_el": 111e3, "i": 54.6, "weight": 21.8, "type": "RHS"},
    "RHS 200x150x8": {"A": 5104, "I": 30.1e6, "W_el": 301e3, "i": 76.8, "weight": 40.0, "type": "RHS"},
    "RHS 250x150x10": {"A": 7500, "I": 71.0e6, "W_el": 568e3, "i": 97.3, "weight": 58.9, "type": "RHS"},
    "I-150": {"A": 2130, "I": 16.0e6, "W_el": 213e3, "i": 86.7, "weight": 16.7, "type": "I-Beam"},
    "I-200": {"A": 3310, "I": 38.0e6, "W_el": 380e3, "i": 107.1, "weight": 26.0, "type": "I-Beam"},
    "I-250": {"A": 4820, "I": 76.0e6, "W_el": 608e3, "i": 125.6, "weight": 37.8, "type": "I-Beam"},
    "I-300": {"A": 6720, "I": 136e6, "W_el": 907e3, "i": 142.3, "weight": 52.8, "type": "I-Beam"},
    "I-350": {"A": 9020, "I": 226e6, "W_el": 1290e3, "i": 158.3, "weight": 70.8, "type": "I-Beam"},
    "I-400": {"A": 11800, "I": 348e6, "W_el": 1740e3, "i": 171.8, "weight": 92.6, "type": "I-Beam"},
    "Box 200x100x8": {"A": 4544, "I": 28.3e6, "W_el": 283e3, "i": 78.9, "weight": 35.7, "type": "Box"},
    "Box 250x150x10": {"A": 7400, "I": 72.0e6, "W_el": 576e3, "i": 98.6, "weight": 58.1, "type": "Box"},
    "Box 300x200x12": {"A": 11424, "I": 156.0e6, "W_el": 1040e3, "i": 116.8, "weight": 89.7, "type": "Box"},
    "Glulam 150x300": {"A": 45000, "I": 337.5e6, "W_el": 2250e3, "i": 86.6, "weight": 24.75, "type": "Wood"},
    "Glulam 200x400": {"A": 80000, "I": 1066.7e6, "W_el": 5333e3, "i": 115.5, "weight": 44.0, "type": "Wood"},
    "Aluminum 150x150x5": {"A": 2900, "I": 8.1e6, "W_el": 108e3, "i": 52.8, "weight": 7.83, "type": "Aluminum"}
}

# ============================================================
# SHAPE FUNCTIONS
# ============================================================
def get_beam_shape(x, span, rise, shape_type="parabolic"):
    """Calculate beam height at position x based on shape type"""
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
    else:
        return rise * (1 - x_norm**2)

# ============================================================
# TRUSS FUNCTIONS
# ============================================================
def generate_truss_members(x, z_beam, truss_type="warren", num_panels=4):
    """Generate truss member coordinates"""
    members = []
    n = len(x)
    panel_size = n // num_panels
    
    if truss_type == "warren":
        # V-shaped diagonals
        for i in range(0, n - panel_size, panel_size):
            j = i + panel_size
            # Top chord
            members.append(("top", i, j))
            # Bottom chord
            members.append(("bottom", i, j))
            # Diagonal
            members.append(("diag", i, j))
            members.append(("diag", j, i))
    elif truss_type == "pratt":
        # Vertical + diagonal
        for i in range(0, n - panel_size, panel_size):
            j = i + panel_size
            members.append(("top", i, j))
            members.append(("bottom", i, j))
            members.append(("vertical", i, j))
            members.append(("diag", i, j))
    elif truss_type == "howe":
        # Vertical + diagonal (opposite direction)
        for i in range(0, n - panel_size, panel_size):
            j = i + panel_size
            members.append(("top", i, j))
            members.append(("bottom", i, j))
            members.append(("vertical", i, j))
            members.append(("diag", j, i))
    elif truss_type == "vierendeel":
        # Rectangular with rigid joints
        for i in range(0, n - panel_size, panel_size):
            j = i + panel_size
            members.append(("top", i, j))
            members.append(("bottom", i, j))
            members.append(("vertical", i, j))
    
    return members

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
if "comments" not in st.session_state:
    st.session_state.comments = ""
if "show_project_browser" not in st.session_state:
    st.session_state.show_project_browser = False
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False
if "show_structural_report" not in st.session_state:
    st.session_state.show_structural_report = False
if "selected_standard" not in st.session_state:
    st.session_state.selected_standard = "EU"

# Enhanced Materials State
if "materials" not in st.session_state:
    st.session_state.materials = {
        "standard": "EU",
        "material_type": "Steel",
        "steel_grade": "S355",
        "aluminum_grade": "6061-T6",
        "wood_grade": "Glulam",
        "composite_grade": "GFRP",
        "section_size": "CHS 168.3x7.1",
        "fabric_type": "PVC-coated Polyester",
        "fabric_thickness": 0.8,
        "wire_rope_type": "6x19 Galvanized",
        "wire_rope_diameter": 12,
        "num_bays": 2,
        "tie_down_vertical_angle": 45,
        "tie_down_horizontal_spread": 30,
        "wind_zone": "Zone 2",
        "terrain_category": "II",
        "building_height": 10.0,
        "importance_factor": 1.0,
        "safety_factor": 1.5,
        "shape_type": "parabolic",
        "member_type": "single_beam",
        "truss_type": "warren",
        "anchoring_pattern": "standard",
        "prestress_level": "medium",
        "custom_prestress": 3.0
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
        "materials": st.session_state.materials,
        "selected_standard": st.session_state.selected_standard
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)
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
                        "standard": data.get("selected_standard", "EU")
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
            st.session_state.selected_standard = data.get("selected_standard", "EU")
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
    st.session_state.comments = ""
    st.session_state.show_project_browser = False
    st.session_state.show_registration = False
    st.session_state.show_structural_report = False
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    save_cache()

def save_project():
    if not st.session_state.project_info.get("name"):
        st.error("⚠️ Project name is required")
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
        "materials": st.session_state.materials,
        "selected_standard": st.session_state.selected_standard
    }
    filename = f"project_{ref}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(CACHE_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    st.success(f"✅ Project saved!")
    update_projects_index()
    save_cache()

def get_projects_list():
    if os.path.exists(PROJECTS_LIST_FILE):
        with open(PROJECTS_LIST_FILE, "r") as f:
            return json.load(f)
    return []

# Load cache
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
    st.session_state.selected_standard = cached.get("selected_standard", "EU")

# ============================================================
# STANDARD-SPECIFIC FUNCTIONS
# ============================================================
def get_standard_label(standard_code):
    labels = {
        "EU": "🇪🇺 Eurocode (EN 1993/EN 1991)",
        "CN": "🇨🇳 China (GB 50009/GB/T 1591)",
        "UK": "🇬🇧 British (BS 5950/BS 6399)",
        "MY": "🇲🇾 Malaysia (MS EN 1993/MS EN 1991)",
        "US": "🇺🇸 USA (ASTM/ASCE 7)"
    }
    return labels.get(standard_code, standard_code)

# ============================================================
# ENHANCED 3D GENERATOR - SADDLE SPAN WITH ALL OPTIONS
# ============================================================
def generate_saddle_span(params, materials=None):
    span = params.get("B", 10.0)
    rise = params.get("A", 6.0)
    laa = params.get("LAA", 15.0)
    num_points = 50

    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()

    # Get shape and member type from materials
    shape_type = materials.get("shape_type", "parabolic") if materials else "parabolic"
    member_type = materials.get("member_type", "single_beam") if materials else "single_beam"
    truss_type = materials.get("truss_type", "warren") if materials else "warren"
    anchoring_pattern = materials.get("anchoring_pattern", "standard") if materials else "standard"
    prestress_level = materials.get("prestress_level", "medium") if materials else "medium"
    
    # Prestress values
    prestress_values = {"none": 0, "low": 1.5, "medium": 3.0, "high": 5.0}
    if prestress_level == "custom":
        prestress = materials.get("custom_prestress", 3.0) if materials else 3.0
    else:
        prestress = prestress_values.get(prestress_level, 3.0)

    # Generate beam shape
    x = np.linspace(-span/2, span/2, num_points)
    z_beam = get_beam_shape(x, span, rise, shape_type)
    
    # Beam offsets (for width)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    y2 = laa/2 * (1 - (2 * x / span)**2)

    fig = go.Figure()

    # ===== DRAW BEAMS/TRUSSES =====
    if member_type == "single_beam":
        # Single beam
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
        
    elif member_type == "planar_truss":
        # Planar truss
        truss_members = generate_truss_members(x, z_beam, truss_type, min(4, num_points//4))
        
        # Top chord (Beam 1)
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_beam,
            mode='lines', name='Beam 1 (Truss)',
            line=dict(color='#FF6B6B', width=5)
        ))
        # Top chord (Beam 2)
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_beam,
            mode='lines', name='Beam 2 (Truss)',
            line=dict(color='#FF6B6B', width=5)
        ))
        
        # Bottom chords (offset downward)
        z_bottom = z_beam * 0.7
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_bottom,
            mode='lines', name='Bottom Chord 1',
            line=dict(color='#FF9B6B', width=4, dash='dot')
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_bottom,
            mode='lines', name='Bottom Chord 2',
            line=dict(color='#FF9B6B', width=4, dash='dot')
        ))
        
        # Diagonals and verticals (simplified - just show pattern)
        for i in range(0, num_points - 5, 5):
            idx = i
            idx_next = min(i + 5, num_points - 1)
            if idx != idx_next:
                # Diagonal from top to bottom
                fig.add_trace(go.Scatter3d(
                    x=[x[idx], x[idx_next]],
                    y=[y1[idx], y1[idx_next]],
                    z=[z_beam[idx], z_bottom[idx_next]],
                    mode='lines',
                    line=dict(color='#FFB6A0', width=2),
                    showlegend=False
                ))
                fig.add_trace(go.Scatter3d(
                    x=[x[idx], x[idx_next]],
                    y=[y2[idx], y2[idx_next]],
                    z=[z_beam[idx], z_bottom[idx_next]],
                    mode='lines',
                    line=dict(color='#FFB6A0', width=2),
                    showlegend=False
                ))

    elif member_type == "space_truss":
        # Space truss - double layer grid
        fig.add_trace(go.Scatter3d(
            x=x, y=y1, z=z_beam,
            mode='lines', name='Top Layer 1',
            line=dict(color='#FF6B6B', width=4)
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y2, z=z_beam,
            mode='lines', name='Top Layer 2',
            line=dict(color='#FF6B6B', width=4)
        ))
        # Add grid lines
        for i in range(0, num_points, 5):
            fig.add_trace(go.Scatter3d(
                x=[x[i]]*2, y=[y1[i], y2[i]], z=[z_beam[i], z_beam[i]],
                mode='lines',
                line=dict(color='#FF9B6B', width=2, dash='dot'),
                showlegend=False
            ))

    # ===== MEMBRANE SURFACE =====
    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    # Prestress factor affects membrane stiffness (visual representation)
    prestress_factor = 1 + prestress / 10.0

    for i, x_pos in enumerate(x):
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = z_beam[i]
        for j, v_val in enumerate(np.linspace(0, 1, num_points)):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            saddle_factor = 1 - 0.3 * (1 - (2 * v_val - 1)**2)
            z_pos = z_at_x * saddle_factor * prestress_factor
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    # Opacity based on prestress (higher prestress = more transparent)
    opacity = max(0.3, min(0.7, 0.5 + prestress / 20.0))

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
        opacity=opacity, showscale=False, name='Membrane'
    ))

    # ===== APEX AND SUPPORTS =====
    fig.add_trace(go.Scatter3d(
        x=[0], y=[y1[num_points//2]], z=[z_beam[num_points//2]],
        mode='markers', name='Apex 1',
        marker=dict(color='#FFD93D', size=10, symbol='diamond')
    ))
    fig.add_trace(go.Scatter3d(
        x=[0], y=[y2[num_points//2]], z=[z_beam[num_points//2]],
        mode='markers', name='Apex 2',
        marker=dict(color='#FFD93D', size=10, symbol='diamond')
    ))
    fig.add_trace(go.Scatter3d(
        x=[-span/2, span/2],
        y=[0, 0],
        z=[0, 0],
        mode='markers', name='Supports',
        marker=dict(color='#4ECDC4', size=8, symbol='square')
    ))

    # ===== BRACING AND TIE-DOWNS =====
    if materials:
        num_bays = materials.get("num_bays", 2)
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        horizontal_spread = materials.get("tie_down_horizontal_spread", 30)
        
        bracing_x = generate_bracing_positions(span, num_bays)
        
        # Store bracing points for tie-downs
        bracing_points = []
        
        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            y1_pos = y1[idx]
            y2_pos = y2[idx]
            z_pos = z_beam[idx]
            
            bracing_points.append({
                "x": bx,
                "y1": y1_pos,
                "y2": y2_pos,
                "z": z_pos,
                "idx": idx
            })
            
            # Draw bracing
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[y1_pos, y2_pos], z=[z_pos, z_pos],
                mode='lines', name='Bracing',
                line=dict(color='#FF6B6B', width=3, dash='dash'),
                showlegend=False
            ))
        
        # ===== TIE-DOWNS WITH ANCHORING PATTERN =====
        if anchoring_pattern == "standard":
            # Use bracing points only
            anchor_x_positions = bracing_x
        elif anchoring_pattern == "continuous":
            # Use more points along beam
            anchor_x_positions = np.linspace(-span/2 * 0.8, span/2 * 0.8, num_bays * 4).tolist()
        elif anchoring_pattern == "hybrid":
            # Use bracing points + additional mid-points
            extra_points = []
            for i in range(len(bracing_x) - 1):
                mid = (bracing_x[i] + bracing_x[i+1]) / 2
                extra_points.append(mid)
            anchor_x_positions = sorted(bracing_x + extra_points)
        else:
            anchor_x_positions = bracing_x
        
        # Calculate tie-down anchors
        tie_down_anchors = calculate_tie_down_positions(
            span, laa, rise, anchor_x_positions, vertical_angle, horizontal_spread
        )
        
        # Draw tie-downs
        for anchor in tie_down_anchors:
            bx = anchor["beam_x"]
            idx = np.argmin(np.abs(x - bx))
            beam_z = z_beam[idx]
            beam_y = anchor["beam_y"]
            
            fig.add_trace(go.Scatter3d(
                x=[bx, anchor["anchor_x"]],
                y=[beam_y, anchor["anchor_y"]],
                z=[beam_z, anchor["anchor_z"]],
                mode='lines', name='Tie-Down',
                line=dict(color='#FFD93D', width=3),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter3d(
                x=[anchor["anchor_x"]],
                y=[anchor["anchor_y"]],
                z=[anchor["anchor_z"]],
                mode='markers', name='Anchor',
                marker=dict(color='#FF4444', size=8, symbol='x'),
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
            bgcolor='rgba(10,14,23,0.7)',
            bordercolor='#2a3a4f',
            borderwidth=1
        )
    )
    return fig

def generate_bracing_positions(span, num_bays):
    if num_bays == 1:
        return [0.0]
    elif num_bays == 2:
        return [-span/3, span/3]
    elif num_bays == 3:
        return [-span/4, 0.0, span/4]
    else:
        return np.linspace(-span/2 * 0.8, span/2 * 0.8, num_bays).tolist()

def calculate_tie_down_positions(span, laa, height, x_positions, vertical_angle, horizontal_spread):
    vertical_rad = np.radians(vertical_angle)
    horizontal_rad = np.radians(horizontal_spread)
    distance = height * np.tan(vertical_rad)
    
    anchors = []
    beam_ys = [-laa/2, laa/2]
    
    for bx in x_positions:
        for beam_y in beam_ys:
            if beam_y < 0:
                y_direction = -1
            else:
                y_direction = 1
            
            anchor_x = bx + distance * np.cos(horizontal_rad) * (1 if bx >= 0 else -1)
            anchor_y = beam_y + distance * np.sin(horizontal_rad) * y_direction
            
            anchors.append({
                "beam_x": bx,
                "beam_y": beam_y,
                "anchor_x": anchor_x,
                "anchor_y": anchor_y,
                "anchor_z": 0
            })
    
    return anchors

# ============================================================
# OTHER GENERATORS (Placeholders for other structures)
# ============================================================
def generate_tent(params):
    span = params.get("span_width", 10.0)
    ridge = params.get("ridge_height", 5.0)
    bays = params.get("num_bays", 4)
    bay_dist = params.get("bay_distance", 5.0)
    total_len = bays * bay_dist

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=[0,0], y=[0,total_len], z=[ridge,ridge],
        mode='lines', name='Ridge',
        line=dict(width=8, color='#f39c12')
    ))
    fig.add_trace(go.Scatter3d(
        x=[-span/2,-span/2], y=[0,total_len], z=[0,0],
        mode='lines', name='Eave Left',
        line=dict(width=5, color='#4a7a9c')
    ))
    fig.add_trace(go.Scatter3d(
        x=[span/2,span/2], y=[0,total_len], z=[0,0],
        mode='lines', name='Eave Right',
        line=dict(width=5, color='#4a7a9c')
    ))
    
    X = np.linspace(-span/2, span/2, 30)
    Y = np.linspace(0, total_len, 30)
    X, Y = np.meshgrid(X, Y)
    Z = ridge * (1 - (X/(span/2))**2) * (1 - (Y/total_len)**2 * 0.1)
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z, opacity=0.5,
        colorscale='Reds', showscale=False, name='Fabric'
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0)
    )
    return fig

def generate_tensile(params):
    mast = params.get("mast_height", 8.0)
    length = params.get("span_length", 20.0)
    width = params.get("span_width", 15.0)
    cables = params.get("cable_count", 4)

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=[0,0], y=[0,0], z=[0,mast],
        mode='lines', name='Mast',
        line=dict(width=10, color='#f39c12')
    ))
    
    X = np.linspace(-length/2, length/2, 30)
    Y = np.linspace(-width/2, width/2, 30)
    X, Y = np.meshgrid(X, Y)
    Z = mast * np.exp(-((X/(length/2))**2 + (Y/(width/2))**2) * 0.5)
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z, opacity=0.4,
        colorscale='Greens', showscale=False, name='Membrane'
    ))
    
    for i in range(cables):
        angle = i * 2*np.pi/cables
        x_end = length/2 * np.cos(angle)
        y_end = width/2 * np.sin(angle)
        fig.add_trace(go.Scatter3d(
            x=[0, x_end], y=[0, y_end], z=[mast, 0],
            mode='lines', name=f'Cable {i+1}',
            line=dict(width=4, color='#4a7a9c')
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Length (m)', yaxis_title='Width (m)', zaxis_title='Height (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
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
    fig.add_trace(go.Scatter3d(
        x=x, y=[0]*len(x), z=z,
        mode='lines', name='Portal Frame',
        line=dict(width=8, color='#4a7a9c')
    ))
    for i in range(bays):
        y = i * bay_spacing
        fig.add_trace(go.Scatter3d(
            x=x, y=[y]*len(x), z=z,
            mode='lines',
            line=dict(width=4, color='#4a7a9c', opacity=0.3),
            showlegend=False
        ))
    
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), np.linspace(-span/2, span/2, 30))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z, opacity=0.3,
        colorscale='Greys', showscale=False, name='Roof'
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
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
            mode='lines', line=dict(color='#4a7a9c', width=3),
            showlegend=False
        ))
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
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
# ENGINEERING FUNCTIONS
# ============================================================
def calculate_wind_pressure_standard(wind_zone, terrain_category, height, importance_factor, standard="EU"):
    """Calculate wind pressure using selected standard"""
    # Simple implementation for now
    return {
        "basic_wind_speed": 37.2,
        "terrain_roughness": "Suburban",
        "height_factor": 0.86,
        "peak_pressure": 0.8,
        "design_pressure": 0.8,
        "zone_description": "Zone 2",
        "standard": standard,
        "standard_label": get_standard_label(standard)
    }

def calculate_steel_capacity_standard(grade, section, length, safety_factor, standard="EU", material_type="Steel"):
    """Calculate steel capacity using selected standard"""
    # Get material properties based on type
    if material_type == "Steel" and grade in STEEL_GRADES:
        material = STEEL_GRADES[grade]
    elif material_type == "Aluminum" and grade in ALUMINUM_GRADES:
        material = ALUMINUM_GRADES[grade]
    elif material_type == "Wood" and grade in WOOD_GRADES:
        material = WOOD_GRADES[grade]
    elif material_type == "Composite" and grade in COMPOSITE_GRADES:
        material = COMPOSITE_GRADES[grade]
    else:
        material = STEEL_GRADES["S355"]
    
    section_data = SECTION_PROPERTIES.get(section, SECTION_PROPERTIES["CHS 168.3x7.1"])
    
    fy = material["fy"]
    A = section_data["A"]
    I = section_data["I"]
    W_el = section_data["W_el"]
    weight = section_data["weight"]
    
    N_crd = (A * fy) / (safety_factor * 1000)
    M_crd = (W_el * fy) / (safety_factor * 1e6)
    
    L = length
    i = (I / A)**0.5 / 10
    lambda_bar = L / i if i > 0 else 0
    
    if lambda_bar < 0.2:
        chi = 1.0
    elif lambda_bar < 1.0:
        chi = 1.0 / (1 + lambda_bar**2)
    else:
        chi = 1.0 / (lambda_bar**2 + 0.5)
    
    N_buck = chi * N_crd
    
    return {
        "grade": grade,
        "material_type": material_type,
        "section": section,
        "fy": fy,
        "area": A,
        "weight_kg_m": weight,
        "N_crd": N_crd,
        "M_crd": M_crd,
        "radius_of_gyration": i,
        "slenderness": lambda_bar,
        "N_buckling": N_buck,
        "efficiency": N_buck / N_crd if N_crd > 0 else 0,
        "standard": standard,
        "standard_label": get_standard_label(standard)
    }

def calculate_cable_size_standard(force_kn, safety_factor, cable_type):
    """Calculate cable size"""
    cable_data = {
        "6x19 Galvanized": {"breaking_load": {6: 20, 8: 35, 10: 55, 12: 80, 14: 105, 16: 140, 18: 180, 20: 220}},
        "6x19 Stainless": {"breaking_load": {6: 25, 8: 42, 10: 65, 12: 95, 14: 125, 16: 160, 18: 200, 20: 245}}
    }
    
    cable = cable_data.get(cable_type, cable_data["6x19 Galvanized"])
    required_breaking_load = force_kn * safety_factor
    
    selected_diameter = 12
    selected_breaking_load = 80
    
    for diam, load in sorted(cable["breaking_load"].items()):
        if load >= required_breaking_load:
            selected_diameter = diam
            selected_breaking_load = load
            break
    
    return {
        "cable_type": cable_type,
        "selected_diameter": selected_diameter,
        "breaking_load": selected_breaking_load,
        "required_breaking_load": required_breaking_load,
        "safety_factor": safety_factor,
        "is_adequate": selected_breaking_load >= required_breaking_load
    }

def generate_structural_health_report(params, materials):
    """Generate comprehensive structural health report"""
    span = params.get("B", 10.0)
    laa = params.get("LAA", 15.0)
    rise = params.get("A", 6.0)
    
    m = materials
    standard = m.get("standard", "EU")
    
    wind_result = calculate_wind_pressure_standard(
        m.get("wind_zone", "Zone 2"),
        m.get("terrain_category", "II"),
        m.get("building_height", 10.0),
        m.get("importance_factor", 1.0),
        standard
    )
    
    material_type = m.get("material_type", "Steel")
    grade = m.get("steel_grade", "S355")
    
    steel_capacity = calculate_steel_capacity_standard(
        grade,
        m.get("section_size", "CHS 168.3x7.1"),
        span,
        m.get("safety_factor", 1.5),
        standard,
        material_type
    )
    
    membrane_area = span * laa * 1.1
    wind_force = wind_result["design_pressure"] * membrane_area
    
    num_anchors = m.get("num_bays", 2) * 2
    tie_down_force = (wind_force * 0.8) / num_anchors if num_anchors > 0 else 0
    
    cable_selection = calculate_cable_size_standard(
        tie_down_force,
        m.get("safety_factor", 1.5),
        m.get("wire_rope_type", "6x19 Galvanized")
    )
    
    # Health Score
    health_score = 100
    
    if wind_result["design_pressure"] > 1.5:
        health_score -= 10
    elif wind_result["design_pressure"] > 1.0:
        health_score -= 5
    
    if steel_capacity["efficiency"] < 0.5:
        health_score -= 15
    elif steel_capacity["efficiency"] < 0.7:
        health_score -= 8
    
    if not cable_selection["is_adequate"]:
        health_score -= 20
    
    if steel_capacity["slenderness"] > 100:
        health_score -= 10
    elif steel_capacity["slenderness"] > 50:
        health_score -= 5
    
    health_score = max(0, min(100, health_score))
    
    if health_score >= 80:
        status = "GOOD"
        color = "#2ecc71"
        recommendation = "✅ Structure appears sound. Continue with design."
    elif health_score >= 60:
        status = "FAIR"
        color = "#f39c12"
        recommendation = "⚠️ Some minor concerns identified. Consider reinforcing weak areas."
    else:
        status = "POOR"
        color = "#e74c3c"
        recommendation = "❌ Significant concerns identified. Major strengthening required."
    
    return {
        "health_score": health_score,
        "health_status": status,
        "health_color": color,
        "recommendation": recommendation,
        "standard_label": get_standard_label(standard),
        "wind_analysis": wind_result,
        "steel_capacity": steel_capacity,
        "wind_force": wind_force,
        "tie_down_force": tie_down_force,
        "cable_selection": cable_selection,
        "membrane_area": membrane_area,
        "num_anchors": num_anchors,
        "span": span,
        "rise": rise,
        "laa": laa,
        "detailed_checks": {
            "wind_pressure_check": wind_result["design_pressure"] < 2.0,
            "steel_capacity_check": steel_capacity["efficiency"] > 0.5,
            "cable_adequacy_check": cable_selection["is_adequate"],
            "slenderness_check": steel_capacity["slenderness"] < 100
        }
    }

# ============================================================
# UI FUNCTIONS
# ============================================================
def render_structural_health_report(report):
    """Render the structural health report"""
    st.markdown("## 🏥 STRUCTURAL HEALTH REPORT")
    st.markdown(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    st.markdown(f"*Standard: {report.get('standard_label', 'EU')}*")
    st.markdown("---")
    
    score = report["health_score"]
    status = report["health_status"]
    color = report["health_color"]
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background-color: #141e2b; border-radius: 16px; border: 3px solid {color};">
            <div style="font-size: 4rem; font-weight: 700; color: {color};">{score}%</div>
            <div style="font-size: 2rem; font-weight: 600; color: {color};">{status}</div>
            <div style="color: #b0c4de; margin-top: 0.5rem; font-size: 1.1rem;">{report['recommendation']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("✅ Detailed Checks")
    checks = report["detailed_checks"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Wind Pressure", "✅ PASS" if checks["wind_pressure_check"] else "❌ FAIL")
    with col2:
        st.metric("Steel Capacity", "✅ PASS" if checks["steel_capacity_check"] else "❌ FAIL")
    with col3:
        st.metric("Cable Adequacy", "✅ PASS" if checks["cable_adequacy_check"] else "❌ FAIL")
    with col4:
        st.metric("Slenderness", "✅ PASS" if checks["slenderness_check"] else "⚠️ CHECK")
    
    st.markdown("---")
    
    st.subheader("🌪️ Wind Analysis")
    wind = report["wind_analysis"]
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Standard:** {wind['standard_label']}")
        st.write(f"**Wind Zone:** {wind.get('zone_description', 'N/A')}")
        st.write(f"**Basic Wind Speed:** {wind['basic_wind_speed']:.1f} m/s")
    with col2:
        st.write(f"**Terrain Category:** {wind['terrain_roughness']}")
        st.write(f"**Peak Pressure:** {wind['peak_pressure']:.2f} kN/m²")
        st.write(f"**Design Pressure:** {wind['design_pressure']:.2f} kN/m²")
    
    st.markdown("---")
    
    st.subheader("🏗️ Steel Member Capacity")
    steel = report["steel_capacity"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Material:** {steel['material_type']}")
        st.write(f"**Grade:** {steel['grade']}")
        st.write(f"**Section:** {steel['section']}")
    with col2:
        st.write(f"**fy:** {steel['fy']} MPa")
        st.write(f"**Area:** {steel['area']:.0f} mm²")
        st.write(f"**Weight:** {steel['weight_kg_m']:.1f} kg/m")
    with col3:
        st.write(f"**Compression Capacity:** {steel['N_crd']:.1f} kN")
        st.write(f"**Buckling Capacity:** {steel['N_buckling']:.1f} kN")
        st.write(f"**Efficiency:** {steel['efficiency']*100:.1f}%")
    
    st.markdown("---")
    
    st.subheader("🔗 Tie-Down System & Cable Sizing")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Membrane Area:** {report['membrane_area']:.1f} m²")
        st.write(f"**Number of Anchors:** {report['num_anchors']}")
        st.write(f"**Wind Force:** {report['wind_force']:.1f} kN")
        st.write(f"**Tie-Down Force/Anchor:** {report['tie_down_force']:.1f} kN")
    with col2:
        cable = report["cable_selection"]
        st.write(f"**Cable Type:** {cable['cable_type']}")
        st.write(f"**Selected Diameter:** {cable['selected_diameter']} mm")
        st.write(f"**Breaking Load:** {cable['breaking_load']:.1f} kN")
        st.write(f"**Status:** {'✅ ADEQUATE' if cable['is_adequate'] else '❌ INADEQUATE'}")

def render_dashboard():
    st.title("🏗️ SDS Design Studio - Saddle Span Pro")
    st.caption("Advanced Saddle Span Design with Shape, Member Type, and Material Options")
    
    projects = get_projects_list()
    
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
            <div class="value">4</div>
            <div class="label">Shape Variants</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="icon">🔧</div>
            <div class="value">3</div>
            <div class="label">Member Types</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="icon">🧱</div>
            <div class="value">12+</div>
            <div class="label">Materials</div>
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

def render_workspace():
    params = st.session_state.params
    materials = st.session_state.materials
    typ_key = st.session_state.typology
    typ = TYPOLOGIES[typ_key] if typ_key in TYPOLOGIES else TYPOLOGIES["saddle_span"]
    info = st.session_state.project_info
    standard = materials.get("standard", "EU")
    
    st.markdown("## 🧠 Saddle Span Design Workspace")
    st.caption(f"🏕️ Shape: {materials.get('shape_type', 'parabolic').title()} | Member: {materials.get('member_type', 'single_beam').replace('_', ' ').title()} | Anchoring: {materials.get('anchoring_pattern', 'standard').title()}")
    
    # Health Report Button
    col_report1, col_report2 = st.columns([4, 1])
    with col_report2:
        if st.button("📊 Health Report", use_container_width=True, type="primary"):
            st.session_state.show_structural_report = True
            st.rerun()
    
    if st.session_state.show_structural_report:
        report = generate_structural_health_report(params, materials)
        render_structural_health_report(report)
        if st.button("❌ Close Report", use_container_width=True, key="close_report"):
            st.session_state.show_structural_report = False
            st.rerun()
        st.markdown("---")
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        # Project Info
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📊 Project</div>', unsafe_allow_html=True)
        st.write(f"**Name:** {info.get('name', 'Untitled')}")
        st.write(f"**Client:** {info.get('client', 'Unknown')}")
        st.write(f"**Ref:** {info.get('reference', 'N/A')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== SHAPE SELECTION =====
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔄 Shape Variant</div>', unsafe_allow_html=True)
        shape_options = ["parabolic", "elliptical", "circular", "catenary"]
        shape_labels = ["Parabolic", "Elliptical", "Circular", "Catenary"]
        current_shape = materials.get("shape_type", "parabolic")
        if current_shape not in shape_options:
            current_shape = "parabolic"
        shape_idx = shape_options.index(current_shape) if current_shape in shape_options else 0
        
        materials["shape_type"] = st.selectbox(
            "Select Shape",
            shape_labels,
            index=shape_idx,
            key="shape_select",
            help="Different curve geometries for the saddle span"
        )
        shape_map = dict(zip(shape_labels, shape_options))
        materials["shape_type"] = shape_map[materials["shape_type"]]
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== MEMBER TYPE SELECTION =====
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔧 Member Type</div>', unsafe_allow_html=True)
        member_options = ["single_beam", "planar_truss", "space_truss"]
        member_labels = ["Single Beam", "Planar Truss", "Space Truss"]
        current_member = materials.get("member_type", "single_beam")
        if current_member not in member_options:
            current_member = "single_beam"
        member_idx = member_options.index(current_member) if current_member in member_options else 0
        
        materials["member_type"] = st.selectbox(
            "Select Member Type",
            member_labels,
            index=member_idx,
            key="member_select",
            help="Single beam, planar truss, or space truss"
        )
        member_map = dict(zip(member_labels, member_options))
        materials["member_type"] = member_map[materials["member_type"]]
        
        # Truss type (if truss selected)
        if materials["member_type"] in ["planar_truss", "space_truss"]:
            truss_options = ["warren", "pratt", "howe", "vierendeel"]
            truss_labels = ["Warren", "Pratt", "Howe", "Vierendeel"]
            current_truss = materials.get("truss_type", "warren")
            if current_truss not in truss_options:
                current_truss = "warren"
            truss_idx = truss_options.index(current_truss) if current_truss in truss_options else 0
            
            materials["truss_type"] = st.selectbox(
                "Truss Type",
                truss_labels,
                index=truss_idx,
                key="truss_select"
            )
            truss_map = dict(zip(truss_labels, truss_options))
            materials["truss_type"] = truss_map[materials["truss_type"]]
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== MATERIAL SELECTION =====
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🧱 Material</div>', unsafe_allow_html=True)
        
        material_types = ["Steel", "Aluminum", "Wood", "Composite"]
        current_material_type = materials.get("material_type", "Steel")
        if current_material_type not in material_types:
            current_material_type = "Steel"
        
        materials["material_type"] = st.selectbox(
            "Material Type",
            material_types,
            index=material_types.index(current_material_type),
            key="material_type_select"
        )
        
        # Grade selection based on material type
        if materials["material_type"] == "Steel":
            grade_options = list(STEEL_GRADES.keys())
            current_grade = materials.get("steel_grade", "S355")
            if current_grade not in grade_options:
                current_grade = "S355"
            materials["steel_grade"] = st.selectbox(
                "Steel Grade",
                grade_options,
                index=grade_options.index(current_grade),
                key="steel_grade_select"
            )
            grade_display = f"fy: {STEEL_GRADES[materials['steel_grade']]['fy']} MPa"
            
        elif materials["material_type"] == "Aluminum":
            grade_options = list(ALUMINUM_GRADES.keys())
            current_grade = materials.get("aluminum_grade", "6061-T6")
            if current_grade not in grade_options:
                current_grade = "6061-T6"
            materials["aluminum_grade"] = st.selectbox(
                "Aluminum Grade",
                grade_options,
                index=grade_options.index(current_grade),
                key="aluminum_grade_select"
            )
            grade_display = f"fy: {ALUMINUM_GRADES[materials['aluminum_grade']]['fy']} MPa"
            
        elif materials["material_type"] == "Wood":
            grade_options = list(WOOD_GRADES.keys())
            current_grade = materials.get("wood_grade", "Glulam")
            if current_grade not in grade_options:
                current_grade = "Glulam"
            materials["wood_grade"] = st.selectbox(
                "Wood Grade",
                grade_options,
                index=grade_options.index(current_grade),
                key="wood_grade_select"
            )
            grade_display = f"Strength: {WOOD_GRADES[materials['wood_grade']]['fy']} MPa"
            
        else:  # Composite
            grade_options = list(COMPOSITE_GRADES.keys())
            current_grade = materials.get("composite_grade", "GFRP")
            if current_grade not in grade_options:
                current_grade = "GFRP"
            materials["composite_grade"] = st.selectbox(
                "Composite Type",
                grade_options,
                index=grade_options.index(current_grade),
                key="composite_grade_select"
            )
            grade_display = f"Strength: {COMPOSITE_GRADES[materials['composite_grade']]['fy']} MPa"
        
        st.caption(f"📊 {grade_display}")
        
        # Section Selection
        # Filter sections by material type (simplified - show all for now)
        section_options = list(SECTION_PROPERTIES.keys())
        current_section = materials.get("section_size", "CHS 168.3x7.1")
        if current_section not in section_options:
            current_section = "CHS 168.3x7.1"
        
        materials["section_size"] = st.selectbox(
            "Section Size",
            section_options,
            index=section_options.index(current_section),
            key="section_select"
        )
        
        # Show section properties
        section_data = SECTION_PROPERTIES[materials["section_size"]]
        st.caption(f"📐 A: {section_data['A']:.0f} mm² | Weight: {section_data['weight']:.1f} kg/m")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== ANCHORING PATTERN =====
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📍 Anchoring Pattern</div>', unsafe_allow_html=True)
        pattern_options = ["standard", "continuous", "hybrid"]
        pattern_labels = ["Standard (Bracing Points)", "Continuous (Full Length)", "Hybrid (Mixed)"]
        current_pattern = materials.get("anchoring_pattern", "standard")
        if current_pattern not in pattern_options:
            current_pattern = "standard"
        pattern_idx = pattern_options.index(current_pattern) if current_pattern in pattern_options else 0
        
        materials["anchoring_pattern"] = st.selectbox(
            "Anchoring Pattern",
            pattern_labels,
            index=pattern_idx,
            key="pattern_select",
            help="Tie-down anchor placement pattern"
        )
        pattern_map = dict(zip(pattern_labels, pattern_options))
        materials["anchoring_pattern"] = pattern_map[materials["anchoring_pattern"]]
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== PRESTRESS OPTIONS =====
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔧 Prestress Level</div>', unsafe_allow_html=True)
        prestress_options = ["none", "low", "medium", "high", "custom"]
        prestress_labels = ["None (0 kN/m)", "Low (1.5 kN/m)", "Medium (3.0 kN/m)", "High (5.0 kN/m)", "Custom"]
        current_prestress = materials.get("prestress_level", "medium")
        if current_prestress not in prestress_options:
            current_prestress = "medium"
        prestress_idx = prestress_options.index(current_prestress) if current_prestress in prestress_options else 0
        
        materials["prestress_level"] = st.selectbox(
            "Prestress Level",
            prestress_labels,
            index=prestress_idx,
            key="prestress_select"
        )
        prestress_map = dict(zip(prestress_labels, prestress_options))
        materials["prestress_level"] = prestress_map[materials["prestress_level"]]
        
        if materials["prestress_level"] == "custom":
            materials["custom_prestress"] = st.slider(
                "Custom Prestress (kN/m)",
                min_value=0.0, max_value=10.0, step=0.5,
                value=float(materials.get("custom_prestress", 3.0)),
                key="custom_prestress"
            )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== BAYS & TIE-DOWN ANGLES =====
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔗 Bracing & Tie-Downs</div>', unsafe_allow_html=True)
        materials["num_bays"] = st.selectbox("Bracing Bays", [1, 2, 3], index=1, key="num_bays")
        
        materials["tie_down_vertical_angle"] = st.slider(
            "Tie-Down Vertical Angle (°)", 
            min_value=20, max_value=70, step=5, 
            value=int(materials.get("tie_down_vertical_angle", 45)),
            key="tie_down_vertical",
            help="Angle from horizontal - higher = steeper cable"
        )
        
        materials["tie_down_horizontal_spread"] = st.slider(
            "Tie-Down Horizontal Spread (°)", 
            min_value=10, max_value=60, step=5, 
            value=int(materials.get("tie_down_horizontal_spread", 30)),
            key="tie_down_spread",
            help="Outward spread angle from the beam"
        )
        
        materials["wire_rope_type"] = st.selectbox(
            "Cable Type",
            ["6x19 Galvanized", "6x19 Stainless"],
            index=0,
            key="cable_type"
        )
        
        materials["safety_factor"] = st.number_input(
            "Safety Factor",
            min_value=1.0, max_value=3.0, step=0.1,
            value=float(materials.get("safety_factor", 1.5)),
            key="safety_factor"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== STANDARD SELECTION =====
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🌍 Design Standard</div>', unsafe_allow_html=True)
        standard_options = ["EU", "CN", "UK", "MY", "US"]
        standard_labels = [get_standard_label(s) for s in standard_options]
        current_standard = materials.get("standard", "EU")
        if current_standard not in standard_options:
            current_standard = "EU"
        
        selected_label = st.selectbox(
            "Select Standard",
            standard_labels,
            index=standard_options.index(current_standard),
            key="standard_select"
        )
        materials["standard"] = standard_options[standard_labels.index(selected_label)]
        st.session_state.selected_standard = materials["standard"]
        
        badge_class = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(materials["standard"], "badge-eu")
        st.markdown(f'<span class="standard-badge {badge_class}">{materials["standard"]}</span> {get_standard_label(materials["standard"])}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Comments
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">💬 Notes</div>', unsafe_allow_html=True)
        comments = st.text_area("", value=st.session_state.comments, height=80, placeholder="Add design notes...", key="comments_area")
        st.session_state.comments = comments
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.subheader("🔬 3D Model")
        st.caption("🟥 Red = Structure | 🟨 Yellow = Tie-Downs | 🔴 Red X = Ground Anchors")
        
        fig = generate_saddle_span(params, materials)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        
        st.divider()
        col_act1, col_act2, col_act3, col_act4, col_act5 = st.columns(5)
        with col_act1:
            if st.button("🔒 Lock", use_container_width=True, key="lock_btn"):
                st.session_state.locked = True
                save_cache()
                st.rerun()
        with col_act2:
            if st.button("💾 Save", use_container_width=True, type="primary", key="save_btn"):
                save_project()
        with col_act3:
            if st.button("📊 Report", use_container_width=True, key="report_btn"):
                st.session_state.show_structural_report = True
                st.rerun()
        with col_act4:
            if st.button("📋 New", use_container_width=True, key="new_btn"):
                go_to_dashboard()
                st.rerun()
        with col_act5:
            if st.button("🏠 Home", use_container_width=True, key="home_btn"):
                go_to_dashboard()
                st.rerun()
    
    st.divider()
    
    # Parameters
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">📐 Main Parameters</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        params["A"] = st.number_input("Rise (A) m", min_value=2.0, max_value=20.0, step=0.5, value=float(params.get("A", 6.0)), format="%.1f", key="param_A")
    with col2:
        params["B"] = st.number_input("Span (B) m", min_value=4.0, max_value=40.0, step=0.5, value=float(params.get("B", 10.0)), format="%.1f", key="param_B")
    with col3:
        params["LAA"] = st.number_input("Apex Dist (LAA) m", min_value=4.0, max_value=50.0, step=0.5, value=float(params.get("LAA", 15.0)), format="%.1f", key="param_LAA")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Q&A
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">❓ Design Confirmation</div>', unsafe_allow_html=True)
    for i, q in enumerate(typ.get("qa", [])):
        key = f"qa_{i}"
        default = st.session_state.qa_answers.get(key, "Yes")
        ans = st.radio(q, ["Yes", "No", "Not Sure"], index=["Yes", "No", "Not Sure"].index(default), key=f"qa_{i}")
        st.session_state.qa_answers[key] = ans
    st.markdown('</div>', unsafe_allow_html=True)
    
    save_cache()

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
            "Are there two primary curved beams?",
            "Are both beams supported at their lower ends?",
            "Is the membrane attached continuously along the beams?",
            "Is A the vertical rise from support to apex?",
            "Is B the horizontal span between supports?",
            "Is LAA the distance between the two apexes?"
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
            "Sidewalls open or enclosed?"
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
            "Edge cables included?"
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
            "num_bays": {"label": "Number of Bays", "min": 2, "max": 30, "step": 1, "default": 5}
        },
        "qa": [
            "Column bases pin-supported?",
            "Roof purlin-supported?",
            "Overhead crane present?",
            "Fully enclosed cladding?"
        ]
    },
    "custom": {
        "name": "Custom Design",
        "icon": "🧩",
        "params": {
            "width": {"label": "Width (m)", "min": 1.0, "max": 100.0, "step": 0.5, "default": 10.0},
            "length": {"label": "Length (m)", "min": 1.0, "max": 100.0, "step": 0.5, "default": 15.0},
            "height": {"label": "Height (m)", "min": 1.0, "max": 50.0, "step": 0.5, "default": 8.0}
        },
        "qa": [
            "This is a custom design. Add your description below."
        ]
    }
}

# ============================================================
# MAIN APP ROUTING
# ============================================================

# Top Bar
col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 1, 1])
with col1:
    if st.button("🏗️", help="Dashboard", key="logo_btn"):
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
    standard = st.session_state.materials.get("standard", "EU")
    badge_class = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(standard, "badge-eu")
    st.markdown(f'<span class="standard-badge {badge_class}">{standard}</span>', unsafe_allow_html=True)
with col5:
    if st.session_state.locked:
        st.caption("🔒 Locked")
with col6:
    if st.session_state.locked:
        if st.button("🔓 Unlock", use_container_width=True, key="unlock_btn"):
            st.session_state.locked = False
            save_cache()
            st.rerun()
with col7:
    if st.session_state.project_registered and st.session_state.typology:
        if st.button("📊 Report", use_container_width=True, key="top_report_btn"):
            st.session_state.show_structural_report = True
            st.rerun()

# Project Browser
if st.session_state.show_project_browser:
    st.subheader("📂 Saved Projects")
    if st.button("⬅ Back", use_container_width=True, key="back_browser"):
        st.session_state.show_project_browser = False
        st.rerun()
    
    projects = get_projects_list()
    if not projects:
        st.info("No saved projects found.")
    else:
        for proj in projects:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.write(f"**{proj.get('name', 'Untitled')}** — {proj.get('client', 'Unknown')}")
                standard = proj.get('standard', 'EU')
                badge_class = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(standard, "badge-eu")
                st.markdown(f'<span class="standard-badge {badge_class}">{standard}</span> {proj.get("typology", "Unknown")} {"🔒" if proj.get("locked") else "📝"}', unsafe_allow_html=True)
            with col2:
                if st.button("Load", key=f"load_{proj.get('file')}"):
                    if load_project_from_file(proj.get('file')):
                        st.session_state.show_project_browser = False
                        st.rerun()
            with col3:
                if st.button("Delete", key=f"del_{proj.get('file')}"):
                    delete_project_file(proj.get('file'))
                    st.rerun()
            with col4:
                st.caption(proj.get("date", "")[:10])
            st.divider()
    st.stop()

# Registration
if st.session_state.show_registration:
    st.subheader("📋 New Project")
    if st.button("⬅ Back", use_container_width=True, key="back_reg"):
        st.session_state.show_registration = False
        st.rerun()
    
    with st.form("register_form"):
        name = st.text_input("Project Name *", placeholder="e.g., Marina Bay Canopy")
        client = st.text_input("Client Name *", placeholder="e.g., Marina Bay Sands")
        location = st.text_input("Location", placeholder="e.g., Singapore")
        standard = st.selectbox("Design Standard", ["EU", "CN", "UK", "MY", "US"], index=3)
        
        ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        st.caption(f"Reference: SDS-{ref}")
        
        submitted = st.form_submit_button("🚀 Start Design", use_container_width=True, type="primary")
        
        if submitted:
            if not name or not client:
                st.error("⚠️ Project Name and Client Name are required.")
            else:
                st.session_state.project_info = {
                    "name": name,
                    "client": client,
                    "location": location,
                    "reference": f"SDS-{ref}",
                    "date": datetime.now().isoformat()
                }
                st.session_state.project_registered = True
                st.session_state.show_registration = False
                st.session_state.selected_standard = standard
                st.session_state.materials["standard"] = standard
                save_cache()
                st.rerun()
    st.stop()

# Dashboard
if not st.session_state.project_registered:
    render_dashboard()
    st.stop()

# Typology Selection (Only Saddle Span for now)
if st.session_state.typology is None:
    st.subheader("Choose a structure type:")
    st.caption("🏕️ Saddle Span - Complete Module with Shape, Member, and Material Options")
    
    # Show only saddle span and basic placeholders for others
    cols = st.columns(2)
    with cols[0]:
        if st.button("🏕️ Saddle Span (Complete)", use_container_width=True, type="primary"):
            st.session_state.typology = "saddle_span"
            st.session_state.params = {p: v["default"] for p, v in TYPOLOGIES["saddle_span"]["params"].items()}
            st.session_state.qa_answers = {}
            st.session_state.locked = False
            save_cache()
            st.rerun()
    with cols[1]:
        st.button("⏳ More Coming Soon", use_container_width=True, disabled=True)
    st.stop()

# Main Workspace
render_workspace()

# Footer
st.divider()
st.caption("SDS Design Studio | Saddle Span Pro v2.0 | Shape / Member / Material / Anchoring / Prestress")

save_cache()
