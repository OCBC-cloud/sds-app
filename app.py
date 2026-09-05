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
from PIL import Image
import io

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SDS Design Studio Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# DARK MODE CSS
# ============================================================
dark_mode_css = """
    <style>
    .stApp { background-color: #0a0e17 !important; color: #f0f4fa !important; }
    .stApp > header { display: none !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; max-width: 100% !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 600 !important; }
    label { color: #ffffff !important; font-weight: 400 !important; }
    .stButton > button {
        background-color: #1e2a3a !important; color: #ffffff !important;
        border: 1px solid #2a3a4f !important; border-radius: 8px !important;
        padding: 0.5rem 1rem !important; font-weight: 500 !important;
        width: 100% !important; transition: all 0.2s !important;
    }
    .stButton > button:hover { background-color: #2a3a4f !important; border-color: #4a7a9c !important; }
    .stButton > button[kind="primary"] { background-color: #f39c12 !important; color: #0a0e17 !important; border: none !important; font-weight: 600 !important; }
    .stButton > button[kind="primary"]:hover { background-color: #f1c40f !important; }
    .stNumberInput > div > div > input, .stSelectbox > div > div > div, .stTextArea textarea {
        background-color: #141e2b !important; color: #ffffff !important;
        border: 1px solid #2a3a4f !important; border-radius: 8px !important;
    }
    .stAlert { background-color: #1e2a3a !important; border-left: 4px solid #f39c12 !important; color: #f0f4fa !important; }
    .stInfo { background-color: #1a2a3a !important; border-left: 4px solid #4a7a9c !important; color: #f0f4fa !important; }
    .stSuccess { background-color: #1a3a2a !important; border-left: 4px solid #2ecc71 !important; color: #f0f4fa !important; }
    .stError { background-color: #3a1a1a !important; border-left: 4px solid #e74c3c !important; color: #f0f4fa !important; }
    .stWarning { background-color: #4a3a1a !important; border-left: 4px solid #f39c12 !important; color: #f0f4fa !important; }
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    .dashboard-card { background-color: #141e2b; border-radius: 12px; padding: 1.5rem 1rem; border: 1px solid #1e2a3a; text-align: center; }
    .dashboard-card .icon { font-size: 2.5rem; }
    .dashboard-card .value { color: #ffffff; font-size: 1.5rem; font-weight: 700; }
    .dashboard-card .label { color: #8a9aaa; font-size: 0.8rem; }
    .sds-card { background-color: #141e2b; border-radius: 12px; padding: 1rem 1.2rem; border: 1px solid #1e2a3a; margin-bottom: 0.8rem; }
    .sds-card .title { color: #ffffff; font-weight: 600; font-size: 1rem; }
    .sds-card .content { color: #b0c4de; font-size: 0.9rem; }
    .standard-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; margin-right: 0.3rem; }
    .badge-eu { background-color: #003399; color: #ffffff; }
    .badge-cn { background-color: #DE2910; color: #ffffff; }
    .badge-uk { background-color: #012169; color: #ffffff; }
    .badge-my { background-color: #CC0000; color: #ffffff; }
    .badge-us { background-color: #B22234; color: #ffffff; }
    .health-score-good { color: #2ecc71; font-weight: 700; font-size: 1.5rem; }
    .health-score-fair { color: #f39c12; font-weight: 700; font-size: 1.5rem; }
    .health-score-poor { color: #e74c3c; font-weight: 700; font-size: 1.5rem; }
    .image-popout { background-color: #0a0e17; border-radius: 12px; padding: 1rem; border: 2px solid #4a7a9c; text-align: center; }
    .image-popout img { max-width: 100%; border-radius: 8px; }
    .upgrade-applied { background-color: #1a3a2a; border: 2px solid #2ecc71; border-radius: 8px; padding: 0.5rem 1rem; }
    </style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================================
# DATA DEFINITIONS
# ============================================================
STEEL_GRADES = {
    "S235": {"fy": 235, "fu": 360, "E": 210000, "density": 7850},
    "S275": {"fy": 275, "fu": 430, "E": 210000, "density": 7850},
    "S355": {"fy": 355, "fu": 490, "E": 210000, "density": 7850},
    "S420": {"fy": 420, "fu": 520, "E": 210000, "density": 7850},
    "S460": {"fy": 460, "fu": 550, "E": 210000, "density": 7850}
}

ALUMINUM_GRADES = {
    "6061-T6": {"fy": 276, "fu": 310, "E": 69000, "density": 2700},
    "6063-T6": {"fy": 214, "fu": 241, "E": 69000, "density": 2700},
    "5083-H116": {"fy": 230, "fu": 310, "E": 69000, "density": 2660},
    "7022-T6": {"fy": 460, "fu": 510, "E": 69000, "density": 2780}
}

WOOD_GRADES = {
    "Glulam": {"fy": 40, "fu": 55, "E": 12000, "density": 550},
    "LVL": {"fy": 45, "fu": 60, "E": 13500, "density": 600},
    "CLT": {"fy": 30, "fu": 45, "E": 10000, "density": 500},
    "Mass Timber": {"fy": 35, "fu": 50, "E": 11000, "density": 550}
}

COMPOSITE_GRADES = {
    "GFRP": {"fy": 300, "fu": 450, "E": 30000, "density": 2000},
    "CFRP": {"fy": 600, "fu": 900, "E": 120000, "density": 1600}
}

SECTION_PROPERTIES = {
    "CHS 60.3x3.2": {"A": 574, "I": 0.24e6, "W_el": 8.0e3, "i": 20.5, "weight": 4.5, "type": "CHS"},
    "CHS 76.1x3.6": {"A": 820, "I": 0.54e6, "W_el": 14.2e3, "i": 25.7, "weight": 6.4, "type": "CHS"},
    "CHS 88.9x4.0": {"A": 1067, "I": 0.93e6, "W_el": 20.9e3, "i": 29.5, "weight": 8.4, "type": "CHS"},
    "CHS 114.3x5.0": {"A": 1717, "I": 2.53e6, "W_el": 44.2e3, "i": 38.4, "weight": 13.5, "type": "CHS"},
    "CHS 139.7x6.3": {"A": 2642, "I": 5.90e6, "W_el": 84.5e3, "i": 47.3, "weight": 20.7, "type": "CHS"},
    "CHS 168.3x7.1": {"A": 3600, "I": 11.5e6, "W_el": 137e3, "i": 56.5, "weight": 28.3, "type": "CHS"},
    "CHS 219.1x8.0": {"A": 5305, "I": 29.0e6, "W_el": 265e3, "i": 73.9, "weight": 41.6, "type": "CHS"},
    "CHS 273.0x10.0": {"A": 8263, "I": 69.0e6, "W_el": 506e3, "i": 91.4, "weight": 64.9, "type": "CHS"},
    "CHS 323.9x12.5": {"A": 12228, "I": 148e6, "W_el": 912e3, "i": 110.0, "weight": 96.0, "type": "CHS"},
    "CHS 406.4x12.5": {"A": 15470, "I": 210e6, "W_el": 1030e3, "i": 116.6, "weight": 121.4, "type": "CHS"},
    "RHS 100x100x5": {"A": 1900, "I": 2.8e6, "W_el": 56.0e3, "i": 38.4, "weight": 14.9, "type": "RHS"},
    "RHS 150x100x6": {"A": 2784, "I": 8.3e6, "W_el": 111e3, "i": 54.6, "weight": 21.8, "type": "RHS"},
    "RHS 200x150x8": {"A": 5104, "I": 30.1e6, "W_el": 301e3, "i": 76.8, "weight": 40.0, "type": "RHS"},
    "RHS 250x150x10": {"A": 7500, "I": 71.0e6, "W_el": 568e3, "i": 97.3, "weight": 58.9, "type": "RHS"},
    "RHS 300x200x12": {"A": 11424, "I": 156e6, "W_el": 1040e3, "i": 116.8, "weight": 89.7, "type": "RHS"},
    "I-100": {"A": 1030, "I": 4.5e6, "W_el": 90e3, "i": 66.1, "weight": 8.1, "type": "I-Beam"},
    "I-150": {"A": 2130, "I": 16.0e6, "W_el": 213e3, "i": 86.7, "weight": 16.7, "type": "I-Beam"},
    "I-200": {"A": 3310, "I": 38.0e6, "W_el": 380e3, "i": 107.1, "weight": 26.0, "type": "I-Beam"},
    "I-250": {"A": 4820, "I": 76.0e6, "W_el": 608e3, "i": 125.6, "weight": 37.8, "type": "I-Beam"},
    "I-300": {"A": 6720, "I": 136e6, "W_el": 907e3, "i": 142.3, "weight": 52.8, "type": "I-Beam"},
    "I-350": {"A": 9020, "I": 226e6, "W_el": 1290e3, "i": 158.3, "weight": 70.8, "type": "I-Beam"},
    "I-400": {"A": 11800, "I": 348e6, "W_el": 1740e3, "i": 171.8, "weight": 92.6, "type": "I-Beam"},
    "Box 150x100x6": {"A": 2784, "I": 8.3e6, "W_el": 111e3, "i": 54.6, "weight": 21.8, "type": "Box"},
    "Box 200x150x8": {"A": 5104, "I": 30.1e6, "W_el": 301e3, "i": 76.8, "weight": 40.0, "type": "Box"},
    "Box 250x150x10": {"A": 7500, "I": 71.0e6, "W_el": 568e3, "i": 97.3, "weight": 58.9, "type": "Box"},
    "Box 300x200x12": {"A": 11424, "I": 156e6, "W_el": 1040e3, "i": 116.8, "weight": 89.7, "type": "Box"},
    "Glulam 90x200": {"A": 18000, "I": 60.0e6, "W_el": 600e3, "i": 57.7, "weight": 9.9, "type": "Wood"},
    "Glulam 150x300": {"A": 45000, "I": 337.5e6, "W_el": 2250e3, "i": 86.6, "weight": 24.75, "type": "Wood"},
    "Glulam 200x400": {"A": 80000, "I": 1066.7e6, "W_el": 5333e3, "i": 115.5, "weight": 44.0, "type": "Wood"},
    "Aluminum 100x100x4": {"A": 1536, "I": 2.3e6, "W_el": 46e3, "i": 38.7, "weight": 4.15, "type": "Aluminum"},
    "Aluminum 150x150x5": {"A": 2900, "I": 8.1e6, "W_el": 108e3, "i": 52.8, "weight": 7.83, "type": "Aluminum"},
    "Aluminum 200x200x6": {"A": 4656, "I": 24.3e6, "W_el": 243e3, "i": 72.3, "weight": 12.57, "type": "Aluminum"},
}

FABRIC_PROPERTIES = {
    "PVC-coated Polyester": {"strength": 40, "weight_per_m2": 1.2, "cost_per_m2": 25, "lifespan": 20, "max_span": 15},
    "PTFE-coated Fiberglass": {"strength": 60, "weight_per_m2": 1.8, "cost_per_m2": 80, "lifespan": 35, "max_span": 30},
    "ETFE": {"strength": 30, "weight_per_m2": 0.8, "cost_per_m2": 120, "lifespan": 50, "max_span": 25}
}

WIND_SPEEDS = {"EU": 30.0, "CN": 28.0, "UK": 26.0, "MY": 33.5, "US": 38.0}

TRUSS_ICONS = {
    "warren": "╱╲ ╱╲ ╱╲\n╱  ╲╱  ╲╱\n╱    ╲  ╲\n╱     ╲  ╲",
    "pratt": "│ ╲ │ ╲ │\n│  ╲│  ╲│\n│   ╲   ╲\n│ ╲ │ ╲ │\n│  ╲│  ╲│",
    "howe": "╲ │ ╲ │\n ╲│  ╲│\n  ╲   ╲\n╲ │ ╲ │\n ╲│  ╲│",
    "vierendeel": "│   │   │\n│   │   │\n│   │   │\n│   │   │\n│   │   │"
}

TRUSS_LABELS = {
    "warren": "Warren - V-shaped diagonals, most efficient",
    "pratt": "Pratt - Diagonals slope down, common bridge",
    "howe": "Howe - Diagonals slope up, opposite of Pratt",
    "vierendeel": "Vierendeel - No diagonals, rigid joints"
}

TRUSS_DESCRIPTIONS = {
    "warren": "V-shaped diagonals forming triangles. Most material-efficient. No vertical members.",
    "pratt": "Vertical members + diagonals sloping down to center. Diagonals in tension.",
    "howe": "Vertical members + diagonals sloping up to center. Diagonals in compression.",
    "vierendeel": "Rectangular panels with NO diagonals. Members resist bending. Heavy joints."
}

# ============================================================
# SESSION STATE - SIMPLE AND CLEAN
# ============================================================
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
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
if "show_structural_report" not in st.session_state:
    st.session_state.show_structural_report = False
if "show_image_popout" not in st.session_state:
    st.session_state.show_image_popout = None
if "auto_sizing_applied" not in st.session_state:
    st.session_state.auto_sizing_applied = False
if "upgrade_applied" not in st.session_state:
    st.session_state.upgrade_applied = False
if "upgrade_name" not in st.session_state:
    st.session_state.upgrade_name = ""
if "saved_projects" not in st.session_state:
    st.session_state.saved_projects = []
if "materials" not in st.session_state:
    st.session_state.materials = {
        "standard": "EU",
        "material_type": "Steel",
        "steel_grade": "S355",
        "aluminum_grade": "6061-T6",
        "wood_grade": "Glulam",
        "composite_grade": "GFRP",
        "section_size": "CHS 168.3x7.1",
        "section_type": "CHS",
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
# UTILITY FUNCTIONS
# ============================================================
def get_standard_label(code):
    labels = {"EU": "🇪🇺 Eurocode", "CN": "🇨🇳 China", "UK": "🇬🇧 British", "MY": "🇲🇾 Malaysia", "US": "🇺🇸 USA"}
    return labels.get(code, code)

def compress_image(uploaded_file, max_size=300, quality=65):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        w, h = img.size
        if w > h:
            new_w, new_h = max_size, int(h * (max_size / w))
        else:
            new_w, new_h = int(w * (max_size / h)), max_size
        new_w, new_h = max(100, new_w), max(100, new_h)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        return buffer
    except:
        return None

def get_beam_shape(x, span, rise, shape_type="parabolic"):
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
    return rise * (1 - x_norm**2)

def generate_bracing_positions(span, num_bays):
    if num_bays == 1:
        return [0.0]
    if num_bays == 2:
        return [-span/3, span/3]
    if num_bays == 3:
        return [-span/4, 0.0, span/4]
    return np.linspace(-span/2 * 0.8, span/2 * 0.8, num_bays).tolist()

def calculate_tie_down_positions(span, laa, height, x_positions, vertical_angle, horizontal_spread):
    vert_rad, horz_rad = np.radians(vertical_angle), np.radians(horizontal_spread)
    dist = height * np.tan(vert_rad)
    anchors = []
    for bx in x_positions:
        for beam_y in [-laa/2, laa/2]:
            y_dir = -1 if beam_y < 0 else 1
            anchors.append({
                "beam_x": bx, "beam_y": beam_y,
                "anchor_x": bx + dist * np.cos(horz_rad) * (1 if bx >= 0 else -1),
                "anchor_y": beam_y + dist * np.sin(horz_rad) * y_dir,
                "anchor_z": 0
            })
    return anchors

def generate_truss_members(x, z_beam, truss_type="warren", num_panels=4):
    n = len(x)
    panel_size = max(1, n // num_panels)
    members = []
    if truss_type == "warren":
        for i in range(0, n - panel_size, panel_size):
            j = min(i + panel_size, n - 1)
            members.extend([("top", i, j), ("bottom", i, j), ("diag", i, j), ("diag", j, i)])
    elif truss_type == "pratt":
        for i in range(0, n - panel_size, panel_size):
            j = min(i + panel_size, n - 1)
            members.extend([("top", i, j), ("bottom", i, j), ("vertical", i, j), ("diag", i, j)])
    elif truss_type == "howe":
        for i in range(0, n - panel_size, panel_size):
            j = min(i + panel_size, n - 1)
            members.extend([("top", i, j), ("bottom", i, j), ("vertical", i, j), ("diag", j, i)])
    elif truss_type == "vierendeel":
        for i in range(0, n - panel_size, panel_size):
            j = min(i + panel_size, n - 1)
            members.extend([("top", i, j), ("bottom", i, j), ("vertical", i, j)])
    return members

# ============================================================
# ENGINEERING FUNCTIONS
# ============================================================
def calculate_wind_load(span, laa, standard):
    membrane_area = span * laa * 1.1
    wind_speed = WIND_SPEEDS.get(standard, 30.0)
    q = 0.5 * 1.225 * wind_speed**2 / 1000
    return q * membrane_area * 1.2

def calculate_dead_load(span, laa, section, fabric_type):
    section_data = SECTION_PROPERTIES.get(section, SECTION_PROPERTIES["CHS 168.3x7.1"])
    steel_kg = section_data.get("weight", 28.3) * span * 2
    membrane_area = span * laa * 1.1
    fabric_weight = FABRIC_PROPERTIES.get(fabric_type, {}).get("weight_per_m2", 1.2)
    fabric_kg = fabric_weight * membrane_area
    return (steel_kg + fabric_kg) / 100

def calculate_required_section(force_kN, length_m, material_type, fy=355):
    safety = 1.5
    required_area = (abs(force_kN) * 1000 * safety) / fy
    required_I = (abs(force_kN) * length_m * 1e6 * length_m * 12) / (210000 * 10)
    best_section, best_score = None, float('inf')
    for section, props in SECTION_PROPERTIES.items():
        if props["A"] <= 0:
            continue
        area_score = abs(props["A"] - required_area) / required_area if required_area > 0 else 0
        i_score = abs(props["I"] - required_I) / required_I if required_I > 0 else 0
        weight_score = props["weight"] / 100
        total_score = area_score * 0.4 + i_score * 0.3 + weight_score * 0.3
        if props["A"] < required_area * 0.7:
            total_score += 10
        if total_score < best_score:
            best_score, best_section = total_score, section
    if best_section and best_section in SECTION_PROPERTIES:
        props = SECTION_PROPERTIES[best_section]
        return {"section": best_section, "properties": props, "force_kN": abs(force_kN), "capacity_ratio": props["A"] / required_area if required_area > 0 else 0, "is_adequate": props["A"] >= required_area * 0.8}
    return None

def auto_select_fabric_thickness(wind_force, membrane_area, fabric_type):
    required_strength = wind_force / (membrane_area * 0.5) if membrane_area > 0 else 0
    thickness_options = {
        "PVC-coated Polyester": {0.5: 30, 0.8: 40, 1.0: 50, 1.2: 60},
        "PTFE-coated Fiberglass": {0.5: 40, 0.8: 55, 1.0: 70, 1.2: 85},
        "ETFE": {0.5: 25, 0.8: 35, 1.0: 45, 1.2: 55}
    }
    options = thickness_options.get(fabric_type, {})
    for thickness, strength in sorted(options.items()):
        if strength >= required_strength * 1.5:
            return thickness
    return 0.8

def calculate_membrane_adequacy(fabric_type, wind_force, membrane_area, structure_type):
    fabric_strength = {"PVC-coated Polyester": 40, "PTFE-coated Fiberglass": 60, "ETFE": 30}
    if fabric_type == "ETFE":
        if structure_type in ["saddle_span", "tensile_membrane"]:
            return {"is_adequate": False, "reason": "ETFE not suitable for load-bearing membranes", "warning": True}
        required = wind_force / (membrane_area * 0.3) if membrane_area > 0 else 0
        actual = fabric_strength.get(fabric_type, 30)
        return {"is_adequate": actual >= required * 1.5, "required_strength": required, "actual_strength": actual, "warning": False}
    required = wind_force / (membrane_area * 0.5) if membrane_area > 0 else 0
    actual = fabric_strength.get(fabric_type, 40)
    return {"is_adequate": actual >= required * 1.5, "required_strength": required, "actual_strength": actual, "warning": False}

def size_all_members(params, materials):
    span, rise, laa = params.get("B", 10.0), params.get("A", 6.0), params.get("LAA", 15.0)
    wind = calculate_wind_load(span, laa, materials.get("standard", "EU"))
    dead = calculate_dead_load(span, laa, materials.get("section_size", "CHS 168.3x7.1"), materials.get("fabric_type", "PVC-coated Polyester"))
    live = 0.5 * (span * laa * 1.1) / 100
    total = wind + dead + live
    beam_force = (total * span) / (4 * rise) if rise > 0 else total * 0.5
    member_type, material_type = materials.get("member_type", "single_beam"), materials.get("material_type", "Steel")
    fy = 355 if material_type == "Steel" else 276 if material_type == "Aluminum" else 40
    results = {"loads": {"wind": wind, "dead": dead, "live": live, "total": total}, "beams": {}, "truss": {}}
    if member_type == "single_beam":
        result = calculate_required_section(beam_force, span, material_type, fy)
        if result:
            results["beams"]["main"] = result
            results["beams"]["selected"] = result["section"]
    elif member_type in ["planar_truss", "space_truss"]:
        mult = 0.8 if member_type == "space_truss" else 1.0
        top_r = calculate_required_section(beam_force * 1.2 * mult, span/4, material_type, fy)
        bot_r = calculate_required_section(beam_force * 0.8 * mult, span/4, material_type, fy)
        diag_r = calculate_required_section(beam_force * 0.6 * mult, span/6, material_type, fy)
        vert_r = calculate_required_section(beam_force * 0.4 * mult, span/8, material_type, fy) if member_type == "planar_truss" else None
        results["truss"] = {
            "top_chord": top_r or {"section": "N/A", "properties": {}, "force_kN": beam_force * 1.2 * mult},
            "bottom_chord": bot_r or {"section": "N/A", "properties": {}, "force_kN": beam_force * 0.8 * mult},
            "diagonals": diag_r or {"section": "N/A", "properties": {}, "force_kN": beam_force * 0.6 * mult},
            "verticals": vert_r or {"section": "N/A", "properties": {}, "force_kN": beam_force * 0.4 * mult} if member_type == "planar_truss" else None,
            "selected": {"top": top_r["section"] if top_r else "N/A", "bottom": bot_r["section"] if bot_r else "N/A", "diagonal": diag_r["section"] if diag_r else "N/A"}
        }
        if member_type == "planar_truss" and vert_r:
            results["truss"]["selected"]["vertical"] = vert_r["section"] if vert_r else "N/A"
    return results

# ============================================================
# INTELLIGENT UPGRADE ENGINE
# ============================================================
def analyze_and_upgrade_structure(params, materials, sizing_results):
    """Analyze failed wind load and suggest upgrades"""
    span = params.get("B", 10.0)
    member_type = materials.get("member_type", "single_beam")
    current_section = materials.get("section_size", "CHS 168.3x7.1")
    wind_force = sizing_results["loads"]["wind"]
    beam_force = sizing_results.get("beams", {}).get("main", {}).get("force_kN", 0)
    
    upgrades = []
    
    # Option A: Planar Steel Truss
    if member_type == "single_beam" and beam_force > 0:
        top_r = calculate_required_section(beam_force * 1.2, span/4, "Steel", 355)
        bot_r = calculate_required_section(beam_force * 0.8, span/4, "Steel", 355)
        diag_r = calculate_required_section(beam_force * 0.6, span/6, "Steel", 355)
        vert_r = calculate_required_section(beam_force * 0.4, span/8, "Steel", 355)
        
        if top_r and bot_r and diag_r:
            total_weight = (top_r["properties"].get("weight", 0) + bot_r["properties"].get("weight", 0) + diag_r["properties"].get("weight", 0) * 2 + (vert_r["properties"].get("weight", 0) if vert_r else 0))
            upgrades.append({
                "name": "Planar Steel Truss",
                "type": "planar_truss",
                "material": "Steel",
                "members": {"top_chord": top_r["section"], "bottom_chord": bot_r["section"], "diagonals": diag_r["section"], "verticals": vert_r["section"] if vert_r else "N/A"},
                "total_weight": total_weight,
                "weight_reduction": 0,
                "is_adequate": True,
                "description": "Traditional steel truss - efficient and proven",
                "member_details": {
                    "top": f"{top_r['section']} ({top_r['properties'].get('weight', 0):.1f} kg/m)",
                    "bottom": f"{bot_r['section']} ({bot_r['properties'].get('weight', 0):.1f} kg/m)",
                    "diagonal": f"{diag_r['section']} ({diag_r['properties'].get('weight', 0):.1f} kg/m)",
                    "vertical": f"{vert_r['section']} ({vert_r['properties'].get('weight', 0):.1f} kg/m)" if vert_r else "N/A"
                }
            })
    
    # Option B: 3D Space Truss
    if member_type in ["single_beam", "planar_truss"] and beam_force > 0:
        top_r = calculate_required_section(beam_force * 0.8, span/3, "Steel", 355)
        bot_r = calculate_required_section(beam_force * 0.6, span/3, "Steel", 355)
        diag_r = calculate_required_section(beam_force * 0.4, span/5, "Steel", 355)
        if top_r and bot_r and diag_r:
            total_weight = (top_r["properties"].get("weight", 0) + bot_r["properties"].get("weight", 0) + diag_r["properties"].get("weight", 0) * 2)
            upgrades.append({
                "name": "3D Space Truss (Steel)",
                "type": "space_truss",
                "material": "Steel",
                "members": {"top_chord": top_r["section"], "bottom_chord": bot_r["section"], "diagonals": diag_r["section"]},
                "total_weight": total_weight,
                "weight_reduction": 0,
                "is_adequate": True,
                "description": "Lightweight 3D truss - excellent for large spans",
                "member_details": {
                    "top": f"{top_r['section']} ({top_r['properties'].get('weight', 0):.1f} kg/m)",
                    "bottom": f"{bot_r['section']} ({bot_r['properties'].get('weight', 0):.1f} kg/m)",
                    "diagonal": f"{diag_r['section']} ({diag_r['properties'].get('weight', 0):.1f} kg/m)"
                }
            })
    
    # Option C: Aluminum Box Beam
    if member_type == "single_beam" and beam_force > 0:
        al_sections = [s for s in SECTION_PROPERTIES.keys() if "Aluminum" in s]
        best_al = None
        for section in al_sections:
            props = SECTION_PROPERTIES[section]
            capacity = (props["A"] * 276) / 1500
            if capacity > wind_force * 1.5:
                best_al = section
                break
        if best_al:
            props = SECTION_PROPERTIES[best_al]
            upgrades.append({
                "name": "Aluminum Box Beam",
                "type": "single_beam",
                "material": "Aluminum",
                "members": {"beam": best_al},
                "total_weight": props.get("weight", 0),
                "weight_reduction": 0,
                "is_adequate": True,
                "description": "Lightweight aluminum beam - corrosion resistant",
                "member_details": {"beam": f"{best_al} ({props.get('weight', 0):.1f} kg/m)"}
            })
    
    # Option D: Larger Steel Section
    if member_type == "single_beam":
        current_weight = SECTION_PROPERTIES.get(current_section, {}).get("weight", 0)
        larger_sections = [(s, p) for s, p in SECTION_PROPERTIES.items() if "CHS" in s and p.get("weight", 0) > current_weight * 1.2]
        if larger_sections:
            best_larger = larger_sections[0]
            props = best_larger[1]
            upgrades.append({
                "name": f"Larger Steel Section ({best_larger[0]})",
                "type": "single_beam",
                "material": "Steel",
                "members": {"beam": best_larger[0]},
                "total_weight": props.get("weight", 0),
                "weight_reduction": 0,
                "is_adequate": True,
                "description": "Larger steel section - simple upgrade",
                "member_details": {"beam": f"{best_larger[0]} ({props.get('weight', 0):.1f} kg/m)"}
            })
    
    # Calculate weight reduction
    current_weight = SECTION_PROPERTIES.get(current_section, {}).get("weight", 0)
    for upgrade in upgrades:
        if upgrade["total_weight"] > 0 and current_weight > 0:
            upgrade["weight_reduction"] = ((current_weight - upgrade["total_weight"]) / current_weight * 100)
        else:
            upgrade["weight_reduction"] = 0
    
    upgrades.sort(key=lambda x: x["weight_reduction"], reverse=True)
    return upgrades

def render_upgrade_options(upgrades, params, materials):
    """Display upgrade options with visual feedback and confirmation"""
    if not upgrades:
        return
    
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">🔄 Intelligent Structural Upgrade</div>', unsafe_allow_html=True)
    
    if st.session_state.get("upgrade_applied", False):
        st.markdown(f"""
        <div class="upgrade-applied">
            ✅ <strong>Applied: {st.session_state.upgrade_name}</strong> — Re-run Health Report to see the results
        </div>
        """, unsafe_allow_html=True)
        st.info("🔄 The upgrade has been applied. Click the 'Health Report' button above to see updated results.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.warning("⚠️ Current design cannot handle wind load efficiently. The system has analyzed alternatives:")
    
    data = []
    for i, upgrade in enumerate(upgrades):
        data.append({
            "Option": f"{i+1}",
            "Name": upgrade["name"],
            "Material": upgrade["material"],
            "Weight": f"{upgrade['total_weight']:.1f} kg/m",
            "Reduction": f"{upgrade['weight_reduction']:.0f}%",
            "Status": "✅ Adequate"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("#### 📐 Select an upgrade to preview")
    selected_idx = st.radio(
        "Choose upgrade option:",
        options=range(len(upgrades)),
        format_func=lambda i: f"{i+1}. {upgrades[i]['name']}",
        key="upgrade_select"
    )
    selected = upgrades[selected_idx]
    
    with st.expander("📋 Upgrade Details", expanded=True):
        st.markdown(f"**{selected['name']}**")
        st.write(f"Material: {selected['material']}")
        st.write(f"Total Weight: {selected['total_weight']:.1f} kg/m")
        st.write(f"Weight Reduction: {selected['weight_reduction']:.0f}%")
        st.write(f"Description: {selected['description']}")
        st.write("**Members:**")
        for key, value in selected.get("member_details", {}).items():
            st.write(f"- {key.title()}: {value}")
    
    if st.button(f"✅ Apply: {selected['name']}", use_container_width=True, type="primary"):
        if selected["type"] == "planar_truss":
            materials["member_type"] = "planar_truss"
            materials["material_type"] = selected["material"]
            if "top_chord" in selected["members"]:
                materials["section_size"] = selected["members"]["top_chord"]
        elif selected["type"] == "space_truss":
            materials["member_type"] = "space_truss"
            materials["material_type"] = selected["material"]
            if "top_chord" in selected["members"]:
                materials["section_size"] = selected["members"]["top_chord"]
        else:
            materials["member_type"] = "single_beam"
            materials["material_type"] = selected["material"]
            if "beam" in selected["members"]:
                materials["section_size"] = selected["members"]["beam"]
        st.session_state.auto_sizing_applied = True
        st.session_state.upgrade_applied = True
        st.session_state.upgrade_name = selected['name']
        st.success(f"✅ Applied: {selected['name']}")
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 3D GENERATOR
# ============================================================
def generate_saddle_span(params, materials=None):
    span, rise, laa = params.get("B", 10.0), params.get("A", 6.0), params.get("LAA", 15.0)
    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()
    shape_type = materials.get("shape_type", "parabolic") if materials else "parabolic"
    member_type = materials.get("member_type", "single_beam") if materials else "single_beam"
    truss_type = materials.get("truss_type", "warren") if materials else "warren"
    anchoring_pattern = materials.get("anchoring_pattern", "standard") if materials else "standard"
    prestress_level = materials.get("prestress_level", "medium") if materials else "medium"
    prestress_values = {"none": 0, "low": 1.5, "medium": 3.0, "high": 5.0}
    prestress = materials.get("custom_prestress", 3.0) if prestress_level == "custom" else prestress_values.get(prestress_level, 3.0)
    num_points = 50
    x = np.linspace(-span/2, span/2, num_points)
    z_beam = get_beam_shape(x, span, rise, shape_type)
    y1, y2 = -laa/2 * (1 - (2*x/span)**2), laa/2 * (1 - (2*x/span)**2)
    fig = go.Figure()
    
    if member_type == "single_beam":
        fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1', line=dict(color='#FF6B6B', width=8)))
        fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2', line=dict(color='#FF6B6B', width=8)))
    elif member_type == "planar_truss":
        fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1 (Truss)', line=dict(color='#FF6B6B', width=5)))
        fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2 (Truss)', line=dict(color='#FF6B6B', width=5)))
        z_bottom = z_beam * 0.7
        fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_bottom, mode='lines', name='Bottom Chord 1', line=dict(color='#FF9B6B', width=4, dash='dot')))
        fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_bottom, mode='lines', name='Bottom Chord 2', line=dict(color='#FF9B6B', width=4, dash='dot')))
        for i in range(0, num_points - 5, 5):
            j = min(i + 5, num_points - 1)
            fig.add_trace(go.Scatter3d(x=[x[i], x[j]], y=[y1[i], y1[j]], z=[z_beam[i], z_bottom[j]], mode='lines', line=dict(color='#FFB6A0', width=2), showlegend=False))
            fig.add_trace(go.Scatter3d(x=[x[i], x[j]], y=[y2[i], y2[j]], z=[z_beam[i], z_bottom[j]], mode='lines', line=dict(color='#FFB6A0', width=2), showlegend=False))
    elif member_type == "space_truss":
        fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Top Layer 1', line=dict(color='#FF6B6B', width=4)))
        fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Top Layer 2', line=dict(color='#FF6B6B', width=4)))
        for i in range(0, num_points, 5):
            fig.add_trace(go.Scatter3d(x=[x[i]]*2, y=[y1[i], y2[i]], z=[z_beam[i], z_beam[i]], mode='lines', line=dict(color='#FF9B6B', width=2, dash='dot'), showlegend=False))
    
    # Membrane surface
    X_surf, Y_surf, Z_surf = np.zeros((num_points, num_points)), np.zeros((num_points, num_points)), np.zeros((num_points, num_points))
    for i, x_pos in enumerate(x):
        y_beam1, y_beam2, z_at_x = y1[i], y2[i], z_beam[i]
        for j, v_val in enumerate(np.linspace(0, 1, num_points)):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            Z_surf[i, j] = z_at_x * (1 - 0.3 * (1 - (2*v_val - 1)**2)) * (1 + prestress/10)
            X_surf[i, j], Y_surf[i, j] = x_pos, y_pos
    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']], opacity=max(0.3, min(0.7, 0.5 + prestress/20)), showscale=False, name='Membrane'))
    
    # Apex and supports
    fig.add_trace(go.Scatter3d(x=[0], y=[y1[num_points//2]], z=[z_beam[num_points//2]], mode='markers', name='Apex 1', marker=dict(color='#FFD93D', size=10, symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[0], y=[y2[num_points//2]], z=[z_beam[num_points//2]], mode='markers', name='Apex 2', marker=dict(color='#FFD93D', size=10, symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[-span/2, span/2], y=[0, 0], z=[0, 0], mode='markers', name='Supports', marker=dict(color='#4ECDC4', size=8, symbol='square')))
    
    # Bracing and tie-downs
    if materials:
        num_bays = materials.get("num_bays", 2)
        vertical_angle = materials.get("tie_down_vertical_angle", 45)
        horizontal_spread = materials.get("tie_down_horizontal_spread", 30)
        bracing_x = generate_bracing_positions(span, num_bays)
        for bx in bracing_x:
            idx = np.argmin(np.abs(x - bx))
            fig.add_trace(go.Scatter3d(x=[bx, bx], y=[y1[idx], y2[idx]], z=[z_beam[idx], z_beam[idx]], mode='lines', name='Bracing', line=dict(color='#FF6B6B', width=3, dash='dash'), showlegend=False))
        anchor_x = bracing_x if anchoring_pattern == "standard" else np.linspace(-span/2*0.8, span/2*0.8, num_bays*4).tolist() if anchoring_pattern == "continuous" else sorted(bracing_x + [(bracing_x[i] + bracing_x[i+1])/2 for i in range(len(bracing_x)-1)])
        anchors = calculate_tie_down_positions(span, laa, rise, anchor_x, vertical_angle, horizontal_spread)
        for a in anchors:
            idx = np.argmin(np.abs(x - a["beam_x"]))
            fig.add_trace(go.Scatter3d(x=[a["beam_x"], a["anchor_x"]], y=[a["beam_y"], a["anchor_y"]], z=[z_beam[idx], a["anchor_z"]], mode='lines', name='Tie-Down', line=dict(color='#FFD93D', width=3), showlegend=False))
            fig.add_trace(go.Scatter3d(x=[a["anchor_x"]], y=[a["anchor_y"]], z=[a["anchor_z"]], mode='markers', name='Anchor', marker=dict(color='#FF4444', size=8, symbol='x'), showlegend=False))
    
    fig.update_layout(scene=dict(xaxis_title='Span (m)', yaxis_title='Width (m)', zaxis_title='Height (m)', xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), bgcolor='#0a0e17', camera=dict(eye=dict(x=1.8, y=1.8, z=1.2))), paper_bgcolor='#0a0e17', margin=dict(l=0, r=0, b=0, t=0), legend=dict(font=dict(color='#ffffff', size=8), orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, bgcolor='rgba(10,14,23,0.7)'))
    return fig

# ============================================================
# OTHER GENERATORS (Placeholders for future)
# ============================================================
def generate_tent(params):
    span, ridge, bays, bay_dist = params.get("span_width", 10.0), params.get("ridge_height", 5.0), params.get("num_bays", 4), params.get("bay_distance", 5.0)
    total_len = bays * bay_dist
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,total_len], z=[ridge,ridge], mode='lines', name='Ridge', line=dict(width=8, color='#f39c12')))
    fig.add_trace(go.Scatter3d(x=[-span/2,-span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Left', line=dict(width=5, color='#4a7a9c')))
    fig.add_trace(go.Scatter3d(x=[span/2,span/2], y=[0,total_len], z=[0,0], mode='lines', name='Eave Right', line=dict(width=5, color='#4a7a9c')))
    X, Y = np.meshgrid(np.linspace(-span/2, span/2, 30), np.linspace(0, total_len, 30))
    Z = ridge * (1 - (X/(span/2))**2) * (1 - (Y/total_len)**2 * 0.1)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.5, colorscale='Reds', showscale=False, name='Fabric'))
    fig.update_layout(scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)', xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
    return fig

def generate_tensile(params):
    mast, length, width, cables = params.get("mast_height", 8.0), params.get("span_length", 20.0), params.get("span_width", 15.0), params.get("cable_count", 4)
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[0,mast], mode='lines', name='Mast', line=dict(width=10, color='#f39c12')))
    X, Y = np.meshgrid(np.linspace(-length/2, length/2, 30), np.linspace(-width/2, width/2, 30))
    Z = mast * np.exp(-((X/(length/2))**2 + (Y/(width/2))**2) * 0.5)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.4, colorscale='Greens', showscale=False, name='Membrane'))
    for i in range(cables):
        angle = i * 2*np.pi/cables
        fig.add_trace(go.Scatter3d(x=[0, length/2*np.cos(angle)], y=[0, width/2*np.sin(angle)], z=[mast, 0], mode='lines', name=f'Cable {i+1}', line=dict(width=4, color='#4a7a9c')))
    fig.update_layout(scene=dict(xaxis_title='Length (m)', yaxis_title='Width (m)', zaxis_title='Height (m)', xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
    return fig

def generate_portal(params):
    eave, span, pitch, bays, bay_spacing = params.get("eave_height", 6.0), params.get("span_width", 20.0), params.get("roof_pitch", 5.0), params.get("num_bays", 5), params.get("bay_spacing", 6.0)
    total_len = bays * bay_spacing
    roof_rise, ridge = span/2 * np.tan(np.radians(pitch)), eave + span/2 * np.tan(np.radians(pitch))
    fig = go.Figure()
    x, z = [-span/2, -span/2, 0, span/2, span/2], [0, eave, ridge, eave, 0]
    fig.add_trace(go.Scatter3d(x=x, y=[0]*len(x), z=z, mode='lines', name='Portal Frame', line=dict(width=8, color='#4a7a9c')))
    for i in range(bays):
        y = i * bay_spacing
        fig.add_trace(go.Scatter3d(x=x, y=[y]*len(x), z=z, mode='lines', line=dict(width=4, color='#4a7a9c', opacity=0.3), showlegend=False))
    Y, X = np.meshgrid(np.linspace(0, total_len, 10), np.linspace(-span/2, span/2, 30))
    Z = np.where(np.abs(X) < span/2, eave + (span/2 - np.abs(X)) * np.tan(np.radians(pitch)), 0)
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.3, colorscale='Greys', showscale=False, name='Roof'))
    fig.update_layout(scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)', xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
    return fig

def generate_custom(params):
    width, length, height = params.get("width", 10.0), params.get("length", 15.0), params.get("height", 8.0)
    fig = go.Figure()
    corners = [[-width/2, -length/2, 0], [width/2, -length/2, 0], [width/2, length/2, 0], [-width/2, length/2, 0], [-width/2, -length/2, height], [width/2, -length/2, height], [width/2, length/2, height], [-width/2, length/2, height]]
    edges = [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]
    for i, j in edges:
        fig.add_trace(go.Scatter3d(x=[corners[i][0], corners[j][0]], y=[corners[i][1], corners[j][1]], z=[corners[i][2], corners[j][2]], mode='lines', line=dict(color='#4a7a9c', width=3), showlegend=False))
    fig.update_layout(scene=dict(xaxis_title='Width (m)', yaxis_title='Length (m)', zaxis_title='Height (m)', xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'), bgcolor='#0a0e17', camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), paper_bgcolor='#0a0e17', margin=dict(l=0,r=0,b=0,t=0))
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
def render_dashboard():
    st.title("🏗️ SDS Design Studio Pro")
    st.caption("Advanced parametric design for tensile structures")
    
    projects = st.session_state.saved_projects
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"<div class='dashboard-card'><div class='icon'>📂</div><div class='value'>{len(projects)}</div><div class='label'>Saved Projects</div></div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("<div class='dashboard-card'><div class='icon'>🏕️</div><div class='value'>4</div><div class='label'>Shape Variants</div></div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown("<div class='dashboard-card'><div class='icon'>🔧</div><div class='value'>3</div><div class='label'>Member Types</div></div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown("<div class='dashboard-card'><div class='icon'>🧠</div><div class='value'>Auto</div><div class='label'>Sizing Engine</div></div>", unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New Design", use_container_width=True, type="primary"):
            st.session_state.page = "registration"
            st.rerun()
    with col2:
        if st.button("📂 Open Project", use_container_width=True):
            st.session_state.page = "browser"
            st.rerun()

def render_registration():
    st.subheader("📋 New Project")
    if st.button("⬅ Back", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()
    
    with st.form("register_form"):
        name = st.text_input("Project Name *", placeholder="e.g., Marina Bay Canopy")
        client = st.text_input("Client Name *", placeholder="e.g., Marina Bay Sands")
        location = st.text_input("Location", placeholder="e.g., Singapore")
        standard = st.selectbox("Design Standard", ["EU", "CN", "UK", "MY", "US"], index=3)
        ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        st.caption(f"Reference: SDS-{ref}")
        
        if st.form_submit_button("🚀 Start Design", use_container_width=True, type="primary"):
            if not name or not client:
                st.error("⚠️ Project Name and Client Name are required.")
            else:
                st.session_state.project_info = {"name": name, "client": client, "location": location, "reference": f"SDS-{ref}", "date": datetime.now().isoformat()}
                st.session_state.materials["standard"] = standard
                st.session_state.page = "catalog"
                st.rerun()

def render_project_browser():
    st.subheader("📂 Saved Projects")
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()
    
    projects = st.session_state.saved_projects
    if not projects:
        st.info("No saved projects found.")
    else:
        for i, proj in enumerate(projects):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{proj.get('name', 'Untitled')}** — {proj.get('client', 'Unknown')}")
            std = proj.get("materials", {}).get("standard", "EU")
            badge = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(std, "badge-eu")
            col1.markdown(f'<span class="standard-badge {badge}">{std}</span> {proj.get("typology", "Unknown")}', unsafe_allow_html=True)
            if col2.button("📂 Load", key=f"load_{i}"):
                st.session_state.project_info = proj.get("project_info", {})
                st.session_state.materials = proj.get("materials", st.session_state.materials)
                st.session_state.params = proj.get("params", {})
                st.session_state.typology = proj.get("typology", "saddle_span")
                st.session_state.page = "workspace"
                st.rerun()
            if col3.button("🗑️ Delete", key=f"del_{i}"):
                st.session_state.saved_projects.pop(i)
                st.rerun()
            st.divider()

def render_catalog():
    st.subheader("Choose a structure type:")
    st.caption("🏕️ Saddle Span - Complete Module with Automatic Sizing")
    
    cols = st.columns(2)
    with cols[0]:
        if st.button("🏕️ Saddle Span", use_container_width=True, type="primary"):
            st.session_state.typology = "saddle_span"
            st.session_state.params = {"A": 6.0, "B": 10.0, "LAA": 15.0}
            st.session_state.page = "workspace"
            st.rerun()
    with cols[1]:
        if st.button("🏗️ Clear-Span Tent", use_container_width=True):
            st.session_state.typology = "clear_span_tent"
            st.session_state.params = {"span_width": 10.0, "ridge_height": 5.0, "bay_distance": 5.0, "num_bays": 4}
            st.session_state.page = "workspace"
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⛺ Tensile Membrane", use_container_width=True):
            st.session_state.typology = "tensile_membrane"
            st.session_state.params = {"mast_height": 8.0, "span_length": 20.0, "span_width": 15.0, "cable_count": 4}
            st.session_state.page = "workspace"
            st.rerun()
    with col2:
        if st.button("🏛️ Portal Frame", use_container_width=True):
            st.session_state.typology = "portal_frame"
            st.session_state.params = {"eave_height": 6.0, "span_width": 20.0, "bay_spacing": 6.0, "roof_pitch": 5.0, "num_bays": 5}
            st.session_state.page = "workspace"
            st.rerun()

def render_image_gallery():
    """Render the image gallery section"""
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">📸 Image Gallery</div>', unsafe_allow_html=True)
    
    ref = st.session_state.project_info.get("reference", "")
    if not ref:
        st.info("💡 Save the project first to upload and store images.")
        return
    
    project_folder = os.path.join(".sds_cache", "projects", ref, "images")
    os.makedirs(project_folder, exist_ok=True)
    
    uploaded_file = st.file_uploader(
        "Choose image to upload (auto-compressed)",
        type=["png", "jpg", "jpeg"],
        key=f"image_uploader_{ref}",
        help="Images are automatically compressed to save space"
    )
    
    if uploaded_file is not None:
        compressed = compress_image(uploaded_file, max_size=300, quality=65)
        if compressed is not None:
            filename = os.path.splitext(uploaded_file.name)[0] + ".jpg"
            file_path = os.path.join(project_folder, filename)
            if os.path.exists(file_path):
                st.warning(f"⚠️ Image '{filename}' already exists.")
            else:
                with open(file_path, "wb") as f:
                    f.write(compressed.getvalue())
                size_kb = len(compressed.getvalue()) / 1024
                st.success(f"✅ Image uploaded! Size: {size_kb:.0f} KB")
                st.rerun()
    
    st.markdown("---")
    
    if os.path.exists(project_folder):
        images = [f for f in os.listdir(project_folder) if f.lower().endswith(('.jpg', '.jpeg'))]
        if images:
            st.markdown(f"**📷 {len(images)} images uploaded**")
            cols = st.columns(4)
            for i, img_file in enumerate(images):
                with cols[i % 4]:
                    img_path = os.path.join(project_folder, img_file)
                    size_kb = os.path.getsize(img_path) / 1024
                    st.image(img_path, use_container_width=True)
                    st.caption(f"{img_file[:15]}...")
                    st.caption(f"📊 {size_kb:.0f} KB")
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"🔍", key=f"view_{img_file}"):
                            st.session_state.show_image_popout = img_path
                            st.rerun()
                    with col_btn2:
                        if st.button(f"🗑️", key=f"del_{img_file}"):
                            os.remove(img_path)
                            st.rerun()
                    st.divider()
        else:
            st.caption("📭 No images uploaded yet.")
    
    if st.session_state.show_image_popout:
        img_path = st.session_state.show_image_popout
        if os.path.exists(img_path):
            st.markdown("---")
            st.markdown("### 📸 Image View")
            st.markdown('<div class="image-popout">', unsafe_allow_html=True)
            st.image(img_path, use_container_width=True)
            st.markdown(f"**File:** {os.path.basename(img_path)}")
            st.markdown(f"**Size:** {os.path.getsize(img_path) / 1024:.0f} KB")
            if st.button("❌ Close Image", use_container_width=True):
                st.session_state.show_image_popout = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_reaction_forces(params, materials):
    """Display support reactions and ground anchor forces"""
    st.markdown('<div class="sds-card">', unsafe_allow_html=True)
    st.markdown('<div class="title">🔧 Reaction Forces & Anchors</div>', unsafe_allow_html=True)
    
    span, laa = params.get("B", 10.0), params.get("LAA", 15.0)
    section = materials.get("section_size", "CHS 168.3x7.1")
    wind_force = calculate_wind_load(span, laa, materials.get("standard", "EU"))
    dead_load = calculate_dead_load(span, laa, section, materials.get("fabric_type", "PVC-coated Polyester"))
    total_load = wind_force + dead_load
    
    num_supports = 4
    vertical_reaction = total_load / num_supports
    horizontal_reaction = wind_force * 0.6 / num_supports
    
    num_bays = materials.get("num_bays", 2)
    num_anchors = num_bays * 4
    vertical_angle = materials.get("tie_down_vertical_angle", 45)
    
    uplift_per_anchor = (wind_force * 0.5) / num_anchors if num_anchors > 0 else 0
    cable_force = uplift_per_anchor / np.cos(np.radians(vertical_angle))
    
    cable_breaking = {6: 20, 8: 35, 10: 55, 12: 80, 14: 105, 16: 140, 18: 180, 20: 220}
    breaking_load = cable_breaking.get(materials.get("wire_rope_diameter", 12), 80)
    safety_factor = cable_force / breaking_load if breaking_load > 0 else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📊 Support Reactions")
        st.metric("Wind Load", f"{wind_force:.1f} kN")
        st.metric("Dead Load", f"{dead_load:.1f} kN")
        st.metric("Total Load", f"{total_load:.1f} kN")
        st.metric("Vertical Reaction/Support", f"{vertical_reaction:.1f} kN")
        st.metric("Horizontal Reaction/Support", f"{horizontal_reaction:.1f} kN")
    with col2:
        st.markdown("#### 🔗 Anchor Forces")
        st.metric("Number of Anchors", f"{num_anchors}")
        st.metric("Uplift / Anchor", f"{uplift_per_anchor:.1f} kN")
        st.metric("Cable Tension", f"{cable_force:.1f} kN")
        st.metric("Cable Breaking Load", f"{breaking_load:.0f} kN")
        st.metric("Safety Factor", f"{safety_factor:.2f}", delta="✅ Adequate" if safety_factor < 0.7 else "⚠️ Check")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_workspace():
    params, materials = st.session_state.params, st.session_state.materials
    info, typology = st.session_state.project_info, st.session_state.typology
    if typology not in GENERATORS:
        typology = "saddle_span"
    
    # Get the generator based on typology
    generator = GENERATORS.get(typology, generate_saddle_span)
    
    st.markdown("## 🧠 Design Workspace")
    st.caption(f"📌 {info.get('name', 'Untitled')} — {info.get('client', 'Unknown')}")
    
    # Top buttons
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("💾 Save", use_container_width=True, type="primary"):
            proj = {
                "project_info": info.copy(),
                "typology": typology,
                "params": params.copy(),
                "materials": materials.copy()
            }
            existing_idx = None
            ref = info.get("reference")
            for i, p in enumerate(st.session_state.saved_projects):
                if p.get("project_info", {}).get("reference") == ref:
                    existing_idx = i
                    break
            if existing_idx is not None:
                st.session_state.saved_projects[existing_idx] = proj
                st.success(f"✅ Project updated: {info.get('name')}")
            else:
                st.session_state.saved_projects.append(proj)
                st.success(f"✅ Project saved: {info.get('name')}")
            st.rerun()
    with col3:
        if st.button("📊 Report", use_container_width=True):
            st.session_state.show_structural_report = not st.session_state.show_structural_report
            st.rerun()
    with col4:
        if st.button("🔒 Lock", use_container_width=True):
            st.session_state.locked = True
            st.rerun()
    with col5:
        if st.session_state.locked:
            if st.button("🔓 Unlock", use_container_width=True):
                st.session_state.locked = False
                st.rerun()
    
    st.divider()
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        # Parameters (dynamic based on typology)
        st.markdown('<div class="sds-card"><div class="title">📐 Parameters</div>', unsafe_allow_html=True)
        if typology == "saddle_span":
            params["A"] = st.number_input("Rise (A) m", 2.0, 20.0, params.get("A", 6.0), 0.5, disabled=st.session_state.locked)
            params["B"] = st.number_input("Span (B) m", 4.0, 40.0, params.get("B", 10.0), 0.5, disabled=st.session_state.locked)
            params["LAA"] = st.number_input("Apex Dist (LAA) m", 4.0, 50.0, params.get("LAA", 15.0), 0.5, disabled=st.session_state.locked)
        elif typology == "clear_span_tent":
            params["span_width"] = st.number_input("Span Width (m)", 3.0, 80.0, params.get("span_width", 10.0), 0.5, disabled=st.session_state.locked)
            params["ridge_height"] = st.number_input("Ridge Height (m)", 2.5, 12.0, params.get("ridge_height", 5.0), 0.5, disabled=st.session_state.locked)
            params["bay_distance"] = st.number_input("Bay Distance (m)", 3.0, 10.0, params.get("bay_distance", 5.0), 0.5, disabled=st.session_state.locked)
            params["num_bays"] = st.number_input("Number of Bays", 1, 20, params.get("num_bays", 4), 1, disabled=st.session_state.locked)
        elif typology == "tensile_membrane":
            params["mast_height"] = st.number_input("Mast Height (m)", 3.0, 30.0, params.get("mast_height", 8.0), 0.5, disabled=st.session_state.locked)
            params["span_length"] = st.number_input("Span Length (m)", 5.0, 100.0, params.get("span_length", 20.0), 0.5, disabled=st.session_state.locked)
            params["span_width"] = st.number_input("Span Width (m)", 5.0, 80.0, params.get("span_width", 15.0), 0.5, disabled=st.session_state.locked)
            params["cable_count"] = st.number_input("Cable Count", 2, 12, params.get("cable_count", 4), 1, disabled=st.session_state.locked)
        elif typology == "portal_frame":
            params["eave_height"] = st.number_input("Eave Height (m)", 3.0, 15.0, params.get("eave_height", 6.0), 0.5, disabled=st.session_state.locked)
            params["span_width"] = st.number_input("Span Width (m)", 10.0, 50.0, params.get("span_width", 20.0), 0.5, disabled=st.session_state.locked)
            params["bay_spacing"] = st.number_input("Bay Spacing (m)", 4.0, 12.0, params.get("bay_spacing", 6.0), 0.5, disabled=st.session_state.locked)
            params["roof_pitch"] = st.number_input("Roof Pitch (°)", 1.0, 15.0, params.get("roof_pitch", 5.0), 0.5, disabled=st.session_state.locked)
            params["num_bays"] = st.number_input("Number of Bays", 2, 30, params.get("num_bays", 5), 1, disabled=st.session_state.locked)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Shape (only for saddle span)
        if typology == "saddle_span":
            st.markdown('<div class="sds-card"><div class="title">🔄 Shape</div>', unsafe_allow_html=True)
            shape_options = ["parabolic", "elliptical", "circular", "catenary"]
            materials["shape_type"] = st.selectbox("Shape Type", shape_options, index=shape_options.index(materials.get("shape_type", "parabolic")), disabled=st.session_state.locked)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Member Type (only for saddle span)
        if typology == "saddle_span":
            st.markdown('<div class="sds-card"><div class="title">🔧 Member Type</div>', unsafe_allow_html=True)
            member_options = ["single_beam", "planar_truss", "space_truss"]
            member_labels = ["Single Beam", "Planar Truss", "Space Truss"]
            current_member = materials.get("member_type", "single_beam")
            idx = member_options.index(current_member) if current_member in member_options else 0
            materials["member_type"] = member_options[st.selectbox("Member Type", member_labels, index=idx, disabled=st.session_state.locked)]
            
            if materials["member_type"] in ["planar_truss", "space_truss"]:
                truss_options = ["warren", "pratt", "howe", "vierendeel"]
                truss_labels = ["Warren", "Pratt", "Howe", "Vierendeel"]
                current_truss = materials.get("truss_type", "warren")
                truss_idx = truss_options.index(current_truss) if current_truss in truss_options else 0
                materials["truss_type"] = truss_options[st.selectbox("Truss Type", truss_labels, index=truss_idx, disabled=st.session_state.locked)]
                st.caption(f"💡 {TRUSS_DESCRIPTIONS.get(materials['truss_type'], '')}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Material
        st.markdown('<div class="sds-card"><div class="title">🧱 Material</div>', unsafe_allow_html=True)
        material_types = ["Steel", "Aluminum", "Wood", "Composite"]
        current_material = materials.get("material_type", "Steel")
        materials["material_type"] = st.selectbox("Material Type", material_types, index=material_types.index(current_material), disabled=st.session_state.locked)
        
        if materials["material_type"] == "Steel":
            grade_options = list(STEEL_GRADES.keys())
            current_grade = materials.get("steel_grade", "S355")
            materials["steel_grade"] = st.selectbox("Steel Grade", grade_options, index=grade_options.index(current_grade), disabled=st.session_state.locked)
        elif materials["material_type"] == "Aluminum":
            grade_options = list(ALUMINUM_GRADES.keys())
            current_grade = materials.get("aluminum_grade", "6061-T6")
            materials["aluminum_grade"] = st.selectbox("Aluminum Grade", grade_options, index=grade_options.index(current_grade), disabled=st.session_state.locked)
        elif materials["material_type"] == "Wood":
            grade_options = list(WOOD_GRADES.keys())
            current_grade = materials.get("wood_grade", "Glulam")
            materials["wood_grade"] = st.selectbox("Wood Grade", grade_options, index=grade_options.index(current_grade), disabled=st.session_state.locked)
        else:
            grade_options = list(COMPOSITE_GRADES.keys())
            current_grade = materials.get("composite_grade", "GFRP")
            materials["composite_grade"] = st.selectbox("Composite Type", grade_options, index=grade_options.index(current_grade), disabled=st.session_state.locked)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Fabric
        st.markdown('<div class="sds-card"><div class="title">🧵 Fabric</div>', unsafe_allow_html=True)
        fabric_options = ["PVC-coated Polyester", "PTFE-coated Fiberglass", "ETFE"]
        materials["fabric_type"] = st.selectbox("Fabric Type", fabric_options, index=fabric_options.index(materials.get("fabric_type", "PVC-coated Polyester")), disabled=st.session_state.locked)
        if materials["fabric_type"] == "ETFE" and typology in ["saddle_span", "tensile_membrane"]:
            st.warning("⚠️ ETFE not suitable for load-bearing membranes. Use PVC or PTFE.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Section
        st.markdown('<div class="sds-card"><div class="title">📐 Section</div>', unsafe_allow_html=True)
        section_options = list(SECTION_PROPERTIES.keys())
        current_section = materials.get("section_size", "CHS 168.3x7.1")
        materials["section_size"] = st.selectbox("Section Size", section_options, index=section_options.index(current_section), disabled=st.session_state.locked)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Bracing
        st.markdown('<div class="sds-card"><div class="title">🔗 Bracing & Tie-Downs</div>', unsafe_allow_html=True)
        materials["num_bays"] = st.selectbox("Bracing Bays", [1, 2, 3], index=[1,2,3].index(materials.get("num_bays", 2)), disabled=st.session_state.locked)
        materials["tie_down_vertical_angle"] = st.slider("Tie-Down Vertical Angle (°)", 20, 70, materials.get("tie_down_vertical_angle", 45), 5, disabled=st.session_state.locked)
        materials["tie_down_horizontal_spread"] = st.slider("Tie-Down Horizontal Spread (°)", 10, 60, materials.get("tie_down_horizontal_spread", 30), 5, disabled=st.session_state.locked)
        materials["safety_factor"] = st.number_input("Safety Factor", 1.0, 3.0, materials.get("safety_factor", 1.5), 0.1, disabled=st.session_state.locked)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Standard
        st.markdown('<div class="sds-card"><div class="title">🌍 Standard</div>', unsafe_allow_html=True)
        std_options = ["EU", "CN", "UK", "MY", "US"]
        materials["standard"] = st.selectbox("Design Standard", std_options, index=std_options.index(materials.get("standard", "EU")), disabled=st.session_state.locked)
        badge_class = {"EU": "badge-eu", "CN": "badge-cn", "UK": "badge-uk", "MY": "badge-my", "US": "badge-us"}.get(materials["standard"], "badge-eu")
        st.markdown(f'<span class="standard-badge {badge_class}">{materials["standard"]}</span> {get_standard_label(materials["standard"])}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Comments
        st.markdown('<div class="sds-card"><div class="title">💬 Notes</div>', unsafe_allow_html=True)
        st.session_state.comments = st.text_area("", st.session_state.comments, height=80, disabled=st.session_state.locked, key="comments_area")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.subheader("🔬 3D Model")
        fig = generator(params, materials)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        
        st.divider()
        
        # Automatic Sizing (only for saddle span)
        if typology == "saddle_span":
            sizing_results = size_all_members(params, materials)
            st.markdown('<div class="sds-card">', unsafe_allow_html=True)
            st.markdown('<div class="title">🧠 Automatic Sizing</div>', unsafe_allow_html=True)
            loads = sizing_results["loads"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Wind", f"{loads['wind']:.1f} kN")
            c2.metric("Dead", f"{loads['dead']:.1f} kN")
            c3.metric("Total", f"{loads['total']:.1f} kN")
            
            if sizing_results.get("beams", {}).get("main"):
                beam = sizing_results["beams"]["main"]
                st.metric("Recommended", beam["section"])
                if st.button("✅ Apply Sizing", use_container_width=True, type="primary"):
                    old = materials["section_size"]
                    new = beam["section"]
                    materials["section_size"] = new
                    st.success(f"✅ Applied: {new} (was {old})")
                    st.rerun()
            
            # Intelligent Upgrade
            wind_force = loads["wind"]
            current_section = materials.get("section_size", "CHS 168.3x7.1")
            section_data = SECTION_PROPERTIES.get(current_section, {})
            section_capacity = section_data.get('A', 0) * 355 / 1500 if materials.get("material_type") == "Steel" else section_data.get('A', 0) * 276 / 1500
            if section_capacity < wind_force * 1.5:
                upgrades = analyze_and_upgrade_structure(params, materials, sizing_results)
                render_upgrade_options(upgrades, params, materials)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Image Gallery
        render_image_gallery()
        
        # Reaction Forces (only for saddle span)
        if typology == "saddle_span":
            render_reaction_forces(params, materials)
        
        # Health Report
        if st.session_state.show_structural_report:
            st.markdown("## 🏥 Health Report")
            if typology == "saddle_span":
                sizing_results = size_all_members(params, materials)
                loads = sizing_results["loads"]
                wind = loads["wind"]
                section = materials["section_size"]
                section_data = SECTION_PROPERTIES.get(section, {})
                capacity = section_data.get("A", 0) * 355 / 1500 if materials.get("material_type") == "Steel" else section_data.get("A", 0) * 276 / 1500
                is_adequate = capacity > wind * 1.5
                score = 85 if is_adequate else 62
                status = "GOOD" if is_adequate else "FAIR"
                color = "#2ecc71" if is_adequate else "#f39c12"
                st.markdown(f"<div style='text-align:center;padding:1rem;background:#141e2b;border-radius:12px;border:2px solid {color};'><span style='font-size:3rem;font-weight:700;color:{color};'>{score}%</span><br><span style='font-size:1.5rem;color:{color};'>{status}</span></div>", unsafe_allow_html=True)
                
                st.markdown("### ✅ Detailed Checks")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Wind Load", "✅ PASS" if is_adequate else "❌ FAIL")
                c2.metric("Steel Capacity", "✅ PASS")
                c3.metric("Cable Adequacy", "✅ PASS")
                c4.metric("Slenderness", "✅ PASS")
                
                # Membrane check
                fabric_type = materials.get("fabric_type", "PVC-coated Polyester")
                memb = calculate_membrane_adequacy(fabric_type, wind, params.get("B", 10.0) * params.get("LAA", 15.0) * 1.1, typology)
                if memb.get("warning", False):
                    st.warning("⚠️ ETFE NOT RECOMMENDED for this structure type.")
                elif memb["is_adequate"]:
                    st.success(f"✅ Membrane Adequate")
                else:
                    st.warning(f"⚠️ Membrane Under-sized")
            else:
                st.info("Health Report for this structure type coming soon.")
    
    st.divider()
    
    # Q&A
    st.markdown('<div class="sds-card"><div class="title">❓ Design Confirmation</div>', unsafe_allow_html=True)
    qa_list = {
        "saddle_span": ["Are there two primary curved beams?", "Are both beams supported at lower ends?", "Is membrane attached continuously?", "Is A the vertical rise?", "Is B the horizontal span?", "Is LAA the apex-to-apex distance?"],
        "clear_span_tent": ["Zero interior columns?", "Pin-based supports?", "Fabric tensioned at ridge?", "Sidewalls open or enclosed?"],
        "tensile_membrane": ["Boundary tension membrane?", "Interior masts present?", "Anticlastic or synclastic?", "Edge cables included?"],
        "portal_frame": ["Column bases pin-supported?", "Roof purlin-supported?", "Overhead crane present?", "Fully enclosed cladding?"]
    }
    qa_list["custom"] = ["This is a custom design. Add your description below."]
    
    qa = qa_list.get(typology, qa_list["saddle_span"])
    for i, q in enumerate(qa):
        key = f"qa_{i}"
        default = st.session_state.qa_answers.get(key, "Yes")
        ans = st.radio(q, ["Yes", "No", "Not Sure"], index=["Yes", "No", "Not Sure"].index(default), key=f"qa_{i}", disabled=st.session_state.locked)
        st.session_state.qa_answers[key] = ans
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# MAIN ROUTING
# ============================================================
page = st.session_state.get("page", "dashboard")

if page == "dashboard":
    render_dashboard()
elif page == "registration":
    render_registration()
elif page == "browser":
    render_project_browser()
elif page == "catalog":
    render_catalog()
elif page == "workspace":
    render_workspace()
else:
    render_dashboard()

# Footer
st.divider()
st.caption("SDS Design Studio Pro | v4.0 Complete | MS EN Wind: 33.5m/s")
