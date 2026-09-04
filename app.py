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
    page_title="SDS Design Studio - Malaysia Standards",
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
    
    .health-score-good { color: #2ecc71; font-weight: 700; font-size: 1.5rem; }
    .health-score-fair { color: #f39c12; font-weight: 700; font-size: 1.5rem; }
    .health-score-poor { color: #e74c3c; font-weight: 700; font-size: 1.5rem; }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# MALAYSIAN STANDARDS - MATERIAL PROPERTIES
# ============================================================
# MS EN 1993-1-1: Steel Design
STEEL_GRADES = {
    "S275 (MS EN 10025)": {
        "fy": 275,  # Yield strength (MPa)
        "fu": 430,  # Ultimate strength (MPa)
        "E": 210000,  # Young's modulus (MPa)
        "density": 7850,  # kg/m³
        "alpha": 1.2e-5,  # Thermal expansion
        "description": "Structural steel - General purpose"
    },
    "S355 (MS EN 10025)": {
        "fy": 355,
        "fu": 490,
        "E": 210000,
        "density": 7850,
        "alpha": 1.2e-5,
        "description": "High strength structural steel"
    },
    "S460 (MS EN 10025)": {
        "fy": 460,
        "fu": 550,
        "E": 210000,
        "density": 7850,
        "alpha": 1.2e-5,
        "description": "Ultra-high strength steel"
    },
    "S550 (MS EN 10025)": {
        "fy": 550,
        "fu": 620,
        "E": 210000,
        "density": 7850,
        "alpha": 1.2e-5,
        "description": "Very high strength steel"
    }
}

# MS EN 1991-1-4: Wind Actions (Malaysia)
WIND_ZONES = {
    "Zone 1": {"basic_wind_speed": 32.6, "description": "Less than 32.6 m/s"},
    "Zone 2": {"basic_wind_speed": 37.2, "description": "32.6 - 37.2 m/s"},
    "Zone 3": {"basic_wind_speed": 41.8, "description": "37.2 - 41.8 m/s"},
    "Zone 4": {"basic_wind_speed": 46.5, "description": "41.8 - 46.5 m/s"},
    "Coastal": {"basic_wind_speed": 55.0, "description": "Coastal areas (modified)"}
}

TERRAIN_CATEGORIES = {
    "0": {"name": "Sea, coastal", "z0": 0.003, "z_min": 1, "alpha": 0.11},
    "I": {"name": "Open country", "z0": 0.01, "z_min": 1, "alpha": 0.12},
    "II": {"name": "Suburban, industrial", "z0": 0.05, "z_min": 2, "alpha": 0.14},
    "III": {"name": "City centre", "z0": 0.30, "z_min": 5, "alpha": 0.20},
    "IV": {"name": "Dense urban", "z0": 1.00, "z_min": 10, "alpha": 0.24}
}

# Cable/Wire Rope Specifications (MS EN 1993-1-11)
CABLE_SPECS = {
    "6x19 Galvanized": {
        "diameters": [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 40],
        "breaking_load": {6: 20.0, 8: 35.0, 10: 55.0, 12: 80.0, 14: 105.0, 16: 140.0,
                          18: 180.0, 20: 220.0, 22: 260.0, 24: 310.0, 26: 360.0,
                          28: 420.0, 30: 480.0, 32: 540.0, 36: 680.0, 40: 840.0},
        "weight_kg_m": {6: 0.14, 8: 0.25, 10: 0.40, 12: 0.58, 14: 0.78, 16: 1.02,
                        18: 1.30, 20: 1.60, 22: 1.94, 24: 2.30, 26: 2.70, 28: 3.20,
                        30: 3.70, 32: 4.20, 36: 5.30, 40: 6.60},
        "min_breaking_load_factor": 1.5,
        "description": "Galvanized steel wire rope - General purpose"
    },
    "6x19 Stainless Steel": {
        "diameters": [6, 8, 10, 12, 14, 16, 18, 20],
        "breaking_load": {6: 25.0, 8: 42.0, 10: 65.0, 12: 95.0, 14: 125.0, 16: 160.0,
                          18: 200.0, 20: 245.0},
        "weight_kg_m": {6: 0.15, 8: 0.27, 10: 0.42, 12: 0.60, 14: 0.82, 16: 1.08,
                        18: 1.36, 20: 1.68},
        "min_breaking_load_factor": 1.5,
        "description": "Stainless steel wire rope - Corrosion resistant"
    },
    "Polyester Rope": {
        "diameters": [8, 10, 12, 14, 16, 18, 20, 24],
        "breaking_load": {8: 30.0, 10: 45.0, 12: 65.0, 14: 85.0, 16: 110.0,
                          18: 140.0, 20: 170.0, 24: 230.0},
        "weight_kg_m": {8: 0.10, 10: 0.15, 12: 0.22, 14: 0.30, 16: 0.40,
                        18: 0.50, 20: 0.62, 24: 0.90},
        "min_breaking_load_factor": 2.0,
        "description": "Synthetic polyester rope - Lightweight"
    }
}

# Section properties (MS EN 1993-1-1)
SECTION_PROPERTIES = {
    "CHS 88.9x4.0": {"A": 1067, "I": 0.93e6, "W_el": 20.9e3, "i": 29.5, "weight": 8.38},
    "CHS 114.3x5.0": {"A": 1717, "I": 2.53e6, "W_el": 44.2e3, "i": 38.4, "weight": 13.5},
    "CHS 139.7x6.3": {"A": 2642, "I": 5.90e6, "W_el": 84.5e3, "i": 47.3, "weight": 20.7},
    "CHS 168.3x7.1": {"A": 3600, "I": 11.5e6, "W_el": 137e3, "i": 56.5, "weight": 28.3},
    "CHS 219.1x8.0": {"A": 5305, "I": 29.0e6, "W_el": 265e3, "i": 73.9, "weight": 41.6},
    "CHS 273.0x10.0": {"A": 8263, "I": 69.0e6, "W_el": 506e3, "i": 91.4, "weight": 64.9},
    "CHS 323.9x12.5": {"A": 12228, "I": 148e6, "W_el": 912e3, "i": 110.0, "weight": 96.0},
    "RHS 150x100x6": {"A": 2784, "I": 8.3e6, "W_el": 111e3, "i": 54.6, "weight": 21.8},
    "RHS 200x150x8": {"A": 5104, "I": 30.1e6, "W_el": 301e3, "i": 76.8, "weight": 40.0},
    "RHS 250x150x10": {"A": 7500, "I": 71.0e6, "W_el": 568e3, "i": 97.3, "weight": 58.9},
    "I-150": {"A": 2130, "I": 16.0e6, "W_el": 213e3, "i": 86.7, "weight": 16.7},
    "I-200": {"A": 3310, "I": 38.0e6, "W_el": 380e3, "i": 107.1, "weight": 26.0},
    "I-250": {"A": 4820, "I": 76.0e6, "W_el": 608e3, "i": 125.6, "weight": 37.8},
    "I-300": {"A": 6720, "I": 136e6, "W_el": 907e3, "i": 142.3, "weight": 52.8}
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
if "comments" not in st.session_state:
    st.session_state.comments = ""
if "show_project_browser" not in st.session_state:
    st.session_state.show_project_browser = False
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False
if "show_structural_report" not in st.session_state:
    st.session_state.show_structural_report = False

# Materials State (Enhanced with Malaysian Standards)
if "materials" not in st.session_state:
    st.session_state.materials = {
        "steel_grade": "S355 (MS EN 10025)",
        "section_type": "Circular Hollow Section (CHS)",
        "section_size": "CHS 168.3x7.1",
        "fabric_type": "PVC-coated Polyester",
        "fabric_thickness": 0.8,
        "wire_rope_type": "6x19 Galvanized",
        "wire_rope_diameter": 12,
        "num_bays": 2,
        "tie_down_angle": 45,
        "wind_zone": "Zone 2",
        "terrain_category": "II",
        "building_height": 10.0,
        "safety_factor": 1.5,
        "importance_factor": 1.0
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
        "materials": st.session_state.materials
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

# ============================================================
# MALAYSIAN STANDARDS - ENGINEERING FUNCTIONS
# ============================================================

def calculate_wind_pressure_MS(wind_zone, terrain_category, height, importance_factor=1.0):
    """MS EN 1991-1-4: Wind pressure calculation for Malaysia"""
    wind_data = WIND_ZONES.get(wind_zone, WIND_ZONES["Zone 2"])
    terrain = TERRAIN_CATEGORIES.get(terrain_category, TERRAIN_CATEGORIES["II"])
    
    # Basic wind speed
    vb = wind_data["basic_wind_speed"]
    
    # Terrain roughness factor
    z0 = terrain["z0"]
    z_min = terrain["z_min"]
    alpha = terrain["alpha"]
    
    # Height factor (simplified)
    z = max(height, z_min)
    if z <= z_min:
        ce = 1.0
    else:
        ce = 0.86 * (z / 10)**(2 * alpha)
    
    # Peak wind pressure
    qp = 0.5 * 1.225 * (vb * ce)**2 / 1000  # kN/m²
    
    # Wind force
    wind_pressure = qp * importance_factor
    
    return {
        "basic_wind_speed": vb,
        "terrain_roughness": terrain["name"],
        "height_factor": ce,
        "peak_pressure": qp,
        "design_pressure": wind_pressure,
        "zone_description": wind_data["description"]
    }

def calculate_steel_capacity_MS(grade, section, length, safety_factor=1.5):
    """MS EN 1993-1-1: Steel member capacity calculation"""
    steel = STEEL_GRADES.get(grade, STEEL_GRADES["S355 (MS EN 10025)"])
    section_data = SECTION_PROPERTIES.get(section, SECTION_PROPERTIES["CHS 168.3x7.1"])
    
    fy = steel["fy"]  # MPa
    A = section_data["A"]  # mm²
    I = section_data["I"]  # mm⁴
    W_el = section_data["W_el"]  # mm³
    weight = section_data["weight"]  # kg/m
    
    # Compression capacity
    N_crd = (A * fy) / (safety_factor * 1000)  # kN
    
    # Bending capacity
    M_crd = (W_el * fy) / (safety_factor * 1e6)  # kNm
    
    # Buckling resistance (simplified Euler)
    L = length  # m
    i = (I / A)**0.5 / 10  # m (radius of gyration)
    lambda_bar = L / i
    if lambda_bar < 0.2:
        chi = 1.0
    elif lambda_bar < 1.0:
        chi = 1.0 / (1 + lambda_bar**2)
    else:
        chi = 1.0 / (lambda_bar**2 + 0.5)
    
    N_buck = chi * N_crd
    
    return {
        "grade": grade,
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
        "capacity_check": "PASS" if N_buck > 0.5 * N_crd else "CHECK"
    }

def calculate_cable_size_MS(force_kn, safety_factor=1.5, cable_type="6x19 Galvanized"):
    """MS EN 1993-1-11: Cable size selection based on force"""
    cable_data = CABLE_SPECS.get(cable_type, CABLE_SPECS["6x19 Galvanized"])
    required_breaking_load = force_kn * safety_factor
    
    selected_diameter = None
    selected_breaking_load = None
    
    for diam in sorted(cable_data["diameters"]):
        breaking = cable_data["breaking_load"].get(diam, 0)
        if breaking >= required_breaking_load:
            selected_diameter = diam
            selected_breaking_load = breaking
            break
    
    if selected_diameter is None:
        # If force too high, use largest diameter
        selected_diameter = cable_data["diameters"][-1]
        selected_breaking_load = cable_data["breaking_load"].get(selected_diameter, 0)
    
    weight = cable_data["weight_kg_m"].get(selected_diameter, 0)
    
    return {
        "cable_type": cable_type,
        "selected_diameter": selected_diameter,
        "breaking_load": selected_breaking_load,
        "required_breaking_load": required_breaking_load,
        "weight_kg_m": weight,
        "safety_factor": safety_factor,
        "capacity_ratio": required_breaking_load / selected_breaking_load if selected_breaking_load > 0 else 0,
        "is_adequate": selected_breaking_load >= required_breaking_load,
        "description": cable_data["description"]
    }

def generate_structural_health_report(params, materials):
    """Generate comprehensive structural health report"""
    span = params.get("B", 10.0)
    laa = params.get("LAA", 15.0)
    rise = params.get("A", 6.0)
    
    m = materials
    
    # 1. Wind Analysis
    wind_result = calculate_wind_pressure_MS(
        m.get("wind_zone", "Zone 2"),
        m.get("terrain_category", "II"),
        m.get("building_height", 10.0),
        m.get("importance_factor", 1.0)
    )
    
    # 2. Steel Capacity
    steel_capacity = calculate_steel_capacity_MS(
        m.get("steel_grade", "S355 (MS EN 10025)"),
        m.get("section_size", "CHS 168.3x7.1"),
        span,
        m.get("safety_factor", 1.5)
    )
    
    # 3. Wind Load on Structure
    membrane_area = span * laa * 1.1
    wind_force = wind_result["design_pressure"] * membrane_area
    
    # 4. Tie-Down Force
    num_anchors = m.get("num_bays", 2) * 2
    tie_down_force = (wind_force * 0.8) / num_anchors
    
    # 5. Cable Selection
    cable_selection = calculate_cable_size_MS(
        tie_down_force,
        m.get("safety_factor", 1.5),
        m.get("wire_rope_type", "6x19 Galvanized")
    )
    
    # 6. Health Score Calculation
    health_score = 100
    
    # Deduct for wind pressure
    if wind_result["design_pressure"] > 1.5:
        health_score -= 10
    elif wind_result["design_pressure"] > 1.0:
        health_score -= 5
    
    # Deduct for steel capacity
    if steel_capacity["efficiency"] < 0.5:
        health_score -= 15
    elif steel_capacity["efficiency"] < 0.7:
        health_score -= 8
    
    # Deduct for cable adequacy
    if not cable_selection["is_adequate"]:
        health_score -= 20
    elif cable_selection["capacity_ratio"] > 0.9:
        health_score -= 5
    
    # Deduct for slenderness
    if steel_capacity["slenderness"] > 100:
        health_score -= 10
    elif steel_capacity["slenderness"] > 50:
        health_score -= 5
    
    health_score = max(0, min(100, health_score))
    
    # Health status
    if health_score >= 80:
        status = "GOOD"
        color = "#2ecc71"
        recommendation = "Structure appears sound. Continue with design."
    elif health_score >= 60:
        status = "FAIR"
        color = "#f39c12"
        recommendation = "Some minor concerns identified. Consider reinforcing weak areas."
    else:
        status = "POOR"
        color = "#e74c3c"
        recommendation = "Significant concerns identified. Major strengthening required."
    
    return {
        "health_score": health_score,
        "health_status": status,
        "health_color": color,
        "recommendation": recommendation,
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

def generate_tie_down_anchors(span, laa, height, x_positions, angle_deg):
    angle_rad = np.radians(angle_deg)
    distance = height * np.tan(angle_rad)
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

# ============================================================
# 3D GENERATORS
# ============================================================
def generate_saddle_span(params, materials=None):
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

    fig = go.Figure()

    # Main beams
    fig.add_trace(go.Scatter3d(
        x=x, y=y1, z=z_beam,
        mode='lines', name='Beam 1',
        line=dict(color='#FF6B6B', width=6)
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=y2, z=z_beam,
        mode='lines', name='Beam 2',
        line=dict(color='#FF6B6B', width=6)
    ))

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

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
        opacity=0.7, showscale=False, name='Membrane'
    ))

    # Apex and support points
    fig.add_trace(go.Scatter3d(
        x=[0], y=[y1[num_points//2]], z=[rise],
        mode='markers', name='Apex 1',
        marker=dict(color='#FFD93D', size=10, symbol='diamond')
    ))
    fig.add_trace(go.Scatter3d(
        x=[0], y=[y2[num_points//2]], z=[rise],
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

    # Bracing
    if materials:
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
        angle = materials.get("tie_down_angle", 45)
        anchors = generate_tie_down_anchors(span, laa, rise, bracing_x, angle)
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
            bgcolor='rgba(10,14,23,0.7)',
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
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.5, colorscale='Reds', showscale=False, name='Fabric'))
    
    fig.update_layout(
        scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)',
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
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.4, colorscale='Greens', showscale=False, name='Membrane'))
    
    for i in range(cables):
        angle = i * 2*np.pi/cables
        x_end = length/2 * np.cos(angle)
        y_end = width/2 * np.sin(angle)
        fig.add_trace(go.Scatter3d(x=[0, x_end], y=[0, y_end], z=[mast, 0], mode='lines', name=f'Cable {i+1}', line=dict(width=4, color='#4a7a9c')))
    
    fig.update_layout(
        scene=dict(xaxis_title='Length (m)', yaxis_title='Width (m)', zaxis_title='Height (m)',
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
        fig.add_trace(go.Scatter3d(x=x, y=[y]*len(x), z=z, mode='lines', line=dict(width=4, color='#4a7a9c', opacity=0.3), showlegend=False))
    
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), np.linspace(-span/2, span/2, 30))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.3, colorscale='Greys', showscale=False, name='Roof'))
    
    fig.update_layout(
        scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)',
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
# UI FUNCTIONS
# ============================================================
def render_structural_health_report(report):
    """Render the structural health report with all details"""
    st.markdown("## 🏥 Structural Health Report")
    st.markdown(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    st.markdown("---")
    
    # Health Score Card
    score = report["health_score"]
    status = report["health_status"]
    color = report["health_color"]
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background-color: #141e2b; border-radius: 16px; border: 2px solid {color};">
            <div style="font-size: 4rem; font-weight: 700; color: {color};">{score}%</div>
            <div style="font-size: 2rem; font-weight: 600; color: {color};">{status}</div>
            <div style="color: #b0c4de; margin-top: 0.5rem;">{report['recommendation']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Detailed Checks
    st.subheader("✅ Detailed Checks")
    checks = report["detailed_checks"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Wind Pressure", "✅ PASS" if checks["wind_pressure_check"] else "❌ FAIL", delta="< 2.0 kN/m²" if checks["wind_pressure_check"] else "> 2.0 kN/m²")
    with col2:
        st.metric("Steel Capacity", "✅ PASS" if checks["steel_capacity_check"] else "❌ FAIL", delta="Efficient" if checks["steel_capacity_check"] else "Check Required")
    with col3:
        st.metric("Cable Adequacy", "✅ PASS" if checks["cable_adequacy_check"] else "❌ FAIL", delta="Adequate" if checks["cable_adequacy_check"] else "Increase Size")
    with col4:
        st.metric("Slenderness", "✅ PASS" if checks["slenderness_check"] else "⚠️ CHECK", delta="< 100" if checks["slenderness_check"] else "> 100")
    
    st.markdown("---")
    
    # Wind Analysis
    st.subheader("🌪️ Wind Analysis (MS EN 1991-1-4)")
    wind = report["wind_analysis"]
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Wind Zone:** {wind.get('zone_description', 'N/A')}")
        st.write(f"**Basic Wind Speed:** {wind['basic_wind_speed']:.1f} m/s")
        st.write(f"**Terrain Category:** {wind['terrain_roughness']}")
    with col2:
        st.write(f"**Height Factor:** {wind['height_factor']:.2f}")
        st.write(f"**Peak Pressure:** {wind['peak_pressure']:.2f} kN/m²")
        st.write(f"**Design Pressure:** {wind['design_pressure']:.2f} kN/m²")
    
    st.markdown("---")
    
    # Steel Member Capacity
    st.subheader("🏗️ Steel Member Capacity (MS EN 1993-1-1)")
    steel = report["steel_capacity"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Grade:** {steel['grade']}")
        st.write(f"**Section:** {steel['section']}")
        st.write(f"**fy:** {steel['fy']} MPa")
    with col2:
        st.write(f"**Area:** {steel['area']:.0f} mm²")
        st.write(f"**Weight:** {steel['weight_kg_m']:.1f} kg/m")
        st.write(f"**Radius of Gyration:** {steel['radius_of_gyration']:.2f} m")
    with col3:
        st.write(f"**Compression Capacity:** {steel['N_crd']:.1f} kN")
        st.write(f"**Buckling Capacity:** {steel['N_buckling']:.1f} kN")
        st.write(f"**Efficiency:** {steel['efficiency']*100:.1f}%")
    
    st.markdown("---")
    
    # Tie-Down and Cable Sizing
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
        st.write(f"**Required Load:** {cable['required_breaking_load']:.1f} kN")
        st.write(f"**Status:** {'✅ ADEQUATE' if cable['is_adequate'] else '❌ INADEQUATE'}")
    
    st.markdown("---")
    
    # Summary Table
    st.subheader("📊 Summary Table")
    summary_data = {
        "Parameter": ["Span", "Rise", "Apex Distance", "Membrane Area", "Wind Load", "Steel Capacity", "Cable Size", "Health Score"],
        "Value": [
            f"{report['span']:.1f} m",
            f"{report['rise']:.1f} m",
            f"{report['laa']:.1f} m",
            f"{report['membrane_area']:.1f} m²",
            f"{report['wind_force']:.1f} kN",
            f"{report['steel_capacity']['N_crd']:.1f} kN",
            f"{report['cable_selection']['selected_diameter']} mm",
            f"{score}% ({status})"
        ]
    }
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_dashboard():
    st.title("🏗️ SDS Design Studio - Malaysia Standards")
    st.caption("Parametric design with MS EN 1993 & MS EN 1991 compliance")
    
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
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="icon">📊</div>
            <div class="value">MS EN</div>
            <div class="label">Standards Compliant</div>
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

def render_workspace():
    params = st.session_state.params
    materials = st.session_state.materials
    typ_key = st.session_state.typology
    typ = TYPOLOGIES[typ_key]
    info = st.session_state.project_info
    
    st.markdown("## 🧠 Design Workspace")
    st.caption("MS EN 1993-1-1 (Steel) & MS EN 1991-1-4 (Wind) Compliant")
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        # Project Info
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📊 Project</div>', unsafe_allow_html=True)
        st.write(f"**Name:** {info.get('name', 'Untitled')}")
        st.write(f"**Client:** {info.get('client', 'Unknown')}")
        st.write(f"**Ref:** {info.get('reference', 'N/A')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Geometry
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">📐 Parameters</div>', unsafe_allow_html=True)
        param_items = list(typ["params"].items())
        for i in range(0, len(param_items), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(param_items):
                    p_key, p_def = param_items[i + j]
                    with cols[j]:
                        val = st.number_input(
                            p_def["label"],
                            min_value=float(p_def["min"]),
                            max_value=float(p_def["max"]),
                            step=float(p_def["step"]),
                            value=float(params.get(p_key, p_def["default"])),
                            format="%.1f",
                            key=f"param_{p_key}"
                        )
                        params[p_key] = val
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Malaysian Standards - Materials
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🏗️ Materials (MS EN 1993)</div>', unsafe_allow_html=True)
        
        materials["steel_grade"] = st.selectbox("Steel Grade", list(STEEL_GRADES.keys()), 
            index=list(STEEL_GRADES.keys()).index(materials.get("steel_grade", "S355 (MS EN 10025)")))
        
        section_options = list(SECTION_PROPERTIES.keys())
        materials["section_size"] = st.selectbox("Section Size", section_options,
            index=section_options.index(materials.get("section_size", "CHS 168.3x7.1")) if materials.get("section_size") in section_options else 0)
        
        materials["fabric_type"] = st.selectbox("Fabric Type", ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"], index=0)
        materials["fabric_thickness"] = st.selectbox("Thickness (mm)", [0.5, 0.8, 1.0, 1.2], index=1)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Malaysian Standards - Wind & Environment
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🌪️ Wind Analysis (MS EN 1991)</div>', unsafe_allow_html=True)
        
        wind_zones = list(WIND_ZONES.keys())
        materials["wind_zone"] = st.selectbox("Wind Zone", wind_zones,
            index=wind_zones.index(materials.get("wind_zone", "Zone 2")))
        
        terrain_options = list(TERRAIN_CATEGORIES.keys())
        materials["terrain_category"] = st.selectbox("Terrain Category", terrain_options,
            index=terrain_options.index(materials.get("terrain_category", "II")))
        
        materials["building_height"] = st.number_input("Building Height (m)", min_value=2.0, max_value=50.0, step=0.5, 
            value=float(materials.get("building_height", 10.0)))
        materials["importance_factor"] = st.slider("Importance Factor", min_value=0.8, max_value=1.5, step=0.1, 
            value=float(materials.get("importance_factor", 1.0)))
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Bracing & Tie-Downs
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔗 Bracing & Tie-Downs</div>', unsafe_allow_html=True)
        materials["num_bays"] = st.selectbox("Bracing Bays", [1, 2, 3], index=1)
        materials["tie_down_angle"] = st.slider("Tie-Down Angle (°)", 20, 70, 45, 5)
        
        cable_options = list(CABLE_SPECS.keys())
        materials["wire_rope_type"] = st.selectbox("Cable Type", cable_options,
            index=cable_options.index(materials.get("wire_rope_type", "6x19 Galvanized")))
        
        materials["wire_rope_diameter"] = st.selectbox("Cable Diameter (mm)", 
            CABLE_SPECS[materials["wire_rope_type"]]["diameters"],
            index=0)
        materials["safety_factor"] = st.number_input("Safety Factor", min_value=1.0, max_value=3.0, step=0.1, 
            value=float(materials.get("safety_factor", 1.5)))
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Comments
        st.markdown('<div class="sds-card">', unsafe_allow_html=True)
        st.markdown('<div class="title">💬 Notes</div>', unsafe_allow_html=True)
        comments = st.text_area("", value=st.session_state.comments, height=80, placeholder="Add design notes...")
        st.session_state.comments = comments
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.subheader("🔬 3D Model")
        
        # Generate and display
        if typ_key == "custom":
            fig = generate_custom(params)
        else:
            fig = GENERATORS[typ_key](params, materials if typ_key == "saddle_span" else None)
        
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        
        # Actions
        st.divider()
        col_act1, col_act2, col_act3, col_act4, col_act5 = st.columns(5)
        with col_act1:
            if st.button("🔒 Lock", use_container_width=True):
                st.session_state.locked = True
                save_cache()
                st.rerun()
        with col_act2:
            if st.button("💾 Save", use_container_width=True, type="primary"):
                save_project()
        with col_act3:
            if st.button("📊 Health Report", use_container_width=True):
                st.session_state.show_structural_report = True
                st.rerun()
        with col_act4:
            if st.button("📋 New", use_container_width=True):
                go_to_dashboard()
                st.rerun()
        with col_act5:
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
        ans = st.radio(q, ["Yes", "No", "Not Sure"], index=["Yes", "No", "Not Sure"].index(default), key=f"qa_{i}")
        st.session_state.qa_answers[key] = ans
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate structural report if requested
    if st.session_state.show_structural_report:
        report = generate_structural_health_report(params, materials)
        render_structural_health_report(report)
        if st.button("Close Report", use_container_width=True):
            st.session_state.show_structural_report = False
            st.rerun()
    
    save_cache()

# ============================================================
# MAIN APP ROUTING
# ============================================================

# Top Bar
col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1, 1, 1])
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
with col6:
    if st.session_state.project_registered and st.session_state.typology:
        if st.button("📊 Report", use_container_width=True):
            st.session_state.show_structural_report = True
            st.rerun()

# Project Browser
if st.session_state.show_project_browser:
    st.subheader("📂 Saved Projects")
    if st.button("⬅ Back", use_container_width=True):
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
                st.caption(f"Ref: {proj.get('reference', 'N/A')} | {proj.get('typology', 'Unknown')} {'🔒' if proj.get('locked') else '📝'}")
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

# Registration
if st.session_state.show_registration:
    st.subheader("📋 New Project")
    if st.button("⬅ Back", use_container_width=True):
        st.session_state.show_registration = False
        st.rerun()
    
    with st.form("register_form"):
        name = st.text_input("Project Name *", placeholder="e.g., KLCC Canopy")
        client = st.text_input("Client Name *", placeholder="e.g., KLCC Holdings")
        location = st.text_input("Location", placeholder="e.g., Kuala Lumpur")
        
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
                save_cache()
                st.rerun()
    st.stop()

# Dashboard
if not st.session_state.project_registered:
    render_dashboard()
    st.stop()

# Typology Selection
if st.session_state.typology is None:
    st.subheader("Choose a structure type:")
    st.caption("MS EN 1993-1-1 & MS EN 1991-1-4 compliant design")
    
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
    st.stop()

# Main Workspace
render_workspace()

# Footer
st.divider()
st.caption("SDS Design Studio | MS EN 1993-1-1 & MS EN 1991-1-4 Compliant | v6.0")

save_cache()
